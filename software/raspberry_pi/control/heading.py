"""Controlo de rumo (heading hold) do SAILSAFE.

Contem apenas logica de controlo, independente de sensores e atuadores:
- normalize_angle: reduz um angulo ao intervalo (-180, 180]
- heading_error: erro entre rumo alvo e atual, ja normalizado
- HeadingController: controlador proporcional simples, com histerese no
  sentido de rotacao quando o erro anda perto de +/-180 (OPEN-018)

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


# Meia-largura, em graus, da banda a volta de +/-180 onde o sentido de
# rotacao fica comprometido. NAO e medido: 15 graus e uma escolha de
# secretaria, larga o suficiente para o ruido do rumo (~1 grau em repouso,
# bancada de 10-11) e para a ondulacao nao a atravessarem, estreita o
# suficiente para o pior caso ser rodar 195 graus em vez de 165. Rever com
# dados da agua. Zero desliga a histerese.
FLIP_BAND_DEG = 15.0


class HeadingController:
    """Controlador proporcional de rumo.

    steer = Kp * erro, limitado a [-max_steer, +max_steer].
    Sem termos integral/derivativo por agora (decisao de 2026-07-17):
    so aumentar a complexidade quando houver dados reais que a justifiquem.

    HISTERESE EM +/-180 (OPEN-018, observado na bancada a 2026-11-10)

    Com o barco virado ao contrario do alvo, o lado curto muda com decimas
    de grau: 180,2 -> 179,6 -> 180,1 dava steer +100, -100, +100 a 5 Hz. E
    matematica, nao ruido -- e no barco e leme todo a um lado e ao outro
    enquanto ele nao sair dali, que e precisamente quando nao sai, porque
    as duas ordens se anulam.

    Por isso, dentro de uma banda de +/-flip_band_deg a volta dos 180, o
    controlador COMPROMETE-SE com o primeiro sentido que escolheu e mantem-no
    ate o erro sair da banda. Se entretanto o lado curto passar a ser o
    outro, vai pelo comprido -- no maximo 180 + flip_band_deg em vez de
    180 - flip_band_deg. Fora da banda o comportamento e exatamente o de
    antes: sempre o lado curto.

    O compromisso vive no erro e nao no alvo, portanto um alvo que muda a
    cada ciclo (o bearing do WaypointNav) nao o perturba.
    """

    def __init__(self, kp=2.0, max_steer=100.0, flip_band_deg=FLIP_BAND_DEG):
        if not 0.0 <= flip_band_deg < 90.0:
            raise ValueError("flip_band_deg tem de estar em [0, 90)")
        self.kp = kp
        self.max_steer = max_steer
        self.flip_band_deg = flip_band_deg
        self.target = None
        self._turn = 0      # sentido comprometido na banda: +1, -1, 0 = nenhum

    def set_target(self, heading_deg):
        self.target = normalize_angle(heading_deg)

    def clear_target(self):
        self.target = None
        self._turn = 0

    @property
    def committed_turn(self):
        """+1 (estibordo), -1 (bombordo) ou 0 se nao ha sentido comprometido."""
        return self._turn

    def error(self, current_heading):
        """Erro que o controlador esta de facto a seguir, com a histerese.

        Fora da banda e o heading_error() normal, em (-180, 180]. Dentro
        dela pode sair desse intervalo -- ate +/-(180 + flip_band_deg) --
        quando o sentido comprometido deixou de ser o lado curto. Atualiza
        o compromisso: chamar uma vez por ciclo, como o update().
        """
        err = heading_error(self.target, current_heading)
        if self.flip_band_deg > 0.0 and abs(err) >= 180.0 - self.flip_band_deg:
            if self._turn == 0:
                self._turn = 1 if err > 0 else -1
            elif (err > 0) != (self._turn > 0):
                err += 360.0 * self._turn     # o lado comprido, no sentido ja escolhido
        else:
            self._turn = 0
        return err

    def update(self, current_heading):
        """Devolve o steering para o rumo atual. 0.0 se nao houver alvo."""
        if self.target is None:
            self._turn = 0
            return 0.0
        err = self.error(current_heading)
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
