# SAILSAFE — site do projeto

Site estático e bilingue (PT/EN) que apresenta o SAILSAFE, uma plataforma autónoma de superfície em catamarã, com um visualizador 3D interativo do modelo CAD.

Sem build, sem dependências de CDN, sem framework. Basta servir a pasta.

---

## Ver o site

### Sem instalar nada — `SAILSAFE.html`

Duplo clique em **`SAILSAFE.html`**. É um ficheiro único e autónomo, com o three.js,
o modelo 3D e todo o código embutidos. Funciona offline, sem servidor, sem CDN.

### Versão para publicar — `index.html`

Esta é a que vai para o GitHub Pages. Usa módulos ES e carrega o `.glb`
separadamente, por isso **tem de ser servida por HTTP** — o browser bloqueia
módulos em `file://`.

**Windows** — duplo clique em `serve.bat`. **macOS / Linux:**

```bash
python3 -m http.server 8000
```

Depois abre <http://localhost:8000>.

### Regenerar o ficheiro único

```bash
npm install esbuild
node build_standalone.mjs
```

---

## Publicar no GitHub Pages

1. Cria um repositório no GitHub e envia o conteúdo desta pasta para a raiz:

   ```bash
   git init
   git add .
   git commit -m "SAILSAFE project site"
   git branch -M main
   git remote add origin https://github.com/<utilizador>/<repositorio>.git
   git push -u origin main
   ```

2. No GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.

3. O workflow em `.github/workflows/deploy.yml` publica automaticamente a cada `push` para `main`.

O site fica em `https://<utilizador>.github.io/<repositorio>/`.

> O ficheiro `.nojekyll` está incluído para que o Jekyll não ignore pastas — não o apagues.

---

## Estrutura

```
.
├── SAILSAFE.html                 ficheiro único autónomo (duplo clique)
├── index.html                    versão modular, para GitHub Pages
├── build_standalone.mjs          gera o SAILSAFE.html
├── serve.bat                     servidor local para Windows
├── .nojekyll
├── .github/workflows/deploy.yml  publicação automática
└── assets/
    ├── sailsafe.glb              modelo 3D (41 peças · 6 960 triângulos · 408 kB)
    ├── css/style.css
    ├── js/
    │   ├── app.js                arranque, i18n, construção das secções
    │   ├── viewer.js             visualizador three.js
    │   ├── data.js               componentes, especificações, subsistemas
    │   └── i18n.js               textos PT / EN
    └── vendor/three/             three.js r169 (licença MIT incluída)
```

---

## O modelo 3D

`assets/sailsafe.glb` foi reconstruído a partir de `SAILSAFE_concept_v6_3.step` com as cotas exatas do ficheiro CAD. Face ao STEP original foram feitas cinco alterações, todas deliberadas:

1. **Cavidades reais abertas no casco** para os motores, veios, waterjets, ESCs e reforços de espelho de popa. No STEP estas peças estavam embebidas num bloco maciço sem booleana resolvida, o que impedia qualquer corte ou vista de secção.
2. **Arestas arredondadas com 4 mm** no casco e 1–3 mm nas restantes peças. Isto é mais fiel à construção real do que a aresta viva: as arestas e o fundo levam fita de fibra de vidro com epóxi, que não produz um canto vivo.
3. **Normais suavizadas por ângulo** (limite de 38°): as concordâncias ficam suaves e as arestas duras ficam nítidas. Sem isto o modelo lê-se como um bloco facetado.
4. **Coordenadas de textura** por projeção de caixa. O STEP não tinha nenhumas, e sem UVs não é possível aplicar materiais texturados.
5. **Materiais corrigidos.** O STEP declara todas as peças como aço a 7,85 g/cm³, o que é o valor por omissão do CAD e contradiz XPS, contraplacado e LiPo. Os materiais de render (gelcoat com clearcoat no casco, veio de madeira nas travessas, alumínio escovado nos motores, PCB nas placas) são gerados proceduralmente em `assets/js/materials.js`.

Nada mais foi alterado. Todas as posições, dimensões e relações entre peças são as do ficheiro original — verificadas peça a peça com tolerância de 0,05 mm.

Para regenerar o modelo a partir do STEP, ver `build_model.py` (requer `trimesh`, `manifold3d`, `scipy`, `numpy`).

---

## Funcionalidades do visualizador

- Órbita, zoom e enquadramento livre
- Ligar e desligar cada um dos cinco subsistemas
- Clicar em qualquer peça para ver descrição e especificações
- Cinco vistas predefinidas (isométrica, topo, lateral, proa, popa)
- Plano de água ao calado derivado para 6,2 kg
- Corte longitudinal pelo plano de simetria
- Vista explodida contínua
- Modo de cor por material ou por subsistema
- Iluminação de estúdio com envmap gerado em tempo de execução, sombras suaves e tone mapping ACES

---

## Nota sobre os dados

Cada valor apresentado no site está marcado com a sua origem:

| Marca | Significado |
|---|---|
| **Validado** | Medido ou confirmado em bancada |
| **Estimado** | Cálculo de arquitetura sobre datasheet, ainda sem medição |
| **Derivado** | Calculado a partir da geometria CAD |
| **Em aberto** | Decisão por tomar |

Os componentes de propulsão ainda não chegaram fisicamente ao projeto, pelo que nenhum número de desempenho é ainda uma medição em água. Esta separação é mantida deliberadamente.

---

## Créditos

Projeto pessoal de engenharia de **Gonçalo Martins da Silva**
Engenharia Eletrotécnica e de Computadores · Instituto Superior Técnico

Documentação de arquitetura v1.11 · modelo CAD v6.3

[three.js](https://threejs.org) r169 — licença MIT, incluída em `assets/vendor/three/LICENSE`.
