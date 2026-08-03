// ESP32Servo.h FALSO -- ver stub/Arduino.h.
//
// Estas assinaturas foram escritas a partir do uso que o .ino faz da
// biblioteca, NAO lidas da ESP32Servo instalada. Se a biblioteca real tiver
// outra API, este check passa e o build a serio falha. E a limitacao
// principal do syntax_check.sh e esta escrita aqui para nao se perder.
#pragma once

#include "Arduino.h"

class Servo {
 public:
  void setPeriodHertz(int hz);
  int attach(int pin, int min, int max);
  void writeMicroseconds(int value);
};
