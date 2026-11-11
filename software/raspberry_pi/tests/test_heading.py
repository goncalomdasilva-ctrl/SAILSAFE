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


# --- histerese em +/-180 (OPEN-018) ---------------------------------------
# Os tres primeiros valores sao os observados na bancada a 2026-11-10: alvo a
# 0, rumo a oscilar decimas de grau a volta de 180.

def test_180_nao_troca_de_lado_com_decimas_de_grau():
    c = HeadingController(kp=2.0, max_steer=100.0)
    c.set_target(0.0)
    steers = [c.update(h) for h in (180.2, 179.6, 180.1, 179.9, 180.4)]
    assert steers[0] == 100.0              # 180,2 -> erro +179,8: estibordo
    assert steers == [100.0] * 5           # e fica em estibordo
    assert c.committed_turn == 1


def test_180_o_primeiro_lado_escolhido_e_o_curto():
    c = HeadingController(kp=2.0, max_steer=100.0)
    c.set_target(0.0)
    assert c.update(179.6) == -100.0       # erro -179,6: bombordo e o curto
    assert c.update(180.2) == -100.0       # e mantem-se, pelo comprido
    assert c.committed_turn == -1
    assert abs(c.error(180.2) - (-180.2)) < 1e-9   # erro seguido sai de (-180, 180]


def test_180_fora_da_banda_volta_ao_lado_curto():
    c = HeadingController(kp=2.0, max_steer=100.0, flip_band_deg=15.0)
    c.set_target(0.0)
    assert c.update(180.2) == 100.0        # compromete-se com estibordo
    # o barco roda para estibordo: o rumo cresce, o erro desce
    assert c.update(190.0) == 100.0        # erro +170, ainda na banda
    assert c.update(200.0) == 100.0        # erro +160, saiu: lado curto, o mesmo
    assert c.committed_turn == 0
    # empurrado para o lado errado ate sair da banda pelo outro lado:
    c.update(180.2)                        # volta a comprometer-se (+1)
    assert c.update(170.0) == 100.0        # erro -170 seguido como +190
    assert c.update(160.0) == -100.0       # erro -160: fora da banda, larga
    assert c.committed_turn == 0


def test_180_nao_mexe_em_erros_pequenos():
    com = HeadingController(kp=2.0, max_steer=100.0)
    sem = HeadingController(kp=2.0, max_steer=100.0, flip_band_deg=0.0)
    for alvo in (0.0, 90.0, 180.0, -135.0):
        com.set_target(alvo)
        sem.set_target(alvo)
        for desvio in range(-164, 165, 7):
            h = alvo - desvio
            assert com.update(h) == sem.update(h), (alvo, desvio)
            assert com.committed_turn == 0


def test_180_banda_a_zero_e_o_comportamento_antigo():
    c = HeadingController(kp=2.0, max_steer=100.0, flip_band_deg=0.0)
    c.set_target(0.0)
    assert [c.update(h) for h in (180.2, 179.6, 180.1)] == [100.0, -100.0, 100.0]


def test_180_alvo_que_muda_e_clear_target():
    c = HeadingController(kp=2.0, max_steer=100.0)
    c.set_target(0.0)
    assert c.update(180.2) == 100.0
    c.set_target(0.5)                      # o bearing do waypoint mexe a cada ciclo
    assert c.update(180.2) == 100.0        # erro -179,7 seguido como +180,3
    c.clear_target()
    assert c.committed_turn == 0
    assert c.update(180.2) == 0.0          # sem alvo nao ha steer nem compromisso
    c.set_target(0.0)
    assert c.update(179.6) == -100.0       # compromisso novo, de raiz


def test_180_banda_invalida_e_recusada():
    for banda in (-1.0, 90.0, 200.0):
        try:
            HeadingController(flip_band_deg=banda)
        except ValueError:
            continue
        raise AssertionError(f"banda {banda} devia ser recusada")


def test_180_malha_fechada_sai_do_impasse():
    """Barco sintetico LENTO virado ao contrario do alvo, com ruido de decimas.

    O impasse so existe quando o barco roda menos por ciclo do que o rumo
    treme -- um barco com inercia, ou o sensor parado na bancada. Aqui roda
    0,12 graus por ciclo contra +/-0,4 de ruido. Sem histerese as ordens
    trocam de lado e anulam-se em parte; com ela o barco roda sempre para o
    mesmo lado.
    """
    from control.mixer import mix
    from control.sources import SimulatedHeading
    ruido = [0.3, -0.4, 0.2, -0.3, 0.4, -0.2]

    def correr(banda):
        c = HeadingController(kp=2.0, max_steer=100.0, flip_band_deg=banda)
        c.set_target(0.0)
        boat = SimulatedHeading(heading=180.0, yaw_gain=0.02)
        trocas, anterior = 0, 0
        for i in range(150):                              # 30 s a 5 Hz
            steer = c.update(boat.read() + ruido[i % len(ruido)])
            sinal = (steer > 0) - (steer < 0)
            if sinal and anterior and sinal != anterior:
                trocas += 1
            anterior = sinal or anterior
            left, right = mix(20, steer, 0, 30)
            boat.update(left, right, dt=0.2)
        rodou = 180.0 - abs(heading_error(0.0, boat.read()))
        return trocas, rodou

    trocas_com, rodou_com = correr(15.0)
    assert trocas_com == 0
    assert abs(rodou_com - 150 * 0.12) < 1e-6      # todos os ciclos para o mesmo lado

    # e o controlo: o mesmo cenario sem histerese troca de lado e rende menos
    trocas_sem, rodou_sem = correr(0.0)
    assert trocas_sem > 0
    assert rodou_sem < rodou_com


def _run():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(tests)} testes passaram.")


if __name__ == "__main__":
    _run()
