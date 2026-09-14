#!/usr/bin/env python3
"""Gera o procedimento de ensaio de bancada do SAILSAFE em PDF A4."""

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
                     "SAILSAFE_procedimento_bancada_v1.pdf")

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


def tabela_pwm():
    linhas = [["Comando", "PWM esperado", "Resposta do ESP32"],
              ["L: 0 R: 0", "1000 us", "Parado. Propulsao DESTRAVADA"],
              ["L: 10 R: 10", "1100 us", "Left: 1100 us | Right: 1100 us"],
              ["L: 20 R: 20", "1200 us", "Left: 1200 us | Right: 1200 us"],
              ["L: 30 R: 30", "1300 us", "Left: 1300 us | Right: 1300 us"],
              ["L: 31 R: 0", "-- recusado --", "VALOR FORA DO LIMITE SEGURO"]]
    dados = [[Paragraph(f"<font size=7.6>{c}</font>",
                        MONO if i and j != 1 else BODY) for j, c in enumerate(r)]
             for i, r in enumerate(linhas)]
    t = Table(dados, colWidths=[32 * mm, 32 * mm, 116 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINHA),
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#FBEAEA")),
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
                      "SAILSAFE \u2014 procedimento de ensaio de bancada v1 \u2014 "
                      "sess\u00e3o SEM propuls\u00e3o")
    canvas.drawRightString(195 * mm, 10 * mm, f"pagina {doc.page}")
    canvas.setStrokeColor(LINHA)
    canvas.setLineWidth(0.4)
    canvas.line(15 * mm, 13 * mm, 195 * mm, 13 * mm)
    canvas.restoreState()


def construir():
    doc = BaseDocTemplate(SAIDA, pagesize=A4,
                          leftMargin=15 * mm, rightMargin=15 * mm,
                          topMargin=14 * mm, bottomMargin=17 * mm,
                          title="SAILSAFE - Procedimento de ensaio de bancada",
                          author="Goncalo Martins da Silva")
    frame = Frame(15 * mm, 17 * mm, 180 * mm, A4[1] - 31 * mm, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=rodape)])

    s = []
    s.append(Paragraph("SAILSAFE &mdash; Procedimento de ensaio de bancada", H1))
    s.append(Paragraph(
        "Sess&atilde;o <b>sem propuls&atilde;o</b>: grava&ccedil;&atilde;o do firmware e "
        "verifica&ccedil;&atilde;o da cadeia de seguran&ccedil;a. Nenhum motor &eacute; "
        "energizado. Preencher &agrave; medida que se avan&ccedil;a &mdash; o valor "
        "escrito na altura vale mais do que a mem&oacute;ria no fim.", SUB))
    s.append(cabecalho_campos())
    s.append(Spacer(1, 7))

    s.append(caixa_aviso(
        "N&Atilde;O FAZER NESTA SESS&Atilde;O",
        ["&bull; N&atilde;o ligar bateria ao ESC. N&atilde;o ligar motor ao ESC. "
         "N&atilde;o montar h&eacute;lice nem jato.",
         "&bull; Motivo: sem <b>loop key XT90</b> n&atilde;o existe corte manual de "
         "pot&ecirc;ncia, e a regra do projeto &eacute; que nenhuma energiza&ccedil;&atilde;o "
         "de ESC acontece sem ele.",
         "&bull; O ESP32 &eacute; alimentado <b>s&oacute; por USB</b>. O circuito de "
         "propuls&atilde;o fica fisicamente aberto durante toda a sess&atilde;o."]))
    s.append(Spacer(1, 6))

    s.append(caixa_aviso(
        "CRIT&Eacute;RIOS DE ABORTO &mdash; parar e n&atilde;o continuar",
        ["&bull; O ESP32 imprime um <b>Left:</b> ou <b>Right:</b> acima de "
         "<b>1300 us</b> &rarr; o tecto de 30% foi furado.",
         "&bull; O failsafe <b>n&atilde;o</b> dispara at&eacute; 2 s depois de a "
         "comunica&ccedil;&atilde;o parar.",
         "&bull; O sistema <b>n&atilde;o</b> arranca travado (aceita propuls&atilde;o "
         "sem ter recebido <font face='Courier-Bold'>L: 0 R: 0</font>).",
         "&bull; Depois do failsafe, um comando de propuls&atilde;o volta a ser "
         "obedecido sem passar por zero.",
         "&bull; Cheiro, calor an&oacute;malo ou fumo &rarr; desligar o USB "
         "imediatamente.",
         "&bull; Qualquer um destes bloqueia ensaios com motor at&eacute; ser "
         "corrigido e re-verificado."]))
    s.append(Spacer(1, 7))

    s.append(Paragraph("<b>Refer&ecirc;ncia r&aacute;pida &mdash; o que o firmware deve "
                       "responder</b>", BODY))
    s.append(Spacer(1, 3))
    s.append(tabela_pwm())
    s.append(Paragraph(
        "PWM = 1000 + 10 &times; percentagem. Qualquer valor fora de [0, 30] &eacute; "
        "recusado pelo firmware, n&atilde;o limitado.", SMALL))

    # ---------------------------------------------------------------- A
    s += seccao("A &mdash; Prepara&ccedil;&atilde;o")
    s.append(passo(1, "Circuito de propuls&atilde;o aberto e confirmado &agrave; vista", [
        ("t", "Verificar fisicamente que n&atilde;o h&aacute; bateria ligada ao ESC e que "
              "o motor n&atilde;o est&aacute; ligado ao ESC. Confirmar antes de ligar "
              "o USB, n&atilde;o depois."),
    ]))
    s.append(passo(2, "Terminal s&eacute;rie a enviar mudan&ccedil;a de linha", [
        ("t", "O firmware s&oacute; processa um comando quando recebe "
              "<font face='Courier-Bold'>\\n</font>. Um terminal sem "
              "termina&ccedil;&atilde;o de linha faz o sistema parecer morto."),
        ("t", "No Serial Monitor do Arduino IDE: p&ocirc;r <b>115200 baud</b> e "
              "termina&ccedil;&atilde;o <b>New Line (NL)</b>."),
    ], nota="Se nenhum comando obtiver resposta, esta &eacute; a primeira causa a "
            "eliminar &mdash; antes de suspeitar do firmware."))

    # ---------------------------------------------------------------- B
    s += seccao("B &mdash; Firmware no ESP32")
    s.append(passo(3, "Identificar a porta e gravar o firmware", [
        ("c", "arduino-cli board list"),
        ("c", "arduino-cli upload -p COM? --fqbn esp32:esp32:esp32 software/esp32"),
        ("t", "Substituir <b>COM?</b> pela porta listada no comando anterior."),
    ], campos=["Porta usada", "Grava&ccedil;&atilde;o concluiu sem erro? (S/N)"],
       nota="Primeira vez que este firmware vai para uma placa. At&eacute; aqui "
            "existia apenas compilado."))
    s.append(passo(4, "Mensagens de arranque", [
        ("t", "Abrir o monitor s&eacute;rie e carregar no bot&atilde;o <b>EN/RESET</b> "
              "da placa."),
        ("e", "quatro linhas, a &uacute;ltima das quais<br/>"
              "<font face='Courier-Bold'>PROPULSAO TRAVADA no arranque - enviar "
              "'L: 0 R: 0' para destravar</font>"),
    ], campos=["As quatro linhas apareceram? (S/N)"],
       nota="Se a &uacute;ltima linha n&atilde;o aparecer, a placa tem firmware antigo: "
            "repetir o passo 3."))

    # ---------------------------------------------------------------- C
    s += seccao("C &mdash; Protocolo, ack e limites")
    s.append(passo(5, "O ack do STOP &mdash; passo cr&iacute;tico", [
        ("c", "L: 0 R: 0"),
        ("e", "<font face='Courier-Bold'>Parado. Propulsao DESTRAVADA</font>"),
        ("t", "<b>Copiar a resposta exatamente como aparece</b>, incluindo "
              "mai&uacute;sculas e acentos (ou aus&ecirc;ncia deles)."),
    ], campos=["String exata observada", "Cont&eacute;m 'DESTRAVADA'? (S/N)"],
       nota="Toda a confirma&ccedil;&atilde;o de STOP do Raspberry Pi assenta nesta "
            "string. Se for diferente, o Pi recusa ARM sempre &mdash; falha "
            "segura, mas inutilizante. Neste caso corrigir STOP_ACK em "
            "communication/serial_link.py antes dos passos da sec&ccedil;&atilde;o E."))
    s.append(passo(6, "Arranque travado", [
        ("t", "Carregar em <b>RESET</b> e, sem enviar nada antes, mandar:"),
        ("c", "L: 20 R: 20"),
        ("e", "<font face='Courier-Bold'>PROPULSAO TRAVADA - ignorado. Enviar "
              "'L: 0 R: 0' para destravar</font>"),
    ], campos=["Recusou a propuls&atilde;o? (S/N)"],
       nota="Se obedecer, ABORTAR: o sistema n&atilde;o est&aacute; a arrancar "
            "travado."))
    s.append(passo(7, "Obedi&ecirc;ncia depois de destravar", [
        ("c", "L: 0 R: 0"),
        ("c", "L: 20 R: 20"),
        ("e", "<font face='Courier-Bold'>Left: 1200 us | Right: 1200 us</font>"),
    ], campos=["Valor observado (us)"]))
    s.append(passo(8, "Tecto de 30% e comandos malformados", [
        ("c", "L: 30 R: 30"),
        ("e", "1300 us &mdash; aceite, &eacute; o m&aacute;ximo"),
        ("c", "L: 31 R: 0"),
        ("e", "<font face='Courier-Bold'>VALOR FORA DO LIMITE SEGURO - motores "
              "parados</font>"),
        ("c", "L: abc R: 0"),
        ("e", "<font face='Courier-Bold'>COMANDO INVALIDO - motores parados</font>"),
    ], campos=["Os tr&ecirc;s comportamentos confirmados? (S/N)"],
       nota="Um valor fora de limites n&atilde;o &eacute; cortado para 30: &eacute; "
            "recusado por inteiro e os motores param."))

    # ---------------------------------------------------------------- D
    s += seccao("D &mdash; Failsafe e trava de re-arme")
    s.append(passo(9, "O failsafe dispara com o sil&ecirc;ncio", [
        ("t", "Destravar e p&ocirc;r propuls&atilde;o:"),
        ("c", "L: 0 R: 0"),
        ("c", "L: 20 R: 20"),
        ("t", "<b>Parar de escrever</b> e contar at&eacute; tr&ecirc;s."),
        ("e", "<font face='Courier-Bold'>FAILSAFE ATIVO - motores parados e "
              "propulsao TRAVADA</font>"),
    ], campos=["Disparou em menos de 2 s? (S/N)"],
       nota="O timeout do firmware &eacute; 1 s. N&atilde;o &eacute; preciso "
            "cronometrar; o que interessa &eacute; que dispare e que seja "
            "manifestamente r&aacute;pido."))
    s.append(passo(10, "O regresso da liga&ccedil;&atilde;o n&atilde;o rearma", [
        ("t", "Logo a seguir ao failsafe, sem enviar zero, mandar:"),
        ("c", "L: 20 R: 20"),
        ("e", "<font face='Courier-Bold'>PROPULSAO TRAVADA - ignorado</font>"),
        ("t", "Repetir o mesmo comando mais 4 ou 5 vezes seguidas."),
        ("e", "continua travado, e o aviso <b>s&oacute; aparece uma vez</b>"),
    ], campos=["Manteve-se travado? (S/N)"],
       nota="Esta &eacute; a propriedade que impede o barco de voltar a andar "
            "sozinho depois de um Pi reiniciar. Se falhar, ABORTAR."))
    s.append(passo(11, "S&oacute; o zero abre a trava", [
        ("c", "L: 0 R: 0"),
        ("e", "<font face='Courier-Bold'>Parado. Propulsao DESTRAVADA</font>"),
        ("c", "L: 20 R: 20"),
        ("e", "1200 us &mdash; volta a obedecer"),
    ], campos=["Confirmado? (S/N)"]))

    # ---------------------------------------------------------------- E
    s += seccao("E &mdash; Raspberry Pi ligado ao ESP32")
    s.append(passo(12, "ARM exige confirma&ccedil;&atilde;o da trava", [
        ("t", "Ligar o ESP32 ao Pi por USB e correr no Pi:"),
        ("c", "python3 software/raspberry_pi/main.py"),
        ("t", "Carregar em <b>a</b> (ARM)."),
        ("e", "<font face='Courier-Bold'>[STATE] ARMED</font> e, no CSV da "
              "sess&atilde;o, uma linha <font face='Courier-Bold'>STOP ... arm: "
              "confirmado</font>"),
    ], campos=["Armou? (S/N)", "Ficheiro CSV da sess&atilde;o"],
       nota="Se aparecer 'ARM recusado: a trava do ESP32 nao confirmou abertura', "
            "o ack difere do esperado &mdash; voltar ao passo 5."))
    s.append(passo(13, "Perda de s&eacute;rie desarma dos dois lados", [
        ("t", "Com o sistema em <b>ARMED</b>, desligar o cabo USB do ESP32."),
        ("e", "no Pi: <font face='Courier-Bold'>[WARN] Ligacao serie perdida -> "
              "DISARMED</font>"),
        ("t", "Voltar a ligar o cabo e observar o Pi."),
        ("e", "reconecta e <b>continua DISARMED</b> &mdash; nunca arma sozinho"),
    ], campos=["Desarmou na perda? (S/N)", "Continuou DISARMED ao voltar? (S/N)"],
       nota="&Eacute; a primeira observa&ccedil;&atilde;o em hardware das duas "
            "camadas a funcionar em cadeia: o Pi desarma por perda de s&eacute;rie "
            "e o ESP32 trava por timeout."))
    s.append(passo(14, "Controlo sem terminal", [
        ("t", "No Pi, correr sem terminal interativo e anotar o PID impresso:"),
        ("c", "python3 software/raspberry_pi/main.py &lt; /dev/null &amp;"),
        ("t", "Comandar pelo FIFO e depois parar por sinal:"),
        ("c", "echo a &gt; /tmp/sailsafe.ctl"),
        ("c", "kill -USR1 &lt;PID&gt;"),
        ("e", "o FIFO arma; o sinal p&otilde;e <font face='Courier-Bold'>[STOP] STOP "
              "-&gt; DISARMED</font>"),
    ], campos=["PID observado", "FIFO armou? (S/N)", "Sinal parou? (S/N)"],
       nota="&Eacute; assim que o processo vai correr no barco: arrancado por um "
            "servi&ccedil;o, sem teclado ligado."))

    # ---------------------------------------------------------------- F
    s += seccao("F &mdash; Encerramento")
    s.append(passo(15, "Registo final", [
        ("t", "Guardar o CSV da sess&atilde;o e anotar tudo o que tenha sido "
              "diferente do esperado, mesmo que tenha acabado por funcionar."),
    ], campos=["Algum crit&eacute;rio de aborto atingido? (S/N)",
               "Pronto para ensaio com motor? (S/N)"]))

    s.append(Spacer(1, 5))
    s.append(Paragraph("<b>Notas e desvios</b>", BODY))
    notas = Table([[""]] * 20, colWidths=[180 * mm], rowHeights=[8.5 * mm] * 20)
    notas.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINHA),
    ]))
    s.append(notas)
    s.append(Spacer(1, 4))
    s.append(Paragraph(
        "Um ensaio que corre bem e n&atilde;o &eacute; registado &eacute; "
        "indistingu&iacute;vel de um ensaio que n&atilde;o se fez.", SMALL))

    doc.build(s)
    print(f"OK  {SAIDA}")


if __name__ == "__main__":
    construir()
