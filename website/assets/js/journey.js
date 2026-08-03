/* SAILSAFE — viagem imersiva.

   Duas panorâmicas equirectangulares reais da Praia da Marinha entram como
   céu esférico. A câmara roda dentro delas, por isso o movimento lê-se: é o
   cenário que passa. O scroll avança nos capítulos, o arrasto olha à volta,
   e as fichas técnicas aparecem ancoradas às peças do modelo.            */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { assign } from './materials.js';

const WL = 0.0382;

const LOWQ = (() => { try {
  return matchMedia('(max-width:820px)').matches || matchMedia('(pointer:coarse)').matches;
} catch { return false; } })();
/* quem pediu menos movimento continua a ver a cena, mas sem agitação */
const CALM = (() => { try {
  return matchMedia('(prefers-reduced-motion: reduce)').matches;
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
    this.onFrame = null;   // gancho: os marcadores correm neste loop, não noutro
    this.active = true;    // desligado quando o palco sai do ecrã
    this._init();
  }

  _init() {
    const r = this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas, antialias: !LOWQ, alpha: true,
      powerPreference: 'high-performance'
    });
    r.setPixelRatio(Math.min(devicePixelRatio, LOWQ ? 1.25 : 2));
    r.toneMapping = THREE.ACESFilmicToneMapping;
    r.toneMappingExposure = 1.05;
    const sc = this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(36, 2, 0.02, 200);

    /* --- iluminação do ambiente ---
       O fundo do palco é um gradiente CSS, por isso não há céu esférico a
       desenhar. A panorâmica serve unicamente de fonte para o envmap: entra
       uma vez, gera o PMREM e é descartada. Antes carregavam-se aqui duas
       equirectangulares de 2,2 MB em esferas com visible=false — 4,4 MB
       transferidos, descodificados e enviados para a GPU sem nunca aparecer
       um único pixel deles no ecrã. */
    const ENV = (window.__SS_PANO__ && window.__SS_PANO__[0]) || 'assets/img/pano_env.jpg';
    new THREE.TextureLoader().load(ENV, tx => {
      tx.colorSpace = THREE.SRGBColorSpace;
      tx.mapping = THREE.EquirectangularReflectionMapping;
      this._applyEnv(tx);
      tx.dispose();
    });

    const sun = new THREE.DirectionalLight(0xfff2dc, 2.6);
    sun.position.set(2.0, 1.6, 0.8); sc.add(sun);
    sc.add(new THREE.HemisphereLight(0xd8ecfa, 0x4a6b70, 0.9));

    /* --- água local, fundida com o mar da panorâmica ---
       O plano tem 30 m mas a ondulação só existe dentro do disco onde
       fall > 0 (raio √30 ≈ 5,48 m) — cerca de 10 % dos vértices. Guardamos
       uma lista desses índices para o loop tocar apenas neles em vez de
       varrer os 12 321 vértices a cada frame. */
    const seg = LOWQ ? 64 : 110;
    const geo = new THREE.PlaneGeometry(30, 30, seg, seg);
    geo.rotateX(-Math.PI / 2);
    geo.attributes.position.setUsage(THREE.DynamicDrawUsage);
    geo.attributes.normal.setUsage(THREE.DynamicDrawUsage);
    this.wGeo = geo;
    this.wBase = Float32Array.from(geo.attributes.position.array);
    {
      const base = this.wBase, idx = [], fall = [];
      for (let i = 0; i < base.length; i += 3) {
        const f = 1 - (base[i] * base[i] + base[i + 2] * base[i + 2]) / 30;
        if (f > 0.01) { idx.push(i); fall.push(f); }
      }
      this.wIdx = Int32Array.from(idx);
      this.wFall = Float32Array.from(fall);
      /* fora do disco a superfície é plana: normal fixa a apontar para cima */
      const nrmA = geo.attributes.normal.array;
      for (let i = 0; i < nrmA.length; i += 3) { nrmA[i] = 0; nrmA[i + 1] = 1; nrmA[i + 2] = 0; }
      geo.attributes.normal.needsUpdate = true;
    }
    const am = document.createElement('canvas'); am.width = am.height = 256;
    const ax = am.getContext('2d');
    const rg = ax.createRadialGradient(128, 128, 8, 128, 128, 126);
    rg.addColorStop(0, '#fff'); rg.addColorStop(.30, '#fff');
    rg.addColorStop(.60, '#909090'); rg.addColorStop(.85, '#303030');
    rg.addColorStop(1, '#000');
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
    if (!LOWQ) {
      this.nrm2 = this.nrm.clone(); this.nrm2.needsUpdate = true;
      this.nrm2.wrapS = this.nrm2.wrapT = THREE.RepeatWrapping;
      this.nrm2.repeat.set(21, 21);
    }

    /* O clearcoat é dos shaders mais caros do three.js e a água ocupa o ecrã
       todo. Em ecrãs de toque cai para MeshStandardMaterial com uma só camada
       de ondulação: à escala a que a água se vê, a diferença não se nota. */
    const wOpts = {
      color: 0x4d9cb4, roughness: 0.13, metalness: 0.0,
      normalMap: this.nrm, normalScale: new THREE.Vector2(0.55, 0.55),
      alphaMap: new THREE.CanvasTexture(am), transparent: true,
      depthWrite: false, envMapIntensity: 2.1, side: THREE.DoubleSide
    };
    this.water = new THREE.Mesh(geo, LOWQ
      ? new THREE.MeshStandardMaterial(wOpts)
      : new THREE.MeshPhysicalMaterial(Object.assign({
          clearcoat: 0.9, clearcoatRoughness: 0.10, clearcoatNormalMap: this.nrm2
        }, wOpts)));
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

    /* Repuxo de waterjet como na referência: água BRANCA e AREJADA.
       Três camadas:
       1. coluna de espuma — corrente de sprites froth ao longo da parábola,
          densa à saída, a abrir e a desfazer-se;
       2. campo de lavagem — tapete de espuma turbulenta na água atrás da popa;
       3. salpicos — partículas que saltam da zona de impacto.               */

    /* textura de espuma: aglomerados brancos irregulares com buracos */
    const frothTex = (seed) => {
      const cv = document.createElement('canvas'); cv.width = cv.height = 128;
      const g = cv.getContext('2d');
      let rnd = seed;
      const R = () => (rnd = (rnd * 16807) % 2147483647) / 2147483647;
      for (let i = 0; i < 150; i++) {
        const x = R() * 128, y = R() * 128, r0 = 2 + R() * 9;
        const gr = g.createRadialGradient(x, y, 0.5, x, y, r0);
        gr.addColorStop(0, `rgba(255,255,255,${0.5 + R() * 0.5})`);
        gr.addColorStop(1, 'rgba(255,255,255,0)');
        g.fillStyle = gr; g.beginPath(); g.arc(x, y, r0, 0, 6.283); g.fill();
      }
      g.globalCompositeOperation = 'destination-out';
      for (let i = 0; i < 40; i++) {
        const x = R() * 128, y = R() * 128, r0 = 1 + R() * 4;
        g.fillStyle = `rgba(0,0,0,${0.3 + R() * 0.5})`;
        g.beginPath(); g.arc(x, y, r0, 0, 6.283); g.fill();
      }
      /* apagar as bordas para o sprite não ter recorte quadrado */
      const vg = g.createRadialGradient(64, 64, 34, 64, 64, 64);
      vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,1)');
      g.fillStyle = vg; g.fillRect(0, 0, 128, 128);
      return new THREE.CanvasTexture(cv);
    };
    const F1 = frothTex(1234), F2 = frothTex(9876);

    /* 1 — coluna de espuma: cadeia de sprites por bocal */
    const NCH = LOWQ ? 10 : 16;
    this.chain = [];
    [1, -1].forEach(side => {
      const arr = [];
      for (let i = 0; i < NCH; i++) {
        const m = new THREE.Mesh(
          new THREE.PlaneGeometry(1, 1),
          new THREE.MeshBasicMaterial({ map: (i % 2) ? F1 : F2,
            transparent: true, depthWrite: false, opacity: 0.9 }));
        m.frustumCulled = false;
        this.scene.add(m); arr.push(m);
      }
      this.chain.push({ side, arr, seed: side * 7.3 });
    });

    /* 2 — campo de lavagem: dois planos de espuma a rolar na água */
    const mkWash = (w, l, rep) => {
      const t1 = frothTex(rep * 31 + 7);
      t1.wrapS = t1.wrapT = THREE.RepeatWrapping;
      t1.repeat.set(rep, rep * 3);
      const m = new THREE.Mesh(
        new THREE.PlaneGeometry(w, l, 1, 8),
        new THREE.MeshBasicMaterial({ map: t1, transparent: true,
          depthWrite: false, opacity: 0.8 }));
      m.rotation.x = -Math.PI / 2;
      m.frustumCulled = false;
      this.scene.add(m);
      return { m, t: t1 };
    };
    this.wash  = mkWash(0.55, 2.6, 2);   // tapete principal atrás da popa
    this.wash2 = mkWash(0.80, 1.2, 3);   // fervura larga logo à saída

    /* esteiras lineares antigas fora — o campo de lavagem substitui-as */
    this.wakes.forEach(m => { m.visible = false; });

    this.N = LOWQ ? 90 : 260;
    this.sp = new Float32Array(this.N * 3);
    this.sv = new Float32Array(this.N * 3);
    this.sl = new Float32Array(this.N);
    for (let i = 0; i < this.N; i++) this.sl[i] = Math.random();
    const pg = new THREE.BufferGeometry();
    pg.setAttribute('position', new THREE.BufferAttribute(this.sp, 3));
    this.spray = new THREE.Points(pg, new THREE.PointsMaterial({
      map: rad('rgba(255,255,255,1)', 'rgba(255,255,255,.6)', 'rgba(255,255,255,0)'),
      size: 0.024, transparent: true, depthWrite: false, sizeAttenuation: true
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
    /* o listener de movimento só existe enquanto o dedo/rato está em baixo */
    this.canvas.addEventListener('pointerdown', e => {
      dn(e); addEventListener('pointermove', mv, { passive: true });
    });
    addEventListener('pointerup', e => { up(e); removeEventListener('pointermove', mv); });
    addEventListener('pointercancel', e => { up(e); removeEventListener('pointermove', mv); });

    this.zoom = 1;   // fixo: a roda fica livre para o scroll da página

    /* botão para repor o enquadramento, já que não volta sozinho */
    this.reset = () => {
      this.userAz = 0; this.userEl = 0;
      this.velAz = 0; this.velEl = 0;
    };

    addEventListener('resize', () => this._resize());
    if (window.ResizeObserver)
      new ResizeObserver(() => this._resize()).observe(this.canvas.parentElement);

    /* desligar quando o palco sai do ecrã; se não houver suporte, fica ligado */
    try {
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(es => {
          this.active = es[0].isIntersecting;
          if (!this.active) this._last = 0;
        }, { threshold: 0 }).observe(this.canvas);
      }
    } catch { /* sem observador: mantém-se sempre activo */ }
    addEventListener('visibilitychange', () => { this._last = 0; });

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

  /* Altura e declive da onda de uma só vez.
     A soma de senos tem derivada conhecida, por isso a normal sai da fórmula
     em vez de sair de computeVertexNormals(), que percorria os 24 200
     triângulos do plano a cada frame só para obter o mesmo resultado.
     Escreve em out = [h, dh/dx, dh/dz]. */
  _waveD(x, z, t, out) {
    const A = x * 2.6 + t * 1.8;
    const B = z * 4.0 - t * 1.4;
    const C = (x * 0.6 + z) * 6.2 + t * 2.6;
    const sA = Math.sin(A), sB = Math.sin(B), sC = Math.sin(C);
    out[0] = 0.0058 * sA + 0.0038 * sB + 0.0021 * sC;
    out[1] = 0.0058 * 2.6 * Math.cos(A) + 0.0021 * 3.72 * Math.cos(C);
    out[2] = 0.0038 * 4.0 * Math.cos(B) + 0.0021 * 6.2 * Math.cos(C);
    return out;
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
    const v = (this._pv || (this._pv = new THREE.Vector3()))
      .set(a[0] + this.bx, a[1] + this.by, a[2]);
    v.project(this.camera);
    if (v.z > 1) return null;
    /* dimensões vindas do _resize: chamar getBoundingClientRect() aqui era
       uma leitura de layout por marcador e por frame */
    return { x: (v.x * 0.5 + 0.5) * this._w, y: (-v.y * 0.5 + 0.5) * this._h };
  }

  _resize() {
    const p = this.canvas.parentElement;
    const w = p.clientWidth, h = p.clientHeight;
    if (!w || !h) return;
    this._w = w; this._h = h;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();

    /* O barco fica sempre ao centro do quadro — é ele o assunto. Em vez de o
       empurrar para o lado para dar lugar ao texto, a câmara afasta-se: o
       enquadramento continua centrado e o espaço aparece à volta do modelo. */
    this.estreito = Math.max(0, Math.min(1, (1.30 - w / h) / 0.80));
  }

  /* Afastamento da câmara para o capítulo a esta distância.

     20 % em todos os ecrãs, que é o ar que faltava à volta do modelo.
     Em ecrãs estreitos soma-se mais, e sobretudo nos grandes planos: o fov
     do three.js é o vertical, por isso um ecrã ao alto corta muito mais nos
     lados, e são os capítulos de perto que sofrem com isso. Um afastamento
     igual para todos resolveria o último capítulo à custa de encolher o
     plano de abertura, que não tem problema nenhum — daí o termo depender
     da distância do capítulo. */
  _distK(dist) {
    const e = this.estreito || 0;
    const perto = Math.max(0, Math.min(1, (2.0 - dist) / 1.5));
    return 1.20 * (1 + 0.125 * e) * (1 + 0.75 * e * perto);
  }

  _loop() {
    requestAnimationFrame(() => this._loop());
    /* Fora do ecrã ou com o separador escondido não há nada a mostrar: o
       loop existe, mas não desenha nem calcula. Era isto que mantinha dois
       contextos WebGL a 60 fps durante a leitura do resto da página. */
    if (!this.active || document.hidden) { this._last = 0; return; }

    /* Passo real em vez de 0,016 fixo. Com o passo fixo, um frame de 33 ms
       fazia a cena andar a meia velocidade — parte do arrastar que se via
       no telemóvel não era falta de fps, era a animação a atrasar-se. */
    const now = performance.now();
    const dt = this._last ? Math.min(0.05, (now - this._last) / 1000) : 0.016;
    this._last = now;
    this.t += dt;
    this.frame = (this.frame || 0) + 1;
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
    /* ao mudar de cenário a câmara afasta-se e volta, como um voo curto */
    const swoop = Math.sin(Math.min(1, Math.max(0, (this.ch + this.mix - 2.1))) * Math.PI) * 0.9;

    const e = 1 - Math.pow(1 - this.intro, 3);
    const thr = L(a.thr, b.thr) * (0.45 + 0.55 * e);
    const vel = thr * 2.0;
    this.phase += vel * dt;

    /* água: só os vértices dentro do disco da ondulação, com a normal vinda
       da derivada. Em ecrãs de toque a malha refaz-se a cada dois frames —
       a 60 Hz a diferença não se lê e poupa metade das transferências para
       a GPU. */
    if (!LOWQ || (this.frame & 1)) {
      const pos = this.wGeo.attributes.position, nrm = this.wGeo.attributes.normal;
      const arr = pos.array, nA = nrm.array, base = this.wBase;
      const idx = this.wIdx, fal = this.wFall, ph = this.phase, t = this.t;
      const d = this._d || (this._d = [0, 0, 0]);
      for (let k = 0; k < idx.length; k++) {
        const i = idx[k], f = fal[k];
        this._waveD(base[i] + ph, base[i + 2], t, d);
        arr[i + 1] = d[0] * f;
        /* regra do produto: o esbatimento radial também inclina a superfície */
        const gx = d[1] * f + d[0] * (-base[i] / 15);
        const gz = d[2] * f + d[0] * (-base[i + 2] / 15);
        const inv = 1 / Math.sqrt(gx * gx + gz * gz + 1);
        nA[i] = -gx * inv; nA[i + 1] = inv; nA[i + 2] = -gz * inv;
      }
      pos.needsUpdate = true; nrm.needsUpdate = true;
    }
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
      if (this.nrm2) this.nrm2.offset.set(-this.phase * 0.09, -this.t * 0.032);

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
      this.spray.material.opacity = 0.25 + thr * 0.70;
      this.spray.material.size = (LOWQ ? 0.020 : 0.024) * (0.6 + thr * 0.7);

      /* 1 — coluna de espuma ao longo da parábola de cada bocal */
      const vx0 = 0.9 + thr * 2.8;
      this.chain.forEach(ch => {
        const z0 = ch.side * 0.117 + sway;
        const n = ch.arr.length;
        for (let i = 0; i < n; i++) {
          const m = ch.arr[i];
          const tt = (i / (n - 1)) * 0.34;                    // tempo ao longo do arco
          const wob = Math.sin(this.t * 11 + i * 1.7 + ch.seed) * 0.006 * (i / n);
          const px = bx + 0.409 + vx0 * tt;
          const py = Math.max(WL - 0.002,
                     WL + 0.004 + by + (0.06 + thr * 0.12) * tt - 4.9 * tt * tt) + wob;
          m.position.set(px, py, z0 + wob * 1.6);
          m.quaternion.copy(this.camera.quaternion);          // billboard
          const grow = 0.05 + (i / n) * (0.16 + thr * 0.16);  // abre ao afastar-se
          m.scale.set(grow * (1.15 + thr), grow, 1);
          m.rotation.z += Math.sin(this.t * 5 + i) * 0.002;   // fervilhar
          m.material.opacity = thr < 0.03 ? 0
            : (0.92 - (i / n) * 0.55) * (0.35 + thr * 0.65);
          m.visible = thr > 0.02;
        }
      });

      /* 2 — campo de lavagem: branco, a correr para trás, a morrer à distância */
      const washOn = thr > 0.03;
      [this.wash, this.wash2].forEach((w, k) => {
        w.m.visible = washOn;
        if (!washOn) return;
        const L0 = k ? 0.6 + thr * 0.5 : 1.4 + thr * 1.8;
        w.m.scale.set(0.7 + thr * 0.6, L0, 1);
        w.m.position.set(bx + 0.42 + L0 * (k ? 0.25 : 0.48), WL + 0.0015 + by * 0.4, sway);
        w.t.offset.y = (w.t.offset.y - vel * (k ? 0.14 : 0.08)) % 1;
        w.t.offset.x = Math.sin(this.t * (k ? 2.1 : 1.3)) * 0.02;
        w.m.material.opacity = (k ? 0.55 : 0.42) * (0.25 + thr * 0.75);
      });

      /* câmara: ângulo do capítulo      /* câmara: ângulo do capítulo      /* câmara: ângulo do capítulo + arrasto do utilizador, com inércia */
      /* inércia depois de largar; o ângulo fica onde o utilizador o deixou */
      this.userAz += this.velAz * dt; this.velAz *= 0.88;
      this.userEl += this.velEl * dt; this.velEl *= 0.88;
      this.userEl = Math.max(-14, Math.min(30, this.userEl));

      const d0 = L(a.dist, b.dist);
      const dist = (d0 * this._distK(d0) + swoop) * (this.zoom || 1) + (1 - e) * 2.4;
      const azd = L(a.az, b.az) + this.userAz;
      const eld = Math.max(-8, Math.min(34, L(a.el, b.el) + this.userEl));
      const fov = L(a.fov, b.fov);
      if (Math.abs(this.camera.fov - fov) > .01) {
        this.camera.fov = fov; this.camera.updateProjectionMatrix();
      }
      const az = azd * Math.PI / 180, el = eld * Math.PI / 180;
      const shake = CALM ? 0 : thr * 0.0035 * Math.sin(this.t * 9.1);
      this.camera.position.set(
        bx + dist * Math.cos(el) * Math.cos(az),
        WL + dist * Math.sin(el) + shake + (CALM ? 0 : Math.sin(this.t * .6) * .006),
        dist * Math.cos(el) * Math.sin(az));
      /* a câmara aponta ao barco e ele fica ao centro do quadro */
      this.camera.lookAt(bx, WL + 0.06, sway);

      /* o céu acompanha o barco em posição e roda com a marcha: é a rotação
         do cenário que faz o movimento ler-se, não o deslocamento do barco */
      /* fundo em gradiente CSS: uniforme, sem paralaxe — nada a alinhar */

      this.water.position.set(bx, 0, 0);
    }
    this.renderer.render(this.scene, this.camera);
    if (this.onFrame) this.onFrame();
  }
}
