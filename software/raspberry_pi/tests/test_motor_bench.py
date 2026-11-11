"""Testes do impulso de bancada dos motores (sem hardware).

Exercitam tools/motor_bench.py contra o ESP32 falso do proprio modulo, que
espelha a trava, o teto e o failsafe do motor_safety.h. O relogio e falso:
so avanca quando o codigo dorme, portanto 30 s de impulso correm num
instante -- a mesma ideia do test_stop_confirmado.py.

O que isto NAO prova: nada sobre a placa, o ESC ou o motor. Prova que o
script nunca manda propulsao sem a trava confirmada, nunca passa do pedido,
mantem o heartbeat dentro do failsafe e para sempre no fim.

Correr com: python3 tests/test_motor_bench.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from communication.serial_link import SerialLink
from tools.motor_bench import (ACK_TIMEOUT_S, DRY_MAX_PCT, DRY_MAX_S,
                               HEARTBEAT_S, MAX_DUR_S, SAFE_MAX, FakeEsp32,
                               comando, correr, main, perfil, recusa, validar)

STOP = "L: 0 R: 0"


class Relogio:
    """Relogio que so avanca quando o codigo dorme."""

    def __init__(self, salto_em=None, salto=0.0):
        self.t = 100.0
        self.salto_em = salto_em      # instante (desde o inicio) em que o
        self.salto = salto            # processo "congela" durante `salto` s
        self._saltou = False

    def clock(self):
        return self.t

    def sleep(self, dt):
        self.t += dt
        if (self.salto_em is not None and not self._saltou
                and self.t - 100.0 >= self.salto_em):
            self._saltou = True
            self.t += self.salto


class Log:
    def __init__(self):
        self.linhas = []

    def log(self, evento, estado="", detalhe=""):
        self.linhas.append((evento, estado, detalhe))

    def eventos(self, nome):
        return [d for e, _, d in self.linhas if e == nome]


def montar(rel=None, **kw):
    rel = rel or Relogio()
    link = SerialLink()
    link.ser = FakeEsp32(clock=rel.clock, **kw)
    return link, link.ser, rel


def pares(esp):
    """Comandos recebidos pelo ESP32 como pares (L, R)."""
    out = []
    for linha in esp.recebidos:
        l, r = linha.replace("L:", "").split("R:")
        out.append((int(l), int(r)))
    return out


def _silencio(*a, **k):
    pass


# --- validacao do pedido ---------------------------------------------------

def test_validar_aceita_o_normal():
    p = validar("e", 10, 3.0, seco=False)
    assert (p.lado, p.pct, p.dur, p.seco) == ("e", 10, 3.0, False)
    assert validar("ambos", SAFE_MAX, MAX_DUR_S).pct == SAFE_MAX


def test_validar_recusa_fora_dos_limites():
    maus = [("x", 10, 1), ("e", 0, 1), ("e", SAFE_MAX + 1, 1), ("e", -5, 1),
            ("e", 10, 0), ("e", 10, -1), ("e", 10, MAX_DUR_S + 0.1),
            ("e", 10.5, 1)]
    for lado, pct, dur in maus:
        try:
            validar(lado, pct, dur)
        except ValueError:
            continue
        raise AssertionError(f"devia recusar {(lado, pct, dur)}")
    try:
        validar("e", 10, 1, rampa=-1)
    except ValueError:
        pass
    else:
        raise AssertionError("rampa negativa devia ser recusada")


def test_validar_a_seco_limita_potencia_e_tempo():
    assert validar("e", DRY_MAX_PCT, DRY_MAX_S, seco=True).seco
    for pct, dur in ((DRY_MAX_PCT + 1, 0.5), (5, DRY_MAX_S + 0.1), (30, 10)):
        try:
            validar("e", pct, dur, seco=True)
        except ValueError:
            continue
        raise AssertionError(f"a seco devia recusar {(pct, dur)}")
    # o mesmo pedido, declarado submerso, passa
    assert validar("e", 30, 10, seco=False).pct == 30


def test_rampa_nunca_e_maior_do_que_o_impulso():
    assert validar("e", 10, 0.5, rampa=2.0).rampa == 0.5


def test_perfil_sobe_sem_passar_do_alvo_e_nunca_da_zero():
    p = validar("e", 20, 5.0, rampa=1.0)
    valores = [perfil(p, i * 0.05) for i in range(120)]
    assert min(valores) >= 1                 # zero e so do STOP
    assert max(valores) == 20
    assert valores == sorted(valores)        # monotona
    assert perfil(p, 1.0) == 20 and perfil(p, 4.9) == 20
    assert perfil(validar("e", 20, 5.0, rampa=0.0), 0.0) == 20


def test_comando_por_lado():
    p = lambda lado: validar(lado, 10, 1.0)     # noqa: E731
    assert comando(p("e"), 7) == (7, 0)
    assert comando(p("d"), 7) == (0, 7)
    assert comando(p("ambos"), 7) == (7, 7)


def test_recusa_nao_confunde_destravada_com_travada():
    assert not recusa("Parado. Propulsao DESTRAVADA")
    assert not recusa("Left: 1100 us | Right: 1000 us")
    assert recusa("PROPULSAO TRAVADA - ignorado. Enviar 'L: 0 R: 0' para destravar")
    assert recusa("FAILSAFE ATIVO - motores parados e propulsao TRAVADA")
    assert recusa("COMANDO INVALIDO - motores parados")
    assert recusa("VALOR FORA DO LIMITE SEGURO - motores parados")


# --- o impulso ---------------------------------------------------------------

def test_impulso_normal_abre_a_trava_mantem_e_para():
    link, esp, rel = montar()
    plano = validar("e", 10, 3.0)
    res = correr(link, plano, clock=rel.clock, sleep=rel.sleep, out=_silencio)
    assert res.ok and bool(res)
    assert res.motivo == ""
    cmds = pares(esp)
    assert cmds[0] == (0, 0)                  # abre a trava primeiro
    assert cmds[-1] == (0, 0)                 # e acaba parado
    meio = cmds[1:-1]
    assert meio and all(r == 0 for _, r in meio)          # so o lado pedido
    assert all(1 <= l <= 10 for l, _ in meio)             # nunca acima do pedido
    assert max(l for l, _ in meio) == 10                  # chegou ao patamar
    assert abs(len(meio) - 3.0 / HEARTBEAT_S) <= 1        # 5 Hz
    assert res.pwm_max == (1100, 1000)
    assert res.acks == res.enviados == len(meio)
    assert not any("FAILSAFE" in l for l in res.linhas)   # heartbeat a horas
    assert esp.left == esp.right == 1000                  # ESP32 ficou parado
    assert abs(res.duracao - 3.0) < 0.05


def test_impulso_nos_dois_lados_e_no_direito():
    for lado, esperado in (("ambos", (1200, 1200)), ("d", (1000, 1200))):
        link, esp, rel = montar()
        res = correr(link, validar(lado, 20, 2.0), clock=rel.clock,
                     sleep=rel.sleep, out=_silencio)
        assert res.ok, res.motivo
        assert res.pwm_max == esperado


def test_impulso_maximo_de_30s_nunca_deixa_o_failsafe_disparar():
    link, esp, rel = montar()
    res = correr(link, validar("ambos", SAFE_MAX, MAX_DUR_S), clock=rel.clock,
                 sleep=rel.sleep, out=_silencio)
    assert res.ok, res.motivo
    assert not esp.failsafe or esp.left == 1000
    assert not any("FAILSAFE" in l for l in res.linhas)
    assert max(max(p) for p in pares(esp)) == SAFE_MAX


def test_sem_ack_da_trava_nao_sai_propulsao_nenhuma():
    link, esp, rel = montar(mudo=True)
    res = correr(link, validar("e", 10, 3.0), clock=rel.clock,
                 sleep=rel.sleep, out=_silencio)
    assert not res.ok
    assert not res.destravou
    assert "trava" in res.motivo
    assert res.enviados == 0
    assert all(c == (0, 0) for c in pares(esp))   # so tentativas de STOP


def test_porta_fechada_recusa_sem_enviar():
    link = SerialLink()                           # nunca ligada
    res = correr(link, validar("e", 10, 1.0), out=_silencio)
    assert not res.ok and res.motivo == "sem ligacao serie"
    assert res.stop is None


def test_esp32_que_se_cala_a_meio_aborta_depressa_e_tenta_parar():
    link, esp, rel = montar(encrava_apos=6)       # responde a 1 STOP + 5 comandos
    res = correr(link, validar("e", 10, 10.0), clock=rel.clock,
                 sleep=rel.sleep, out=_silencio)
    assert not res.ok
    assert "sem responder" in res.motivo
    assert res.duracao < 5 * HEARTBEAT_S + ACK_TIMEOUT_S + 0.5   # nao esperou os 10 s
    assert pares(esp)[-1] == (0, 0)               # tentou parar na mesma
    assert not res.stop                           # e sabe que nao foi confirmado


def test_parar_pelo_operador_termina_e_para_confirmado():
    link, esp, rel = montar()
    res = correr(link, validar("e", 10, 10.0), clock=rel.clock, sleep=rel.sleep,
                 parar=lambda: rel.t - 100.0 > 1.5, out=_silencio)
    assert not res.ok                             # nao chegou ao fim: nao e "ok"
    assert "operador" in res.motivo
    assert res.duracao < 2.0
    assert bool(res.stop)
    assert esp.left == esp.right == 1000


def test_processo_congelado_mais_de_1s_e_apanhado_pelo_failsafe_e_aborta():
    # O Pi "congela" 1,5 s a meio: o ESP32 trava sozinho. Quando o script
    # volta, a propulsao esta travada e ele tem de dar por isso e desistir,
    # nao continuar a mandar comandos para uma trava fechada.
    rel = Relogio(salto_em=1.0, salto=1.5)
    link, esp, rel = montar(rel)
    res = correr(link, validar("e", 10, 10.0), clock=rel.clock,
                 sleep=rel.sleep, out=_silencio)
    assert not res.ok
    assert "recusou" in res.motivo
    assert any("FAILSAFE" in l for l in res.linhas)
    assert res.duracao < 4.0
    assert bool(res.stop)


def test_escrita_que_falha_aborta_e_nao_finge_que_parou():
    link, esp, rel = montar()
    original = esp.write
    estado = {"n": 0}

    def escreve(data):
        estado["n"] += 1
        if estado["n"] == 4:
            raise OSError("cabo solto")
        return original(data)

    esp.write = escreve
    res = correr(link, validar("e", 10, 5.0), clock=rel.clock,
                 sleep=rel.sleep, out=_silencio)
    assert not res.ok
    assert "escrita falhou" in res.motivo
    assert not res.stop                            # porta fechada: nao confirmado


def test_pwm_acima_do_pedido_aborta():
    class EspGuloso(FakeEsp32):
        def _diz(self, texto):
            super()._diz(texto.replace("Left: 1100", "Left: 1300"))

    rel = Relogio()
    link = SerialLink()
    link.ser = EspGuloso(clock=rel.clock)
    res = correr(link, validar("e", 10, 5.0, rampa=0.0), clock=rel.clock,
                 sleep=rel.sleep, out=_silencio)
    assert not res.ok
    assert "fora do pedido" in res.motivo
    assert bool(res.stop)


def test_pwm_no_lado_que_devia_estar_parado_aborta():
    class EspTrocado(FakeEsp32):
        def _diz(self, texto):
            super()._diz(texto.replace("Right: 1000", "Right: 1050"))

    rel = Relogio()
    link = SerialLink()
    link.ser = EspTrocado(clock=rel.clock)
    res = correr(link, validar("e", 10, 5.0), clock=rel.clock,
                 sleep=rel.sleep, out=_silencio)
    assert not res.ok and "fora do pedido" in res.motivo


def test_excecao_a_meio_para_na_mesma():
    link, esp, rel = montar()

    def parar_rebenta():
        if rel.t - 100.0 > 1.0:
            raise RuntimeError("defeito no chamador")
        return False

    res = correr(link, validar("e", 10, 5.0), clock=rel.clock, sleep=rel.sleep,
                 parar=parar_rebenta, out=_silencio)
    assert not res.ok and "excecao" in res.motivo
    assert bool(res.stop)
    assert pares(esp)[-1] == (0, 0)


def test_log_regista_inicio_tx_rx_stop_e_fim():
    link, esp, rel = montar()
    log = Log()
    res = correr(link, validar("e", 10, 1.0), log=log, clock=rel.clock,
                 sleep=rel.sleep, out=_silencio)
    assert res.ok
    pulso = log.eventos("PULSO")
    assert len(pulso) == 2 and pulso[0].startswith("inicio") and pulso[1].startswith("fim")
    assert len(log.eventos("TX")) == res.enviados
    assert any("us" in d for d in log.eventos("RX"))
    assert log.eventos("STOP")
    assert not log.eventos("ALERTA")


def test_o_esp32_falso_tem_a_trava_o_teto_e_o_failsafe():
    # Guarda contra o espelho se afastar do motor_safety.h nos tres pontos
    # de que estes testes dependem.
    rel = Relogio()
    esp = FakeEsp32(clock=rel.clock)
    esp.write(b"L: 10 R: 10\n")
    assert esp.left == 1000 and b"TRAVADA" in esp.rx          # arranca travado
    esp.write(b"L: 0 R: 0\n")
    esp.write(b"L: 10 R: 10\n")
    assert (esp.left, esp.right) == (1100, 1100)
    esp.write(b"L: 31 R: 0\n")
    assert esp.left == 1000 and b"FORA DO LIMITE" in esp.rx   # teto
    esp.write(b"L: 10 R: 10\n")
    rel.sleep(1.2)
    assert esp.in_waiting and esp.left == 1000 and esp.locked  # failsafe trava
    esp.write(b"L: 10 R: 10\n")
    assert esp.left == 1000                                   # e fica travado


# --- linha de comandos -------------------------------------------------------

def test_main_recusa_pedido_invalido_antes_de_qualquer_ligacao():
    assert main(["--fake", "--seco", "--lado", "e", "--pct", "20",
                 "--dur", "1", "--sem-log"]) == 2
    assert main(["--fake", "--seco", "--lado", "e", "--pct", "10",
                 "--dur", "3", "--sem-log"]) == 2


def test_main_fake_corre_de_ponta_a_ponta():
    # relogio verdadeiro: 0,4 s
    assert main(["--fake", "--seco", "--lado", "e", "--pct", "10",
                 "--dur", "0.4", "--rampa", "0.2", "--sem-log"]) == 0


def _run():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    import contextlib
    import io
    for fn in tests:
        with contextlib.redirect_stdout(io.StringIO()):
            fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(tests)} testes passaram.")


if __name__ == "__main__":
    _run()
