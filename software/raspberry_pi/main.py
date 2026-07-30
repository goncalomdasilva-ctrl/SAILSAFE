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

Regista a sessao em CSV via telemetry.SessionLogger.
Teclas (terminal): a=ARM  n=NAV  d=DISARM  s=STOP  q=sair
"""

import argparse
import signal
import sys
import select
import termios
import tty
import time
from collections import namedtuple

from communication.serial_link import SerialLink
from telemetry.logger import SessionLogger
from control.heading import HeadingController
from control.mixer import mix
from control.navigation import WaypointNav
from control.sources import SimulatedBoat

HEARTBEAT_S = 0.2
RECONNECT_S = 10
SAFE_MAX = 30        # teto que o ESP32 aceita (rejeita comandos > 30%)
NAV_THROTTLE = 20    # impulso base em NAV, com margem para o steer
ARRIVAL_RADIUS_M = 4.0
DISARMED, ARMED, NAV = "DISARMED", "ARMED", "NAV"

# Missao SINTETICA de demonstracao: 40 m a Norte, depois 40 m a Este.
# Substituir por waypoints reais quando houver GPS.
MISSION_START = (38.73600, -9.14000)
MISSION_WAYPOINTS = [
    (38.736359, -9.140000),   # ~40 m a Norte  (bearing 0)
    (38.736359, -9.139539),   # ~40 m a Este   (bearing 90)
]

running = True


def shutdown(signum, frame):
    global running
    print(f"\n[INFO] Sinal {signum} recebido. A terminar em seguranca.", flush=True)
    running = False


class KeyReader:
    """Le teclas isoladas do terminal sem bloquear e sem Enter."""

    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.enabled = sys.stdin.isatty()
        self.old = None

    def __enter__(self):
        if self.enabled:
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        return self

    def __exit__(self, *a):
        if self.enabled and self.old:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)

    def get(self):
        if self.enabled and select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1).lower()
        return None


NavStep = namedtuple("NavStep", "left right bearing dist done lat lon")

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
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    log = SessionLogger()
    print("[INFO] SAILSAFE iniciado", flush=True)
    print(f"[INFO] Log da sessao: {log.path}", flush=True)
    state = DISARMED
    log.log("BOOT", state, "")
    print(f"[STATE] {state}", flush=True)
    print("[INFO] Teclas: a=ARM  n=NAV  d=DISARM  s=STOP  q=sair", flush=True)

    link = SerialLink()
    if link.connect():
        print("[INFO] Ligacao serie ao ESP32 ativa", flush=True)
        log.log("SERIAL", state, "conectado")
    else:
        print("[INFO] Sem ESP32; a continuar sem ligacao serie", flush=True)
        log.log("SERIAL", state, "ausente")

    last_hb = 0.0
    last_reconnect = time.monotonic()

    # Navegacao. Posicao e rumo vem de um barco SINTETICO (sem GPS, BNO055
    # nem motores): em NAV os comandos enviados realimentam-no, fechando a
    # malha nav -> heading hold -> mixer -> barco -> posicao.
    ctrl = HeadingController(kp=2.0, max_steer=100.0)
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

    with KeyReader() as keys:
        try:
            while running:
                now = time.monotonic()

                k = keys.get()
                if k == "q":
                    break
                elif k == "s":
                    state = DISARMED
                    link.stop_motors()
                    log.log("STOP", state, "")
                    print("[STOP] STOP -> DISARMED", flush=True)
                    print(f"[STATE] {state}", flush=True)
                elif k == "a":
                    if state == DISARMED:
                        if link.is_open:
                            state = ARMED
                            # O ESP32 arranca com a propulsao travada e volta a
                            # travar sempre que o failsafe dispara. A trava so
                            # abre com um comando de paragem, e armar e o
                            # momento certo para o mandar: e um gesto humano.
                            link.stop_motors()
                            last_hb = 0.0
                            log.log("STATE", state, "arm")
                            print(f"[STATE] {state}", flush=True)
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
                        state = NAV
                        # abre a trava do ESP32 antes do primeiro comando de
                        # propulsao (ver esp32/motor_safety.h)
                        link.stop_motors()
                        # missao recomecada do inicio, a partir da posicao atual
                        nav = WaypointNav(MISSION_WAYPOINTS,
                                          arrival_radius_m=ARRIVAL_RADIUS_M)
                        ctrl.clear_target()
                        last_hb = 0.0
                        log.log("STATE", state,
                                f"missao {len(MISSION_WAYPOINTS)} wp ({nav_mode})")
                        print(f"[STATE] {state} (navegacao por waypoints, "
                              f"{len(MISSION_WAYPOINTS)} wp, {nav_mode})", flush=True)
                elif k == "d":
                    if state != DISARMED:
                        state = DISARMED
                        link.stop_motors()
                        log.log("STATE", state, "disarm")
                        print(f"[STATE] {state}", flush=True)

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
                    step = nav_step(nav, ctrl, boat)
                    if step.done:
                        # missao cumprida: parar e regressar ao estado seguro
                        link.stop_motors()
                        state = DISARMED
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
