"""Testes da logica de heading hold (sem hardware).

Correr com: python3 tests/test_heading.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control.heading import normalize_angle, heading_error, HeadingController


def test_normalize():
    assert normalize_angle(0) == 0
    assert normalize_angle(90) == 90
    assert normalize_angle(180) == 180
    assert normalize_angle(-180) == 180
    assert normalize_angle(190) == -170
    assert normalize_angle(360) == 0
    assert normalize_angle(450) == 90
    assert normalize_angle(-90) == -90


def test_error_wrap():
    assert heading_error(1, 359) == 2      # +2, nao -358
    assert heading_error(359, 1) == -2     # -2, nao +358
    assert heading_error(90, 0) == 90
    assert heading_error(0, 90) == -90


def test_controller():
    c = HeadingController(kp=2.0, max_steer=100.0)
    assert c.update(0.0) == 0.0            # sem alvo -> nao mexe
    c.set_target(90.0)
    assert c.update(0.0) == 100.0          # erro grande -> saturado
    assert c.update(90.0) == 0.0           # no alvo -> zero
    assert abs(c.update(89.0) - 2.0) < 1e-9  # erro pequeno -> proporcional
    c.set_target(10.0)
    assert c.update(0.0) > 0               # alvo a estibordo -> positivo
    c.set_target(-10.0)
    assert c.update(0.0) < 0               # alvo a bombordo -> negativo


def _run():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(tests)} testes passaram.")


if __name__ == "__main__":
    _run()
