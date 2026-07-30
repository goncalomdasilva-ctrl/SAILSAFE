// SAILSAFE - controlo dos ESCs no ESP32.
//
// Este ficheiro trata do HARDWARE: serie, pinos, sinal PWM. Toda a decisao
// de seguranca (tecto de 30%, failsafe por timeout, trava de re-arme) esta
// em motor_safety.h, que nao depende do Arduino e e testado com g++ em
// software/esp32/tests/.
//
// Protocolo: "L: <0-30> R: <0-30>\n"
// O sistema arranca TRAVADO. Ate receber "L: 0 R: 0" nao ha propulsao.

#include <ESP32Servo.h>
#include "motor_safety.h"

using namespace sailsafe;

Servo escLeft;
Servo escRight;

const int LEFT_ESC_PIN = 18;
const int RIGHT_ESC_PIN = 19;

MotorSafety safety;

static char serialBuffer[64];
static int bufferIndex = 0;
static bool avisoTravaImpresso = false;

void setup() {
  Serial.begin(115200);
  delay(1000);

  escLeft.setPeriodHertz(50);
  escRight.setPeriodHertz(50);

  escLeft.attach(LEFT_ESC_PIN, PWM_STOP, PWM_MAX);
  escRight.attach(RIGHT_ESC_PIN, PWM_STOP, PWM_MAX);

  safety.begin(millis());
  aplicarPWM();

  Serial.println("ESP32 motor controller iniciado");
  Serial.println("Formato: L: 10 R: 10   (terminar com \\n)");
  Serial.println("Limite seguro atual: 0% a 30%");
  Serial.println("PROPULSAO TRAVADA no arranque - enviar 'L: 0 R: 0' para destravar");
}

void loop() {
  readSerialNonBlocking();

  if (safety.tick(millis())) {
    Serial.println("FAILSAFE ATIVO - motores parados e propulsao TRAVADA");
    Serial.println("Enviar 'L: 0 R: 0' para destravar");
    avisoTravaImpresso = false;
  }

  aplicarPWM();

  delay(20);
}

void aplicarPWM() {
  escLeft.writeMicroseconds(safety.leftPWM);
  escRight.writeMicroseconds(safety.rightPWM);
}

void readSerialNonBlocking() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      serialBuffer[bufferIndex] = '\0';
      processCommand(serialBuffer);
      bufferIndex = 0;
    } else {
      if (bufferIndex < 63) {
        serialBuffer[bufferIndex++] = c;
      }
    }
  }
}

void processCommand(char *cmd) {
  CmdResult r = safety.handleLine(cmd, millis());

  switch (r) {
    case CMD_MALFORMED:
      Serial.println("COMANDO INVALIDO - motores parados");
      break;

    case CMD_OUT_OF_RANGE:
      Serial.println("VALOR FORA DO LIMITE SEGURO - motores parados");
      break;

    case CMD_LOCKED:
      // Nao inunda a consola: o Pi manda comandos a 5 Hz.
      if (!avisoTravaImpresso) {
        Serial.println("PROPULSAO TRAVADA - ignorado. Enviar 'L: 0 R: 0' para destravar");
        avisoTravaImpresso = true;
      }
      break;

    case CMD_IDLE:
      Serial.println("Parado. Propulsao DESTRAVADA");
      avisoTravaImpresso = false;
      break;

    case CMD_OK:
      Serial.print("Left: ");
      Serial.print(safety.leftPWM);
      Serial.print(" us | Right: ");
      Serial.print(safety.rightPWM);
      Serial.println(" us");
      break;
  }
}
