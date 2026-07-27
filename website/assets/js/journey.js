/* SAILSAFE — viagem imersiva.

   Duas panorâmicas equirectangulares reais da Praia da Marinha entram como
   céu esférico. A câmara roda dentro delas, por isso o movimento lê-se: é o
   cenário que passa. O scroll avança nos capítulos, o arrasto olha à volta,
   e as fichas técnicas aparecem ancoradas às peças do modelo.            */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { assign } from './materials.js';

const WL = 0.0382;

/* Rotação base do céu. Numa equirectangular, a coluna u vê-se na direção
   -X quando u=0. Resolvendo R = -az - 2πu para a água da enseada (u≈0,475)
   ficar no azimute de abertura (34°), dá 2,705 rad. É isto que põe o barco
   dentro da água e não em cima da areia. */
const SKY0 = 2.705;
const LOWQ = (() => { try {
  return matchMedia('(max-width:820px)').matches || matchMedia('(pointer:coarse)').matches;
} catch { return false; } })();

/* Capítulos. pano: 0 = mar aberto, 1 = na areia.
   az/el = ângulo de partida da câmara; o utilizador soma o seu arrasto. */
export const CH = [
  { id: 'run',    pano: 0, dist: 3.6, az:  34, el:  5, thr: 1.00, fov: 36, spots: [] },
  { id: 'jets',   pano: 0, dist: 1.15, az:  10, el:  4, thr: 0.95, fov: 40,
    spots: ['waterjet_dir', 'esc_dir'] },
  { id: 'hull',   pano: 0, dist: 1.55, az:  95, el:  2, thr: 0.55, fov: 34,
    spots: ['casco_direito', 'bateria_5000_dir'] },
  { id: 'beach',  pano: 1, dist: 1.30, az: 150, el:  8, thr: 0.12, fov: 32,
    spots: ['caixa_IP66', 'gps_modulo'] },
  { id: 'inside', pano: 1, dist: 0.72, az: 205, el: 16, thr: 0.00, fov: 30,
    spots: ['raspberry_pi_4', 'esp32_devkit', 'bno055_imu'] }
];

/* Âncoras no modelo, em metros (Y-up, X centrado no barco). */
export const ANCHOR = {
  waterjet_dir:     [ 0.395, 0.040, -0.117],
  esc_dir:          [ 0.327, 0.119, -0.117],
  casco_direito:    [-0.150, 0.100, -0.150],
  bateria_5000_dir: [-0.066, 0.062, -0.123],
  caixa_IP66:       [-0.053, 0.252,  0.000],
  gps_modulo:       [-0.135, 0.244, -0.060],
  raspberry_pi_4:   [-0.065, 0.183,  0.044],
  esp32_devkit:     [-0.080, 0.176, -0.019],
  bno055_imu:       [ 0.002, 0.220,  0.000]
};

export class Journey {
  constructor(canvas, onSpot) {
    this.canvas = canvas;
    this.onSpot = onSpot;
    this.t = 0; this.phase = 0; this.intro = 0;
    this.ch = 0; this.mix = 0;
    this.userAz = 0; this.userEl = 0;      // arrasto do utilizador
    this.velAz = 0; this.velEl = 0;
    this.ready = false;
    this._init();
  }

  _init() {
    const r = this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas, antialias: true
    });
    r.setPixelRatio(Math.min(devicePixelRatio, LOWQ ? 1.5 : 2));
    r.toneMapping = THREE.ACESFilmicToneMapping;
    r.toneMappingExposure = 1.05;
    const sc = this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(36, 2, 0.02, 200);

    /* --- céu esférico: duas panorâmicas com crossfade --- */
    const loader = new THREE.TextureLoader();
    const mk = (url, order) => {
      const t = loader.load(url, tx => {
        tx.colorSpace = THREE.SRGBColorSpace;
        tx.mapping = THREE.EquirectangularReflectionMapping;
        if (order === 0) this._applyEnv(tx);
      });
      const m = new THREE.Mesh(
        new THREE.SphereGeometry(60, 48, 32),
        new THREE.MeshBasicMaterial({ map: t, side: THREE.BackSide,
          transparent: true, opacity: order === 0 ? 1 : 0, depthWrite: false }));
      m.renderOrder = -10 + order;
      sc.add(m);
      return m;
    };
    /* no ficheiro único as panorâmicas vêm embutidas em base64 */
    const P = window.__SS_PANO__ || ['assets/img/pano_mar.jpg', 'assets/img/pano_areia.jpg'];
    this.skyYaw = 0;
    this.sky = [mk(P[0], 0), mk(P[1], 1)];

    const sun = new THREE.DirectionalLight(0xfff2dc, 2.6);
    sun.position.set(2.0, 1.6, 0.8); sc.add(sun);
    sc.add(new THREE.HemisphereLight(0xd8ecfa, 0x4a6b70, 0.9));

    /* --- água local, fundida com o mar da panorâmica --- */
    const seg = LOWQ ? 56 : 110;
    const geo = new THREE.PlaneGeometry(22, 22, seg, seg);
    geo.rotateX(-Math.PI / 2);
    this.wGeo = geo;
    this.wBase = Float32Array.from(geo.attributes.position.array);
    const am = document.createElement('canvas'); am.width = am.height = 256;
    const ax = am.getContext('2d');
    const rg = ax.createRadialGradient(128, 128, 8, 128, 128, 126);
    rg.addColorStop(0, '#fff'); rg.addColorStop(.42, '#fff');
    rg.addColorStop(.78, '#555'); rg.addColorStop(1, '#000');
    ax.fillStyle = rg; ax.fillRect(0, 0, 256, 256);
    /* normal map de ondulação fina: duas cópias a correr a velocidades
       diferentes dão a quebra irregular que uma malha só não consegue */
    const nn = document.createElement('canvas'); nn.width = nn.height = 256;
    const nx = nn.getContext('2d'), nd = nx.createImageData(256, 256), np = nd.data;
    for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) {
      const i = (y * 256 + x) * 4;
      const u = x / 256 * 6.283, v = y / 256 * 6.283;
      const dx = Math.cos(u * 3) * 0.5 + Math.cos(u * 7 + v * 2) * 0.3 + Math.cos(u * 13 - v) * 0.2;
      const dy = Math.cos(v * 4) * 0.5 + Math.cos(v * 9 - u * 3) * 0.3 + Math.cos(v * 15) * 0.2;
      np[i] = 128 + dx * 52; np[i + 1] = 128 + dy * 52; np[i + 2] = 246; np[i + 3] = 255;
    }
    nx.putImageData(nd, 0, 0);
    this.nrm = new THREE.CanvasTexture(nn);
    this.nrm.wrapS = this.nrm.wrapT = THREE.RepeatWrapping;
    this.nrm.repeat.set(9, 9);
    this.nrm2 = this.nrm.clone(); this.nrm2.needsUpdate = true;
    this.nrm2.wrapS = this.nrm2.wrapT = THREE.RepeatWrapping;
    this.nrm2.repeat.set(21, 21);

    this.water = new THREE.Mesh(geo, new THREE.MeshPhysicalMaterial({
      color: 0x2f97a4, roughness: 0.13, metalness: 0.0,
      normalMap: this.nrm, normalScale: new THREE.Vector2(0.55, 0.55),
      clearcoat: 0.9, clearcoatRoughness: 0.10,
      clearcoatNormalMap: this.nrm2,
      alphaMap: new THREE.CanvasTexture(am), transparent: true,
      depthWrite: false, envMapIntensity: 2.1, side: THREE.DoubleSide
    }));
    sc.add(this.water);

    /* --- espuma, esteira e jato --- */
    const rad = (a, b, c) => {
      const cv = document.createElement('canvas'); cv.width = cv.height = 128;
      const g = cv.getContext('2d'), gr = g.createRadialGradient(64, 64, 3, 64, 64, 62);
      gr.addColorStop(0, a); gr.addColorStop(.4, b); gr.addColorStop(1, c);
      g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
      return new THREE.CanvasTexture(cv);
    };
    const foam = rad('rgba(255,255,255,.9)', 'rgba(255,255,255,.3)', 'rgba(255,255,255,0)');
    this.bow = [1, -1].map(s => {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.20),
        new THREE.MeshBasicMaterial({ map: foam, transparent: true, depthWrite: false }));
      m.rotation.x = -Math.PI / 2; m.position.set(-0.26, WL + 0.003, -s * 0.117);
      sc.add(m); return m;
    });

    const wc = document.createElement('canvas'); wc.width = 8; wc.height = 256;
    const wx = wc.getContext('2d'), wg = wx.createLinearGradient(0, 0, 0, 256);
    wg.addColorStop(0, 'rgba(255,255,255,.95)');
    wg.addColorStop(.3, 'rgba(255,255,255,.32)');
    wg.addColorStop(1, 'rgba(255,255,255,0)');
    wx.fillStyle = wg; wx.fillRect(0, 0, 8, 256);
    this.wakeTex = new THREE.CanvasTexture(wc);
    this.wakeTex.wrapS = this.wakeTex.wrapT = THREE.RepeatWrapping;
    this.wakes = [1, -1].map(s => {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(0.09, 2.6),
        new THREE.MeshBasicMaterial({ map: this.wakeTex, transparent: true, depthWrite: false }));
      m.rotation.x = -Math.PI / 2; m.position.set(1.6, WL + 0.002, -s * 0.117);
      sc.add(m); return m;
    });

    /* jato tipo torneira: um tubo de água opaco e vidrado que sai do bocal
       e cai em arco balístico. Sem blending aditivo — água não brilha, tem
       corpo. A curva é recalculada por frame com a gravidade real. */
    const SEGJ = 26;
    this.jets = [1, -1].map(() => {
      const g = new THREE.CylinderGeometry(1, 1, 1, 12, SEGJ, true);
      g.rotateX(Math.PI / 2);                       // eixo ao longo de Z local
      const m = new THREE.Mesh(g, new THREE.MeshPhysicalMaterial({
        color: 0xbfe6ee, roughness: 0.05, metalness: 0.0,
        transmission: 0.5, thickness: 0.02, ior: 1.33,
        clearcoat: 1.0, clearcoatRoughness: 0.04,
        transparent: true, opacity: 0.85, side: THREE.DoubleSide,
        envMapIntensity: 2.2, depthWrite: false
      }));
      m.frustumCulled = false;
      this.scene.add(m);
      return { mesh: m, geo: g, base: Float32Array.from(g.attributes.position.array) };
    });

    /* dobra o cilindro unitário ao longo da parábola do jato */
    this._bendJet = (jet, x0, y0, z0, vx, vy, thr) => {
      const pos = jet.geo.attributes.position.array, base = jet.base;
      const r0 = 0.0065 * (0.6 + thr * 0.5);        // raio à saída do bocal
      const T = 0.34;                               // tempo de voo representado
      for (let i = 0; i < pos.length; i += 3) {
        const t = (base[i + 2] + 0.5) * T;          // ao longo do tubo: 0..T
        const rr = r0 * (1 + t * 2.6);              // alarga ao afastar-se
        pos[i]     = x0 + vx * t + base[i] * rr;
        pos[i + 1] = Math.max(WL - 0.004, y0 + vy * t - 4.9 * t * t) + base[i + 1] * rr;
        pos[i + 2] = z0 + base[i] * 0;              // sem desvio lateral
      }
      jet.geo.attributes.position.needsUpdate = true;
      jet.geo.computeVertexNormals();
    };

    this.N = LOWQ ? 110 : 260;
    this.sp = new Float32Array(this.N * 3);
    this.sv = new Float32Array(this.N * 3);
    this.sl = new Float32Array(this.N);
    for (let i = 0; i < this.N; i++) this.sl[i] = Math.random();
    const pg = new THREE.BufferGeometry();
    pg.setAttribute('position', new THREE.BufferAttribute(this.sp, 3));
    this.spray = new THREE.Points(pg, new THREE.PointsMaterial({
      map: rad('rgba(255,255,255,.98)', 'rgba(232,250,255,.42)', 'rgba(214,240,255,0)'),
      size: 0.017, transparent: true, depthWrite: false, sizeAttenuation: true,
      blending: THREE.AdditiveBlending
    }));
    sc.add(this.spray);

    /* --- arrasto: o utilizador olha à volta --- */
    let down = null, pinch = 0;
    const dn = e => { down = { x: e.clientX, y: e.clientY }; this.canvas.style.cursor = 'grabbing'; };
    const up = () => { down = null; this.canvas.style.cursor = 'grab'; };
    const mv = e => {
      if (!down) return;
      /* sensibilidade alta: uma travessia do ecrã dá quase uma volta completa */
      this.userAz -= (e.clientX - down.x) * 0.55;
      this.userEl += (e.clientY - down.y) * 0.34;
      this.velAz = -(e.clientX - down.x) * 1.1;      // inércia ao largar
      this.velEl =  (e.clientY - down.y) * 0.6;
      down = { x: e.clientX, y: e.clientY };
      this.touched = true;
    };
    this.canvas.addEventListener('pointerdown', dn);
    addEventListener('pointerup', up);
    addEventListener('pointermove', mv);

    this.zoom = 1;   // fixo: a roda fica livre para o scroll da página

    /* botão para repor o enquadramento, já que não volta sozinho */
    this.reset = () => {
      this.userAz = 0; this.userEl = 0;
      this.velAz = 0; this.velEl = 0;
    };

    addEventListener('resize', () => this._resize());
    if (window.ResizeObserver)
      new ResizeObserver(() => this._resize()).observe(this.canvas.parentElement);
    this._resize();
    this._loop();
  }

  _applyEnv(tx) {
    const pm = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pm.fromEquirectangular(tx).texture;
    pm.dispose();
  }

  async load(model) {
    const l = new GLTFLoader();
    const gltf = model instanceof ArrayBuffer
      ? await new Promise((res, rej) => l.parse(model, '', res, rej))
      : await l.loadAsync(model);
    const g = this.boat = new THREE.Group();
    gltf.scene.traverse(o => {
      if (!o.isMesh) return;
      assign(o, (o.name || '').replace(/_\d+$/, '').split('__')[0],
             o.material.color ? o.material.color.getHex() : 0x999999);
      o.material.envMapIntensity = 1.3;
    });
    g.add(gltf.scene); this.scene.add(g);

    const refl = gltf.scene.clone(true);
    refl.traverse(o => {
      if (!o.isMesh) return;
      o.material = o.material.clone();
      o.material.transparent = true; o.material.opacity = 0.20;
      o.material.depthWrite = false; o.material.side = THREE.BackSide;
    });
    const R = this.refl = new THREE.Group();
    R.add(refl); R.scale.y = -1; R.position.y = 2 * WL;
    this.scene.add(R);

    /* peças que fecham o veículo: desvanecem no capítulo do interior */
    const SHELL = /^casco|^caixa_IP66|^escotilha|^cobertura_ESC/;
    this.shell = [];
    g.traverse(o => {
      if (!o.isMesh) return;
      const n = (o.name || '').replace(/_\d+$/, '').split('__')[0];
      if (SHELL.test(n)) {
        o.material = o.material.clone();
        this.shell.push({ m: o.material, base: o.material.opacity ?? 1 });
      }
    });

    this.ready = true;
    return true;
  }

  _wave(x, z, t) {
    return 0.0058 * Math.sin(x * 2.6 + t * 1.8)
         + 0.0038 * Math.sin(z * 4.0 - t * 1.4)
         + 0.0021 * Math.sin((x * 0.6 + z) * 6.2 + t * 2.6);
  }

  setProgress(p) {
    const n = CH.length - 1;
    const q = Math.max(0, Math.min(n, p));
    this.ch = Math.floor(q); this.mix = q - this.ch;
  }

  /* posição de ecrã de uma âncora, ou null se estiver atrás da câmara */
  project(key) {
    const a = ANCHOR[key];
    if (!a || !this.ready) return null;
    const v = new THREE.Vector3(a[0] + this.bx, a[1] + this.by, a[2]);
    v.project(this.camera);
    if (v.z > 1) return null;
    const r = this.canvas.getBoundingClientRect();
    return { x: (v.x * 0.5 + 0.5) * r.width, y: (-v.y * 0.5 + 0.5) * r.height };
  }

  _resize() {
    const p = this.canvas.parentElement;
    const w = p.clientWidth, h = p.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h; this.camera.updateProjectionMatrix();
  }

  _loop() {
    requestAnimationFrame(() => this._loop());
    const dt = 0.016;
    this.t += dt;
    if (this.intro < 1) this.intro = Math.min(1, this.intro + dt / 3.0);

    const a = CH[this.ch], b = CH[Math.min(CH.length - 1, this.ch + 1)];
    const k = this.mix * this.mix * (3 - 2 * this.mix);
    const L = (u, v) => u + (v - u) * k;

    /* a caixa e as tampas abrem-se no capítulo do interior */
    const open = Math.max(0, Math.min(1, (this.ch + this.mix) - 3.15));
    if (this.shell) this.shell.forEach(o => {
      const t = 1 - open * 0.90;
      o.m.transparent = t < 1; o.m.opacity = t;
      o.m.depthWrite = t >= 1; o.m.needsUpdate = true;
    });

    /* crossfade das duas panorâmicas */
    const wantBeach = L(a.pano, b.pano);
    this.sky[1].material.opacity += (wantBeach - this.sky[1].material.opacity) * 0.05;
    /* ao mudar de cenário a câmara afasta-se e volta, como um voo curto */
    const swoop = Math.sin(Math.min(1, Math.max(0, (this.ch + this.mix - 2.1))) * Math.PI) * 0.9;

    const e = 1 - Math.pow(1 - this.intro, 3);
    const thr = L(a.thr, b.thr) * (0.45 + 0.55 * e);
    const vel = thr * 2.0;
    this.phase += vel * dt;

    /* água */
    const arr = this.wGeo.attributes.position.array, base = this.wBase;
    for (let i = 0; i < arr.length; i += 3)
      arr[i + 1] = this._wave(base[i] + this.phase, base[i + 2], this.t);
    this.wGeo.attributes.position.needsUpdate = true;
    this.wGeo.computeVertexNormals();
    this.water.material.opacity = 1 - wantBeach * 0.25;

    if (this.ready) {
      const ph = this.phase;
      const hC = this._wave(ph, 0, this.t);
      const hF = this._wave(ph - .4, 0, this.t), hA = this._wave(ph + .4, 0, this.t);
      const hL = this._wave(ph, -.117, this.t), hR = this._wave(ph, .117, this.t);
      const bx = this.bx = (1 - e) * 2.6;
      const by = this.by = hC - WL + 0.0006;
      const roll = Math.atan2(hR - hL, .234) * .26;
      const pitch = Math.atan2(hA - hF, .8) * .7 - thr * .020;
      const yaw = Math.sin(this.t * 0.33) * 0.05 * thr;
      const sway = Math.sin(this.t * 0.33) * 0.055 * thr;
      this.boat.position.set(bx, by, sway);
      this.boat.rotation.set(roll + yaw * 0.5, yaw, pitch);
      this.refl.position.set(bx, 2 * WL - by, sway);
      this.refl.rotation.set(-roll - yaw * 0.5, yaw, -pitch);

      this.bow.forEach(m => {
        m.material.opacity = 0.10 + thr * 0.6;
        m.scale.set(.6 + thr * .8, .7 + thr * .7, 1);
        m.position.x = bx - 0.30; m.position.y = WL + .003 + by * .5;
      });
      this.wakes.forEach(m => {
        m.material.opacity = 0.08 + thr * 0.62;
        m.scale.x = .5 + thr * 1.2;
        m.position.x = bx + 1.6; m.position.y = WL + .002 + by * .4;
      });
      this.wakeTex.offset.y = (this.wakeTex.offset.y - vel * .03) % 1;
      /* as duas camadas de ondulação correm a velocidades diferentes */
      this.nrm.offset.set(this.phase * 0.16, this.t * 0.020);
      this.nrm2.offset.set(-this.phase * 0.09, -this.t * 0.032);

      const P = this.sp, V = this.sv, LF = this.sl, jet = 0.7 + thr * 3.2;
      for (let i = 0; i < this.N; i++) {
        const j = i * 3;
        LF[i] -= dt * (1.1 + thr);
        if (LF[i] <= 0) {
          LF[i] = .22 + Math.random() * .30;
          /* salpicos no ponto onde o arco do jato encontra a água */
          const vx0 = 0.9 + thr * 2.6;
          const tImp = (0.10 + Math.sqrt(0.01 + 2 * 9.8 * 0.045)) / 9.8 * 4;
          P[j] = bx + .409 + vx0 * tImp * (0.85 + Math.random() * 0.3);
          P[j + 1] = WL + 0.001;
          P[j + 2] = ((i % 2) ? .117 : -.117) + (Math.random() - .5) * .05;
          V[j] = vx0 * (.25 + Math.random() * .3);
          V[j + 1] = .25 + Math.random() * .55;              // ressalto para cima
          V[j + 2] = (Math.random() - .5) * .35;
        }
        V[j + 1] -= 4.4 * dt;                 // cai depressa: são gotas pequenas
        P[j] += V[j] * dt; P[j + 1] += V[j + 1] * dt; P[j + 2] += V[j + 2] * dt;
        if (P[j + 1] < WL) { P[j + 1] = WL; V[j + 1] *= -.18; }
      }
      this.spray.geometry.attributes.position.needsUpdate = true;
      this.spray.material.opacity = 0.10 + thr * 0.62;
      this.spray.material.size = (LOWQ ? 0.014 : 0.017) * (0.55 + thr * 0.75);

      /* jatos: parábola desde o bocal, espessura e alcance com a potência */
      this.jets.forEach((jet, i) => {
        const side = (i ? -0.117 : 0.117) + sway;
        const vx = 0.9 + thr * 2.6;                 // velocidade de saída
        const vyj = 0.05 + thr * 0.10;
        this._bendJet(jet, bx + 0.409, WL + 0.004 + by, side, vx, vyj, thr);
        jet.mesh.material.opacity = thr < 0.03 ? 0 : 0.55 + thr * 0.32;
        jet.mesh.visible = thr > 0.02;
      });

      /* câmara: ângulo do capítulo      /* câmara: ângulo do capítulo + arrasto do utilizador, com inércia */
      /* inércia depois de largar; o ângulo fica onde o utilizador o deixou */
      this.userAz += this.velAz * dt; this.velAz *= 0.88;
      this.userEl += this.velEl * dt; this.velEl *= 0.88;
      this.userEl = Math.max(-40, Math.min(78, this.userEl));

      const dist = (L(a.dist, b.dist) + swoop) * (this.zoom || 1) + (1 - e) * 2.4;
      const azd = L(a.az, b.az) + this.userAz;
      const eld = Math.max(-16, Math.min(82, L(a.el, b.el) + this.userEl));
      const fov = L(a.fov, b.fov);
      if (Math.abs(this.camera.fov - fov) > .01) {
        this.camera.fov = fov; this.camera.updateProjectionMatrix();
      }
      const az = azd * Math.PI / 180, el = eld * Math.PI / 180;
      const shake = thr * 0.0035 * Math.sin(this.t * 9.1);
      this.camera.position.set(
        bx + dist * Math.cos(el) * Math.cos(az),
        WL + dist * Math.sin(el) + shake + Math.sin(this.t * .6) * .006,
        dist * Math.cos(el) * Math.sin(az));
      this.camera.lookAt(bx, WL + 0.06, sway);

      /* o céu acompanha o barco em posição e roda com a marcha: é a rotação
         do cenário que faz o movimento ler-se, não o deslocamento do barco */
      this.skyYaw = (this.skyYaw || 0) + vel * dt * 0.085;
      this.sky.forEach(s => {
        s.position.set(this.camera.position.x, 0, this.camera.position.z);
        s.rotation.y = SKY0 + this.skyYaw;
      });
      this.water.position.set(bx, 0, 0);
    }
    this.renderer.render(this.scene, this.camera);
  }
}
