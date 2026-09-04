#!/usr/bin/env python3
"""Desenha os PNGs do cenario proprio (tiles) em assets-src/sprites/tiles/.

    .venv/bin/python tools/spr/gen_tiles.py

Tudo e arte original gerada por codigo (Pillow) — nenhum pixel vem da Tibia ou
de NTO (ADR-002). O manifesto que declara esses tiles como itens NOVOS do TFS e
`assets-src/sprites/tiles.json`, mantido a mao; este script so (re)desenha os
PNGs que ele referencia.

Convencao: celula 32x32 RGBA, alpha binario, "chao" na linha y=31.
Um PNG por FASE de animacao; cada PNG tem width*32 x height*32 pixels.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw  # noqa: E402

from art import _c, _Rnd, outline_inner  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "assets-src", "sprites", "tiles")
CELL = 32


def img(w_tiles=1, h_tiles=1):
    return Image.new("RGBA", (w_tiles * CELL, h_tiles * CELL), (0, 0, 0, 0))


def shade(c, k):
    return (_c(c[0] + k), _c(c[1] + k), _c(c[2] + k), 255)


# --------------------------------------------------------------------- chaos
def tatami():
    """Tatame: esteira de palha com bordas de tecido escuro."""
    base = (196, 184, 126)
    im = img()
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 31, 31], fill=base + (255,))
    rnd = _Rnd(4211)
    # trama: metade superior com fibras horizontais, inferior com verticais
    for y in range(2, 30):
        for x in range(2, 30):
            if y < 16:
                k = 8 if (x + y // 2) % 3 == 0 else -6
            else:
                k = 8 if (y + x // 2) % 3 == 0 else -6
            k += rnd.next(5) - 2
            im.putpixel((x, y), shade(base, k))
    # bordao de tecido (heri) nas quatro bordas
    hem = (58, 74, 62)
    d.rectangle([0, 0, 31, 1], fill=hem + (255,))
    d.rectangle([0, 30, 31, 31], fill=hem + (255,))
    d.rectangle([0, 0, 1, 31], fill=hem + (255,))
    d.rectangle([30, 0, 31, 31], fill=hem + (255,))
    for i in range(0, 32, 4):
        im.putpixel((i, 0), shade(hem, 26))
        im.putpixel((i + 1, 31), shade(hem, 26))
    # divisa entre as duas metades da trama
    d.line([2, 15, 29, 15], fill=shade(base, -30))
    return im


def village_dirt():
    """Terra batida de vila: caminho pisado, com pedrinhas e marcas de passo."""
    base = (146, 118, 88)
    im = img()
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 31, 31], fill=base + (255,))
    rnd = _Rnd(9173)
    for _ in range(220):
        x, y = rnd.next(32), rnd.next(32)
        im.putpixel((x, y), shade(base, rnd.next(21) - 10))
    # sulcos claros (terra compactada)
    for _ in range(6):
        y = 3 + rnd.next(26)
        x0 = rnd.next(20)
        d.line([x0, y, min(31, x0 + 6 + rnd.next(8)), y], fill=shade(base, 16))
    # pedrinhas
    for _ in range(9):
        x, y = 1 + rnd.next(29), 1 + rnd.next(29)
        c = shade((122, 118, 112), rnd.next(20) - 10)
        im.putpixel((x, y), c)
        if rnd.next(2):
            im.putpixel((min(31, x + 1), y), shade(c, -18))
    # borda para o grid ficar legivel
    for i in range(32):
        im.putpixel((i, 31), shade(base, -26))
        im.putpixel((31, i), shade(base, -26))
    return im


# --------------------------------------------------------------------- paredes
def _wood_planks(im, d, vertical, base=(126, 92, 58)):
    d.rectangle([0, 0, 31, 31], fill=base + (255,))
    rnd = _Rnd(551 if vertical else 907)
    step = 8
    for i in range(0, 32, step):
        if vertical:
            d.line([i, 0, i, 31], fill=shade(base, -38))
            d.line([i + 1, 0, i + 1, 31], fill=shade(base, 18))
        else:
            d.line([0, i, 31, i], fill=shade(base, -38))
            d.line([0, i + 1, 31, i + 1], fill=shade(base, 18))
    # veios
    for _ in range(46):
        x, y = rnd.next(32), rnd.next(32)
        im.putpixel((x, y), shade(base, rnd.next(17) - 8))
    return im


def wood_wall(vertical):
    """Parede de madeira da casa: variacao vertical (norte-sul) e horizontal."""
    im = img()
    d = ImageDraw.Draw(im)
    _wood_planks(im, d, vertical)
    beam = (92, 66, 40)
    if vertical:
        # montantes nas pontas
        d.rectangle([0, 0, 3, 31], fill=beam + (255,))
        d.rectangle([28, 0, 31, 31], fill=beam + (255,))
    else:
        d.rectangle([0, 0, 31, 3], fill=beam + (255,))
        d.rectangle([0, 28, 31, 31], fill=beam + (255,))
    d.rectangle([0, 0, 31, 31], outline=(48, 34, 22, 255))
    return im


# ------------------------------------------------------------------ torii 2x1
def torii():
    """Portao torii vermelho, 2 tiles de largura por 1 de altura (64x32)."""
    im = img(2, 1)
    d = ImageDraw.Draw(im)
    red = (176, 52, 44)
    dark = (118, 30, 28)
    lite = (214, 92, 78)
    black = (38, 26, 24, 255)

    # pilares
    for px in (6, 52):
        d.rectangle([px, 8, px + 5, 31], fill=red + (255,))
        d.line([px, 8, px, 31], fill=lite + (255,))
        d.line([px + 5, 8, px + 5, 31], fill=dark + (255,))
        # base de pedra
        d.rectangle([px - 1, 28, px + 6, 31], fill=(108, 106, 100, 255))
    # travessa inferior (nuki)
    d.rectangle([4, 13, 59, 16], fill=red + (255,))
    d.line([4, 13, 59, 13], fill=lite + (255,))
    d.line([4, 16, 59, 16], fill=dark + (255,))
    # travessa superior (shimaki)
    d.rectangle([2, 6, 61, 9], fill=red + (255,))
    d.line([2, 6, 61, 6], fill=lite + (255,))
    # kasagi (viga do topo, com as pontas curvadas para cima)
    d.rectangle([0, 2, 63, 5], fill=dark + (255,))
    d.line([0, 2, 63, 2], fill=(150, 44, 38, 255))
    d.rectangle([0, 1, 4, 2], fill=dark + (255,))
    d.rectangle([59, 1, 63, 2], fill=dark + (255,))
    # gakuzuka (pequeno pilar central entre as duas travessas)
    d.rectangle([30, 9, 33, 13], fill=red + (255,))
    # shimenawa: corda de palha pendurada no meio
    d.rectangle([20, 17, 43, 19], fill=(214, 200, 148, 255))
    for x in range(21, 43, 4):
        d.line([x, 20, x, 22], fill=(214, 200, 148, 255))
    outline_inner(im, black)
    return im


# ------------------------------------------------------------------ mobiliario
def wood_sign():
    """Placa de madeira com escrita rabiscada."""
    im = img()
    d = ImageDraw.Draw(im)
    post = (96, 70, 44, 255)
    board = (162, 124, 76)
    d.rectangle([14, 18, 17, 31], fill=post)
    d.rectangle([4, 6, 27, 20], fill=board + (255,))
    d.rectangle([4, 6, 27, 7], fill=shade(board, 26))
    d.rectangle([4, 19, 27, 20], fill=shade(board, -30))
    for y in range(8, 19):
        for x in range(5, 27):
            if (x * 3 + y * 5) % 11 == 0:
                im.putpixel((x, y), shade(board, -14))
    # "texto"
    ink = (48, 40, 36, 255)
    for y, xs in ((10, (7, 12)), (10, (16, 23)), (13, (7, 18)), (16, (9, 20))):
        d.line([xs[0], y, xs[1], y], fill=ink)
    d.line([9, 9, 9, 12], fill=ink)
    d.line([19, 12, 19, 17], fill=ink)
    outline_inner(im, (38, 30, 26, 255))
    return im


def paper_lantern(phase):
    """Lanterna de papel (chochin). 2 fases: a chama oscila."""
    im = img()
    d = ImageDraw.Draw(im)
    warm = (238, 196, 116) if phase == 0 else (246, 214, 140)
    paper = (232, 186, 108) if phase == 0 else (238, 198, 124)
    d.rectangle([13, 1, 18, 3], fill=(72, 56, 44, 255))       # gancho
    d.line([15, 3, 15, 5], fill=(72, 56, 44, 255))
    d.rectangle([11, 5, 20, 7], fill=(70, 52, 40, 255))       # aro de cima
    # corpo bojudo
    for y in range(8, 24):
        t = abs(y - 15.5) / 8.0
        half = int(round(7 - 4 * t * t))
        d.line([15 - half, y, 16 + half, y], fill=paper + (255,))
    for y in range(9, 24, 4):                                  # aros de bambu
        t = abs(y - 15.5) / 8.0
        half = int(round(7 - 4 * t * t))
        d.line([15 - half, y, 16 + half, y], fill=shade(paper, -42))
    d.rectangle([11, 24, 20, 26], fill=(70, 52, 40, 255))     # aro de baixo
    d.rectangle([14, 27, 17, 29], fill=(58, 44, 34, 255))     # borla
    # brilho interno da chama
    cy = 15 if phase == 0 else 14
    d.ellipse([12, cy - 3, 19, cy + 3], fill=warm + (255,))
    d.ellipse([14, cy - 1, 17, cy + 1], fill=(255, 244, 206, 255))
    outline_inner(im, (44, 32, 26, 255))
    return im


def bamboo_fence():
    """Cerca de bambu: colmos verticais amarrados por duas travessas."""
    im = img()
    d = ImageDraw.Draw(im)
    green = (150, 168, 96)
    for x in (2, 9, 16, 23, 29):
        d.rectangle([x, 4, x + 3, 31], fill=green + (255,))
        d.line([x, 4, x, 31], fill=shade(green, 26))
        d.line([x + 3, 4, x + 3, 31], fill=shade(green, -34))
        for y in range(7, 32, 9):                              # nos do bambu
            d.line([x, y, x + 3, y], fill=shade(green, -44))
        d.line([x, 4, x + 3, 4], fill=shade(green, 34))        # ponta cortada
    rail = (128, 142, 78)
    for y in (11, 24):
        d.rectangle([0, y, 31, y + 2], fill=rail + (255,))
        d.line([0, y, 31, y], fill=shade(rail, 22))
    # amarras de corda
    for x in (3, 17):
        for y in (11, 24):
            d.rectangle([x, y - 1, x + 2, y + 3], fill=(196, 172, 116, 255))
    outline_inner(im, (40, 46, 28, 255))
    return im


# ----------------------------------------------------------------------- main
TILES = {
    "tatami_floor.png": tatami,
    "village_dirt.png": village_dirt,
    "wood_wall_v.png": lambda: wood_wall(True),
    "wood_wall_h.png": lambda: wood_wall(False),
    "torii_gate.png": torii,
    "wood_sign.png": wood_sign,
    "paper_lantern_0.png": lambda: paper_lantern(0),
    "paper_lantern_1.png": lambda: paper_lantern(1),
    "bamboo_fence.png": bamboo_fence,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in sorted(TILES.items()):
        im = fn()
        # alpha binario: o .spr de 1098 e RGB
        px = im.load()
        for y in range(im.size[1]):
            for x in range(im.size[0]):
                r, g, b, a = px[x, y]
                px[x, y] = (r, g, b, 255 if a >= 128 else 0)
        im.save(os.path.join(OUT, name))
        print("%-22s %dx%d" % (name, im.size[0], im.size[1]))
    print("%d PNGs em %s" % (len(TILES), OUT))
    print("declare-os em assets-src/sprites/tiles.json e rode build_assets.py")


if __name__ == "__main__":
    main()
