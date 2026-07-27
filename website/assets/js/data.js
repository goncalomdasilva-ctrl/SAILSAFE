/* SAILSAFE — base de dados de componentes e subsistemas
   Geometria: SAILSAFE_concept_v6_3.step
   Dados técnicos: SAILSAFE_Architecture_v1_11.docx
   status: 'validated' | 'estimated' | 'derived' | 'open'            */

export const SUBSYSTEMS = {
  structure:  { color: '#C99A5B', pt: 'Estrutura',   en: 'Structure' },
  power:      { color: '#E0483C', pt: 'Energia',     en: 'Power' },
  propulsion: { color: '#38BDF8', pt: 'Propulsão',   en: 'Propulsion' },
  compute:    { color: '#22C55E', pt: 'Computação',  en: 'Compute' },
  sensing:    { color: '#A855F7', pt: 'Perceção',    en: 'Sensing' }
};

const P = (pt, en) => ({ pt, en });

export const PARTS = {
  /* ---------------- ESTRUTURA ---------------- */
  casco_direito: {
    sub: 'structure', qty: 2,
    name: P('Casco de estibordo', 'Starboard hull'),
    desc: P('Núcleo em XPS de célula fechada com pele híbrida: contraplacado marítimo de 3 mm nas zonas planas (X 200–800) e laminação em fibra de vidro 200 g/m² + epóxi na proa em cunha (X 0–200). Arestas e fundo com fita de fibra e selagem epóxi.',
            'Closed-cell XPS core with a hybrid skin: 3 mm marine plywood over the flat prismatic region (X 200–800) and 200 g/m² fibreglass + epoxy lamination over the wedge bow (X 0–200). Edges and bottom taped with fibreglass and epoxy-sealed.'),
    specs: [P('800 × 116 × 146 mm', '800 × 116 × 146 mm'),
            P('Zona prismática: X 200–800 mm', 'Prismatic region: X 200–800 mm'),
            P('Semiângulo de entrada: 15,5°', 'Entry half-angle: 15.5°'),
            P('L/B = 6,90', 'L/B = 6.90')],
    status: 'validated'
  },
  casco_esquerdo: { alias: 'casco_direito', name: P('Casco de bombordo', 'Port hull') },

  travessa_T1: {
    sub: 'structure', qty: 3,
    name: P('Travessa estrutural', 'Structural crossbeam'),
    desc: P('Três travessas unem os cascos e recebem a caixa IP66 no vão T1–T2. Aparafusam às longarinas de convés embutidas, nunca à espuma.',
            'Three crossbeams tie the hulls together and carry the IP66 enclosure in the T1–T2 bay. They bolt into the recessed deck stringers, never into the foam.'),
    specs: [P('350 × 45 × 40 mm', '350 × 45 × 40 mm'),
            P('Centros em X = 222,5 / 485 / 663 mm', 'Centres at X = 222.5 / 485 / 663 mm'),
            P('Vão T1–T2: 217,5 mm', 'T1–T2 bay: 217.5 mm')],
    status: 'validated'
  },
  travessa_T2: { alias: 'travessa_T1' },
  travessa_T3: { alias: 'travessa_T1' },

  longarina_proa_dir: {
    sub: 'structure', qty: 4,
    name: P('Longarina de convés', 'Deck stringer'),
    desc: P('Longarina embutida em rasgo no convés de cada casco e colada no XPS. Serve de ponto de aparafusamento das travessas em madeira em vez de espuma.',
            'Stringer recessed into a groove in each hull deck and bonded into the XPS. Provides a timber bolting point for the crossbeams instead of foam.'),
    specs: [P('20 × 10 mm de secção', '20 × 10 mm section'),
            P('Proa X 200–245 · Ré X 430–800 mm', 'Fwd X 200–245 · Aft X 430–800 mm')],
    status: 'validated'
  },
  longarina_proa_esq: { alias: 'longarina_proa_dir' },
  longarina_re_dir:   { alias: 'longarina_proa_dir' },
  longarina_re_esq:   { alias: 'longarina_proa_dir' },

  escotilha_dir: {
    sub: 'structure', qty: 2,
    name: P('Escotilha de serviço', 'Service hatch'),
    desc: P('Acesso ao alojamento da bateria de propulsão. Reforço perimetral em segunda camada, 6 insertos roscados M4 de latão, parafusos de orelhas M4 em nylon e junta de neopreno de 3 mm colada à tampa. O compartimento não é hermético: dois entalhes de 2 mm no rebordo funcionam como respiro, por exigência de segurança LiPo.',
            'Access to the propulsion battery bay. Second-layer perimeter reinforcement, 6 brass M4 threaded inserts, M4 nylon wing bolts and a 3 mm neoprene gasket bonded to the lid. The compartment is deliberately not airtight: two 2 mm notches in the rim act as a vent, a LiPo safety requirement.'),
    specs: [P('185 × 85 mm · abertura útil 155 × 55 mm', '185 × 85 mm · 155 × 55 mm clear opening'),
            P('6 × insertos M4 em latão', '6 × M4 brass inserts'),
            P('Junta de neopreno 3 mm + respiro', '3 mm neoprene gasket + vent')],
    status: 'validated'
  },
  escotilha_esq: { alias: 'escotilha_dir' },

  transom_insert_dir: {
    sub: 'structure', qty: 2,
    name: P('Reforço de espelho de popa', 'Transom insert'),
    desc: P('Placa de contraplacado de 9–10 mm integrada na popa e laminada à estrutura, para que os parafusos do waterjet nunca apertem contra XPS. Os furos são selados com epóxi antes da montagem final.',
            'A 9–10 mm plywood plate built into the transom and laminated to the structure, so waterjet fasteners never clamp against XPS. Holes are epoxy-sealed before final assembly.'),
    specs: [P('110 × 140 mm · 9 mm', '110 × 140 mm · 9 mm')],
    status: 'validated'
  },
  transom_insert_esq: { alias: 'transom_insert_dir' },

  cobertura_ESC_dir: {
    sub: 'structure', qty: 2,
    name: P('Cobertura do ESC', 'ESC cover'),
    desc: P('Cobre o alojamento do ESC no convés, protegendo-o de salpicos e mantendo o acesso para manutenção e gestão térmica. Os ESCs não podem ser encapsulados permanentemente em XPS ou epóxi.',
            'Covers the ESC bay in the deck, shielding it from spray while keeping access for maintenance and thermal management. ESCs must never be permanently encapsulated in XPS or epoxy.'),
    specs: [P('95 × 50 × 29 mm', '95 × 50 × 29 mm')],
    status: 'validated'
  },
  cobertura_ESC_esq: { alias: 'cobertura_ESC_dir' },

  calco_IP66_1: {
    sub: 'structure', qty: 4,
    name: P('Calço de apoio da caixa', 'Enclosure shim'),
    desc: P('Quatro calços colados ao convés elevam a caixa IP66. A caixa é retida por duas ripas aparafusadas às faces de T1 e T2.',
            'Four shims bonded to the deck seat the IP66 enclosure, which is retained by two battens bolted to the faces of T1 and T2.'),
    specs: [P('24 × 20 × 6 mm', '24 × 20 × 6 mm')],
    status: 'validated'
  },
  calco_IP66_2: { alias: 'calco_IP66_1' },
  calco_IP66_3: { alias: 'calco_IP66_1' },
  calco_IP66_4: { alias: 'calco_IP66_1' },

  /* ---------------- COMPUTAÇÃO ---------------- */
  caixa_IP66: {
    sub: 'compute', qty: 1,
    name: P('Caixa de eletrónica IP66', 'IP66 electronics enclosure'),
    desc: P('Caixa comercial IP66 com tampa articulada, assente ao nível do convés. Todas as entradas de cabo passam por bucins PG7/PG9 — um furo sem bucim anula a classificação IP. Cada cabo forma um laço de gotejamento antes de entrar. A caixa não pode descer abaixo do convés: o túnel entre cascos tem 118 mm e a caixa tem 155 mm de largura.',
            'Commercial IP66 enclosure with a hinged lid, seated at deck level. Every cable entry goes through a PG7/PG9 gland — an unglanded hole voids the IP rating. Each cable forms a drip loop before entering. It cannot sit below deck: the tunnel between hulls is 118 mm and the enclosure is 155 mm wide.'),
    specs: [P('204 × 155 × 100 mm', '204 × 155 × 100 mm'),
            P('Fundo z = 152 · topo z = 252 mm', 'Base z = 152 · top z = 252 mm'),
            P('Bucins PG7 / PG9', 'PG7 / PG9 glands')],
    status: 'validated'
  },
  raspberry_pi_4: {
    sub: 'compute', qty: 1,
    name: P('Raspberry Pi 4 (2 GB)', 'Raspberry Pi 4 (2 GB)'),
    desc: P('Computador de bordo. Trata da navegação de alto nível, leitura de GPS, IMU e ADC, gestão de waypoints, logging e telemetria. Opera headless com acesso por SSH, hostname sailsafe-pi. É alimentado pelo conversor DC-DC através dos pinos GPIO 2 e 4 (5 V) e 6 e 14 (GND), com condensador de 470–1000 µF junto ao ponto de entrega.',
            'On-board computer. Handles high-level navigation, GPS, IMU and ADC reads, waypoint management, logging and telemetry. Runs headless over SSH, hostname sailsafe-pi. Powered from the DC-DC converter through GPIO pins 2 and 4 (5 V) and 6 and 14 (GND), with a 470–1000 µF capacitor at the delivery point.'),
    specs: [P('85 × 56 × 20 mm', '85 × 56 × 20 mm'),
            P('I2C + UART ativos', 'I2C + UART enabled'),
            P('USB-C reservado a diagnóstico', 'USB-C reserved for diagnostics')],
    status: 'validated'
  },
  esp32_devkit: {
    sub: 'compute', qty: 1,
    name: P('ESP32 DevKit', 'ESP32 DevKit'),
    desc: P('Controlador de tempo real dos motores. Recebe comandos do Raspberry Pi por USB-C, valida-os, gera o PWM para os dois ESCs e executa o watchdog. Esta separação impede que atrasos do sistema operativo do Raspberry Pi cheguem aos ESCs.',
            'Real-time motor controller. Receives commands from the Raspberry Pi over USB-C, validates them, generates PWM for both ESCs and runs the watchdog. This split keeps Raspberry Pi OS scheduling latency away from the ESCs.'),
    specs: [P('55 × 28 × 13 mm', '55 × 28 × 13 mm'),
            P('Failsafe medido: ≈1,1 s', 'Measured failsafe: ≈1.1 s'),
            P('Ponte CH341 → /dev/ttyUSB0', 'CH341 bridge → /dev/ttyUSB0')],
    status: 'validated'
  },
  ads1015: {
    sub: 'compute', qty: 1,
    name: P('ADS1015', 'ADS1015'),
    desc: P('ADC externo de 12 bits em I2C, para leituras analógicas de tensão e corrente de bateria e sensores adicionais.',
            'External 12-bit I2C ADC for analogue battery voltage and current reads and additional sensors.'),
    specs: [P('25 × 18 × 4 mm', '25 × 18 × 4 mm'),
            P('I2C, partilhado com o BNO055', 'I2C, shared with the BNO055')],
    status: 'validated'
  },

  /* ---------------- PERCEÇÃO ---------------- */
  gps_modulo: {
    sub: 'sensing', qty: 1,
    name: P('GPS NEO-8M', 'NEO-8M GPS'),
    desc: P('Módulo GPS completo com antena ativa, em UART dedicada. Fornece posição e velocidade para a navegação por waypoints. Sem fix válido, o sistema não inicia navegação autónoma.',
            'Complete GPS module with active antenna on a dedicated UART. Supplies position and speed for waypoint navigation. Without a valid fix the system will not start autonomous navigation.'),
    specs: [P('25 × 25 × 8 mm', '25 × 25 × 8 mm'),
            P('UART dedicada', 'Dedicated UART'),
            P('Ponto mais alto do veículo', 'Highest point on the vehicle')],
    status: 'validated'
  },
  suporte_GPS: {
    sub: 'sensing', qty: 1,
    name: P('Mastro do GPS', 'GPS mast'),
    desc: P('Eleva a antena do GPS 85 mm acima da base da caixa, procurando a melhor vista do céu e o maior afastamento possível dos cabos de potência.',
            'Raises the GPS antenna 85 mm above the enclosure floor, seeking the best sky view and the greatest possible separation from power cabling.'),
    specs: [P('15 × 14 × 85 mm', '15 × 14 × 85 mm')],
    status: 'validated'
  },
  bno055_imu: {
    sub: 'sensing', qty: 1,
    name: P('BNO055 IMU', 'BNO055 IMU'),
    desc: P('Unidade inercial em I2C. Fornece heading, inclinação e dados inerciais ao controlador de rumo. É a referência de orientação de todo o controlo de heading hold.',
            'I2C inertial measurement unit supplying heading, attitude and inertial data to the heading controller. It is the orientation reference for the whole heading-hold loop.'),
    specs: [P('20 × 27 × 5 mm', '20 × 27 × 5 mm'),
            P('I2C (SDA/SCL partilhados)', 'I2C (shared SDA/SCL)')],
    status: 'validated'
  },
  suporte_BNO055: {
    sub: 'sensing', qty: 1,
    name: P('Suporte da IMU', 'IMU standoff'),
    desc: P('Eleva e centra a IMU, afastando-a dos cabos de potência para reduzir interferência magnética.',
            'Raises and centres the IMU, keeping it away from power cabling to reduce magnetic interference.'),
    specs: [P('14 × 14 × 60 mm', '14 × 14 × 60 mm')],
    status: 'validated'
  },

  /* ---------------- ENERGIA ---------------- */
  bateria_5000_dir: {
    sub: 'power', qty: 2,
    name: P('LiPo 3S 5000 mAh — propulsão', 'LiPo 3S 5000 mAh — propulsion'),
    desc: P('Uma bateria de propulsão por casco, alojada abaixo do convés com forro interior em contraplacado de 3 mm selado a epóxi — o LiPo nunca contacta o XPS. Foi esta decisão que baixou o centro de gravidade de ≈142 para ≈107 mm. O carregamento é sempre feito fora do barco, em saco ou superfície ignífuga.',
            'One propulsion battery per hull, housed below deck in an epoxy-sealed 3 mm plywood liner — the LiPo never touches the XPS. This decision is what dropped the centre of gravity from ≈142 to ≈107 mm. Charging is always done outside the boat, in a fireproof bag or on a fireproof surface.'),
    specs: [P('155 × 48 × 35 mm · 11,1 V', '155 × 48 × 35 mm · 11.1 V'),
            P('Centro X = 341, y = ±123, fundo z = 45 mm', 'Centre X = 341, y = ±123, floor z = 45 mm'),
            P('Loop key XT90-S por casco', 'XT90-S loop key per hull'),
            P('Circuito de propulsão independente', 'Independent propulsion circuit')],
    status: 'validated'
  },
  bateria_5000_esq: { alias: 'bateria_5000_dir' },
  bateria_pi_2200: {
    sub: 'power', qty: 1,
    name: P('LiPo 2S 2200 mAh — eletrónica', 'LiPo 2S 2200 mAh — electronics'),
    desc: P('Bateria dedicada à eletrónica, através do conversor DC-DC de 5 V. Os positivos das duas redes permanecem separados e as baterias nunca são ligadas em paralelo; existe uma única ligação de referência, em estrela, entre o GND da eletrónica e o barramento negativo de potência.',
            'Dedicated electronics battery feeding the 5 V DC-DC converter. The two positive rails stay separate and the batteries are never paralleled; a single star reference bonds electronics ground to the power negative bus.'),
    specs: [P('35 × 105 × 25 mm · 7,4 V (2S)', '35 × 105 × 25 mm · 7.4 V (2S)'),
            P('Fusível 10 A + interruptor estanque', '10 A fuse + sealed switch')],
    status: 'validated'
  },
  conversor_DCDC_5V: {
    sub: 'power', qty: 1,
    name: P('Conversor DC-DC 5 V', '5 V DC-DC converter'),
    desc: P('Alimenta o Raspberry Pi, o ESP32 e os módulos compatíveis. É proibido alimentar o Raspberry Pi em simultâneo pela entrada USB-C e pelos pinos GPIO.',
            'Feeds the Raspberry Pi, the ESP32 and compatible modules. Powering the Raspberry Pi simultaneously through USB-C and the GPIO pins is prohibited.'),
    specs: [P('65 × 35 × 20 mm', '65 × 35 × 20 mm')],
    status: 'validated'
  },
  distribuidor_fusiveis: {
    sub: 'power', qty: 1,
    name: P('Distribuição e proteção', 'Distribution and protection'),
    desc: P('Distribuição e proteção. Na arquitetura de três circuitos independentes do esquema v1.11 não existe barramento comum nem fusível principal: cada casco tem o seu fusível de 40 A junto à própria bateria, e a eletrónica tem fusível de 10 A com interruptor estanque. Nenhum cabo de potência atravessa a ponte. Os Wagos e bornes ficam limitados a sinais e baixa corrente.',
            'Distribution and protection. In the three-independent-circuit architecture of schematic v1.11 there is no common bus bar and no main fuse: each hull carries its own 40 A fuse next to its own battery, and the electronics branch has a 10 A fuse with a sealed switch. No power cable crosses the bridge. Wagos and terminal blocks are limited to signals and low current.'),
    specs: [P('Fusível de 40 A por casco', '40 A fuse per hull'),
            P('Fusível da eletrónica 10 A', 'Electronics fuse 10 A'),
            P('Cabo 6 / 1,5 / 0,75 mm²', 'Cable 6 / 1.5 / 0.75 mm²')],
    status: 'validated'
  },
  sensor_corrente: {
    sub: 'power', qty: 1,
    name: P('Sensor de corrente', 'Current sensor'),
    desc: P('Medição elétrica através do ADS1015. Cada casco tem um divisor resistivo de 10 kΩ / 2,2 kΩ ligado a jusante da chave de corte, o que faz o sinal servir duas funções: mede a tensão da bateria e indica o estado do ramo — 0 V significa casco desarmado. É a peça que permitirá substituir por medição real as estimativas de consumo, autonomia e eficiência.',
            'Electrical measurement through the ADS1015. Each hull has a 10 kΩ / 2.2 kΩ divider tapped downstream of the cut-off key, so the signal does double duty: it reads battery voltage and reports branch state — 0 V means that hull is disarmed. This is the part that will let real measurements replace the current, endurance and efficiency estimates.'),
    specs: [P('31 × 13 × 15 mm', '31 × 13 × 15 mm'),
            P('Divisor 10 kΩ / 2,2 kΩ por casco', '10 kΩ / 2.2 kΩ divider per hull'),
            P('0 V = casco desarmado', '0 V = hull disarmed')],
    status: 'validated'
  },

  /* ---------------- PROPULSÃO ---------------- */
  motor_dir: {
    sub: 'propulsion', qty: 2,
    name: P('Motor brushless 2440 KV4500', '2440 KV4500 brushless motor'),
    desc: P('Motor brushless de 300 W, sem GND próprio — três fases U, V e W. Habitualmente usado em kits de waterjet para embarcações de 40 a 110 cm, o que coloca o SAILSAFE, com 80 cm, dentro da gama recomendada e na sua zona mais leve.',
            'A 300 W brushless motor with no ground of its own — three phases, U, V and W. Commonly used in waterjet kits for 40 to 110 cm craft, which puts SAILSAFE, at 80 cm, inside the recommended range and at its lighter end.'),
    specs: [P('Ø36 × 70 mm · 300 W', 'Ø36 × 70 mm · 300 W'),
            P('7,4–11,1 V (2S–3S)', '7.4–11.1 V (2S–3S)'),
            P('Eixo em y = ±117, z = 40 mm', 'Axis at y = ±117, z = 40 mm')],
    status: 'validated'
  },
  motor_esq: { alias: 'motor_dir' },
  esc_dir: {
    sub: 'propulsion', qty: 2,
    name: P('ESC brushless 40 A', '40 A brushless ESC'),
    desc: P('Um ESC por waterjet, instalado junto ao respetivo motor para manter curtos os três cabos de fase. A alimentação vem da distribuição central por dois cabos de 6 mm², acompanhados do sinal PWM e respetivo GND, em conduíte corrugado de 16 mm ao longo da travessa traseira.',
            'One ESC per waterjet, mounted next to its motor to keep the three phase leads short. Power is brought from central distribution by two 6 mm² cables, accompanied by the PWM signal and its ground, in 16 mm corrugated conduit along the aft crossbeam.'),
    specs: [P('80 × 40 × 30 mm · 40 A', '80 × 40 × 30 mm · 40 A'),
            P('Fusível de ramo 35–40 A', 'Branch fuse 35–40 A')],
    status: 'validated'
  },
  esc_esq: { alias: 'esc_dir' },
  waterjet_dir: {
    sub: 'propulsion', qty: 2,
    name: P('Unidade waterjet', 'Waterjet unit'),
    desc: P('Propulsão por jato de água, uma unidade por casco. A manobra combina empuxo diferencial entre os dois lados com um bocal orientável accionado por servo, comandado pelo ESP32 (sinais SRV_E e SRV_D do esquema elétrico). Não existe leme. A autoridade de guinada por diferencial vem do braço de 234 mm entre os dois eixos. O modelo final da unidade está por definir: a geometria aqui representada é um volume de referência, não o componente real, e o servo do bocal ainda não está modelado.',
            'Waterjet propulsion, one unit per hull. Steering combines differential thrust between the two sides with a servo-actuated steering nozzle driven by the ESP32 (signals SRV_E and SRV_D in the electrical schematic). There is no rudder. Differential yaw authority comes from the 234 mm arm between the two axes. The final unit is still to be selected: the geometry shown is a reference envelope, not the real component, and the nozzle servo is not yet modelled.'),
    specs: [P('Ø24 × 95 mm (volume de referência)', 'Ø24 × 95 mm (reference envelope)'),
            P('Ultrapassa o espelho em 15 mm', 'Extends 15 mm past the transom'),
            P('Bocal orientável por servo', 'Servo-actuated steering nozzle'),
            P('Modelo final por definir', 'Final unit to be selected')],
    status: 'open'
  },
  waterjet_esq: { alias: 'waterjet_dir' },
  veio_motor_dir: {
    sub: 'propulsion', qty: 2,
    name: P('Veio de transmissão', 'Drive shaft'),
    desc: P('Liga o motor à unidade de waterjet, atravessando o espelho de popa reforçado.',
            'Couples the motor to the waterjet unit through the reinforced transom.'),
    specs: [P('Ø5 × 20 mm', 'Ø5 × 20 mm')],
    status: 'validated'
  },
  veio_motor_esq: { alias: 'veio_motor_dir' }
};

/* Resolve aliases */
for (const [k, v] of Object.entries(PARTS)) {
  if (v.alias) PARTS[k] = { ...PARTS[v.alias], ...v };
}

/* ---------------- Especificações da plataforma ---------------- */
export const SPECS = [
  { g:'dim', k:P('Comprimento do casco','Hull length'), v:'800 mm', s:'validated' },
  { g:'dim', k:P('Comprimento máximo','Overall length'), v:'815 mm', s:'validated' },
  { g:'dim', k:P('Boca total','Overall beam'), v:'350 mm', s:'validated' },
  { g:'dim', k:P('Altura total','Overall height'), v:'252 mm', s:'validated' },
  { g:'dim', k:P('Altura de casco','Hull depth'), v:'146 mm', s:'validated' },
  { g:'dim', k:P('Boca de cada casco','Beam per hull'), v:'116 mm', s:'validated' },
  { g:'dim', k:P('Túnel entre cascos','Tunnel between hulls'), v:'118 mm', s:'validated' },
  { g:'dim', k:P('Distância entre eixos de propulsão','Propulsion axis spacing'), v:'234 mm', s:'validated' },
  { g:'dim', k:P('Relação L/B por casco','Hull L/B ratio'), v:'6,90', s:'validated' },

  { g:'mass', k:P('Massa estimada','Estimated mass'), v:'6,0–6,5 kg', s:'estimated' },
  { g:'mass', k:P('Meta de massa otimizada','Optimised mass target'), v:'≈5,0 kg', s:'estimated' },
  { g:'mass', k:P('Centro de gravidade (z)','Centre of gravity (z)'), v:'≈107 mm', s:'estimated' },
  { g:'mass', k:P('Área de flutuação','Waterplane area'), v:'0,1624 m²', s:'derived' },
  { g:'mass', k:P('Calado a 6,2 kg','Draft at 6.2 kg'), v:'≈38 mm', s:'derived' },
  { g:'mass', k:P('Bordo livre a 6,2 kg','Freeboard at 6.2 kg'), v:'≈108 mm', s:'derived' },

  { g:'prop', k:P('Configuração','Configuration'), v:'2 × waterjet', s:'validated' },
  { g:'prop', k:P('Motores','Motors'), v:'2 × 2440 KV4500 · 300 W', s:'validated' },
  { g:'prop', k:P('ESCs','ESCs'), v:'2 × 40 A', s:'validated' },
  { g:'prop', k:P('Manobra','Steering'), v:P('Diferencial + bocal por servo','Differential + servo nozzle'), s:'open' },
  { g:'prop', k:P('Potência combinada','Combined power'), v:'600 W', s:'validated' },
  { g:'prop', k:P('Rácio potência/peso','Power-to-weight'), v:'≈97 W/kg', s:'estimated' },
  { g:'prop', k:P('Impulso estático estimado','Estimated static thrust'), v:'2–3 kgf', s:'estimated' },
  { g:'prop', k:P('Velocidade estimada','Estimated speed'), v:'≈2 m/s', s:'estimated' },
  { g:'prop', k:P('Regime de navegação','Operating regime'), v:P('Deslocamento','Displacement'), s:'validated' },

  { g:'elec', k:P('Baterias de propulsão','Propulsion batteries'), v:'2 × LiPo 3S 5000 mAh', s:'validated' },
  { g:'elec', k:P('Bateria de eletrónica','Electronics battery'), v:'1 × LiPo 2S 2200 mAh', s:'validated' },
  { g:'elec', k:P('Arquitetura elétrica','Electrical architecture'), v:P('3 circuitos independentes','3 independent circuits'), s:'validated' },
  { g:'elec', k:P('Tensão de propulsão','Propulsion voltage'), v:'11,1 V (3S)', s:'validated' },
  { g:'elec', k:P('Tensão da eletrónica','Electronics voltage'), v:'7,4 V (2S)', s:'validated' },
  { g:'elec', k:P('Fusível por casco','Fuse per hull'), v:'40 A', s:'validated' },
  { g:'elec', k:P('Fusível da eletrónica','Electronics fuse'), v:'10 A', s:'validated' },
  { g:'elec', k:P('Corte de emergência','Emergency cut-off'), v:P('Loop key XT90-S por casco','XT90-S loop key per hull'), s:'validated' },
  { g:'elec', k:P('Potência a atravessar a ponte','Power crossing the bridge'), v:P('Nenhuma — só sinais','None — signals only'), s:'validated' },
  { g:'elec', k:P('Corrente máxima estimada','Estimated peak current'), v:'≈54 A', s:'estimated' },
  { g:'elec', k:P('Autonomia em cruzeiro (30 %)','Cruise endurance (30 %)'), v:'30–60 min', s:'estimated' },

  { g:'ctrl', k:P('Computador de bordo','On-board computer'), v:'Raspberry Pi 4 (2 GB)', s:'validated' },
  { g:'ctrl', k:P('Controlador de tempo real','Real-time controller'), v:'ESP32 DevKit', s:'validated' },
  { g:'ctrl', k:P('Ligação Pi ↔ ESP32','Pi ↔ ESP32 link'), v:'USB-C serial', s:'validated' },
  { g:'ctrl', k:P('Saídas do ESP32','ESP32 outputs'), v:P('2 × PWM + 2 × servo','2 × PWM + 2 × servo'), s:'validated' },
  { g:'ctrl', k:P('Protocolo de comando','Command protocol'), v:'L:&lt;%&gt; R:&lt;%&gt;', s:'validated' },
  { g:'ctrl', k:P('Heartbeat','Heartbeat'), v:'5 Hz (200 ms)', s:'validated' },
  { g:'ctrl', k:P('Timeout de failsafe','Failsafe timeout'), v:'≈1,1 s', s:'validated' },
  { g:'ctrl', k:P('Teto de potência em ensaio','Test power ceiling'), v:'30 %', s:'validated' },
  { g:'ctrl', k:P('GPS','GPS'), v:'NEO-8M', s:'validated' },
  { g:'ctrl', k:P('IMU','IMU'), v:'BNO055', s:'validated' },
  { g:'ctrl', k:P('ADC','ADC'), v:'ADS1015 (12-bit)', s:'validated' }
];

export const SPEC_GROUPS = {
  dim:  P('Dimensões e geometria','Dimensions and geometry'),
  mass: P('Massa e hidrostática','Mass and hydrostatics'),
  prop: P('Propulsão','Propulsion'),
  elec: P('Energia e distribuição','Power and distribution'),
  ctrl: P('Controlo e perceção','Control and sensing')
};
