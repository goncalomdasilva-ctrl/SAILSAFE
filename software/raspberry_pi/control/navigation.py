"""Navegacao por waypoints do SAILSAFE.

Contas geodesicas sobre coordenadas (lat, lon), independentes de hardware:
- haversine_m: distancia em metros entre dois pontos
- bearing_deg: rumo (0-360, 0=Norte, 90=Este) de um ponto para outro
- WaypointNav: gere uma lista de waypoints, devolve o bearing para o alvo
  atual e avanca para o seguinte ao entrar no raio de chegada.

O bearing devolvido serve de alvo ao HeadingController (heading hold).
Funciona com posicao simulada agora e com GPS real depois, sem alteracoes.
"""

import math

EARTH_RADIUS_M = 6371000.0


def haversine_m(lat1, lon1, lat2, lon2):
    """Distancia em metros entre (lat1,lon1) e (lat2,lon2)."""
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    """Rumo inicial de (lat1,lon1) para (lat2,lon2), em graus 0-360.

    0 = Norte, 90 = Este, 180 = Sul, 270 = Oeste (bussola, sentido horario).
    """
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlmb = math.radians(lon2 - lon1)
    y = math.sin(dlmb) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlmb)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


class WaypointNav:
    """Percorre uma lista de waypoints [(lat, lon), ...] por ordem.

    update(lat, lon) devolve (bearing_alvo, distancia_m, done):
    - avanca de waypoint sempre que a distancia <= raio de chegada;
    - done = True quando todos os waypoints foram atingidos.
    """

    def __init__(self, waypoints, arrival_radius_m=3.0):
        self.waypoints = list(waypoints)
        self.arrival_radius_m = arrival_radius_m
        self.index = 0

    @property
    def done(self):
        return self.index >= len(self.waypoints)

    def update(self, lat, lon):
        while not self.done:
            wlat, wlon = self.waypoints[self.index]
            dist = haversine_m(lat, lon, wlat, wlon)
            if dist <= self.arrival_radius_m:
                self.index += 1  # chegou: passa ao seguinte
                continue
            return bearing_deg(lat, lon, wlat, wlon), dist, False
        return None, 0.0, True


if __name__ == "__main__":
    # Ciclo fechado SINTETICO: nav -> heading hold -> mixer -> barco -> posicao.
    from control.heading import HeadingController
    from control.mixer import mix
    from control.sources import SimulatedBoat

    inicio = (38.7360, -9.1400)
    wps = [(38.73690, -9.14000),   # ~100 m a Norte
           (38.73690, -9.13880)]   # depois ~100 m a Este
    nav = WaypointNav(wps, arrival_radius_m=4.0)
    ctrl = HeadingController(kp=2.0, max_steer=100.0)
    boat = SimulatedBoat(inicio[0], inicio[1], heading=0.0, yaw_gain=0.4, speed_ms=3.0)

    print("[SIM] navegacao por waypoints (sintetico, sem GPS/motores)")
    lat, lon = boat.position()
    for i in range(2000):
        bearing, dist, done = nav.update(lat, lon)
        if done:
            print(f"[SIM] todos os waypoints atingidos ao passo {i} (~{i}s)")
            break
        ctrl.set_target(bearing)
        steer = ctrl.update(boat.heading)
        left, right = mix(30, steer, 0, 30)
        lat, lon, heading = boat.update(left, right, dt=1.0)
        if i % 15 == 0:
            print(f"passo {i:4d}: wp={nav.index}  dist={dist:6.1f} m  "
                  f"bearing={bearing:5.1f}  heading={heading:5.1f}")
