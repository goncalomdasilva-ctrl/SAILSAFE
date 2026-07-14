# Engineering log

A viabilidade do projeto SAILSAFE tem vindo a ser analisada desde fevereiro de 2026. Durante o período letivo, o foco esteve na exploração de opções de arquitetura, integração de subsistemas e definição dos principais requisitos técnicos.

Uma das tentativas iniciais incluiu o desenho de uma PCB para integração elétrica. Essa abordagem revelou-se inadequada para distribuição de potência, sobretudo pela ausência de planos de cobre e pela fase ainda inicial de experiência em desenho de PCBs. Ainda assim, essa tentativa foi útil para clarificar restrições do sistema e reforçar a decisão de adotar uma arquitetura elétrica mais conservadora e robusta.

Após várias iterações, foi definida uma arquitetura inicial suficientemente sólida para avançar para a fase de execução e validação experimental.

## 2026-07-05

### Trabalho realizado

* Preparação inicial do código do ESP32 antes da chegada dos ESCs e do Raspberry Pi.
* Criação do esquema elétrico v1.

### Problemas / limitações

* Curva de aprendizagem inicial do KiCad, com algum tempo necessário para compreender a ferramenta e estruturar corretamente o esquema.

### Resultado do dia

* Base inicial de firmware preparada.
* Primeira versão do esquema elétrico concluída.

### Próximo passo

* Refinar a arquitetura elétrica e continuar a consolidação da documentação principal.

## 2026-07-06

### Trabalho realizado

* Firmware inicial do ESP32 preparado.
* Esquema elétrico v1 fechado.
* Documentação principal do projeto atualizada.
* BOM consolidada.
* Estratégia de controlo inicial por Wi-Fi definida.
* Recebido o Raspberry Pi 4 para o projeto.
* Configurado cartão microSD de 32 GB com Raspberry Pi OS.
* Configurado acesso remoto por SSH.
* Atualizado o sistema operativo do Raspberry Pi.
* Ativadas as interfaces I2C e Serial.
* Instaladas ferramentas base de desenvolvimento: Python 3, pip, venv, git, i2c-tools, screen e minicom.
* Criada a estrutura inicial de pastas do projeto no Raspberry Pi.

### Decisões técnicas

* O kill-switch físico/remoto foi identificado como requisito futuro, mas adiado por motivos de orçamento.
* Foi decidido não ligar ainda ESCs, motores ou baterias de potência antes da validação da comunicação Raspberry Pi → ESP32.

### Problemas / limitações

* O KiCad não incluía vários módulos específicos necessários para o projeto, obrigando ao uso de conectores genéricos no esquema.
* O esquema elétrico ainda requer melhorias de representação, embora os pontos principais de arquitetura estejam definidos.
* A preparação inicial do Raspberry Pi exigiu adaptação de hardware disponível para configurar o microSD.

### Resultado do dia

* O projeto ficou num estado técnico muito mais sólido em termos de arquitetura, documentação e preparação para testes de bancada.
* O Raspberry Pi ficou operacional e preparado para integração futura com sensores e comunicação com o ESP32.
* O projeto encontra-se a aguardar a chegada dos componentes para iniciar testes físicos.

### Próximo passo

* Testar comunicação Raspberry Pi → ESP32 por USB.

## 2026-07-07

### Trabalho realizado

* Iniciada a criação do repositório GitHub do projeto SAILSAFE.
* Definida a estrutura inicial para documentação pública do projeto.
* Preparado o conteúdo inicial do README e da organização de ficheiros.
* Estruturados assistentes de IA para apoio à documentação, organização de tarefas e maior consistência na escrita técnica.

### Decisões técnicas

* Foi decidido começar com uma estrutura simples de repositório, suficientemente organizada para ser mantida sem fricção excessiva.
* A documentação pública será construída de forma incremental, em vez de tentar formalizar tudo de uma só vez.

### Problemas / limitações

* Curva de aprendizagem inicial do GitHub e da lógica de repositórios.
* Ainda sem integração total dos ficheiros técnicos no repositório.

### Resultado do dia

* O projeto passou a ter uma base inicial para documentação pública e portefólio técnico.
* Ficou definido um caminho mais claro para organizar arquitetura, software, hardware e registos de evolução.
* Os assistentes de IA passaram a integrar o processo como ferramenta de apoio à produtividade e revisão técnica, sem substituir validação própria.

### Próximo passo

* Fazer upload da documentação principal, esquema elétrico, ficheiro 3D e código do ESP32 para o repositório.



## 2026-07-08

### Trabalho realizado

* Validada comunicação Raspberry Pi 4 → ESP32 por USB (ligação detetada como /dev/ttyUSB0).
* Confirmada interface USB-série CH341 no sistema.
* Validada comunicação UART entre Raspberry Pi e ESP32.
* Confirmado formato de comando textual:
L:10 R:10
* Validada conversão interna no ESP32:
percentagem → PWM (ex.: 10% → 1100 µs).
* Confirmado funcionamento de failsafe por perda de input (timeout → motores parados).
* Criado script Python no Raspberry Pi para envio periódico de comandos (keep-alive).
* Reestruturado parser UART do ESP32 para abordagem não bloqueante baseada em buffer + newline.

### Problemas / limitações

* Cabo USB inicial não suportava dados (sem deteção do ESP32).
* Uso de screen causava envio inválido de comandos (carácter a carácter).
* Diferença entre documentação e implementação (PWM vs percentagem).
* Parser inicial (readStringUntil) introduzia risco de bloqueio.
* Conflito de acesso à porta série ao usar simultaneamente screen e Python.

### Decisões técnicas

* Manter arquitetura:

  * Raspberry Pi → controlo de alto nível
  * ESP32 → controlo em tempo real + failsafe
* Congelar protocolo atual:
comando textual em percentagem (L:x R:y + newline)
* Limitar output inicial a 0–30% para segurança em bancada.
* Usar keep-alive como mecanismo normal e failsafe como redundância.

### Resultado do dia

* Cadeia de controlo RPi → ESP32 validada em bancada.
* Protocolo básico de comando e segurança funcional.
* Base sólida estabelecida para integração futura com ESCs e motores.

### Próximo passo

* Validar repetibilidade do keep-alive e comando STOP.
* Evoluir comando para modelo throttle + steering.
* Só depois iniciar integração com ESCs, motores e testes de potência.





### 2026-07-10

#### Trabalho realizado

* Aquisição de material elétrico para preparação da montagem física do sistema.
* Compra de cabos elétricos com secções de 6 mm², 1,5 mm² e 0,75 mm².
* Compra de conectores Wago para ligações de baixa corrente e sinais.
* Compra do carregador para as baterias LiPo.
* Aquisição de consumíveis e acessórios necessários à futura montagem elétrica.

#### Decisões técnicas

* Reservar o cabo de 6 mm² para o circuito de potência: bateria de 5000 mAh, fusíveis, barramentos e alimentação dos ESCs.
* Reservar o cabo de 1,5 mm² para alimentação da eletrónica, entrada do conversor DC-DC e ligação de referência entre os negativos dos dois subsistemas.
* Reservar o cabo de 0,75 mm², ou os fios originais dos módulos, para sinais PWM, GND de sinal e sensores.
* Manter os Wagos limitados a ligações de baixa corrente e sinais, não os utilizando no caminho principal de corrente dos motores.

#### Resultado do dia

* Material elétrico principal obtido para iniciar a preparação e os testes de montagem.
* Cablagem disponível com secções diferenciadas para potência, eletrónica e sinais.

#### Próximo passo

* Definir a arquitetura mecânica dos cascos, a localização das caixas, dos ESCs e das passagens de cabos antes de cortar ou montar a estrutura definitiva.

### 2026-07-11

#### Trabalho realizado

* Revisão crítica da arquitetura mecânica e elétrica do primeiro protótipo.
* Definição preliminar de dois cascos em XPS de célula fechada, revestidos com fibra de vidro e resina epóxi.
* Definição de reforços locais em contraplacado nas popas, pontos de fixação das travessas, base da caixa central e ponto de recuperação por corda.
* Definição preliminar de dimensões: aproximadamente 800 mm de comprimento total, 350 mm de largura total, cascos com cerca de 100–110 mm de largura e 130–140 mm de altura.
* Definição de três travessas estruturais: frontal, central e traseira.
* Análise da passagem dos cabos por conduítes no interior das travessas e, depois, pela face superior/interior dos cascos, devidamente fixos e protegidos.
* Revisão da localização dos ESCs, passando a privilegiar a instalação de cada ESC próximo do respetivo waterjet para reduzir o comprimento dos três cabos de fase do motor.
* Consolidação da separação das duas baterias: LiPo 5000 mAh dedicada à propulsão e LiPo 2200 mAh dedicada à eletrónica através do conversor DC-DC.
* Clarificação da estratégia de GND comum entre potência e eletrónica.

#### Decisões técnicas

* Não ligar os positivos das duas baterias e não colocar as baterias em paralelo.
* Ligar o negativo da bateria de potência ao barramento negativo de potência e o negativo da bateria de eletrónica ao ponto de GND da eletrónica.
* Criar uma única ligação de referência, em estrela, entre o GND da eletrónica e o barramento negativo de potência.
* Manter os fios GND que acompanham os sinais PWM dos dois ESCs, sem depender exclusivamente destes fios finos para estabelecer o GND comum do sistema.
* Usar cabo de 6 mm² entre a distribuição de potência e cada ESC.
* Usar cabo de 1,5 mm² para a ligação única de referência entre o GND eletrónico e o barramento negativo de potência.
* Isolar os fios de 5 V/BEC dos ESCs, caso existam, enquanto a eletrónica for alimentada pelo conversor DC-DC dedicado.
* Não fixar os waterjets diretamente ao XPS; utilizar contraplacado reforçado na popa, laminado e selado, com parafusos, anilhas e vedação adequados.
* Manter os ESCs acessíveis, protegidos contra água e com possibilidade de dissipação térmica; não os encapsular permanentemente em foam ou epóxi.

#### Riscos e limitações identificados

* A estimativa inicial de massa de 1,8–2,2 kg pode ser otimista para o protótipo completo; a massa real deve ser medida durante a construção.
* O XPS sem laminação não possui resistência suficiente para impactos, parafusos ou cargas concentradas.
* Cabos exteriores mal fixos podem entrar na admissão dos waterjets, sofrer abrasão ou conduzir água para as caixas.
* A inexistência de kill-switch físico/remoto mantém a restrição de testes na água com corda de recuperação, potência limitada e supervisão direta.

#### Resultado do dia

* Conceito mecânico preliminar consolidado para uma construção híbrida: XPS + fibra de vidro + epóxi, com reforços estruturais em contraplacado.
* Percurso preliminar de cabos e localização dos ESCs definidos.
* Arquitetura de duas baterias e GND comum clarificada sem união dos positivos.
* Base técnica preparada para atualizar o documento de arquitetura para a versão v1.5.

#### Próximo passo

* Confirmar as dimensões físicas e a massa de todos os componentes.
* Fazer uma disposição à escala real em cartão antes de cortar XPS ou madeira.
* Confirmar o modelo exato, o procedimento de arming e a presença de BEC nos ESCs.
* Comprar os materiais mecânicos e de laminação após confirmar disponibilidade, compatibilidade e quantidades.

### 2026-07-12
 
#### Trabalho realizado
 
* Compra de contraplacado para os cascos e para a estrutura.
* Iteração de vários modelos CAD (.step); consolidada a versão v3 do modelo: caixas centrais ocas em contraplacado de 9 mm com tampas, placa base a distribuir a carga da pilha de caixas pelas travessas 1 e 2, componentes internos modelados (baterias, bus bars, fusível principal, Raspberry Pi 4, ESP32, DC-DC, BNO055, ADS1015, módulo GPS), antena GPS relocalizada para o topo da tampa e coberturas de proteção sobre os ESCs.
* Revisão do orçamento de massa com base nos volumes reais do modelo v3: ≈4,5–5,5 kg tal como modelado (madeira ≈2,6 kg, XPS ≈0,74 kg, fibra+epóxi ≈0,45 kg, restantes componentes ≈1,3 kg), invalidando a estimativa anterior de 1,8–2,2 kg.
* Análise de compatibilidade massa/potência: a 5,5 kg, ≈110 W/kg e impulso/peso estimado de 0,4–0,55 — adequado a navegação em deslocamento e ao OBJ-001; planeio excluído. Calado estimado ≈31 mm (≈6 mm/kg), favorável à submersão das admissões dos waterjets.
* Documento de arquitetura atualizado para v1.6: REQ-MEC-003, secções 5.3 e 17.2 e histórico de revisões.
* Conversor DC-DC colocado em funcionamento, com saída estimada em ≈5,1 V reais.
* Diagnóstico do multímetro: erro de escala consistente de ×1,86 confirmado com três referências independentes (LiPo a 11,8 V confirmados pelo carregador vs 22 lidos; pilha alcalina ~1,6 V vs 3,00 lidos; leitura do DC-DC coerente com o mesmo fator).
#### Decisões técnicas
 
* Alvo de saída do DC-DC fixado em 5,1 V (compensação da queda na cablagem até ao Raspberry Pi); ligação do Pi condicionada a verificação sob carga.
* Validação do DC-DC feita por medição comparativa contra referência conhecida, dado o erro de escala do multímetro; valores absolutos deste multímetro considerados não fiáveis até substituição.
* Meta de aligeiramento estrutural registada na v1.6: contraplacado de 5–6 mm nas caixas, travessas furadas ou em tubo de alumínio 20×20 e possível unificação das duas caixas (objetivo 3,5–4,0 kg).
#### Problemas / limitações
 
* Multímetro com leituras infladas por fator ≈1,86 (referência interna degradada); compartimento da pilha inacessível até agora, substituição pendente.
* As leituras erradas causaram falso alarme inicial (baterias aparentemente a 21–22 V e DC-DC aparentemente a 9,4–9,6 V), consumindo tempo de diagnóstico.
* A compra de contraplacado para os cascos pode implicar mudança da arquitetura de cascos (XPS + fibra → contraplacado), com impacto direto no orçamento de massa da v1.6; decisão ainda não formalizada.
#### Resultado do dia
 
* DC-DC operacional com saída estimada correta; baterias validadas como saudáveis (11,8 V confirmados pelo carregador).
* Modelo CAD v3 com componentes integrados e correções estruturais; documentação de arquitetura atualizada para v1.6 com orçamento de massa realista.
* Material estrutural (contraplacado) adquirido.
#### Próximo passo
 
* Adquirir multímetro fiável antes de qualquer teste com ESCs e motores.
* Verificar a saída do DC-DC sob carga e remedir a referência no fim da sessão.
* Decidir formalmente a arquitetura dos cascos (XPS + fibra vs contraplacado) e refazer o cálculo de massa antes de qualquer corte definitivo.
* Manter a disposição à escala real antes do corte, conforme definido a 2026-07-11.

  
### 2026-07-13
 
#### Trabalho realizado
 
* Consolidação física da cadeia de alimentação de 5 V: soldaduras reforçadas, fusível adicionado ao circuito e termorretráctil aplicado em todas as ligações.
* Validação da saída do conversor DC-DC: 5 V estáveis confirmados após a consolidação.
* Análise comparativa das duas vias de alimentação do Raspberry Pi 4: entrada USB-C (com cabo A-para-C descarnado) vs pinos GPIO (5 V nos pinos 2/4, GND nos pinos 6/14).
* Avaliação dos cabos disponíveis: cabo A-para-C descarnado considerado subdimensionado para a corrente do Pi 4 (condutores finos, retorno pela malha de blindagem); identificado cabo micro-B para a ligação Pi → ESP32.
* Definição do procedimento de identificação dos pinos GPIO com multímetro (continuidade pino 2 ↔ pino 4; continuidade pino 6 ↔ carcaça USB) e do procedimento de soldadura (solda no topo do pino, ≤3–4 s, termorretráctil, alívio de tensão com abraçadeira ao furo de montagem).
#### Decisões técnicas
 
* Alimentar o Raspberry Pi 4 pelos pinos GPIO (2/4 = +5 V; 6/14 = GND) com fio de 0,75 mm², usando os dois pares para dividir corrente e dar redundância mecânica; via USB-C mantida como alternativa.
* Alimentar o ESP32 exclusivamente pelo cabo USB a partir do Pi (dados + alimentação); não ligar VIN em simultâneo com USB.
* Instalar condensador eletrolítico (470–1000 µF, ≥10 V) junto ao ponto de entrega no Pi, como reservatório para picos de corrente; cerâmico de 100 nF a adicionar quando disponível.
* Riscos de soldadura identificados: ponte entre pino 2 (5 V) e pino 1 (3,3 V) é destrutiva; verificação final de continuidade 5 V↔GND e 5 V↔3,3 V obrigatória antes de dar corrente.
* Critério de aceitação da alimentação: vcgencmd get_throttled = 0x0 com o sistema em bateria.
#### Problemas / limitações
 
* Apenas disponível o condensador eletrolítico; o cerâmico de 100 nF fica pendente (impacto reduzido: filtra ruído de alta frequência, não afeta a estabilidade de tensão média).
* Multímetro de confiança ainda por adquirir; medições de corrente e verificações finais dependem dele.
#### Resultado do dia
 
* Cadeia de alimentação de 5 V consolidada e protegida (fusível + termorretráctil), com saída estável.
* Arquitetura de alimentação do par Pi/ESP32 decidida e documentada: DC-DC → GPIO do Pi; Pi → USB → ESP32.
* Procedimentos de identificação de pinos, soldadura e verificação definidos antes da execução.
#### Próximo passo
 
* Soldar os rabichos de 0,75 mm² aos pinos GPIO com o procedimento definido.
* Primeiro arranque do Pi em bateria; verificar get_throttled; só depois ligar o ESP32 e repetir.
* Testar o cabo micro-B (deteção de /dev/ttyUSB0) e correr keep-alive + failsafe integralmente em bateria.
* Comprar multímetro e condensador cerâmico de 100 nF.

