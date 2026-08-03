"""Caminhos de comando do operador -- teclado, FIFO e sinal.

-------------------------------------------------------------------------
O PROBLEMA

O controlo do main.py vivia todo no `KeyReader`, que le teclas do terminal
e se desliga sozinho quando `sys.stdin.isatty()` e falso. Debaixo de
systemd, de `nohup` ou de um `ssh` sem tty -- que e exatamente como isto
vai correr no barco -- nao havia ARM, nao havia DISARM e, sobretudo, nao
havia STOP. O comando de paragem existia apenas na configuracao em que
alguem estava sentado ao teclado, que e a configuracao em que ele e menos
preciso.

-------------------------------------------------------------------------
TRES CAMINHOS, COM PROPRIEDADES DIFERENTES

`KeyReader`   teclado do terminal. Comodo na bancada, ausente sem tty.
`FifoControl` FIFO nomeado: `echo s > /tmp/sailsafe.ctl`. Da controlo
              completo a partir de qualquer sessao, script ou servico.
`SignalStop`  SIGUSR1 -> STOP. Nao da controlo nenhum a nao ser parar.

A razao de existirem tres e que so o terceiro nao pode faltar. O tty
depende de haver terminal; o FIFO depende de o sistema de ficheiros o
deixar criar e de o processo ter permissoes. Um sinal nao depende de nada:
enquanto o processo existir, `kill -USR1 <pid>` chega-lhe. O caminho mais
pobre em funcionalidade e o unico com disponibilidade garantida, e e por
isso que e o que carrega o STOP.

Consequencia pratica: as funcoes que ARMAM podem nao estar disponiveis --
e isso e inofensivo, porque um barco que nao arma fica quieto. A funcao
que PARA esta sempre disponivel. A assimetria e o desenho.

O handler do sinal so poe uma flag. Nao imprime, nao escreve no log e nao
mexe na serie: o que corre dentro de um handler pode interromper qualquer
linha do programa, e as unicas operacoes seguras la dentro sao as que nao
podem ficar a meio.
"""

import os
import select
import signal
import stat
import sys

# a=ARM  n=NAV  d=DISARM  s=STOP  q=sair
VALID_KEYS = "andsq"

DEFAULT_FIFO = "/tmp/sailsafe.ctl"

# Importados so quando ha terminal: num sistema sem tty (ou noutro sistema
# operativo) estes modulos podem nem existir.
try:
    import termios
    import tty
    _TTY_OK = True
except ImportError:  # pragma: no cover
    _TTY_OK = False


class KeyReader:
    """Le teclas isoladas do terminal sem bloquear e sem Enter."""

    name = "teclado"
    can_stop = True

    def __init__(self, stream=None):
        self.stream = stream or sys.stdin
        try:
            self.fd = self.stream.fileno()
            self.enabled = _TTY_OK and self.stream.isatty()
        except (AttributeError, ValueError, OSError):
            self.fd = None
            self.enabled = False
        self.old = None

    def open(self):
        if self.enabled:
            try:
                self.old = termios.tcgetattr(self.fd)
                tty.setcbreak(self.fd)
            except (termios.error, OSError):
                self.enabled = False
        return self.enabled

    def close(self):
        if self.enabled and self.old:
            try:
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
            except (termios.error, OSError):
                pass
            self.old = None

    def get(self):
        if not self.enabled:
            return None
        try:
            if select.select([self.stream], [], [], 0)[0]:
                c = self.stream.read(1).lower()
                return c if c in VALID_KEYS else None
        except (OSError, ValueError):
            self.enabled = False
        return None

    # Mantem o uso antigo `with KeyReader() as keys:` a funcionar.
    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *a):
        self.close()


class FifoControl:
    """Comandos por FIFO nomeado: `echo s > /tmp/sailsafe.ctl`.

    O FIFO e aberto para leitura E para escrita pelo proprio processo. O
    descritor de escrita nunca e usado para escrever: existe so para
    garantir que ha sempre um escritor. Sem ele, o instante em que o
    ultimo `echo` termina fecharia o FIFO em EOF e as leituras seguintes
    devolveriam vazio para sempre -- o canal de controlo morria depois do
    primeiro comando.
    """

    name = "fifo"
    can_stop = True

    def __init__(self, path=DEFAULT_FIFO, mode=0o600):
        self.path = path
        self.mode = mode
        self.rfd = None
        self.wfd = None
        self.enabled = False
        self.error = ""
        self._criado = False

    def open(self):
        try:
            if os.path.exists(self.path):
                if not stat.S_ISFIFO(os.stat(self.path).st_mode):
                    self.error = f"{self.path} existe e nao e um FIFO"
                    return False
            else:
                os.mkfifo(self.path, self.mode)
                self._criado = True
            self.rfd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
            # segura o FIFO aberto do lado do escritor (ver docstring)
            self.wfd = os.open(self.path, os.O_WRONLY | os.O_NONBLOCK)
            self.enabled = True
            return True
        except OSError as e:
            self.error = str(e)
            self.close()
            return False

    def close(self):
        for attr in ("rfd", "wfd"):
            fd = getattr(self, attr)
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
                setattr(self, attr, None)
        if self._criado:
            try:
                os.unlink(self.path)
            except OSError:
                pass
            self._criado = False
        self.enabled = False

    def get(self):
        """Devolve a proxima tecla valida escrita no FIFO, ou None.

        Le tudo o que estiver pendente e devolve a PRIMEIRA tecla valida.
        Um `echo s` manda "s\\n"; o newline e o resto do lixo sao
        ignorados em vez de recusados, porque a alternativa -- exigir o
        formato exato -- transformava um erro de digitacao num STOP que
        nao acontece.
        """
        if not self.enabled:
            return None
        try:
            dados = os.read(self.rfd, 256)
        except BlockingIOError:
            return None
        except OSError:
            self.enabled = False
            return None
        for c in dados.decode("utf-8", errors="ignore").lower():
            if c in VALID_KEYS:
                return c
        return None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *a):
        self.close()


class SignalStop:
    """SIGUSR1 -> STOP. O caminho que nao pode faltar.

    Nao arma, nao navega, nao desarma: so para. Um sinal e um canal de um
    bit, e o unico bit que tem de chegar sempre e o que trava o barco.
    """

    name = "sinal"
    can_stop = True

    SIGNALS = (signal.SIGUSR1,)

    def __init__(self):
        self._pendente = False
        self.enabled = False
        self._anteriores = {}

    def open(self):
        try:
            for s in self.SIGNALS:
                self._anteriores[s] = signal.getsignal(s)
                signal.signal(s, self._handler)
            self.enabled = True
        except (ValueError, OSError, AttributeError):
            # signal.signal so funciona na thread principal
            self.enabled = False
        return self.enabled

    def close(self):
        for s, anterior in self._anteriores.items():
            try:
                signal.signal(s, anterior)
            except (ValueError, OSError, TypeError):
                pass
        self._anteriores.clear()
        self.enabled = False

    def _handler(self, signum, frame):
        # So poe a flag. Ver nota no cabecalho do modulo.
        self._pendente = True

    def get(self):
        if self._pendente:
            self._pendente = False
            return "s"
        return None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *a):
        self.close()


class CommandBus:
    """Junta os caminhos de comando e devolve uma tecla de cada vez.

    A ordem de consulta poe o STOP por sinal em primeiro lugar. Numa volta
    em que cheguem dois comandos por caminhos diferentes, ganha o que para
    o barco -- e a mesma prioridade absoluta que o STOP ja tem na maquina
    de estados.
    """

    def __init__(self, sources=None, fifo_path=DEFAULT_FIFO, use_tty=True):
        if sources is None:
            sources = []
            sources.append(SignalStop())
            if fifo_path:
                sources.append(FifoControl(fifo_path))
            if use_tty:
                sources.append(KeyReader())
        self.sources = sources

    def open(self):
        for s in self.sources:
            s.open()
        return self

    def close(self):
        for s in reversed(self.sources):
            s.close()

    def get(self):
        for s in self.sources:
            if not getattr(s, "enabled", False):
                continue
            k = s.get()
            if k:
                return k
        return None

    @property
    def active(self):
        return [s for s in self.sources if getattr(s, "enabled", False)]

    def can_stop(self):
        """Ha algum caminho capaz de entregar um STOP?"""
        return any(getattr(s, "can_stop", False) for s in self.active)

    def can_command(self):
        """Ha algum caminho capaz de entregar ARM/NAV/DISARM?

        O SignalStop nao conta: so sabe dizer 's'. Sem nenhum caminho de
        comando o processo corre e nao arma -- inofensivo, mas convem
        dizer-se em vez de o operador descobrir a carregar em teclas que
        ninguem le.
        """
        return any(s.name in ("teclado", "fifo") for s in self.active)

    def describe(self):
        """Linhas a imprimir no arranque a dizer como se comanda isto."""
        linhas = []
        for s in self.sources:
            if not getattr(s, "enabled", False):
                motivo = getattr(s, "error", "") or "indisponivel"
                linhas.append(f"  [ ] {s.name}: {motivo}")
            elif s.name == "teclado":
                linhas.append("  [x] teclado: a=ARM  n=NAV  d=DISARM  s=STOP  q=sair")
            elif s.name == "fifo":
                linhas.append(f"  [x] fifo: echo s > {s.path}   (a/n/d/s/q)")
            elif s.name == "sinal":
                linhas.append(f"  [x] sinal: kill -USR1 {os.getpid()}   (STOP)")
        return linhas

    def __enter__(self):
        return self.open()

    def __exit__(self, *a):
        self.close()
