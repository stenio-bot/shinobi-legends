#!/usr/bin/env python3
"""Extrai terreno e objetos REAIS de screenshots de clientes Open Tibia.

Passos (subcomandos):

  grid     descobre a escala (px por tile) e o deslocamento da grade por
           autocorrelacao da textura do chao e alinhamento das bordas de
           terreno; desenha a grade numerada sobre uma copia da imagem.
  ground   classifica cada celula da grade por cor media/variancia em
           grama clara / grama escura / terra, descarta celulas sujas
           (arvore, sombra, criatura, borda de terreno) pela distancia a
           mediana da classe, deduplica e salva variantes 32x32.
  objects  recorta objetos (arvores, arbustos, pedras, tufos, galhos) em
           caixas alinhadas a grade, com o chao removido por diferenca com
           a cor de fundo local -> canal alpha.
  sheet    monta a folha de revisao 8x8 com os tiles lado a lado, para
           conferir se as bordas casam (tileable).

Escala descoberta neste material: o cliente NAO desenha 32 px por tile.
Ele renderiza 21 tiles na largura de 1920 px, entao cada tile ocupa
1920/21 = 91.43 px (o equivalente a um zoom de ~2.86x sobre a arte de 32).
Por isso todo recorte de chao e reduzido de 91 -> 32 com LANCZOS + unsharp
leve + quantizacao, para voltar ao "pixel art" de 32.

Saida: assets-src/import/extracted/screenshot/ (material privado, fora do git).
Consumido por assets-src/sprites/overrides/20_screenshot.json.

Ver docs/sistemas/arte-e-sprites.md, secao "Extracao de screenshots".
"""
import argparse
import hashlib
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(ROOT, "assets-src", "import")
OUT_DIR = os.path.join(SRC_DIR, "extracted", "screenshot")
DEFAULT_IMG = os.path.join(SRC_DIR, "screenshot_forest_full.png")

CELL = 32                 # tamanho final (grade do Tibia)
UI_TOP = 34               # barra de icones do cliente
FPS_BOX = (0, 0, 345, 42)  # caixa do contador de FPS


# ------------------------------------------------------------------ utilidades
def load(path):
    return Image.open(path).convert("RGB")


def arr(img):
    return np.asarray(img, dtype=np.float32)


def in_ui(x, y, w, h):
    """A caixa (x,y,w,h) encosta na barra de UI ou no contador de FPS?"""
    if y < UI_TOP:
        return True
    fx0, fy0, fx1, fy1 = FPS_BOX
    return x < fx1 and y < fy1 and x + w > fx0 and y + h > fy0


def to32(patch, sharp=1.0, colors=0, box=None, tiles=1):
    """91x91 (ou o que for) -> 32x32 pixel art: LANCZOS + unsharp + quantizacao.

    `box` e a caixa de origem em coordenadas FRACIONARIAS: como o periodo real e
    91.4286 e nao um inteiro, cortar em pixel inteiro acumula ~0.43 px de erro
    por tile e estraga a costura. Image.resize(box=...) reamostra na posicao
    exata e resolve isso."""
    img = patch.resize((CELL * tiles, CELL * tiles), Image.LANCZOS, box=box)
    if sharp:
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=int(60 * sharp),
                                                 threshold=2))
    if colors:
        img = img.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT,
                                          dither=Image.NONE).convert("RGB")
    return img


def phash(img):
    return hashlib.md5(img.convert("RGB").resize((16, 16), Image.LANCZOS).tobytes()
                       ).hexdigest()[:12]


# ------------------------------------------------------------------- 1. grade
def autocorr(a, axis, lo, hi):
    out = {}
    for p in range(lo, hi + 1):
        d = a[p:] - a[:-p] if axis == 0 else a[:, p:] - a[:, :-p]
        out[p] = float(np.abs(d).mean())
    return out


def sharpest_dip(prof, win=8):
    def dip(p):
        v = [prof[q] for q in range(p - win, p + win + 1)
             if q in prof and abs(q - p) > 2]
        return (sum(v) / len(v)) - prof[p] if v else -1e9
    best = max(prof, key=dip)
    return best, dip(best)


def detect_period(img):
    """Periodo do tile em px. O chao do Tibia repete a cada tile, entao a
    autocorrelacao da area de mapa tem um vale nitido no periodo (e nos seus
    multiplos). Depois refina para a fracao exata 1920/N, porque o cliente
    escala o framebuffer para a janela e o periodo raramente e inteiro."""
    a = arr(img)[UI_TOP:, :, :]
    px = autocorr(a, 1, 20, 160)
    py = autocorr(a, 0, 20, 160)
    prof = {p: (px[p] + py[p]) / 2 for p in px}
    p, strength = sharpest_dip(prof)
    # fracao exata: quantos tiles cabem na largura
    n = round(img.width / p)
    exact = img.width / n
    return exact, p, n, strength, prof


def terrain_mask(a):
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    return (r > 145) & (g > 115) & (b > 80) & (r > g + 18)   # terra/areia


def detect_offset(img, period):
    """Fase da grade. As bordas entre tipos de chao (grama<->terra) sao
    desenhadas por tiles inteiros de borda, entao as transicoes da mascara de
    terra se acumulam nas linhas da grade."""
    a = arr(img)
    m = terrain_mask(a)
    m[:UI_TOP] = False
    n = int(round(period))
    accx = np.zeros(n + 1)
    accy = np.zeros(n + 1)
    for y in range(UI_TOP, m.shape[0]):
        for x in np.where(m[y, 1:] != m[y, :-1])[0] + 1:
            if x > 3 and x < m.shape[1] - 3:
                accx[int(round(x % period)) % n] += 1
    for x in range(m.shape[1]):
        col = m[:, x]
        for y in np.where(col[UI_TOP + 1:] != col[UI_TOP:-1])[0] + UI_TOP + 1:
            if y < m.shape[0] - 3:
                accy[int(round(y % period)) % n] += 1
    def smooth(v):
        k = np.array([1, 2, 3, 2, 1], dtype=np.float32)
        return np.convolve(np.concatenate([v[-2:], v, v[:2]]), k, "valid")
    return int(np.argmax(smooth(accx[:n]))), int(np.argmax(smooth(accy[:n])))


def grid_of(img, period, ox, oy):
    """Lista de (col, row, x, y) das celulas inteiras fora da UI."""
    out = []
    col = 0
    x = ox
    while x + period <= img.width:
        row = 0
        y = oy
        while y + period <= img.height:
            if not in_ui(int(x), int(y), int(period), int(period)):
                out.append((col, row, x, y))
            row += 1
            y += period
        col += 1
        x += period
    return out


def crop(img, x, y, period, tiles=1):
    s = int(round(period * tiles))
    return img.crop((int(round(x)), int(round(y)), int(round(x)) + s,
                     int(round(y)) + s))


def cmd_grid(args):
    img = load(args.image)
    exact, raw, n, strength, prof = detect_period(img)
    ox, oy = detect_offset(img, exact)
    print("autocorrelacao: vale mais nitido em %d px (forca %.2f)" % (raw, strength))
    print("periodo exato : %.3f px/tile  (%d tiles na largura de %d px)"
          % (exact, n, img.width))
    print("escala vs 32px: %.2fx" % (exact / CELL))
    print("offset da grade: x=%d y=%d" % (ox, oy))
    os.makedirs(OUT_DIR, exist_ok=True)

    vis = img.copy()
    d = ImageDraw.Draw(vis)
    cells = grid_of(img, exact, ox, oy)
    x = ox
    while x <= img.width:
        d.line([(x, 0), (x, img.height)], fill=(255, 0, 255)); x += exact
    y = oy
    while y <= img.height:
        d.line([(0, y), (img.width, y)], fill=(255, 0, 255)); y += exact
    for c, r, cx, cy in cells:
        d.text((cx + 3, cy + 2), "%d,%d" % (c, r), fill=(255, 255, 0))
    d.rectangle([0, 0, img.width - 1, UI_TOP], outline=(0, 255, 255), width=2)
    d.rectangle(list(FPS_BOX), outline=(0, 255, 255), width=2)
    vis.save(os.path.join(OUT_DIR, "_grid.png"))
    vis.crop((0, 0, 960, 620)).save(os.path.join(OUT_DIR, "_grid_zoom.png"))
    cfg = {"image": os.path.relpath(args.image, ROOT), "period": exact,
           "offset": [ox, oy], "tiles_x": n, "scale_vs_32": exact / CELL}
    with open(os.path.join(OUT_DIR, "_grid.json"), "w") as fh:
        json.dump(cfg, fh, indent=1)
    print("grade em", os.path.join(OUT_DIR, "_grid.png"))
    return cfg


def read_grid():
    with open(os.path.join(OUT_DIR, "_grid.json")) as fh:
        return json.load(fh)


# ------------------------------------------------------------------- 2. chao
# Classes de chao procuradas. (nome, teste sobre a cor media RGB)
# Classes de chao procuradas, sobre a cor media RGB da celula.
# A copa das arvores tambem e verde, mas MUITO mais saturada (r < 45): exigir
# r acima disso separa o chao de grama da folhagem por cima dele.
CLASSES = {
    "grass_light": lambda r, g, b: r > 62 and g >= 126 and g > r + 28 and b < 48,
    "grass_dark":  lambda r, g, b: r > 46 and 104 <= g < 126 and g > r + 28 and b < 48,
    "dirt":        lambda r, g, b: r > g + 18 and r > 150 and b < g,
}


def cell_stats(patch):
    a = arr(patch)
    return a.reshape(-1, 3).mean(axis=0), float(a.reshape(-1, 3).std(axis=0).mean())


def purity(patch, ref, radius):
    """Fracao de pixels dentro de uma bola de cor em volta de `ref`.

    E o filtro que joga fora as celulas com copa de arvore, sombra, arbusto ou
    criatura por cima do chao: a media e o desvio da celula ainda podem parecer
    normais, mas um pedaco grande dela esta longe da cor da classe."""
    a = arr(patch).reshape(-1, 3)
    return float((np.abs(a - ref).max(axis=1) <= radius).mean())


def seam_error(img):
    """Quao bem o tile casa consigo mesmo lado a lado (menor = melhor)."""
    a = arr(img)
    h = np.abs(a[:, -1] - a[:, 0]).mean()
    v = np.abs(a[-1, :] - a[0, :]).mean()
    # tambem compara com a media das colunas/linhas vizinhas, para punir tiles
    # que tenham uma faixa artificial na borda
    return float((h + v) / 2)


def cmd_ground(args):
    cfg = read_grid()
    img = load(os.path.join(ROOT, cfg["image"]))
    period, (ox, oy) = cfg["period"], cfg["offset"]
    cells = grid_of(img, period, ox, oy)
    if args.substeps > 1:
        # O chao repete com o periodo do tile, entao QUALQUER janela de um
        # periodo tirada de uma area homogenea ja e um tile valido e tileable.
        # Amostrar tambem em fracoes de tile multiplica os candidatos, o que
        # deixa o filtro de pureza escolher variantes realmente limpas em vez de
        # aceitar celulas com uma folha escura da copa vizinha.
        step = period / args.substeps
        extra = []
        for c, r, x, y in cells:
            for k in range(args.substeps):
                for l in range(args.substeps):
                    if k == 0 and l == 0:
                        continue
                    nx, ny = x + k * step, y + l * step
                    if (nx + period <= img.width and ny + period <= img.height
                            and not in_ui(int(nx), int(ny), int(period), int(period))):
                        extra.append((c, r, nx, ny))
        cells = cells + extra

    buckets = {k: [] for k in CLASSES}
    for c, r, x, y in cells:
        patch = crop(img, x, y, period)
        mean, std = cell_stats(patch)
        rr, gg, bb = mean
        for name, test in CLASSES.items():
            if test(rr, gg, bb):
                buckets[name].append({"col": c, "row": r, "x": x, "y": y,
                                      "mean": mean, "std": std, "patch": patch})
                break

    os.makedirs(OUT_DIR, exist_ok=True)
    result = {}
    for name, items in buckets.items():
        if not items:
            print("%-12s nenhuma celula" % name)
            continue
        med = np.median(np.stack([i["mean"] for i in items]), axis=0)
        med_std = float(np.median([i["std"] for i in items]))
        # celula "limpa": cor perto da mediana da classe E textura sem o
        # contraste de uma copa/sombra por cima
        for i in items:
            i["pure"] = purity(i["patch"], med, args.radius)
        clean = [i for i in items
                 if np.abs(i["mean"] - med).max() <= args.tol
                 and i["std"] <= med_std * args.std_tol
                 and i["pure"] >= args.purity]
        clean.sort(key=lambda i: (np.abs(i["mean"] - med).max() / args.tol
                                  + i["std"] / max(med_std, 1e-3)
                                  + 4.0 * (1.0 - i["pure"])))
        out_dir = os.path.join(OUT_DIR, name)
        os.makedirs(out_dir, exist_ok=True)
        for f in os.listdir(out_dir):
            os.remove(os.path.join(out_dir, f))
        seen, kept = set(), []
        for i in clean:
            t = to32(img, sharp=args.sharp, colors=args.colors,
                     box=(i["x"], i["y"], i["x"] + period, i["y"] + period))
            h = phash(t)
            if h in seen:
                continue
            seen.add(h)
            kept.append((seam_error(t), t, i))
            if len(kept) >= args.variants * 4:
                break
        kept.sort(key=lambda k: k[0])
        kept = kept[:args.variants]
        names = []
        for n, (se, t, i) in enumerate(kept):
            fn = "%s_%02d.png" % (name, n)
            t.save(os.path.join(out_dir, fn))
            names.append(fn)
            print("  %-18s celula %2d,%-2d  cor %s  pureza %.2f  seam %.1f"
                  % (fn, i["col"], i["row"],
                     tuple(int(v) for v in i["mean"]), i["pure"], se))
        print("%-12s %3d celulas -> %3d limpas -> %d variantes"
              % (name, len(items), len(clean), len(names)))
        result[name] = names
    with open(os.path.join(OUT_DIR, "_ground.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    return result


# ---------------------------------------------------------------- 3. objetos
def ground_models(img, period, ox, oy):
    """Cor mediana de cada classe de chao da imagem, para servir de fundo."""
    meds = {}
    for c, r, x, y in grid_of(img, period, ox, oy):
        m, _ = cell_stats(crop(img, x, y, period))
        for name, test in CLASSES.items():
            if test(*m):
                meds.setdefault(name, []).append(m)
                break
    # grass_dark quase sempre e copa de arvore neste material, nao chao: usar
    # essa mediana como fundo apagaria a folhagem que queremos recortar.
    return {k: np.median(np.stack(v), axis=0) for k, v in meds.items()
            if v and k != "grass_dark"}


def foreground_mask(img, meds, tol=52):
    """Pixels que NAO sao chao: distancia de cor a todos os modelos de chao."""
    a = arr(img)
    d = np.full(a.shape[:2], 1e9, dtype=np.float32)
    for m in meds.values():
        d = np.minimum(d, np.abs(a - m).max(axis=2))
    m = d > tol
    m[:UI_TOP] = False
    fx0, fy0, fx1, fy1 = FPS_BOX
    m[fy0:fy1, fx0:fx1] = False
    return m


def label(mask):
    """Rotulagem de componentes conexas 4-vizinhos (union-find, sem scipy)."""
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    parent = [0]
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)
    for y in range(h):
        row = mask[y]
        for x in np.flatnonzero(row):
            up = lab[y - 1, x] if y else 0
            lf = lab[y, x - 1] if x else 0
            if up and lf:
                lab[y, x] = min(up, lf); union(up, lf)
            elif up or lf:
                lab[y, x] = up or lf
            else:
                parent.append(len(parent)); lab[y, x] = len(parent) - 1
    flat = np.array([find(i) for i in range(len(parent))], dtype=np.int32)
    return flat[lab]


# (nome, lado em tiles, preenchimento minimo, maximo) do miolo da caixa.
OBJECT_KINDS = [
    ("tree", 2, 0.38, 0.97),
    ("bush", 1, 0.28, 0.97),
]


def is_scenery(patch):
    """Descarta recortes que peguem a cobra vermelha (boss) ou o jogador."""
    a = arr(patch).reshape(-1, 3)
    red = ((a[:, 0] > a[:, 1] + 40) & (a[:, 0] > 90) & (a[:, 2] < a[:, 0] - 30)).mean()
    blue = ((a[:, 2] > a[:, 0] + 25) & (a[:, 2] > 80)).mean()
    return red < 0.02 and blue < 0.06


def ring_color(img, x, y, side, period):
    """Cor mediana do anel em volta da caixa: fundo LOCAL. Serve para os
    objetos que ficam sobre a copa da floresta, e nao sobre grama."""
    a = arr(img)
    m = int(round(period * 0.35))
    x0, y0 = max(0, int(x) - m), max(UI_TOP, int(y) - m)
    x1, y1 = min(img.width, int(x + side) + m), min(img.height, int(y + side) + m)
    parts = [a[y0:y1, x0:int(x)], a[y0:y1, int(x + side):x1],
             a[y0:int(y), x0:x1], a[int(y + side):y1, x0:x1]]
    px = np.concatenate([p.reshape(-1, 3) for p in parts if p.size])
    return np.median(px, axis=0)


def cut_object(img, x, y, tiles, period, meds, thresh=48, anchor="bottom",
               extra_bg=None):
    """Recorta tiles x tiles a partir de (x,y) e transforma o chao em alpha.

    Nao da para usar so a distancia de cor: o brilho das folhas tem quase a
    mesma cor da grama, e um alpha por pixel esburaca a copa inteira. Entao a
    mascara e fechada morfologicamente e o que vira transparente e apenas o
    fundo CONECTADO a borda do recorte — buraco interno continua opaco."""
    s = int(np.ceil(period * tiles)) + 1
    ix, iy = int(np.floor(x)), int(np.floor(y))
    box = img.crop((ix, iy, ix + s, iy + s))
    a = arr(box)
    d = np.full(a.shape[:2], 1e9, dtype=np.float32)
    for m in list(meds.values()) + list(extra_bg or []):
        d = np.minimum(d, np.abs(a - m).max(axis=2))
    m = Image.fromarray(((d > thresh) * 255).astype(np.uint8))
    k = max(3, int(period * 0.06) | 1)
    m = m.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))
    fgm = np.asarray(m) > 127
    lab = label(~fgm)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    border.discard(0)
    bg = np.isin(lab, list(border))
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    alpha = np.asarray(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1.2)))
    rgba = np.dstack([a.astype(np.uint8), alpha])
    out = Image.fromarray(rgba).convert("RGBA")
    fx, fy = x - ix, y - iy
    small = out.resize((CELL * tiles, CELL * tiles), Image.LANCZOS,
                       box=(fx, fy, fx + period * tiles, fy + period * tiles))
    if tiles > 1:
        # A copa e um recorte de uma massa continua de folhagem: nas bordas da
        # caixa o corte sai reto e o sprite fica com cara de quadrado. Roer a
        # borda com um ruido deterministico devolve uma silhueta de folha (o
        # .spr 1098 e alpha de 1 bit, entao suavizar nao adiantaria).
        px = np.array(small)
        rng = np.random.default_rng(1098)
        w = 3
        noise = rng.random(px.shape[:2])
        ring = np.zeros(px.shape[:2], dtype=bool)
        ring[:w, :] = ring[-w:, :] = ring[:, :w] = ring[:, -w:] = True
        px[..., 3] = np.where(ring & (noise < 0.55), 0, px[..., 3])
        small = Image.fromarray(px)

    if anchor == "bottom":
        bbox = small.getbbox()
        if bbox:
            cut = small.crop(bbox)
            out2 = Image.new("RGBA", small.size, (0, 0, 0, 0))
            out2.paste(cut, ((small.width - cut.width) // 2,
                             small.height - cut.height))
            small = out2
    return small


PICKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "screenshot_objects.json")


def cmd_objects(args):
    cfg = read_grid()
    img = load(os.path.join(ROOT, cfg["image"]))
    period, (ox, oy) = cfg["period"], cfg["offset"]
    meds = ground_models(img, period, ox, oy)
    print("modelos de chao:", {k: tuple(int(v) for v in m) for k, m in meds.items()})
    fg = foreground_mask(img, meds, args.tol)

    # Varredura de caixas alinhadas a grade (e meio tile). Um objeto isolado tem
    # o miolo cheio de "nao-chao" e o anel em volta cheio de chao — e isso que
    # separa uma arvore solta da mancha continua de copas do fundo da floresta.
    ii = np.cumsum(np.cumsum(fg.astype(np.float64), axis=0), axis=1)

    def frac(x0, y0, x1, y1):
        x0 = max(0, min(fg.shape[1] - 1, int(x0))); x1 = max(0, min(fg.shape[1] - 1, int(x1)))
        y0 = max(0, min(fg.shape[0] - 1, int(y0))); y1 = max(0, min(fg.shape[0] - 1, int(y1)))
        if x1 <= x0 or y1 <= y0:
            return 0.0
        tot = ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]
        return float(tot / ((x1 - x0) * (y1 - y0)))

    out_dir = os.path.join(OUT_DIR, "objects")
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        os.remove(os.path.join(out_dir, f))

    made = {}
    taken = []

    # --- recortes escolhidos a mao (tools/spr/screenshot_objects.json).
    # A floresta do material e densa: quase nenhuma copa fica isolada dentro de
    # um tile, entao a varredura automatica sozinha nao acha 5 arvores boas.
    if os.path.exists(PICKS_FILE) and not args.auto_only:
        with open(PICKS_FILE) as fh:
            picks = json.load(fh)["objects"]
        for p in picks:
            t = p.get("tiles", 2)
            x = ox + p["col"] * period + p.get("dx", 0)
            y = oy + p["row"] * period + p.get("dy", 0)
            extra = ([ring_color(img, x, y, period * t, period)]
                     if p.get("bg") == "local" else None)
            obj = cut_object(img, x, y, t, period, meds, thresh=args.thresh,
                             extra_bg=extra)
            fn = "%s.png" % p["name"]
            obj.save(os.path.join(out_dir, fn))
            made.setdefault(t, []).append(fn)
            taken.append((x, y, period * t))
            al = np.asarray(obj)[:, :, 3]
            print("  %-16s %dx%d em (%4d,%4d)  opaco %.2f  [manual]"
                  % (fn, t, t, x, y, (al > 128).mean()))

    for kind, tiles, amin, amax in OBJECT_KINDS:
        side = period * tiles
        m = period * 0.18                      # anel de fundo em volta da caixa
        cand = []
        y = oy - period
        while y + side <= img.height:
            x = ox - period
            while x + side <= img.width:
                if x >= 0 and y >= UI_TOP:
                    inner = frac(x + m, y + m, x + side - m, y + side - m)
                    outer = (frac(x - m, y - m, x + side + m, y + side + m)
                             * (side + 2 * m) ** 2 - frac(x, y, x + side, y + side)
                             * side ** 2) / max((side + 2 * m) ** 2 - side ** 2, 1)
                    if amin <= inner <= amax and outer < args.ring:
                        cand.append((inner - 2.0 * outer, x, y, inner, outer))
                x += period / 4.0
            y += period / 4.0
        cand.sort(key=lambda c: -c[0])
        n = 0
        for sc, x, y, inner, outer in cand:
            if n >= args.per_kind:
                break
            if any(abs(x - tx) < ts * 0.7 and abs(y - ty) < ts * 0.7
                   for tx, ty, ts in taken):
                continue
            patch = crop(img, x, y, period, tiles)
            if not is_scenery(patch):
                continue
            obj = cut_object(img, x, y, tiles, period, meds, thresh=args.thresh)
            al = np.asarray(obj)[:, :, 3]
            if (al > 128).mean() < 0.25:
                continue
            taken.append((x, y, side))
            fn = "%s%d_%02d.png" % (kind, tiles, n)
            obj.save(os.path.join(out_dir, fn))
            made.setdefault(tiles, []).append(fn)
            print("  %-14s %dx%d em (%4d,%4d)  miolo %.2f  anel %.2f"
                  % (fn, tiles, tiles, x, y, inner, outer))
            n += 1

    with open(os.path.join(OUT_DIR, "_objects.json"), "w") as fh:
        json.dump({str(k): v for k, v in made.items()}, fh, indent=1)
    return made


# ------------------------------------------------------------------ 4. folha
def cmd_sheet(args):
    """Folha 8x8 com cada variante repetida 2x2 (bordas se tocam) para
    conferir tileabilidade, e uma faixa com os objetos."""
    with open(os.path.join(OUT_DIR, "_ground.json")) as fh:
        ground = json.load(fh)
    rows = []
    for name, files in ground.items():
        for fn in files:
            rows.append((name, os.path.join(OUT_DIR, name, fn)))
    n = 8
    sh = Image.new("RGB", (n * CELL * 2, ((len(rows) + n - 1) // n) * CELL * 2),
                   (24, 24, 28))
    for i, (name, path) in enumerate(rows):
        t = Image.open(path).convert("RGB")
        bx, by = (i % n) * CELL * 2, (i // n) * CELL * 2
        for j in range(2):
            for k in range(2):
                sh.paste(t, (bx + j * CELL, by + k * CELL))
    sh = sh.resize((sh.width * 3, sh.height * 3), Image.NEAREST)
    out = os.path.join(OUT_DIR, "_review_ground.png")
    sh.save(out)
    print("folha de revisao (cada tile repetido 2x2):", out, sh.size)

    obj_dir = os.path.join(OUT_DIR, "objects")
    if os.path.isdir(obj_dir):
        files = sorted(os.listdir(obj_dir))
        cw = CELL * 3
        sh2 = Image.new("RGBA", (min(8, len(files)) * cw,
                                 ((len(files) + 7) // 8) * cw), (40, 90, 40, 255))
        for i, fn in enumerate(files):
            im = Image.open(os.path.join(obj_dir, fn)).convert("RGBA")
            sh2.alpha_composite(im, ((i % 8) * cw, (i // 8) * cw))
        sh2 = sh2.resize((sh2.width * 2, sh2.height * 2), Image.NEAREST)
        out2 = os.path.join(OUT_DIR, "_review_objects.png")
        sh2.save(out2)
        print("folha de objetos:", out2, sh2.size)


# -------------------------------------------------------------------- cli
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("grid")
    g.add_argument("--image", default=DEFAULT_IMG)
    g.set_defaults(fn=cmd_grid)

    o = sub.add_parser("ground")
    o.add_argument("--variants", type=int, default=8)
    o.add_argument("--tol", type=float, default=22.0,
                   help="distancia maxima da cor media a mediana da classe")
    o.add_argument("--std-tol", type=float, default=1.25,
                   help="desvio maximo em multiplos do desvio mediano da classe")
    o.add_argument("--radius", type=float, default=62.0,
                   help="raio da bola de cor da classe, para medir pureza")
    o.add_argument("--purity", type=float, default=0.985,
                   help="fracao minima de pixels dentro da bola de cor")
    o.add_argument("--substeps", type=int, default=3,
                   help="amostras por tile em cada eixo (1 = so a grade)")
    o.add_argument("--sharp", type=float, default=1.0)
    o.add_argument("--colors", type=int, default=24)
    o.set_defaults(fn=cmd_ground)

    b = sub.add_parser("objects")
    b.add_argument("--tol", type=float, default=52.0,
                   help="distancia de cor minima para o pixel nao ser chao")
    b.add_argument("--thresh", type=float, default=48.0,
                   help="limiar do alpha ao recortar o objeto")
    b.add_argument("--per-kind", type=int, default=4)
    b.add_argument("--auto-only", action="store_true",
                   help="ignora screenshot_objects.json")
    b.add_argument("--ring", type=float, default=0.30,
                   help="fracao maxima de nao-chao no anel em volta da caixa")
    b.set_defaults(fn=cmd_objects)

    s = sub.add_parser("sheet")
    s.set_defaults(fn=cmd_sheet)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
