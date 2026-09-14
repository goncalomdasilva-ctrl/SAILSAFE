"""Gatilho de regresso pela tensao da bateria da eletronica.

O canal A2 do ADS1015 nao e um mostrador. E o unico aviso que o barco tem
de que esta prestes a perder radio, registo e controlo ao mesmo tempo --
que e a falha mais grave possivel, porque deixa o barco a deriva e sem
posicao conhecida. O esgotamento da propulsao, em comparacao, deixa o
barco parado mas localizavel.

Politica desta classe, e a razao de cada parte:

  * LATCHING. Uma vez decidido o regresso, nao ha volta atras sem alguem
    chamar reset(). Uma bateria descarregada recupera tensao assim que a
    carga alivia: com os motores a 0 a leitura sobe, o limiar deixa de
    estar violado e a missao recomecava -- e voltava a cair. O barco
    ficaria a oscilar entre abortar e continuar, cada vez com menos
    energia. E a mesma regra da trava de propulsao do ESP32: nenhum
    caminho leva de "parado por falha" a "a andar" sem passar por uma
    decisao explicita.

  * DEBOUNCE. O arranque de um ESC afunda o rail por instantes. Um unico
    valor abaixo do limiar nao e uma bateria vazia, e um transitorio.
    Exigem-se N leituras seguidas.

  * FICAR CEGO CONTA COMO MOTIVO PARA REGRESSAR. Sem leitura de tensao,
    o barco perde precisamente o aviso que o faria voltar a tempo.
    Continuar a missao as cegas troca uma certeza pequena (voltar mais
    cedo do que era preciso) por uma incerteza grande (nao voltar). A
    tolerancia e um parametro, mas o lado para que se falha nao e.

  * SEM CALIBRACAO NAO SE DISPARA. Com resistores de 5 %, o erro a 12,6 V
    e de +-1,09 V -- maior do que a distancia entre "cheia" e "no
    limite". Um limiar aplicado a numeros por calibrar decide ao acaso.
    Por omissao a guarda recusa-se a funcionar nesse estado, e diz porque.
"""

import time

ESTADO_OK = "ok"
ESTADO_REGRESSO = "regresso"
ESTADO_INDEFINIDO = "indefinido"     # ainda sem leituras suficientes


class BatteryGuardUnusable(Exception):
    """A guarda nao pode decidir: faltam-lhe as condicoes para o fazer."""


class BatteryGuard:
    """Decide quando abortar a missao por tensao da eletronica.

    Parametros:
      threshold_v         limiar de regresso, em volts de bateria. NAO tem
                          valor por omissao de proposito: sai da medicao do
                          consumo real, que ainda nao foi feita. Ver o
                          ponto 8 do documento de sense.
      consecutive         leituras seguidas abaixo do limiar antes de
                          disparar
      max_blind_s         tempo sem leitura valida ao fim do qual se
                          regressa na mesma
      require_calibration recusar decidir com leituras nao calibradas
      clock               relogio monotonico, injetavel
    """

    def __init__(self, threshold_v, consecutive=3, max_blind_s=10.0,
                 require_calibration=True, clock=time.monotonic):
        if threshold_v is None:
            raise ValueError(
                "limiar de regresso por definir. Medir primeiro o consumo "
                "real da eletronica (sense v1.11.1, ponto 8).")
        self.threshold_v = float(threshold_v)
        self.consecutive = int(consecutive)
        self.max_blind_s = float(max_blind_s)
        self.require_calibration = require_calibration
        self._clock = clock

        self.state = ESTADO_INDEFINIDO
        self.reason = "sem leituras"
        self._below = 0
        self._last_good_t = None
        self._last_volts = None

    # -- decisao ---------------------------------------------------------

    def update(self, reading, now=None):
        """Alimenta a guarda com uma Reading do canal da eletronica.

        Devolve o estado. Uma vez em ESTADO_REGRESSO, fica.
        """
        now = self._clock() if now is None else now

        if self.state == ESTADO_REGRESSO:
            return self.state

        if self.require_calibration and not getattr(reading, "calibrated", False):
            raise BatteryGuardUnusable(
                "leituras nao calibradas: um limiar aplicado a estes numeros "
                "decide ao acaso. Calibrar o canal contra multimetro primeiro.")

        if reading is None or not getattr(reading, "available", False):
            return self._blind(now, getattr(reading, "note", "sem leitura"))

        self._last_good_t = now
        self._last_volts = reading.value

        if reading.value < self.threshold_v:
            self._below += 1
            if self._below >= self.consecutive:
                return self._trip(
                    f"{reading.value:.2f} V abaixo de {self.threshold_v:.2f} V "
                    f"em {self._below} leituras seguidas")
            self.state = ESTADO_OK
            self.reason = (f"{reading.value:.2f} V abaixo do limiar "
                           f"({self._below}/{self.consecutive})")
            return self.state

        self._below = 0
        self.state = ESTADO_OK
        self.reason = f"{reading.value:.2f} V"
        return self.state

    def _blind(self, now, nota):
        if self._last_good_t is None:
            # Nunca houve leitura boa: arranca-se o relogio da cegueira
            # agora, para o barco nao abortar por ainda nao ter comecado.
            self._last_good_t = now
        cego_ha = now - self._last_good_t
        if cego_ha > self.max_blind_s:
            return self._trip(
                f"sem leitura de tensao ha {cego_ha:.1f} s ({nota})")
        self.state = ESTADO_OK if self.state == ESTADO_OK else ESTADO_INDEFINIDO
        self.reason = f"sem leitura ha {cego_ha:.1f} s ({nota})"
        return self.state

    def _trip(self, motivo):
        self.state = ESTADO_REGRESSO
        self.reason = motivo
        return self.state

    # -- estado ----------------------------------------------------------

    @property
    def should_return(self):
        return self.state == ESTADO_REGRESSO

    @property
    def last_volts(self):
        return self._last_volts

    def reset(self):
        """Levanta a trava. Deliberadamente explicito: so quem sabe o que
        aconteceu a bateria e que pode voltar a deixar o barco sair."""
        self.state = ESTADO_INDEFINIDO
        self.reason = "reposta a mao"
        self._below = 0
        self._last_good_t = None
        return self.state
