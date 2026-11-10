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
    python3 -m tools.heading_bench --guardar-cal    # grava ao chegar a 3333
    python3 -m tools.heading_bench --carregar-cal   # parte da gravada

Calibracao gravada: o BNO055 perde-a sempre que perde alimentacao.
--guardar-cal grava os offsets em config/bno055_calibration.json na
primeira vez que os quatro contadores chegam a 3; --carregar-cal escreve-os
no sensor ao arrancar. Na bancada o sensor passou a 3333 em ~1 s depois de
carregar, sem movimento (contra ~80 s de calibracao completa). Por isso
mesmo, o sensor nao distingue offsets certos de errados: offsets gravados
com a placa na mao NAO valem para o barco montado, e carrega-los la daria
um rumo plausivel e errado com os contadores todos a 3.

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
import os
import sys
import time

from control.heading import HeadingController, heading_error
from control.mixer import mix
from control.real_heading import MAX_RATE_DPS, HeadingUnavailable, RealHeading

THROTTLE_MOSTRADO = 20      # so para ilustrar o mixer; nao e enviado
CAP = 30                    # o mesmo teto que o ESP32 impoe
CAL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "config", "bno055_calibration.json")


class FakeBNO055:
    """Sensor falso que roda devagar. Para ver o ecra sem hardware.

    Sobe a calibracao ao fim de 3 s, para exercitar tambem o caminho de
    "ainda nao esta calibrado".
    """

    def __init__(self):
        self.t0 = time.monotonic()
        # offsets falsos, so para --guardar-cal/--carregar-cal correrem
        self.offsets_accelerometer = (0, 0, 0)
        self.offsets_gyroscope = (0, 0, 0)
        self.offsets_magnetometer = (0, 0, 0)
        self.radius_accelerometer = 1000
        self.radius_magnetometer = 480

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
    p.add_argument("--guardar-cal", action="store_true",
                   help=f"gravar a calibracao ao chegar a 3333 ({CAL_PATH})")
    p.add_argument("--carregar-cal", action="store_true",
                   help="carregar no sensor a calibracao gravada, ao arrancar")
    p.add_argument("--taxa-max", type=float, default=MAX_RATE_DPS,
                   help="taxa de rotacao maxima credivel, graus/s "
                        f"(omissao {MAX_RATE_DPS:.0f})")
    args = p.parse_args()

    if args.fake:
        print("[BANCADA] Sensor FALSO. Nada disto sao medicoes reais.")
        heading_src = RealHeading(FakeBNO055(), mount_offset_deg=args.offset,
                                  declination_deg=args.declinacao,
                                  max_rate_dps=args.taxa_max)
    else:
        try:
            from control.real_heading import create_bno055
            heading_src = create_bno055(mount_offset_deg=args.offset,
                                        declination_deg=args.declinacao,
                                        max_rate_dps=args.taxa_max)
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

    if args.carregar_cal:
        try:
            data = heading_src.load_calibration(CAL_PATH)
        except FileNotFoundError:
            print(f"[ERRO] Nao ha calibracao gravada em {CAL_PATH}.")
            print("       Calibrar primeiro com --guardar-cal.")
            return 1
        except (OSError, ValueError) as e:
            print(f"[ERRO] Calibracao gravada nao carregou: {e}")
            print("       O sensor ficou como estava. Apagar o ficheiro e "
                  "recalibrar com --guardar-cal.")
            return 1
        print(f"[CAL] Carregada a calibracao de {data.get('saved_at', '?')}. "
              "Confirmar que foi gravada nesta montagem.")

    ctrl = HeadingController(kp=args.kp, max_steer=100.0)
    ctrl.set_target(args.alvo)
    periodo = 1.0 / args.hz

    print(f"[BANCADA] alvo={args.alvo:.1f} deg  kp={args.kp}  "
          f"offset={args.offset:.1f}  declinacao={args.declinacao:.1f}")
    print("[BANCADA] Sem serie e sem motores. Rodar o sensor a mao. Ctrl-C para sair.")
    print()

    gravada = False
    rejeitadas = 0
    try:
        while True:
            cal = heading_src.calibration()
            if args.guardar_cal and not gravada and tuple(cal) == (3, 3, 3, 3):
                try:
                    heading_src.save_calibration(CAL_PATH)
                    gravada = True
                    print(f"[CAL] Calibracao 3333 gravada em {CAL_PATH}",
                          flush=True)
                except (OSError, ValueError) as e:
                    # 3333 lido aqui pode ja nao ser 3333 dentro do save;
                    # tenta-se outra vez na volta seguinte
                    print(f"[CAL] Nao gravou ({e}); volta a tentar.",
                          flush=True)
            try:
                heading = heading_src.read()
            except HeadingUnavailable as e:
                print(f"  cal={cal.sys}{cal.gyro}{cal.accel}{cal.mag}  "
                      f"SEM RUMO -> em NAV isto seria DISARM  ({e})",
                      flush=True)
                time.sleep(periodo)
                continue

            aviso = ""
            if heading_src.rejected_total > rejeitadas:
                rejeitadas = heading_src.rejected_total
                aviso = f"  [salto rejeitado, total {rejeitadas}]"

            err = heading_error(args.alvo, heading)
            steer = ctrl.update(heading)
            left, right = mix(THROTTLE_MOSTRADO, steer, 0, CAP)
            bussola = heading % 360.0

            print(f"  cal={cal.sys}{cal.gyro}{cal.accel}{cal.mag}  "
                  f"rumo={bussola:6.1f}  erro={err:+7.1f}  "
                  f"steer={steer:+6.1f} [{barra(steer)}]  "
                  f"L={left:4.1f} R={right:4.1f} (nao enviado){aviso}",
                  flush=True)
            time.sleep(periodo)
    except KeyboardInterrupt:
        print("\n[BANCADA] Terminado. Nada foi enviado ao ESP32.")
        print(f"[BANCADA] Saltos rejeitados nesta sessao: {rejeitadas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
