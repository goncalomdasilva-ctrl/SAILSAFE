#!/usr/bin/env python3
"""Ensaio do processo INTEIRO contra hardware falso. Sem GPS e sem ESP32.

Os outros bench exercitam um sensor cada um. Este exercita o main.py: o
ciclo de estados, a serie, o GPS e as decisoes que os ligam. E a diferenca
entre "as pecas passam nos testes" e "o processo faz a coisa certa quando
o GPS se cala a meio de uma missao" -- que sao perguntas diferentes e so a
segunda e a que interessa na agua.

Como funciona: dois pseudo-terminais. Um debita tramas NMEA validas a 1 Hz
e faz de NEO-8M; o outro le os comandos de motor e responde ao STOP com o
ack da trava, fazendo de ESP32. O main.py corre como corre no Pi, com
--gps-port e --esp32-port apontados a eles, e nao sabe a diferenca.

O ensaio percorre a sequencia que interessa:
  1. ARM cedo demais, com a janela do ponto de regresso ainda por encher
  2. ARM a serio, com o ponto gravado
  3. NAV
  4. o GPS CALA-SE a meio -- e e aqui que se ve se o processo vai mesmo a
     estado seguro, ou se continua a navegar sobre uma posicao velha

Correr com:  python3 -m tools.system_bench
Sai com codigo 1 se alguma verificacao falhar, para poder entrar no lote.

NAO substitui os testes unitarios nem o ensaio na agua. O que apanha, e
que os testes unitarios por construcao nao apanham, sao os defeitos que
so existem na COSTURA entre as pecas: uma trama RMC sem HDOP a rebentar o
registo, um ponto de regresso gravado por um ARM que foi recusado, uma
mensagem de erro presa no motivo do arranque a frio. Os tres foram
encontrados assim.
"""

import os
import pty
import re
import subprocess
import sys
import threading
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIFO = "/tmp/sailsafe_system_bench.ctl"

# Lisboa, ~38 41,5' N / 9 08,5' W -- o mesmo ponto dos testes
LAT_ESPERADA = "38.691667"


def nmea(corpo):
    """Fecha uma trama com o checksum certo."""
    soma = 0
    for c in corpo:
        soma ^= ord(c)
    return f"${corpo}*{soma:02X}\r\n".encode()


def main():
    gps_m, gps_s = pty.openpty()
    esp_m, esp_s = pty.openpty()
    porta_gps, porta_esp = os.ttyname(gps_s), os.ttyname(esp_s)
    print(f"[bench] GPS falso em {porta_gps} | ESP32 falso em {porta_esp}",
          flush=True)

    calar = threading.Event()

    def alimenta_gps():
        i = 0
        while not calar.is_set():
            hh = f"12{i // 60:02d}{i % 60:02d}.00"
            os.write(gps_m, nmea(f"GPGGA,{hh},3841.500,N,00908.500,W,"
                                 f"1,09,0.9,20.0,M,,M,,"))
            i += 1
            time.sleep(1.0)
        print("[bench] >>> GPS CALADO <<<", flush=True)

    def faz_de_esp32():
        """Responde a 'L: 0 R: 0' com o ack que destrava a propulsao."""
        buf = b""
        while True:
            try:
                buf += os.read(esp_m, 256)
            except OSError:
                return
            while b"\n" in buf:
                linha, buf = buf.split(b"\n", 1)
                m = re.match(r"L:\s*(-?\d+)\s*R:\s*(-?\d+)",
                             linha.decode(errors="replace").strip())
                if m and m.group(1) == "0" and m.group(2) == "0":
                    os.write(esp_m, b"PROPULSAO DESTRAVADA\r\n")

    threading.Thread(target=alimenta_gps, daemon=True).start()
    threading.Thread(target=faz_de_esp32, daemon=True).start()

    # O FIFO e criado AQUI, e nao pelo main.py: escrever para um caminho
    # que ainda nao e FIFO deixa la um ficheiro normal, e o processo
    # arranca sem caminho de comando nenhum.
    if os.path.exists(FIFO):
        os.unlink(FIFO)
    os.mkfifo(FIFO)

    p = subprocess.Popen(
        [sys.executable, "main.py", "--gps", "--gps-port", porta_gps,
         "--esp32-port", porta_esp, "--sim", "--no-tty",
         "--control-fifo", FIFO],
        cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    linhas = []

    def le():
        for linha in p.stdout:
            linhas.append(linha.rstrip())
            print("   " + linha.rstrip(), flush=True)

    threading.Thread(target=le, daemon=True).start()

    def cmd(c):
        with open(FIFO, "w") as f:
            f.write(c + "\n")

    def marca(t):
        print(f"\n[bench] --- {t} ---", flush=True)

    limite = time.time() + 20
    while time.time() < limite:
        if any("Caminhos de comando" in linha for linha in linhas):
            break
        time.sleep(0.2)
    else:
        print("[bench] o processo nunca anunciou os caminhos de comando")
    time.sleep(0.5)

    marca("1. ARM cedo demais: a janela do regresso ainda nao tem fixes")
    cmd("a")
    time.sleep(2)
    regressos_antes = sum("[REGRESSO]" in linha for linha in linhas)

    marca("2. esperar pela janela e armar a serio")
    time.sleep(6)
    cmd("a")
    time.sleep(2)

    marca("3. NAV")
    cmd("d")
    time.sleep(1)
    cmd("n")
    time.sleep(3)

    marca("4. calar o GPS a meio da missao")
    calar.set()
    time.sleep(8)

    cmd("q")
    time.sleep(1)
    p.terminate()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()

    texto = "\n".join(linhas)
    i_recusa = texto.find("ARM recusado: ponto de regresso")
    i_regresso = texto.find("[REGRESSO]")

    verificacoes = [
        ("o GPS falso abriu e deu posicao",
         f"[GPS] {LAT_ESPERADA}" in texto),
        ("ARM sem janela cheia e recusado",
         i_recusa >= 0),
        ("um ARM recusado NAO grava o ponto de regresso",
         regressos_antes == 0),
        ("o ponto so se grava no ARM que chega ao fim",
         i_regresso > i_recusa >= 0),
        ("armou depois de a janela encher",
         "[STATE] ARMED" in texto),
        ("entrou em NAV",
         "[STATE] NAV" in texto),
        ("uma falha de posicao isolada nao aborta",
         "sem posicao (1/3" in texto),
        ("o GPS calado leva a estado seguro",
         "Posicao perdida -> DISARMED" in texto),
        ("o aborto distingue 'calado' de 'sem leituras'",
         "modulo calado" in texto),
        ("o STOP do aborto foi confirmado pelo ESP32",
         "DESTRAVADA" in texto),
    ]

    print("\n===== VEREDICTO =====")
    falhas = 0
    for nome, cond in verificacoes:
        if not cond:
            falhas += 1
        print(f"  {'OK   ' if cond else 'FALHA'} {nome}")
    print(f"\n{len(verificacoes) - falhas}/{len(verificacoes)} verificacoes "
          f"passaram")

    os.unlink(FIFO)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
