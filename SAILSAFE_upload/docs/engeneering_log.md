# Engineering Diary

A viabilidade do projeto SAILSAFE tem vindo a ser analisada desde fevereiro de 2026. Durante o período letivo, o foco esteve na exploração de opções de arquitetura, integração de subsistemas e definição dos principais requisitos técnicos.

Uma das tentativas iniciais incluiu o desenho de uma PCB para integração elétrica. Essa abordagem revelou-se inadequada para distribuição de potência, sobretudo pela ausência de planos de cobre e pela fase ainda inicial de experiência em desenho de PCBs. Ainda assim, essa tentativa foi útil para clarificar restrições do sistema e reforçar a decisão de adotar uma arquitetura elétrica mais conservadora e robusta.

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
- O projeto ficou num estado técnico muito mais sólido em termos de arquitetura, documentação e preparação para testes de bancada.
- O Raspberry Pi ficou operacional e preparado para integração futura com sensores e comunicação com o ESP32.
- O projeto encontra-se a aguardar a chegada dos componentes para iniciar testes físicos.

### Próximo passo
- Testar comunicação Raspberry Pi → ESP32 por USB.

## 2026-07-07

### Trabalho realizado
- Iniciada a criação do repositório GitHub do projeto SAILSAFE.
- Definida a estrutura inicial para documentação pública do projeto.
- Preparado o conteúdo inicial do README e da organização de ficheiros.
- Estruturados assistentes de IA para apoio à documentação, organização de tarefas e maior consistência na escrita técnica.

### Decisões técnicas
- Foi decidido começar com uma estrutura simples de repositório, suficientemente organizada para ser mantida sem fricção excessiva.
- A documentação pública será construída de forma incremental, em vez de tentar formalizar tudo de uma só vez.

### Problemas / limitações
- Curva de aprendizagem inicial do GitHub e da lógica de repositórios.
- Ainda sem integração total dos ficheiros técnicos no repositório.

### Resultado do dia
- O projeto passou a ter uma base inicial para documentação pública e portefólio técnico.
- Ficou definido um caminho mais claro para organizar arquitetura, software, hardware e registos de evolução.
- Os assistentes de IA passaram a integrar o processo como ferramenta de apoio à produtividade e revisão técnica, sem substituir validação própria.

### Próximo passo
- Fazer upload da documentação principal, esquema elétrico, ficheiro 3D e código do ESP32 para o repositório.

