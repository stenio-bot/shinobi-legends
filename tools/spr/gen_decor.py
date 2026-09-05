#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gerador de pixel art de DECORAÇÃO por código, estilo Tibia 7.x/8.x.

Desenha os PNGs de `assets-src/sprites/terrain/decor/` (arte própria, versionada
— nada vem da Tibia nem de NTO, ADR-002). São itens NOVOS de cenário (declarados
em `assets-src/sprites/tiles_decor.json`, formato igual ao `tiles.json`): ponte de
madeira, pedras, tocos, flores, tufos de grama, cogumelos, galho caído, poça
decorativa, tocha de rua em poste, placa de trilha, barril, caixote, cerca de
madeira e caminho de pedras soltas.

Reaproveita as paletas e as primitivas de desenho de `gen_terrain.py` (import
direto do módulo — mesma pasta) em vez de duplicá-las: `P_WOOD`, `P_STONE`,
`P_BARK`, `P_GRASS_DOT`, `P_FLOWER`, `P_PUDDLE`, `SHADOW`, `Rnd`, `put`, `rect`,
`ellipse`, `outline`, `shade`, `fbm`.

Fogueira do acampamento (id 1428) e tendas (id 7605) JÁ existem em
`gen_terrain.py`/`overrides/10_terrain.json` — não são redesenhadas aqui.
`tools/map/decor.py` reaproveita esses ids vanilla diretamente.

    .venv/bin/python tools/spr/gen_decor.py
"""
from __future__ import annotations

import math
import os

from PIL import Image

import gen_terrain as GT

CELL = GT.CELL
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT_DIR = os.path.join(ROOT, "assets-src", "sprites", "terrain", "decor")


# =========================================================== PONTE DE MADEIRA
def _bridge_planks(seed_shift=0):
    """Piso da ponte: tábuas horizontais (mesma técnica de `wood_floor`)."""
    img = Image.new("RGBA", (CELL, CELL), GT.P_WOOD[2])
    f = GT.fbm(CELL, 8080 + seed_shift, octaves=((3, 1.0), (16, 0.45)))
    px = img.load()
    for y in range(CELL):
        for x in range(CELL):
            band = (y // 8) % 3
            base = GT.P_WOOD[1 + band]
            v = f[y][x]
            px[x, y] = GT.shade(base, -10 if v < 0.4 else (10 if v > 0.68 else 0))
    for y in (7, 15, 23, 31):                    # emenda entre tábuas
        for x in range(CELL):
            GT.put(img, x, y, GT.P_WOOD[0])
            GT.put(img, x, y - 1, GT.shade(GT.P_WOOD[3], 8))
    rnd = GT.Rnd(9500 + seed_shift)
    for by in range(4):                          # pregos
        x = (by * 11 + 5) % CELL
        for yb in (3, 11, 19, 27):
            GT.put(img, x, yb, GT.shade(GT.P_WOOD[0], -6))
    return img


def bridge_center():
    """Tábua central da ponte — chão caminhável."""
    return _bridge_planks(0)


def bridge_head_west():
    """Cabeceira oeste: viga de ancoragem grossa na borda que encosta na margem."""
    img = _bridge_planks(1)
    GT.rect(img, 0, 0, 3, CELL - 1, GT.shade(GT.P_WOOD[0], -6))
    GT.rect(img, 0, 0, 3, 1, GT.P_WOOD[4])
    return img


def bridge_head_east():
    """Cabeceira leste: viga de ancoragem grossa do outro lado."""
    img = _bridge_planks(2)
    GT.rect(img, CELL - 4, 0, CELL - 1, CELL - 1, GT.shade(GT.P_WOOD[0], -6))
    GT.rect(img, CELL - 4, 0, CELL - 1, 1, GT.P_WOOD[4])
    return img


def _bridge_rail(edge):
    """Corrimão de madeira (item, NÃO chão) — vazado, só a grade sobre o vão.

    `edge`: "north" (grade encostada na borda de cima do tile) ou "south"
    (encostada na borda de baixo). Item de grupo `wall`, bloqueia 1 tile.
    """
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    y0 = 2 if edge == "north" else CELL - 14
    for x in (3, 15, 27):                        # mourões
        GT.rect(img, x - 1, y0, x + 1, y0 + 11, GT.P_WOOD[1])
        GT.rect(img, x - 1, y0, x - 1, y0 + 11, GT.P_WOOD[0])
        GT.rect(img, x - 1, y0, x + 1, y0, GT.P_WOOD[4])
    GT.rect(img, 0, y0, CELL - 1, y0 + 1, GT.P_WOOD[3])       # travessa de cima
    GT.rect(img, 0, y0 + 2, CELL - 1, y0 + 2, GT.P_WOOD[0])
    GT.rect(img, 0, y0 + 8, CELL - 1, y0 + 9, GT.P_WOOD[2])   # travessa de baixo
    GT.rect(img, 0, y0 + 10, CELL - 1, y0 + 10, GT.P_WOOD[0])
    return GT.outline(img)


def bridge_rail_north():
    return _bridge_rail("north")


def bridge_rail_south():
    return _bridge_rail("south")


# =========================================================== PEDRAS
def stone(v):
    """Pedra solta (pequena v=0 / média v=1) — decoração caminhável."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    r = 4.0 + v * 2.6
    cx, cy = 16, 20
    GT.ellipse(img, cx, int(cy + r * 0.7), r * 1.15, r * 0.4, GT.SHADOW)
    for i, c in enumerate(GT.P_STONE[:4]):
        rr = r * (1.0 - i * 0.18)
        GT.ellipse(img, cx - i, int(cy - i * 1.1), rr, rr * 0.78, c)
    return GT.outline(img)


def stone_small():
    return stone(0)


def stone_medium():
    return stone(1)


def stone_large():
    """Pedregulho 2x2 (64x64), ancorado no canto inferior direito — bloqueia."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    rnd = GT.Rnd(4400)
    cx, cy = 46, 50
    GT.ellipse(img, cx, cy + 11, 20, 6, GT.SHADOW)
    for i, c in enumerate(GT.P_STONE):
        rr = 18 - i * 3
        GT.ellipse(img, int(cx - i * 1.5), cy - i * 2, rr, rr * 0.82, c)
    for _ in range(7):                            # rachaduras
        x = cx - 8 + rnd.i(16)
        y = cy - 8 + rnd.i(12)
        GT.put(img, x, y, GT.shade(GT.P_STONE[0], -22), wrap=False)
    return GT.outline(img)


# =========================================================== TOCOS DE ÁRVORE
def stump(v):
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 27, 9, 3, GT.SHADOW)
    GT.rect(img, 12, 20, 20, 27, GT.P_BARK[0])            # base do toco
    GT.rect(img, 12, 20, 13, 27, GT.shade(GT.P_BARK[0], -8))
    for i, rr in enumerate((7, 5, 3)):                    # anéis concêntricos
        GT.ellipse(img, 16, 19 - v, rr, rr * 0.72, GT.P_BARK[1 + (i % 3)])
    GT.ellipse(img, 16, 19 - v, 1, 1, GT.P_BARK[3])
    if v == 1:                                            # lasca quebrada
        GT.rect(img, 19, 14, 22, 20, GT.P_BARK[2])
        GT.rect(img, 19, 14, 20, 20, GT.shade(GT.P_BARK[2], -10))
    return GT.outline(img)


def stump_0():
    return stump(0)


def stump_1():
    return stump(1)


# =========================================================== FLORES / TUFOS / COGUMELOS
def flower(v):
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    cx, cy = 16, 21
    GT.rect(img, cx, cy - 5, cx, cy + 2, GT.P_GRASS_DOT[1])       # caule
    GT.put(img, cx + 1, cy - 2, GT.shade(GT.P_GRASS_DOT[1], 14), wrap=False)
    c = GT.P_FLOWER[v % len(GT.P_FLOWER)]
    for dx, dy in ((0, -8), (-2, -6), (2, -6), (-1, -9), (1, -9)):
        GT.put(img, cx + dx, cy + dy, c, wrap=False)
    GT.put(img, cx, cy - 7, GT.shade(c, 40), wrap=False)
    return img


def flower_0():
    return flower(0)


def flower_1():
    return flower(1)


def flower_2():
    return flower(2)


def tuft(v):
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    rnd = GT.Rnd(7100 + v)
    cx, cy = 16, 24
    for _ in range(7 + v):
        bx = cx - 7 + rnd.i(15)
        h = 6 + rnd.i(7)
        lean = rnd.i(3) - 1
        for k in range(h):
            tone = GT.P_GRASS_DOT[0] if k % 3 else GT.shade(GT.P_GRASS_DOT[0], -18)
            GT.put(img, bx + (k * lean) // max(h, 1), cy - k, tone, wrap=False)
    return img


def tuft_0():
    return tuft(0)


def tuft_1():
    return tuft(1)


def tuft_2():
    return tuft(2)


def mushroom(v):
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    cap = (176, 62, 50, 255) if v == 0 else (150, 120, 82, 255)
    GT.ellipse(img, 15, 25, 8, 2, GT.SHADOW)
    GT.rect(img, 15, 20, 17, 25, (222, 214, 196, 255))
    GT.rect(img, 15, 20, 16, 25, (198, 190, 172, 255))
    GT.ellipse(img, 16, 19, 5, 3, cap)
    GT.ellipse(img, 16, 18, 3, 2, GT.shade(cap, 34))
    if v == 0:
        for dx, dy in ((-2, -1), (2, 0), (0, -2)):
            GT.put(img, 16 + dx, 19 + dy, (250, 244, 230, 255), wrap=False)
    return GT.outline(img)


def mushroom_0():
    return mushroom(0)


def mushroom_1():
    return mushroom(1)


# =========================================================== GALHO / POÇA
def branch_0():
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 24, 12, 3, GT.SHADOW)
    for i in range(24):
        x = 4 + i
        y = 20 - int(4 * math.sin(i / 24.0 * math.pi))
        GT.put(img, x, y, GT.P_BARK[1 + (i % 2)], wrap=False)
        GT.put(img, x, y + 1, GT.P_BARK[0], wrap=False)
    for (x, y) in ((10, 17), (18, 14)):                   # galhos secundários
        GT.rect(img, x, y, x + 1, y + 3, GT.P_BARK[2])
    return GT.outline(img)


def puddle_small():
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 18, 9, 5, GT.P_PUDDLE[0])
    GT.ellipse(img, 16, 17, 6, 3, GT.P_PUDDLE[1])
    GT.ellipse(img, 14, 16, 2, 1, GT.shade(GT.P_PUDDLE[2], 24))
    return img


# =========================================================== TOCHA DE RUA / PLACA
def torch_pole(phase):
    """Tocha em poste, de pé (distinta da tocha de PAREDE 2059 de gen_terrain)."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    rnd = GT.Rnd(8800 + phase)
    GT.ellipse(img, 16, 29, 7, 3, GT.SHADOW)
    GT.rect(img, 14, 14, 18, 29, GT.P_BARK[2])            # poste
    GT.rect(img, 14, 14, 15, 29, GT.P_BARK[1])
    GT.rect(img, 11, 11, 21, 15, (70, 68, 64, 255))       # braseiro
    GT.rect(img, 11, 11, 21, 12, (108, 106, 100, 255))
    k = 0 if phase == 0 else 1
    GT.ellipse(img, 16, 6 - k, 6, 8 + k, (198, 92, 24, 255))
    GT.ellipse(img, 16, 7 - k, 4, 6, (238, 160, 40, 255))
    GT.ellipse(img, 16 + (1 if k else -1), 8 - k, 2, 4, (252, 226, 140, 255))
    for _ in range(4):
        GT.put(img, 13 + rnd.i(7), rnd.i(6), (252, 200, 90, 255), wrap=False)
    return img


def torch_pole_0():
    return torch_pole(0)


def torch_pole_1():
    return torch_pole(1)


def signpost_trail():
    """Placa indicativa de duas colunas com ponta em seta (trilha)."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 29, 6, 2, GT.SHADOW)
    for x in (11, 21):
        GT.rect(img, x - 1, 14, x + 1, 29, GT.P_WOOD[1])
        GT.rect(img, x - 1, 14, x - 1, 29, GT.P_WOOD[0])
    GT.rect(img, 6, 9, 26, 15, GT.P_WOOD[2])
    GT.rect(img, 6, 9, 26, 10, GT.P_WOOD[4])
    GT.rect(img, 6, 14, 26, 15, GT.P_WOOD[0])
    for dy in range(-3, 4):                                # ponta em seta
        GT.rect(img, 26 + (3 - abs(dy)), 12 + dy, 27 + (3 - abs(dy)), 12 + dy,
                GT.P_WOOD[2])
    for y in (11, 13):                                      # "texto"
        GT.rect(img, 9, y, 23, y, (62, 44, 26, 255))
    return GT.outline(img)


# =========================================================== BARRIL / CAIXOTE
def barrel():
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 29, 10, 3, GT.SHADOW)
    GT.rect(img, 7, 10, 25, 27, GT.P_WOOD[2])
    GT.rect(img, 6, 13, 26, 24, GT.P_WOOD[1])              # barriga mais larga
    GT.rect(img, 7, 10, 25, 10, GT.P_WOOD[4])
    for y in (11, 20, 26):                                  # arcos de metal
        GT.rect(img, 6, y, 26, y + 1, (90, 84, 50, 255))
    for x in range(9, 25, 4):
        GT.put(img, x, 11, GT.shade(GT.P_WOOD[0], -10), wrap=False)
    return GT.outline(img)


def crate():
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 29, 11, 3, GT.SHADOW)
    GT.rect(img, 6, 10, 26, 27, GT.P_WOOD[2])
    GT.rect(img, 6, 10, 26, 11, GT.P_WOOD[4])
    for x in (6, 16, 26):
        GT.rect(img, x - 1, 10, x, 27, GT.P_WOOD[0])
    GT.rect(img, 6, 17, 26, 18, GT.P_WOOD[3])
    return GT.outline(img)


# =========================================================== CERCA DE MADEIRA
def fence_wood_h():
    """Cerca leste-oeste (própria — distinta da `fence` vanilla 1533/1534)."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    for x in (4, 28):
        GT.rect(img, x - 1, 10, x + 1, 29, GT.P_WOOD[1])
        GT.rect(img, x - 1, 10, x - 1, 29, GT.P_WOOD[0])
        GT.rect(img, x - 1, 10, x + 1, 10, GT.P_WOOD[4])
    for y in (15, 22):
        GT.rect(img, 0, y, 31, y + 1, GT.P_WOOD[2])
        GT.rect(img, 0, y + 2, 31, y + 2, GT.P_WOOD[0])
    return GT.outline(img)


def fence_wood_v():
    """Cerca norte-sul."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    for y in (4, 28):
        GT.rect(img, 10, y - 1, 29, y + 1, GT.P_WOOD[1])
        GT.rect(img, 10, y - 1, 29, y - 1, GT.P_WOOD[0])
        GT.rect(img, 10, y - 1, 10, y + 1, GT.P_WOOD[4])
    for x in (15, 22):
        GT.rect(img, x, 0, x + 1, 31, GT.P_WOOD[2])
        GT.rect(img, x + 2, 0, x + 2, 31, GT.P_WOOD[0])
    return GT.outline(img)


def fence_wood_c():
    """Canto — meia travessa horizontal + meia vertical, poste no encontro."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.rect(img, 0, 15, 16, 16, GT.P_WOOD[2])
    GT.rect(img, 0, 17, 16, 17, GT.P_WOOD[0])
    GT.rect(img, 15, 0, 16, 16, GT.P_WOOD[2])
    GT.rect(img, 17, 0, 17, 16, GT.P_WOOD[0])
    GT.rect(img, 13, 13, 19, 29, GT.P_WOOD[1])            # poste de canto
    GT.rect(img, 13, 13, 14, 29, GT.P_WOOD[0])
    GT.rect(img, 13, 13, 19, 13, GT.P_WOOD[4])
    return GT.outline(img)


# =========================================================== TRILHA DE PEDRAS
def stepping_stone(v):
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    rnd = GT.Rnd(9900 + v)
    cx, cy = 16 + rnd.i(5) - 2, 18 + rnd.i(5) - 2
    GT.ellipse(img, cx, cy + 4, 10, 3, GT.SHADOW)
    GT.ellipse(img, cx, cy, 10, 6, GT.P_STONE[1])
    GT.ellipse(img, cx, cy - 1, 7, 4, GT.P_STONE[3])
    GT.ellipse(img, cx - 2, cy - 2, 2, 1, GT.shade(GT.P_STONE[4], 10))
    return GT.outline(img)


def stepping_stone_0():
    return stepping_stone(0)


def stepping_stone_1():
    return stepping_stone(1)


def stepping_stone_2():
    return stepping_stone(2)


# =========================================================== MOBILIARIO (v2)
#: cadeira/estatua/lanterna pedidas pelo tour in-game do mapa v2.1: os itens
#: VANILLA usados ate agora (1650 "wooden chair", 1442 "statue") tem thing no
#: Tibia.dat mas o sprite e' um placeholder quase vazio (so' 25 de 1024px
#: opacos, um pontinho de 2px — visto exportando o sprite com dump_dat.py/
#: sprformat.py) — a causa raiz do "invisivel"/"losango cinza" reportado em
#: docs/sistemas/mapas.md, nao um buraco no .dat em si. Em vez de tentar
#: consertar o placeholder generico de 2 ids vanilla especificos, os itens
#: entram como NOVOS (mesmo fluxo dos demais deste arquivo), com arte de
#: verdade e sem depender do gerador de placeholders.
def chair(facing):
    """Cadeira de madeira, vista 3/4 — encosto do lado OPOSTO a `facing`
    (quem senta olha para `facing`). 2 orientacoes: 'east'/'west'."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 27, 8, 3, GT.SHADOW)
    east = facing == "east"
    back_x = 10 if east else 22                  # encosto do lado de tras
    # pernas
    for lx, ly in ((11, 22), (20, 22), (11, 26), (20, 26)):
        GT.rect(img, lx, ly, lx + 1, 27, GT.P_WOOD[0])
    # assento
    GT.rect(img, 9, 18, 22, 21, GT.P_WOOD[2])
    GT.rect(img, 9, 18, 22, 19, GT.P_WOOD[3])
    GT.rect(img, 9, 20, 22, 21, GT.shade(GT.P_WOOD[1], -6))
    # encosto (ripas verticais), mais alto do lado `back_x`
    for k in range(3):
        x = back_x + (k - 1) * 4 * (1 if east else -1)
        GT.rect(img, x - 1, 6, x + 1, 18, GT.P_WOOD[1])
        GT.rect(img, x - 1, 6, x - 1, 18, GT.P_WOOD[0])
    GT.rect(img, back_x - 6 if east else back_x - 2, 5,
            back_x + 2 if east else back_x + 6, 7, GT.P_WOOD[3])
    return GT.outline(img)


def chair_east():
    return chair("east")


def chair_west():
    return chair("west")


#: estatua de guardiao de santuario (estilo jizo/oni-menor) — pedra em 3 tons,
#: rosto simplificado, base retangular. v=0 pedra crua, v=1 com musgo (manchas
#: verdes no topo/ombros, onde a chuva escorre menos e o musgo pega).
_MOSS = [(74, 100, 52, 255), (96, 124, 66, 255)]


def shrine_statue(mossy):
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    rnd = GT.Rnd(6600 + (1 if mossy else 0))
    GT.ellipse(img, 16, 29, 9, 3, GT.SHADOW)
    # base/pedestal
    GT.rect(img, 9, 25, 23, 29, GT.P_STONE[0])
    GT.rect(img, 9, 25, 23, 26, GT.P_STONE[1])
    GT.rect(img, 9, 28, 23, 29, GT.shade(GT.P_STONE[0], -14))
    # corpo (tunica/robe), mais estreito no topo
    GT.ellipse(img, 16, 17, 7, 9, GT.P_STONE[2])
    GT.ellipse(img, 16, 16, 6, 8, GT.P_STONE[3])
    GT.rect(img, 12, 17, 20, 25, GT.P_STONE[2])
    GT.rect(img, 12, 17, 13, 25, GT.shade(GT.P_STONE[1], -6))
    GT.rect(img, 19, 17, 20, 25, GT.shade(GT.P_STONE[1], -10))
    # maos unidas (gesto de oracao) — bloco central mais claro
    GT.rect(img, 14, 19, 18, 22, GT.P_STONE[3])
    GT.rect(img, 15, 20, 17, 21, GT.shade(GT.P_STONE[4], 6))
    # cabeca (redonda, sem tracos — leitura de pedra, nao de rosto humano)
    GT.ellipse(img, 16, 8, 5, 5, GT.P_STONE[3])
    GT.ellipse(img, 15, 7, 2, 2, GT.shade(GT.P_STONE[4], 10))
    # chapeu/capuz do jizo — disco achatado por cima da cabeca
    GT.ellipse(img, 16, 4, 6, 2, GT.P_STONE[1])
    GT.ellipse(img, 16, 3, 5, 1, GT.shade(GT.P_STONE[2], 8))
    # rachaduras finas (idade)
    for _ in range(3):
        x, y = 12 + rnd.i(8), 12 + rnd.i(10)
        GT.put(img, x, y, GT.shade(GT.P_STONE[0], -16), wrap=False)
    if mossy:
        for (mx, my, mr) in ((16, 4, 3), (13, 18, 2), (19, 26, 2)):
            GT.ellipse(img, mx, my, mr, mr * 0.6, _MOSS[0])
            GT.ellipse(img, mx, my - 1, mr - 1, mr * 0.4, _MOSS[1])
    return GT.outline(img)


def shrine_statue_plain():
    return shrine_statue(False)


def shrine_statue_mossy():
    return shrine_statue(True)


def stone_lantern(phase):
    """Toro (lanterna de pedra japonesa), acesa — 2 fases de chama, luz quente
    igual a `street_torch` (ver tiles.json)."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 29, 8, 3, GT.SHADOW)
    # base
    GT.rect(img, 12, 26, 20, 29, GT.P_STONE[0])
    GT.rect(img, 13, 24, 19, 26, GT.P_STONE[1])
    # haste
    GT.rect(img, 14, 18, 18, 24, GT.P_STONE[2])
    GT.rect(img, 14, 18, 15, 24, GT.shade(GT.P_STONE[1], -6))
    # camara da luz (o "farol" do toro) — vazada, mostra o brilho por dentro
    GT.rect(img, 10, 11, 22, 18, GT.P_STONE[3])
    GT.rect(img, 12, 13, 20, 16, (70, 56, 40, 255))
    k = 0 if phase == 0 else 1
    GT.ellipse(img, 16, 14 - k, 3, 3 + k, (238, 160, 60, 255))
    GT.ellipse(img, 16, 14 - k, 2, 2, (252, 210, 130, 255))
    # telhado (capitel) em 2 aguas, mais largo que a camara
    GT.rect(img, 8, 8, 24, 11, GT.P_STONE[1])
    GT.rect(img, 8, 8, 24, 9, GT.shade(GT.P_STONE[2], 8))
    GT.ellipse(img, 16, 8, 9, 2, GT.P_STONE[2])
    # remate no topo
    GT.rect(img, 15, 5, 17, 8, GT.P_STONE[3])
    GT.ellipse(img, 16, 5, 2, 2, GT.shade(GT.P_STONE[4], 6))
    return img


def stone_lantern_0():
    return stone_lantern(0)


def stone_lantern_1():
    return stone_lantern(1)


# =========================================================== DECOR DE PRAIA
#: paleta propria (nao vem de gen_terrain.py: nada la cobre conchas/madeira
#: encalhada com o tom certo de "bege claro/lavado pelo sal").
_P_SHELL = [(224, 206, 182, 255), (238, 222, 200, 255), (198, 158, 148, 255), (250, 240, 226, 255)]
_P_DRIFTWOOD = [(118, 110, 96, 255), (138, 130, 114, 255), (156, 148, 130, 255), (172, 164, 146, 255)]
_P_WET = [(58, 66, 68, 255), (78, 88, 90, 255), (100, 112, 114, 255)]
#: sombra propria para decor de praia: `GT.SHADOW` tem tom ESVERDEADO (pensada
#: para grama) e destoa muito sobre areia — 1a rodada de revisao visual
#: (`driftwood`/`mooring_post`) mostrou uma mancha verde estranha na base.
_BEACH_SHADOW = (64, 56, 42, 255)


def seashell(v):
    """v=0: concha em cone/caramujo (bandas horizontais estreitando pro topo,
    silhueta em gota — a 1a versao era um blob redondo sem leitura nenhuma de
    concha); v=1: concha em leque (vieira)."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 22, 7, 2, _BEACH_SHADOW)
    if v == 0:
        cx = 16
        # bandas empilhadas, estreitando pro topo (silhueta de cone/caramujo)
        bands = [(24, 8, 0), (22, 7.4, 1), (20, 6.4, 0), (18, 5.2, 1),
                 (16, 3.8, 0), (14, 2.6, 1), (12, 1.6, 0)]
        for (y, half_w, tone) in bands:
            c = _P_SHELL[tone]
            GT.ellipse(img, cx, y, half_w, 2.4, c)
            GT.ellipse(img, cx - 1, y - 1, half_w - 1, 1.6, GT.shade(c, 12))
        GT.ellipse(img, cx, 11, 1.3, 1, _P_SHELL[3])           # apice
        # abertura (aperture) da concha, lado direito, tom mais escuro
        GT.ellipse(img, cx + 4, 22, 2.4, 5, _P_SHELL[2])
        GT.ellipse(img, cx + 4, 22, 1.3, 4, GT.shade(_P_SHELL[2], -18))
    else:
        cx, cy = 16, 20
        GT.ellipse(img, cx, cy, 7, 5, _P_SHELL[0])
        GT.ellipse(img, cx, cy - 1, 6, 4, _P_SHELL[1])
        for i in range(-3, 4):                 # nervuras em leque
            x = cx + i * 2
            GT.rect(img, x, cy - 4, x, cy + 3, GT.shade(_P_SHELL[2], 4 if i % 2 else -6))
        GT.ellipse(img, cx, cy - 4, 2, 1, _P_SHELL[3])
    return GT.outline(img)


def seashell_0():
    return seashell(0)


def seashell_1():
    return seashell(1)


def wet_rock():
    """Pedra molhada na maré — mais escura que `stone_*`, com brilho
    especular frio (reflexo de agua) e uma poça rasa na base."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    rnd = GT.Rnd(7700)
    cx, cy = 16, 20
    GT.ellipse(img, cx, cy + 5, 11, 4, _BEACH_SHADOW)
    GT.ellipse(img, cx, cy + 6, 10, 3, (70, 92, 96, 200))   # poça rasa na base
    for i, c in enumerate(_P_WET):
        rr = 9 - i * 2.4
        GT.ellipse(img, cx - i, cy - i, rr, rr * 0.8, c)
    for _ in range(5):                          # brilho especular (molhado)
        x = cx - 4 + rnd.i(9)
        y = cy - 6 + rnd.i(5)
        GT.put(img, x, y, GT.shade(_P_WET[2], 60), wrap=False)
    GT.put(img, cx - 2, cy - 5, (232, 240, 240, 255), wrap=False)
    return GT.outline(img)


def mooring_post():
    """Poste de amarração do cais, com corda enrolada — item, bloqueia
    1 tile (rotateable nao se aplica; e' decoracao vertical fixa)."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 29, 5, 2, _BEACH_SHADOW)
    GT.rect(img, 13, 8, 19, 28, GT.P_WOOD[2])
    GT.rect(img, 13, 8, 14, 28, GT.shade(GT.P_WOOD[1], -6))
    GT.rect(img, 18, 8, 19, 28, GT.shade(GT.P_WOOD[0], -4))
    GT.ellipse(img, 16, 8, 4, 2, GT.P_WOOD[3])
    rope = (198, 168, 108, 255)
    for i, y in enumerate((13, 16, 19, 22)):                 # corda enrolada
        GT.ellipse(img, 16, y, 4, 2, rope if i % 2 == 0 else GT.shade(rope, -18))
        GT.ellipse(img, 16, y, 3, 1, GT.shade(rope, 16))
    # ponta solta da corda caindo
    for k in range(6):
        GT.put(img, 20 + (k % 2), 23 + k, rope, wrap=False)
    return GT.outline(img)


# =========================================================== RUINAS DO CLA MARIONETISTA
def broken_puppet():
    """Marionete de guerra quebrada, caida — decor tematico das Ruinas do Cla
    Marionetista. Entulho: caminhavel, nao bloqueia."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 27, 10, 3, GT.SHADOW)
    wood = GT.P_WOOD
    GT.rect(img, 8, 20, 22, 25, wood[2])                  # corpo caido de lado
    GT.rect(img, 8, 20, 22, 21, wood[3])
    GT.rect(img, 8, 24, 22, 25, GT.shade(wood[0], -6))
    GT.ellipse(img, 6, 21, 4, 4, (214, 202, 178, 255))     # cabeca/mascara rachada
    GT.put(img, 5, 20, (60, 54, 46, 255), wrap=False)
    GT.put(img, 6, 22, (60, 54, 46, 255), wrap=False)
    GT.rect(img, 22, 16, 27, 18, wood[1])                 # braco solto, angulo quebrado
    GT.rect(img, 24, 12, 26, 17, wood[1])
    GT.rect(img, 4, 25, 9, 27, wood[0])
    rnd = GT.Rnd(6900)
    for (x0, y0) in ((10, 8), (18, 6), (24, 10)):          # fios de marionete arrebentados
        for k in range(6):
            GT.put(img, x0 + k // 2, y0 + k, (176, 168, 140, 255), wrap=False)
    for (x, y) in ((11, 22), (17, 21), (14, 24)):
        GT.put(img, x, y, GT.shade(wood[0], -20), wrap=False)
    return GT.outline(img)


def pillar_fallen():
    """Pilar de pedra caido — entulho, caminhavel."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 25, 13, 3, GT.SHADOW)
    for i, c in enumerate(GT.P_STONE[:4]):
        GT.rect(img, 4 + i, 18 - i, 28 - i, 23 - i, c)
    for k in range(3):                                    # aneis do fuste (tambor de pedra)
        x = 6 + k * 8
        GT.rect(img, x, 17, x, 24, GT.shade(GT.P_STONE[0], -18))
    GT.put(img, 24, 19, GT.shade(GT.P_STONE[0], -22), wrap=False)
    return GT.outline(img)


def pillar_standing():
    """Pilar de pedra de pe, alto — bloqueia (sala do boss das Ruinas)."""
    img = Image.new("RGBA", (CELL, 64), (0, 0, 0, 0))
    GT.ellipse(img, 16, 60, 10, 3, GT.SHADOW)
    for i, c in enumerate(GT.P_STONE[:4]):
        GT.rect(img, 10 + i, 6, 22 - i, 60, c)
    GT.rect(img, 8, 4, 24, 8, GT.P_STONE[3])              # capitel
    GT.rect(img, 8, 56, 24, 61, GT.P_STONE[1])            # base
    for y in range(10, 56, 6):                            # aneis/juntas
        GT.rect(img, 11, y, 21, y, GT.shade(GT.P_STONE[0], -14))
    return GT.outline(img)


# =========================================================== MONTANHA DO TROVAO
#: bandeiras de oracao — 5 cores tradicionais em tom FOSCO/desbotado (regra
#: "nunca neon" do projeto): vermelho, azul, amarelo, branco, verde.
_PRAYER_COLORS = [(158, 60, 54, 255), (70, 92, 120, 255), (168, 150, 70, 255),
                  (206, 200, 186, 255), (74, 108, 70, 255)]


def prayer_flag_post():
    """Poste com bandeiras de oracao no topo da Montanha do Trovao — bloqueia
    (como um poste de tocha)."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 29, 5, 2, GT.SHADOW)
    GT.rect(img, 15, 6, 17, 29, GT.P_BARK[2])
    GT.rect(img, 15, 6, 15, 29, GT.P_BARK[1])
    rope = (176, 168, 140, 255)
    GT.rect(img, 4, 6, 28, 7, rope)
    for i, c in enumerate(_PRAYER_COLORS):
        x0 = 4 + i * 5
        GT.rect(img, x0, 7, x0 + 3, 12, c)
        GT.rect(img, x0, 12, x0 + 3, 12, GT.shade(c, -20))
        GT.put(img, x0 + 1, 13, GT.shade(c, -10), wrap=False)
    return GT.outline(img)


def torch_pole_red(phase):
    """Tocha de rua em poste com chama VERMELHA (Covil da Nuvem Vermelha) —
    variante de `torch_pole`, tom de fogo escurecido/avermelhado, nunca neon."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    rnd = GT.Rnd(8900 + phase)
    GT.ellipse(img, 16, 29, 7, 3, GT.SHADOW)
    GT.rect(img, 14, 14, 18, 29, GT.P_BARK[2])
    GT.rect(img, 14, 14, 15, 29, GT.P_BARK[1])
    GT.rect(img, 11, 11, 21, 15, (60, 46, 46, 255))
    GT.rect(img, 11, 11, 21, 12, (90, 70, 70, 255))
    k = 0 if phase == 0 else 1
    GT.ellipse(img, 16, 6 - k, 6, 8 + k, (168, 40, 34, 255))
    GT.ellipse(img, 16, 7 - k, 4, 6, (206, 70, 46, 255))
    GT.ellipse(img, 16 + (1 if k else -1), 8 - k, 2, 4, (232, 120, 80, 255))
    for _ in range(4):
        GT.put(img, 13 + rnd.i(7), rnd.i(6), (222, 96, 60, 255), wrap=False)
    return img


# =========================================================== COVIL DA NUVEM VERMELHA
def blood_pool():
    """Poca de sangue seco/escuro — nao caminhavel. Tom terroso escuro (nunca
    vermelho vivo/neon), decor de horror comedido."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 20, 11, 6, (46, 16, 14, 255))
    GT.ellipse(img, 16, 19, 8, 4.4, (66, 22, 18, 255))
    GT.ellipse(img, 14, 17, 3, 1.6, GT.shade((66, 22, 18, 255), 14))
    for k in range(4):
        GT.put(img, 16 + (k % 3) - 1, 24 + k, (46, 16, 14, 255), wrap=False)
    return img


def lava_pool_cold():
    """Lava fria (solidificada, brilho residual esmaecido) — nao caminhavel."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 20, 12, 6, (30, 24, 24, 255))
    GT.ellipse(img, 16, 19, 9, 4.6, (48, 30, 26, 255))
    rnd = GT.Rnd(3700)
    for _ in range(6):                                     # veios residuais de calor
        x = 10 + rnd.i(12)
        y = 17 + rnd.i(5)
        GT.put(img, x, y, (108, 48, 34, 255), wrap=False)
    return img


def gate_marker():
    """Limiar de pedra baixo, gravado — marca visual de entrada de regiao
    (carrega o actionid do gate de rank; ver tools/map/build_regions.py).
    Walkable: nao bloqueia, so avisa (analogo ao torii_gate da vila)."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.rect(img, 3, 24, 28, 29, GT.P_STONE[1])
    GT.rect(img, 3, 24, 28, 25, GT.P_STONE[3])
    GT.rect(img, 3, 28, 28, 29, GT.shade(GT.P_STONE[0], -14))
    for x in (3, 28):
        GT.rect(img, x, 20, x, 29, GT.P_STONE[2])
    for x in range(8, 24, 4):                              # gravura simbolica no meio
        GT.put(img, x, 26, GT.shade(GT.P_STONE[4], 10), wrap=False)
    return GT.outline(img)


def driftwood():
    """Galho de madeira encalhado, esbranquiçado pelo sal (paleta propria,
    mais clara/acinzentada que `P_BARK`/`P_WOOD`). 1a versao usava so' 1px de
    espessura de tronco contra uma sombra grande — a sombra dominava a
    leitura e o galho lia como uma mancha esverdeada; agora o tronco tem 4-5px
    de espessura (silhueta reconhecivel de longe) e a sombra encolheu."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    GT.ellipse(img, 16, 25, 11, 2, _BEACH_SHADOW)
    rnd = GT.Rnd(4100)
    for i in range(23):
        x = 5 + i
        yc = 20 - int(3.0 * math.sin(i / 23.0 * math.pi))
        for dy in (-2, -1, 0, 1):                # tronco grosso (4px)
            tone = _P_DRIFTWOOD[1] if dy <= -1 else _P_DRIFTWOOD[0]
            if dy == -2:
                tone = _P_DRIFTWOOD[3]
            GT.put(img, x, yc + dy, tone, wrap=False)
    for (x, y) in ((8, 15), (25, 13)):                       # toco de galho quebrado
        GT.rect(img, x, y, x + 2, y + 4, _P_DRIFTWOOD[1])
        GT.rect(img, x, y, x + 2, y + 1, _P_DRIFTWOOD[3])
    for _ in range(5):                                       # rachaduras secas
        x = 7 + rnd.i(18)
        yc = 20 - int(3.0 * math.sin((x - 5) / 23.0 * math.pi))
        GT.put(img, x, yc, GT.shade(_P_DRIFTWOOD[0], -18), wrap=False)
    return GT.outline(img)


# ------------------------------------------------------------------ escrita
def save(img, name):
    path = os.path.join(OUT_DIR, name + ".png")
    img.save(path)
    return name + ".png"


def build():
    os.makedirs(OUT_DIR, exist_ok=True)
    n = {}

    def bump(k, c=1):
        n[k] = n.get(k, 0) + c

    save(bridge_center(), "bridge_center")
    save(bridge_head_west(), "bridge_head_west")
    save(bridge_head_east(), "bridge_head_east")
    save(bridge_rail_north(), "bridge_rail_north")
    save(bridge_rail_south(), "bridge_rail_south")
    bump("ponte", 5)

    save(stone_small(), "stone_small")
    save(stone_medium(), "stone_medium")
    save(stone_large(), "stone_large")
    bump("pedras", 3)

    save(stump_0(), "stump_0")
    save(stump_1(), "stump_1")
    bump("tocos", 2)

    for v, fn in enumerate((flower_0, flower_1, flower_2)):
        save(fn(), "flower_%d" % v)
    bump("flores", 3)

    for v, fn in enumerate((tuft_0, tuft_1, tuft_2)):
        save(fn(), "tuft_%d" % v)
    bump("tufos de grama", 3)

    save(mushroom_0(), "mushroom_0")
    save(mushroom_1(), "mushroom_1")
    bump("cogumelos", 2)

    save(branch_0(), "branch_0")
    bump("galho caido", 1)
    save(puddle_small(), "puddle_small")
    bump("poca decorativa", 1)

    save(torch_pole_0(), "torch_pole_0")
    save(torch_pole_1(), "torch_pole_1")
    bump("tocha de rua (fases)", 2)

    save(signpost_trail(), "signpost_trail")
    bump("placa de trilha", 1)

    save(barrel(), "barril")
    bump("barril", 1)
    save(crate(), "caixote")
    bump("caixote", 1)

    save(fence_wood_h(), "fence_wood_h")
    save(fence_wood_v(), "fence_wood_v")
    save(fence_wood_c(), "fence_wood_c")
    bump("cerca de madeira", 3)

    for v, fn in enumerate((stepping_stone_0, stepping_stone_1, stepping_stone_2)):
        save(fn(), "stepping_stone_%d" % v)
    bump("caminho de pedras soltas", 3)

    save(chair_east(), "chair_east")
    save(chair_west(), "chair_west")
    bump("cadeira de madeira", 2)

    save(shrine_statue_plain(), "shrine_statue_plain")
    save(shrine_statue_mossy(), "shrine_statue_mossy")
    bump("estatua de santuario", 2)

    save(stone_lantern_0(), "stone_lantern_0")
    save(stone_lantern_1(), "stone_lantern_1")
    bump("lanterna de pedra (fases)", 2)

    save(seashell_0(), "seashell_0")
    save(seashell_1(), "seashell_1")
    bump("concha", 2)

    save(wet_rock(), "wet_rock")
    bump("pedra molhada", 1)

    save(mooring_post(), "mooring_post")
    bump("poste de amarracao", 1)

    save(driftwood(), "driftwood")
    bump("madeira encalhada", 1)

    save(broken_puppet(), "broken_puppet")
    bump("marionete quebrada", 1)
    save(pillar_fallen(), "pillar_fallen")
    bump("pilar caido", 1)
    save(pillar_standing(), "pillar_standing")
    bump("pilar de pe", 1)

    save(prayer_flag_post(), "prayer_flag_post")
    bump("poste de bandeiras de oracao", 1)
    save(torch_pole_red(0), "torch_pole_red_0")
    save(torch_pole_red(1), "torch_pole_red_1")
    bump("tocha vermelha (fases)", 2)

    save(blood_pool(), "blood_pool")
    bump("poca de sangue", 1)
    save(lava_pool_cold(), "lava_pool_cold")
    bump("lava fria", 1)
    save(gate_marker(), "gate_marker")
    bump("limiar de gate de rank", 1)

    total = sum(n.values())
    print("decoracao -> %s" % OUT_DIR)
    for k in sorted(n):
        print("  %-28s %d" % (k, n[k]))
    print("  %-28s %d PNGs" % ("TOTAL", total))
    return n


if __name__ == "__main__":
    build()
