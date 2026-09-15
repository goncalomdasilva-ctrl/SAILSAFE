#!/usr/bin/env python3
"""Ensaio de bancada do GPS: ver se o NEO-8M fala e se o fix presta.

NAO liga a serie do ESP32, NAO mexe em motores, NAO navega. De proposito.
So responde a tres perguntas, por esta ordem, que e a ordem em que
costumam falhar:

  1. Chega alguma coisa a porta? (cabo, baud, TX/RX trocados)
  2. As tramas passam o checksum? (baud errado da linhas que quase
     parecem tramas, e uma taxa de rejeicao alta com sinal e o sintoma)
  3. O fix presta? (satelites e HDOP, nao so "tem posicao")

Uso:
    cd software/raspberry_pi
    python3 -m tools.gps_bench                      # /dev/serial0 a 9600
    python3 -m tools.gps_bench --fake               # sem hardware
    python3 -m tools.gps_bench --porta /dev/ttyUSB1 --baud 38400
    python3 -m tools.gps_bench --cru                # mostrar as tramas

A primeira fixacao a frio leva minutos e precisa de ceu: a antena tem de
ver o ceu, nao o teto. Se depois de cinco minutos a janela continuar sem
fix, o problema ja nao e paciencia.
"""

import argparse
import sys
import time

from control.real_position import PositionUnavailable, RealPosition


class FakePort:
    """GPS falso: dois segundos sem fix, depois fix a melhorar."""

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._t0 = clock()
        self._i = 0

    @staticmethod
    def _nmea(corpo):
        soma = 0
        for c in corpo:
            soma ^= ord(c)
        return f"${corpo}*{soma:02X}\r\n".encode("ascii")

    @property
    def in_waiting(self):
        return 1

    def readline(self):
        self._i += 1
        decorrido = self._clock() - self._t0
        if decorrido < 2.0:
            return self._nmea("GPGGA,120001.00,,,,,0,00,99.9,,M,,M,,")
        sats = min(11, 3 + int(decorrido))
        hdop = max(0.8, 5.0 - decorrido * 0.5)
        lat = 3841.500 + (self._i % 20) * 0.001
        return self._nmea(
            f"GPGGA,1200{decorrido:04.1f},{lat:.3f},N,00908.500,W,1,"
            f"{sats:02d},{hdop:.1f},20.0,M,,M,,")


def contadores(st):
    """Uma linha com os quatro contadores, cada um com significado proprio."""
    return (f"tramas {st.seen}  checksum mau {st.bad_checksum}  "
            f"sem fix {st.no_fix}  recusadas {st.rejected}  "
            f"aceites {st.accepted}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Ensaio de bancada do GPS")
    p.add_argument("--fake", action="store_true", help="sem hardware")
    p.add_argument("--porta", default="/dev/serial0")
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--cru", action="store_true", help="mostrar as tramas cruas")
    p.add_argument("--intervalo", type=float, default=1.0)
    p.add_argument("--min-sats", type=int, default=4, dest="min_sats")
    p.add_argument("--max-hdop", type=float, default=2.5, dest="max_hdop")
    args = p.parse_args(argv)

    if args.fake:
        gps = RealPosition(FakePort(), min_satellites=args.min_sats,
                           max_hdop=args.max_hdop)
        print("[GPS] porta simulada")
    else:
        from control.real_position import create_neo8m
        try:
            gps = create_neo8m(args.porta, baudrate=args.baud,
                               min_satellites=args.min_sats,
                               max_hdop=args.max_hdop)
        except Exception as e:                       # noqa: BLE001
            print(f"[ERRO] nao abriu {args.porta} a {args.baud}: {e}")
            print("       raspi-config -> Serial Port: consola NAO, "
                  "hardware SIM. No Pi 4 ver tambem o dtoverlay=disable-bt.")
            return 1
        print(f"[GPS] {args.porta} a {args.baud} baud")

    print(f"[GPS] criterios: >= {args.min_sats} satelites, HDOP <= "
          f"{args.max_hdop:.1f}. Ctrl-C para sair.\n")

    t0 = time.monotonic()
    primeiro_fix = None
    try:
        while True:
            # Um leitor so: as tramas passam sempre pelo poll(), e o
            # mostrador de tramas cruas e apenas um observador. Ler a
            # porta em dois sitios faz desaparecer metade das tramas --
            # e sao as boas que desaparecem, porque sao as que interessam.
            mostrar = None
            if args.cru:
                def mostrar(linha, fix):
                    print(f"  {'ok ' if fix else '-- '}{linha.strip()}")
            gps.poll(on_line=mostrar)

            try:
                posicao, motivo = gps.position(), ""
            except PositionUnavailable as e:
                posicao, motivo = None, str(e)
            st = gps.stats
            decorrido = time.monotonic() - t0
            fix = gps.last_fix

            if posicao and primeiro_fix is None:
                primeiro_fix = decorrido
                print(f"[GPS] primeira fixacao ao fim de {primeiro_fix:.0f} s\n")

            if posicao:
                lat, lon = posicao
                detalhe = ""
                if fix is not None and fix.satellites is not None:
                    detalhe = f"  {fix.satellites} sat  HDOP {fix.hdop:.1f}"
                print(f"  {decorrido:6.0f}s  {lat:11.6f} {lon:12.6f}{detalhe}"
                      f"   {contadores(st)}")
            else:
                print(f"  {decorrido:6.0f}s  sem posicao: {motivo}"
                      f"   {contadores(st)}")

            # O aviso so dispara com tramas CORROMPIDAS. Tramas integras
            # que nao dao posicao sao o normal de um arranque a frio, e
            # avisar sobre elas seria ensinar a ignorar o aviso.
            if st.seen == 0 and decorrido > 5:
                print("       Nada chega a porta. Verificar TX/RX cruzados, "
                      "massa comum e o baud.")
            elif st.seen > 20 and st.bad_checksum > st.seen * 0.5:
                print("       Mais de metade das tramas vem corrompida. "
                      "Quase sempre e o baud errado ou massa em falta.")

            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\n[GPS] fim")
        return 0


if __name__ == "__main__":
    sys.exit(main())
