#!/usr/bin/env python3
"""Folha de revisao ad-hoc (nao faz parte do pipeline): compoe os 6 looktypes
procedurais de animal (940-945) com as cores REAIS de data/tfs_mapping.json,
replicando o MULTIPLY que o cliente faz em tempo de render
(Creature::internalDraw, client-otc/src/client/creature.cpp):

    resultado = layer0_pixel                                   (default)
    resultado = layer0_pixel * (outfit_color / 255)   onde layer1 == mascara

so multiplica os pixels do layer0 cuja mascara (layer1, cor EXATA
vermelho/verde/azul/amarelo = body/legs/feet/head) bate; o resto (olho,
linha, sombra) fica exatamente como foi desenhado no layer0 (o cliente NUNCA
os recolore, ver overwriteMask em client-otc/src/framework/graphics/image.cpp).

Uso: .venv/bin/python tools/spr/review_animals.py
Saida: screenshots/animais_v2_review.png (zoom 3x, fundo verde, 6 animais x
4 direcoes x 3 fases de andar).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

import animal_art as AA
import art
import tibia_colors as TC

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CELL = 32
ZOOM = 3
DIRECTIONS = 4
PHASES = 3  # so o ciclo de andar (fase 1..3), pra bater com a missao (3 fases)
DIR_NAMES = ["Norte (costas)", "Leste (perfil)", "Sul (frente)", "Oeste (perfil)"]

DRAW = {
    "wolf": AA.draw_wolf,
    "deer": AA.draw_deer,
    "eagle": AA.draw_eagle,
    "snake": AA.draw_snake,
    "leech": AA.draw_leech,
    "toad": lambda d, p, l: art.draw_toad(d, p, l, {}),
}

# um monstro representativo por looktype (o que aparece no jogo de verdade
# nas areas early-game, ver data/tfs_mapping.json)
MONSTERS = [
    ("wolf", "Lobo (wolf)"),
    ("deer", "Cervo (forest_deer)"),
    ("eagle", "Aguia do Trovao (thunder_eagle)"),
    ("snake", "Cobra da Floresta (forest_snake)"),
    ("toad", "Sapo Gigante (giant_toad)"),
    ("leech", "Sanguessuga (leech)"),
]
MONSTER_ID_OF_KIND = {
    "wolf": "wolf", "deer": "forest_deer", "eagle": "thunder_eagle",
    "snake": "forest_snake", "toad": "giant_toad", "leech": "leech",
}


def composite(kind, direction, phase, colors):
    """Desenha layer0 (base) + layer1 (mascara) e aplica o MULTIPLY por
    regiao, exatamente como Creature::internalDraw."""
    draw = DRAW[kind]
    base = draw(direction, phase, 0)
    art.outline_inner(base)  # gen_animals.py aplica isso so no layer0
    mask = draw(direction, phase, 1)

    base = base.convert("RGBA")
    mask = mask.convert("RGBA")
    out = base.copy()
    bp = base.load()
    mp = mask.load()
    op = out.load()

    region_color = {
        art.MASK_HEAD: colors["head"],
        art.MASK_BODY: colors["body"],
        art.MASK_LEGS: colors["legs"],
        art.MASK_FEET: colors["feet"],
    }
    for y in range(CELL):
        for x in range(CELL):
            mc = mp[x, y]
            if mc[3] == 0:
                continue
            target = region_color.get(mc)
            if target is None:
                continue
            r, g, b, a = bp[x, y]
            if a == 0:
                continue
            tr, tg, tb = target
            op[x, y] = (
                (r * tr) // 255,
                (g * tg) // 255,
                (b * tb) // 255,
                a,
            )
    return out


def colors_for(monster_id, mapping):
    m = mapping["monsters"][monster_id]
    return {
        "head": TC.color_rgb(m["head"]),
        "body": TC.color_rgb(m["body"]),
        "legs": TC.color_rgb(m["legs"]),
        "feet": TC.color_rgb(m["feet"]),
    }


def main():
    with open(os.path.join(ROOT, "data", "tfs_mapping.json"), encoding="utf-8") as f:
        mapping = json.load(f)

    label_h = 16
    header_h = 14
    cell_px = CELL * ZOOM
    cols = DIRECTIONS * PHASES
    col_w = cell_px
    row_h = cell_px + label_h
    sheet_w = 200 + cols * col_w + 20
    sheet_h = header_h + len(MONSTERS) * (row_h + 20) + 20

    sheet = Image.new("RGB", (sheet_w, sheet_h), (46, 92, 46))  # fundo verde
    d = ImageDraw.Draw(sheet)

    # cabecalho de direcao
    for di, name in enumerate(DIR_NAMES):
        x = 200 + di * PHASES * col_w
        d.rectangle([x, 0, x + PHASES * col_w - 1, header_h - 1], fill=(30, 60, 30))
        d.text((x + 4, 2), name, fill=(255, 255, 255))

    y = header_h + 6
    for kind, label in MONSTERS:
        monster_id = MONSTER_ID_OF_KIND[kind]
        colors = colors_for(monster_id, mapping)
        d.text((4, y + row_h // 2 - 6), label, fill=(255, 255, 255))
        d.text((4, y + row_h // 2 + 4),
               "h=%s b=%s l=%s f=%s" % (colors["head"], colors["body"], colors["legs"], colors["feet"]),
               fill=(200, 230, 200))
        for di in range(DIRECTIONS):
            for pi in range(PHASES):
                phase = pi + 1  # 1..3 (ciclo de andar; pula o "parado"=0)
                img = composite(kind, di, phase, colors)
                img = img.resize((cell_px, cell_px), Image.NEAREST)
                x = 200 + (di * PHASES + pi) * col_w
                sheet.paste(img, (x, y), img)
                d.text((x + 2, y + cell_px + 1), "f%d" % phase, fill=(220, 220, 220))
        y += row_h + 20

    out_path = os.path.join(ROOT, "screenshots", "animais_v2_review.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    print("salvo:", out_path, sheet.size)


if __name__ == "__main__":
    main()
