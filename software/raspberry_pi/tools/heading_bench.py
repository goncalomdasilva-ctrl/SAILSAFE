#!/usr/bin/env python3
"""Ensaio de bancada do heading hold: rodar o sensor a mao.

NAO liga a serie, NAO fala com o ESP32, NAO mexe em motores. De proposito.
Este script existe para validar a unica coisa que ainda nao esta validada
-- a leitura real do BNO055 e a reacao do controlador a ela -- sem
arrastar navegacao, posicao nem propulsao para o meio.

O que faz: le o rumo, mostra a calibracao, calcula o erro para o alvo e
mostra o steer e os comandos L/R que o mixer daria. Os L/R sao impressos,
nunca enviados.

Uso:
    cd software/raspberry_pi
    python3 -m tools.heading_bench                 # BNO055 real
    python3 -m tools.heading_bench --fake          # sem hardware, so ver o ecra
    python3 -m tools.heading_bench --alvo 90 --declinacao -2.1 --offset 0

Procedimento de calibracao do BNO055 (modo NDOF):
  gyro  -> pousar parado alguns segundos
  accel -> inclinar em 6 posicoes, parando em cada uma
  mag   -> movimento em oito, amplo e lento
  sys   -> sobe sozinho quando os outros tres chegam a 3

IMPORTANTE: calibrar com o sensor no sitio definitivo e com as baterias e
motores montados. O ferro e as correntes do barco distorcem o campo, e uma
calibracao feita com a placa na mao nao vale para o barco montado.
"""

import argparse
import math
import sys
import time

from control.heading import HeadingController, heading_error
from control.mixer import mix
from control.real_heading import HeadingUnavailable, RealHeading

THROTTLE_MOSTRADO = 20      # so para ilustrar o mixer; nao e enviado
CAP = 30                    # o mesmo teto que o ESP32 impoe


class FakeBNO055:
    """Sensor falso que roda devagar. Para ver o ecra sem hardware.

    Sobe a calibracao ao fim de 3 s, para exercitar tambem o caminho de
    "ainda nao esta calibrado".
    """

    def __init__(self):
        self.t0 = time.monotonic()

    @property
    def _dt(self):
        return time.monotonic() - self.t0

    @property
    def calibration_status(self):
        c = 3 if self._dt > 3.0 else 0
        return (c, 3, 3, c)

    @property
    def euler(self):
        if self._dt < 1.0:
            return None                      # fusao ainda sem solucao
        return (30.0 * math.sin(self._dt / 4.0), 0.0, 0.0)


def barra(valor, largura=24):
    """Barra de texto para ver o steer de relance, sem ler numeros."""
    meio = largura // 2
    pos = int(round(meio + (valor / 100.0) * meio))
    pos = max(0, min(largura - 1, pos))
    linha = ["-"] * largura
    linha[meio] = "|"
    linha[pos] = "#"
    return "".join(linha)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--alvo", type=float, default=0.0, help="rumo alvo em graus")
    p.add_argument("--kp", type=float, default=2.0, help="ganho proporcional")
    p.add_argument("--offset", type=float, default=0.0,
                   help="offset de montagem da placa, em graus")
    p.add_argument("--declinacao", type=float, default=0.0,
                   help="declinacao magnetica local, em graus (Este positivo)")
    p.add_argument("--hz", type=float, default=5.0, help="taxa de leitura")
    p.add_argument("--fake", action="store_true",
                   help="usar um sensor falso, sem hardware")
    args = p.parse_args()

    if args.fake:
        print("[BANCADA] Sensor FALSO. Nada disto sao medicoes reais.")
        heading_src = RealHeading(FakeBNO055(), mount_offset_deg=args.offset,
                                  declination_deg=args.declinacao)
    else:
        try:
            from control.real_heading import create_bno055
            heading_src = create_bno055(mount_offset_deg=args.offset,
                                        declination_deg=args.declinacao)
        except ImportError as e:
            print(f"[ERRO] Falta a biblioteca do BNO055: {e}")
            print("       pip install adafruit-circuitpython-bno055")
            print("       ou correr com --fake para so ver o ecra.")
            return 1
        except (OSError, ValueError) as e:
            print(f"[ERRO] BNO055 nao responde no I2C: {e}")
            print("       Verificar ligacoes e `i2cdetect -y 1` (deve dar 0x28).")
            return 1

    if args.declinacao == 0.0 and not args.fake:
        print("[AVISO] Declinacao a 0: o rumo mostrado e MAGNETICO, nao "
              "verdadeiro. Passar --declinacao antes de comparar com "
              "bearings de navegacao.")

    ctrl = HeadingController(kp=args.kp, max_steer=100.0)
    ctrl.set_target(args.alvo)
    periodo = 1.0 / args.hz

    print(f"[BANCADA] alvo={args.alvo:.1f} deg  kp={args.kp}  "
          f"offset={args.offset:.1f}  declinacao={args.declinacao:.1f}")
    print("[BANCADA] Sem serie e sem motores. Rodar o sensor a mao. Ctrl-C para sair.")
    print()

    try:
        while True:
            cal = heading_src.calibration()
            try:
                heading = heading_src.read()
            except HeadingUnavailable as e:
                print(f"  cal={cal.sys}{cal.gyro}{cal.accel}{cal.mag}  "
                      f"SEM RUMO -> em NAV isto seria DISARM  ({e})",
                      flush=True)
                time.sleep(periodo)
                continue

            err = heading_error(args.alvo, heading)
            steer = ctrl.update(heading)
            left, right = mix(THROTTLE_MOSTRADO, steer, 0, CAP)
            bussola = heading % 360.0

            print(f"  cal={cal.sys}{cal.gyro}{cal.accel}{cal.mag}  "
                  f"rumo={bussola:6.1f}  erro={err:+7.1f}  "
                  f"steer={steer:+6.1f} [{barra(steer)}]  "
                  f"L={left:4.1f} R={right:4.1f} (nao enviado)", flush=True)
            time.sleep(periodo)
    except KeyboardInterrupt:
        print("\n[BANCADA] Terminado. Nada foi enviado ao ESP32.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
