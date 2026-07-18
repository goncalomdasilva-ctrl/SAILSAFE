import time
import serial

PORTA = "/dev/ttyUSB0"
BAUD = 115200
PERIODO_S = 0.2   # 200 ms

def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, int(round(x))))

def format_cmd(left, right):
    left = clamp(left)
    right = clamp(right)
    return f"L: {left} R: {right}\n"

def main():
    ser = serial.Serial(PORTA, BAUD, timeout=0)
    time.sleep(2)

    left = 10
    right = 10

    print("[INFO] Porta aberta")
    print("[INFO] Ctrl+C para sair")

    try:
        while True:
            cmd = format_cmd(left, right)

            ser.write(cmd.encode("utf-8"))

            if ser.in_waiting:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    print("[RX]", line)

            print("[TX]", cmd.strip())

            time.sleep(PERIODO_S)

    except KeyboardInterrupt:
        stop_cmd = format_cmd(0, 0)
        ser.write(stop_cmd.encode("utf-8"))
        print("\n[INFO] STOP enviado")

    finally:
        ser.close()
        print("[INFO] Porta fechada")


if __name__ == "__main__":
    main()
