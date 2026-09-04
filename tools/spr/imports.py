#!/usr/bin/env python3
"""Aplica assets-src/sprites/imports.json por cima do manifest.json.

O imports.json diz qual recorte de assets-src/import/extracted/ vira qual
looktype / efeito / missile / icone de item. Os PNGs de origem vem do material
privado do usuario (assets-src/import/ esta no .gitignore), entao **toda entrada
cujo PNG nao existir e ignorada com aviso** — o build continua com o placeholder.

As folhas montadas (ja encaixadas na grade 32x32 do Tibia) sao gravadas em
assets-src/import/extracted/_sheets/ e referenciadas no manifesto por caminho
relativo ao sheet_root (../import/extracted/_sheets/...).

Ver docs/sistemas/arte-e-sprites.md, secao "Importar folhas de sprites".
"""
import json
import os

from PIL import Image

CELL = 32
MAX_TILES = 4          # o .dat guarda width/height em U8; o cliente aceita ate 4
DIRECTIONS = 4
PHASES_IDLE = 1
PHASES_MOVING = 3


# --------------------------------------------------------------- utilidades
def _binarize(img):
    """O .spr 1098 e RGB: alpha vira binario (>=128 opaco)."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)
    return img


def _trim(img):
    box = img.getbbox()
    return img.crop(box) if box else img


def auto_tiles(img):
    """Quantos tiles de 32px o sprite ocupa. Ate 1.4x de folga cabe no tile de
    baixo (o recorte e reduzido), acima disso sobe um tamanho."""
    m = max(img.width, img.height)
    for t in range(1, MAX_TILES + 1):
        if m <= t * CELL * 1.45:
            return t
    return MAX_TILES


def fit(img, tiles, anchor="bottom", upscale_small=False):
    """Encaixa o recorte numa celula de tiles*32. Ancorado embaixo e centralizado
    na horizontal (e assim que o Tibia desenha: o tile do bicho e o canto
    inferior direito da caixa)."""
    box = tiles * CELL
    img = _trim(img)
    s = min(box / img.width, box / img.height)
    if s < 1.0:
        img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))),
                         Image.LANCZOS)
    elif upscale_small and s >= 2.0:
        k = int(min(s, 2))
        img = img.resize((img.width * k, img.height * k), Image.NEAREST)
    img = _binarize(img.convert("RGBA"))
    out = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    x = (box - img.width) // 2
    y = box - img.height if anchor == "bottom" else (box - img.height) // 2
    out.paste(img, (x, y))
    return out


def scaled(img, factor):
    if factor == 1.0:
        return img.copy()
    w = max(1, round(img.width * factor))
    h = max(1, round(img.height * factor))
    small = img.resize((w, h), Image.LANCZOS if factor < 1 else Image.NEAREST)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(small, ((img.width - w) // 2, (img.height - h) // 2))
    return _binarize(out)


# ------------------------------------------------------------------ montagem
class Importer:
    def __init__(self, cfg, root, sheet_root):
        self.cfg = cfg
        self.src_root = os.path.join(root, cfg.get("root", "assets-src/import/extracted"))
        self.build_dir = os.path.join(root, cfg.get("build_dir",
                                                    "assets-src/import/extracted/_sheets"))
        self.sheet_root = sheet_root
        os.makedirs(self.build_dir, exist_ok=True)
        self.missing = []
        self.applied = {"creatures": 0, "effects": 0, "missiles": 0, "items": 0}

    # ---- fontes
    def _open(self, entry, key="src"):
        rel = entry[key]
        path = os.path.join(self.src_root, rel)
        if not os.path.exists(path):
            self.missing.append(rel)
            return None
        img = Image.open(path).convert("RGBA")
        crop = entry.get("crop")
        if crop:
            img = img.crop((crop[0], crop[1], crop[0] + crop[2], crop[1] + crop[3]))
        return img

    def _frames(self, entry):
        rels = entry.get("frames") or [entry["src"]]
        out = []
        for rel in rels:
            img = self._open({"src": rel, "crop": entry.get("crop")})
            if img is None:
                return None
            out.append(img)
        return out

    def _save(self, img, name):
        path = os.path.join(self.build_dir, name)
        img.save(path)
        return os.path.relpath(path, self.sheet_root).replace(os.sep, "/")

    # ---- criaturas
    def creature(self, e):
        srcs = e.get("dirs") or [e.get("src")] * DIRECTIONS
        imgs = []
        for rel in srcs:
            img = self._open({"src": rel, "crop": e.get("crop")})
            if img is None:
                return None
            imgs.append(img)
        tiles = e.get("tiles") or auto_tiles(imgs[0])
        cells = [fit(i, tiles) for i in imgs]
        rows = PHASES_IDLE + PHASES_MOVING
        sh = Image.new("RGBA", (DIRECTIONS * tiles * CELL, rows * tiles * CELL), (0, 0, 0, 0))
        for row in range(rows):
            for d in range(DIRECTIONS):
                sh.paste(cells[d % len(cells)], (d * tiles * CELL, row * tiles * CELL))
        rel = self._save(sh, "look_%03d.png" % e["id"])
        self.applied["creatures"] += 1
        return {
            "category": "creature", "id": e["id"],
            "name": e.get("name", "import_%03d" % e["id"]),
            "width": tiles, "height": tiles, "exact_size": min(255, tiles * CELL),
            "layers": 1,                       # arte importada ja vem colorida
            "pattern_x": DIRECTIONS, "pattern_y": 1, "pattern_z": 1,
            "frame_groups": [
                {"type": 0, "phases": PHASES_IDLE},
                {"type": 1, "phases": PHASES_MOVING,
                 "animation": {"async": False, "loop_count": 0, "start_phase": 0,
                               "durations": [[220, 220]] * PHASES_MOVING}},
            ],
            "sheets": [rel],
            "_import": e.get("dirs") or e.get("src"),
        }

    # ---- efeitos
    def effect(self, e):
        frames = self._frames(e)
        if frames is None:
            return None
        grow = e.get("grow")
        if grow:
            base = frames[0]
            frames = [scaled(base, f) for f in grow]
        tiles = e.get("tiles") or auto_tiles(frames[0])
        cells = [fit(f, tiles, anchor="center") for f in frames]
        sh = Image.new("RGBA", (tiles * CELL, len(cells) * tiles * CELL), (0, 0, 0, 0))
        for i, c in enumerate(cells):
            sh.paste(c, (0, i * tiles * CELL))
        rel = self._save(sh, "effect_%03d.png" % e["id"])
        dur = e.get("duration", 100)
        self.applied["effects"] += 1
        return {
            "category": "effect", "id": e["id"],
            "name": e.get("name", "import_fx_%03d" % e["id"]),
            "width": tiles, "height": tiles, "exact_size": min(255, tiles * CELL),
            "layers": 1, "pattern_x": 1, "pattern_y": 1, "pattern_z": 1,
            "frame_groups": [{"type": 0, "phases": len(cells),
                              "animation": {"async": True, "loop_count": 1,
                                            "start_phase": 0,
                                            "durations": [[dur, dur]] * len(cells)}}],
            "sheets": [rel],
            "_import": e.get("frames") or e.get("src"),
        }

    # ---- missiles (3x3 direcoes)
    def missile(self, e):
        img = self._open(e)
        if img is None:
            return None
        import math
        base = e.get("rotate")           # angulo em que a arte "aponta" (graus)
        cells = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                cur = img
                if base is not None and (dx or dy):
                    want = math.degrees(math.atan2(-dy, dx))
                    cur = img.rotate(want - base, resample=Image.NEAREST, expand=True)
                cells.append(fit(cur, 1, anchor="center"))
        sh = Image.new("RGBA", (3 * CELL, 3 * CELL), (0, 0, 0, 0))
        for i, c in enumerate(cells):
            sh.paste(c, ((i % 3) * CELL, (i // 3) * CELL))
        rel = self._save(sh, "missile_%03d.png" % e["id"])
        self.applied["missiles"] += 1
        return {
            "category": "missile", "id": e["id"],
            "name": e.get("name", "import_mi_%03d" % e["id"]),
            "width": 1, "height": 1, "layers": 1,
            "pattern_x": 3, "pattern_y": 3, "pattern_z": 1,
            "frame_groups": [{"type": 0, "phases": 1}],
            "sheets": [rel],
            "_import": e["src"],
        }

    # ---- icones de item (1x1)
    def item(self, e):
        img = self._open(e)
        if img is None:
            return None
        cell = fit(img, 1, anchor="center", upscale_small=True)
        rel = self._save(cell, "item_%s.png" % e["name"])
        self.applied["items"] += 1
        return rel


def apply(manifest, cfg, root, sheet_root):
    """Sobrescreve things e overrides de item do manifesto. Devolve o Importer
    com as estatisticas."""
    imp = Importer(cfg, root, sheet_root)

    by_key = {}
    for i, th in enumerate(manifest["things"]):
        by_key[(th["category"], th["id"])] = i

    for kind, fn in (("creatures", imp.creature), ("effects", imp.effect),
                     ("missiles", imp.missile)):
        cat = {"creatures": "creature", "effects": "effect", "missiles": "missile"}[kind]
        for e in cfg.get(kind, []):
            spec = fn(e)
            if spec is None:
                continue
            k = (cat, e["id"])
            if k in by_key:
                manifest["things"][by_key[k]] = spec
            else:
                by_key[k] = len(manifest["things"])
                manifest["things"].append(spec)

    ov = manifest["items"]["overrides"]
    for e in cfg.get("items", []):
        rel = imp.item(e)
        if rel is None:
            continue
        for sid in e["server_ids"]:
            ov[str(sid)] = {"name": e["name"], "sheet": rel, "icon": "import"}
    return imp


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
