"""Pixel art procedural para animais (lobo, cervo, aguia, cobra, sanguessuga),
usada por `gen_animals.py`.

Mesma convencao de `art.py`: celula 32x32 RGBA, fundo transparente, "chao" em
y=30. Camada 0 = tons CLAROS nas regioes colorizaveis (BASE, quase branco,
para o MULTIPLY do cliente funcionar), camada 1 = mascara exata (MASK_OF:
vermelho=body, verde=legs, azul=feet, amarelo=head) — diferente do sistema
antigo de "fera generica" (looktype 21 etc.) que hardcodava a cor final na
camada 0 e por isso nunca deixava `data/tfs_mapping.json` diferenciar
monstros que compartilham o looktype. Aqui a cor final vem SEMPRE do
head/body/legs/feet do monstro no tfs_mapping, multiplicado pelo cliente.

Direcao: 0=Norte (costas) 1=Leste 2=Sul (frente) 3=Oeste (espelho do Leste).
Fase: 0=parado (frame group idle), 1/2/3=ciclo de andar (frame group moving).

Nenhum pixel vem da Tibia, de NTO ou de qualquer outro jogo (ADR-002) — tudo
aqui e geometria desenhada por codigo.
"""
from PIL import Image

import art
from art import BASE, MASK_OF, TRANSPARENT, new_image, _rect

# sombra no chao: pixel opaco (o .spr 1098 nao tem alpha parcial, ver FORMATO.md
# §2 "RGB, nao RGBA" — uma sombra "translucida" teria que ser opaca mesmo).
SHADOW = (54, 66, 50, 255)


def _col(region, layer):
    if layer == 1:
        return MASK_OF.get(region, TRANSPARENT)
    if region == "shadow":
        return SHADOW
    if region == "eye":
        return BASE["eye"]
    if region == "line":
        return BASE["line"]
    return BASE.get(region, TRANSPARENT)


def _mk(direction):
    """True se a pose e vista de perfil (Leste/Oeste)."""
    return direction in (1, 3)


def _finish(img, direction):
    """Poses de perfil sao desenhadas olhando para Leste; Oeste e o espelho."""
    if direction == 3:
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def _walk(phase, lead):
    """Deslocamento vertical da perna (mesma tabela de art._leg_offset).
    `lead` alterna o par diagonal (0=dianteira-trocada, 1=oposta)."""
    table = (0, -1, 0, 1)
    if lead:
        table = (0, 1, 0, -1)
    return table[phase % 4]


# ------------------------------------------------------------------- lobo
def draw_wolf(direction, phase, layer):
    img = new_image()

    def rect(x0, y0, x1, y1, region):
        c = _col(region, layer)
        if c[3]:
            _rect(img, x0, y0, x1, y1, c)

    if _mk(direction):
        sw_a, sw_b = _walk(phase, 0), _walk(phase, 1)
        rect(6, 29, 25, 30, "shadow")
        # cauda (baixa, farta)
        rect(2, 15, 6, 19, "legs")
        rect(1, 12, 4, 16, "legs")
        # patas traseiras / dianteiras (perfil, olhando p/ Leste)
        rect(8, 19, 10, 24 + sw_a, "legs")
        rect(19, 19, 21, 24 + sw_b, "legs")
        rect(8, 25 + sw_a, 11, 27 + sw_a, "feet")
        rect(19, 25 + sw_b, 22, 27 + sw_b, "feet")
        # torso (baixo, alongado — silhueta de lobo, nao de urso)
        rect(6, 13, 23, 20, "body")
        rect(5, 12, 8, 15, "body")           # peito mais alto
        # cabeca/focinho apontando p/ frente
        rect(20, 7, 27, 15, "head")
        rect(25, 10, 29, 13, "head")         # focinho
        rect(28, 11, 29, 12, "line")         # nariz escuro
        # orelhas triangulares eretas
        rect(20, 4, 22, 7, "head")
        rect(24, 3, 26, 7, "head")
        rect(23, 10, 24, 11, "eye")           # olho (na cabeca, nao no torso)
    else:
        # Quadrupede visto de frente/costas: cabeca grande no topo (com
        # orelhas), corpo CURTO e LARGO (nunca uma torre alta = silhueta de
        # gente em pe), 2 patas visiveis por baixo. Frente: peito largo
        # afunilando pra baixo (so as patas dianteiras aparecem, o corpo
        # "recua" atras). Costas: dorso estreito no pescoco alargando pras
        # ancas, cauda baixa entre as 2 patas traseiras (mais afastadas que
        # as dianteiras — quadril e mais largo que ombro).
        front = direction == 2
        sw_a, sw_b = _walk(phase, 0), _walk(phase, 1)
        rect(9, 29, 22, 30, "shadow")
        if front:
            rect(8, 16, 23, 22, "body")          # peito largo (ombros)
            rect(11, 21, 20, 25, "body")          # afunila pro corpo curto atras
            rect(12, 22, 14, 27 + sw_a, "legs")    # pata dianteira esquerda
            rect(17, 22, 19, 27 + sw_b, "legs")    # pata dianteira direita
            rect(11, 26 + sw_a, 15, 28 + sw_a, "feet")
            rect(16, 26 + sw_b, 20, 28 + sw_b, "feet")
        else:
            rect(11, 16, 20, 19, "body")          # dorso estreito perto do pescoco
            rect(7, 19, 24, 24, "body")           # ancas largas (quadril > ombro)
            # cauda na cor do CORPO (nao das patas): se fosse "legs" ficaria
            # identica as 2 patas traseiras e as 3 formas grudariam num so
            # blob marrom sem contorno interno (mascara nao desenha borda
            # entre regioes vizinhas, so no limite com o fundo transparente).
            rect(14, 20, 18, 27, "body")          # cauda baixa, entre as patas
            rect(9, 22, 12, 27 + sw_a, "legs")     # pata traseira esquerda
            rect(19, 22, 22, 27 + sw_b, "legs")    # pata traseira direita
            rect(8, 26 + sw_a, 13, 28 + sw_a, "feet")
            rect(18, 26 + sw_b, 23, 28 + sw_b, "feet")
        rect(10, 5, 22, 16, "head")               # cabeca grande
        rect(9, 2, 13, 7, "head")                 # orelha esquerda
        rect(19, 2, 23, 7, "head")                # orelha direita
        if front:
            rect(13, 11, 14, 12, "eye")
            rect(18, 11, 19, 12, "eye")
            rect(14, 13, 17, 14, "line")          # focinho escuro
    return img


# ------------------------------------------------------------------ cervo
def draw_deer(direction, phase, layer):
    img = new_image()

    def rect(x0, y0, x1, y1, region):
        c = _col(region, layer)
        if c[3]:
            _rect(img, x0, y0, x1, y1, c)

    if _mk(direction):
        sw_a, sw_b = _walk(phase, 0), _walk(phase, 1)
        rect(7, 29, 24, 30, "shadow")
        rect(3, 16, 6, 20, "legs")           # rabo curto
        # pernas finas (cervo e mais esguio que o lobo)
        rect(9, 19, 10, 25 + sw_a, "legs")
        rect(20, 19, 21, 25 + sw_b, "legs")
        rect(8, 26 + sw_a, 11, 28 + sw_a, "feet")
        rect(19, 26 + sw_b, 22, 28 + sw_b, "feet")
        # torso esguio, pescoco alto
        rect(8, 14, 22, 19, "body")
        rect(19, 7, 24, 15, "body")          # pescoco
        rect(22, 6, 28, 12, "head")
        rect(26, 8, 29, 10, "line")          # focinho
        # chifres (galhos simples, 2 pontas)
        rect(23, 1, 24, 6, "legs")
        rect(21, 1, 22, 4, "legs")
        rect(26, 1, 27, 6, "legs")
        rect(28, 1, 29, 4, "legs")
        rect(25, 9, 26, 10, "eye")            # olho (na cabeca)
    else:
        # Mesma logica de quadrupede do lobo (corpo curto/largo, nunca uma
        # torre): pernas do cervo mais finas ("cervo e mais esguio"), chifres
        # pequenos SO de frente (mission: cauda curta de costas).
        front = direction == 2
        sw_a, sw_b = _walk(phase, 0), _walk(phase, 1)
        rect(10, 29, 21, 30, "shadow")
        if front:
            rect(9, 17, 22, 22, "body")           # peito
            rect(12, 21, 19, 25, "body")          # afunila pro corpo curto atras
            rect(13, 23, 14, 28 + sw_a, "legs")    # pata dianteira esquerda (fina)
            rect(17, 23, 18, 28 + sw_b, "legs")    # pata dianteira direita (fina)
            rect(12, 27 + sw_a, 15, 29 + sw_a, "feet")
            rect(16, 27 + sw_b, 19, 29 + sw_b, "feet")
            # chifres pequenos (2 pontas cada, so aparecem de frente)
            rect(11, 1, 12, 5, "legs")
            rect(9, 1, 10, 3, "legs")
            rect(20, 1, 21, 5, "legs")
            rect(22, 1, 23, 3, "legs")
        else:
            rect(12, 16, 19, 19, "body")          # dorso estreito perto do pescoco
            rect(8, 19, 23, 24, "body")           # ancas largas
            rect(14, 21, 17, 25, "legs")          # cauda CURTA (so um coto, nao desce ate os pes)
            rect(10, 22, 11, 27 + sw_a, "legs")    # pata traseira esquerda (fina)
            rect(20, 22, 21, 27 + sw_b, "legs")    # pata traseira direita (fina)
            rect(9, 26 + sw_a, 12, 28 + sw_a, "feet")
            rect(19, 26 + sw_b, 22, 28 + sw_b, "feet")
        rect(12, 7, 19, 16, "head")
        rect(11, 5, 13, 8, "head")                # orelha esquerda
        rect(18, 5, 20, 8, "head")                # orelha direita
        if front:
            rect(13, 10, 14, 11, "eye")           # olho esquerdo (gap p/ nao grudar no direito)
            rect(17, 10, 18, 11, "eye")           # olho direito
            rect(15, 12, 16, 13, "line")
    return img


# ------------------------------------------------------------------ aguia
def draw_eagle(direction, phase, layer):
    """1x1, sempre em voo — asas abertas, sombra deslocada no chao."""
    img = new_image()

    def rect(x0, y0, x1, y1, region):
        c = _col(region, layer)
        if c[3]:
            _rect(img, x0, y0, x1, y1, c)

    flap = (0, -3, -5, -3)[phase % 4]      # bate-asas substitui o andar (asa sobe e desce)
    bob = (0, -1, -1, 0)[phase % 4]        # corpo sobe/desce levemente
    rect(11, 27, 20, 29, "shadow")          # sombra no chao, deslocada (ave paira)
    if _mk(direction):
        # perfil: corpo horizontal + cabeca/bico a frente, asa em "degraus" varrida
        # para tras e pra cima (leque classico de ave planando vista de lado).
        y = 16 + bob
        rect(9, y, 20, y + 3, "body")
        rect(18, y - 2, 24, y + 1, "head")
        rect(23, y - 1, 26, y, "line")          # bico
        rect(3, y - 1, 8, y + 2, "legs")        # cauda em leque (atras)
        # asa varrida: 3 segmentos que sobem e se afastam do corpo (raiz -> ponta)
        wy = y - 2 + flap
        rect(6, wy, 14, wy + 3, "body")
        rect(2, wy - 3, 9, wy, "body")
        rect(0, wy - 6 if flap <= -4 else wy - 5, 5, (wy - 3) if flap <= -4 else wy - 2, "body")
        rect(12, y + 4, 15, y + 7, "feet")      # garras recolhidas sob o corpo
        rect(19, y - 1, 20, y, "eye")
    else:
        front = direction == 2
        rect(9, 15 + bob, 22, 20 + bob, "body")
        rect(12, 11 + bob, 19, 17 + bob, "head")
        rect(2, 12 + bob - flap, 10, 15 + bob - flap, "legs")   # asa esquerda
        rect(21, 12 + bob - flap, 29, 15 + bob - flap, "legs")  # asa direita
        rect(2, 16 + bob + flap, 10, 18 + bob + flap, "legs")
        rect(21, 16 + bob + flap, 29, 18 + bob + flap, "legs")
        rect(13, 21 + bob, 18, 24 + bob, "feet")
        if front:
            rect(13, 13 + bob, 14, 14 + bob, "eye")
            rect(17, 13 + bob, 18, 14 + bob, "eye")
            rect(14, 15 + bob, 17, 16 + bob, "line")
    return img


# ------------------------------------------------------------------- cobra
def draw_snake(direction, phase, layer):
    """Enrolada parada (fase 0), rastejando nas fases de andar. Layers=2:
    varios monstros (Cobra/Serpente Menor/Serpente de Magma) compartilham
    este looktype e diferem so pela cor em data/tfs_mapping.json."""
    import math
    img = new_image()

    def put(x, y, region, r=0):
        c = _col(region, layer)
        if not c[3]:
            return
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if abs(dx) + abs(dy) <= r:
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 32 and 0 <= yy < 32:
                        img.putpixel((xx, yy), c)

    # sombra fixa
    for x in range(9, 23):
        put(x, 29, "shadow")

    if phase == 0:
        # enrolada: espiral fechada, cabeca no meio olhando p/ direcao
        cx, cy = 16, 19
        for t in range(0, 620, 4):
            ang = t / 100.0
            rad = 2 + ang * 1.6
            x = int(cx + rad * math.cos(ang))
            y = int(cy * 0.6 + rad * math.sin(ang) * 0.6) + 8
            put(x, y, "body", r=1)
        hx, hy = cx + (6 if direction != 3 else -6), cy - 2
        put(hx, hy, "head", r=2)
        if direction == 2:
            put(hx - 1, hy - 1, "eye")
            put(hx + 1, hy - 1, "eye")
    else:
        off = phase * 3
        rightward = direction != 3
        for i in range(24):
            x = 3 + i if rightward else 29 - i
            y = int(19 + 6 * math.sin((i + off) * 0.5))
            put(x, y, "body", r=2)
        hx = 27 if rightward else 4
        hy = int(19 + 6 * math.sin(((hx - 3 if rightward else 29 - hx) + off) * 0.5))
        put(hx, hy, "head", r=2)
        if direction == 2 or direction == 0:
            put(hx - 1, hy - 1, "eye")
            put(hx + 1, hy - 1, "eye")
    return img


# --------------------------------------------------------------- sanguessuga
def draw_leech(direction, phase, layer):
    """Verme fino ondulando, ventosa nas duas pontas — silhueta bem diferente
    da cobra (mais fina, sem cabeca triangular) e do "blob" antigo."""
    import math
    img = new_image()

    def put(x, y, region, r=0):
        c = _col(region, layer)
        if not c[3]:
            return
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r + 1:
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 32 and 0 <= yy < 32:
                        img.putpixel((xx, yy), c)

    for x in range(11, 21):
        put(x, 29, "shadow")

    off = phase * 2.2
    rightward = direction != 3
    length = 18
    pts = []
    for i in range(length):
        x = 7 + i if rightward else 25 - i
        y = int(18 + 3.5 * math.sin((i + off) * 0.7))
        pts.append((x, y))
    for i, (x, y) in enumerate(pts):
        r = 2 if 2 < i < length - 3 else 1
        region = "feet" if i in (0, length - 1) else ("head" if i < 3 else "body")
        put(x, y, region, r=r)
        if layer == 0 and i % 4 == 0:
            put(x, y, "line")            # aneis do corpo (so decoracao, layer0)
    return img
