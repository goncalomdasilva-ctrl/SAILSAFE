#!/usr/bin/env python3
"""Testes do RealPosition, sem GPS nenhum.

A porta serie e substituida por uma fila de linhas. O que se testa nao e
o modulo -- e a politica: o que a classe faz quando o GPS nao tem fix,
tem um fix mau, manda lixo, cala-se, ou reporta 0,0.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control.real_position import (PositionUnavailable, RealBoat,   # noqa: E402
                                   RealPosition, ddmm_to_degrees,
                                   nmea_checksum_ok, parse_sentence)


def nmea(corpo):
    """Fecha uma trama com o checksum certo. '$' e '*' entram aqui."""
    soma = 0
    for c in corpo:
        soma ^= ord(c)
    return f"${corpo}*{soma:02X}\r\n"


# Lisboa, ~38 41,5' N / 9 08,5' W
GGA_BOM = nmea("GPGGA,120000.00,3841.500,N,00908.500,W,1,09,0.9,20.0,M,,M,,")
GGA_SEM_FIX = nmea("GPGGA,120001.00,,,,,0,00,99.9,,M,,M,,")
GGA_POUCOS_SATS = nmea("GPGGA,120002.00,3841.500,N,00908.500,W,1,03,1.2,20.0,M,,M,,")
GGA_HDOP_MAU = nmea("GPGGA,120003.00,3841.500,N,00908.500,W,1,09,7.8,20.0,M,,M,,")
GGA_NULA = nmea("GPGGA,120004.00,0000.000,N,00000.000,E,1,09,0.9,0.0,M,,M,,")
RMC_BOM = nmea("GPRMC,120000.00,A,3841.500,N,00908.500,W,0.1,0.0,130926,,")
RMC_VOID = nmea("GPRMC,120005.00,V,,,,,,,130926,,")
GNGGA_BOM = nmea("GNGGA,120006.00,3841.600,N,00908.500,W,1,11,0.8,20.0,M,,M,,")


class FakePort:
    """Porta serie com uma fila de linhas."""

    def __init__(self, linhas=None, binario=True):
        self.linhas = list(linhas or [])
        self.binario = binario

    @property
    def in_waiting(self):
        return len(self.linhas)

    def readline(self):
        if not self.linhas:
            return b"" if self.binario else ""
        linha = self.linhas.pop(0)
        if isinstance(linha, bytes):
            return linha
        return linha.encode("ascii") if self.binario else linha


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


# --- checksum -----------------------------------------------------------

def test_checksum_valido():
    assert nmea_checksum_ok(GGA_BOM)


def test_checksum_errado_e_rejeitado():
    partida = GGA_BOM.strip()[:-2] + "00"
    assert not nmea_checksum_ok(partida)


def test_linha_sem_checksum_e_rejeitada():
    # Nao ha como saber se chegou inteira, logo nao conta como valida.
    assert not nmea_checksum_ok("$GPGGA,120000.00,3841.500,N")


def test_linha_partida_a_meio():
    assert parse_sentence("$GPGGA,120000.00,3841.5") is None


# --- coordenadas --------------------------------------------------------

def test_ddmm_para_graus():
    # 3841.500 = 38 graus 41,5 minutos = 38,691666...
    assert abs(ddmm_to_degrees("3841.500", "N") - 38.6916667) < 1e-6


def test_hemisferio_sul_e_oeste_sao_negativos():
    assert ddmm_to_degrees("3841.500", "S") < 0
    assert ddmm_to_degrees("00908.500", "W") < 0


def test_campo_vazio_nao_da_coordenada():
    assert ddmm_to_degrees("", "N") is None
    assert ddmm_to_degrees("3841.500", "") is None


def test_minutos_impossiveis_sao_rejeitados():
    assert ddmm_to_degrees("3875.000", "N") is None


# --- tramas -------------------------------------------------------------

def test_gga_com_fix():
    fix = parse_sentence(GGA_BOM)
    assert fix is not None and fix.satellites == 9 and abs(fix.hdop - 0.9) < 1e-9


def test_gga_sem_fix_nao_da_posicao():
    assert parse_sentence(GGA_SEM_FIX) is None


def test_rmc_com_estado_A():
    fix = parse_sentence(RMC_BOM)
    assert fix is not None and abs(fix.lon + 9.1416667) < 1e-6


def test_rmc_void_nao_da_posicao():
    assert parse_sentence(RMC_VOID) is None


def test_talker_gn_tambem_serve():
    # Com GPS e GLONASS o modulo passa a emitir GN em vez de GP.
    assert parse_sentence(GNGGA_BOM) is not None


def test_trama_que_nao_interessa():
    assert parse_sentence(nmea("GPGSV,3,1,11,01,00,000,")) is None


# --- politica de aceitacao ----------------------------------------------

def test_posicao_boa_passa():
    p = RealPosition(FakePort([GGA_BOM]))
    lat, lon = p.position()
    assert abs(lat - 38.6916667) < 1e-6 and abs(lon + 9.1416667) < 1e-6


def test_sem_fix_levanta():
    p = RealPosition(FakePort([GGA_SEM_FIX, RMC_VOID]))
    try:
        p.position()
    except PositionUnavailable:
        return
    raise AssertionError("inventou uma posicao sem fix")


def test_poucos_satelites_sao_rejeitados():
    p = RealPosition(FakePort([GGA_POUCOS_SATS]), min_satellites=4)
    try:
        p.position()
    except PositionUnavailable:
        return
    raise AssertionError("aceitou um fix com tres satelites")


def test_hdop_mau_e_rejeitado():
    p = RealPosition(FakePort([GGA_HDOP_MAU]), max_hdop=2.5)
    try:
        p.position()
    except PositionUnavailable:
        return
    raise AssertionError("aceitou um fix com HDOP de 7,8")


def test_posicao_nula_e_rejeitada():
    # Um modulo sem fix as vezes reporta 0,0 -- uma coordenada valida ao
    # largo de Africa, que nao e a nossa.
    p = RealPosition(FakePort([GGA_NULA]))
    try:
        p.position()
    except PositionUnavailable:
        return
    raise AssertionError("aceitou a ilha nula")


def test_fix_velho_deixa_de_servir():
    relogio = FakeClock()
    porta = FakePort([GGA_BOM])
    p = RealPosition(porta, max_stale_s=2.0, clock=relogio)
    p.position()                      # fix fresco, passa
    relogio.t = 10.0                  # GPS calado desde entao
    try:
        p.position()
    except PositionUnavailable:
        return
    raise AssertionError("devolveu a ultima posicao conhecida como se fosse atual")


def test_fica_com_a_trama_mais_recente_do_buffer():
    # A mesma armadilha do ack do STOP: o que esta na fila nao acabou de
    # acontecer. Parar na primeira e navegar com passado.
    p = RealPosition(FakePort([GGA_BOM, GNGGA_BOM]))
    lat, _ = p.position()
    assert abs(lat - 38.6933333) < 1e-6       # 3841.600, a segunda


def test_lixo_entre_tramas_nao_impede_a_leitura():
    porta = FakePort([b"\x00\xff lixo de arranque\r\n", GGA_BOM])
    p = RealPosition(porta)
    assert p.position() is not None


def test_porta_em_texto_tambem_serve():
    p = RealPosition(FakePort([GGA_BOM], binario=False))
    assert p.position() is not None


def test_position_or_none_nao_levanta():
    p = RealPosition(FakePort([GGA_SEM_FIX]))
    assert p.position_or_none() is None


def test_stats_separam_corrompido_de_sem_fix():
    # Uma trama integra que nao da posicao NAO e o mesmo que uma trama
    # corrompida: a primeira e o normal de um arranque a frio, a segunda
    # aponta para baud errado. Contar as duas juntas faz um arranque
    # normal parecer avaria.
    partida = GGA_BOM.strip()[:-2] + "00\r\n"
    p = RealPosition(FakePort([GGA_SEM_FIX, partida, GGA_BOM]))
    p.position()
    st = p.stats
    assert st.seen == 3
    assert st.bad_checksum == 1        # so a partida
    assert st.no_fix == 1              # a GGA sem fix, integra
    assert st.accepted == 1            # a boa
    assert st.rejected == 0


def test_stats_contam_fix_recusado_por_criterio():
    p = RealPosition(FakePort([GGA_POUCOS_SATS]), min_satellites=4)
    try:
        p.position()
    except PositionUnavailable:
        pass
    st = p.stats
    assert st.rejected == 1 and st.bad_checksum == 0 and st.no_fix == 0


def test_arranque_a_frio_nao_conta_como_corrompido():
    # O caso real da bancada de 15-09: onze tramas por segundo, todas
    # integras, nenhuma com posicao. bad_checksum tem de ficar a zero.
    p = RealPosition(FakePort([GGA_SEM_FIX, RMC_VOID] * 5))
    p.poll()
    st = p.stats
    assert st.bad_checksum == 0 and st.no_fix == st.seen


def test_on_line_ve_todas_as_tramas_sem_as_roubar():
    # O defeito de 15-09: o mostrador de tramas cruas lia a porta por sua
    # conta, ficava com as tramas boas, e o contador dizia "aceites 0" com
    # posicoes validas no ecra. Observar nao pode consumir.
    vistas = []
    p = RealPosition(FakePort([GGA_SEM_FIX, GGA_BOM]))
    p.poll(on_line=lambda linha, fix: vistas.append((linha.strip(), fix is not None)))
    assert len(vistas) == 2
    assert vistas[1][1] is True                 # a GGA_BOM produziu Fix
    assert p.stats.accepted == 1                # e chegou ao estado
    assert p.position() is not None             # e da posicao


def test_on_line_tambem_ve_as_corrompidas():
    partida = GGA_BOM.strip()[:-2] + "00\r\n"
    vistas = []
    p = RealPosition(FakePort([partida]))
    p.poll(on_line=lambda linha, fix: vistas.append(fix))
    assert vistas == [None] and p.stats.bad_checksum == 1


def test_max_lines_limita_o_poll():
    p = RealPosition(FakePort([GGA_BOM] * 100), max_lines=5)
    assert p.poll() == 5


# --- fonte para o nav_guard ---------------------------------------------

def test_nao_e_sintetico():
    # O nav_guard() do main.py so deixa comandar motores com isto a False.
    assert RealPosition(FakePort()).SYNTHETIC is False
    assert RealBoat(None, None).SYNTHETIC is False


def test_real_boat_expoe_a_interface_do_simulado():
    class FakeHeading:
        def read(self):
            return 90.0

    b = RealBoat(RealPosition(FakePort([GGA_BOM] * 4)), FakeHeading())
    assert b.position() is not None
    assert abs(b.heading - 90.0) < 1e-9
    assert len(b.update(10, 10)) == 3


if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    falhas = 0
    for t in testes:
        try:
            t()
            print(f"  OK   {t.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"  FALHA {t.__name__}: {e}")
    print(f"\n{len(testes) - falhas}/{len(testes)} testes passaram")
    sys.exit(1 if falhas else 0)
