// SAILSAFE - decisao de seguranca dos motores, sem dependencias do Arduino.
//
// Este ficheiro contem a LOGICA: dado um comando recebido e o relogio,
// que PWM devem ter os motores. Nao fala com a serie, nao mexe em pinos e
// nao inclui <Arduino.h>. O esp32.ino trata do hardware e chama isto.
//
// A separacao existe por uma razao pratica: assim a logica compila e testa-se
// num PC com g++, sem ESP32 nenhum -- a mesma ideia do driver falso do
// RealHeading, que permite testar a politica sem ter o sensor.
//   software/esp32/tests/test_motor_safety.cpp
//
// -------------------------------------------------------------------------
// A TRAVA (latch)
//
// O failsafe por timeout para os motores quando o Raspberry Pi cala. Mas
// parar nao chega: se bastar um comando valido para voltar a andar, entao um
// Pi que reinicie e comece a falar poe helices a girar sem que ninguem tenha
// mandado. O barco voltava a arrancar sozinho.
//
// Por isso o failsafe TRAVA a propulsao, e a trava so se abre com um comando
// de paragem explicito ("L: 0 R: 0"). E o mesmo principio dos ESCs de
// aeromodelismo: o acelerador tem de voltar ao minimo antes de rearmar.
//
// Consequencia: o sistema arranca travado, e nenhum caminho leva de "motores
// parados por falha" a "motores a andar" sem passar por zero.
// -------------------------------------------------------------------------

#ifndef SAILSAFE_MOTOR_SAFETY_H
#define SAILSAFE_MOTOR_SAFETY_H

#include <stdlib.h>
#include <string.h>

namespace sailsafe {

const int PWM_STOP = 1000;   // us, motor parado
const int PWM_MAX = 2000;    // us, 100%
const int PERCENT_MIN = 0;
const int PERCENT_MAX_SAFE = 30;   // tecto de bancada imposto no firmware

// ~1 s. A 3 m/s sao ~3 m percorridos ao ultimo comando antes de parar.
const unsigned long FAILSAFE_TIMEOUT_MS = 1000;

enum CmdResult {
  CMD_OK,            // comando valido: propulsao aplicada
  CMD_IDLE,          // "L: 0 R: 0": para e ABRE a trava
  CMD_LOCKED,        // valido, mas a propulsao esta travada -> ignorado
  CMD_MALFORMED,     // nao se percebeu -> parado
  CMD_OUT_OF_RANGE   // fora de [0, 30] -> parado
};

inline int percentToPWM(long percent) {
  return (int)(PWM_STOP + percent * (PWM_MAX - PWM_STOP) / 100);
}

// Le um inteiro depois de "L:" ou "R:". Devolve false se nao houver digito
// nenhum -- um comando ilegivel e recusado, nao interpretado como zero.
inline bool parseValue(const char *p, long *out) {
  while (*p == ' ' || *p == '\t') {
    p++;
  }
  char *end = 0;
  long v = strtol(p, &end, 10);
  if (end == p) {
    return false;
  }
  *out = v;
  return true;
}

struct MotorSafety {
  int leftPWM;
  int rightPWM;
  bool locked;             // propulsao travada; so "L: 0 R: 0" abre
  bool failsafeActive;
  unsigned long lastCommandMs;

  // Arranque: travado e com o failsafe ja disparado.
  //
  // O `now - FAILSAFE_TIMEOUT_MS - 1` e de proposito. Com lastCommandMs a
  // zero e millis() a comecar em zero, durante o primeiro segundo o firmware
  // acreditava ter recebido um comando que nunca chegou. Assim o watchdog
  // nasce expirado. A subtracao pode dar a volta ao contador; em aritmetica
  // sem sinal a diferenca continua certa (ha teste para isso).
  void begin(unsigned long now) {
    leftPWM = PWM_STOP;
    rightPWM = PWM_STOP;
    locked = true;
    failsafeActive = true;
    lastCommandMs = now - FAILSAFE_TIMEOUT_MS - 1;
  }

  void stop() {
    leftPWM = PWM_STOP;
    rightPWM = PWM_STOP;
  }

  // Chamado a cada volta do loop. Devolve true so na volta em que o failsafe
  // dispara, para a mensagem sair uma vez e nao 50 vezes por segundo.
  bool tick(unsigned long now) {
    if (now - lastCommandMs > FAILSAFE_TIMEOUT_MS) {
      bool primeiraVez = !failsafeActive;
      failsafeActive = true;
      locked = true;      // <-- a trava. Parar nao chega; tem de ficar parado.
      stop();
      return primeiraVez;
    }
    return false;
  }

  CmdResult handleLine(const char *line, unsigned long now) {
    const char *l = strstr(line, "L:");
    const char *r = strstr(line, "R:");
    if (l == 0 || r == 0 || r <= l) {
      stop();
      return CMD_MALFORMED;
    }
    long lv = 0, rv = 0;
    if (!parseValue(l + 2, &lv) || !parseValue(r + 2, &rv)) {
      stop();
      return CMD_MALFORMED;
    }
    if (lv < PERCENT_MIN || lv > PERCENT_MAX_SAFE ||
        rv < PERCENT_MIN || rv > PERCENT_MAX_SAFE) {
      stop();
      return CMD_OUT_OF_RANGE;
    }

    // Paragem explicita: o unico comando que abre a trava.
    if (lv == 0 && rv == 0) {
      stop();
      locked = false;
      failsafeActive = false;
      lastCommandMs = now;
      return CMD_IDLE;
    }

    // Travado: o comando e valido mas nao se obedece. E de proposito que NAO
    // se actualiza o lastCommandMs -- um comando que nao produz propulsao
    // tambem nao deve alimentar o watchdog que vigia a propulsao.
    if (locked) {
      stop();
      return CMD_LOCKED;
    }

    leftPWM = percentToPWM(lv);
    rightPWM = percentToPWM(rv);
    failsafeActive = false;
    lastCommandMs = now;
    return CMD_OK;
  }
};

}  // namespace sailsafe

#endif  // SAILSAFE_MOTOR_SAFETY_H
