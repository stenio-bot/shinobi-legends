#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mini-renderer PNG do mapa gerado, SEM precisar do cliente OTClient.

Reusa `tools/map/build_valley.py` como biblioteca (mesma sequencia exata que
gera o `valley.otbm`: build -> carve_clearings -> connect_clearings ->
apply_borders) e desenha uma area retangular usando os PNGs de
`assets-src/sprites/terrain/` (chao/objetos vanilla, via
`assets-src/sprites/overrides/10_terrain.json`) e de
`assets-src/sprites/tiles.json` (bordas, predios importados, mobiliario
proprio). 32px por tile; itens com `height: 64` (paredes/portas/tocha/etc) sao
ancorados subindo 32px sobre o tile (base do sprite = base do tile); itens
2x2 (arvores, tenda) sao ancorados pelo canto inferior direito, igual ao
cliente real (ver docstring de tools/spr/gen_terrain.py).

Uso:
    .venv/bin/python tools/map/render_preview.py
    .venv/bin/python tools/map/render_preview.py --area 1000 1020 1120 1080 \
        --out screenshots/preview_borders.png
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "spr"))

import build_valley as BV  # noqa: E402

ROOT = BV.ROOT
SPRITES = BV.SPRITES
TERRAIN_DIR = os.path.join(SPRITES, "terrain")
OVERRIDES = os.path.join(SPRITES, "overrides", "10_terrain.json")
CELL = 32

DEFAULT_AREA = (1000, 1020, 1120, 1080)  # x0,y0,x1,y1 -> vila + floresta
FALLBACK = (200, 40, 200, 255)           # magenta: "sprite nao encontrado"


class SpriteBook:
    """server_id -> (PNG carregado, tiles_wh, height_px)."""

    def __init__(self):
        self.by_id = {}
        self._cache = {}
        self._load_overrides()
        self._load_tiles_json()

    def _img(self, relpath):
        img = self._cache.get(relpath)
        if img is None:
            path = os.path.join(TERRAIN_DIR, relpath) if not os.path.isabs(relpath) else relpath
            img = Image.open(path).convert("RGBA")
            self._cache[relpath] = img
        return img

    def _img_root(self, relpath):
        path = os.path.join(SPRITES, relpath)
        img = self._cache.get(path)
        if img is None:
            img = Image.open(path).convert("RGBA")
            self._cache[path] = img
        return img

    def _load_overrides(self):
        with open(OVERRIDES, encoding="utf-8") as fh:
            cfg = json.load(fh)
        for it in cfg["items"]:
            if "server_ids" not in it:
                continue
            frames = it.get("frames") or [it["src"]]
            img = self._img(frames[0])
            tiles = it.get("tiles", 1)
            height = it.get("height", CELL if tiles == 1 else CELL * tiles)
            for sid in it["server_ids"]:
                self.by_id[sid] = (img, tiles, height)

    def _load_tiles_json(self):
        with open(os.path.join(SPRITES, "tiles.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        with open(os.path.join(SPRITES, "allocations.json"), encoding="utf-8") as fh:
            alloc = json.load(fh)["by_key"]
        for t in cfg["tiles"]:
            e = alloc.get(t["key"])
            if e is None:
                continue
            sid = e["server_id"]
            w, h = t.get("size", [1, 1])
            frame0 = t["frames"][0]
            try:
                img = self._img_root(frame0)
            except FileNotFoundError:
                continue
            # tiles.json declara [largura, altura] em tiles; usamos o maior
            # lado para decidir a ancoragem (a maioria e 1x1 ou 1x2 "sobe").
            tiles_span = max(w, h)
            height_px = h * CELL
            self.by_id[sid] = (img, tiles_span if w == h else 1, height_px)

    def get(self, sid):
        return self.by_id.get(sid)


def paste_item(canvas, book, sid, col, row, ox, oy):
    entry = book.get(sid)
    tx, ty = ox + col * CELL, oy + row * CELL
    if entry is None:
        canvas.paste(Image.new("RGBA", (CELL, CELL), FALLBACK), (tx, ty))
        return
    img, tiles, height_px = entry
    w, h = img.size
    # ancora: base do sprite = base do tile (linha `row`), lado direito = col.
    px = tx + CELL - w
    py = ty + CELL - h
    canvas.paste(img, (px, py), img)


def render(b, area, out_path):
    x0, y0, x1, y1 = area
    book = SpriteBook()
    w_px = (x1 - x0 + 1) * CELL
    h_px = (y1 - y0 + 1) * CELL
    canvas = Image.new("RGBA", (w_px, h_px), (10, 10, 12, 255))

    drawn = 0
    missing = set()
    # varre com folga a esquerda/acima (predios 2x2 fora da janela ainda pintam
    # dentro dela); folga de 3 tiles cobre as arvores (2x2) e as paredes (1x2).
    for y in range(y0 - 3, y1 + 1):
        for x in range(x0 - 3, x1 + 1):
            c = b.cells.get((x, y))
            if c is None:
                continue
            col, row = x - x0, y - y0
            if c.ground is not None:
                entry = book.get(c.ground)
                if entry is None:
                    missing.add(c.ground)
                elif 0 <= col < (x1 - x0 + 1) and 0 <= row < (y1 - y0 + 1):
                    img = entry[0]
                    canvas.paste(img.crop((0, 0, CELL, CELL)), (col * CELL, row * CELL))
            for it in c.items:
                entry = book.get(it.id)
                if entry is None:
                    missing.add(it.id)
                paste_item(canvas, book, it.id, col, row, 0, 0)
            drawn += 1
    canvas.crop((0, 0, w_px, h_px)).save(out_path)
    return drawn, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"),
                     default=DEFAULT_AREA)
    ap.add_argument("--out", default=os.path.join(ROOT, "screenshots", "preview_borders.png"))
    args = ap.parse_args()

    types = BV.load_items_otb(BV.ITEMS_OTB)
    tpls, sid, novos = BV.load_imported()
    for k, v in novos.items():
        types.setdefault(k, v)

    b, npcs = BV.build(tpls, sid)
    BV.carve_clearings(b)
    BV.connect_clearings(b)
    placed = BV.apply_borders(b, sid)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    drawn, missing = render(b, tuple(args.area), args.out)
    print("preview -> %s" % args.out)
    print("  area ............. %r" % (tuple(args.area),))
    print("  tiles desenhados .. %d" % drawn)
    print("  bordas colocadas .. %d (mapa inteiro)" % placed)
    if missing:
        print("  AVISO: %d server ids sem PNG conhecido (desenhados em magenta): %s"
              % (len(missing), sorted(missing)[:20]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
