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


# Paleta nomeada de conveniencia (indice Tibia), pensada para o lore dos
# monstros desta missao. Nao e exaustiva -- so o que os grupos precisam.
NAMED = {
    "brown_bandit": nearest((132, 92, 54)),
    "olive_archer": nearest((100, 112, 56)),
    "navy_mercenary": nearest((46, 58, 96)),
    "wood_puppet": nearest((176, 150, 104)),
    "cream_puppet": nearest((214, 198, 168)),
    "rogue_slate": nearest((70, 66, 84)),
    "chief_red": nearest((150, 40, 36)),
    "chief_black": nearest((40, 38, 44)),
    "puppeteer_violet": nearest((104, 60, 132)),
    "spectral_pale_purple": nearest((150, 130, 176)),
    "spectral_ghost_white": nearest((208, 202, 214)),
    "curse_partner_purple": nearest((78, 46, 96)),
    "curse_partner_armor": nearest((60, 58, 68)),
    "oni_icy_blue": nearest((150, 196, 214)),
    "oni_icy_white": nearest((222, 236, 240)),
    "wolf_gray_brown": nearest((110, 96, 84)),
    "wolf_dark": nearest((70, 60, 54)),
    "deer_tan": nearest((176, 140, 96)),
    "deer_cream": nearest((214, 196, 164)),
    "eagle_slate": nearest((90, 100, 116)),
    "eagle_gold": nearest((196, 156, 64)),
    "snake_forest_green": nearest((70, 128, 64)),
    "snake_venom_green": nearest((120, 170, 40)),
    "snake_magma_red": nearest((190, 70, 40)),
    "toad_swamp_green": nearest((90, 140, 76)),
    "leech_dark_purple": nearest((90, 50, 90)),
}


if __name__ == "__main__":
    for name, idx in sorted(NAMED.items()):
        print("%-24s idx=%3d rgb=%s" % (name, idx, color_rgb(idx)))
