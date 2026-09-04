#!/usr/bin/env python3
"""Gera os PNGs placeholder em assets-src/sprites/ e o manifest.json que o
build_assets.py consome.

Uso:  .venv/bin/python tools/spr/gen_placeholders.py

Toda a arte e desenhada por codigo (tools/spr/art.py). Nenhum pixel vem da
Tibia ou de outro jogo — ver ADR-002 em docs/03-decisoes-tecnicas.md.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "assets-src", "sprites")

CELL = 32

# --------------------------------------------------------------- helpers
def save(img, relpath):
    path = os.path.join(OUT, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return relpath.replace(os.sep, "/")


def sheet(w_tiles, h_tiles, cols, rows):
    from PIL import Image
    return Image.new("RGBA", (cols * w_tiles * CELL, rows * h_tiles * CELL), (0, 0, 0, 0))


def minimap_rgb(idx):
    """Indice de cor de minimapa da Tibia (paleta 6x6x6) -> RGB."""
    if idx <= 0 or idx > 215:
        return (52, 60, 52)
    return ((idx // 36) % 6 * 51, (idx // 6) % 6 * 51, idx % 6 * 51)


# ------------------------------------------------------------------ itens
GROUND_MINIMAP_COLORS = [0, 12, 24, 51, 86, 114, 121, 129, 140, 179, 186, 192, 207, 210, 215]

WALL_TINTS = [(122, 122, 130), (104, 92, 78), (86, 96, 104)]
PICKUP_TINTS = [(196, 92, 60), (86, 132, 196), (110, 176, 96), (200, 176, 84),
                (156, 108, 188), (140, 140, 148)]
STACK_TINTS = [(200, 176, 84), (168, 168, 176), (176, 112, 72), (120, 168, 200)]
DECO_TINTS = [(96, 92, 100), (110, 96, 82), (84, 100, 92)]

TFS_MAPPING = os.path.join(ROOT, "data", "tfs_mapping.json")

# palavra-chave no id do item (data/tfs_mapping.json) -> icone + matiz
ICON_RULES = [
    (("kunai", "tanto", "katana", "kodachi", "blade", "sword", "naginata", "spear"),
     "blade", (128, 132, 146)),
    (("shuriken", "senbon", "star"), "star", (150, 152, 164)),
    (("scroll", "pergaminho"), "scroll", (176, 68, 56)),
    (("vest", "bandana", "headband", "cloak", "robe", "haori", "sash"), "cloth", (74, 128, 90)),
    (("pants", "hakama"), "pants", (60, 62, 72)),
    (("sandals", "boots", "geta"), "boot", (76, 68, 60)),
    (("mask", "helm", "hood"), "helm", (216, 212, 202)),
    (("gloves", "wrap"), "glove", (128, 96, 66)),
    (("potion", "pill", "oil", "antidote", "elixir", "tonic"), "vial", (92, 116, 208)),
    (("onigiri", "food", "ration", "dango", "rice"), "food", (240, 240, 236)),
    (("pelt", "skin", "hide", "fur"), "pelt", (128, 118, 112)),
    (("fang", "claw", "tooth", "horn"), "fang", (232, 228, 214)),
    (("ring", "amulet", "necklace"), "ring", (196, 176, 96)),
    (("backpack", "bag", "pouch"), "bag", (132, 96, 64)),
    (("ryo", "coin", "gold"), "coin", (214, 180, 68)),
    (("emblem", "badge", "crest", "token"), "emblem", (160, 60, 56)),
    (("gland", "core", "essence", "shard"), "pill", (140, 88, 168)),
]


def icon_for(name):
    for keys, kind, tint in ICON_RULES:
        if any(k in name for k in keys):
            h = (sum(ord(c) for c in name) % 40 - 20) / 255.0
            return kind, (art._c(tint[0] + h * 255 * 0.35),
                          art._c(tint[1] + h * 255 * 0.35),
                          art._c(tint[2] + h * 255 * 0.35))
    return "cube", art.hsv((sum(ord(c) for c in name) % 97) / 97.0, 0.55, 0.72)[:3]


def load_mapping():
    with open(TFS_MAPPING, encoding="utf-8") as fh:
        return json.load(fh)


def gen_items():
    sheets = {}
    for mc in GROUND_MINIMAP_COLORS:
        sheets["ground_%d" % mc] = save(art.draw_ground(minimap_rgb(mc), seed=mc),
                                        "items/ground_%d.png" % mc)
    for i, t in enumerate(WALL_TINTS):
        sheets["wall_%d" % i] = save(art.draw_wall(t), "items/wall_%d.png" % i)
    sheets["container"] = save(art.draw_container(), "items/container.png")
    sheets["splash"] = save(art.draw_splash((92, 132, 196)), "items/splash.png")
    sheets["fluid"] = save(art.draw_vial((92, 132, 196)), "items/fluid.png")
    for i, t in enumerate(PICKUP_TINTS):
        sheets["pickup_%d" % i] = save(art.draw_cube(t), "items/pickup_%d.png" % i)
    for i, t in enumerate(STACK_TINTS):
        sheets["stack_%d" % i] = save(art.draw_stack(t), "items/stack_%d.png" % i)
    for i, t in enumerate(DECO_TINTS):
        sheets["deco_%d" % i] = save(art.draw_marker(t), "items/deco_%d.png" % i)

    overrides = {}
    for name, server_id in sorted(load_mapping()["items"].items()):
        kind, tint = icon_for(name)
        rel = save(art.draw_icon(kind, tint), "items/own/%s.png" % name)
        # a chave e o SERVER id do TFS; build_assets.py resolve para clientId no OTB
        overrides[str(server_id)] = {"name": name, "sheet": rel, "icon": kind}
    return sheets, overrides


# -------------------------------------------------------------- criaturas
MONSTER_ARCHETYPES = [
    (("wolf", "hound", "eagle", "beast", "boar"), "wolf"),
    (("snake", "serpent", "viper"), "snake"),
    (("toad", "frog"), "toad"),
    (("leech", "slime", "ooze", "worm"), "leech"),
    (("bandit", "rogue", "puppet", "sentinel"), "bandit"),
]


def archetypes_from_mapping():
    """looktype -> arquetipo, lido de data/tfs_mapping.json (monstros e NPCs)."""
    m = load_mapping()
    out = {}
    entries = sorted(m["monsters"].items(), key=lambda kv: kv[0].startswith("boss"))
    for name, cfg in entries:
        lt = cfg.get("looktype")
        if not lt or lt in out:
            continue
        arch = "ninja"
        for keys, a in MONSTER_ARCHETYPES:
            if any(k in name for k in keys):
                arch = a
                break
        out[lt] = arch
    for _, cfg in sorted(m["npc_outfits"].items()):
        lt = cfg.get("type")
        if lt and lt not in out:
            out[lt] = "ninja"
    return out


ARCHETYPE_OVERRIDES = archetypes_from_mapping()

SERVER_DIRS = [os.path.join(ROOT, "server", "tfs", "data", "monster"),
               os.path.join(ROOT, "server", "tfs", "data", "npc")]
LOOK_RE = re.compile(r'look\s+type\s*=\s*"(\d+)"', re.I)


def server_looktypes():
    """Todo looktype citado nos XML de monstro/NPC do TFS (inclui os vanilla do
    mapa padrao). O .dat precisa cobrir ate o maior deles sem buracos."""
    found = set()
    for base in SERVER_DIRS:
        for dirpath, _, files in os.walk(base):
            for fn in files:
                if not fn.lower().endswith(".xml"):
                    continue
                try:
                    with open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace") as fh:
                        txt = fh.read()
                except OSError:
                    continue
                for m in LOOK_RE.finditer(txt):
                    v = int(m.group(1))
                    if 0 < v < 65535:
                        found.add(v)
    return found


SERVER_LOOKTYPES = server_looktypes()
# 20 looktypes livres acima do maior usado ficam reservados para chefes 2x2
BOSS_FIRST = max([160] + sorted(SERVER_LOOKTYPES)) + 1
BOSS_LAST = BOSS_FIRST + 19
CREATURE_MAX = BOSS_LAST
GENERIC_VARIANTS = 6


def archetype_for(looktype):
    """Arquetipo do placeholder. Looktypes citados em data/tfs_mapping.json ganham
    arte tematica; o resto do intervalo (monstros/NPCs vanilla do mapa do TFS)
    vira uma fera generica cinza, so para o cliente ter o que desenhar."""
    if looktype in ARCHETYPE_OVERRIDES:
        return ARCHETYPE_OVERRIDES[looktype]
    if looktype >= BOSS_FIRST:
        return "boss_beast" if looktype % 2 else "boss_ninja"
    return "generic"


def beast_palette(looktype, base_hue, sat=0.42, val=0.62):
    h = (base_hue + ((looktype % 5) - 2) * 0.028) % 1.0
    return {
        "body": art.hsv(h, sat, val),
        "head": art.hsv(h, sat * 0.9, val * 1.15),
        "legs": art.hsv(h, sat, val * 0.78),
        "feet": art.hsv(h, sat, val * 0.62),
    }


PALETTE_BASE_HUE = {"wolf": 0.08, "snake": 0.30, "toad": 0.26, "leech": 0.80,
                    "boss_beast": 0.95}

GENERIC_TINTS = [
    {"body": (128, 128, 136, 255), "head": (150, 150, 158, 255),
     "legs": (104, 104, 112, 255), "feet": (86, 86, 94, 255)},
    {"body": (140, 132, 122, 255), "head": (162, 154, 142, 255),
     "legs": (114, 108, 100, 255), "feet": (94, 90, 84, 255)},
    {"body": (118, 126, 134, 255), "head": (138, 146, 156, 255),
     "legs": (96, 104, 112, 255), "feet": (80, 86, 94, 255)},
    {"body": (134, 126, 134, 255), "head": (156, 148, 156, 255),
     "legs": (110, 104, 110, 255), "feet": (90, 86, 90, 255)},
    {"body": (122, 134, 126, 255), "head": (144, 156, 148, 255),
     "legs": (100, 110, 104, 255), "feet": (84, 92, 86, 255)},
    {"body": (146, 140, 128, 255), "head": (168, 162, 150, 255),
     "legs": (120, 116, 106, 255), "feet": (98, 94, 88, 255)},
]

PHASES_IDLE = 1
PHASES_MOVING = 3
DIRECTIONS = 4


def draw_creature_cell(arch, direction, phase, layer, looktype):
    big = arch.startswith("boss")
    if arch == "generic":
        pal = GENERIC_TINTS[looktype % GENERIC_VARIANTS]
        return art.draw_quadruped(direction, phase, layer, pal, big=False)
    if arch in ("ninja", "bandit", "boss_ninja"):
        style = {"ninja": "ninja", "bandit": "bandit", "boss_ninja": "boss"}[arch]
        return art.draw_humanoid(direction, phase, layer, style, {}, big=big)
    pal = beast_palette(looktype, PALETTE_BASE_HUE.get(arch, 0.5))
    if arch in ("wolf", "boss_beast"):
        return art.draw_quadruped(direction, phase, layer, pal, big=big)
    if arch == "snake":
        return art.draw_serpent(direction, phase, layer, pal)
    if arch == "toad":
        return art.draw_toad(direction, phase, layer, pal)
    return art.draw_blob(direction, phase, layer, pal)


def gen_creatures():
    things = []
    total_phases = PHASES_IDLE + PHASES_MOVING
    cache = {}

    def sheets_for(arch, looktype, tiles):
        # looktypes genericos compartilham folha (evita milhares de PNGs iguais)
        if arch == "generic":
            key = ("generic", looktype % GENERIC_VARIANTS)
            stem = "creatures/generic_%d" % (looktype % GENERIC_VARIANTS)
        else:
            key = ("look", looktype)
            stem = "creatures/look_%03d" % looktype
        got = cache.get(key)
        if got:
            return got
        out = []
        for layer in (0, 1):
            sh = sheet(tiles, tiles, DIRECTIONS, total_phases)
            for a in range(total_phases):
                for d in range(DIRECTIONS):
                    cell = draw_creature_cell(arch, d, a, layer, looktype)
                    if layer == 0:
                        art.outline_inner(cell)
                    sh.paste(cell, (d * tiles * CELL, a * tiles * CELL))
            out.append(save(sh, "%s_l%d.png" % (stem, layer)))
        cache[key] = out
        return out

    for looktype in range(1, CREATURE_MAX + 1):
        arch = archetype_for(looktype)
        big = arch.startswith("boss")
        tiles = 2 if big else 1
        things.append({
            "category": "creature",
            "id": looktype,
            "name": "%s_%03d" % (arch, looktype),
            "width": tiles, "height": tiles,
            "exact_size": 32 if not big else 64,
            "layers": 2,
            "pattern_x": DIRECTIONS, "pattern_y": 1, "pattern_z": 1,
            "frame_groups": [
                {"type": 0, "phases": PHASES_IDLE},
                {"type": 1, "phases": PHASES_MOVING,
                 "animation": {"async": False, "loop_count": 0, "start_phase": 0,
                               "durations": [[220, 220]] * PHASES_MOVING}},
            ],
            "sheets": sheets_for(arch, looktype, tiles),
        })
    return things


# ---------------------------------------------------------------- efeitos
EFFECT_KINDS = ["burst", "sparks", "smoke", "slash", "pulse"]
EFFECT_MAX = 255            # o protocolo 1098 manda id de efeito em U8
MISSILE_MAX = 255
DETAILED_EFFECTS = 70       # 1..70 tem arte propria; o resto e placeholder simples
DETAILED_MISSILES = 50
SHARED_TINTS = 12


def gen_effects():
    things = []
    cache = {}
    for eid in range(1, EFFECT_MAX + 1):
        kind = EFFECT_KINDS[eid % len(EFFECT_KINDS)]
        if eid <= DETAILED_EFFECTS:
            phases = 4 + (eid % 4)
            tint = art.hsv((eid * 0.113) % 1.0, 0.72, 0.95)[:3]
            key = ("own", eid)
            name = "effects/effect_%03d.png" % eid
        else:
            phases = 3
            bucket = eid % SHARED_TINTS
            tint = art.hsv(bucket / float(SHARED_TINTS), 0.60, 0.88)[:3]
            key = ("shared", kind, bucket)
            name = "effects/generic_%s_%02d.png" % (kind, bucket)
        rel = cache.get(key)
        if rel is None:
            sh = sheet(1, 1, 1, phases)
            for a in range(phases):
                sh.paste(art.draw_effect(kind, a, phases, tint), (0, a * CELL))
            rel = save(sh, name)
            cache[key] = rel
        things.append({
            "category": "effect", "id": eid, "name": "%s_%03d" % (kind, eid),
            "width": 1, "height": 1, "layers": 1,
            "pattern_x": 1, "pattern_y": 1, "pattern_z": 1,
            "frame_groups": [{"type": 0, "phases": phases,
                              "animation": {"async": True, "loop_count": 1,
                                            "start_phase": 0,
                                            "durations": [[75, 75]] * phases}}],
            "sheets": [rel],
        })
    return things


MISSILE_KINDS = ["shuriken", "bolt", "orb"]


def gen_missiles():
    things = []
    cache = {}
    for mid in range(1, MISSILE_MAX + 1):
        kind = MISSILE_KINDS[mid % len(MISSILE_KINDS)]
        if mid <= DETAILED_MISSILES:
            tint = art.hsv((mid * 0.173) % 1.0, 0.66, 0.96)[:3]
            key = ("own", mid)
            name = "missiles/missile_%03d.png" % mid
        else:
            bucket = mid % SHARED_TINTS
            tint = art.hsv(bucket / float(SHARED_TINTS), 0.58, 0.90)[:3]
            key = ("shared", kind, bucket)
            name = "missiles/generic_%s_%02d.png" % (kind, bucket)
        rel = cache.get(key)
        if rel is None:
            sh = sheet(1, 1, 3, 3)
            for yi, dy in enumerate((-1, 0, 1)):
                for xi, dx in enumerate((-1, 0, 1)):
                    sh.paste(art.draw_missile(dx, dy, kind, tint), (xi * CELL, yi * CELL))
            rel = save(sh, name)
            cache[key] = rel
        things.append({
            "category": "missile", "id": mid, "name": "%s_%03d" % (kind, mid),
            "width": 1, "height": 1, "layers": 1,
            "pattern_x": 3, "pattern_y": 3, "pattern_z": 1,
            "frame_groups": [{"type": 0, "phases": 1}],
            "sheets": [rel],
        })
    return things


# ---------------------------------------------------------------- manifest
def main():
    os.makedirs(OUT, exist_ok=True)
    item_sheets, item_overrides = gen_items()
    things = gen_creatures() + gen_effects() + gen_missiles()

    manifest = {
        "_doc": ("Manifesto de sprites do Shinobi Legends. Consumido por "
                 "tools/spr/build_assets.py, que gera client-otc/data/things/1098/"
                 "Tibia.spr e Tibia.dat. Regenere os PNGs com "
                 "tools/spr/gen_placeholders.py."),
        "format": 1,
        "client_version": 1098,
        "sprite_size": CELL,
        "dat_signature": "0x57BBD603",
        "spr_signature": "0x57BBD603",
        "sheet_root": "assets-src/sprites",
        "sheet_layout": ("cada PNG e uma grade: colunas = pattern_x, linhas = "
                         "((fase * pattern_z + z) * pattern_y + y). Cada celula tem "
                         "width*32 x height*32. Um arquivo por camada (layers)."),
        "items": {
            "otb": "server/tfs/data/items/items.otb",
            "_doc": ("Os things de item sao gerados para TODO clientId referenciado pelo "
                     "items.otb (o cliente le o .dat sequencialmente; faltar um id "
                     "desalinha o arquivo). O estilo visual vem da primeira regra que casa."),
            "sheets": item_sheets,
            "rules": [
                {"style": "ground", "when": {"group": "ground"},
                 "sheet": "ground_{minimap_color}", "fallback_sheet": "ground_0"},
                {"style": "container", "when": {"group": "container"}, "sheet": "container"},
                {"style": "splash", "when": {"group_in": ["splash"]}, "sheet": "splash"},
                {"style": "fluid", "when": {"group_in": ["fluid"]}, "sheet": "fluid"},
                {"style": "wall",
                 "when": {"flags_all": ["BLOCK_SOLID"], "flags_none": ["PICKUPABLE", "MOVEABLE"]},
                 "sheet": "wall_{v3}"},
                {"style": "stack", "when": {"flags_all": ["STACKABLE"]}, "sheet": "stack_{v4}"},
                {"style": "pickup", "when": {"flags_all": ["PICKUPABLE"]}, "sheet": "pickup_{v6}"},
                {"style": "deco", "when": {}, "sheet": "deco_{v3}"},
            ],
            "override_id_space": "server",
            "_doc_overrides": ("as chaves de 'overrides' sao SERVER ids do TFS "
                               "(data/tfs_mapping.json). O build resolve para clientId "
                               "pelo items.otb."),
            "overrides": item_overrides,
        },
        "things": things,
    }
    path = os.path.join(OUT, "manifest.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    n_png = sum(len(files) for _, _, files in os.walk(OUT))
    print("manifest: %s" % path)
    print("looktypes citados nos XML do TFS: %d (maior: %d)"
          % (len(SERVER_LOOKTYPES), max(SERVER_LOOKTYPES) if SERVER_LOOKTYPES else 0))
    print("things descritos: %d criaturas (1..%d, chefes 2x2 em %d..%d) + %d efeitos + %d missiles"
          % (CREATURE_MAX, CREATURE_MAX, BOSS_FIRST, BOSS_LAST, EFFECT_MAX, MISSILE_MAX))
    print("arquivos em assets-src/sprites: %d" % n_png)


if __name__ == "__main__":
    main()
