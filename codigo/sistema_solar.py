"""Simulador 3D interativo do Sistema Solar - Projeto A3 (CGeRV, UNICURITIBA).

- Órbitas circulares (x = R cos theta, z = R sen theta) calculadas com as matrizes da
  Aula 6; o ângulo começa na posição média de hoje (dados do JPL/NASA, ver orbitas.py).
- Toda a cena usa Model Matrix 4x4 própria (transformacoes.py): M = T . R . S.
- Três modos de escala (tecla R):
  proporcional (padrão): distâncias na proporção real entre si e tamanhos na
    proporção real entre si; os corpos ficam ~47x maiores para serem visíveis;
  real: tamanhos e distâncias no mesmo fator (1 UA = 100 unidades);
  compacto: distâncias e tamanhos comprimidos para ver tudo de uma vez.
- 20 luas principais, inclinação do eixo dos planetas, anéis de Saturno no equador.
- Texturas UV (Solar System Scope, CC BY 4.0; ver texturas.py) e iluminação Lambert.
- Câmera de espectador: livre (mouse olha, WASD voa) ou 3ª pessoa seguindo um corpo.

Controles: ver AJUDA abaixo (tecla H esconde/mostra a interface).

Uso:
    python sistema_solar.py                  # janela interativa
    python sistema_solar.py --captura a.png  # salva uma imagem e encerra
    opções: --foco Terra  --dist 6  --data 2026-10-28  --real  --dias 0
"""
import math
import sys
from datetime import datetime, timezone

from ursina import (Ursina, Entity, Mesh, Vec3, color, window, application, camera, time, Text,
                    held_keys, mouse, clamp)
from panda3d.core import Filename

import dados_planetas as dp
import transformacoes as tf
import orbitas as orb
from shader_solar import sombreamento_solar
from texturas import textura, esfera_uv, anel_uv

# ---------------------------------------------------------------- argumentos
ARGS = sys.argv[1:]


def arg(nome, padrao=None):
    return ARGS[ARGS.index(nome) + 1] if nome in ARGS else padrao


CAPTURA = arg("--captura")
FOCO_INICIAL = arg("--foco", "Sol")
DIST_INICIAL = float(arg("--dist", "0"))           # 0 = automático
DATA = arg("--data")
inicio = (datetime.strptime(DATA, "%Y-%m-%d").replace(tzinfo=timezone.utc) if DATA
          else datetime.now(timezone.utc))
dias = orb.dias_desde_j2000(inicio) + float(arg("--dias", "0"))
MODOS = ["proporcional", "real", "compacto"]          # tecla R alterna nesta ordem
modo = "real" if "--real" in ARGS else "compacto" if "--compacto" in ARGS else "proporcional"

app = Ursina(title="Sistema Solar 3D - A3", borderless=False, size=(1280, 720) if CAPTURA else None)
window.color = color.black
window.exit_button.visible = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False
window.fps_counter.enabled = not CAPTURA
camera.fov = 70

# ---------------------------------------------------------------- escalas
K_REAL = 100.0                       # real: 1 UA = 100 unidades, corpos no mesmo fator
# proporcional: distâncias na proporção real (1 UA = 250 un.) e tamanhos na proporção
# real entre si (raio da Terra = 0,5 un.); corpos ampliados ~47x em relação às distâncias
D_PROP = 250.0
S_PROP = 0.5 / 6371.0
R_SOL_KM = 695_700.0
RAIO_KM = {p[0]: p[4] / 2 for p in dp.PLANETAS}
ROT_H = {p[0]: p[5] for p in dp.PLANETAS}


def km_corpo(km):
    """Tamanhos (e distâncias das luas) em km -> unidades da cena."""
    return km / orb.UA_KM * K_REAL if modo == "real" else km * S_PROP


def raio_planeta(nome):
    return dp.raio_visual(RAIO_KM[nome] * 2) if modo == "compacto" else km_corpo(RAIO_KM[nome])


def raio_sol():
    return dp.RAIO_SOL if modo == "compacto" else km_corpo(R_SOL_KM)


LUAS_AMPLIADAS = 4.0   # proporcional: luas 4x maiores que a proporção real (aviso na tela)


def raio_lua(r_km):
    if modo == "compacto":
        return 0.05 + 0.1 * math.log10(max(r_km, 10) / 10)
    return km_corpo(r_km) * (LUAS_AMPLIADAS if modo == "proporcional" else 1.0)


def dist_lua(a_km, planeta):
    if modo != "compacto":
        return km_corpo(a_km)
    # compacto: cada lua ganha a sua faixa (mesma ordem do real, sem sobrepor);
    # em Saturno começa por fora dos anéis (2,27 raios)
    ordem = sorted(l[2] for l in orb.LUAS if l[1] == planeta).index(a_km)
    inicio = 2.7 if planeta == "Saturno" else 1.9
    return raio_planeta(planeta) * (inicio + 0.65 * ordem)


def para_cena(x, y, z):
    """Posição em UA (eixos da cena, y = norte da eclíptica) -> unidades da cena.
    Real e proporcional: distância proporcional. Compacto: direção real, distância
    6 + 14*sqrt(r) (raiz comprime os externos; 14 separa Vênus da Terra alinhados)."""
    v = Vec3(x, y, z)
    if modo == "real":
        return v * K_REAL
    if modo == "proporcional":
        return v * D_PROP
    r = v.length()
    return v.normalized() * (6.0 + 14.0 * math.sqrt(r)) if r > 0 else v


# ---------------------------------------------------------------- estrelas (fundo)
import random
random.seed(42)
pts = []
for _ in range(1500):
    a, c = random.uniform(0, 2 * math.pi), random.uniform(-1, 1)
    s_ = math.sqrt(1 - c * c)
    pts.append(Vec3(s_ * math.cos(a), c, s_ * math.sin(a)) * 10)
estrelas = Entity(model=Mesh(vertices=pts, mode="point", thickness=2), color=color.white66, unlit=True)
estrelas.setBin("background", 0)
estrelas.setDepthWrite(False)
estrelas.setDepthTest(False)


# ---------------------------------------------------------------- corpos
# Cada corpo recebe uma Model Matrix 4x4 calculada aqui na CPU com transformacoes.py
# (notação da Aula 6: P' = M . P, coordenadas homogêneas) e enviada pronta à GPU.
#
#   Sol:      M = S(2R)
#   Planeta:  M = T(posição orbital) . Rz(obliquidade) . Ry(rotação própria) . S(2r)
#   Lua:      M = T(posição do planeta) . Rz(obliquidade) . Rx(inclinação)
#                 . Ry(ângulo na órbita) . T(d, 0, 0) . S(2r)
#   Anéis:    M = T(posição de Saturno) . Rz(obliquidade) . S(r)
#
# Lendo da direita para a esquerda: a esfera (raio 0,5) é escalada, girada no próprio
# eixo, inclinada e só então transladada para a órbita. Na lua, T(d,0,0) vem ANTES de
# Ry: transladar e depois rotacionar faz a lua girar em volta do planeta (órbita);
# na ordem inversa ela só giraria no lugar - o exemplo de não-comutatividade da aula.
from panda3d.core import LMatrix4f


def enviar_matriz(ent, M):
    """Entrega M à GPU. O Panda3D usa vetor LINHA (p' = p . M_panda), então a matriz
    enviada é a transposta: (M . P)^T = P^T . M^T (propriedade da transposta, Aula 3)."""
    T = tf.transposta(M)
    ent.setMat(LMatrix4f(*[v for linha in T for v in linha]))
    ent.M = M
    ent.centro = Vec3(*tf.posicao_de(M))


def aplicar_textura(entidade, nome):
    tex = textura(nome)
    if tex:
        entidade.texture = tex
        entidade.color = color.white
    return tex


def novo_corpo(nome, cor, iluminado=True):
    e = Entity(model=esfera_uv(), color=color.rgb(*cor), collider="sphere",
               **({"shader": sombreamento_solar} if iluminado else {"unlit": True}))
    e.nome, e.raio, e.M, e.centro, e.formula = nome, 1.0, tf.identidade(), Vec3(0, 0, 0), ""
    aplicar_textura(e, nome.split(" ")[0])
    return e


selecionaveis = []      # corpos que podem ser focados (clique) e usados no near plane

sol = novo_corpo("Sol", (1.0, 0.78, 0.24), iluminado=False)
sol.formula = "M = S(2R)"
selecionaveis.append(sol)


class Planeta:
    def __init__(self, nome, cor):
        self.nome = nome
        self.corpo = novo_corpo(nome, cor)
        self.corpo.formula = "M = T(posição) . Rz(obliquidade) . Ry(rotação) . S(2r)"
        self.M_equador = tf.identidade()
        self.luas = []
        self.linhas = {m: self._linha(m) for m in MODOS}

    def _linha(self, m):
        global modo
        antigo, modo = modo, m
        pts = [para_cena(*p) for p in orb.orbita(self.nome)]
        modo = antigo
        return Entity(model=Mesh(vertices=pts, mode="line", thickness=1), color=color.rgba(1, 1, 1, 0.25))

    def escalar(self):
        self.corpo.raio = raio_planeta(self.nome)
        for m, linha in self.linhas.items():
            linha.enabled = m == modo
        for lua in self.luas:
            lua.escalar()

    def atualizar(self, d):
        pos = para_cena(*orb.posicao(self.nome, d))
        # rotação própria: ângulo = 360 graus x (tempo / período). Negativo = sentido
        # direto (de +x para +z, o mesmo das órbitas). |período| porque a rotação
        # retrógrada de Vênus e Urano já está na obliquidade > 90 graus.
        theta = -360.0 * (d / (abs(ROT_H[self.nome]) / 24.0) % 1.0)
        self.M_equador = tf.compor(tf.translacao(pos.x, pos.y, pos.z), tf.rot_z(orb.OBLIQUIDADE[self.nome]))
        enviar_matriz(self.corpo, tf.compor(self.M_equador, tf.rot_y(theta), tf.escala(2 * self.corpo.raio)))
        for lua in self.luas:
            lua.atualizar(d)


class Lua:
    def __init__(self, planeta, nome, a_km, periodo, incl, r_km, cor, fase):
        self.planeta, self.nome, self.a_km, self.r_km = planeta, nome, a_km, r_km
        self.periodo, self.fase, self.incl = abs(periodo), fase, incl   # Tritão: retrógrada pela inclinação 157 graus
        self.corpo = novo_corpo(nome, cor)
        self.corpo.nome = f"{nome} (lua de {planeta.nome})"
        self.corpo.formula = "M = T(planeta) . Rz(obliq.) . Rx(incl.) . Ry(órbita) . T(d,0,0) . S(2r)"
        planeta.luas.append(self)

    def escalar(self):
        self.corpo.raio = raio_lua(self.r_km)
        self.d = dist_lua(self.a_km, self.planeta.nome)

    def atualizar(self, d):
        ang = -(360.0 * d / self.periodo + self.fase)          # negativo = sentido direto
        if self.nome == "Lua":                                  # a Lua orbita perto da eclíptica
            c = self.planeta.corpo.centro
            base = tf.translacao(c.x, c.y, c.z)
        else:                                                   # demais: equador do planeta
            base = self.planeta.M_equador
        M = tf.compor(base, tf.rot_x(self.incl), tf.rot_y(ang), tf.translacao(self.d, 0, 0),
                      tf.escala(2 * self.corpo.raio))
        enviar_matriz(self.corpo, M)


planetas = {}
for nome, cor, *_ in dp.PLANETAS:
    planetas[nome] = Planeta(nome, cor)
for i, (nome, pl, a_km, per, incl, r_km, cor) in enumerate(orb.LUAS):
    Lua(planetas[pl], nome, a_km, per, incl, r_km, cor, fase=math.degrees(i * 2.39996))   # fase NÃO real
for p in planetas.values():
    selecionaveis.append(p.corpo)
    selecionaveis += [l.corpo for l in p.luas]

# Anéis de Saturno no plano do equador: de 1,24 a 2,27 raios do planeta
# (borda interna do anel C a borda externa do anel A), UV radial
saturno = planetas["Saturno"]
aneis = Entity(model=anel_uv(1.24, 2.27), color=color.rgba(0.86, 0.78, 0.59, 0.8),
               double_sided=True, unlit=True)
if aplicar_textura(aneis, "Anéis"):
    aneis.color = color.rgba(1, 1, 1, 0.95)


def atualizar_corpos(d):
    enviar_matriz(sol, tf.escala(2 * sol.raio))
    for p in planetas.values():
        p.atualizar(d)
    enviar_matriz(aneis, tf.compor(saturno.M_equador, tf.escala(saturno.corpo.raio)))


def aplicar_escala():
    sol.raio = raio_sol()
    for p in planetas.values():
        p.escalar()


aplicar_escala()

# ---------------------------------------------------------------- câmera de espectador
# Estado: yaw/pitch (graus), posição. Modo "seguir": a câmera gira em volta do alvo
# a uma distância; modo "livre": voa pela cena. Movimento com aceleração suave.
cam = {"yaw": 0.0, "pitch": 35.0, "pos": Vec3(0, 0, 0), "vel": Vec3(0, 0, 0),
       "modo": "seguir", "alvo": sol, "dist": 1.0, "dist_alvo": 1.0,
       "de": Vec3(0, 0, 0), "trans": 1.0, "vel_mult": 1.0}
SENS = 90.0          # sensibilidade do mouse (graus por unidade de mouse.velocity)


def raio_de(ent):
    return ent.raio


def dist_padrao(ent):
    """Distância da câmera ao focar. Nos modos proporcional e compacto ela é a MESMA
    para todos os planetas, para dar para comparar os tamanhos (Júpiter enche a tela,
    Mercúrio fica pequeno). Só cresce se o corpo não couber na tela."""
    if ent is sol:
        return raio_sol() * {"compacto": 38, "real": 8, "proporcional": 30}[modo]
    if modo == "real":
        return raio_de(ent) * 6
    fixa = 9.0 if modo == "proporcional" else 6.0
    if "(lua de" in ent.nome:
        fixa /= 4
    return max(fixa, raio_de(ent) * 2.2)


def frente(yaw, pitch):
    """Direção do olhar = Ry(yaw) . Rx(pitch) . [0 0 1 0]^T  (w = 0: é direção, não ponto)."""
    x, y, z, _ = tf.aplicar(tf.compor(tf.rot_y(yaw), tf.rot_x(pitch)), tf.direcao(0, 0, 1))
    return Vec3(x, y, z)


def seguir(ent, instantaneo=False):
    """Passa a seguir `ent` em 3ª pessoa. A transição sai do ponto que estava
    sendo olhado e desliza até o novo corpo (sem salto de câmera)."""
    if instantaneo:
        cam["de"] = ent.centro
    elif cam["modo"] == "seguir":
        cam["de"] = ponto_focado()
    else:
        cam["de"] = camera.world_position + frente(cam["yaw"], cam["pitch"]) * cam["dist"]
    cam["modo"], cam["alvo"] = "seguir", ent
    cam["dist_alvo"] = dist_padrao(ent)
    cam["trans"] = 1.0 if instantaneo else 0.0
    if instantaneo:
        cam["dist"] = cam["dist_alvo"]


def ponto_focado():
    alvo = cam["alvo"].centro
    t = cam["trans"]
    s = t * t * (3 - 2 * t)                       # suavização (smoothstep)
    return cam["de"] + (alvo - cam["de"]) * s


def livre():
    if cam["modo"] == "livre":
        return
    cam["modo"] = "livre"
    cam["pos"] = camera.world_position
    cam["vel"] = Vec3(0, 0, 0)


def distancia_superficie():
    """Distância da câmera à superfície do corpo mais próximo (para near plane e velocidade)."""
    p = camera.world_position
    return min(max((e.centro - p).length() - raio_de(e), 1e-7) for e in selecionaveis)


def atualizar_camera(dt):
    # olhar com o mouse (cursor travado), como câmera de espectador
    if mouse.locked:
        cam["yaw"] += mouse.velocity[0] * SENS
        cam["pitch"] = clamp(cam["pitch"] - mouse.velocity[1] * SENS, -89, 89)
    f = frente(cam["yaw"], cam["pitch"])

    mover = Vec3(held_keys["d"] - held_keys["a"], held_keys["space"] - max(held_keys["control"], held_keys["left control"]),
                 held_keys["w"] - held_keys["s"])
    if mover.length() > 0 and not CAPTURA:
        livre()

    if cam["modo"] == "seguir":
        cam["trans"] = min(1.0, cam["trans"] + dt / 0.9)
        cam["dist"] += (cam["dist_alvo"] - cam["dist"]) * (1 - math.exp(-dt * 6))
        alvo = ponto_focado()
        camera.world_position = alvo - f * cam["dist"]
    else:
        # velocidade proporcional à distância até o corpo mais próximo: rápido no vazio,
        # devagar perto dos planetas (funciona nas duas escalas)
        base = clamp(distancia_superficie() * 1.2, 1e-5 if modo == "real" else 0.02, 2000.0)
        alvo_vel = Vec3(0, 0, 0)
        if mover.length() > 0:
            dirr = (camera.right * mover.x + Vec3(0, 1, 0) * mover.y + f * mover.z).normalized()
            alvo_vel = dirr * base * cam["vel_mult"] * (4 if held_keys["shift"] else 1)
        cam["vel"] += (alvo_vel - cam["vel"]) * (1 - math.exp(-dt * 5))     # acelera e freia suave
        cam["pos"] += cam["vel"] * dt
        camera.world_position = cam["pos"]
    camera.rotation = Vec3(cam["pitch"], cam["yaw"], 0)

    # planos de recorte: perto da superfície mais próxima (escala real tem corpos minúsculos)
    camera.clip_plane_near = clamp(distancia_superficie() * 0.3, 1e-6, 0.1)
    # profundidade de 24 bits: a razão far/near precisa ficar perto de 1e6 ou a imagem some
    camera.clip_plane_far = min(2e4, max(camera.clip_plane_near * 1.5e6, 100.0))
    estrelas.world_position = camera.world_position
    estrelas.scale = max(camera.clip_plane_near * 20, 1e-4)


# ---------------------------------------------------------------- tempo e interface
VELOCIDADES = [(1 / 86400, "tempo real"), (1 / 24, "1 hora/s"), (0.25, "6 horas/s"), (1, "1 dia/s"),
               (2, "2 dias/s"), (7, "1 semana/s"), (30, "1 mês/s"), (100, "100 dias/s"), (365.25, "1 ano/s")]
estado = {"vel": 1, "pausa": False, "hud": True, "matriz": False}      # começa em 1 hora/s (luas com período real)

AJUDA = ("Mouse: olhar | WASD: voar | Espaço/Ctrl: subir/descer | Shift: rápido | Roda: zoom/velocidade\n"
         "1-8: focar planeta (Mercúrio a Netuno; o mouse gira em volta) | F: seguir/livre\n"
         "Tab: soltar o mouse (clique no Sol ou numa lua para focar) | +/-: velocidade do tempo\n"
         "P: pausar tudo (solta o mouse) | Esc: fechar | "
         "R: escala | M: matriz do corpo | H: esconder interface")
ajuda = Text(AJUDA, position=(-0.87, 0.48), scale=0.75, color=color.rgba(1, 1, 1, 0.8))
status = Text("", position=(-0.87, -0.43), scale=0.9)
painel = Text("", position=(0.28, 0.40), scale=0.8, color=color.rgba(0.85, 1, 0.85, 0.95))


def nome_foco():
    return cam["alvo"].nome if cam["modo"] == "seguir" else "câmera livre"


def atualizar_hud():
    data = orb.data_de(dias).astimezone()
    vel = "PAUSADO" if estado["pausa"] else VELOCIDADES[estado["vel"]][1]
    escala = {"real": "escala real", "proporcional": "proporcional (corpos 47x, luas 4x a mais)",
              "compacto": "compacto (didático)"}[modo]
    status.text = f"{data:%d/%m/%Y %H:%M}  |  {vel}  |  {escala}  |  {nome_foco()}"
    ajuda.enabled = status.enabled = estado["hud"] and not CAPTURA
    painel.enabled = estado["hud"] and estado["matriz"]
    if painel.enabled:
        a = cam["alvo"]
        c = a.centro
        painel.text = (f"{a.nome}\n{a.formula}\n\nM_total (calculada na CPU, P' = M . P):\n{tf.formatar(a.M, 2)}\n\n"
                       f"centro = M . [0 0 0 1]^T = ({c.x:.2f}, {c.y:.2f}, {c.z:.2f})\n"
                       f"distância ao Sol = |centro| = {tf.norma([c.x, c.y, c.z]):.2f} un.")
    window.fps_counter.enabled = estado["hud"] and not CAPTURA


ORDEM_NUM = ["Sol"] + [p[0] for p in dp.PLANETAS]


def input(key):
    global modo
    if CAPTURA:
        return
    if estado["pausa"] and key not in ("p", "escape", "h", "m"):
        return                                      # pausado: tudo congelado
    if key in [str(i) for i in range(1, 9)]:
        seguir(planetas[ORDEM_NUM[int(key)]].corpo)      # planeta no centro; mouse gira em volta
    elif key == "f":
        if cam["modo"] == "seguir":
            livre()
        else:
            seguir(cam["alvo"])
    elif key == "tab":
        mouse.locked = not mouse.locked
    elif key == "left mouse down" and not mouse.locked:
        if mouse.hovered_entity in selecionaveis:
            seguir(mouse.hovered_entity)
    elif key == "scroll up":
        if cam["modo"] == "seguir":
            cam["dist_alvo"] = max(cam["dist_alvo"] * 0.85, raio_de(cam["alvo"]) * 1.3)
        else:
            cam["vel_mult"] = min(cam["vel_mult"] * 1.25, 20)
    elif key == "scroll down":
        if cam["modo"] == "seguir":
            cam["dist_alvo"] *= 1 / 0.85
        else:
            cam["vel_mult"] = max(cam["vel_mult"] / 1.25, 0.05)
    elif key in ("+", "=", "gamepad dpad up") or key == "keypad +":
        estado["vel"] = min(estado["vel"] + 1, len(VELOCIDADES) - 1)
    elif key in ("-", "keypad -"):
        estado["vel"] = max(estado["vel"] - 1, 0)
    elif key == "p":
        estado["pausa"] = not estado["pausa"]
        mouse.locked = not estado["pausa"]          # pausado: solta o mouse
    elif key == "escape":
        application.quit()
    elif key == "r":
        modo = MODOS[(MODOS.index(modo) + 1) % len(MODOS)]
        aplicar_escala()
        atualizar_corpos(dias)
        if cam["modo"] == "seguir":
            seguir(cam["alvo"], instantaneo=True)
        else:
            seguir(sol, instantaneo=True)
    elif key == "m":
        estado["matriz"] = not estado["matriz"]
    elif key == "h":
        estado["hud"] = not estado["hud"]


# ---------------------------------------------------------------- início
atualizar_corpos(dias)
inicial = sol if FOCO_INICIAL == "Sol" else next((e for e in selecionaveis if e.nome.split(" ")[0] == FOCO_INICIAL), sol)
seguir(inicial, instantaneo=True)
if DIST_INICIAL:
    cam["dist"] = cam["dist_alvo"] = DIST_INICIAL if modo == "compacto" else DIST_INICIAL * raio_de(inicial)
mouse.locked = not CAPTURA
frames = 0


def update():
    global dias, frames
    dt = time.dt
    if estado["pausa"]:                             # pausa de verdade: nada se mexe
        atualizar_hud()
        return
    if not CAPTURA:
        dias += VELOCIDADES[estado["vel"]][0] * dt
    atualizar_corpos(dias)
    atualizar_camera(dt if not CAPTURA else 1.0)
    atualizar_hud()
    frames += 1
    if CAPTURA and frames == 8:
        base.win.saveScreenshot(Filename(CAPTURA))
        application.quit()


app.run()
