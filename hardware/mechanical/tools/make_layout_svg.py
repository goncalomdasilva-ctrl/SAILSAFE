#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Desenho de implantacao (2 vistas ortograficas) a partir do STEP, em SVG."""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

SRC, DST = sys.argv[1], sys.argv[2]
doc = TDocStd_Document(TCollection_ExtendedString("d"))
rd = STEPCAFControl_Reader()
rd.SetNameMode(True)
rd.ReadFile(SRC)
rd.Transfer(doc)
tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
free = TDF_LabelSequence()
tool.GetFreeShapes(free)

bb = {}


def visit(label):
    if tool.IsAssembly_s(label):
        comp = TDF_LabelSequence()
        tool.GetComponents_s(label, comp)
        for i in range(1, comp.Length() + 1):
            visit(comp.Value(i))
        return
    nm = TDataStd_Name()
    name = ''
    if label.FindAttribute(TDataStd_Name.GetID_s(), nm):
        name = nm.Get().ToExtString().split(':')[0]
    r = TDF_Label()
    sh = tool.GetShape_s(r if tool.GetReferredShape_s(label, r) else label)
    if sh.IsNull():
        return
    b = Bnd_Box()
    BRepBndLib.Add_s(sh, b)
    bb[name] = b.Get()


for i in range(1, free.Length() + 1):
    visit(free.Value(i))

COL = {
    'casco': '#c9a227', 'travessa': '#b08d3f', 'longarina': '#b08d3f',
    'escotilha': '#d8c48a', 'transom': '#b08d3f', 'calco': '#b08d3f',
    'caixa_IP66': '#9aa7b5', 'cobertura': '#9aa7b5',
    'bateria': '#e05a3c', 'waterjet': '#4c9be8',
    'raspberry': '#0d7340', 'esp32': '#1f4090', 'bno055': '#8033a0',
    'gps': '#e58019', 'suporte': '#9a9a9e', 'conversor': '#e5cc33',
    'distribuidor': '#cc2626', 'sensor': '#8c1a1a', 'ads1015': '#1ab3bf',
    'esc': '#2e2e33', 'motor': '#bfc4c9', 'veio': '#72777f',
}
STRUCT = ('casco', 'travessa', 'longarina', 'escotilha', 'transom', 'calco',
          'caixa_IP66', 'cobertura')


def colour(n):
    for k, v in COL.items():
        if n.startswith(k):
            return v
    return '#888'


def is_struct(n):
    return n.startswith(STRUCT)


S = 1.0            # escala px/mm
PAD = 60
LEG = 250          # coluna de legenda
W = int(800 * S + 2 * PAD + LEG)
H = int((350 + 260) * S + 3 * PAD + 60)
out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
       'viewBox="0 0 %d %d" font-family="DejaVu Sans, Arial" font-size="9">' % (W, H, W, H),
       '<rect x="0" y="0" width="%d" height="%d" fill="#fbfbfa"/>' % (W, H)]


def rect(x, y, w, h, c, op, sw=0.6):
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" '
               'fill-opacity="%.2f" stroke="#333" stroke-width="%.1f"/>'
               % (x, y, w, h, c, op, sw))


def label(x, y, t, anchor='middle', size=9, col='#111'):
    out.append('<text x="%.1f" y="%.1f" text-anchor="%s" font-size="%d" fill="%s">%s</text>'
               % (x, y, anchor, size, col, t))


comp = sorted([n for n in bb if not is_struct(n)])
num = {n: i + 1 for i, n in enumerate(comp)}


def badge(cx, cy, n):
    out.append('<circle cx="%.1f" cy="%.1f" r="6.5" fill="#fff" fill-opacity="0.92" '
               'stroke="#222" stroke-width="0.7"/>' % (cx, cy))
    label(cx, cy + 3, str(num[n]), 'middle', 8)


# ---- vista de cima (X horizontal, Y vertical)
ox, oy = PAD, PAD + 10
label(PAD, PAD - 4, 'VISTA DE CIMA  (proa a esquerda)', 'start', 11)
for n, (x0, y0, z0, x1, y1, z1) in sorted(bb.items(), key=lambda kv: not is_struct(kv[0])):
    rect(ox + x0 * S, oy + (175 - y1) * S, (x1 - x0) * S, (y1 - y0) * S,
         colour(n), .28 if is_struct(n) else .85)
for n in comp:
    x0, y0, z0, x1, y1, z1 = bb[n]
    badge(ox + (x0 + x1) / 2 * S, oy + (175 - (y0 + y1) / 2) * S, n)

# ---- vista lateral (X horizontal, Z vertical)
oy2 = oy + 350 * S + PAD + 20
label(PAD, oy2 - 14, 'VISTA LATERAL  (corte pelo eixo)', 'start', 11)
for n, (x0, y0, z0, x1, y1, z1) in sorted(bb.items(), key=lambda kv: not is_struct(kv[0])):
    rect(ox + x0 * S, oy2 + (252 - z1) * S, (x1 - x0) * S, (z1 - z0) * S,
         colour(n), .22 if is_struct(n) else .85)
for n in comp:
    if n.endswith('_esq'):
        continue
    x0, y0, z0, x1, y1, z1 = bb[n]
    badge(ox + (x0 + x1) / 2 * S, oy2 + (252 - (z0 + z1) / 2) * S, n)

# ---- legenda
lx = PAD + 800 * S + 24
ly = oy + 4
label(lx, ly, 'COMPONENTES', 'start', 11)
ly += 16
for n in comp:
    x0, y0, z0, x1, y1, z1 = bb[n]
    out.append('<rect x="%.1f" y="%.1f" width="9" height="9" fill="%s" stroke="#333" '
               'stroke-width="0.5"/>' % (lx, ly - 8, colour(n)))
    out.append('<circle cx="%.1f" cy="%.1f" r="6.5" fill="#fff" stroke="#222" '
               'stroke-width="0.7"/>' % (lx + 21, ly - 3.5))
    label(lx + 21, ly - 0.5, str(num[n]), 'middle', 8)
    label(lx + 32, ly, n, 'start', 8)
    label(lx + LEG - 34, ly, '%g x %g x %g' % (x1 - x0, y1 - y0, z1 - z0), 'end', 7, '#666')
    ly += 13

# escala
out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#111" stroke-width="1"/>'
           % (ox, H - 28, ox + 100 * S, H - 28))
label(ox + 50 * S, H - 32, '100 mm', 'middle', 9)
label(W - 24, H - 28, 'SAILSAFE - conceito v6.3 - implantacao de componentes', 'end', 10, '#555')
out.append('</svg>')
open(DST, 'w', encoding='utf-8').write('\n'.join(out))
print('escrito', DST, '|', len(bb), 'partes')
