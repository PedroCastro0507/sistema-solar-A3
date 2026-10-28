"""Órbitas dos planetas e dados das luas (Projeto A3 - CGeRV).

Modelo (só a matemática das aulas do Prof. Rubem):
  - Órbita circular no plano da eclíptica, raio R = semieixo maior a (UA).
  - Ângulo cresce de forma uniforme com o tempo:  theta(t) = L0 + n . t
    (L0 = longitude média em J2000; n = graus por século).
  - Posição pela matriz de rotação da Aula 6 aplicada ao ponto (R, 0, 0):
        P = Ry(-theta) . [R 0 0 1]^T  =  [R cos(theta)  0  R sen(theta)  1]^T
    ou seja, x = R cos(theta), z = R sen(theta) (eixo y = norte da eclíptica).

Fonte de a, L0 e n: JPL/NASA "Approximate Positions of the Planets", Tabela 1
(https://ssd.jpl.nasa.gov/planets/approx_pos.html, conferida em 28/10/2026).
Simplificações assumidas: órbitas circulares (sem excentricidade) e todas no mesmo
plano (sem inclinação orbital). Por isso a posição na tela fica perto da real, mas
não exata: o erro é maior em Mercúrio e Marte, que têm órbitas mais alongadas.
"""
from datetime import datetime, timezone, timedelta

import transformacoes as tf

UA_KM = 149_597_870.7
J2000 = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)

# nome: (a [UA], L0 [graus], n [graus por século])  - JPL Tabela 1
ORBITAS = {
    "Mercúrio": (0.38709927, 252.25032350, 149472.67411175),
    "Vênus":    (0.72333566, 181.97909950, 58517.81538729),
    "Terra":    (1.00000261, 100.46457166, 35999.37244981),
    "Marte":    (1.52371034, -4.55343205, 19140.30268499),
    "Júpiter":  (5.20288700, 34.39644051, 3034.74612775),
    "Saturno":  (9.53667594, 49.95424423, 1222.49362201),
    "Urano":    (19.18916464, 313.23810451, 428.48202785),
    "Netuno":   (30.06992276, -55.12002969, 218.45945325),
}

# Inclinação do eixo (graus) - NASA Planetary Fact Sheet. Acima de 90 graus = rotação
# retrógrada (Vênus, Urano); por isso o período de rotação é usado sem sinal.
OBLIQUIDADE = {"Mercúrio": 0.03, "Vênus": 177.4, "Terra": 23.4, "Marte": 25.2,
               "Júpiter": 3.1, "Saturno": 26.7, "Urano": 97.8, "Netuno": 28.3}

# Luas principais: (nome, planeta, a [km], período [dias, negativo = retrógrada],
#                   inclinação [graus], raio [km], cor RGB)
# a, período e inclinação: JPL "Planetary Satellite Mean Elements"
# (https://ssd.jpl.nasa.gov/sats/elem/sep.html) para Lua, Marte, Júpiter e Saturno;
# NASA NSSDC Uranian/Neptunian Satellite Fact Sheets para Urano e Netuno.
# Raios: valores médios usuais da NASA (os de Urano e Netuno conferidos nas fichas
# do NSSDC; os demais NÃO conferidos nesta versão).
# Órbita das luas: circular, no equador do planeta (a Lua da Terra, na eclíptica).
# A fase inicial de cada lua NÃO é a real.
LUAS = [
    ("Lua",       "Terra",   384400, 27.322,     5.16, 1737.4, (0.80, 0.80, 0.80)),
    ("Fobos",     "Marte",     9375, 0.3187,     1.1,    11.1, (0.55, 0.50, 0.45)),
    ("Deimos",    "Marte",    23457, 1.2625,     1.8,     6.2, (0.60, 0.55, 0.50)),
    ("Io",        "Júpiter", 421800, 1.762732,   0.0,  1821.6, (0.95, 0.85, 0.35)),
    ("Europa",    "Júpiter", 671100, 3.525463,   0.5,  1560.8, (0.85, 0.80, 0.70)),
    ("Ganimedes", "Júpiter",1070400, 7.155588,   0.2,  2631.2, (0.60, 0.55, 0.50)),
    ("Calisto",   "Júpiter",1882700, 16.690440,  0.3,  2410.3, (0.45, 0.40, 0.35)),
    ("Mimas",     "Saturno", 186000, 0.942422,   1.6,   198.2, (0.75, 0.75, 0.75)),
    ("Encélado",  "Saturno", 238400, 1.370218,   0.0,   252.1, (0.95, 0.95, 0.95)),
    ("Tétis",     "Saturno", 295000, 1.887802,   1.1,   531.1, (0.85, 0.85, 0.85)),
    ("Dione",     "Saturno", 377700, 2.736916,   0.0,   561.4, (0.80, 0.80, 0.80)),
    ("Reia",      "Saturno", 527200, 4.517503,   0.3,   763.8, (0.78, 0.78, 0.78)),
    ("Titã",      "Saturno",1221900, 15.945448,  0.3,  2574.7, (0.90, 0.65, 0.30)),
    ("Jápeto",    "Saturno",3561700, 79.331002,  7.6,   734.5, (0.55, 0.50, 0.45)),
    ("Miranda",   "Urano",   129900, 1.413479,   0.0,   235.8, (0.70, 0.70, 0.70)),
    ("Ariel",     "Urano",   190900, 2.520379,   0.0,   578.9, (0.75, 0.75, 0.75)),
    ("Umbriel",   "Urano",   266000, 4.144176,   0.0,   584.7, (0.45, 0.45, 0.45)),
    ("Titânia",   "Urano",   436300, 8.705867,   0.0,   788.9, (0.70, 0.68, 0.65)),
    ("Oberon",    "Urano",   583500, 13.463234,  0.0,   761.4, (0.65, 0.60, 0.58)),
    ("Tritão",    "Netuno",  354760, -5.876854, 157.345, 1353.4, (0.85, 0.75, 0.75)),
]


def dias_desde_j2000(quando: datetime) -> float:
    return (quando - J2000).total_seconds() / 86400.0


def data_de(dias: float) -> datetime:
    return J2000 + timedelta(days=dias)


def angulo(nome, dias):
    """theta(t) = L0 + n . T, com T em séculos julianos desde J2000 (graus, 0..360)."""
    a, L0, n = ORBITAS[nome]
    return (L0 + n * dias / 36525.0) % 360.0


def posicao(nome, dias):
    """Posição heliocêntrica (UA), eixos da cena (y = norte da eclíptica):
    P = Ry(-theta) . [R 0 0 1]^T  ->  (R cos theta, 0, R sen theta).
    Ry(-theta) porque nesta cena o sentido direto das órbitas vai de +x para +z."""
    R = ORBITAS[nome][0]
    x, y, z, _ = tf.aplicar(tf.rot_y(-angulo(nome, dias)), tf.ponto(R, 0, 0))
    return x, y, z


def orbita(nome, n=360):
    """Pontos do círculo da órbita (UA): o mesmo ponto (R,0,0) girado de 0 a 360 graus."""
    R = ORBITAS[nome][0]
    return [tuple(tf.aplicar(tf.rot_y(-360.0 * k / n), tf.ponto(R, 0, 0))[:3]) for k in range(n + 1)]
