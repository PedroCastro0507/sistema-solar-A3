"""Cálculos e gráficos parciais do Projeto A3 (sem janela 3D): órbitas, velocidades e matriz de rotação."""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import dados_planetas as dp

PASTA_IMG = "../img" if os.path.isdir("../img") else "../entrega"   # onde ficam as imagens

plt.rcParams.update({"font.family": "Liberation Serif", "font.size": 11})
NOMES = [p[0] for p in dp.PLANETAS]
COR = ["#8c8c8c", "#c9a24d", "#2f6fd0", "#c4522c", "#b88a68", "#c8b06a", "#5fb7c4", "#2d3fb0"]

# --- 1) Órbitas no plano XZ: x = R cos(t), z = R sin(t)
fig, ax = plt.subplots(figsize=(6.2, 6.2))
t = np.linspace(0, 2 * math.pi, 400)
for nome, cor, p in zip(NOMES, COR, dp.PLANETAS):
    R = dp.raio_orbital_visual(p[2])
    ax.plot(R * np.cos(t), R * np.sin(t), color=cor, lw=1.3, label=f"{nome} (R = {R:.1f})")
ax.plot(0, 0, "o", color="#f2b705", ms=10, label="Sol")
ax.set_aspect("equal"); ax.set_xlabel("x (unidades da cena)"); ax.set_ylabel("z (unidades da cena)")
ax.grid(alpha=.25); ax.legend(fontsize=7.5, loc="upper right", ncol=2)
fig.tight_layout(); fig.savefig(f"{PASTA_IMG}/grafico_orbitas_xz.png", dpi=200); plt.close(fig)

# --- 2) Velocidade angular orbital (rad/s) com 1 ano terrestre = 20 s
w = [dp.velocidade_angular(p[3]) for p in dp.PLANETAS]
fig, ax = plt.subplots(figsize=(6.2, 3.4))
ax.bar(NOMES, w, color=COR)
ax.set_yscale("log"); ax.set_ylabel("ω orbital (rad/s, escala log)")
ax.grid(axis="y", alpha=.25); plt.setp(ax.get_xticklabels(), rotation=30)
fig.tight_layout(); fig.savefig(f"{PASTA_IMG}/grafico_velocidades.png", dpi=200); plt.close(fig)

# --- 3) Tabela de parâmetros usados na cena
print("Planeta | UA | R_cena | T(anos) | w(rad/s) | raio_cena | rot(graus/s)")
for p in dp.PLANETAS:
    print(f"{p[0]} | {p[2]} | {dp.raio_orbital_visual(p[2]):.2f} | {p[3]} | {dp.velocidade_angular(p[3]):.4f} | "
          f"{dp.raio_visual(p[4]):.2f} | {dp.velocidade_rotacao(p[5]):.2f}")

# --- 4) Verificações numéricas
def Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

a = math.radians(37)
M = Ry(a)
print("\nRy(37°) ortogonal (R^T R = I):", np.allclose(M.T @ M, np.eye(3)))
print("det Ry(37°) =", round(float(np.linalg.det(M)), 12))
# rotação em Y não altera a coordenada y e preserva a norma
v = np.array([1.0, 2.0, 3.0]); u = M @ v
print("y preservado:", math.isclose(u[1], v[1]), "| norma preservada:", math.isclose(np.linalg.norm(u), np.linalg.norm(v)))
# composição Ry(a) Ry(b) = Ry(a+b)
b = math.radians(53)
print("Ry(a)Ry(b) = Ry(a+b):", np.allclose(Ry(a) @ Ry(b), Ry(a + b)))
# distância ao Sol constante ao longo da órbita (círculo)
for p in dp.PLANETAS:
    R = dp.raio_orbital_visual(p[2]); ang = np.linspace(0, 2 * math.pi, 50)
    assert np.allclose(np.hypot(R * np.cos(ang), R * np.sin(ang)), R)
print("Distância ao Sol constante nas 8 órbitas: True")
# Terra completa uma volta em 20 s
wT = dp.velocidade_angular(1.0)
print("Período simulado da Terra (s):", round(2 * math.pi / wT, 6))
# razão entre períodos obedece aos dados reais (Netuno/Terra)
print("Período simulado de Netuno (s, 163,7 anos x 20 s):", round(2 * math.pi / dp.velocidade_angular(59800 / 365.25), 1))
# translação em t = 5 s da Terra (quarto de volta): (0, R)
R = dp.raio_orbital_visual(1.0)
x, z = R * math.cos(wT * 5), R * math.sin(wT * 5)
print(f"Terra em t=5 s: x={x:.4f}, z={z:.4f} (esperado ~ (0, {R:.1f}))")

# --- 5) Sistemas lineares (Aula 4): desfazer uma rotação é resolver R x = u
x = np.linalg.solve(M, u)
print("\nSistema R x = u resolvido com numpy.linalg.solve recupera o vetor original:", np.allclose(x, v))
print("Inversa da rotação é a transposta (R^-1 = R^T):", np.allclose(np.linalg.inv(M), M.T))

# --- 6) Imagem como matriz RGB (Aula 4 prática): dia e noite na captura da Terra
import matplotlib.image as mpimg
img = mpimg.imread(f"{PASTA_IMG}/cena_terra_lua.png")[:, :, :3]        # matriz altura x largura x 3
alt, larg, _ = img.shape
lum = 0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1] + 0.0722 * img[:, :, 2]   # luminância
yy, xx = np.mgrid[0:alt, 0:larg]
cx, cy, r = 640, 360, 240                                             # disco do planeta na captura
disco = (xx - cx) ** 2 + (yy - cy) ** 2 <= r ** 2
lado_esq, lado_dir = disco & (xx < cx), disco & (xx >= cx)
print(f"\nCaptura da Terra: matriz {alt} x {larg} x 3 | pixels do disco: {int(disco.sum())}")
print(f"Luminância média, metade esquerda: {lum[lado_esq].mean():.3f} | metade direita: {lum[lado_dir].mean():.3f}")
print(f"Fração do disco com luminância < 0,05 (noite): {(lum[disco] < 0.05).mean():.1%}")
