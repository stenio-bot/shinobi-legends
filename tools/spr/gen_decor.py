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

    total = sum(n.values())
    print("decoracao -> %s" % OUT_DIR)
    for k in sorted(n):
        print("  %-28s %d" % (k, n[k]))
    print("  %-28s %d PNGs" % ("TOTAL", total))
    return n


if __name__ == "__main__":
    build()
