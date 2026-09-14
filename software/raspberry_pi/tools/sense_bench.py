#!/usr/bin/env python3
"""Ensaio de bancada do sense: ver os canais e calibra-los.

NAO liga a serie, NAO fala com o ESP32, NAO mexe em motores. De proposito.
Este script existe para fazer, com fonte de bancada e multimetro, os dois
passos que o documento de sense exige antes de se poder confiar em
qualquer estimativa de carga:

  1. Varrer 9 -> 13 V e confirmar que a leitura acompanha e NAO satura.
  2. Calibrar o fator de escala de cada canal contra o multimetro.

Uso:
    cd software/raspberry_pi
    python3 -m tools.sense_bench                    # ADS1015 real, continuo
    python3 -m tools.sense_bench --fake             # sem hardware, so ver o ecra
    python3 -m tools.sense_bench --once             # uma leitura e sai
    python3 -m tools.sense_bench --calibrar a2 12.60

O --calibrar le o canal com o fator a 1,0, compara com o valor que o
multimetro deu e guarda o quociente em config/calibration.json. Um ponto
chega: o erro dominante e de ganho (tolerancia dos resistores), e o
divisor passa pela origem.

Ordem sugerida na bancada, com a fonte limitada em corrente:
  - ligar so o divisor do canal, sem bateria nenhuma
  - subir a fonte de 9 a 13 V em degraus de 0,5 V e anotar as duas colunas
  - calibrar a 12,6 V, que e o topo da escala util
  - repetir para os tres canais de tensao
"""

import argparse
import sys
import time

from sensors.ads1015 import (ADS1015, GAIN_2048, GAIN_4096,
                             SenseUnavailable)
from sensors.power_sense import (CHANNELS, PowerSense,
                                 default_config_path,
                                 factor_from_measurement, load_calibration,
                                 save_calibration)


class FakeBus:
    """Barramento falso que devolve uma 3S a descarregar devagar.

    Conhece o LSB para que o --ganho-errado mostre mesmo a saturacao, e
    nao uma leitura a metade. E o unico ponto deste script onde o falso
    tem de imitar o chip e nao so os numeros.
    """

    def __init__(self, lsb_v=0.002):
        self.t = 0.0
        self.lsb_v = lsb_v
        self._canal = 0

    def write_i2c_block_data(self, address, register, data):
        palavra = (data[0] << 8) | data[1]
        self._canal = {0x4000: 0, 0x5000: 1, 0x6000: 2, 0x7000: 3}.get(
            palavra & 0x7000, 0)

    def read_i2c_block_data(self, address, register, length):
        if register == 0x01:
            return [0x80, 0x00]
        self.t += 0.05
        volts = {0: 12.4, 1: 12.3, 2: 12.6 - 0.02 * self.t, 3: 1.8}[self._canal]
        v_adc = 1.8 if self._canal == 3 else volts / 6.0
        contagens = max(-2048, min(2047, int(v_adc / self.lsb_v)))
        palavra = (contagens & 0x0FFF) << 4
        return [(palavra >> 8) & 0xFF, palavra & 0xFF]


def construir(args):
    ganho = GAIN_2048 if args.ganho_errado else GAIN_4096
    if args.fake:
        lsb = (2.048 if args.ganho_errado else 4.096) / 2048
        return ADS1015(FakeBus(lsb_v=lsb), gain=ganho, sleep=lambda s: None)
    from sensors.ads1015 import create_ads1015
    return create_ads1015(gain=ganho)


def mostrar(sense, adc):
    fatores, calibrado = load_calibration(sense.config_path)
    marca = "" if calibrado else "   [POR CALIBRAR]"
    print(f"  {'canal':<14}{'contagens':>10}{'V no ADC':>10}"
          f"{'valor':>12}{'  nota'}{marca}")
    for canal in sense.channels:
        leitura = sense.read_channel(canal)
        if canal.installed:
            try:
                contagens = adc.read_counts(canal.index)
                v_adc = f"{contagens * adc.lsb_v:9.4f}"
                contagens = f"{contagens:10d}"
            except SenseUnavailable as e:
                contagens, v_adc = f"{'--':>10}", f"{'--':>9}"
                leitura = leitura._replace(note=str(e))
        else:
            contagens, v_adc = f"{'--':>10}", f"{'--':>9}"

        if leitura.available:
            valor = f"{leitura.value:11.3f}{leitura.unit}"
            por_celula = sense.per_cell(leitura)
            extra = f"  ({por_celula:.2f} V/celula)" if por_celula else ""
        else:
            valor, extra = f"{'sem leitura':>12}", ""
        print(f"  {leitura.name:<14}{contagens}{v_adc} {valor}"
              f"  {leitura.note}{extra}")


def calibrar(sense, adc, canal_id, medido):
    canal = next((c for c in sense.channels if f"a{c.index}" == canal_id
                  or c.name == canal_id), None)
    if canal is None:
        print(f"[ERRO] canal desconhecido: {canal_id}")
        return 1
    cru = PowerSense(adc, calibration={}, channels=sense.channels)
    leitura = cru.read_channel(canal)
    if not leitura.available:
        print(f"[ERRO] o canal nao deu leitura: {leitura.note}")
        return 1
    try:
        fator = factor_from_measurement(medido, leitura.value)
    except ValueError as e:
        print(f"[ERRO] {e}")
        return 1

    fatores, _ = load_calibration(sense.config_path)
    fatores[f"a{canal.index}"] = round(fator, 6)
    caminho = save_calibration(fatores, sense.config_path)
    print(f"  canal      {canal.name} (A{canal.index})")
    print(f"  reportado  {leitura.value:.3f} {leitura.unit}")
    print(f"  multimetro {medido:.3f} {leitura.unit}")
    print(f"  fator      {fator:.6f}   ({(fator - 1) * 100:+.2f} %)")
    print(f"  guardado   {caminho}")
    if abs(fator - 1.0) > 0.15:
        print("  [AVISO] mais de 15 % de correcao. Isto ja nao e tolerancia "
              "de resistor -- verificar os valores do divisor antes de "
              "aceitar este fator.")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Ensaio e calibracao do sense")
    p.add_argument("--fake", action="store_true",
                   help="sem hardware: barramento simulado")
    p.add_argument("--once", action="store_true", help="uma leitura e sai")
    p.add_argument("--intervalo", type=float, default=1.0)
    p.add_argument("--calibrar", nargs=2, metavar=("CANAL", "VOLTS"),
                   help="calibrar um canal contra o multimetro (ex.: a2 12.60)")
    p.add_argument("--ganho-errado", action="store_true", dest="ganho_errado",
                   help="forcar o PGA de +-2,048 V para VER a saturacao "
                        "descrita no documento de sense")
    args = p.parse_args(argv)

    adc = construir(args)
    sense = PowerSense(adc)

    print(f"[SENSE] FSR +-{adc.full_scale_v:.3f} V   LSB {adc.lsb_v * 1e3:.3f} mV"
          f"   calibracao: {default_config_path()}")
    if args.ganho_errado:
        print("[AVISO] PGA a +-2,048 V de proposito: acima de 12,29 V de "
              "bateria a leitura satura e a bateria parece cheia.")
    print()

    if args.calibrar:
        return calibrar(sense, adc, args.calibrar[0], float(args.calibrar[1]))

    try:
        while True:
            mostrar(sense, adc)
            if args.once:
                return 0
            print()
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\n[SENSE] fim")
        return 0


if __name__ == "__main__":
    sys.exit(main())
