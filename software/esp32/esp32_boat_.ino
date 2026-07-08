#include <ESP32Servo.h>

Servo escLeft;
Servo escRight;

const int LEFT_ESC_PIN = 18;
const int RIGHT_ESC_PIN = 19;

const int PWM_STOP = 1000;
const int PWM_MIN = 1000;
const int PWM_MAX = 2000;

const int PERCENT_MIN = 0;
const int PERCENT_MAX_SAFE = 30;

unsigned long lastCommandTime = 0;
const unsigned long FAILSAFE_TIMEOUT_MS = 1000;

bool failsafeActive = false;

int leftPWM = PWM_STOP;
int rightPWM = PWM_STOP;

static char serialBuffer[64];
static int bufferIndex = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  escLeft.setPeriodHertz(50);
  escRight.setPeriodHertz(50);

  escLeft.attach(LEFT_ESC_PIN, PWM_MIN, PWM_MAX);
  escRight.attach(RIGHT_ESC_PIN, PWM_MIN, PWM_MAX);

  stopMotors();

  Serial.println("ESP32 motor controller iniciado");
  Serial.println("Modo: percentagem");
  Serial.println("Formato: L:10 R:10");
  Serial.println("Terminar comando com \\n");
  Serial.println("Limite seguro atual: 0% a 30%");
}

void loop() {
  readSerialNonBlocking();

  if (millis() - lastCommandTime > FAILSAFE_TIMEOUT_MS) {
    if (!failsafeActive) {
      Serial.println("FAILSAFE ATIVO - motores parados");
      failsafeActive = true;
    }
    stopMotors();
  }

  escLeft.writeMicroseconds(leftPWM);
  escRight.writeMicroseconds(rightPWM);

  delay(20);
}

void readSerialNonBlocking() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      serialBuffer[bufferIndex] = '\0';
      processCommand(serialBuffer);
      bufferIndex = 0;
    }
    else {
      if (bufferIndex < 63) {
        serialBuffer[bufferIndex++] = c;
      }
    }
  }
}

void processCommand(char *cmd) {
  String s = String(cmd);
  s.trim();

  int lIndex = s.indexOf("L:");
  int rIndex = s.indexOf("R:");

  if (lIndex == -1 || rIndex == -1 || rIndex <= lIndex) {
    Serial.println("COMANDO INVALIDO - motores parados");
    stopMotors();
    return;
  }

  int lValue = s.substring(lIndex + 2, rIndex).toInt();
  int rValue = s.substring(rIndex + 2).toInt();

  if (lValue < PERCENT_MIN || lValue > PERCENT_MAX_SAFE ||
      rValue < PERCENT_MIN || rValue > PERCENT_MAX_SAFE) {

    Serial.println("VALOR FORA DO LIMITE SEGURO - motores parados");
    stopMotors();
    return;
  }

  leftPWM = percentToPWM(lValue);
  rightPWM = percentToPWM(rValue);

  lastCommandTime = millis();
  failsafeActive = false;

  Serial.print("Left: ");
  Serial.print(lValue);
  Serial.print("% -> ");
  Serial.print(leftPWM);
  Serial.print(" us | Right: ");
  Serial.print(rValue);
  Serial.print("% -> ");
  Serial.print(rightPWM);
  Serial.println(" us");
}

int percentToPWM(int percent) {
  return map(percent, 0, 100, PWM_STOP, PWM_MAX);
}

void stopMotors() {
  leftPWM = PWM_STOP;
  rightPWM = PWM_STOP;

  escLeft.writeMicroseconds(PWM_STOP);
  escRight.writeMicroseconds(PWM_STOP);
}
