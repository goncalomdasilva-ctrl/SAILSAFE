#!/usr/bin/env python3
"""Gera o procedimento de ensaio de sensores do SAILSAFE em PDF A4.

Sessao sem propulsao e sem bateria de potencia: primeira ligacao do
BNO055, do ADS1015 e do NEO-8M ao Raspberry Pi.
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

import os
SAIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "SAILSAFE_procedimento_sensores_v1.pdf")

AZUL = colors.HexColor("#123A5E")
CINZA = colors.HexColor("#5A6672")
VERM = colors.HexColor("#A32020")
FUNDO_AVISO = colors.HexColor("#FBEAEA")
FUNDO_CAMPO = colors.HexColor("#F2F4F6")
LINHA = colors.HexColor("#C8CFD6")

ss = getSampleStyleSheet()

H1 = ParagraphStyle("H1", parent=ss["Normal"], fontName="Helvetica-Bold",
                    fontSize=15, leading=18, textColor=AZUL, spaceAfter=1)
SUB = ParagraphStyle("SUB", parent=ss["Normal"], fontName="Helvetica",
                     fontSize=9.5, leading=12, textColor=CINZA, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=ss["Normal"], fontName="Helvetica-Bold",
                    fontSize=10.5, leading=13, textColor=colors.white,
                    spaceBefore=0, spaceAfter=0)
BODY = ParagraphStyle("BODY", parent=ss["Normal"], fontName="Helvetica",
                      fontSize=8.6, leading=11, alignment=TA_LEFT)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=7.6, leading=9.6,
                       textColor=CINZA)
MONO = ParagraphStyle("MONO", parent=BODY, fontName="Courier-Bold",
                      fontSize=8.4, leading=10.6)
AVISO = ParagraphStyle("AVISO", parent=BODY, fontSize=8.8, leading=11.4,
                       textColor=VERM)
AVISOB = ParagraphStyle("AVISOB", parent=AVISO, fontName="Helvetica-Bold")


def seccao(texto):
    t = Table([[Paragraph(texto, H2)]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    return [Spacer(1, 7), t, Spacer(1, 4)]


def passo(num, titulo, linhas, campos=None, nota=None):
    """Um passo com caixa para marcar, corpo e campos de registo."""
    corpo = [Paragraph(f"<b>{num}. {titulo}</b>", BODY)]
    for tipo, txt in linhas:
        if tipo == "t":
            corpo.append(Paragraph(txt, BODY))
        elif tipo == "c":
            corpo.append(Spacer(1, 1.5))
            corpo.append(Paragraph(txt, MONO))
            corpo.append(Spacer(1, 1.5))
        elif tipo == "e":
            corpo.append(Paragraph(f"<b>Esperado:</b> {txt}", BODY))
    if nota:
        corpo.append(Paragraph(nota, SMALL))
    if campos:
        dados = [[Paragraph(f"<font size=7.4>{c}</font>", BODY), ""] for c in campos]
        tc = Table(dados, colWidths=[42 * mm, 122 * mm])
        tc.setStyle(TableStyle([
            ("BACKGROUND", (1, 0), (1, -1), FUNDO_CAMPO),
            ("LINEBELOW", (1, 0), (1, -1), 0.4, LINHA),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
        ]))
        corpo.append(Spacer(1, 2))
        corpo.append(tc)

    t = Table([["", corpo]], colWidths=[9 * mm, 171 * mm])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (0, 0), 0.9, AZUL),
        ("VALIGN", (0, 0), (0, 0), "TOP"),
        ("VALIGN", (1, 0), (1, 0), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, LINHA),
    ]))
    # a caixa de marcar tem de ser um quadrado pequeno, nao a altura toda
    quad = Table([[""]], colWidths=[5 * mm], rowHeights=[5 * mm])
    quad.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.9, AZUL)]))
    t = Table([[quad, corpo]], colWidths=[9 * mm, 171 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, LINHA),
    ]))
    return KeepTogether(t)


def caixa_aviso(titulo, itens, cor_fundo=FUNDO_AVISO, cor_borda=VERM):
    corpo = [Paragraph(titulo, AVISOB)]
    for i in itens:
        corpo.append(Paragraph(i, AVISO))
    t = Table([[corpo]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), cor_fundo),
        ("BOX", (0, 0), (-1, -1), 1.1, cor_borda),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def cabecalho_campos():
    campos = [["Data", "", "Hora de inicio", ""],
              ["Operador", "", "Hora de fim", ""],
              ["Commit (git log -1)", "", "Porta serie (COM)", ""]]
    dados = []
    for a, b, c, d in campos:
        dados.append([Paragraph(f"<font size=7.6><b>{a}</b></font>", BODY), b,
                      Paragraph(f"<font size=7.6><b>{c}</b></font>", BODY), d])
    t = Table(dados, colWidths=[33 * mm, 57 * mm, 33 * mm, 57 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (1, 0), (1, -1), FUNDO_CAMPO),
        ("BACKGROUND", (3, 0), (3, -1), FUNDO_CAMPO),
        ("GRID", (0, 0), (-1, -1), 0.4, LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t



def tabela_referencia():
    linhas = [["O quê", "Onde", "Esperado"],
              ["BNO055", "I2C, barramento 1", "0x28  (0x29 com ADR a 3V3)"],
              ["ADS1015", "I2C, barramento 1", "0x48  (ADDR a GND)"],
              ["ESP32", "USB", "/dev/ttyUSB0  (CH341)"],
              ["NEO-8M", "UART do GPIO", "/dev/serial0 -> ttyAMA0, 9600 8N1"],
              ["ADS1015 a 3,3 V", "A0, fio direto", "~1650 contagens, ~3,300 V"]]
    dados = [[Paragraph(f"<font size=7.6>{c}</font>",
                        MONO if i and j != 0 else BODY) for j, c in enumerate(r)]
             for i, r in enumerate(linhas)]
    t = Table(dados, colWidths=[38 * mm, 44 * mm, 98 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(CINZA)
    canvas.drawString(15 * mm, 10 * mm,
                      "SAILSAFE — procedimento de ensaio de sensores v1 — "
                      "sessão SEM propulsão e SEM bateria de potência")
    canvas.drawRightString(195 * mm, 10 * mm, f"pagina {doc.page}")
    canvas.setStrokeColor(LINHA)
    canvas.setLineWidth(0.4)
    canvas.line(15 * mm, 13 * mm, 195 * mm, 13 * mm)
    canvas.restoreState()


def construir():
    doc = BaseDocTemplate(SAIDA, pagesize=A4,
                          leftMargin=15 * mm, rightMargin=15 * mm,
                          topMargin=14 * mm, bottomMargin=17 * mm,
                          title="SAILSAFE - Procedimento de ensaio de sensores",
                          author="Goncalo Martins da Silva")
    frame = Frame(15 * mm, 17 * mm, 180 * mm, A4[1] - 31 * mm, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=rodape)])

    s = []
    s.append(Paragraph("SAILSAFE &mdash; Procedimento de ensaio de sensores", H1))
    s.append(Paragraph(
        "Primeira ligação do BNO055, do ADS1015 e do NEO-8M ao Raspberry Pi. "
        "<b>Sem propulsão e sem bateria de potência.</b> Preencher à medida "
        "que se avança &mdash; o valor escrito na altura vale mais do que a "
        "memória no fim.", SUB))
    s.append(cabecalho_campos())
    s.append(Spacer(1, 7))

    s.append(caixa_aviso(
        "NÃO FAZER NESTA SESSÃO",
        ["&bull; <b>Não ligar nenhuma bateria diretamente a uma entrada do ADS1015.</b> "
         "12,6 V numa entrada excedem o máximo absoluto (VDD + 0,3 = 5,3 V) e "
         "destroem o chip. Tensão de bateria só entra pelo divisor 10k/2k, e só "
         "depois de a saída desse divisor ter sido <b>medida ao multímetro</b> "
         "&mdash; secção G.",
         "&bull; Não ligar bateria ao ESC, não ligar motor, não montar "
         "hélice nem jato. Continua a valer a regra: sem loop key não há "
         "energização de ESC.",
         "&bull; Não alimentar o Raspberry Pi ao mesmo tempo pela USB-C e pelos "
         "pinos GPIO. Um caminho de alimentação de cada vez.",
         "&bull; Não pôr 5 V no pino de dados do NEO-8M. O GPIO do Pi é "
         "de 3,3 V e não é tolerante a 5 V."]))
    s.append(Spacer(1, 6))

    s.append(caixa_aviso(
        "CRITÉRIOS DE ABORTO &mdash; parar e não continuar",
        ["&bull; O <font face='Courier-Bold'>i2cdetect</font> não mostra os dois "
         "endereços &rarr; parar e verificar cablagem <b>antes</b> de correr "
         "código. Um sensor que não responde no barramento não se resolve "
         "em Python.",
         "&bull; Um canal do ADS lê <b>saturado</b> com 3,3 V à entrada &rarr; "
         "o PGA ou a ligação estão errados. Não prosseguir para "
         "tensões maiores.",
         "&bull; O Pi reinicia, aparece o raio de subtensão ou "
         "<font face='Courier-Bold'>vcgencmd get_throttled</font> deixa de dar "
         "<font face='Courier-Bold'>0x0</font> &rarr; alimentação "
         "insuficiente para o conjunto.",
         "&bull; Cheiro, calor anómalo ou fumo &rarr; cortar a alimentação "
         "imediatamente.",
         "&bull; O BNO055 não passa de <font face='Courier-Bold'>sys=0</font> ao "
         "fim de 5 min de calibração &rarr; o rumo desta sessão não "
         "serve para nada e não deve ser registado como válido."]))
    s.append(Spacer(1, 7))

    s.append(Paragraph("<b>Referência rápida &mdash; o que deve aparecer</b>",
                       BODY))
    s.append(Spacer(1, 3))
    s.append(tabela_referencia())
    s.append(Paragraph(
        "O ADS1015 tem LSB de 2,000 mV no fundo de escala de ±4,096 V. Com o "
        "ganho por omissão de ±2,048 V, 3,3 V à entrada dão "
        "saturação &mdash; o que é exatamente o que o passo 11 usa para "
        "confirmar que a deteção funciona.", SMALL))

    # ---------------------------------------------------------------- A
    s += seccao("A &mdash; Antes de ligar seja o que for")
    s.append(passo(1, "Curto-circuito entre 5 V e GND, com tudo desligado", [
        ("t", "Multímetro em continuidade, ponta a ponta em cada breadboard: "
              "5 V contra GND e 3,3 V contra GND."),
        ("e", "sem continuidade em nenhum dos pares"),
    ], campos=["5 V &ndash; GND", "3,3 V &ndash; GND"],
       nota="É o único passo que se faz antes de haver energia, e o único "
            "que não se pode fazer depois."))
    s.append(passo(2, "Massa comum entre as placas", [
        ("t", "Confirmar continuidade entre o GND do Pi, o do ESP32, o do BNO055 e o "
              "do ADS1015."),
        ("e", "continuidade em todos &mdash; uma massa em falta dá leituras "
              "plausíveis e erradas, não dá erro"),
    ], campos=["Pi &ndash; ESP32", "Pi &ndash; BNO055", "Pi &ndash; ADS1015"]))
    s.append(passo(3, "Tensões de alimentação medidas, não assumidas", [
        ("t", "Com o Pi ligado e antes de ligar os sensores, medir os pinos que "
              "vão alimentá-los."),
        ("e", "3,3 V entre 3,25 e 3,35 V; 5 V entre 4,90 e 5,10 V"),
    ], campos=["3,3 V medido", "5 V medido"]))

    # ---------------------------------------------------------------- B
    s += seccao("B &mdash; Barramento I2C")
    s.append(passo(4, "Os dois sensores aparecem no barramento", [
        ("t", "Com o BNO055 e o ADS1015 ligados a SDA/SCL e alimentados:"),
        ("c", "sudo apt install -y i2c-tools &amp;&amp; i2cdetect -y 1"),
        ("e", "<font face='Courier-Bold'>28</font> e "
              "<font face='Courier-Bold'>48</font> na grelha"),
    ], campos=["Endereços vistos", "Falta algum? (qual)"],
       nota="Se faltar um: alimentação, SDA/SCL trocados ou o I2C "
            "desativado no raspi-config. Não continuar sem os dois."))
    s.append(passo(5, "Dependências instaladas", [
        ("c", "pip install smbus2 pyserial adafruit-circuitpython-bno055"),
        ("t", "Se o pip recusar por ambiente gerido, acrescentar "
              "<font face='Courier-Bold'>--break-system-packages</font>."),
    ]))

    # ---------------------------------------------------------------- C
    s += seccao("C &mdash; BNO055 (rumo)")
    s.append(passo(6, "Calibrar e ver os contadores a subir", [
        ("c", "cd software/raspberry_pi &amp;&amp; python3 -m tools.heading_bench"),
        ("t", "<b>gyro:</b> pousar parado alguns segundos. <b>accel:</b> inclinar em "
              "6 posições, parando em cada uma. <b>mag:</b> movimento em oito, "
              "amplo e lento. <b>sys</b> sobe sozinho quando os outros três "
              "chegarem a 3."),
        ("e", "<font face='Courier-Bold'>sys=3</font> e "
              "<font face='Courier-Bold'>mag=3</font>"),
    ], campos=["sys/gyro/accel/mag ao fim de 2 min", "Tempo até sys=3"],
       nota="Calibrar com o sensor no sítio definitivo, na placa de acrílico, "
            "com o Pi e o ESP32 a trabalhar. Uma calibração feita com a placa "
            "na mão não vale para o conjunto montado."))
    s.append(passo(7, "Declinação magnética consultada, não adivinhada", [
        ("t", "Consultar a calculadora da NOAA/NCEI para a data e as coordenadas do "
              "ensaio e anotar o valor. Lisboa anda na ordem de &minus;2°, mas o "
              "número a usar é o consultado."),
        ("c", "python3 -m tools.heading_bench --declinacao &lt;valor&gt;"),
    ], campos=["Declinação consultada", "Data da consulta"],
       nota="É erro sistemático: não desaparece com médias nem com "
            "mais amostras. Enquanto ficar a zero, o rumo verdadeiro está errado "
            "por esse valor em todas as leituras."))
    s.append(passo(8, "Offset de montagem da placa", [
        ("t", "Apontar a proa a uma direção conhecida (bússola, ou uma "
              "parede de orientação conhecida) e anotar o que o sensor diz. "
              "Repetir três vezes, rodando o conjunto todo entre medições."),
        ("e", "as três diferenças coincidem dentro de poucos graus"),
    ], campos=["Referência usada", "Leituras (3)", "Offset a usar"]))
    s.append(passo(9, "O ambiente magnético da placa de acrílico", [
        ("t", "Sem mexer no conjunto, anotar o rumo com o Pi e o ESP32 em repouso e "
              "outra vez com ambos a trabalhar."),
        ("e", "diferença de poucos graus"),
        ("t", "Repetir mais tarde com as baterias e os ESCs montados, que é quando "
              "o campo muda a sério."),
    ], campos=["Em repouso", "A trabalhar", "Diferença"],
       nota="Uma variação grande aqui quer dizer que o BNO055 está "
            "demasiado perto de corrente ou de ferro, e isso resolve-se movendo o "
            "sensor &mdash; não resolve em software."))

    # ---------------------------------------------------------------- D
    s += seccao("D &mdash; ADS1015 (sense), ainda sem divisores")
    s.append(passo(10, "A0 ligado ao 3,3 V do próprio Pi", [
        ("t", "Um fio direto do pino de 3,3 V à entrada A0. Mais nada ligado ao ADS."),
        ("c", "python3 -m tools.sense_bench --once"),
        ("e", "coluna <b>V no ADC</b> ≈ 3,300 V, contagens ≈ 1650, nenhuma "
              "linha com <i>saturado</i>"),
        ("t", "Medir o mesmo pino com o multímetro e anotar as duas leituras lado "
              "a lado."),
    ], campos=["Contagens", "V no ADC", "V no multímetro", "Diferença"],
       nota="A coluna de <i>valor</i> vai mostrar cerca de 19,8 V, e está certa "
            "assim: o código está a aplicar o divisor de 1/6 a uma entrada "
            "que não o tem. O que se verifica neste passo é a coluna do ADC."))
    s.append(passo(11, "Ver a avaria de propósito", [
        ("c", "python3 -m tools.sense_bench --once --ganho-errado"),
        ("e", "os três canais de tensão dizem <i>saturado</i>"),
    ], campos=["Detetou saturação? (S/N)"],
       nota="Confirma, sem risco nenhum, que a deteção de saturação "
            "funciona &mdash; antes de haver uma bateria ligada, que é quando "
            "deixaria de ser um exercício."))
    s.append(passo(12, "NÃO calibrar com o fio direto", [
        ("t", "A calibração de um ponto corrige o ganho do <b>circuito "
              "montado</b>. Feita agora, com o fio direto, ficava a compensar a "
              "ausência do divisor e teria de ser deitada fora. A calibração "
              "acontece na secção G, sobre o circuito montado."),
        ("t", "Se por engano correr o <font face='Courier-Bold'>--calibrar</font>, "
              "apagar o ficheiro:"),
        ("c", "rm software/raspberry_pi/config/calibration.json"),
    ], campos=["Ficheiro de calibração ausente no fim? (S/N)"]))

    # ---------------------------------------------------------------- E
    s += seccao("E &mdash; NEO-8M na UART do GPIO")
    s.append(passo(13, "Consola série desligada, UART por hardware ligada", [
        ("c", "sudo raspi-config"),
        ("t", "Interface Options &rarr; Serial Port &rarr; consola de login: "
              "<b>NÃO</b>; porta série por hardware: <b>SIM</b>."),
    ]))
    s.append(passo(14, "Fixar a PL011 em vez da mini-UART", [
        ("t", "No Pi 4, <font face='Courier-Bold'>/dev/serial0</font> aponta por "
              "omissão para a mini-UART, cujo baud está preso ao relógio "
              "do core: o GPS ora lê ora dá lixo conforme a carga do CPU."),
        ("c", "sudo nano /boot/firmware/config.txt   # acrescentar: dtoverlay=disable-bt"),
        ("c", "sudo reboot"),
        ("c", "ls -l /dev/serial0"),
        ("e", "aponta para <font face='Courier-Bold'>ttyAMA0</font>, não para "
              "<font face='Courier-Bold'>ttyS0</font>"),
    ], campos=["serial0 aponta para", "Reiniciou bem? (S/N)"]))
    s.append(passo(15, "Ligação cruzada e alimentação a 3,3 V", [
        ("t", "<b>TX do módulo</b> &rarr; GPIO15 (RXD). <b>RX do módulo</b> "
              "&rarr; GPIO14 (TXD). VCC a 3,3 V, GND ao GND. Cruzados &mdash; TX com "
              "TX não dá erro, dá silêncio."),
    ], campos=["Conferido à vista? (S/N)"]))
    s.append(passo(16, "As tramas chegam e passam o checksum", [
        ("c", "python3 -m tools.gps_bench --cru"),
        ("e", "linhas <font face='Courier-Bold'>$GPGGA</font> ou "
              "<font face='Courier-Bold'>$GNGGA</font> marcadas com "
              "<font face='Courier-Bold'>ok</font>"),
        ("t", "Nada a chegar &rarr; TX/RX ou a consola ainda ativa. Bytes a chegar mas "
              "nada a passar o checksum &rarr; quase sempre o baud errado."),
    ], campos=["Tramas vistas", "% rejeitadas", "Causa, se houve"]))
    s.append(passo(17, "Primeira fixação, com a antena a ver céu", [
        ("t", "Junto a uma janela aberta ou na rua. A fixação a frio leva "
              "minutos e não acontece dentro de casa com o teto pelo meio."),
        ("e", "<font face='Courier-Bold'>primeira fixação ao fim de N s</font>, "
              "depois HDOP a descer"),
    ], campos=["Tempo até ao primeiro fix", "Satélites", "HDOP estável"]))
    s.append(passo(18, "Dispersão com o barco parado", [
        ("t", "Deixar 10 minutos a correr sem mexer na antena e anotar a "
              "latitude/longitude mínima e máxima observadas."),
        ("t", "É este número, e não o catálogo do módulo, que "
              "diz qual tem de ser o raio de chegada de um waypoint e a "
              "tolerância do ponto de regresso."),
    ], campos=["Variação observada (m)", "Raio de chegada proposto"]))

    # ---------------------------------------------------------------- F
    s += seccao("F &mdash; Os três em conjunto")
    s.append(passo(19, "O ESP32 continua onde estava", [
        ("t", "Com o GPS na UART e o ESP32 na USB, confirmar que o ESP32 continua a "
              "ser encontrado e que o GPS não lhe roubou o nome."),
        ("c", "ls -l /dev/serial/by-id/"),
        ("e", "o CH341 do ESP32 com um nome estável, independente da ordem de "
              "ligação"),
    ], campos=["Nome by-id do ESP32"],
       nota="É a informação que falta para fechar a pendência da "
            "porta série por by-id, em aberto desde 4 de agosto."))
    s.append(passo(20, "Alimentação aguenta o conjunto", [
        ("t", "Com tudo ligado e o <font face='Courier-Bold'>main.py</font> a correr:"),
        ("c", "vcgencmd get_throttled"),
        ("e", "<font face='Courier-Bold'>throttled=0x0</font>"),
    ], campos=["Valor lido", "Houve subtensão? (S/N)"]))
    s.append(passo(21, "Medir a bateria da eletrónica, para o CAD", [
        ("t", "Medir a LiPo 3S 2200 real: comprimento, largura e altura, com o cabo "
              "dobrado como vai ficar."),
        ("t", "O modelo 3D tem-na a 35 &times; 105 &times; 25 mm, que é medida de "
              "uma 2S. Se a real for maior, o alojamento e o recorte do acrílico "
              "mudam."),
    ], campos=["C × L × A medidos", "Cabe no alojamento? (S/N)"]))

    # ---------------------------------------------------------------- G
    s += seccao("G &mdash; Primeiro divisor 10k/2k (se houver tempo)")
    s.append(passo(22, "Montar um divisor e medi-lo <b>antes</b> de o ligar ao ADS", [
        ("t", "10 k&Omega; do positivo ao nó de sense, 2 k&Omega; do nó à massa. Alimentar "
              "com a bateria da eletrónica ou com fonte de bancada, e medir a entrada e a "
              "saída com o multímetro."),
        ("t", "O fio só vai ao ADS depois deste número estar conferido."),
        ("e", "saída &asymp; 1/6 da entrada &mdash; 2,10 V para 12,6 V"),
    ], campos=["V de entrada", "V de saída", "Rácio obtido"],
       nota="Trocar os dois resistores dá 5/6 em vez de 1/6, ou seja 10,5 V numa entrada "
            "que aguenta 4,096 V. É este passo que apanha a troca, e é por isso que "
            "acontece com o multímetro e não com o ADS ligado."))
    s.append(passo(23, "Ligar ao A0 e comparar as duas leituras", [
        ("c", "python3 -m tools.sense_bench --once"),
        ("e", "coluna de <b>valor</b> a coincidir com o multímetro dentro de cerca de "
              "1 V &mdash; é a tolerância dos resistores, ainda por calibrar"),
    ], campos=["Valor no sense_bench", "V no multímetro", "Diferença"]))
    s.append(passo(24, "Calibrar, e só com o condensador já montado", [
        ("c", "python3 -m tools.sense_bench --calibrar a0 &lt;V do multímetro&gt;"),
        ("t", "A calibração corrige o ganho do circuito tal como ele está. Feita sem o "
              "condensador, tem de ser refeita depois de o pôr &mdash; a fuga de um "
              "eletrolítico entra no rácio."),
        ("t", "Qualquer valor entre 1 e 4,7 µF serve para o filtro. Sem condensador "
              "nenhum dá para medir e calibrar, mas passa a ser obrigatório antes do "
              "primeiro ensaio com motores a girar."),
    ], campos=["Condensador montado? (valor)", "Fator obtido"]))

    # ---------------------------------------------------------------- H
    s += seccao("H &mdash; Encerramento")
    s.append(passo(25, "Registo final", [
        ("t", "Guardar a saída do <font face='Courier-Bold'>i2cdetect</font>, os "
              "contadores de calibração e o ecrã do "
              "<font face='Courier-Bold'>gps_bench</font> no primeiro fix. Anotar tudo "
              "o que tenha sido diferente do esperado, mesmo que tenha acabado por "
              "funcionar."),
    ], campos=["Algum critério de aborto atingido? (S/N)",
               "Divisor verificado ao multímetro? (S/N)"]))

    s.append(Spacer(1, 5))
    s.append(Paragraph("<b>Notas e desvios</b>", BODY))
    notas = Table([[""]] * 18, colWidths=[180 * mm], rowHeights=[8.5 * mm] * 18)
    notas.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, LINHA)]))
    s.append(notas)
    s.append(Spacer(1, 4))
    s.append(Paragraph(
        "Um ensaio que corre bem e não é registado é "
        "indistinguível de um ensaio que não se fez.", SMALL))

    doc.build(s)
    print(f"OK  {SAIDA}")


if __name__ == "__main__":
    construir()
