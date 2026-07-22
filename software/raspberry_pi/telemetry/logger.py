"""Logging de sessao em CSV para o SAILSAFE.

Cria um ficheiro por sessao em logs/, com uma linha por evento.
Escrita imediata (flush) para sobreviver a falhas ou cortes de energia.
Colunas: timestamp, event, state, detail

Eventos previstos: BOOT, STATE, TX, RX, SERIAL, STOP, SHUTDOWN.
Colunas para heading/GPS/waypoints serao acrescentadas quando existirem.
"""

import csv
import os
from datetime import datetime

DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)
FIELDS = ["timestamp", "event", "state", "detail"]


class SessionLogger:
    def __init__(self, log_dir=DEFAULT_DIR):
        os.makedirs(log_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(log_dir, f"session_{stamp}.csv")
        self._f = open(self.path, "a", newline="", encoding="utf-8")
        self._w = csv.writer(self._f)
        self._w.writerow(FIELDS)
        self._f.flush()

    def log(self, event, state="", detail=""):
        ts = datetime.now().isoformat(timespec="milliseconds")
        self._w.writerow([ts, event, state, detail])
        self._f.flush()

    def close(self):
        try:
            self._f.close()
        except OSError:
            pass


if __name__ == "__main__":
    log = SessionLogger()
    log.log("BOOT", "DISARMED", "auto-teste")
    log.log("STATE", "ARMED", "")
    log.log("TX", "ARMED", "0,0")
    log.log("RX", "ARMED", "Left: 0% -> 1000 us")
    log.close()
    print(f"[INFO] Log de teste escrito em: {log.path}")
    with open(log.path, encoding="utf-8") as f:
        print(f.read())
