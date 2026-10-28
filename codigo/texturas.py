"""Texturas e malhas com coordenadas UV (Projeto A3 - CGeRV).

Texturas: Solar System Scope (https://www.solarsystemscope.com/textures/),
licença Creative Commons Attribution 4.0 International (CC BY 4.0).
Imagens em projeção equirretangular 2048x1024 (exceto o anel de Saturno).

Mapeamento UV da esfera (parametrização por latitude e longitude):
    theta (0 no polo norte, pi no polo sul), phi (0 a 2*pi ao redor do eixo Y)
    x = r sen(theta) cos(phi)   y = r cos(theta)   z = r sen(theta) sen(phi)
    u = phi / (2*pi)            v = 1 - theta / pi
Assim cada ponto da imagem (u, v) cai em uma longitude e latitude da esfera.
"""
import math
from functools import lru_cache
from pathlib import Path

from ursina import Mesh, Vec3, Vec2, Texture

PASTA = Path(__file__).resolve().parent / "texturas"

# Arquivos originais do Solar System Scope (2k = 2048 px de largura)
ARQUIVOS = {
    "Sol": "2k_sun.jpg",
    "Mercúrio": "2k_mercury.jpg",
    "Vênus": "2k_venus_atmosphere.jpg",
    "Terra": "2k_earth_daymap.jpg",
    "Lua": "2k_moon.jpg",
    "Marte": "2k_mars.jpg",
    "Júpiter": "2k_jupiter.jpg",
    "Saturno": "2k_saturn.jpg",
    "Anéis": "2k_saturn_ring_alpha.png",
    "Urano": "2k_uranus.jpg",
    "Netuno": "2k_neptune.jpg",
}


def textura(nome):
    """Carrega a textura do corpo `nome`. Aceita o nome original (2k_mars.jpg)
    ou o nome baixado com prefixo (A3tex_2k_mars.jpg). Sem o arquivo, devolve
    None e o corpo fica com a cor sólida de antes."""
    arquivo = ARQUIVOS.get(nome)
    if not arquivo:
        return None
    for candidato in (PASTA / arquivo, PASTA / ("A3tex_" + arquivo)):
        if candidato.exists():
            return Texture(candidato)
    return None


@lru_cache(maxsize=None)
def _dados_esfera(n_lat, n_lon, r):
    """Calcula vértices, normais, UV e triângulos uma única vez."""
    verts, uvs, normais, tris = [], [], [], []
    for i in range(n_lat + 1):
        theta = math.pi * i / n_lat
        for j in range(n_lon + 1):            # coluna extra: costura em u = 1
            phi = 2 * math.pi * j / n_lon
            n = Vec3(math.sin(theta) * math.cos(phi), math.cos(theta), math.sin(theta) * math.sin(phi))
            verts.append(n * r)
            normais.append(n)
            uvs.append(Vec2(j / n_lon, 1 - i / n_lat))
    linha = n_lon + 1
    for i in range(n_lat):
        for j in range(n_lon):
            a, b = i * linha + j, i * linha + j + 1
            c, d = a + linha, b + linha
            tris += [a, d, b, a, c, d]   # anti-horário visto de fora (face da frente)
    return verts, tris, uvs, normais


def esfera_uv(n_lat=48, n_lon=96, r=0.5):
    """Esfera paramétrica com normais e UV. r = 0,5 para ter diâmetro 1 (como a
    esfera padrão do Ursina), então a escala da entidade continua sendo o diâmetro.
    Cada chamada devolve uma malha nova: no Ursina uma malha só pode ter um dono."""
    verts, tris, uvs, normais = _dados_esfera(n_lat, n_lon, r)
    return Mesh(vertices=list(verts), triangles=list(tris), uvs=list(uvs), normals=list(normais), mode="triangle")


def anel_uv(r_int, r_ext, n=128):
    """Disco dos anéis: u vai de 0 (borda interna) a 1 (borda externa), igual à
    faixa horizontal da imagem 2k_saturn_ring_alpha.png."""
    verts, uvs, tris = [], [], []
    for k in range(n + 1):
        a = 2 * math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        verts += [Vec3(r_int * c, 0, r_int * s), Vec3(r_ext * c, 0, r_ext * s)]
        uvs += [Vec2(0, 0.5), Vec2(1, 0.5)]
    for k in range(n):
        i, j = 2 * k, 2 * (k + 1)
        tris += [i, i + 1, j + 1, i, j + 1, j]
    return Mesh(vertices=verts, triangles=tris, uvs=uvs, mode="triangle")
