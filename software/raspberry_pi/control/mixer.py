"""Mixer de propulsao do SAILSAFE.

Converte um comando de alto nivel (throttle + steering) em comandos
para os dois motores (esquerdo/direito), respeitando o protocolo
0-100 (so avante; os waterjets nao tem marcha atras).

throttle: 0..100  (impulso comum, avante)
steer:   -100..100 (viragem; positivo = estibordo/direita)
"""


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def mix(throttle, steer, lo=0, hi=100):
    """Devolve (left, right) em [lo, hi].

    steer > 0 (estibordo) => motor esquerdo mais rapido que o direito,
    fazendo o barco rodar para a direita. A saturacao em [0, 100] trata
    os casos em que throttle +/- steer sai dos limites.
    """
    left = clamp(throttle + steer, lo, hi)
    right = clamp(throttle - steer, lo, hi)
    return left, right
