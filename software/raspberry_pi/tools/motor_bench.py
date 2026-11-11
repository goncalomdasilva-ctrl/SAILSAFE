#!/usr/bin/env python3
"""Ensaio de bancada dos ESCs e motores: impulsos LONGOS, com heartbeat.

Porque existe: a mao, pelo Serial Monitor, um comando da no maximo 1 s de
rotacao -- o failsafe do ESP32 trava a propulsao ao fim desse tempo, e ainda
bem. Chega para ver o sentido de rotacao; nao chega para ler um wattmeter
nem para puxar uma balanca de mola. Para isso e preciso repetir o comando a
5 Hz durante o tempo do impulso, que e o que este script faz, e mais nada.

O QUE FAZ, POR ORDEM
  1. abre a trava com um STOP confirmado -- sem ack, nao sai propulsao
  2. sobe em rampa ate a percentagem pedida e mantem-na, um comando a cada
     200 ms (o mesmo heartbeat do main.py)
  3. para com STOP confirmado, aconteca o que acontecer pelo meio: fim do
     tempo, Ctrl-C, recusa do ESP32, excecao
  4. regista TX e RX no CSV da sessao, ao milissegundo, para a corrente lida
     no wattmeter se poder alinhar com o que foi mandado

O QUE NAO FAZ
  - nao passa do teto: acima de 30 % recusa antes de falar com o ESP32 (e o
    firmware recusaria na mesma -- sao duas guardas, nao uma)
  - nao mede corrente nenhuma. Os divisores e o sensor de corrente nao estao
    montados; a leitura e do wattmeter, e o script so a aceita no fim para
    ficar no log ao lado do impulso que a produziu
  - nao decide se o jato esta dentro de agua. Isso declara-se: --seco ou
    --submerso, sempre um dos dois

--seco      jato fora de agua: no maximo 10 % e 1 s. O motor e o jato sao
            uma so peca e o arrefecimento e pela agua que o jato bombeia.
--submerso  jato num alguidar, admissao coberta: ate 30 % e 30 s.

Correr com:
    python3 -m tools.motor_bench --fake --submerso --lado e --pct 10 --dur 3
    python3 -m tools.motor_bench --seco --lado e --pct 10 --dur 1
    python3 -m tools.motor_bench --submerso --lado ambos --pct 20 --dur 10 \\
        --esp32-port /dev/serial/by-id/...

ANTES DE CORRER COM HARDWARE (procedimento de 2026-09-25 e de 2026-11-11):
ESP32 ligado e a dar 1000 us ANTES de a loop key entrar; polaridade medida
ao multimetro; fusivel em serie; so sinal e massa do ESC, fio vermelho do
BEC desligado; motor preso. E OPEN-019 fechado primeiro: enquanto o ESP32
nao tiver watchdog, um loop() encravado deixa o ultimo PWM a sair e nada
neste script o consegue parar -- so a loop key.

ESTADO: testado contra um ESP32 falso (tests/test_motor_bench.py). NUNCA
correu contra a placa nem contra um ESC.
"""

import argparse
import os
import re
import signal
import sys
import time
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from communication.serial_link import SerialLink  # noqa: E402

HEARTBEAT_S = 0.2        # o mesmo do main.py
SAFE_MAX = 30            # PERCENT_MAX_SAFE do esp32/motor_safety.h
DRY_MAX_PCT = 10         # a seco: so para ver o sentido de rotacao
DRY_MAX_S = 1.0
MAX_DUR_S = 30.0
RAMP_S = 1.0

# Tres heartbeats sem um "Left: ... us" de volta e o ESP32 nao esta a
# obedecer (ou nao esta la). Fica abaixo do timeout do failsafe (1 s): o
# script desiste antes de o firmware ter de travar.
ACK_TIMEOUT_S = 3 * HEARTBEAT_S

PWM_STOP = 1000
_ACK_PWM = re.compile(r"Left:\s*(\d+)\s*us\s*\|\s*Right:\s*(\d+)\s*us")

Plano = namedtuple("Plano", "lado pct dur rampa seco")


def validar(lado, pct, dur, rampa=RAMP_S, seco=False):
    """Devolve um Plano ou levanta ValueError com o motivo.

    Tudo o que e recusavel sem hardware recusa-se aqui, antes de a porta
    abrir: um impulso mal pedido nao deve chegar a destravar a propulsao.
    """
    if lado not in ("e", "d", "ambos"):
        raise ValueError("lado tem de ser 'e', 'd' ou 'ambos'")
    if int(pct) != pct:
        raise ValueError("pct tem de ser inteiro: o protocolo so leva inteiros")
    pct = int(pct)
    if not 1 <= pct <= SAFE_MAX:
        raise ValueError(f"pct tem de estar entre 1 e {SAFE_MAX} "
                         f"(teto do firmware)")
    if not 0 < dur <= MAX_DUR_S:
        raise ValueError(f"dur tem de estar em ]0, {MAX_DUR_S:.0f}] s")
    if rampa < 0:
        raise ValueError("rampa nao pode ser negativa")
    if seco:
        if pct > DRY_MAX_PCT:
            raise ValueError(f"a seco o maximo e {DRY_MAX_PCT} % "
                             f"(pedido {pct} %)")
        if dur > DRY_MAX_S:
            raise ValueError(f"a seco o maximo e {DRY_MAX_S:.0f} s "
                             f"(pedido {dur:g} s): o jato arrefece pela agua")
    return Plano(lado, pct, float(dur), min(float(rampa), float(dur)), bool(seco))


def perfil(plano, t):
    """Percentagem a mandar ao instante t (s) desde o inicio do impulso.

    Rampa linear de 1 % ate ao alvo, depois patamar. Nunca devolve 0: zero
    e o comando de paragem, e esse so sai pelo stop_motors().
    """
    if plano.rampa <= 0 or t >= plano.rampa:
        return plano.pct
    return max(1, min(plano.pct, int(round(plano.pct * t / plano.rampa))))


def comando(plano, pct):
    """(left, right) para a percentagem dada, conforme o lado do plano."""
    return (pct if plano.lado in ("e", "ambos") else 0,
            pct if plano.lado in ("d", "ambos") else 0)


def recusa(linha):
    """True se a linha do ESP32 disser que NAO esta a obedecer.

    Cuidado com a armadilha: o ack bom e "Propulsao DESTRAVADA", que contem
    "TRAVADA". Procurar "TRAVADA" sem mais transformava o ack do STOP numa
    recusa -- por isso DESTRAVADA sai primeiro.
    """
    up = linha.upper()
    if "DESTRAVADA" in up:
        return False
    return any(k in up for k in ("TRAVADA", "FAILSAFE", "INVALIDO",
                                 "FORA DO LIMITE"))


class Resultado:
    """O que aconteceu no impulso. Verdadeiro so se correu ate ao fim E parou."""

    def __init__(self):
        self.motivo = ""             # vazio = chegou ao fim do tempo
        self.destravou = False
        self.enviados = 0            # comandos de propulsao enviados
        self.acks = 0                # "Left: ... us" recebidos
        self.pwm_max = (PWM_STOP, PWM_STOP)
        self.duracao = 0.0
        self.stop = None             # StopResult da paragem final
        self.linhas = []

    @property
    def ok(self):
        return (self.destravou and not self.motivo and self.acks > 0
                and bool(self.stop))

    def __bool__(self):
        return self.ok


def correr(link, plano, log=None, clock=time.monotonic, sleep=time.sleep,
           parar=lambda: False, out=print):
    """Executa um impulso. Devolve Resultado. Nao levanta: para sempre.

    `parar` e consultado a cada volta; devolver True termina o impulso.
    `clock` e `sleep` entram por parametro pelo mesmo motivo que no
    stop_motors(): os testes correm o tempo sem esperar por ele.
    """
    res = Resultado()

    def reg(evento, detalhe):
        if log is not None:
            log.log(evento, "BENCH", detalhe)

    def rx(linhas):
        for linha in linhas:
            res.linhas.append(linha)
            reg("RX", linha)

    if not link.is_open:
        res.motivo = "sem ligacao serie"
        return res

    # 1. Abrir a trava. Sem confirmacao nao sai propulsao -- a mesma regra
    #    do ARM no main.py.
    r = link.stop_motors(clock=clock, sleep=sleep)
    rx(r.lines)
    if not r:
        res.motivo = f"trava nao confirmou abertura ({r.reason})"
        reg("ALERTA", res.motivo)
        return res
    res.destravou = True
    reg("PULSO", f"inicio lado={plano.lado} pct={plano.pct} "
                 f"dur={plano.dur:g} rampa={plano.rampa:g} "
                 f"{'seco' if plano.seco else 'submerso'}")

    teto_pwm = PWM_STOP + plano.pct * 10
    t0 = clock()
    ultimo_hb = None
    ultimo_ack = None
    try:
        while True:
            agora = clock()
            t = agora - t0
            if t >= plano.dur:
                break
            if parar():
                res.motivo = "interrompido pelo operador"
                break

            if ultimo_hb is None or agora - ultimo_hb >= HEARTBEAT_S:
                ultimo_hb = agora
                left, right = comando(plano, perfil(plano, t))
                if not link.send_motors(left, right):
                    res.motivo = "escrita falhou; porta fechada"
                    break
                res.enviados += 1
                if ultimo_ack is None:
                    ultimo_ack = agora      # o prazo conta do primeiro envio
                reg("TX", f"{left},{right}")

            abortar = False
            while True:
                linha = link.read_line()
                if linha is None:
                    break
                rx([linha])
                if recusa(linha):
                    res.motivo = f"ESP32 recusou: {linha}"
                    abortar = True
                    break
                m = _ACK_PWM.search(linha)
                if m:
                    pl, pr = int(m.group(1)), int(m.group(2))
                    res.acks += 1
                    ultimo_ack = agora
                    res.pwm_max = (max(res.pwm_max[0], pl),
                                   max(res.pwm_max[1], pr))
                    esperado_l, esperado_r = comando(plano, plano.pct)
                    if (pl > teto_pwm or pr > teto_pwm
                            or (esperado_l == 0 and pl != PWM_STOP)
                            or (esperado_r == 0 and pr != PWM_STOP)):
                        res.motivo = (f"PWM aplicado fora do pedido: {linha} "
                                      f"(teto {teto_pwm} us)")
                        abortar = True
                        break
            if abortar:
                break
            if not link.is_open:
                res.motivo = "porta fechou durante o impulso"
                break
            if ultimo_ack is not None and agora - ultimo_ack > ACK_TIMEOUT_S:
                res.motivo = (f"ESP32 sem responder aos comandos ha "
                              f"{agora - ultimo_ack:.1f} s")
                break
            sleep(0.01)
    except KeyboardInterrupt:
        res.motivo = "interrompido (Ctrl-C)"
    except Exception as e:                                      # noqa: BLE001
        res.motivo = f"excecao: {type(e).__name__}: {e}"
    finally:
        # 3. Parar. Sempre, e com confirmacao.
        res.duracao = clock() - t0
        res.stop = link.stop_motors(clock=clock, sleep=sleep)
        rx(res.stop.lines)
        if res.motivo:
            reg("ALERTA", f"impulso abortado: {res.motivo}")
        if res.stop:
            reg("STOP", f"confirmado ({res.stop.attempts} tent.)")
        else:
            reg("ALERTA", f"STOP NAO confirmado - {res.stop.reason}")
            out(f"[ALERTA] STOP nao confirmado ({res.stop.reason}). O failsafe "
                f"trava em ~1 s. TIRAR A LOOP KEY se houver duvida.")
        reg("PULSO", f"fim dur={res.duracao:.2f} enviados={res.enviados} "
                     f"acks={res.acks} pwm_max={res.pwm_max[0]},{res.pwm_max[1]}")
    return res


# --- ESP32 falso ----------------------------------------------------------
# Espelho em Python do esp32/motor_safety.h, com as respostas do esp32.ino.
# Serve o --fake e os testes. A VERDADE E O .h: se os dois discordarem, este
# e que esta errado. Existe para o script poder ser ensaiado sem placa, nao
# para provar nada sobre o firmware.

class FakeEsp32:
    TIMEOUT_S = 1.0

    def __init__(self, clock=time.monotonic, mudo=False, encrava_apos=None):
        self.is_open = True
        self.clock = clock
        self.mudo = mudo                    # recebe e nao responde
        self.encrava_apos = encrava_apos    # deixa de responder apos N comandos
        self.locked = True
        self.failsafe = True
        self.left = self.right = PWM_STOP
        self.ultimo = clock() - self.TIMEOUT_S - 1
        self.recebidos = []
        self.rx = b""
        self._buf = b""
        self._avisou_trava = False

    def _diz(self, texto):
        if not self.mudo:
            self.rx += (texto + "\n").encode()

    def _tick(self):
        if self.clock() - self.ultimo > self.TIMEOUT_S:
            primeira = not self.failsafe
            self.failsafe = self.locked = True
            self.left = self.right = PWM_STOP
            if primeira:
                self._diz("FAILSAFE ATIVO - motores parados e propulsao TRAVADA")
                self._avisou_trava = False

    def write(self, data):
        self._tick()
        self._buf += data
        while b"\n" in self._buf:
            linha, self._buf = self._buf.split(b"\n", 1)
            self._comando(linha.decode("utf-8", errors="ignore"))
        return len(data)

    def _comando(self, linha):
        self.recebidos.append(linha)
        if self.encrava_apos is not None and len(self.recebidos) > self.encrava_apos:
            return
        m = re.match(r"\s*L:\s*(-?\d+)\s*R:\s*(-?\d+)\s*$", linha)
        if not m:
            self.left = self.right = PWM_STOP
            return self._diz("COMANDO INVALIDO - motores parados")
        lv, rv = int(m.group(1)), int(m.group(2))
        if not (0 <= lv <= SAFE_MAX and 0 <= rv <= SAFE_MAX):
            self.left = self.right = PWM_STOP
            return self._diz("VALOR FORA DO LIMITE SEGURO - motores parados")
        if lv == 0 and rv == 0:
            self.left = self.right = PWM_STOP
            self.locked = self.failsafe = False
            self.ultimo = self.clock()
            self._avisou_trava = False
            return self._diz("Parado. Propulsao DESTRAVADA")
        if self.locked:
            self.left = self.right = PWM_STOP
            if not self._avisou_trava:
                self._avisou_trava = True
                self._diz("PROPULSAO TRAVADA - ignorado. Enviar 'L: 0 R: 0' "
                          "para destravar")
            return None
        self.left, self.right = PWM_STOP + lv * 10, PWM_STOP + rv * 10
        self.failsafe = False
        self.ultimo = self.clock()
        return self._diz(f"Left: {self.left} us | Right: {self.right} us")

    @property
    def in_waiting(self):
        self._tick()
        return len(self.rx)

    def read(self, n):
        out, self.rx = self.rx[:n], self.rx[n:]
        return out

    def reset_input_buffer(self):
        self.rx = b""

    def close(self):
        self.is_open = False


def link_falso(**kw):
    link = SerialLink()
    link.ser = FakeEsp32(**kw)
    return link


# --- linha de comandos ----------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Impulso longo de bancada para ESCs/motores, com heartbeat.")
    p.add_argument("--lado", choices=("e", "d", "ambos"), required=True,
                   help="motor a acionar: e(squerdo), d(ireito) ou ambos")
    p.add_argument("--pct", type=int, required=True,
                   help=f"percentagem (1..{SAFE_MAX}; a seco ate {DRY_MAX_PCT})")
    p.add_argument("--dur", type=float, required=True,
                   help=f"duracao em s (ate {MAX_DUR_S:.0f}; a seco ate "
                        f"{DRY_MAX_S:.0f})")
    p.add_argument("--rampa", type=float, default=RAMP_S,
                   help=f"subida linear ate ao alvo, em s (por omissao {RAMP_S})")
    agua = p.add_mutually_exclusive_group(required=True)
    agua.add_argument("--seco", action="store_true",
                      help="jato FORA de agua: limita a 10 %% e 1 s")
    agua.add_argument("--submerso", action="store_true",
                      help="jato dentro de agua, admissao coberta")
    p.add_argument("--esp32-port", default=None, dest="esp32_port",
                   help="porta serie do ESP32 (por omissao a do SerialLink)")
    p.add_argument("--fake", action="store_true",
                   help="ESP32 falso em memoria: ensaia o script sem placa")
    p.add_argument("--sem-confirmar", action="store_true", dest="sem_confirmar",
                   help="nao pede o 'sim' antes do impulso (so com --fake ou "
                        "quando o procedimento ja foi feito)")
    p.add_argument("--sem-log", action="store_true", dest="sem_log",
                   help="nao escreve CSV de sessao")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        plano = validar(args.lado, args.pct, args.dur, args.rampa, args.seco)
    except ValueError as e:
        print(f"[RECUSADO] {e}")
        return 2

    onde = "A SECO" if plano.seco else "SUBMERSO"
    print(f"[bench] impulso: lado={plano.lado}  {plano.pct} %  {plano.dur:g} s  "
          f"rampa {plano.rampa:g} s  jato {onde}")

    if args.fake:
        link = link_falso()
        print("[bench] ESP32 FALSO: nenhum motor vai girar.")
    else:
        link = SerialLink(args.esp32_port) if args.esp32_port else SerialLink()
        if not link.connect():
            print("[RECUSADO] sem ligacao serie ao ESP32.")
            return 2
        if not args.sem_confirmar:
            if not sys.stdin.isatty():
                print("[RECUSADO] sem terminal para confirmar. Usar "
                      "--sem-confirmar de proposito, ou correr num terminal.")
                link.close()
                return 2
            print("  Motor preso? Polaridade medida? Fusivel em serie? "
                  "ESP32 a 1000 us antes da loop key?")
            print(f"  Jato {onde}. Mao na loop key.")
            if input("  Escrever 'sim' para dar o impulso: ").strip().lower() != "sim":
                print("[bench] cancelado. Nada foi enviado.")
                link.close()
                return 1

    log = None
    if not args.sem_log:
        from telemetry.logger import SessionLogger
        log = SessionLogger()
        print(f"[bench] log: {log.path}")

    # SIGTERM e SIGUSR1 param o impulso pelo mesmo caminho do fim de tempo.
    pedido = {"parar": False}

    def _parar(signum, frame):
        pedido["parar"] = True

    for s in (signal.SIGTERM, getattr(signal, "SIGUSR1", None)):
        if s is not None:
            try:
                signal.signal(s, _parar)
            except (ValueError, OSError):
                pass

    try:
        res = correr(link, plano, log=log, parar=lambda: pedido["parar"])
    finally:
        link.close()

    print(f"[bench] durou {res.duracao:.2f} s | comandos {res.enviados} | "
          f"respostas {res.acks} | PWM max E={res.pwm_max[0]} "
          f"D={res.pwm_max[1]} us")
    if res.motivo:
        print(f"[ALERTA] impulso abortado: {res.motivo}")
    print(f"[bench] STOP final: "
          f"{'confirmado' if res.stop else 'NAO CONFIRMADO'}")

    if log is not None:
        if res.ok and not args.fake and sys.stdin.isatty():
            lido = input("  Corrente lida no wattmeter, em A "
                         "(Enter para saltar): ").strip().replace(",", ".")
            if lido:
                try:
                    log.log("MEDIDA", "BENCH",
                            f"corrente_A={float(lido):.2f} lado={plano.lado} "
                            f"pct={plano.pct} (wattmeter, lida pelo operador)")
                except ValueError:
                    print("  nao e um numero; nao ficou registado.")
        log.close()
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
