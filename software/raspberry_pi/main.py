#!/usr/bin/env python3
"""SAILSAFE - processo principal do Raspberry Pi.

Maquina de estados: DISARMED <-> ARMED / NAV.
- Arranca sempre em DISARMED (seguro).
- DISARMED: nunca envia propulsao; motores parados pelo failsafe do ESP32.
- ARMED: envia heartbeat a 5 Hz (0/0) para manter o failsafe satisfeito.
- NAV: navegacao por waypoints. O WaypointNav da o bearing para o waypoint
  atual, que passa a ser o alvo do heading hold (ja nao um rumo fixo). O
  controlador calcula o steer, o mixer converte em L/R (<=30%) e o comando
  segue para o ESP32, fechando a malha pelo barco SINTETICO (sem GPS, BNO055
  nem motores). Trocar as fontes pelas reais nao altera a logica de controlo.
- Fim de missao: para os motores e volta a DISARMED (estado seguro).
- STOP tem prioridade absoluta e forca DISARMED.
- O regresso da ligacao serie nunca arma sozinho.
- Fontes sinteticas NUNCA comandam motores sem ser pedido na linha de
  comandos. Ver nav_guard() e os modos --sim / --sim-motores.
- Com --gps a posicao vem do NEO-8M e e registada em todos os estados,
  nao so em NAV: uma sessao de bancada passa a deixar dados de dispersao
  sem ser preciso correr o tools/gps_bench.py ao lado.
- Perder posicao em NAV leva a estado seguro, com a mesma politica da
  perda de serie e uma tolerancia curta. Ver PositionWatch.
- O ponto de regresso e gravado no ARM, a partir de fixes validados, e
  nao se reescreve. Sem ele, com --gps, o ARM e recusado.
- O STOP e repetido ate o ESP32 confirmar; nao confirmar e ruidoso e fica
  no log. Ver communication/serial_link.py.
- ARMAR exige confirmacao de que a trava do ESP32 abriu. Sem prova de que
  a propulsao esta destravada, o sistema fica DISARMED.
- O controlo nao depende de terminal: FIFO e SIGUSR1 funcionam debaixo de
  systemd ou nohup. Ver commands.py.

Regista a sessao em CSV via telemetry.SessionLogger.
Comandos: a=ARM  n=NAV  d=DISARM  s=STOP  q=sair
  terminal (se houver tty)  |  echo s > FIFO  |  kill -USR1 <pid> (STOP)
"""

import argparse
import math
import os
import signal
import time
from collections import namedtuple

from commands import CommandBus, DEFAULT_FIFO
from communication.serial_link import SerialLink
from telemetry.logger import SessionLogger
from control.heading import HeadingController
from control.mixer import mix
from control.navigation import WaypointNav
from control.real_position import PositionUnavailable, RealBoat, create_neo8m
from control.return_point import ReturnPoint, ReturnPointUnavailable
from control.sources import SimulatedBoat, SimulatedHeading

HEARTBEAT_S = 0.2
RECONNECT_S = 10
SAFE_MAX = 30        # teto que o ESP32 aceita (rejeita comandos > 30%)
NAV_THROTTLE = 20    # impulso base em NAV, com margem para o steer
ARRIVAL_RADIUS_M = 4.0
DISARMED, ARMED, NAV = "DISARMED", "ARMED", "NAV"

GPS_PORT = "/dev/serial0"
GPS_POLL_S = 0.5     # o modulo emite a 1 Hz; ler ao dobro nao deixa acumular
GPS_LOG_S = 1.0      # uma linha de posicao por segundo no CSV da sessao
GPS_PRINT_S = 5.0    # no ecra e so para o operador ver que ha sinal

# Ciclos de NAV seguidos sem posicao antes de abortar a missao. Ver
# PositionWatch para o porque de nao ser 1.
NAV_POS_MISSES = 3

# Missao SINTETICA de demonstracao: 40 m a Norte, depois mais 40 m a Este.
# As coordenadas sao DERIVADAS de uma origem, e nao escritas a mao, para
# que a mesma missao possa ser montada a partir do ponto de regresso real
# quando ha GPS. Waypoints absolutos so tinham sentido enquanto a origem
# tambem era inventada.
MISSION_START = (38.73600, -9.14000)
MISSION_OFFSETS_M = [
    (40.0, 0.0),     # ~40 m a Norte  (bearing 0)
    (40.0, 40.0),    # e mais ~40 m a Este  (bearing 90 no segundo troco)
]

METRES_PER_DEG_LAT = 111320.0


def mission_from(lat, lon, offsets=MISSION_OFFSETS_M):
    """Waypoints a partir de uma origem, com deslocamentos em metros.

    offsets sao pares (norte, este) em metros. A conversao usa a latitude
    da origem para todos os pontos: a esta escala (dezenas de metros) a
    diferenca e de centimetros, muito abaixo da dispersao do proprio GPS.
    Nao serve para missoes de quilometros, e nao e para isso que existe.
    """
    escala_lon = METRES_PER_DEG_LAT * math.cos(math.radians(lat))
    return [(lat + norte / METRES_PER_DEG_LAT, lon + este / escala_lon)
            for norte, este in offsets]


MISSION_WAYPOINTS = mission_from(*MISSION_START)

running = True


def shutdown(signum, frame):
    global running
    print(f"\n[INFO] Sinal {signum} recebido. A terminar em seguranca.", flush=True)
    running = False


def motivo_sem_fix(gps):
    """Porque e que nao ha posicao agora, em linguagem util.

    O last_reject do RealPosition diz porque e que a ultima trama foi
    RECUSADA por criterio -- satelites, HDOP, ilha nula. Nao cobre o caso
    em que houve fixes bons e o modulo se calou: aí nada foi recusado, e o
    last_reject fica preso no "ainda sem leituras" do arranque, que e
    exatamente a mensagem errada. Silencio e recusa sao defeitos com
    remedios opostos, e o ecra tem de os distinguir.
    """
    idade = gps.fix_age()
    if idade is not None and idade > gps.max_stale_s:
        return (f"ultimo fix ha {idade:.1f} s (maximo "
                f"{gps.max_stale_s:.1f} s) -- modulo calado")
    return gps.last_reject


def qualidade(valor, fmt=".2f"):
    """Formata satelites/HDOP, que podem nao existir.

    As tramas RMC dao posicao e nao dao qualidade nenhuma: satellites e
    hdop vem a None e o Fix e aceite na mesma, porque o estado 'A' ja diz
    que ha fix. Quem regista isto tem de saber a diferenca entre "nao
    medido" e "zero" -- formatar None como se fosse numero rebenta, e
    imprimir 0 seria pior, porque parecia uma medicao.
    """
    return "n/d" if valor is None else format(valor, fmt)


NavStep = namedtuple("NavStep", "left right bearing dist done lat lon")


def stop_confirmado(link, log, state, motivo):
    """Manda parar, regista o resultado e diz alto se nao foi confirmado.

    Devolve o StopResult. Um StopResult so e verdadeiro quando confirmado,
    portanto `if stop_confirmado(...)` ja e a leitura conservadora.

    Nao confirmar nao e "os motores continuam a andar": e "nao sabemos se
    o comando chegou, e o failsafe do ESP32 trava a propulsao dentro de
    1 s". A diferenca entre as duas leituras passa a estar no log em vez
    de ficar por adivinhar.

    Sem porta aberta nao ha alarme nenhum. Um STOP sem serie nao falhou:
    nunca houve caminho para a propulsao, portanto nao ha nada a parar.
    Gritar aqui seria gritar em todas as sessoes de simulacao sem ESP32 --
    e um alarme que dispara quando nao esta nada em jogo e um alarme que
    se aprende a ignorar, o que o torna pior do que nao existir.
    """
    havia_porta = link.is_open
    r = link.stop_motors()
    for linha in r.lines:
        print(f"[RX] {linha}", flush=True)
        log.log("RX", state, linha)
    if r.confirmed:
        log.log("STOP", state, f"{motivo}: confirmado ({r.attempts} tent.)")
    elif not havia_porta:
        log.log("STOP", state, f"{motivo}: sem serie, nada para parar")
    else:
        log.log("ALERTA", state, f"{motivo}: STOP NAO confirmado - {r.reason}")
        print(f"[ALERTA] STOP nao confirmado pelo ESP32 ({r.reason}).", flush=True)
        print("[ALERTA] O failsafe trava a propulsao ~1 s apos o ultimo "
              "comando. Cortar a alimentacao se houver duvida.", flush=True)
    return r

# --- guarda do modo NAV -------------------------------------------------
# O nav_step() fecha a malha no SimulatedBoat: le a posicao dele, calcula
# L/R a partir dela e realimenta-o. Se esses mesmos L/R seguirem para o
# ESP32, motores reais executam a missao de um barco que so existe em
# memoria -- o barco fisico vai onde calhar e o sintetico "chega" ao
# waypoint. A malha fica fechada no lado errado.
#
# Por isso o modo NAV pergunta pela PROVENIENCIA das fontes antes de deixar
# comandar seja o que for.

NAV_RECUSADO = "recusado"      # fontes sinteticas sem autorizacao explicita
NAV_SEM_MOTORES = "sem_motores"  # simulacao: calcula e imprime, envia so 0/0
NAV_COM_MOTORES = "com_motores"  # propulsao real segue para o ESP32


def is_synthetic(source):
    """True se a fonte for sintetica.

    O valor por omissao e True de proposito: uma fonte que nao se declara
    e tratada como sintetica e o NAV recusa. Falhar para o lado conservador
    e a mesma politica do RealHeading -- perante duvida, nao dar numero.
    """
    return getattr(source, "SYNTHETIC", True)


def nav_guard(sources, allow_sim=False, sim_drives_motors=False):
    """Decide se o NAV pode arrancar e se pode comandar motores.

    Devolve (modo, motivo). O modo e uma das constantes NAV_* acima.

    Regra: com fontes reais, o NAV comanda os motores -- e para isso que
    existe. Com fontes sinteticas exige-se um pedido explicito na linha de
    comandos, e mesmo assim a propulsao so sai com --sim-motores. O
    --sim sozinho segue o padrao ja usado no tools/heading_bench.py:
    calcula os comandos e imprime-os sem os enviar.
    """
    sinteticas = [s for s in sources if is_synthetic(s)]
    if not sinteticas:
        return NAV_COM_MOTORES, "fontes reais"
    nomes = ", ".join(type(s).__name__ for s in sinteticas)
    if sim_drives_motors:
        return NAV_COM_MOTORES, f"--sim-motores com fontes sinteticas ({nomes})"
    if allow_sim:
        return NAV_SEM_MOTORES, f"--sim: fontes sinteticas ({nomes}), sem propulsao"
    return NAV_RECUSADO, (f"fontes sinteticas ({nomes}) sem --sim. "
                          "Motores reais nao seguem um barco imaginario.")


# --- perda de posicao em NAV --------------------------------------------
# O RealPosition ja se recusa a devolver uma posicao velha: passados
# max_stale_s levanta PositionUnavailable em vez de entregar a ultima
# conhecida. Falta decidir o que o barco faz com essa recusa, e e isso que
# esta classe decide.
#
# Porque nao abortar a primeira falha: a 1 Hz, uma unica trama perdida
# poe a idade do fix no limite. Um aborto por cada mensagem perdida seria
# um alarme a disparar quando nao se passa nada -- e o projeto ja escreveu,
# a proposito dos contadores do gps_bench, que um alarme desses e pior do
# que nao existir, porque se aprende a ignora-lo.
#
# Porque nao seguir em frente: navegar sem posicao e navegar as cegas, e a
# unica coisa que o barco sabe fazer as cegas e continuar a andar para onde
# estava virado. Durante a tolerancia a propulsao vai a ZERO e o heartbeat
# continua -- o barco fica parado e comandavel, em vez de parado pelo
# failsafe ou a andar sem saber para onde.
#
# O orcamento total de silencio e max_stale_s + max_misses * HEARTBEAT_S,
# hoje 2,5 + 3 x 0,2 = 3,1 s.

class PositionWatch:
    """Conta falhas seguidas de posicao e decide quando abortar a missao.

    LATCHING, pela mesma razao da guarda de bateria e da trava do ESP32:
    recuperar o fix nao desfaz o aborto. Um GPS que volta a si sozinho
    reiniciaria a missao a meio, sem ninguem ter decidido nada -- e um
    caminho de "parado por falha" para "a andar" sem gesto humano pelo
    meio e exatamente o que o resto do sistema recusa ter.

    Nao faz I/O: quem chama e que apanha a excecao e reporta o resultado.
    """

    def __init__(self, max_misses=NAV_POS_MISSES):
        self.max_misses = max_misses
        self.misses = 0
        self.tripped = False
        self.reason = ""

    def ok(self):
        """Posicao valida: limpa a contagem. Nao levanta um aborto ja dado."""
        self.misses = 0
        return self.tripped

    def miss(self, motivo):
        """Falha de posicao. Devolve True quando a missao tem de abortar."""
        self.misses += 1
        if self.misses >= self.max_misses:
            if not self.tripped:
                self.reason = f"{self.misses} ciclos sem posicao: {motivo}"
            self.tripped = True
        return self.tripped

    def reset(self):
        """Limpa o aborto. Gesto explicito -- entrar em NAV ou em ARM."""
        self.misses = 0
        self.tripped = False
        self.reason = ""

    def describe(self):
        if self.tripped:
            return f"abortado ({self.reason})"
        if self.misses:
            return f"{self.misses}/{self.max_misses} ciclos sem posicao"
        return "posicao valida"


def nav_step(nav, ctrl, boat, throttle=NAV_THROTTLE, cap=SAFE_MAX, dt=HEARTBEAT_S):
    """Um passo de navegacao autonoma, sem qualquer I/O.

    Le a posicao do barco, pede ao WaypointNav o bearing para o waypoint
    atual e usa-o como alvo do heading hold; o controlador da o steer, o
    mixer converte em comandos de motor limitados a [0, cap], e o resultado
    realimenta o barco SINTETICO (fecha a malha).

    Devolve um NavStep. Com a missao concluida devolve left=right=0 e
    done=True, ou seja, sem propulsao.

    Nao toca em serie nem em ficheiros, para poder ser testado sem hardware.
    """
    lat, lon = boat.position()
    bearing, dist, done = nav.update(lat, lon)
    if done:
        return NavStep(0, 0, None, 0.0, True, lat, lon)
    ctrl.set_target(bearing)                     # o alvo passa a vir do waypoint
    steer = ctrl.update(boat.heading)            # rumo medido antes de atuar
    left, right = mix(throttle, steer, 0, cap)
    boat.update(left, right, dt=dt)              # SINTETICO: fecha a malha
    return NavStep(left, right, bearing, dist, False, lat, lon)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="SAILSAFE - processo principal.")
    p.add_argument("--sim", action="store_true",
                   help="permite NAV com fontes sinteticas; calcula e imprime "
                        "os comandos SEM os enviar (so heartbeat 0/0)")
    p.add_argument("--sim-motores", action="store_true", dest="sim_motores",
                   help="PERIGO: NAV com fontes sinteticas a comandar mesmo os "
                        "motores. So com o barco preso na bancada.")
    p.add_argument("--esp32-port", default=None, dest="esp32_port",
                   help="porta serie do ESP32. Por omissao a do SerialLink "
                        "(/dev/ttyUSB0). Um nome estavel de "
                        "/dev/serial/by-id/ evita que dois dispositivos USB "
                        "troquem de numero entre arranques.")
    p.add_argument("--gps", action="store_true",
                   help="usa o GPS real (NEO-8M) como fonte de posicao. Sem "
                        "isto a posicao e a do barco sintetico.")
    p.add_argument("--gps-port", default=GPS_PORT, dest="gps_port",
                   help=f"porta serie do GPS (por omissao {GPS_PORT})")
    p.add_argument("--control-fifo", default=DEFAULT_FIFO, dest="control_fifo",
                   help=f"FIFO de comandos (por omissao {DEFAULT_FIFO}). "
                        "Vazio desliga o FIFO.")
    p.add_argument("--no-tty", action="store_true", dest="no_tty",
                   help="ignora o teclado mesmo havendo terminal")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    log = SessionLogger()
    print("[INFO] SAILSAFE iniciado", flush=True)
    print(f"[INFO] PID {os.getpid()}", flush=True)
    print(f"[INFO] Log da sessao: {log.path}", flush=True)
    state = DISARMED
    log.log("BOOT", state, f"pid={os.getpid()}")
    print(f"[STATE] {state}", flush=True)

    link = SerialLink(args.esp32_port) if args.esp32_port else SerialLink()
    if link.connect():
        print("[INFO] Ligacao serie ao ESP32 ativa", flush=True)
        log.log("SERIAL", state, "conectado")
    else:
        print("[INFO] Sem ESP32; a continuar sem ligacao serie", flush=True)
        log.log("SERIAL", state, "ausente")

    last_hb = 0.0
    last_reconnect = time.monotonic()
    last_gps = 0.0
    last_gps_log = 0.0
    last_gps_print = 0.0

    # Navegacao. Posicao e rumo vem de um barco SINTETICO (sem GPS, BNO055
    # nem motores): em NAV os comandos enviados realimentam-no, fechando a
    # malha nav -> heading hold -> mixer -> barco -> posicao.
    ctrl = HeadingController(kp=2.0, max_steer=100.0)
    gps = None
    home = ReturnPoint()
    watch = PositionWatch()

    if args.gps:
        try:
            gps = create_neo8m(device=args.gps_port)
        except Exception as e:                                  # noqa: BLE001
            # Pediram GPS e nao ha GPS. Continuar sem ele era correr um
            # sistema diferente daquele que foi pedido, com o barco
            # sintetico a fazer de posicao e ninguem a dar por isso. Sair
            # e a unica leitura honesta.
            print(f"[ALERTA] --gps pedido e a porta {args.gps_port} nao abriu: "
                  f"{e}", flush=True)
            print("[ALERTA] Verificar enable_uart=1, dtoverlay=disable-bt e "
                  "que /dev/serial0 aponta para ttyAMA0.", flush=True)
            log.log("ALERTA", state, f"gps nao abriu: {e}")
            log.close()
            raise SystemExit(2)
        print(f"[GPS] NEO-8M em {args.gps_port}", flush=True)
        log.log("GPS", state, f"porta {args.gps_port}")

    if gps is not None:
        # Posicao real, rumo sintetico enquanto nao ha BNO055. O RealBoat
        # declara-se sintetico por causa do rumo, e por isso o nav_guard
        # continua a recusar motores -- que e o que se quer: com um rumo
        # inventado, propulsao real nao sai daqui.
        boat = RealBoat(gps, SimulatedHeading(heading=0.0, yaw_gain=0.4))
    else:
        boat = SimulatedBoat(MISSION_START[0], MISSION_START[1],
                             heading=0.0, yaw_gain=0.4, speed_ms=3.0)
    nav = WaypointNav(MISSION_WAYPOINTS, arrival_radius_m=ARRIVAL_RADIUS_M)

    # As fontes nao mudam durante a execucao, portanto a guarda decide-se
    # uma vez e fica dita no arranque -- e no log -- em vez de so aparecer
    # quando alguem carrega em 'n'.
    nav_mode, nav_motivo = nav_guard([boat], allow_sim=args.sim,
                                     sim_drives_motors=args.sim_motores)
    log.log("NAVMODE", state, f"{nav_mode}: {nav_motivo}")
    if nav_mode == NAV_RECUSADO:
        print(f"[NAV] indisponivel: {nav_motivo}", flush=True)
        print("[NAV] usar --sim (sem propulsao) ou --sim-motores (com o barco "
              "preso na bancada).", flush=True)
    elif nav_mode == NAV_SEM_MOTORES:
        print(f"[NAV] {nav_motivo}. Os comandos sao calculados e impressos, "
              "nao enviados.", flush=True)
    elif args.sim_motores:
        print("[AVISO] --sim-motores: uma missao SINTETICA vai comandar os "
              "motores reais.", flush=True)
        print("[AVISO] O barco fisico nao sabe onde esta. So com ele preso "
              "e fora de agua.", flush=True)

    if gps is not None:
        print("[GPS] posicao real. O ARM grava o ponto de regresso e e "
              "recusado sem ele.", flush=True)
        print(f"[GPS] tolerancia em NAV: {NAV_POS_MISSES} ciclos sem posicao "
              f"(~{NAV_POS_MISSES * HEARTBEAT_S:.1f} s alem da idade maxima do "
              f"fix) antes de abortar.", flush=True)

    with CommandBus(fifo_path=args.control_fifo,
                    use_tty=not args.no_tty) as bus:
        print("[INFO] Caminhos de comando:", flush=True)
        for linha in bus.describe():
            print(linha, flush=True)
        log.log("CONTROL", state,
                "|".join(s.name for s in bus.active) or "nenhum")
        if not bus.can_command():
            print("[AVISO] Sem caminho para ARM/NAV/DISARM: so ha STOP por "
                  "sinal. O processo corre e nao arma.", flush=True)
        if not bus.can_stop():
            # Nao deve acontecer -- o sinal so falha fora da thread
            # principal -- mas se acontecer nao se arma nada.
            print("[ALERTA] Sem caminho de STOP. Nao usar com motores.", flush=True)

        try:
            while running:
                now = time.monotonic()

                k = bus.get()
                if k == "q":
                    break
                elif k == "s":
                    # STOP tem prioridade absoluta: o estado passa a
                    # DISARMED aconteca o que acontecer a confirmacao. Uma
                    # paragem que so vale se o ESP32 responder nao e uma
                    # paragem, e um pedido.
                    state = DISARMED
                    stop_confirmado(link, log, state, "stop")
                    print("[STOP] STOP -> DISARMED", flush=True)
                    print(f"[STATE] {state}", flush=True)
                elif k == "a":
                    if state == DISARMED:
                        # O ponto de regresso e a PRIMEIRA condicao, antes
                        # de se falar com o ESP32. Duas razoes: nao vale a
                        # pena destravar a propulsao para um ARM que vai ser
                        # recusado a seguir, e a condicao mais barata e a
                        # que deve falhar primeiro.
                        #
                        # Sem --gps nao ha ponto de regresso para gravar e
                        # esta condicao nao existe -- na bancada, sem
                        # posicao nenhuma, exigi-la so impediria trabalho.
                        # E com GPS a regra e a mesma que ja vale para a
                        # trava: nao se anuncia ARMED sem saber para onde
                        # e que o barco volta.
                        pode_regresso, motivo_regresso = (
                            home.check() if gps is not None else (True, ""))
                        if not pode_regresso:
                            print(f"[WARN] ARM recusado: ponto de regresso "
                                  f"por gravar - {motivo_regresso}", flush=True)
                            log.log("WARN", state,
                                    f"arm recusado: regresso - {motivo_regresso}")
                        elif link.is_open:
                            # O ESP32 arranca com a propulsao travada e volta a
                            # travar sempre que o failsafe dispara. A trava so
                            # abre com um comando de paragem, e armar e o
                            # momento certo para o mandar: e um gesto humano.
                            #
                            # Armar sem confirmacao seria anunciar ARMED sem
                            # saber se a trava abriu -- e o operador ficava a
                            # acreditar num estado que o firmware nao tem.
                            if stop_confirmado(link, log, state, "arm"):
                                # Verificado antes da trava, GRAVADO so
                                # aqui: o ponto de regresso pertence a um
                                # ARM que aconteceu, nao a um que falhou.
                                gravado = None
                                if gps is not None:
                                    try:
                                        gravado = home.record()
                                    except ReturnPointUnavailable as e:
                                        # A janela azedou entre a
                                        # verificacao e a trava (~0,24 s).
                                        # Raro, e mesmo assim nao se arma.
                                        print(f"[WARN] ARM recusado: o ponto "
                                              f"de regresso deixou de ser "
                                              f"gravavel - {e}", flush=True)
                                        log.log("WARN", state,
                                                f"arm recusado: regresso "
                                                f"perdido - {e}")
                                if gps is not None and gravado is None:
                                    pass          # recusado mesmo acima
                                else:
                                    state = ARMED
                                    last_hb = 0.0
                                    watch.reset()
                                    log.log("STATE", state, "arm")
                                    if gravado is not None:
                                        log.log("REGRESSO", state,
                                                home.describe())
                                        print(f"[REGRESSO] {home.describe()}",
                                              flush=True)
                                    print(f"[STATE] {state}", flush=True)
                            else:
                                print("[WARN] ARM recusado: a trava do ESP32 "
                                      "nao confirmou abertura", flush=True)
                                log.log("WARN", state, "arm recusado: trava nao confirmada")
                        else:
                            print("[WARN] Nao e possivel ARM sem ligacao serie", flush=True)
                            log.log("WARN", state, "arm sem serie")
                elif k == "n":
                    # A serie so e exigida quando o NAV vai mesmo comandar
                    # motores. Uma simulacao sem propulsao nao precisa de
                    # ESP32 nenhum para correr.
                    precisa_serie = nav_mode == NAV_COM_MOTORES
                    if nav_mode == NAV_RECUSADO:
                        print(f"[NAV] recusado: {nav_motivo}", flush=True)
                        log.log("NAV", state, "recusado")
                    elif state != DISARMED:
                        print("[WARN] NAV so a partir de DISARMED", flush=True)
                    elif precisa_serie and not link.is_open:
                        print("[WARN] Nao e possivel NAV sem ligacao serie", flush=True)
                    else:
                        # Com propulsao em jogo, a trava tem de confirmar
                        # abertura antes de a missao comecar -- mesma regra
                        # do ARM. Em simulacao sem motores nao ha trava
                        # nenhuma para abrir.
                        if precisa_serie and not stop_confirmado(link, log, state, "nav"):
                            print("[WARN] NAV recusado: a trava do ESP32 nao "
                                  "confirmou abertura", flush=True)
                            log.log("WARN", state, "nav recusado: trava nao confirmada")
                        elif gps is not None and not home.is_set:
                            # Com posicao real, a missao mede-se a partir do
                            # ponto de regresso. Sem ele nao ha de onde
                            # contar os waypoints -- e, mais a serio, nao ha
                            # para onde voltar se a missao abortar.
                            print("[WARN] NAV recusado: ponto de regresso por "
                                  "gravar (armar primeiro)", flush=True)
                            log.log("WARN", state, "nav recusado: sem regresso")
                        else:
                            state = NAV
                            # Com GPS, os waypoints contam-se do ponto de
                            # regresso; sem ele, da origem sintetica. Em
                            # ambos os casos a missao recomeca do inicio.
                            if gps is not None:
                                waypoints = mission_from(*home.position())
                            else:
                                waypoints = MISSION_WAYPOINTS
                            nav = WaypointNav(waypoints,
                                              arrival_radius_m=ARRIVAL_RADIUS_M)
                            ctrl.clear_target()
                            watch.reset()
                            last_hb = 0.0
                            log.log("STATE", state,
                                    f"missao {len(waypoints)} wp ({nav_mode})")
                            print(f"[STATE] {state} (navegacao por waypoints, "
                                  f"{len(waypoints)} wp, {nav_mode})", flush=True)
                elif k == "d":
                    if state != DISARMED:
                        state = DISARMED
                        stop_confirmado(link, log, state, "disarm")
                        log.log("STATE", state, "disarm")
                        print(f"[STATE] {state}", flush=True)

                # GPS: le-se em TODOS os estados, nao so em NAV. Uma
                # sessao de bancada passa a deixar um registo de posicao
                # com satelites, HDOP e idade do fix, que e a materia
                # prima para refazer a dispersao no local sem ter de
                # correr o gps_bench ao lado. Alimenta tambem a janela do
                # ponto de regresso, para que o ARM encontre a janela ja
                # cheia em vez de ter de esperar por ela.
                if gps is not None and now - last_gps >= GPS_POLL_S:
                    last_gps = now
                    pos = gps.position_or_none()
                    fix = gps.last_fix
                    idade = gps.fix_age()
                    if pos is not None:
                        home.feed(*pos)
                    if now - last_gps_log >= GPS_LOG_S:
                        last_gps_log = now
                        if pos is not None and fix is not None:
                            log.log("GPS", state,
                                    f"lat={pos[0]:.6f} lon={pos[1]:.6f} "
                                    f"sats={qualidade(fix.satellites, '.0f')} "
                                    f"hdop={qualidade(fix.hdop)} "
                                    f"idade={idade:.1f} fonte={fix.source}")
                        else:
                            st = gps.stats
                            log.log("GPS", state,
                                    f"sem posicao: {motivo_sem_fix(gps)} "
                                    f"(tramas={st.seen} checksum_mau="
                                    f"{st.bad_checksum} sem_fix={st.no_fix} "
                                    f"recusadas={st.rejected} "
                                    f"aceites={st.accepted})")
                    if now - last_gps_print >= GPS_PRINT_S:
                        last_gps_print = now
                        if pos is not None and fix is not None:
                            print(f"[GPS] {pos[0]:.6f}, {pos[1]:.6f}  "
                                  f"sats={qualidade(fix.satellites, '.0f')} "
                                  f"hdop={qualidade(fix.hdop)} "
                                  f"idade={idade:.1f} s  "
                                  f"regresso: {home.describe()}", flush=True)
                        else:
                            print(f"[GPS] sem posicao: {motivo_sem_fix(gps)}",
                                  flush=True)

                if not link.is_open and now - last_reconnect >= RECONNECT_S:
                    last_reconnect = now
                    if link.connect():
                        print("[INFO] ESP32 ligado (continua DISARMED)", flush=True)
                        log.log("SERIAL", state, "reconectado")

                # A perda de serie desarma sempre que haja propulsao em jogo.
                # A excecao e o NAV em simulacao sem motores, que nao comanda
                # nada e por isso nao tem nada para desarmar.
                sem_propulsao = state == NAV and nav_mode == NAV_SEM_MOTORES
                if state in (ARMED, NAV) and not link.is_open and not sem_propulsao:
                    state = DISARMED
                    log.log("STATE", state, "perda serie")
                    print("[WARN] Ligacao serie perdida -> DISARMED", flush=True)
                    print(f"[STATE] {state}", flush=True)

                if state == ARMED and now - last_hb >= HEARTBEAT_S:
                    last_hb = now
                    link.send_motors(0, 0)
                    log.log("TX", state, "0,0")
                elif state == NAV and now - last_hb >= HEARTBEAT_S:
                    last_hb = now
                    try:
                        step = nav_step(nav, ctrl, boat)
                    except PositionUnavailable as e:
                        # Sem posicao nao se navega. Enquanto se tolera, a
                        # propulsao vai a ZERO e o heartbeat continua: o
                        # barco fica parado e comandavel, em vez de parado
                        # pelo failsafe ou a andar sem saber para onde.
                        step = None
                        if watch.miss(str(e)):
                            state = DISARMED
                            stop_confirmado(link, log, state, "sem posicao")
                            log.log("NAV", state, f"abortado: {watch.reason}")
                            print(f"[ALERTA] Posicao perdida -> DISARMED "
                                  f"({watch.reason})", flush=True)
                            print("[ALERTA] Recuperar o fix nao recomeca a "
                                  "missao. Armar outra vez, de proposito.",
                                  flush=True)
                            print(f"[STATE] {state}", flush=True)
                        else:
                            link.send_motors(0, 0)
                            log.log("TX", state, "0,0 (sem posicao)")
                            log.log("NAV", state,
                                    f"sem posicao ({watch.describe()}): {e}")
                            print(f"[WARN] sem posicao ({watch.describe()}): "
                                  f"{e}", flush=True)
                    else:
                        watch.ok()
                    if step is None:
                        pass          # perda de posicao, ja tratada acima
                    elif step.done:
                        # missao cumprida: parar e regressar ao estado seguro
                        state = DISARMED
                        stop_confirmado(link, log, state, "fim de missao")
                        log.log("NAV", state, "missao concluida")
                        print("[NAV] Missao concluida -> DISARMED", flush=True)
                        print(f"[STATE] {state}", flush=True)
                    else:
                        # NAV_SEM_MOTORES: os comandos calculam-se e imprimem-se,
                        # mas o que sai para o ESP32 e 0/0 -- o suficiente para
                        # manter o failsafe satisfeito sem dar propulsao.
                        if nav_mode == NAV_COM_MOTORES:
                            link.send_motors(step.left, step.right)
                            log.log("TX", state, f"{step.left:.0f},{step.right:.0f}")
                            marca = ""
                        else:
                            link.send_motors(0, 0)
                            log.log("TX", state, "0,0 (sim)")
                            marca = "  [nao enviado]"
                        log.log("NAV", state,
                                f"wp={nav.index} dist={step.dist:.1f} "
                                f"bearing={step.bearing:.1f} heading={boat.heading:.1f} "
                                f"lat={step.lat:.6f} lon={step.lon:.6f}")
                        print(f"[NAV] wp={nav.index}  dist={step.dist:6.1f} m  "
                              f"bearing={step.bearing:5.1f}  heading={boat.heading:5.1f}  "
                              f"L={step.left:.0f} R={step.right:.0f}{marca}", flush=True)

                if link.is_open:
                    line = link.read_line()
                    if line:
                        print(f"[RX] {line}", flush=True)
                        log.log("RX", state, line)

                time.sleep(0.02)
        finally:
            link.close()
            log.log("SHUTDOWN", state, "")
            log.close()
            print("[INFO] SAILSAFE terminado em seguranca.", flush=True)


if __name__ == "__main__":
    main()
