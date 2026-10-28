"""Vetores e matrizes de transformação 4x4 do simulador (Projeto A3 - CGeRV).

Segue a notação das aulas do Prof. Rubem (Aula 2 - vetores; Aula 3 - matrizes;
Aula 6 - "Transformações Lineares, Espaços Vetoriais e Coordenadas Homogêneas em CG"):

- Ponto como vetor coluna em coordenadas homogêneas  P = [x y z w]^T,
  com w = 1 para pontos e w = 0 para vetores de direção.
- Transformação:  P' = M . P
- Matrizes primárias: escala S(sx, sy, sz), translação T(tx, ty, tz) e rotações
  Rx, Ry, Rz (sentido anti-horário para ângulo positivo, regra da mão direita).
- Composição:  M_total = M3 . M2 . M1  (a da direita é aplicada primeiro).
  A ordem importa: rotacionar e depois transladar != transladar e depois rotacionar.
- M_total é calculada uma vez por quadro na CPU e enviada à GPU (Model Matrix).

Escrito sem NumPy de propósito, para cada conta ficar visível (linha x coluna).
"""
import math

# ------------------------------------------------------------------ vetores (Aula 2)


def soma(u, v):
    return [a + b for a, b in zip(u, v)]


def escalar(k, v):
    return [k * a for a in v]


def produto_escalar(u, v):
    """u . v = |u| |v| cos(ang). Zero = ortogonais. Usado na luz de Lambert (N . L)."""
    return sum(a * b for a, b in zip(u, v))


def produto_vetorial(u, v):
    """u x v: vetor perpendicular a u e a v (ex.: normal de uma face)."""
    return [u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0]]


def norma(v):
    return math.sqrt(produto_escalar(v, v))


def normalizar(v):
    n = norma(v)
    return [a / n for a in v] if n else list(v)


def ponto(x, y, z):
    return [x, y, z, 1.0]          # w = 1: sofre translação


def direcao(x, y, z):
    return [x, y, z, 0.0]          # w = 0: translação não afeta direções


# ------------------------------------------------------------------ matrizes (Aula 3)


def identidade():
    return [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]


def multiplicar(A, B):
    """(A B)[i][j] = soma_k A[i][k] B[k][j]  - linha de A vezes coluna de B."""
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def compor(*matrizes):
    """compor(M3, M2, M1) = M3 . M2 . M1 (M1 é aplicada primeiro ao ponto)."""
    M = identidade()
    for m in matrizes:
        M = multiplicar(M, m)
    return M


def aplicar(M, P):
    """P' = M . P (P é vetor coluna homogêneo de 4 componentes)."""
    return [sum(M[i][k] * P[k] for k in range(4)) for i in range(4)]


def transposta(M):
    return [[M[j][i] for j in range(4)] for i in range(4)]


# ------------------------------------------------------------------ transformações primárias (Aula 6)


def escala(sx, sy=None, sz=None):
    sy = sx if sy is None else sy
    sz = sx if sz is None else sz
    return [[sx, 0, 0, 0],
            [0, sy, 0, 0],
            [0, 0, sz, 0],
            [0, 0, 0, 1]]


def translacao(tx, ty, tz):
    return [[1, 0, 0, tx],
            [0, 1, 0, ty],
            [0, 0, 1, tz],
            [0, 0, 0, 1]]


def rot_x(graus):
    c, s = math.cos(math.radians(graus)), math.sin(math.radians(graus))
    return [[1, 0, 0, 0],
            [0, c, -s, 0],
            [0, s, c, 0],
            [0, 0, 0, 1]]


def rot_y(graus):
    c, s = math.cos(math.radians(graus)), math.sin(math.radians(graus))
    return [[c, 0, s, 0],
            [0, 1, 0, 0],
            [-s, 0, c, 0],
            [0, 0, 0, 1]]


def rot_z(graus):
    c, s = math.cos(math.radians(graus)), math.sin(math.radians(graus))
    return [[c, -s, 0, 0],
            [s, c, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]


def posicao_de(M):
    """Translação contida em M_total = M . [0 0 0 1]^T (origem local levada ao mundo)."""
    p = aplicar(M, ponto(0, 0, 0))
    return p[0], p[1], p[2]


def formatar(M, casas=3):
    largura = casas + 6
    return "\n".join("[" + " ".join(f"{v:{largura}.{casas}f}" for v in linha) + " ]" for linha in M)
