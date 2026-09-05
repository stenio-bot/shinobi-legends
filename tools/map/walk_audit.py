#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoria estática de caminhabilidade do mapa `valley.otbm`.

Compara, para CADA tile do mapa, duas coisas:

  1. **O que o TFS realmente faz** (`tfs_walkable`): reproduz a regra de
     `Tile::queryAdd` para jogadores (`server/tfs/src/tile.cpp`) usando as
     flags REAIS lidas de `server/tfs/data/items/items.otb` — não as
     declaradas em `tiles.json`. A regra (ver `queryAdd`, linha ~603): o chão
     precisa existir e não ser `blockSolid`; a passagem é recusada se
     QUALQUER item da pilha (chão ou empilhado) tiver `blockSolid=true`.
     `hasHeight`/elevação NÃO bloqueia passo manual (só afeta empilhamento de
     itens, `queryAdd` ramo de `Thing` não-criatura) — é um mito comum de
     dev OT. `blockPathfind` também não bloqueia o passo manual: ele só faz o
     autoWalk (`g_game.findPath`/A*) recusar a rota (`game.cpp:750`,
     `TILESTATE_BLOCKPATH`), por isso é auditado à parte.

  2. **A intenção visual** (`intent_walkable`): chão que parece piso comum
     (grama/terra/pedra/lama/ponte) com, no máximo, itens "decoração
     caminhável" por cima (flag `walkable: true` no manifesto de origem,
     `tiles.json`/`tiles_decor.json`, ou item de porta) — ou seja, o que um
     jogador OLHANDO para o tile esperaria poder pisar.

Tiles onde as duas respostas divergem são o "travamento fantasma" reportado
pelo usuário. O relatório agrupa por item causador (id + nome), conta
ocorrências e lista amostras de posições.

Também compara, para ids >= 30000 (tiles novos do projeto), as flags REAIS no
OTB com as flags DECLARADAS em tiles.json/tiles_decor.json — divergência aqui
é bug de conversão em `tools/spr/tiles.py`.

Uso:
    .venv/bin/python tools/map/walk_audit.py [valley.otbm] [items.otb]

Sem argumentos, usa os arquivos instalados em
`server/tfs/data/world/valley.otbm` e `server/tfs/data/items/items.otb`.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "spr"))

from otbm import OtbmMap  # noqa: E402
import otb as otb_mod  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DEFAULT_MAP = os.path.join(ROOT, "server", "tfs", "data", "world", "valley.otbm")
DEFAULT_OTB = os.path.join(ROOT, "server", "tfs", "data", "items", "items.otb")
ITEMS_XML = os.path.join(ROOT, "server", "tfs", "data", "items", "items.xml")
TILES_JSON = os.path.join(ROOT, "assets-src", "sprites", "tiles.json")
TILES_DECOR_JSON = os.path.join(ROOT, "assets-src", "sprites", "tiles_decor.json")
ALLOC_JSON = os.path.join(ROOT, "assets-src", "sprites", "allocations.json")

FLAG_BLOCK_SOLID = otb_mod.FLAG_BLOCK_SOLID
FLAG_BLOCK_PATHFIND = otb_mod.FLAG_BLOCK_PATHFIND
FLAG_HAS_HEIGHT = otb_mod.FLAG_HAS_HEIGHT
FLAG_ALWAYSONTOP = otb_mod.FLAG_ALWAYSONTOP

# door ids vanilla usados nas fachadas dos prédios importados (ver build_valley.DOOR_IDS)
VANILLA_DOOR_IDS = {1210, 1209, 1219, 1220, 1540}


# --------------------------------------------------------------------- items.otb
def load_otb_items(path):
    """{server_id: {flags, group_name}} lido diretamente do items.otb real."""
    header, items = otb_mod.parse_items_otb(path)
    by_id = {}
    for it in items:
        by_id[it["server_id"]] = it
    return by_id


# --------------------------------------------------------------------- items.xml
def load_items_xml_names(path):
    """{id: name} via regex simples (não precisamos de XML completo)."""
    import re
    names = {}
    if not os.path.exists(path):
        return names
    with open(path, encoding="utf-8", errors="replace") as fh:
        content = fh.read()
    is_door = set()
    for m in re.finditer(
            r'<item\s+id="(\d+)"(?:\s+fromid="\d+"\s+toid="\d+")?[^>]*\bname="([^"]*)"',
            content):
        sid, name = m.groups()
        names[int(sid)] = name
    for m in re.finditer(r'<item\s+id="(\d+)"[^>]*>(.*?)</item>', content, re.S):
        sid, body = m.groups()
        if 'key="type" value="door"' in body:
            is_door.add(int(sid))
    return names, is_door


# --------------------------------------------------------------------- tiles.json
def load_manifest_flags():
    """{server_id: {"key":..., "group":..., "flags": {...}}} para ids alocados
    em allocations.json (tiles.json + tiles_decor.json), usando as flags
    DECLARADAS (a intenção do manifesto)."""
    alloc = {}
    if os.path.exists(ALLOC_JSON):
        with open(ALLOC_JSON, encoding="utf-8") as fh:
            alloc = json.load(fh).get("by_key", {})

    by_key_spec = {}
    for path in (TILES_JSON, TILES_DECOR_JSON):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            cfg = json.load(fh)
        for t in cfg.get("tiles", []):
            by_key_spec[t["key"]] = t

    by_id = {}
    for key, e in alloc.items():
        spec = by_key_spec.get(key)
        if spec is None:
            continue
        by_id[e["server_id"]] = {
            "key": key,
            "group": spec.get("group"),
            "flags": spec.get("flags") or {},
        }
    return by_id


def expected_otb_flags(spec_flags, num_frames_gt_1=False):
    """Reimplementação de tools/spr/tiles.py:otb_flags, só para comparação."""
    f = 0
    fl = spec_flags or {}
    walkable = fl.get("walkable", True)
    if not walkable:
        f |= FLAG_BLOCK_SOLID
        if fl.get("blocks_pathfind", True):
            f |= FLAG_BLOCK_PATHFIND
    elif fl.get("blocks_pathfind"):
        f |= FLAG_BLOCK_PATHFIND
    alias = {
        "blocks_projectile": otb_mod.FLAG_BLOCK_PROJECTILE,
        "has_height": otb_mod.FLAG_HAS_HEIGHT,
        "useable": otb_mod.FLAG_USEABLE,
        "pickupable": otb_mod.FLAG_PICKUPABLE,
        "movable": otb_mod.FLAG_MOVEABLE,
        "stackable": otb_mod.FLAG_STACKABLE,
        "on_top": otb_mod.FLAG_ALWAYSONTOP,
        "readable": otb_mod.FLAG_READABLE,
        "rotatable": otb_mod.FLAG_ROTATABLE,
        "hangable": otb_mod.FLAG_HANGABLE,
        "vertical": otb_mod.FLAG_VERTICAL,
        "horizontal": otb_mod.FLAG_HORIZONTAL,
        "cannot_decay": otb_mod.FLAG_CANNOTDECAY,
        "allow_dist_read": otb_mod.FLAG_ALLOWDISTREAD,
        "look_through": otb_mod.FLAG_LOOKTHROUGH,
        "force_use": otb_mod.FLAG_FORCEUSE,
        "full_tile": otb_mod.FLAG_FULLTILE,
    }
    for name, bit in alias.items():
        if fl.get(name):
            f |= bit
    if num_frames_gt_1:
        f |= otb_mod.FLAG_ANIMATION
    for name in spec_flags.get("otb_flags", []) if spec_flags else []:
        f |= otb_mod.FLAG_NAMES[name]
    return f


FLAG_BITS = [
    ("blockSolid", FLAG_BLOCK_SOLID),
    ("blockProjectile", otb_mod.FLAG_BLOCK_PROJECTILE),
    ("blockPathfind", FLAG_BLOCK_PATHFIND),
    ("hasHeight", FLAG_HAS_HEIGHT),
    ("alwaysOnTop", FLAG_ALWAYSONTOP),
    ("moveable", otb_mod.FLAG_MOVEABLE),
    ("pickupable", otb_mod.FLAG_PICKUPABLE),
    ("stackable", otb_mod.FLAG_STACKABLE),
]


def flags_repr(f):
    return "+".join(n for n, b in FLAG_BITS if f & b) or "(none)"


# --------------------------------------------------------------------- main
def main():
    map_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MAP
    otb_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OTB

    print("Lendo %s ..." % otb_path)
    otb_items = load_otb_items(otb_path)
    names, door_type_ids = load_items_xml_names(ITEMS_XML)
    manifest = load_manifest_flags()

    print("Lendo %s ..." % map_path)
    m = OtbmMap.read(map_path)

    def item_name(iid):
        if iid in names:
            return names[iid]
        if iid in manifest:
            return manifest[iid]["key"]
        return "?"

    def is_door_like(iid):
        return iid in VANILLA_DOOR_IDS or iid in door_type_ids or (
            manifest.get(iid, {}).get("group") == "door")

    # --------------------------------------------------- 1) ids novos: OTB vs manifesto
    id_bugs = []
    for sid, spec in sorted(manifest.items()):
        real = otb_items.get(sid)
        if real is None:
            id_bugs.append((sid, spec["key"], "AUSENTE no items.otb", None, None))
            continue
        exp = expected_otb_flags(spec["flags"])
        # ignora bits que dependem de runtime/paridade de frames (animation);
        # comparamos só os bits relevantes para caminhabilidade + os declarados
        mask = 0
        for _n, b in FLAG_BITS:
            mask |= b
        real_f = real["flags"] & mask
        exp_f = exp & mask
        if real_f != exp_f:
            id_bugs.append((sid, spec["key"], "flags divergem", exp_f, real_f))

    # --------------------------------------------------- 2) por tile: TFS real vs intenção
    divergences = defaultdict(list)  # (offending_item_id) -> [ (x,y,z, reason) ]
    id_bugs_ids = {sid for sid, *_ in id_bugs}
    n_tiles = 0
    n_walkable_tfs = 0
    n_walkable_intent = 0
    n_diverge = 0

    for (x, y, z), tile in m.tiles.items():
        n_tiles += 1
        ground = tile.ground
        if ground is None:
            continue  # sem chão: nem TFS nem visual consideram "piso"
        ground_type = otb_items.get(ground.id)
        if ground_type is None:
            continue
        ground_blocks = bool(ground_type["flags"] & FLAG_BLOCK_SOLID)

        stack = tile.items  # itens empilhados (sem contar o chão via attr_item)
        # TFS real: bloqueia se ground OU qualquer item da pilha tiver blockSolid
        tfs_blockers = []
        if ground_blocks:
            tfs_blockers.append(ground.id)
        for it in stack:
            it_type = otb_items.get(it.id)
            if it_type and (it_type["flags"] & FLAG_BLOCK_SOLID):
                tfs_blockers.append(it.id)
        tfs_walkable = not tfs_blockers

        # intenção visual: chão comum (grupo ground, não bloqueante no manifesto
        # OU vanilla ground conhecido) + só itens "decoração caminhável"/porta
        # por cima
        intent_blockers = []
        for it in stack:
            if is_door_like(it.id):
                continue
            spec = manifest.get(it.id)
            if spec is not None:
                if not spec["flags"].get("walkable", True):
                    intent_blockers.append(it.id)
            else:
                # item vanilla sem manifesto: usa a MESMA regra do TFS real
                # (não temos "intenção" separada pra vanilla) como intenção
                it_type = otb_items.get(it.id)
                if it_type and (it_type["flags"] & FLAG_BLOCK_SOLID):
                    intent_blockers.append(it.id)
        intent_ground_blocks = ground_blocks  # chão não tem "intenção" separada aqui
        intent_walkable = not intent_ground_blocks and not intent_blockers

        if tfs_walkable:
            n_walkable_tfs += 1
        if intent_walkable:
            n_walkable_intent += 1

        if tfs_walkable != intent_walkable:
            n_diverge += 1
            # motivo: item(ns) que causam bloqueio real mas eram esperados
            # caminháveis (o caso do bug relatado), ou vice-versa
            culprits = tfs_blockers if (not tfs_walkable and intent_walkable) else (
                intent_blockers if (tfs_walkable and not intent_walkable) else [])
            if not culprits:
                culprits = tfs_blockers or intent_blockers or [ground.id]
            for cid in culprits:
                divergences[cid].append((x, y, z))

        # blocks_pathfind (auto-walk trava sem bloquear passo manual)
        pathfind_blockers = []
        all_ids = [ground.id] + [it.id for it in stack]
        for iid in all_ids:
            it_type = otb_items.get(iid)
            if it_type and (it_type["flags"] & FLAG_BLOCK_PATHFIND) and not (
                    it_type["flags"] & FLAG_BLOCK_SOLID):
                pathfind_blockers.append(iid)
        if tfs_walkable and pathfind_blockers:
            for cid in pathfind_blockers:
                divergences[("PATHFIND", cid)].append((x, y, z))

    # --------------------------------------------------------------- relatório
    print()
    print("=" * 78)
    print("AUDITORIA DE CAMINHABILIDADE — %s" % map_path)
    print("=" * 78)
    print("Tiles com chão: %d" % n_tiles)
    print("Caminháveis (regra real do TFS): %d" % n_walkable_tfs)
    print("Caminháveis (intenção visual):   %d" % n_walkable_intent)
    print("Tiles com DIVERGÊNCIA (travamento fantasma ou passagem indevida): %d" % n_diverge)
    print()

    print("-" * 78)
    print("1) Divergências walkable-real vs walkable-visual, agrupadas por item")
    print("-" * 78)
    rows = []
    for key, positions in divergences.items():
        if isinstance(key, tuple):
            kind, iid = key
        else:
            kind, iid = "BLOCKSOLID", key
        rows.append((kind, iid, len(positions), positions))
    rows.sort(key=lambda r: -r[2])
    for kind, iid, count, positions in rows:
        real = otb_items.get(iid)
        flags_s = flags_repr(real["flags"]) if real else "?"
        tag = "[novo id]" if iid in manifest else ""
        print("  %-9s id=%-6d %-28s flags=%-40s n=%-5d %s"
              % (kind, iid, item_name(iid), flags_s, count, tag))
        sample = positions[:5]
        print("      amostras: %s" % ", ".join("(%d,%d,%d)" % p for p in sample))
    if not rows:
        print("  (nenhuma)")
    print()

    print("-" * 78)
    print("2) ids >= 30000 com flags divergentes entre OTB real e tiles.json/tiles_decor.json")
    print("-" * 78)
    if id_bugs:
        for sid, key, why, exp_f, real_f in id_bugs:
            if exp_f is None:
                print("  id=%-6d key=%-30s %s" % (sid, key, why))
            else:
                print("  id=%-6d key=%-30s %s: esperado=%s real=%s"
                      % (sid, key, why, flags_repr(exp_f), flags_repr(real_f)))
    else:
        print("  (nenhuma)")
    print()

    return 0 if not divergences and not id_bugs else 1


if __name__ == "__main__":
    sys.exit(main())
