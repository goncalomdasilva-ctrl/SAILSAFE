#!/usr/bin/env python3
"""SAILSAFE - processo principal do Raspberry Pi.

Maquina de estados: DISARMED <-> ARMED / NAV.
- Arranca sempre em DISARMED (seguro).
- DISARMED: nunca envia propulsao; motores parados pelo failsafe do ESP32.
- ARMED: envia heartbeat a 5 Hz (0/0) para manter o failsafe satisfeito.
- NAV: heading hold. Le o rumo (fonte SINTETICA, sem BNO055 nem motores),
  calcula o steer, mistura com o throttle e envia comandos L/R (<=30%) ao
  ESP32, fechando a malha pelo simulador. Trocar a fonte pelo BNO055 real
  nao altera a logica de controlo.
- STOP tem prioridade absoluta e forca DISARMED.
- O regresso da ligacao serie nunca arma sozinho.

Regista a sessao em CSV via telemetry.SessionLogger.
Teclas (terminal): a=ARM  n=NAV  d=DISARM  s=STOP  q=sair
"""

import signal
import sys
import select
import termios
import tty
import time

from communication.serial_link import SerialLink
from telemetry.logger import SessionLogger
from control.heading import HeadingController
from control.mixer import mix
from control.sources import SimulatedHeading

HEARTBEAT_S = 0.2
RECONNECT_S = 10
SAFE_MAX = 30        # teto que o ESP32 aceita (rejeita comandos > 30%)
NAV_THROTTLE = 20    # impulso base em NAV, com margem para o steer
NAV_TARGET = 90.0    # rumo alvo a manter, em graus
DISARMED, ARMED, NAV = "DISARMED", "ARMED", "NAV"

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


def main():
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

    # Controlo de rumo. Fonte de heading SINTETICA (sem BNO055 nem motores):
    # em NAV os comandos enviados realimentam o simulador para fechar a malha.
    ctrl = HeadingController(kp=2.0, max_steer=100.0)
    sim_heading = SimulatedHeading(heading=0.0, yaw_gain=0.5)

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
                            last_hb = 0.0
                            log.log("STATE", state, "arm")
                            print(f"[STATE] {state}", flush=True)
                        else:
                            print("[WARN] Nao e possivel ARM sem ligacao serie", flush=True)
                            log.log("WARN", state, "arm sem serie")
                elif k == "n":
                    if state == DISARMED and link.is_open:
                        state = NAV
                        ctrl.set_target(NAV_TARGET)
                        last_hb = 0.0
                        log.log("STATE", state, f"alvo={NAV_TARGET:.0f}")
                        print(f"[STATE] {state} (heading hold, alvo {NAV_TARGET:.0f} deg)", flush=True)
                    elif not link.is_open:
                        print("[WARN] Nao e possivel NAV sem ligacao serie", flush=True)
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

                if state in (ARMED, NAV) and not link.is_open:
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
                    heading = sim_heading.read()
                    steer = ctrl.update(heading)
                    left, right = mix(NAV_THROTTLE, steer, 0, SAFE_MAX)
                    link.send_motors(left, right)
                    # fecha a malha: os comandos rodam o barco simulado (sintetico)
                    sim_heading.update(left, right, dt=HEARTBEAT_S)
                    log.log("TX", state, f"{left:.0f},{right:.0f}")
                    log.log("HEADING", state, f"{heading:.1f}")
                    print(f"[NAV] heading={heading:5.1f}  L={left:.0f} R={right:.0f}", flush=True)

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
