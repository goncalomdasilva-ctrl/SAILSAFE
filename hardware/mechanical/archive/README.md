# Arquivo de modelos CAD

Versões que já não são fonte de nada nem entram em nenhuma cadeia de geração.
Ficam no repositório por historial: mostram como a implantação evoluiu, e
serviram de referência em decisões registadas no `Engineering_log.md`.

**Nada aqui deve ser usado como ponto de partida para trabalho novo.**
O modelo corrente é `../SAILSAFE_concept_v6_4.step`.

| Ficheiro | Porque foi arquivado |
|---|---|
| `SAILSAFE_concept_v1.step` | primeiro esboço, geometria abandonada |
| `SAILSAFE_concept_v2.step` | idem, substituído pelas variantes v2_* |
| `SAILSAFE_concept_v2_fixed.step` | correção de topologia da v2 |
| `SAILSAFE_concept_v2_advbrep.step` | tentativa de exportação BREP avançada |
| `SAILSAFE_concept_v2_coloured_cut.step` | corte colorido, só para visualização |
| `SAILSAFE_concept_v2_wood.step` | variante em madeira da v2 |
| `SAILSAFE_concept_v3_wood.step` | variante em madeira da v3 |
| `SAILSAFE_concept_v4.step` | último bom antes da série v6 |
| `SAILSAFE_concept_v6_1.step` | esboço por caixas, pior que a v4 (ver log 07-23) |
| `SAILSAFE_v3_preview.svg` | pré-visualização da v3 |

## O que NÃO está aqui, e porquê

Três ficheiros que pareciam versões velhas mas não são, e por isso ficaram
na pasta acima:

- **`SAILSAFE_concept_v6_2.step`** — é a **fonte** dos scripts de geração.
  Tanto `tools/build_concept_v6_3.py` como `tools/build_concept_v6_4.py`
  têm a v6_2 como `SRC` por omissão. Arquivá-la partia a reconstrução do
  modelo corrente.
- **`SAILSAFE_concept_v6_3.step`** — é a geometria de que foi feito o
  `website/assets/sailsafe.glb` publicado no GitHub Pages, conforme
  `website/README.md` e `website/assets/js/data.js`. Enquanto o site
  publicado vier daí, a proveniência tem de continuar à mão.
- **`hull.step`** — casco base exportado do Fusion 360 (17 MB), origem de
  toda a série.
