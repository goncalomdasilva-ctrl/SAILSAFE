#!/bin/sh
# Verificacao de sintaxe do esp32.ino num PC, sem ESP32 e sem o
# toolchain da Espressif.
#
# -------------------------------------------------------------------------
# O QUE ISTO PROVA
#   - o ficheiro e C++ valido e passa com -Wall -Wextra -Wshadow
#   - as chamadas a API do Arduino e do ESP32Servo batem certo com as
#     assinaturas declaradas em tools/stub/
#   - o motor_safety.h continua a encaixar no .ino que o usa
#
# O QUE ISTO NAO PROVA
#   - que compila com o toolchain real do ESP32 (versoes do core, macros
#     especificas, tamanho de tipos, features do compilador xtensa)
#   - que a biblioteca ESP32Servo instalada tem mesmo esta API
#   - absolutamente nada sobre o comportamento em hardware
#
# Ou seja: apanha erros de escrita, nao substitui `arduino-cli compile`.
#
# Os cabecalhos falsos vivem em tools/stub/ e nao na raiz do sketch porque o
# builder do Arduino so compila a raiz e o que estiver dentro de src/. Se
# este Arduino.h falso estivesse na raiz, tapava o verdadeiro e o build para
# a placa passava a usar declaracoes sem implementacao nenhuma.
# Serve para o .ino deixar de ser a unica parte do projeto que nao passa
# por compilador nenhum entre sessoes de bancada. Antes de gravar, compilar
# a serio:
#
#   arduino-cli compile --fqbn esp32:esp32:esp32 software/esp32
#
# -------------------------------------------------------------------------
# NOTA SOBRE OS PROTOTIPOS
# Um .ino nao e um .cpp: o builder do Arduino gera automaticamente os
# prototipos das funcoes antes de compilar, e e por isso que o setup() pode
# chamar o aplicarPWM() que so aparece 30 linhas abaixo. Este script faz a
# mesma coisa a mao. Se um dia o .ino passar a .cpp, os prototipos tem de
# ficar escritos no ficheiro.
#
# Correr com: sh software/esp32/tools/syntax_check.sh

set -e

AQUI=$(dirname "$0")
ESP32_DIR="$AQUI/.."
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

{
  echo '#include "Arduino.h"'
  # os prototipos que o builder do Arduino geraria
  echo 'void aplicarPWM();'
  echo 'void readSerialNonBlocking();'
  echo 'void processCommand(char *cmd);'
  echo 'void setup();'
  echo 'void loop();'
  cat "$ESP32_DIR/esp32.ino"
} > "$TMP/ino.cpp"

cp "$ESP32_DIR/motor_safety.h" "$TMP/"
cp "$AQUI/stub/Arduino.h" "$AQUI/stub/ESP32Servo.h" "$TMP/"

if g++ -std=c++11 -Wall -Wextra -Wshadow -fsyntax-only -I"$TMP" "$TMP/ino.cpp"; then
  echo "OK  esp32.ino: sintaxe valida e assinaturas coerentes"
  echo "    (NAO e um build para a placa -- ver cabecalho deste script)"
else
  echo "FALHA  esp32.ino nao compila"
  exit 1
fi
