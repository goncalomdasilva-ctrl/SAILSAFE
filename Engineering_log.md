# Engineering log

A viabilidade do projeto SAILSAFE tem vindo a ser analisada desde fevereiro de 2026. Durante o período letivo, o foco esteve na exploração de opções de arquitetura, integração de subsistemas e definição dos principais requisitos técnicos.

Uma das tentativas iniciais incluiu o desenho de uma PCB para integração elétrica. Essa abordagem revelou-se inadequada para distribuição de potência, sobretudo pela ausência de planos de cobre e pela fase ainda inicial de experiência em desenho de PCBs. Ainda assim, essa tentativa foi útil para clarificar restrições do sistema e reforçar a decisão de adotar uma arquitetura elétrica mais conservadora e robusta.

Após várias iterações, foi definida uma arquitetura inicial suficientemente sólida para avançar para a fase de execução e validação experimental.

### 2026-07-05

#### Trabalho realizado

* Preparação inicial do código do ESP32 antes da chegada dos ESCs e do Raspberry Pi.
* Criação do esquema elétrico v1.

#### Problemas / limitações

* Curva de aprendizagem inicial do KiCad, com algum tempo necessário para compreender a ferramenta e estruturar corretamente o esquema.

#### Resultado do dia

* Base inicial de firmware preparada.
* Primeira versão do esquema elétrico concluída.

#### Próximo passo

* Refinar a arquitetura elétrica e continuar a consolidação da documentação principal.

### 2026-07-06

#### Trabalho realizado

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

#### Decisões técnicas

* O kill-switch físico/remoto foi identificado como requisito futuro, mas adiado por motivos de orçamento.
* Foi decidido não ligar ainda ESCs, motores ou baterias de potência antes da validação da comunicação Raspberry Pi → ESP32.

#### Problemas / limitações

* O KiCad não incluía vários módulos específicos necessários para o projeto, obrigando ao uso de conectores genéricos no esquema.
* O esquema elétrico ainda requer melhorias de representação, embora os pontos principais de arquitetura estejam definidos.
* A preparação inicial do Raspberry Pi exigiu adaptação de hardware disponível para configurar o microSD.

#### Resultado do dia

* O projeto ficou num estado técnico muito mais sólido em termos de arquitetura, documentação e preparação para testes de bancada.
* O Raspberry Pi ficou operacional e preparado para integração futura com sensores e comunicação com o ESP32.
* O projeto encontra-se a aguardar a chegada dos componentes para iniciar testes físicos.

#### Próximo passo

* Testar comunicação Raspberry Pi → ESP32 por USB.

### 2026-07-07

#### Trabalho realizado

* Iniciada a criação do repositório GitHub do projeto SAILSAFE.
* Definida a estrutura inicial para documentação pública do projeto.
* Preparado o conteúdo inicial do README e da organização de ficheiros.
* Estruturados assistentes de IA para apoio à documentação, organização de tarefas e maior consistência na escrita técnica.

#### Decisões técnicas

* Foi decidido começar com uma estrutura simples de repositório, suficientemente organizada para ser mantida sem fricção excessiva.
* A documentação pública será construída de forma incremental, em vez de tentar formalizar tudo de uma só vez.

#### Problemas / limitações

* Curva de aprendizagem inicial do GitHub e da lógica de repositórios.
* Ainda sem integração total dos ficheiros técnicos no repositório.

#### Resultado do dia

* O projeto passou a ter uma base inicial para documentação pública e portefólio técnico.
* Ficou definido um caminho mais claro para organizar arquitetura, software, hardware e registos de evolução.
* Os assistentes de IA passaram a integrar o processo como ferramenta de apoio à produtividade e revisão técnica, sem substituir validação própria.

#### Próximo passo

* Fazer upload da documentação principal, esquema elétrico, ficheiro 3D e código do ESP32 para o repositório.



### 2026-07-08

#### Trabalho realizado

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

#### Problemas / limitações

* Cabo USB inicial não suportava dados (sem deteção do ESP32).
* Uso de screen causava envio inválido de comandos (carácter a carácter).
* Diferença entre documentação e implementação (PWM vs percentagem).
* Parser inicial (readStringUntil) introduzia risco de bloqueio.
* Conflito de acesso à porta série ao usar simultaneamente screen e Python.

#### Decisões técnicas

* Manter arquitetura:

  * Raspberry Pi → controlo de alto nível
  * ESP32 → controlo em tempo real + failsafe
* Congelar protocolo atual:
comando textual em percentagem (L:x R:y + newline)
* Limitar output inicial a 0–30% para segurança em bancada.
* Usar keep-alive como mecanismo normal e failsafe como redundância.

#### Resultado do dia

* Cadeia de controlo RPi → ESP32 validada em bancada.
* Protocolo básico de comando e segurança funcional.
* Base sólida estabelecida para integração futura com ESCs e motores.

#### Próximo passo

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

### 2026-07-14

#### Trabalho realizado
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

#### Decisões técnicas
- Não alimentar simultaneamente o Raspberry Pi pela entrada USB-C e pelos pinos GPIO.
- Validar inicialmente o Raspberry Pi sem o ESP32, sensores ou outros periféricos ligados.
- Confirmar primeiro o funcionamento do Raspberry Pi através de uma fonte USB-C de confiança.
- Repetir posteriormente o teste com alimentação exclusiva através da bateria e do conversor DC-DC.
- Utilizar `sudo poweroff` antes de interromper fisicamente a alimentação, sempre que existir acesso ao sistema.
- Manter `vcgencmd get_throttled` como principal verificação interna da qualidade da alimentação.
- Adotar `throttled=0x0` como critério inicial de aceitação da alimentação pelo circuito do barco.

#### Problemas / limitações
- Durante o primeiro ensaio existiu receio de danificar o Raspberry Pi devido à alimentação direta pelos pinos GPIO.
- A alimentação foi interrompida antes de o sistema concluir o arranque e sem encerramento controlado.
- Após a interrupção, ocorreu provável corrupção de ficheiros ou da configuração do Raspberry Pi OS no cartão microSD.
- O Raspberry Pi deixou de ficar acessível por SSH e não apareceu de forma fiável na rede local.
- Alguns endereços IP encontrados respondiam a `ping`, mas recusavam ligações na porta 22, dificultando a identificação do Raspberry Pi.
- A tentativa de ativar manualmente o SSH através da partição `bootfs` não resolveu imediatamente o problema.
- Foi necessário regravar o cartão microSD para recuperar uma instalação limpa e eliminar a incerteza causada pela possível corrupção de ficheiros.

#### Resultado do dia
- Não foram observados sinais imediatos de dano elétrico no Raspberry Pi, como fumo, cheiro a queimado, aquecimento rápido ou perda do LED vermelho de alimentação.
- O cartão microSD não ficou fisicamente danificado: continuou a ser reconhecido pelo computador e a partição `bootfs` permaneceu acessível.
- A falha de acesso foi associada a corrupção lógica ou perda da configuração do sistema, e não a uma avaria física confirmada.
- O Raspberry Pi OS foi regravado com sucesso.
- O hostname `sailsafe-pi`, o utilizador, o Wi-Fi e o acesso por SSH foram novamente configurados.
- O Raspberry Pi voltou a ficar preparado para acesso remoto.
- A alimentação através do circuito soldado ficou pendente de validação completa com o Raspberry Pi arrancado exclusivamente pela bateria e pelo conversor DC-DC.

#### Lições aprendidas
- O LED vermelho confirma a presença de alimentação, mas não garante, por si só, que a tensão esteja correta e estável.
- O LED verde pode piscar intensamente durante o arranque e apenas ocasionalmente depois, sem que isso represente necessariamente uma falha.
- Interromper a alimentação durante a atividade do cartão pode corromper o sistema de ficheiros sem danificar fisicamente o microSD.
- O cartão microSD deve ser regravado quando a instalação ainda não contém dados importantes e o estado do sistema fica incerto.
- A alimentação do Raspberry Pi deve ser validada de forma incremental, começando pelo Raspberry Pi isolado.
- Deve existir um procedimento de encerramento seguro antes de desligar fisicamente a alimentação.
- A validação visual dos LEDs deve ser complementada por verificações internas do sistema.

#### Próximo passo
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


### 2026-07-22

#### Trabalho realizado
- Adotado o fluxo de trabalho baseado em Git: clonado o repositório no PC (via HTTPS), passando o desenvolvimento a editar-no-PC -> commit/push -> git pull no Pi, eliminando a transferência de código por base64 no terminal.
- Corrigido o parser série do lado do Pi: read_line passa a acumular bytes num buffer interno e só devolve linhas completas; connect faz reset_input_buffer para descartar o lixo de arranque do ESP32 (fim do COMANDO INVALIDO inicial).
- Implementada a lógica de controlo de rumo em control/heading.py: normalize_angle (intervalo -180..+180), heading_error (evita o salto 359<->0) e HeadingController proporcional com saturação.
- Implementado o mixer de propulsão em control/mixer.py: converte throttle + steer em comandos L/R, com saturação.
- Criada a fonte de heading sintética em control/sources.py (SimulatedHeading) e um ciclo fechado de simulação controlador -> mixer -> barco.
- Criados testes automáticos sem hardware (tests/test_heading.py, tests/test_mixer.py), incluindo o caso crítico do salto angular.
- Integrado o modo NAV na máquina de estados do main.py: em NAV, o heading hold gera comandos L/R (limitados a 30%) enviados ao ESP32, com a malha fechada pelo simulador; regista heading e comandos no CSV.
- Validação com hardware real na comunicação: NAV testado com o ESP32 ligado, com o rumo simulado a convergir de 0 para o alvo de 90 graus em ~7 s e os motores a estabilizarem em 20/20. O ESP32 aceitou todos os comandos.
- Auditoria de segredos ao repositório e ao histórico (limpa: sem chaves, passwords, IPs ou emails privados); adicionada LICENSE (MIT) com aviso de segurança.
- Fusão develop -> main; histórico reescrito para uniformizar o autor de todos os commits como Gonçalo Silva; push forçado e re-sincronização do Pi.
- Implementada a navegação por waypoints em control/navigation.py (haversine_m, bearing_deg, WaypointNav) com SimulatedBoat (posição + rumo) em control/sources.py e tests/test_navigation.py; ciclo fechado simulado a percorrer dois waypoints (100 m Norte + 100 m Este) validado no PC e no Pi.

#### Decisões técnicas
- Manter o desenvolvimento do heading hold em simulação: sem motores a malha não se fecha fisicamente; a fonte de dados fica separada da lógica para trocar o simulado pelo BNO055 real sem alterar o controlador.
- Reconciliar o teto de segurança: o Pi limita os comandos de NAV a 30%, alinhando com o PERCENT_MAX_SAFE imposto pelo ESP32.
- Manter o controlador proporcional puro (sem I/D), conforme decidido a 2026-07-17.
- Descartado o uso de um LLM para previsão de eficiência/consumo: é um problema de regressão numérica com estrutura física (modelo físico de energia + regressão sobre os logs + medição de corrente/tensão), não de linguagem.
- Passar a trabalhar diretamente na branch main (projeto solo; a develop cumpriu o seu papel durante a reestruturação).

#### Problemas / limitações
- Falha de importação no Pi por módulos escritos mas não commitados antes de se construir por cima deles; lição: commitar cada peça antes de depender dela.
- O ciclo fechado do NAV é sintético; a afinação real do controlador só será possível com motores e testes na água.
- O BNO055 ainda não está integrado nem calibrado; waypoints pendentes de GPS real.

#### Resultado do dia
- Fluxo de desenvolvimento profissional estabelecido (Git como fonte de verdade).
- MVP de navegação em simulação: heading hold + waypoints, integrado na máquina de estados e validado com comunicação real ao ESP32.
- Repositório público em ordem: main como branch principal, LICENSE, autoria uniformizada.

#### Lições aprendidas
- Separar fontes de dados da lógica de controlo permite desenvolver navegação sem sensores/atuadores reais.
- No fluxo Git, dependências têm de ser commitadas antes do código que as usa.
- Escolher a ferramenta pelo problema: previsão física pede modelo físico e dados medidos, não um LLM.

#### Próximo passo
- Ligar o WaypointNav ao modo NAV do main.py (bearing do waypoint como alvo do heading hold).
- Preparar a interface RealHeading para o BNO055 (teste de rodar à mão, sem motores).
- Adiar a energização dos ESCs e motores até à chegada da loop key e da cadeia de potência protegida por fusíveis.


### 2026-07-23

#### Trabalho realizado
- Revisão mecânica maior: produzido o blueprint em madeira v6.1 (5 folhas). Baterias alojadas dentro dos cascos (X=341, Y=+/-123, fundo z=45, ~6 mm acima da linha de água), eliminando a placa base e a caixa central de baterias. Caixa IP66 (204x155) pousada ao nível do convés (fundo z=152, topo z=252), com calços e ripas de retenção aparafusadas a T1/T2. Travessa T2 recolocada em X=485. Escotilhas 185x85 com reforço perimetral, junta de neopreno 3 mm, 6 insertos M4 de latão e parafusos de orelhas em nylon; compartimento não hermético com respiro (regra 18.4). Pele em contraplacado marítimo 3 mm; proa (X 0-200) laminada em fibra de vidro + epóxi; lista de materiais consolidada (folha 5).
- Correção geométrica da v6 verificada em 3D: o túnel entre cascos (118 mm) é mais estreito do que a caixa IP66 (155 mm), impedindo a caixa de descer abaixo do convés.
- Definidas as sequências de serviço das baterias (retirar chaves -> abrir escotilhas -> extração pela patilha -> carregar fora do barco) e de montagem (fechar tampas -> ligar eletrónica -> esperar neutro do ESP32 -> inserir chaves).
- Pesquisa sobre o kill-switch remoto: avaliada e descartada a hipótese de usar uma antena DVB TW25.
- Definição da arquitetura de logging e armazenamento de dados a bordo e em terra.
- Enquadramento do projeto como campo de treino para a cadeira de Algoritmos e Estruturas de Dados (AED).
- Análise de âmbito para futura câmara e sensores.

#### Decisões técnicas
- Kill-switch remoto: a antena DVB TW25 não serve (antena de receção de TV, banda UHF de broadcast; não transmite nem corta). A solução é um sistema RC de hobby (2,4 GHz) com failsafe do recetor a cortar a potência, ou um link LoRa com heartbeat; a antena tem de ser da banda do rádio escolhido. Mantém-se a loop key XT90 como corte manual temporário.
- Logging a bordo: ficheiro sequencial (CSV ou registos binários de tamanho fixo) com flush regular, sobre um buffer circular em array estático - sem base de dados e sem malloc em ciclo de tempo real. SQLite fica reservado para análise em terra.
- Confirmado que a navegação por waypoints é geometria + controlo (haversine, bearing, cross-track, PID de rumo), não algoritmos de grafos; pathfinding só entraria para zonas proibidas ou cobertura de área.
- Usar o projeto como aplicação prática da AED: buffer circular para amostras a alta frequência, lista ligada para a lista de waypoints da missão, structs + ponteiros para os registos.
- Câmara e sensores adiados para depois do núcleo. Se adicionada, a câmara grava a bordo e analisa-se em terra (sincronização vídeo-logs por timestamp; metadados em SQLite). Preferir geofencing por GPS à deteção de obstáculos por sensores.

#### Problemas / limitações
- PIR não funciona na água; ultrassons e ToF/laser comportam-se mal com ondas e reflexos; deteção de obstáculos em superfície é um problema difícil (câmara + visão), fora do âmbito atual.
- Processamento de vídeo em tempo real no Pi é proibitivo em CPU e consumo.
- Kill-switch remoto continua por resolver em hardware.

#### Resultado do dia
- Arquitetura mecânica consolidada na v6.1, com as baterias nos cascos e simplificação estrutural.
- Estratégia de dados clara: sequencial + buffer circular a bordo, SQLite em terra.
- Caminho do kill-switch remoto esclarecido (RC/LoRa, não antena de TV).

#### Lições aprendidas
- A estrutura de dados certa depende do padrão de acesso: array circular para fluxo contínuo, lista ligada para coleções pequenas e ordenadas editadas manualmente.
- malloc em ciclo de tempo real evita-se por princípio.
- Trabalho de bancada de alto valor sem ESCs nem motores: gravar dados reais do IMU/GPS e afinar o controlo contra dados gravados.

#### Próximo passo
- Ligar o WaypointNav ao modo NAV do main.py, fechando a navegação autónoma completa em simulação.
- Implementar o buffer circular de logging como exercício de AED.
- Definir o sistema de rádio para o kill-switch remoto (RC 2,4 GHz vs LoRa) e a cadeia de corte.
- Manter a proibição de energizar ESCs/motores até existir corte físico dimensionado.

### 2026-07-24

#### Trabalho realizado
- Adicionado `hardware/mechanical/SAILSAFE_concept_v6_2.step`: o modelo v6 (exportação real do Fusion) com aberturas de acesso às baterias cortadas nos dois cascos, para extração vertical dos packs 5000.
- Recorte por casco: janela retangular X 258.5-423.5, Y +/-90.5 a +/-155.5, do assento da bateria (z=45) através do convés (z=146). Deixa lábio de ~10 mm dentro da pegada da escotilha (185x85) para a tampa assentar; folga de 5 mm em X e ~8 mm em Y à volta do pack (155x48x35). Livre entre T1 e T2 (sem travessa por cima).
- Verificado programaticamente (OpenCASCADE): 25 componentes preservados com nomes originais; apenas casco_direito e casco_esquerdo alterados (-50 cm3 cada); janela do convés confirmada aberta (0 cm3 de material residual). Restantes 23 corpos idênticos em volume e bounding box.

#### Notas / limitações
- O corte foi feito por operação booleana sobre a geometria exportada; o ficheiro foi reescrito pelo kernel OpenCASCADE (cabeçalho deixa de ser "Autodesk Translation Framework") e não traz histórico paramétrico. Para versão 100% limpa com timeline, replicar o recorte no Fusion com as cotas acima e reexportar STEP.
- Mantido o `SAILSAFE_concept_v6_1.step` (esboço de caixas) no repo; substituição/remoção fica para decisão separada.

#### Efeito no CG
- As duas baterias 5000 (baixas, z 45-80, simétricas em Y, centradas em X~341) são as maiores massas removíveis. Retirá-las não induz adorno lateral (simetria) mas sobe o CG e desloca-o ligeiramente para a ré; reverificar trim com baterias fora.

#### Próximo passo
- Ligar o WaypointNav ao modo NAV do main.py (navegação autónoma completa em simulação).
- Confirmar as cotas de acesso à bateria contra o blueprint v6.1 e, se necessário, replicar o recorte no Fusion para o modelo mestre.

### 2026-07-25

(Sessão da noite de 25 para 26; os commits correspondentes ficam com data de 26.)

#### Trabalho realizado
- Revisão do esquema elétrico v1.11 durante a passagem do desenho para KiCad. Detetado um erro de dimensionamento no sense de tensão: com o divisor 10k/2k2 (k=0.180328), uma LiPo 3S carregada dá 2.272 V à entrada do ADS1015, acima do FSR por omissão de ±2.048 V. O limite de saturação referido à bateria é 11.36 V, ou seja toda a zona útil de descarga (12.6 → 11.4 V) lia saturado; a bateria pareceria cheia até já ir a meio da descarga.
- Correção adotada sem alterar hardware: PGA do ADS1015 em ±4.096 V (GAIN_ONE). Fundo de escala passa a 22.71 V de bateria, com resolução de 11.09 mV (3.70 mV por célula).
- Escrita a especificação `hardware/electrical/SAILSAFE_sense_v1_11_1.md`: tabelas de conversão, análise de erro, filtro, reserva de canais para corrente, alterações a fazer no KiCad e plano de verificação em bancada.
- Fechada a navegação autónoma em simulação: o modo NAV do `main.py` deixa de manter um rumo fixo de 90° e passa a seguir o bearing do waypoint atual, dado pelo WaypointNav. Era o ponto 1 da lista de próximos passos e o último item em falta do MVP de software.
- `main.py`: `SimulatedHeading` substituído por `SimulatedBoat` (o modo NAV precisa de posição, não só de rumo); acrescentada a missão de demonstração (dois waypoints, 40 m a Norte e depois 40 m a Este) e o raio de chegada de 4 m; removida a constante NAV_TARGET.
- Extraída a função `nav_step()`, um passo de navegação sem qualquer I/O: posição → bearing → heading hold → mixer → barco.
- Novo `tests/test_nav_mode.py` com 8 testes. Passam os 18 testes do projeto (heading 3, mixer 4, navigation 3, nav_mode 8).
- Verificado o ciclo fechado a 5 Hz: missão concluída em 619 passos (~124 s), com a viragem para o segundo waypoint a convergir em ~20 s.

#### Decisões técnicas
- Manter o divisor 10k/2k2 em vez de apertar para 10k/1k5: a resolução extra não se traduz em precisão real (o erro dominante são os resistores, não o ADC) e mantém margem para 4S — 16.8 V dá 3.03 V, dentro do FSR e do máximo absoluto de entrada (VDD+0.3 = 5.3 V).
- Resistores de sense especificados a 1 % metal film. A 5 % o erro seria ±1.07 V a 12.6 V, mais de um terço da janela útil de descarga.
- Calibração de um ponto por canal em software (multímetro → fator de escala em configuração), porque mesmo a 1 % o erro (±0.21 V) é ~19x pior que a resolução do ADC.
- Condensador de 1 µF em paralelo com o resistor inferior de cada divisor (fc = 88 Hz com Rsrc = 1.80 k), para rejeitar o ruído de comutação do ESC.
- Reservados A2/A3 do ADS1015 para ISENSE_E / ISENSE_D (ACS758LCB-050U, Hall isolado, 60 mV/A, 33 mA por conta). Sem corrente não há modelo de autonomia possível; os quatro canais ficam exatamente preenchidos.
- Fim de missão vai a DISARMED com `stop_motors()` explícito, em vez de ficar em ARMED. Zera a propulsão de forma ativa em vez de depender do timeout do failsafe, e não deixa o barco armado à espera; coerente com o princípio de estado seguro por omissão.
- Ao entrar em NAV a missão é recriada do início, a partir da posição atual do barco. Carregar em `n` reinicia sempre a missão, sem estado escondido de execuções anteriores.
- `nav_step()` devolve um namedtuple (left, right, bearing, dist, done, lat, lon), e a posição devolvida é a do instante da decisão e não a de depois do movimento, para o log registar aquilo sobre que o controlador decidiu.
- Testes incluem invariantes de segurança e não só convergência: comandos sempre em [0, 30] (sem marcha atrás, abaixo do teto do ESP32), missão concluída nunca devolve propulsão residual, e coerência entre NAV_THROTTLE, SAFE_MAX e o heartbeat face ao failsafe de ~1 s.

#### Problemas / limitações
- Com os quatro canais do ADS1015 ocupados não sobra entrada para monitorizar o próprio rail de 5 V. A saída do ACS758 é ratiométrica à sua alimentação e o ADS1015 mede contra referência interna, portanto oscilações do 5 V desviam a leitura de corrente. Compensação ratiométrica exigiria um segundo ADS1015 (endereço alternativo pelo pino ADDR).
- Liga-se ao pendente dos servos no rail de 5 V: se os servos ficarem nesse rail, os picos de corrente deles passam a contaminar também a leitura de corrente.
- Um dos testes falhou à primeira por erro do próprio teste (não registava a amostra de chegada ao último waypoint, dando 4.1 m contra um raio de 4.0 m). Corrigido no teste; a navegação estava certa.
- O modo NAV continua a exigir ligação série aberta para arrancar, por isso o ciclo principal completo não é testável sem ESP32; só `nav_step()` é que é. Limitação aceite, não defeito.
- Nada do sense está verificado em hardware: o ADS1015 e os sensores de corrente ainda não existem na bancada.
- Tudo na navegação continua sintético: sem GPS, sem BNO055, sem motores. O que está validado é a lógica, não o comportamento do barco na água.

#### Resultado do dia
- MVP de software concluído dentro do prazo que o próprio log tinha fixado para 2026-07-26: máquina de estados, heading hold, navegação por waypoints, logging e testes, tudo validado em simulação com comunicação real ao ESP32.
- Corrigido um erro de dimensionamento do sense que teria inutilizado a leitura de bateria sem dar sinal de avaria — leria sempre um valor plausível, só que errado.

#### Lições aprendidas
- Verificar sempre a gama de entrada de um ADC contra a configuração por omissão, e não só contra o máximo absoluto. O circuito estava eletricamente seguro e mesmo assim inútil: a saturação não queima nada, só mente.
- Num divisor resistivo, o erro dominante costuma ser a tolerância dos resistores e não a resolução do conversor. Vale mais gastar em 1 % e calibrar um ponto do que em bits.
- Um teste que falha não é necessariamente um defeito no código; desta vez o erro estava no próprio teste. Convém ler o que o teste mede antes de mexer naquilo que ele testa.
- Extrair a lógica para uma função sem I/O (`nav_step`) foi o que tornou o modo NAV testável sem hardware. O que depende de portas série e ficheiros não se consegue testar; o que é cálculo puro, sim.
- Começar a perceber o código já escrito antes de acrescentar camadas por cima. Definida a ordem de leitura de baixo para cima: mixer → heading → navigation → sources → logger/serial → main → firmware do ESP32.

#### Próximo passo
- Interface `RealHeading` para o BNO055 (teste de rodar à mão, sem motores), substituindo a fonte sintética de rumo sem tocar no controlador.
- Buffer circular de logging como exercício de AED.
- Aplicar no KiCad as alterações de sense: tolerância 1 % em R1..R4, condensadores de 1 µF nos dois divisores, nós ISENSE_E/ISENSE_D em A2/A3, e nota do PGA junto de U4.
- Exportar o STEP do Fusion para substituir o `SAILSAFE_concept_v6_1.step` (esboço de caixas) e decidir a sua remoção.
- Kill-switch remoto (RC 2,4 GHz vs LoRa) e cadeia de corte — continua a ser o bloqueio para qualquer ensaio na água.

### 2026-07-26

#### Trabalho realizado
- Modelo de conceito `SAILSAFE_concept_v6_3.step`: o v6_2 tinha só estrutura, baterias e waterjets. Acrescentados 16 sólidos com os componentes que faltavam — eletrónica dentro da caixa IP66, ESCs e motores nos cascos.
- Dentro da caixa (interior útil X 254,5..453,5 · Y ±75 · Z 154,5..252): `raspberry_pi_4` (85×56×20, sobre espaçadores de 8 mm), `esp32_devkit` (55×28×13), `bno055_imu` (20×27×5) sobre `suporte_BNO055`, `gps_modulo` (25×25×8) sobre `suporte_GPS`, `conversor_DCDC_5V` (65×35×20), `distribuidor_fusiveis` (60×40×30), `sensor_corrente` (31×13×15) e `ads1015` (25×18×4).
- Nos cascos: `esc_dir`/`esc_esq` (80×40×30) sob a longarina de ré, e `motor_dir`/`motor_esq` (cilindro Ø36×70) coaxiais com o waterjet, ligados por `veio_motor_*` (Ø5×20) até à admissão.
- `bateria_pi_2200` redimensionada de 120×60×30 (valor inventado) para 105×35×25 (LiPo 3S 2200 mAh real) e movida para a antepara de vante, atravessada — no sítio antigo colidia com o Raspberry Pi.
- Escrito `hardware/mechanical/tools/build_concept_v6_3.py`, que gera o v6_3 a partir do v6_2. Até agora os STEP do repositório não tinham gerador versionado; a partir daqui o modelo de layout é reproduzível.
- Escritos `tools/verify_concept.py` (integridade referencial, colisões AABB, folgas, CG) e `tools/validate_occ.py` (BRepCheck_Analyzer sólido a sólido). Resultado: 0 referências mortas, 0 ids duplicados, 41/41 sólidos válidos, 0 colisões entre componentes.
- Escrito `tools/make_layout_svg.py` e gerado `SAILSAFE_layout_v6_3.svg`: vista de cima e vista lateral com legenda numerada, para rever o arranjo sem abrir CAD.

#### Decisões técnicas
- Não gerar B-rep de raiz. Sem kernel CAD garantido (CadQuery/OCP não instala de forma fiável), o gerador clona a topologia de dois sólidos já válidos do próprio ficheiro — `calco_IP66_1` para caixas e `waterjet_dir` para cilindros — e aplica-lhes uma transformação afim por eixo. Como os moldes estão alinhados aos eixos, a transformação preserva a validade, desde que as *pcurves* sejam reescaladas com os fatores dos eixos locais de cada superfície (para o cilindro, u é ângulo e não escala; v é distância axial e escala).
- GPS no topo e a vante, ~70 mm do Raspberry Pi. O Pi 4 é uma fonte conhecida de ruído perto de 1,5 GHz; encostar o módulo GPS ao Pi degrada a receção. O suporte tira-o também do plano dos cabos de potência.
- BNO055 sobre coluna, ao centro em Y e a meio do comprimento, longe da eletrónica de potência. Como é magnetómetro, interessa afastá-lo dos condutores de corrente elevada e das baterias.
- ESC a z 104..134, 2 mm abaixo da longarina de ré. A primeira tentativa (z 116..146, encostado ao convés) atravessava a longarina — apanhado pelo verificador de colisões, não a olho.
- Componentes modelados como envelopes com folga, não como modelos de fabricante. O objetivo é decidir arranjo e confirmar que cabe, não desenhar suportes.
- Manter as LiPo 4S 5000 mAh nos cascos (155×48×35 já era realista) em vez de as passar para a caixa: baixam o CG e libertam a caixa para a eletrónica.

#### Problemas / limitações
- CG estimado em X = 468 mm, ou seja 58 % do comprimento a contar da proa, com massa total ~11,6 kg. Está deslocado para ré: motores, waterjets, ESCs e transom insert somam ~2,5 kg concentrados no último quarto. Provoca trim de popa; a correção natural é passar as LiPo 5000 mAh para vante nos cascos, que é a massa maior e a mais fácil de mover.
- O `caixa_IP66` do modelo é um tabuleiro aberto (paredes de 2,5 mm, sem tampa). As folgas verificadas são ao interior do tabuleiro; a altura livre real fica menor quando houver tampa e vedante.
- A `cobertura_ESC_*` continua a ser um bloco maciço no modelo, por isso o ESC aparece "dentro" dela em corte. É limitação da representação, não do arranjo.
- Sem cablagem, bucins, suportes de motor nem furação. O veio motor–waterjet é um cilindro reto: não há acoplamento nem chumaceira modelados, e é aí que o alinhamento real vai doer.
- Todas as dimensões dos componentes que ainda não existem (ESC, motores, GPS) são valores típicos de catálogo. Quando as peças chegarem, medir e voltar a correr o gerador.

#### Resultado do dia
- O modelo de conceito passou a responder à pergunta que interessa antes de comprar: cabe tudo, e onde. Sobram ~68 mm à ré do Pi e ~45 mm à proa dentro da caixa, com o pior aperto em +X no distribuidor de fusíveis (5,5 mm).
- Ficou uma cadeia reprodutível: gerar → verificar colisões e folgas → validar sólidos → desenhar. Um erro de arranjo (ESC contra a longarina) foi apanhado por script e não por inspeção visual.

#### Lições aprendidas
- Um modelo de layout com colisões verificadas por script vale mais do que um render bonito. As duas colisões deste dia não se viam na vista de cima.
- Quando não há a ferramenta certa, clonar geometria já válida e transformá-la é mais seguro do que escrever B-rep à mão: herda-se a topologia correta e só há que acertar coordenadas.
- Um valor "provisório" num modelo (a bateria de 120×60×30) sobrevive muito para lá do provisório e depois choca com o resto. Vale a pena pôr dimensões reais assim que se souberem.

#### Próximo passo
- Passar as LiPo 5000 mAh para vante nos cascos e voltar a correr o cálculo de CG, com objetivo de 45–50 % do comprimento.
- Interface `RealHeading` para o BNO055 (teste de rodar à mão, sem motores).
- Buffer circular de logging como exercício de AED.
- Exportar o STEP do Fusion e decidir a remoção do `SAILSAFE_concept_v6_1.step`.
- Kill-switch remoto (RC 2,4 GHz vs LoRa) e cadeia de corte — continua a bloquear qualquer ensaio na água.

### 2026-07-26 (sessão 2 — apresentação e correções cruzadas)

#### Trabalho realizado
- Análise estruturada de todo o material do projeto (STEP v6_3, arquitetura v1.11, layout SVG), com assistência de IA, e relatório de Fase 0: confirmado vs. estimado vs. em falta, contradições entre documentos, e lista priorizada de melhorias visuais.
- Primeira versão do site do projeto: visualizador 3D interativo (three.js) com o modelo reconstruído a partir do STEP, toggles por subsistema, ficha técnica por componente ao clicar, corte longitudinal, linha de água ao calado derivado e vista explodida. Conteúdo bilingue PT/EN. Versão de ficheiro único (`website/SAILSAFE.html`) que abre por duplo clique, e versão modular preparada para GitHub Pages.
- Esquema elétrico v1.11 cruzado com o site e com a arquitetura: detetadas e corrigidas três divergências no conteúdo publicado.
- Modelo `SAILSAFE_concept_v6_4.step` gerado com o motor de clonagem do `build_concept_v6_3.py`: 50 sólidos novos que decompõem os envelopes em geometria reconhecível — Raspberry Pi 4 (13 sólidos: GPIO, USB, RJ45, SoC), ESP32 (8), GPS (4), BNO055 (3), waterjet com admissão/grelha/estator/tubeira/bocal orientável (7 por lado) e servo do bocal (4 por lado). Duto do waterjet da v6_2 reescalado para X 735..793 para dar lugar ao detalhe a jusante.
- `verify_concept.py` sobre o v6_4: primeira passagem acusou 19 colisões do detalhe contra o duto original; anatomia reorganizada até zero colisões. Envelope preservado (815×350×252). Uma colisão era real: o conector CSI contra a RAM do Pi — RAM deslocada em Y como na placa verdadeira.

#### Decisões técnicas
- O site marca cada valor com a proveniência (validado / estimado / derivado / em aberto), mantendo o estatuto que os números têm na documentação — nenhum valor de desempenho é apresentado como medição.
- Divergências fechadas a favor do esquema elétrico, por ser o documento mais recente: bateria da eletrónica é 2S 2200 (não 3S); arquitetura de três circuitos independentes sem fusível principal de 100 A nem bus bars (40 A por casco + 10 A eletrónica, nenhum cabo de potência atravessa a ponte); manobra combina diferencial com bocal orientável por servo (SRV_E/SRV_D) — marcada "em aberto" porque o firmware ainda só tem os dois ESCs.
- Componentes detalhados gerados a partir das cotas dos desenhos mecânicos públicos, não de CAD de terceiros — evita problemas de licença no repositório.

#### Problemas / limitações
- O `verify_concept.py` rebenta no cálculo de folgas com o v6_4 (procura os nomes antigos `raspberry_pi_4` etc., agora decompostos em `rpi4_*`); a verificação de colisões corre completa antes disso.
- O firmware não tem saídas de servo; o esquema tem M3/M4. Divergência registada, por resolver no código.

#### Resultado do dia
- Projeto passou a ter apresentação: relatório de análise, site interativo e modelo com componentes reconhecíveis, tudo coerente com a documentação e com as divergências documentais identificadas e corrigidas.

#### Lições aprendidas
- Cruzar o esquema elétrico com o documento-mãe apanhou três divergências que nenhum dos documentos denunciava sozinho. A validação entre documentos vale tanto como a validação dentro de cada um.
- O verificador de colisões voltou a pagar-se: 19 sobreposições na primeira passagem do detalhe, uma delas um erro real de posicionamento (CSI vs. RAM).

#### Próximo passo
- Adaptar o cálculo de folgas do `verify_concept.py` aos nomes decompostos do v6_4.
- Acrescentar as saídas SRV_E/SRV_D ao firmware do ESP32 ou reverter o esquema, para eliminar a divergência.

### 2026-07-27

#### Trabalho realizado
- Site reescrito como viagem imersiva: panorâmica equirectangular como céu esférico 360º em que a câmara roda de verdade, cinco capítulos guiados pelo scroll (navegação → jatos → casco → praia → interior), arrasto livre para olhar à volta e marcadores ancorados às peças 3D que abrem a ficha técnica de cada componente.
- No capítulo do interior, a caixa IP66, escotilhas e coberturas desvanecem para expor a eletrónica — transição de cenário (mar → areia) por crossfade entre panorâmicas com movimento de câmara.
- Pipeline HDR: escrito leitor de Radiance RGBE de raiz (o imageio colapsava para 8 bits) com tone mapping ACES e exposição automática pela mediana. Convertida uma HDRI CC0 de praia (Poly Haven, 4096×2048) e geradas duas cenas da mesma imagem — dia e fim de tarde (−2 EV, tom quente) — eliminando a panorâmica anterior de 1024 px e a foto com marca de água de origem desconhecida.
- Jato dos waterjets refeito três vezes até ficar aceitável: partículas soltas → núcleo aditivo (parecia uma lanterna) → tubo de água opaco com transmissão/clearcoat/IOR 1,33, dobrado por frame ao longo de parábola balística, com salpicos a nascer no ponto de impacto na água.
- Controlo do palco iterado com feedback de utilização: sensibilidade final ~3× a inicial, zoom por roda removido (roubava o scroll da página), câmara fica onde o utilizador a deixa, botão de repor vista.
- Rotação base do céu calculada analiticamente (R = −az − 2πu, com a água da enseada a u≈0,475 → 2,705 rad) para o barco flutuar na água da fotografia e não sobre a areia.

#### Decisões técnicas
- Sem geração de imagens disponível, a qualidade do fundo fica limitada à resolução da fonte: 4096 nativos na versão GitHub Pages, 2560 embutidos no ficheiro único (3,9 MB). HDRI de 8/16K do Poly Haven ou panorâmica própria de telemóvel como caminho de melhoria.
- Água sem blending aditivo em nenhum elemento — água reflete e transmite, não emite.

#### Problemas / limitações
- O jato ainda é uma aproximação (tubo + salpicos); não há simulação de fluido nem espuma de impacto persistente.
- O ambiente de teste não tem WebGL: a validação visual continua a depender de abrir o ficheiro no browser real.

#### Resultado do dia
- Site com movimento legível (é o cenário que passa), fundo fotográfico ao nível da fonte, jatos com comportamento de água e controlo de câmara utilizável. Onze iterações de ficheiro único até à v11.

#### Lições aprendidas
- Movimento sem referência visual não se lê: o barco "andava" mas o fundo fixo anulava a perceção. Rodar o cenário resolveu o que aumentar a velocidade não resolvia.
- Blending aditivo é para luz, não para água. O mesmo efeito com material físico (transmissão + clearcoat) muda a leitura por completo.
- Em UX de scroll, qualquer elemento que capture a roda do rato compete com a navegação da página — interação de câmara deve ficar no arrasto.

#### Próximo passo
- Panorâmica própria (rio) para substituir a HDRI genérica; conversor pronto em `website/hdr2jpg.py`.
- Publicar no GitHub Pages com as panorâmicas de 4096 externas.
- Fase 2 do interior: cablagem gerada a partir da netlist do KiCad e transições de câmara por subsistema.

### 2026-07-27 (sessão 2 — wash dos jatos, fundo e preparação de publicação)

#### Trabalho realizado
- Wash dos waterjets refeito a partir de fotografia de referência de uma embarcação a jato real: em vez de "tubo de água", espuma branca arejada em três camadas — cadeia de sprites de espuma ao longo da parábola balística do jato, planos de wash junto à superfície com textura a rolar no sentido do escoamento, e partículas de salpico no ponto de impacto. Tudo com blending normal (regra mantida: água não emite luz).
- Fundo fotográfico abandonado em definitivo. Duas tentativas de manter a foto fixa alinhada com a câmara 3D (deslocamento de `backgroundPosition` com o tilt; projeção do horizonte 3D sobre o da foto) falharam pela mesma razão de fundo: uma fotografia é um ponto de vista fixo e a câmara do palco é livre — qualquer rotação lê-se como "a água mexeu-se", não como "eu mexi-me".
- Substituído por gradiente CSS uniforme, como na primeira versão do site. Sem paralaxe não há nada que traia o movimento da câmara. Após teste, o céu branco inicial foi suavizado para azul-cinza (#a9c3d6 → #b9c9cd) por encandear.
- Mantida uma panorâmica pequena (92 kB) apenas como environment map, para os reflexos na água e no casco não morrerem com a saída da fotografia.
- Criado workflow de deploy no GitHub Actions (`.github/workflows/deploy-site.yml`): publica a pasta `website/` no GitHub Pages e só dispara quando há alterações em `website/**`.
- Rebuild final do ficheiro único `SAILSAFE.html` (1,72 MB) e sincronização de todos os ficheiros para o repositório.

#### Decisões técnicas
- Fundo neutro em gradiente em vez de fotografia: menos espetacular parado, mas coerente em movimento — o realismo percebido depende mais da consistência do que da resolução do fundo.
- O environment map fica desacoplado do fundo visível: os reflexos continuam fotográficos com o céu em gradiente.

#### Problemas / limitações
- O wash continua a ser uma aproximação por sprites; sem simulação de fluido, a espuma não interage com a ondulação da água.
- O site nunca foi renderizado num telemóvel real — media queries e LOWQ estão validados apenas por inspeção de código.

#### Resultado do dia
- Palco visualmente estável: jatos com aspeto de wash real, fundo que não compete com o movimento da câmara, repositório pronto para commit, push e ativação do GitHub Pages.

#### Lições aprendidas
- Fotografia de fundo fixa é incompatível com câmara livre; ou o fundo é 360º (panorâmica esférica) ou é neutro. Meio-termo não existe.
- Vale a pena separar o papel visual de um asset (fundo) do papel de iluminação (envmap) — remover um não obriga a perder o outro.

#### Próximo passo
- `git add -A && git commit && git push`; ativar Pages (Settings → Pages → Source: GitHub Actions) e verificar o site publicado, sobretudo no telemóvel.

### 2026-07-28

(Sessão da noite de 28 para 29; os commits correspondentes ficam com data de 29.)

#### Trabalho realizado
- Fechada a arquitetura do kill-switch remoto, que estava em aberto desde a v1.10 (OPEN-008). Corte por relé na linha positiva de cada casco, a jusante do fusível e da loop key, comandado por um canal PWM de rádio que não atravessa o Raspberry Pi nem o ESP32.
- Verificado no modelo v6_4 que a abertura de acesso às baterias sobreviveu às revisões v6_3/v6_4 (0 cm³ de material na janela do convés nos dois cascos) e que nada obstrui a extração vertical além da própria escotilha.
- Medido em simulação o desequilíbrio de trabalho entre cascos em quatro missões: 0,0 % em linha reta, −1,6 % em ziguezague, +8,9 % na missão de demonstração e +13,6 % num quadrado com viragens todas do mesmo lado.
- Calculada a autonomia comparada das baterias em função do tempo a andar, e reatribuídos os quatro canais do ADS1015.
- Confirmada fisicamente a bateria da eletrónica como LiPo 3S 2200 mAh.
- Corrigidos os três sítios do site publicado que indicavam 2S 2200 (`website/assets/js/data.js` ×2 e `i18n.js`).
- Produzido `docs/SAILSAFE_Architecture_v1_12.docx` (nova secção 21, histórico e tabelas de decisões e BOM actualizados) e revista a especificação `hardware/electrical/SAILSAFE_sense_v1_11_1.md` para a revisão 2.
- Levantada e orçamentada a lista de compras; escolhido o caminho de menor custo para o rádio.

#### Decisões técnicas
- O corte remoto atua no POSITIVO, nunca no negativo. O negativo de cada casco é a referência de massa e o seu único caminho até à massa da eletrónica é o fio preto da ficha servo do ESC; cortá-lo obrigaria a corrente de retorno a passar por um fio dimensionado para miliamperes.
- Hierarquia de proteção fixada em fusível (40–50 A) < relé (60–70 A) < cabo (6 mm²). O fusível tem de ser o elo mais fraco por ser o único componente desenhado para falhar de forma controlada. Descartada a hipótese de dimensionar o fusível também a 60–70 A por simetria com o relé: nesse caso deixaria de proteger o ESC de 40 A, que arderia sem o fusível chegar a atuar.
- Bobinas dos relés alimentadas pela bateria do próprio casco, a montante dos contactos: alimentá-las pela bateria da eletrónica custaria ~35 % da autonomia desta (1,9 h → 1,3 h), contra 4–6 % por missão quando saem do casco.
- Um módulo RC-switch por casco, não um partilhado: um só módulo obrigaria a corrente das bobinas a atravessar a ponte pela massa da eletrónica e criaria um ponto único de falha a comandar os dois cascos. Um único canal do recetor comanda ambos.
- O caminho do kill não passa por software do projeto. O PWM do ESP32 é gerado pelo periférico LEDC, em hardware: se o firmware encravar sem reiniciar, o sinal mantém-se com o último valor e o failsafe de software nunca chega a correr.
- Loop keys XT90-S mantidas e não substituídas pelo corte remoto. Respondem a perguntas diferentes: a chave garante que é seguro pôr as mãos junto aos jatos, o rádio garante que o barco pára à distância. Descartada a ideia de as accionar por cordel — o XT90 tem vários quilos de retenção e não é um cordão de emergência; a extração das baterias faz-se pela escotilha.
- Corte apenas de um polo: cortar um já isola a bateria por completo, e cortar o segundo acrescentaria um contacto a mais para arcar ou corroer sem ganho de segurança.
- Sense reatribuído a três tensões (dois cascos e eletrónica) e uma corrente. Um divisor custa cêntimos e um sensor de corrente custa euros, logo o recurso escasso é o canal e não o componente.
- Divisores passam a 5k/1k, aproveitando resistores já disponíveis. Condensador de filtro sobe para 2,2 µF porque a impedância de fonte desceu de 1,80 kΩ para 833 Ω.
- A bateria da eletrónica passa a gatilho de regresso, e não apenas a mostrador.

#### Problemas / limitações
- Com 5k/1k, o limite de saturação no FSR por omissão sobe para 12,29 V — ainda abaixo de uma 3S carregada. A troca de divisor não dispensa a configuração do PGA para ±4,096 V.
- **Revertida a decisão de 07-26.** Nessa sessão a divergência sobre a bateria da eletrónica foi fechada a favor do esquema elétrico (2S 2200), por ser o documento mais recente. Estava errado: a bateria física é 3S 2200, e as secções 5.2 e 17.6 do documento de arquitetura, mais antigas, é que estavam certas. Critério corrigido para o futuro: perante documentos em conflito sobre uma peça física, verifica-se a peça e não a data do documento.
- O esquema elétrico v1.11 indica 2S 2200 mAh para a eletrónica quando a bateria real é 3S 2200 mAh. As secções 5.2 e 17.6 do documento de arquitetura já indicavam 3S, portanto o erro está no esquema. Correção pendente no KiCad.
- Continua sem sobrar canal para monitorizar o rail de 5 V, do qual a saída do ACS758 é ratiométrica.
- O casco direito fica sem medição de corrente até haver segundo ADS1015.
- Um jato obstruído no casco não instrumentado não é detetado diretamente; só indiretamente pela queda de tensão.
- Orçamento por fechar. Apenas o recetor ELRS ER6 tem preço confirmado (29,90 €, distribuidor europeu); as restantes rubricas assentam em ordens de grandeza e carecem de cotação antes de encomendar.
- Nada disto está verificado em hardware: continuam em falta ESCs, motores, GPS, relés e rádio.

#### Resultado do dia
- A última decisão estrutural em aberto desde a v1.10 ficou fechada, e com ela o caminho para ensaios na água sem corda deixa de estar bloqueado por indefinição de arquitetura — passa a estar bloqueado apenas por compras.
- Identificada uma inversão de prioridades que estava errada desde o início: a bateria pequena, e não as de propulsão, é o recurso crítico do sistema.

#### Lições aprendidas
- Duas baterias não se comparam pela capacidade mas pelo relógio a que se gastam. Uma consome-se com o tempo, a outra com a distância, e por isso a mais pequena pode ser a que limita a missão.
- Em cadeias de proteção, cada componente é dimensionado por um critério diferente e em sentidos opostos: o fusível pelo mínimo que protege, o relé e o cabo pelo máximo que suportam. Aplicar o mesmo número a todos anula a proteção.
- Segurança encaminhada através de um sistema que pode falhar não é segurança. O corte de emergência tem de ser independente daquilo de que desconfia.
- Peças que parecem alternativas podem responder a perguntas diferentes. A loop key e o corte remoto não competem: uma protege as mãos, a outra protege o barco à distância.
- Documentos que se contradizem entre si custam mais a descobrir do que um erro isolado. Convém confrontar o esquema com o documento-mãe sempre que se toca num valor.

#### Próximo passo
- Confirmar na ficha do ESC escolhido o comportamento ao perder sinal (OPEN-010), porque determina se um corte ao nível do sinal seria sequer admissível.
- Decidir o sistema de rádio (OPEN-011) e encomendar.
- Corrigir o esquema elétrico no KiCad: 3S 2200 mAh, três divisores 5k/1k, condensadores de 2,2 µF, nota do PGA junto de U4.
- Interface `RealHeading` para o BNO055, ainda por fazer.
- Buffer circular de logging como exercício de AED.
- Modo manual com comando de consola ligado ao Raspberry Pi, como forma de exercitar o código e pilotar em ensaios próximos sem depender do rádio.

### 2026-07-29

#### Trabalho realizado
- Escrito `control/real_heading.py`: leitor de rumo real do BNO055 com a mesma interface `read()` do `SimulatedHeading`, mais o tratamento de tudo o que a fonte simulada nunca teve de tratar (calibração NDOF, ausência de solução de fusão, I2C em baixo, offset de montagem, declinação magnética).
- Escrito `tools/heading_bench.py`: ensaio de "rodar à mão". Não abre a série nem fala com o ESP32; calcula e imprime os L/R que o mixer daria, sem os enviar. Tem modo `--fake` para exercitar o ecrã sem hardware.
- Escritos 13 testes em `tests/test_real_heading.py`, todos com driver falso e sem hardware. Os 18 testes anteriores continuam a passar.
- Arquivadas 10 versões antigas de CAD em `hardware/mechanical/archive/`, com README a explicar o que está lá e o que deliberadamente não está.
- Corrigido `tools/README.md`, que ainda dava o v6_3 como modelo corrente e não listava o `build_concept_v6_4.py`.

#### Decisões técnicas
- **O `RealHeading` levanta exceção em vez de devolver um número.** Um sensor descalibrado não dá erro: dá um valor plausível e errado, que é pior do que a ausência de valor, porque a ausência obriga a decidir e o valor errado não. `HeadingUnavailable` força o chamador ao estado seguro, como já acontece com a perda de série.
- Calibração como condição de segurança e não como mostrador: exige-se `sys >= 3` **e** `mag >= 3`. O `sys` sozinho não basta e há um teste dedicado a isso. Com o I2C em baixo, `calibration()` devolve `(0,0,0,0)` — falha para o lado conservador.
- Tolerância `max_stale_s = 0,5 s`: perante uma leitura falhada devolve a última boa se for mais nova do que isso, e levanta se não for. A 5 Hz uma leitura perdida é normal e desarmar por causa dela dava um barco inutilizável; ignorar falhas dava navegação às cegas. A janela resolve as duas coisas com um só parâmetro.
- Saída em (−180, 180], a convenção do `SimulatedHeading`, e não a de bússola. Como o `heading_error()` normaliza a diferença, a convenção é indiferente ao controlador, e assim o `RealHeading` é mesmo um *drop-in*. O ecrã da bancada mostra `% 360` só para comparação com uma bússola.
- Driver injetado por parâmetro, com o `import adafruit_bno055` dentro do `create_bno055()`: o módulo importa-se e testa-se num PC sem `adafruit-blinka`.
- **O `main.py` não foi tocado, de propósito.** Enquanto a posição vier do `SimulatedBoat`, misturar rumo real com posição simulada dá uma malha incoerente: o barco sintético avança segundo o rumo *dele*, não segundo o do sensor, e as duas coisas divergem à primeira iteração. O `RealHeading` só entra no `main.py` quando houver GPS.
- Ordem de trabalhos revista para o hardware: loop key primeiro, depois um motor em bancada, depois a segunda bateria, e só então o kill-switch remoto. O ESC só chega domingo.
- Fusível de 30 A dado por suficiente para a bancada: com o tecto de 30 % do ESP32 a corrente fica muito abaixo, e 30 A à frente de um ESC de 40 A queima primeiro que o ESC, que é o que se quer num ensaio. Os 40–50 A da hierarquia da v1.12 passam a ser requisito para potência plena na água, não para bancada.

#### Problemas / limitações
- **O `verify_concept.py` não corre no modelo corrente.** Rebenta com `KeyError: 'raspberry_pi_4'` no v6_4, porque o v6_4 decompôs os módulos em sub-peças (42 → 88 sólidos): `raspberry_pi_4` passou a 13 `rpi4_*`, `esp32_devkit` a 8 `esp32_*`, e o mesmo para BNO055 e GPS. Dos 11 nomes da lista `INSIDE`, 7 existem no v6_4 e 11 existiam no v6_3. Consequência: as verificações de *bounding box* e de colisões correram, mas **as folgas ao interior da caixa IP66 e a estimativa de CG nunca correram no v6_4**. O dicionário `MASS` tem o mesmo problema, portanto o CG estaria incompleto mesmo sem o crash.
- Corrigir o KiCad ficou bloqueado: o projeto está em `Documents\Autonomus_boat_catamara\`, fora do repositório, e o repo só tem um netlist de 22-07 e um PNG. A fonte do esquema não está versionada, logo qualquer correção não fica registada. Acrescentar os condensadores de 2,2 µF exige mexer em símbolos e fios e tem de ser feito no Eeschema, não por script.
- Declinação magnética ainda por confirmar. Está a −2,1° como ordem de grandeza para Lisboa, não como valor verificado na calculadora da NOAA/NCEI.
- O `RealHeading` nunca viu um BNO055. Está testado contra um driver falso, o que valida a política e não a leitura.

#### Resultado do dia
- A navegação passa a ter uma fonte de rumo real pronta a ligar, com o comportamento de falha definido antes de haver falhas para observar.
- O `hardware/mechanical/` deixou de ter 14 ficheiros STEP onde 4 interessam.

#### Lições aprendidas
- Ao arquivar versões, o número na versão não diz se é lixo. O `v6_2` parecia velho e é o `SRC` por omissão dos dois scripts de build; o `v6_3` parecia superado e é a geometria de que foi feito o `.glb` do site publicado. Arquivá-los partia a reconstrução do modelo e a proveniência do site. **O critério é quem depende do ficheiro, não a data nem o número.**
- Um script de verificação que rebenta é melhor que um que devolve resultados sobre metade das peças em silêncio — mas só se alguém o correr. Este esteve uma semana sem correr no modelo que verifica.
- Detalhar um modelo CAD tem custo escondido: decompor peças em sub-peças invalida por nome tudo o que dependia dos nomes anteriores.
- Um sensor que falha ruidosamente é mais fácil de programar do que um que mente. A parte difícil do `RealHeading` não foi ler o I2C; foi decidir o que fazer quando a leitura existe e não presta.

#### Próximo passo
- Comprar a loop key. Confirmar na ficha do jato se pode rodar a seco (chumaceira/vedante lubrificados pela água) antes de o pôr a girar sem água.
- Domingo, com o ESC: um motor em bancada, ≤30 %, amarrado, com o fusível de 30 A em série.
- Corrigir a lista `INSIDE` e o dicionário `MASS` do `verify_concept.py` para os nomes do v6_4, e voltar a correr as folgas e o CG.
- Copiar o projeto KiCad para `hardware/electrical/kicad/` e commitar, antes de lhe mexer.
- Correr o `heading_bench.py` no Pi com o BNO055, e calibrar já com o barco montado — o ferro e as correntes do barco distorcem o campo, e uma calibração feita com a placa na mão não vale para o barco montado.

### 2026-07-30

#### Trabalho realizado
- `verify_concept.py` a correr outra vez no modelo corrente. A lista `INSIDE` e o dicionário `MASS`, ambos por nome de sólido, foram substituídos por uma tabela `MODULES` que mapeia módulo → sólidos → massa. A bounding box do módulo é a união das sub-peças e a massa aplica-se no centroide dessa união.
- Acrescentado um bloco de integridade que corre antes das folgas e do CG e reporta as três direções de erro: sólidos sem módulo (órfãos), módulos cujos sólidos não existem no STEP (ausentes) e sólidos declarados em mais de um módulo (duplos). No v6_4 dá `87/87 mapeados, sem órfãos nem duplicados`.
- **Folgas ao interior da caixa IP66 correram pela primeira vez no v6_4: os 11 módulos cabem todos.** Quatro estão a menos de 6 mm de uma parede — `gps_modulo` +Y 3,0 mm, `bateria_pi_2200` −X 3,0 mm, `distribuidor_fusiveis` +X 5,5 mm e `ads1015` +X 5,5 mm.
- **CG recalculado no v6_4:** massa 11,63 kg, X = 469 mm (58,6 % do casco a contar da proa), Y = +0,7 mm, Z = 103 mm.
- Servos do bocal orientável ganharam massa na tabela (0,012 kg por lado). Estavam no modelo desde o v6_4 e não estavam em massa nenhuma.
- `tools/README.md` documenta o raciocínio por módulo e o bloco de integridade.

#### Decisões técnicas
- **A unidade de análise passa a ser o módulo e não o sólido.** A pergunta que as folgas respondem é "o Pi cabe na caixa?", não "o conector CSI cabe na caixa?". Com o módulo como unidade, detalhar mais o CAD deixa de invalidar o verificador: acrescentam-se sólidos à lista do módulo e o resultado físico não muda.
- **Massa do waterjet distribuída pela união das sub-peças em vez de ficar no duto.** Os 0,35 kg por lado são do conjunto; deixá-los no `waterjet_dir` (X 735..793) punha o centroide a montante do jato real, que se estende até X 815.
- Comprimento para a percentagem de CG passou a ser derivado da bounding box dos cascos em vez de `800` fixo no código. O envelope estende-se até 815 por causa do bocal, e a percentagem tem de ser do casco.
- O bloco de integridade imprime sempre, mesmo quando está tudo bem. Um verificador que só fala quando falha não distingue "verificado e correto" de "não corri".

#### Problemas / limitações
- A massa dos servos é de catálogo para a classe SG90 (o corpo modelado é 23 × 12 × 18). Se o bocal exigir engrenagem metálica — provável, contra o impulso do jato — o número triplica. Fica anotado no próprio ficheiro.
- Continua tudo estimado: nenhuma das 43 massas foi a uma balança. O CG e o calado mantêm o estatuto de "estimado".
- As folgas verificam envelopes, não instalação: 3 mm de folga no GPS não deixam espaço para ficha, cabo nem dedo. Cabe no desenho e pode não caber na montagem.

#### Resultado do dia
- A verificação que estava parada há uma semana voltou a correr, e o modo de falha que a tornou inútil — dar resultados sobre metade das peças em silêncio — passou a ser impossível sem aviso no ecrã.
- O CG do v6_4 (11,63 kg, X 469, Z 103) bate com o que tinha sido estimado no v6_2 (~11,6 kg, X 468, z_G ≈ 107). Detalhar o modelo não mexeu na distribuição de massa, que era a dúvida que justificava voltar a correr.

#### Lições aprendidas
- Um valor que confirma o anterior não é trabalho perdido: antes de hoje, "o CG é 468 mm" e "o CG não é verificado desde o v6_2" eram indistinguíveis. Reproduzir o número no modelo corrente é o que transforma um valor herdado em valor válido.
- `dict.get(chave, 0)` é conveniente para ler e perigoso para verificar. Foi o `.get(k, 0.0)` do `MASS`, e não o `KeyError` do `INSIDE`, o erro mais grave dos dois: o `KeyError` gritou, o `.get` teria dado um CG errado com ar de certo.
- A folga apertada aparece onde não se procura. Os quatro módulos a menos de 6 mm da parede não são os grandes — são o GPS, o ADS1015 e o distribuidor, precisamente as peças que "obviamente cabem".

#### Próximo passo
- Rever a implantação dentro da caixa para dar folga de montagem ao GPS (+Y 3 mm) e à bateria da eletrónica (−X 3 mm), contando com fichas e cabos e não só com o envelope.
- Copiar o projeto KiCad para `hardware/electrical/kicad/` e commitar antes de lhe mexer.
- Confirmar a declinação magnética na calculadora da NOAA para as coordenadas do ensaio. O WMM2025 dá ≈ −0,9° para Lisboa, e não os −2,1° que estão no `real_heading.py` como ordem de grandeza; a ~1° a declinação é ruído comparada com o erro de calibração do magnetómetro.
- Bancada adiada por decisão: sem multímetro fiável não há verificação de continuidade, e soldar o BNO055 sem forma de confirmar que não há curto não se justifica. Solda, loop key, ESC, motor e multímetro passam a um único pacote, quando o ESC chegar.
- Confirmar se o recetor ELRS escolhido precisa de emissora que ainda não existe — os 29,90 € do ER6 são metade da cadeia.

### 2026-07-30 (sessão 2 — revisão da cadeia de segurança)

#### Trabalho realizado
- Revisão linha a linha dos três ficheiros que decidem se os motores param: `main.py`, `communication/serial_link.py` e `esp32/esp32_boat_.ino` (475 linhas). Quatro problemas encontrados, um deles corrigido hoje.
- **Corrigido: o modo NAV podia comandar motores reais a partir do barco sintético.** Entrar em NAV *exigia* ligação série, e o `nav_step()` enviava ao ESP32 os L/R calculados a partir da posição do `SimulatedBoat`. Com motores ligados, carregar em `n` punha hélices reais a executar a missão de um barco que só existe em memória.
- As fontes passam a declarar proveniência (`SYNTHETIC`): `True` no `SimulatedBoat` e no `SimulatedHeading`, `False` no `RealHeading`. O `nav_guard()` do `main.py` decide o modo a partir disso e das opções da linha de comandos, uma vez no arranque, e imprime a decisão.
- Três modos: sem opções o NAV **recusa** com fontes sintéticas; `--sim` corre a missão e imprime os comandos **sem os enviar** (só heartbeat 0/0); `--sim-motores` comanda mesmo os motores, com aviso, para bancada com o barco preso.
- O NAV em `--sim` deixou de exigir ESP32 — uma simulação sem propulsão não precisa de hardware nenhum. A perda de série continua a desarmar em todos os modos com propulsão em jogo.
- 9 testes novos no `test_nav_mode.py` (8 → 17; 31 → 40 no total).

#### Decisões técnicas
- **A proveniência é atributo da fonte, não parâmetro do chamador.** Se fosse uma opção passada ao `nav_guard()`, seria mais uma coisa para alguém se lembrar de pôr certa; como atributo de classe, o `SimulatedBoat` traz consigo a informação de que é sintético para onde quer que vá.
- **`is_synthetic()` devolve `True` por omissão.** Uma fonte que não se declara é tratada como sintética e o NAV recusa. É a mesma política do `RealHeading`: perante dúvida, não dar número. O inverso — assumir real — faria com que esquecer o atributo numa fonte nova destrancasse os motores em silêncio.
- **`--sim` não envia propulsão, segue o padrão do `tools/heading_bench.py`:** calcula, imprime, não envia. Já existia precedente no projeto para "exercitar a lógica sem atuar", e não valia a pena inventar um segundo padrão para a mesma ideia.
- `--sim-motores` mantido em vez de proibido: com o barco preso e fora de água, correr uma missão sintética contra os ESCs é um ensaio legítimo. O que não é legítimo é isso acontecer sem ninguém ter pedido.
- A guarda decide-se no arranque e não quando se carrega em `n`: as fontes não mudam durante a execução, e é preferível saber o que a sessão pode fazer antes de começar do que descobri-lo ao tentar.

#### Problemas / limitações
- **Por corrigir: o ESP32 não tem re-arme.** Depois do failsafe disparar, qualquer comando válido volta a pôr os motores a girar (`failsafeActive = false` no `processCommand`). A regra "o regresso da ligação nunca arma sozinho" existe no `main.py` e não existe na camada que segura os ESCs. É o mesmo raciocínio do kill-switch aplicado ao contrário: a autoridade está onde a regra não está.
- **Por corrigir: o STOP é um único `write()` best-effort.** `link.stop_motors()` devolve `True`/`False` e ninguém lê o retorno; não há repetição nem confirmação. Salva-o o failsafe do ESP32 1 s depois, mas então o STOP primário é o timeout e não o comando.
- **Por corrigir: sem terminal não há controlo nenhum.** `KeyReader.enabled = sys.stdin.isatty()`; debaixo de systemd ou `nohup` — que é como isto vai correr no barco — não há ARM, STOP nem DISARM.
- Menores: `SAFE_MAX` (Pi) e `PERCENT_MAX_SAFE` (ESP32) são o mesmo número em dois sítios; `DEFAULT_PORT` fixo em `/dev/ttyUSB0` não é estável com o GPS também em USB; `String` no `processCommand` fragmenta a heap ao fim de horas; `delay(20)` bloqueia o loop.
- Nenhum destes quatro foi observado em hardware. A revisão é de leitura, não de ensaio.

#### Resultado do dia
- O erro que podia partir hardware no primeiro ensaio de bancada com motores deixou de ser possível por omissão, e passou a exigir uma opção com nome que diz o que faz.
- A cadeia de segurança está lida e os três problemas que ficam estão escritos com o mecanismo, não só com o sintoma.

#### Lições aprendidas
- Uma regra escrita no comentário não é uma regra. O `real_heading.py` já dizia que misturar rumo real com posição simulada dá uma malha incoerente, e o raciocínio estava certo — mas ficou no docstring, e o código continuava a deixar fazê-lo. A diferença entre saber e proteger é uma linha de `if`.
- Em sistemas em camadas, a pergunta útil não é "a regra existe?" mas "a regra existe na camada que tem a autoridade?". O Pi recusa armar sozinho; quem manda nos ESCs é o ESP32, e esse aceita qualquer coisa que apareça na porta.
- Valores por omissão são decisões de segurança. `getattr(s, "SYNTHETIC", True)` e `getattr(s, "SYNTHETIC", False)` diferem numa palavra e em tudo o resto: um faz com que esquecer o atributo trave os motores, o outro faz com que os liberte.

#### Próximo passo
- Latch de re-arme no ESP32, antes de ligar motores a sério.
- STOP repetido até confirmação, e caminho de controlo que não dependa de terminal interativo.
- Unificar o tecto de 30% num sítio só e passar a porta série para um caminho `by-id`.

### 2026-07-30 (sessão 3 — trava de propulsão no ESP32)

#### Trabalho realizado
- **Corrigido o segundo dos quatro problemas: o ESP32 já não reinicia os motores sozinho.** O failsafe deixou de se limitar a parar e passa a **travar** a propulsão. A trava só abre com um comando de paragem explícito (`L: 0 R: 0`). Nenhum caminho leva de "parado por falha" a "a andar" sem passar por zero.
- O sistema passa também a **arrancar travado**, e o watchdog nasce expirado (`lastCommandMs = now - TIMEOUT - 1`). Antes, com `millis()` a começar em zero e `lastCommandTime` a zero, o firmware passava o primeiro segundo a acreditar num comando que nunca chegou.
- A lógica de segurança saiu do `.ino` para `software/esp32/motor_safety.h`, sem dependências do Arduino: tecto de 30 %, parsing do comando, failsafe por timeout e trava. O `.ino` ficou com o hardware — série, pinos, PWM.
- Escritos 13 testes em `software/esp32/tests/test_motor_safety.cpp` (182 verificações) que correm num PC com `g++`, sem ESP32. **É a primeira vez que o firmware tem testes.**
- `main.py` manda um `stop_motors()` ao entrar em ARMED e em NAV, que é o que abre a trava. Armar passa a ser o gesto humano que destranca a propulsão.
- Parsing endurecido: `toInt()` da Arduino devolvia 0 perante lixo, o que era seguro mas mudo. Agora uma linha sem dígitos é recusada como malformada e dá mensagem própria. Saiu também o `String` do caminho crítico, que fragmentava a heap.

#### Decisões técnicas
- **A trava abre com o comando de paragem, não com um comando novo de re-arme.** Não obriga a mexer no protocolo, e o Pi já manda `0/0` como heartbeat em ARMED. É o mesmo princípio dos ESCs de aeromodelismo: o acelerador tem de voltar ao mínimo antes de rearmar. Um protocolo com menos verbos é um protocolo com menos maneiras de errar.
- **Um comando travado não alimenta o watchdog.** Se um comando que não produz propulsão refrescasse o `lastCommandMs`, um Pi avariado a debitar 25 % mantinha o failsafe eternamente satisfeito sem nunca mover nada — e no instante em que a trava abrisse, arrancava. O watchdog vigia propulsão; só comandos que produzem propulsão o alimentam. Tem teste próprio.
- **A lógica separada do hardware não é arrumação, é testabilidade.** Enquanto viveu dentro do `.ino`, a única forma de a verificar era gravar o ESP32 e ligar motores — ou seja, testar o failsafe com hélices a girar. É a mesma razão pela qual o `RealHeading` recebe o driver por parâmetro.
- Mantido o `delay(20)` e o resto da estrutura do `.ino`. A refactorização era para separar a decisão da atuação, não para reescrever o que já funcionava.

#### Problemas / limitações
- **Os testes validam política, não hardware.** Que o PWM chegue mesmo aos ESCs só se verifica com osciloscópio ou com um motor na bancada. O que está provado é o que o firmware *decide*, não o que o pino *faz*.
- O firmware novo nunca foi gravado num ESP32. Compila com `g++` na parte que não depende do Arduino; o `.ino` completo não foi compilado com o toolchain do ESP32.
- Ficam dois dos quatro problemas da revisão: o STOP continua a ser um único `write()` best-effort, e sem terminal interativo não há ARM, STOP nem DISARM.
- `SAFE_MAX` (Pi) e `PERCENT_MAX_SAFE` (ESP32) continuam a ser o mesmo número em dois sítios.

#### Resultado do dia
- O firmware que segura os ESCs passou a ter a mesma regra que o Pi já tinha — "o regresso da ligação nunca arma sozinho" — mas agora na camada que tem a autoridade.
- 40 testes em Python e 13 em C++. O `.ino` deixou de ser a única parte do projeto sem forma de ser verificada.

#### Lições aprendidas
- Parar não é o mesmo que ficar parado. Um failsafe que só corta é reversível por acidente; para não o ser tem de deixar o sistema num estado que exija uma ação deliberada para sair. A diferença entre `stopMotors()` e `locked = true` é a diferença entre um travão e um travão de mão.
- Código difícil de testar não é um problema de disciplina, é um problema de desenho. A lógica não tinha testes porque estava presa ao hardware; assim que se separou, os testes escreveram-se em meia hora.
- Um valor por omissão silencioso esconde-se bem: o `toInt()` a devolver 0 falhava para o lado seguro, e por isso ninguém repara que está a falhar. Seguro e mudo ainda é mudo.

#### Próximo passo
- STOP repetido até confirmação e caminho de controlo sem terminal interativo — os dois que faltam da revisão.
- Unificar o tecto de 30 % num sítio só; porta série por `by-id`.
- Compilar o `.ino` com o toolchain do ESP32 antes de gravar.

### 2026-07-30 (sessão 4 — leitura crítica do código de segurança)

#### Trabalho realizado
- Passagem de leitura sobre quatro ficheiros do caminho de segurança, sem alterar código: `control/mixer.py`, `control/heading.py`, `esp32/motor_safety.h` e `esp32/tests/test_motor_safety.cpp`.
- Confirmada linha a linha a ordem das verificações do `handleLine()`: limites primeiro, depois o comando de paragem que abre a trava, depois a trava, e só no fim a obediência. A ordem é o desenho de segurança e não uma sequência arbitrária.
- Reconstruída e verificada a aritmética sem sinal do `lastCommandMs`: a volta ao contador acontece duas vezes, na subtração que se guarda e na que se verifica, e cancela-se. O valor intermédio é grande e nunca é lido por ninguém — a variável só aparece dentro de uma diferença.

#### Decisões técnicas
- **Um defeito real e inatingível documenta-se, não se corrige.** A aritmética do `millis()` deixa de dar a diferença certa ao fim de 49 dias de alimentação contínua. Com 1,9 h de autonomia da bateria da eletrónica, são cerca de 600 vezes mais do que o alcançável. Acrescentar código para o tratar poria instruções novas — logo, defeitos possíveis novos — no caminho crítico do failsafe, para resolver uma situação que não ocorre. Fica registado o limite e o código fica como está.
- Mantida a separação entre o que os testes provam e o que não provam. Os 182 verificações do `test_motor_safety.cpp` validam a **política** — que decisão o firmware toma perante cada comando e perante o silêncio. Não dizem nada sobre o sinal chegar ao pino, o ESC entender o sinal ou o motor rodar. A frase "está testado" não deve ser lida como mais do que isto na bancada de domingo.
- Registada a razão de desenho de duas escolhas que não são óbvias na leitura: o `parseValue()` recebe `long *out` porque tem de devolver duas informações independentes — se conseguiu ler e o que leu — e é isso que distingue um comando ilegível de um pedido legítimo de paragem; e o `tick()` recebe o instante por parâmetro em vez de chamar o `millis()`, que é o que torna possível testar um timeout de 1 s e a volta dos 49 dias sem esperar nem 1 s nem 49 dias.

#### Problemas / limitações
- Leitura não é ensaio. Nenhuma das conclusões desta sessão foi confirmada em hardware.
- Os dois defeitos por corrigir da revisão anterior continuam por corrigir: o STOP é um único `write()` sem confirmação nem repetição, e sem terminal interativo não há ARM, STOP nem DISARM.
- O `.ino` completo continua sem ter sido compilado com o toolchain do ESP32; só a parte independente do Arduino compila com `g++`.

#### Resultado do dia
- A cadeia de segurança está lida de ponta a ponta, com as razões de desenho de cada verificação escritas em vez de implícitas.
- O limite dos 49 dias passou de propriedade desconhecida a limitação conhecida, quantificada e deliberadamente não corrigida.

#### Lições aprendidas
- Ler os testes é a via mais rápida para saber o que um módulo promete. O ficheiro diz *como*; os nomes dos testes dizem *o quê*, e lidos em sequência são a lista de garantias.
- O que entra por parâmetro pode ser fingido no ensaio; o que a função vai buscar sozinha, não. Vale para o relógio do `tick()` e para o driver do `RealHeading`, e é o critério que decide se um módulo é testável antes de existir hardware.
- Um valor intermédio absurdo não é necessariamente um erro. O `lastCommandMs` fica com um número enorme no arranque e está certo, porque nunca é lido isolado — só como extremo de uma diferença.

#### Próximo passo
- Corrigir os dois defeitos que faltam da revisão da cadeia de segurança.
- Compilar o `.ino` com o toolchain do ESP32 antes de gravar.
