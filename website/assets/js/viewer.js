/* SAILSAFE — visualizador 3D */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader }    from 'three/addons/loaders/GLTFLoader.js';
import { PARTS, SUBSYSTEMS } from './data.js';
import { assign, studioEnvironment, waterNormals } from './materials.js';

const WATERLINE = 0.0382;          // calado derivado para 6,2 kg

/* Peças que fecham o veículo e escondem tudo o que está dentro.
   O modo "ver interior" torna-as translúcidas. */
const SHELL = /^casco|^caixa_IP66|^escotilha|^cobertura_ESC/;

/* Qualidade reduzida em ecrãs pequenos ou sem rato: sombras e pixel ratio
   altos custam bateria e fluidez no telemóvel. Detetado no arranque; pode
   ser forçado com window.__SS_MOBILE__ = true/false. */
const LOWQ = (() => {
  if (typeof window.__SS_MOBILE__ !== 'undefined') return !!window.__SS_MOBILE__;
  try {
    return matchMedia('(max-width: 820px)').matches ||
           matchMedia('(pointer: coarse)').matches;
  } catch { return false; }
})();

export class Viewer {
  constructor(canvas, onSelect) {
    this.canvas = canvas;
    this.onSelect = onSelect;
    this.parts = new Map();
    this.visible = new Set(Object.keys(SUBSYSTEMS));
    this.colorBySub = false;
    this.xray = false;
    this.selected = null;
    this.hovered = null;
    this.ready = false;
    this._init();
  }

  _init() {
    const r = this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas, antialias: true, alpha: true,
      powerPreference: 'high-performance'
    });
    r.setPixelRatio(Math.min(devicePixelRatio, LOWQ ? 1.5 : 2));
    r.shadowMap.enabled = !LOWQ;
    r.shadowMap.type = THREE.PCFSoftShadowMap;
    r.toneMapping = THREE.ACESFilmicToneMapping;
    r.toneMappingExposure = 1.0;
    r.localClippingEnabled = true;

    const sc = this.scene = new THREE.Scene();
    this.env = studioEnvironment(r);
    sc.environment = this.env;

    this.camera = new THREE.PerspectiveCamera(36, 1, 0.02, 60);
    this.camera.position.set(0.92, 0.58, 0.92);

    const c = this.controls = new OrbitControls(this.camera, this.canvas);
    c.enableDamping = true; c.dampingFactor = 0.075;
    c.minDistance = 0.3; c.maxDistance = 4;
    c.maxPolarAngle = Math.PI * 0.54;
    c.target.set(0, 0.085, 0);
    c.autoRotateSpeed = 0.8;

    /* ---- luz ---- */
    const key = new THREE.DirectionalLight(0xfff6ec, 2.4);
    key.position.set(0.85, 1.45, 0.65);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    const s = 0.7, sh = key.shadow.camera;
    sh.left = -s; sh.right = s; sh.top = s; sh.bottom = -s; sh.near = 0.1; sh.far = 6;
    key.shadow.bias = -0.0006; key.shadow.normalBias = 0.004;
    key.shadow.radius = 3;
    sc.add(key);

    const fill = new THREE.DirectionalLight(0xd6e8ff, 0.9);
    fill.position.set(-1.1, 0.55, -0.85); sc.add(fill);
    const rim = new THREE.DirectionalLight(0xffffff, 1.5);
    rim.position.set(-0.6, 0.35, -1.3); sc.add(rim);

    /* ---- chão de estúdio com sombra suave ---- */
    const g = new THREE.Mesh(
      new THREE.CircleGeometry(2.2, 64),
      new THREE.MeshStandardMaterial({ color: 0x2a3138, roughness: 0.62, metalness: 0.05 })
    );
    g.rotation.x = -Math.PI / 2; g.position.y = -0.0015; g.receiveShadow = true;
    this.ground = g; sc.add(g);

    /* ---- plano de água ---- */
    const wn = waterNormals();
    this.waterNormalMap = wn;
    const wl = new THREE.Mesh(
      new THREE.CircleGeometry(2.2, 64),
      new THREE.MeshPhysicalMaterial({
        color: 0x2a6f96, roughness: 0.08, metalness: 0.0,
        transmission: 0.55, thickness: 0.25, ior: 1.33,
        normalMap: wn, normalScale: new THREE.Vector2(0.22, 0.22),
        transparent: true, opacity: 0.94, side: THREE.DoubleSide, depthWrite: false
      })
    );
    wl.rotation.x = -Math.PI / 2; wl.position.y = WATERLINE; wl.visible = false;
    this.waterline = wl; sc.add(wl);

    this.clipPlane = new THREE.Plane(new THREE.Vector3(0, 0, -1), 0.001);

    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();
    this.canvas.addEventListener('pointerdown', e => this._down = { x: e.clientX, y: e.clientY });
    this.canvas.addEventListener('pointerup', e => {
      if (this._down && Math.hypot(e.clientX - this._down.x, e.clientY - this._down.y) < 5) this._pick(e);
      this._down = null;
    });
    this.canvas.addEventListener('pointermove', e => this._hover(e));
    this.canvas.addEventListener('pointerleave', () => this._setHover(null));

    addEventListener('resize', () => this._resize());
    if (window.ResizeObserver) new ResizeObserver(() => this._resize()).observe(this.canvas.parentElement);
    this._resize();
    this._loop();
  }

  async load(url) {
    const loader = new GLTFLoader();
    const gltf = url instanceof ArrayBuffer
      ? await new Promise((res, rej) => loader.parse(url, '', res, rej))
      : await loader.loadAsync(url);

    const root = gltf.scene;
    const meshes = [];
    root.traverse(o => { if (o.isMesh) meshes.push(o); });

    const group = this.group = new THREE.Group();
    meshes.forEach(o => o.updateWorldMatrix(true, false));
    meshes.forEach(o => {
      const raw  = (o.name || '').replace(/_\d+$/, '');
      const name = raw.split('__')[0];
      const meta = PARTS[name];
      o.castShadow = true; o.receiveShadow = true;
      o.userData.part = name;
      o.userData.sub = meta ? meta.sub : 'structure';
      const src = o.material.color ? o.material.color.getHex() : 0x999999;
      const m = assign(o, name, src);
      o.matrix.copy(o.matrixWorld);
      o.matrix.decompose(o.position, o.quaternion, o.scale);
      group.add(o);
      this.parts.set(raw, {
        mesh: o, mat: m,
        base: name, shell: SHELL.test(name),
        baseColor: m.color.clone(),
        baseMap: m.map || null,
        subColor: new THREE.Color(SUBSYSTEMS[o.userData.sub].color)
      });
    });

    const bb = new THREE.Box3().setFromObject(group);
    const centre = bb.getCenter(new THREE.Vector3());
    this.parts.forEach(p => {
      const b = new THREE.Box3().setFromObject(p.mesh);
      p.home = p.mesh.position.clone();
      p.dir = b.getCenter(new THREE.Vector3()).sub(centre);
      p.dir.y = p.dir.y * 1.6 + 0.02;
    });

    this.scene.add(group);
    this.ready = true;
    this._applyColors();
    this.setView('iso', false);
    return true;
  }

  /* ---------------- seleção ---------------- */
  _cast(e) {
    const r = this.canvas.getBoundingClientRect();
    this.pointer.set(((e.clientX - r.left) / r.width) * 2 - 1,
                     -((e.clientY - r.top) / r.height) * 2 + 1);
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const tg = [];
    this.parts.forEach(p => { if (p.mesh.visible) tg.push(p.mesh); });
    return this.raycaster.intersectObjects(tg, false)[0] || null;
  }
  _pick(e) { if (this.ready) this.select(this._cast(e)?.object.userData.part || null); }
  _hover(e) {
    if (!this.ready) return;
    const h = this._cast(e);
    this.canvas.style.cursor = h ? 'pointer' : 'grab';
    this._setHover(h ? h.object.userData.part : null);
  }
  _setHover(n) { if (this.hovered !== n) { this.hovered = n; this._applyColors(); } }

  select(name) {
    this.selected = name;
    this._applyColors();
    this.onSelect?.(name);
  }

  _applyColors() {
    this.parts.forEach((p, key) => {
      const name = p.base;
      const m = p.mat;
      const sel = this.selected === name;
      const dim = this.selected && !sel;
      const ghost = this.xray && p.shell && !sel;
      if (this.colorBySub) { m.color.copy(p.subColor); m.map = null; }
      else { m.color.copy(p.baseColor); m.map = p.baseMap; }
      const op = dim ? 0.12 : (ghost ? 0.17 : 1);
      m.transparent = op < 1;
      m.opacity = op;
      m.depthWrite = op >= 1;
      m.side = (op < 1 && p.shell) ? THREE.DoubleSide : THREE.FrontSide;
      if (m.emissive) {
        m.emissive.setHex(sel ? 0x2b6fa0 : (this.hovered === name && !dim ? 0x14304a : 0x000000));
      }
      m.needsUpdate = true;
    });
  }

  /* ---------------- controlos ---------------- */
  toggleSubsystem(sub, on) {
    on ? this.visible.add(sub) : this.visible.delete(sub);
    this.parts.forEach(p => { p.mesh.visible = this.visible.has(p.mesh.userData.sub); });
    if (this.selected && !this.visible.has(PARTS[this.selected]?.sub)) this.select(null);
  }
  setExplode(v) {
    this.explode = v;
    this.parts.forEach(p => p.mesh.position.copy(p.home).addScaledVector(p.dir, v * 1.6));
  }
  setWaterline(on) { this.waterline.visible = on; this.ground.visible = !on; }
  setSection(on) {
    this.parts.forEach(p => {
      p.mat.clippingPlanes = on ? [this.clipPlane] : [];
      p.mat.side = on ? THREE.DoubleSide : THREE.FrontSide;
      p.mat.needsUpdate = true;
    });
  }
  setColorMode(v) { this.colorBySub = v; this._applyColors(); }
  setAutoRotate(v) { this.controls.autoRotate = v; }
  /* torna cascos, caixa, escotilhas e coberturas translúcidos, revelando
     as baterias nos cascos, os motores, os ESCs e a eletrónica */
  setXray(v) { this.xray = v; this._applyColors(); }

  setView(v, animate = true) {
    const d = { iso:[0.92,0.58,0.92], top:[0.01,1.35,0.02], side:[0.01,0.16,1.32],
                bow:[-1.30,0.26,0.01], stern:[1.30,0.28,0.01] }[v] || [0.92,0.58,0.92];
    const to = new THREE.Vector3(...d);
    const tgt = new THREE.Vector3(0, v === 'top' ? 0.06 : 0.085, 0);
    if (!animate) { this.camera.position.copy(to); this.controls.target.copy(tgt); return; }
    this._anim = { from: this.camera.position.clone(), to, ft: this.controls.target.clone(), tt: tgt, t: 0 };
  }
  reset() { this.select(null); this.setExplode(0); this.setView('iso'); }

  _resize() {
    const p = this.canvas.parentElement;
    const w = p.clientWidth, h = p.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  _loop() {
    requestAnimationFrame(() => this._loop());
    if (this._anim) {
      const a = this._anim;
      a.t = Math.min(1, a.t + 0.05);
      const k = 1 - Math.pow(1 - a.t, 3);
      this.camera.position.lerpVectors(a.from, a.to, k);
      this.controls.target.lerpVectors(a.ft, a.tt, k);
      if (a.t >= 1) this._anim = null;
    }
    if (this.waterline.visible) {
      const t = performance.now() * 0.00004;
      this.waterNormalMap.offset.set(t, t * 0.6);
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}

export { WATERLINE };
