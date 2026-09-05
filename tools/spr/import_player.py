#!/usr/bin/env python3
"""Aplica ao outfit do JOGADOR (looktype 128) as mesmas duas tecnicas usadas em
`import_mugen.py`: vista de COSTAS **sintetizada** (o material de
`assets-src/import/player/` tambem nao tem nenhuma, so aproximacoes) e 4a fase
de andar (o material so dava 3 quadros por direcao).

Le os quadros ja identificados em `player_frames.json` (a triagem manual
documentada), sintetiza costas + 4a fase com `char_synth`, grava os PNGs em
`assets-src/import/player/_synth/` e REESCREVE `overrides/30_player.json`
(mantendo a entrada `naruto_attack`/898 intocada — ela ja tem 4 fases e nao e um
ciclo de andar). O pipeline de nitidez (downscale por area + realce + contorno
1px) e automatico: e o novo padrao de `imports.fit_uniform`, usado por
`creature_dirs` para TODA criatura com `directions` — nao precisa de nada aqui.

Uso::

    .venv/bin/python tools/spr/import_player.py
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import char_synth as CS  # noqa: E402

SRC = "assets-src/import/player"
SYNTH_DIR = "assets-src/import/player/_synth"
OVERRIDE = "assets-src/sprites/overrides/30_player.json"
FRAMES_DOC = "assets-src/sprites/player_frames.json"

EAST_IDLE = 80
EAST_WALK = [84, 83, 75]          # contato, passagem, contato oposto (reais)
SOUTH_IDLE = 71
SOUTH_WALK = [70, 76]             # 70-mirror completa o 3o (feito abaixo)


def load(n):
    return Image.open(os.path.join(ROOT, SRC, "sprite_%04d.png" % n)).convert("RGBA")


def hair_color(imgs):
    """`char_synth.estimate_colors` amostra o terco superior inteiro, que aqui
    (sprite de so 18x40px) e dominado pela bandana AZUL, nao pelos fios —
    devolvia um cinza-azulado. Este outfit em especial tem cor de cabelo
    conhecida (loiro/amarelo): filtra so pixels QUENTES (r>g>b, pouco azul) do
    terco superior, a mesma logica de is_skin mas sem exigir tom de pele."""
    px = []
    for im in imgs:
        a = np.array(im.convert("RGBA"))
        y1 = max(1, int(im.height * 0.35))
        top = a[:y1]
        op = top[:, :, 3] >= 128
        r, g, b = top[:, :, 0].astype(int), top[:, :, 1].astype(int), top[:, :, 2].astype(int)
        yellow = op & (r > 150) & (g > 110) & (r >= b + 40) & (g >= b)
        if yellow.any():
            px.append(top[:, :, :3][yellow])
    if not px:
        return (200, 160, 60)
    return tuple(int(v) for v in np.concatenate(px).mean(axis=0))


def main():
    out_dir = os.path.join(ROOT, SYNTH_DIR)
    os.makedirs(out_dir, exist_ok=True)

    east_idle = load(EAST_IDLE)
    east_walk_imgs = [load(n) for n in EAST_WALK]
    south_idle = load(SOUTH_IDLE)
    south_walk_imgs = [load(SOUTH_WALK[0]), load(SOUTH_WALK[1]),
                       CS.synth_walk_offset(load(SOUTH_WALK[0]), leg_dx=0)]
    from PIL import ImageOps
    south_walk_imgs[2] = ImageOps.mirror(load(SOUTH_WALK[0]))

    skin_rgb, _ = CS.estimate_colors([east_idle, south_idle] + east_walk_imgs)
    hair_rgb = hair_color([east_idle, south_idle] + east_walk_imgs)
    print("pele~%s cabelo~%s" % (skin_rgb, hair_rgb))

    # 4a fase de andar SINTETICA (o material so tem 3 quadros uteis por ciclo):
    # desloca as pernas do quadro de PASSAGEM em torno oposto.
    east_walk4 = east_walk_imgs + [CS.synth_walk_offset(east_walk_imgs[1], leg_dx=-2, body_dy=1, shear=-1)]
    south_walk4 = south_walk_imgs + [CS.synth_walk_offset(south_walk_imgs[1], leg_dx=2, body_dy=1, shear=1)]

    # vista de COSTAS sintetizada a partir do perfil LESTE (mirror + repintura
    # da regiao do rosto na cor do cabelo + escurecimento) — ver
    # char_synth.synthesize_back; substitui a antiga aproximacao (quadro 0068
    # "sem olhos desenhados"), que so funcionava por sorte de um quadro do rip.
    back_idle = CS.synthesize_back(east_idle, hair_rgb, mirror=True)
    back_walk4 = [CS.synthesize_back(im, hair_rgb, mirror=True) for im in east_walk4]

    names = {}
    back_idle.save(os.path.join(out_dir, "back_idle.png")); names["back_idle"] = "back_idle.png"
    for i, im in enumerate(back_walk4):
        im.save(os.path.join(out_dir, "back_walk%d.png" % i)); names["back_walk%d" % i] = "back_walk%d.png" % i
    east_walk4[3].save(os.path.join(out_dir, "east_walk3_synth.png")); names["east_walk3"] = "east_walk3_synth.png"
    south_walk4[3].save(os.path.join(out_dir, "south_walk3_synth.png")); names["south_walk3"] = "south_walk3_synth.png"

    ov_path = os.path.join(ROOT, OVERRIDE)
    with open(ov_path, encoding="utf-8") as fh:
        doc = json.load(fh)
    player = next(c for c in doc["creatures"] if c["id"] == 128)
    rel = lambda n: "_synth/%s" % names[n]  # noqa: E731  (root = assets-src/import/player)

    player["directions"]["0"] = {
        "_dir": ("norte / costas — SINTETIZADA a partir do perfil leste "
                 "(char_synth.synthesize_back: mirror + repintura do rosto na "
                 "cor do cabelo ~%s + escurecimento). Antes disso o norte era "
                 "so o quadro 0068 (o unico sem olhos desenhados) + seu "
                 "espelho; agora usa o MESMO ciclo de pernas do leste (4 "
                 "fases), so recolorido — anda de verdade em vez de balancar."
                 % (hair_rgb,)),
        "idle": rel("back_idle"),
        "walk": [rel("back_walk0"), rel("back_walk1"), rel("back_walk2"), rel("back_walk3")],
    }
    player["directions"]["1"] = {
        "_dir": "leste (perfil para a direita) — 4a fase SINTETICA (deslocamento de pernas) somada as 3 reais",
        "idle": "sprite_0080.png",
        "walk": ["sprite_0084.png", "sprite_0083.png", "sprite_0075.png", rel("east_walk3")],
    }
    player["directions"]["2"] = {
        "_dir": "sul / de frente — 4a fase SINTETICA somada as 3 reais (0070, 0076, 0070-espelhado)",
        "idle": "sprite_0071.png",
        "walk": ["sprite_0070.png", "sprite_0076.png",
                 {"src": "sprite_0070.png", "mirror": True}, rel("south_walk3")],
    }
    # direcao 3 (oeste) continua mirror_of 1 — sem mudanca

    with open(ov_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("atualizado", OVERRIDE)

    # ---- player_frames.json: documenta a mudanca (mesmo estilo do arquivo)
    fd_path = os.path.join(ROOT, FRAMES_DOC)
    with open(fd_path, encoding="utf-8") as fh:
        fd = json.load(fh)
    dirs = fd["outfit"]["directions"]
    dirs["0"]["walk"] = [68, {"frame": 68, "mirror": True}, 68, "synth:back_walk3"]
    marker = " ATUALIZADO:"
    nota0 = dirs["0"]["_nota"].split(marker)[0].rstrip()
    dirs["0"]["_nota"] = nota0 + (marker + " o norte agora e SINTETIZADO a partir do "
                           "ciclo de 4 fases do leste (char_synth.synthesize_back), "
                           "nao mais o quadro 0068 sozinho — ver "
                           "tools/spr/import_player.py. skin~%s hair~%s." % (skin_rgb, hair_rgb))
    for d, note in (("1", "synth:east_walk3 (deslocamento de pernas sobre 0083)"),
                    ("2", "synth:south_walk3 (deslocamento de pernas sobre 0070-mirror)")):
        w = [x for x in dirs[d]["walk"] if not (isinstance(x, str) and x.startswith("synth:"))]
        w.append(note)
        dirs[d]["walk"] = w
    with open(fd_path, "w", encoding="utf-8") as fh:
        json.dump(fd, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("atualizado", FRAMES_DOC)


if __name__ == "__main__":
    main()
