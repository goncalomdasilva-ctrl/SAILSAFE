"""Ponto de regresso do SAILSAFE.

O ponto de regresso e a posicao para onde o barco volta quando a missao
aborta -- por bateria da eletronica, por perda de rumo, ou por ordem do
operador. E a unica coordenada do sistema que nao pode estar errada: um
waypoint mal posto faz o barco passar ao lado; um ponto de regresso mal
posto manda-o para longe de quem o pode ir buscar.

Politica desta classe, e a razao de cada parte:

  * MEDIA DE VARIOS FIXES, NAO UM. A dispersao medida a 15 de setembro
    diz que o receptor e preciso ao segundo (~30 cm em 10 s) e arrasta-se
    ao longo dos minutos. Uma janela curta de fixes seguidos cai no lado
    bom desse comportamento: a media de N fixes de poucos segundos tira o
    ruido sem ter tempo de apanhar a deriva.

  * SO FIXES VALIDADOS. As amostras entram por quem ja passou pelos
    criterios do RealPosition (satelites, HDOP, ilha nula). Esta classe
    nao repete esses criterios -- repeti-los seria ter duas politicas de
    aceitacao a divergir com o tempo.

  * AMOSTRAS COM PRAZO. Um fix de ha cinco minutos nao descreve onde o
    barco esta agora. As amostras velhas saem da janela, e se a janela
    ficar vazia o ponto nao se grava.

  * DISPERSAO E CRITERIO, NAO ORNAMENTO. Se as N amostras estiverem
    espalhadas por mais do que max_spread_m, a media delas nao e uma
    posicao -- e o centro de uma nuvem. Nesse caso recusa-se a gravar e
    diz-se porque. Falhar aqui e recusar armar, que e o lado seguro.

  * GRAVA UMA VEZ E NAO SE REESCREVE. Depois de gravado, nenhum caminho
    automatico lhe toca. Um ponto de regresso que se atualiza sozinho
    segue o barco: quando fosse preciso, apontaria para onde o barco ja
    esta, e nao para onde o operador ficou. Regravar existe, mas e um
    gesto explicito -- reset() --, a mesma regra da trava do ESP32 e da
    guarda de bateria.

Nota sobre a media: a esta escala a media aritmetica de latitudes e
longitudes chega perfeitamente (dezenas de metros, longe dos polos e da
linha de mudanca de data). Nao serve para pontos separados por centenas
de quilometros, e nao e para isso que existe.
"""

import time
from collections import namedtuple

from control.navigation import haversine_m

DEFAULT_MIN_FIXES = 5
DEFAULT_WINDOW_S = 15.0
DEFAULT_MAX_SPREAD_M = 5.0

Sample = namedtuple("Sample", "lat lon t")
Point = namedtuple("Point", "lat lon fixes spread_m t")


class ReturnPointUnavailable(Exception):
    """Nao ha material para gravar um ponto de regresso de confianca."""


class ReturnPoint:
    """Guarda a posicao de regresso, gravada uma vez no ARM.

    Parametros:
      min_fixes      amostras validas exigidas na janela antes de gravar.
                     Cinco, a 1 Hz, sao cinco segundos de receptor parado
      window_s       idade maxima de uma amostra. Acima disto sai da
                     janela: descreve onde o barco esteve, nao onde esta
      max_spread_m   distancia maxima de qualquer amostra ao centro. Acima
                     disto a media nao e uma posicao. PROVISORIO: sai da
                     dispersao medida ao parapeito (~30 cm em 10 s de
                     curto prazo), que e o melhor numero que ha hoje, e
                     fica por refazer em agua aberta com o barco montado
      clock          relogio monotonico, injetavel
    """

    def __init__(self, min_fixes=DEFAULT_MIN_FIXES, window_s=DEFAULT_WINDOW_S,
                 max_spread_m=DEFAULT_MAX_SPREAD_M, clock=time.monotonic):
        if min_fixes < 1:
            raise ValueError("min_fixes tem de ser pelo menos 1")
        self.min_fixes = min_fixes
        self.window_s = window_s
        self.max_spread_m = max_spread_m
        self._clock = clock
        self._samples = []
        self._point = None

    # -- recolha ---------------------------------------------------------

    def feed(self, lat, lon):
        """Junta uma amostra a janela. Espera um fix JA validado.

        Continua a aceitar amostras depois de o ponto estar gravado: a
        janela serve tambem para saber se, no momento do ARM, havia
        receptor a funcionar. O que nao acontece e o ponto mudar.
        """
        agora = self._clock()
        self._samples.append(Sample(lat, lon, agora))
        self._prune(agora)

    def _prune(self, agora=None):
        if agora is None:
            agora = self._clock()
        limite = agora - self.window_s
        self._samples = [s for s in self._samples if s.t >= limite]

    @property
    def samples(self):
        """As amostras dentro da janela, ja sem as que expiraram."""
        self._prune()
        return list(self._samples)

    # -- gravacao --------------------------------------------------------

    def _mean(self, amostras):
        n = float(len(amostras))
        return (sum(s.lat for s in amostras) / n,
                sum(s.lon for s in amostras) / n)

    def _spread(self, amostras, lat, lon):
        """Distancia da amostra mais afastada ao centro, em metros."""
        return max(haversine_m(lat, lon, s.lat, s.lon) for s in amostras)

    def _evaluate(self):
        """(lat, lon, n, spread) da janela atual, ou levanta.

        Uma so politica de aceitacao, para dois chamadores: o check(), que
        pergunta, e o record(), que grava. Duas copias da mesma regra
        divergem assim que uma delas for mexida.
        """
        amostras = self.samples
        if len(amostras) < self.min_fixes:
            raise ReturnPointUnavailable(
                f"{len(amostras)} fixes validos nos ultimos "
                f"{self.window_s:.0f} s (minimo {self.min_fixes})")
        lat, lon = self._mean(amostras)
        spread = self._spread(amostras, lat, lon)
        if spread > self.max_spread_m:
            raise ReturnPointUnavailable(
                f"fixes espalhados por {spread:.1f} m "
                f"(maximo {self.max_spread_m:.1f} m)")
        return lat, lon, len(amostras), spread

    def check(self):
        """(pode gravar?, motivo). Nao grava nada.

        Existe por causa de uma ordem que nao e detalhe: quem arma quer
        saber se ha ponto de regresso ANTES de destravar a propulsao no
        ESP32 -- a condicao mais barata deve falhar primeiro --, mas so
        deve GRAVAR o ponto se o ARM chegar mesmo ao fim. Um ARM recusado
        a meio que deixasse o ponto gravado fixava o regresso num sitio
        onde o barco nunca chegou a ficar armado, e como o ponto nao se
        reescreve, ficava assim para a sessao inteira.
        """
        if self._point is not None:
            return True, "ja gravado"
        try:
            self._evaluate()
        except ReturnPointUnavailable as e:
            return False, str(e)
        return True, ""

    def preview(self):
        """(lat, lon, n, spread_m) do que seria gravado agora, ou None."""
        try:
            return self._evaluate()
        except ReturnPointUnavailable:
            return None

    def record(self):
        """Grava o ponto de regresso a partir da janela atual.

        Devolve o Point gravado. Com o ponto ja gravado devolve-o
        inalterado -- e a regra do "grava uma vez": um segundo ARM na
        mesma sessao nao mexe no ponto, e quem quiser outro chama reset().

        Levanta ReturnPointUnavailable se faltarem amostras ou se elas
        estiverem espalhadas por mais do que max_spread_m.
        """
        if self._point is not None:
            return self._point
        lat, lon, n, spread = self._evaluate()
        self._point = Point(lat, lon, n, spread, self._clock())
        return self._point

    def reset(self):
        """Apaga o ponto gravado. Gesto explicito, nunca automatico.

        A janela de amostras fica, porque continua a descrever onde o
        barco esta -- o que se apaga e a decisao, nao a medicao.
        """
        self._point = None

    # -- consulta --------------------------------------------------------

    @property
    def is_set(self):
        return self._point is not None

    @property
    def point(self):
        """O Point gravado, ou None. Nunca inventa um a partir da janela."""
        return self._point

    def position(self):
        """(lat, lon) do ponto gravado.

        Levanta ReturnPointUnavailable se nao houver ponto. Nao devolve a
        posicao atual como substituto: regressar para onde ja se esta nao
        e regressar, e quem chama tem de saber a diferenca.
        """
        if self._point is None:
            raise ReturnPointUnavailable("ponto de regresso por gravar")
        return self._point.lat, self._point.lon

    def distance_from(self, lat, lon):
        """Metros entre (lat, lon) e o ponto de regresso."""
        p_lat, p_lon = self.position()
        return haversine_m(lat, lon, p_lat, p_lon)

    def describe(self):
        """Uma linha para o ecra e para o log."""
        if self._point is None:
            amostras = len(self.samples)
            return (f"por gravar ({amostras}/{self.min_fixes} fixes na janela "
                    f"de {self.window_s:.0f} s)")
        p = self._point
        return (f"{p.lat:.6f}, {p.lon:.6f} "
                f"({p.fixes} fixes, dispersao {p.spread_m:.1f} m)")
