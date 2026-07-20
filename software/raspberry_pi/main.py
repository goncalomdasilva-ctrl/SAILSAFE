#!/usr/bin/env python3
"""SAILSAFE - processo principal do Raspberry Pi.

Estado atual: DISARMED. Nunca envia comandos de propulsao;
apenas abre a ligacao serie (se o ESP32 existir), escuta
telemetria e fecha em seguranca ao receber SIGINT/SIGTERM.
"""

import signal
import time

from communication.serial_link import SerialLink

RECONNECT_S = 10  # tentar religar ao ESP32 a cada 10 s

running = True


def shutdown(signum, frame):
    global running
    print(f"[INFO] Sinal {signum} recebido. A terminar em seguranca.", flush=True)
    running = False


def main():
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("[INFO] SAILSAFE iniciado", flush=True)
    print("[STATE] DISARMED", flush=True)

    link = SerialLink()
    if link.connect():
        print("[INFO] Ligacao serie ao ESP32 ativa", flush=True)
    else:
        print("[INFO] Sem ESP32; a continuar sem ligacao serie", flush=True)

    last_attempt = time.monotonic()
    try:
        while running:
            if link.is_open:
                line = link.read_line()
                if line:
                    print(f"[RX] {line}", flush=True)
            elif time.monotonic() - last_attempt >= RECONNECT_S:
                last_attempt = time.monotonic()
                if link.connect():
                    print("[INFO] ESP32 ligado", flush=True)
            time.sleep(0.1)
    finally:
        link.close()  # envia STOP se a porta estiver aberta
        print("[INFO] SAILSAFE terminado em seguranca.", flush=True)


if __name__ == "__main__":
    main()
