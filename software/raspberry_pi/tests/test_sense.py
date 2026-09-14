#!/usr/bin/env python3
"""Testes do ADS1015 e do PowerSense, sem hardware nenhum.

O barramento I2C e substituido por um falso. O que se testa nao e o
conversor -- e a politica: o que o codigo faz quando o ganho esta errado,
quando a entrada satura, quando o canal nao existe e quando ninguem
calibrou nada.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensors import ads1015 as A                                  # noqa: E402
from sensors.ads1015 import (ADS1015, SenseSaturated,             # noqa: E402
                             SenseUnavailable)
from sensors.power_sense import (CHANNELS, Channel, PowerSense,   # noqa: E402
                                 factor_from_measurement,
                                 load_calibration)


class FakeBus:
    """Barramento I2C controlavel.

    counts: dict canal -> contagens que o conversor devolve.
    """

    def __init__(self, counts=None, raise_os=False, never_ready=False):
        self.counts = counts or {}
        self.raise_os = raise_os
        self.never_ready = never_ready
        self.config_writes = []
        self._channel = 0

    def write_i2c_block_data(self, address, register, data):
        if self.raise_os:
            raise OSError("I2C timeout simulado")
        palavra = (data[0] << 8) | data[1]
        self.config_writes.append(palavra)
        mux = palavra & 0x7000
        for canal, valor in A.MUX_SINGLE.items():
            if valor == mux:
                self._channel = canal

    def read_i2c_block_data(self, address, register, length):
        if self.raise_os:
            raise OSError("I2C timeout simulado")
        if register == A.REG_CONFIG:
            pronto = 0 if self.never_ready else A.OS_SINGLE
            palavra = pronto
        else:
            contagens = self.counts.get(self._channel, 0)
            palavra = (contagens & 0x0FFF) << 4
        return [(palavra >> 8) & 0xFF, palavra & 0xFF]


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def _adc(**kwargs):
    bus = kwargs.pop("bus", None) or FakeBus()
    return ADS1015(bus, sleep=lambda s: None, **kwargs), bus


# --- ADS1015: o ganho ---------------------------------------------------

def test_ganho_por_omissao_da_classe_e_4096():
    adc, _ = _adc()
    assert adc.gain == A.GAIN_4096
    assert abs(adc.full_scale_v - 4.096) < 1e-9


def test_lsb_e_2mV():
    adc, _ = _adc()
    assert abs(adc.lsb_v - 0.002) < 1e-9


def test_pga_e_reescrito_em_cada_conversao():
    # O motivo esta escrito no topo do ads1015.py: um reset do chip volta
    # ao ganho de +-2,048 V e a leitura passa a mentir sem dar erro.
    adc, bus = _adc(bus=FakeBus(counts={0: 1000, 1: 1000}))
    adc.read_counts(0)
    adc.read_counts(1)
    assert len(bus.config_writes) == 2
    for palavra in bus.config_writes:
        assert palavra & 0x0E00 == A.GAIN_4096


def test_ganho_desconhecido_e_recusado():
    try:
        ADS1015(FakeBus(), gain=0x1234)
    except ValueError:
        return
    raise AssertionError("aceitou um ganho que nao existe")


# --- ADS1015: leitura ---------------------------------------------------

def test_contagens_com_sinal():
    adc, _ = _adc(bus=FakeBus(counts={0: -100}))
    assert adc.read_counts(0) == -100


def test_volts_a_partir_das_contagens():
    # 1050 contagens * 2 mV = 2,100 V, que e a 3S cheia atras do divisor.
    adc, _ = _adc(bus=FakeBus(counts={2: 1050}))
    assert abs(adc.read_volts(2) - 2.100) < 1e-6


def test_saturacao_levanta_em_vez_de_devolver_numero():
    adc, _ = _adc(bus=FakeBus(counts={0: A.SATURATION_COUNTS}))
    try:
        adc.read_volts(0)
    except SenseSaturated:
        return
    raise AssertionError("devolveu um numero para uma entrada saturada")


def test_saturado_tambem_e_indisponivel():
    # Quem so quer saber se tem numero apanha as duas com um except.
    adc, _ = _adc(bus=FakeBus(counts={0: 2047}))
    try:
        adc.read_volts(0)
    except SenseUnavailable:
        return
    raise AssertionError("SenseSaturated devia ser SenseUnavailable")


def test_i2c_morto_levanta_sense_unavailable():
    adc, _ = _adc(bus=FakeBus(raise_os=True))
    try:
        adc.read_counts(0)
    except SenseUnavailable:
        return
    raise AssertionError("erro de I2C nao foi convertido")


def test_conversao_que_nunca_termina_da_timeout():
    relogio = FakeClock()

    def avanca(s):
        relogio.t += 0.001

    adc = ADS1015(FakeBus(never_ready=True), clock=relogio, sleep=avanca)
    try:
        adc.read_counts(0)
    except SenseUnavailable:
        return
    raise AssertionError("ficou preso a espera do bit OS")


def test_canal_fora_do_intervalo():
    adc, _ = _adc()
    try:
        adc.read_counts(4)
    except ValueError:
        return
    raise AssertionError("aceitou um canal que nao existe")


# --- PowerSense: conversao ----------------------------------------------

def _sense(counts, calibration=None):
    adc = ADS1015(FakeBus(counts=counts), sleep=lambda s: None)
    return PowerSense(adc, calibration=calibration or {})


def test_tensao_de_bateria_pelo_divisor():
    # 2,100 V a entrada / (1/6) = 12,60 V: a 3S cheia.
    s = _sense({2: 1050})
    leitura = s.read_channel(s.channel_by_name("eletronica"))
    assert leitura.available
    assert abs(leitura.value - 12.60) < 0.01


def test_volts_por_celula():
    s = _sense({2: 1050})
    leitura = s.read_channel(s.channel_by_name("eletronica"))
    assert abs(s.per_cell(leitura) - 4.20) < 0.01


def test_calibracao_multiplica():
    s = _sense({2: 1050}, calibration={"a2": 1.05})
    leitura = s.read_channel(s.channel_by_name("eletronica"))
    assert abs(leitura.value - 13.23) < 0.02


def test_canal_nao_instalado_da_none_e_nao_zero():
    # O ACS758 ainda nao existe. Um zero seria indistinguivel de um casco
    # parado, que e exatamente a leitura de um barco a deriva.
    s = _sense({3: 300})
    leitura = s.read_channel(s.channel_by_name("corrente_esq"))
    assert leitura.value is None
    assert not leitura.available
    assert "nao instalado" in leitura.note


def test_corrente_quando_instalado():
    canais = tuple(c._replace(installed=True) if c.name == "corrente_esq" else c
                   for c in CHANNELS)
    adc = ADS1015(FakeBus(counts={3: 900}), sleep=lambda s: None)
    s = PowerSense(adc, calibration={}, channels=canais)
    leitura = s.read_channel(s.channel_by_name("corrente_esq"))
    # 900 * 2 mV = 1,800 V -> (1,8 - 0,6) / 0,06 = 20 A
    assert abs(leitura.value - 20.0) < 0.01


def test_casco_sem_alimentacao_e_estado_e_nao_avaria():
    s = _sense({0: 10})       # 0,02 V a entrada -> 0,12 V de bateria
    leitura = s.read_channel(s.channel_by_name("casco_esq"))
    assert leitura.available
    assert "sem alimentacao" in leitura.note


def test_saturacao_chega_ao_power_sense_como_ausencia():
    s = _sense({0: 2047})
    leitura = s.read_channel(s.channel_by_name("casco_esq"))
    assert leitura.value is None
    assert "saturado" in leitura.note


def test_read_all_da_todos_os_canais():
    s = _sense({0: 900, 1: 900, 2: 1050})
    todas = s.read_all()
    assert set(todas) == {"casco_esq", "casco_dir", "eletronica", "corrente_esq"}


# --- calibracao ---------------------------------------------------------

def test_sem_ficheiro_nao_esta_calibrado():
    fatores, calibrado = load_calibration("/nao/existe/calibration.json")
    assert not calibrado
    assert fatores["a0"] == 1.0


def test_fator_de_um_ponto():
    # Multimetro diz 12,60; o canal reportou 12,40 com fator 1,0.
    f = factor_from_measurement(12.60, 12.40)
    assert abs(12.40 * f - 12.60) < 1e-9


def test_fator_recusa_dividir_por_zero():
    try:
        factor_from_measurement(12.6, 0.0)
    except ValueError:
        return
    raise AssertionError("aceitou uma leitura de zero como referencia")


def test_channel_namedtuple_tem_os_campos_do_documento():
    assert Channel._fields == ("index", "name", "kind", "cells", "installed")


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
