"""Testes do STOP com repeticao e confirmacao (sem hardware).

Exercitam SerialLink.stop_motors() contra um ESP32 falso que responde
como o firmware real: a "L: 0 R: 0" responde "Parado. Propulsao
DESTRAVADA", e a mais nada.

O relogio e a espera entram por parametro, portanto os testes de timeout
correm instantaneamente -- a mesma ideia do tick(now) do motor_safety.h.

Correr com: python3 tests/test_stop_confirmado.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from communication.serial_link import (SerialLink, StopResult, format_cmd,
                                       STOP_ACK, STOP_ATTEMPTS,
                                       STOP_CONFIRM_S)

FAILSAFE_TIMEOUT_S = 1.0   # FAILSAFE_TIMEOUT_MS do esp32/motor_safety.h
ACK = "Parado. Propulsao DESTRAVADA"


class FakeSerial:
    """ESP32 falso. Responde ao STOP como o firmware, ou fica mudo."""

    def __init__(self, responde=True, falha_escrita_em=None, mudo_ate=0):
        self.is_open = True
        self.responde = responde
        self.falha_escrita_em = falha_escrita_em  # nº da escrita que rebenta
        self.mudo_ate = mudo_ate                  # ignora os N primeiros STOP
        self.escrito = []
        self.rx = b""

    # --- lado do Pi -----------------------------------------------------
    def write(self, data):
        self.escrito.append(data)
        if self.falha_escrita_em == len(self.escrito):
            raise OSError("cabo solto")
        if data == format_cmd(0, 0).encode() and self.responde:
            if len(self.escrito) > self.mudo_ate:
                self.rx += (ACK + "\n").encode()
        return len(data)

    @property
    def in_waiting(self):
        return len(self.rx)

    def read(self, n):
        out, self.rx = self.rx[:n], self.rx[n:]
        return out

    def reset_input_buffer(self):
        self.rx = b""

    def close(self):
        self.is_open = False

    # --- lado do ESP32 (para os testes) ---------------------------------
    def emitir(self, texto):
        """O ESP32 escreve uma linha por iniciativa propria."""
        self.rx += (texto + "\n").encode()


class RelogioFalso:
    """Relogio que so avanca quando o codigo dorme."""

    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


def _ligado(**kw):
    link = SerialLink()
    fake = FakeSerial(**kw)
    link.ser = fake
    return link, fake


def _stop(link, **kw):
    r = RelogioFalso()
    return link.stop_motors(clock=r.now, sleep=r.sleep, **kw)


# --- confirmacao ---------------------------------------------------------

def test_stop_confirmado_a_primeira():
    """Com o ESP32 a responder, o STOP confirma na primeira tentativa."""
    link, fake = _ligado()
    r = _stop(link)
    assert r.confirmed, r
    assert r.attempts == 1
    assert r.sent
    assert fake.escrito == [format_cmd(0, 0).encode()]


def test_stop_result_e_falso_quando_nao_confirmado():
    """`if not link.stop_motors()` tem de dar o ramo conservador.

    Um namedtuple seria sempre verdadeiro e transformava "nao sei" em
    "correu bem" em todos os sitios que testassem o valor de retorno.
    """
    link, _ = _ligado(responde=False)
    r = _stop(link)
    assert not r.confirmed
    assert bool(r) is False
    assert not r


def test_stop_confirmado_e_verdadeiro():
    link, _ = _ligado()
    assert bool(_stop(link)) is True


# --- o teste que justifica a drenagem ------------------------------------

def test_ack_antigo_no_buffer_nao_confirma_o_stop_atual():
    """Um ack por ler nao pode passar por resposta ao comando de agora.

    Em ARMED o Pi manda 0/0 a 5 Hz e o ESP32 responde a cada um: ha
    sempre acks pendentes. Sem drenagem, um STOP que nunca chegasse ao
    ESP32 seria "confirmado" pelo eco de um comando anterior -- que e
    precisamente o modo de falha que a confirmacao devia apanhar.
    """
    link, fake = _ligado(responde=False)   # o ESP32 nao vai responder
    fake.emitir(ACK)                       # ...mas ha um ack antigo por ler
    fake.emitir(ACK)
    r = _stop(link)
    assert not r.confirmed, "confirmou com o eco de um comando anterior"
    assert r.reason.startswith("sem ack")


def test_a_drenagem_devolve_as_linhas_em_vez_de_as_deitar_fora():
    """O que se drena e para registar, nao para perder."""
    link, fake = _ligado()
    fake.emitir("COMANDO INVALIDO - motores parados")
    r = _stop(link)
    assert r.confirmed
    assert any("INVALIDO" in l for l in r.lines), r.lines


def test_drain_esvazia_tambem_a_linha_incompleta():
    """Um fragmento sem newline foi escrito antes do STOP: tambem e resto."""
    link, fake = _ligado()
    fake.rx = b"linha inteira\nfragmento sem fim"
    linhas = link.drain()
    assert linhas == ["linha inteira"]
    assert link._buf == b""


# --- repeticao -----------------------------------------------------------

def test_insiste_ate_ao_limite_quando_o_esp32_esta_mudo():
    link, fake = _ligado(responde=False)
    r = _stop(link)
    assert not r.confirmed
    assert r.attempts == STOP_ATTEMPTS
    assert len(fake.escrito) == STOP_ATTEMPTS, "nao repetiu o comando"
    assert r.sent, "chegou a enviar, mesmo sem confirmacao"


def test_confirma_a_segunda_tentativa():
    """O primeiro STOP perde-se; o segundo chega. Confirma e para de insistir."""
    link, fake = _ligado(mudo_ate=1)
    r = _stop(link)
    assert r.confirmed
    assert r.attempts == 2
    assert len(fake.escrito) == 2, "insistiu depois de confirmado"


def test_numero_de_tentativas_configuravel():
    link, fake = _ligado(responde=False)
    r = _stop(link, attempts=5)
    assert r.attempts == 5
    assert len(fake.escrito) == 5


# --- falhas do canal -----------------------------------------------------

def test_porta_fechada_nao_finge_ter_enviado():
    link = SerialLink()          # nunca ligou
    r = _stop(link)
    assert not r.sent and not r.confirmed
    assert r.attempts == 0
    assert "fechada" in r.reason


def test_escrita_que_rebenta_nao_insiste_e_fecha_a_porta():
    """Sem porta nao ha caminho; insistir so gasta tempo.

    A protecao neste caso e o failsafe do ESP32, que trava a propulsao
    ~1 s depois de a serie calar.
    """
    link, fake = _ligado(falha_escrita_em=1)
    r = _stop(link)
    assert not r.confirmed
    assert not link.is_open, "a porta devia ter fechado"
    assert "escrita falhou" in r.reason


def test_falha_a_meio_da_repeticao_reporta_que_chegou_a_enviar():
    link, fake = _ligado(responde=False, falha_escrita_em=2)
    r = _stop(link)
    assert r.sent, "a primeira escrita passou"
    assert not r.confirmed


# --- orcamento de tempo --------------------------------------------------

def test_o_stop_falha_antes_de_o_failsafe_ter_de_entrar():
    """As duas protecoes encadeiam-se em vez de competirem.

    Se o STOP demorasse mais do que o timeout do ESP32, o failsafe
    disparava enquanto o Pi ainda estava a tentar -- e o resultado do
    STOP chegava depois de a decisao ja ter sido tomada noutra camada.
    """
    pior_caso = STOP_ATTEMPTS * STOP_CONFIRM_S
    assert pior_caso < FAILSAFE_TIMEOUT_S, (
        f"STOP demora ate {pior_caso:.2f} s, failsafe dispara a "
        f"{FAILSAFE_TIMEOUT_S:.2f} s")


def test_o_relogio_falso_nao_espera_de_verdade():
    """Se este teste demorasse 0,24 s, o clock nao estava a ser injetado."""
    import time as _t
    link, _ = _ligado(responde=False)
    t0 = _t.monotonic()
    _stop(link)
    assert _t.monotonic() - t0 < 0.05


# --- protocolo -----------------------------------------------------------

def test_o_ack_e_o_do_firmware():
    """STOP_ACK tem de aparecer mesmo na resposta do esp32.ino."""
    assert STOP_ACK in ACK.upper()


def test_so_o_comando_de_paragem_e_enviado():
    """O STOP nao pode mandar propulsao nenhuma, nem por engano."""
    link, fake = _ligado(responde=False)
    _stop(link)
    for d in fake.escrito:
        assert d == b"L: 0 R: 0\n", d


# --- o alarme do main.py: so grita quando ha alguma coisa em jogo --------

class _LogFalso:
    def __init__(self):
        self.linhas = []

    def log(self, tipo, state, texto):
        self.linhas.append((tipo, texto))

    def tipos(self):
        return [t for t, _ in self.linhas]


def _stop_confirmado(link):
    """Corre o main.stop_confirmado() e devolve (resultado, log, ecra)."""
    import contextlib
    import io
    from main import stop_confirmado
    log = _LogFalso()
    ecra = io.StringIO()
    with contextlib.redirect_stdout(ecra):
        r = stop_confirmado(link, log, "DISARMED", "teste")
    return r, log, ecra.getvalue()


def test_stop_sem_serie_nao_da_alarme():
    """Um STOP sem ESP32 nao falhou: nunca houve propulsao para parar.

    Sem esta distincao, toda a sessao de simulacao sem hardware enchia o
    ecra de [ALERTA] -- e um alarme que dispara quando nao esta nada em
    jogo e um alarme que se aprende a ignorar.
    """
    link = SerialLink()          # porta fechada
    r, log, ecra = _stop_confirmado(link)
    assert not r.confirmed
    assert "ALERTA" not in ecra, ecra
    assert "ALERTA" not in log.tipos()
    assert any("sem serie" in t for _, t in log.linhas), log.linhas


def test_stop_com_serie_e_sem_ack_da_alarme():
    """Com porta aberta e sem confirmacao, tem de gritar."""
    link, _ = _ligado(responde=False)
    r, log, ecra = _stop_confirmado(link)
    assert not r.confirmed
    assert "ALERTA" in ecra
    assert "ALERTA" in log.tipos()


def test_stop_confirmado_regista_a_confirmacao():
    link, _ = _ligado()
    r, log, ecra = _stop_confirmado(link)
    assert r.confirmed
    assert "ALERTA" not in ecra
    assert any("confirmado" in t for _, t in log.linhas), log.linhas


def test_linhas_lidas_durante_o_stop_vao_para_o_log():
    """O que se drena e registado; nao se perde uma mensagem do ESP32."""
    link, fake = _ligado()
    fake.emitir("VALOR FORA DO LIMITE SEGURO - motores parados")
    r, log, ecra = _stop_confirmado(link)
    assert any(t == "RX" for t, _ in log.linhas), log.linhas
    assert "FORA DO LIMITE" in ecra


def _run():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(tests)} testes passaram.")


if __name__ == "__main__":
    _run()
