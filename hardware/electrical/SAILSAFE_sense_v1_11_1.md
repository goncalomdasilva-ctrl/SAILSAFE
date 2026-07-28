# Sense de tensão e corrente — especificação

Aplica-se ao circuito da caixa IP66 (U4 = ADS1015) do esquema elétrico v1.11.

## Revisões

| rev | data | alterações |
|---|---|---|
| 1 | 2026-07-25 | Versão inicial. Detetada a saturação do ADS1015 com o divisor 10k/2k2. |
| 2 | 2026-07-28 | Divisores passam a 5k/1k (resistores disponíveis). Canais reatribuídos: entra a tensão da bateria da eletrónica, sai a corrente do casco direito. Condensador de filtro passa a 2,2 µF. Bateria da eletrónica confirmada 3S 2200 mAh. |

---

## 1. O problema original

Os divisores de sense estavam especificados a 10k/2k2, com rácio 0,180328. Uma LiPo 3S carregada
(12,6 V) dá **2,272 V** à entrada do ADS1015, acima do FSR por omissão de **±2,048 V**. O limite de
saturação referido à bateria era 11,36 V — ou seja, **toda a zona útil de descarga lia saturado** e a
bateria pareceria cheia até já ir a meio da descarga.

Não é uma avaria que se manifeste: o circuito está eletricamente são e a leitura é sempre plausível.
Só está errada.

## 2. Divisor adotado — 5k / 1k

Aproveitam-se resistores já disponíveis. Nenhuma compra necessária.

| | valor |
|---|---|
| Resistor superior (ao positivo) | 5 kΩ |
| Resistor inferior (à massa) | 1 kΩ |
| Rácio k | 0,16667 |
| PGA / FSR | **±4,096 V** (GAIN_ONE) — **não** o default de ±2,048 V |
| Fundo de escala referido à bateria | 24,6 V |
| Resolução | 12,00 mV (4,00 mV por célula numa 3S) |
| Impedância de fonte | 833 Ω |
| Corrente permanente | 2,10 mA a 12,6 V |

Tabela de conversão (3S):

| V bateria | V no ADC |
|---:|---:|
| 12,60 (cheia) | 2,100 |
| 11,10 (nominal) | 1,850 |
|  9,90 (vazia) | 1,650 |

### ⚠ A correção do PGA continua a ser obrigatória

Com 5k/1k o limite de saturação no FSR por omissão sobe para **12,29 V** — que ainda é **inferior a uma
3S carregada (12,6 V)**. Trocar o divisor não resolve o problema sozinho.

**O PGA tem de ser configurado para ±4,096 V (GAIN_ONE) no código.** Sem isso, o topo da carga continua
a ler saturado.

Margem para 4S: 16,8 V dá 2,800 V, dentro do FSR e bem abaixo do máximo absoluto de entrada
(VDD + 0,3 = 5,3 V). Uma futura passagem a 4S não obriga a mexer em hardware.

## 3. O erro dominante são os resistores, não o ADC

| Tolerância | Erro de rácio | Erro a 12,6 V |
|---|---|---|
| 1 % | 1,7 % | ±0,21 V |
| 5 % | 8,6 % | ±1,09 V |

A resolução do conversor (12 mV) é uma a duas ordens de grandeza melhor do que o erro dos resistores.
Gastar em resistores de precisão vale mais do que gastar em bits.

**Calibração de um ponto por canal é obrigatória**, seja qual for a tolerância: medir a tensão real com
multímetro, comparar com a leitura, guardar um fator de escala por canal em ficheiro de configuração.
Elimina praticamente todo o erro de ganho e permite usar resistores de 5 % com confiança.

## 4. Filtragem

Condensador em paralelo com o resistor inferior de cada divisor (SENSE→GND do respetivo circuito).

Com a impedância de fonte de **833 Ω** (era 1,80 kΩ na revisão 1):

| C | fc |
|---|---|
| 1,0 µF | 191 Hz |
| **2,2 µF** | **87 Hz** ← recomendado |

A tensão de bateria é um sinal lento; o corte a 87 Hz rejeita o ruído de comutação do ESC, que é a
fonte de ruído dominante a bordo.

## 5. Atribuição dos quatro canais

O ADS1015 tem quatro entradas. Um divisor custa cêntimos; um sensor de corrente custa euros. **O recurso
escasso é o canal, não o componente** — por isso gastam-se três canais em tensões e um em corrente.

| canal | sinal | sensor |
|---|---|---|
| A0 | Tensão do casco esquerdo | divisor 5k/1k |
| A1 | Tensão do casco direito | divisor 5k/1k |
| A2 | **Tensão da bateria da eletrónica (3S 2200)** | divisor 5k/1k |
| A3 | Corrente do casco esquerdo | ACS758-050U |

### Porque entra a bateria da eletrónica

As baterias esgotam-se em relógios diferentes: a da eletrónica consome-se com o **tempo decorrido**,
independentemente de o barco andar; as de propulsão só enquanto há impulso. Em qualquer utilização com
paragens, deriva ou navegação lenta, **a bateria da eletrónica esgota-se primeiro** (≈2,7 h a 7,2 W).

É também a falha mais grave: ao esgotar-se perdem-se rádio, registo e controlo em simultâneo, e o barco
fica à deriva sem posição conhecida. O esgotamento da propulsão deixa o barco parado mas localizável.

Este canal não é um mostrador — é o **gatilho de regresso**. Abaixo de um limiar, a missão é abortada.

### Porque sai a corrente do casco direito

Instrumentar um só casco introduz um erro aceitável no modelo de energia. Desequilíbrio entre cascos
medido em simulação:

| missão | desequilíbrio |
|---|---|
| linha reta | 0,0 % |
| ziguezague (viragens alternadas) | −1,6 % |
| missão de demonstração (1 viragem) | +8,9 % |
| quadrado (4 viragens do mesmo lado) | +13,6 % |

Medir um casco e duplicar dá um erro de cerca de **7 %** no total — abaixo da incerteza atual da
potência dos motores, que ainda não é conhecida.

**Limitação aceite:** um jato obstruído no casco não instrumentado não é detetado diretamente. Mitigação
parcial: a queda de tensão sob carga funciona como indicador indireto, calibrando no casco instrumentado
a relação entre queda e corrente e aplicando-a ao outro pela tensão.

### Sensor de corrente

ACS758-050U (Hall, isolado, unidirecional 0–50 A, 60 mV/A, offset 0,6 V).

| Corrente | Saída |
|---:|---:|
| 0 A | 0,600 V |
| 20 A | 1,800 V |
| 40 A | 3,000 V |

Cabe no mesmo FSR de ±4,096 V, com resolução de 33 mA por conta.

Ligação: o sensor fica no casco, em série com o positivo **a jusante da loop key e do relé** (mantém a
propriedade "0 V / 0 A = casco desarmado"). Atravessam a ponte apenas +5 V, GND_ELEC e a saída analógica
— sinais e alimentação de baixa corrente, pelo que a regra de nenhum cabo de potência atravessar a ponte
se mantém.

## 6. Limitações conhecidas

- **Não sobra canal para monitorizar o próprio rail de 5 V.** A saída do ACS758 é ratiométrica à sua
  alimentação enquanto o ADS1015 mede contra referência interna, portanto oscilações do 5 V desviam a
  leitura de corrente. Compensação exigiria um segundo ADS1015 (endereço alternativo pelo pino ADDR).
- **Casco direito sem medição de corrente** até haver segundo ADS1015 (OPEN-012).
- Se os servos dos bocais ficarem no rail de 5 V, os seus picos de corrente contaminam também a leitura.
- **O esquema elétrico v1.11 indica 2S 2200 mAh para a eletrónica; a bateria real é 3S 2200 mAh.**
  Correção pendente no KiCad.

## 7. Alterações a fazer no KiCad

1. Divisores a 5 kΩ / 1 kΩ, com **tolerância anotada** no campo do componente.
2. **Três** divisores: SENSE_E, SENSE_D e SENSE_ELEC (novo).
3. Condensadores de **2,2 µF** em paralelo com o resistor inferior de cada divisor.
4. A3 do U4 ligado a ISENSE_E (ACS758). Casco direito sem corrente, documentado como reserva.
5. Corrigir o circuito da caixa IP66 para **LiPo 3S 2200 mAh**.
6. Nota junto de U4:
   `ADS1015 PGA = +-4.096 V (GAIN_ONE). Com o default de +-2.048 V a leitura satura acima de 12.3 V.`

## 8. Verificação quando houver hardware

- Varrer 9→13 V com fonte de bancada e confirmar que a leitura acompanha linearmente e **não satura**.
- Calibrar o fator de escala de cada um dos três canais de tensão contra multímetro.
- Medir o consumo real da eletrónica para fixar o limiar de regresso com margem de segurança.
- Só depois disto confiar em qualquer estimativa de estado de carga ou de autonomia.
