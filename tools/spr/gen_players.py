#!/usr/bin/env python3
"""Gera os 9 PERSONAGENS JOGAVEIS (looktypes 900-909, exceto 906) em
pixel-art procedural PROPRIA, `layers=2` (base + mascara de cor) -- coloriveis
como um outfit de Tibia de verdade (`data/tfs_mapping.json` escolhe
head/body/legs/feet). Substitui os sprites MUGEN importados de
`overrides/40_mugen.json` para estes 9 looktypes (ADR-002: nada de sprite
copiado de NTO/anime bloqueava publicar o jogo -- ver docs/03-decisoes-tecnicas.md).

Uso:  .venv/bin/python tools/spr/gen_players.py
Saida: assets-src/sprites/creatures/look_9NN_l{0,1}.png +
       assets-src/sprites/overrides/62_players.json (chave "creature_sheets",
       aplicada por build_assets.py via imports.py:apply() -- mesmo mecanismo
       de overrides/60_animals.json/61_humanoid_variants.json). Como o nome do
       arquivo (62_*) ordena DEPOIS de 40_mugen.json, esta sobrescreve
       qualquer entrada MUGEN residual para os mesmos ids -- mas o
       import_mugen.py tambem foi ajustado para pular estes 9 looktypes.

Nenhum pixel vem da Tibia, de NTO, do MUGEN ou de qualquer outro jogo
(ADR-002): tudo aqui e geometria desenhada por codigo em `player_art.py`.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

import player_art as PA  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "assets-src", "sprites")
OVERRIDES_PATH = os.path.join(OUT, "overrides", "62_players.json")
CHARACTERS_PATH = os.path.join(ROOT, "data", "characters.json")

CELL = 32
DIRECTIONS = 4
PHASES_IDLE = 1
PHASES_MOVING = 3
TOTAL_PHASES = PHASES_IDLE + PHASES_MOVING

# looktype 906 fica de fora: e o NPC "Mestre Hayato" (mugen_looktypes.json,
# sprite "Kakashi"), nao um personagem jogavel de data/characters.json --
# continua importado do MUGEN, fora do escopo desta missao.
SKIP_LOOKTYPES = {906}

# adereco fixo (nao mascara) + descricao curta por personagem -- usado no
# relatorio e em docs/sistemas/arte-e-sprites.md. `fixed` sobrescreve
# skin/eye default (so a Herdeira Hyuga usa olhos claros fixos).
GEAR_NOTES = {
    "genin_laranja": dict(fixed={}, note="cabelo espetado + bandana azul na testa + jaqueta de gola alta"),
    "genin_uchiha": dict(fixed={}, note="cabelo liso com franja lateral + colarinho alto com fecho + faixa branca no braço"),
    "kunoichi_rosa": dict(fixed={}, note="cabelo médio + abertura triangular no colo do vestido + luvas vermelhas"),
    "herdeira_hyuga": dict(fixed={"eye": PA.PALE_EYE}, note="cabelo longo escuro + casaco alargado nas laterais + olhos claros (fixo)"),
    "ninja_verde": dict(fixed={}, note="corte de tigela (franja reta espessa) + bandagens brancas nos punhos/tornozelos"),
    "kunoichi_armas": dict(fixed={}, note="coques duplos + colarinho de blusa chinesa + pergaminho marrom nas costas"),
    "sabio_loiro": dict(fixed={}, note="cabelo espetado longo e selvagem + pergaminho enorme diagonal nas costas"),
    "sabio_cerimonial": dict(fixed={}, note="chapéu cônico de palha largo + selos vermelhos no peito"),
    "ninja_abelha": dict(fixed={}, note="óculos escuros cobrindo os olhos + 2 lâminas cruzadas em metal nas costas"),
}


def load_characters():
    with open(CHARACTERS_PATH, encoding="utf-8") as fh:
        chars = json.load(fh)
    out = []
    for c in chars:
        lt = int(c["looktype"])
        if lt in SKIP_LOOKTYPES:
            continue
        out.append(c)
    return sorted(out, key=lambda c: c["looktype"])


def save(img, relpath):
    path = os.path.join(OUT, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return relpath.replace(os.sep, "/")


def build_sheet(char_id, looktype, fixed):
    sheets = []
    for layer in (0, 1):
        sh = Image.new("RGBA", (DIRECTIONS * CELL, TOTAL_PHASES * CELL), (0, 0, 0, 0))
        for a in range(TOTAL_PHASES):
            phase = a
            for d in range(DIRECTIONS):
                cell = PA.render(d, phase, layer, char_id, fixed)
                sh.paste(cell, (d * CELL, a * CELL))
        rel = save(sh, "creatures/look_%03d_l%d.png" % (looktype, layer))
        sheets.append(rel)
    return sheets


def gen_players():
    things = []
    for c in load_characters():
        char_id = c["id"]
        looktype = int(c["looktype"])
        info = GEAR_NOTES.get(char_id, dict(fixed={}, note=""))
        sheets = build_sheet(char_id, looktype, info["fixed"])
        things.append({
            "category": "creature",
            "id": looktype,
            "name": "player_%s_%03d" % (char_id, looktype),
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
            "_doc": "%s (%s) — procedural, tools/spr/gen_players.py. layers=2: "
                    "data/tfs_mapping.json (characters.%s) escolhe head/body/legs/feet. "
                    "Adereco fixo: %s." % (c["name"], char_id, char_id, info["note"]),
        })
    return things


def write_overrides(things):
    cfg = {
        "format": 1,
        "_doc": (
            "Os 9 PERSONAGENS JOGAVEIS (looktypes 900-909, exceto 906) em pixel-art "
            "procedural PROPRIA (tools/spr/player_art.py, reaproveita a convencao de "
            "humanoid_art.py: 4 direcoes reais + 3 fases de andar), gerados por "
            "tools/spr/gen_players.py. Substitui os sprites MUGEN importados de "
            "overrides/40_mugen.json para estes 9 ids (ADR-002). Mesmo mecanismo de "
            "overrides/60_animals.json ('creature_sheets', aplicado por build_assets.py "
            "via imports.py:apply(), em ordem de nome de arquivo -- '62' ordena DEPOIS "
            "de '40_mugen.json' entao sobrescreve qualquer entrada residual), mas "
            "'layers=2' (base clara + mascara de cor): ao contrario dos looktypes "
            "946-957 (layers=1, cor gravada no pixel), aqui a cor de "
            "cabelo/roupa/calca/sandalia vem de data/tfs_mapping.json (characters.*, "
            "indice 0..132 da paleta real de outfit) -- coloriveis como um outfit de "
            "Tibia de verdade. Pele/olhos e os 1-2 adereços fixos de cada personagem "
            "(bandana, luvas, pergaminho, oculos escuros...) NAO sao coloriveis (fixos "
            "na base) para o personagem continuar reconhecivel em qualquer cor de "
            "outfit. Nao editar a mao: rode tools/spr/gen_players.py de novo."
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
    things = gen_players()
    path = write_overrides(things)
    print("gerado:", path)
    for c in load_characters():
        info = GEAR_NOTES.get(c["id"], dict(note=""))
        print("  looktype %d = %s (%s) -- %s" % (c["looktype"], c["id"], c["name"], info["note"]))


if __name__ == "__main__":
    main()
