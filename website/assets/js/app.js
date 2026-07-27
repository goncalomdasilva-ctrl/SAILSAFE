/* SAILSAFE — aplicação */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Viewer } from './viewer.js';
import { Journey, CH, ANCHOR } from './journey.js';
import { assign, studioEnvironment } from './materials.js';
import { t } from './i18n.js';
import { PARTS, SUBSYSTEMS, SPECS, SPEC_GROUPS } from './data.js';

/* localStorage lança em origens opacas (ficheiro aberto por file://) e quando
   as cookies de terceiros estão bloqueadas. Nunca pode derrubar a página. */
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* sem persistência */ } }
};

let lang = store.get('ss-lang') || ((navigator.language || 'pt').slice(0, 2).toLowerCase());
if (lang !== 'en') lang = 'pt';

const L  = o => (o && typeof o === 'object' && 'pt' in o) ? o[lang] : o;
const $  = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];

/* O modelo pode vir embutido (versão de ficheiro único) ou de assets/. */
const MODEL = (() => {
  const b64 = window.__SAILSAFE_GLB__;
  if (!b64) return 'assets/sailsafe.glb';
  const bin = atob(b64), buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
})();

/* ---------------- i18n ---------------- */
function applyLang() {
  document.documentElement.lang = lang;
  $$('[data-i18n]').forEach(el => el.textContent = t(el.dataset.i18n, lang));
  $$('[data-i18n-svg]').forEach(el => el.textContent = t(el.dataset.i18nSvg, lang));
  $$('.lang button').forEach(b => b.classList.toggle('on', b.dataset.lang === lang));
  buildSubCards(); buildSpecs(); buildSafety(); buildSoftware(); buildToggles();
  if (viewer?.selected) showInfo(viewer.selected);
  journey?._relabel?.();
  store.set('ss-lang', lang);
}
$$('.lang button').forEach(b => b.onclick = () => { lang = b.dataset.lang; applyLang(); });

$('#burger').onclick = () => $('#nav').classList.toggle('open');
$$('#nav a').forEach(a => a.onclick = () => $('#nav').classList.remove('open'));

const badge = s => `<span class="badge b-${s}">${t('st.' + s, lang)}</span>`;

function buildSubCards() {
  $('#subCards').innerHTML = Object.entries(SUBSYSTEMS).map(([k, v]) => `
    <div class="card" style="--c:${v.color}">
      <h3><span class="dot"></span>${t('s.' + k + '.t', lang)}</h3>
      <p>${t('s.' + k + '.b', lang)}</p>
    </div>`).join('');
}

let specTab = 'dim';
function buildSpecs() {
  $('#specTabs').innerHTML = Object.entries(SPEC_GROUPS).map(([k, v]) =>
    `<button data-g="${k}" class="${k === specTab ? 'on' : ''}">${L(v)}</button>`).join('');
  $$('#specTabs button').forEach(b => b.onclick = () => { specTab = b.dataset.g; buildSpecs(); });
  $('#specBody').innerHTML = SPECS.filter(s => s.g === specTab).map(s =>
    `<tr><td>${L(s.k)}</td><td>${L(s.v)}</td><td>${badge(s.s)}</td></tr>`).join('');
}
const buildSafety   = () => $('#safetyGrid').innerHTML = [1,2,3,4,5,6].map(i =>
  `<div class="mini"><h4>${t('sf.'+i+'.t', lang)}</h4><p>${t('sf.'+i+'.b', lang)}</p></div>`).join('');
const buildSoftware = () => $('#swGrid').innerHTML = [1,2,3,4,5,6].map(i =>
  `<div class="mini"><h4>${t('sw.'+i+'.t', lang)}</h4><p>${t('sw.'+i+'.b', lang)}</p></div>`).join('');

/* ---------------- visualizador ----------------
   Criado só depois de confirmar WebGL. Se falhar, o resto da página
   continua a funcionar — nenhuma falha do 3D pode esvaziar o site.     */
let viewer = null;

function buildToggles() {
  $('#subToggles').innerHTML = Object.entries(SUBSYSTEMS).map(([k, v]) => `
    <label class="chk" style="color:${v.color}">
      <input type="checkbox" data-sub="${k}">
      <span class="box"></span><span class="dot" style="background:${v.color}"></span>
      <span class="lbl">${v[lang]}</span>
    </label>`).join('');
  $$('#subToggles input').forEach(i => {
    i.checked = viewer ? viewer.visible.has(i.dataset.sub) : true;
    i.onchange = () => viewer?.toggleSubsystem(i.dataset.sub, i.checked);
  });
}

function showInfo(name) {
  const box = $('#vInfo'), p = name && PARTS[name];
  if (!p) return box.classList.remove('on');
  const sub = SUBSYSTEMS[p.sub];
  $('#iName').textContent = L(p.name);
  $('#iSub').textContent  = sub[lang] + (p.qty > 1 ? ` · ${p.qty}×` : '');
  $('#iSub').style.color  = sub.color;
  $('#iDesc').textContent = L(p.desc);
  $('#iSpecs').innerHTML  = (p.specs || []).map(s => `<li>${L(s)}</li>`).join('');
  $('#iBadge').innerHTML  = badge(p.status);
  box.classList.add('on');
}
$('#infoClose').onclick = () => viewer?.select(null);

$$('#viewBtns button').forEach(b => b.onclick = () => {
  $$('#viewBtns button').forEach(x => x.classList.remove('on'));
  b.classList.add('on'); viewer?.setView(b.dataset.view);
});
const toggle = (el, fn) => el.onclick = () => { el.classList.toggle('on'); fn(el.classList.contains('on')); };
toggle($('#btnXray'),    v => viewer?.setXray(v));
toggle($('#btnWater'),   v => viewer?.setWaterline(v));
toggle($('#btnSection'), v => viewer?.setSection(v));
toggle($('#btnColor'),   v => viewer?.setColorMode(v));
toggle($('#btnRotate'),  v => viewer?.setAutoRotate(v));
$('#explode').oninput = e => viewer?.setExplode(e.target.value / 100);
$('#btnReset').onclick = () => {
  viewer?.reset(); $('#explode').value = 0;
  ['#btnXray','#btnWater','#btnSection','#btnColor','#btnRotate'].forEach(s => $(s).classList.remove('on'));
  viewer?.setXray(false); viewer?.setWaterline(false); viewer?.setSection(false);
  viewer?.setColorMode(false); viewer?.setAutoRotate(false);
  $$('#viewBtns button').forEach((x, i) => x.classList.toggle('on', i === 0));
  $$('#subToggles input').forEach(i => { i.checked = true; viewer?.toggleSubsystem(i.dataset.sub, true); });
};

/* ---------------- viagem ---------------- */
let journey = null;

function startJourney() {
  const cv = $('#jCanvas');
  if (!cv) return;
  journey = new Journey(cv);
  journey.load(MODEL instanceof ArrayBuffer ? MODEL.slice(0) : MODEL)
         .catch(e => console.error('journey', e));

  /* marcadores: um por âncora, posicionados a cada frame sobre a peça */
  const host = $('#spots');
  host.innerHTML = Object.keys(ANCHOR).map(k =>
    `<button class="spot" data-k="${k}"><i></i><b></b></button>`).join('');
  const spots = {};
  $$('.spot').forEach(el => {
    spots[el.dataset.k] = el;
    el.onclick = () => showSpot(el.dataset.k);
  });

  function labels() {
    Object.entries(spots).forEach(([k, el]) => {
      const p = PARTS[k];
      if (p) el.querySelector('b').textContent = L(p.name);
    });
  }
  labels();
  journey._relabel = labels;

  const card = $('#spotCard');
  function showSpot(k) {
    const p = PARTS[k];
    if (!p) return;
    const sub = SUBSYSTEMS[p.sub];
    $('#sName').textContent = L(p.name);
    $('#sSub').textContent  = sub[lang] + (p.qty > 1 ? ` · ${p.qty}×` : '');
    $('#sSub').style.color  = sub.color;
    $('#sDesc').textContent = L(p.desc);
    $('#sSpecs').innerHTML  = (p.specs || []).map(s => `<li>${L(s)}</li>`).join('');
    $('#sBadge').innerHTML  = badge(p.status);
    card.classList.add('on');
    Object.entries(spots).forEach(([kk, el]) => el.classList.toggle('sel', kk === k));
  }
  $('#spotClose').onclick = () => {
    card.classList.remove('on');
    $$('.spot').forEach(el => el.classList.remove('sel'));
  };

  /* reposicionar os marcadores em cada frame */
  (function tick() {
    requestAnimationFrame(tick);
    if (!journey.ready) return;
    const act = new Set(CH[journey.ch].spots.concat(
      journey.mix > 0.4 ? CH[Math.min(CH.length - 1, journey.ch + 1)].spots : []));
    Object.entries(spots).forEach(([k, el]) => {
      if (!act.has(k)) { el.classList.remove('on'); return; }
      const pt = journey.project(k);
      if (!pt) { el.classList.remove('on'); return; }
      el.style.transform = `translate(${pt.x}px,${pt.y}px)`;
      el.classList.add('on');
    });
  })();

  const rb = $('#jReset');
  if (rb) rb.onclick = () => journey.reset();

  /* scroll: avança nos capítulos */
  const dots = $('#stageDots');
  dots.innerHTML = CH.map((_, i) => `<i class="${i ? '' : 'on'}"></i>`).join('');
  const beats = $$('.beat');
  const stage = $('.stage');
  let cur = -1;
  const onScroll = () => {
    const r = stage.getBoundingClientRect();
    const total = stage.offsetHeight - innerHeight;
    const p = Math.max(0, Math.min(1, -r.top / Math.max(1, total)));
    const q = Math.max(0, (p - 0.08) / 0.92) * (CH.length - 1);
    journey.setProgress(q);
    const idx = Math.min(CH.length - 1, Math.round(q));
    if (idx !== cur) {
      cur = idx;
      beats.forEach((b, i) => b.classList.toggle('on', i === idx));
      $$('#stageDots i').forEach((d, i) => d.classList.toggle('on', i === idx));
      card.classList.remove('on');
      $$('.spot').forEach(el => el.classList.remove('sel'));
    }
    const hint = $('.dragHint');
    if (hint) hint.style.opacity = p > 0.03 && p < 0.9 ? 1 : 0;
  };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

/* ---------------- arranque ---------------- */
applyLang();                       // o conteúdo textual nunca depende do 3D

const hasWebGL = (() => {
  try { return !!document.createElement('canvas').getContext('webgl2'); }
  catch (e) { return false; }
})();

if (!hasWebGL) {
  $('#vLoad').textContent = lang === 'en'
    ? 'This browser has no WebGL 2 — the 3D viewer cannot run.'
    : 'Este browser não tem WebGL 2 — o visualizador 3D não pode arrancar.';
} else {
  try {
    viewer = new Viewer($('#viewCanvas'), showInfo);
    buildToggles();
    viewer.load(MODEL instanceof ArrayBuffer ? MODEL.slice(0) : MODEL)
      .then(() => { $('#vLoad').classList.add('gone'); buildToggles(); })
      .catch(err => { $('#vLoad').textContent = 'Erro: ' + err.message; console.error(err); });
    startJourney();
  } catch (err) {
    $('#vLoad').textContent = 'Erro: ' + err.message;
    console.error(err);
  }
}

/* Animação de entrada — puramente decorativa. Só é activada se o browser a
   suportar, para que nenhum elemento possa ficar invisível por falha do JS. */
try {
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    }), { threshold: 0.06 });
    $$('section .wrap > *').forEach((el, i) => {
      el.classList.add('rise');
      el.style.transitionDelay = (i % 4) * 55 + 'ms';
      io.observe(el);
    });
    /* rede de segurança: se algo correr mal, revela tudo passado 2 s */
    setTimeout(() => $$('.rise:not(.in)').forEach(el => el.classList.add('in')), 2000);
  }
} catch (e) { $$('.rise').forEach(el => el.classList.add('in')); }
