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

print("\n5. Órbitas circulares (modelo da proposta): raio constante e período")
DIAS = 9797.75   # 28/10/2026 em dias desde J2000 (aprox.)
for nome, (a, L0, n) in orb.ORBITAS.items():
    raios = [math.dist((0, 0, 0), orb.posicao(nome, DIAS + k * 37.3, "circular")) for k in range(50)]
    periodo_dias = 36525.0 * 360.0 / n
    linha(f"   {nome:9s} |P| constante = {a:.4f} UA; período = {periodo_dias:9.1f} dias",
          max(raios) - min(raios) < 1e-9)
terra_0 = orb.posicao("Terra", DIAS, "circular")
terra_ano = orb.posicao("Terra", DIAS + 36525.0 * 360.0 / orb.ORBITAS["Terra"][2], "circular")
linha("   Terra volta ao mesmo ponto depois de um período", math.dist(terra_0, terra_ano) < 1e-6)

print("\n6. Equação de Kepler E - e.sen(E) = M (método de Newton)")
for nome in ("Mercúrio", "Marte"):
    a, e, I, L, wb, Om = orb.elementos(nome, DIAS)
    M = (L - wb + 180) % 360 - 180
    E = orb.kepler(M, e)
    resto = E - math.degrees(e) * math.sin(math.radians(E)) - M
    linha(f"   {nome:9s} M = {M:8.3f}  E = {E:8.3f}  resto E - e.senE - M", f"{resto:.1e} graus")
linha("   e = 0  ->  E = M (a elipse vira círculo)", abs(orb.kepler(123.4, 0.0) - 123.4) < 1e-9)

print("\n7. Órbita elíptica: periélio e afélio")
for nome in orb.ELEMENTOS:
    a, e = orb.elementos(nome, DIAS)[:2]
    raios = [math.dist((0, 0, 0), p) for p in orb.orbita(nome, 3600, "elíptico", DIAS)]
    ok = abs(min(raios) - a * (1 - e)) < 1e-6 and abs(max(raios) - a * (1 + e)) < 1e-6
    linha(f"   {nome:9s} min = a(1-e) = {a*(1-e):7.4f}  max = a(1+e) = {a*(1+e):7.4f} UA", ok)
linha("   Rz(Omega).Rx(I).Rz(omega) é ortogonal (R^T R = I)",
      iguais(tf.multiplicar(tf.transposta(orb.matriz_orbita("Mercúrio", DIAS)), orb.matriz_orbita("Mercúrio", DIAS)),
             tf.identidade()))

print("\n8. Modelos x posição real (astropy, efeméride 'builtin'), 28/10/2026 12h UTC")
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
    print(f"   {'':9s} {'real':>6s} | {'circular':>8s} {'erro':>6s} | {'elíptico':>8s} {'erro':>6s} | {'dist. real':>10s} {'circ.':>7s} {'elípt.':>7s}")
    with solar_system_ephemeris.set("builtin"):
        sol = get_body_barycentric("sun", t)
        for nome, corpo in corpos.items():
            r = get_body_barycentric(corpo, t) - sol
            x, y, z = (r.x.to(u.au).value, r.y.to(u.au).value, r.z.to(u.au).value)
            ye = y * math.cos(eps) + z * math.sin(eps)          # equatorial -> eclíptica
            ze = -y * math.sin(eps) + z * math.cos(eps)
            lon_real = math.degrees(math.atan2(ye, x)) % 360
            dist_real = math.sqrt(x * x + ye * ye + ze * ze)
            res = []
            for qual in ("circular", "elíptico"):
                px, py, pz = orb.posicao(nome, d, qual)                # cena: x, y = norte, z
                lon = math.degrees(math.atan2(pz, px)) % 360
                res.append(((lon - lon_real + 180) % 360 - 180, math.sqrt(px * px + py * py + pz * pz)))
            print(f"   {nome:9s} {lon_real:6.1f} | {lon_real + res[0][0]:8.1f} {res[0][0]:+6.1f} | "
                  f"{lon_real + res[1][0]:8.1f} {res[1][0]:+6.2f} | {dist_real:10.3f} {res[0][1]:7.3f} {res[1][1]:7.3f}")
except ImportError:
    print("   astropy não instalado: comparação pulada.")

print("\n9. Sombras: raio angular do Sol e da lua vistos da superfície do planeta (valores reais)")
R_SOL_KM = 695_700.0
RAIO_PLANETA_KM = {"Terra": 6371.0, "Júpiter": 69911.0}   # raio médio (NASA Fact Sheet)
for planeta, lua in (("Terra", "Lua"), ("Júpiter", "Io"), ("Júpiter", "Ganimedes")):
    _, _, a_km, _, _, r_km, _ = next(l for l in orb.LUAS if l[0] == lua)
    dist_sol = math.dist((0, 0, 0), orb.posicao(planeta, DIAS, "elíptico")) * orb.UA_KM
    aS = math.degrees(math.asin(R_SOL_KM / dist_sol))
    aO = math.degrees(math.asin(r_km / (a_km - RAIO_PLANETA_KM[planeta])))
    tipo = "total (a lua cobre o Sol inteiro)" if aO >= aS else "anular (sobra um anel do Sol)"
    linha(f"   {lua:9s} sobre {planeta:7s}: Sol {aS:.3f}°, {lua} {aO:.3f}° (dist. média)", tipo)

print("\n10. Céu de hoje (ceu_hoje.py) x astropy: altura e azimute em Curitiba, 28/10/2026")
try:
    import warnings
    warnings.filterwarnings("ignore")
    from astropy.utils import iers
    iers.conf.auto_download = False
    from astropy.time import Time
    from astropy.coordinates import EarthLocation, AltAz, get_body, solar_system_ephemeris
    import astropy.units as u
    import ceu_hoje as ceu
    local = EarthLocation(lat=ceu.LATITUDE * u.deg, lon=ceu.LONGITUDE * u.deg, height=930 * u.m)
    corpos = {"Sol": "sun", "Mercúrio": "mercury", "Vênus": "venus", "Marte": "mars", "Júpiter": "jupiter",
              "Saturno": "saturn", "Urano": "uranus", "Netuno": "neptune"}
    pior_alt = pior_az = 0.0
    with solar_system_ephemeris.set("builtin"):
        for h in (0, 6, 21):
            quando = datetime(2026, 10, 28, h, tzinfo=timezone.utc)
            t = Time(quando)
            for nome, corpo in corpos.items():
                real = get_body(corpo, t, local).transform_to(AltAz(obstime=t, location=local))
                alt, az = ceu.altura_azimute(nome, orb.dias_desde_j2000(quando))
                pior_alt = max(pior_alt, abs(alt - real.alt.deg))
                pior_az = max(pior_az, abs((az - real.az.deg + 180) % 360 - 180))
    linha("   maior diferença de altura (24 casos)", f"{pior_alt:.2f} graus")
    linha("   maior diferença de azimute (24 casos)", f"{pior_az:.2f} graus")
except ImportError:
    print("   astropy não instalado: comparação pulada.")
