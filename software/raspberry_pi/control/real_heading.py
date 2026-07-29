"""Leitura de rumo REAL a partir do BNO055 (I2C).

Substitui SimulatedHeading mantendo a mesma interface read(). Tudo o que
esta classe tem a mais existe porque a fonte simulada nunca falha e o
sensor real falha de quatro maneiras:

  1. Pode nao estar calibrado. O magnetometro so converge depois de
     movimento. Uma leitura mal calibrada NAO da erro: da um numero
     plausivel e errado, que e pior do que nao dar numero nenhum.
  2. Pode nao responder (timeout de I2C, cabo solto, alimentacao em falta).
  3. Da o norte MAGNETICO; o bearing_deg de navigation.py usa o norte
     VERDADEIRO. A diferenca (declinacao) e erro sistematico: nao
     desaparece com medias nem com mais amostras.
  4. Da o rumo da PLACA, nao o da proa. Depende de como o sensor ficou
     montado.

Politica desta classe: perante duvida, nao devolver numero. read() levanta
HeadingUnavailable em vez de inventar um rumo, e cabe ao chamador aplicar
o estado seguro -- tal como o main.py ja faz quando perde a serie.

O driver e injetado (parametro `driver`) para que os testes corram sem
hardware nenhum. Ver create_bno055() para o caso real.
"""

import time
from collections import namedtuple

from control.heading import normalize_angle


class HeadingUnavailable(Exception):
    """Nao ha rumo fiavel disponivel. O chamador deve ir para estado seguro."""


# Os quatro contadores de calibracao do BNO055, cada um de 0 a 3.
Calibration = namedtuple("Calibration", "sys gyro accel mag")

# Declinacao magnetica: soma-se ao rumo magnetico para obter o verdadeiro.
# Positiva a Este, negativa a Oeste. Lisboa esta na ordem de -2 graus, mas
# NAO deixar este valor por adivinhar: consultar a calculadora da NOAA/NCEI
# para a data e coordenadas do ensaio e passar o valor no construtor.
DECLINATION_UNSET = 0.0


class RealHeading:
    """Rumo do barco medido pelo BNO055.

    Mesma interface que SimulatedHeading: read() devolve graus. O intervalo
    e (-180, 180], igual ao do simulado, para ser mesmo um drop-in -- o
    heading_error() normaliza a diferenca, portanto a convencao escolhida
    nao altera o controlador.

    Parametros:
      driver           objeto com .euler e .calibration_status (BNO055_I2C
                       da Adafruit, ou um falso nos testes)
      mount_offset_deg graus a somar por causa da orientacao da placa no
                       barco (0 = eixo X do sensor aponta para a proa)
      declination_deg  declinacao magnetica local (magnetico -> verdadeiro)
      min_sys/min_mag  calibracao minima exigida para dar leitura por boa
      max_stale_s      tolerancia a falhas transitorias: perante uma leitura
                       falhada devolve a ultima boa se for mais nova do que
                       isto; caso contrario levanta HeadingUnavailable
    """

    def __init__(self, driver, mount_offset_deg=0.0,
                 declination_deg=DECLINATION_UNSET,
                 min_sys=3, min_mag=3, max_stale_s=0.5, clock=time.monotonic):
        self.driver = driver
        self.mount_offset_deg = mount_offset_deg
        self.declination_deg = declination_deg
        self.min_sys = min_sys
        self.min_mag = min_mag
        self.max_stale_s = max_stale_s
        self._clock = clock
        self._last_good = None      # rumo ja corrigido
        self._last_good_t = None
        self._fail_count = 0

    # -- calibracao ------------------------------------------------------

    def calibration(self):
        """Devolve Calibration(sys, gyro, accel, mag), cada campo 0-3.

        Se o sensor nao responder devolve tudo a zero, que e o mesmo que
        dizer "nao calibrado" -- o lado conservador.
        """
        try:
            s, g, a, m = self.driver.calibration_status
        except (OSError, TypeError, ValueError):
            return Calibration(0, 0, 0, 0)
        return Calibration(s or 0, g or 0, a or 0, m or 0)

    def is_calibrated(self):
        """True quando a calibracao chega ao minimo exigido para navegar."""
        c = self.calibration()
        return c.sys >= self.min_sys and c.mag >= self.min_mag

    # -- leitura ---------------------------------------------------------

    def _read_raw(self):
        """Rumo magnetico cru da placa, ou None se o sensor nao der numero.

        O driver da Adafruit devolve None (ou tuplos com None dentro)
        enquanto a fusao nao tem solucao. Isso nao e excecao, e ausencia
        de dados, e tem de ser tratado como tal.
        """
        try:
            euler = self.driver.euler
        except OSError:
            return None
        if not euler:
            return None
        yaw = euler[0]
        if yaw is None:
            return None
        return float(yaw)

    def read(self):
        """Rumo verdadeiro do barco, em graus (-180, 180].

        Levanta HeadingUnavailable se o sensor nao responder, se a fusao
        ainda nao tiver solucao ou se a calibracao estiver abaixo do
        minimo. Nunca devolve um valor de conveniencia.
        """
        now = self._clock()
        raw = self._read_raw()

        if raw is None or not self.is_calibrated():
            self._fail_count += 1
            # Falha transitoria: a ultima leitura boa ainda serve.
            if (self._last_good is not None and self._last_good_t is not None
                    and now - self._last_good_t <= self.max_stale_s):
                return self._last_good
            motivo = "sem resposta do sensor" if raw is None else \
                     f"calibracao insuficiente {tuple(self.calibration())}"
            raise HeadingUnavailable(motivo)

        heading = normalize_angle(raw + self.mount_offset_deg
                                  + self.declination_deg)
        self._last_good = heading
        self._last_good_t = now
        self._fail_count = 0
        return heading

    def read_or_none(self):
        """Como read(), mas devolve None em vez de levantar.

        Para o script de bancada, onde uma falha e informacao a mostrar no
        ecra e nao um motivo para abortar.
        """
        try:
            return self.read()
        except HeadingUnavailable:
            return None

    @property
    def fail_count(self):
        """Leituras falhadas seguidas desde a ultima boa."""
        return self._fail_count


def create_bno055(i2c=None, **kwargs):
    """Constroi um RealHeading ligado ao BNO055 fisico.

    O import fica aqui dentro de proposito: control/real_heading.py tem de
    poder ser importado (e testado) numa maquina sem adafruit-blinka
    instalado. Nada em cima depende de hardware.

    Requer, no Pi:  pip install adafruit-circuitpython-bno055
    e o I2C ligado (raspi-config -> Interface Options -> I2C).
    """
    import board                      # noqa: PLC0415
    import adafruit_bno055            # noqa: PLC0415

    if i2c is None:
        i2c = board.I2C()
    sensor = adafruit_bno055.BNO055_I2C(i2c)
    return RealHeading(sensor, **kwargs)
