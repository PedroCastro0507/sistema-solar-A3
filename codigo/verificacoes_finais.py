"""Verificações numéricas da versão final do simulador (Projeto A3 - CGeRV).

Roda sem janela 3D:  python verificacoes_finais.py
Usa só transformacoes.py e orbitas.py (as mesmas funções do simulador).
A comparação com a posição real dos planetas usa o astropy, se estiver instalado
(pip install astropy); sem ele, essa parte é pulada.
"""
import math
from datetime import datetime, timezone

import orbitas as orb
import transformacoes as tf

TOL = 1e-9


def iguais(A, B, tol=TOL):
    return all(abs(a - b) < tol for la, lb in zip(A, B) for a, b in zip(la, lb))


def det3(M):
    """Determinante da parte 3x3 (regra de Sarrus, Aula 3)."""
    a = M
    return (a[0][0] * a[1][1] * a[2][2] + a[0][1] * a[1][2] * a[2][0] + a[0][2] * a[1][0] * a[2][1]
            - a[0][2] * a[1][1] * a[2][0] - a[0][0] * a[1][2] * a[2][1] - a[0][1] * a[1][0] * a[2][2])


def linha(texto, valor):
    print(f"{texto:<62} {valor}")


print("1. Matrizes de rotação 4x4 (Aula 6)")
for nome, R in (("Rx(37)", tf.rot_x(37)), ("Ry(37)", tf.rot_y(37)), ("Rz(37)", tf.rot_z(37))):
    linha(f"   {nome}: ortogonal (R^T R = I)", iguais(tf.multiplicar(tf.transposta(R), R), tf.identidade()))
    linha(f"   {nome}: determinante", round(det3(R), 12))
linha("   Ry(a) Ry(b) = Ry(a+b)", iguais(tf.multiplicar(tf.rot_y(25), tf.rot_y(50)), tf.rot_y(75)))
linha("   Rx(30) Rz(40) = Rz(40) Rx(30)  (comutam?)", iguais(tf.compor(tf.rot_x(30), tf.rot_z(40)), tf.compor(tf.rot_z(40), tf.rot_x(30))))

print("\n2. Coordenadas homogêneas: ponto (w = 1) e direção (w = 0)")
T = tf.translacao(5, 0, 0)
linha("   T(5,0,0) . [1 2 3 1]^T", tf.aplicar(T, tf.ponto(1, 2, 3)))
linha("   T(5,0,0) . [1 2 3 0]^T  (direção não se move)", tf.aplicar(T, tf.direcao(1, 2, 3)))

print("\n3. Não-comutatividade: lua a d = 2 do planeta, ângulo de 90 graus")
p = tf.ponto(0, 0, 0)
orbita = tf.aplicar(tf.compor(tf.rot_y(-90), tf.translacao(2, 0, 0)), p)
gira_no_lugar = tf.aplicar(tf.compor(tf.translacao(2, 0, 0), tf.rot_y(-90)), p)
linha("   Ry(-90) . T(2,0,0) . origem  (transladar e depois girar)", [round(v, 6) for v in orbita])
linha("   T(2,0,0) . Ry(-90) . origem  (girar e depois transladar)", [round(v, 6) for v in gira_no_lugar])

print("\n4. Transposta no envio à GPU: (M P)^T = P^T M^T")
M = tf.compor(tf.translacao(3, -1, 2), tf.rot_z(23.4), tf.rot_y(70), tf.escala(2))
P = tf.ponto(0.5, 0.2, -0.1)
coluna = tf.aplicar(M, P)
linha_vetor = [sum(P[k] * tf.transposta(M)[k][j] for k in range(4)) for j in range(4)]
linha("   M.P (vetor coluna) = P^T.M^T (vetor linha)", all(abs(a - b) < TOL for a, b in zip(coluna, linha_vetor)))

print("\n5. Órbitas circulares: raio constante e período")
DIAS = 9797.75   # 28/10/2026 em dias desde J2000 (aprox.)
for nome, (a, L0, n) in orb.ORBITAS.items():
    raios = [math.dist((0, 0, 0), orb.posicao(nome, DIAS + k * 37.3)) for k in range(50)]
    periodo_dias = 36525.0 * 360.0 / n
    linha(f"   {nome:9s} |P| constante = {a:.4f} UA; período = {periodo_dias:9.1f} dias",
          max(raios) - min(raios) < 1e-9)
terra_0 = orb.posicao("Terra", DIAS)
terra_ano = orb.posicao("Terra", DIAS + 36525.0 * 360.0 / orb.ORBITAS["Terra"][2])
linha("   Terra volta ao mesmo ponto depois de um período", math.dist(terra_0, terra_ano) < 1e-6)

print("\n6. Modelo circular x posição real (astropy, efeméride 'builtin')")
try:
    from astropy.time import Time
    from astropy.coordinates import get_body_barycentric, solar_system_ephemeris
    import astropy.units as u
    quando = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
    d = orb.dias_desde_j2000(quando)
    t = Time(quando)
    eps = math.radians(23.43928)
    corpos = {"Mercúrio": "mercury", "Vênus": "venus", "Terra": "earth", "Marte": "mars", "Júpiter": "jupiter",
              "Saturno": "saturn", "Urano": "uranus", "Netuno": "neptune"}
    with solar_system_ephemeris.set("builtin"):
        sol = get_body_barycentric("sun", t)
        for nome, corpo in corpos.items():
            r = get_body_barycentric(corpo, t) - sol
            x, y, z = (r.x.to(u.au).value, r.y.to(u.au).value, r.z.to(u.au).value)
            ye = y * math.cos(eps) + z * math.sin(eps)          # equatorial -> eclíptica
            lon_real = math.degrees(math.atan2(ye, x)) % 360
            lon_modelo = orb.angulo(nome, d)
            dif = (lon_modelo - lon_real + 180) % 360 - 180
            linha(f"   {nome:9s} longitude real {lon_real:6.1f} | modelo {lon_modelo:6.1f} | erro", f"{dif:+.1f} graus")
except ImportError:
    print("   astropy não instalado: comparação pulada.")
