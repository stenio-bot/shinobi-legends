#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gerador de TILES DE BORDA (autoborder) por codigo, estilo Tibia 7.x/8.x.

Desenha, para cada par de materiais (grama->terra, grama->agua, grama->lama,
cobble->terra), um conjunto de 12 pecas 32x32 RGBA com alpha REAL (nao binario):
o `.spr` de 1098 nao tem alpha por pixel para o CHAO, mas para um item de
DECORACAO desenhado por cima (grupo "decoration", ALWAYSONTOP) o formato aceita
alpha binario tambem — entao aqui usamos alpha binario (0 ou 255) igual ao
resto do projeto (ver FORMATO.md), so que a MASCARA e uma faixa irregular, nao
um retangulo cheio: e isso que faz a peca "flutuar" por cima do chao existente
em vez de cobrir o tile inteiro.

Paletas: REUSADAS de `gen_terrain.py` (P_GRASS, P_DIRT, P_WATER, P_MUD,
P_COBBLE e as funcoes `shade`/`shared_field`/`quantize`/`Rnd`) — nada de nova
paleta, para o material da borda casar exatamente com o material do chao.

Convencao de par: `<alto>_<baixo>` = o material ALTO (mais "por cima" na
hierarquia agua < lama < terra < grama < cobble) manda uma faixa ondulada
INVADINDO o tile do material BAIXO. A missao pede os pares "grama->terra",
"grama->agua", "grama->lama" e "terra->cobblestone"; os 3 primeiros ja tem o
alto->baixo na ordem hierarquica (grama > terra/agua/lama). O quarto, seguindo
a MESMA hierarquia (cobble e o mais alto de todos), fica ao contrario do nome
citado na missao: aqui o par e `cobble_terra` (cobblestone invade terra), nao
`terra_cobblestone` — a hierarquia declarada tem precedencia sobre o nome do
par, que era so um jeito de falar. Ver docs/sistemas/mapas.md secao Autoborder.

12 pecas por par (nomes usados como sufixo de arquivo e como peca no algoritmo
de tools/map/build_valley.py):
    n, s, e, w                     bordas retas (o vizinho NESSA direcao e o
                                    material alto; a faixa entra por essa borda)
    cnw, cne, csw, cse              cantos EXTERNOS (o alto toca so na diagonal)
    icnw, icne, icsw, icse           cantos INTERNOS (o alto cerca as duas
                                    laterais que formam esse canto)

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

# par -> (paleta do material ALTO, paleta do material baixo so p/ sombra de contato)
PAIRS = {
    "grass_dirt": (GT.P_GRASS, GT.P_DIRT),
    "grass_water": (GT.P_GRASS, GT.P_WATER),
    "grass_mud": (GT.P_GRASS, GT.P_MUD),
    "cobble_dirt": (GT.P_COBBLE, GT.P_DIRT),
}

EDGES = ("n", "s", "e", "w")
OUTER = ("cnw", "cne", "csw", "cse")
INNER = ("icnw", "icne", "icsw", "icse")
PIECES = EDGES + OUTER + INNER

OUTLINE = (18, 16, 14, 255)


# --------------------------------------------------------------------- forma
def _wave(rnd, n, base, amp, lo_amp):
    """Perfil ondulado de profundidade de invasao (em px), n amostras ao longo
    da borda, periodico (o inicio casa com o fim para poder repetir o tile)."""
    # soma de 2 senoides de periodo != 32 + ruido -> "irregular", nao serrilhado
    out = []
    ph1 = rnd.f() * math.tau
    ph2 = rnd.f() * math.tau
    for i in range(n):
        t = i / float(n) * math.tau
        v = base + amp * (0.6 * math.sin(t * 2 + ph1) + 0.4 * math.sin(t * 5 + ph2))
        v += (rnd.f() - 0.5) * lo_amp
        out.append(v)
    return out


def _depth_field(seed, base=5.5, amp=2.4, lo_amp=1.6):
    """Profundidade de invasao para cada uma das 32 colunas/linhas do tile,
    usada tanto pelas bordas retas quanto pelos cantos (mesma "textura" de
    faixa em todas as pecas do par, para casarem quando colocadas lado a lado)."""
    rnd = GT.Rnd(seed)
    return _wave(rnd, CELL, base, amp, lo_amp)


def _mask_straight(depth):
    """Mascara 32x32: True nas linhas y < depth[x] (faixa entrando pelo norte).
    As outras 3 retas sao a mesma mascara rotacionada."""
    m = [[False] * CELL for _ in range(CELL)]
    for x in range(CELL):
        d = int(round(depth[x]))
        for y in range(max(0, d)):
            m[y][x] = True
    return m


def _rotate(m, k):
    """Rotaciona a mascara 90*k graus (k=1 -> norte vira leste, etc.)."""
    for _ in range(k % 4):
        m = [[m[CELL - 1 - x][y] for x in range(CELL)] for y in range(CELL)]
    return m


def _mask_outer(depth_a, depth_b, corner):
    """Canto EXTERNO: o alto so toca a tile pela diagonal `corner` — uma
    lingua curta que nasce no canto e encolhe para as duas bordas."""
    m = [[False] * CELL for _ in range(CELL)]
    cx, cy = corner  # 0 = lado esquerdo/topo, CELL-1 = lado direito/baixo
    # forma: quarto de elipse decrescente a partir do canto (o alto so toca a
    # tile perto da diagonal `corner`, some antes de chegar nas duas bordas)
    r0 = 0.55 * (sum(depth_a) / len(depth_a) + sum(depth_b) / len(depth_b))
    for y in range(CELL):
        for x in range(CELL):
            dx = x if cx == 0 else (CELL - 1 - x)
            dy = y if cy == 0 else (CELL - 1 - y)
            # perfil radial ondulado reaproveitando as duas listas de profundidade
            wobble = (depth_a[(dx * 2) % CELL] + depth_b[(dy * 2) % CELL]) * 0.5 - \
                     (sum(depth_a) / len(depth_a))
            r = r0 * 1.15 + wobble * 0.35
            if dx * dx + dy * dy <= r * r and dx < r0 * 2.2 and dy < r0 * 2.2:
                m[y][x] = True
    return m


def _mask_inner(depth_a, depth_b, corner):
    """Canto INTERNO: o alto cerca as DUAS bordas que formam esse canto (o
    baixo fica so num bolsao no canto oposto) — a faixa cobre tudo MENOS um
    quarto de elipse encolhendo a partir do canto oposto ao `corner`."""
    m = [[True] * CELL for _ in range(CELL)]
    cx, cy = corner
    ox, oy = (CELL - 1) - cx, (CELL - 1) - cy  # canto oposto = onde sobra "baixo"
    r0 = 0.62 * (sum(depth_a) / len(depth_a) + sum(depth_b) / len(depth_b))
    for y in range(CELL):
        for x in range(CELL):
            dx = x if ox == 0 else (CELL - 1 - x)
            dy = y if oy == 0 else (CELL - 1 - y)
            wobble = (depth_a[(dx * 2) % CELL] + depth_b[(dy * 2) % CELL]) * 0.5 - \
                     (sum(depth_a) / len(depth_a))
            r = r0 * 1.05 + wobble * 0.35
            if dx * dx + dy * dy <= r * r:
                m[y][x] = False
    return m


# ------------------------------------------------------------------ textura
def _texture_hi(pair_key, hi_pal):
    """Textura RGBA 32x32 do material alto — mesmo ruido/paleta do gen_terrain,
    semente propria por par para nao repetir pixel a pixel com o chao normal."""
    seed = (abs(hash(pair_key)) % 90000) + 31
    f = GT.shared_field("border_" + pair_key, seed, seed + 500)
    return GT.quantize(f, hi_pal, dither=0.06)


def _apply_mask(tex, mask, contact_shade=None, contact_bias=None):
    """Recorta `tex` pela mascara; opcionalmente escurece/clareia perto da
    linha de contato para dar profundidade (bias: campo 0..CELL com a mesma
    forma da mascara, usado so como marcador visual, aqui simplificado)."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    px = img.load()
    tx = tex.load()
    for y in range(CELL):
        for x in range(CELL):
            if mask[y][x]:
                px[x, y] = tx[x, y]
    return img


def _contact_line(img, mask, color):
    """1px de sombra/contorno na linha onde a mascara termina (o "limite" da
    invasao) — separa visualmente a borda do chao por baixo."""
    px = img.load()
    w, h = img.size
    add = []
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            # e' beira se algum vizinho (dentro do tile) NAO esta na mascara
            beira = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and not mask[ny][nx]:
                    beira = True
                    break
            if beira:
                add.append((x, y))
    for x, y in add:
        px[x, y] = GT.shade(px[x, y], -26) if px[x, y][3] else px[x, y]
    return img


def _sprinkle(img, mask, rnd, color, n):
    for _ in range(n):
        x, y = rnd.i(CELL), rnd.i(CELL)
        if mask[y][x]:
            img.putpixel((x, y), color)


# ------------------------------------------------------------------ pecas
def make_piece(pair_key, piece, hi_pal, lo_pal):
    seed_edges = (abs(hash(pair_key + "_edges")) % 90000) + 7
    depth = _depth_field(seed_edges)
    # profundidade "irmã" (perpendicular), semente derivada p/ os cantos
    depth2 = _depth_field(seed_edges + 101)

    if piece in EDGES:
        k = EDGES.index(piece)  # n=0,s=1,e=2,w=3
        if piece == "n":
            mask = _mask_straight(depth)
        elif piece == "s":
            mask = _rotate(_mask_straight(depth), 2)
        elif piece == "e":
            mask = _rotate(_mask_straight(depth), 1)
        else:
            mask = _rotate(_mask_straight(depth), 3)
    else:
        corner_map = {
            "cnw": (0, 0), "cne": (CELL - 1, 0),
            "csw": (0, CELL - 1), "cse": (CELL - 1, CELL - 1),
            "icnw": (0, 0), "icne": (CELL - 1, 0),
            "icsw": (0, CELL - 1), "icse": (CELL - 1, CELL - 1),
        }
        corner = corner_map[piece]
        if piece in OUTER:
            mask = _mask_outer(depth, depth2, corner)
        else:
            mask = _mask_inner(depth, depth2, corner)

    tex = _texture_hi(pair_key, hi_pal)
    img = _apply_mask(tex, mask)
    rnd = GT.Rnd((abs(hash(pair_key + piece)) % 90000) + 3)
    # respingos do material baixo "sobrevivendo" bem na crista da invasao
    # (poucos pixels, so pra nao ficar um degrau limpo demais)
    _sprinkle(img, mask, rnd, GT.shade(lo_pal[-1], -6), 3)
    img = _contact_line(img, mask, OUTLINE)
    img = GT.outline(img)
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
        for piece in PIECES:
            img = make_piece(pk, piece, hi_pal, lo_pal)
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
