#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validacao do STEP com o kernel OpenCASCADE (OCP): le a montagem, verifica
cada solido com BRepCheck_Analyzer e imprime volume e bounding box."""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence
from OCP.TDataStd import TDataStd_Name
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.IFSelect import IFSelect_ReturnStatus

path = sys.argv[1]
doc = TDocStd_Document(TCollection_ExtendedString("d"))
rd = STEPCAFControl_Reader()
rd.SetNameMode(True)
rd.SetColorMode(True)
st = rd.ReadFile(path)
assert st == IFSelect_ReturnStatus.IFSelect_RetDone, 'falhou a leitura do STEP'
assert rd.Transfer(doc), 'falhou a transferencia'

tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
labels = TDF_LabelSequence()
tool.GetFreeShapes(labels)

rows = []
bad = []
total = 0.0


def walk(label):
    global total
    name = ''
    from OCP.TDF import TDF_Label
    nm = TDataStd_Name()
    if label.FindAttribute(TDataStd_Name.GetID_s(), nm):
        name = nm.Get().ToExtString()
    if tool.IsAssembly_s(label):
        comp = TDF_LabelSequence()
        tool.GetComponents_s(label, comp)
        for i in range(1, comp.Length() + 1):
            c = comp.Value(i)
            ref = c
            from OCP.TDF import TDF_Label as L
            r = L()
            if tool.GetReferredShape_s(c, r):
                nm2 = TDataStd_Name()
                lbl = c
                sub = r
                walk_named(sub, c)
            else:
                walk(c)
        return
    walk_named(label, label)


def walk_named(shape_label, name_label):
    global total
    nm = TDataStd_Name()
    name = ''
    if name_label.FindAttribute(TDataStd_Name.GetID_s(), nm):
        name = nm.Get().ToExtString()
    if not name and shape_label.FindAttribute(TDataStd_Name.GetID_s(), nm):
        name = nm.Get().ToExtString()
    sh = tool.GetShape_s(shape_label)
    if sh.IsNull():
        return
    ok = BRepCheck_Analyzer(sh).IsValid()
    p = GProp_GProps()
    BRepGProp.VolumeProperties_s(sh, p)
    v = p.Mass() / 1000.0                      # mm3 -> cm3
    b = Bnd_Box()
    BRepBndLib.Add_s(sh, b)
    xmin, ymin, zmin, xmax, ymax, zmax = b.Get()
    rows.append((name.strip(':1'), ok, v, xmin, xmax, ymin, ymax, zmin, zmax))
    if not ok:
        bad.append(name)
    total += v


for i in range(1, labels.Length() + 1):
    walk(labels.Value(i))

print('%-24s %-5s %9s   %s' % ('parte', 'valid', 'vol cm3', 'bounding box (mm)'))
for r in sorted(rows):
    print('%-24s %-5s %9.1f   X %7.1f..%7.1f  Y %7.1f..%7.1f  Z %7.1f..%7.1f'
          % (r[0], 'OK' if r[1] else 'MAU', r[2], r[3], r[4], r[5], r[6], r[7], r[8]))
print('\n%d solidos lidos | invalidos: %s | volume total %.0f cm3'
      % (len(rows), bad or 'nenhum', total))
