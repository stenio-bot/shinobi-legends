"""Pixel art placeholder desenhada por codigo (Pillow).

Tudo aqui e arte original gerada proceduralmente — nenhum pixel vem da Tibia,
de NTO ou de qualquer outro jogo (ADR-002).

Convencao de celula: 32x32, RGBA, fundo transparente, "chao" na linha y=30.
Criaturas tem duas camadas:
  layer 0 = base (tons claros nas areas colorizaveis, para o MULTIPLY funcionar)
  layer 1 = template de mascara (vermelho=body, verde=legs, azul=feet, amarelo=head)
"""
import math

from PIL import Image, ImageDraw

CELL = 32

TRANSPARENT = (0, 0, 0, 0)
OUTLINE = (26, 22, 30, 255)

# cores exatas que o cliente procura em Image::overwriteMask
MASK_BODY = (255, 0, 0, 255)
MASK_LEGS = (0, 255, 0, 255)
MASK_FEET = (0, 0, 255, 255)
MASK_HEAD = (255, 255, 0, 255)

# base clara nas regioes colorizaveis: MULTIPLY * cor do outfit = a cor do outfit
BASE = {
    "skin": (226, 190, 154, 255),
    "head": (238, 238, 238, 255),   # cabelo/bandana  -> mascara amarela
    "body": (242, 242, 242, 255),   # colete          -> mascara vermelha
    "legs": (232, 232, 232, 255),   # calca           -> mascara verde
    "feet": (222, 222, 222, 255),   # sandalia        -> mascara azul
    "gear": (120, 122, 132, 255),
    "eye": (24, 22, 32, 255),
    "line": OUTLINE,
}

MASK_OF = {"head": MASK_HEAD, "body": MASK_BODY, "legs": MASK_LEGS, "feet": MASK_FEET}


def new_image(w_tiles=1, h_tiles=1):
    return Image.new("RGBA", (w_tiles * CELL, h_tiles * CELL), TRANSPARENT)


def hsv(h, s, v, a=255):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255), a)


def _rect(px, x0, y0, x1, y1, color):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if 0 <= x < px.size[0] and 0 <= y < px.size[1]:
                px.putpixel((x, y), color)


# --------------------------------------------------------------------- itens
def draw_ground(tint, seed=0):
    img = new_image()
    d = ImageDraw.Draw(img)
    r, g, b = tint
    d.rectangle([0, 0, 31, 31], fill=(r, g, b, 255))
    rnd = _Rnd(seed * 7919 + 13)
    for _ in range(70):
        x, y = rnd.next(32), rnd.next(32)
        k = rnd.next(3) - 1
        img.putpixel((x, y), (_c(r + k * 14), _c(g + k * 14), _c(b + k * 14), 255))
    # borda sutil para o grid ficar visivel
    for i in range(32):
        img.putpixel((i, 31), (_c(r - 22), _c(g - 22), _c(b - 22), 255))
        img.putpixel((31, i), (_c(r - 22), _c(g - 22), _c(b - 22), 255))
    return img


def draw_wall(tint=(122, 122, 130)):
    img = new_image()
    d = ImageDraw.Draw(img)
    r, g, b = tint
    d.rectangle([0, 0, 31, 31], fill=(r, g, b, 255))
    d.rectangle([0, 0, 31, 31], outline=(_c(r - 45), _c(g - 45), _c(b - 45), 255))
    for row, y in enumerate((6, 14, 22, 30)):
        d.line([0, y, 31, y], fill=(_c(r - 35), _c(g - 35), _c(b - 35), 255))
        off = 0 if row % 2 == 0 else 8
        for x in range(off, 32, 16):
            d.line([x, y - 7, x, y], fill=(_c(r - 35), _c(g - 35), _c(b - 35), 255))
    d.line([0, 0, 31, 0], fill=(_c(r + 40), _c(g + 40), _c(b + 40), 255))
    return img


def draw_container(tint=(140, 96, 52)):
    img = new_image()
    d = ImageDraw.Draw(img)
    r, g, b = tint
    d.rectangle([5, 10, 26, 28], fill=(r, g, b, 255), outline=OUTLINE)
    d.rectangle([5, 10, 26, 15], fill=(_c(r + 30), _c(g + 30), _c(b + 30), 255), outline=OUTLINE)
    d.rectangle([14, 16, 17, 21], fill=(198, 176, 84, 255), outline=OUTLINE)
    return img


def draw_cube(tint, small=False):
    """Item generico: cubo isometrico simples."""
    img = new_image()
    d = ImageDraw.Draw(img)
    r, g, b = tint
    if small:
        box = (11, 13, 20, 22)
    else:
        box = (8, 10, 23, 25)
    d.rectangle(box, fill=(r, g, b, 255), outline=OUTLINE)
    d.line([box[0] + 1, box[1] + 1, box[2] - 1, box[1] + 1],
           fill=(_c(r + 55), _c(g + 55), _c(b + 55), 255))
    d.line([box[0] + 1, box[3] - 1, box[2] - 1, box[3] - 1],
           fill=(_c(r - 45), _c(g - 45), _c(b - 45), 255))
    return img


def draw_stack(tint):
    img = new_image()
    d = ImageDraw.Draw(img)
    r, g, b = tint
    for i, y in enumerate((22, 18, 14)):
        w = 10 - i * 2
        d.ellipse([16 - w, y, 15 + w, y + 5], fill=(r, g, b, 255), outline=OUTLINE)
    return img


def draw_splash(tint):
    img = new_image()
    d = ImageDraw.Draw(img)
    r, g, b = tint
    d.ellipse([6, 16, 25, 27], fill=(r, g, b, 210), outline=(_c(r - 40), _c(g - 40), _c(b - 40), 255))
    d.ellipse([11, 19, 19, 23], fill=(_c(r + 45), _c(g + 45), _c(b + 45), 220))
    return img


def draw_vial(tint):
    img = new_image()
    d = ImageDraw.Draw(img)
    r, g, b = tint
    d.rectangle([12, 8, 19, 11], fill=(190, 190, 200, 255), outline=OUTLINE)
    d.rectangle([10, 12, 21, 26], fill=(r, g, b, 255), outline=OUTLINE)
    d.line([12, 14, 12, 24], fill=(_c(r + 60), _c(g + 60), _c(b + 60), 255))
    return img


def draw_marker(tint):
    """Decoracao discreta: um losango pequeno, para nao poluir o mapa."""
    img = new_image()
    r, g, b = tint
    for dy in range(-3, 4):
        w = 3 - abs(dy)
        for dx in range(-w, w + 1):
            img.putpixel((16 + dx, 18 + dy), (r, g, b, 255))
    return img


def outline_inner(img, color=OUTLINE):
    """Escurece os pixels opacos que fazem fronteira com o transparente.
    Deixa a silhueta legivel sem alterar o tamanho do sprite."""
    w, h = img.size
    px = img.load()
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= w or ny >= h or px[nx, ny][3] == 0:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = color
    return img


def _c(v):
    return max(0, min(255, int(v)))


class _Rnd:
    """LCG deterministico (nao usa random global, build reprodutivel)."""

    def __init__(self, seed):
        self.s = (seed * 2654435761 + 12345) & 0xFFFFFFFF

    def next(self, n):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s % n


# ---------------------------------------------------------------- criaturas
def _leg_offset(phase, side):
    """Deslocamento vertical/horizontal das pernas por fase de caminhada."""
    if phase == 0:
        return 0
    swing = (0, -1, 0, 1)[phase % 4]
    return swing if side == 0 else -swing


def draw_humanoid(direction, phase, layer, style, palette, big=False):
    """Ninja/bandido 1x1 (ou 2x2 se big). direction: 0=N 1=L 2=S 3=O."""
    tiles = 2 if big else 1
    img = new_image(tiles, tiles)
    scale = 2 if big else 1
    ox = 0
    oy = 0

    def col(region):
        if layer == 1:
            return MASK_OF.get(region, TRANSPARENT)
        if region in palette:
            return palette[region]
        return BASE.get(region, TRANSPARENT)

    def rect(x0, y0, x1, y1, region):
        c = col(region)
        if c[3] == 0:
            return
        _rect(img, ox + x0 * scale, oy + y0 * scale,
              ox + (x1 + 1) * scale - 1, oy + (y1 + 1) * scale - 1, c)

    gear = {"ninja": (214, 116, 44, 255), "bandit": (150, 56, 52, 255),
            "boss": (206, 168, 64, 255)}.get(style, BASE["gear"])
    palette = dict(palette)
    palette.setdefault("gear", gear)

    front = direction == 2
    back = direction == 0
    side = direction in (1, 3)

    # pernas (animadas)
    l0 = _leg_offset(phase, 0)
    l1 = _leg_offset(phase, 1)
    if side:
        rect(13, 22, 16, 27 + l0, "legs")
        rect(15, 22, 18, 27 + l1, "legs")
        rect(13, 28 + l0, 17, 29 + l0, "feet")
        rect(15, 28 + l1, 19, 29 + l1, "feet")
    else:
        rect(11, 22, 14, 27 + l0, "legs")
        rect(17, 22, 20, 27 + l1, "legs")
        rect(11, 28 + l0, 15, 29 + l0, "feet")
        rect(17, 28 + l1, 21, 29 + l1, "feet")

    # tronco / colete
    if side:
        rect(12, 13, 19, 22, "body")
        rect(11, 14, 12, 21, "skin")        # braco
    else:
        rect(10, 13, 21, 22, "body")
        rect(8, 14, 10, 21, "skin")
        rect(21, 14, 23, 21, "skin")

    # cabeca
    if side:
        rect(13, 5, 19, 12, "skin")
        rect(13, 4, 19, 7, "head")          # bandana / cabelo
    else:
        rect(11, 5, 20, 12, "skin")
        rect(11, 4, 20, 7, "head")

    # detalhes por estilo
    if layer == 0:
        if front:
            rect(13, 9, 14, 10, "eye")
            rect(17, 9, 18, 10, "eye")
            if style == "bandit":
                rect(11, 8, 20, 8, "gear")   # faixa no rosto
            if style == "boss":
                rect(11, 3, 20, 3, "gear")
        elif side:
            rect(16 if direction == 1 else 14, 9, 17 if direction == 1 else 15, 10, "eye")
        if style in ("ninja", "boss"):
            # faixa de peito + kunai nas costas
            if side:
                rect(12, 13, 19, 15, "gear")
                rect(20, 10, 21, 18, "gear")
            else:
                rect(10, 13, 21, 15, "gear")
                rect(22, 10, 23, 18, "gear")
        if back:
            rect(11, 4, 20, 9, "head")

    return img


def draw_quadruped(direction, phase, layer, palette, big=False):
    """Lobo / fera de 4 patas."""
    tiles = 2 if big else 1
    img = new_image(tiles, tiles)
    scale = 2 if big else 1

    def col(region):
        if layer == 1:
            return MASK_OF.get(region, TRANSPARENT)
        return palette.get(region, BASE.get(region, TRANSPARENT))

    def rect(x0, y0, x1, y1, region):
        c = col(region)
        if c[3] == 0:
            return
        _rect(img, x0 * scale, y0 * scale, (x1 + 1) * scale - 1, (y1 + 1) * scale - 1, c)

    swing = (0, 1, 0, -1)[phase % 4]
    side = direction in (1, 3)
    if side:
        rect(6, 14, 25, 23, "body")
        rect(21 if direction == 1 else 4, 10, 27 if direction == 1 else 10, 17, "head")
        rect(7, 23, 9, 28 + swing, "feet")
        rect(12, 23, 14, 28 - swing, "feet")
        rect(18, 23, 20, 28 + swing, "feet")
        rect(22, 23, 24, 28 - swing, "feet")
        rect(2 if direction == 1 else 27, 12, 6 if direction == 1 else 30, 15, "legs")  # cauda
        if layer == 0:
            rect(25 if direction == 1 else 5, 12, 26 if direction == 1 else 6, 13, "eye")
    else:
        rect(9, 14, 22, 26, "body")
        rect(11, 7, 20, 15, "head")
        rect(9, 26, 12, 29 + swing, "feet")
        rect(19, 26, 22, 29 - swing, "feet")
        if layer == 0:
            if direction == 2:           # so de frente aparecem os olhos
                rect(12, 10, 13, 11, "eye")
                rect(18, 10, 19, 11, "eye")
            rect(10, 5, 12, 7, "legs")   # orelhas
            rect(19, 5, 21, 7, "legs")
    return img


def draw_serpent(direction, phase, layer, palette):
    img = new_image()

    def col(region):
        if layer == 1:
            return MASK_OF.get(region, TRANSPARENT)
        return palette.get(region, BASE.get(region, TRANSPARENT))

    def put(x, y, region):
        c = col(region)
        if c[3] and 0 <= x < 32 and 0 <= y < 32:
            img.putpixel((x, y), c)

    off = phase * 2
    for i in range(26):
        x = 3 + i
        y = int(20 + 5 * math.sin((i + off) * 0.55))
        for t in range(-3, 4):
            put(x, y + t, "body")
    hx = 27 if direction != 3 else 4
    hy = int(20 + 5 * math.sin(((hx - 3) + off) * 0.55))
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if abs(dx) + abs(dy) <= 5:
                put(hx + dx, hy + dy, "head")
    if layer == 0:
        put(hx - 1, hy - 1, "eye")
        put(hx + 1, hy - 1, "eye")
    return img


def draw_toad(direction, phase, layer, palette):
    img = new_image()

    def col(region):
        if layer == 1:
            return MASK_OF.get(region, TRANSPARENT)
        return palette.get(region, BASE.get(region, TRANSPARENT))

    def rect(x0, y0, x1, y1, region):
        c = col(region)
        if c[3]:
            _rect(img, x0, y0, x1, y1, c)

    hop = (0, -2, 0, 1)[phase % 4]
    rect(7, 13 + hop, 24, 27 + hop, "body")
    rect(10, 8 + hop, 21, 15 + hop, "head")
    rect(5, 24 + hop, 9, 28 + hop, "feet")
    rect(22, 24 + hop, 26, 28 + hop, "feet")
    rect(9, 20 + hop, 22, 24 + hop, "legs")
    if layer == 0:
        rect(11, 6 + hop, 14, 9 + hop, "head")
        rect(17, 6 + hop, 20, 9 + hop, "head")
        if direction != 0:
            rect(12, 7 + hop, 13, 8 + hop, "eye")
            rect(18, 7 + hop, 19, 8 + hop, "eye")
    return img


def draw_blob(direction, phase, layer, palette):
    """Sanguessuga / massa amorfa."""
    img = new_image()

    def col(region):
        if layer == 1:
            return MASK_OF.get(region, TRANSPARENT)
        return palette.get(region, BASE.get(region, TRANSPARENT))

    squash = (0, 1, 2, 1)[phase % 4]
    c = col("body")
    if c[3]:
        d = ImageDraw.Draw(img)
        d.ellipse([6, 14 + squash, 25, 28], fill=c)
        d.ellipse([10, 10 + squash, 21, 20 + squash], fill=c)
    h = col("head")
    if h[3]:
        d = ImageDraw.Draw(img)
        d.ellipse([12, 8 + squash, 19, 15 + squash], fill=h)
    if layer == 0 and direction != 0:
        img.putpixel((14, 11 + squash), BASE["eye"])
        img.putpixel((17, 11 + squash), BASE["eye"])
    return img


# ------------------------------------------------------------------ efeitos
def draw_effect(kind, phase, phases, tint):
    img = new_image()
    d = ImageDraw.Draw(img)
    t = (phase + 1) / float(phases)
    r, g, b = tint
    if kind == "burst":
        rad = 2 + int(13 * t)
        alpha = int(255 * (1.0 - 0.55 * t))
        d.ellipse([16 - rad, 16 - rad, 15 + rad, 15 + rad], outline=(r, g, b, alpha))
        d.ellipse([16 - rad + 2, 16 - rad + 2, 13 + rad, 13 + rad],
                  outline=(_c(r + 60), _c(g + 60), _c(b + 60), alpha))
    elif kind == "sparks":
        for i in range(8):
            a = i * math.pi / 4 + t * 0.8
            rad = 3 + 11 * t
            x = int(16 + math.cos(a) * rad)
            y = int(16 + math.sin(a) * rad)
            d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=(r, g, b, 255))
    elif kind == "smoke":
        for i in range(5):
            rad = 3 + i + int(4 * t)
            y = 24 - i * 4 - int(6 * t)
            d.ellipse([16 - rad, y - rad // 2, 15 + rad, y + rad // 2],
                      fill=(r, g, b, max(30, 210 - i * 35)))
    elif kind == "slash":
        for i in range(16):
            a = -0.6 + i * 0.12 + t * 1.2
            x = int(16 + math.cos(a) * 12)
            y = int(16 + math.sin(a) * 12)
            d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=(r, g, b, 255))
    else:  # pulse
        rad = 4 + int(8 * math.sin(math.pi * t))
        d.ellipse([16 - rad, 16 - rad, 15 + rad, 15 + rad], fill=(r, g, b, 190))
    return img


def draw_missile(dx, dy, kind, tint):
    """dx/dy em {-1,0,1}: direcao do voo."""
    img = new_image()
    d = ImageDraw.Draw(img)
    r, g, b = tint
    ang = math.atan2(dy, dx) if (dx or dy) else 0.0
    if kind == "shuriken":
        for i in range(4):
            a = ang + i * math.pi / 2
            x = int(16 + math.cos(a) * 7)
            y = int(16 + math.sin(a) * 7)
            d.line([16, 16, x, y], fill=(r, g, b, 255), width=2)
        d.ellipse([13, 13, 18, 18], fill=(_c(r + 50), _c(g + 50), _c(b + 50), 255), outline=OUTLINE)
    elif kind == "bolt":
        x0 = int(16 - math.cos(ang) * 11)
        y0 = int(16 - math.sin(ang) * 11)
        x1 = int(16 + math.cos(ang) * 11)
        y1 = int(16 + math.sin(ang) * 11)
        d.line([x0, y0, x1, y1], fill=(r, g, b, 255), width=3)
        d.ellipse([x1 - 2, y1 - 2, x1 + 2, y1 + 2],
                  fill=(_c(r + 70), _c(g + 70), _c(b + 70), 255))
    else:  # orb com rastro
        for i in range(6):
            f = i / 5.0
            x = int(16 - math.cos(ang) * 10 * f)
            y = int(16 - math.sin(ang) * 10 * f)
            rad = 5 - i // 2
            d.ellipse([x - rad, y - rad, x + rad, y + rad],
                      fill=(r, g, b, int(255 - 150 * f)))
    return img


# ----------------------------------------------------- icones de itens nossos
def draw_icon(kind, tint):
    """Icone 32x32 para os itens do data/tfs_mapping.json."""
    img = new_image()
    d = ImageDraw.Draw(img)
    r, g, b = tint
    main = (r, g, b, 255)
    light = (_c(r + 60), _c(g + 60), _c(b + 60), 255)
    dark = (_c(r - 55), _c(g - 55), _c(b - 55), 255)

    if kind == "blade":          # kunai / tanto / katana
        d.polygon([(16, 3), (20, 12), (16, 16), (12, 12)], fill=(206, 210, 220, 255), outline=OUTLINE)
        d.rectangle([14, 16, 17, 27], fill=main, outline=OUTLINE)
        d.rectangle([11, 15, 20, 17], fill=dark, outline=OUTLINE)
    elif kind == "star":         # shuriken
        for i in range(4):
            a = i * math.pi / 2 + math.pi / 4
            x = int(16 + math.cos(a) * 12)
            y = int(16 + math.sin(a) * 12)
            d.polygon([(16, 16), (x, y), (int(16 + math.cos(a + 0.5) * 5),
                                          int(16 + math.sin(a + 0.5) * 5))],
                      fill=main, outline=OUTLINE)
        d.ellipse([14, 14, 18, 18], fill=(40, 40, 48, 255))
    elif kind == "cloth":        # colete / bandana
        d.polygon([(8, 9), (23, 9), (26, 14), (22, 14), (22, 26), (9, 26), (9, 14), (5, 14)],
                  fill=main, outline=OUTLINE)
        d.line([16, 10, 16, 25], fill=dark)
    elif kind == "pants":
        d.polygon([(10, 8), (22, 8), (22, 27), (18, 27), (16, 17), (14, 27), (10, 27)],
                  fill=main, outline=OUTLINE)
    elif kind == "boot":
        d.polygon([(11, 8), (18, 8), (18, 22), (24, 22), (24, 27), (11, 27)],
                  fill=main, outline=OUTLINE)
        d.line([11, 26, 24, 26], fill=dark)
    elif kind == "helm":         # mascara anbu
        d.ellipse([8, 8, 24, 26], fill=main, outline=OUTLINE)
        d.rectangle([11, 14, 14, 17], fill=(30, 30, 38, 255))
        d.rectangle([18, 14, 21, 17], fill=(30, 30, 38, 255))
        d.line([10, 21, 22, 21], fill=dark)
    elif kind == "glove":
        d.rectangle([11, 12, 21, 25], fill=main, outline=OUTLINE)
        d.rectangle([9, 14, 11, 19], fill=main, outline=OUTLINE)
        d.line([11, 22, 21, 22], fill=dark)
    elif kind == "vial":
        return draw_vial(tint)
    elif kind == "pill":
        d.ellipse([10, 12, 22, 24], fill=main, outline=OUTLINE)
        d.ellipse([12, 14, 17, 19], fill=light)
    elif kind == "food":         # onigiri
        d.polygon([(16, 8), (25, 26), (7, 26)], fill=(244, 244, 240, 255), outline=OUTLINE)
        d.rectangle([12, 20, 20, 26], fill=(38, 52, 44, 255))
    elif kind == "pelt":
        d.polygon([(9, 8), (23, 8), (26, 18), (20, 27), (12, 27), (6, 18)],
                  fill=main, outline=OUTLINE)
        d.line([13, 13, 19, 13], fill=dark)
    elif kind == "fang":
        d.polygon([(16, 6), (21, 24), (16, 27), (11, 24)], fill=(238, 234, 220, 255), outline=OUTLINE)
    elif kind == "scroll":
        d.rectangle([8, 9, 23, 25], fill=(228, 214, 176, 255), outline=OUTLINE)
        d.rectangle([6, 7, 25, 10], fill=main, outline=OUTLINE)
        d.rectangle([6, 24, 25, 27], fill=main, outline=OUTLINE)
        for y in (14, 18, 21):
            d.line([11, y, 20, y], fill=(96, 84, 66, 255))
    elif kind == "ring":
        d.ellipse([10, 10, 22, 24], outline=main, width=3)
        d.ellipse([13, 6, 19, 12], fill=light, outline=OUTLINE)
    elif kind == "bag":
        d.rectangle([7, 12, 24, 27], fill=main, outline=OUTLINE)
        d.arc([11, 5, 20, 16], 180, 360, fill=OUTLINE)
        d.rectangle([13, 16, 18, 21], fill=dark)
    elif kind == "coin":
        d.ellipse([9, 11, 22, 24], fill=main, outline=OUTLINE)
        d.ellipse([12, 14, 19, 21], outline=light)
    elif kind == "emblem":
        d.polygon([(16, 6), (25, 12), (22, 25), (10, 25), (7, 12)], fill=main, outline=OUTLINE)
        d.line([16, 11, 16, 20], fill=light, width=2)
    else:
        return draw_cube(tint)
    return img
