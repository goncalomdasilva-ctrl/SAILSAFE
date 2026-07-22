"""Controlo de rumo (heading hold) do SAILSAFE.

Contem apenas logica de controlo, independente de sensores e atuadores:
- normalize_angle: reduz um angulo ao intervalo (-180, 180]
- heading_error: erro entre rumo alvo e atual, ja normalizado
- HeadingController: controlador proporcional simples

O controlador devolve um valor de "steering" (viragem) com sinal:
positivo = virar para estibordo (direita), negativo = para bombordo.
A conversao steering->motores (mixer) e o rumo real (BNO055) virao de
modulos separados; aqui nada depende de hardware.
"""


def normalize_angle(deg):
    """Reduz um angulo ao intervalo (-180, 180]."""
    a = (deg + 180.0) % 360.0 - 180.0
    if a == -180.0:  # manter o limite superior fechado
        a = 180.0
    return a


def heading_error(target, current):
    """Erro de rumo normalizado (target - current) em (-180, 180].

    Evita o salto entre 359 e 0: de 359 para 1 o erro e +2, nao -358.
    """
    return normalize_angle(target - current)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


class HeadingController:
    """Controlador proporcional de rumo.

    steer = Kp * erro, limitado a [-max_steer, +max_steer].
    Sem termos integral/derivativo por agora (decisao de 2026-07-17):
    so aumentar a complexidade quando houver dados reais que a justifiquem.
    """

    def __init__(self, kp=2.0, max_steer=100.0):
        self.kp = kp
        self.max_steer = max_steer
        self.target = None

    def set_target(self, heading_deg):
        self.target = normalize_angle(heading_deg)

    def clear_target(self):
        self.target = None

    def update(self, current_heading):
        """Devolve o steering para o rumo atual. 0.0 se nao houver alvo."""
        if self.target is None:
            return 0.0
        err = heading_error(self.target, current_heading)
        return clamp(self.kp * err, -self.max_steer, self.max_steer)


if __name__ == "__main__":
    # Simulacao SINTETICA (sem hardware): um barco cujo rumo roda a uma
    # taxa proporcional ao steering. Serve so para ver o controlador a
    # convergir para o alvo. Os valores NAO sao medicoes reais.
    KP = 2.0
    ALVO = 90.0
    YAW_GAIN = 0.02  # graus por passo, por unidade de steering (sintetico)

    ctrl = HeadingController(kp=KP, max_steer=100.0)
    ctrl.set_target(ALVO)
    heading = 0.0

    print(f"[SIM] alvo={ALVO} deg, Kp={KP} (dados sinteticos, sem hardware)")
    for i in range(400):
        steer = ctrl.update(heading)
        heading = normalize_angle(heading + YAW_GAIN * steer)
        err = heading_error(ALVO, heading)
        if i % 20 == 0:
            print(f"passo {i:3d}: heading={heading:7.2f}  erro={err:7.2f}  steer={steer:7.2f}")
        if abs(err) < 0.1:
            print(f"[SIM] convergiu ao passo {i}: heading={heading:.2f}")
            break
