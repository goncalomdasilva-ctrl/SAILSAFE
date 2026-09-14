"""Leitura de tensoes e corrente a bordo (sense do ADS1015).

Implementa o documento hardware/electrical/SAILSAFE_sense_v1_11_1.md. O
driver do conversor esta em sensors/ads1015.py; aqui sabe-se o que esta
ligado a cada canal e como transformar volts a entrada do ADC em volts de
bateria e amperes de casco.

Atribuicao dos canais (sense v1.11.1, rev 2):

    A0  tensao do casco esquerdo      divisor 10k/2k
    A1  tensao do casco direito       divisor 10k/2k
    A2  tensao da bateria da eletronica (3S 2200)   divisor 10k/2k
    A3  corrente do casco esquerdo    ACS758-050U

Tres decisoes que valem a pena ficar escritas:

  * Um canal que nao existe devolve None, nunca 0. Hoje o ACS758 ainda
    nao foi comprado e o A3 esta por ligar. Um zero seria indistinguivel
    de "casco parado, sem consumo" -- exatamente a leitura que se espera
    ver num barco a deriva. Ausencia tem de se ler como ausencia.

  * Sem calibracao nao se decide nada. O erro dominante sao os resistores
    (+-1,09 V a 12,6 V com tolerancia de 5 %), nao o conversor (12 mV de
    resolucao). As leituras continuam a ser produzidas para a bancada,
    mas vem marcadas como nao calibradas, e o BatteryGuard recusa-se a
    disparar um regresso com base nelas.

  * Tensao quase nula num canal de casco nao e avaria: e a loop key fora.
    A propriedade "0 V = casco desarmado" e do desenho eletrico e vale a
    pena ser lida como estado, e nao como falha de sensor.
"""

import json
import os
from collections import namedtuple

from sensors.ads1015 import SenseSaturated, SenseUnavailable

# --- constantes do hardware --------------------------------------------

# Divisor 10k / 2k: k = 1/6. O par mudou de 5k/1k para 10k/2k na revisao 3
# do documento de sense (foi o que havia em stock) e ESTE NUMERO NAO MUDOU:
# 2/(10+2) e o mesmo 1/6 que 1/(5+1). O que mudou foi a impedancia de fonte,
# que nao entra em conta nenhuma feita aqui. O valor real de cada divisor sai
# da calibracao; este e so o ponto de partida.
DIVIDER_RATIO = 1.0 / 6.0

# ACS758-050U: Hall, isolado, unidirecional 0-50 A.
ACS758_OFFSET_V = 0.600
ACS758_V_PER_A = 0.060

# Abaixo disto (referido a bateria) o circuito esta sem alimentacao.
# 1 V nao e nenhuma bateria possivel e e muito acima do ruido do divisor.
UNPOWERED_V = 1.0

CalibrationDefaults = {"a0": 1.0, "a1": 1.0, "a2": 1.0, "a3": 1.0}

Channel = namedtuple("Channel", "index name kind cells installed")

CHANNELS = (
    Channel(0, "casco_esq", "voltage", 3, True),
    Channel(1, "casco_dir", "voltage", 3, True),
    Channel(2, "eletronica", "voltage", 3, True),
    # O ACS758 ainda nao existe. Passar installed=True quando estiver
    # ligado -- e nao antes, para nao haver um zero a fingir de medicao.
    Channel(3, "corrente_esq", "current", None, False),
)


class Reading(namedtuple("Reading", "name kind value unit calibrated note")):
    """Uma leitura de um canal. value=None significa que nao ha medicao."""

    @property
    def available(self):
        return self.value is not None


class PowerSense:
    """Tensoes e correntes de bordo, a partir de um ADS1015.

    Parametros:
      adc           objeto com read_volts(canal) (sensors.ads1015.ADS1015
                    ou um falso, nos testes)
      calibration   dict {"a0": fator, ...}. None carrega do ficheiro.
      channels      permite descrever outra cablagem sem tocar no codigo
      config_path   ficheiro de calibracao (JSON)
    """

    def __init__(self, adc, calibration=None, channels=CHANNELS,
                 config_path=None):
        self.adc = adc
        self.channels = tuple(channels)
        self.config_path = config_path
        if calibration is None:
            calibration, self.calibrated = load_calibration(config_path)
        else:
            self.calibrated = True
        self.calibration = dict(CalibrationDefaults, **calibration)

    # -- conversoes ------------------------------------------------------

    def _scale(self, index):
        return float(self.calibration.get(f"a{index}", 1.0))

    def _to_battery_volts(self, v_adc, index):
        return v_adc / DIVIDER_RATIO * self._scale(index)

    def _to_amps(self, v_adc, index):
        return (v_adc - ACS758_OFFSET_V) / ACS758_V_PER_A * self._scale(index)

    # -- leitura ---------------------------------------------------------

    def read_channel(self, channel):
        """Le um canal e devolve uma Reading.

        Nunca levanta por causa do sensor: um canal em falta, saturado ou
        sem resposta e informacao a registar, nao motivo para derrubar o
        ciclo de controlo. Quem precisar de decidir com isto olha para
        Reading.available e para BatteryGuard.
        """
        if not channel.installed:
            unidade = "V" if channel.kind == "voltage" else "A"
            return Reading(channel.name, channel.kind, None, unidade,
                           self.calibrated, "canal nao instalado")

        unidade = "V" if channel.kind == "voltage" else "A"
        try:
            v_adc = self.adc.read_volts(channel.index)
        except SenseSaturated as e:
            return Reading(channel.name, channel.kind, None, unidade,
                           self.calibrated, f"saturado: {e}")
        except SenseUnavailable as e:
            return Reading(channel.name, channel.kind, None, unidade,
                           self.calibrated, f"sem leitura: {e}")

        if channel.kind == "voltage":
            valor = self._to_battery_volts(v_adc, channel.index)
            nota = "circuito sem alimentacao" if valor < UNPOWERED_V else ""
        else:
            valor = self._to_amps(v_adc, channel.index)
            # O ACS758 e ratiometrico ao seu proprio 5 V e o ADS1015 mede
            # contra referencia interna: uma quebra do rail desvia isto e
            # nao ha canal livre para a corrigir (OPEN-012).
            nota = "sem compensacao do rail de 5 V"
            if valor < 0:
                # Unidirecional: corrente negativa e offset por calibrar,
                # nao corrente ao contrario.
                nota = "negativa: offset do ACS758 por calibrar"
        return Reading(channel.name, channel.kind, valor, unidade,
                       self.calibrated, nota)

    def read_all(self):
        """Dict nome -> Reading, para todos os canais descritos."""
        return {c.name: self.read_channel(c) for c in self.channels}

    def electronics_volts(self):
        """Tensao da bateria da eletronica, ou None se nao houver leitura.

        E este o canal que serve de gatilho de regresso: a bateria da
        eletronica esgota-se ao relogio e nao ao andar, e quando se
        esgotar perdem-se radio, registo e controlo ao mesmo tempo.
        """
        for c in self.channels:
            if c.name == "eletronica":
                return self.read_channel(c).value
        return None

    def per_cell(self, reading):
        """Volts por celula, para a leitura dada. None se nao se aplicar."""
        canal = self.channel_by_name(reading.name)
        if canal is None or not canal.cells or not reading.available:
            return None
        return reading.value / canal.cells

    def channel_by_name(self, name):
        for c in self.channels:
            if c.name == name:
                return c
        return None


# --- calibracao ---------------------------------------------------------

def default_config_path():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(raiz, "config", "calibration.json")


def load_calibration(path=None):
    """Devolve (dict de fatores, calibrado?).

    Sem ficheiro devolve fatores de 1,0 e False. Nao levanta: uma bancada
    sem calibracao ainda mede, so nao decide. Quem decide -- o
    BatteryGuard -- e que exige o segundo valor a True.
    """
    if path is None:
        path = default_config_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (FileNotFoundError, ValueError, OSError):
        return dict(CalibrationDefaults), False

    fatores = {}
    for chave, valor in dados.items():
        if chave.startswith("a") and isinstance(valor, (int, float)):
            fatores[chave] = float(valor)
    return dict(CalibrationDefaults, **fatores), bool(fatores)


def save_calibration(factors, path=None):
    """Escreve os fatores em JSON, criando a pasta se for preciso."""
    if path is None:
        path = default_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(factors, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def factor_from_measurement(measured_v, reported_v):
    """Fator de escala de um ponto: o que o multimetro diz a dividir pelo
    que o canal reportou com fator 1,0.

    Um ponto chega porque o erro dominante e de ganho (tolerancia dos
    resistores), nao de offset: o divisor passa pela origem.
    """
    if reported_v == 0:
        raise ValueError("leitura reportada igual a zero: nao ha ganho a corrigir")
    return float(measured_v) / float(reported_v)
