#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gerador de pixel art de TERRENO por codigo, estilo Tibia 7.x/8.x.

Desenha os PNGs de `assets-src/sprites/terrain/` (arte propria, versionada — nada
vem da Tibia nem de NTO, ADR-002). O mapeamento server id -> PNG fica em
`assets-src/sprites/overrides/10_terrain.json`, aplicado por `tools/spr/imports.py`
por cima do manifesto no `build_assets.py`.

    .venv/bin/python tools/spr/gen_terrain.py
    .venv/bin/python tools/spr/build_assets.py
    .venv/bin/python tools/spr/dump_dat.py

Regras de estilo (o que faz "parecer Tibia"):

* paleta LIMITADA por material (4–6 tons), nunca gradiente continuo;
* ruido de valor **tileavel** (interpolacao bilinear numa grade que da a volta),
  quantizado nos tons da paleta -> manchas organicas, sem "quadrado chapado";
* nenhuma borda desenhada no perimetro do tile: a emenda entre tiles vizinhos
  some porque o ruido e periodico em 32px e as decoracoes dao a volta (wrap);
* objetos com contorno escuro de 1px, copa/corpo em 3 tons e sombra opaca no chao
  (o .spr de 1098 nao tem alpha: sombra transparente e impossivel, ver FORMATO.md);
* chao 32x32; arvores 64x64 (2x2 tiles) ancoradas no canto INFERIOR DIREITO —
  o cliente desenha o sprite (w,h) em ((width-1-w),(height-1-h))*32, entao a copa
  sobe e vai para a esquerda, como na Tibia;
* paredes/portas 32x64 (1 tile de largura, 2 de altura): sobem 32px sobre o tile.
"""
from __future__ import annotations

import math
import os

from PIL import Image

CELL = 32
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT_DIR = os.path.join(ROOT, "assets-src", "sprites", "terrain")


# --------------------------------------------------------------------- rng
class Rnd:
    """xorshift32 deterministico — nao depende da versao do `random`."""

    def __init__(self, seed):
        self.s = (seed * 2654435761 + 12345) & 0xFFFFFFFF or 1

    def u32(self):
        s = self.s
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        self.s = s & 0xFFFFFFFF
        return self.s

    def f(self):
        return self.u32() / 4294967296.0

    def i(self, n):
        return self.u32() % n

    def pick(self, seq):
        return seq[self.i(len(seq))]

    def chance(self, p):
        return self.f() < p


# ------------------------------------------------------------------ ruido
def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def noise_tile(size, cells, seed):
    """Ruido de valor **periodico** em `size` px, grade `cells`x`cells`.

    Como a grade da a volta (indices % cells), o resultado e continuo quando o
    tile e repetido lado a lado — e o que elimina a emenda entre tiles vizinhos.
    """
    rnd = Rnd(seed)
    g = [[rnd.f() for _ in range(cells)] for _ in range(cells)]
    step = size / float(cells)
    out = [[0.0] * size for _ in range(size)]
    for y in range(size):
        fy = y / step
        y0 = int(math.floor(fy)) % cells
        y1 = (y0 + 1) % cells
        ty = _smooth(fy - math.floor(fy))
        for x in range(size):
            fx = x / step
            x0 = int(math.floor(fx)) % cells
            x1 = (x0 + 1) % cells
            tx = _smooth(fx - math.floor(fx))
            a = g[y0][x0] + (g[y0][x1] - g[y0][x0]) * tx
            b = g[y1][x0] + (g[y1][x1] - g[y1][x0]) * tx
            out[y][x] = a + (b - a) * ty
    return out


def fbm(size, seed, octaves=((3, 1.0), (6, 0.5), (12, 0.25))):
    acc = [[0.0] * size for _ in range(size)]
    total = 0.0
    for k, (cells, amp) in enumerate(octaves):
        n = noise_tile(size, cells, seed * 131 + k * 977 + 7)
        for y in range(size):
            ay, ny = acc[y], n[y]
            for x in range(size):
                ay[x] += ny[x] * amp
        total += amp
    # normaliza min..max -> 0..1. Sem isso cada semente teria um brilho medio
    # diferente e o mapa viraria um xadrez de tiles claros e escuros.
    lo = min(min(r) for r in acc)
    hi = max(max(r) for r in acc)
    k = 1.0 / max(hi - lo, 1e-6)
    for y in range(size):
        for x in range(size):
            acc[y][x] = (acc[y][x] - lo) * k
    return acc


_BASE_CACHE = {}


def shared_field(key, seed, mix_seed, w=0.55, octaves=((3, 1.0), (6, 0.5), (12, 0.25))):
    """Campo do material = base COMUM + um pouco de variacao propria.

    Todas as variantes de grama (por exemplo) partem do mesmo ruido; so 28% do
    valor vem da semente da variante. Sem isso cada variante tem uma distribuicao
    de brilho diferente e o mapa vira um xadrez de tiles claros e escuros —
    visivel de longe, mesmo com as bordas casando.
    """
    base = _BASE_CACHE.get(key)
    if base is None:
        base = _BASE_CACHE[key] = fbm(CELL, seed, octaves)
    var = fbm(CELL, mix_seed, octaves)
    return [[base[y][x] * w + var[y][x] * (1.0 - w) for x in range(CELL)]
            for y in range(CELL)]


# matriz de Bayer 4x4 para dither ordenado (o "chuvisco" tipico do pixel art)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def quantize(field, palette, dither=0.055):
    """Campo 0..1 -> imagem RGBA usando SO as cores de `palette` (do escuro ao claro)."""
    size = len(field)
    img = Image.new("RGBA", (size, size))
    px = img.load()
    n = len(palette)
    for y in range(size):
        for x in range(size):
            v = field[y][x] + (BAYER[y & 3][x & 3] / 16.0 - 0.47) * dither
            i = int(v * n)
            px[x, y] = palette[0 if i < 0 else (n - 1 if i >= n else i)]
    return img


# ------------------------------------------------------------------ pintura
def put(img, x, y, color, wrap=True):
    w, h = img.size
    if wrap:
        x %= w
        y %= h
    elif not (0 <= x < w and 0 <= y < h):
        return
    img.putpixel((x, y), color)


def blob(img, cx, cy, r, color, rnd, wrap=True, squash=1.0):
    """Mancha irregular (nao um circulo perfeito) com borda ruidosa."""
    ri = int(math.ceil(r)) + 1
    for dy in range(-ri, ri + 1):
        for dx in range(-ri, ri + 1):
            d = math.hypot(dx, dy * squash)
            if d <= r - 0.6 or (d <= r + 0.4 and rnd.chance(0.55)):
                put(img, cx + dx, cy + dy, color, wrap)


def ellipse(img, cx, cy, rx, ry, color, wrap=False):
    for dy in range(-int(ry) - 1, int(ry) + 2):
        for dx in range(-int(rx) - 1, int(rx) + 2):
            if (dx / max(rx, 0.1)) ** 2 + (dy / max(ry, 0.1)) ** 2 <= 1.0:
                put(img, cx + dx, cy + dy, color, wrap)


def rect(img, x0, y0, x1, y1, color, wrap=False):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(img, x, y, color, wrap)


def outline(img, color=(22, 20, 16, 255)):
    """Contorno de 1px por fora da silhueta — o traco escuro do estilo Tibia."""
    px = img.load()
    w, h = img.size
    add = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] and px[nx, ny] != color:
                    add.append((x, y))
                    break
    for x, y in add:
        px[x, y] = color
    return img


def shade(c, k):
    """Clareia (k>0) / escurece (k<0) preservando a cara da paleta."""
    return (max(0, min(255, int(c[0] + k))), max(0, min(255, int(c[1] + k))),
            max(0, min(255, int(c[2] + k))), c[3] if len(c) > 3 else 255)


# ------------------------------------------------------------------ paletas
#: v4 — REVERSAO do contraste aberto da v3 (feedback: "manchada, escura,
#: remendos retangulares/xadrez por tile, mofo"). A causa raiz da v3 nao era
#: so a paleta 44..138: era misturar em cada variante um campo fbm PROPRIO
#: (normalizado 0..1 de forma independente por semente — `shared_field`,
#: peso 45%) por cima do campo comum. Normalizar cada campo ao seu proprio
#: min..max faz cada variante ter uma media/desvio ligeiramente diferentes
#: mesmo depois da mistura — o suficiente para o olho notar a media por-tile
#: divergindo em bloco (o "xadrez"). v4: SEM mistura por variante — todas as
#: 8 variantes usam o MESMO campo fbm (`P_GRASS_V4_FIELD_SEED`), so as
#: decoracoes esparsas (tufo raro) diferem. Isso zera a diferenca de media/
#: desvio entre variantes E a diferenca de borda entre vizinhas (medido:
#: ver docs, secao "Grama v4"). Paleta com so 3 tons bem proximos (base
#: unica ~#569639, ±6%) em vez dos 5 tons 44..138 da v3.
P_GRASS_V4 = [(81, 141, 53, 255), (86, 150, 56, 255), (91, 159, 59, 255)]
#: compat: mantido para quem ainda importar P_GRASS (nao usado por grass()).
P_GRASS = P_GRASS_V4
P_GRASS_DOT = [(150, 178, 98, 255), (38, 58, 28, 255)]
P_GRASS_BLADE = (118, 144, 70, 255)   # nao usado na v4 (risco de lamina saiu)
P_FLOWER = [(214, 206, 128, 255), (206, 132, 148, 255), (196, 196, 214, 255)]

P_DIRT = [(78, 60, 42, 255), (96, 74, 52, 255), (114, 90, 64, 255),
          (132, 106, 78, 255), (148, 122, 92, 255)]

P_COBBLE_GROUT = (44, 42, 40, 255)
P_COBBLE = [(92, 90, 88, 255), (110, 108, 104, 255), (128, 126, 120, 255),
            (146, 144, 138, 255)]

P_STONE = [(118, 116, 110, 255), (140, 138, 132, 255), (158, 156, 150, 255),
           (174, 172, 166, 255), (188, 186, 180, 255)]

P_WOOD = [(84, 58, 34, 255), (104, 74, 44, 255), (124, 90, 54, 255),
          (144, 108, 68, 255), (162, 126, 84, 255)]

#: v4 — mesma regra de baixo contraste da grama: 3 tons proximos (base unica
#: ~(78,72,52), ±8%) em vez dos 5 tons 48..110 da v3, que faziam variantes
#: divergirem em media quando cada uma vinha de shared_field() com fbm
#: proprio (mesma causa raiz do xadrez da grama).
P_MUD_V4 = [(72, 66, 48, 255), (78, 72, 52, 255), (84, 78, 56, 255)]
P_MUD = P_MUD_V4
P_PUDDLE = [(42, 48, 42, 255), (52, 60, 50, 255), (66, 76, 62, 255)]

#: areia de praia — mesma regra de baixo contraste da grama/lama v4 (3 tons
#: proximos, base unica ~(198,178,138) +-6%): a Costa das Mares usava os ids
#: vanilla 104/231/9059 sem NENHUM override proprio (gen_placeholders.py cai
#: na regra de estilo generica -> quadrado liso), causa raiz do "praia lisa
#: com quadrados cinza" reportado no tour in-game.
P_SAND_V4 = [(186, 166, 128, 255), (198, 178, 138, 255), (210, 190, 148, 255)]
P_SAND = P_SAND_V4

P_WATER = [(34, 62, 84, 255), (44, 76, 100, 255), (56, 92, 116, 255),
           (70, 108, 132, 255), (92, 130, 152, 255)]

#: 4 tons por especie, do escuro ao claro. O intervalo e LARGO de proposito:
#: com tons proximos a copa vira um disco chapado.
P_LEAF = {
    "fir":      [(20, 42, 26, 255), (34, 66, 38, 255), (58, 98, 56, 255), (88, 128, 76, 255)],
    "sycamore": [(40, 64, 28, 255), (62, 94, 42, 255), (92, 128, 60, 255), (126, 162, 82, 255)],
    "willow":   [(42, 70, 40, 255), (64, 100, 56, 255), (96, 134, 80, 255), (130, 166, 104, 255)],
    "beech":    [(56, 66, 26, 255), (84, 98, 40, 255), (118, 134, 58, 255), (152, 170, 84, 255)],
    "pine":     [(18, 40, 28, 255), (30, 62, 40, 255), (48, 88, 56, 255), (72, 116, 78, 255)],
}
P_BARK = [(48, 36, 26, 255), (66, 50, 34, 255), (86, 66, 46, 255), (106, 84, 60, 255)]
P_DEAD = [(58, 48, 38, 255), (78, 66, 52, 255), (98, 84, 68, 255), (118, 104, 86, 255)]
SHADOW = (46, 54, 34, 255)          # sombra opaca (alpha binario, ver FORMATO.md)
DARK = (20, 18, 16, 255)


# =========================================================== CHAO (32x32)
#: campo de ruido UNICO para todas as variantes de grama v4 (ver P_GRASS_V4).
#: periodo = CELL = 32px (noise_tile ja e periodico em `size`, entao qualquer
#: `cells` da grade fecha sem costura — "periodo multiplo de 32" cumprido
#: trivialmente com multiplicador 1). Nao ha como fazer a fase depender da
#: posicao do tile no mundo (as variantes sao PNGs fixos, gerados sem saber
#: onde vao cair no mapa — isso e decidido depois por tools/map/build_valley.py,
#: fora do escopo deste trabalho); a alternativa adotada, e que resolve o
#: mesmo problema por outro caminho, e todas as variantes usarem o MESMO
#: campo em vez de um campo por variante — a emenda entao e EXATA (mesma
#: textura) em vez de apenas "estatisticamente parecida".
GRASS_V4_OCTAVES = ((3, 1.0), (7, 0.4))
GRASS_V4_SEED = 42010


def grass(v):
    """v4 — grama de baixo contraste, estilo Tibia classico (revisao da v3).

    Feedback que motivou a reescrita: a v3 abriu contraste demais (paleta
    44..138, tufos escuros, laminas, flor, pedrinha) e cada variante vinha de
    `shared_field()` — campo comum (55%) + um fbm PROPRIO por variante (45%,
    normalizado 0..1 de forma independente). Normalizar cada campo ao seu
    proprio min/max faz a MEDIA da mistura variar um pouco de variante para
    variante mesmo com o mesmo campo base — o suficiente para o mapa ler como
    um xadrez de tiles um pouco mais claros/escuros lado a lado (medido: ver
    docs, secao "Grama v4"). A v4 elimina a causa raiz em vez de so abafar o
    sintoma: TODAS as 8 variantes usam o **mesmo** campo `fbm` (nenhuma
    mistura por variante), paleta de **3 tons** bem proximos (base unica
    ±6%, ver P_GRASS_V4) e a UNICA decoracao e um tufo claro de 2-4px em
    **2 das 8 variantes** (25%, o mais perto de "20%" que da com 8 variantes
    discretas) — nada de touceira escura, lamina, flor ou pedrinha (essas
    decoracoes tinham 1-3px de mancha mais escura que a v3 empilhava aos
    montes por tile; a v4 corta todas para não ter NENHUMA mancha escura).
    Sem contorno preto (outline() nunca e chamado aqui, como antes)."""
    f = fbm(CELL, GRASS_V4_SEED, GRASS_V4_OCTAVES)
    img = quantize(f, P_GRASS_V4, dither=0.035)
    if v in (1, 5):                      # tufo raro: 2 de 8 variantes (~25%)
        rnd = Rnd(9200 + v * 71)
        cx, cy = 6 + rnd.i(CELL - 12), 6 + rnd.i(CELL - 12)
        tuft = shade(P_GRASS_V4[2], 14)  # 1 tom acima do mais claro da paleta
        offsets = [(0, 0), (0, -1), (1, 0), (1, -1)][:2 + rnd.i(3)]  # 2-4px
        for dx, dy in offsets:
            put(img, cx + dx, cy + dy, tuft, wrap=False)
    return img


def grass_shade(v, amount=-26):
    """Variante de grama escurecida para tiles ADJACENTES a arvore (vinheta de
    sombra). NAO e aplicada pelo build atual — tools/map/build_valley.py
    (autoborder/decor) e que decidiria, por vizinhanca, trocar o server id do
    tile por esta variante; fora do escopo deste trabalho (ver docs). Aqui so
    geramos a arte de referencia: mesma base + decoracoes de `grass(v)`,
    escurecida em bloco (nao regenerada do zero, para casar pixel a pixel com
    a variante normal e emendar sem costura)."""
    img = grass(v).copy()
    px = img.load()
    for y in range(CELL):
        for x in range(CELL):
            px[x, y] = shade(px[x, y], amount)
    return img


def dirt(v):
    """v3 — terra batida: ruido mais grosso + cascalho em 2 tons + rachaduras
    finas (a v2 so tinha cascalho claro; rachaduras dao a leitura de terra
    RESSECADA, nao so 'marrom com pontinhos')."""
    oct_ = ((2, 1.0), (5, 0.55), (10, 0.3))
    f = shared_field("dirt", 2000, 2000 + v + 1, octaves=oct_)
    img = quantize(f, P_DIRT, dither=0.08)
    rnd = Rnd(7700 + v * 53)
    for _ in range(14):                  # cascalho claro
        x, y = rnd.i(CELL), rnd.i(CELL)
        put(img, x, y, shade(P_DIRT[4], 16))
        if rnd.chance(0.4):
            put(img, x + 1, y, P_DIRT[4])
    for _ in range(6):                   # cascalho escuro (2º tom, contraste)
        x, y = rnd.i(CELL), rnd.i(CELL)
        put(img, x, y, shade(P_DIRT[0], -10))
    for _ in range(5):                   # sulcos de pisada
        blob(img, rnd.i(CELL), rnd.i(CELL), 1.8 + rnd.f() * 1.4, P_DIRT[0], rnd, squash=1.9)
    for _ in range(3):                   # rachaduras finas (terra ressecada)
        x, y = rnd.i(CELL), rnd.i(CELL)
        ang = rnd.f() * 2 * math.pi
        for k in range(3 + rnd.i(4)):
            put(img, x + int(k * math.cos(ang)), y + int(k * math.sin(ang)), shade(P_DIRT[0], -16))
            ang += (rnd.f() - 0.5) * 0.9
    return img


def cobble(v):
    """Paralelepipedo: pedras irregulares (voronoi grosseiro) + rejunte escuro."""
    img = Image.new("RGBA", (CELL, CELL), P_COBBLE_GROUT)
    rnd = Rnd(3100 + v * 71)
    # sementes numa grade 4x4 com jitter -> pedras de ~8px, todas dentro do tile
    # sementes numa grade 4x4 com jitter; as pedras PREENCHEM o tile e o rejunte
    # e so a fronteira entre celulas (diferenca das 2 menores distancias < 1.3px)
    seeds = []
    for gy in range(4):
        for gx in range(4):
            seeds.append((gx * 8 + 4 + rnd.i(5) - 2, gy * 8 + 4 + rnd.i(5) - 2,
                          rnd.i(len(P_COBBLE)), rnd.i(9) - 4))
    px = img.load()
    for y in range(CELL):
        for x in range(CELL):
            d1, d2, best = 1e9, 1e9, None
            for s in seeds:
                dx = min(abs(x - s[0]), CELL - abs(x - s[0]))
                dy = min(abs(y - s[1]), CELL - abs(y - s[1]))
                d = math.hypot(dx, dy)
                if d < d1:
                    d1, d2, best = d, d1, s
                elif d < d2:
                    d2 = d
            if d2 - d1 < 1.35:           # rejunte escuro entre as pedras
                continue
            c = shade(P_COBBLE[best[2]], best[3])
            dy = y - best[1]
            if d2 - d1 < 2.6:            # bisel: escurece perto da borda...
                c = shade(c, -18)
            if dy <= -2:                 # ...e o topo da pedra recebe luz
                c = shade(c, 18)
            elif dy >= 3:
                c = shade(c, -10)
            px[x, y] = shade(c, rnd.i(7) - 3)
    for _ in range(14):                  # sujeira nas juntas
        put(img, rnd.i(CELL), rnd.i(CELL), shade(P_COBBLE[0], -14))
    return img


def stone_floor():
    """Piso de pedra clara (praca/templo): lajes de 16x16 em FIADA (a fiada de
    baixo desloca 8px), junta discreta e desgaste — nao um papel quadriculado."""
    f = fbm(CELL, 5150, octaves=((4, 1.0), (9, 0.45)))
    img = quantize(f, P_STONE, dither=0.05)
    rnd = Rnd(9110)
    joint = shade(P_STONE[0], -44)        # v3: junta mais funda (era -30, lia como risco fraco)
    lip = shade(P_STONE[4], 12)
    px = img.load()
    # 4 lajes: linha 0 comeca em x=0, linha 1 desloca 8px (aparelho de tijolo)
    for row in range(2):
        y0, y1 = row * 16, row * 16 + 15
        tone = 0
        for col in range(2):
            x0 = (col * 16 + row * 8) % CELL
            tone = rnd.i(9) - 4
            for y in range(y0, y1 + 1):
                for k in range(16):
                    x = (x0 + k) % CELL
                    px[x, y] = shade(px[x, y], tone)
            for k in range(16):          # junta vertical + quina iluminada
                x = (x0 + k) % CELL
                px[x, y1] = joint
                px[x, y0] = lip
            px[x0 % CELL, y0] = joint
            for y in range(y0, y1 + 1):
                px[x0 % CELL, y] = joint
                px[(x0 + 1) % CELL, y] = lip
    for _ in range(26):                  # desgaste / manchas
        x, y = rnd.i(CELL), rnd.i(CELL)
        px[x, y] = shade(px[x, y], -10 if rnd.chance(0.6) else 10)
    for _ in range(5):
        blob(img, rnd.i(CELL), rnd.i(CELL), 1.4 + rnd.f(), shade(P_STONE[1], -6), rnd)
    return img


def wood_floor():
    """Piso de madeira: tabuas de 8px com veio e prego."""
    img = Image.new("RGBA", (CELL, CELL), P_WOOD[2])
    rnd = Rnd(6060)
    f = fbm(CELL, 6061, octaves=((3, 1.0), (16, 0.45)))
    px = img.load()
    for y in range(CELL):
        for x in range(CELL):
            band = (y // 8) % 4
            base = P_WOOD[1 + (band % 3)]
            v = f[y][x]
            px[x, y] = shade(base, -10 if v < 0.4 else (10 if v > 0.68 else 0))
    for y in (7, 15, 23, 31):            # seam entre tabuas (periodico)
        for x in range(CELL):
            put(img, x, y, P_WOOD[0])
            put(img, x, y - 1, shade(P_WOOD[3], 8))
    for by in range(4):                  # topo de tabua (junta vertical)
        x = (by * 11 + 5) % CELL
        for y in range(by * 8, by * 8 + 7):
            put(img, x, y, shade(P_WOOD[0], 6))
        put(img, (x + 3) % CELL, by * 8 + 3, P_WOOD[0])      # prego
        put(img, (x + 3) % CELL, by * 8 + 2, shade(P_WOOD[4], 12))
    return img


MUD_V4_OCTAVES = ((4, 1.0), (9, 0.35))
MUD_V4_SEED = 51030


def mud(v):
    """v4 — mesma regra de baixo contraste da grama (docs, secao "Grama v4"):
    TODAS as variantes usam o MESMO campo fbm (era `shared_field()` com um
    fbm proprio por variante — mesma causa raiz do xadrez da grama v3),
    paleta de 3 tons proximos (P_MUD_V4, ±8%, era 5 tons 48..110) e poca
    atenuada (P_PUDDLE clareado — era quase preto, contraste desnecessario
    contra uma lama ja escura)."""
    f = fbm(CELL, MUD_V4_SEED, MUD_V4_OCTAVES)
    img = quantize(f, P_MUD_V4, dither=0.05)
    rnd = Rnd(1230 + v * 97)
    for _ in range(1 + v % 2):           # pocas: elipses largas e rasas
        cx, cy = rnd.i(CELL), rnd.i(CELL)
        rx = 6.0 + rnd.f() * 3.0
        ry = rx * 0.52
        ellipse(img, cx, cy, rx, ry, P_PUDDLE[1], wrap=True)
        ellipse(img, cx, cy, rx - 1.6, ry - 0.9, P_PUDDLE[0], wrap=True)
        for i in range(-2, 3):           # reflexo na agua parada
            put(img, cx + i, cy - int(ry * 0.45), P_PUDDLE[2])
    for _ in range(8):                   # torroes secos (1 tom acima/abaixo, discreto)
        x, y = rnd.i(CELL), rnd.i(CELL)
        put(img, x, y, shade(P_MUD_V4[2], 6))
        put(img, x + 1, y, shade(P_MUD_V4[2], -4))
    return img


SAND_V4_OCTAVES = ((3, 1.0), (8, 0.4))
SAND_V4_SEED = 61040


def sand(v):
    """v4 (mesma familia grass/mud v4) — areia de praia: TODAS as variantes
    usam o MESMO campo fbm (evita o xadrez de tiles claros/escuros, ver docs
    secao "Grama v4"), paleta de 3 tons proximos e decoracao esparsa
    (conchinhas/pontos de sombra) para nao virar mancha bege lisa."""
    f = fbm(CELL, SAND_V4_SEED, SAND_V4_OCTAVES)
    img = quantize(f, P_SAND_V4, dither=0.045)
    rnd = Rnd(3300 + v * 61)
    for _ in range(10):                   # graozinhos/conchinhas claras
        x, y = rnd.i(CELL), rnd.i(CELL)
        put(img, x, y, shade(P_SAND_V4[2], 20))
    for _ in range(5):                    # sombra rasa (pegada/depressao)
        x, y = rnd.i(CELL), rnd.i(CELL)
        put(img, x, y, shade(P_SAND_V4[0], -14))
    if v == 1:                            # ondulacao sutil de vento em 1 das 3
        for x in range(0, CELL, 4):
            y = (10 + int(2.0 * math.sin(x / 6.0))) % CELL
            put(img, x, y, shade(P_SAND_V4[0], -8))
            put(img, (x + 1) % CELL, y, shade(P_SAND_V4[0], -8))
    return img


# =========================================================== RUINAS (piso rachado)
#: mesma regra de baixo contraste v4 (grama/lama/areia): 3 tons proximos, TODAS
#: as variantes no MESMO campo fbm — so a densidade de rachadura/musgo muda.
#: Tom acinzentado-amarronzado, distinto do stone_floor cinza-claro da praca
#: (evita o "mesmo piso de cobble liso" reportado pelo usuario).
P_CRACKSTONE_V4 = [(104, 96, 82, 255), (112, 104, 88, 255), (120, 112, 94, 255)]
CRACKSTONE_V4_OCTAVES = ((3, 1.0), (7, 0.4))
CRACKSTONE_V4_SEED = 71050


def crackstone(v):
    """Piso de pedra antiga rachada — Ruinas do Cla Marionetista. v=0/1 so
    rachaduras (densidade crescente); v=2 rachaduras + musgo esparso."""
    f = fbm(CELL, CRACKSTONE_V4_SEED, CRACKSTONE_V4_OCTAVES)
    img = quantize(f, P_CRACKSTONE_V4, dither=0.04)
    rnd = Rnd(4200 + v * 83)
    for _ in range(2 + v * 2):            # rachaduras finas ramificadas
        x, y = rnd.i(CELL), rnd.i(CELL)
        ang = rnd.f() * 2 * math.pi
        for k in range(4 + rnd.i(5)):
            put(img, x + int(k * math.cos(ang)), y + int(k * math.sin(ang)),
                shade(P_CRACKSTONE_V4[0], -30), wrap=False)
            ang += (rnd.f() - 0.5) * 0.7
    if v == 2:                            # musgo esparso (1 das 3 variantes)
        for _ in range(4):
            x, y = rnd.i(CELL), rnd.i(CELL)
            put(img, x, y, (70, 88, 52, 255), wrap=False)
    return img


# =========================================================== MONTANHA DO TROVAO
#: rocha cinza-azulada (trilha/planalto) — mesma regra low-contrast v4.
P_ROCK_V4 = [(96, 104, 116, 255), (104, 112, 124, 255), (112, 120, 132, 255)]
ROCK_V4_OCTAVES = ((3, 1.0), (7, 0.4))
ROCK_V4_SEED = 81060


def rock(v):
    """Piso de rocha da Montanha do Trovao. v=1 ganha respingos claros de
    neve (perto das bordas nevadas do topo)."""
    f = fbm(CELL, ROCK_V4_SEED, ROCK_V4_OCTAVES)
    img = quantize(f, P_ROCK_V4, dither=0.045)
    rnd = Rnd(5300 + v * 61)
    for _ in range(6):                    # veios minerais claros
        x, y = rnd.i(CELL), rnd.i(CELL)
        put(img, x, y, shade(P_ROCK_V4[2], 18), wrap=False)
    if v == 1:
        for _ in range(5):
            x, y = rnd.i(CELL), rnd.i(CELL)
            put(img, x, y, (222, 230, 236, 255), wrap=False)
    return img


#: neve — usada no rim/topo da montanha (chao proprio) E como material ALTO do
#: par de autoborder snow_rock (gen_borders.py).
P_SNOW_V4 = [(210, 220, 228, 255), (222, 230, 236, 255), (234, 240, 244, 255)]
SNOW_V4_OCTAVES = ((3, 1.0), (7, 0.4))
SNOW_V4_SEED = 81070


def snow(v):
    f = fbm(CELL, SNOW_V4_SEED, SNOW_V4_OCTAVES)
    img = quantize(f, P_SNOW_V4, dither=0.04)
    rnd = Rnd(5400 + v * 61)
    for _ in range(6):                    # sombra rasa (pegada/depressao)
        x, y = rnd.i(CELL), rnd.i(CELL)
        put(img, x, y, shade(P_SNOW_V4[0], -16), wrap=False)
    return img


#: gelo do lago congelado — bloqueia (mesma regra do abismo de agua da trilha).
P_ICE_V4 = [(150, 190, 208, 255), (176, 210, 224, 255), (204, 228, 236, 255)]


def ice():
    f = fbm(CELL, 81080, ((3, 1.0), (6, 0.4)))
    img = quantize(f, P_ICE_V4, dither=0.05)
    rnd = Rnd(9700)
    for _ in range(4):                    # rachaduras no gelo
        x, y = rnd.i(CELL), rnd.i(CELL)
        ang = rnd.f() * 2 * math.pi
        for k in range(6 + rnd.i(6)):
            put(img, x + int(k * math.cos(ang)), y + int(k * math.sin(ang) * 0.5),
                shade(P_ICE_V4[0], -20), wrap=False)
            ang += (rnd.f() - 0.5) * 0.4
    return img


# =========================================================== COVIL DA NUVEM VERMELHA
#: basalto escuro — baixo contraste, quase preto, com veios avermelhados
#: DISCRETOS (regra "nunca neon" do projeto: tom terroso escuro, nao vermelho vivo).
P_BASALT_V4 = [(46, 42, 44, 255), (52, 48, 50, 255), (58, 54, 56, 255)]
BASALT_V4_OCTAVES = ((3, 1.0), (7, 0.4))
BASALT_V4_SEED = 91090


def basalt(v):
    """Piso de basalto do Covil da Nuvem Vermelha."""
    f = fbm(CELL, BASALT_V4_SEED, BASALT_V4_OCTAVES)
    img = quantize(f, P_BASALT_V4, dither=0.045)
    rnd = Rnd(6100 + v * 61)
    for _ in range(5):                    # veios de calor residual, discretos
        x, y = rnd.i(CELL), rnd.i(CELL)
        put(img, x, y, (86, 46, 40, 255), wrap=False)
    return img


def basalt_wall(kind):
    """Parede de rocha negra (Covil) — mesma alvenaria de `stone_wall`, paleta
    quase preta com veios avermelhados discretos (calor residual do vulcao)."""
    pal = [(38, 36, 36, 255), (52, 48, 48, 255), (64, 60, 60, 255),
           (78, 72, 72, 255), (92, 86, 86, 255)]
    img = _wall_base(pal, {"h": 31, "v": 32, "c": 33}[kind], (24, 22, 22, 255))
    rnd = Rnd(199 + ord(kind))
    if kind == "v":
        for y in range(4, 64):
            for x in range(0, 6):
                img.putpixel((x, y), shade(img.getpixel((x, y)), -18))
    if kind == "c":
        for y in range(6, 62):
            for x in range(6, 26):
                img.putpixel((x, y), shade(img.getpixel((x, y)), 8))
        rect(img, 6, 6, 25, 6, shade(pal[4], 12))
        rect(img, 6, 6, 6, 61, shade(pal[4], 6))
        rect(img, 25, 6, 25, 61, shade(pal[0], -8))
    for _ in range(10):                   # veios avermelhados discretos
        x, y = rnd.i(CELL), 20 + rnd.i(40)
        put(img, x, y, (74, 40, 36, 255), wrap=False)
    return img


def stone_wall_broken():
    """Segmento de parede de pedra QUEBRADA (Ruinas do Cla Marionetista) —
    topo em silhueta IRREGULAR (a parede "desabou" em alturas diferentes por
    coluna), nao um retangulo perfeito. Ainda bloqueia (blockSolid), mas le
    como muro em ruina, distinto da stone_wall intacta da praca/vila."""
    pal = [(70, 68, 64, 255), (96, 94, 90, 255), (118, 116, 110, 255),
           (140, 138, 132, 255), (160, 158, 152, 255)]
    img = Image.new("RGBA", (CELL, 64), (0, 0, 0, 0))
    rnd = Rnd(2600)
    heights = [26 + rnd.i(24) for _ in range(CELL)]     # 26..49px de altura
    for x in range(CELL):
        top = 64 - heights[x]
        for y in range(top, 64):
            band = (y - top) // 8
            c = pal[1 + (band % (len(pal) - 1))]
            k = 16 if y == top else (-14 if y >= 60 else 0)
            img.putpixel((x, y), shade(c, k + rnd.i(7) - 3))
        img.putpixel((x, top), shade(pal[4], 10))       # quina lascada
    rect(img, 0, 60, 31, 63, shade(pal[0], -10))
    for _ in range(14):                    # musgo
        x, y = rnd.i(CELL), 30 + rnd.i(30)
        if img.getpixel((x, y))[3]:
            put(img, x, y, (66, 84, 50, 255), wrap=False)
    for _ in range(8):                     # rachaduras na quina
        x = rnd.i(CELL)
        top = 64 - heights[x]
        y = top + 2 + rnd.i(4)
        if y < 64:
            put(img, x, y, shade(pal[0], -26), wrap=False)
    return img


def water(phase, phases=3):
    """v3 — agua rasa animada: o campo de ruido ANDA (offset por fase) e o
    brilho ondula. `phases` fases -> `animationPhases` no .dat (o id 4608 tem
    FLAG_ANIMATION no OTB, ver FORMATO.md secao 5). Reforcado com uma segunda
    faixa de crista (reflexo) e cintilacao mais forte (a v2 tinha uma unica
    crista discreta e lia como 'agua fosca', sem brilho)."""
    f = fbm(CELL, 4400, octaves=((2, 1.0), (4, 0.55), (8, 0.3)))
    sh = (phase * CELL) // phases        # deslocamento inteiro = continua tileavel
    rolled = [[f[(y + sh) % CELL][(x + (sh // 2)) % CELL] for x in range(CELL)]
              for y in range(CELL)]
    img = quantize(rolled, P_WATER, dither=0.06)
    rnd = Rnd(5500)
    # cristas de onda: senoide de periodo 16px (tileavel), deslocada pela fase.
    # Discretas de proposito — onda forte demais vira listra de papel de parede.
    for x in range(CELL):
        y = int(7 + 3.0 * math.sin((x / 16.0 + phase / float(phases)) * 2 * math.pi))
        for k in range(2):
            yy = (y + k * 16) % CELL
            if (x + phase * 3) % 5:
                put(img, x, yy, P_WATER[4])
            put(img, x, yy + 1, P_WATER[1])
    for x in range(CELL):                # 2ª crista (reflexo), fase deslocada
        y = int(23 + 2.4 * math.sin((x / 14.0 + 0.4 + phase / float(phases)) * 2 * math.pi))
        if (x + phase * 2) % 4 == 0:
            put(img, x, y % CELL, shade(P_WATER[4], 20))
    for _ in range(14):                  # cintilacao / brilho (era 10, mais fraco)
        put(img, rnd.i(CELL), (rnd.i(CELL) + phase * 5) % CELL, shade(P_WATER[4], 26))
    for _ in range(4):                   # borrifo de espuma branca (poucas, isoladas)
        put(img, rnd.i(CELL), (rnd.i(CELL) + phase * 7) % CELL, (206, 224, 232, 255))
    return img


# ===================================================== OBJETOS (64x64, 2x2)
def _tree_shadow(img, cx=44, cy=58, rx=17, ry=6):
    ellipse(img, cx, cy, rx, ry, SHADOW)


def _trunk(img, x, y0, y1, half, pal=P_BARK, lean=0.0):
    for y in range(y0, y1 + 1):
        t = (y - y0) / float(max(1, y1 - y0))
        w = int(round(half + t * 1.4))
        xc = int(round(x + lean * (1.0 - t) * 6))
        rect(img, xc - w, y, xc + w, y, pal[2])
        rect(img, xc - w, y, xc - w + 1, y, pal[1])
        put(img, xc + w, y, pal[1])
        put(img, xc + w - 1, y, pal[3])
    # raizes
    rect(img, x - half - 3, y1, x - half, y1, pal[1])
    rect(img, x + half, y1, x + half + 3, y1, pal[1])


def _canopy(img, cx, cy, rx, ry, pal, rnd, lumps=7, wisp=0.0):
    """Copa em 3 tons: silhueta LOBULADA (nunca um disco), massa em meio-tom,
    sombra embaixo/direita e luz vinda do topo-esquerdo — a receita do Tibia."""
    sq = rx / max(ry, 1.0)
    ellipse(img, cx, cy, rx * 0.74, ry * 0.74, pal[1])
    for i in range(lumps):                                   # lobulos da borda
        a = 2 * math.pi * i / lumps + rnd.f() * 0.5
        blob(img, int(cx + math.cos(a) * rx * 0.72),
             int(cy + math.sin(a) * ry * 0.72),
             min(rx, ry) * (0.38 + rnd.f() * 0.22), pal[1], rnd, wrap=False, squash=sq)
    for i in range(6):                                       # sombra (baixo/direita)
        a = math.pi * (0.05 + i * 0.17)
        blob(img, int(cx + math.cos(a) * rx * 0.6), int(cy + math.sin(a) * ry * 0.62),
             min(rx, ry) * (0.30 + rnd.f() * 0.16), pal[0], rnd, wrap=False, squash=sq)
    for i in range(5):                                       # luz (topo/esquerda)
        a = math.pi * (1.02 + i * 0.19)
        blob(img, int(cx + math.cos(a) * rx * 0.52), int(cy + math.sin(a) * ry * 0.5),
             min(rx, ry) * (0.26 + rnd.f() * 0.16), pal[2], rnd, wrap=False, squash=sq)
    for _ in range(16):                                      # folhas iluminadas
        a, r = rnd.f() * 2 * math.pi, rnd.f()
        x = int(cx + math.cos(a) * rx * r * 0.75)
        y = int(cy + math.sin(a) * ry * r * 0.75)
        if img.getpixel((max(0, min(img.width - 1, x)), max(0, min(img.height - 1, y))))[3]:
            put(img, x, y, pal[3] if y < cy else pal[0], wrap=False)
    if wisp:                                                 # galhos pendentes (salgueiro)
        for i in range(13):
            t = i / 12.0
            x = int(cx - rx * 0.9 + t * rx * 1.8)
            # comeca na borda INFERIOR da elipse e desce pouco: sem "pernas de aranha"
            y0 = int(cy + ry * math.sqrt(max(0.0, 1.0 - (2 * t - 1) ** 2)) * 0.9)
            h = int(wisp * (4 + (i % 4) * 3))
            for k in range(h):
                put(img, x, y0 + k, pal[1] if k % 3 else pal[0], wrap=False)


def _conifer(img, pal, rnd, tiers, cx=45):
    """Coniferas: saias triangulares empilhadas, borda serrilhada."""
    for (ytop, ybot, half) in tiers:
        for y in range(ytop, ybot + 1):
            t = (y - ytop) / float(max(1, ybot - ytop))
            w = int(round(t * half)) + (1 if (y % 3 == 0) else 0)
            if w <= 0:
                continue
            rect(img, cx - w, y, cx + w, y, pal[1])
            rect(img, cx - w, y, cx - w + 2, y, pal[2])
            rect(img, cx + w - 2, y, cx + w, y, pal[0])
        rect(img, cx - half - 1, ybot, cx + half + 1, ybot, pal[0])
        for _ in range(6):                                   # agulhas claras
            put(img, cx - half + rnd.i(max(1, 2 * half)),
                ytop + rnd.i(max(1, ybot - ytop)), pal[3], wrap=False)


def tree(kind):
    """5 tipos de arvore viva, 64x64, ancoradas no canto inferior direito."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    rnd = Rnd({"fir": 11, "sycamore": 22, "willow": 33, "beech": 44, "pine": 55}[kind])
    pal = P_LEAF[kind]
    _tree_shadow(img)
    if kind == "fir":                    # pinheiro baixo: 3 saias triangulares
        _trunk(img, 45, 44, 60, 2)
        _conifer(img, pal, rnd, ((10, 26, 12), (18, 38, 18), (28, 50, 24)))
        rect(img, 44, 4, 46, 12, pal[1])
        put(img, 45, 3, pal[2])
    elif kind == "pine":                 # pinheiro ALTO: tronco longo, saias no topo
        _trunk(img, 45, 36, 61, 2)
        _conifer(img, pal, rnd, ((6, 20, 10), (14, 30, 15), (23, 42, 20)))
        rect(img, 44, 1, 46, 8, pal[1])
        for i in range(3):               # galhos secos no tronco
            put(img, 45 - 3 - i, 44 + i * 5, P_BARK[1], wrap=False)
            put(img, 45 + 3 + i, 48 + i * 5, P_BARK[1], wrap=False)
    elif kind == "sycamore":             # copa larga e alta
        _trunk(img, 46, 34, 61, 3, lean=-0.35)
        _canopy(img, 38, 20, 26, 20, pal, rnd, lumps=10)
    elif kind == "beech":                # copa arredondada, galhos aparentes
        _trunk(img, 46, 32, 61, 3)
        for i in range(6):
            put(img, 46 - 2 - i, 34 - i, P_BARK[1], wrap=False)
            put(img, 46 - 3 - i, 34 - i, P_BARK[2], wrap=False)
            put(img, 46 + 2 + i, 36 - i, P_BARK[1], wrap=False)
        _canopy(img, 40, 19, 24, 19, pal, rnd, lumps=7)
    elif kind == "willow":               # salgueiro: copa larga/baixa, galhos caindo
        _trunk(img, 46, 40, 61, 3)
        _canopy(img, 39, 22, 25, 16, pal, rnd, lumps=9, wisp=1.0)
    return outline(img)


def dead_tree(v):
    """5 arvores mortas: so galhos, sem copa."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    rnd = Rnd(700 + v * 131)
    ellipse(img, 45, 58, 12, 5, shade(SHADOW, -6))
    _trunk(img, 46, 26 - v * 2, 61, 2 + (v % 2), pal=P_DEAD, lean=(v - 2) * 0.15)

    def branch(x, y, ang, ln, depth):
        cx, cy = float(x), float(y)
        for i in range(ln):
            cx += math.cos(ang)
            cy += math.sin(ang)
            put(img, int(cx), int(cy), P_DEAD[1 + (i % 2)], wrap=False)
            ang += (rnd.f() - 0.5) * 0.25
        if depth:
            branch(int(cx), int(cy), ang - 0.6 - rnd.f() * 0.3, max(3, ln - 4), depth - 1)
            branch(int(cx), int(cy), ang + 0.6 + rnd.f() * 0.3, max(3, ln - 4), depth - 1)

    top = 26 - v * 2
    branch(46, top + 4, -math.pi / 2 - 0.9 - rnd.f() * 0.3, 9 + v, 2)
    branch(46, top + 8, -math.pi / 2 + 0.9 + rnd.f() * 0.3, 8 + v, 2)
    branch(46, top, -math.pi / 2 + (rnd.f() - 0.5) * 0.4, 10, 2)
    if v % 2:
        branch(46, top + 14, -math.pi / 2 - 1.2, 7, 1)
    return outline(img)


def bush(v):
    """Arbusto 1x1 (32x32): moita compacta."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    rnd = Rnd(310 + v * 47)
    pal = [P_LEAF["sycamore"], P_LEAF["beech"],
           [(70, 62, 40, 255), (94, 84, 52, 255), (118, 106, 68, 255),
            (140, 128, 88, 255)]][v]
    ellipse(img, 16, 27, 11, 4, SHADOW)
    for i in range(6):
        a = 2 * math.pi * i / 6
        blob(img, int(16 + math.cos(a) * 7), int(19 + math.sin(a) * 5),
             5.2, pal[1], rnd, wrap=False)
    ellipse(img, 16, 19, 9, 7, pal[1])
    for i in range(4):
        blob(img, 12 + i, 15 + (i % 2), 3.0, pal[2], rnd, wrap=False)
    for i in range(3):
        blob(img, 20 + i, 23 - (i % 2), 3.0, pal[0], rnd, wrap=False)
    for _ in range(8):
        put(img, 8 + rnd.i(17), 12 + rnd.i(13), pal[3], wrap=False)
    if v == 2:                           # espinhos / galhos secos
        for i in range(5):
            put(img, 8 + i * 4, 12 + (i % 3), P_DEAD[1], wrap=False)
    return outline(img)


def swamp_plant(v):
    """Planta de pantano 1x1: broto, junco, vitoria-regia."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    rnd = Rnd(880 + v * 29)
    green = [(58, 88, 46, 255), (84, 118, 58, 255), (112, 148, 76, 255), (144, 178, 100, 255)]
    if v == 0:                           # broto do lodo: moita de folhas lanceoladas
        ellipse(img, 16, 28, 9, 3, P_PUDDLE[0])
        for i, (x, h, lean) in enumerate(((9, 13, -1), (13, 18, 0), (17, 16, 0),
                                          (21, 11, 1), (15, 21, 0))):
            for k in range(h):
                y = 27 - k
                xx = x + (k * lean) // 4
                put(img, xx, y, green[2] if k > h - 5 else green[1], wrap=False)
                if k % 4 == 2:
                    put(img, xx + lean - 1, y, green[0], wrap=False)
            put(img, x + (h * lean) // 4, 27 - h, green[3], wrap=False)
    elif v == 1:                         # junco
        ellipse(img, 16, 28, 7, 3, P_PUDDLE[1])
        for i, x in enumerate((10, 14, 18, 22)):
            h = 12 + (i % 3) * 5
            for y in range(28, 28 - h, -1):
                put(img, x + ((28 - y) // 6), y, green[1 + ((y + i) % 2)], wrap=False)
            rect(img, x + h // 6 - 1, 28 - h - 3, x + h // 6 + 1, 28 - h, (92, 70, 40, 255))
    else:                                # vitoria-regia + flor
        ellipse(img, 16, 22, 12, 6, green[1])
        ellipse(img, 16, 21, 10, 5, green[2])
        rect(img, 16, 16, 17, 22, green[1])
        for i in range(4):
            put(img, 16 + i - 2, 21 - i // 2, green[3], wrap=False)
        blob(img, 20, 18, 2.4, (226, 214, 232, 255), rnd, wrap=False)
        put(img, 20, 18, (232, 208, 120, 255), wrap=False)
    return outline(img)


# ===================================================== PAREDES (32x64, 1x2)
def _wall_base(pal, seed, joint):
    """Alvenaria 32x64: fiadas de 8px com juntas defasadas; topo iluminado."""
    img = Image.new("RGBA", (CELL, 64), joint)
    rnd = Rnd(seed)
    for row in range(8):
        y0 = row * 8
        off = (row % 2) * 8
        for col in range(-1, 3):
            x0 = col * 16 + off
            c = pal[1 + rnd.i(len(pal) - 1)]
            for y in range(y0 + 1, y0 + 8):
                for x in range(x0 + 1, x0 + 16):
                    if 0 <= x < CELL:
                        k = 0
                        if y == y0 + 1:
                            k = 16
                        elif y >= y0 + 6:
                            k = -14
                        if x == x0 + 1:
                            k += 8
                        elif x >= x0 + 14:
                            k -= 10
                        img.putpixel((x, y), shade(c, k + (rnd.i(7) - 3)))
    # coroamento no topo
    rect(img, 0, 0, 31, 2, shade(pal[3], 10))
    rect(img, 0, 3, 31, 3, shade(pal[0], -10))
    return img


def stone_wall(kind):
    """kind: 'h' (leste-oeste), 'v' (norte-sul), 'c' (canto)."""
    pal = [(70, 68, 64, 255), (96, 94, 90, 255), (118, 116, 110, 255),
           (140, 138, 132, 255), (160, 158, 152, 255)]
    img = _wall_base(pal, {"h": 21, "v": 22, "c": 23}[kind], (46, 44, 42, 255))
    rnd = Rnd(99 + ord(kind))
    if kind == "v":                      # face lateral sombreada (parede N-S)
        for y in range(4, 64):
            for x in range(0, 6):
                img.putpixel((x, y), shade(img.getpixel((x, y)), -18))
    if kind == "c":                      # pilar de canto: pedra maior
        for y in range(6, 62):
            for x in range(6, 26):
                img.putpixel((x, y), shade(img.getpixel((x, y)), 8))
        rect(img, 6, 6, 25, 6, shade(pal[4], 12))
        rect(img, 6, 6, 6, 61, shade(pal[4], 6))
        rect(img, 25, 6, 25, 61, shade(pal[0], -8))
    for _ in range(18):                  # musgo
        x, y = rnd.i(CELL), 30 + rnd.i(34)
        put(img, x, y, (66, 84, 50, 255), wrap=False)
    return img


def wood_wall(kind):
    """Parede de madeira 32x64: tabuas verticais + travessas."""
    img = Image.new("RGBA", (CELL, 64), P_WOOD[1])
    rnd = Rnd(500 + sum(map(ord, kind)))
    for x in range(CELL):
        band = x // 6
        c = P_WOOD[1 + (band % 3)]
        for y in range(4, 64):
            k = 0
            if x % 6 == 0:
                k = -22
            elif x % 6 == 1:
                k = 12
            img.putpixel((x, y), shade(c, k + (rnd.i(5) - 2)))
    rect(img, 0, 0, 31, 3, shade(P_WOOD[4], 14))       # beiral
    rect(img, 0, 4, 31, 4, shade(P_WOOD[0], -12))
    for y in (18, 46):                                  # travessas
        rect(img, 0, y, 31, y + 2, P_WOOD[3])
        rect(img, 0, y + 3, 31, y + 3, P_WOOD[0])
    if kind == "v":
        for y in range(4, 64):
            for x in range(0, 5):
                img.putpixel((x, y), shade(img.getpixel((x, y)), -20))
    if kind == "c":
        rect(img, 12, 4, 19, 63, P_WOOD[4])
        rect(img, 12, 4, 12, 63, P_WOOD[0])
        rect(img, 19, 4, 19, 63, P_WOOD[0])
    if kind == "window":
        rect(img, 7, 20, 24, 40, (36, 40, 48, 255))     # vidro escuro
        for y in range(21, 40):
            for x in range(8, 24):
                if (x + y) % 7 < 2:
                    img.putpixel((x, y), (78, 96, 118, 255))
        rect(img, 6, 19, 25, 19, P_WOOD[4])             # moldura
        rect(img, 6, 41, 25, 41, P_WOOD[0])
        rect(img, 6, 19, 6, 41, P_WOOD[4])
        rect(img, 25, 19, 25, 41, P_WOOD[0])
        rect(img, 15, 20, 16, 40, P_WOOD[3])            # caixilho
        rect(img, 7, 29, 24, 30, P_WOOD[3])
    return img


def door(material, orient):
    """Porta fechada 32x64. material: 'stone' | 'wood'; orient: 'h' | 'v'."""
    if material == "stone":
        img = stone_wall("h" if orient == "h" else "v")
        frame = (86, 84, 80, 255)
        leaf = P_WOOD[1]
        hi, lo = P_WOOD[3], P_WOOD[0]
    else:
        img = wood_wall("h" if orient == "h" else "v")
        frame = P_WOOD[0]
        leaf = P_WOOD[2]
        hi, lo = P_WOOD[4], P_WOOD[0]
    x0, x1, y0, y1 = 6, 25, 22, 63
    rect(img, x0 - 1, y0 - 1, x1 + 1, y1, frame)
    rect(img, x0, y0, x1, y1, leaf)
    for x in range(x0, x1 + 1):          # tabuas da folha
        if (x - x0) % 5 == 0:
            for y in range(y0 + 1, y1):
                put(img, x, y, lo)
                put(img, x + 1, y, hi)
    rect(img, x0, y0, x1, y0 + 1, hi)    # verga
    rect(img, x0, y1 - 1, x1, y1, lo)
    for y in (30, 52):                   # ferragens
        rect(img, x0 + 1, y, x1 - 1, y + 1, (74, 72, 70, 255))
        put(img, x0 + 2, y, (128, 126, 122, 255))
    ellipse(img, 21, 44, 2, 2, (198, 172, 96, 255))     # macaneta
    put(img, 20, 43, (240, 220, 150, 255))
    put(img, 22, 45, (120, 100, 50, 255))
    return img


# ============================================== OUTROS OBJETOS DO MAPA
def torch(phase):
    """Tocha de parede acesa (2 fases — o id 2059 tem FLAG_ANIMATION)."""
    img = Image.new("RGBA", (CELL, 64), (0, 0, 0, 0))
    rnd = Rnd(1400 + phase)
    rect(img, 14, 40, 18, 62, P_BARK[2])                # suporte/cabo
    rect(img, 14, 40, 15, 62, P_BARK[1])
    rect(img, 12, 36, 20, 41, (70, 68, 64, 255))        # bracadeira
    rect(img, 12, 36, 20, 36, (108, 106, 100, 255))
    # chama: 3 tons, muda de forma entre as fases
    k = 0 if phase == 0 else 1
    ellipse(img, 16, 30 - k, 6, 9 + k, (198, 92, 24, 255))
    ellipse(img, 16, 31 - k, 4, 7, (238, 160, 40, 255))
    ellipse(img, 16 + (1 if k else -1), 32 - k, 2, 4, (252, 226, 140, 255))
    for _ in range(4):                                  # faiscas
        put(img, 13 + rnd.i(7), 16 + rnd.i(8), (252, 200, 90, 255), wrap=False)
    return img


def campfire(phase):
    """Fogueira (id 1428 tem FLAG_ANIMATION) — 2 fases, 1x1."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    rnd = Rnd(2400 + phase)
    ellipse(img, 16, 26, 12, 5, (58, 52, 46, 255))      # cinzas
    for i in range(5):                                  # lenha
        a = math.pi * (0.15 + i * 0.18)
        x0 = int(16 + math.cos(a) * 9)
        y0 = int(24 + math.sin(a) * 3)
        rect(img, min(x0, 16), y0, max(x0, 16), y0 + 1, P_BARK[2 - (i % 2)])
    k = phase
    ellipse(img, 16, 18 - k, 7, 8 + k, (196, 78, 20, 255))
    ellipse(img, 16, 20 - k, 5, 6, (238, 150, 36, 255))
    ellipse(img, 16 + (1 if k else -1), 21 - k, 2, 3, (252, 228, 150, 255))
    for _ in range(5):
        put(img, 12 + rnd.i(9), 4 + rnd.i(8), (250, 190, 80, 255), wrap=False)
    return outline(img, (30, 22, 16, 255))


def sign_post():
    """Placa de madeira 1x1."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    ellipse(img, 16, 29, 7, 3, SHADOW)
    rect(img, 15, 16, 17, 29, P_WOOD[1])
    rect(img, 15, 16, 15, 29, P_WOOD[0])
    rect(img, 5, 6, 27, 18, P_WOOD[2])                  # tabua
    rect(img, 5, 6, 27, 7, P_WOOD[4])
    rect(img, 5, 17, 27, 18, P_WOOD[0])
    rect(img, 5, 6, 6, 18, P_WOOD[3])
    rect(img, 26, 6, 27, 18, P_WOOD[0])
    for y in (10, 13):                                  # "texto"
        rect(img, 8, y, 23, y, (62, 44, 26, 255))
        rect(img, 20, y + 1, 23, y + 1, (62, 44, 26, 255))
    return outline(img)


def fence():
    """Cerca de madeira 1x1 (32x32) — bloqueia, tem altura."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    for x in (3, 15, 27):                               # mourões
        rect(img, x - 1, 6, x + 1, 29, P_WOOD[2])
        rect(img, x - 1, 6, x - 1, 29, P_WOOD[0])
        rect(img, x + 1, 6, x + 1, 29, P_WOOD[0])
        rect(img, x - 1, 6, x + 1, 6, P_WOOD[4])
    for y in (12, 22):                                  # travessas
        rect(img, 0, y, 31, y + 1, P_WOOD[3])
        rect(img, 0, y + 2, 31, y + 2, P_WOOD[0])
    return outline(img)


def depot_chest():
    """Bau de depot 1x1."""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    ellipse(img, 16, 29, 12, 3, SHADOW)
    rect(img, 3, 14, 28, 28, P_WOOD[2])                 # corpo
    rect(img, 3, 14, 28, 15, P_WOOD[4])
    rect(img, 3, 27, 28, 28, P_WOOD[0])
    for x in range(4, 28, 6):
        rect(img, x, 16, x, 27, P_WOOD[1])
    rect(img, 3, 7, 28, 14, P_WOOD[3])                  # tampa abaulada
    rect(img, 5, 5, 26, 7, P_WOOD[4])
    rect(img, 3, 13, 28, 14, (108, 96, 40, 255))        # cinta
    rect(img, 3, 8, 4, 27, (108, 96, 40, 255))
    rect(img, 27, 8, 28, 27, (108, 96, 40, 255))
    rect(img, 14, 15, 17, 20, (198, 172, 96, 255))      # fechadura
    put(img, 15, 17, (40, 34, 20, 255))
    put(img, 16, 17, (40, 34, 20, 255))
    return outline(img)


def training_dummy():
    """Boneco de treino 1x2 (32x64)."""
    img = Image.new("RGBA", (CELL, 64), (0, 0, 0, 0))
    ellipse(img, 16, 60, 10, 4, SHADOW)
    rect(img, 14, 40, 18, 60, P_WOOD[1])                # poste
    rect(img, 14, 40, 15, 60, P_WOOD[0])
    rect(img, 4, 30, 27, 33, P_WOOD[2])                 # bracos
    rect(img, 4, 30, 27, 30, P_WOOD[4])
    palha = [(150, 128, 72, 255), (176, 152, 88, 255), (198, 176, 108, 255)]
    ellipse(img, 16, 24, 10, 13, palha[0])              # corpo de palha
    ellipse(img, 15, 23, 8, 11, palha[1])
    ellipse(img, 13, 20, 5, 7, palha[2])
    for i in range(14):
        put(img, 7 + (i * 3) % 19, 13 + (i * 5) % 22, palha[2], wrap=False)
    for y in (18, 28):                                  # cordas
        rect(img, 7, y, 25, y, (96, 74, 44, 255))
    rect(img, 12, 14, 20, 15, (170, 60, 50, 255))       # alvo
    rect(img, 15, 12, 17, 18, (170, 60, 50, 255))
    return outline(img)


def tent():
    """Tenda 2x2 (64x64), ancorada no canto inferior direito."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    lona = [(120, 92, 62, 255), (146, 116, 80, 255), (170, 140, 100, 255),
            (194, 166, 124, 255)]
    ellipse(img, 34, 60, 26, 5, SHADOW)
    for y in range(26, 61):                             # corpo triangular
        t = (y - 26) / 34.0
        half = int(4 + t * 25)
        rect(img, 34 - half, y, 34 + half, y, lona[1])
        rect(img, 34 - half, y, 34 - half + 3, y, lona[2])
        rect(img, 34 + half - 4, y, 34 + half, y, lona[0])
    rect(img, 33, 20, 35, 30, P_WOOD[1])                # mastro
    put(img, 34, 19, (190, 60, 50, 255))
    for i in range(6):                                  # listras
        x = 34 - 24 + i * 10
        for y in range(34, 61):
            put(img, x + (y - 34) // 4, y, lona[3], wrap=False)
    for y in range(40, 61):                             # entrada escura
        half = int((y - 40) * 0.35) + 4
        rect(img, 34 - half, y, 34 + half, y, (58, 44, 32, 255))
    rect(img, 30, 40, 38, 41, lona[3])
    return outline(img)


# ------------------------------------------------------------------ escrita
def save(img, name):
    path = os.path.join(OUT_DIR, name + ".png")
    img.save(path)
    return name + ".png"


def build():
    os.makedirs(OUT_DIR, exist_ok=True)
    n = {}

    def bump(k, c=1):
        n[k] = n.get(k, 0) + c

    for v in range(8):
        save(grass(v), "grass_%d" % v)
        bump("grama")
    for v in range(3):                   # amostra de grass_shade (nao wired a nenhum id;
        save(grass_shade(v), "grass_shade_%d" % v)  # ver docs, secao "Terreno v3")
        bump("grama (sombra, amostra)")
    for v in range(3):
        save(dirt(v), "dirt_%d" % v)
        bump("terra")
    for v in range(5):
        save(cobble(v), "cobble_%d" % v)
        bump("cobblestone")
    save(stone_floor(), "stone_floor")
    bump("piso de pedra")
    save(wood_floor(), "wood_floor")
    bump("piso de madeira")
    for v in range(4):
        save(mud(v), "mud_%d" % v)
        bump("lama/pantano")
    for p in range(3):
        save(water(p), "water_%d" % p)
        bump("agua (fases)")
    for v in range(3):
        save(sand(v), "sand_%d" % v)
        bump("areia")

    for v in range(3):
        save(crackstone(v), "crackstone_%d" % v)
        bump("pedra rachada (ruinas)")
    for v in range(2):
        save(rock(v), "rock_%d" % v)
        bump("rocha (montanha)")
    save(snow(0), "snow_0")
    bump("neve (montanha)")
    save(ice(), "ice")
    bump("gelo (lago congelado)")
    for v in range(2):
        save(basalt(v), "basalt_%d" % v)
        bump("basalto (covil)")
    save(stone_wall_broken(), "stone_wall_broken")
    bump("parede de pedra quebrada (ruinas)")
    for k in ("h", "v", "c"):
        save(basalt_wall(k), "basalt_wall_%s" % k)
        bump("paredes de basalto (covil)")

    for k in ("fir", "sycamore", "willow", "beech", "pine"):
        save(tree(k), "tree_%s" % k)
        bump("arvores")
    for v in range(5):
        save(dead_tree(v), "dead_tree_%d" % v)
        bump("arvores mortas")
    for v in range(3):
        save(bush(v), "bush_%d" % v)
        bump("arbustos")
    for v in range(3):
        save(swamp_plant(v), "swamp_%d" % v)
        bump("plantas de pantano")

    for k in ("h", "v", "c"):
        save(stone_wall(k), "stone_wall_%s" % k)
        bump("paredes de pedra")
    for k in ("h", "v", "c", "window"):
        save(wood_wall(k), "wood_wall_%s" % k)
        bump("paredes de madeira")
    for mat in ("stone", "wood"):
        for o in ("h", "v"):
            save(door(mat, o), "door_%s_%s" % (mat, o))
            bump("portas")

    for p in range(2):
        save(torch(p), "torch_%d" % p)
        bump("tochas (fases)")
    for p in range(2):
        save(campfire(p), "campfire_%d" % p)
        bump("fogueira (fases)")
    save(sign_post(), "sign")
    bump("placa")
    save(fence(), "fence")
    bump("cerca")
    save(depot_chest(), "depot")
    bump("depot")
    save(training_dummy(), "dummy")
    bump("boneco de treino")
    save(tent(), "tent")
    bump("tenda")

    total = sum(n.values())
    print("terreno -> %s" % OUT_DIR)
    for k in sorted(n):
        print("  %-22s %d" % (k, n[k]))
    print("  %-22s %d PNGs" % ("TOTAL", total))
    return n


if __name__ == "__main__":
    build()
