#!/usr/bin/env python3

import signal
import time

running = True


def shutdown(signum, frame):
    global running
    print(f"[INFO] Sinal {signum} recebido. A terminar em segurança.", flush=True)
    running = False


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

print("[INFO] SAILSAFE iniciado", flush=True)
print("[STATE] DISARMED", flush=True)
print("[INFO] Comunicação série desativada; nenhum comando será enviado.", flush=True)

while running:
    time.sleep(1)

print("[INFO] SAILSAFE terminado em segurança.", flush=True)
