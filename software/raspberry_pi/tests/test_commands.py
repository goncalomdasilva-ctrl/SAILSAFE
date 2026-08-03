"""Testes dos caminhos de comando (sem hardware e sem terminal).

O ponto destes testes e serem executaveis exatamente na situacao que o
defeito descrevia: sem tty. Correm num pipe, num cron ou debaixo de
systemd -- se passassem so num terminal, nao provavam nada.

Correr com: python3 tests/test_commands.py
       ou:  python3 tests/test_commands.py < /dev/null | cat
"""

import os
import signal
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from commands import (CommandBus, FifoControl, KeyReader, SignalStop,
                      VALID_KEYS, DEFAULT_FIFO)


class _Tmp:
    """Caminho temporario que nao existe ainda."""

    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="sailsafe_test_")
        return os.path.join(self.dir, "ctl")

    def __exit__(self, *a):
        for f in os.listdir(self.dir):
            try:
                os.unlink(os.path.join(self.dir, f))
            except OSError:
                pass
        os.rmdir(self.dir)


def _escrever(path, texto):
    """Faz o que o operador faria: `echo texto > path`, e fecha."""
    with open(path, "w") as f:
        f.write(texto)


# --- FIFO ----------------------------------------------------------------

def test_fifo_entrega_o_comando():
    with _Tmp() as path:
        with FifoControl(path) as fifo:
            assert fifo.enabled, fifo.error
            _escrever(path, "s\n")
            assert fifo.get() == "s"


def test_fifo_sobrevive_ao_fecho_do_escritor():
    """O canal tem de continuar vivo depois do primeiro `echo`.

    E o motivo de o processo segurar tambem o descritor de escrita. Sem
    isso, o fim do primeiro `echo` fecharia o FIFO em EOF e todos os
    comandos seguintes -- incluindo o STOP -- desapareciam em silencio.
    """
    with _Tmp() as path:
        with FifoControl(path) as fifo:
            for tecla in "adns":
                _escrever(path, tecla + "\n")
                assert fifo.get() == tecla, f"perdeu o comando '{tecla}'"


def test_fifo_ignora_lixo_e_devolve_a_tecla():
    with _Tmp() as path:
        with FifoControl(path) as fifo:
            _escrever(path, "  \n\t s \n")
            assert fifo.get() == "s"


def test_fifo_aceita_maiuscula():
    with _Tmp() as path:
        with FifoControl(path) as fifo:
            _escrever(path, "S\n")
            assert fifo.get() == "s"


def test_fifo_sem_dados_devolve_none():
    with _Tmp() as path:
        with FifoControl(path) as fifo:
            assert fifo.get() is None
            assert fifo.get() is None


def test_fifo_recusa_caminho_que_nao_e_fifo():
    """Um ficheiro normal no caminho do FIFO nao pode ser usado as cegas."""
    with _Tmp() as path:
        with open(path, "w") as f:
            f.write("nao sou um fifo")
        fifo = FifoControl(path)
        assert not fifo.open()
        assert not fifo.enabled
        assert "nao e um FIFO" in fifo.error
        assert os.path.exists(path), "apagou um ficheiro que nao era dele"


def test_fifo_falha_em_diretorio_inexistente_sem_rebentar():
    fifo = FifoControl("/nao/existe/mesmo/ctl")
    assert not fifo.open()
    assert not fifo.enabled
    assert fifo.error


def test_fifo_apaga_o_que_criou_e_so_o_que_criou():
    with _Tmp() as path:
        fifo = FifoControl(path)
        assert fifo.open()
        assert os.path.exists(path)
        fifo.close()
        assert not os.path.exists(path), "deixou o FIFO para tras"

        # um FIFO pre-existente nao e dele: nao o apaga
        os.mkfifo(path)
        outro = FifoControl(path)
        assert outro.open()
        outro.close()
        assert os.path.exists(path), "apagou um FIFO que nao criou"


# --- sinal ---------------------------------------------------------------

def test_sinal_entrega_stop():
    with SignalStop() as sig:
        assert sig.enabled
        os.kill(os.getpid(), signal.SIGUSR1)
        assert sig.get() == "s"


def test_sinal_entrega_uma_vez_por_sinal():
    """Sem consumo, um STOP repetia-se em todas as voltas do loop."""
    with SignalStop() as sig:
        os.kill(os.getpid(), signal.SIGUSR1)
        assert sig.get() == "s"
        assert sig.get() is None


def test_sinal_so_sabe_dizer_stop():
    """O canal de um bit nunca pode armar nada."""
    with SignalStop() as sig:
        for _ in range(3):
            os.kill(os.getpid(), signal.SIGUSR1)
            assert sig.get() == "s"


def test_sinal_repoe_o_handler_anterior():
    anterior = signal.getsignal(signal.SIGUSR1)
    with SignalStop():
        pass
    assert signal.getsignal(signal.SIGUSR1) == anterior


def test_handler_do_sinal_so_poe_a_flag():
    """Nada de I/O dentro do handler: pode interromper qualquer linha."""
    sig = SignalStop()
    sig._handler(signal.SIGUSR1, None)
    assert sig._pendente is True


# --- teclado -------------------------------------------------------------

def test_teclado_desliga_se_sem_tty_e_nao_rebenta():
    """Era exatamente aqui que o controlo desaparecia."""
    with open(os.devnull) as f:
        kr = KeyReader(stream=f)
        kr.open()
        assert not kr.enabled
        assert kr.get() is None
        kr.close()


def test_teclado_aguenta_um_stream_sem_fileno():
    import io
    kr = KeyReader(stream=io.StringIO("s"))
    kr.open()
    assert kr.get() is None


# --- bus -----------------------------------------------------------------

def test_bus_sem_tty_mantem_stop_disponivel():
    """A propriedade que interessa: sem terminal ainda ha como parar."""
    with _Tmp() as path:
        with CommandBus(fifo_path=path, use_tty=False) as bus:
            assert bus.can_stop()
            os.kill(os.getpid(), signal.SIGUSR1)
            assert bus.get() == "s"


def test_bus_so_com_sinal_para_mas_nao_comanda():
    """Sem tty e sem FIFO o barco nao arma -- e isso e seguro."""
    with CommandBus(fifo_path=None, use_tty=False) as bus:
        assert bus.can_stop(), "o STOP nunca pode faltar"
        assert not bus.can_command()


def test_bus_da_prioridade_ao_stop():
    """Com dois comandos na mesma volta, ganha o que para o barco."""
    with _Tmp() as path:
        with CommandBus(fifo_path=path, use_tty=False) as bus:
            _escrever(path, "a\n")                    # ARM pelo FIFO
            os.kill(os.getpid(), signal.SIGUSR1)      # STOP pelo sinal
            assert bus.get() == "s"


def test_bus_entrega_comandos_do_fifo():
    with _Tmp() as path:
        with CommandBus(fifo_path=path, use_tty=False) as bus:
            assert bus.can_command()
            _escrever(path, "a\n")
            assert bus.get() == "a"


def test_bus_sem_comandos_devolve_none():
    with _Tmp() as path:
        with CommandBus(fifo_path=path, use_tty=False) as bus:
            assert bus.get() is None


def test_bus_descreve_como_se_comanda():
    """O arranque tem de dizer o comando exato, nao 'use um sinal'."""
    with _Tmp() as path:
        with CommandBus(fifo_path=path, use_tty=False) as bus:
            texto = "\n".join(bus.describe())
            assert str(os.getpid()) in texto, "nao diz o PID"
            assert path in texto, "nao diz o caminho do FIFO"
            assert "USR1" in texto


def test_bus_fecha_tudo_e_limpa():
    with _Tmp() as path:
        bus = CommandBus(fifo_path=path, use_tty=False).open()
        bus.close()
        assert not os.path.exists(path)
        assert bus.active == []


def test_teclas_validas_sao_as_da_maquina_de_estados():
    assert set(VALID_KEYS) == set("andsq")


def test_fifo_por_omissao_e_escrevivel_sem_root():
    assert DEFAULT_FIFO.startswith("/tmp/")


def _run():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(tests)} testes passaram.")


if __name__ == "__main__":
    _run()
