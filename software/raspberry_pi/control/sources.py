"""Fontes de dados SINTETICAS para desenvolvimento sem hardware.

Nada aqui representa medicoes reais; servem para exercitar a logica de
controlo (heading hold) enquanto o BNO055 e o GPS nao estao disponiveis.
Quando o hardware chegar, estas classes sao substituidas por leitores
reais com a mesma interface read().
"""

import math

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


class SimulatedBoat:
    """Barco SINTETICO com posicao (lat, lon) e rumo.

    Roda conforme a diferenca de impulso (left-right) e avanca conforme a
    media dos motores. Serve para fechar a malha de navegacao sem GPS, BNO055
    nem motores. NAO representa medicoes reais.
    """

    def __init__(self, lat, lon, heading=0.0, yaw_gain=0.4, speed_ms=3.0):
        self.lat = lat
        self.lon = lon
        self.heading = normalize_angle(heading)
        self.yaw_gain = yaw_gain      # graus por (unidade de left-right) por segundo
        self.speed_ms = speed_ms      # velocidade a 100% de impulso medio

    def update(self, left, right, dt=1.0):
        # rotacao: proporcional a diferenca dos motores
        self.heading = normalize_angle(self.heading + self.yaw_gain * (left - right) * dt)
        # avanco: proporcional a media dos motores, ao longo do rumo
        thr = (left + right) / 2.0
        dist = self.speed_ms * (thr / 100.0) * dt
        d_north = dist * math.cos(math.radians(self.heading))
        d_east = dist * math.sin(math.radians(self.heading))
        self.lat += d_north / 111320.0
        self.lon += d_east / (111320.0 * math.cos(math.radians(self.lat)))
        return self.lat, self.lon, self.heading

    def position(self):
        return self.lat, self.lon


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
