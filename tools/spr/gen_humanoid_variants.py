#!/usr/bin/env python3
"""Gera os 12 looktypes humanoides (946-957: bandidos, ninjas, chefes,
marionetes...) em pixel-art procedural PROPRIA (`humanoid_art.py`), com 4
direcoes DE VERDADE (Norte/costas, Leste/perfil, Sul/frente, Oeste = espelho
do Leste) e 3 fases de andar (parado + 2 passos, pernas/bracos deslocados
1-2px) — ver docs/backlog-sprites.md e docs/sistemas/arte-e-sprites.md,
secao "Criaturas procedurais".

Ate esta missao ("continuacao 2") esses looktypes eram uma COPIA do PNG
IMPORTADO com a matiz girada (hue-shift): a MESMA pose "presa" nas 4
direcoes e nas 3 fases de "andar" (a arte de origem nao tinha direcao real
nem ciclo de passada — ver git blame desta funcao/modulo para a versao
antiga). Agora a arte e 100% desenhada por codigo (ADR-002, mesma
convencao de `animal_art.py`): cabeca (8-9px) + tronco + bracos + pernas,
3 tons + contorno derivados da cor-alvo (`tibia_colors.RAW`, o MESMO
dicionario que a versao antiga ja usava pro hue-shift) + um adereco por
classe (capuz, arco, mascara, chapeu, manto, aura, chifres...) — ver
`humanoid_art.py` para a implementacao do boneco e da lista de gears.

Continua `layers=1` (cor final gravada no pixel, sem mascara de outfit —
layers=1 nao ganha mascara, ver FORMATO.md 3.5): a diferenca para
`gen_animals.py` (layers=2) e que aqui cada monstro tem seu PROPRIO
looktype com a cor certa desde a origem, entao nao precisa de
`data/tfs_mapping.json` head/body/legs/feet pra nada (idem versao anterior).

Uso:  .venv/bin/python tools/spr/gen_humanoid_variants.py
Saida: assets-src/sprites/creatures/look_9NN.png (1 arquivo por looktype,
       32x32 ou 64x64 no caso do Oni Glacial) + assets-src/sprites/
       overrides/61_humanoid_variants.json (chave "creature_sheets",
       aplicada por tools/spr/imports.py:apply() — mesmo mecanismo de
       60_animals.json).

Nenhum pixel vem da Tibia, de NTO ou de outro jogo (ADR-002): tudo aqui e
geometria desenhada por codigo em `humanoid_art.py`.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image

import humanoid_art as HA     # noqa: E402
import tibia_colors as TC      # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SPRITES_DIR = os.path.join(ROOT, "assets-src", "sprites")
OUT = SPRITES_DIR
OVERRIDES_PATH = os.path.join(SPRITES_DIR, "overrides", "61_humanoid_variants.json")

CELL = 32
DIRECTIONS = 4
PHASES_IDLE = 1
PHASES_MOVING = 3
TOTAL_PHASES = PHASES_IDLE + PHASES_MOVING       # a=0 parado, a=1..3 andando


def _target_rgb(named_key):
    """RGB "de lore" (pre-quantizacao) — ver comentario de tibia_colors.py:
    RAW. gen_humanoid_variants usa RAW direto (nao NAMED/color_rgb), porque
    quantizar pro indice de outfit faria varias cores abafadas (oliva, navy,
    ardosia) virarem cinza antes mesmo de desenhar."""
    return TC.RAW[named_key]


# id novo (946..957) -> dados da variante. `gear` seleciona o adereco de
# classe em humanoid_art._gear. `tiles` so aparece quando != 1 (Oni Glacial:
# 2x2/64x64, os outros 11 sao 1x1/32x32).
VARIANTS = [
    dict(id=956, monster="bandit", target=_target_rgb("brown_bandit"),
         gear="hood", note="Bandido — marrom, capuz cobrindo o rosto."),
    dict(id=946, monster="bandit_archer", target=_target_rgb("olive_archer"),
         gear="bow", note="Bandido Arqueiro — verde-oliva, arco visivel na mao/costas."),
    dict(id=947, monster="mercenary_bridge", target=_target_rgb("navy_mercenary"),
         gear="spear_pauldron",
         note="Mercenário da Ponte — azul-marinho, ombreira de metal + lança curta."),
    dict(id=948, monster="ruin_puppet", target=_target_rgb("wood_puppet"),
         gear="puppet_joints",
         note="Marionete de Combate — tom de madeira, juntas visiveis nos ombros/joelhos, "
              "sem expressao facial (reforça que é um boneco, não um humano)."),
    dict(id=949, monster="mist_scout", target=_target_rgb("mist_scout_teal"),
         gear="mask", note="Batedor da Névoa — verde-azulado enevoado, máscara cobrindo o rosto."),
    dict(id=950, monster="rogue_ninja", target=_target_rgb("rogue_slate"),
         gear="scarf",
         note="Ninja Renegado — cinza-ardósia, cachecol no rosto + lâminas cruzadas nas costas."),
    dict(id=951, monster="mist_guardian", target=_target_rgb("mist_guardian_steel"),
         gear="hat", note="Guardião da Neblina — cinza-azulado de aço, chapéu cônico largo."),
    dict(id=952, monster="boss_puppeteer", target=_target_rgb("puppeteer_violet"),
         gear="strings",
         note="Marionetista das Ruínas — violeta, barra de controle erguida com fios."),
    dict(id=957, monster="boss_bandit_chief", target=_target_rgb("chief_red"),
         gear="cloak", note="Chefe dos Bandidos — vermelho/preto, manto longo."),
    dict(id=953, monster="spectral_warrior", target=_target_rgb("spectral_pale_purple"),
         gear="aura",
         note="Guerreiro Espectral — roxo-pálido, auréola de partículas claras ao redor."),
    dict(id=954, monster="boss_curse_partner", target=_target_rgb("curse_partner_red"),
         gear="curse_marks",
         note="O Sócio Eterno — vermelho, olhos/marcas brilhantes + tendril de aura escura."),
    dict(id=955, monster="glacier_oni", target=_target_rgb("oni_icy_blue"),
         gear="horns", tiles=2,
         note="Oni da Geleira — azul-gelo, chifres + presas, caixa 2x2 (maior que os demais, "
              "condizente com um oni)."),
]


def save(img, relpath):
    path = os.path.join(OUT, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return relpath.replace(os.sep, "/")


def build_variant(spec):
    tiles = int(spec.get("tiles") or 1)
    box = tiles * CELL
    palette = HA.class_palette(spec["target"])
    big = tiles > 1

    sh = Image.new("RGBA", (DIRECTIONS * box, TOTAL_PHASES * box), (0, 0, 0, 0))
    for row in range(TOTAL_PHASES):
        phase = row              # row 0 = parado (phase 0), rows 1..3 = passos 1..3
        for d in range(DIRECTIONS):
            cell = HA.render(d, phase, palette, gear=spec["gear"], big=big)
            sh.paste(cell, (d * box, row * box))
    rel = save(sh, "creatures/look_%03d.png" % spec["id"])

    return {
        "category": "creature",
        "id": spec["id"],
        "name": "variant_%s_%03d" % (spec["monster"], spec["id"]),
        "width": tiles, "height": tiles, "exact_size": min(255, box),
        "layers": 1,                # boneco procedural ja colorido, sem mascara
        "pattern_x": DIRECTIONS, "pattern_y": 1, "pattern_z": 1,
        "frame_groups": [
            {"type": 0, "phases": PHASES_IDLE},
            {"type": 1, "phases": PHASES_MOVING,
             "animation": {"async": False, "loop_count": 0, "start_phase": 0,
                           "durations": [[220, 220]] * PHASES_MOVING}},
        ],
        "sheets": [rel],
        "_doc": "%s Procedural (tools/spr/humanoid_art.py, gear=%s) — 4 direcoes reais + "
                "3 fases de andar. Gerado por tools/spr/gen_humanoid_variants.py — nao "
                "editar a mao." % (spec["note"], spec["gear"]),
    }


def write_overrides(things):
    cfg = {
        "format": 1,
        "_doc": (
            "Looktypes humanoides (946-957) em pixel-art procedural PROPRIA "
            "(tools/spr/humanoid_art.py) — 4 direcoes reais (Norte sem rosto, Leste/Oeste "
            "perfil espelhado com braco/perna da frente avancados, Sul com rosto) + 3 fases "
            "de andar. Gerado por tools/spr/gen_humanoid_variants.py. Mesmo mecanismo de "
            "overrides/60_animals.json ('creature_sheets', aplicado por build_assets.py via "
            "imports.py:apply()), mas layers=1 (cor final gravada no pixel — a paleta de "
            "cada classe vem de tools/spr/tibia_colors.py:RAW, NAO de "
            "data/tfs_mapping.json head/body/legs/feet, que nao tem efeito em looktype "
            "layers=1 — ver FORMATO.md 3.5). Nao editar a mao: rode "
            "tools/spr/gen_humanoid_variants.py de novo."
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
    things = [build_variant(spec) for spec in VARIANTS]
    path = write_overrides(things)
    print("gerado:", path)
    for spec in VARIANTS:
        print("  looktype %d = %s (gear=%s)" % (spec["id"], spec["monster"], spec["gear"]))


if __name__ == "__main__":
    main()
