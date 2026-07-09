# Engineering Log

A viabilidade do projeto SAILSAFE tem vindo a ser analisada desde fevereiro de 2026. Durante o período letivo, o foco esteve na exploração da arquitetura do sistema, na integração dos principais subsistemas e na definição dos requisitos técnicos iniciais.

Uma tentativa inicial de integração elétrica através de PCB revelou-se inadequada para distribuição de potência, sobretudo pela ausência de planos de cobre e pela fase ainda inicial de experiência em desenho de PCBs. Ainda assim, essa tentativa foi útil para clarificar restrições do sistema e reforçar a decisão de adotar uma arquitetura elétrica mais conservadora e robusta.

Após várias iterações, foi definida uma arquitetura inicial suficientemente sólida para avançar para a fase de execução e validação experimental.

## 2026-07-05

### Trabalho realizado
- Preparação inicial do código do ESP32 antes da chegada dos ESCs e do Raspberry Pi.
- Criação do esquema elétrico v1.

### Problemas / limitações
- Curva de aprendizagem inicial do KiCad, com algum tempo necessário para compreender a ferramenta e estruturar corretamente o esquema.

### Resultado do dia
- Base inicial de firmware preparada.
- Primeira versão do esquema elétrico concluída.

### Próximo passo
- Refinar a arquitetura elétrica e continuar a consolidação da documentação principal.

## 2026-07-06

### Trabalho realizado
- Firmware inicial do ESP32 preparado.
- Esquema elétrico v1 fechado.
- Documentação principal do projeto atualizada.
- BOM consolidada.
- Estratégia de controlo inicial por Wi-Fi definida.
- Recebido o Raspberry Pi 4 para o projeto.
- Configurado cartão microSD de 32 GB com Raspberry Pi OS.
- Configurado acesso remoto por SSH.
- Atualizado o sistema operativo do Raspberry Pi.
- Ativadas as interfaces I2C e Serial.
- Instaladas ferramentas base de desenvolvimento: Python 3, pip, venv, git, i2c-tools, screen e minicom.
- Criada a estrutura inicial de pastas do projeto no Raspberry Pi.

### Decisões técnicas
- O kill-switch físico/remoto foi identificado como requisito futuro, mas adiado por motivos de orçamento.
- Foi decidido não ligar ainda ESCs, motores ou baterias de potência antes da validação da comunicação Raspberry Pi → ESP32.

### Problemas / limitações
- O KiCad não incluía vários módulos específicos necessários para o projeto, obrigando ao uso de conectores genéricos no esquema.
- O esquema elétrico ainda requer melhorias de representação, embora os pontos principais de arquitetura estejam definidos.
- A preparação inicial do Raspberry Pi exigiu adaptação de hardware disponível para configurar o microSD.

### Resultado do dia
- O projeto ficou num estado técnico significativamente mais sólido em termos de arquitetura, documentação e preparação para testes de bancada.
- O Raspberry Pi ficou operacional e preparado para integração futura com sensores e comunicação com o ESP32.
- O projeto ficou a aguardar a chegada dos componentes para iniciar testes físicos.

### Próximo passo
- Testar a comunicação Raspberry Pi → ESP32 por USB.

## 2026-07-07

### Trabalho realizado
- Criado o repositório GitHub público do projeto SAILSAFE.
- Definida e ajustada a estrutura inicial do repositório para documentação, hardware e software.
- Preparado e atualizado o README inicial do projeto.
- Feito upload da documentação principal, ficheiros elétricos, ficheiro mecânico e código do ESP32.
- Corrigida a organização inicial do repositório, removendo a pasta intermédia criada no primeiro upload.
- Estruturadas ferramentas assistidas por IA para apoio à documentação, organização de tarefas e maior consistência na escrita técnica.
- Criado um agente de revisão crítica para apoiar a discussão de decisões técnicas, identificar fragilidades e melhorar a consistência da argumentação do projeto.

### Decisões técnicas
- Foi mantida uma estrutura de repositório simples, suficientemente organizada para acompanhar a evolução do projeto sem introduzir formalismo excessivo.
- A documentação pública será construída de forma incremental, acompanhando a evolução real do sistema.
- O agente de revisão crítica será usado como ferramenta de apoio ao raciocínio técnico e à qualidade documental, sem substituir validação própria.

### Problemas / limitações
- Curva de aprendizagem inicial do GitHub e da lógica de organização de repositórios.
- Algumas limitações de visualização de ficheiros técnicos no GitHub exigiram a criação de versões complementares em formatos mais legíveis.

### Resultado do dia
- O projeto passou a ter uma base pública organizada para documentação e portefólio técnico.
- Ficou estabelecida uma estrutura mínima estável para evolução futura do repositório.
- O processo de documentação ficou significativamente mais claro e sustentável.
- O processo de tomada de decisão passou a contar com um mecanismo adicional de revisão crítica, mantendo validação técnica própria como regra.

### Próximo passo
- Validar a comunicação Raspberry Pi → ESP32 por USB e preparar o primeiro teste funcional de integração em bancada.


## 2026-07-08

### Trabalho realizado
- Validada comunicação Raspberry Pi 4 → ESP32 por USB (ligação detetada como /dev/ttyUSB0).
- Confirmada interface USB-série CH341 no sistema.
- Validada comunicação UART entre Raspberry Pi e ESP32.
- Confirmado formato de comando textual:
  L:10 R:10
- Validada conversão interna no ESP32:
  percentagem → PWM (ex.: 10% → 1100 µs).
- Confirmado funcionamento de failsafe por perda de input (timeout → motores parados).
- Criado script Python no Raspberry Pi para envio periódico de comandos (keep-alive).
- Reestruturado parser UART do ESP32 para abordagem não bloqueante baseada em buffer + newline.

### Problemas / limitações
- Cabo USB inicial não suportava dados (sem deteção do ESP32).
- Uso de screen causava envio inválido de comandos (carácter a carácter).
- Diferença entre documentação e implementação (PWM vs percentagem).
- Parser inicial (readStringUntil) introduzia risco de bloqueio.
- Conflito de acesso à porta série ao usar simultaneamente screen e Python.

### Decisões técnicas
- Manter arquitetura:
  - Raspberry Pi → controlo de alto nível  
  - ESP32 → controlo em tempo real + failsafe
- Congelar protocolo atual:
  comando textual em percentagem (L:x R:y + newline)
- Limitar output inicial a 0–30% para segurança em bancada.
- Usar keep-alive como mecanismo normal e failsafe como redundância.

### Resultado do dia
- Cadeia de controlo RPi → ESP32 validada em bancada.
- Protocolo básico de comando e segurança funcional.
- Base sólida estabelecida para integração futura com ESCs e motores.

### Próximo passo
- Validar repetibilidade do keep-alive e comando STOP.
- Evoluir comando para modelo throttle + steering.
- Só depois iniciar integração com ESCs, motores e testes de potência.



