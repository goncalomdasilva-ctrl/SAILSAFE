# Ferramentas do modelo de conceito (STEP)

Scripts que geram e verificam o modelo de implantação. O corrente é
`SAILSAFE_concept_v6_4.step`; o `v6_3` mantém-se porque é a geometria de que foi
feito o `sailsafe.glb` do site publicado.
O modelo **de referência** continua a ser o Fusion 360 (`.f3d`); isto é um modelo de
**layout**, para decidir onde vai cada componente, verificar folgas e estimar o CG.

As versões anteriores à v6_2 estão em `../archive/` (ver o README de lá). **O
`SAILSAFE_concept_v6_2.step` não é uma versão velha**: é o `SRC` por omissão dos
dois scripts de build e não pode ser arquivado nem apagado.

Sistema de coordenadas (mm): X proa→popa, Y bombordo(−)/estibordo(+), Z quilha→cima.
Casco 800 × 350, convés a z = 146, interior útil da caixa IP66
X 254,5..453,5 · Y ±75 · Z 154,5..252.

## Scripts

| ficheiro | o que faz | dependências |
|---|---|---|
| `build_concept_v6_3.py` | lê o v6_2 e escreve o v6_3 com os componentes internos | nenhuma (Python 3) |
| `build_concept_v6_4.py` | lê o v6_2 e escreve o v6_4 (componentes detalhados, jatos vetorizados) | nenhuma (Python 3) |
| `verify_concept.py` | integridade referencial, bounding boxes, colisões, folgas, CG | nenhuma |
| `validate_occ.py` | valida cada sólido com `BRepCheck_Analyzer` e dá volumes | `cadquery-ocp` |
| `make_layout_svg.py` | desenho de implantação (vista de cima + lateral) em SVG | `cadquery-ocp` |

```bash
cd hardware/mechanical
python3 tools/build_concept_v6_4.py SAILSAFE_concept_v6_2.step SAILSAFE_concept_v6_4.step
python3 tools/verify_concept.py SAILSAFE_concept_v6_4.step
python3 tools/validate_occ.py SAILSAFE_concept_v6_4.step          # opcional
python3 tools/make_layout_svg.py SAILSAFE_concept_v6_4.step SAILSAFE_layout_v6_4.svg
```

## Como o build funciona

Não há kernel CAD garantido no ambiente, por isso o script **não gera B-rep de raiz**.
Clona a topologia de dois sólidos já válidos do próprio ficheiro — `calco_IP66_1`
(caixa: 6 faces planas) e `waterjet_dir` (cilindro: 2 tampas + lateral) — e aplica-lhes
uma transformação afim por eixo (translação + escala), incluindo o reescalonamento
correto das *pcurves* e dos raios. Como toda a geometria dos moldes está alinhada aos
eixos, a transformação preserva a validade do sólido. Depois acrescenta os cabeçalhos
de produto, as relações de montagem e as cores.

Consequência prática: só se conseguem criar **caixas alinhadas aos eixos** e **cilindros
de eixo X**. Chega para um modelo de implantação; qualquer geometria a sério faz-se no
Fusion.

## Aviso

Os componentes são **envelopes**, não modelos de fabricante: dimensões típicas com folga,
sem conectores, sem furação, sem cablagem. Servem para decidir arranjo e verificar que
tudo cabe — não para desenhar suportes definitivos.
