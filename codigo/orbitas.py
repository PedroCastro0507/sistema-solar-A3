"""Órbitas dos planetas e dados das luas (Projeto A3 - CGeRV).

Dois modelos (tecla O no simulador alterna entre eles):

1) CIRCULAR (o da proposta, só a matemática das aulas):
     theta(t) = L0 + n . t        (L0 = longitude média em J2000; n = graus por século)
     P = Ry(-theta) . [R 0 0 1]^T = [R cos(theta)  0  R sen(theta)  1]^T

2) ELÍPTICO (padrão, algoritmo do JPL com os mesmos dados da Tabela 1):
     M = L - w_barra                       (anomalia média)
     E - e.sen(E) = M                      (equação de Kepler, resolvida por Newton)
     no plano da órbita:  x' = a(cos E - e),  y' = a.raiz(1 - e^2).sen E
     no espaço:  P = Rz(Omega) . Rx(I) . Rz(omega) . [x' y' 0 1]^T
   As três rotações são as matrizes da Aula 6: omega gira a elipse dentro do próprio
   plano (onde fica o periélio), I inclina o plano e Omega gira a linha dos nodos.
   Nos eixos da cena (y = norte da eclíptica, sentido direto de +x para +z) a mesma
   composição fica  P = Ry(-Omega) . Rx(-I) . Ry(-omega) . [x' 0 y' 1]^T.

Fonte de todos os elementos (a, e, I, L, w_barra, Omega e as taxas por século):
JPL/NASA "Approximate Positions of the Planets", Tabela 1, válida de 1800 a 2050
(https://ssd.jpl.nasa.gov/planets/approx_pos.html, conferida em 29/10/2026).
Na Tabela 1, a "Terra" é o baricentro Terra-Lua.
"""
import math
from datetime import datetime, timezone, timedelta

import transformacoes as tf

UA_KM = 149_597_870.7
J2000 = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)

# nome: (a [UA], L0 [graus], n [graus por século])  - JPL Tabela 1 (modelo circular)
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

# Elementos keplerianos completos - JPL Tabela 1 (modelo elíptico).
# nome: ((a, e, I, L, w_barra, Omega) em J2000,  (taxas por século))
# a em UA; e sem unidade; ângulos em graus.
ELEMENTOS = {
    "Mercúrio": ((0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593),
                 (0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081)),
    "Vênus":    ((0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
                 (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418)),
    "Terra":    ((1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
                 (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0)),
    "Marte":    ((1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
                 (0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343)),
    "Júpiter":  ((5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
                 (-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106)),
    "Saturno":  ((9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
                 (-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794)),
    "Urano":    ((19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503),
                 (-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589)),
    "Netuno":   ((30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574),
                 (0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664)),
}

MODELOS = ["elíptico", "circular"]
modelo = "elíptico"          # o simulador troca com a tecla O

# Inclinação do eixo (graus) - NASA Planetary Fact Sheet. Acima de 90 graus = rotação
# retrógrada (Vênus, Urano); por isso o período de rotação é usado sem sinal.
OBLIQUIDADE = {"Mercúrio": 0.03, "Vênus": 177.4, "Terra": 23.4, "Marte": 25.2,
               "Júpiter": 3.1, "Saturno": 26.7, "Urano": 97.8, "Netuno": 28.3}

# Luas principais: (nome, planeta, a [km], período [dias, negativo = retrógrada],
#                   inclinação [graus], raio [km], cor RGB)
# a, período e inclinação: JPL "Planetary Satellite Mean Elements"
# (https://ssd.jpl.nasa.gov/sats/elem/sep.html) para Lua, Marte, Júpiter e Saturno;
# NASA NSSDC Uranian/Neptunian Satellite Fact Sheets para Urano e Netuno.
# Raios médios: JPL "Planetary Satellite Physical Parameters"
# (https://ssd.jpl.nasa.gov/sats/phys_par/, conferidos em 16/11/2026); Tritão pela
# ficha do NSSDC.
# Órbita das luas: circular, no equador do planeta (a Lua da Terra, na eclíptica).
# A fase inicial de cada lua NÃO é a real.
LUAS = [
    ("Lua",       "Terra",   384400, 27.322,     5.16, 1737.4, (0.80, 0.80, 0.80)),
    ("Fobos",     "Marte",     9375, 0.3187,     1.1,    11.1, (0.55, 0.50, 0.45)),
    ("Deimos",    "Marte",    23457, 1.2625,     1.8,     6.2, (0.60, 0.55, 0.50)),
    ("Io",        "Júpiter", 421800, 1.762732,   0.0,  1821.5, (0.95, 0.85, 0.35)),
    ("Europa",    "Júpiter", 671100, 3.525463,   0.5,  1560.8, (0.85, 0.80, 0.70)),
    ("Ganimedes", "Júpiter",1070400, 7.155588,   0.2,  2631.2, (0.60, 0.55, 0.50)),
    ("Calisto",   "Júpiter",1882700, 16.690440,  0.3,  2410.3, (0.45, 0.40, 0.35)),
    ("Mimas",     "Saturno", 186000, 0.942422,   1.6,   198.2, (0.75, 0.75, 0.75)),
    ("Encélado",  "Saturno", 238400, 1.370218,   0.0,   252.1, (0.95, 0.95, 0.95)),
    ("Tétis",     "Saturno", 295000, 1.887802,   1.1,   531.1, (0.85, 0.85, 0.85)),
    ("Dione",     "Saturno", 377700, 2.736916,   0.0,   561.4, (0.80, 0.80, 0.80)),
    ("Reia",      "Saturno", 527200, 4.517503,   0.3,   763.5, (0.78, 0.78, 0.78)),
    ("Titã",      "Saturno",1221900, 15.945448,  0.3,  2574.7, (0.90, 0.65, 0.30)),
    ("Jápeto",    "Saturno",3561700, 79.331002,  7.6,   734.3, (0.55, 0.50, 0.45)),
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
    """Modelo circular: theta(t) = L0 + n . T, com T em séculos desde J2000 (graus, 0..360)."""
    a, L0, n = ORBITAS[nome]
    return (L0 + n * dias / 36525.0) % 360.0


def elementos(nome, dias):
    """Elementos no instante: valor em J2000 + taxa . T (T em séculos julianos)."""
    T = dias / 36525.0
    base, taxa = ELEMENTOS[nome]
    return [v + t * T for v, t in zip(base, taxa)]


def kepler(M_graus, e):
    """Resolve E - e.sen(E) = M pelo método de Newton (passo 3 do JPL). Graus."""
    M = (M_graus + 180.0) % 360.0 - 180.0
    e_graus = math.degrees(e)
    E = M + e_graus * math.sin(math.radians(M))
    for _ in range(30):
        dM = M - (E - e_graus * math.sin(math.radians(E)))
        dE = dM / (1.0 - e * math.cos(math.radians(E)))
        E += dE
        if abs(dE) <= 1e-6:
            break
    return E


def matriz_orbita(nome, dias):
    """Rotação que leva o plano da órbita para o espaço da cena:
    Ry(-Omega) . Rx(-I) . Ry(-omega)  (= Rz(Omega) . Rx(I) . Rz(omega) nos eixos da eclíptica)."""
    a, e, I, L, w_barra, Omega = elementos(nome, dias)
    return tf.compor(tf.rot_y(-Omega), tf.rot_x(-I), tf.rot_y(-(w_barra - Omega)))


def posicao_eliptica(nome, dias):
    a, e, I, L, w_barra, Omega = elementos(nome, dias)
    E = math.radians(kepler(L - w_barra, e))
    x1 = a * (math.cos(E) - e)                          # x' (na direção do periélio)
    y1 = a * math.sqrt(1.0 - e * e) * math.sin(E)       # y'
    x, y, z, _ = tf.aplicar(matriz_orbita(nome, dias), tf.ponto(x1, 0, y1))
    return x, y, z


def posicao_circular(nome, dias):
    """P = Ry(-theta) . [R 0 0 1]^T  ->  (R cos theta, 0, R sen theta).
    Ry(-theta) porque nesta cena o sentido direto das órbitas vai de +x para +z."""
    R = ORBITAS[nome][0]
    x, y, z, _ = tf.aplicar(tf.rot_y(-angulo(nome, dias)), tf.ponto(R, 0, 0))
    return x, y, z


def posicao(nome, dias, qual=None):
    """Posição heliocêntrica (UA), eixos da cena (y = norte da eclíptica)."""
    qual = qual or modelo
    return posicao_eliptica(nome, dias) if qual == "elíptico" else posicao_circular(nome, dias)


def orbita(nome, n=360, qual=None, dias=None):
    """Pontos da órbita (UA). Circular: o ponto (R,0,0) girado de 0 a 360 graus.
    Elíptica: E de 0 a 360 graus no plano da órbita, levado ao espaço pela mesma matriz."""
    qual = qual or modelo
    if qual == "circular":
        R = ORBITAS[nome][0]
        return [tuple(tf.aplicar(tf.rot_y(-360.0 * k / n), tf.ponto(R, 0, 0))[:3]) for k in range(n + 1)]
    dias = 0.0 if dias is None else dias
    a, e, I, L, w_barra, Omega = elementos(nome, dias)
    R = matriz_orbita(nome, dias)
    b = a * math.sqrt(1.0 - e * e)
    pts = []
    for k in range(n + 1):
        E = 2 * math.pi * k / n
        pts.append(tuple(tf.aplicar(R, tf.ponto(a * (math.cos(E) - e), 0, b * math.sin(E)))[:3]))
    return pts
