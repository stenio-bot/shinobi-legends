#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decoração de cenário para o "Vale da Folha" — funções PURAS chamadas pelo
coordenador de dentro de `tools/map/build_valley.py` (este arquivo NÃO edita
`build_valley.py`; só o importa para ler constantes/paletas já existentes).

Cada `place_*` recebe:
  * `b`   — o `Builder` já criado por `build_valley.build(...)` (mesma API:
            `put`, `ground`, `clear_items`, `is_protected`, `cells`, `rng`);
  * `ids` — dict `key -> server_id` com as chaves de
            `assets-src/sprites/tiles_decor.json` (o coordenador monta esse
            dict depois de mesclar `tiles_decor.json` em `tiles.json` e rodar
            `tools/spr/allocate_ids.py`).

Funções:
  * `place_bridge(b, ids)`         — troca o piso de pedra (431) + cerca (1533)
    da travessia do rio pela ponte de madeira nova.
  * `place_forest_decor(b, ids, rng)` — espalha pedras/tocos/flores/tufos/
    cogumelos/galho/poça pela floresta a oeste do rio, com densidade baixa,
    evitando vila, trilhas, clareiras de spawn e áreas protegidas; acrescenta
    pedras soltas ao longo das trilhas de terra.
  * `place_camp_decor(b, ids)`     — barris/caixotes junto às tendas do
    acampamento dos bandidos e um trecho de cerca de madeira nova completando
    a paliçada (fogueira/tendas em si são reaproveitadas do `gen_terrain.py` —
    ids 1428/7605 — e não são reposicionadas aqui, só usadas como referência).
  * `place_village_decor(b, ids)`  — tochas de rua (poste) nas quinas da praça
    e uma placa de trilha perto do portão; tochas + placa extras no hub do
    pântano.

`__main__` monta ids FICTÍCIOS (30900+), roda `build_valley.build(...)` +
`carve_clearings`/`connect_clearings`, aplica as 4 funções acima e valida com o
MESMO BFS de `build_valley.validate` — sem gravar nenhum `.otbm`.
"""
from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TILES_DECOR_JSON = os.path.join(ROOT, "assets-src", "sprites", "tiles_decor.json")


# --------------------------------------------------------------- place_bridge
def place_bridge(b, ids):
    """Ponte de madeira leste-oeste sobre o rio, substituindo piso de pedra
    (431) + cerca (1533) usados hoje em `build_valley.build()` passo 4.

    Usa as constantes RIVER_X0/X1 e BRIDGE_Y0/Y1 de `build_valley` — a mesma
    extensão que o piso de pedra ocupa hoje, para o resto do mapa (trilhas,
    `protect()`, waypoint "Ponte") continuar batendo.
    """
    import build_valley as BV

    x_west = BV.RIVER_X0 - 1
    x_east = BV.RIVER_X1 + 1
    n = 0
    for y in range(BV.BRIDGE_Y0, BV.BRIDGE_Y1 + 1):
        for x in range(x_west, x_east + 1):
            b.clear_items(x, y)
            if x == x_west:
                b.ground(x, y, ids["bridge_wood_head_west"])
            elif x == x_east:
                b.ground(x, y, ids["bridge_wood_head_east"])
            else:
                b.ground(x, y, ids["bridge_wood_center"])
            n += 1
    for x in range(x_west, x_east + 1):
        b.clear_items(x, BV.BRIDGE_Y0 - 1)
        b.clear_items(x, BV.BRIDGE_Y1 + 1)
        b.put(x, BV.BRIDGE_Y0 - 1, ids["bridge_wood_rail_north"])
        b.put(x, BV.BRIDGE_Y1 + 1, ids["bridge_wood_rail_south"])
        n += 2
    b.notes.append("ponte de madeira: %d tiles (chao+corrimao)" % n)
    return n


# ---------------------------------------------------------- place_forest_decor
_FOREST_POOL_KEYS = (
    "rock_small", "rock_medium",
    "tree_stump_0", "tree_stump_1",
    "wildflower_yellow", "wildflower_pink", "wildflower_white",
    "tall_grass_0", "tall_grass_1", "tall_grass_2",
    "mushroom_red", "mushroom_brown",
    "fallen_branch", "small_puddle",
)
_STEPPING_KEYS = ("stepping_stone_0", "stepping_stone_1", "stepping_stone_2")

_FOREST_DENSITY = 0.012          # baixa: 1.2% dos tiles de grama elegíveis
_STEPPING_DENSITY = 0.06         # ao longo das trilhas de terra


def place_forest_decor(b, ids, rng):
    """Espalha decoração pela floresta a oeste do rio (grama), com densidade
    baixa, evitando a vila, as áreas já protegidas (`b.is_protected`) e um raio
    de segurança ao redor de cada clareira de spawn (`CLEARINGS`). Adiciona
    também pedras soltas esparsas sobre as trilhas de terra já carregadas.
    """
    import build_valley as BV

    grass_ids = set(BV.GRASS) if isinstance(BV.GRASS, (list, tuple)) else {BV.GRASS}
    dirt_ids = set(BV.DIRT) if isinstance(BV.DIRT, (list, tuple)) else {BV.DIRT}
    pool = [ids[k] for k in _FOREST_POOL_KEYS]
    stepping_pool = [ids[k] for k in _STEPPING_KEYS]

    def near_clearing(x, y):
        for (_, cx, cy, r) in BV.CLEARINGS:
            if (x - cx) ** 2 + (y - cy) ** 2 <= (r + 2) ** 2:
                return True
        return False

    n_decor = 0
    n_path = 0
    for (x, y), c in list(b.cells.items()):
        if x >= BV.RIVER_X0 or BV.in_village(x, y) or b.is_protected(x, y):
            continue
        if c.ground in grass_ids and not c.items:
            if near_clearing(x, y):
                continue
            if rng.random() < _FOREST_DENSITY:
                b.put(x, y, rng.choice(pool))
                n_decor += 1
        elif c.ground in dirt_ids and not c.items:
            if rng.random() < _STEPPING_DENSITY:
                b.put(x, y, rng.choice(stepping_pool))
                n_path += 1

    b.notes.append("decoracao da floresta: %d itens (+ %d pedras de trilha)"
                    % (n_decor, n_path))
    return n_decor + n_path


# ------------------------------------------------------------- place_camp_decor
def place_camp_decor(b, ids):
    """Barris/caixotes junto às tendas do acampamento dos bandidos + um trecho
    de cerca de madeira nova completando a paliçada ao sul (o norte já tem a
    cerca vanilla de `build_valley.build()` passo 9).

    Fogueira (1428) e tendas (7605) já são colocadas por `build_valley.build()`
    — NÃO são repetidas aqui, só usadas (via `build_valley.CAMP_CENTER`) como
    referência de posição.
    """
    import build_valley as BV

    ccx, ccy = BV.CAMP_CENTER
    n = 0

    # barril/caixote ao lado de cada tenda (build_valley coloca as tendas em
    # ccx+-4, ccy+-3)
    tents = [(ccx - 4, ccy - 3), (ccx + 4, ccy - 3),
             (ccx - 4, ccy + 3), (ccx + 4, ccy + 3)]
    for i, (tx, ty) in enumerate(tents):
        bx = tx + (2 if tx < ccx else -2)
        by = ty
        c = b.cells.get((bx, by))
        if c is not None and not c.items:
            key = "wood_barrel" if i % 2 == 0 else "wood_crate"
            b.put(bx, by, ids[key])
            n += 1

    # caixote junto da fogueira (ccx, ccy-2)
    c = b.cells.get((ccx + 1, ccy - 2))
    if c is not None and not c.items:
        b.put(ccx + 1, ccy - 2, ids["wood_crate"])
        n += 1

    # completa a paliçada ao sul com a cerca de madeira NOVA (o norte já usa a
    # cerca vanilla FENCE_H em build_valley.build())
    for x in range(ccx - 6, ccx + 7, 2):
        if x == ccx:
            continue
        c = b.cells.get((x, ccy + 7))
        if c is not None and not c.items:
            b.put(x, ccy + 7, ids["wood_fence_h"])
            n += 1

    b.notes.append("decoracao do acampamento: %d itens novos "
                    "(fogueira/tendas reaproveitadas, nao duplicadas)" % n)
    return n


# ----------------------------------------------------------- place_village_decor
def place_village_decor(b, ids):
    """Tochas de rua (poste) nas quinas da praça central + placa de trilha
    perto do portão sul; tochas e placa extras no hub de NPCs do pântano.

    As tochas de PAREDE do portão (id 2059, via `build_valley.build()`) e a
    tocha/placa/fogueira já cravadas no hub NÃO são repetidas aqui.
    """
    import build_valley as BV

    n = 0
    px0, py0, px1, py1 = BV.PLAZA
    for (x, y) in ((px0, py0), (px1, py0), (px0, py1), (px1, py1)):
        c = b.cells.get((x, y))
        if c is not None and not c.items:
            b.put(x, y, ids["street_torch"])
            n += 1

    # Playtest arco 2 (2026-09-05): a placa ficava no centro da faixa de saida do Portao Sul
    # ("Nao ha espaco suficiente" ao andar reto para o sul). Fica ao LADO da faixa.
    sign_x = BV.GATE_X[1] + 2
    c = b.cells.get((sign_x, BV.GATE_Y + 2))
    if c is not None and not c.items:
        b.put(sign_x, BV.GATE_Y + 2, ids["signpost_trail"])
        n += 1

    hx0, hy0, hx1, hy1 = BV.HUB
    for (x, y) in ((hx0 + 1, hy1 - 1), (hx1 - 1, hy0 + 1)):
        c = b.cells.get((x, y))
        if c is not None and not c.items:
            b.put(x, y, ids["street_torch"])
            n += 1
    c = b.cells.get((hx0 + 3, hy0 + 1))
    if c is not None and not c.items:
        b.put(hx0 + 3, hy0 + 1, ids["signpost_trail"])
        n += 1

    b.notes.append("tochas de rua e placas novas (vila + hub): %d itens" % n)
    return n


# ------------------------------------------------------------------ __main__
def _load_decor_specs():
    with open(TILES_DECOR_JSON, encoding="utf-8") as fh:
        return json.load(fh)["tiles"]


def _fake_allocate(specs, start=30900):
    """Ids FICTÍCIOS só para o teste de conectividade — nada é gravado em
    `allocations.json` (esse arquivo pertence a `tools/spr/allocate_ids.py`,
    que só lê `assets-src/sprites/tiles.json`)."""
    ids = {}
    sid = start
    for spec in specs:
        ids[spec["key"]] = sid
        sid += 1
    return ids


def _synthetic_types(specs, ids):
    """Mesma técnica de `build_valley.load_imported()`: ItemType mínimo (grupo
    + bloqueio) só para o BFS de conectividade conseguir classificar os ids
    novos — sem precisar do `items.otb` reescrito de verdade."""
    from items_otb import ItemType, FLAG_BLOCK_SOLID, ITEM_GROUP_GROUND

    types = {}
    for spec in specs:
        sid = ids[spec["key"]]
        fl = spec.get("flags") or {}
        flags = 0 if fl.get("walkable", True) else FLAG_BLOCK_SOLID
        group = ITEM_GROUP_GROUND if spec["group"] == "ground" else 0
        types[sid] = ItemType(sid, sid, group, flags)
    return types


def main():
    import build_valley as BV

    specs = _load_decor_specs()
    ids = _fake_allocate(specs)
    decor_types = _synthetic_types(specs, ids)

    types = BV.load_items_otb(BV.ITEMS_OTB)
    tpls, sid, novos = BV.load_imported()
    for k in sorted(n for n in novos if n not in types):
        types[k] = novos[k]
    types.update(decor_types)

    b, npcs = BV.build(tpls, sid)
    BV.carve_clearings(b)
    BV.connect_clearings(b)

    place_bridge(b, ids)
    place_forest_decor(b, ids, b.rng)
    place_camp_decor(b, ids)
    place_village_decor(b, ids)

    sf = BV.build_spawns(b, npcs)
    problems, walk, reach = BV.validate(b, types, sf, npcs)

    print("tiles_decor.json: %d tiles, ids ficticios %d..%d"
          % (len(specs), min(ids.values()), max(ids.values())))
    for n in b.notes:
        print("  nota:", n)
    if problems:
        print("TESTE DE CONECTIVIDADE FALHOU:")
        for p in problems[:40]:
            print("  -", p)
        print("  (%d problemas)" % len(problems))
        return 1

    print("TESTE DE CONECTIVIDADE OK")
    print("  caminhaveis ...... %d  alcancaveis do templo: %d (%.1f%%)"
          % (len(walk), len(reach), 100.0 * len(reach) / len(walk)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
