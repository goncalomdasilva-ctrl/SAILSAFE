"""Testes do mixer de propulsao (sem hardware).

Correr com: python3 tests/test_mixer.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control.mixer import mix


def test_straight():
    assert mix(50, 0) == (50, 50)      # sem viragem -> motores iguais
    assert mix(0, 0) == (0, 0)


def test_starboard():
    assert mix(50, 20) == (70, 30)     # vira a direita: esquerdo mais rapido


def test_port():
    assert mix(50, -20) == (30, 70)    # vira a esquerda: direito mais rapido


def test_saturation():
    assert mix(30, 100) == (100, 0)    # nunca abaixo de 0 nem acima de 100
    assert mix(100, 50) == (100, 50)


def _run():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(tests)} testes passaram.")


if __name__ == "__main__":
    _run()
