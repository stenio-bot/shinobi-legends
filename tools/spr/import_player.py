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

FILTRO OBRIGATORIO do ciclo de andar (mesmas regras a-e de `char_synth.
validate_cycle`/`import_mugen.py`, feedback do orquestrador sobre golpes/
agachamentos vazando pro ciclo): os ciclos leste e sul, ja escolhidos a mao
(EAST_WALK/SOUTH_WALK), sao validados contra o idle da direcao e CONSERTADOS
por `char_synth.repair_cycle` — troca por outro quadro do material (dos 76
disponiveis) que passe nas regras, ou sintese de deslocamento de pernas, se
nenhum passar perto. Rejeicoes viram nota em `player_frames.json` (chave
`quadros_rejeitados`).

Uso::

    .venv/bin/python tools/spr/import_player.py
"""
import glob
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import char_synth as CS  # noqa: E402

SRC = "assets-src/import/player"
SYNTH_DIR = "assets-src/import/player/_synth"
OVERRIDE = "assets-src/sprites/overrides/30_player.json"
FRAMES_DOC = "assets-src/sprites/player_frames.json"
CYCLE_SHEET = "assets-src/import/extracted/mugen/_cycle_128.png"

EAST_IDLE = 80
EAST_WALK = [84, 83, 75]          # contato, passagem, contato oposto (reais)
SOUTH_IDLE = 71
SOUTH_WALK = [70, 76]             # 70-mirror completa o 3o (feito abaixo)


def load(n):
    return Image.open(os.path.join(ROOT, SRC, "sprite_%04d.png" % n)).convert("RGBA")


def load_all_candidates():
    """Todos os sprite_NNNN.png do material (pool de busca para o conserto do
    ciclo — ver `char_synth.repair_cycle`)."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, SRC, "sprite_*.png"))):
        m = re.search(r"sprite_(\d+)\.png$", path)
        if not m:
            continue
        n = int(m.group(1))
        out.append((n, Image.open(path).convert("RGBA")))
    return out


def hair_color(imgs):
    """`char_synth.estimate_colors` amostra o terco superior inteiro, que aqui
    (sprite de so 18x40px) e dominado pela bandana AZUL, nao pelos fios —
    devolvia um cinza-azulado. Este outfit em especial tem cor de cabelo
    conhecida (loiro/amarelo): filtra so pixels QUENTES (r>g>b, pouco azul) do
    terco superior, a mesma logica de is_skin mas sem exigir tom de pele."""
    px = []
    for im in imgs:
        a = __import__("numpy").array(im.convert("RGBA"))
        y1 = max(1, int(im.height * 0.35))
        top = a[:y1]
        op = top[:, :, 3] >= 128
        r, g, b = top[:, :, 0].astype(int), top[:, :, 1].astype(int), top[:, :, 2].astype(int)
        yellow = op & (r > 150) & (g > 110) & (r >= b + 40) & (g >= b)
        if yellow.any():
            px.append(top[:, :, :3][yellow])
    if not px:
        return (200, 160, 60)
    np = __import__("numpy")
    return tuple(int(v) for v in np.concatenate(px).mean(axis=0))


def _lbl(x):
    """Rotulo curto pra celula da folha: numero do quadro (int OU string tipo
    '70m' = 70 espelhado, ambos REAIS) fica como esta; 'synth:...' vira 'S'."""
    if isinstance(x, str) and x.startswith("synth"):
        return "S"
    return str(x)


def cycle_sheet(idle_imgs, walk_imgs_by_dir, labels_by_dir):
    """Mesma folha `_cycle_<lt>.png` do import_mugen.py: idle + 4 fases de
    andar nas 4 direcoes, numero do quadro de origem ou 'S' por celula."""
    import imports as I
    box, zoom = 32, 3
    cols = [("N", 0), ("L", 1), ("S", 2), ("O", 3)]
    allimgs = [idle_imgs[d] for _, d in cols] + \
        [im for _, d in cols for im in walk_imgs_by_dir[d]]
    scale = min(box / float(max(i.width for i in allimgs)),
                box / float(max(i.height for i in allimgs)), 1.0)
    pad, head = 4, 16
    W = len(cols) * (box * zoom + pad) + pad
    H = head + 5 * (box * zoom + pad) + pad + 14
    sh = Image.new("RGBA", (W, H), (28, 28, 34, 255))
    d = ImageDraw.Draw(sh)
    d.text((pad, 3), "128 Jogador (outfit)  parado+4andar", fill=(255, 235, 120, 255))
    for c, (lab, dirn) in enumerate(cols):
        x = pad + c * (box * zoom + pad)
        imgs = [idle_imgs[dirn]] + list(walk_imgs_by_dir[dirn])
        labels = labels_by_dir[dirn]
        for r, im in enumerate(imgs):
            y = head + r * (box * zoom + pad)
            cell = I.fit_uniform(im, box, scale, False)
            bg = Image.new("RGBA", (box, box), (70, 70, 78, 255))
            bg.alpha_composite(cell)
            sh.paste(bg.resize((box * zoom, box * zoom), Image.NEAREST), (x, y))
            cl = labels[r]
            color = (255, 140, 60, 255) if cl == "S" else (140, 230, 140, 255)
            dd = ImageDraw.Draw(sh)
            dd.rectangle((x, y, x + (12 if cl == "S" else 20), y + 11), fill=(20, 20, 24, 220))
            dd.text((x + 2, y + 1), cl, fill=color)
        d.text((x + 2, H - 12), lab, fill=(190, 190, 200, 255))
    return sh


def main():
    out_dir = os.path.join(ROOT, SYNTH_DIR)
    os.makedirs(out_dir, exist_ok=True)

    east_idle = load(EAST_IDLE)
    east_walk_imgs = [load(n) for n in EAST_WALK]
    south_idle = load(SOUTH_IDLE)
    south_walk_imgs = [load(SOUTH_WALK[0]), load(SOUTH_WALK[1]),
                       ImageOps.mirror(load(SOUTH_WALK[0]))]

    skin_rgb, _ = CS.estimate_colors([east_idle, south_idle] + east_walk_imgs)
    hair_rgb = hair_color([east_idle, south_idle] + east_walk_imgs)
    print("pele~%s cabelo~%s" % (skin_rgb, hair_rgb))

    # 4a fase de andar SINTETICA (o material so tem 3 quadros uteis por ciclo):
    # desloca as pernas do quadro de PASSAGEM em torno oposto.
    east_walk4 = east_walk_imgs + [CS.synth_walk_offset(east_walk_imgs[1], leg_dx=-2, body_dy=1, shear=-1)]
    south_walk4 = south_walk_imgs + [CS.synth_walk_offset(south_walk_imgs[1], leg_dx=2, body_dy=1, shear=1)]

    # ---- filtro obrigatorio (regras a-e): valida os ciclos ja escolhidos a
    # mao e conserta (troca por outro quadro do material ou sintetiza) o que
    # reprovar — mesma tecnica de import_mugen.py, ver char_synth.repair_cycle.
    candidates = load_all_candidates()
    rejected = []
    east_items = [(EAST_WALK[0], east_walk4[0]), (EAST_WALK[1], east_walk4[1]),
                  (EAST_WALK[2], east_walk4[2]), ("synth:%d" % EAST_WALK[1], east_walk4[3])]
    east_walk4, east_labels = CS.repair_cycle(east_items, east_idle, candidates, rejected, "leste")
    south_items = [(SOUTH_WALK[0], south_walk4[0]), (SOUTH_WALK[1], south_walk4[1]),
                   ("%dm" % SOUTH_WALK[0], south_walk4[2]),
                   ("synth:%dm" % SOUTH_WALK[0], south_walk4[3])]
    south_walk4, south_labels = CS.repair_cycle(south_items, south_idle, candidates, rejected, "sul")
    for r in rejected:
        print("REJEITADO quadro %s (%s): %s -> %s" % (
            r["quadro_rejeitado"], r["ciclo"], "; ".join(r["motivos"]), r["substituido_por"]))

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

    # Os 4 quadros finais (real, trocado OU sintetico) de cada direcao —
    # qualquer posicao pode ter deixado de ser o quadro original por causa do
    # conserto acima, entao gravamos TODAS num arquivo proprio (nao so a 4a) e
    # referenciamos por caminho relativo, em vez de assumir sprite_NNNN.png.
    def save_walk(prefix, imgs, labels):
        rel = []
        for i, (im, lb) in enumerate(zip(imgs, labels)):
            fn = "%s%d_%s.png" % (prefix, i, str(lb).replace(":", "_").replace("m", "mir"))
            im.save(os.path.join(out_dir, fn))
            rel.append("_synth/%s" % fn)
        return rel

    east_walk_rel = save_walk("east_walk", east_walk4, east_labels)
    south_walk_rel = save_walk("south_walk", south_walk4, south_labels)

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
        "_dir": "leste (perfil para a direita) — ciclo validado/consertado (regras a-e, ver docs)",
        "idle": "sprite_0080.png",
        "walk": east_walk_rel,
    }
    player["directions"]["2"] = {
        "_dir": "sul / de frente — ciclo validado/consertado (regras a-e, ver docs)",
        "idle": "sprite_0071.png",
        "walk": south_walk_rel,
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
    dirs["1"]["walk"] = [str(x) for x in east_labels]
    dirs["2"]["walk"] = [str(x) for x in south_labels]
    fd["quadros_rejeitados"] = rejected
    with open(fd_path, "w", encoding="utf-8") as fh:
        json.dump(fd, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("atualizado", FRAMES_DOC)

    # ---- folha de revisao _cycle_128.png (idle + 4 fases x 4 direcoes,
    # numero do quadro de origem ou 'S' por celula)
    west_walk4 = [ImageOps.mirror(im) for im in east_walk4]
    idle_imgs = {
        0: back_idle, 1: east_idle, 2: south_idle, 3: ImageOps.mirror(east_idle),
    }
    walk_imgs_by_dir = {0: back_walk4, 1: east_walk4, 2: south_walk4, 3: west_walk4}
    labels_by_dir = {
        0: ["S"] * 5,
        1: ["%d" % EAST_IDLE] + [_lbl(x) for x in east_labels],
        2: ["%d" % SOUTH_IDLE] + [_lbl(x) for x in south_labels],
        3: ["%d" % EAST_IDLE] + [_lbl(x) for x in east_labels],
    }
    sheet = cycle_sheet(idle_imgs, walk_imgs_by_dir, labels_by_dir)
    sheet_path = os.path.join(ROOT, CYCLE_SHEET)
    os.makedirs(os.path.dirname(sheet_path), exist_ok=True)
    sheet.save(sheet_path)
    print("folha de revisao ->", CYCLE_SHEET)


if __name__ == "__main__":
    main()
