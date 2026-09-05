#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validador cruzado do mundo gerado (Lote M da auditoria de história, item 6).

Lê `data/npcs/*.json`, `data/tasks.json`, `data/dailies.json`,
`data/monsters/*.json` e o artefato final (`server/generated/world/
valley-spawn.xml` + `valley.otbm`) e FALHA (exit 1) se:

  (a) algum `monster_id` exigido por `objective.kill` de uma missão (`quests`
      de `data/npcs/*.json`), tarefa (`data/tasks.json`) ou missão diária
      (`data/dailies.json`) não tem NENHUM spawn no XML final — exceto os
      listados em `SUMMON_ONLY_MONSTERS` (criaturas que só existem como
      reforço de fase de outro boss — `phases[].summons` em `data/monsters/
      *.json` — nunca como spawn solto; documentadas abaixo com o motivo).

  (b) algum NPC com `quests` (não vazio) ou `type == "shop"` em `data/npcs/
      *.json` não aparece (pelo nome exato) no XML final — o mesmo bug que
      deixou Ancião Kaito/Tsubaki/Mestra Yuki/Ferreiro Genzo invisíveis antes
      do Lote M (docs/design/auditoria-historia.md, itens B1/C1).

  (c) algum NPC ou monstro do XML final está numa posição que o próprio
      `build_valley.py` não consideraria caminhável — chão bloqueante ou
      item empilhado com `blockSolid` (mesma regra usada por
      `tools/map/walk_audit.py`, que reproduz `Tile::queryAdd` do TFS).
      Monstro exige a célula EXATA caminhável; NPC aceita um raio de 3 tiles
      (mesmo critério de "conversa de perto" usado por
      `build_valley.validate()`, pensado pra NPC de loja atrás de balcão).

Saída em pt-BR. Exit 0 se nenhum problema, exit 1 se qualquer FALHA (avisos
não fazem o script falhar).

Uso:
    .venv/bin/python tools/map/validate_world.py

Roda DEPOIS de `tools/map/build_valley.py` (que gera o `.otbm`/`-spawn.xml`
em `server/generated/world/`) — ver docs/sistemas/mapas.md e CLAUDE.md.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "spr"))

from otbm import OtbmMap  # noqa: E402
import otb as otb_mod  # noqa: E402
import walk_audit  # noqa: E402  (reaproveita load_otb_items)

ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
DATA = os.path.join(ROOT, "data")
WORLD_DIR = os.path.join(ROOT, "server", "generated", "world")
SPAWN_XML = os.path.join(WORLD_DIR, "valley-spawn.xml")
MAP_OTBM = os.path.join(WORLD_DIR, "valley.otbm")
ITEMS_OTB = os.path.join(ROOT, "server", "tfs", "data", "items", "items.otb")

FLAG_BLOCK_SOLID = otb_mod.FLAG_BLOCK_SOLID

# Monstros que SÓ existem como reforço de fase de outro boss (data/monsters/
# *.json, `phases[].summons`) — nunca têm (nem devem ter) spawn solto no
# mapa. Checado nesta missão (Lote M): nenhum dos dois é hoje alvo de
# `objective.kill` de nenhuma quest/task/daily — a lista existe como
# salvaguarda documentada, pra não virar falso-positivo se um dia alguém
# criar uma missão pra caçá-los sem perceber que são summon-only.
SUMMON_ONLY_MONSTERS = {
    "invoked_path",   # "Caminho Invocado" — reforço da fase final do Covil (akatsuki_lair.json)
    "crimson_echo",   # "Eco Carmesim" — reforço da fase final do Covil (akatsuki_lair.json)
}


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def collect_npcs():
    """[{id, name, file, has_quests, has_shop}, ...] de data/npcs/*.json."""
    out = []
    for f in sorted(glob.glob(os.path.join(DATA, "npcs", "*.json"))):
        for npc in _load_json(f):
            out.append({
                "file": os.path.relpath(f, ROOT),
                "id": npc["id"],
                "name": npc["name"],
                "has_quests": bool(npc.get("quests")),
                "has_shop": npc.get("type") == "shop",
            })
    return out


def collect_monsters():
    """{monster_id: (name, arquivo, is_boss)} de data/monsters/*.json."""
    out = {}
    for f in sorted(glob.glob(os.path.join(DATA, "monsters", "*.json"))):
        for m in _load_json(f):
            out[m["id"]] = (m["name"], os.path.relpath(f, ROOT), bool(m.get("boss")))
    return out


def collect_kill_targets():
    """{monster_id: [descrição da fonte, ...]} — quests (data/npcs/*.json,
    objective.kind == "kill") + data/tasks.json + data/dailies.json."""
    targets = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(DATA, "npcs", "*.json"))):
        for npc in _load_json(f):
            for q in npc.get("quests", []):
                obj = q.get("objective", {})
                if obj.get("kind") == "kill" and obj.get("kill"):
                    targets[obj["kill"]].append(
                        "%s: %s.%s" % (os.path.relpath(f, ROOT), npc["id"], q["id"]))
    for fname in ("tasks.json", "dailies.json"):
        for t in _load_json(os.path.join(DATA, fname)):
            mid = t.get("monster_id")
            if mid:
                targets[mid].append("data/%s: %s" % (fname, t["id"]))
    return targets


def parse_spawn_xml(path):
    """-> (nomes_de_monstro:set, nomes_de_npc:set, posicoes:[(kind,name,x,y,z)])."""
    tree = ET.parse(path)
    monster_names = set()
    npc_names = set()
    positions = []
    for spawn in tree.getroot().findall("spawn"):
        cx = int(spawn.get("centerx"))
        cy = int(spawn.get("centery"))
        cz = int(spawn.get("centerz"))
        for mon in spawn.findall("monster"):
            name = mon.get("name")
            monster_names.add(name)
            x = cx + int(mon.get("x", 0))
            y = cy + int(mon.get("y", 0))
            positions.append(("monstro", name, x, y, cz))
        for npc in spawn.findall("npc"):
            name = npc.get("name")
            npc_names.add(name)
            x = cx + int(npc.get("x", 0))
            y = cy + int(npc.get("y", 0))
            positions.append(("NPC", name, x, y, cz))
    return monster_names, npc_names, positions


def walkable_set(map_path, otb_path):
    """{(x,y,z)} — mesma regra de tools/map/walk_audit.py (Tile::queryAdd real
    do TFS): chão precisa existir e não ser blockSolid; bloqueado se QUALQUER
    item empilhado tiver blockSolid."""
    otb_items = walk_audit.load_otb_items(otb_path)
    m = OtbmMap.read(map_path)
    walk = set()
    for (x, y, z), tile in m.tiles.items():
        ground = tile.ground
        if ground is None:
            continue
        gtype = otb_items.get(ground.id)
        if gtype is None or (gtype["flags"] & FLAG_BLOCK_SOLID):
            continue
        blocked = False
        for it in tile.items:
            it_type = otb_items.get(it.id)
            if it_type and (it_type["flags"] & FLAG_BLOCK_SOLID):
                blocked = True
                break
        if not blocked:
            walk.add((x, y, z))
    return walk


def main():
    problems = []
    warnings = []

    if not os.path.exists(SPAWN_XML):
        print("ERRO: %s não existe — rode `.venv/bin/python tools/map/build_valley.py` "
              "primeiro." % os.path.relpath(SPAWN_XML, ROOT))
        return 1

    print("Lendo data/npcs/*.json, data/monsters/*.json, data/tasks.json, "
          "data/dailies.json ...")
    npcs = collect_npcs()
    monsters = collect_monsters()
    kill_targets = collect_kill_targets()

    print("Lendo %s ..." % os.path.relpath(SPAWN_XML, ROOT))
    spawn_monster_names, spawn_npc_names, positions = parse_spawn_xml(SPAWN_XML)

    # -- (a) monster_id de objective.kill sem spawn no mapa ------------------
    for mid, sources in sorted(kill_targets.items()):
        if mid in SUMMON_ONLY_MONSTERS:
            continue
        info = monsters.get(mid)
        if info is None:
            problems.append(
                "monstro '%s' (usado em %s) não existe em NENHUM data/monsters/*.json"
                % (mid, sources[0]))
            continue
        name, _file, _is_boss = info
        if name not in spawn_monster_names:
            problems.append(
                "monstro '%s' (\"%s\") é exigido por %d missão(ões)/tarefa(s) "
                "(ex.: %s) mas NÃO tem nenhum spawn em %s"
                % (mid, name, len(sources), sources[0], os.path.relpath(SPAWN_XML, ROOT)))

    # -- (b) NPC com quests/shop sem spawn no mapa ---------------------------
    for npc in npcs:
        if not (npc["has_quests"] or npc["has_shop"]):
            continue
        if npc["name"] not in spawn_npc_names:
            tipo = "quests" if npc["has_quests"] else "loja (type=shop)"
            problems.append(
                "NPC '%s' (\"%s\", %s) tem %s mas NÃO está em %s"
                % (npc["id"], npc["name"], npc["file"], tipo,
                   os.path.relpath(SPAWN_XML, ROOT)))

    # NPCs sem quests/shop (mestres de tarefa, quadro de diárias etc.) fora
    # do critério (b) — vira só aviso, não falha, mas ajuda a achar buracos.
    for npc in npcs:
        if npc["has_quests"] or npc["has_shop"]:
            continue
        if npc["name"] not in spawn_npc_names:
            warnings.append(
                "NPC '%s' (\"%s\") não tem quests/shop (fora do critério (b)) e "
                "também não está em %s — só aviso"
                % (npc["id"], npc["name"], os.path.relpath(SPAWN_XML, ROOT)))

    # -- (c) caminhabilidade de cada NPC/monstro do mapa ---------------------
    if not os.path.exists(MAP_OTBM):
        problems.append("%s não existe — rode `.venv/bin/python tools/map/build_valley.py` "
                         "primeiro" % os.path.relpath(MAP_OTBM, ROOT))
    elif not os.path.exists(ITEMS_OTB):
        problems.append("%s não existe (items.otb do servidor)" % os.path.relpath(ITEMS_OTB, ROOT))
    else:
        walk = walkable_set(MAP_OTBM, ITEMS_OTB)

        def reach_radius(x, y, z, r):
            return any((x + dx, y + dy, z) in walk
                       for dx in range(-r, r + 1) for dy in range(-r, r + 1))

        for (kind, name, x, y, z) in positions:
            radius = 3 if kind == "NPC" else 0
            if not reach_radius(x, y, z, radius):
                problems.append(
                    "%s '%s' em (%d,%d,%d) não está em tile caminhável "
                    "(nem a %d tile(s) de distância — regra real do TFS, "
                    "ver tools/map/walk_audit.py)" % (kind, name, x, y, z, radius))

    # --------------------------------------------------------------- saída
    print()
    print("=" * 78)
    print("VALIDADOR CRUZADO DO MUNDO (tools/map/validate_world.py)")
    print("=" * 78)
    print("  NPCs em data/npcs/*.json ................ %d" % len(npcs))
    print("  monster_id exigidos por missão/tarefa .... %d" % len(kill_targets))
    print("  monstros no spawn.xml final .............. %d nomes distintos"
          % len(spawn_monster_names))
    print("  NPCs no spawn.xml final ................... %d nomes distintos"
          % len(spawn_npc_names))

    if warnings:
        print("\nAVISOS (%d, não falham o build):" % len(warnings))
        for w in warnings:
            print("  - %s" % w)

    if problems:
        print("\nFALHAS (%d):" % len(problems))
        for p in problems:
            print("  - %s" % p)
        print("\nRESULTADO: FALHOU — %d problema(s) encontrado(s)." % len(problems))
        return 1

    print("\nRESULTADO: OK — nenhuma falha encontrada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
