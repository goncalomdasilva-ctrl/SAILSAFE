#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificacao do STEP: integridade referencial, bounding boxes, colisoes e CG."""
import re
import sys
import itertools

SRC = sys.argv[1]
raw = open(SRC, encoding='utf-8').read()
body = raw.split('DATA;', 1)[1].rsplit('ENDSEC;', 1)[0]
ents = {}
dups = []
for m in re.finditer(r'#(\d+)\s*=\s*(.*?);\s*(?=#\d+\s*=|$)', body, re.S):
    i = int(m.group(1))
    if i in ents:
        dups.append(i)
    ents[i] = ' '.join(m.group(2).split())


def refs(t):
    return [int(x) for x in re.findall(r'#(\d+)', t)]


def tup(t):
    a = t.rindex('(')
    return [float(x) for x in t[a + 1:t.index(')', a)].split(',')]


missing = sorted({r for t in ents.values() for r in refs(t)} - set(ents))
print('entidades: %d | ids duplicados: %s | referencias mortas: %s'
      % (len(ents), dups or 'nenhum', missing or 'nenhuma'))

parts = {}
for i, s in ents.items():
    if not s.startswith('SHAPE_DEFINITION_REPRESENTATION'):
        continue
    pds, rep = refs(s)[:2]
    pd = refs(ents[pds])[0]
    pid = refs(ents[refs(ents[pd])[0]])[0]
    name = re.match(r"PRODUCT\('([^']*)'", ents[pid]).group(1)
    br = [n for n in refs(ents[rep]) if ents.get(n, '').startswith('MANIFOLD_SOLID_BREP')]
    if br:
        parts[name] = br[0]


def reach(root):
    seen, st = set(), [root]
    while st:
        n = st.pop()
        if n in seen or n not in ents:
            continue
        seen.add(n)
        st += refs(ents[n])
    return seen


boxes = {}
for name, brep in parts.items():
    sub = reach(brep)
    pts = [tup(ents[refs(ents[n])[0]]) for n in sub if ents[n].startswith('VERTEX_POINT')]
    cyls = []
    for n in sub:
        if ents[n].startswith('CYLINDRICAL_SURFACE'):
            a2p = refs(ents[n])[0]
            o = tup(ents[refs(ents[a2p])[0]])
            ax = tup(ents[refs(ents[a2p])[1]])
            r = float(ents[n].rsplit(',', 1)[1].rstrip(') '))
            cyls.append((o, ax, r))
    for o, ax, r in cyls:                       # bbox do cilindro: eixo + raio
        ia = [i for i, v in enumerate(ax) if abs(v) > .5][0]
        for p in list(pts):
            for k in range(3):
                if k != ia:
                    q = list(p)
                    q[k] = o[k] + r
                    pts.append(q)
                    q2 = list(p)
                    q2[k] = o[k] - r
                    pts.append(q2)
    xs, ys, zs = zip(*[(p[0], p[1], p[2]) for p in pts])
    boxes[name] = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))

NEW = ['raspberry_pi_4', 'esp32_devkit', 'suporte_BNO055', 'bno055_imu', 'suporte_GPS',
       'gps_modulo', 'conversor_DCDC_5V', 'distribuidor_fusiveis', 'sensor_corrente',
       'ads1015', 'esc_dir', 'esc_esq', 'motor_dir', 'motor_esq',
       'veio_motor_dir', 'veio_motor_esq', 'bateria_pi_2200']
print('\npartes: %d' % len(boxes))
for k in sorted(boxes):
    b = boxes[k]
    tag = '  <-- NOVO' if k in NEW else ''
    print('%-24s X %7.1f..%7.1f  Y %7.1f..%7.1f  Z %7.1f..%7.1f   (%6.1f x %6.1f x %6.1f)%s'
          % (k, b[0], b[1], b[2], b[3], b[4], b[5], b[1] - b[0], b[3] - b[2], b[5] - b[4], tag))

# --- colisoes entre componentes internos (ignora envolventes estruturais)
SHELL = {'casco_direito', 'casco_esquerdo', 'caixa_IP66', 'cobertura_ESC_dir',
         'cobertura_ESC_esq', 'escotilha_dir', 'escotilha_esq', 'transom_insert_dir',
         'transom_insert_esq'}


def ov(a, b):
    return min(a[1], b[1]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[2], b[2]), \
        min(a[5], b[5]) - max(a[4], b[4])


print('\ncolisoes entre componentes (excluindo cascos/caixa/coberturas):')
bad = 0
for a, b in itertools.combinations(sorted(boxes), 2):
    if a in SHELL or b in SHELL:
        continue
    o = ov(boxes[a], boxes[b])
    if all(v > 1e-6 for v in o):
        bad += 1
        print('  X %-22s %-22s  sobreposicao %.1f x %.1f x %.1f' % (a, b, *o))
print('  nenhuma' if not bad else '  %d colisoes' % bad)

# --- componentes dentro da caixa: verificar que cabem no interior
INT = (254.5, 453.5, -75.0, 75.0, 154.5, 252.0)
INSIDE = ['raspberry_pi_4', 'esp32_devkit', 'suporte_BNO055', 'bno055_imu', 'suporte_GPS',
          'gps_modulo', 'conversor_DCDC_5V', 'distribuidor_fusiveis', 'sensor_corrente',
          'ads1015', 'bateria_pi_2200']
print('\nfolgas ao interior da caixa (X %.1f..%.1f, Y %.1f..%.1f, Z %.1f..%.1f):'
      % INT)
for k in INSIDE:
    b = boxes[k]
    f = (b[0] - INT[0], INT[1] - b[1], b[2] - INT[2], INT[3] - b[3], b[4] - INT[4], INT[5] - b[5])
    status = 'OK ' if min(f) >= -1e-6 else 'FORA'
    print('  %s %-24s  -X %6.1f  +X %6.1f  -Y %6.1f  +Y %6.1f  -Z %6.1f  +Z %6.1f'
          % (status, k, *f))

# --- CG estimado (massas tipicas, kg)
MASS = {
    'casco_direito': 2.2, 'casco_esquerdo': 2.2,
    'travessa_T1': 0.45, 'travessa_T2': 0.45, 'travessa_T3': 0.45,
    'longarina_proa_dir': .08, 'longarina_proa_esq': .08,
    'longarina_re_dir': .35, 'longarina_re_esq': .35,
    'escotilha_dir': .12, 'escotilha_esq': .12,
    'transom_insert_dir': .18, 'transom_insert_esq': .18,
    'cobertura_ESC_dir': .12, 'cobertura_ESC_esq': .12,
    'caixa_IP66': 0.9, 'calco_IP66_1': .02, 'calco_IP66_2': .02,
    'calco_IP66_3': .02, 'calco_IP66_4': .02,
    'bateria_5000_dir': 0.55, 'bateria_5000_esq': 0.55, 'bateria_pi_2200': 0.19,
    'waterjet_dir': 0.35, 'waterjet_esq': 0.35,
    'motor_dir': 0.32, 'motor_esq': 0.32, 'veio_motor_dir': .02, 'veio_motor_esq': .02,
    'esc_dir': 0.12, 'esc_esq': 0.12,
    'raspberry_pi_4': 0.05, 'esp32_devkit': 0.01, 'bno055_imu': 0.005,
    'gps_modulo': 0.02, 'suporte_BNO055': 0.01, 'suporte_GPS': 0.015,
    'conversor_DCDC_5V': 0.04, 'distribuidor_fusiveis': 0.09,
    'sensor_corrente': 0.02, 'ads1015': 0.005,
}
tot = 0.0
mom = [0.0, 0.0, 0.0]
for k, b in boxes.items():
    m = MASS.get(k, 0.0)
    c = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)
    tot += m
    for i in range(3):
        mom[i] += m * c[i]
print('\nmassa estimada %.2f kg   CG  X %.0f mm (%.0f%% do comprimento)  Y %+.1f mm  Z %.0f mm'
      % (tot, mom[0] / tot, mom[0] / tot / 800 * 100, mom[1] / tot, mom[2] / tot))
