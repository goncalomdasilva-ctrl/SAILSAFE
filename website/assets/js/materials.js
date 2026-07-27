/* SAILSAFE — texturas procedurais e materiais PBR */
import * as THREE from 'three';

const cv = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
const tex = (c, rep = 1) => {
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(rep, rep);
  t.anisotropy = 8;
  return t;
};
const rnd = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(42);

/* --------- veio de madeira --------- */
function woodMaps() {
  const S = 512, c = cv(S, S), x = c.getContext('2d');
  x.fillStyle = '#c08a4e'; x.fillRect(0, 0, S, S);
  for (let i = 0; i < 2600; i++) {
    const y = rnd() * S, amp = 5 + rnd() * 16, ph = rnd() * 6.28;
    const l = 0.55 + rnd() * 0.45;
    x.strokeStyle = `rgba(${90 + l * 80 | 0},${58 + l * 60 | 0},${28 + l * 40 | 0},${0.06 + rnd() * 0.16})`;
    x.lineWidth = 0.6 + rnd() * 2.4;
    x.beginPath();
    for (let px = 0; px <= S; px += 8) x.lineTo(px, y + Math.sin(px / 46 + ph) * amp + Math.sin(px / 11) * 2);
    x.stroke();
  }
  for (let i = 0; i < 26; i++) {                       /* nós */
    const kx = rnd() * S, ky = rnd() * S, r = 4 + rnd() * 11;
    for (let j = r; j > 0; j -= 1.1) {
      x.strokeStyle = `rgba(72,44,20,${0.05 + 0.1 * rnd()})`;
      x.lineWidth = 0.8;
      x.beginPath(); x.ellipse(kx, ky, j, j * 0.55, rnd(), 0, 6.283); x.stroke();
    }
  }
  const r = cv(S, S), rx = r.getContext('2d');
  rx.drawImage(c, 0, 0);
  const d = rx.getImageData(0, 0, S, S), p = d.data;
  for (let i = 0; i < p.length; i += 4) {
    const v = 150 + (p[i] - 150) * 0.5;
    p[i] = p[i + 1] = p[i + 2] = v;
  }
  rx.putImageData(d, 0, 0);
  return { map: tex(c), rough: tex(r) };
}

/* --------- granulado (ABS, plástico técnico) --------- */
function grainMap(base = 190, amt = 46) {
  const S = 256, c = cv(S, S), x = c.getContext('2d');
  const d = x.createImageData(S, S), p = d.data;
  for (let i = 0; i < p.length; i += 4) {
    const v = base + (rnd() - 0.5) * amt;
    p[i] = p[i + 1] = p[i + 2] = v; p[i + 3] = 255;
  }
  x.putImageData(d, 0, 0);
  return tex(c, 4);
}

/* --------- metal escovado --------- */
function brushedMap() {
  const S = 256, c = cv(S, S), x = c.getContext('2d');
  x.fillStyle = '#8a8a8a'; x.fillRect(0, 0, S, S);
  for (let i = 0; i < 5200; i++) {
    const y = rnd() * S, l = 20 + rnd() * 190;
    x.strokeStyle = `rgba(${rnd() > .5 ? 255 : 0},${rnd() > .5 ? 255 : 0},${rnd() > .5 ? 255 : 0},.035)`;
    x.lineWidth = 0.5 + rnd();
    x.beginPath(); x.moveTo(rnd() * S, y); x.lineTo(rnd() * S + l, y + (rnd() - .5)); x.stroke();
  }
  return tex(c, 3);
}

/* --------- PCB --------- */
function pcbMaps(base = '#0d6b3c') {
  const S = 512, c = cv(S, S), x = c.getContext('2d');
  x.fillStyle = base; x.fillRect(0, 0, S, S);
  x.strokeStyle = 'rgba(215,180,60,.5)'; x.lineCap = 'square';
  for (let i = 0; i < 150; i++) {
    x.lineWidth = 1 + rnd() * 2.5;
    let px = rnd() * S, py = rnd() * S;
    x.beginPath(); x.moveTo(px, py);
    for (let k = 0; k < 4 + rnd() * 5; k++) {
      rnd() > .5 ? px += (rnd() - .5) * 130 : py += (rnd() - .5) * 130;
      x.lineTo(px, py);
    }
    x.stroke();
  }
  x.fillStyle = 'rgba(226,190,80,.85)';
  for (let i = 0; i < 260; i++) {
    const s = 3 + rnd() * 5;
    x.fillRect(rnd() * S, rnd() * S, s, s);
  }
  x.fillStyle = 'rgba(12,12,14,.9)';
  for (let i = 0; i < 26; i++) x.fillRect(rnd() * S, rnd() * S, 10 + rnd() * 44, 8 + rnd() * 26);
  return { map: tex(c, 1.6) };
}

let CACHE = null;
function maps() {
  if (!CACHE) CACHE = {
    wood: woodMaps(),
    grain: grainMap(196, 40),
    grainFine: grainMap(210, 22),
    brushed: brushedMap(),
    pcbGreen: pcbMaps('#0d6b3c'),
    pcbBlue: pcbMaps('#16326e')
  };
  return CACHE;
}

const WOOD  = /travessa|longarina|escotilha|calco|cobertura_ESC|transom/;
const HULL  = /^casco/;
const METAL = /^motor|^waterjet|^veio|^suporte_/;
const PCB   = /raspberry|esp32|ads1015|bno055|sensor_corrente/;
const BATT  = /^bateria/;
const DARK  = /^esc_/;

/* Aplica um material realista a uma peça, mantendo a cor de origem
   como base quando não há textura específica. */
export function assign(mesh, name, baseColor) {
  const M = maps();
  const common = { envMapIntensity: 1.15 };
  let m;

  /* Componentes detalhados (nome__material) já trazem cor, metalness e
     roughness corretos de detail.py — não há nada a adivinhar. */
  if (name.includes('__')) {
    const src = mesh.material;
    m = new THREE.MeshStandardMaterial({
      color: src.color ? src.color.clone() : new THREE.Color(baseColor),
      metalness: src.metalness ?? 0.2,
      roughness: src.roughness ?? 0.5,
      envMapIntensity: 1.2
    });
    if (m.metalness > 0.7) m.roughnessMap = M.brushed;
    m.name = name;
    mesh.material.dispose();
    mesh.material = m;
    return m;
  }

  if (HULL.test(name)) {
    m = new THREE.MeshPhysicalMaterial({
      color: 0xf2f4f5, roughness: 0.34, metalness: 0.0,
      clearcoat: 0.9, clearcoatRoughness: 0.1,
      roughnessMap: M.grainFine, sheen: 0.15, sheenColor: 0xbcd6e6, ...common
    });
  } else if (WOOD.test(name)) {
    m = new THREE.MeshStandardMaterial({
      map: M.wood.map, roughnessMap: M.wood.rough,
      roughness: 0.82, metalness: 0.0, color: 0xffffff, ...common
    });
  } else if (name === 'caixa_IP66') {
    m = new THREE.MeshPhysicalMaterial({
      color: 0x8e969e, roughness: 0.62, metalness: 0.0,
      roughnessMap: M.grain, clearcoat: 0.35, clearcoatRoughness: 0.5, ...common
    });
  } else if (METAL.test(name)) {
    const anod = /waterjet/.test(name);
    m = new THREE.MeshStandardMaterial({
      color: anod ? 0x9aa4ad : 0xc6ccd2,
      metalness: 0.96, roughness: anod ? 0.38 : 0.26,
      roughnessMap: M.brushed, ...common
    });
  } else if (PCB.test(name)) {
    const blue = /esp32/.test(name);
    m = new THREE.MeshStandardMaterial({
      map: (blue ? M.pcbBlue : M.pcbGreen).map,
      roughness: 0.55, metalness: 0.15, color: 0xffffff, ...common
    });
  } else if (BATT.test(name)) {
    m = new THREE.MeshPhysicalMaterial({
      color: 0x23262b, roughness: 0.3, metalness: 0.05,
      clearcoat: 0.7, clearcoatRoughness: 0.22, ...common
    });
  } else if (DARK.test(name)) {
    m = new THREE.MeshStandardMaterial({
      color: 0x1c1e21, roughness: 0.72, metalness: 0.1,
      roughnessMap: M.grain, ...common
    });
  } else {
    m = new THREE.MeshStandardMaterial({
      color: baseColor, roughness: 0.5, metalness: 0.1,
      roughnessMap: M.grainFine, ...common
    });
  }
  m.name = name;
  mesh.material.dispose();
  mesh.material = m;
  return m;
}

/* Ambiente de estúdio: softboxes num recinto claro, convertido em envmap.
   Substitui o RoomEnvironment, que dá reflexos baços e sem direção. */
export function studioEnvironment(renderer) {
  const s = new THREE.Scene();
  const box = new THREE.BoxGeometry();
  box.deleteAttribute('uv');
  const put = (col, int, pos, scale) => {
    const m = new THREE.Mesh(box, new THREE.MeshBasicMaterial({ side: THREE.BackSide }));
    m.material.color.setHex(col).multiplyScalar(int);
    m.position.fromArray(pos); m.scale.fromArray(scale);
    s.add(m);
  };
  /* recinto */
  put(0xffffff, 0.62, [0, 0, 0], [22, 13, 22]);
  /* chão frio */
  const floor = new THREE.Mesh(box, new THREE.MeshBasicMaterial());
  floor.material.color.setHex(0xb9c6d1).multiplyScalar(0.55);
  floor.position.set(0, -6.4, 0); floor.scale.set(22, 0.6, 22); s.add(floor);
  /* softboxes */
  const light = (col, int, pos, scale) => {
    const m = new THREE.Mesh(box, new THREE.MeshBasicMaterial());
    m.material.color.setHex(col).multiplyScalar(int);
    m.position.fromArray(pos); m.scale.fromArray(scale); s.add(m);
  };
  light(0xffffff, 7.5, [ 0,  6.2,  0], [7, 0.4, 5]);
  light(0xfff2e2, 5.0, [-5,  3.4,  3], [0.4, 4, 5]);
  light(0xdcecff, 4.2, [ 5,  2.6, -4], [0.4, 3, 6]);
  light(0xffffff, 3.0, [ 0,  1.2,  7], [6, 3, 0.4]);
  light(0xffd9b0, 2.2, [ 3, -1.5, -6], [5, 2, 0.4]);

  const pm = new THREE.PMREMGenerator(renderer);
  const t = pm.fromScene(s, 0.02).texture;
  pm.dispose(); s.traverse(o => o.material && o.material.dispose()); box.dispose();
  return t;
}

/* Normal map de água, animável */
export function waterNormals() {
  const S = 256, c = cv(S, S), x = c.getContext('2d');
  const d = x.createImageData(S, S), p = d.data;
  for (let y = 0; y < S; y++) for (let xx = 0; xx < S; xx++) {
    const i = (y * S + xx) * 4;
    const h = Math.sin(xx / 9 + Math.sin(y / 17) * 2) * Math.cos(y / 13) * 0.5 + 0.5;
    const g = Math.cos(xx / 9) * 0.5;
    p[i] = 128 + g * 40; p[i + 1] = 128 + (h - .5) * 60; p[i + 2] = 245; p[i + 3] = 255;
  }
  x.putImageData(d, 0, 0);
  const t = tex(c, 5);
  return t;
}
