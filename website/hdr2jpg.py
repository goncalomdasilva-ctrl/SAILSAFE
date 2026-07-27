#!/usr/bin/env python3
"""Leitor de Radiance .hdr (RGBE) + tone mapping ACES -> JPEG sRGB."""
import numpy as np, sys
from PIL import Image

def read_hdr(path):
    f = open(path, 'rb')
    if not f.readline().startswith(b'#?'): raise ValueError('não é Radiance')
    while True:
        ln = f.readline()
        if ln.strip() == b'': break
    w = h = None
    res = f.readline().split()
    if res[0] == b'-Y': h, w = int(res[1]), int(res[3])
    else: raise ValueError('orientação não suportada: %s' % res)
    data = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        head = f.read(4)
        if head[0] == 2 and head[1] == 2 and (head[2] << 8 | head[3]) == w:
            # RLE novo: 4 canais separados
            for c in range(4):
                x = 0
                while x < w:
                    n = f.read(1)[0]
                    if n > 128:                       # série repetida
                        v = f.read(1)[0]
                        data[y, x:x + n - 128, c] = v
                        x += n - 128
                    else:                             # série literal
                        buf = f.read(n)
                        data[y, x:x + n, c] = np.frombuffer(buf, np.uint8)
                        x += n
        else:
            raw = head + f.read(w * 4 - 4)
            data[y] = np.frombuffer(raw, np.uint8).reshape(w, 4)
    f.close()
    e = data[..., 3].astype(np.int32)
    scale = np.where(e == 0, 0.0, np.ldexp(1.0, e - 136))
    rgb = data[..., :3].astype(np.float32) * scale[..., None]
    return rgb

def aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)

def tonemap(rgb, exposure=1.0, sat=1.06):
    x = rgb * exposure
    y = aces(x)
    if sat != 1.0:
        lum = (y * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
        y = np.clip(lum + (y - lum) * sat, 0, 1)
    return (np.power(y, 1 / 2.2) * 255).astype(np.uint8)   # sRGB

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    W = int(sys.argv[3]) if len(sys.argv) > 3 else 3072
    ev = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    rgb = read_hdr(src)
    h, w, _ = rgb.shape
    print('HDR %dx%d | luminância: mediana %.3f  p99 %.2f  máx %.0f'
          % (w, h, np.median(rgb), np.percentile(rgb, 99), rgb.max()))
    # exposição automática: põe a mediana num cinzento agradável
    auto = 0.34 / max(1e-4, float(np.median(rgb)))
    ev = ev * auto
    print('exposição aplicada: %.3f' % ev)
    im = Image.fromarray(tonemap(rgb, ev))
    im = im.resize((W, W // 2), Image.LANCZOS)
    im.save(dst, 'JPEG', quality=84, optimize=True, progressive=True)
    import os
    print('->', dst, im.size, os.path.getsize(dst) // 1024, 'kB')
