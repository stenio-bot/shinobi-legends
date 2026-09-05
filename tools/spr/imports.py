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

from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import char_synth as _CS   # noqa: E402  (nitidez do downscale, ver fit_uniform)

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


def _foot_center(img):
    """Centro horizontal do APOIO: centroide dos pixels opacos do terco inferior.

    Centralizar pela caixa faz o corpo escorregar quando um braco/perna se estende
    para fora (poses de ataque, passo largo). O ponto de contato com o chao e o que
    precisa ficar parado entre as fases."""
    px = img.load()
    y0 = max(0, img.height - max(4, img.height // 3))
    tot = n = 0
    for y in range(y0, img.height):
        for x in range(img.width):
            if px[x, y][3] >= 128:
                tot += x
                n += 1
    if not n:
        return img.width / 2.0
    return tot / float(n)


def fit_uniform(img, box, scale, mirror=False, sharpen=True, outline=True):
    """Encaixa um quadro numa celula de `box` px com uma escala JA DECIDIDA.

    Ao contrario de `fit()`, que redimensiona cada quadro para preencher a celula,
    aqui a escala e a MESMA para todos os quadros da criatura — senao o boneco
    encolhe e cresce a cada fase e a cada direcao. Depois de escalar, o quadro e
    alinhado pela BASE (pes no chao da celula) e pelo centro do apoio.

    `sharpen` troca o downscale de LANCZOS direto por **downscale de AREA
    (Image.BOX, media dos pixels) + realce** (`char_synth.unsharp`) — comparado
    em `tools/spr/compare_sharpen.py` contra LANCZOS puro e contra quantizar a
    paleta original: a quantizacao por pixel mais proximo criou RUIDO de
    sal-e-pimenta nas bordas ja suavizadas (a paleta do material tem centenas de
    tons por causa do antialiasing do rip; "cor mais proxima" por pixel escolhe
    tons errados nas bordas) e foi descartada. `outline` redesenha um contorno
    escuro de 1px na silhueta final — o contorno do material original se perde
    no downscale de 60->32px, e o estilo Tibia depende de silhueta legivel.
    """
    img = _trim(img.convert("RGBA"))
    if mirror:
        img = ImageOps.mirror(img)
    if scale < 1.0:
        w = max(1, round(img.width * scale))
        h = max(1, round(img.height * scale))
        if sharpen:
            img = img.resize((w, h), Image.BOX)
            img = _CS.unsharp(img, amount=0.8)
        else:
            img = img.resize((w, h), Image.LANCZOS)
    img = _binarize(img.convert("RGBA"))
    img = _trim(img)                      # o resize pode devolver borda vazia
    out = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    x = int(round(box / 2.0 - _foot_center(img)))
    x = max(min(x, box - img.width), min(0, box - img.width))
    out.paste(img, (x, box - img.height))
    if sharpen and outline:
        out = _CS.outline_1px(out)
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

    # ---- criaturas: quadro solto de uma entrada `directions`
    def _dir_frame(self, spec, e):
        """Um quadro de `directions`: "caminho.png" ou {"src":..., "mirror":true}."""
        if isinstance(spec, str):
            spec = {"src": spec}
        img = self._open({"src": spec["src"], "crop": spec.get("crop", e.get("crop"))})
        if img is None:
            return None
        return _trim(img), bool(spec.get("mirror"))

    def creature_dirs(self, e):
        """Criatura com arte POR DIRECAO e ciclo de andar (ver README/FORMATO).

            "directions": {
              "0": {"idle": "a.png", "walk": ["b.png", "a.png",
                                              {"src": "b.png", "mirror": true}]},
              "1": {...}, "2": {...},
              "3": {"mirror_of": 1}            <- espelha a direcao 1
            }

        Direcoes na ordem do enum Otc::Direction: 0=Norte, 1=Leste, 2=Sul, 3=Oeste.
        Produz frame group 0 (parado, 1 fase) + frame group 1 (andando, N fases),
        `layers = 1` (a arte importada ja vem colorida).

        Todos os quadros usam a MESMA escala (a maior que faz o quadro mais alto
        caber na celula) e sao alinhados pela base dos pes — e o que impede o
        boneco de "pular" e de mudar de tamanho ao virar ou andar.
        """
        dirs = e["directions"]
        raw = {}          # d -> [(img, mirror), ...]  (indice 0 = parado)
        pend = {}         # d -> direcao de origem (mirror_of), resolvido depois
        n_walk = 0
        for d in range(DIRECTIONS):
            cfg = dirs.get(str(d)) or dirs.get(d)
            if cfg is None:
                self.warnings.append("%s: direcao %d ausente em 'directions'"
                                     % (e.get("name", e["id"]), d))
                return None
            if "mirror_of" in cfg:
                pend[d] = int(cfg["mirror_of"])
                continue
            walk = cfg.get("walk") or [cfg["idle"]]
            got = [self._dir_frame(s, e) for s in [cfg["idle"]] + list(walk)]
            if any(g is None for g in got):
                return None            # PNG ausente: ja registrado em self.missing
            raw[d] = got
            n_walk = max(n_walk, len(walk))
        for d, src in pend.items():
            if src not in raw:
                self.warnings.append("%s: mirror_of %d nao resolve" % (e.get("name"), src))
                return None
            raw[d] = [(img, not mir) for img, mir in raw[src]]

        # fases iguais em todas as direcoes (repete a ultima quando faltar)
        for d in raw:
            while len(raw[d]) < 1 + n_walk:
                raw[d].append(raw[d][-1])

        tiles = int(e.get("tiles") or 1)
        box = tiles * CELL
        big = max(max(i.width for i, _ in v) for v in raw.values())
        tall = max(max(i.height for i, _ in v) for v in raw.values())
        scale = min(box / float(big), box / float(tall), 1.0)

        rows = PHASES_IDLE + n_walk
        sh = Image.new("RGBA", (DIRECTIONS * box, rows * box), (0, 0, 0, 0))
        for d in range(DIRECTIONS):
            for row in range(rows):
                img, mir = raw[d][row]
                sh.paste(fit_uniform(img, box, scale, mir), (d * box, row * box))
        rel = self._save(sh, "look_%03d.png" % e["id"])
        dur = int(e.get("duration", 220))
        self.applied["creatures"] += 1
        return {
            "category": "creature", "id": e["id"],
            "name": e.get("name", "import_%03d" % e["id"]),
            "width": tiles, "height": tiles, "exact_size": min(255, box),
            "layers": 1,
            "pattern_x": DIRECTIONS, "pattern_y": 1, "pattern_z": 1,
            "frame_groups": [
                {"type": 0, "phases": PHASES_IDLE},
                {"type": 1, "phases": n_walk,
                 "animation": {"async": False, "loop_count": 0, "start_phase": 0,
                               "durations": [[dur, dur]] * n_walk}},
            ],
            "sheets": [rel],
            "_import": "directions",
        }

    # ---- criaturas
    def creature(self, e):
        if e.get("directions"):
            return self.creature_dirs(e)
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

    # "creature_sheets": things de creature JA MONTADOS por um gerador proprio
    # (tools/spr/gen_animals.py, tools/spr/gen_humanoid_variants.py) — ao contrario
    # de "creatures" (que le PNGs crus em `root` e monta a folha aqui), essas entradas
    # ja trazem "sheets" apontando para PNGs prontos em assets-src/sprites/creatures/,
    # entao sao copiadas para o manifesto sem nenhum processamento de imagem. Permite
    # layers=2 (mascara de cor) num override, o que "creatures"/"creature_dirs" nao
    # suportam (sempre gravam layers=1, pensado pra arte importada ja colorida).
    for e in cfg.get("creature_sheets", []):
        spec = dict(e)
        k = ("creature", spec["id"])
        if k in by_key:
            manifest["things"][by_key[k]] = spec
        else:
            by_key[k] = len(manifest["things"])
            manifest["things"].append(spec)
        imp.applied["creatures"] += 1

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
