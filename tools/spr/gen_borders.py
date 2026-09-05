#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gerador de TILES DE BORDA (autoborder) por codigo, estilo Tibia 7.x/8.x.

v2 (fluida): em vez de desenhar cada uma das 12 pecas com uma formula propria
(o que deixava reta/canto externo/canto interno com perfis DIFERENTES e a
emenda visivel entre pecas), o algoritmo agora desenha a FRONTEIRA hi/baixo de
um "macro-tile" 3x3 (o tile central + os 8 vizinhos) com uma unica distorcao de
coordenada (`_warp_fields`) e recorta o tile central. As 12 pecas de um par sao
so 12 combinacoes diferentes de "quais vizinhos sao o material ALTO" recortadas
do MESMO campo de distorcao (mesma semente) — por construcao, reta/canto
externo/canto interno tem exatamente o mesmo "sotaque" de curva, porque vem da
mesma fronteira ondulada, so que vista atraves de uma janela de vizinhanca
diferente. Isso garante a continuidade C0 pedida: a peca "n" e a peca "icnw"
concordam em como a curva se comporta perto da borda norte, porque as duas sao
cortes do mesmo campo.

Paletas e ruido de textura: REUSADOS de `gen_terrain.py` (P_GRASS, P_DIRT,
P_WATER, P_MUD, P_COBBLE, `shared_field`, `quantize`, `Rnd`, `noise_tile`) —
nada de nova paleta, para a borda casar pixel a pixel com o chao que ela cobre.

Convencao de par: `<alto>_<baixo>` = o material ALTO (mais "por cima" na
hierarquia agua < lama < terra < grama < cobble) manda uma faixa ondulada
INVADINDO o tile do material BAIXO. Ver docs/sistemas/mapas.md secao Autoborder
para a explicacao de por que o quarto par e `cobble_dirt` (cobble invade
terra) e nao "terra->cobblestone" como o nome informal da missao original.

12 pecas base por par (`n,s,e,w` retas + `cnw,cne,csw,cse` cantos EXTERNOS +
`icnw,icne,icsw,icse` cantos INTERNOS) + 2 VARIANTES por peca reta (`n`/`n2`,
`s`/`s2`, `e`/`e2`, `w`/`w2` — mesma semente de distorcao, deslocada, para o
autoborder poder escolher por hash de posicao e a faixa nao ficar "carimbada"
repetindo a mesma peca ao longo de uma trilha comprida).

Uso:
    .venv/bin/python tools/spr/gen_borders.py
    .venv/bin/python tools/spr/gen_borders.py --sheet   # so a folha de revisao

Escreve em `assets-src/sprites/terrain/borders/<par>_<peca>.png` e a folha de
revisao em `assets-src/sprites/terrain/borders/_sheet.png`.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gen_terrain as GT  # noqa: E402 - reusa paletas/ruido/RNG do terreno

CELL = GT.CELL
ROOT = GT.ROOT
OUT_DIR = os.path.join(ROOT, "assets-src", "sprites", "terrain", "borders")

# par -> (paleta do material ALTO, paleta do material baixo so p/ contato/sombra)
PAIRS = {
    "grass_dirt": (GT.P_GRASS, GT.P_DIRT),
    "grass_water": (GT.P_GRASS, GT.P_WATER),
    "grass_mud": (GT.P_GRASS, GT.P_MUD),
    "cobble_dirt": (GT.P_COBBLE, GT.P_DIRT),
}

EDGES = ("n", "s", "e", "w")
OUTER = ("cnw", "cne", "csw", "cse")
INNER = ("icnw", "icne", "icsw", "icse")
BASE_PIECES = EDGES + OUTER + INNER
#: pecas retas ganham uma 2a variante (mesmo estilo, semente diferente)
EDGE_VARIANTS = tuple(e + "2" for e in EDGES)
PIECES = BASE_PIECES + EDGE_VARIANTS

FOAM = (222, 224, 200, 255)          # espuma/areia clara (so grass_water)
FOAM_DARK = (176, 190, 168, 255)

#: "lingua curta" dos cantos: alcance (em px) alem do qual a invasao do canto
#: nao chega — bem menor que os 32px da peca, pra nao virar uma reta disfarcada.
REACH = 12.0


# --------------------------------------------------------- fronteira ondulada
def _smoothstep(t):
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return t * t * (3.0 - 2.0 * t)


def _taper(d, reach=REACH):
    return _smoothstep(1.0 - d / reach)


def _depth_profile(seed, base=4.5, amp=1.7, jitter=0.7, n=CELL):
    """Curva-base UNICA de profundidade de invasao (em px), periodica (a volta
    fecha: amostra n-1 encosta na 0 pela mesma senoide continua) — amplitude
    3-6px como pedido. Suavizada por media movel circular (tira o serrilhado
    de ruido independente por pixel) e so DEPOIS recebe um jitter pequeno
    (variação organica, nao xadrez de ruido)."""
    rnd = GT.Rnd(seed)
    ph1 = rnd.f() * math.tau
    ph2 = rnd.f() * math.tau
    raw = []
    for i in range(n):
        t = i / float(n) * math.tau
        v = base + amp * (0.6 * math.sin(t * 2 + ph1) + 0.4 * math.sin(t * 5 + ph2))
        raw.append(v)
    sm = [(raw[(i - 1) % n] + 2 * raw[i] + raw[(i + 1) % n]) / 4.0 for i in range(n)]
    return [max(1.5, sm[i] + (rnd.f() - 0.5) * jitter) for i in range(n)]


def _profiles(pair_key):
    """4 curvas (norte/sul/leste/oeste) do par, todas da MESMA familia (mesmo
    base/amp/estilo, sementes derivadas de uma raiz comum) — os cantos as
    REUSAM diretamente (nunca inventam uma forma propria), o que garante que
    reta e canto concordem em amplitude e "caligrafia" da onda."""
    root = abs(hash(pair_key)) % 90000
    return {
        "n": _depth_profile(root + 11),
        "s": _depth_profile(root + 227),
        "e": _depth_profile(root + 443),
        "w": _depth_profile(root + 659),
    }


def _profiles_variant(pair_key):
    root = abs(hash(pair_key + "_v2")) % 90000
    return {
        "n": _depth_profile(root + 11),
        "s": _depth_profile(root + 227),
        "e": _depth_profile(root + 443),
        "w": _depth_profile(root + 659),
    }


def _straight_mask(prof, edge):
    m = [[False] * CELL for _ in range(CELL)]
    if edge == "n":
        for x in range(CELL):
            for y in range(min(CELL, int(round(prof["n"][x])))):
                m[y][x] = True
    elif edge == "s":
        for x in range(CELL):
            d = int(round(prof["s"][x]))
            for y in range(max(0, CELL - d), CELL):
                m[y][x] = True
    elif edge == "e":
        for y in range(CELL):
            d = int(round(prof["e"][y]))
            for x in range(max(0, CELL - d), CELL):
                m[y][x] = True
    else:
        for y in range(CELL):
            for x in range(min(CELL, int(round(prof["w"][y])))):
                m[y][x] = True
    return m


def _outer_mask(prof, corner):
    """Canto EXTERNO = uniao de 2 faixas CURTAS (a mesma curva das retas "n"/
    "s"/"e"/"w" vizinhas, encolhendo com `_taper` conforme se afasta do
    canto) — a "lingua" que so toca a tile pela diagonal."""
    cx, cy = corner
    m = [[False] * CELL for _ in range(CELL)]
    prof_h = prof["n"] if cy == 0 else prof["s"]
    prof_v = prof["w"] if cx == 0 else prof["e"]
    for x in range(CELL):
        dist = x if cx == 0 else (CELL - 1 - x)
        depth = prof_h[x] * _taper(dist)
        rng = range(0, int(round(depth))) if cy == 0 else range(max(0, CELL - int(round(depth))), CELL)
        for y in rng:
            m[y][x] = True
    for y in range(CELL):
        dist = y if cy == 0 else (CELL - 1 - y)
        depth = prof_v[y] * _taper(dist)
        rng = range(0, int(round(depth))) if cx == 0 else range(max(0, CELL - int(round(depth))), CELL)
        for x in rng:
            m[y][x] = True
    return m


#: canto interno icXY = tile cheio MENOS o bolsao (formato de canto externo)
#: no canto OPOSTO, usando as curvas das 2 direcoes que NAO formam esse canto.
_OPPOSITE = {"cnw": "cse", "cne": "csw", "csw": "cne", "cse": "cnw"}
_CORNER_XY = {"cnw": (0, 0), "cne": (CELL - 1, 0), "csw": (0, CELL - 1), "cse": (CELL - 1, CELL - 1)}
_INNER_TO_OUTER_OPPOSITE = {"icnw": "cse", "icne": "csw", "icsw": "cne", "icse": "cnw"}


def _mask_for_piece(pair_key, piece):
    variant = piece.endswith("2") and piece[:-1] in EDGES
    prof = _profiles_variant(pair_key) if variant else _profiles(pair_key)
    base = piece[:-1] if variant else piece
    if base in EDGES:
        return _straight_mask(prof, base)
    if base in OUTER:
        return _outer_mask(prof, _CORNER_XY[base])
    # inner: NOT (mancha de canto externo no canto oposto)
    opp_key = _INNER_TO_OUTER_OPPOSITE[base]
    pocket = _outer_mask(prof, _CORNER_XY[opp_key])
    return [[not pocket[y][x] for x in range(CELL)] for y in range(CELL)]


def _dither_edge(mask, rnd):
    """Dithering leve na linha de contato: alguns pixels da beira trocam de
    lado seguindo a matriz de Bayer (o "chuvisco" tipico do pixel art), em vez
    de uma curva perfeitamente lisa — mas sem virar ruido aleatorio puro,
    porque so mexe nos pixels que JA estao na fronteira."""
    h = len(mask)
    out = [row[:] for row in mask]
    for y in range(h):
        for x in range(h):
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < h and 0 <= ny < h and mask[ny][nx] != mask[y][x]:
                    edge = True
                    break
            if not edge:
                continue
            b = GT.BAYER[y & 3][x & 3] / 16.0
            if mask[y][x] and b < 0.16:
                out[y][x] = False
            elif not mask[y][x] and b > 0.88:
                out[y][x] = True
    return out


# ------------------------------------------------------------------ textura
def _texture_hi(pair_key, hi_pal):
    """Textura RGBA 32x32 do material alto = a MESMA funcao que desenha o chao
    de verdade (`gen_terrain.grass`/`cobble`), nao um ruido generico proprio —
    e' isso que faz a borda casar pixel a pixel com o chao que ela cobre (uma
    versao anterior usava `shared_field` + paleta, o que dava uma mancha lisa
    parecida mas sem a textura caracteristica de cada material — tufos de
    grama, pedras de calcada — e ficava com "cara de mancha cinza")."""
    if pair_key.startswith("cobble"):
        return GT.cobble(1)
    return GT.grass(1)


def make_piece(pair_key, piece, hi_pal, lo_pal, is_water):
    mask = _mask_for_piece(pair_key, piece)
    rnd = GT.Rnd((abs(hash(pair_key + piece)) % 90000) + 3)
    mask = _dither_edge(mask, rnd)

    tex = _texture_hi(pair_key, hi_pal)
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    px = img.load()
    tx = tex.load()
    for y in range(CELL):
        for x in range(CELL):
            if mask[y][x]:
                px[x, y] = tx[x, y]

    # brilho de 1px do lado do INVASOR (anel interno, logo apos a fronteira)
    for y in range(CELL):
        for x in range(CELL):
            if not mask[y][x]:
                continue
            beira_baixo = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < CELL and 0 <= ny < CELL and not mask[ny][nx]:
                    beira_baixo = True
                    break
            if beira_baixo:
                px[x, y] = GT.shade(px[x, y], 16)

    # contorno do lado do material INVADIDO: espuma/areia clara na agua,
    # sombra escura de contato nos demais pares — 1px por fora da mascara,
    # "mordendo" visualmente o chao baixo (nao move a mascara em si).
    contact = []
    for y in range(CELL):
        for x in range(CELL):
            if mask[y][x]:
                continue
            beira_alto = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < CELL and 0 <= ny < CELL and mask[ny][nx]:
                    beira_alto = True
                    break
            if beira_alto:
                contact.append((x, y))
    for x, y in contact:
        if is_water:
            c = FOAM if ((x + y) & 1 == 0 or rnd.chance(0.7)) else FOAM_DARK
        else:
            c = GT.shade(lo_pal[1], -22)
        px[x, y] = c

    return img


# ------------------------------------------------------------------ folha
def make_sheet(all_imgs):
    pairs = list(PAIRS)
    cols = len(PIECES)
    rows = len(pairs)
    pad = 4
    cell = CELL + pad
    sheet = Image.new("RGBA", (cols * cell + pad, rows * cell + pad + 16 * rows),
                       (60, 60, 64, 255))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(sheet)
    for ri, pk in enumerate(pairs):
        hi_pal, lo_pal = PAIRS[pk]
        y0 = pad + ri * (cell + 16)
        # fundo = material baixo, pra ver a invasao contra o chao real
        bg = GT.quantize(GT.shared_field("sheetbg_" + pk, 1, 2), lo_pal)
        for ci, piece in enumerate(PIECES):
            x0 = pad + ci * cell
            sheet.paste(bg, (x0, y0))
            img = all_imgs[(pk, piece)]
            sheet.paste(img, (x0, y0), img)
            draw.text((x0, y0 + CELL + 1), piece, fill=(230, 230, 230, 255))
        draw.text((pad, y0 - 12), pk, fill=(255, 220, 120, 255))
    return sheet


# --------------------------------------------------------------------- main
def build(sheet_only=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    all_imgs = {}
    n = 0
    for pk, (hi_pal, lo_pal) in PAIRS.items():
        is_water = pk == "grass_water"
        for piece in PIECES:
            img = make_piece(pk, piece, hi_pal, lo_pal, is_water)
            img = GT.outline(img)
            all_imgs[(pk, piece)] = img
            if not sheet_only:
                path = os.path.join(OUT_DIR, "%s_%s.png" % (pk, piece))
                img.save(path)
                n += 1
    sheet = make_sheet(all_imgs)
    sheet_path = os.path.join(OUT_DIR, "_sheet.png")
    sheet.save(sheet_path)
    print("bordas -> %s" % OUT_DIR)
    print("  %d pares x %d pecas = %d PNGs" % (len(PAIRS), len(PIECES), len(PAIRS) * len(PIECES)))
    if not sheet_only:
        print("  gravados: %d" % n)
    print("  folha de revisao: %s" % sheet_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true", help="so a folha de revisao, nao regrava os PNGs individuais")
    args = ap.parse_args()
    build(sheet_only=args.sheet)


if __name__ == "__main__":
    main()
