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

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "spr"))

import build_valley as BV  # noqa: E402

ROOT = BV.ROOT
SPRITES = BV.SPRITES
TERRAIN_DIR = os.path.join(SPRITES, "terrain")
OVERRIDES = os.path.join(SPRITES, "overrides", "10_terrain.json")
CELL = 32

DEFAULT_AREA = (1000, 1020, 1120, 1080)  # x0,y0,x1,y1 -> vila + floresta
FULL_AREA = (1000, 1000, 1199, 1119)     # mapa jogavel inteiro (sem interiores/arena)
INTERIORS_AREA = (1298, 998, 1332, 1036)  # apendice: interiores das lojas + arena
VILLAGE_ZOOM_AREA = (1009, 1029, 1050, 1070)
FALLBACK = (200, 40, 200, 255)           # magenta: "sprite nao encontrado"

#: rotulos (nome, x, y) para a versao anotada — coordenadas do MUNDO (nao px).
#: y eh a linha de cima do texto; o texto desce a partir dai.
LABELS = [
    ("Portao Sul", BV.GATE_X[0] - 3, BV.GATE_Y + 3),
    ("Templo", BV.TEMPLE[0], BV.TEMPLE[1] - 2),
    ("Praca Central", BV.PLAZA[0], BV.PLAZA[1] - 1),
    ("Torre do Hokage", 1023, 1030),
    ("Bairro Residencial (N)", 1012, 1029),
    ("Rua dos Mercadores", BV.SHOPS[0][3] - 1, BV.SHOP_ROW_Y - 6),
    ("Ichiro", BV.SHOPS[0][3], BV.SHOP_ROW_Y - 4),
    ("Hayato", BV.SHOPS[1][3], BV.SHOP_ROW_Y - 4),
    ("Rin", BV.SHOPS[2][3], BV.SHOP_ROW_Y - 4),
    ("Academia Ninja", BV.ACADEMY[0] - 1, BV.ACADEMY[1] - 3),
    ("Taverna / Prisao", BV.PRISON_XY[0], BV.PRISON_XY[1] + 3),
    ("Bairro Residencial (S)", 1020, 1066),
    ("Portao Leste", BV.GATE_E_X + 1, (BV.GATE_E_Y[0] + BV.GATE_E_Y[1]) // 2),
    ("Ponte", BV.RIVER_X0 - 1, BV.BRIDGE_Y0 - 3),
    ("Muro da Floresta da Morte", BV.DEATH_WALL[0] + 1, BV.DEATH_GATE_Y[0] - 3),
    ("Hub do Pantano", BV.HUB[0], BV.HUB[1] - 2),
    ("Torre do Sapo Anciao", BV.TOWER[0] - 3, BV.TOWER[1] - 3),
    ("Acampamento dos Bandidos", BV.CAMP_CENTER[0] - 6, BV.CAMP_CENTER[1] - 9),
] + [(name, cx - 2, cy - r - 2) for (name, cx, cy, r) in BV.CLEARINGS] \
  + [(name, cx - 2, cy - r - 2) for (name, cx, cy, r) in BV.DEATH_CLEARINGS]

INTERIOR_LABELS = [
    ("Interior - Ichiro", BV.INTERIOR_ICHIRO[0], BV.INTERIOR_ICHIRO[1] - 2),
    ("Interior - Hayato", BV.INTERIOR_HAYATO[0], BV.INTERIOR_HAYATO[1] - 2),
    ("Interior - Rin", BV.INTERIOR_RIN[0], BV.INTERIOR_RIN[1] - 2),
    ("Arena do Exame Chunin", BV.ARENA[0], BV.ARENA[1] - 2),
]


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

    #: ids vanilla usados no v2 (mobiliario de interior/praca/arena) sem PNG
    #: no override de terreno — o cliente real ja tem o sprite oficial via
    #: Tibia.dat/.spr; aqui e so pra o preview nao pintar tudo de magenta.
    #: (cor RGBA, letra)
    _EXTRA_PLACEHOLDERS = {
        1360: ((80, 150, 220, 255), "F"),   # fountain
        1387: ((160, 60, 220, 255), "T"),   # magic forcefield / teleport
        1617: ((150, 100, 60, 255), "C"),   # counter
        1622: ((150, 100, 60, 255), "M"),   # table
        1662: ((120, 90, 60, 255), "B"),    # bench
        1740: ((190, 150, 40, 255), "X"),   # chest
        1442: ((140, 140, 150, 255), "S"),  # statue
    }

    def _placeholder(self, sid):
        color, letter = self._EXTRA_PLACEHOLDERS[sid]
        img = self._cache.get(("_ph", sid))
        if img is None:
            img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.ellipse((3, 3, CELL - 3, CELL - 3), fill=color, outline=(0, 0, 0, 255))
            d.text((CELL // 2 - 4, CELL // 2 - 7), letter, fill=(255, 255, 255, 255))
            self._cache[("_ph", sid)] = img
        return (img, 1, CELL)

    def get(self, sid):
        entry = self.by_id.get(sid)
        if entry is None and sid in self._EXTRA_PLACEHOLDERS:
            entry = self._placeholder(sid)
        return entry


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


def _font(size):
    # DejaVuSans-Bold costuma vir junto do Pillow (mesmo pacote de fontes
    # padrao); se nao existir no ambiente, cai pro bitmap default do PIL
    # (ainda legivel, so mais feio/pequeno).
    for name in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_labels(canvas, area, labels, cell=CELL):
    """Escreve rotulos (nome, x, y) em coordenadas do MUNDO por cima do
    canvas ja desenhado, com uma faixa escura atras pra ficar legivel sobre
    qualquer chao. Rotulos fora da area sao ignorados."""
    x0, y0, x1, y1 = area
    draw = ImageDraw.Draw(canvas, "RGBA")
    font = _font(14)
    drawn = 0
    for (text, wx, wy) in labels:
        if not (x0 <= wx <= x1 and y0 <= wy <= y1):
            continue
        px, py = (wx - x0) * cell, (wy - y0) * cell
        bbox = draw.textbbox((px, py), text, font=font)
        pad = 2
        draw.rectangle((bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad),
                        fill=(0, 0, 0, 175))
        draw.text((px, py), text, fill=(255, 230, 120, 255), font=font)
        drawn += 1
    return drawn


PRESETS = {
    "default": DEFAULT_AREA,
    "full": FULL_AREA,
    "interiors": INTERIORS_AREA,
    "vila_zoom": VILLAGE_ZOOM_AREA,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"),
                     default=None)
    ap.add_argument("--preset", choices=sorted(PRESETS), default="default",
                     help="area pre-definida (ignorado se --area for passado)")
    ap.add_argument("--zoom", type=int, default=1,
                     help="fator de ampliacao (redimensiona o PNG final, ex.: 3)")
    ap.add_argument("--labels", action="store_true",
                     help="desenha os nomes das zonas/lojas por cima (versao anotada)")
    ap.add_argument("--out", default=os.path.join(ROOT, "screenshots", "preview_borders.png"))
    args = ap.parse_args()
    area = tuple(args.area) if args.area else PRESETS[args.preset]

    types = BV.load_items_otb(BV.ITEMS_OTB)
    tpls, sid, novos = BV.load_imported()
    for k, v in novos.items():
        types.setdefault(k, v)

    b, npcs = BV.build(tpls, sid)
    BV.carve_clearings(b)
    BV.connect_clearings(b)
    placed = BV.apply_borders(b, sid)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    drawn, missing = render(b, area, args.out)

    n_labels = 0
    if args.labels:
        canvas = Image.open(args.out).convert("RGBA")
        all_labels = LABELS + INTERIOR_LABELS
        n_labels = draw_labels(canvas, area, all_labels)
        canvas.save(args.out)

    if args.zoom and args.zoom != 1:
        canvas = Image.open(args.out).convert("RGBA")
        canvas = canvas.resize((canvas.width * args.zoom, canvas.height * args.zoom),
                                Image.NEAREST)
        canvas.save(args.out)

    print("preview -> %s" % args.out)
    print("  area ............. %r" % (area,))
    print("  tiles desenhados .. %d" % drawn)
    print("  bordas colocadas .. %d (mapa inteiro)" % placed)
    if args.labels:
        print("  rotulos ........... %d" % n_labels)
    if missing:
        print("  AVISO: %d server ids sem PNG conhecido (desenhados em magenta): %s"
              % (len(missing), sorted(missing)[:20]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
