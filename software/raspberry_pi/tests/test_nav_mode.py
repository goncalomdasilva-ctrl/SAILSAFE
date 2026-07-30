"""Testes do modo NAV do main.py (sem hardware).

Exercitam nav_step(), que e o passo de navegacao autonoma: waypoint ->
bearing -> heading hold -> mixer -> barco. Nao abrem serie nem ficheiros.

Correr com: python3 tests/test_nav_mode.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control.heading import HeadingController, heading_error
from control.navigation import WaypointNav, haversine_m
from control.sources import SimulatedBoat
from control.real_heading import RealHeading
from main import (nav_step, nav_guard, is_synthetic, parse_args,
                  NAV_RECUSADO, NAV_SEM_MOTORES, NAV_COM_MOTORES,
                  MISSION_START, MISSION_WAYPOINTS,
                  ARRIVAL_RADIUS_M, NAV_THROTTLE, SAFE_MAX, HEARTBEAT_S)


def approx(a, b, tol):
    assert abs(a - b) <= tol, f"{a} != {b} (tol {tol})"


def _fresh():
    """Barco e navegacao no estado inicial da missao."""
    boat = SimulatedBoat(MISSION_START[0], MISSION_START[1],
                         heading=0.0, yaw_gain=0.4, speed_ms=3.0)
    nav = WaypointNav(MISSION_WAYPOINTS, arrival_radius_m=ARRIVAL_RADIUS_M)
    ctrl = HeadingController(kp=2.0, max_steer=100.0)
    return boat, nav, ctrl


def test_alvo_vem_do_waypoint_nao_de_rumo_fixo():
    """O alvo do heading hold tem de ser o bearing do waypoint atual."""
    boat, nav, ctrl = _fresh()
    step = nav_step(nav, ctrl, boat)
    assert not step.done
    # primeiro waypoint fica a Norte -> bearing ~0
    approx(step.bearing, 0.0, 1.0)
    # e o controlador ficou mesmo com esse alvo
    approx(ctrl.target, step.bearing, 1e-9)


def test_comandos_dentro_dos_limites_de_seguranca():
    """Nunca acima do teto de 30% nem negativo (waterjets sem marcha atras)."""
    boat, nav, ctrl = _fresh()
    for _ in range(3000):
        step = nav_step(nav, ctrl, boat)
        assert 0 <= step.left <= SAFE_MAX, f"left fora de [0,{SAFE_MAX}]: {step.left}"
        assert 0 <= step.right <= SAFE_MAX, f"right fora de [0,{SAFE_MAX}]: {step.right}"
        if step.done:
            break


def test_missao_completa_em_simulacao():
    """A missao dos dois waypoints tem de concluir, e nao ficar em circulos."""
    boat, nav, ctrl = _fresh()
    done_em = None
    for i in range(3000):
        step = nav_step(nav, ctrl, boat)
        if step.done:
            done_em = i
            break
    assert done_em is not None, "missao nao concluiu em 3000 passos"
    assert nav.done and nav.index == len(MISSION_WAYPOINTS)
    # a 5 Hz, com ~0.6 m/s e dois trocos de 40 m, esperam-se ~700 passos
    assert done_em < 2000, f"convergencia demasiado lenta: {done_em} passos"


def test_passa_perto_de_cada_waypoint():
    """Cada waypoint tem de ser atingido dentro do raio de chegada."""
    boat, nav, ctrl = _fresh()
    min_dist = [float("inf")] * len(MISSION_WAYPOINTS)
    for _ in range(3000):
        idx = nav.index
        step = nav_step(nav, ctrl, boat)
        # registar antes de sair: a amostra em que a missao fecha e
        # justamente a da chegada ao ultimo waypoint
        if idx < len(MISSION_WAYPOINTS):
            d = haversine_m(step.lat, step.lon, *MISSION_WAYPOINTS[idx])
            min_dist[idx] = min(min_dist[idx], d)
        if step.done:
            break
    for i, d in enumerate(min_dist):
        assert d <= ARRIVAL_RADIUS_M + 1e-6, f"waypoint {i} nunca atingido (min {d:.1f} m)"


def test_converge_para_o_bearing():
    """Depois do transitorio, o rumo deve seguir o bearing do waypoint."""
    boat, nav, ctrl = _fresh()
    erro = None
    for i in range(3000):
        step = nav_step(nav, ctrl, boat)
        if step.done:
            break
        if i > 50 and nav.index == 0:      # ja estabilizado no primeiro troco
            erro = abs(heading_error(step.bearing, boat.heading))
    assert erro is not None and erro < 5.0, f"erro de rumo por convergir: {erro}"


def test_missao_concluida_nao_da_propulsao():
    """Com a missao feita, o passo devolve zero - nunca propulsao residual."""
    boat, nav, ctrl = _fresh()
    for _ in range(3000):
        if nav_step(nav, ctrl, boat).done:
            break
    for _ in range(10):
        step = nav_step(nav, ctrl, boat)
        assert step.done
        assert step.left == 0 and step.right == 0
        assert step.bearing is None


def test_nao_avanca_waypoint_sem_la_chegar():
    """O indice so avanca dentro do raio de chegada."""
    boat, nav, ctrl = _fresh()
    step = nav_step(nav, ctrl, boat)
    assert nav.index == 0 and step.dist > ARRIVAL_RADIUS_M


def test_parametros_de_seguranca_coerentes():
    """O throttle base tem de caber debaixo do teto imposto ao ESP32."""
    assert NAV_THROTTLE <= SAFE_MAX, "throttle de NAV acima do teto de seguranca"
    assert SAFE_MAX <= 30, "o ESP32 rejeita comandos acima de 30%"
    assert HEARTBEAT_S <= 0.5, "heartbeat mais lento que o failsafe de ~1 s do ESP32"


# --- guarda do modo NAV -------------------------------------------------
# O que estes testes protegem: que uma fonte sintetica nunca comande motores
# reais sem que alguem o tenha pedido explicitamente na linha de comandos.

class _FonteReal:
    SYNTHETIC = False


class _FonteMuda:
    """Fonte que nao declara proveniencia. Deve ser tratada como sintetica."""


def test_simulated_boat_declara_se_sintetico():
    boat, _, _ = _fresh()
    assert is_synthetic(boat), "o SimulatedBoat tem de se declarar sintetico"


def test_real_heading_declara_se_real():
    assert not is_synthetic(RealHeading(driver=object())), \
        "o RealHeading tem de se declarar fonte real"


def test_fonte_que_nao_se_declara_conta_como_sintetica():
    """Falhar fechado: perante duvida sobre a proveniencia, o NAV recusa."""
    assert is_synthetic(_FonteMuda())
    modo, _ = nav_guard([_FonteMuda()])
    assert modo == NAV_RECUSADO


def test_sinteticas_sem_flags_recusam_nav():
    """O caso perigoso: motores reais a seguir o barco sintetico."""
    boat, _, _ = _fresh()
    modo, motivo = nav_guard([boat])
    assert modo == NAV_RECUSADO
    assert "SimulatedBoat" in motivo


def test_sim_permite_nav_mas_sem_propulsao():
    boat, _, _ = _fresh()
    modo, _ = nav_guard([boat], allow_sim=True)
    assert modo == NAV_SEM_MOTORES


def test_sim_motores_permite_propulsao_com_fontes_sinteticas():
    """Escotilha deliberada para a bancada, com o barco preso."""
    boat, _, _ = _fresh()
    modo, _ = nav_guard([boat], allow_sim=True, sim_drives_motors=True)
    assert modo == NAV_COM_MOTORES
    # --sim-motores nao precisa de --sim para valer
    modo, _ = nav_guard([boat], sim_drives_motors=True)
    assert modo == NAV_COM_MOTORES


def test_fontes_reais_comandam_motores_sem_flags():
    modo, _ = nav_guard([_FonteReal(), _FonteReal()])
    assert modo == NAV_COM_MOTORES


def test_uma_fonte_sintetica_contamina_o_conjunto():
    """Basta uma fonte sintetica para o conjunto deixar de ser real."""
    boat, _, _ = _fresh()
    modo, _ = nav_guard([_FonteReal(), boat])
    assert modo == NAV_RECUSADO


def test_por_omissao_a_linha_de_comandos_e_a_mais_segura():
    a = parse_args([])
    assert not a.sim and not a.sim_motores
    assert parse_args(["--sim"]).sim
    assert parse_args(["--sim-motores"]).sim_motores


def _run():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(tests)} testes passaram.")


if __name__ == "__main__":
    _run()
