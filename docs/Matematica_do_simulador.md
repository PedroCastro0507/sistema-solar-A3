# Matemática do Simulador do Sistema Solar (A3 — CGeRV)

Como cada conta do simulador usa o que foi visto nas aulas do Prof. Rubem. Código em `codigo/`.

## 1. Pontos e vetores em coordenadas homogêneas (Aula 2 e Aula 6)

Todo ponto é um vetor coluna `P = [x y z w]^T`:

- `w = 1` para **pontos** (sofrem translação);
- `w = 0` para **direções** (a translação não as afeta).

Exemplo no código: a direção do olhar da câmera é `[0 0 1 0]^T` (w = 0), e o centro de um planeta é `[0 0 0 1]^T` (w = 1). Arquivo: `transformacoes.py` (`ponto`, `direcao`).

## 2. Matrizes primárias 4×4 (Aula 6)

```
S(sx,sy,sz) = | sx  0   0   0 |     T(tx,ty,tz) = | 1 0 0 tx |
              | 0   sy  0   0 |                   | 0 1 0 ty |
              | 0   0   sz  0 |                   | 0 0 1 tz |
              | 0   0   0   1 |                   | 0 0 0 1  |

Ry(θ) = |  cos θ  0  sen θ  0 |     Rz(θ) = | cos θ  -sen θ  0  0 |
        |  0      1  0      0 |             | sen θ   cos θ  0  0 |
        | -sen θ  0  cos θ  0 |             | 0       0      1  0 |
        |  0      0  0      1 |             | 0       0      0  1 |
```

Também se usa Rx(θ). A transformação é sempre `P' = M · P`, com o produto feito linha × coluna (Aula 3). O código não usa NumPy, para que cada conta fique visível.

## 3. Órbita dos planetas: x = R·cos θ, z = R·sen θ

O ângulo cresce uniformemente com o tempo:

`θ(t) = L0 + n · t`

Aqui `L0` é a posição média em 01/01/2000 e `n` é a velocidade angular média. Os dois vêm da tabela do JPL/NASA. Por isso, ao abrir, cada planeta começa perto de onde está hoje.

A posição sai da matriz de rotação aplicada ao ponto `(R, 0, 0)`:

```
P = Ry(−θ) · [R 0 0 1]^T = [R·cos θ   0   R·sen θ   1]^T
```

O `R` é o raio da órbita (semieixo maior). O traço da órbita é o mesmo ponto girado de 0° a 360°. Arquivo: `orbitas.py`.

**Simplificações assumidas:**
- As órbitas são circulares e estão todas no mesmo plano.
- A posição é a média. Medido em 28/10/2026 contra o astropy (`verificacoes_finais.py`): Vênus e Netuno ficam a 0,7° da posição real, Terra a 1,8°, Júpiter, Saturno e Urano entre 4,9° e 6,1°, Marte a 9,4° e Mercúrio a 21,4° (as duas órbitas mais alongadas).

## 4. Matriz do modelo de cada corpo (composição, Aula 6)

A matriz combinada é calculada **uma vez por quadro na CPU** e enviada pronta à GPU (Model Matrix). Ela é lida da direita para a esquerda:

| Corpo | M_total |
|---|---|
| Sol | `S(2R)` |
| Planeta | `T(posição) · Rz(obliquidade) · Ry(rotação própria) · S(2r)` |
| Lua | `T(planeta) · Rz(obliquidade) · Rx(inclinação) · Ry(ângulo na órbita) · T(d,0,0) · S(2r)` |
| Anéis de Saturno | `T(Saturno) · Rz(obliquidade) · S(r)` |

No planeta, a ordem é esta:
1. A esfera de raio 0,5 é escalada.
2. Gira no próprio eixo, com `Ry`. O ângulo é `360° · t / período de rotação`.
3. Inclina o eixo, com `Rz(obliquidade)`. A Terra tem 23,4° e Urano 97,8°.
4. Vai para a órbita, com `T`.

**Não-comutatividade (exemplo da aula):** na lua, `T(d,0,0)` vem antes de `Ry`. Transladar e depois rotacionar faz a lua **girar em volta do planeta**. Na ordem inversa ela só giraria no lugar. É o "rotacionar e depois transladar ≠ transladar e depois rotacionar" da Aula 6.

Com a tecla **M**, o simulador mostra ao vivo a fórmula e os 16 números da `M_total` do corpo focado. Mostra também o centro, que é `M · [0 0 0 1]^T`, e a distância ao Sol, que é a norma do centro.

## 5. Transposta no envio à GPU (Aula 3)

O motor gráfico (Panda3D) usa vetor **linha**. Pela propriedade da transposta, `(M·P)^T = P^T·M^T`, então a matriz enviada é a `M^T`. Arquivo: `sistema_solar.py` (`enviar_matriz`).

## 6. Câmera (vetores e rotações)

A direção do olhar é `Ry(yaw) · Rx(pitch) · [0 0 1 0]^T`. Ao voar, a câmera anda na soma vetorial `frente·W/S + direita·A/D + cima·Espaço/Ctrl`. Esse vetor é normalizado (norma = 1) e multiplicado pela velocidade. Isso usa soma de vetores, multiplicação por escalar e norma, da Aula 2.

## 7. Textura UV e iluminação (Aulas 6 e 7)

- **Esfera paramétrica:**
  - `x = r·sen θ·cos φ`, `y = r·cos θ`, `z = r·sen θ·sen φ`
  - `u = φ/2π`, `v = 1 − θ/π`
  - Arquivo: `texturas.py`.
- **Luz difusa de Lambert:** `I = ambiente + (1 − ambiente)·max(0, N·L)`, com ambiente = 0,05. O `N·L` é o **produto escalar** entre a normal e a direção do Sol. Arquivo: `shader_solar.py`.

## 8. Escalas (tecla R)

| Modo | Distâncias | Tamanhos |
|---|---|---|
| Proporcional (padrão) | proporção real (1 UA = 250 un.) | proporção real entre si, ampliados ~47×; luas 4× a mais (para serem visíveis) |
| Real | 1 UA = 100 un. | mesmo fator das distâncias (planetas viram pontos) |
| Compacto | `6 + 14·√R` | comprimidos (log), luas em faixas fixas |

## Fontes dos dados

- Órbitas: JPL/NASA, *Approximate Positions of the Planets*, Tabela 1. https://ssd.jpl.nasa.gov/planets/approx_pos.html (acesso em 28 out. 2026).
- Luas: JPL, *Planetary Satellite Mean Elements*. https://ssd.jpl.nasa.gov/sats/elem/sep.html. NASA NSSDC, *Uranian Satellite Fact Sheet* e *Neptunian Satellite Fact Sheet*.
- Texturas: Solar System Scope, *Solar Textures*, CC BY 4.0. https://www.solarsystemscope.com/textures/.

## Limites

- Os raios das luas de Marte, Júpiter e Saturno e da nossa Lua não foram conferidos nesta versão.
- A posição inicial das luas na órbita não é a real.
- A direção para onde aponta o eixo de cada planeta é simplificada. Só o ângulo de inclinação é real.
