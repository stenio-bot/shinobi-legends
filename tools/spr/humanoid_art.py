"""Pixel art procedural para os 12 humanoides looktypes 946-957 (bandidos,
ninjas, chefes, marionetes...), usada por `gen_humanoid_variants.py`.

Ate aqui esses looktypes eram uma COPIA do PNG importado (hue-shift, ver
git blame / docs/sistemas/arte-e-sprites.md secao "Criaturas procedurais"):
a mesma pose nas 4 direcoes e nas 3 fases de "andar" (a arte de origem nao
tinha direcao real nem ciclo de passada). Este modulo desenha um "boneco
Tibia" procedural do zero (mesma convencao de `art.py`/`animal_art.py`:
celula 32x32 RGBA, fundo transparente, chao em y~30) com:

- 4 direcoes DE VERDADE: Norte (costas, sem rosto), Sul (frente, com
  rosto), Leste (perfil, braco/perna da frente avançados), Oeste = espelho
  horizontal do Leste (mesma tecnica de `animal_art._finish`).
- 3 fases de andar (parado + 2 passos) com pernas/bracos deslocados 1-2 px
  (front/back: bounce vertical; perfil: tesoura horizontal).
- Adereco por classe (capuz, arco, mascara, chapeu, manto, aura/bracelete,
  chifres...) para reconhecer a classe de longe alem da cor.

Diferenca chave para `animal_art.py`: aqui `layers=1` (a cor final e
GRAVADA no pixel na hora de gerar, sem mascara de outfit — layers=1 nao
ganha mascara, ver FORMATO.md 3.5), entao a paleta de cada classe
(`class_palette`) computa os tons diretamente a partir do RGB "de lore" de
`tibia_colors.RAW` (o mesmo dicionario que `gen_humanoid_variants.py` ja
usava para o hue-shift) — nao existe camada de mascara para desenhar.

Nenhum pixel vem da Tibia, de NTO ou de outro jogo (ADR-002): tudo aqui e
geometria desenhada por codigo.
"""
from PIL import Image

import art
from art import new_image, _rect, TRANSPARENT, outline_inner

CELL = 32


def _c(v):
    return max(0, min(255, int(v)))


def shade(rgb, factor, alpha=255):
    """factor>0 clareia em direcao a branco, factor<0 escurece em direcao a
    preto (mesma cor, so muda o V do HSV de forma simples e barata)."""
    r, g, b = rgb[0], rgb[1], rgb[2]
    if factor >= 0:
        r = r + (255 - r) * factor
        g = g + (255 - g) * factor
        b = b + (255 - b) * factor
    else:
        r = r * (1 + factor)
        g = g * (1 + factor)
        b = b * (1 + factor)
    return (_c(r), _c(g), _c(b), alpha)


def desat(rgb, amount):
    """Puxa a cor em direcao ao cinza de mesmo brilho (0=sem mudanca,
    1=cinza puro) — usado para as correias/fivelas metalicas (accent)."""
    r, g, b = rgb[0], rgb[1], rgb[2]
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    return (_c(r + (gray - r) * amount), _c(g + (gray - g) * amount), _c(b + (gray - b) * amount), 255)


DEFAULT_SKIN = (224, 186, 150, 255)
EYE = (22, 20, 28, 255)

# tons NEUTROS (independentes da paleta da classe) para armas/objetos que
# precisam de contraste garantido contra QUALQUER cor de roupa — usar o
# "accent" (dessaturado da propria cor-alvo) as vezes fica proximo demais do
# tom da roupa (ex.: arco verde-oliva quase invisivel sobre o Arqueiro).
GEAR_WOOD = (96, 64, 34, 255)
GEAR_WOOD_DARK = (60, 40, 22, 255)
GEAR_METAL = (150, 152, 160, 255)
GEAR_METAL_DARK = (90, 92, 100, 255)


def class_palette(target_rgb, skin=None, eye=None, accent_desat=0.55):
    """Deriva a paleta de uma classe a partir da cor-alvo de lore (RGB livre,
    tibia_colors.RAW). `body` = tom principal do colete/roupa (a propria cor
    alvo), `legs` mais escuro, `feet`/`outline` quase pretos (tingidos),
    `head` levemente mais claro (bandana/cabelo), `accent` dessaturado
    (correias, fivelas, metal)."""
    body = shade(target_rgb, 0.0)
    legs = shade(target_rgb, -0.28)
    feet = shade(target_rgb, -0.50)
    head = shade(target_rgb, 0.22)
    outline = shade(target_rgb, -0.66)
    accent = desat(shade(target_rgb, -0.12), accent_desat)
    return {
        "body": body, "legs": legs, "feet": feet, "head": head,
        "outline": outline, "accent": accent,
        "skin": skin or DEFAULT_SKIN, "eye": eye or EYE,
    }


def _walk(phase, lead):
    """Deslocamento vertical (front/back) — mesma tabela de art._leg_offset."""
    table = (0, -1, 0, 1)
    if lead:
        table = (0, 1, 0, -1)
    return table[phase % 4]


def _stride(phase, lead):
    """Deslocamento horizontal (perfil) — tesoura: perna/braco da frente e de
    tras alternam +-2px por fase."""
    table = (0, 2, 0, -2)
    if lead:
        table = (0, -2, 0, 2)
    return table[phase % 4]


# --------------------------------------------------------------------------
def draw_body(direction, phase, palette, gear="none", big=False):
    """Boneco humanoide generico: cabeca (8-9px), tronco, bracos, pernas,
    3 tons + contorno. `direction`: 0=Norte(costas) 1=Leste 2=Sul(frente)
    3=Oeste (nunca desenhado direto — ver `render()` abaixo, que gera 1 e
    espelha)."""
    tiles = 2 if big else 1
    img = new_image(tiles, tiles)
    scale = 2 if big else 1

    def col(region):
        return palette.get(region, TRANSPARENT)

    def rect(x0, y0, x1, y1, region):
        c = col(region) if isinstance(region, str) else region
        if c[3] == 0:
            return
        _rect(img, x0 * scale, y0 * scale, (x1 + 1) * scale - 1, (y1 + 1) * scale - 1, c)

    front = direction == 2
    back = direction == 0
    side = direction == 1          # so Leste e desenhado; Oeste = espelho

    if not side:
        # ------------------------------------------------------ frente/costas
        l0, l1 = _walk(phase, 0), _walk(phase, 1)
        a0, a1 = _walk(phase, 1), _walk(phase, 0)   # bracos balancam oposto as pernas

        # sombra no chao
        rect(10, 30, 21, 30, "outline")

        # pernas
        rect(11, 22, 14, 27 + l0, "legs")
        rect(17, 22, 20, 27 + l1, "legs")
        rect(11, 28 + l0, 15, 29 + l0, "feet")
        rect(17, 28 + l1, 21, 29 + l1, "feet")

        # tronco
        rect(10, 12, 21, 21, "body")
        rect(10, 20, 21, 20, "accent")         # cinto: separa tronco/pernas na silhueta
        # bracos (pele), com leve balanco
        rect(7, 14 + a0, 9, 20 + a0, "skin")
        rect(22, 14 + a1, 24, 20 + a1, "skin")

        # cabeca (8-9 px)
        rect(11, 3, 20, 11, "skin")
        rect(11, 2, 20, 6, "head")            # cabelo/bandana cobre o topo

        if front:
            rect(13, 8, 14, 9, "eye")
            rect(17, 8, 18, 9, "eye")
            rect(14, 10, 17, 10, "outline")   # boca/sombra do queixo
        # costas: sem rosto (so cabelo/nuca) — nada a mais aqui

        _gear(rect, gear, direction, phase, front, back, side=False)
    else:
        # ---------------------------------------------------------- perfil (Leste)
        # perna/braco "da frente" (mais perto de x alto) avancam com a passada;
        # perna/braco "de tras" ficam mais perto do tronco.
        fwd = _stride(phase, True)     # perna/braco da frente
        bwd = _stride(phase, False)    # perna/braco de tras
        bob = 0 if phase == 0 else (1 if phase == 2 else 0)

        rect(11, 30, 22, 30, "outline")

        # perna de tras (mais parada, quase sob o tronco)
        rect(12 + bwd // 2, 22, 15 + bwd // 2, 27, "legs")
        rect(12 + bwd // 2, 28, 16 + bwd // 2, 29, "feet")
        # perna da frente (avanca/recua)
        rect(15 + fwd // 2, 22, 18 + fwd // 2, 27, "legs")
        rect(15 + fwd // 2, 28, 19 + fwd // 2, 29, "feet")

        # tronco (mais estreito, olhando p/ Leste)
        rect(11, 12 + bob, 20, 21 + bob, "body")
        rect(11, 20 + bob, 20, 20 + bob, "accent")   # cinto
        # braco de tras (sliver atras do tronco)
        rect(10, 14 + bob, 12, 19 + bob, "skin")
        # braco da frente (avanca com a passada, "um braco a frente")
        rect(19 + max(0, fwd), 13 + bob - max(0, -fwd) // 2, 23 + max(0, fwd), 19 + bob, "skin")

        # cabeca de perfil (nariz apontando p/ Leste)
        rect(12, 3 + bob, 19, 11 + bob, "skin")
        rect(12, 2 + bob, 19, 6 + bob, "head")
        rect(19, 6 + bob, 21, 8 + bob, "skin")     # nariz/queixo saliente
        rect(16, 8 + bob, 17, 9 + bob, "eye")

        _gear(rect, gear, direction, phase, False, False, side=True, fwd=fwd, bob=bob)

    return img


def _gear(rect, gear, direction, phase, front, back, side, fwd=0, bob=0):
    """Adereco por classe, desenhado por cima do corpo generico. So mexe em
    pixels ALEM da silhueta base (correias, chapeu, arma) — nunca redesenha
    cabeca/tronco, entao qualquer gear funciona com qualquer direcao."""
    if gear == "hood":
        # capuz bandido: cobre a cabeca inteira (inclusive testa), visivel
        # igual nas 4 direcoes — reforca "fora da lei" escondendo o rosto.
        if side:
            rect(12, 1 + bob, 20, 7 + bob, "head")
            rect(19, 4 + bob, 21, 6 + bob, "head")   # ponta do capuz p/ frente
        else:
            rect(10, 1, 21, 7, "head")
    elif gear == "bow":
        # arco arqueiro: silhueta em "(" (3 segmentos, bojo pro lado do corpo),
        # SEMPRE em madeira/corda neutra (nao a paleta da classe) pra garantir
        # contraste mesmo quando a roupa ja e proxima do tom de madeira/oliva
        # — encostado no braco (que fica por baixo) mas esticando pra dentro
        # do fundo transparente, onde o outline_inner fecha o contorno sozinho.
        if side:
            rect(25, 9 + bob, 26, 12 + bob, GEAR_WOOD)
            rect(24, 13 + bob, 25, 18 + bob, GEAR_WOOD)
            rect(25, 19 + bob, 26, 22 + bob, GEAR_WOOD)
            rect(26, 11 + bob, 26, 20 + bob, GEAR_WOOD_DARK)   # corda
        elif back:
            rect(8, 5, 9, 20, "accent")               # aljava a tiracolo
            rect(7, 4, 10, 6, "outline")
            rect(8, 3, 8, 5, "head")                   # pena de flecha
        elif front:
            rect(5, 9, 6, 12, GEAR_WOOD)
            rect(4, 13, 5, 18, GEAR_WOOD)
            rect(5, 19, 6, 22, GEAR_WOOD)
            rect(6, 11, 6, 20, GEAR_WOOD_DARK)          # corda
    elif gear == "spear_pauldron":
        # mercenario: ombreira de metal (poke acima do ombro, pega contorno
        # automatico) + lanca curta as costas/perfil, sempre em metal neutro.
        if side:
            rect(11, 10 + bob, 14, 12 + bob, GEAR_METAL)
            rect(22, 8 + bob, 23, 24 + bob, GEAR_METAL)   # haste da lanca
            rect(21, 6 + bob, 24, 8 + bob, GEAR_METAL_DARK)   # ponta
        else:
            rect(9, 10, 12, 13, GEAR_METAL)
            rect(19, 10, 22, 13, GEAR_METAL)
            if back:
                rect(6, 4, 7, 22, GEAR_METAL)
                rect(5, 3, 8, 4, GEAR_METAL_DARK)
    elif gear == "puppet_joints":
        # marionete de combate: juntas de madeira visiveis (circulos escuros
        # nos ombros/joelhos) e rosto em branco (sem boca), reforcando boneco.
        joints = [(9, 15), (23, 15), (12, 23), (19, 23)] if not side else [(11, 16 + bob), (16, 23)]
        for (jx, jy) in joints:
            rect(jx, jy, jx + 1, jy + 1, "outline")
        if front:
            rect(14, 10, 17, 10, "outline")  # boca-costura reta (sem expressao)
    elif gear == "mask":
        # batedor da nevoa: mascara/veu cobrindo metade inferior do rosto.
        if front:
            rect(11, 9, 20, 11, "accent")
        elif side:
            rect(12, 8 + bob, 19, 10 + bob, "accent")
        elif back:
            rect(11, 2, 20, 4, "accent")     # laco do veu amarrado atras
    elif gear == "scarf":
        # ninja renegado: cachecol/veu + 2 laminas curtas nas costas (cruzadas).
        if front:
            rect(11, 9, 20, 12, "accent")
        elif side:
            rect(12, 8 + bob, 19, 11 + bob, "accent")
        elif back:
            # 2 laminas curtas cruzadas nas costas (X), presas acima do cinto.
            rect(12, 13, 13, 20, GEAR_METAL)
            rect(18, 13, 19, 20, GEAR_METAL)
            rect(14, 12, 15, 13, GEAR_METAL_DARK)
            rect(16, 12, 17, 13, GEAR_METAL_DARK)
    elif gear == "hat":
        # guardiao da neblina: chapeu conico largo, ultrapassa a cabeca.
        if side:
            rect(9, 0 + bob, 22, 2 + bob, "accent")
            rect(11, -2 + bob, 20, 0 + bob, "accent")
        else:
            rect(8, 0, 23, 2, "accent")
            rect(11, -2, 20, 0, "accent")
            rect(9, 2, 22, 3, "outline")
    elif gear == "cloak":
        # chefe dos bandidos: manto longo pendurado dos ombros ate as pernas.
        if back:
            rect(8, 10, 23, 27, "accent")
            rect(9, 11, 22, 26, "legs")
        elif side:
            rect(9, 12 + bob, 12, 27, "accent")
        elif front:
            rect(8, 10, 10, 20, "accent")
            rect(21, 10, 23, 20, "accent")
    elif gear == "aura":
        # guerreiro espectral: bracelete brilhante + auréola de pontos claros
        # ao redor (sem alpha parcial no .spr — simulado com pontilhado).
        dots = [(6, 8), (25, 6), (4, 18), (27, 20), (8, 26), (23, 27), (16, 1)]
        for (dx, dy) in dots:
            rect(dx, dy, dx, dy, "head")
        if front or back:
            rect(8, 17, 9, 18, "head")
            rect(22, 17, 23, 18, "head")
        elif side:
            rect(20 + max(0, fwd), 17 + bob, 21 + max(0, fwd), 18 + bob, "head")
    elif gear == "curse_marks":
        # socio amaldicoado: olhos/marcas brilhantes vermelhas + tendril de
        # aura escura ao redor (pontilhado, mesma tecnica do espectral).
        dots = [(5, 10), (26, 9), (4, 22), (27, 24), (10, 27), (21, 27)]
        for (dx, dy) in dots:
            rect(dx, dy, dx, dy, "accent")
        if front:
            rect(13, 8, 14, 9, "accent")
            rect(17, 8, 18, 9, "accent")
    elif gear == "strings":
        # marionetista: barra de controle nas maos erguidas + fios finos.
        if front or back:
            rect(9, 10, 24, 11, "accent")
            rect(9, 11, 9, 14, "outline")
            rect(24, 11, 24, 14, "outline")
            rect(15, 3, 16, 11, "outline")
        elif side:
            rect(9, 9 + bob, 23, 10 + bob, "accent")
            rect(16, 3 + bob, 17, 9 + bob, "outline")
    elif gear == "horns":
        # oni glacial: chifres na cabeca + presas.
        if side:
            rect(17, -2 + bob, 19, 3 + bob, "accent")
        else:
            rect(11, -2, 13, 3, "accent")
            rect(18, -2, 20, 3, "accent")
            if front:
                rect(13, 10, 14, 11, "head")   # presa
                rect(17, 10, 18, 11, "head")


def render(direction, phase, palette, gear="none", big=False):
    """Gera a celula final para qualquer uma das 4 direcoes: desenha so
    Norte/Leste/Sul e espelha Leste -> Oeste (mesma tecnica de
    `animal_art._finish`), depois fecha o contorno externo com
    `outline_inner` (silhueta legivel, sem mudar o tamanho do sprite)."""
    src_dir = 1 if direction == 3 else direction
    img = draw_body(src_dir, phase, palette, gear=gear, big=big)
    if direction == 3:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    outline_inner(img, palette["outline"])
    return img
