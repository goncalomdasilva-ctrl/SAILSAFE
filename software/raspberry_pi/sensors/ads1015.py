"""Driver do ADS1015 (ADC I2C de 12 bit, 4 canais).

Este ficheiro so fala com o conversor. A interpretacao do que cada canal
mede -- divisores, sensor de corrente, calibracao -- esta em
sensors/power_sense.py, de proposito: o que esta aqui depende do chip e o
que esta la depende da cablagem, e as duas coisas mudam em alturas
diferentes.

Duas regras desenhadas a partir do documento de sense v1.11.1:

  1. O PGA e escrito a cada conversao, e nao uma vez no arranque.
     O ADS1015 nao tem memoria: qualquer reset -- brownout, cabo de I2C
     tocado, alimentacao a oscilar quando o ESC arranca -- devolve-o ao
     ganho por omissao de +-2,048 V. Com os divisores de 10k/2k, esse
     ganho satura a 12,29 V referidos a bateria, ou seja, ABAIXO de uma
     3S carregada. A leitura continua a ser um numero plausivel: nao da
     erro, nao acende nada, so mente. Como cada conversao e single-shot e
     ja exige uma escrita ao registo de configuracao, reafirmar o ganho
     nessa escrita nao custa nada e fecha o buraco.

  2. Saturacao NAO e um valor. Uma contagem no topo da escala nao quer
     dizer "muita tensao", quer dizer "esta tensao esta fora do que eu
     consigo medir". Devolver 24,6 V a quem pediu seria transformar a
     ausencia de medicao numa medicao -- o mesmo erro do ack antigo do
     STOP, que aceitava um resto do buffer como confirmacao. read_volts()
     levanta SenseSaturated e cabe ao chamador decidir.

Requer, no Pi:  pip install smbus2
e o I2C ligado (raspi-config -> Interface Options -> I2C).
"""

import time

ADDRESS_DEFAULT = 0x48       # ADDR a GND. 0x49 VDD, 0x4A SDA, 0x4B SCL.

REG_CONVERSION = 0x00
REG_CONFIG = 0x01

# --- campos do registo de configuracao ---------------------------------
OS_SINGLE = 0x8000           # comecar uma conversao
MODE_SINGLE_SHOT = 0x0100
DR_1600SPS = 0x0080          # 625 us por conversao
COMP_DISABLE = 0x0003        # comparador desligado

# MUX, entradas simples referidas a GND
MUX_SINGLE = {0: 0x4000, 1: 0x5000, 2: 0x6000, 3: 0x7000}

# PGA. O nome do fundo de escala e o valor do campo.
GAIN_6144 = 0x0000
GAIN_4096 = 0x0200           # <= o unico admissivel neste projeto
GAIN_2048 = 0x0400           # omissao do chip; satura com os nossos divisores
GAIN_1024 = 0x0600
GAIN_0512 = 0x0800
GAIN_0256 = 0x0A00

FULL_SCALE_V = {
    GAIN_6144: 6.144,
    GAIN_4096: 4.096,
    GAIN_2048: 2.048,
    GAIN_1024: 1.024,
    GAIN_0512: 0.512,
    GAIN_0256: 0.256,
}

# O ADS1015 da 12 bit com sinal: -2048 a 2047.
COUNTS_FULL_SCALE = 2048
SATURATION_COUNTS = 2047


class SenseUnavailable(Exception):
    """O canal nao deu leitura. O chamador deve tratar como ausencia."""


class SenseSaturated(SenseUnavailable):
    """A entrada esta no topo da escala: fora do que o ADC mede.

    E subclasse de SenseUnavailable de proposito. Quem so quiser saber
    "tenho numero ou nao" apanha as duas com um except; quem quiser
    distinguir "nao respondeu" de "esta acima do fundo de escala" -- que e
    quase sempre erro de divisor ou de ganho, nao do sensor -- apanha esta.
    """


class ADS1015:
    """Conversor ADS1015 lido canal a canal, em modo single-shot.

    Parametros:
      bus       objeto no estilo do smbus2 (write_i2c_block_data /
                read_i2c_block_data). Injetado para os testes correrem sem
                I2C nenhum.
      address   endereco I2C (0x48 com ADDR a GND)
      gain      campo do PGA. So GAIN_4096 passa sem aviso: ver a regra 1
                no topo do ficheiro.
      clock     relogio monotonico, injetavel para testes instantaneos
      sleep     espera, injetavel pela mesma razao
    """

    def __init__(self, bus, address=ADDRESS_DEFAULT, gain=GAIN_4096,
                 data_rate=DR_1600SPS, clock=time.monotonic, sleep=time.sleep,
                 conversion_timeout_s=0.05):
        if gain not in FULL_SCALE_V:
            raise ValueError(f"ganho desconhecido: {gain:#06x}")
        self.bus = bus
        self.address = address
        self.gain = gain
        self.data_rate = data_rate
        self._clock = clock
        self._sleep = sleep
        self.conversion_timeout_s = conversion_timeout_s

    # -- conversao -------------------------------------------------------

    @property
    def full_scale_v(self):
        return FULL_SCALE_V[self.gain]

    @property
    def lsb_v(self):
        """Tensao de um bit. 2,000 mV no fundo de escala de +-4,096 V."""
        return self.full_scale_v / COUNTS_FULL_SCALE

    def _config_word(self, channel):
        if channel not in MUX_SINGLE:
            raise ValueError(f"canal fora de 0-3: {channel}")
        return (OS_SINGLE | MUX_SINGLE[channel] | self.gain
                | MODE_SINGLE_SHOT | self.data_rate | COMP_DISABLE)

    def _write_config(self, word):
        self.bus.write_i2c_block_data(self.address, REG_CONFIG,
                                      [(word >> 8) & 0xFF, word & 0xFF])

    def _read_register(self, register):
        hi, lo = self.bus.read_i2c_block_data(self.address, register, 2)
        return (hi << 8) | lo

    def _wait_ready(self):
        """Espera pelo bit OS a 1 (conversao terminada).

        Sondar em vez de dormir um tempo fixo apanha de graca o barramento
        morto: sem resposta, o timeout dispara e o erro diz o que se
        passou, em vez de se ler lixo de um registo que nunca mudou.
        """
        limite = self._clock() + self.conversion_timeout_s
        while True:
            if self._read_register(REG_CONFIG) & OS_SINGLE:
                return
            if self._clock() >= limite:
                raise SenseUnavailable(
                    f"conversao nao terminou em {self.conversion_timeout_s * 1e3:.0f} ms")
            self._sleep(0.0002)

    def read_counts(self, channel):
        """Contagens cruas com sinal, -2048 a 2047.

        Levanta SenseUnavailable se o I2C falhar. Nao deteta saturacao --
        isso e trabalho do read_volts(), porque so ai se sabe que a
        contagem ia ser convertida em tensao e usada como se fosse uma.
        """
        try:
            self._write_config(self._config_word(channel))
            self._wait_ready()
            bruto = self._read_register(REG_CONVERSION)
        except OSError as e:
            raise SenseUnavailable(f"I2C falhou no canal A{channel}: {e}") from e

        valor = bruto >> 4                      # 12 bit alinhados a esquerda
        if valor & 0x800:                       # complemento para dois
            valor -= 0x1000
        return valor

    def read_volts(self, channel):
        """Tensao a entrada do ADC, em volts.

        Levanta SenseSaturated se a contagem estiver no topo da escala.
        Isto nao e zelo: com os divisores de 10k/2k e o ganho por omissao
        de +-2,048 V, toda a zona util de descarga de uma 3S le saturado e
        a bateria parece cheia ate ja ir a meio.
        """
        contagens = self.read_counts(channel)
        if abs(contagens) >= SATURATION_COUNTS:
            raise SenseSaturated(
                f"A{channel} no topo da escala ({contagens} contagens, "
                f"FSR +-{self.full_scale_v:.3f} V). "
                "Entrada acima do fundo de escala ou PGA errado.")
        return contagens * self.lsb_v


def create_ads1015(bus_number=1, address=ADDRESS_DEFAULT, **kwargs):
    """Constroi um ADS1015 ligado ao barramento fisico.

    O import fica aqui dentro para que sensors/ads1015.py possa ser
    importado e testado numa maquina sem smbus2 e sem I2C.

    Requer, no Pi:  pip install smbus2
    """
    from smbus2 import SMBus                    # noqa: PLC0415

    return ADS1015(SMBus(bus_number), address=address, **kwargs)
