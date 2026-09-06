#!/usr/bin/env python3
"""Folha de revisao ad-hoc (nao faz parte do pipeline): compoe os 9
personagens jogaveis (900-909, exceto 906) com as cores DEFAULT de
data/tfs_mapping.json.characters, replicando o MULTIPLY que o cliente faz em
tempo de render (Creature::internalDraw / Image::overwriteMask — mesma tecnica
de `review_animals.py::composite`, mas para `player_art.py`).

Uso: .venv/bin/python tools/spr/review_players.py
Saida: screenshots/players_v1_review.png (zoom 3x, fundo verde, 9 personagens
x 4 direcoes x 4 fases [parado + 3 de andar]).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

import art
import player_art as PA
import tibia_colors as TC

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CELL = 32
ZOOM = 3
DIRECTIONS = 4
PHASES = 4  # 0=parado, 1..3=andar
DIR_NAMES = ["Norte (costas)", "Leste (perfil)", "Sul (frente)", "Oeste (perfil)"]

GEAR_NOTES = {
    "genin_laranja": "cabelo espetado + bandana azul + jaqueta de gola alta",
    "genin_uchiha": "franja lateral + colarinho alto com fecho + faixa no braço",
    "kunoichi_rosa": "cabelo médio + abertura no colo + luvas vermelhas",
    "herdeira_hyuga": "cabelo longo + casaco alargado + olhos claros",
    "ninja_verde": "corte de tigela + bandagens punho/tornozelo",
    "kunoichi_armas": "coques duplos + colarinho chinês + pergaminho nas costas",
    "sabio_loiro": "cabelo espetado selvagem + pergaminho enorme nas costas",
    "sabio_cerimonial": "chapéu cônico de palha + selos no peito",
    "ninja_abelha": "óculos escuros + 2 lâminas cruzadas nas costas",
}


def composite(char_id, direction, phase, colors, fixed):
    base = PA.render(direction, phase, 0, char_id, fixed)
    mask = PA.render(direction, phase, 1, char_id, fixed)
    base = base.convert("RGBA")
    mask = mask.convert("RGBA")
    out = base.copy()
    bp, mp, op = base.load(), mask.load(), out.load()
    region_color = {
        art.MASK_HEAD: colors["head"], art.MASK_BODY: colors["body"],
        art.MASK_LEGS: colors["legs"], art.MASK_FEET: colors["feet"],
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
            op[x, y] = ((r * tr) // 255, (g * tg) // 255, (b * tb) // 255, a)
    return out


def colors_for(char_id, mapping):
    c = mapping["characters"][char_id]
    return {k: TC.color_rgb(c[k]) for k in ("head", "body", "legs", "feet")}


def main():
    with open(os.path.join(ROOT, "data", "tfs_mapping.json"), encoding="utf-8") as f:
        mapping = json.load(f)
    with open(os.path.join(ROOT, "data", "characters.json"), encoding="utf-8") as f:
        chars = json.load(f)
    chars = [c for c in chars if int(c["looktype"]) != 906]
    chars.sort(key=lambda c: c["looktype"])

    label_w = 260
    label_h = 16
    header_h = 14
    cell_px = CELL * ZOOM
    cols = DIRECTIONS * PHASES
    col_w = cell_px
    row_h = cell_px + label_h
    sheet_w = label_w + cols * col_w + 20
    sheet_h = header_h + len(chars) * (row_h + 22) + 20

    sheet = Image.new("RGB", (sheet_w, sheet_h), (46, 92, 46))
    d = ImageDraw.Draw(sheet)

    for di, name in enumerate(DIR_NAMES):
        x = label_w + di * PHASES * col_w
        d.rectangle([x, 0, x + PHASES * col_w - 1, header_h - 1], fill=(30, 60, 30))
        d.text((x + 4, 2), name, fill=(255, 255, 255))

    y = header_h + 6
    for c in chars:
        char_id = c["id"]
        colors = colors_for(char_id, mapping)
        fixed = {"eye": PA.PALE_EYE} if char_id == "herdeira_hyuga" else {}
        d.text((4, y + 2), "%d %s" % (c["looktype"], c["name"]), fill=(255, 255, 255))
        d.text((4, y + 14), GEAR_NOTES.get(char_id, ""), fill=(210, 235, 210))
        d.text((4, y + row_h - 14),
               "h=%s b=%s l=%s f=%s" % (colors["head"], colors["body"], colors["legs"], colors["feet"]),
               fill=(200, 230, 200))
        for di in range(DIRECTIONS):
            for pi in range(PHASES):
                img = composite(char_id, di, pi, colors, fixed)
                img = img.resize((cell_px, cell_px), Image.NEAREST)
                x = label_w + (di * PHASES + pi) * col_w
                sheet.paste(img, (x, y), img)
                label = "parado" if pi == 0 else "f%d" % pi
                d.text((x + 2, y + cell_px + 1), label, fill=(220, 220, 220))
        y += row_h + 22

    out_path = os.path.join(ROOT, "screenshots", "players_v1_review.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    print("salvo:", out_path, sheet.size)


if __name__ == "__main__":
    main()
