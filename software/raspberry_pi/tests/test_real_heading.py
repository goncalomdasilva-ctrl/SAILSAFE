#!/usr/bin/env python3
"""Testes do RealHeading, sem hardware nenhum.

Todo o BNO055 e substituido por um driver falso. O que se testa aqui nao e
o sensor -- e a politica: o que a classe faz quando o sensor mente, falha
ou ainda nao esta calibrado.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control.real_heading import (Calibration, HeadingUnavailable,  # noqa: E402
                                  RealHeading)


class FakeDriver:
    """BNO055 controlavel: define-se o que devolve e se rebenta."""

    def __init__(self, yaw=0.0, cal=(3, 3, 3, 3), raise_os=False):
        self.yaw = yaw
        self.cal = cal
        self.raise_os = raise_os

    @property
    def euler(self):
        if self.raise_os:
            raise OSError("I2C timeout simulado")
        if self.yaw is None:
            return None
        return (self.yaw, 0.0, 0.0)

    @property
    def calibration_status(self):
        if self.raise_os:
            raise OSError("I2C timeout simulado")
        return self.cal


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_leitura_calibrada():
    h = RealHeading(FakeDriver(yaw=45.0))
    assert abs(h.read() - 45.0) < 1e-9


def test_offset_e_declinacao_somam():
    # placa montada 90 deg torta, declinacao de -2 deg
    h = RealHeading(FakeDriver(yaw=10.0), mount_offset_deg=90.0,
                    declination_deg=-2.0)
    assert abs(h.read() - 98.0) < 1e-9


def test_saida_normalizada():
    # 350 + 20 = 370 -> 10, e nao 370
    h = RealHeading(FakeDriver(yaw=350.0), mount_offset_deg=20.0)
    assert abs(h.read() - 10.0) < 1e-9
    # 200 deg em bussola e -160 na convencao do heading.py
    h2 = RealHeading(FakeDriver(yaw=200.0))
    assert abs(h2.read() - (-160.0)) < 1e-9


def test_sem_calibracao_nao_da_numero():
    """O caso perigoso: o sensor responde, mas o valor nao presta."""
    h = RealHeading(FakeDriver(yaw=45.0, cal=(0, 3, 3, 0)))
    try:
        h.read()
    except HeadingUnavailable as e:
        assert "calibracao" in str(e)
    else:
        raise AssertionError("leu um rumo sem calibracao")


def test_mag_por_calibrar_chumba_mesmo_com_sys_alto():
    h = RealHeading(FakeDriver(yaw=45.0, cal=(3, 3, 3, 1)))
    try:
        h.read()
    except HeadingUnavailable:
        pass
    else:
        raise AssertionError("aceitou magnetometro por calibrar")


def test_fusao_sem_solucao():
    h = RealHeading(FakeDriver(yaw=None))
    try:
        h.read()
    except HeadingUnavailable as e:
        assert "sensor" in str(e)
    else:
        raise AssertionError("leu um rumo com euler=None")


def test_i2c_em_baixo():
    h = RealHeading(FakeDriver(raise_os=True))
    try:
        h.read()
    except HeadingUnavailable:
        pass
    else:
        raise AssertionError("nao detetou o I2C em baixo")


def test_calibracao_com_i2c_em_baixo_e_zero():
    h = RealHeading(FakeDriver(raise_os=True))
    assert h.calibration() == Calibration(0, 0, 0, 0)


def test_falha_curta_usa_ultima_boa():
    """Uma leitura perdida a 5 Hz nao pode desarmar o barco."""
    clock = FakeClock()
    drv = FakeDriver(yaw=30.0)
    h = RealHeading(drv, max_stale_s=0.5, clock=clock)
    assert abs(h.read() - 30.0) < 1e-9

    drv.yaw = None                 # falhou uma leitura
    clock.t = 0.2                  # dentro da tolerancia
    assert abs(h.read() - 30.0) < 1e-9
    assert h.fail_count == 1


def test_falha_longa_levanta():
    """Perder o sensor por mais de max_stale_s tem de ser visivel."""
    clock = FakeClock()
    drv = FakeDriver(yaw=30.0)
    h = RealHeading(drv, max_stale_s=0.5, clock=clock)
    h.read()

    drv.yaw = None
    clock.t = 2.0                  # muito para la da tolerancia
    try:
        h.read()
    except HeadingUnavailable:
        pass
    else:
        raise AssertionError("continuou a dar um rumo velho de 2 s")


def test_recupera_depois_da_falha():
    clock = FakeClock()
    drv = FakeDriver(yaw=30.0)
    h = RealHeading(drv, max_stale_s=0.5, clock=clock)
    h.read()
    drv.yaw = None
    clock.t = 0.2
    h.read()
    assert h.fail_count == 1

    drv.yaw = 60.0                 # sensor voltou
    clock.t = 0.4
    assert abs(h.read() - 60.0) < 1e-9
    assert h.fail_count == 0


def test_interface_igual_ao_simulado():
    """RealHeading tem de ser um drop-in de SimulatedHeading."""
    from control.sources import SimulatedHeading
    real = RealHeading(FakeDriver(yaw=0.0))
    sim = SimulatedHeading()
    assert callable(real.read) and callable(sim.read)
    assert isinstance(real.read(), float)
    assert isinstance(sim.read(), float)


def test_is_calibrated():
    assert RealHeading(FakeDriver(cal=(3, 3, 3, 3))).is_calibrated()
    assert not RealHeading(FakeDriver(cal=(2, 3, 3, 3))).is_calibrated()
    assert not RealHeading(FakeDriver(cal=(3, 3, 3, 2))).is_calibrated()


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
