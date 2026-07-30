// Testes da logica de seguranca dos motores. Correm num PC, sem ESP32.
//
//   g++ -std=c++11 -Wall -o /tmp/tms software/esp32/tests/test_motor_safety.cpp
//   /tmp/tms
//
// Testam politica, nao hardware: que decisao toma o firmware perante cada
// comando e perante o silencio. Que o sinal PWM chega mesmo aos ESCs so se
// verifica com um osciloscopio ou com um motor na bancada.

#include <cstdio>
#include <cstdlib>
#include "../motor_safety.h"

using namespace sailsafe;

static int falhas = 0;
static int total = 0;

#define CHECK(cond, msg)                                              \
  do {                                                                \
    total++;                                                          \
    if (!(cond)) {                                                    \
      printf("FALHA  %-52s (linha %d)\n", msg, __LINE__);             \
      falhas++;                                                       \
    }                                                                 \
  } while (0)

static void ok(const char *nome) { printf("OK  %s\n", nome); }

// Estado ja destravado e a andar, para os testes que precisam disso.
static MotorSafety aAndar(unsigned long *t) {
  MotorSafety s;
  s.begin(*t);
  s.handleLine("L: 0 R: 0", *t);
  *t += 200;
  s.handleLine("L: 20 R: 20", *t);
  return s;
}

// -------------------------------------------------------------------------

static void test_arranca_travado_e_parado() {
  MotorSafety s;
  s.begin(0);
  CHECK(s.locked, "arranca travado");
  CHECK(s.failsafeActive, "arranca com failsafe ativo");
  CHECK(s.leftPWM == PWM_STOP && s.rightPWM == PWM_STOP, "arranca parado");
  ok("test_arranca_travado_e_parado");
}

static void test_watchdog_nasce_expirado() {
  // Antes, com lastCommandMs = 0 e millis() a comecar em 0, o firmware
  // passava o primeiro segundo a acreditar num comando que nunca chegou.
  MotorSafety s;
  s.begin(0);
  s.failsafeActive = false;          // finge que ninguem tinha reparado
  CHECK(s.tick(0), "failsafe dispara logo no instante zero");
  CHECK(s.locked, "e deixa travado");
  ok("test_watchdog_nasce_expirado");
}

static void test_comando_valido_nao_anda_enquanto_travado() {
  MotorSafety s;
  s.begin(0);
  CHECK(s.handleLine("L: 25 R: 25", 100) == CMD_LOCKED, "travado recusa propulsao");
  CHECK(s.leftPWM == PWM_STOP && s.rightPWM == PWM_STOP, "e fica parado");
  ok("test_comando_valido_nao_anda_enquanto_travado");
}

static void test_paragem_explicita_destrava() {
  MotorSafety s;
  s.begin(0);
  CHECK(s.handleLine("L: 0 R: 0", 100) == CMD_IDLE, "0/0 e aceite");
  CHECK(!s.locked, "0/0 destrava");
  CHECK(s.leftPWM == PWM_STOP, "0/0 nao da propulsao");
  CHECK(s.handleLine("L: 25 R: 25", 200) == CMD_OK, "depois de destravar, anda");
  CHECK(s.leftPWM == 1250 && s.rightPWM == 1250, "25% -> 1250 us");
  ok("test_paragem_explicita_destrava");
}

// O teste que motivou tudo isto.
static void test_failsafe_nao_reinicia_os_motores_sozinho() {
  unsigned long t = 1000;
  MotorSafety s = aAndar(&t);
  CHECK(s.leftPWM > PWM_STOP, "estava mesmo a andar");

  t += FAILSAFE_TIMEOUT_MS + 1;      // o Pi calou-se
  CHECK(s.tick(t), "failsafe dispara");
  CHECK(s.leftPWM == PWM_STOP, "failsafe para os motores");
  CHECK(s.locked, "failsafe TRAVA a propulsao");

  // O Pi reinicia e volta a falar. Nada disto pode fazer o motor andar.
  for (int i = 0; i < 20; i++) {
    t += 200;
    CHECK(s.handleLine("L: 25 R: 25", t) == CMD_LOCKED, "comando apos failsafe e ignorado");
    CHECK(s.leftPWM == PWM_STOP, "motor continua parado apos failsafe");
  }

  // So depois de passar por zero e que volta a haver propulsao.
  t += 200;
  s.handleLine("L: 0 R: 0", t);
  t += 200;
  CHECK(s.handleLine("L: 25 R: 25", t) == CMD_OK, "passa a andar depois de passar por zero");
  ok("test_failsafe_nao_reinicia_os_motores_sozinho");
}

static void test_comando_travado_nao_alimenta_o_watchdog() {
  MotorSafety s;
  s.begin(0);
  unsigned long t = 5000;
  s.handleLine("L: 0 R: 0", t);      // destrava
  s.locked = true;                   // volta a travar
  unsigned long antes = s.lastCommandMs;
  s.handleLine("L: 25 R: 25", t + 300);
  CHECK(s.lastCommandMs == antes, "comando travado nao refresca o watchdog");
  ok("test_comando_travado_nao_alimenta_o_watchdog");
}

static void test_comando_invalido_nao_alimenta_o_watchdog() {
  unsigned long t = 1000;
  MotorSafety s = aAndar(&t);
  unsigned long antes = s.lastCommandMs;
  s.handleLine("lixo", t + 300);
  CHECK(s.lastCommandMs == antes, "linha corrompida nao refresca o watchdog");
  CHECK(s.leftPWM == PWM_STOP, "linha corrompida para os motores");
  ok("test_comando_invalido_nao_alimenta_o_watchdog");
}

static void test_tecto_de_30_por_cento() {
  unsigned long t = 1000;
  MotorSafety s = aAndar(&t);
  CHECK(s.handleLine("L: 30 R: 30", t + 100) == CMD_OK, "30% e aceite");
  CHECK(s.leftPWM == 1300, "30% -> 1300 us");
  CHECK(s.handleLine("L: 31 R: 0", t + 200) == CMD_OUT_OF_RANGE, "31% e recusado");
  CHECK(s.handleLine("L: 100 R: 100", t + 300) == CMD_OUT_OF_RANGE, "100% e recusado");
  CHECK(s.handleLine("L: -5 R: 0", t + 400) == CMD_OUT_OF_RANGE, "negativo e recusado");
  CHECK(s.leftPWM == PWM_STOP, "recusa deixa parado");
  ok("test_tecto_de_30_por_cento");
}

static void test_linhas_malformadas() {
  MotorSafety s;
  s.begin(0);
  s.handleLine("L: 0 R: 0", 100);
  CHECK(s.handleLine("", 200) == CMD_MALFORMED, "linha vazia");
  CHECK(s.handleLine("L: 10", 200) == CMD_MALFORMED, "falta o R");
  CHECK(s.handleLine("R: 10 L: 10", 200) == CMD_MALFORMED, "R antes de L");
  CHECK(s.handleLine("L: x R: y", 200) == CMD_MALFORMED, "sem digitos");
  CHECK(s.handleLine("L:  R: 10", 200) == CMD_MALFORMED, "L sem valor");
  CHECK(s.leftPWM == PWM_STOP, "malformado deixa parado");
  ok("test_linhas_malformadas");
}

static void test_espacos_e_formato_do_pi() {
  MotorSafety s;
  s.begin(0);
  s.handleLine("L: 0 R: 0", 100);
  // exactamente o que o serial_link.py escreve
  CHECK(s.handleLine("L: 12 R: 8", 200) == CMD_OK, "formato do serial_link.py");
  CHECK(s.leftPWM == 1120 && s.rightPWM == 1080, "12% e 8% convertidos");
  CHECK(s.handleLine("L:12 R:8", 300) == CMD_OK, "tambem sem espaco");
  ok("test_espacos_e_formato_do_pi");
}

static void test_sobrevive_ao_overflow_do_millis() {
  // millis() da a volta ao fim de ~49 dias. A subtracao sem sinal continua
  // certa; o que nao pode acontecer e o failsafe deixar de disparar.
  unsigned long t = 0xFFFFFF00UL;    // perto do fim do contador
  MotorSafety s;
  s.begin(t);
  s.handleLine("L: 0 R: 0", t);
  t += 100;
  CHECK(s.handleLine("L: 20 R: 20", t) == CMD_OK, "anda antes da volta");
  t += FAILSAFE_TIMEOUT_MS + 1;      // aqui o contador ja deu a volta
  CHECK(s.tick(t), "failsafe dispara na volta do contador");
  CHECK(s.leftPWM == PWM_STOP, "e para os motores");
  ok("test_sobrevive_ao_overflow_do_millis");
}

static void test_failsafe_so_avisa_uma_vez() {
  unsigned long t = 1000;
  MotorSafety s = aAndar(&t);
  t += FAILSAFE_TIMEOUT_MS + 1;
  CHECK(s.tick(t), "primeira volta avisa");
  CHECK(!s.tick(t + 20), "segunda volta nao avisa");
  CHECK(!s.tick(t + 40), "terceira volta nao avisa");
  ok("test_failsafe_so_avisa_uma_vez");
}

static void test_comando_a_horas_evita_o_failsafe() {
  unsigned long t = 1000;
  MotorSafety s = aAndar(&t);
  for (int i = 0; i < 50; i++) {     // heartbeat a 5 Hz, 10 s
    t += 200;
    CHECK(s.handleLine("L: 20 R: 20", t) == CMD_OK, "comando aceite");
    CHECK(!s.tick(t + 10), "failsafe nao dispara com heartbeat a 5 Hz");
  }
  CHECK(s.leftPWM == 1200, "continua a andar a 20%");
  ok("test_comando_a_horas_evita_o_failsafe");
}

int main() {
  test_arranca_travado_e_parado();
  test_watchdog_nasce_expirado();
  test_comando_valido_nao_anda_enquanto_travado();
  test_paragem_explicita_destrava();
  test_failsafe_nao_reinicia_os_motores_sozinho();
  test_comando_travado_nao_alimenta_o_watchdog();
  test_comando_invalido_nao_alimenta_o_watchdog();
  test_tecto_de_30_por_cento();
  test_linhas_malformadas();
  test_espacos_e_formato_do_pi();
  test_sobrevive_ao_overflow_do_millis();
  test_failsafe_so_avisa_uma_vez();
  test_comando_a_horas_evita_o_failsafe();

  printf("\n%d verificacoes, %d falhas\n", total, falhas);
  return falhas == 0 ? 0 : 1;
}
