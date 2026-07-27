#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAILSAFE — componentes detalhados.

Substitui os paralelepipedos de referencia por geometria reconhecivel,
modelada a partir das cotas publicas de cada placa. Nao usa CAD de
terceiros: e' tudo gerado aqui, com as dimensoes do datasheet mecanico.

Cada funcao devolve uma lista de (nome_material, mesh) em milimetros, com
origem no canto minimo da envolvente da peca. O build principal trata de
posicionar e orientar.
"""
import numpy as np, trimesh
from trimesh.creation import box, cylinder, icosphere

def _b(sx, sy, sz, x=0, y=0, z=0):
    m = box(extents=(sx, sy, sz))
    m.apply_translation((x + sx/2, y + sy/2, z + sz/2))
    return m

def _cyl(r, h, axis='z', x=0, y=0, z=0, sec=20):
    m = cylinder(radius=r, height=h, sections=sec)
    if axis == 'x': m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0,1,0]))
    if axis == 'y': m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0]))
    m.apply_translation((x, y, z))
    return m

def _pins(nx, ny, pitch, x, y, z, h=3.0, w=0.64):
    """cabecalho de pinos: um bloco de plastico + os pinos dourados"""
    out = []
    for i in range(nx):
        for j in range(ny):
            out.append(_b(w, w, h, x + i*pitch + (pitch-w)/2, y + j*pitch + (pitch-w)/2, z))
    return trimesh.util.concatenate(out) if out else None


# --------------------------------------------------------------- Raspberry Pi
def raspberry_pi_4():
    """85 x 56 x 1.4 mm de PCB. Cotas do desenho mecanico da Raspberry Pi Foundation."""
    P = []
    P.append(('pcb',    _b(85, 56, 1.4, 0, 0, 0)))
    # header GPIO 2x20, passo 2.54, centro a 3.5 mm da borda longa
    P.append(('header', _b(51.0, 5.1, 8.5, 7.0, 49.5, 1.4)))
    pins = _pins(20, 2, 2.54, 7.4, 49.9, 9.4, h=2.2)
    if pins is not None: P.append(('gold', pins))
    # SoC, RAM e PMIC
    P.append(('chip',   _b(15, 15, 1.6, 26, 20, 1.4)))
    P.append(('chip',   _b(11.5, 10, 1.1, 45, 4, 1.4)))
    P.append(('chip',   _b(7, 7, 1.0, 26, 6, 1.4)))
    # USB: 2 x 3.0 e 2 x 2.0, saem 2 mm fora da placa
    for yy in (2.0, 20.5):
        P.append(('metal', _b(17.3, 13.2, 15.6, 69.7, yy, 1.4)))
    # Ethernet RJ45
    P.append(('metal', _b(21.3, 16.0, 13.5, 65.7, 38.0, 1.4)))
    # USB-C, 2 x micro-HDMI, jack de audio na borda inferior
    P.append(('metal', _b(9.0, 7.5, 3.2, 3.5, -1.0, 1.4)))
    P.append(('metal', _b(7.5, 8.0, 3.5, 21.5, -1.2, 1.4)))
    P.append(('metal', _b(7.5, 8.0, 3.5, 34.5, -1.2, 1.4)))
    P.append(('black', _cyl(3.0, 6.0, 'y', 52.0, 1.0, 4.4, 14)))
    # conectores CSI / DSI (brancos)
    P.append(('white', _b(3.0, 22.0, 5.5, 45.0, 17.0, 1.4)))
    P.append(('white', _b(3.0, 22.0, 5.5, 0.5, 17.0, 1.4)))
    # 4 furos de fixacao M2.5
    return P

# ------------------------------------------------------------------- ESP32
def esp32_devkit():
    """55 x 28 x 1.6 de PCB, com o modulo WROOM blindado e a antena impressa."""
    P = []
    P.append(('pcb_blue', _b(55, 28, 1.6, 0, 0, 0)))
    # modulo ESP32-WROOM: blindagem de aco 18 x 16 x 3.1
    P.append(('metal', _b(18.0, 16.0, 3.1, 12.0, 6.0, 1.6)))
    # antena impressa (zona dourada na ponta da placa)
    P.append(('gold',  _b(9.0, 12.0, 0.2, 1.5, 8.0, 1.6)))
    # dois headers de 19 pinos
    for yy in (0.3, 25.16):
        P.append(('header', _b(48.3, 2.54, 2.5, 3.0, yy, -2.5)))
        pins = _pins(19, 1, 2.54, 3.2, yy + 0.95, -5.0, h=5.0)
        if pins is not None: P.append(('gold', pins))
    # micro-USB, regulador e dois botoes
    P.append(('metal', _b(8.0, 6.0, 2.7, 47.5, 11.0, 1.6)))
    P.append(('black', _b(6.5, 6.5, 3.5, 38.0, 3.0, 1.6)))
    P.append(('black', _b(6.5, 6.5, 3.5, 38.0, 18.5, 1.6)))
    P.append(('chip',  _b(4.0, 3.0, 1.0, 33.0, 12.0, 1.6)))
    return P

# -------------------------------------------------------------------- GPS
def gps_neo8m():
    """25 x 25 x 8: PCB com antena ceramica quadrada por cima."""
    P = []
    P.append(('pcb_blue', _b(25, 25, 1.6, 0, 0, 0)))
    P.append(('ceramic',  _b(18, 18, 4.0, 3.5, 3.5, 1.6)))   # antena ceramica
    P.append(('metal',    _b(7.0, 7.0, 1.2, 9.0, 9.0, 5.6))) # placa de alimentacao
    P.append(('chip',     _b(4.5, 4.5, 0.9, 1.0, 19.0, 1.6)))
    P.append(('header',   _b(10.2, 2.54, 2.5, 7.4, 0.2, -2.5)))
    pins = _pins(4, 1, 2.54, 7.6, 1.15, -5.0, h=5.0)
    if pins is not None: P.append(('gold', pins))
    return P

# -------------------------------------------------------------------- IMU
def bno055():
    """20 x 27 x 5: placa de desenvolvimento roxa com o chip da Bosch."""
    P = []
    P.append(('pcb_purple', _b(20, 27, 1.6, 0, 0, 0)))
    P.append(('black',      _b(5.2, 3.8, 1.1, 7.4, 12.0, 1.6)))   # BNO055
    P.append(('chip',       _b(3.0, 3.0, 0.8, 3.0, 20.0, 1.6)))
    P.append(('header',     _b(2.54, 15.2, 2.5, 0.3, 6.0, -2.5)))
    pins = _pins(1, 6, 2.54, 1.25, 6.2, -5.0, h=5.0)
    if pins is not None: P.append(('gold', pins))
    return P

# ---------------------------------------------------------------- waterjet
def waterjet(length=95.0, dia=24.0, sec=30):
    """Unidade de jato de kit: corpo conico em plastico preto, flange de
       fixacao ao espelho com parafusos, tubeira e bocal orientavel.
       Eixo em X, origem na entrada. Modelado a partir da foto do conjunto."""
    P = []
    def cone(r0, r1, x0, x1, mat):
        m = trimesh.creation.cone(radius=max(r0, r1), height=abs(x1 - x0), sections=sec)
        # tronco de cone: escala a ponta em vez de a deixar em bico
        v = m.vertices.copy()
        h = abs(x1 - x0)
        t = np.clip(v[:, 2] / h, 0, 1)
        k = (r0 + (r1 - r0) * t) / max(r0, r1)
        v[:, 0] *= k; v[:, 1] *= k
        m = trimesh.Trimesh(vertices=v, faces=m.faces, process=False)
        m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2, [0, 1, 0]))
        m.apply_translation((x0, 0, 0))
        P.append((mat, m))
    # corpo conico: entrada larga junto a admissao, afunila para a tubeira
    cone(13.0, 9.2, 0.0, length * 0.72, 'jetblack')
    # admissao por baixo, com grelha
    intake = box(extents=(length * 0.30, dia * 0.92, 7.0))
    intake.apply_translation((length * 0.17, 0, -10.5))
    P.append(('jetblack', intake))
    for k in (-1, 0, 1):
        P.append(('jetgrey', _b(length * 0.24, 1.5, 1.5, length * 0.05, k * 5.0 - 0.75, -14.6)))
    # flange redonda de fixacao ao espelho, com 4 parafusos
    P.append(('jetblack', _cyl(15.0, 4.0, 'x', length * 0.74, 0, 0, sec)))
    for a in range(4):
        ang = np.pi / 4 + a * np.pi / 2
        P.append(('steel', _cyl(1.5, 5.0, 'x', length * 0.74,
                                12.0 * np.cos(ang), 12.0 * np.sin(ang), 10)))
    # tubeira e bocal orientavel
    P.append(('jetblack', _cyl(9.2, length * 0.16, 'x', length * 0.77, 0, 0, sec)))
    P.append(('jetgrey',  _cyl(7.4, length * 0.10, 'x', length * 0.92, 0, 0, sec)))
    # haste de comando do bocal, ao longo do topo
    P.append(('steel', _cyl(0.9, length * 0.55, 'x', length * 0.30, 0, 12.5, 10)))
    P.append(('brass', _b(6.0, 3.0, 7.0, length * 0.86, -1.5, 9.0)))
    return P

# ------------------------------------------------------- motor brushless
def motor_bl(length=70.0, dia=36.0, sec=28):
    """2440 KV4500: carcaca preta com aletas de refrigeracao na traseira."""
    r = dia / 2
    P = [('motorblack', _cyl(r, length * 0.80, 'x', length * 0.10, 0, 0, sec))]
    # aletas de refrigeracao
    for k in range(9):
        a = k * 2 * np.pi / 9
        f = box(extents=(length * 0.16, 2.0, dia * 0.9))
        f.apply_transform(trimesh.transformations.rotation_matrix(a, [1, 0, 0]))
        f.apply_translation((length * 0.06, 0, 0))
        P.append(('motorblack', f))
    # tampa dianteira e veio
    P.append(('steel', _cyl(r * 0.62, 4.0, 'x', length * 0.90, 0, 0, sec)))
    P.append(('steel', _cyl(2.5, 8.0, 'x', length * 0.96, 0, 0, 12)))
    # cabos de fase
    for k, dy in enumerate((-6.5, 0, 6.5)):
        P.append(('wire%d' % (k % 3), _cyl(1.6, 16.0, 'x', -14.0, dy, 4.0, 8)))
    return P

# ------------------------------------------------------------ servo do bocal
def servo():
    """Micro servo 23 x 12 x 22 com a patilha de fixacao."""
    P = []
    P.append(('nylon_dark', _b(23, 12, 18, 0, 0, 0)))
    P.append(('nylon_dark', _b(32, 12, 2.5, -4.5, 0, 12)))     # abas
    P.append(('white',      _cyl(3.0, 4.0, 'z', 6.0, 6.0, 19.0, 16)))
    P.append(('white',      _b(16, 3.0, 1.6, 2.0, 4.5, 21.0))) # braco
    return P

MATERIALS = {
    'pcb':        ('#1c6b3a', 0.05, 0.55),
    'pcb_blue':   ('#1a3f8f', 0.05, 0.52),
    'pcb_purple': ('#5b2f8f', 0.05, 0.52),
    'header':     ('#141414', 0.00, 0.72),
    'gold':       ('#d8b34a', 0.85, 0.34),
    'metal':      ('#c9ced4', 0.92, 0.28),
    'chip':       ('#2a2d33', 0.25, 0.48),
    'black':      ('#17181b', 0.05, 0.62),
    'white':      ('#e8e8e6', 0.00, 0.55),
    'ceramic':    ('#dfe3e6', 0.05, 0.38),
    'alu':        ('#b7bfc7', 0.90, 0.30),
    'alu_dark':   ('#7d868f', 0.88, 0.36),
    'nylon':      ('#26282c', 0.00, 0.58),
    'nylon_dark': ('#1b1d20', 0.00, 0.62),
    'jetblack':   ('#191b1e', 0.05, 0.42),   # plastico do corpo do jato
    'jetgrey':    ('#2b2e32', 0.10, 0.46),
    'motorblack': ('#141517', 0.15, 0.40),
    'steel':      ('#aeb4ba', 0.90, 0.26),
    'brass':      ('#b8912f', 0.85, 0.32),
    'wire0':      ('#c9302c', 0.00, 0.55),
    'wire1':      ('#1c1c1c', 0.00, 0.55),
    'wire2':      ('#d9d9d9', 0.00, 0.55),
}
