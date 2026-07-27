/* SAILSAFE — textos bilingues PT / EN */

export const T = {
  /* ---------- navegação ---------- */
  'nav.model':    ['Modelo 3D', '3D model'],
  'nav.arch':     ['Arquitetura', 'Architecture'],
  'nav.sub':      ['Subsistemas', 'Subsystems'],
  'nav.specs':    ['Especificações', 'Specifications'],
  'nav.safety':   ['Segurança', 'Safety'],
  'nav.software': ['Software', 'Software'],
  'nav.status':   ['Estado', 'Status'],

  /* ---------- hero ---------- */
  'hero.kicker':  ['Plataforma autónoma de superfície', 'Autonomous surface platform'],
  'hero.title':   ['SAILSAFE', 'SAILSAFE'],
  'hero.sub': [
    'Um catamarã elétrico de 800 mm, com propulsão diferencial por dois waterjets independentes e uma arquitetura de controlo distribuída em dois níveis. Projeto pessoal de engenharia — eletrónica de potência, sistemas embebidos, navegação autónoma e integração de sistemas.',
    'An 800 mm electric catamaran with differential thrust from two independent waterjets and a two-tier distributed control architecture. A personal engineering project spanning power electronics, embedded systems, autonomous navigation and systems integration.'
  ],
  'hero.scroll':  ['Explorar', 'Explore'],
  'j.reset':      ['Repor vista', 'Reset view'],
  'j.drag':       ['Arrasta para olhar à volta · desliza a página para avançar', 'Drag to look around · scroll the page to move on'],
  'b4.k': ['04 — Interior', '04 — Inside'],
  'b4.t': ['Dentro da caixa', 'Inside the enclosure'],
  'b4.b': [
    'Raspberry Pi e ESP32 lado a lado dentro de uma caixa IP66 ao nível do convés, com o GPS no topo do mastro e a IMU elevada e centrada. Toca em qualquer peça para veres a ficha.',
    'Raspberry Pi and ESP32 side by side inside an IP66 enclosure at deck level, the GPS at the top of the mast and the IMU raised and centred. Tap any part to see its data sheet.'
  ],
  'hero.photo':   ['Praia da Marinha, Algarve', 'Praia da Marinha, Algarve'],

  /* ---------- momentos da cena de abertura ---------- */
  'b1.k': ['01 — Propulsão', '01 — Propulsion'],
  'b1.t': ['Dois jatos, sem leme', 'Two jets, no rudder'],
  'b1.b': [
    'Cada casco leva o seu waterjet, o seu motor de 300 W e o seu ESC. A viragem faz-se pela diferença de potência entre os dois lados, com o braço de 234 mm entre eixos a dar a autoridade de guinada, e por um bocal orientável por servo em cada unidade.',
    'Each hull carries its own waterjet, its own 300 W motor and its own ESC. Turning comes from the power difference between the two sides, with the 234 mm arm between axes providing yaw authority, plus a servo-actuated steering nozzle on each unit.'
  ],
  'b2.k': ['02 — Flutuação', '02 — Flotation'],
  'b2.t': ['38 mm de calado', '38 mm of draft'],
  'b2.b': [
    'A 6,2 kg o casco mergulha 38 mm e deixa 108 mm de bordo livre. Com as duas baterias alojadas dentro dos cascos, o centro de gravidade fica a 107 mm — e a distância entre flutuadores torna a plataforma quase impossível de inclinar.',
    'At 6.2 kg the hull sits 38 mm deep and leaves 108 mm of freeboard. With both batteries housed inside the hulls, the centre of gravity drops to 107 mm — and the spacing between floats makes the platform almost impossible to heel.'
  ],
  'b3.k': ['03 — Autonomia', '03 — Autonomy'],
  'b3.t': ['Decide e protege-se', 'It decides, and it protects itself'],
  'b3.b': [
    'Um Raspberry Pi calcula o rumo e os waypoints. Um ESP32 vigia-o: se deixar de receber comandos válidos durante 1,1 segundos, corta os motores sozinho. Três circuitos elétricos independentes, um por casco e um para a eletrónica.',
    'A Raspberry Pi computes heading and waypoints. An ESP32 watches over it: if valid commands stop arriving for 1.1 seconds, it cuts the motors on its own. Three independent electrical circuits, one per hull and one for the electronics.'
  ],

  'hero.author':  ['Gonçalo Martins da Silva · Instituto Superior Técnico', 'Gonçalo Martins da Silva · Instituto Superior Técnico'],

  /* ---------- visualizador ---------- */
  'v.title':      ['Modelo interativo', 'Interactive model'],
  'v.lead': [
    'Roda, aproxima e desliga subsistemas. Clica em qualquer componente para ver as suas especificações. A geometria vem diretamente do ficheiro CAD do projeto.',
    'Orbit, zoom and toggle subsystems. Click any component to see its specifications. The geometry comes straight from the project CAD file.'
  ],
  'v.loading':    ['A carregar o modelo…', 'Loading model…'],
  'v.subsystems': ['Subsistemas', 'Subsystems'],
  'v.views':      ['Vistas', 'Views'],
  'v.display':    ['Visualização', 'Display'],
  'v.iso':        ['Isométrica', 'Isometric'],
  'v.top':        ['Topo', 'Top'],
  'v.side':       ['Lateral', 'Side'],
  'v.bow':        ['Proa', 'Bow'],
  'v.stern':      ['Popa', 'Stern'],
  'v.xray':       ['Ver interior', 'See inside'],
  'v.waterline':  ['Linha de água', 'Waterline'],
  'v.section':    ['Corte longitudinal', 'Longitudinal section'],
  'v.explode':    ['Vista explodida', 'Exploded view'],
  'v.colormode':  ['Cor por subsistema', 'Colour by subsystem'],
  'v.autorotate': ['Rotação automática', 'Auto-rotate'],
  'v.reset':      ['Repor', 'Reset'],
  'v.hint':       ['Clica num componente', 'Click a component'],
  'v.hintbody': [
    'Arrasta para rodar · roda do rato para aproximar · clica numa peça para ver os detalhes. Liga «ver interior» para ver as baterias dentro dos cascos.',
    'Drag to orbit · scroll to zoom · click a part for details. Turn on "see inside" to reveal the batteries inside the hulls.'
  ],
  'v.qty':        ['Quantidade', 'Quantity'],
  'v.dims':       ['Envolvente', 'Bounding box'],
  'v.close':      ['Fechar', 'Close'],
  'v.wlnote':     ['Calado derivado para 6,2 kg', 'Draft derived for 6.2 kg'],

  /* ---------- estados ---------- */
  'st.validated': ['Validado', 'Validated'],
  'st.estimated': ['Estimado', 'Estimated'],
  'st.derived':   ['Derivado', 'Derived'],
  'st.open':      ['Em aberto', 'Open'],
  'st.legend': [
    'Validado — medido ou confirmado em bancada. Estimado — cálculo de arquitetura sobre datasheet, ainda sem medição. Derivado — calculado a partir da geometria CAD. Em aberto — decisão por tomar.',
    'Validated — measured or confirmed on the bench. Estimated — architecture calculation from datasheets, not yet measured. Derived — computed from the CAD geometry. Open — decision still to be made.'
  ],

  /* ---------- arquitetura ---------- */
  'a.title':  ['Arquitetura do sistema', 'System architecture'],
  'a.lead': [
    'A arquitetura separa deliberadamente a lógica de alto nível do controlo de baixa latência. O Raspberry Pi decide para onde ir; o ESP32 garante que os motores param quando alguma coisa corre mal. Essa separação existe para que atrasos do sistema operativo nunca cheguem aos ESCs.',
    'The architecture deliberately separates high-level logic from low-latency control. The Raspberry Pi decides where to go; the ESP32 guarantees the motors stop when something goes wrong. That split exists so operating-system latency never reaches the ESCs.'
  ],
  'a.op':     ['Operador', 'Operator'],
  'a.oplink': ['Wi-Fi · interface web', 'Wi-Fi · web interface'],
  'a.pi':     ['Raspberry Pi 4', 'Raspberry Pi 4'],
  'a.pirole': ['Computador de bordo', 'On-board computer'],
  'a.pitasks':['Navegação · GPS · IMU · ADC · waypoints · logging', 'Navigation · GPS · IMU · ADC · waypoints · logging'],
  'a.link':   ['USB-C serial · heartbeat 5 Hz', 'USB-C serial · 5 Hz heartbeat'],
  'a.esp':    ['ESP32', 'ESP32'],
  'a.esprole':['Controlo de tempo real', 'Real-time control'],
  'a.esptasks':['Validação · PWM · watchdog · failsafe', 'Validation · PWM · watchdog · failsafe'],
  'a.escL':   ['ESC esquerdo', 'Left ESC'],
  'a.escR':   ['ESC direito', 'Right ESC'],
  'a.wjL':    ['Waterjet esquerdo', 'Left waterjet'],
  'a.wjR':    ['Waterjet direito', 'Right waterjet'],
  'a.sensors':['Sensores', 'Sensors'],
  'a.why':    ['Porquê dois controladores?', 'Why two controllers?'],
  'a.whybody': [
    'O Raspberry Pi corre Linux, e Linux não dá garantias de tempo real. Se o escalonador atrasar um ciclo, um sinal PWM gerado diretamente pelo Pi pode ficar num estado indefinido com os motores a rodar. O ESP32 resolve isto: recebe uma intenção em percentagem, valida-a, e se deixar de receber comandos válidos durante ≈1,1 s corta os motores sozinho, independentemente do que o Pi esteja a fazer.',
    'The Raspberry Pi runs Linux, and Linux makes no real-time guarantees. If the scheduler stalls for a cycle, a PWM signal generated directly by the Pi can be left in an undefined state with the motors spinning. The ESP32 solves this: it receives an intent as a percentage, validates it, and if valid commands stop arriving for ≈1.1 s it cuts the motors on its own, regardless of what the Pi is doing.'
  ],

  /* ---------- subsistemas ---------- */
  's.title': ['Subsistemas', 'Subsystems'],
  's.lead': [
    'Cinco blocos independentes. A modularidade é um objetivo declarado do projeto: navegação, controlo de motores, sensores, alimentação e segurança evoluem separadamente.',
    'Five independent blocks. Modularity is a declared project goal: navigation, motor control, sensing, power and safety each evolve on their own.'
  ],
  's.structure.t': ['Estrutura e flutuação', 'Structure and flotation'],
  's.structure.b': [
    'Dois cascos com núcleo em XPS de célula fechada e pele híbrida — contraplacado marítimo de 3 mm nas zonas planas e fibra de vidro laminada na proa em cunha, onde nenhuma placa plana assenta sem facetagem. Três travessas unem os cascos e aparafusam a longarinas embutidas no convés, nunca à espuma. A configuração catamarã foi escolhida pela estabilidade, pela área útil e pela distribuição de massa.',
    'Two hulls with a closed-cell XPS core and a hybrid skin — 3 mm marine plywood over the flat regions and laminated fibreglass over the wedge bow, where no flat sheet can sit without faceting. Three crossbeams tie the hulls together and bolt into stringers recessed in the deck, never into the foam. The catamaran configuration was chosen for stability, usable deck area and mass distribution.'
  ],
  's.power.t': ['Energia e distribuição', 'Power and distribution'],
  's.power.b': [
    'Três circuitos completamente independentes. Cada casco tem a sua LiPo 3S de 5000 mAh alojada abaixo do convés, o seu fusível de 40 A e a sua loop key XT90-S, alimentando apenas o ESC e o waterjet daquele lado. A eletrónica tem circuito próprio: LiPo 2S de 2200 mAh, fusível de 10 A, interruptor estanque e conversor DC-DC de 5 V. Nenhum cabo de potência atravessa a ponte — só passam sinais. Os negativos dos dois cascos encontram o GND da eletrónica num único ponto, dentro da caixa IP66, pelo fio preto da ficha servo de cada ESC.',
    'Three completely independent circuits. Each hull carries its own 5000 mAh 3S LiPo below deck, its own 40 A fuse and its own XT90-S loop key, feeding only that side\'s ESC and waterjet. The electronics run on their own circuit: a 2200 mAh 2S LiPo, a 10 A fuse, a sealed switch and a 5 V DC-DC converter. No power cable crosses the bridge — only signals do. The two hull negatives meet electronics ground at a single point inside the IP66 enclosure, through the black wire of each ESC servo lead.'
  ],
  's.propulsion.t': ['Propulsão', 'Propulsion'],
  's.propulsion.b': [
    'Dois waterjets independentes, cada um com o seu motor brushless de 300 W e o seu ESC de 40 A instalado junto ao motor para manter curtos os cabos de fase. Não há leme. A manobra combina duas vias: empuxo diferencial entre os lados, com a autoridade de guinada a vir do braço de 234 mm entre os eixos, e um bocal orientável accionado por servo em cada unidade, comandado pelo ESP32. O regime é de deslocamento — o planeio está excluído tanto pela massa como pela forma dos cascos.',
    'Two independent waterjets, each with its own 300 W brushless motor and its own 40 A ESC mounted next to the motor to keep the phase leads short. There is no rudder. Steering works two ways: differential thrust between the sides, with yaw authority from the 234 mm arm between the axes, and a servo-actuated steering nozzle on each unit, driven by the ESP32. The regime is displacement — planing is ruled out by both mass and hull form.'
  ],
  's.compute.t': ['Computação', 'Compute'],
  's.compute.b': [
    'Um Raspberry Pi 4 como computador de bordo e um ESP32 como controlador de tempo real, ligados por USB-C, os dois dentro de uma caixa IP66 assente ao nível do convés. Todas as entradas de cabo passam por bucins e cada cabo forma um laço de gotejamento antes de entrar. A caixa não pode descer abaixo do convés: tem 155 mm de largura e o túnel entre cascos tem 118 mm.',
    'A Raspberry Pi 4 as on-board computer and an ESP32 as real-time controller, linked over USB-C, both inside an IP66 enclosure seated at deck level. Every cable entry passes through a gland and each cable forms a drip loop before entering. The enclosure cannot sit below deck: it is 155 mm wide and the tunnel between hulls is 118 mm.'
  ],
  's.sensing.t': ['Perceção', 'Sensing'],
  's.sensing.b': [
    'GPS NEO-8M com antena ativa em UART dedicada, IMU BNO055 e ADC ADS1015 a partilhar o barramento I2C. O GPS está no ponto mais alto do veículo e a IMU está elevada e centrada, ambos afastados dos cabos de potência — a interferência elétrica nos sensores é um risco identificado e a separação física é a mitigação.',
    'A NEO-8M GPS with active antenna on a dedicated UART, a BNO055 IMU and an ADS1015 ADC sharing the I2C bus. The GPS sits at the highest point of the vehicle and the IMU is raised and centred, both kept away from power cabling — electrical interference with the sensors is an identified risk and physical separation is the mitigation.'
  ],

  /* ---------- especificações ---------- */
  'sp.title': ['Especificações', 'Specifications'],
  'sp.lead': [
    'Cada valor está marcado com a sua origem. Os componentes de propulsão ainda não chegaram fisicamente ao projeto, pelo que nenhum número de desempenho é ainda uma medição.',
    'Every value is tagged with its provenance. The propulsion components have not physically arrived yet, so no performance figure here is a measurement.'
  ],

  /* ---------- segurança ---------- */
  'sf.title': ['Segurança e failsafe', 'Safety and failsafe'],
  'sf.lead': [
    'O sistema combina água, baterias LiPo, correntes elevadas, motores brushless e software autónomo. A filosofia é explícita: qualquer estado duvidoso reduz potência ou para os motores.',
    'The system combines water, LiPo batteries, high currents, brushless motors and autonomous software. The philosophy is explicit: any doubtful state reduces power or stops the motors.'
  ],
  'sf.1.t': ['Perda de comunicação', 'Loss of communication'],
  'sf.1.b': ['O ESP32 para os motores após timeout, medido em ≈1,1 s. O heartbeat a 5 Hz dá margem confortável.',
             'The ESP32 stops the motors after a timeout, measured at ≈1.1 s. The 5 Hz heartbeat leaves comfortable margin.'],
  'sf.2.t': ['Comando inválido', 'Invalid command'],
  'sf.2.b': ['Comandos fora do formato ou fora do limite seguro são rejeitados e provocam estado seguro.',
             'Commands outside the format or outside the safe limit are rejected and force a safe state.'],
  'sf.3.t': ['Corte manual', 'Manual cut-off'],
  'sf.3.b': ['Loop key XT90-S em cada casco, mais interruptor estanque no circuito da eletrónica. Sem chave inserida, aquele casco não tem alimentação — e o sinal de sense, ligado a jusante da chave, lê 0 V e reporta o ramo como desarmado.',
             'An XT90-S loop key in each hull, plus a sealed switch on the electronics circuit. With no key inserted that hull has no power — and the sense signal, tapped downstream of the key, reads 0 V and reports the branch as disarmed.'],
  'sf.4.t': ['Sem fix de GPS', 'No GPS fix'],
  'sf.4.b': ['O sistema não inicia navegação autónoma sem posição válida.',
             'The system will not start autonomous navigation without a valid position.'],
  'sf.5.t': ['Arranque em DISARMED', 'Boot in DISARMED'],
  'sf.5.b': ['O sistema arranca sempre desarmado. A perda e o regresso da ligação série nunca rearmam sozinhos.',
             'The system always boots disarmed. Losing and regaining the serial link never re-arms on its own.'],
  'sf.6.t': ['Ventilação das baterias', 'Battery venting'],
  'sf.6.b': ['O compartimento das LiPo não é hermético: em caso de falha de célula há libertação de gases, e dois entalhes de 2 mm funcionam como respiro.',
             'The LiPo compartment is deliberately not airtight: a cell failure releases gas, and two 2 mm notches act as a vent.'],
  'sf.open.t': ['Decisão em aberto: kill-switch remoto', 'Open decision: remote kill-switch'],
  'sf.open.b': [
    'Não existe ainda corte remoto independente do software. Está adiado por orçamento e é obrigatório antes de qualquer teste sem corda, autonomia livre ou operação afastada da margem. Duas opções em avaliação: um sistema RC a 2,4 GHz com canal dedicado ao corte de alta corrente, mais simples e desenhado para o efeito, ou um link LoRa com heartbeat, de maior alcance mas exigindo desenvolver a lógica de failsafe. Uma antena DVB foi avaliada e descartada — é de receção, não transmite.',
    'There is still no remote cut-off independent of the software. It is deferred on budget grounds and is mandatory before any untethered test, free autonomy or operation away from the bank. Two options are under evaluation: a 2.4 GHz RC system with a dedicated channel driving a high-current cut-off, simpler and purpose-built, or a LoRa link with heartbeat, longer range but requiring the failsafe logic to be developed. A DVB antenna was evaluated and ruled out — it receives, it does not transmit.'
  ],

  /* ---------- software ---------- */
  'sw.title': ['Software', 'Software'],
  'sw.lead': [
    'Organizado em packages com um orquestrador. Validado em simulação de ciclo fechado com comunicação real ao ESP32 — o modo NAV foi testado com o ESP32 a aceitar comandos, com a malha fechada pelo simulador e sem motores.',
    'Organised in packages with an orchestrator. Validated in closed-loop simulation with real communication to the ESP32 — NAV mode was tested with the ESP32 accepting commands, the loop closed by the simulator and no motors connected.'
  ],
  'sw.1.t': ['SerialLink', 'SerialLink'],
  'sw.1.b': ['Ligação série robusta: tolera ESP32 ausente, faz buffer de linhas completas, descarta o lixo de arranque e garante STOP no fecho.',
             'Robust serial link: tolerates a missing ESP32, buffers complete lines, discards boot garbage and guarantees STOP on close.'],
  'sw.2.t': ['Máquina de estados', 'State machine'],
  'sw.2.b': ['DISARMED ↔ ARMED / NAV. Arranque sempre em DISARMED, heartbeat 0/0 a 5 Hz quando armado, STOP com prioridade absoluta.',
             'DISARMED ↔ ARMED / NAV. Always boots disarmed, 0/0 heartbeat at 5 Hz when armed, STOP with absolute priority.'],
  'sw.3.t': ['Heading hold', 'Heading hold'],
  'sw.3.b': ['Normalização do erro angular para (−180°, 180°] e controlador proporcional com saturação. O mixer converte throttle e steer em L/R com teto de 30 %.',
             'Angular error normalised to (−180°, 180°] and a proportional controller with saturation. The mixer converts throttle and steer into L/R with a 30 % ceiling.'],
  'sw.4.t': ['Navegação por waypoints', 'Waypoint navigation'],
  'sw.4.b': ['Haversine, bearing e raio de chegada. Validada em ciclo fechado sintético no PC e no Raspberry Pi.',
             'Haversine, bearing and arrival radius. Validated in synthetic closed loop on both PC and Raspberry Pi.'],
  'sw.5.t': ['Telemetria', 'Telemetry'],
  'sw.5.b': ['Um CSV por sessão, timestamp ao milissegundo e flush imediato. Eventos BOOT, SERIAL, STATE, TX, RX, STOP, HEADING e SHUTDOWN.',
             'One CSV per session, millisecond timestamps and immediate flush. BOOT, SERIAL, STATE, TX, RX, STOP, HEADING and SHUTDOWN events.'],
  'sw.6.t': ['Testes automáticos', 'Automated tests'],
  'sw.6.b': ['Heading, mixer e navegação testados sem hardware, para que a lógica possa evoluir sem o barco montado.',
             'Heading, mixer and navigation tested without hardware, so the logic can evolve without the boat assembled.'],
  'sw.proto': ['Protocolo de comando', 'Command protocol'],

  /* ---------- estado ---------- */
  'stt.title': ['Estado do projeto', 'Project status'],
  'stt.lead': [
    'O que já funciona, o que é estimativa e o que continua por decidir. Esta separação é mantida deliberadamente — é a diferença entre um projeto documentado e um projeto anunciado.',
    'What already works, what is an estimate and what is still undecided. This separation is kept deliberately — it is the difference between a documented project and an announced one.'
  ],
  'stt.done':   ['Validado em bancada', 'Validated on the bench'],
  'stt.wip':    ['Estimado, à espera de medição', 'Estimated, awaiting measurement'],
  'stt.open':   ['Decisões em aberto', 'Open decisions'],
  'stt.d1': ['Comunicação Raspberry Pi ↔ ESP32 por USB-C, com parser não bloqueante', 'Raspberry Pi ↔ ESP32 communication over USB-C, with a non-blocking parser'],
  'stt.d2': ['Failsafe por timeout, confirmado experimentalmente', 'Timeout failsafe, experimentally confirmed'],
  'stt.d3': ['Máquina de estados, heading hold e navegação por waypoints em simulação', 'State machine, heading hold and waypoint navigation in simulation'],
  'stt.d4': ['Logging CSV com eventos ao milissegundo', 'CSV logging with millisecond events'],
  'stt.d5': ['Raspberry Pi operacional headless, I2C e Serial ativos', 'Raspberry Pi running headless, I2C and Serial enabled'],
  'stt.d6': ['Arquitetura mecânica v6.1 validada em 3D', 'Mechanical architecture v6.1 validated in 3D'],
  'stt.w1': ['Massa: 6,0–6,5 kg por cálculo de volumes, nunca pesada', 'Mass: 6.0–6.5 kg from volume calculations, never weighed'],
  'stt.w2': ['Impulso, corrente e autonomia, todos a partir de datasheet', 'Thrust, current and endurance, all from datasheets'],
  'stt.w3': ['Fusível principal de 100 A, dimensionamento teórico', '100 A main fuse, theoretical sizing'],
  'stt.w4': ['Componentes de propulsão ainda não recebidos', 'Propulsion components not yet received'],
  'stt.o1': ['Kill-switch remoto: RC 2,4 GHz ou LoRa com heartbeat', 'Remote kill-switch: 2.4 GHz RC or LoRa with heartbeat'],
  'stt.o2': ['Modelo final das unidades de waterjet', 'Final waterjet unit selection'],
  'stt.o3': ['Função final de cada bateria, após medições', 'Final role of each battery, after measurements'],
  'stt.o4': ['Estratégia de Return-To-Home e telemetria em tempo real', 'Return-to-home strategy and real-time telemetry'],

  'stt.scope.t': ['Fora de âmbito, por decisão', 'Out of scope, by decision'],
  'stt.scope.b': [
    'Deteção de obstáculos, redundância de hardware, telemetria 4G/LTE e algoritmos de IA ficaram deliberadamente fora desta fase. Estão registados para que a omissão não seja lida como lacuna: o objetivo imediato é validar a arquitetura base, não acrescentar complexidade que atrasaria um veículo funcional.',
    'Obstacle detection, hardware redundancy, 4G/LTE telemetry and AI algorithms were deliberately left out of this phase. They are recorded so the omission is not read as an oversight: the immediate goal is to validate the base architecture, not to add complexity that would delay a working vehicle.'
  ],

  /* ---------- rodapé ---------- */
  'f.project':  ['Projeto pessoal de engenharia', 'Personal engineering project'],
  'f.author':   ['Gonçalo Martins da Silva', 'Gonçalo Martins da Silva'],
  'f.school':   ['Engenharia Eletrotécnica e de Computadores · Instituto Superior Técnico', 'Electrical and Computer Engineering · Instituto Superior Técnico'],
  'f.docs':     ['Arquitetura v1.11 · esquema elétrico v1.11 · modelo CAD v6.3', 'Architecture v1.11 · electrical schematic v1.11 · CAD model v6.3'],
  'f.note': [
    'Os valores apresentados mantêm o estatuto que têm na documentação técnica do projeto. Nenhum número de desempenho é ainda uma medição em água.',
    'The figures shown keep the status they hold in the project technical documentation. No performance figure here is yet a measurement on water.'
  ]
};

export function t(key, lang) {
  const e = T[key];
  if (!e) return key;
  return lang === 'en' ? e[1] : e[0];
}
