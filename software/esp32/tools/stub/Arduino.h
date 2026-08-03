// Arduino.h FALSO -- so para o syntax_check.sh compilar o .ino num PC.
//
// Nao ha implementacao por tras destas declaracoes: o script usa
// -fsyntax-only, portanto nada disto chega a ser ligado. Declara-se o
// minimo que o esp32.ino usa, e mais nada.
//
// Se o .ino passar a usar uma funcao do Arduino que nao esteja aqui, o
// check falha -- e falhar assim e o comportamento certo: obriga a declarar
// a assinatura em vez de a assumir.
#pragma once

#include <stdint.h>
#include <stdio.h>

typedef unsigned char byte;

unsigned long millis();
void delay(unsigned long ms);

struct SerialT {
  void begin(unsigned long baud);
  int available();
  int read();
  void print(const char *s);
  void print(int v);
  void println(const char *s);
  void println(int v);
};

extern SerialT Serial;
