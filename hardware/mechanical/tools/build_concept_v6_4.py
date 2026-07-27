#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAILSAFE - gerador do modelo de conceito v6_3.

Parte do v6_2 (STEP AP214, exportado por Open CASCADE) e ACRESCENTA os
componentes internos: eletronica na caixa IP66, ESCs e motores nos cascos.

Metodo: nao ha kernel CAD disponivel (CadQuery/OpenCASCADE nao instala de
forma fiavel na sandbox). Em vez de gerar B-rep de raiz, o script CLONA a
topologia de dois solidos ja validados do proprio ficheiro
  - 'calco_IP66_1'  -> molde de caixa (6 faces planas, 8 vertices)
  - 'waterjet_dir'  -> molde de cilindro (2 tampas + lateral cilindrica)
e aplica-lhes uma transformacao afim por eixo (translacao + escala).
Como toda a geometria dos moldes e' alinhada aos eixos, a transformacao
preserva a validade do B-rep, incluindo as curvas parametricas (pcurves).

Sistema de coordenadas (mm): X = proa->popa, Y = bombordo(-)/estibordo(+),
Z = quilha->cima. Casco 800 x 350, conves a z=146.

Autor: Gonçalo Silva
"""
import re
import sys
import os

SRC = sys.argv[1] if len(sys.argv) > 1 else 'SAILSAFE_concept_v6_2.step'
DST = sys.argv[2] if len(sys.argv) > 2 else 'SAILSAFE_concept_v6_4.step'

# ---------------------------------------------------------------- parsing ---
raw = open(SRC, encoding='utf-8').read()
head, rest = raw.split('DATA;', 1)
body, tail = rest.rsplit('ENDSEC;', 1)

ents = {}
order = []
for m in re.finditer(r'#(\d+)\s*=\s*(.*?);\s*(?=#\d+\s*=|$)', body, re.S):
    i = int(m.group(1))
    ents[i] = ' '.join(m.group(2).split())
    order.append(i)
next_id = max(ents) + 1


def refs(txt):
    return [int(x) for x in re.findall(r'#(\d+)', txt)]


def etype(txt):
    m = re.match(r'\(?\s*([A-Z_0-9]+)\s*\(', txt)
    return m.group(1) if m else ''


def nums(txt):
    return [float(x) for x in re.findall(r'-?\d+\.?\d*(?:[eE][+-]?\d+)?', txt)]


def tuple_of(txt):
    """valores dentro do ultimo par de parenteses de um CARTESIAN_POINT/DIRECTION"""
    a = txt.rindex('(')
    inner = txt[a + 1: txt.index(')', a)]
    return [float(x) for x in inner.split(',')]


def reach(root, stop=()):
    seen, stack = set(), [root]
    while stack:
        n = stack.pop()
        if n in seen or n in stop or n not in ents:
            continue
        seen.add(n)
        stack += refs(ents[n])
    return seen


# produto -> (product_definition, brep, absr, product_id)
parts = {}
for i, s in ents.items():
    if not s.startswith('SHAPE_DEFINITION_REPRESENTATION'):
        continue
    pds, rep = refs(s)[:2]
    pd = refs(ents[pds])[0]
    pdf = refs(ents[pd])[0]
    pid = refs(ents[pdf])[0]
    name = re.match(r"PRODUCT\('([^']*)'", ents[pid]).group(1)
    breps = [n for n in refs(ents[rep]) if ents.get(n, '').startswith('MANIFOLD_SOLID_BREP')]
    if breps:
        parts[name] = dict(pd=pd, brep=breps[0], absr=rep, prod=pid, sdr=i)


def bbox(name):
    pts = []
    for n in reach(parts[name]['brep']):
        if ents[n].startswith('VERTEX_POINT'):
            pts.append(tuple_of(ents[refs(ents[n])[0]]))
    xs, ys, zs = zip(*pts)
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


# --------------------------------------------------- transformacao afim -----
AX = {(1., 0., 0.): 0, (-1., 0., 0.): 0,
      (0., 1., 0.): 1, (0., -1., 0.): 1,
      (0., 0., 1.): 2, (0., 0., -1.): 2}


def axis_of(d):
    key = tuple(round(v, 9) + 0.0 for v in d)
    if key not in AX:
        raise ValueError('direccao nao alinhada aos eixos: %s' % (d,))
    return AX[key]


def param_scales(subgraph, scale):
    """(su, sv) para cada DEFINITIONAL_REPRESENTATION, via a superficie do PCURVE."""
    out = {}
    for n in subgraph:
        if not ents[n].startswith('PCURVE'):
            continue
        surf, defrep = refs(ents[n])[:2]
        st = etype(ents[surf])
        a2p = refs(ents[surf])[0]
        _, axis, refdir = refs(ents[a2p])[:3]
        ia = axis_of(tuple_of(ents[axis]))
        iu = axis_of(tuple_of(ents[refdir]))
        if st == 'PLANE':
            iv = ({0, 1, 2} - {ia, iu}).pop()
            su, sv = scale[iu], scale[iv]
        elif st == 'CYLINDRICAL_SURFACE':
            su, sv = 1.0, scale[ia]          # u = angulo, v = distancia axial
        else:
            raise ValueError('superficie nao suportada: ' + st)
        out.setdefault(defrep, (su, sv))
    return out


def fmt(v):
    if v == int(v):
        return '%d.' % int(v)
    return repr(round(v, 9))


def transform(subgraph, scale, offset, origin):
    """Devolve {id: texto_transformado} para o subgrafo dado.
    ponto3d -> offset + (p - origin) * scale ; radios e pcurves escalados."""
    pscale = param_scales(subgraph, scale)
    owner = {}
    for defrep, sv in pscale.items():
        for n in reach(defrep):
            owner[n] = sv
    new = {}
    for n in subgraph:
        t = ents[n]
        k = etype(t)
        if k == 'CARTESIAN_POINT':
            v = tuple_of(t)
            if len(v) == 3:
                v = [offset[a] + (v[a] - origin[a]) * scale[a] for a in range(3)]
            else:
                su, sv = owner.get(n, (1.0, 1.0))
                v = [v[0] * su, v[1] * sv]
            t = "CARTESIAN_POINT('',(%s))" % ','.join(fmt(x) for x in v)
        elif k == 'CIRCLE':
            a2p = refs(t)[0]
            r = nums(t.rsplit(',', 1)[1])[0]
            if len(tuple_of(ents[refs(ents[a2p])[0]])) == 3:
                s = scale[({0, 1, 2} - {axis_of(tuple_of(ents[refs(ents[a2p])[1]]))}).pop()]
            else:
                s = owner.get(n, (1.0, 1.0))[0]
            t = "CIRCLE('',#%d,%s)" % (a2p, fmt(r * s))
        elif k == 'CYLINDRICAL_SURFACE':
            a2p = refs(t)[0]
            r = nums(t.rsplit(',', 1)[1])[0]
            ia = axis_of(tuple_of(ents[refs(ents[a2p])[1]]))
            s = scale[({0, 1, 2} - {ia}).pop()]
            t = "CYLINDRICAL_SURFACE('',#%d,%s)" % (a2p, fmt(r * s))
        new[n] = t
    return new


# --------------------------------------------------------------- clonagem ---
added = []          # textos "#id = ...;" a acrescentar
placements = []     # AXIS2_PLACEMENT_3D a juntar ao SHAPE_REPRESENTATION #10
occurrences = 26    # ja existem 26 NEXT_ASSEMBLY_USAGE_OCCURRENCE


def new_ent(txt):
    global next_id
    i = next_id
    next_id += 1
    added.append((i, txt))
    return i


def clone_solid(src_part, name, scale, offset, origin, colour):
    """Clona o solido de src_part com transformacao afim e regista-o na montagem."""
    global occurrences
    sub = reach(parts[src_part]['brep'])
    txt = transform(sub, scale, offset, origin)
    remap = {}
    for n in sorted(sub):
        remap[n] = next_id + len(remap)
    for n in sorted(sub):
        s = re.sub(r'#(\d+)', lambda m: '#%d' % remap.get(int(m.group(1)), int(m.group(1))), txt[n])
        added.append((remap[n], s))
    globals()['next_id'] = next_id + len(sub)

    brep = remap[parts[src_part]['brep']]
    # cabecalho do produto
    pctx = new_ent("PRODUCT_CONTEXT('',#2,'mechanical')")
    prod = new_ent("PRODUCT('%s','%s','',(#%d))" % (name, name, pctx))
    pdf = new_ent("PRODUCT_DEFINITION_FORMATION('','',#%d)" % prod)
    pdctx = new_ent("PRODUCT_DEFINITION_CONTEXT('part definition',#2,'design')")
    pd = new_ent("PRODUCT_DEFINITION('design','',#%d,#%d)" % (pdf, pdctx))
    pds = new_ent("PRODUCT_DEFINITION_SHAPE('','',#%d)" % pd)
    absr = new_ent("ADVANCED_BREP_SHAPE_REPRESENTATION('',(#11,#%d),#2011)" % brep)
    new_ent("SHAPE_DEFINITION_REPRESENTATION(#%d,#%d)" % (pds, absr))
    new_ent("PRODUCT_RELATED_PRODUCT_CATEGORY('part',$,(#%d))" % prod)
    # montagem (transformacao identidade: geometria ja esta em coords absolutas)
    org = new_ent("CARTESIAN_POINT('',(0.,0.,0.))")
    dz = new_ent("DIRECTION('',(0.,0.,1.))")
    dx = new_ent("DIRECTION('',(1.,0.,0.))")
    ax = new_ent("AXIS2_PLACEMENT_3D('',#%d,#%d,#%d)" % (org, dz, dx))
    placements.append(ax)
    idt = new_ent("ITEM_DEFINED_TRANSFORMATION('','',#11,#%d)" % ax)
    rr = new_ent("( REPRESENTATION_RELATIONSHIP('','',#%d,#10) "
                 "REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION(#%d) "
                 "SHAPE_REPRESENTATION_RELATIONSHIP() )" % (absr, idt))
    occurrences += 1
    nauo = new_ent("NEXT_ASSEMBLY_USAGE_OCCURRENCE('%d','%s:1','',#5,#%d,$)"
                   % (occurrences, name, pd))
    pds2 = new_ent("PRODUCT_DEFINITION_SHAPE('Placement','Placement of an item',#%d)" % nauo)
    new_ent("CONTEXT_DEPENDENT_SHAPE_REPRESENTATION(#%d,#%d)" % (rr, pds2))
    # cor
    col = new_ent("COLOUR_RGB('',%s)" % ','.join('%.6f' % c for c in colour))
    fac = new_ent("FILL_AREA_STYLE_COLOUR('',#%d)" % col)
    fas = new_ent("FILL_AREA_STYLE('',(#%d))" % fac)
    ssf = new_ent("SURFACE_STYLE_FILL_AREA(#%d)" % fas)
    sss = new_ent("SURFACE_SIDE_STYLE('',(#%d))" % ssf)
    ssu = new_ent("SURFACE_STYLE_USAGE(.BOTH.,#%d)" % sss)
    psa = new_ent("PRESENTATION_STYLE_ASSIGNMENT((#%d))" % ssu)
    si = new_ent("STYLED_ITEM('color',(#%d),#%d)" % (psa, brep))
    new_ent("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(#%d),#2011)" % si)
    return brep


BOX_SRC = 'calco_IP66_1'
CYL_SRC = 'waterjet_dir'
box_bb = bbox(BOX_SRC)
cyl_bb = bbox(CYL_SRC)          # so' os 2 vertices do seam
CYL_X0, CYL_X1 = cyl_bb[0], cyl_bb[1]
CYL_R = 12.0
CYL_YC, CYL_ZC = 117.0, 40.0


def box(name, x0, y0, z0, dx, dy, dz, colour):
    s = ((box_bb[1] - box_bb[0]), (box_bb[3] - box_bb[2]), (box_bb[5] - box_bb[4]))
    clone_solid(BOX_SRC, name,
                scale=(dx / s[0], dy / s[1], dz / s[2]),
                offset=(x0, y0, z0),
                origin=(box_bb[0], box_bb[2], box_bb[4]),
                colour=colour)


def cyl_x(name, x0, length, yc, zc, r, colour):
    """cilindro com eixo X, de x0 a x0+length, centro (yc, zc), raio r"""
    sr = r / CYL_R
    clone_solid(CYL_SRC, name,
                scale=(length / (CYL_X1 - CYL_X0), sr, sr),
                offset=(x0, yc, zc),
                origin=(CYL_X0, CYL_YC, CYL_ZC),
                colour=colour)


# ------------------------------------------------- reposicionar a bateria ---
# 2200 mAh 3S real ~ 105 x 35 x 25; estava 120 x 60 x 30 a meio da caixa
# (colidia com o Raspberry Pi). Passa para a faixa de bombordo do fundo.
bb = bbox('bateria_pi_2200')
tgt = (257.5, -52.5, 155.0, 35.0, 105.0, 25.0)   # atravessada na antepara de vante
sub = reach(parts['bateria_pi_2200']['brep'])
newtxt = transform(sub,
                   scale=(tgt[3] / (bb[1] - bb[0]), tgt[4] / (bb[3] - bb[2]), tgt[5] / (bb[5] - bb[4])),
                   offset=(tgt[0], tgt[1], tgt[2]),
                   origin=(bb[0], bb[2], bb[4]))
ents.update(newtxt)

# ------------------------------------------------------ novos componentes ---
GREEN = (0.05, 0.45, 0.25)
BLUE = (0.12, 0.25, 0.55)
PURPLE = (0.50, 0.20, 0.60)
ORANGE = (0.90, 0.50, 0.10)
GREY = (0.60, 0.60, 0.62)
YELLOW = (0.90, 0.80, 0.20)
RED = (0.80, 0.15, 0.15)
DARKRED = (0.55, 0.10, 0.10)
CYAN = (0.10, 0.70, 0.75)
BLACK = (0.18, 0.18, 0.20)
SILVER = (0.75, 0.77, 0.80)
STEEL = (0.45, 0.47, 0.50)

# --- dentro da caixa IP66 (interior util: X 254.5..453.5, Y +-75, Z 154.5..252)
# zona digital (a re', longe do DC-DC e dos cabos de potencia)
# ---------------------------------------------------------------------------
# COMPONENTES DETALHADOS (v6.4)
# Mesmas cotas de envolvente da v6.3, mas decompostos nas pecas que os tornam
# reconhecidos a olho: conectores, blindagens, headers e antenas.
# Cotas dos desenhos mecanicos publicos de cada placa.
# ---------------------------------------------------------------------------
PCB_GREEN = (0.11, 0.42, 0.23)
PCB_BLUE  = (0.10, 0.25, 0.56)
PCB_PURP  = (0.36, 0.18, 0.56)
GOLD      = (0.85, 0.70, 0.29)
METAL     = (0.79, 0.81, 0.83)
CHIP      = (0.16, 0.18, 0.20)
WHITEC    = (0.91, 0.91, 0.90)
CERAMIC   = (0.87, 0.89, 0.90)
NYLON     = (0.15, 0.16, 0.17)

# --- Raspberry Pi 4 (envolvente 85 x 56 x 20 em 300,-72,163) ---
PX, PY, PZ = 300.0, -72.0, 163.0
box('rpi4_pcb',        PX,        PY,        PZ,        85.0, 56.0, 1.4, PCB_GREEN)
box('rpi4_gpio',       PX + 7.0,  PY + 49.5, PZ + 1.4,  51.0,  5.1, 8.5, CHIP)
box('rpi4_gpio_pinos', PX + 7.4,  PY + 49.9, PZ + 9.9,  50.2,  4.3, 2.0, GOLD)
box('rpi4_soc',        PX + 26.0, PY + 20.0, PZ + 1.4,  15.0, 15.0, 1.6, CHIP)
box('rpi4_ram',        PX + 45.0, PY + 4.0,  PZ + 1.4,  11.5, 10.0, 1.1, CHIP)
box('rpi4_usb3',       PX + 69.7, PY + 2.0,  PZ + 1.4,  17.3, 13.2, 15.6, METAL)
box('rpi4_usb2',       PX + 69.7, PY + 20.5, PZ + 1.4,  17.3, 13.2, 15.6, METAL)
box('rpi4_ethernet',   PX + 65.7, PY + 38.0, PZ + 1.4,  21.3, 16.0, 13.5, METAL)
box('rpi4_usbc',       PX + 3.5,  PY - 1.0,  PZ + 1.4,   9.0,  7.5,  3.2, METAL)
box('rpi4_hdmi0',      PX + 21.5, PY - 1.2,  PZ + 1.4,   7.5,  8.0,  3.5, METAL)
box('rpi4_hdmi1',      PX + 34.5, PY - 1.2,  PZ + 1.4,   7.5,  8.0,  3.5, METAL)
box('rpi4_csi',        PX + 45.0, PY + 17.0, PZ + 1.4,   3.0, 22.0,  5.5, WHITEC)
box('rpi4_dsi',        PX + 0.5,  PY + 17.0, PZ + 1.4,   3.0, 22.0,  5.5, WHITEC)

# --- ESP32 DevKit (55 x 28 x 13 em 300,5,163) ---
EX, EY, EZ = 300.0, 5.0, 163.0
box('esp32_pcb',       EX,        EY,        EZ,        55.0, 28.0, 1.6, PCB_BLUE)
box('esp32_wroom',     EX + 12.0, EY + 6.0,  EZ + 1.6,  18.0, 16.0, 3.1, METAL)
box('esp32_antena',    EX + 1.5,  EY + 8.0,  EZ + 1.6,   9.0, 12.0, 0.3, GOLD)
box('esp32_header_a',  EX + 3.0,  EY + 0.3,  EZ - 2.5,  48.3,  2.5, 2.5, CHIP)
box('esp32_header_b',  EX + 3.0,  EY + 25.2, EZ - 2.5,  48.3,  2.5, 2.5, CHIP)
box('esp32_usb',       EX + 47.5, EY + 11.0, EZ + 1.6,   8.0,  6.0, 2.7, METAL)
box('esp32_btn_a',     EX + 38.0, EY + 3.0,  EZ + 1.6,   6.5,  6.5, 3.5, CHIP)
box('esp32_btn_b',     EX + 38.0, EY + 18.5, EZ + 1.6,   6.5,  6.5, 3.5, CHIP)

# --- IMU BNO055 sobre coluna (20 x 27 x 5 em 400,-13.5,215) ---
box('suporte_BNO055',  403.0, -7.0,   155.0, 14.0, 14.0, 60.0, GREY)
box('bno055_pcb',      400.0, -13.5,  215.0, 20.0, 27.0,  1.6, PCB_PURP)
box('bno055_chip',     407.4, -1.5,   216.6,  5.2,  3.8,  1.1, CHIP)
box('bno055_header',   400.3, -7.5,   212.5,  2.5, 15.2,  2.5, CHIP)

# --- GPS NEO-8M no topo do mastro (25 x 25 x 8 em 260,47,240) ---
box('suporte_GPS',     262.0, 55.0,   155.0, 15.0, 14.0, 85.0, GREY)
box('gps_pcb',         260.0, 47.0,   240.0, 25.0, 25.0,  1.6, PCB_BLUE)
box('gps_antena',      263.5, 50.5,   241.6, 18.0, 18.0,  4.0, CERAMIC)
box('gps_lna',         269.0, 56.0,   245.6,  7.0,  7.0,  1.2, METAL)
box('gps_header',      267.4, 47.2,   236.5, 10.2,  2.5,  2.5, CHIP)

box('conversor_DCDC_5V',     300.0,  38.0, 155.0,  65.0, 35.0, 20.0, YELLOW)
box('distribuidor_fusiveis', 388.0,  30.0, 155.0,  60.0, 40.0, 30.0, RED)
box('sensor_corrente',       390.0,  10.0, 155.0,  31.0, 13.0, 15.0, DARKRED)
box('ads1015',               423.0,  10.0, 155.0,  25.0, 18.0,  4.0, CYAN)

# --- cascos: ESC sob a escotilha/cobertura, motor coaxial com o waterjet
for lado, sy in (('dir', 1.0), ('esq', -1.0)):
    y_esc = 97.0 if sy > 0 else -137.0
    # z 104..134: 2 mm de folga sob a longarina de re' (z 136..146)
    box('esc_%s' % lado, 695.0, y_esc, 104.0, 80.0, 40.0, 30.0, BLACK)
    cyl_x('motor_%s' % lado, 630.0, 70.0, 117.0 * sy, 40.0, 18.0, SILVER)
    cyl_x('veio_motor_%s' % lado, 700.0, 20.0, 117.0 * sy, 40.0, 2.5, STEEL)

# --- detalhe dos waterjets (a jusante do duto, sem sobreposicoes) ---
#  735..793 duto (reescalado acima) · 793..800 estator · 800..809 tubeira
#  809..815 bocal orientavel · admissao e grelha por baixo · servo no convés
ALU  = (0.72, 0.75, 0.78)
ALUD = (0.49, 0.53, 0.56)
for lado, sy in (('dir', 1.0), ('esq', -1.0)):
    yc = 117.0 * sy
    box('wj_admissao_%s' % lado,  737.0, yc - 10.3, 21.0, 28.0, 20.6, 6.8, ALU)
    for k in (-1, 0, 1):
        box('wj_grelha_%s%d' % (lado, k + 1), 739.0, yc + k * 4.5 - 0.7, 19.4, 24.0, 1.4, 1.4, ALUD)
    cyl_x('wj_estator_%s' % lado, 793.0,  7.0, yc, 40.0, 11.5, ALUD)
    cyl_x('wj_tubeira_%s' % lado, 800.2,  8.6, yc, 40.0, 10.5, ALU)
    cyl_x('wj_bocal_%s'   % lado, 809.0,  6.0, yc, 40.0,  6.7, ALUD)
    # servo do bocal: no convés, à ré da cobertura do ESC, com o braço a descer
    box('servo_corpo_%s' % lado,  700.0, yc - 6.0, 56.0, 23.0, 12.0, 18.0, NYLON)
    box('servo_abas_%s'  % lado,  695.5, yc - 6.0, 74.0, 32.0, 12.0,  2.5, NYLON)
    box('servo_veio_%s'  % lado,  706.0, yc - 3.0, 76.5,  6.0,  6.0,  4.0, WHITEC)
    box('wj_braco_servo_%s' % lado, 796.0, yc + 13.0, 54.0, 15.2, 2.5, 12.0, NYLON)

# --- encolher os dutos que vem da v6.2 para dar lugar ao detalhe da v6.4 ---
# original: X 720..815 cheio. Agora e' so' o corpo do duto: X 735..793.
for _l, _sy in (('dir', 1.0), ('esq', -1.0)):
    _n = 'waterjet_%s' % _l
    _bb = bbox(_n)
    _sub = reach(parts[_n]['brep'])
    ents.update(transform(_sub,
        scale=(58.0 / (_bb[1] - _bb[0]), 1.0, 1.0),
        offset=(735.0, _bb[2], _bb[4]),
        origin=(_bb[0], _bb[2], _bb[4])))

# ------------------------------------------------------------- escrita -----
ents[10] = re.sub(r'\)\s*,\s*#115\s*\)$',
                  ',' + ','.join('#%d' % p for p in placements) + '),#115)',
                  ents[10])
assert all(('#%d' % p) in ents[10] for p in placements), 'falhou juntar placements a #10'

out = [head, 'DATA;\n']
for i in order:
    out.append('#%d = %s;\n' % (i, ents[i]))
for i, t in added:
    out.append('#%d = %s;\n' % (i, t))
out.append('ENDSEC;')
out.append(tail)
res = ''.join(out)
res = res.replace("FILE_NAME('Open CASCADE Shape Model'",
                  "FILE_NAME('SAILSAFE_concept_v6_4'", 1)
open(DST, 'w', encoding='utf-8').write(res)
print('escrito %s  (%d entidades, %d novas)' % (DST, len(order) + len(added), len(added)))
