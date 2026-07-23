"""Testes da navegacao por waypoints (sem hardware).

Correr com: python3 tests/test_navigation.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control.navigation import haversine_m, bearing_deg, WaypointNav


def approx(a, b, tol):
    assert abs(a - b) <= tol, f"{a} != {b} (tol {tol})"


def test_haversine():
    approx(haversine_m(0, 0, 0, 1), 111195, 50)   # 1 grau de longitude no equador
    approx(haversine_m(0, 0, 1, 0), 111195, 50)   # 1 grau de latitude
    approx(haversine_m(38.736, -9.14, 38.736, -9.14), 0, 1e-6)


def test_bearing():
    approx(bearing_deg(0, 0, 1, 0), 0, 0.5)       # Norte
    approx(bearing_deg(0, 0, 0, 1), 90, 0.5)      # Este
    approx(bearing_deg(0, 0, -1, 0), 180, 0.5)    # Sul
    approx(bearing_deg(0, 0, 0, -1), 270, 0.5)    # Oeste


def test_waypoint_advance():
    nav = WaypointNav([(0.0, 0.0), (0.001, 0.0)], arrival_radius_m=5.0)
    # longe do primeiro waypoint
    _, dist, done = nav.update(0.01, 0.0)
    assert not done and nav.index == 0 and dist > 5
    # em cima do primeiro -> avanca para o segundo
    _, _, done = nav.update(0.0, 0.0)
    assert nav.index == 1 and not done
    # em cima do segundo -> concluido
    _, _, done = nav.update(0.001, 0.0)
    assert done and nav.index == 2


def _run():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(tests)} testes passaram.")


if __name__ == "__main__":
    _run()
