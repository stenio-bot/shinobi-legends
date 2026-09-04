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
import sys

from PIL import Image

CELL = 32
FLAG_ANIMATION = 1 << 24        # itemflags_t do items.otb (ver FORMATO.md secao 5)
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


def _build_assets():
    """O modulo build_assets, sem importar em circulo.

    build_assets importa este arquivo no topo; quando ele roda como script o seu
    nome e ``__main__``. Reaproveitar o modulo ja carregado evita executa-lo duas
    vezes (e evita duplicar aqui a traducao flags do OTB -> atributos do .dat)."""
    for name in ("build_assets", "__main__"):
        mod = sys.modules.get(name)
        if mod is not None and hasattr(mod, "item_attrs"):
            return mod
    import build_assets            # noqa: F401  (fallback: uso fora do build)
    return build_assets


def _dat_attrs(otb_item):
    """Atributos do .dat do item, no formato do manifesto (["A_GROUND", 100])."""
    import sprformat as S
    ba = _build_assets()
    names = {getattr(S, n): n for n in dir(S) if n.startswith("A_")}
    return [[names[a]] + list(args) for a, args in ba.item_attrs(otb_item)]


_OTB_CACHE = {}


def otb_items(manifest, root):
    """Itens do items.otb BASE (o .vanilla quando existe, igual ao build)."""
    path = os.path.join(root, manifest["items"]["otb"])
    if os.path.exists(path + ".vanilla"):
        path += ".vanilla"
    got = _OTB_CACHE.get(path)
    if got is None:
        from otb import parse_items_otb
        got = _OTB_CACHE[path] = parse_items_otb(path)[1]
    return got


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
        self.warnings = []
        self.applied = {"creatures": 0, "effects": 0, "missiles": 0, "items": 0,
                        "item_things": 0}

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

    # ---- icones de item (1x1, arte solta que so troca o desenho)
    def item(self, e):
        img = self._open(e)
        if img is None:
            return None
        cell = fit(img, 1, anchor="center", upscale_small=True)
        rel = self._save(cell, "item_%s.png" % e["name"])
        self.applied["items"] += 1
        return rel

    # ---- itens com GEOMETRIA propria (multi-tile / parede alta / animados)
    def item_thing(self, e, otb_item, client_id):
        """Monta um thing de item completo para o manifesto.

        Aceita, alem de `src`/`crop`:

        ``tiles``          1 ou 2 — largura = altura em tiles, ancorado no canto
                           INFERIOR DIREITO (o cliente desenha o sprite (w,h) em
                           ``((width-1-w),(height-1-h))*32``: a arte sobe e vai
                           para a esquerda, como as arvores da Tibia).
        ``height``         64 -> 1 tile de largura por 2 de altura (paredes: a
                           parede sobe 32px acima do tile).
        ``frames``+``duration``  animacao -> ``animationPhases > 1`` com bloco
                           Animator. **Regra da secao 5 do FORMATO.md**: quem
                           manda e a FLAG_ANIMATION do OTB. Sem a flag o item NAO
                           pode ter mais de 1 fase (sobraria um byte no pacote de
                           mapa); com a flag ele PRECISA de pelo menos 2.
        ``displacement``   [x, y] opcional (atributo Displacement do .dat).

        O item ja existe no items.otb: grupo, flags, luz e speed vem de la — aqui
        so muda a arte e a geometria.
        """
        frames = self._frames(e)
        if frames is None:
            return None

        if e.get("height") and int(e["height"]) > CELL:
            w_t, h_t = 1, int(e["height"]) // CELL
        else:
            w_t = h_t = int(e.get("tiles", 1))
        w_px, h_px = w_t * CELL, h_t * CELL

        animated = bool(otb_item["flags"] & FLAG_ANIMATION)
        if len(frames) > 1 and not animated:
            self.warnings.append(
                "%s (server id %s): o OTB nao tem FLAG_ANIMATION, %d fases "
                "reduzidas a 1 (FORMATO.md secao 5)"
                % (e["name"], e["server_ids"][0], len(frames)))
            frames = frames[:1]
        if animated and len(frames) == 1:
            frames = frames * 2          # 2 fases obrigatorias; mesmo sprite

        cells = []
        for f in frames:
            cell = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
            f = _binarize(f.convert("RGBA"))
            if f.size != (w_px, h_px):   # encaixa no canto inferior direito
                f = _trim(f)
                s = min(w_px / f.width, h_px / f.height, 1.0)
                if s < 1.0:
                    f = f.resize((max(1, round(f.width * s)),
                                  max(1, round(f.height * s))), Image.LANCZOS)
                    f = _binarize(f.convert("RGBA"))
            cell.paste(f, (w_px - f.width, h_px - f.height))
            cells.append(cell)

        sh = Image.new("RGBA", (w_px, len(cells) * h_px), (0, 0, 0, 0))
        for i, c in enumerate(cells):
            sh.paste(c, (0, i * h_px))
        rel = self._save(sh, "item_%s.png" % e["name"])

        attrs = _dat_attrs(otb_item)
        disp = e.get("displacement")
        if disp:
            attrs.append(["A_DISPLACEMENT", int(disp[0]), int(disp[1])])

        group = {"type": 0, "phases": len(cells)}
        if len(cells) > 1:
            dur = int(e.get("duration", 500))
            group["animation"] = {"async": True, "loop_count": 0, "start_phase": 0,
                                  "durations": [[dur, dur]] * len(cells)}
        self.applied["item_things"] += 1
        return {
            "category": "item", "id": client_id,
            "name": e.get("name", "item_%d" % client_id),
            "width": w_t, "height": h_t,
            "exact_size": min(255, max(w_px, h_px)),
            "layers": 1, "pattern_x": 1, "pattern_y": 1, "pattern_z": 1,
            "frame_groups": [group],
            "sheets": [rel],
            "attrs": attrs,
            "_import": e.get("frames") or e.get("src"),
        }


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
    by_sid = None
    for e in cfg.get("items", []):
        if not e.get("server_ids"):
            continue                     # entrada so de comentario ("_g": "...")
        rich = bool(e.get("tiles", 1) != 1 or e.get("height") or e.get("displacement")
                    or len(e.get("frames") or [e.get("src")]) > 1)
        if not rich:
            rel = imp.item(e)
            if rel is None:
                continue
            for sid in e["server_ids"]:
                ov[str(sid)] = {"name": e["name"], "sheet": rel, "icon": "import"}
            continue

        # geometria propria: vira um thing de item no manifesto, que o build
        # aplica DEPOIS de build_items() e portanto substitui a arte de regra.
        if by_sid is None:
            by_sid = {it["server_id"]: it for it in otb_items(manifest, root)}
        for sid in e["server_ids"]:
            it = by_sid.get(int(sid))
            if not it or not it["client_id"]:
                imp.warnings.append("%s: server id %s nao existe no items.otb"
                                    % (e.get("name"), sid))
                continue
            spec = imp.item_thing(e, it, it["client_id"])
            if spec is None:
                break                    # PNG ausente: ja registrado em missing
            k = ("item", spec["id"])
            if k in by_key:
                manifest["things"][by_key[k]] = spec
            else:
                by_key[k] = len(manifest["things"])
                manifest["things"].append(spec)
    for w in imp.warnings:
        print("imports: AVISO:", w)
    return imp


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
