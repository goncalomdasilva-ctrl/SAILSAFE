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

Regista a sessao em CSV via telemetry.SessionLogger.
Teclas (terminal): a=ARM  n=NAV  d=DISARM  s=STOP  q=sair
"""

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

    # Navegacao. Posicao e rumo vem de um barco SINTETICO (sem GPS, BNO055
    # nem motores): em NAV os comandos enviados realimentam-no, fechando a
    # malha nav -> heading hold -> mixer -> barco -> posicao.
    ctrl = HeadingController(kp=2.0, max_steer=100.0)
    boat = SimulatedBoat(MISSION_START[0], MISSION_START[1],
                         heading=0.0, yaw_gain=0.4, speed_ms=3.0)
    nav = WaypointNav(MISSION_WAYPOINTS, arrival_radius_m=ARRIVAL_RADIUS_M)

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
                        # missao recomecada do inicio, a partir da posicao atual
                        nav = WaypointNav(MISSION_WAYPOINTS,
                                          arrival_radius_m=ARRIVAL_RADIUS_M)
                        ctrl.clear_target()
                        last_hb = 0.0
                        log.log("STATE", state, f"missao {len(MISSION_WAYPOINTS)} wp")
                        print(f"[STATE] {state} (navegacao por waypoints, "
                              f"{len(MISSION_WAYPOINTS)} wp)", flush=True)
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
                    step = nav_step(nav, ctrl, boat)
                    if step.done:
                        # missao cumprida: parar e regressar ao estado seguro
                        link.stop_motors()
                        state = DISARMED
                        log.log("NAV", state, "missao concluida")
                        print("[NAV] Missao concluida -> DISARMED", flush=True)
                        print(f"[STATE] {state}", flush=True)
                    else:
                        link.send_motors(step.left, step.right)
                        log.log("TX", state, f"{step.left:.0f},{step.right:.0f}")
                        log.log("NAV", state,
                                f"wp={nav.index} dist={step.dist:.1f} "
                                f"bearing={step.bearing:.1f} heading={boat.heading:.1f} "
                                f"lat={step.lat:.6f} lon={step.lon:.6f}")
                        print(f"[NAV] wp={nav.index}  dist={step.dist:6.1f} m  "
                              f"bearing={step.bearing:5.1f}  heading={boat.heading:5.1f}  "
                              f"L={step.left:.0f} R={step.right:.0f}", flush=True)

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
