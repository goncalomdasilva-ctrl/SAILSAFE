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

#### 2026-07-14

##### Trabalho realizado
- Soldadura do condensador eletrolítico junto ao ponto de alimentação do Raspberry Pi 4.
- Soldadura dos cabos de alimentação diretamente aos pinos de alimentação do Raspberry Pi:
  - +5 V nos pinos físicos 2 e 4;
  - GND nos pinos físicos 6 e 14.
- Isolamento das ligações e preparação da cablagem para alimentar o Raspberry Pi através do conversor DC-DC.
- Primeiro ensaio de alimentação do Raspberry Pi através do circuito do barco.
- Observação dos LEDs de alimentação e atividade durante o arranque.
- Teste comparativo com alimentação através da entrada USB-C.
- Ligação do cartão microSD ao computador para diagnóstico.
- Confirmação de que o cartão era reconhecido fisicamente e de que a partição `bootfs` permanecia acessível.
- Regravação do Raspberry Pi OS através do Raspberry Pi Imager.
- Nova configuração do Wi-Fi, hostname, utilizador e acesso por SSH.

##### Decisões técnicas
- Não alimentar simultaneamente o Raspberry Pi pela entrada USB-C e pelos pinos GPIO.
- Validar inicialmente o Raspberry Pi sem o ESP32, sensores ou outros periféricos ligados.
- Confirmar primeiro o funcionamento do Raspberry Pi através de uma fonte USB-C de confiança.
- Repetir posteriormente o teste com alimentação exclusiva através da bateria e do conversor DC-DC.
- Utilizar `sudo poweroff` antes de interromper fisicamente a alimentação, sempre que existir acesso ao sistema.
- Manter `vcgencmd get_throttled` como principal verificação interna da qualidade da alimentação.
- Adotar `throttled=0x0` como critério inicial de aceitação da alimentação pelo circuito do barco.

##### Problemas / limitações
- Durante o primeiro ensaio existiu receio de danificar o Raspberry Pi devido à alimentação direta pelos pinos GPIO.
- A alimentação foi interrompida antes de o sistema concluir o arranque e sem encerramento controlado.
- Após a interrupção, ocorreu provável corrupção de ficheiros ou da configuração do Raspberry Pi OS no cartão microSD.
- O Raspberry Pi deixou de ficar acessível por SSH e não apareceu de forma fiável na rede local.
- Alguns endereços IP encontrados respondiam a `ping`, mas recusavam ligações na porta 22, dificultando a identificação do Raspberry Pi.
- A tentativa de ativar manualmente o SSH através da partição `bootfs` não resolveu imediatamente o problema.
- Foi necessário regravar o cartão microSD para recuperar uma instalação limpa e eliminar a incerteza causada pela possível corrupção de ficheiros.

##### Resultado do dia
- Não foram observados sinais imediatos de dano elétrico no Raspberry Pi, como fumo, cheiro a queimado, aquecimento rápido ou perda do LED vermelho de alimentação.
- O cartão microSD não ficou fisicamente danificado: continuou a ser reconhecido pelo computador e a partição `bootfs` permaneceu acessível.
- A falha de acesso foi associada a corrupção lógica ou perda da configuração do sistema, e não a uma avaria física confirmada.
- O Raspberry Pi OS foi regravado com sucesso.
- O hostname `sailsafe-pi`, o utilizador, o Wi-Fi e o acesso por SSH foram novamente configurados.
- O Raspberry Pi voltou a ficar preparado para acesso remoto.
- A alimentação através do circuito soldado ficou pendente de validação completa com o Raspberry Pi arrancado exclusivamente pela bateria e pelo conversor DC-DC.

##### Lições aprendidas
- O LED vermelho confirma a presença de alimentação, mas não garante, por si só, que a tensão esteja correta e estável.
- O LED verde pode piscar intensamente durante o arranque e apenas ocasionalmente depois, sem que isso represente necessariamente uma falha.
- Interromper a alimentação durante a atividade do cartão pode corromper o sistema de ficheiros sem danificar fisicamente o microSD.
- O cartão microSD deve ser regravado quando a instalação ainda não contém dados importantes e o estado do sistema fica incerto.
- A alimentação do Raspberry Pi deve ser validada de forma incremental, começando pelo Raspberry Pi isolado.
- Deve existir um procedimento de encerramento seguro antes de desligar fisicamente a alimentação.
- A validação visual dos LEDs deve ser complementada por verificações internas do sistema.

##### Próximo passo
- Confirmar o arranque e o acesso por SSH com alimentação USB-C.
- Encerrar corretamente o Raspberry Pi com `sudo poweroff`.
- Retirar completamente a alimentação USB-C.
- Arrancar o Raspberry Pi exclusivamente através da bateria e do conversor DC-DC.
- Confirmar que não existe nenhuma outra fonte ligada simultaneamente à linha de 5 V.
- Após o arranque, executar `vcgencmd get_throttled`.
- Confirmar que o resultado é `throttled=0x0`.
- Executar `uptime` para verificar se o Raspberry Pi não reiniciou.
- Consultar os registos de possíveis problemas de alimentação com `dmesg | grep -i -E "under-voltage|voltage|thrott"`.
- Manter o Raspberry Pi ligado durante 10–15 minutos e repetir as verificações.
- Só depois ligar o ESP32 por USB e repetir o teste de estabilidade da alimentação.

### 2026-07-15

#### Trabalho realizado
- Validação completa da alimentação do Raspberry Pi 4 através do conversor DC-DC ligado aos pinos GPIO.
- Execução de stress test (CPU 100%) para validação de estabilidade elétrica.
- Monitorização do estado de alimentação através de vcgencmd get_throttled.
- Confirmação de ausência de undervoltage e throttling durante operação sob carga.
- Configuração e validação do systemd para execução automática do software.
- Criação do serviço sailsafe.service em /etc/systemd/system/.
- Debug de erros de configuração do systemd:
  - Correção de paths inválidos (/etc/system vs /etc/systemd/system).
  - Correção do utilizador (pi → goncalo).
  - Correção do caminho do script Python.
- Integração inicial com GitHub:
  - Clonagem do repositório SAILSAFE para o Raspberry Pi.
  - Introdução do fluxo de deploy baseado em git (git pull).
- Diagnóstico de falha de execução do serviço:
  - Identificação de ausência de código no Raspberry Pi.
  - Identificação de inconsistência na estrutura do repositório.
- Revisão e refactor do código Python de controlo:
  - Implementação de retry automático da porta serial.
  - Tratamento de exceções na escrita e leitura.
  - Reconexão automática em caso de falha.
  - Tornar o código compatível com execução via systemd.

#### Decisões técnicas
- Utilizar systemd como mecanismo de execução automática do software no Raspberry Pi.
- Utilizar GitHub como fonte única de verdade para o código (deploy via git pull).
- Definir um ponto de entrada único para o sistema: software/main.py.
- Implementar robustez mínima no código antes de integração com hardware (retry + reconexão).
- Adiar implementação de udev rules para fixação da porta serial para fase seguinte.
- Manter potência de saída limitada (≈10%) para testes iniciais.

#### Problemas / limitações
- Estrutura do repositório GitHub inconsistente e não alinhada com o systemd.
- Ausência inicial do código no Raspberry Pi após reset do sistema.
- Dependência de path fixo (/dev/ttyUSB0) sem garantia de persistência.
- Possível ausência de dependências Python (ex: pyserial).
- Ausência de kill-switch físico/remoto (restrição já conhecida).
- Código ainda sem validação completa com hardware real (ESP32).

#### Resultado do dia
- Alimentação do Raspberry Pi validada sob carga máxima (sem throttling).
- systemd configurado corretamente e funcional ao nível de sistema.
- Pipeline de deploy (GitHub → Raspberry Pi) definido e operacional.
- Código Python atualizado para versão robusta compatível com operação contínua.
- Sistema global próximo de execução autónoma.

#### Riscos identificados
- Porta serial dinâmica (/dev/ttyUSB0 pode mudar após reboot).
- Falha de comunicação com ESP32 pode levar a ausência de controlo.
- Ausência de kill-switch mantém risco operacional em testes reais.
- Estrutura do repositório pode causar erros de integração futuros.

#### Próximo passo
- Confirmar estrutura final do repositório:
  - SAILSAFE/software/main.py
- Executar teste manual do script Python no Raspberry Pi.
- Validar funcionamento do serviço systemd (estado active running).
- Instalar dependências Python necessárias (pyserial).
- Testar comunicação real Raspberry Pi ↔ ESP32.
- Implementar udev rule para fixar a porta serial.

### 2026-07-16

#### Trabalho realizado
- Revisão crítica do plano de desenvolvimento com base em restrições logísticas (impossibilidade de receber encomendas durante duas semanas).
- Definição de estratégia de desenvolvimento em duas fases:
  - Semana fora: foco exclusivo em software e integração lógica.
  - Regresso: início da construção da estrutura mecânica com apoio especializado.
- Análise detalhada do sistema de segurança e decisão de adiar a implementação do kill-switch remoto baseado em RC.
- Introdução de uma solução temporária de segurança:
  - utilização de loop key XT90 como método de corte manual de energia.
- Revisão da arquitetura elétrica para acomodar a ausência de kill-switch remoto:
  - bateria → loop key → fusível principal → distribuição → ESCs.
- Planeamento da distribuição de fusíveis:
  - fusível principal (~80A estimado)
  - fusíveis individuais de 40A por ESC.
- Definição de política de testes para fase atual:
  - testes de motores apenas em bancada
  - potência limitada
  - sistema fisicamente contido
- Decisão de adiar aquisição de sistema RC (rádio + receiver) para fase posterior, por restrições de orçamento.
- Consolidação da estratégia de compras:
  - prioridade a conectores (XT90, XT60), fusíveis e solução de corte manual
  - adiamento de componentes não críticos para a fase atual.
- Planeamento detalhado do uso do tempo durante as próximas semanas:
  - desenvolvimento de software durante o período fora
  - desenvolvimento mecânico após regresso

#### Decisões técnicas
- Implementar loop key XT90 como solução de kill manual temporária.
- Adiar sistema de kill-switch remoto baseado em RC para fase posterior.
- Adiar aquisição de rádio e receiver devido a restrições de orçamento e ausência de necessidade imediata.
- Separar claramente fases de desenvolvimento:
  - Fase 1: software e integração lógica
  - Fase 2: estrutura e integração física
- Limitar testes de potência até existência de sistema de segurança mais robusto.

#### Problemas / limitações
- Ausência de conectores adicionais XT90 limita montagem elétrica completa.
- Impossibilidade de receber encomendas durante duas semanas impede avanço em subsistema de potência.
- Ausência de multímetro impede validação elétrica detalhada (tensão, continuidade, quedas).
- Ausência de kill-switch remoto limita segurança em testes com motores.
- Dependência de ferramentas e apoio externo para construção da estrutura.

#### Resultado do dia
- Estratégia global do projeto ajustada à realidade logística e financeira.
- Arquitetura elétrica simplificada e adaptada à fase atual.
- Plano de desenvolvimento para as próximas semanas claramente definido.
- Riscos principais identificados e mitigados dentro do possível.

#### Riscos identificados
- Dependência de corte manual de energia (loop key) como único mecanismo de segurança.
- Potencial erro de ligação elétrica sem instrumentação adequada.
- Possível atraso na integração de potência devido a falta de componentes.
- Risco de comportamento inesperado dos ESCs em cortes sob carga.

#### Próximo passo
- Finalizar software do Raspberry Pi:
  - garantir execução estável via systemd
  - implementar logging básico
  - integrar leitura da IMU
- Validar comunicação contínua Raspberry Pi ↔ ESP32.
- Preparar estrutura do código para integração futura do controlo (heading hold).
- Definir layout físico preliminar da estrutura antes da construção.
- Adquirir conectores e componentes elétricos assim que possível após regresso.

  
### 2026-07-17

#### Trabalho realizado
- Revisão do feedback técnico recebido sobre as prioridades imediatas do projeto: implementação de um corte físico independente, desenvolvimento de heading hold antes da navegação por waypoints e logging completo desde o início dos testes.
- Revisão da arquitetura de segurança da Fase 1, tendo em conta a indisponibilidade temporária de um kill-switch remoto.
- Definição de uma solução temporária de corte manual através de uma loop key com conector XT90.
- Definição da cadeia elétrica de segurança: bateria de propulsão → loop key XT90 → fusível principal → distribuição → fusíveis individuais → ESCs.
- Atualização do documento principal de arquitetura da versão v1.9 para v1.10.
- Adição da secção 10.1 — Arquitetura de Segurança Temporária — Fase 1.
- Adição de SAFE-007 para falha total do sistema, com corte manual imediato de energia através da loop key.
- Adição de TEST-011 para validar o comportamento do sistema durante a remoção da loop key.
- Adição de RISK-009, relativo ao possível comportamento imprevisível dos ESCs durante um corte de energia sob carga.
- Atualização de OPEN-008 para registar a loop key como solução temporária e manter o kill-switch remoto como requisito obrigatório antes de operação autónoma ou testes sem corda.
- Inclusão explícita da loop key no diagrama da arquitetura elétrica.
- Revisão do estado do fusível principal de 100 A.
- Definição do plano de desenvolvimento do software até 2026-07-26.
- Separação entre as funcionalidades que podem ser desenvolvidas sem hardware físico e as validações que dependem da chegada da loop key, GPS, ESCs e restantes componentes.
- Definição de uma abordagem baseada em fontes simuladas para desenvolver e testar o heading hold e a navegação por waypoints sem depender imediatamente do BNO055 ou do GPS físico.

#### Decisões técnicas
- Utilizar temporariamente uma loop key XT90 como meio manual de corte da alimentação da propulsão durante a Fase 1.
- Instalar a loop key entre a bateria de propulsão e o fusível principal, garantindo que a sua remoção desenergiza todo o circuito de potência dos ESCs.
- Manter o kill-switch remoto independente como requisito obrigatório antes de testes sem corda, operação autónoma ou operação afastada da margem.
- Não considerar a loop key como substituto definitivo do kill-switch remoto, uma vez que exige a presença física do operador e não permite corte à distância.
- Não energizar os ESCs antes de existir um meio físico, imediato e independente de cortar a alimentação.
- Não transportar os ESCs para os trabalhos de software enquanto não estiver prevista a sua energização; os ESCs poderão ser levados apenas para inspeção, identificação de ligações ou preparação da montagem.
- Manter os testes em água proibidos enquanto não existir um sistema de recuperação por corda, supervisão direta e potência limitada.
- Alterar o estado do fusível principal de 100 A de “confirmado” para estimativa baseada no dimensionamento teórico de dois ESCs de 40 A.
- Validar o valor definitivo do fusível principal apenas depois de existirem medições reais de corrente, incluindo picos de arranque e funcionamento simultâneo dos dois motores.
- Implementar e validar primeiro o heading hold, antes de avançar para a navegação por waypoints.
- Começar o heading hold com um controlador proporcional simples, adiando a utilização de PI ou PID até existirem dados físicos que justifiquem maior complexidade.
- Normalizar o erro angular do heading para o intervalo entre −180° e +180°, evitando erros durante a transição entre 359° e 0°.
- Separar as fontes de dados da lógica de controlo, permitindo utilizar heading e posição simulados enquanto o BNO055 e o GPS físico não estiverem disponíveis.
- Criar uma fonte de posição simulada para desenvolver o cálculo de distância, bearing, raio de chegada e transição entre waypoints.
- Identificar explicitamente todos os dados simulados como sintéticos, evitando apresentá-los como medições reais.
- Implementar o logging antes dos testes físicos dos ESCs e antes da validação da navegação autónoma.
- Criar um ficheiro CSV diferente para cada sessão, contendo timestamps, estado do sistema, modo de controlo, comandos, estado da comunicação, failsafe, heading, GPS e dados dos waypoints.
- Implementar uma máquina de estados com, pelo menos, BOOT, DISARMED, ARMED, RUNNING, FAILSAFE e ERROR.
- Garantir que o sistema inicia sempre em estado seguro e que os comandos de movimento são rejeitados enquanto o sistema estiver desarmado.
- Garantir que o regresso da comunicação após um failsafe não provoca movimento automático; deverá ser exigido um novo comando explícito de arming.
- Manter o comando STOP com prioridade absoluta sobre qualquer modo manual ou automático.
- Definir como objetivo para 2026-07-26 a conclusão do software MVP em bancada lógica e simulação, sem declarar ainda o sistema autónomo como fisicamente validado.

#### Problemas / limitações
- A loop key XT90 ainda não se encontra disponível, ficando prevista apenas para a semana seguinte.
- A ausência da loop key impede, por razões de segurança, a energização dos ESCs através da bateria de propulsão.
- O GPS físico ainda não se encontra disponível.
- A integração e calibração física do BNO055 não estão concluídas.
- O valor de 100 A do fusível principal ainda não foi confirmado através de medições reais.
- O comportamento dos ESCs durante a inicialização, arming, timeout, corte de energia e reposição da alimentação permanece por validar.
- O neutro real, a gama de comando e a resposta dos ESCs ainda não foram medidos.
- A afinação do heading hold não pode ser concluída apenas por simulação, pois dependerá da resposta física do barco, da inércia, dos waterjets, do vento e das condições da água.
- A navegação por waypoints poderá ser implementada com dados simulados, mas continuará pendente de validação com GPS físico e testes na água.
- O prazo até 2026-07-26 permite concluir o MVP de software, mas não permite garantir a validação física completa de todos os subsistemas que ainda não estão disponíveis.

#### Resultado do dia
- Documento principal de arquitetura atualizado e fechado como SAILSAFE Architecture v1.10.
- Arquitetura temporária de segurança com loop key XT90 definida e documentada.
- Limitações da solução temporária e condições obrigatórias para testes registadas formalmente.
- Estado do fusível principal corrigido para refletir que o valor de 100 A continua por validar experimentalmente.
- Decisão tomada de não energizar os ESCs antes da chegada da loop key ou da disponibilidade de outro meio de corte físico devidamente dimensionado.
- Confirmado que a ausência temporária da loop key e do GPS não bloqueia o desenvolvimento do software.
- Definida uma estratégia de desenvolvimento com GPS e heading simulados.
- Heading hold priorizado antes da navegação por waypoints.
- Logging definido como funcionalidade obrigatória antes dos testes físicos.
- Plano de trabalho estabelecido para concluir o software MVP até 2026-07-26.
- Validações físicas pendentes claramente separadas das funcionalidades implementáveis em simulação.

#### Lições aprendidas
- Um failsafe por timeout protege contra perda de comunicação, mas não cobre todos os modos de falha possíveis do software, ESP32 ou ESCs.
- Um botão STOP por software não substitui um corte físico independente da eletrónica de controlo.
- Uma solução temporária de segurança deve ter as suas limitações explicitamente documentadas, não podendo ser apresentada como equivalente à solução definitiva.
- “Implementado” e “validado fisicamente” são estados diferentes e devem ser registados separadamente.
- A ausência temporária de sensores ou atuadores não impede o desenvolvimento quando o software utiliza interfaces bem separadas e fontes simuladas.
- O heading hold deve ser validado antes dos waypoints, porque a navegação por GPS depende de um controlo de rumo estável e previsível.
- O logging deve ser desenvolvido antes dos ensaios físicos, para garantir que qualquer falha ou comportamento inesperado pode ser posteriormente analisado.
- Os dados sintéticos são adequados para testar a lógica, desde que sejam claramente identificados e não sejam confundidos com medições reais.
- A complexidade do controlador deve aumentar apenas quando os resultados experimentais demonstrarem essa necessidade.

#### Próximo passo
- Consolidar e congelar o protocolo de comunicação Raspberry Pi → ESP32.
- Rever o parser não bloqueante do ESP32 e confirmar a utilização de newline como delimitador.
- Implementar uma máquina de estados explícita no ESP32.
- Garantir arranque em DISARMED e rejeição de movimento antes de um comando ARM válido.
- Confirmar o funcionamento do keep-alive a 5 Hz e do timeout de comunicação.
- Garantir que STOP tem prioridade sobre todos os restantes comandos.
- Criar o sistema de logging por sessão no Raspberry Pi.
- Criar fontes simuladas de heading e posição.
- Implementar e testar a normalização do erro angular.
- Implementar o controlador proporcional inicial de heading hold.
- Desenvolver a gestão de waypoints utilizando posições sintéticas.
- Adiar a energização dos ESCs até à chegada da loop key e à preparação da cadeia de potência protegida por fusíveis.


### 2026-07-18

#### Trabalho realizado
- Configuração completa de autenticação SSH no Raspberry Pi para integração com GitHub.
- Geração de chave SSH (ed25519) e validação de autenticação sem password.
- Alteração do remote do repositório de HTTPS para SSH (git@github.com).
- Validação da ligação através de git fetch.
- Diagnóstico da ausência de ficheiros de comunicação (serial_link.py) no sistema local.
- Identificação de inconsistências entre repositório GitHub e diretório local.
- Execução de git pull para sincronização completa com o repositório remoto.
- Análise da estrutura resultante após sincronização.
- Identificação de estrutura incorreta no repositório:
  - pasta com nome inválido ("rasberry pi")
  - duplicação de diretórios (rasberrypi vs software/rasberry pi)
- Tentativas de reorganização manual do sistema de ficheiros.
- Identificação de erros recorrentes devido a:
  - typos nos paths
  - uso incorreto de nomes com espaços
- Localização correta do ficheiro serial_link.py dentro de:
  software/rasberry pi/
- Início do processo de refactor da estrutura de pastas para arquitetura modular:
  - raspberrypi/comms
  - raspberrypi/control

#### Decisões técnicas
- Utilizar exclusivamente SSH para operações Git no Raspberry Pi.
- Utilizar GitHub como fonte de verdade única para o código.
- Corrigir a estrutura do repositório antes de avançar com desenvolvimento.
- Adotar uma arquitetura modular:
  - comms (comunicação)
  - control (lógica de decisão)
  - main (orquestração)
- Eliminar nomes inválidos (espaços e typos) em diretórios.
- Priorizar consistência de naming como requisito de arquitetura.
- Adiar desenvolvimento de lógica de controlo até estrutura do projeto estar estável.

#### Problemas / limitações
- Estrutura do repositório inconsistente (pastas duplicadas e mal nomeadas).
- Presença de espaços em nomes de diretórios (ex: "rasberry pi") a dificultar comandos shell.
- Múltiplos typos nos paths (rasberry, rasberypi, rasberrpi).
- Dificuldade em localizar ficheiros devido a inconsistência estrutural.
- Confusão entre diretório local e conteúdo sincronizado do Git.
- Falta de disciplina inicial no versionamento (ficheiros fora do repo).
- Curva de aprendizagem do sistema de ficheiros Linux e comandos CLI.

#### Resultado do dia
- Sistema Git totalmente funcional via SSH.
- Ligação Raspberry Pi ↔ GitHub estabilizada.
- Repositório sincronizado com sucesso.
- Ficheiro serial_link.py confirmado no repositório.
- Problemas de localização de ficheiros diagnosticados.
- Identificada a causa raiz:
  - estrutura incorreta + naming inconsistente
- Plano claro para reorganização do projeto.
- Base estabelecida para modularização do software.

#### Lições aprendidas
- `git fetch` não atualiza ficheiros locais (necessário `git pull`).
- A estrutura do repositório é tão importante como o código.
- Espaços em nomes de diretórios criam fricção significativa.
- Pequenos erros de naming (typos) escalam rapidamente em sistemas reais.
- O Git não protege contra má organização — apenas versiona o estado atual.
- Debug de sistemas reais depende de inspeção direta (ls, find, pwd).
- AI não substitui visibilidade sobre o sistema real.
- Integração (filesystem + Git + código) é mais difícil que programação isolada.

#### Próximo passo
- Eliminar estrutura duplicada (remover rasberrypi manual).
- Renomear corretamente:
  software/rasberry pi → raspberrypi
- Remover pasta software após migração.
- Criar estrutura final:
  - raspberrypi/comms
  - raspberrypi/control
  - raspberrypi/logging
- Mover serial_link.py para raspberrypi/comms/.
- Validar execução do módulo de comunicação isoladamente.
- Fazer commit da nova estrutura limpa.
- Iniciar implementação de main.py.
- Integrar modelo throttle + steering.


### 2026-07-19

#### Trabalho realizado
- Estudo dedicado do centro de gravidade e da distribuição de peso (documento SAILSAFE_estudo_CG_distribuicao_peso_v1), com orçamento de massas por componente (posições x/z), hidrostática integrada da geometria v5 e comparação de quatro configurações.
- Quantificação do problema na configuração v5: pilha placa base → caixa de baterias → caixa IP66 com topo a ≈385 mm e z_G ≈ 142 mm (≈105 mm acima da linha de água; calado estático ≈37 mm).
- Avaliação das opções: B1 (pilha pousada no convés, −8 mm), B2 (caixa suspensa entre travessas, −24 mm), A (duas baterias alojadas nos cascos, −33 mm) e C (combinada, −42 mm teóricos).
- Cálculo do lastro equivalente: igualar a opção C com chumbo no fundo exigiria ≈2,7 kg (+46 % de massa, +19 % de área molhada); lastro rejeitado.
- Revisão da arquitetura elétrica para três circuitos independentes, sem cabos de potência a atravessar a ponte: por casco, LiPo 5000 → fusível 40 A → loop key XT90-S → ESC → waterjet; na caixa IP66, LiPo 2200 dedicada → fusível/interruptor → DC-DC 5 V → Raspberry Pi + ESP32 + sensores.
- Definição da estratégia de comunicação: Wi-Fi do Pi para desenvolvimento; recetor ExpressLRS 868 MHz (UART/CRSF) como elo de segurança planeado, com canal de três posições desarmado / autónomo / recall; LoRa/4G apenas como evolução posterior.
- Definição das regras de recall/RTH: na Fase 1, recall = paragem dos motores; na Fase 2, recall = Return-To-Home com posição de casa gravada no momento de armar, recusa de arming sem fix GPS e station-keeping à chegada; perda de ligação executa a mesma ação do recall.
- Atualização do documento principal de arquitetura de v1.10 para v1.11: nova secção 20, tabelas vivas (REQ, energia 5.2, BOM, Apêndice B), OPEN-003 fechado e OPEN-006/OPEN-008 atualizados.
- Geração do modelo CAD v6 em STEP (25 sólidos nomeados: cascos com alojamentos escavados, travessas, longarinas, escotilhas, baterias, caixa IP66, calços, transom inserts e waterjets).
- Verificação geométrica 3D com identificação de dois conflitos que o estudo em vista lateral não apanhou: o túnel entre cascos tem 118 mm e a caixa IP66 tem 155 mm de largura (a caixa não pode descer abaixo do convés); e o vão T1–T2 da v5 (133 mm) não recebe nem os alojamentos (165 mm) nem a caixa (204 mm).
- Consolidação do layout v6: T2 reposicionada para X = 485 (vão T1–T2 de 217,5 mm); alojamentos com interior 165×62, centros X = 341 e Y = ±123, fundo interior a z = 45; caixa IP66 pousada em quatro calços de 6 mm ao nível do convés (fundo a z = 152), retida por ripas nas faces de T1/T2; longarinas de convés divididas em dois troços por casco (interrompidas nas escotilhas).
- Recalculo com as cotas finais: z_G ≈ 107 mm (−35 mm vs v5), massa estimada ≈6,2 kg, calado ≈39 mm, x_G ≈ 474 vs LCB ≈ 456 (ligeiro caimento à popa, favorável à alimentação dos jatos).
- Emissão da blueprint madeira v6 (3 folhas: vistas de conjunto, lista de corte revista e detalhes dos alojamentos e do apoio da caixa), em substituição da folha v5.
- Definição prática do GND comum na nova topologia: referência exclusivamente pelos fios de GND das fichas servo dos ESCs até ao ESP32, num único ponto na caixa IP66; sense de tensão das duas baterias de propulsão por fio único de positivo com resistência de ≈10 kΩ na origem e divisor junto ao ADS1015.
- Definição construtiva das loop keys: fêmea XT90-S em série no positivo (ambos os fios da tomada são positivo), chave em macho com pinos em ponte de 12 AWG, montada em poço recortado no convés entre a escotilha e o ESC, com cordão e boia; fusível dentro do alojamento, junto à bateria.
- Definição da sequência de operação: eletrónica primeiro (ESP32 a emitir neutro), só depois inserir as chaves; desarme pela ordem inversa.

#### Decisões técnicas
- Adotada a opção C revista (v6) como arquitetura mecânica: duas baterias de propulsão alojadas nos cascos, eliminação da caixa de baterias e da placa base (peças 3–9 da lista de corte) e caixa IP66 ao nível do convés.
- Rejeitado o uso de lastro para baixar o centro de gravidade; reservados apenas 50–100 g para acerto fino do caimento após a pesagem real.
- Adotada a topologia de três circuitos elétricos independentes; a ligação em estrela entre negativos definida a 2026-07-11 fica sem efeito, substituída pela referência por GND de sinal.
- Adotados dois loop keys (um por casco) como corte manual, substituindo o loop key único na distribuição central; fusível principal de 100 A e bus bars eliminados (proteção por fusível de 40 A junto a cada bateria).
- Rejeitado o corte de energia por rádio com relé ou MOSFET no caminho de potência: num barco autónomo, o corte remoto correto atua no sinal (STOP/recall por software), porque um corte de energia em perda de ligação impediria o próprio RTH; interruptor de estado sólido comandado pelo ESP32 registado apenas como upgrade opcional futuro.
- Ligar o sense de tensão a jusante da tomada do loop, de modo a que a mesma medição indique também o estado armado/desarmado de cada casco; o modo autónomo deverá recusar arming com um casco desarmado.
- Manter as regras LiPo (18.4) estendidas aos alojamentos: forro de contraplacado selado (sem contacto do LiPo com o XPS), respiro no rebordo da escotilha, carregamento sempre fora do barco — agora com três baterias.
- TEST-011 passa a ser executado nos dois ramos de propulsão (remoção e inserção de cada chave, com verificação de ausência de movimento durante o arming).

#### Problemas / limitações
- Os ficheiros de arquitetura originais não estavam disponíveis na primeira sessão de análise; o estudo partiu da folha blueprint v5 e as massas da eletrónica são estimativas assinaladas, a substituir por pesagens reais.
- Erratas identificadas no estudo de CG entretanto emitido: a profundidade do alojamento é de 101 mm desde o convés (fundo a z = 45; onde se lê 55 mm) e a posição ótima teórica das baterias (x ≈ 270) não é construível — as restrições geométricas fixam x = 341.
- O z_G real da v6 (≈107 mm) é 7 mm pior do que o ótimo teórico da opção C (≈100 mm), por a caixa IP66 não poder descer abaixo do convés.
- A segunda LiPo 5000, as loop keys XT90-S, o recetor ELRS e o multímetro fiável continuam por adquirir; todos os valores de massa, calado e trim permanecem "estimados", não "validados".
- A descarga assimétrica das duas baterias de propulsão passa a ser um modo de degradação próprio da nova topologia; mitigação por saída com cargas iguais e compensação de trim por software, pendente de validação física.

#### Resultado do dia
- Arquitetura mecânica e elétrica revista e fechada como SAILSAFE Architecture v1.11, com cotas finais na blueprint madeira v6 e no modelo SAILSAFE_concept_v6.step.
- Centro de gravidade reduzido de ≈142 para ≈107 mm (−25 %) sem lastro, com trim longitudinal dentro do alvo e autonomia duplicada pela segunda bateria.
- Cadeia de segurança clarificada em três camadas: física (loop keys por casco), lógica (arming/recall por software e, futuramente, ELRS) e automática (failsafe por timeout e watchdog).
- Conjunto de documentos coerente entre si: estudo de CG, documento de arquitetura v1.11, blueprint v6 e STEP v6.

#### Lições aprendidas
- Um estudo em vista lateral não substitui a verificação geométrica 3D: dois conflitos de montagem (largura do túnel e vãos entre travessas) só apareceram ao modelar o conjunto.
- Mover massa para baixo é muito mais eficiente do que acrescentar lastro; o lastro paga-se em calado, área molhada e autonomia.
- Num sistema autónomo, o kill remoto pertence à camada de sinal, não à de potência: cortar energia à distância destruiria a própria capacidade de o barco voltar.
- Separar circuitos elimina classes inteiras de falhas (brownout do Pi, paralelo de baterias), mas cria modos novos (descarga assimétrica) que têm de ser monitorizados.
- O ótimo teórico de um cálculo deve ser sempre confrontado com as restrições construtivas antes de entrar na documentação.

#### Próximo passo
- Pesar todos os componentes reais (waterjets, ESCs, caixa IP66 equipada, baterias) e recalcular z_G e x_G com as fórmulas do estudo de CG antes de qualquer corte.
- Fazer a disposição à escala real no vão T1–T2 (escotilhas + caixa) para confirmar as folgas de 3 e 3,5 mm.
- Adquirir a segunda LiPo 5000, as loop keys XT90-S (fêmeas + machos para as chaves e uma sobresselente), o divisor de tensão e o multímetro.
- Atualizar o esquema elétrico KiCad para a topologia de três circuitos.
- Prosseguir o plano de software de 2026-07-17 (máquina de estados, logging, heading hold com fontes simuladas), agora com o estado armado/desarmado por casco lido pelo sense.

  ### 2026-07-20

#### Trabalho realizado
- Reescrita do `serial_link.py`: de script de teste (comando fixo 10/10 em loop) para classe reutilizável `SerialLink`:
  - nenhuma ação ao ser importado; nunca envia comandos por iniciativa própria;
  - `connect()` devolve True/False em vez de lançar exceção com o ESP32 ausente;
  - tratamento de exceções em escrita/leitura e STOP (0/0) garantido no fecho da porta;
  - protocolo textual `L: x R: y\n` mantido intacto.
- Teste do módulo com o ESP32 desligado: aviso limpo e saída sem traceback (cenário "ESP32 ausente sem crash" validado).
- Commit e push da alteração; upstream da branch develop configurado no Raspberry Pi.
- Correção da localização do `main.py`: movido de `software/` para `software/raspberry_pi/` com `git mv`.
- Reescrita do `main.py` para integrar o `SerialLink`:
  - abre a ligação série se o ESP32 existir e escuta telemetria;
  - tentativa de religação automática a cada 10 s;
  - mantém-se em DISARMED — nunca envia comandos de propulsão;
  - STOP + fecho da porta garantidos ao sair (SIGINT/SIGTERM).
- Teste do `main.py` sem ESP32: arranque limpo, tolerância à ausência da porta e encerramento seguro confirmados.
- Primeira ligação física do ESP32 ao Raspberry Pi nesta fase: deteção em `/dev/ttyUSB0`.
- Execução do `main.py` com o ESP32 ligado: ligação série ativa e encerramento limpo.
- Validação da comunicação bidirecional com comando STOP (0/0):
  - resposta do ESP32: `Left: 0% -> 1000 us | Right: 0% -> 1000 us`;
  - failsafe do firmware confirmado em condições reais (`FAILSAFE ATIVO - motores parados` após comando isolado).

#### Decisões técnicas
- O `serial_link.py` passa a ser um módulo passivo: quem decide o que enviar é o `main.py`; o único valor por defeito é o STOP.
- O `main.py` permanece DISARMED nesta fase; a validação com hardware foi feita apenas com escuta e STOP, sem comandos de propulsão.
- Testes realizados com o ESP32 alimentado exclusivamente por USB, sem potência aos motores.
- Confirmada implicação de design para a fase seguinte: o modo ARMED terá de enviar comandos periódicos (heartbeat), caso contrário o failsafe do ESP32 corta os motores.

#### Problemas / limitações
- ESP32 inicialmente ligado à porta USB-C do Raspberry Pi (entrada de alimentação, não porta de dados) — sem deteção; resolvido ao mudar para uma porta USB-A.
- O firmware do ESP32 não envia telemetria por iniciativa própria; responde apenas a comandos recebidos.
- Porta série ainda fixa em `/dev/ttyUSB0`, sem udev rule (pendente de fase anterior).
- Eco do terminal ao colar heredocs longos dificulta a confirmação visual; a validação passou a ser feita por execução (um ficheiro truncado daria `SyntaxError`).

#### Resultado do dia
- Cadeia de comunicação Raspberry Pi ↔ ESP32 validada ponta a ponta com o novo código modular.
- Failsafe do ESP32 confirmado com hardware real, como segunda camada de segurança independente do Pi.
- Dois commits publicados na branch develop: refactor do `serial_link.py` e integração no `main.py`.

#### Próximo passo
- Implementar a máquina de estados DISARMED/ARMED no `main.py`, com heartbeat periódico e transições explícitas e seguras entre estados.


### 2026-07-21

#### Trabalho realizado
- Implementada máquina de estados mínima DISARMED ↔ ARMED no `main.py`, com controlo por teclado em bancada (a=ARM, d=DISARM, s=STOP, q=sair).
- Adicionado heartbeat a 5 Hz no estado ARMED (comando 0/0), para manter o failsafe do ESP32 satisfeito sem mover os motores.
- Garantido arranque sempre em DISARMED; rejeição de ARM sem ligação série; STOP com prioridade absoluta; regresso/perda da ligação série nunca arma sozinho.
- Criado o módulo de logging `telemetry/logger.py` (classe `SessionLogger`): um ficheiro `session_<timestamp>.csv` por arranque, colunas `timestamp, event, state, detail`, escrita com flush imediato.
- Adicionado `logs/` ao `.gitignore` (dados de execução, não versionados).
- Integrado o `SessionLogger` no `main.py`: registo de BOOT, SERIAL, STATE, TX, RX, STOP, WARN e SHUTDOWN.
- Validação com hardware real (ESP32 por USB, sem potência aos motores): máquina de estados e logging testados ponta a ponta.
- Três commits publicados na branch `develop` (`9e9ede9`, `b04e118`, `20797b8`).

#### Decisões técnicas
- Heartbeat fixado em 5 Hz (200 ms), com folga larga sobre o timeout do failsafe do ESP32.
- No estado ARMED, o heartbeat envia 0/0 por agora, por ainda não existir fonte de propulsão; o objetivo desta fase foi validar o mecanismo, não mover motores.
- Logging definido com esquema genérico (`event`/`state`/`detail`) para acomodar futuros campos de heading, GPS e waypoints sem quebrar o formato.
- Logs mantidos dentro do projeto (`software/raspberry_pi/logs/`), fora do controlo de versões.
- Adotar daqui em diante o fluxo editar-no-PC → `git push` → `git pull` no Pi, abandonando a edição direta no Pi.

#### Problemas / limitações
- O terminal/SSH do Pi corrompeu repetidamente colagens de várias linhas (perda e substituição de caracteres), impedindo colar ficheiros via heredoc. Contornado com transferência em base64 partida em pedaços pequenos e verificada por hash — solução funcional mas lenta, a eliminar com o fluxo Git.
- O parser não-bloqueante ocasionalmente lê meia linha por ciclo, partindo mensagens do ESP32 em dois registos (ex.: `Right: 0%` e `-> 1000 us` separados); conteúdo correto, apresentação por limpar.
- Surge um `COMANDO INVALIDO` inicial (lixo no buffer quando a porta abre e o ESP32 reinicia); inofensivo, motores parados.
- Heartbeat a 0/0 apenas; sem controlo de propulsão real até existir loop key e cadeia de potência protegida.

#### Resultado do dia
- Máquina de estados DISARMED/ARMED operacional e validada com hardware, com as duas camadas de segurança (heartbeat + failsafe do ESP32) confirmadas a trabalhar em conjunto.
- Sistema de logging por sessão funcional, com timestamps ao milissegundo.
- Timeout do failsafe do ESP32 medido a partir dos logs: ≈ 1,1 s após o último comando — margem confortável face aos 200 ms do heartbeat.
- Cadência do heartbeat confirmada nos dados (~204 ms entre envios).

#### Lições aprendidas
- O logging paga-se sozinho: permitiu medir o timeout do failsafe e a cadência do heartbeat sem instrumentação extra.
- Uma máquina de estados só é segura se o estado seguro for o de arranque e se nenhum evento (perda/regresso de ligação) provocar movimento automático.
- Colar código via terminal não é fluxo de trabalho; a fonte de verdade em Git com `git pull` no destino evita corrupção e retrabalho.

#### Próximo passo
- Migrar o fluxo de desenvolvimento para editar no PC e sincronizar por `git pull` no Pi.
- Limpar o parser das linhas partidas e filtrar o `COMANDO INVALIDO` do arranque.
- Iniciar o heading hold com fontes de heading e posição simuladas (controlador proporcional), conforme o plano de 2026-07-17.
- Adiar a energização dos ESCs até à chegada da loop key e da cadeia de potência protegida por fusíveis.
