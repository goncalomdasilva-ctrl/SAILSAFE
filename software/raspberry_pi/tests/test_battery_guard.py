#!/usr/bin/env python3
"""Testes do BatteryGuard, sem hardware nenhum.

O que se testa e a politica de regresso: quando dispara, quando nao
dispara, e sobretudo que nao volta atras sozinho.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from safety.battery_guard import (ESTADO_OK, ESTADO_REGRESSO,       # noqa: E402
                                  BatteryGuard, BatteryGuardUnusable)
from sensors.power_sense import Reading                             # noqa: E402


def leitura(volts, calibrado=True, nota=""):
    return Reading("eletronica", "voltage", volts, "V", calibrado, nota)


def ausente(calibrado=True, nota="sem leitura"):
    return Reading("eletronica", "voltage", None, "V", calibrado, nota)


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def guarda(**kwargs):
    kwargs.setdefault("threshold_v", 10.5)
    return BatteryGuard(**kwargs)


def test_limiar_sem_valor_e_recusado():
    # Sai da medicao do consumo real, que ainda nao foi feita.
    try:
        BatteryGuard(threshold_v=None)
    except ValueError:
        return
    raise AssertionError("aceitou uma guarda sem limiar")


def test_bateria_cheia_fica_ok():
    g = guarda()
    assert g.update(leitura(12.4)) == ESTADO_OK
    assert not g.should_return


def test_uma_leitura_baixa_nao_chega():
    # O arranque de um ESC afunda o rail por instantes.
    g = guarda(consecutive=3)
    assert g.update(leitura(10.0)) == ESTADO_OK
    assert not g.should_return


def test_tres_leituras_baixas_disparam():
    g = guarda(consecutive=3)
    g.update(leitura(10.0))
    g.update(leitura(10.1))
    assert g.update(leitura(9.9)) == ESTADO_REGRESSO
    assert g.should_return


def test_o_contador_reinicia_com_uma_leitura_boa():
    g = guarda(consecutive=3)
    g.update(leitura(10.0))
    g.update(leitura(10.0))
    g.update(leitura(12.0))          # transitorio passou
    g.update(leitura(10.0))
    assert not g.should_return


def test_nao_desdispara_quando_a_tensao_recupera():
    # Com a carga a aliviar a tensao sobe. Se a guarda cedesse, o barco
    # oscilava entre abortar e continuar com cada vez menos energia.
    g = guarda(consecutive=2)
    g.update(leitura(10.0))
    g.update(leitura(10.0))
    assert g.should_return
    g.update(leitura(12.5))
    assert g.should_return


def test_reset_e_a_unica_saida():
    g = guarda(consecutive=1)
    g.update(leitura(9.0))
    assert g.should_return
    g.reset()
    assert not g.should_return


def test_cegueira_prolongada_manda_regressar():
    relogio = FakeClock()
    g = guarda(max_blind_s=10.0, clock=relogio)
    g.update(leitura(12.0))
    relogio.t = 5.0
    assert g.update(ausente()) == ESTADO_OK
    relogio.t = 20.0
    assert g.update(ausente()) == ESTADO_REGRESSO


def test_cegueira_curta_nao_dispara():
    relogio = FakeClock()
    g = guarda(max_blind_s=10.0, clock=relogio)
    g.update(leitura(12.0))
    relogio.t = 3.0
    assert not g.should_return


def test_arrancar_sem_leitura_nao_dispara_de_imediato():
    # O relogio da cegueira comeca na primeira tentativa, nao no big bang.
    relogio = FakeClock()
    relogio.t = 500.0
    g = guarda(max_blind_s=10.0, clock=relogio)
    assert g.update(ausente()) != ESTADO_REGRESSO


def test_recusa_decidir_sem_calibracao():
    g = guarda()
    try:
        g.update(leitura(9.0, calibrado=False))
    except BatteryGuardUnusable:
        return
    raise AssertionError("decidiu com numeros por calibrar")


def test_pode_ser_dispensada_a_calibracao_de_proposito():
    # Para a bancada, onde se quer ver a logica a funcionar.
    g = guarda(require_calibration=False, consecutive=1)
    assert g.update(leitura(9.0, calibrado=False)) == ESTADO_REGRESSO


def test_motivo_fica_escrito():
    g = guarda(consecutive=1)
    g.update(leitura(9.4))
    assert "9.4" in g.reason and "10.5" in g.reason


def test_last_volts_guarda_a_ultima_boa():
    g = guarda()
    g.update(leitura(11.7))
    g.update(ausente())
    assert abs(g.last_volts - 11.7) < 1e-9


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
