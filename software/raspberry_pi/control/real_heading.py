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
  5. Pode dar UMA leitura absurda no meio de leituras boas. Observado na
     bancada de 2026-11-10: 23 -> 134 -> 25 graus a 5 Hz, ou seja, um salto
     de ~110 graus numa amostra que volta logo atras. Com calibracao 3/3,
     sem erro de I2C. No NAV isso seria um golpe de leme de uma amostra.

Politica desta classe: perante duvida, nao devolver numero. read() levanta
HeadingUnavailable em vez de inventar um rumo, e cabe ao chamador aplicar
o estado seguro -- tal como o main.py ja faz quando perde a serie.

O driver e injetado (parametro `driver`) para que os testes corram sem
hardware nenhum. Ver create_bno055() para o caso real.
"""

import json
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

# Taxa de rotacao maxima credivel para o barco, em graus/s. Um catamara de
# 80 cm com jatos diferenciais a 30% roda muito abaixo disto; o valor e
# folgado de proposito, porque o filtro existe para apanhar leituras
# fisicamente impossiveis (~550 graus/s observados), nao para alisar
# rotacoes reais. NAO e um valor medido -- rever quando houver ensaio na
# agua.
MAX_RATE_DPS = 180.0

# Intervalo minimo considerado entre leituras, para a taxa nao explodir
# quando duas leituras chegam quase ao mesmo tempo.
_MIN_DT_S = 0.02


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
      max_rate_dps     taxa de rotacao maxima credivel, em graus/s. Uma
                       leitura que implique rodar mais depressa do que isto
                       desde a ultima boa e posta de quarentena (ver read())
    """

    # Fonte real: o main.py so deixa o modo NAV comandar o ESP32 quando
    # todas as fontes tem SYNTHETIC False. Ver nav_guard() no main.py.
    SYNTHETIC = False

    def __init__(self, driver, mount_offset_deg=0.0,
                 declination_deg=DECLINATION_UNSET,
                 min_sys=3, min_mag=3, max_stale_s=0.5,
                 max_rate_dps=MAX_RATE_DPS, clock=time.monotonic):
        self.driver = driver
        self.mount_offset_deg = mount_offset_deg
        self.declination_deg = declination_deg
        self.min_sys = min_sys
        self.min_mag = min_mag
        self.max_stale_s = max_stale_s
        self.max_rate_dps = max_rate_dps
        self._clock = clock
        self._suspect = None        # ultima leitura posta de quarentena
        self._suspect_t = None
        self._rejected_total = 0
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

        if not self._plausible(heading, now):
            # Quarentena: esta leitura nao entra. Fica guardada para ser
            # confirmada (ou nao) pela proxima.
            self._suspect = heading
            self._suspect_t = now
            self._rejected_total += 1
            self._fail_count += 1
            # _plausible() so rejeita com uma leitura boa recente, portanto
            # devolve-la e seguro e e o mesmo que a falha transitoria faz.
            return self._last_good

        self._last_good = heading
        self._last_good_t = now
        self._suspect = None
        self._suspect_t = None
        self._fail_count = 0
        return heading

    def _rate_ok(self, a, b, dt):
        dt = max(dt, _MIN_DT_S)
        return abs(normalize_angle(a - b)) / dt <= self.max_rate_dps

    def _plausible(self, heading, now):
        """A leitura e fisicamente possivel face ao que se sabe?

        Aceita sempre que nao ha referencia recente: sem ultima leitura boa,
        ou com ela mais velha do que max_stale_s. Sem isto, depois de uma
        falha longa durante a qual o barco rodou de verdade, todas as
        leituras novas seriam rejeitadas para sempre.

        Rejeita um salto acima de max_rate_dps em relacao a ultima boa,
        A MENOS que a leitura anterior (a de quarentena) concorde com esta.
        Duas leituras seguidas coerentes entre si sao uma rotacao real e
        rapida (a mao na bancada, por exemplo); uma leitura isolada que nao
        concorda com nada, antes nem depois, e o defeito observado. O custo
        e uma amostra de atraso num salto real, e e so esse.
        """
        if self._last_good is None or self._last_good_t is None:
            return True
        if now - self._last_good_t > self.max_stale_s:
            return True
        if self._rate_ok(heading, self._last_good, now - self._last_good_t):
            return True
        if (self._suspect is not None and self._suspect_t is not None
                and self._rate_ok(heading, self._suspect,
                                  now - self._suspect_t)):
            return True
        return False

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

    @property
    def rejected_total(self):
        """Leituras postas de quarentena desde o arranque (saltos impossiveis)."""
        return self._rejected_total

    # -- persistencia da calibracao --------------------------------------

    def save_calibration(self, path):
        """Grava os offsets de calibracao do sensor num JSON.

        So grava com os quatro contadores a 3. Offsets de uma calibracao
        incompleta seriam carregados no arranque seguinte como se fossem
        bons, e o sensor partiria de um ponto errado sem nada o dizer.
        """
        cal = self.calibration()
        if tuple(cal) != (3, 3, 3, 3):
            raise ValueError(f"calibracao incompleta {tuple(cal)}: "
                             "so se grava com 3333")
        d = self.driver
        data = {
            "sensor": "BNO055",
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "offsets_accelerometer": list(d.offsets_accelerometer),
            "offsets_gyroscope": list(d.offsets_gyroscope),
            "offsets_magnetometer": list(d.offsets_magnetometer),
            "radius_accelerometer": int(d.radius_accelerometer),
            "radius_magnetometer": int(d.radius_magnetometer),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data

    def load_calibration(self, path):
        """Carrega no sensor os offsets gravados por save_calibration().

        Valida tudo ANTES de escrever no sensor: um ficheiro mal formado
        levanta ValueError e o sensor fica como estava. Nao muda a politica
        de leitura -- o read() continua a exigir sys e mag a 3.

        ATENCAO: o gate nao protege contra offsets errados. Medido na
        bancada (2026-11-10): depois de carregar, o sensor reportou 3333 em
        ~1 s, sem movimento nenhum, e deu rumo. O sensor confia nos offsets
        que recebe; se forem de outra placa ou de outra montagem, o rumo
        sai plausivel e errado e nenhum contador o denuncia. So carregar
        offsets gravados na mesma montagem.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        vals = {}
        for k in ("offsets_accelerometer", "offsets_gyroscope",
                  "offsets_magnetometer"):
            v = data.get(k)
            if (not isinstance(v, list) or len(v) != 3
                    or not all(_is_int16(x) for x in v)):
                raise ValueError(f"{k} invalido em {path}: {v!r}")
            vals[k] = tuple(v)
        for k in ("radius_accelerometer", "radius_magnetometer"):
            v = data.get(k)
            if not _is_int16(v):
                raise ValueError(f"{k} invalido em {path}: {v!r}")
            vals[k] = v
        d = self.driver
        d.offsets_accelerometer = vals["offsets_accelerometer"]
        d.offsets_gyroscope = vals["offsets_gyroscope"]
        d.offsets_magnetometer = vals["offsets_magnetometer"]
        d.radius_accelerometer = vals["radius_accelerometer"]
        d.radius_magnetometer = vals["radius_magnetometer"]
        return data


def _is_int16(x):
    return (isinstance(x, int) and not isinstance(x, bool)
            and -32768 <= x <= 32767)


# Enderecos possiveis do BNO055. O pino ADD do modulo escolhe entre os dois:
# a GND da 0x28, a VDD da 0x29. Deixado ao ar, NAO da erro -- da um endereco
# indefinido, e o sensor aparece e desaparece do barramento.
ADDRESS_ADD_LOW = 0x28
ADDRESS_ADD_HIGH = 0x29


def create_bno055(i2c=None, address=ADDRESS_ADD_LOW, **kwargs):
    """Constroi um RealHeading ligado ao BNO055 fisico.

    O import fica aqui dentro de proposito: control/real_heading.py tem de
    poder ser importado (e testado) numa maquina sem adafruit-blinka
    instalado. Nada em cima depende de hardware.

    O `address` existe porque o endereco e uma propriedade da CABLAGEM e nao
    do sensor: depende de a que ficou preso o pino ADD do modulo. Com 0x28
    por omissao, que e o que o projeto usa (ADD a GND), mas passavel sem
    ter de mexer no ficheiro quando a placa estiver ligada ao contrario.

    Requer, no Pi:  pip install adafruit-circuitpython-bno055
    e o barramento I2C configurado. Ver secao 22.7 do documento de
    arquitetura -- alem de `dtparam=i2c_arm=on`, este sensor exige
    `dtparam=i2c_arm_baudrate=10000` no config.txt, porque usa clock
    stretching e o controlador do Broadcom trata isso mal: em vez de erro,
    da leituras corrompidas.
    """
    import board                      # noqa: PLC0415
    import adafruit_bno055            # noqa: PLC0415

    if i2c is None:
        i2c = board.I2C()
    sensor = adafruit_bno055.BNO055_I2C(i2c, address=address)
    return RealHeading(sensor, **kwargs)
