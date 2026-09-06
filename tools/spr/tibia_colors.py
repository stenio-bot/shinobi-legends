"""Paleta de cores de outfit da Tibia (indice 0..132) e busca do indice mais
proximo de um RGB alvo.

Formula extraida de `client-otc/src/client/outfit.cpp` (`Outfit::getColor`),
HSI_H_STEPS=19, HSI_SI_VALUES=7 (19*7=133 indices). Reimplementada aqui em
Python para escolher cores de outfit (head/body/legs/feet) coerentes com o
lore, sem precisar adivinhar indices na mao.
"""
import math

HSI_H_STEPS = 19
HSI_SI_VALUES = 7

_SI_TABLE = {
    0: (0.25, 1.00),
    1: (0.25, 0.75),
    2: (0.50, 0.75),
    3: (0.667, 0.75),
    4: (1.00, 1.00),
    5: (1.00, 0.75),
    6: (1.00, 0.50),
}


def color_rgb(color):
    """Replica Outfit::getColor: indice 0..132 -> (r,g,b) 0..255."""
    if color >= HSI_H_STEPS * HSI_SI_VALUES:
        color = 0
    if color % HSI_H_STEPS != 0:
        loc1 = (color % HSI_H_STEPS) / 18.0
        loc2, loc3 = _SI_TABLE[color // HSI_H_STEPS]
    else:
        loc1 = 0.0
        loc2 = 0.0
        loc3 = 1 - float(color) / HSI_H_STEPS / HSI_SI_VALUES

    if loc3 == 0:
        return (0, 0, 0)
    if loc2 == 0:
        v = int(loc3 * 255)
        return (v, v, v)

    if loc1 < 1 / 6.0:
        red = loc3
        blue = loc3 * (1 - loc2)
        green = blue + (loc3 - blue) * 6 * loc1
    elif loc1 < 2 / 6.0:
        green = loc3
        blue = loc3 * (1 - loc2)
        red = green - (loc3 - blue) * (6 * loc1 - 1)
    elif loc1 < 3 / 6.0:
        green = loc3
        red = loc3 * (1 - loc2)
        blue = red + (loc3 - red) * (6 * loc1 - 2)
    elif loc1 < 4 / 6.0:
        blue = loc3
        red = loc3 * (1 - loc2)
        green = blue - (loc3 - red) * (6 * loc1 - 3)
    elif loc1 < 5 / 6.0:
        blue = loc3
        green = loc3 * (1 - loc2)
        red = green + (loc3 - green) * (6 * loc1 - 4)
    else:
        red = loc3
        green = loc3 * (1 - loc2)
        blue = red - (loc3 - green) * (6 * loc1 - 5)
    return (int(red * 255), int(green * 255), int(blue * 255))


_ALL = [color_rgb(i) for i in range(HSI_H_STEPS * HSI_SI_VALUES)]


def nearest(rgb):
    """Indice 0..132 cujo RGB fica mais perto do alvo (distancia euclidiana)."""
    r, g, b = rgb[:3]
    best_i, best_d = 0, 1e18
    for i, (cr, cg, cb) in enumerate(_ALL):
        d = (cr - r) ** 2 + (cg - g) ** 2 + (cb - b) ** 2
        if d < best_d:
            best_d, best_i = d, i
    return best_i


def nearest_hue(h, s=0.8, v=0.8):
    """Atalho: converte HSV alvo pra RGB e acha o indice Tibia mais proximo."""
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return nearest((r * 255, g * 255, b * 255))


# Paleta nomeada de conveniencia, pensada para o lore dos monstros desta
# missao. Nao e exaustiva -- so o que os grupos precisam.
#
# RAW guarda o RGB "desejado" tal qual pensado pro lore (livre, qualquer cor).
# NAMED quantiza RAW pro indice 0..132 da paleta REAL de outfit da Tibia (so
# 133 cores no total — client-otc/src/client/outfit.cpp) e serve pros campos
# head/body/legs/feet de data/tfs_mapping.json (protocolo manda indice, nao
# RGB; so faz efeito em looktype layers=2/mascara — ver FORMATO.md §3.5).
# Quantizar perde informacao (a paleta e BEM esparsa: so 7 combinacoes de
# saturacao/intensidade por matiz, e varias cores "abafadas" tipo oliva/navy/
# ardosia caem mais perto de uma entrada CINZA do que de qualquer entrada
# colorida — e assim mesmo no jogo de verdade, nao e bug). Por isso
# tools/spr/gen_humanoid_variants.py (recolor de PIXEL, sem mascara de
# protocolo) usa RAW diretamente, nunca NAMED/color_rgb(NAMED[...]) — do
# contrario o alvo do hue-shift vira cinza em vez da cor pretendida.
RAW = {
    "brown_bandit": (132, 92, 54),
    "olive_archer": (100, 112, 56),
    "navy_mercenary": (46, 58, 96),
    "wood_puppet": (176, 150, 104),
    "cream_puppet": (214, 198, 168),
    "rogue_slate": (70, 66, 84),
    "chief_red": (150, 40, 36),
    "chief_black": (40, 38, 44),
    "puppeteer_violet": (104, 60, 132),
    "spectral_pale_purple": (150, 130, 176),
    "spectral_ghost_white": (208, 202, 214),
    "curse_partner_purple": (78, 46, 96),
    "curse_partner_armor": (60, 58, 68),
    "oni_icy_blue": (150, 196, 214),
    "oni_icy_white": (222, 236, 240),
    "wolf_gray_brown": (110, 96, 84),
    "wolf_dark": (70, 60, 54),
    "deer_tan": (176, 140, 96),
    "deer_cream": (214, 196, 164),
    "eagle_slate": (90, 100, 116),
    "eagle_gold": (196, 156, 64),
    "snake_forest_green": (70, 128, 64),
    "snake_venom_green": (120, 170, 40),
    "snake_magma_red": (190, 70, 40),
    "toad_swamp_green": (90, 140, 76),
    "leech_dark_purple": (90, 50, 90),
    # adicionados na continuacao da missao de criaturas procedurais (variantes
    # de paleta para looktypes humanoides importados compartilhados —
    # tools/spr/gen_humanoid_variants.py):
    "mist_scout_teal": (70, 108, 112),
    "mist_guardian_steel": (92, 108, 128),
    "curse_partner_red": (150, 44, 40),
}

NAMED = {name: nearest(rgb) for name, rgb in RAW.items()}

# Correcao manual: `nearest()` euclidiano puro cai numa entrada CINZA (indice
# multiplo de 19) pra varios RAW pouco saturados (marrom-acinzentado do lobo,
# ardosia da aguia, verde-pantano do sapo/cobra, roxo escuro da sanguessuga) —
# a distancia RGB pra um cinza medio fica menor que pra qualquer entrada colorida
# disponivel nos 7 combos de saturacao/intensidade da paleta real. Resultado:
# lobo/cobra-da-floresta/sapo saindo LITERALMENTE cinza puro (e o mesmo cinza
# uns dos outros!) no jogo. Estes indices foram escolhidos a mao direto da
# tabela de 114 cores coloridas (ver `python3 tibia_colors.py` + filtro
# `idx % 19 != 0`), priorizando ficar na familia de matiz certa em vez do
# vizinho euclidiano mais proximo:
NAMED.update({
    # BUG real corrigido nesta missao (redesenho de poses N/S do lobo/cervo,
    # ver docs/sistemas/arte-e-sprites.md): idx=20 -> (191,159,143) e um BEGE
    # de pele quente (mesma familia do BASE["skin"] de art.py!), nao um
    # "cinza-marrom". Com layers=2 (base quase branca * MULTIPLY), a cabeca e
    # o corpo inteiros do lobo saiam literalmente cor de pele — lido como um
    # boneco em pe, nao um lobo. Trocado para o idx=76 (109,109,109), cinza
    # neutro medio-escuro (a "correcao manual" original evitou o cinza puro
    # da distancia euclidiana, mas exagerou pro lado claro/rosado; 76 fica no
    # meio: cinza de verdade, sem ficar bege nem preto puro).
    "wolf_gray_brown": 76,      # (109,109,109) cinza medio-escuro
    "wolf_dark": 115,           # (127,42,0) marrom escuro
    "eagle_slate": 30,          # (143,159,191) azul-ardosia claro
    "toad_swamp_green": 43,     # (127,191,95) verde medio
    "snake_forest_green": 63,   # (63,191,63) verde puro (distinto do venom_green)
    "leech_dark_purple": 128,   # (85,0,127) roxo escuro de verdade
})


if __name__ == "__main__":
    for name, idx in sorted(NAMED.items()):
        print("%-24s idx=%3d rgb=%s" % (name, idx, color_rgb(idx)))
