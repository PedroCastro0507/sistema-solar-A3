"""Dados físicos e escalas visuais do Sistema Solar 3D (Projeto A3 - CGeRV).

Fonte dos valores reais: NASA Planetary Fact Sheet
(https://nssdc.gsfc.nasa.gov/planetary/factsheet/), conferida em 12/10/2026.
Os períodos orbitais foram obtidos da tabela em dias e convertidos em anos (dias / 365,25).
Períodos de rotação negativos indicam rotação retrógrada (Vênus e Urano).
"""
import math

# nome, cor RGB (0-1), semieixo maior (UA), período orbital (anos terrestres),
# diâmetro (km), período de rotação (horas)
PLANETAS = [
    ("Mercúrio", (0.62, 0.58, 0.55), 0.387, 88.0 / 365.25, 4879, 1407.6),
    ("Vênus",    (0.90, 0.75, 0.45), 0.723, 224.7 / 365.25, 12104, -5832.5),
    ("Terra",    (0.20, 0.45, 0.85), 1.000, 365.25 / 365.25, 12756, 23.93),
    ("Marte",    (0.80, 0.35, 0.20), 1.524, 687.0 / 365.25, 6792, 24.62),
    ("Júpiter",  (0.85, 0.65, 0.50), 5.203, 4331 / 365.25, 142984, 9.93),
    ("Saturno",  (0.90, 0.80, 0.55), 9.537, 10747 / 365.25, 120536, 10.66),
    ("Urano",    (0.55, 0.80, 0.85), 19.191, 30589 / 365.25, 51118, -17.24),
    ("Netuno",   (0.25, 0.35, 0.85), 30.069, 59800 / 365.25, 49528, 16.11),
]

# Escalas visuais (decisão de projeto: a escala real é inviável na tela)
RAIO_SOL = 3.0            # unidades da cena


def raio_orbital_visual(ua: float) -> float:
    """Compressão de distâncias: R = 6 + 5*sqrt(UA) (mantém a ordem e cabe na tela)."""
    return 6.0 + 5.0 * math.sqrt(ua)


def raio_visual(diametro_km: float) -> float:
    """Compressão logarítmica de tamanhos: raio = 0.25 + 0.7*log10(d/4879) (Mercúrio 0,25; Júpiter ~1,28)."""
    return 0.25 + 0.7 * math.log10(diametro_km / 4879.0) + 0.0


def velocidade_angular(periodo_anos: float, ano_terrestre_em_s: float = 20.0) -> float:
    """Velocidade angular (rad/s) com 1 ano terrestre = `ano_terrestre_em_s` segundos."""
    return 2.0 * math.pi / (periodo_anos * ano_terrestre_em_s)


def velocidade_rotacao(periodo_horas: float, dia_terrestre_em_s: float = 4.0) -> float:
    """Velocidade de rotação (graus/s) com 1 dia terrestre = `dia_terrestre_em_s` s.
    Sinal negativo preserva a rotação retrógrada."""
    return 360.0 / (abs(periodo_horas) / 24.0 * dia_terrestre_em_s) * (1 if periodo_horas > 0 else -1)
