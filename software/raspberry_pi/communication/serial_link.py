"""Ligacao serie ao ESP32.

Modulo reutilizavel: nao faz nada ao ser importado e nunca envia
comandos por iniciativa propria. Quem decide o que enviar e o main.py.
Protocolo: "L: <0-100> R: <0-100>\n"
"""

import time
import serial

DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_BAUD = 115200


def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, int(round(x))))


def format_cmd(left, right):
    return f"L: {clamp(left)} R: {clamp(right)}\n"


class SerialLink:
    def __init__(self, port=DEFAULT_PORT, baud=DEFAULT_BAUD):
        self.port = port
        self.baud = baud
        self.ser = None

    @property
    def is_open(self):
        return self.ser is not None and self.ser.is_open

    def connect(self):
        """Tenta abrir a porta. Devolve True/False; nunca lanca excecao."""
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0)
            time.sleep(2)  # o ESP32 reinicia quando a porta abre
            return True
        except (serial.SerialException, OSError) as e:
            print(f"[WARN] ESP32 nao disponivel em {self.port}: {e}")
            self.ser = None
            return False

    def send_motors(self, left, right):
        """Envia comando aos motores. True apenas se foi mesmo enviado."""
        if not self.is_open:
            return False
        try:
            self.ser.write(format_cmd(left, right).encode("utf-8"))
            return True
        except (serial.SerialException, OSError) as e:
            print(f"[WARN] Falha de escrita: {e}")
            self.close()
            return False

    def stop_motors(self):
        return self.send_motors(0, 0)

    def read_line(self):
        """Devolve uma linha recebida do ESP32, ou None."""
        if not self.is_open:
            return None
        try:
            if self.ser.in_waiting:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                return line or None
        except (serial.SerialException, OSError):
            self.close()
        return None

    def close(self):
        """Envia STOP (se possivel) e fecha a porta."""
        if self.is_open:
            try:
                self.ser.write(format_cmd(0, 0).encode("utf-8"))
            except (serial.SerialException, OSError):
                pass
        if self.ser is not None:
            try:
                self.ser.close()
            except (serial.SerialException, OSError):
                pass
            self.ser = None


if __name__ == "__main__":
    # Auto-teste inofensivo: tenta ligar, reporta, fecha. Nao move motores.
    link = SerialLink()
    if link.connect():
        print("[INFO] Porta aberta com sucesso")
        link.close()
        print("[INFO] Porta fechada")
    else:
        print("[INFO] Sem ligacao — comportamento esperado se o ESP32 estiver desligado")
