"""Ligacao serie ao ESP32.

Modulo reutilizavel: nao faz nada ao ser importado e nunca envia
comandos por iniciativa propria. Quem decide o que enviar e o main.py.
Protocolo: "L: <0-100> R: <0-100>\n"

-------------------------------------------------------------------------
O STOP CONFIRMADO

Um `write()` unico nao prova nada. O sistema operativo aceita os bytes para
o buffer de saida e devolve sucesso; se o cabo estiver solto, se o ESP32
estiver em reset ou se a linha estiver corrompida, o STOP nunca chega e
ninguem fica a saber. O failsafe do ESP32 acaba por travar a propulsao 1 s
depois, o que salva o barco -- mas entao o STOP primario e o timeout, e o
comando passa a ser decorativo.

Por isso o `stop_motors()` repete ate o ESP32 confirmar. A confirmacao
existe no protocolo: perante "L: 0 R: 0" o firmware responde sempre
"Parado. Propulsao DESTRAVADA" (CmdResult CMD_IDLE em motor_safety.h), e
esse e o unico comando com essa resposta.

Duas subtilezas que fazem a diferenca entre confirmar e fingir que confirma:

1. O buffer e DRENADO antes de enviar. Em ARMED o Pi manda 0/0 a 5 Hz, ou
   seja, ha sempre acks antigos por ler. Aceitar um deles como resposta ao
   STOP de agora seria confirmar com o eco de um comando anterior. Uma
   confirmacao so vale se nao puder ser um resto.
2. O orcamento de tempo total fica muito abaixo do timeout do failsafe
   (STOP_ATTEMPTS * STOP_CONFIRM_S ~ 0,24 s contra 1 s). Se a confirmacao
   nunca chegar, o failsafe do ESP32 ainda dispara dentro da mesma janela
   -- as duas protecoes nao competem, encadeiam-se.

Nao confirmar NAO significa "os motores continuam a andar". Significa uma
de duas coisas, ambas seguras e agora distinguiveis no log: ou o ESP32
recebeu e a resposta perdeu-se, ou a ligacao morreu e o failsafe trava a
propulsao em 1 s. O que faltava nao era seguranca, era saber qual das duas
aconteceu.
-------------------------------------------------------------------------
"""

import time

try:
    import serial
    _SERIAL_ERRORS = (serial.SerialException, OSError)
except ImportError:  # pragma: no cover - PC sem pyserial
    # O modulo tem de importar-se num PC sem pyserial para os testes
    # correrem sem hardware, tal como o real_heading.py faz com o driver
    # do BNO055. Sem pyserial so o connect() falha; o resto e testavel.
    serial = None
    _SERIAL_ERRORS = (OSError,)

DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_BAUD = 115200

# Resposta do ESP32 a "L: 0 R: 0" (CMD_IDLE). E o unico comando que a
# produz, logo serve de confirmacao inequivoca do STOP.
STOP_ACK = "DESTRAVADA"

# Orcamento do STOP: 3 tentativas x 80 ms = 240 ms no pior caso, contra os
# 1000 ms do FAILSAFE_TIMEOUT_MS do ESP32. O STOP falha bem antes de o
# failsafe ter de entrar.
STOP_ATTEMPTS = 3
STOP_CONFIRM_S = 0.08
STOP_POLL_S = 0.005


def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, int(round(x))))


def format_cmd(left, right):
    return f"L: {clamp(left)} R: {clamp(right)}\n"


class StopResult:
    """Resultado de um STOP: o que foi enviado e o que o ESP32 confirmou.

    Verdadeiro apenas quando CONFIRMADO. E de proposito: quem escrever
    `if not link.stop_motors():` fica com o ramo conservador sem ter de
    saber que existe um campo chamado `confirmed`. Um namedtuple seria
    sempre verdadeiro e transformava a duvida em sucesso silencioso.
    """

    def __init__(self, sent, confirmed, attempts, lines=None, reason=""):
        self.sent = sent              # algum write() chegou a ser aceite
        self.confirmed = confirmed    # o ESP32 respondeu com o ack
        self.attempts = attempts      # quantas tentativas foram feitas
        self.lines = lines or []      # linhas lidas durante a operacao
        self.reason = reason

    def __bool__(self):
        return self.confirmed

    def __repr__(self):
        estado = "confirmado" if self.confirmed else "NAO confirmado"
        return (f"<StopResult {estado} sent={self.sent} "
                f"tentativas={self.attempts} motivo='{self.reason}'>")


class SerialLink:
    def __init__(self, port=DEFAULT_PORT, baud=DEFAULT_BAUD):
        self.port = port
        self.baud = baud
        self.ser = None
        self._buf = b""  # bytes recebidos ainda sem newline

    @property
    def is_open(self):
        return self.ser is not None and self.ser.is_open

    def connect(self):
        """Tenta abrir a porta. Devolve True/False; nunca lanca excecao."""
        if serial is None:
            print("[WARN] pyserial nao instalado; sem ligacao ao ESP32")
            return False
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0)
            time.sleep(2)  # o ESP32 reinicia quando a porta abre
            self.ser.reset_input_buffer()  # descarta lixo de arranque do ESP32
            self._buf = b""
            return True
        except _SERIAL_ERRORS as e:
            print(f"[WARN] ESP32 nao disponivel em {self.port}: {e}")
            self.ser = None
            return False

    def send_motors(self, left, right):
        """Envia comando aos motores. True apenas se foi mesmo enviado."""
        if not self.is_open:
            return False
        try:
            self.ser.write(format_cmd(left, right).encode("utf-8"))
            return True
        except _SERIAL_ERRORS as e:
            print(f"[WARN] Falha de escrita: {e}")
            self.close()
            return False

    def drain(self):
        """Le e devolve tudo o que estiver pendente, deixando o buffer vazio.

        Existe para o STOP: sem isto, um ack anterior por ler podia passar
        por resposta ao comando atual. Descarta tambem a linha incompleta
        que esteja a meio -- foi escrita antes do STOP, logo tambem e
        resto. Perde-se parte de uma mensagem de consola; nao se perde
        nenhuma decisao.
        """
        linhas = []
        while True:
            linha = self.read_line()
            if linha is None:
                break
            linhas.append(linha)
        self._buf = b""
        return linhas

    def stop_motors(self, attempts=STOP_ATTEMPTS, confirm_s=STOP_CONFIRM_S,
                    clock=time.monotonic, sleep=time.sleep):
        """Manda parar e repete ate o ESP32 confirmar. Devolve StopResult.

        O relogio e a espera entram por parametro para os testes poderem
        exercitar o timeout sem esperar por ele -- o mesmo motivo pelo qual
        o tick() do motor_safety.h recebe o instante em vez de chamar o
        millis().
        """
        linhas = []
        if not self.is_open:
            return StopResult(False, False, 0, linhas, "porta fechada")

        enviou_alguma = False
        for tentativa in range(1, attempts + 1):
            if not self.is_open:
                return StopResult(enviou_alguma, False, tentativa, linhas,
                                  "porta fechou durante o STOP")

            # Drenar ANTES de enviar: so assim o ack que vier a seguir e
            # necessariamente resposta a este comando.
            linhas.extend(self.drain())

            if not self.send_motors(0, 0):
                # O send_motors ja fechou a porta. Insistir nao ajuda: sem
                # porta nao ha caminho. O failsafe do ESP32 assume daqui.
                return StopResult(enviou_alguma, False, tentativa, linhas,
                                  "escrita falhou; porta fechada")
            enviou_alguma = True

            limite = clock() + confirm_s
            while clock() < limite:
                linha = self.read_line()
                if linha is None:
                    sleep(STOP_POLL_S)
                    continue
                linhas.append(linha)
                if STOP_ACK in linha.upper():
                    return StopResult(True, True, tentativa, linhas,
                                      "ack do ESP32")

        return StopResult(enviou_alguma, False, attempts, linhas,
                          f"sem ack em {attempts} tentativas")

    def read_line(self):
        """Devolve uma linha completa do ESP32, ou None.

        Acumula os bytes recebidos num buffer interno e so devolve
        texto quando o newline chega, evitando linhas partidas quando
        a mensagem chega em varios pedacos.
        """
        if not self.is_open:
            return None
        try:
            n = self.ser.in_waiting
            if n:
                self._buf += self.ser.read(n)
        except _SERIAL_ERRORS:
            self.close()
            return None
        if b"\n" not in self._buf:
            return None
        raw, self._buf = self._buf.split(b"\n", 1)
        return raw.decode("utf-8", errors="ignore").strip() or None

    def close(self):
        """Envia STOP (se possivel) e fecha a porta.

        Aqui o STOP e mesmo um write() unico e sem confirmacao, de
        proposito: estamos a fechar a porta a seguir, portanto nao ha
        caminho para ler resposta nenhuma. A protecao no encerramento e o
        failsafe do ESP32, que dispara 1 s depois de a porta calar.
        """
        if self.is_open:
            try:
                self.ser.write(format_cmd(0, 0).encode("utf-8"))
            except _SERIAL_ERRORS:
                pass
        if self.ser is not None:
            try:
                self.ser.close()
            except _SERIAL_ERRORS:
                pass
            self.ser = None


if __name__ == "__main__":
    # Auto-teste inofensivo: tenta ligar, reporta, fecha. Nao move motores.
    link = SerialLink()
    if link.connect():
        print("[INFO] Porta aberta com sucesso")
        r = link.stop_motors()
        print(f"[INFO] STOP: {r!r}")
        link.close()
        print("[INFO] Porta fechada")
    else:
        print("[INFO] Sem ligacao — comportamento esperado se o ESP32 estiver desligado")
