#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fatia `assets-src/import/village_buildings.png` em tiles 32x32 de PRÉDIOS.

A folha é material de referência de uso privado (`assets-src/import/` está no
.gitignore). O que este script versiona é o RESULTADO: os PNGs de 32x32 em
`assets-src/sprites/tiles/buildings/` e as entradas novas de
`assets-src/sprites/tiles.json` / `assets-src/sprites/buildings.json`.

Etapas
------
1. **Alinhamento**: testa os 32 deslocamentos possíveis em x e em y e escolhe o
   que minimiza a quantidade de pixels opacos EM CIMA das linhas de grade
   (uma grade bem alinhada corta o mínimo possível de desenho).
   Resultado medido nesta folha: offset (0, 0) — 8 colunas x 32 linhas.

2. **Células**: recorta 32x32, descarta as células totalmente transparentes.

3. **Prédios**: o método pedido (componentes conexos na grade) NÃO funciona
   nesta folha — os prédios se tocam e os 243 tiles não-vazios formam UM único
   componente (veja `--components`). Por isso a segmentação é a tabela
   `SEGMENTS` abaixo, feita à mão em cima da folha de revisão. O modo
   `--components` continua disponível para conferir isso em folhas futuras.

4. **Dedup**: células com os mesmos pixels (hash SHA1 do RGBA) viram UM item só.
   Telhado laranja repetido não gera 40 itens iguais.

5. **Porta**: heurística = na linha de baixo do prédio, a célula mais central
   com maior fração de pixels escuros (a abertura). `SEGMENTS` pode fixar a
   porta à mão via `door=(col, row)`.

Saídas
------
    assets-src/import/extracted/buildings/<predio>/<col>_<row>.png   (revisão)
    assets-src/import/extracted/buildings/_review.png                (folha numerada)
    assets-src/import/extracted/buildings/_grid.png                  (grade sobreposta)
    assets-src/sprites/tiles/buildings/<key>.png                     (arte versionada)
    assets-src/sprites/tiles.json                                    (itens novos)
    assets-src/sprites/buildings.json                                (templates)

Uso
---
    .venv/bin/python tools/spr/slice_buildings.py --align      # só o relatório
    .venv/bin/python tools/spr/slice_buildings.py --components # só o teste de CC
    .venv/bin/python tools/spr/slice_buildings.py              # fatia e escreve tudo
    .venv/bin/python tools/spr/slice_buildings.py --dry-run    # não escreve JSON
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys

from PIL import Image, ImageDraw

CELL = 32

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SHEET = os.path.join(ROOT, "assets-src", "import", "village_buildings.png")
EXTRACT_DIR = os.path.join(ROOT, "assets-src", "import", "extracted", "buildings")
ART_DIR = os.path.join(ROOT, "assets-src", "sprites", "tiles", "buildings")
ART_REL = "tiles/buildings"           # relativo a sheet_root (assets-src/sprites)
TILES_JSON = os.path.join(ROOT, "assets-src", "sprites", "tiles.json")
BUILDINGS_JSON = os.path.join(ROOT, "assets-src", "sprites", "buildings.json")

#: uma célula com menos que isto de pixels opacos é considerada vazia
MIN_OPAQUE = 8

# --------------------------------------------------------------- segmentação
# (chave, nome, kind, col0, row0, col1, row1, porta fixa ou None)
#
# kind: "building"  = corpo bloqueia, uma célula vira porta
#       "wall"      = painel/muro, tudo bloqueia, sem porta
#       "prop"      = decoração bloqueante 1x1 (arbusto, poste, árvore)
#       "ground"    = decoração caminhável (grama)
# A porta fixa, quando dada, é em coordenadas LOCAIS (col, row) da matriz.
SEGMENTS = [
    ("tower",        "Torre do Líder",        "building", 0,  0, 4,  5, (2, 5)),
    ("blue_shop",    "Loja Azul",             "building", 5,  0, 7,  3, (1, 3)),
    ("grass_patch",  "Tufo de Grama",         "ground",   6,  4, 6,  4, None),
    ("bushes",       "Arbustos",              "prop",     5,  5, 7,  5, None),
    ("newbie_shop",  "Newbie Shop",           "building", 0,  6, 3,  9, (1, 3)),
    ("ramen_shop",   "Barraca de Lámen",      "building", 4,  6, 7, 10, (2, 4)),
    ("blue_house",   "Casa de Telhado Azul",  "building", 0, 10, 2, 13, (1, 3)),
    ("tree",         "Árvore da Vila",        "prop",     0, 14, 2, 14, None),
    ("prison",       "Prisão",                "building", 3, 11, 6, 14, (1, 3)),
    ("lamp_post",    "Poste de Luz",          "prop",     7, 11, 7, 14, None),
    ("house_green",  "Casa do Painel Verde",  "building", 0, 15, 3, 18, (1, 3)),
    ("dark_panel",   "Vão Escuro",            "wall",     4, 16, 4, 18, None),
    ("roof_orange",  "Telhado Laranja",       "wall",     5, 15, 7, 18, None),
    ("tavern",       "Taverna",               "building", 0, 19, 4, 23, (2, 4)),
    ("gate_east",    "Muro Leste",            "wall",     5, 19, 7, 23, None),
    ("big_house",    "Casa Grande de Doces",  "building", 0, 24, 4, 29, (1, 5)),
    ("green_gate_a", "Painel Verde A",        "wall",     5, 24, 6, 26, None),
    ("shop_east",    "Muro Leste com Telhado", "wall",    5, 27, 7, 29, None),
    ("big_bush",     "Moita Grande",          "prop",     0, 30, 2, 31, None),
    ("green_gate_b", "Painel Verde B",        "wall",     3, 30, 4, 31, None),
    ("green_gate_c", "Painel Verde C",        "wall",     6, 30, 7, 31, None),
]


# ------------------------------------------------------------------- helpers
def load_sheet():
    if not os.path.exists(SHEET):
        sys.exit("folha nao encontrada: %s" % SHEET)
    return Image.open(SHEET).convert("RGBA")


def opaque_mask(im):
    px = im.load()
    w, h = im.size
    return [[1 if px[x, y][3] >= 128 else 0 for x in range(w)] for y in range(h)]


def check_alignment(im, verbose=True):
    """Testa deslocamentos 0..31 e devolve (ox, oy) que menos corta desenho."""
    mask = opaque_mask(im)
    w, h = im.size
    colsum = [sum(mask[y][x] for y in range(h)) for x in range(w)]
    rowsum = [sum(row) for row in mask]

    def score(sums, n):
        out = []
        for off in range(CELL):
            lines = range(off, n, CELL)
            out.append((sum(sums[i] for i in lines), off))
        out.sort()
        return out

    sx = score(colsum, w)
    sy = score(rowsum, h)
    if verbose:
        print("alinhamento (menos pixels opacos sobre as linhas de grade):")
        print("  x: " + ", ".join("off=%2d custo=%d" % (o, c) for c, o in sx[:4]))
        print("  y: " + ", ".join("off=%2d custo=%d" % (o, c) for c, o in sy[:4]))
        print("  escolhido: (%d, %d)   grade %dx%d celulas"
              % (sx[0][1], sy[0][1], (w - sx[0][1]) // CELL, (h - sy[0][1]) // CELL))
    return sx[0][1], sy[0][1]


def cell_stats(im, ox, oy):
    """{(col,row): (opacos, escuros)} para toda a grade."""
    px = im.load()
    w, h = im.size
    cols = (w - ox) // CELL
    rows = (h - oy) // CELL
    stats = {}
    for r in range(rows):
        for c in range(cols):
            op = dark = 0
            for y in range(oy + r * CELL, oy + r * CELL + CELL):
                for x in range(ox + c * CELL, ox + c * CELL + CELL):
                    pr, pg, pb, pa = px[x, y]
                    if pa < 128:
                        continue
                    op += 1
                    if pr + pg + pb < 200:
                        dark += 1
            stats[(c, r)] = (op, dark)
    return stats, cols, rows


def components(stats):
    """Componentes conexos (4-vizinhos) das células não-vazias."""
    nodes = {k for k, (op, _) in stats.items() if op >= MIN_OPAQUE}
    seen, comps = set(), []
    for n in sorted(nodes):
        if n in seen:
            continue
        stack, comp = [n], []
        seen.add(n)
        while stack:
            c, r = stack.pop()
            comp.append((c, r))
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                m = (c + d[0], r + d[1])
                if m in nodes and m not in seen:
                    seen.add(m)
                    stack.append(m)
        comps.append(sorted(comp))
    comps.sort(key=len, reverse=True)
    return nodes, comps


def pick_door(seg, stats):
    """Célula de porta: linha de baixo, central, com mais pixels escuros."""
    key, _name, kind, c0, r0, c1, r1, forced = seg
    if kind != "building":
        return None
    if forced:
        return forced
    w = c1 - c0 + 1
    mid = (w - 1) / 2.0
    best = None
    for c in range(c0, c1 + 1):
        op, dark = stats.get((c, r1), (0, 0))
        if op < MIN_OPAQUE:
            continue
        frac = dark / float(op)
        # penaliza células longe do centro horizontal
        centrality = 1.0 - abs((c - c0) - mid) / (mid + 1.0)
        sc = frac * 0.7 + centrality * 0.3
        if best is None or sc > best[0]:
            best = (sc, c - c0)
    return None if best is None else (best[1], r1 - r0)


# ------------------------------------------------------------------- extração
def slice_all(im, ox, oy, stats):
    """Devolve (buildings, unique) onde:

    buildings = [{key, name, kind, w, h, door, grid: [[cellkey|None]*w]*h}]
    unique    = {tilekey: PIL.Image}
    """
    buildings = []
    unique = {}
    by_hash = {}

    for seg in SEGMENTS:
        key, name, kind, c0, r0, c1, r1, _forced = seg
        w, h = c1 - c0 + 1, r1 - r0 + 1
        door = pick_door(seg, stats)
        grid = [[None] * w for _ in range(h)]
        for lr in range(h):
            for lc in range(w):
                c, r = c0 + lc, r0 + lr
                op, _dark = stats.get((c, r), (0, 0))
                if op < MIN_OPAQUE:
                    continue
                box = (ox + c * CELL, oy + r * CELL,
                       ox + c * CELL + CELL, oy + r * CELL + CELL)
                img = im.crop(box)
                dig = hashlib.sha1(img.tobytes()).hexdigest()
                tk = by_hash.get(dig)
                if tk is None:
                    tk = "bld_%s_%d_%d" % (key, lc, lr)
                    by_hash[dig] = tk
                    unique[tk] = img
                grid[lr][lc] = tk
        buildings.append({"key": key, "name": name, "kind": kind,
                          "sheet_rect": [c0, r0, c1, r1],
                          "width": w, "height": h,
                          "door": list(door) if door else None,
                          "grid": grid})
    return buildings, unique


def write_extracted(im, ox, oy, stats, buildings):
    for b in buildings:
        c0, r0, _c1, _r1 = b["sheet_rect"]
        d = os.path.join(EXTRACT_DIR, b["key"])
        os.makedirs(d, exist_ok=True)
        for lr in range(b["height"]):
            for lc in range(b["width"]):
                if b["grid"][lr][lc] is None:
                    continue
                c, r = c0 + lc, r0 + lr
                box = (ox + c * CELL, oy + r * CELL,
                       ox + c * CELL + CELL, oy + r * CELL + CELL)
                im.crop(box).save(os.path.join(d, "%d_%d.png" % (lc, lr)))


def write_art(unique):
    os.makedirs(ART_DIR, exist_ok=True)
    for tk, img in unique.items():
        img.save(os.path.join(ART_DIR, tk + ".png"))


def write_review(im, ox, oy, buildings, scale=3):
    """Folha numerada: caixa e nome por prédio, coordenadas por célula."""
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    out = bg.resize((im.width * scale, im.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(out)
    palette = [(220, 0, 0), (0, 120, 220), (0, 150, 60), (200, 0, 200),
               (230, 120, 0), (0, 160, 160)]
    for i, b in enumerate(buildings):
        c0, r0, c1, r1 = b["sheet_rect"]
        col = palette[i % len(palette)]
        x0 = (ox + c0 * CELL) * scale
        y0 = (oy + r0 * CELL) * scale
        x1 = (ox + (c1 + 1) * CELL) * scale - 1
        y1 = (oy + (r1 + 1) * CELL) * scale - 1
        d.rectangle([x0, y0, x1, y1], outline=col + (255,), width=3)
        d.text((x0 + 4, y0 + 3), "%d %s" % (i, b["key"]), fill=(0, 0, 0, 255))
        if b["door"]:
            dc, dr = b["door"]
            dx0 = (ox + (c0 + dc) * CELL) * scale
            dy0 = (oy + (r0 + dr) * CELL) * scale
            d.rectangle([dx0 + 3, dy0 + 3, dx0 + CELL * scale - 4,
                         dy0 + CELL * scale - 4],
                        outline=(0, 0, 0, 255), width=3)
            d.text((dx0 + 6, dy0 + CELL * scale - 16), "PORTA", fill=(0, 0, 0, 255))
    path = os.path.join(EXTRACT_DIR, "_review.png")
    out.convert("RGB").save(path)
    return path


def write_grid(im, ox, oy, scale=2):
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    out = bg.resize((im.width * scale, im.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(out)
    for x in range(ox, im.width + 1, CELL):
        d.line([(x * scale, 0), (x * scale, out.height)], fill=(255, 0, 0, 255))
    for y in range(oy, im.height + 1, CELL):
        d.line([(0, y * scale), (out.width, y * scale)], fill=(255, 0, 0, 255))
    path = os.path.join(EXTRACT_DIR, "_grid.png")
    out.convert("RGB").save(path)
    return path


# ---------------------------------------------------------------- manifestos
BODY_FLAGS = {"walkable": False, "blocks_projectile": True, "movable": False}
DOOR_FLAGS = {"walkable": True, "movable": False}
PROP_FLAGS = {"walkable": False, "blocks_projectile": False, "movable": False}
GROUND_FLAGS = {"walkable": True, "movable": False}


def tile_specs(buildings, unique):
    """Uma entrada de tiles.json por tile ÚNICO, na ordem de primeira aparição."""
    door_keys = set()
    kind_of = {}
    owner = {}
    for b in buildings:
        for lr in range(b["height"]):
            for lc in range(b["width"]):
                tk = b["grid"][lr][lc]
                if tk is None:
                    continue
                owner.setdefault(tk, (b, lc, lr))
                kind_of.setdefault(tk, b["kind"])
        if b["door"]:
            dc, dr = b["door"]
            door_keys.add(b["grid"][dr][dc])

    specs = []
    for tk in unique:
        b, lc, lr = owner[tk]
        kind = kind_of[tk]
        if tk in door_keys:
            group, flags = "door", dict(DOOR_FLAGS)
            desc = "Entrada de %s." % b["name"]
            nome = "porta de %s" % b["name"].lower()
        elif kind == "prop":
            group, flags = "decoration", dict(PROP_FLAGS)
            desc = "%s (peça %d,%d)." % (b["name"], lc, lr)
            nome = b["name"].lower()
        elif kind == "ground":
            group, flags = "decoration", dict(GROUND_FLAGS)
            desc = "%s." % b["name"]
            nome = b["name"].lower()
        else:
            group, flags = "wall", dict(BODY_FLAGS)
            desc = "%s (peça %d,%d)." % (b["name"], lc, lr)
            nome = b["name"].lower()
        specs.append({
            "key": tk,
            "name": nome,
            "group": group,
            "size": [1, 1],
            "frames": ["%s/%s.png" % (ART_REL, tk)],
            "flags": flags,
            "xml": {"description": desc},
        })
    return specs


def merge_tiles_json(specs, dry_run=False):
    with open(TILES_JSON, encoding="utf-8") as fh:
        cfg = json.load(fh)
    have = {t["key"] for t in cfg["tiles"]}
    novos = [s for s in specs if s["key"] not in have]
    # remove entradas bld_* que sumiram da folha (mantém a ordem das demais)
    validas = {s["key"] for s in specs}
    cfg["tiles"] = [t for t in cfg["tiles"]
                    if not t["key"].startswith("bld_") or t["key"] in validas]
    cfg["tiles"].extend(novos)
    cfg["_doc_buildings"] = (
        "As chaves bld_* sao geradas por tools/spr/slice_buildings.py a partir de "
        "assets-src/import/village_buildings.png (material privado, nao versionado). "
        "Nao edite a mao: rode o slicer de novo. A arte fica em "
        "assets-src/sprites/tiles/buildings/ e os templates em buildings.json.")
    if not dry_run:
        with open(TILES_JSON, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return len(novos), len(cfg["tiles"])


def write_buildings_json(buildings, dry_run=False):
    doc = {
        "format": 1,
        "_doc": ("Templates de predio importados de village_buildings.png. Cada "
                 "'grid' e uma matriz linhas x colunas de CHAVES de tiles.json "
                 "(null = celula vazia), do topo para a base. 'door' e [col, row] "
                 "dentro da matriz. tools/map/build_valley.py estampa com "
                 "stamp_building(), ancorando o canto INFERIOR ESQUERDO."),
        "_gerado_por": "tools/spr/slice_buildings.py",
        "buildings": {b["key"]: {k: b[k] for k in
                                 ("name", "kind", "width", "height", "door", "grid")}
                      for b in buildings},
    }
    if not dry_run:
        with open(BUILDINGS_JSON, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return doc


# ------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--align", action="store_true", help="só o relatório de alinhamento")
    ap.add_argument("--components", action="store_true",
                    help="só o teste de componentes conexos")
    ap.add_argument("--dry-run", action="store_true", help="não escreve JSON/PNG")
    args = ap.parse_args()

    im = load_sheet()
    print("folha: %s  %dx%d %s" % (SHEET, im.width, im.height, im.mode))
    ox, oy = check_alignment(im)

    stats, cols, rows = cell_stats(im, ox, oy)
    nao_vazias = [k for k, (op, _) in stats.items() if op >= MIN_OPAQUE]
    print("celulas: %d na grade, %d nao-vazias" % (len(stats), len(nao_vazias)))

    if args.align:
        if not args.dry_run:
            print("grade sobreposta:", write_grid(im, ox, oy))
        return 0

    nodes, comps = components(stats)
    print("componentes conexos (4-vizinhos): %d  tamanhos=%s"
          % (len(comps), [len(c) for c in comps[:8]]))
    if len(comps) < len(SEGMENTS):
        print("  AVISO: os predios se tocam na folha; componentes conexos NAO")
        print("  separam os predios. Usando a tabela SEGMENTS (feita a mao).")
    if args.components:
        return 0

    buildings, unique = slice_all(im, ox, oy, stats)

    cobertas = set()
    for b in buildings:
        c0, r0, _, _ = b["sheet_rect"]
        for lr in range(b["height"]):
            for lc in range(b["width"]):
                if b["grid"][lr][lc] is not None:
                    cobertas.add((c0 + lc, r0 + lr))
    orfas = sorted(set(nao_vazias) - cobertas)
    if orfas:
        print("  AVISO: %d celulas nao-vazias fora de SEGMENTS: %s"
              % (len(orfas), orfas[:20]))

    total_cel = sum(1 for b in buildings for row in b["grid"] for v in row if v)
    print("predios: %d   celulas usadas: %d   tiles unicos (dedup): %d"
          % (len(buildings), total_cel, len(unique)))
    for b in buildings:
        print("  %-14s %dx%d  %2d celulas  porta=%s  [%s]"
              % (b["key"], b["width"], b["height"],
                 sum(1 for row in b["grid"] for v in row if v),
                 b["door"], b["kind"]))

    if args.dry_run:
        return 0

    write_extracted(im, ox, oy, stats, buildings)
    write_art(unique)
    print("grade sobreposta:", write_grid(im, ox, oy))
    print("folha de revisao:", write_review(im, ox, oy, buildings))

    specs = tile_specs(buildings, unique)
    novos, total = merge_tiles_json(specs)
    write_buildings_json(buildings)
    print("tiles.json: +%d entradas novas (total %d)" % (novos, total))
    print("buildings.json: %d templates" % len(buildings))
    print("\nagora rode: .venv/bin/python tools/spr/allocate_ids.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
