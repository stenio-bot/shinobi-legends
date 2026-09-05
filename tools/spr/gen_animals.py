#!/usr/bin/env python3
"""Gera looktypes NOVOS de animal (lobo, cervo, aguia, cobra, sanguessuga) em
pixel-art procedural, com 4 direcoes de verdade + ciclo de andar de 3 fases +
camada de mascara (layers=2) para `data/tfs_mapping.json` poder recolorir por
monstro.

Resolve dois problemas do backlog (docs/backlog-sprites.md):
1. Lobo/Cervo/Aguia do Trovao usavam o looktype 21 (placeholder generico de
   fera vanilla) — ficavam retangulos com pernas, nao pareciam nada.
2. Cobra da Floresta/Serpente Menor/Serpente de Magma compartilhavam o
   looktype 56 importado (layers=1, arte real mas SEM mascara de cor — as
   3 entradas de cor em tfs_mapping.json nao faziam nada). O novo looktype de
   cobra (943) e layers=2: as 3 serpentes continuam no MESMO looktype mas
   ganham cores DIFERENTES de verdade.

Uso:  .venv/bin/python tools/spr/gen_animals.py
Saida: assets-src/sprites/creatures/look_9NN_l{0,1}.png +
       assets-src/sprites/overrides/60_animals.json (consumido por
       build_assets.py via IMP.apply(), mesmo mecanismo de 30_player.json/
       40_mugen.json — ver `imports.py: apply()` chave "creature_sheets").

Nenhum pixel vem da Tibia, de NTO ou de outro jogo (ADR-002): tudo aqui e
geometria desenhada por codigo em `animal_art.py`.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import animal_art as AA  # noqa: E402
import art  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "assets-src", "sprites")
OVERRIDES_PATH = os.path.join(ROOT, "assets-src", "sprites", "overrides", "60_animals.json")

CELL = 32
DIRECTIONS = 4
PHASES_IDLE = 1
PHASES_MOVING = 3
TOTAL_PHASES = PHASES_IDLE + PHASES_MOVING          # a=0 parado, a=1..3 andando

# looktypes livres >= 940 (teto atual do .dat e 938: BOSS_LAST em
# gen_placeholders.py; 900-926 sao os personagens MUGEN, protegidos pela
# missao — nao mexer). Faixa alocada aqui: 940..945.
LOOKTYPES = {
    "wolf": 940,
    "deer": 941,
    "eagle": 942,
    "snake": 943,
    "toad": 944,
    "leech": 945,
}

DRAW = {
    "wolf": AA.draw_wolf,
    "deer": AA.draw_deer,
    "eagle": AA.draw_eagle,
    "snake": AA.draw_snake,
    "leech": AA.draw_leech,
    # sapo reaproveita a silhueta ja existente em art.py (agachada, 1x1,
    # ja usa BASE/MASK_OF do mesmo jeito que os animais novos) — so muda
    # o looktype (deixa de ser 60/"great_beast" compartilhado com o boss).
    "toad": lambda d, p, l: art.draw_toad(d, p, l, {}),
}

NAMES = {
    "wolf": "Lobo", "deer": "Cervo", "eagle": "Aguia do Trovao",
    "snake": "Serpente", "toad": "Sapo", "leech": "Sanguessuga",
}


def save(img, relpath):
    path = os.path.join(OUT, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return relpath.replace(os.sep, "/")


def build_sheet(kind, looktype):
    from PIL import Image
    draw = DRAW[kind]
    sheets = []
    for layer in (0, 1):
        sh = Image.new("RGBA", (DIRECTIONS * CELL, TOTAL_PHASES * CELL), (0, 0, 0, 0))
        for a in range(TOTAL_PHASES):
            for d in range(DIRECTIONS):
                cell = draw(d, a, layer)
                if layer == 0:
                    art.outline_inner(cell)
                sh.paste(cell, (d * CELL, a * CELL))
        rel = save(sh, "creatures/look_%03d_l%d.png" % (looktype, layer))
        sheets.append(rel)
    return sheets


def gen_animals():
    things = []
    for kind, looktype in LOOKTYPES.items():
        sheets = build_sheet(kind, looktype)
        things.append({
            "category": "creature",
            "id": looktype,
            "name": "animal_%s_%03d" % (kind, looktype),
            "width": 1, "height": 1, "exact_size": 32,
            "layers": 2,
            "pattern_x": DIRECTIONS, "pattern_y": 1, "pattern_z": 1,
            "frame_groups": [
                {"type": 0, "phases": PHASES_IDLE},
                {"type": 1, "phases": PHASES_MOVING,
                 "animation": {"async": False, "loop_count": 0, "start_phase": 0,
                               "durations": [[220, 220]] * PHASES_MOVING}},
            ],
            "sheets": sheets,
            "_doc": "%s (%s) — procedural, tools/spr/gen_animals.py. layers=2: "
                    "data/tfs_mapping.json escolhe head/body/legs/feet por monstro "
                    "no mesmo looktype." % (NAMES[kind], kind),
        })
    return things


def write_overrides(things):
    cfg = {
        "format": 1,
        "_doc": (
            "Looktypes NOVOS de animal (wolf/deer/eagle/snake/toad/leech), gerados por "
            "tools/spr/gen_animals.py em pixel-art procedural propria (ADR-002). Mesmo "
            "mecanismo de overrides/30_player.json e overrides/40_mugen.json (aplicado por "
            "build_assets.py via imports.apply(), em ordem de nome de arquivo), mas com uma "
            "chave propria 'creature_sheets': ao contrario de 'creatures' (que le PNGs crus "
            "de personagem e monta a folha na hora, sempre layers=1), aqui as folhas ja saem "
            "prontas de gen_animals.py (camada 0 = base clara, camada 1 = mascara de cor) e "
            "sao layers=2 — assim varios monstros no MESMO looktype (as 3 serpentes, por "
            "exemplo) ficam com cores DIFERENTES via data/tfs_mapping.json. Nao editar a mao: "
            "rode tools/spr/gen_animals.py de novo."
        ),
        "root": "assets-src/sprites",
        "build_dir": "assets-src/sprites/creatures",
        "creature_sheets": things,
    }
    os.makedirs(os.path.dirname(OVERRIDES_PATH), exist_ok=True)
    with open(OVERRIDES_PATH, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return OVERRIDES_PATH


def main():
    things = gen_animals()
    path = write_overrides(things)
    print("gerado:", path)
    for kind, lt in LOOKTYPES.items():
        print("  looktype %d = %s (%s)" % (lt, kind, NAMES[kind]))


if __name__ == "__main__":
    main()
