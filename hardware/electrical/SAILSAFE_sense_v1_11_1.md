# Sense de tensão e corrente — correção v1.11.1

Aplica-se a `SAILSAFE_electrical_v1_11` (U4 = ADS1015, R1..R4 = divisores de sense).
Data: 2026-07-26.

## 1. Problema encontrado

Os divisores de sense são R=10k / 2k2, logo o rácio é:

```
k = 2200 / (10000 + 2200) = 0.180328
```

Com uma LiPo 3S carregada (12.6 V) isso dá **2.272 V** à entrada do ADS1015.

O ADS1015 arranca com FSR (full-scale range) por omissão de **±2.048 V**. O limite de
saturação referido à bateria é:

```
2.048 / 0.180328 = 11.36 V
```

**Toda a zona útil da bateria satura.** Uma 3S vai de 12.6 V (cheia) a ~9.9 V (vazia, 3.3 V/célula);
tudo acima de 11.36 V lê o mesmo valor máximo. Na prática a bateria parece estar sempre cheia
até já ir a meio da descarga — exatamente o oposto do que o sense serve para fazer.

## 2. Correção adotada: manter o divisor, mudar o PGA

Não é preciso mexer em hardware. Basta configurar o PGA do ADS1015 para **±4.096 V** (GAIN_ONE).

| | valor |
|---|---|
| Divisor | 10k / 2k2 (**inalterado**) |
| PGA / FSR | **±4.096 V** (não o default de ±2.048 V) |
| Fundo de escala referido à bateria | 22.71 V |
| LSB do ADC | 2.00 mV |
| Resolução na bateria | 11.09 mV (3.70 mV por célula) |

Tabela de conversão (3S):

| V bateria | V no ADC | contas @FSR ±4.096 |
|---:|---:|---:|
| 12.60 (cheia) | 2.2721 | 1136 |
| 12.00 | 2.1639 | 1082 |
| 11.40 | 2.0557 | 1028 |
| 11.10 (nominal) | 2.0016 | 1001 |
| 10.50 | 1.8934 | 947 |
|  9.90 (vazia) | 1.7852 | 893 |

### Porque não apertar o divisor

A alternativa seria 10k/1k5 (k=0.1304) com FSR ±2.048 V, que daria melhor resolução (7.7 mV/conta).
Rejeitada porque:

- 11 mV de resolução já é ~19x melhor do que o erro dominante (tolerância dos resistores, ver §3),
  logo a resolução extra não se traduz em precisão real;
- obriga a mexer no BOM;
- perde a margem para 4S. Com 10k/2k2, uma 4S carregada (16.8 V) dá 3.03 V — dentro do FSR de
  4.096 V e bem abaixo do máximo absoluto de entrada (VDD+0.3 = 5.3 V). Se um dia subires para 4S,
  **não é preciso tocar no hardware**.

## 3. O que domina o erro: os resistores, não o ADC

Erro de rácio no pior caso, por tolerância:

| Tolerância | Erro de rácio | Erro a 12.6 V |
|---|---|---|
| 1 % | 1.65 % | ±0.21 V |
| 5 % | 8.47 % | ±1.07 V |

Consequências:

- **Especificar 1 % metal film.** Com 5 % o erro (±1.07 V) é maior que um terço da janela útil
  de descarga — o sense fica inútil para estimar estado de carga.
- Mesmo a 1 %, o erro (±0.21 V) é ~19x pior que a resolução do ADC (11 mV). O ADC não é o
  limitante; os resistores é que são.
- **Fazer calibração de um ponto em software:** medir a tensão real com multímetro, comparar com a
  leitura, guardar um fator de escala por canal em ficheiro de configuração. Isto elimina quase todo
  o erro de ganho e é a diferença entre ±0.21 V e ~±0.02 V.

## 4. Filtragem

Acrescentar um condensador em paralelo com o resistor inferior de cada divisor
(SENSE_E→GND_E e SENSE_D→GND_D). Impedância de fonte do divisor = 10k‖2k2 = **1.80 kΩ**.

| C | fc |
|---|---|
| 100 nF | 883 Hz |
| 470 nF | 188 Hz |
| **1 µF** | **88 Hz** |

**Recomendado: 1 µF.** A tensão da bateria é um sinal lento e o corte a 88 Hz rejeita bem o ruído
de comutação do ESC, que é a fonte de ruído dominante neste barco. Os 1.8 kΩ de impedância de fonte
são suficientemente baixos para não carregar a entrada do ADS1015.

## 5. Reservar A2/A3 para corrente

O sense atual só mede **tensão**. O ponto 5 da roadmap (previsão de autonomia) precisa de energia,
que é V×I×t — sem corrente não há modelo de autonomia possível, só extrapolação de tensão.

O ADS1015 tem 4 canais; a atribuição fica exatamente preenchida:

| Canal | Sinal |
|---|---|
| A0 | SENSE_E (tensão casco esquerdo) — existente |
| A1 | SENSE_D (tensão casco direito) — existente |
| **A2** | **ISENSE_E (corrente casco esquerdo)** — a reservar |
| **A3** | **ISENSE_D (corrente casco direito)** — a reservar |

Sensor sugerido: **ACS758LCB-050U** (Hall, isolado, unidirecional 0–50 A, 60 mV/A, offset 0.6 V).

| Corrente | Saída |
|---:|---:|
| 0 A | 0.600 V |
| 20 A | 1.800 V |
| 40 A | 3.000 V |
| 50 A | 3.600 V |

Cabe no mesmo FSR de ±4.096 V, com resolução de **33 mA por conta**. O ADS1015 permite escrever o
PGA a cada conversão (modo single-shot), portanto os quatro canais podem partilhar o mesmo FSR.

Notas de ligação:

- O sensor é Hall, **isolado** — fica no casco, em série com o positivo **a jusante da chave XT90-S**
  (mantém a propriedade "0 V / 0 A = casco desarmado").
- Atravessam a ponte apenas +5 V, GND_ELEC e a saída analógica: são sinais e alimentação de baixa
  corrente, portanto **a regra de nenhum cabo de potência atravessar a ponte mantém-se**.
- **Ratiometria:** a saída do ACS758 é proporcional à sua própria alimentação, enquanto o ADS1015
  mede contra referência interna. Se o rail de 5 V oscilar, a leitura de corrente desvia
  proporcionalmente. Com os 4 canais ocupados não sobra entrada para monitorizar o próprio 5 V —
  se quiseres compensação ratiométrica, é preciso um segundo ADS1015 (endereço I2C alternativo
  pelo pino ADDR). Alternativa mais simples: DC-DC estável e aceitar o erro residual.
- Isto liga-se ao pendente já assinalado no esquema (servos no rail de 5 V): se os servos ficarem
  no mesmo rail, os picos de corrente deles passam a contaminar também a leitura de corrente.

## 6. Alterações a fazer no KiCad

1. **R1..R4:** manter 10k/2k2, mas anotar **tolerância 1 %** no campo do componente.
2. **Acrescentar C_SE e C_SD:** 1 µF de SENSE_E→GND_E e de SENSE_D→GND_D.
3. **Acrescentar os nós ISENSE_E / ISENSE_D** em A2/A3 do U4 (com os ACS758 ou, para já,
   documentados como reserva — não deixar como no-connect anónimo).
4. **Nota no esquema, junto de U4:**
   `ADS1015 PGA = +-4.096 V (GAIN_ONE). Com o default de +-2.048 V a leitura satura acima de 11.4 V de bateria.`

## 7. Verificação a fazer quando houver hardware

- Alimentar o divisor com fonte de bancada, varrer 9→13 V e confirmar que a leitura acompanha
  linearmente e **não satura** a 11.4 V.
- Calibrar o fator de escala por canal contra multímetro e guardar em configuração.
- Só depois disto confiar em qualquer estimativa de estado de carga.
