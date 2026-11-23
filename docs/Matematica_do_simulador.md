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

## 3. Órbita dos planetas

O simulador tem dois modelos, e a tecla **O** troca entre eles. O padrão é o elíptico (3.2). O circular (3.1) é o da proposta.

### 3.1 Modelo circular: x = R·cos θ, z = R·sen θ

O ângulo cresce uniformemente com o tempo:

`θ(t) = L0 + n · t`

Aqui `L0` é a posição média em 01/01/2000 e `n` é a velocidade angular média. Os dois vêm da tabela do JPL/NASA. Por isso, ao abrir, cada planeta começa perto de onde está hoje.

A posição sai da matriz de rotação aplicada ao ponto `(R, 0, 0)`:

```
P = Ry(−θ) · [R 0 0 1]^T = [R·cos θ   0   R·sen θ   1]^T
```

O `R` é o raio da órbita (semieixo maior). O traço da órbita é o mesmo ponto girado de 0° a 360°. Arquivo: `orbitas.py`.

Nesse modelo as órbitas são círculos, todos no mesmo plano. Medido em 28/10/2026 contra o astropy (`verificacoes_finais.py`): Vênus e Netuno ficam a 0,7° da posição real, Terra a 1,8°, Júpiter, Saturno e Urano entre 4,9° e 6,1°, Marte a 9,4° e Mercúrio a 21,4° (as duas órbitas mais alongadas).

### 3.2 Modelo elíptico: equação de Kepler + três rotações

Mesma tabela do JPL, agora com todos os elementos: `a`, `e` (excentricidade), `I` (inclinação), `L`, `ϖ` (longitude do periélio) e `Ω` (longitude do nodo), cada um com a sua taxa por século.

1. **Anomalia média:** `M = L − ϖ`. É o ângulo "como se fosse círculo".
2. **Equação de Kepler:** `E − e·sen E = M`. Não tem solução direta, então é resolvida pelo método de Newton: `E ← E + (M − (E − e·sen E)) / (1 − e·cos E)`, repetido até a correção ficar menor que 10⁻⁶°.
3. **Ponto no plano da órbita:** `x' = a(cos E − e)`, `y' = a·√(1 − e²)·sen E`. É uma elipse com o Sol em um dos focos.
4. **Do plano da órbita para o espaço**, com três matrizes de rotação da Aula 6:

```
P = Rz(Ω) · Rx(I) · Rz(ω) · [x'  y'  0  1]^T        com ω = ϖ − Ω
```

Lendo da direita para a esquerda:
- `Rz(ω)` gira a elipse dentro do próprio plano, o que define onde fica o periélio.
- `Rx(I)` inclina o plano da órbita.
- `Rz(Ω)` gira a linha dos nodos.

Nos eixos da cena (y para cima), a mesma conta fica `Ry(−Ω)·Rx(−I)·Ry(−ω)·[x' 0 y' 1]^T`. Com `e = 0` e `I = 0`, ela vira exatamente o modelo circular. Arquivo: `orbitas.py` (`kepler`, `matriz_orbita`, `posicao_eliptica`).

**Resultado:** o erro em relação ao astropy caiu para menos de 0,1° em todos os planetas. Por exemplo, Mercúrio foi de 21,4° para 0,01° e Marte de 9,4° para 0,00°. A distância ao Sol também passa a variar entre o periélio `a(1 − e)` e o afélio `a(1 + e)`.

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
- **Luz difusa de Lambert:** `I = ambiente + (1 − ambiente)·max(0, N·L)·visível`, com ambiente = 0,05. O `N·L` é o **produto escalar** entre a normal e a direção do Sol. Arquivo: `shader_solar.py`.

## 7.1 Sombras projetadas (eclipses)

Para cada ponto `P` da superfície, o shader calcula `visível`, que é a fração do disco do Sol que esse ponto enxerga. Ela é testada contra cada corpo do mesmo sistema (centro `C` e raio `r`, enviados pela CPU como um vetor `[x y z r]`), usando só operações com vetores:

- `s = (Sol − P)/|Sol − P|` e `u = (C − P)/|C − P|`: direções normalizadas para o Sol e para o corpo.
- **Raio angular do corpo:** `aO = asen(r / |C − P|)`.
- **Raio angular do Sol:** `aS = asen(R_sol / d)`, com o tamanho e a distância **reais**. O Sol do desenho é ampliado, e usar esse tamanho deixaria todas as sombras borradas.
- **Separação angular:** `θ = atan2(|u × s|, u · s)`, com produto vetorial e produto escalar.

Com esses três ângulos:
- Se `θ ≥ aS + aO`, o corpo não cobre o Sol.
- Se o corpo cobre o Sol inteiro, o ponto fica na **umbra** (escuro).
- Entre os dois casos, o ponto fica na **penumbra**, com uma transição suave.

Isso produz:
- a sombra das luas nos planetas (eclipse do Sol), como o ponto preto de Io em Júpiter;
- as luas escurecendo dentro da sombra do planeta (eclipse da lua);
- a sombra de Saturno nos anéis.

**Anéis em Saturno:** o raio `P + t·s` é cortado pelo plano dos anéis, `n·(X − C) = 0`, o que dá `t = n·(C − P)/(n·s)`. A normal `n` é `M_equador · [0 1 0 0]^T` (w = 0, direção). Se o ponto de corte cai entre o raio interno e o externo, a luz é atenuada pela transparência da textura do anel.

**Conferência** (`verificacoes_finais.py`, seção 9): vista da Terra, a Lua na distância média tem 0,263° e o Sol 0,268°, por isso há eclipses totais e anulares. Vista de Júpiter, Io tem 0,297° e o Sol só 0,050°, por isso a sombra de Io em Júpiter é um ponto preto bem definido.

## 7.2 Céu de hoje (tecla C, `ceu_hoje.py`)

Mostra quais planetas aparecem no céu de Curitiba (latitude −25,43°, longitude −49,27°). As posições vêm **sempre** do modelo elíptico (3.2), porque o circular erraria Mercúrio em até 21°. As contas são estas:

1. **Do observador ao planeta (Aula 2):** `v = P_planeta − P_Terra`, uma subtração de vetores. O Sol visto da Terra é `−P_Terra`.
2. **Distância ao Sol no céu (Aula 2):** `cos(ângulo) = (v · s)/(|v|·|s|)`, pelo produto escalar. Abaixo de 15°, o planeta some na claridade do Sol.
3. **Da eclíptica para o equador (Aula 6):** `v_eq = Rx(23,43928°) · v`, porque o eixo da Terra é inclinado. Daí saem a ascensão reta `α` e a declinação `δ`.
4. **Hora do céu (tempo sideral):** `TSMG = 18,697375 + 24,065709824279·D` horas, com `D` = dias desde J2000. Depois vem o ângulo horário `H = (TSMG − α)·15 + longitude`.
5. **Altura e direção:**
   - `sen(alt) = cos H·cos δ·cos φ + sen δ·sen φ`
   - `tan(az) = −sen H / (tan δ·cos φ − sen φ·cos H)`, com `atan2` e o azimute medido a partir do Norte, girando para o Leste.

O painel procura nas próximas 24 h, de 10 em 10 minutos, quando o céu está escuro (Sol mais de 12° abaixo do horizonte) e o planeta está pelo menos 10° acima do horizonte.

**Fontes:**
- Passos 1 a 3: JPL, *Approximate Positions of the Planets*.
- Passo 4: U.S. Naval Observatory, *Computing Approximate Sidereal Time* (https://aa.usno.navy.mil/faq/GAST).
- Passo 5: USNO, *Computing Altitude and Azimuth from GAST* (https://aa.usno.navy.mil/faq/alt_az).

Todas foram conferidas em 29/10/2026.

**Conferência** (`verificacoes_finais.py`, seção 10): comparado com o Astropy em 24 casos (8 corpos × 3 horários de 28/10/2026), a maior diferença foi 0,39° na altura e 0,70° no azimute. O cálculo não inclui a precessão do eixo da Terra desde 2000 (cerca de 0,4°), a refração do ar nem o tempo de viagem da luz.

## 8. Escalas (tecla R)

| Modo | Distâncias | Tamanhos |
|---|---|---|
| Proporcional (padrão) | proporção real (1 UA = 250 un.) | proporção real entre si, ampliados ~47×; luas 4× a mais (para serem visíveis) |
| Real | 1 UA = 100 un. | mesmo fator das distâncias (planetas viram pontos) |
| Compacto | `6 + 14·√R` | comprimidos (log), luas em faixas fixas |

## Fontes dos dados

- Órbitas: JPL/NASA, *Approximate Positions of the Planets*, Tabela 1 e algoritmo da equação de Kepler. https://ssd.jpl.nasa.gov/planets/approx_pos.html (acesso em 29 out. 2026).
- Luas: JPL, *Planetary Satellite Mean Elements*. https://ssd.jpl.nasa.gov/sats/elem/sep.html. NASA NSSDC, *Uranian Satellite Fact Sheet* e *Neptunian Satellite Fact Sheet*.
- Texturas: Solar System Scope, *Solar Textures*, CC BY 4.0. https://www.solarsystemscope.com/textures/.

## Limites

- As órbitas das luas são circulares. No modo proporcional, as luas e as sombras delas aparecem 4 vezes maiores.
- Os raios das luas foram conferidos em 16/11/2026 na tabela "Planetary Satellite Physical Parameters" do JPL (https://ssd.jpl.nasa.gov/sats/phys_par/).
- A posição inicial das luas na órbita não é a real.
- A direção para onde aponta o eixo de cada planeta é simplificada. Só o ângulo de inclinação é real.
