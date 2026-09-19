"""Posicao REAL a partir do GPS NEO-8M, por NMEA na UART do GPIO.

Substitui a posicao do SimulatedBoat mantendo a interface position(), que
devolve (lat, lon) em graus decimais. Tudo o que esta classe tem a mais
existe porque a fonte simulada nunca falha e o GPS falha de seis maneiras,
todas silenciosas:

  1. Pode nao ter fix. As tramas continuam a chegar, com os campos de
     posicao vazios ou com o estado 'V'. Nao ha erro nenhum a aparecer.
  2. Pode ter fix mau. Com HDOP alto ou tres satelites, a posicao existe
     e pode estar dezenas de metros ao lado. E um numero plausivel e
     errado, que e pior do que nao haver numero.
  3. A linha pode vir partida. A serie perde bytes; meia trama pode
     continuar a parecer uma trama. Por isso o checksum e obrigatorio e
     nao opcional.
  4. Pode estar velha. Se o modulo deixar de responder, a ultima posicao
     conhecida continua em memoria e parece atual -- e o barco navega
     para um sitio onde ja nao esta.
  5. Pode dizer 0,0. Um modulo sem fix as vezes reporta latitude e
     longitude exatamente nulas, ao largo da Africa ocidental. E uma
     coordenada valida; simplesmente nao e a nossa.
  6. O buffer pode estar atrasado. Se se ler uma linha por ciclo e o GPS
     enviar varias por segundo, le-se sempre a posicao mais antiga da
     fila e nao a mais recente. E a mesma armadilha do ack do STOP: o que
     esta no buffer nao e, por ser ler, o que acabou de acontecer.

Politica: perante duvida, nao devolver numero. position() levanta
PositionUnavailable em vez de inventar uma posicao, tal como o RealHeading
faz com o rumo.

Ligacao fisica (decisao de OPEN-005): UART do GPIO, /dev/serial0, 9600 8N1.
Ver create_neo8m() para o que e preciso configurar no Pi -- nao e obvio.
"""

import time
from collections import namedtuple

# Uma posicao ja validada. utc e a hora da trama, tal como veio.
Fix = namedtuple("Fix", "lat lon quality satellites hdop utc source")

# Contadores de diagnostico. Sao QUATRO e nao um, porque "a trama nao deu
# posicao" tem causas com remedios opostos:
#
#   bad_checksum  a linha chegou corrompida -> baud errado, cablagem, massa
#   no_fix        a linha esta boa mas nao traz posicao: ou nao e do tipo
#                 que interessa (GSV, GSA, VTG), ou o modulo ainda nao tem
#                 fix. NAO e defeito nenhum; num arranque a frio sao 100%
#                 das tramas durante minutos
#   rejected      havia posicao, mas nao passou nos criterios (satelites,
#                 HDOP, 0/0)
#   accepted      produziu um fix utilizavel
#
# Somar tudo num contador de "rejeitadas" faz um arranque normal parecer
# uma avaria de baud -- e um alarme que dispara quando nao se passa nada
# ensina o operador a ignora-lo.
Stats = namedtuple("Stats", "seen bad_checksum no_fix rejected accepted")

FIX_INVALIDO = 0


class PositionUnavailable(Exception):
    """Nao ha posicao fiavel. O chamador deve ir para estado seguro."""


def nmea_checksum_ok(line):
    """True se a trama tiver checksum e ele bater certo.

    Sem '*' nao ha checksum, logo nao ha como saber se a linha chegou
    inteira -- e uma linha cuja integridade nao se pode verificar conta
    como invalida, nao como valida por omissao.
    """
    line = line.strip()
    if not line.startswith("$") or "*" not in line:
        return False
    corpo, _, dado = line[1:].partition("*")
    if len(dado) < 2:
        return False
    soma = 0
    for c in corpo:
        soma ^= ord(c)
    try:
        return soma == int(dado[:2], 16)
    except ValueError:
        return False


def ddmm_to_degrees(valor, hemisferio):
    """Converte ddmm.mmmm (o formato do NMEA) em graus decimais.

    O NMEA nao da graus: da graus colados a minutos no mesmo numero.
    Tratar o campo como se fosse graus da um erro que cresce com a
    latitude e que, em Lisboa, chega a centenas de quilometros.
    """
    if valor in (None, "") or hemisferio in (None, ""):
        return None
    try:
        bruto = float(valor)
    except ValueError:
        return None
    graus = int(bruto / 100.0)
    minutos = bruto - graus * 100.0
    if minutos >= 60.0:
        return None                      # campo corrompido
    decimal = graus + minutos / 60.0
    if hemisferio.upper() in ("S", "W"):
        decimal = -decimal
    return decimal


def parse_sentence(line):
    """Devolve um Fix a partir de uma trama RMC ou GGA, ou None.

    None quer dizer "esta linha nao serve": nao e do tipo certo, tem
    checksum errado, esta partida ou o modulo ainda nao tem posicao. Nao
    se distingue aqui porque quem chama quer a proxima linha na mesma.
    """
    if not nmea_checksum_ok(line):
        return None
    campos = line.strip()[1:].split("*")[0].split(",")
    if not campos or len(campos[0]) < 5:
        return None
    tipo = campos[0][-3:]                # ignora o talker: GP, GN, GL...

    if tipo == "RMC":
        # $--RMC,hhmmss,A,ddmm.mmmm,N,dddmm.mmmm,E,vel,rumo,ddmmaa,...
        if len(campos) < 7 or campos[2] != "A":
            return None                  # 'V' = void, sem fix
        lat = ddmm_to_degrees(campos[3], campos[4])
        lon = ddmm_to_degrees(campos[5], campos[6])
        if lat is None or lon is None:
            return None
        return Fix(lat, lon, 1, None, None, campos[1] or None, "RMC")

    if tipo == "GGA":
        # $--GGA,hhmmss,ddmm.mmmm,N,dddmm.mmmm,E,q,sats,hdop,...
        if len(campos) < 9:
            return None
        try:
            qualidade = int(campos[6] or 0)
        except ValueError:
            return None
        if qualidade == FIX_INVALIDO:
            return None
        lat = ddmm_to_degrees(campos[2], campos[3])
        lon = ddmm_to_degrees(campos[4], campos[5])
        if lat is None or lon is None:
            return None
        try:
            sats = int(campos[7] or 0)
        except ValueError:
            sats = 0
        try:
            hdop = float(campos[8] or 99.0)
        except ValueError:
            hdop = 99.0
        return Fix(lat, lon, qualidade, sats, hdop, campos[1] or None, "GGA")

    return None


# Idade maxima de um fix antes de deixar de servir.
#
# O NEO-8M emite a 1 Hz, portanto os fixes chegam de segundo a segundo. Os
# 2,0 s que aqui estavam nao toleravam UMA mensagem perdida: com uma falha,
# o fix seguinte chega exatamente ao limite e a posicao fica indisponivel
# num arranque perfeitamente normal. 2,5 s toleram uma perda com 0,5 s de
# folga para o jitter da porta.
#
# O que este numero custa, e que fica registado em vez de escondido: a 3 m/s
# (velocidade de projeto), 2,5 s de posicao velha sao 7,5 m de incerteza --
# quase o dobro do raio de chegada de 4 m. Ou seja, com o modulo a 1 Hz o
# raio de chegada NAO pode ser apertado abaixo do orcamento de idade, por
# muito bom que seja o fix. Nao ha valor de max_stale_s que resolva isto: o
# remedio e subir a cadencia do modulo (o NEO-8M faz 5 Hz por UBX-CFG-RATE),
# e essa passa a ser a condicao para apertar o raio de chegada.
MAX_STALE_S = 2.5


class RealPosition:
    """Posicao do barco medida pelo GPS.

    Parametros:
      port            objeto com readline() -> bytes/str e, se existir,
                      in_waiting (serial.Serial, ou um falso nos testes)
      max_stale_s     idade maxima da ultima posicao boa antes de deixar
                      de ser aceite. Ver MAX_STALE_S para o porque do
                      valor -- nao e um numero redondo, sai da cadencia
                      do modulo
      min_satellites  minimo de satelites exigido nas tramas GGA
      max_hdop        HDOP maximo aceite. 2,5 e ja generoso para agua
                      aberta; acima disso a posicao anda aos saltos
      max_lines       tramas lidas por poll(). Existe para o poll nao
                      ficar preso a esvaziar um buffer que continua a
                      encher
      clock           relogio monotonico, injetavel
    """

    # Fonte real: o nav_guard() do main.py deixa o NAV comandar motores
    # quando todas as fontes tem SYNTHETIC False.
    SYNTHETIC = False

    def __init__(self, port, max_stale_s=MAX_STALE_S, min_satellites=4,
                 max_hdop=2.5, max_lines=40, clock=time.monotonic):
        self.port = port
        self.max_stale_s = max_stale_s
        self.min_satellites = min_satellites
        self.max_hdop = max_hdop
        self.max_lines = max_lines
        self._clock = clock

        self._last_fix = None
        self._last_fix_t = None
        self._last_reject = "ainda sem leituras"
        self._lines_seen = 0
        self._bad_checksum = 0
        self._no_fix = 0
        self._rejected = 0
        self._accepted = 0

    # -- aceitacao -------------------------------------------------------

    def _acceptable(self, fix):
        """(aceita?, motivo). O motivo fica guardado para diagnostico."""
        if fix.lat == 0.0 and fix.lon == 0.0:
            return False, "posicao 0,0 -- modulo sem fix a reportar nulos"
        if fix.satellites is not None and fix.satellites < self.min_satellites:
            return False, f"{fix.satellites} satelites (minimo {self.min_satellites})"
        if fix.hdop is not None and fix.hdop > self.max_hdop:
            return False, f"HDOP {fix.hdop:.1f} (maximo {self.max_hdop:.1f})"
        return True, ""

    # -- leitura ---------------------------------------------------------

    def _readline(self):
        linha = self.port.readline()
        if isinstance(linha, bytes):
            return linha.decode("ascii", errors="replace")
        return linha or ""

    def poll(self, on_line=None):
        """Le o que estiver no buffer e guarda o fix mais RECENTE.

        Le ate max_lines tramas e fica com a ultima aceitavel, em vez de
        parar na primeira. Uma trama que esta na fila nao acabou de
        acontecer: parar na primeira e ler passado enquanto o presente
        continua a chegar.

        `on_line(linha, fix)` e chamado para cada trama lida, com o Fix
        que ela produziu ou None. Existe para quem quiser VER as tramas
        (o tools/gps_bench.py) sem as ler da porta por sua conta: duas
        leituras da mesma porta fazem com que cada lado fique com metade
        das tramas, e as boas tendem a cair no lado que so as mostra.
        Um leitor so, e quem quiser observar passa por aqui.

        Devolve o numero de tramas lidas.
        """
        lidas = 0
        while lidas < self.max_lines:
            if hasattr(self.port, "in_waiting") and not self.port.in_waiting:
                break
            linha = self._readline()
            if not linha:
                break
            lidas += 1
            self._lines_seen += 1

            if not nmea_checksum_ok(linha):
                self._bad_checksum += 1
                if on_line is not None:
                    on_line(linha, None)
                continue

            fix = parse_sentence(linha)
            if on_line is not None:
                on_line(linha, fix)
            if fix is None:
                # Trama integra que nao da posicao: tipo que nao interessa,
                # ou modulo ainda sem fix. Normal, nao e defeito.
                self._no_fix += 1
                continue

            ok, motivo = self._acceptable(fix)
            if not ok:
                self._rejected += 1
                self._last_reject = motivo
                continue

            self._accepted += 1
            self._last_fix = fix
            self._last_fix_t = self._clock()
        return lidas

    def position(self):
        """(lat, lon) em graus decimais.

        Levanta PositionUnavailable se nunca houve fix aceitavel ou se o
        ultimo ja tem mais de max_stale_s. Nunca devolve a ultima posicao
        conhecida como se fosse atual: um barco que navega para onde ja
        esteve e pior do que um barco que para.
        """
        self.poll()
        if self._last_fix is None or self._last_fix_t is None:
            raise PositionUnavailable(f"sem fix: {self._last_reject}")
        idade = self._clock() - self._last_fix_t
        if idade > self.max_stale_s:
            raise PositionUnavailable(
                f"ultimo fix ha {idade:.1f} s (maximo {self.max_stale_s:.1f} s)")
        return self._last_fix.lat, self._last_fix.lon

    def fix_age(self):
        """Idade do ultimo fix aceite, em segundos, ou None se nunca houve.

        Nao faz poll nem levanta nada. Existe para quem quer MOSTRAR ou
        REGISTAR a idade sem a transformar numa decisao -- o position()
        e que decide, e e o unico que deve decidir. Um segundo sitio a
        comparar idades com limiares seria uma segunda politica a
        divergir da primeira.
        """
        if self._last_fix_t is None:
            return None
        return self._clock() - self._last_fix_t

    def position_or_none(self):
        """Como position(), mas devolve None em vez de levantar.

        Para o script de bancada, onde nao haver fix e informacao a
        mostrar no ecra e nao motivo para abortar.
        """
        try:
            return self.position()
        except PositionUnavailable:
            return None

    @property
    def last_reject(self):
        """Porque e que a ultima trama util nao passou. Texto, para mostrar.

        Nao e uma decisao: e o motivo da ultima recusa, que serve para o
        operador saber se esta perante um arranque a frio, um HDOP mau ou
        uma cablagem errada -- causas com remedios opostos.
        """
        return self._last_reject

    @property
    def last_fix(self):
        """O ultimo Fix aceite, com satelites e HDOP. Pode estar velho."""
        return self._last_fix

    @property
    def stats(self):
        """Stats(seen, bad_checksum, no_fix, rejected, accepted).

        O contador que aponta para avaria de ligacao e o bad_checksum: sao
        linhas que chegaram corrompidas. O no_fix alto e esperado e nao
        significa nada de mau -- num arranque a frio e 100% das tramas.
        """
        return Stats(self._lines_seen, self._bad_checksum, self._no_fix,
                     self._rejected, self._accepted)


class RealBoat:
    """Junta GPS e IMU numa fonte com a mesma interface do SimulatedBoat.

    O nav_step() do main.py pede position(), le .heading e depois chama
    update() para fechar a malha no barco sintetico. Com hardware a malha
    fecha-se na agua: update() nao tem nada para fazer e e, de proposito,
    um no-op que devolve o estado medido.

    INTEGRADO, NAO ENSAIADO EM AGUA. O main.py ja apanha
    PositionUnavailable a volta do nav_step() e vai para estado seguro,
    como ja fazia quando perdia a serie (ver PositionWatch). Falta o
    ensaio real, e falta o rumo: sem BNO055 esta classe so se usa com
    fonte de rumo sintetica, e nesse caso declara-se sintetica.
    """

    def __init__(self, position_source, heading_source):
        self.position_source = position_source
        self.heading_source = heading_source

    @property
    def heading(self):
        return self.heading_source.read()

    def position(self):
        return self.position_source.position()

    def update(self, left, right, dt=1.0):
        # A malha fecha-se na agua. Nao ha modelo nenhum a atualizar aqui.
        return self.position() + (self.heading,)

    # SYNTHETIC e calculado, nao fixo, e a diferenca nao e cosmetica.
    #
    # Estava aqui um `SYNTHETIC = False` de classe, escrito quando se
    # assumia que um RealBoat so se construia com dois sensores reais.
    # Com o BNO055 avariado, a primeira coisa que se quer fazer e
    # exatamente o contrario: GPS real com rumo sintetico, para o GPS
    # entrar no sistema sem esperar pela placa nova. Nessa combinacao o
    # False de classe mentia -- o nav_guard() via uma fonte "real" e
    # deixava comandar motores a partir de um rumo inventado, que e o
    # caso perigoso que o proprio nav_guard existe para impedir.
    #
    # A regra passa a ser a mesma que o nav_guard ja aplica ao conjunto:
    # basta uma fonte sintetica para o todo o ser. E, tal como no
    # is_synthetic(), uma fonte que nao se declara conta como sintetica.
    @property
    def SYNTHETIC(self):        # noqa: N802 - contrato partilhado com as fontes
        return (getattr(self.position_source, "SYNTHETIC", True)
                or getattr(self.heading_source, "SYNTHETIC", True))


def create_neo8m(device="/dev/serial0", baudrate=9600, timeout=0.2, **kwargs):
    """Constroi um RealPosition ligado ao GPS fisico.

    O import fica aqui dentro para que control/real_position.py possa ser
    importado e testado numa maquina sem pyserial.

    Requer, no Pi:  pip install pyserial

    E no raspi-config -> Interface Options -> Serial Port:
      - consola de login pela serie: NAO
      - porta serie por hardware: SIM

    Armadilha do Pi 4, que custa uma tarde a quem nao a conhece: por
    omissao /dev/serial0 aponta para a mini-UART, cujo baud rate esta
    preso ao relogio do core e varia com o governor de frequencia -- o
    GPS ora le, ora da lixo, conforme a carga do CPU. Para ficar com a
    PL011, que tem relogio proprio, acrescentar ao /boot/firmware/config.txt:

        dtoverlay=disable-bt

    (ou 'miniuart-bt' para manter o Bluetooth na mini-UART) e reiniciar.

    Nivel logico: o NEO-8M fala a 3,3 V, tal como o GPIO do Pi. TX do
    modulo vai ao GPIO15/RXD e RX do modulo ao GPIO14/TXD -- cruzados. Nao
    levar o modulo a 5 V no pino de dados.
    """
    import serial                              # noqa: PLC0415

    porta = serial.Serial(device, baudrate=baudrate, timeout=timeout)
    return RealPosition(porta, **kwargs)
