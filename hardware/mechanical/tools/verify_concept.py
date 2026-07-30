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

# --- MODULOS -----------------------------------------------------------
# A partir do v6_4 os modulos deixaram de ser um solido cada: o Raspberry Pi
# passou a 13 solidos `rpi4_*`, o ESP32 a 8 `esp32_*`, e o mesmo para o
# BNO055, o GPS e os waterjets. As folgas e o CG raciocinam sobre o MODULO
# (o Pi cabe na caixa?), nao sobre cada conector, portanto a unidade aqui e
# o modulo: bounding box = uniao das sub-pecas, massa aplicada no centroide
# dessa uniao.
#
# Massas em kg. Estimativas de catalogo, NAO pesagens -- nenhum valor aqui
# foi medido numa balanca.
MODULES = {
    # --- estrutura
    'casco_direito':      (2.2,  ['casco_direito']),
    'casco_esquerdo':     (2.2,  ['casco_esquerdo']),
    'travessa_T1':        (0.45, ['travessa_T1']),
    'travessa_T2':        (0.45, ['travessa_T2']),
    'travessa_T3':        (0.45, ['travessa_T3']),
    'longarina_proa_dir': (.08,  ['longarina_proa_dir']),
    'longarina_proa_esq': (.08,  ['longarina_proa_esq']),
    'longarina_re_dir':   (.35,  ['longarina_re_dir']),
    'longarina_re_esq':   (.35,  ['longarina_re_esq']),
    'escotilha_dir':      (.12,  ['escotilha_dir']),
    'escotilha_esq':      (.12,  ['escotilha_esq']),
    'transom_insert_dir': (.18,  ['transom_insert_dir']),
    'transom_insert_esq': (.18,  ['transom_insert_esq']),
    'cobertura_ESC_dir':  (.12,  ['cobertura_ESC_dir']),
    'cobertura_ESC_esq':  (.12,  ['cobertura_ESC_esq']),
    'caixa_IP66':         (0.9,  ['caixa_IP66']),
    'calco_IP66_1':       (.02,  ['calco_IP66_1']),
    'calco_IP66_2':       (.02,  ['calco_IP66_2']),
    'calco_IP66_3':       (.02,  ['calco_IP66_3']),
    'calco_IP66_4':       (.02,  ['calco_IP66_4']),
    # --- energia
    'bateria_5000_dir':   (0.55, ['bateria_5000_dir']),
    'bateria_5000_esq':   (0.55, ['bateria_5000_esq']),
    'bateria_pi_2200':    (0.19, ['bateria_pi_2200']),
    # --- propulsao
    # 0.35 kg e o conjunto do waterjet, distribuido pela uniao das sub-pecas
    # (duto + admissao + grelha + estator + tubeira + bocal + braco do servo).
    'waterjet_dir':       (0.35, ['waterjet_dir', 'wj_admissao_dir', 'wj_grelha_dir0',
                                  'wj_grelha_dir1', 'wj_grelha_dir2', 'wj_estator_dir',
                                  'wj_tubeira_dir', 'wj_bocal_dir', 'wj_braco_servo_dir']),
    'waterjet_esq':       (0.35, ['waterjet_esq', 'wj_admissao_esq', 'wj_grelha_esq0',
                                  'wj_grelha_esq1', 'wj_grelha_esq2', 'wj_estator_esq',
                                  'wj_tubeira_esq', 'wj_bocal_esq', 'wj_braco_servo_esq']),
    'motor_dir':          (0.32, ['motor_dir']),
    'motor_esq':          (0.32, ['motor_esq']),
    'veio_motor_dir':     (.02,  ['veio_motor_dir']),
    'veio_motor_esq':     (.02,  ['veio_motor_esq']),
    'esc_dir':            (0.12, ['esc_dir']),
    'esc_esq':            (0.12, ['esc_esq']),
    # Servos do bocal orientavel, introduzidos no v6_4 e sem massa ate agora.
    # O corpo modelado (23 x 12 x 18) e da classe SG90 (~9 g); 0.012 inclui
    # veio e abas. Se o bocal precisar de servo de engrenagem metalica --
    # provavel, contra o impulso do jato -- este numero triplica.
    'servo_bocal_dir':    (.012, ['servo_corpo_dir', 'servo_veio_dir', 'servo_abas_dir']),
    'servo_bocal_esq':    (.012, ['servo_corpo_esq', 'servo_veio_esq', 'servo_abas_esq']),
    # --- eletronica (dentro da caixa IP66)
    'raspberry_pi_4':     (0.05, ['rpi4_pcb', 'rpi4_soc', 'rpi4_ram', 'rpi4_gpio',
                                  'rpi4_gpio_pinos', 'rpi4_ethernet', 'rpi4_usb2',
                                  'rpi4_usb3', 'rpi4_usbc', 'rpi4_hdmi0', 'rpi4_hdmi1',
                                  'rpi4_csi', 'rpi4_dsi']),
    'esp32_devkit':       (0.01, ['esp32_pcb', 'esp32_wroom', 'esp32_antena', 'esp32_usb',
                                  'esp32_btn_a', 'esp32_btn_b', 'esp32_header_a',
                                  'esp32_header_b']),
    'bno055_imu':         (.005, ['bno055_pcb', 'bno055_chip', 'bno055_header']),
    'suporte_BNO055':     (.01,  ['suporte_BNO055']),
    'gps_modulo':         (0.02, ['gps_pcb', 'gps_lna', 'gps_antena', 'gps_header']),
    'suporte_GPS':        (.015, ['suporte_GPS']),
    'conversor_DCDC_5V':  (0.04, ['conversor_DCDC_5V']),
    'distribuidor_fusiveis': (0.09, ['distribuidor_fusiveis']),
    'sensor_corrente':    (0.02, ['sensor_corrente']),
    'ads1015':            (.005, ['ads1015']),
}

# --- integridade da tabela de modulos ----------------------------------
# O modo de falha anterior era silencioso: `MASS.get(k, 0.0)` dava massa zero
# a qualquer solido cujo nome tivesse mudado, e o CG saia errado sem aviso.
# Aqui as duas direccoes sao verificadas e impressas.
mapped = {}
absent = {}
for mod, (_, members) in MODULES.items():
    have = [p for p in members if p in boxes]
    gone = [p for p in members if p not in boxes]
    if gone:
        absent[mod] = gone
    for p in have:
        mapped.setdefault(p, []).append(mod)

orphans = sorted(set(boxes) - set(mapped))
doubles = {p: m for p, m in mapped.items() if len(m) > 1}

print('\nintegridade da tabela de modulos:')
print('  modulos %d  |  solidos mapeados %d/%d' % (len(MODULES), len(mapped), len(boxes)))
if absent:
    for mod, gone in sorted(absent.items()):
        print('  AUSENTE  %-22s nao existe neste STEP: %s' % (mod, ', '.join(gone)))
if orphans:
    for p in orphans:
        print('  ORFAO    %-22s solido sem modulo (entra no CG com massa 0)' % p)
if doubles:
    for p, m in sorted(doubles.items()):
        print('  DUPLO    %-22s em varios modulos: %s' % (p, ', '.join(m)))
if not (absent or orphans or doubles):
    print('  tudo mapeado, sem orfaos nem duplicados')

# bounding box do modulo = uniao das sub-pecas presentes
mboxes = {}
for mod, (_, members) in MODULES.items():
    bs = [boxes[p] for p in members if p in boxes]
    if not bs:
        continue
    mboxes[mod] = (min(b[0] for b in bs), max(b[1] for b in bs),
                   min(b[2] for b in bs), max(b[3] for b in bs),
                   min(b[4] for b in bs), max(b[5] for b in bs))

# --- componentes dentro da caixa: verificar que cabem no interior
INT = (254.5, 453.5, -75.0, 75.0, 154.5, 252.0)
INSIDE = ['raspberry_pi_4', 'esp32_devkit', 'suporte_BNO055', 'bno055_imu', 'suporte_GPS',
          'gps_modulo', 'conversor_DCDC_5V', 'distribuidor_fusiveis', 'sensor_corrente',
          'ads1015', 'bateria_pi_2200']
print('\nfolgas ao interior da caixa (X %.1f..%.1f, Y %.1f..%.1f, Z %.1f..%.1f):'
      % INT)
fora = 0
for k in INSIDE:
    if k not in mboxes:
        print('  ??? %-24s modulo sem geometria neste STEP' % k)
        continue
    b = mboxes[k]
    f = (b[0] - INT[0], INT[1] - b[1], b[2] - INT[2], INT[3] - b[3], b[4] - INT[4], INT[5] - b[5])
    status = 'OK ' if min(f) >= -1e-6 else 'FORA'
    fora += status == 'FORA'
    print('  %s %-24s  -X %6.1f  +X %6.1f  -Y %6.1f  +Y %6.1f  -Z %6.1f  +Z %6.1f'
          % (status, k, *f))
print('  %d modulo(s) fora do interior da caixa' % fora if fora else '  todos dentro')

# --- CG estimado (massas de catalogo, kg -- ver nota em MODULES)
tot = 0.0
mom = [0.0, 0.0, 0.0]
sem_massa = []
for mod, (m, _) in MODULES.items():
    if mod not in mboxes:
        sem_massa.append(mod)
        continue
    b = mboxes[mod]
    c = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)
    tot += m
    for i in range(3):
        mom[i] += m * c[i]

# comprimento derivado dos cascos, nao fixo em 800: o envelope estende-se
# ate ao bocal e a percentagem tem de ser do casco.
hulls = [mboxes[h] for h in ('casco_direito', 'casco_esquerdo') if h in mboxes]
L = max(b[1] for b in hulls) - min(b[0] for b in hulls) if hulls else 800.0
X0 = min(b[0] for b in hulls) if hulls else 0.0

print('\nmassa estimada %.2f kg em %d modulos%s'
      % (tot, len(MODULES) - len(sem_massa),
         '  (%d sem geometria: %s)' % (len(sem_massa), ', '.join(sem_massa)) if sem_massa else ''))
print('CG  X %.0f mm (%.1f%% do casco, L=%.0f mm)  Y %+.1f mm  Z %.0f mm'
      % (mom[0] / tot, (mom[0] / tot - X0) / L * 100, L, mom[1] / tot, mom[2] / tot))
if abs(mom[1] / tot) > 5.0:
    print('AVISO: CG lateral a %+.1f mm do plano de simetria.' % (mom[1] / tot))
