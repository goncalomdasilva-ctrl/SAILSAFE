"""Fontes de dados SINTETICAS para desenvolvimento sem hardware.

Nada aqui representa medicoes reais; servem para exercitar a logica de
controlo (heading hold) enquanto o BNO055 e o GPS nao estao disponiveis.
Quando o hardware chegar, estas classes sao substituidas por leitores
reais com a mesma interface read().
"""

from control.heading import normalize_angle


class SimulatedHeading:
    """Rumo do barco a rodar conforme a diferenca de impulso (left-right).

    Modelo cinematico simples: taxa de rotacao proporcional a (left-right).
    NAO e uma medicao real; e so para fechar o ciclo em simulacao.
    """

    def __init__(self, heading=0.0, yaw_gain=0.05):
        self.heading = normalize_angle(heading)
        self.yaw_gain = yaw_gain

    def update(self, left, right, dt=1.0):
        yaw_rate = self.yaw_gain * (left - right)
        self.heading = normalize_angle(self.heading + yaw_rate * dt)
        return self.heading

    def read(self):
        return self.heading


if __name__ == "__main__":
    # Ciclo fechado SINTETICO: controlador -> mixer -> barco simulado.
    from control.heading import HeadingController, heading_error
    from control.mixer import mix

    ALVO, THROTTLE = 90.0, 30.0
    ctrl = HeadingController(kp=2.0, max_steer=100.0)
    ctrl.set_target(ALVO)
    boat = SimulatedHeading(heading=0.0, yaw_gain=0.02)

    print(f"[SIM] alvo={ALVO} deg, throttle={THROTTLE} (sintetico, sem hardware)")
    heading = boat.read()
    for i in range(400):
        steer = ctrl.update(heading)
        left, right = mix(THROTTLE, steer)
        heading = boat.update(left, right)
        err = heading_error(ALVO, heading)
        if i % 20 == 0:
            print(f"passo {i:3d}: heading={heading:7.2f}  erro={err:7.2f}  L={left:6.1f}  R={right:6.1f}")
        if abs(err) < 0.1:
            print(f"[SIM] convergiu ao passo {i}: heading={heading:.2f}  L={left:.1f}  R={right:.1f}")
            break
