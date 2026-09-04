#!/usr/bin/env python3
"""Extrator generico de folhas de sprites soltas (sem grade).

Recebe um PNG com varios sprites espalhados sobre uma cor de fundo chapada,
separa cada sprite por componentes conexos e grava um PNG com alpha por sprite
em assets-src/import/extracted/<folha>/<idx>.png, mais uma folha de revisao
numerada <folha>_contact.png para conferir a segmentacao a olho.

Uso:
    .venv/bin/python tools/spr/import_sheets.py                  # as folhas padrao
    .venv/bin/python tools/spr/import_sheets.py caminho.png --dilate 2

O material de origem (assets-src/import/) e privado do usuario e esta no
.gitignore: nada dele e versionado. Ver docs/sistemas/arte-e-sprites.md.
"""
import argparse
import json
import os
import sys
from collections import Counter, deque

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
IMPORT_DIR = os.path.join(ROOT, "assets-src", "import")
OUT_DIR = os.path.join(IMPORT_DIR, "extracted")

# (arquivo, raio de dilatacao): o npcs_sheet tem sprites quase encostados, so
# fecha certo com dilate=0; o monsters_sheet tem sprites com partes soltas
# (caudas, chamas) e precisa de 1.
DEFAULT_SHEETS = [("monsters_sheet.png", 1), ("npcs_sheet.png", 0)]
# fundos extras tratados como transparentes onde aparecerem (o retangulo verde
# do canto do monsters_sheet e um "chroma key" secundario da folha original)
EXTRA_BG = [(34, 177, 76)]


def detect_bg(rgb):
    return Counter(rgb.getdata()).most_common(1)[0][0]


def build_mask(img, bgs, tol):
    """Mascara 'L' (255 = sprite) a partir da imagem RGBA."""
    w, h = img.size
    px = img.load()
    mask = Image.new("L", (w, h), 0)
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            for br, bg_, bb in bgs:
                if abs(r - br) <= tol and abs(g - bg_) <= tol and abs(b - bb) <= tol:
                    break
            else:
                mp[x, y] = 255
    return mask


def label_components(dil, min_px):
    """Rotula os componentes conexos (8-vizinhos) da mascara dilatada.
    Devolve (labels, n): labels[y][x] = 0 (fundo) ou id do componente."""
    w, h = dil.size
    d = dil.load()
    labels = [[0] * w for _ in range(h)]
    n = 0
    comps = []
    for sy in range(h):
        row = labels[sy]
        for sx in range(w):
            if not d[sx, sy] or row[sx]:
                continue
            n += 1
            q = deque([(sx, sy)])
            row[sx] = n
            cells = 0
            while q:
                x, y = q.popleft()
                cells += 1
                for dy in (-1, 0, 1):
                    ny = y + dy
                    if ny < 0 or ny >= h:
                        continue
                    lrow = labels[ny]
                    for dx in (-1, 0, 1):
                        nx = x + dx
                        if nx < 0 or nx >= w or lrow[nx] or not d[nx, ny]:
                            continue
                        lrow[nx] = n
                        q.append((nx, ny))
            comps.append(cells)
    return labels, n, comps


def extract(path, dilate, tol, min_area, min_side, out_root, bg=None):
    name = os.path.splitext(os.path.basename(path))[0]
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    rgb = img.convert("RGB")
    bgs = [bg or detect_bg(rgb)] + EXTRA_BG
    mask = build_mask(img, bgs, tol)
    dil = mask.filter(ImageFilter.MaxFilter(2 * dilate + 1)) if dilate else mask

    labels, n, _ = label_components(dil, min_area)

    mp = mask.load()
    boxes = {}
    areas = Counter()
    for y in range(h):
        lrow = labels[y]
        for x in range(w):
            lab = lrow[x]
            if not lab or not mp[x, y]:
                continue
            areas[lab] += 1
            b = boxes.get(lab)
            if b is None:
                boxes[lab] = [x, y, x + 1, y + 1]
            else:
                if x < b[0]:
                    b[0] = x
                if y < b[1]:
                    b[1] = y
                if x + 1 > b[2]:
                    b[2] = x + 1
                if y + 1 > b[3]:
                    b[3] = y + 1

    keep = []
    for lab, box in boxes.items():
        bw, bh = box[2] - box[0], box[3] - box[1]
        if areas[lab] < min_area or bw < min_side or bh < min_side:
            continue
        keep.append((lab, box))
    # ordem de leitura: faixas horizontais, depois x
    keep.sort(key=lambda kb: (kb[1][1] // 24, kb[1][0]))

    out_dir = os.path.join(out_root, name)
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.endswith(".png"):
            os.remove(os.path.join(out_dir, old))

    src = img.load()
    entries = []
    for idx, (lab, box) in enumerate(keep):
        x0, y0, x1, y1 = box
        cut = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        cp = cut.load()
        for y in range(y0, y1):
            lrow = labels[y]
            for x in range(x0, x1):
                if lrow[x] == lab and mp[x, y]:
                    r, g, b, _ = src[x, y]
                    cp[x - x0, y - y0] = (r, g, b, 255)
        rel = "%d.png" % idx
        cut.save(os.path.join(out_dir, rel))
        entries.append({"index": idx, "file": "%s/%s" % (name, rel),
                        "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0,
                        "pixels": areas[lab]})

    contact(entries, out_dir, os.path.join(out_root, "%s_contact.png" % name))
    with open(os.path.join(out_root, "%s.json" % name), "w", encoding="utf-8") as fh:
        json.dump({"sheet": os.path.relpath(path, ROOT), "size": [w, h],
                   "background": list(bgs[0]), "dilate": dilate,
                   "sprites": entries}, fh, indent=1)
    print("%s: %d sprites (fundo %s, dilate %d)" % (name, len(entries), bgs[0], dilate))
    return entries


def contact(entries, sprite_dir, out_path, cols=None):
    if not entries:
        return
    cw = max(e["w"] for e in entries) + 8
    ch = max(e["h"] for e in entries) + 20
    cw = max(cw, 56)
    cols = cols or max(1, min(12, int(1200 // cw)))
    rows = (len(entries) + cols - 1) // cols
    sh = Image.new("RGBA", (cols * cw, rows * ch), (24, 24, 28, 255))
    dr = ImageDraw.Draw(sh)
    for i, e in enumerate(entries):
        cx = (i % cols) * cw
        cy = (i // cols) * ch
        dr.rectangle([cx, cy, cx + cw - 1, cy + ch - 1], outline=(70, 70, 80, 255))
        spr = Image.open(os.path.join(sprite_dir, os.path.basename(e["file"])))
        sh.alpha_composite(spr, (cx + (cw - e["w"]) // 2, cy + 14 + (ch - 20 - e["h"]) // 2))
        dr.text((cx + 3, cy + 2), "%d %dx%d" % (e["index"], e["w"], e["h"]),
                fill=(255, 230, 120, 255))
    sh.save(out_path)
    print("   folha de revisao -> %s" % os.path.relpath(out_path, ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheets", nargs="*", default=None)
    ap.add_argument("--dilate", type=int, default=None,
                    help="raio de dilatacao (0..3); padrao: por folha em DEFAULT_SHEETS")
    ap.add_argument("--tol", type=int, default=12, help="tolerancia por canal do fundo")
    ap.add_argument("--min-area", type=int, default=24)
    ap.add_argument("--min-side", type=int, default=4)
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args()

    if args.sheets:
        sheets = [(s, args.dilate if args.dilate is not None else 1) for s in args.sheets]
    else:
        sheets = [(os.path.join(IMPORT_DIR, s), args.dilate if args.dilate is not None else d)
                  for s, d in DEFAULT_SHEETS]
    out_root = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    os.makedirs(out_root, exist_ok=True)
    for s, d in sheets:
        p = s if os.path.isabs(s) else os.path.join(ROOT, s)
        if not os.path.exists(p):
            print("AVISO: nao existe: %s" % p, file=sys.stderr)
            continue
        extract(p, d, args.tol, args.min_area, args.min_side, out_root)


if __name__ == "__main__":
    main()
