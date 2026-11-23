# Simulador 3D do Sistema Solar — Projeto A3

> **EN:** Interactive 3D Solar System simulator in Python/Ursina built for a Computer Graphics course (UNICURITIBA). Every body's 4×4 model matrix is composed on the CPU from scale, rotation and translation matrices in homogeneous coordinates, with Keplerian elliptical orbits, UV-textured spheres, Lambert lighting with cast shadows (eclipses), 20 major moons and a spectator camera.

Projeto A3 da unidade curricular **Computação Gráfica e Realidade Virtual** (UNICURITIBA, Prof. Rubem Matimoto Koide). O simulador aplica vetores, matrizes e transformações em coordenadas homogêneas, como apresentados nas aulas.

![Painel da matriz de Júpiter](docs/imagens/painel_matriz.png)

## O que o simulador faz

- O Sol, os 8 planetas, a Lua e os anéis de Saturno aparecem com texturas reais (mapeamento UV). As outras 19 luas aparecem com cor sólida, a não ser que você baixe os mapas delas com `codigo/texturas/Baixar_texturas_das_luas.bat` (NASA/JPL).
- As órbitas são **elípticas**, pela equação de Kepler (`E − e·sen E = M`), e levadas ao espaço pelas rotações `Rz(Ω)·Rx(I)·Rz(ω)`. Com isso, cada planeta aparece na sua posição real do dia (diferença menor que 0,1° em relação ao Astropy). A tecla **O** troca para o modelo **circular** da proposta (`x = R·cos θ`, `z = R·sen θ`), para comparar.
- Cada corpo tem a sua matriz `M_total = T · R · S`, calculada na CPU e enviada à GPU. A tecla **M** mostra essa matriz ao vivo.
- Cada planeta gira no próprio eixo, com a inclinação real do eixo. Urano fica quase deitado, e os anéis de Saturno ficam no plano do equador.
- A iluminação é a de Lambert, `N·L`, com o Sol como fonte de luz.
- Há **sombras projetadas (eclipses)**: a sombra das luas nos planetas (como a de Io em Júpiter), os planetas escurecendo as luas, a sombra de Saturno nos anéis e a dos anéis em Saturno.

![Io e a sua sombra em Júpiter](docs/imagens/sombra_io_jupiter.png)
- Há três escalas (tecla **R**):
  - **proporcional** (padrão): tamanhos e distâncias na proporção real entre si;
  - **real**: o mesmo fator para tamanhos e distâncias;
  - **compacta**: tudo comprimido para caber na tela.
- A câmera é de espectador: o mouse olha, WASD voa e as teclas 1 a 8 seguem um planeta em 3ª pessoa.
- **Céu de hoje** (tecla **C**): mostra quais planetas aparecem no céu de Curitiba nas próximas 24 horas, com o horário, a altura e a direção para onde olhar. Conferido contra o Astropy: diferença de até 0,4° na altura e 0,7° na direção.

A matemática de cada parte, ligada às aulas, está em [docs/Matematica_do_simulador.md](docs/Matematica_do_simulador.md).

## Como rodar (Windows)

O simulador precisa de **Python 3.12 ou mais novo**, porque o Ursina 8.3.0 não instala no 3.11.

1. Confira a versão: `python --version`. Se for 3.11 ou mais antiga, instale o Python 3.13 (`winget install Python.Python.3.13`) ou baixe em [python.org](https://www.python.org/downloads/).
2. Na pasta `codigo`, instale a dependência:
   ```
   python -m pip install -r ..\requirements.txt
   ```
3. Rode:
   ```
   python sistema_solar.py
   ```

Se o `python` do terminal continuar sendo o 3.11, chame o 3.13 pelo caminho completo (no PowerShell):

```
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m pip install ursina==8.3.0
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" sistema_solar.py
```

**No PC da faculdade:** se não der para instalar programas no computador, confira antes da apresentação se ele já tem o Python 3.12 ou mais novo.

## Controles

| Tecla | Ação |
|---|---|
| Mouse | olhar (o cursor fica preso na janela) |
| W A S D | voar (para onde a câmera olha) |
| Espaço / Ctrl | subir / descer |
| Shift | mais rápido |
| Roda do mouse | aproximar ou afastar (seguindo um planeta) / velocidade do voo (câmera livre) |
| 1 – 8 | seguir Mercúrio … Netuno (o mouse gira em volta) |
| Tab | soltar o mouse (clique no Sol ou numa lua para seguir) |
| F | alternar entre seguir e voar livre |
| + / − | velocidade do tempo (de tempo real até 1 ano/s; começa em 1 hora/s) |
| P | pausar tudo (solta o mouse) |
| R | trocar a escala |
| O | trocar a órbita: elíptica (Kepler) ou circular |
| C | céu de hoje em Curitiba (quais planetas dá para ver) |
| M | mostrar a matriz 4×4 do corpo seguido |
| H | esconder a interface (para prints) |
| Esc | fechar |

Opções de linha de comando: `--captura arquivo.png` (salva uma imagem e fecha), `--foco Terra`, `--dist 6`, `--data 2026-10-28`, `--dias 0.5`, `--real`, `--compacto`, `--circular`, `--yaw 30`, `--pitch 10`, `--do-sol` (câmera do lado do Sol, para ver as sombras), `--ceu` (abre o painel do céu), `--matriz` (abre o painel da matriz).

Exemplo: a sombra de Io em Júpiter (imagem acima) sai com
`python sistema_solar.py --data 2026-10-28 --dias 0.278 --foco Júpiter --yaw -25 --pitch 10 --dist 9`.

## Estrutura

```
codigo/
  sistema_solar.py        cena, câmera, interface e Model Matrix de cada corpo
  transformacoes.py       vetores e matrizes 4x4 (S, T, Rx, Ry, Rz, composição) sem NumPy
  orbitas.py              órbitas elípticas (Kepler) e circulares; dados das luas
  ceu_hoje.py             céu de hoje: altura e direção dos planetas em Curitiba
  texturas.py             esfera paramétrica com UV, anel com UV e carregamento das texturas
  shader_solar.py         shader GLSL: iluminação de Lambert e sombras (eclipses)
  dados_planetas.py       dados físicos dos planetas (NASA Planetary Fact Sheet)
  verificacoes_finais.py  verificações das matrizes e das órbitas, sem janela 3D (python verificacoes_finais.py)
  resultados_parciais.py  verificações da entrega parcial (12/10/2026); grava gráficos em ../entrega/
  texturas/               texturas do Solar System Scope (CC BY 4.0)
docs/
  Matematica_do_simulador.md
  imagens/
```

## Desempenho medido

De **125 a 157 FPS** em um PC com GeForce RTX 3060 e Intel Core i7 de 11ª geração, com Python 3.13 e Ursina 8.3.0 (28/10/2026). Essa medição é de antes das órbitas elípticas e das sombras; a versão atual ainda não foi medida.

## Fontes e créditos

- Órbitas: JPL/NASA, *Approximate Positions of the Planets*, Tabela 1: https://ssd.jpl.nasa.gov/planets/approx_pos.html
- Luas: JPL, *Planetary Satellite Mean Elements*: https://ssd.jpl.nasa.gov/sats/elem/sep.html. NASA NSSDC, *Uranian* e *Neptunian Satellite Fact Sheets*.
- Céu de hoje: U.S. Naval Observatory, *Computing Approximate Sidereal Time* (https://aa.usno.navy.mil/faq/GAST) e *Computing Altitude and Azimuth* (https://aa.usno.navy.mil/faq/alt_az).
- Planetas: NASA, *Planetary Fact Sheet*: https://nssdc.gsfc.nasa.gov/planetary/factsheet/
- Texturas: [Solar System Scope](https://www.solarsystemscope.com/textures/), licença CC BY 4.0.
- Motor: [Ursina](https://www.ursinaengine.org/) 8.3.0 sobre o Panda3D.

## Limites conhecidos

- As órbitas elípticas usam os elementos médios do JPL (válidos de 1800 a 2050). Comparado com a posição real (Astropy, 28/10/2026), o erro ficou abaixo de 0,1° em todos os planetas. No modelo circular (tecla O), o erro vai de 0,7° (Vênus, Netuno) a 9,4° em Marte e 21,4° em Mercúrio. Veja `codigo/verificacoes_finais.py`.
- As órbitas das luas continuam circulares.
- No modo proporcional, as luas são 4 vezes maiores, então as sombras delas também são. Para calcular as sombras, o Sol usa o tamanho angular real visto de cada planeta, e não o Sol ampliado do desenho.
- A posição inicial das luas na órbita não é a real.
- No modo proporcional, as luas aparecem 4 vezes maiores que a proporção real, para ficarem visíveis.
- A direção do eixo de cada planeta é simplificada. Só o ângulo de inclinação é real.
