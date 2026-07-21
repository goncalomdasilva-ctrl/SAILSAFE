#!/usr/bin/env python3
"""SAILSAFE - processo principal do Raspberry Pi.

Maquina de estados minima: DISARMED <-> ARMED.
- Arranca sempre em DISARMED (seguro).
- DISARMED: nunca envia propulsao; motores parados pelo failsafe do ESP32.
- ARMED: envia heartbeat a 5 Hz (0/0 por agora) para manter o failsafe
  do ESP32 satisfeito, sem mover os motores.
- STOP tem prioridade absoluta e forca DISARMED.
- O regresso da ligacao serie nunca arma sozinho: exige 'a' explicito.

Teclas (terminal): a=ARM  d=DISARM  s=STOP  q=sair
"""

import signal
import sys
import select
import termios
import tty
import time

from communication.serial_link import SerialLink

HEARTBEAT_S = 0.2
RECONNECT_S = 10
DISARMED, ARMED = "DISARMED", "ARMED"

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

    print("[INFO] SAILSAFE iniciado", flush=True)
    state = DISARMED
    print(f"[STATE] {state}", flush=True)
    print("[INFO] Teclas: a=ARM  d=DISARM  s=STOP  q=sair", flush=True)

    link = SerialLink()
    if link.connect():
        print("[INFO] Ligacao serie ao ESP32 ativa", flush=True)
    else:
        print("[INFO] Sem ESP32; a continuar sem ligacao serie", flush=True)

    last_hb = 0.0
    last_reconnect = time.monotonic()

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
                    print("[STOP] STOP -> DISARMED", flush=True)
                    print(f"[STATE] {state}", flush=True)
                elif k == "a":
                    if state == DISARMED:
                        if link.is_open:
                            state = ARMED
                            last_hb = 0.0
                            print(f"[STATE] {state}", flush=True)
                        else:
                            print("[WARN] Nao e possivel ARM sem ligacao serie", flush=True)
                elif k == "d":
                    if state != DISARMED:
                        state = DISARMED
                        link.stop_motors()
                        print(f"[STATE] {state}", flush=True)

                if not link.is_open and now - last_reconnect >= RECONNECT_S:
                    last_reconnect = now
                    if link.connect():
                        print("[INFO] ESP32 ligado (continua DISARMED)", flush=True)

                if state == ARMED and not link.is_open:
                    state = DISARMED
                    print("[WARN] Ligacao serie perdida -> DISARMED", flush=True)
                    print(f"[STATE] {state}", flush=True)

                if state == ARMED and now - last_hb >= HEARTBEAT_S:
                    last_hb = now
                    link.send_motors(0, 0)

                if link.is_open:
                    line = link.read_line()
                    if line:
                        print(f"[RX] {line}", flush=True)

                time.sleep(0.02)
        finally:
            link.close()
            print("[INFO] SAILSAFE terminado em seguranca.", flush=True)


if __name__ == "__main__":
    main()
