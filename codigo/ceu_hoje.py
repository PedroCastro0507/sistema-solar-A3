"""Céu de hoje: quais planetas aparecem no céu de Curitiba (Projeto A3 - CGeRV).

Usa sempre as órbitas ELÍPTICAS (orbitas.posicao_eliptica), porque no modelo circular
Mercúrio sai até 21 graus do lugar e o painel erraria.

Contas, passo a passo:
  1) Vetor Terra -> planeta (subtração de vetores, Aula 2):
         v = P_planeta - P_Terra            (eixos da eclíptica, em UA)
     O Sol visto da Terra é  -P_Terra.
  2) Ângulo entre o planeta e o Sol (produto escalar, Aula 2):
         cos(alongamento) = (v . s) / (|v| |s|)
     Perto do Sol (alongamento pequeno), o planeta some na claridade.
  3) Da eclíptica para o equador da Terra (rotação da Aula 6):
         v_eq = Rx(23,43928 graus) . v       (o eixo da Terra é inclinado 23,4 graus)
     Daí saem a ascensão reta (alfa) e a declinação (delta) do planeta.
  4) Hora do céu (tempo sideral de Greenwich, em horas):
         TSMG = 18,697375 + 24,065709824279 . D     (D = dias desde J2000, UT)
     e o ângulo horário  H = (TSMG - alfa) . 15 + longitude.
  5) Altura e direção no horizonte de Curitiba (latitude phi):
         sen(altura) = cos H cos delta cos phi + sen delta sen phi
         tan(azimute) = -sen H / (tan delta cos phi - sen phi cos H)
     azimute medido a partir do Norte, no sentido do Leste.

Fontes das contas:
  - Posição dos planetas e rotação eclíptica -> equador (epsilon = 23,43928 graus):
    JPL/NASA, "Approximate Positions of the Planets"
    (https://ssd.jpl.nasa.gov/planets/approx_pos.html, conferida em 29/10/2026).
  - Tempo sideral: U.S. Naval Observatory, "Computing Approximate Sidereal Time"
    (https://aa.usno.navy.mil/faq/GAST, conferida em 29/10/2026).
  - Altura e azimute: U.S. Naval Observatory, "Computing Altitude and Azimuth from
    Greenwich Apparent Sidereal Time" (https://aa.usno.navy.mil/faq/alt_az,
    conferida em 29/10/2026).
Simplificações: não corrige a precessão do eixo da Terra desde 2000, a refração da
atmosfera, o tempo de viagem da luz nem a diferença entre UT1 e UTC. Conferido contra o
astropy para Curitiba em 28/10/2026: erro de até 0,4 grau na altura e 0,7 grau no
azimute (verificacoes_finais.py, seção 10).
"""
import math
from datetime import timedelta, timezone

import orbitas as orb
import transformacoes as tf

# Observador: centro de Curitiba (latitude e longitude em graus; sul e oeste negativos)
LATITUDE = -25.4284
LONGITUDE = -49.2733
FUSO = timezone(timedelta(hours=-3), "BRT")   # horário de Brasília (sem horário de verão)
EPSILON = 23.43928                            # inclinação do eixo da Terra (JPL)

PLANETAS = ["Mercúrio", "Vênus", "Marte", "Júpiter", "Saturno", "Urano", "Netuno"]
A_OLHO_NU = {"Mercúrio", "Vênus", "Marte", "Júpiter", "Saturno"}   # Urano/Netuno: telescópio
DIRECOES = ["Norte", "Nordeste", "Leste", "Sudeste", "Sul", "Sudoeste", "Oeste", "Noroeste"]


def eclitica(nome, dias):
    """Posição heliocêntrica (UA) nos eixos da eclíptica (x, y no plano, z = norte).
    A cena usa y para cima, então: eclíptica (x, y, z) = cena (x, z, y)."""
    x, y, z = orb.posicao_eliptica(nome, dias)
    return [x, z, y]


def vetor_terra_para(nome, dias):
    """1) v = P_planeta - P_Terra.  O Sol: v = -P_Terra."""
    terra = eclitica("Terra", dias)
    if nome == "Sol":
        return tf.escalar(-1.0, terra)
    return tf.soma(eclitica(nome, dias), tf.escalar(-1.0, terra))


def alongamento(nome, dias):
    """2) Ângulo Sol-Terra-planeta pelo produto escalar (graus)."""
    v, s = vetor_terra_para(nome, dias), vetor_terra_para("Sol", dias)
    c = tf.produto_escalar(v, s) / (tf.norma(v) * tf.norma(s))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def alfa_delta(nome, dias):
    """3) v_eq = Rx(epsilon) . v  ->  ascensão reta (horas) e declinação (graus)."""
    x, y, z, _ = tf.aplicar(tf.rot_x(EPSILON), tf.direcao(*vetor_terra_para(nome, dias)))
    alfa = (math.degrees(math.atan2(y, x)) / 15.0) % 24.0
    delta = math.degrees(math.atan2(z, math.hypot(x, y)))
    return alfa, delta


def tempo_sideral(dias):
    """4) Tempo sideral médio de Greenwich (horas), fórmula do USNO."""
    return (18.697375 + 24.065709824279 * dias) % 24.0


def altura_azimute(nome, dias, lat=LATITUDE, lon=LONGITUDE):
    """5) Altura (graus acima do horizonte) e azimute (graus a partir do Norte, para Leste)."""
    alfa, delta = alfa_delta(nome, dias)
    H = math.radians((tempo_sideral(dias) - alfa) * 15.0 + lon)
    d, f = math.radians(delta), math.radians(lat)
    alt = math.asin(math.cos(H) * math.cos(d) * math.cos(f) + math.sin(d) * math.sin(f))
    az = math.atan2(-math.sin(H), math.tan(d) * math.cos(f) - math.sin(f) * math.cos(H))
    return math.degrees(alt), math.degrees(az) % 360.0


def direcao(az):
    return DIRECOES[int((az + 22.5) // 45) % 8]


def esta_escuro(dias):
    """Noite de verdade: Sol mais de 12 graus abaixo do horizonte."""
    return altura_azimute("Sol", dias)[0] < -12.0


def janela_da_noite(nome, dias, passo_min=10):
    """Procura nas próximas 24 h os momentos em que está escuro e o planeta está
    pelo menos 10 graus acima do horizonte. Devolve (início, fim, altura máx., azimute)."""
    passos = int(24 * 60 / passo_min)
    inicio = fim = None
    melhor = (-90.0, 0.0, None)
    for k in range(passos + 1):
        d = dias + k * passo_min / 1440.0
        if not esta_escuro(d):
            if inicio is not None:
                break
            continue
        alt, az = altura_azimute(nome, d)
        if alt >= 10.0:
            if inicio is None:
                inicio = d
            fim = d
            if alt > melhor[0]:
                melhor = (alt, az, d)
        elif inicio is not None:
            break
    if inicio is None:
        return None
    return inicio, fim, melhor[0], melhor[1], melhor[2]


def hora(dias):
    return orb.data_de(dias).astimezone(FUSO).strftime("%H:%M")


def relatorio(dias):
    """Texto do painel (tecla C)."""
    data = orb.data_de(dias).astimezone(FUSO)
    linhas = [f"CÉU DE CURITIBA a partir de {data:%d/%m/%Y %H:%M} (Brasília)", ""]
    alt_sol = altura_azimute("Sol", dias)[0]
    linhas.append(f"Sol agora: {alt_sol:+.0f} graus ({'noite' if alt_sol < -12 else 'dia' if alt_sol > 0 else 'crepúsculo'})")
    linhas.append("")
    for nome in PLANETAS:
        el = alongamento(nome, dias)
        janela = janela_da_noite(nome, dias)
        olho = "" if nome in A_OLHO_NU else " (só com telescópio)"
        if el < 15:
            linhas.append(f"{nome}: perto demais do Sol ({el:.0f} graus), não dá para ver")
        elif janela is None:
            linhas.append(f"{nome}: não sobe no céu escuro nas próximas 24 h")
        else:
            ini, fim, alt, az, _ = janela
            quando = f"por volta das {hora(ini)}" if hora(ini) == hora(fim) else f"{hora(ini)} às {hora(fim)}"
            linhas.append(f"{nome}{olho}: {quando}, até {alt:.0f} graus de altura, "
                          f"a {direcao(az)}")
    linhas += ["", "Conta: v = P_planeta - P_Terra; Rx(23,4) . v -> alfa, delta;",
               "sen(alt) = cos H cos delta cos phi + sen delta sen phi  (JPL e USNO)"]
    return "\n".join(linhas)


if __name__ == "__main__":
    from datetime import datetime
    print(relatorio(orb.dias_desde_j2000(datetime.now(timezone.utc))))
