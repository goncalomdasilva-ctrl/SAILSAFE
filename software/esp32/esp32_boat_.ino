#include <ESP32Servo.h>

Servo escLeft;
Servo escRight;

// Pinos dos ESCs
const int LEFT_ESC_PIN = 18;
const int RIGHT_ESC_PIN = 19;

// PWM dos ESCs
const int PWM_STOP = 1000;
const int PWM_MIN = 1000;
const int PWM_MAX = 2000;

// Limite seguro inicial em percentagem
const int PERCENT_MIN = 0;
const int PERCENT_MAX_SAFE = 30;

// Failsafe
unsigned long lastCommandTime = 0;
const unsigned long FAILSAFE_TIMEOUT_MS = 1000;

int leftPercent = 0;
int rightPercent = 0;

int leftPWM = PWM_STOP;
int rightPWM = PWM_STOP;

bool failsafeActive = false;

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
  Serial.println("Limite seguro atual: 0% a 30%");
}

void loop() {
  readSerialCommand();

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

void readSerialCommand() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    int lIndex = cmd.indexOf("L:");
    int rIndex = cmd.indexOf("R:");

    // Verificar formato
    if (lIndex == -1 || rIndex == -1 || rIndex <= lIndex) {
      Serial.println("COMANDO INVALIDO - motores parados");
      stopMotors();
      return;
    }

    int lValue = cmd.substring(lIndex + 2, rIndex).toInt();
    int rValue = cmd.substring(rIndex + 2).toInt();

    // Verificar limites seguros
    if (lValue < PERCENT_MIN || lValue > PERCENT_MAX_SAFE ||
        rValue < PERCENT_MIN || rValue > PERCENT_MAX_SAFE) {
      Serial.println("VALOR FORA DO LIMITE SEGURO - motores parados");
      stopMotors();
      return;
    }

    leftPercent = lValue;
    rightPercent = rValue;

    leftPWM = percentToPWM(leftPercent);
    rightPWM = percentToPWM(rightPercent);

    lastCommandTime = millis();
    failsafeActive = false;

    Serial.print("Left: ");
    Serial.print(leftPercent);
    Serial.print("% -> ");
    Serial.print(leftPWM);
    Serial.print(" us");

    Serial.print(" | Right: ");
    Serial.print(rightPercent);
    Serial.print("% -> ");
    Serial.print(rightPWM);
    Serial.println(" us");
  }
}

int percentToPWM(int percent) {
  return map(percent, 0, 100, PWM_STOP, PWM_MAX);
}

void stopMotors() {
  leftPercent = 0;
  rightPercent = 0;

  leftPWM = PWM_STOP;
  rightPWM = PWM_STOP;

  escLeft.writeMicroseconds(PWM_STOP);
  escRight.writeMicroseconds(PWM_STOP);
}