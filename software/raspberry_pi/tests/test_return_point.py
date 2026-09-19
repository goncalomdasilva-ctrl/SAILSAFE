#!/usr/bin/env python3
"""Testes do ponto de regresso, sem GPS nenhum.

O que se testa nao e aritmetica de medias -- e a politica: quando e que o
ponto se grava, quando e que se recusa a gravar, e o que acontece a quem
tenta reescreve-lo.

Correr com: python3 tests/test_return_point.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control.navigation import haversine_m                       # noqa: E402
from control.return_point import (ReturnPoint,                   # noqa: E402
                                  ReturnPointUnavailable)

# Lisboa, ~38 41,5' N / 9 08,5' W
LAT, LON = 38.691667, -9.141667
M_POR_GRAU_LAT = 111320.0


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def avanca(self, dt):
        self.t += dt


def desloca(lat, lon, norte_m, este_m):
    import math
    return (lat + norte_m / M_POR_GRAU_LAT,
            lon + este_m / (M_POR_GRAU_LAT * math.cos(math.radians(lat))))


def enche(rp, clock, n, lat=LAT, lon=LON, dt=1.0):
    """n fixes seguidos no mesmo sitio, a 1 Hz."""
    for _ in range(n):
        rp.feed(lat, lon)
        clock.avanca(dt)


# --- gravacao -----------------------------------------------------------

def test_nao_grava_sem_fixes_suficientes():
    """Menos amostras do que o minimo e recusa, e diz quantas tinha."""
    c = FakeClock()
    rp = ReturnPoint(min_fixes=5, clock=c)
    enche(rp, c, 4)
    try:
        rp.record()
    except ReturnPointUnavailable as e:
        assert "4 fixes" in str(e), str(e)
    else:
        assert False, "gravou com 4 fixes e o minimo era 5"
    assert not rp.is_set


def test_grava_com_fixes_suficientes():
    c = FakeClock()
    rp = ReturnPoint(min_fixes=5, clock=c)
    enche(rp, c, 5)
    p = rp.record()
    assert rp.is_set
    assert p.fixes == 5
    assert haversine_m(p.lat, p.lon, LAT, LON) < 0.01


def test_a_media_fica_no_centro_das_amostras():
    """Ruido simetrico tem de cancelar, e nao arrastar o ponto."""
    c = FakeClock()
    rp = ReturnPoint(min_fixes=4, max_spread_m=10.0, clock=c)
    for norte, este in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
        rp.feed(*desloca(LAT, LON, norte, este))
        c.avanca(1.0)
    p = rp.record()
    assert haversine_m(p.lat, p.lon, LAT, LON) < 0.5, "media fora do centro"


# --- criterio de dispersao ---------------------------------------------

def test_recusa_quando_as_amostras_estao_espalhadas():
    """A media de uma nuvem nao e uma posicao. Recusar e o lado seguro."""
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, max_spread_m=5.0, clock=c)
    for norte in (0, 30, -30):
        rp.feed(*desloca(LAT, LON, norte, 0))
        c.avanca(1.0)
    try:
        rp.record()
    except ReturnPointUnavailable as e:
        assert "espalhados" in str(e), str(e)
    else:
        assert False, "gravou fixes espalhados por 60 m"
    assert not rp.is_set


def test_dispersao_dentro_do_limite_passa():
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, max_spread_m=5.0, clock=c)
    for norte in (0, 2, -2):
        rp.feed(*desloca(LAT, LON, norte, 0))
        c.avanca(1.0)
    p = rp.record()
    assert p.spread_m <= 5.0


# --- prazo das amostras -------------------------------------------------

def test_amostras_velhas_saem_da_janela():
    """Um fix de ha cinco minutos nao diz onde o barco esta agora."""
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, window_s=10.0, clock=c)
    enche(rp, c, 3)
    c.avanca(60.0)
    assert rp.samples == []
    try:
        rp.record()
    except ReturnPointUnavailable as e:
        assert "0 fixes" in str(e), str(e)
    else:
        assert False, "gravou a partir de amostras expiradas"


def test_janela_deslizante_mantem_as_recentes():
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, window_s=5.0, clock=c)
    enche(rp, c, 20)                       # 20 s de fixes a 1 Hz
    # so as dos ultimos 5 s ficam
    assert 4 <= len(rp.samples) <= 6, len(rp.samples)
    assert rp.record().fixes == len(rp.samples)


# --- grava uma vez ------------------------------------------------------

def test_nao_se_reescreve_sozinho():
    """O caso que a politica existe para impedir: o ponto a seguir o barco.

    Se o ponto se atualizasse a cada ARM, um segundo ARM ja longe da
    margem apontaria o regresso para onde o barco esta, e nao para onde
    ficou quem o pode ir buscar.
    """
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, window_s=30.0, max_spread_m=5.0, clock=c)
    enche(rp, c, 3)
    primeiro = rp.record()

    # o barco afasta-se 500 m e alguem volta a armar
    longe = desloca(LAT, LON, 500, 0)
    c.avanca(60.0)
    enche(rp, c, 5, lat=longe[0], lon=longe[1])
    segundo = rp.record()

    assert segundo == primeiro, "o ponto de regresso mudou sozinho"
    assert haversine_m(*rp.position(), LAT, LON) < 0.01


def test_reset_e_um_gesto_explicito():
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, window_s=30.0, clock=c)
    enche(rp, c, 3)
    rp.record()
    rp.reset()
    assert not rp.is_set
    # a janela fica: apaga-se a decisao, nao a medicao
    assert len(rp.samples) == 3
    assert rp.record().fixes == 3


# --- consulta -----------------------------------------------------------

def test_position_nao_inventa_a_partir_da_janela():
    """Ter amostras nao e ter ponto gravado. Sao coisas diferentes."""
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, clock=c)
    enche(rp, c, 10)
    assert rp.point is None
    try:
        rp.position()
    except ReturnPointUnavailable:
        pass
    else:
        assert False, "devolveu posicao sem ponto gravado"


def test_distancia_ao_ponto():
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, clock=c)
    enche(rp, c, 3)
    rp.record()
    longe = desloca(LAT, LON, 100, 0)
    d = rp.distance_from(*longe)
    assert abs(d - 100.0) < 1.0, d


def test_preview_nao_grava():
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, clock=c)
    enche(rp, c, 2)
    assert rp.preview() is None
    rp.feed(LAT, LON)
    prev = rp.preview()
    assert prev is not None and prev[2] == 3
    assert not rp.is_set, "o preview gravou o ponto"


def test_describe_diz_o_estado():
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, clock=c)
    assert "por gravar" in rp.describe()
    enche(rp, c, 3)
    rp.record()
    assert "fixes" in rp.describe() and "dispersao" in rp.describe()


def test_continua_a_aceitar_amostras_depois_de_gravado():
    """A janela serve tambem para saber se ha receptor a funcionar."""
    c = FakeClock()
    rp = ReturnPoint(min_fixes=3, window_s=30.0, clock=c)
    enche(rp, c, 3)
    rp.record()
    enche(rp, c, 3)
    assert len(rp.samples) == 6
    assert rp.point.fixes == 3, "o ponto gravado mudou de numero de fixes"


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
