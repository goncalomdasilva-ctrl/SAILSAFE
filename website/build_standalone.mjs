/* Gera SAILSAFE.html — ficheiro único, sem servidor, sem CDN.
   Junta three.js, o código do site, o CSS e o modelo GLB (base64) num só HTML.
   Uso:  node build_standalone.mjs                                            */

import { build } from 'esbuild';
import fs from 'fs';
import path from 'path';

const here = path.dirname(new URL(import.meta.url).pathname);
const A = p => path.join(here, p);

/* 1. bundle de todo o JS num ficheiro clássico (sem módulos ES) */
const res = await build({
  entryPoints: [A('assets/js/app.js')],
  bundle: true,
  format: 'iife',
  minify: true,
  target: ['es2020'],
  write: false,
  legalComments: 'none',
  alias: {
    'three': A('assets/vendor/three/three.module.js'),
    'three/addons/controls/OrbitControls.js': A('assets/vendor/three/addons/controls/OrbitControls.js'),
    'three/addons/loaders/GLTFLoader.js': A('assets/vendor/three/addons/loaders/GLTFLoader.js'),
    'three/addons/utils/BufferGeometryUtils.js': A('assets/vendor/three/addons/utils/BufferGeometryUtils.js')
  }
});
const js = res.outputFiles[0].text;

/* 2. recursos — a fotografia entra no CSS como data URI, para o ficheiro
   único não depender de nada externo */
/* fundo é gradiente CSS; a panorâmica pequena alimenta só o envmap */
const css = fs.readFileSync(A('assets/css/style.css'), 'utf8');
const envPano = fs.readFileSync(A('assets/img/pano_env.jpg')).toString('base64');
const pano = [envPano, envPano];
const glb = fs.readFileSync(A('assets/sailsafe.glb')).toString('base64');

/* 3. HTML: remove importmap, folha externa e script de módulo.
   As substituições usam funções — uma string de substituição faria o
   JavaScript interpretar $&, $1, $' dentro do bundle minificado e corromper
   o resultado. Fechar a tag também tem de ser evitado dentro do script. */
const safe = s => s.replace(/<\/script/gi, '<\\/script');

/* Um único ficheiro para todos os ecrãs: o layout adapta-se por media
   query e o visualizador baixa a qualidade sozinho em ecrãs de toque. */
const html = fs.readFileSync(A('index.html'), 'utf8')
  .replace(/<!-- three\.js servido localmente[\s\S]*?<\/script>/, () => '')
  .replace(/<link rel="stylesheet"[^>]*>/, () => `<style>\n${css}\n</style>`)
  .replace(/<script type="module" src="assets\/js\/app\.js"><\/script>/, () =>
    `<script>window.__SAILSAFE_GLB__=${JSON.stringify(glb)};`
    + `window.__SS_PANO__=[${pano.map(p => JSON.stringify('data:image/jpeg;base64,' + p)).join(',')}];</script>\n`
    + `<script>\n${safe(js)}\n</script>`)
  .replace(/<meta property="og:image"[^>]*>\s*/, () => '');

fs.writeFileSync(A('SAILSAFE.html'), html);
console.log('SAILSAFE.html ->', (fs.statSync(A('SAILSAFE.html')).size / 1048576).toFixed(2), 'MB');
console.log('  js  ', (js.length / 1024).toFixed(0), 'kB · glb',
            (glb.length / 1024).toFixed(0), 'kB base64 · css', (css.length / 1024).toFixed(0), 'kB');
