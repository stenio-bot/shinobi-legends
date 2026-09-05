#!/usr/bin/env python3
"""Comparativo de nitidez: 4 variantes do downscale 60px->32px, lado a lado,
ampliado 4x. Ferramenta de decisao (mission item 4) — roda sobre alguns quadros
de personagens ja recortados e grava uma folha em /tmp para inspecao visual.
Nao faz parte do pipeline de build; e so o laboratorio que decidiu o que
`imports.fit_uniform` (+ char_synth) aplicam por padrao.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw
import imports as I
import char_synth as C

SAMPLES = [
    ("900 Naruto Kid", "assets-src/import/extracted/mugen/900/idle_0004.png"),
    ("906 Kakashi", "assets-src/import/extracted/mugen/906/idle_0004.png"),
    ("913 Madara", "assets-src/import/extracted/mugen/913/idle_0005.png"),
    ("917 Sakura", "assets-src/import/extracted/mugen/917/idle_0005.png"),
]

BOX = 32
ZOOM = 4


def variant_a(img, scale):
    """(a) baseline atual: crop bbox + LANCZOS direto (fit_uniform de hoje)."""
    return I.fit_uniform(img, BOX, scale)


def variant_b(img, scale):
    """(b) downscale por AREA (Image.BOX, media dos pixels) + realce."""
    im = I._trim(img.convert("RGBA"))
    w, h = max(1, round(im.width * scale)), max(1, round(im.height * scale))
    im = im.resize((w, h), Image.BOX)
    im = C.unsharp(im, amount=0.8)
    im = I._binarize(im.convert("RGBA"))
    im = I._trim(im)
    out = Image.new("RGBA", (BOX, BOX), (0, 0, 0, 0))
    x = int(round(BOX / 2.0 - I._foot_center(im)))
    x = max(min(x, BOX - im.width), min(0, BOX - im.width))
    out.paste(im, (x, BOX - im.height))
    return out


def variant_c(img, scale, palette):
    """(c) LANCZOS + quantizacao a paleta original (sem tons intermediarios)."""
    base = I.fit_uniform(img, BOX, scale)
    return C.quantize_to_palette(base, palette)


def variant_d(img, scale, palette):
    """(d) = (c) + contorno escuro de 1px redesenhado apos a reducao."""
    base = variant_c(img, scale, palette)
    return C.outline_1px(base)


def variant_e(img, scale):
    """(e) = (b) area+realce + contorno 1px, SEM quantizar a paleta (c/d
    pioraram: nearest-color por pixel cria ruido de sal-e-pimenta nas bordas
    ja suavizadas pelo LANCZOS/area — ver folha de comparacao)."""
    base = variant_b(img, scale)
    return C.outline_1px(base)


def main():
    rows = []
    for label, rel in SAMPLES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print("faltando", path)
            continue
        img = Image.open(path)
        scale = min(BOX / img.width, BOX / img.height, 1.0)
        palette = C.extract_palette([img], k=16)
        variants = [
            ("a) lanczos direto", variant_a(img, scale)),
            ("b) area + realce", variant_b(img, scale)),
            ("c) lanczos + paleta", variant_c(img, scale, palette)),
            ("d) c + contorno 1px", variant_d(img, scale, palette)),
            ("e) b + contorno 1px", variant_e(img, scale)),
        ]
        rows.append((label, variants))

    pad = 6
    cell = BOX * ZOOM
    W = pad + 110 + len(rows[0][1]) * (cell + pad)
    H = pad + 16 + len(rows) * (cell + 20 + pad)
    sheet = Image.new("RGBA", (W, H), (24, 24, 30, 255))
    d = ImageDraw.Draw(sheet)
    for c, (label, _) in enumerate(rows[0][1]):
        d.text((pad + 110 + c * (cell + pad), 4), label, fill=(255, 230, 120, 255))
    for r, (label, variants) in enumerate(rows):
        y = pad + 16 + r * (cell + 20 + pad)
        d.text((pad, y + cell // 2), label, fill=(200, 220, 255, 255))
        for c, (_, im) in enumerate(variants):
            x = pad + 110 + c * (cell + pad)
            bg = Image.new("RGBA", (BOX, BOX), (70, 70, 78, 255))
            bg.alpha_composite(im)
            sheet.paste(bg.resize((cell, cell), Image.NEAREST), (x, y))
    out = "/tmp/compare_sharpen.png"
    sheet.save(out)
    print("gravado", out)


if __name__ == "__main__":
    main()
