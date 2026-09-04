#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gerador do mapa "Vale da Folha" (valley.otbm) no estilo Tibia clássico.

Usa itens vanilla do items.otb/items.xml do TFS 1.4.2 MAIS os tiles próprios de
`assets-src/sprites/tiles.json` (prédios importados, ids >= 30000). Esses últimos
só existem no items.otb depois de `tools/spr/build_assets.py`; até lá o gerador
valida contra as flags declaradas em tiles.json e avisa na saída.

Saída (em server/generated/world/):
    valley.otbm        mapa 1024x1024, conteúdo no andar 7
    valley-spawn.xml   monstros + NPCs
    valley-house.xml   vazio (o mapa não tem casas compráveis)

Rode com:
    .venv/bin/python tools/map/build_valley.py

O build FALHA se algum item usado não existir no items.otb, se algum chão não
for do grupo "ground" ou se algum spawn/NPC/templo não for alcançável a pé a
partir do templo (BFS sobre tiles caminháveis).

Ordem correta ao mexer nos prédios importados:
    .venv/bin/python tools/spr/slice_buildings.py   # fatia a folha
    .venv/bin/python tools/spr/allocate_ids.py      # aloca os ids
    .venv/bin/python tools/map/build_valley.py      # gera o mapa
    .venv/bin/python tools/spr/build_assets.py      # grava items.otb/.dat/.spr
    tools/install_generated.sh                      # instala no servidor
"""

from __future__ import annotations

import os
import random
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json

from otbm import (Item, OtbmMap, TILEFLAG_NOLOGOUT, TILEFLAG_PROTECTIONZONE)
from items_otb import ItemType, load_items_otb, FLAG_BLOCK_SOLID, ITEM_GROUP_GROUND
from spawn_xml import SpawnFile, write_empty_house_file

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ITEMS_OTB = os.path.join(ROOT, "server", "tfs", "data", "items", "items.otb")
OUT_DIR = os.path.join(ROOT, "server", "generated", "world")
SPRITES = os.path.join(ROOT, "assets-src", "sprites")
TILES_JSON = os.path.join(SPRITES, "tiles.json")
ALLOC_JSON = os.path.join(SPRITES, "allocations.json")
BUILDINGS_JSON = os.path.join(SPRITES, "buildings.json")

SEED = 1337
# O conteúdo vai de (1000,1000) a (1199,1119); um mapa 1024x1024 não comportaria
# essas coordenadas no Remere's Map Editor (o TFS ignora width/height, mas o RME
# usa para delimitar o canvas). Por isso o cabeçalho declara 2048x2048.
MAP_W = MAP_H = 2048
FLOOR = 7

# ------------------------------------------------------------------ paleta
# Todos os ids são server ids vanilla (server/tfs/data/items/items.xml).

GRASS = [4526, 4527, 4528, 4529, 4530, 4531]     # grass
DIRT = [351, 352, 353]                           # dirt floor (trilhas)
COBBLE = [19744, 19745, 19746, 19747, 19748]     # cobblestone (ruas)
STONE_FLOOR = 431                                # stone floor (praça/templo)
WOOD_FLOOR = 405                                 # wooden floor (interiores)
MUD = [19947, 354, 355, 11145]                   # swamp mud / muddy floor
WATER = 4608                                     # shallow water (bloqueia)

TREES = [2700, 2701, 2702, 2707, 2712]           # fir/sycamore/willow/beech/pine
DEAD_TREES = [2709, 2713, 2714, 2715, 2716]      # dead tree
BUSHES = [2767, 2784, 3986]                      # bush / dry bush / thorn bush
SWAMP_PLANTS = [2771, 2774, 2775]                # mire sprout / reed / lilly

STONE_WALL_H = 1049                              # parede de pedra leste-oeste
STONE_WALL_V = 1050                              # parede de pedra norte-sul
STONE_WALL_C = 1051                              # canto de pedra
WOOD_WALL_H = 5261
WOOD_WALL_V = 5262
WOOD_WALL_C = 5263
WOOD_WINDOW = 5277

DOOR_STONE_H = 1210                              # closed door (destrancada)
DOOR_STONE_V = 1213
DOOR_WOOD_H = 5099
DOOR_WOOD_V = 5101

TORCH = 2059                                     # lit torch bearer
CAMPFIRE = 1428
TENT = 7605
DUMMY = 5787                                     # training dummy
DEPOT = 2594                                     # depot chest
SIGN = 1440
FENCE_H = 1533
FENCE_V = 1534

#: itens que bloqueiam mas podem ser abertos — passáveis no BFS
DOOR_IDS = {DOOR_STONE_H, DOOR_STONE_V, DOOR_WOOD_H, DOOR_WOOD_V, 1540}

# ------------------------------------------------------------------ layout
# Conteúdo em x 1000..1199, y 1000..1119 (200x120) no andar 7.

X0, Y0 = 1000, 1000
X1, Y1 = 1199, 1119

# Vila da Folha: muralha em x 1010..1049, y 1030..1069 (40x40)
V_X0, V_Y0, V_X1, V_Y1 = 1010, 1030, 1049, 1069
GATE_X = (1028, 1030)
GATE_Y = V_Y1

# Praça central e templo
PLAZA = (1022, 1036, 1036, 1052)                 # x0,y0,x1,y1
TEMPLE = (1025, 1038, 1033, 1046)
TEMPLE_DOOR = (1029, 1046)
TEMPLE_POS = (1029, 1042, FLOOR)

# Ruas de cobblestone
ROAD_V = (1028, 1030)                            # faixa vertical
ROAD_H = (1054, 1056)                            # faixa horizontal

# Rio (norte-sul) e ponte
RIVER_X0, RIVER_X1 = 1125, 1129
BRIDGE_Y0, BRIDGE_Y1 = 1058, 1061

# Floresta da Morte a leste do rio
DEATH_X0 = 1130

# Hub de NPCs na entrada da Floresta da Morte
HUB = (1131, 1055, 1139, 1064)

# Torre de pedra (paredes 5x5, interior 3x3)
TOWER = (1163, 1058, 1167, 1062)
TOWER_DOOR = (1163, 1060)
TOWER_CENTER = (1165, 1060)

# Acampamento dos bandidos
CAMP_CENTER = (1100, 1100)


class Cell:
    __slots__ = ("ground", "items", "flags", "protected")

    def __init__(self):
        self.ground = None
        self.items = []
        self.flags = 0


class Builder:
    def __init__(self, seed=SEED):
        self.rng = random.Random(seed)
        self.cells = {}
        self.notes = []
        #: retângulos que trilhas/clareiras nunca podem sobrescrever
        self.protected = []

    def protect(self, x0, y0, x1, y1):
        self.protected.append((x0, y0, x1, y1))

    def is_protected(self, x, y):
        for (x0, y0, x1, y1) in self.protected:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return True
        return False

    # -- primitivas ---------------------------------------------------------
    def cell(self, x, y):
        c = self.cells.get((x, y))
        if c is None:
            c = Cell()
            self.cells[(x, y)] = c
        return c

    def ground(self, x, y, item_id):
        self.cell(x, y).ground = self.pick(item_id)

    def pick(self, item_id):
        return self.rng.choice(item_id) if isinstance(item_id, (list, tuple)) else item_id

    def put(self, x, y, item_id, **kwargs):
        c = self.cell(x, y)
        it = Item(self.pick(item_id), **kwargs)
        c.items.append(it)
        return it

    def clear_items(self, x, y):
        c = self.cells.get((x, y))
        if c:
            c.items = []

    def fill(self, x0, y0, x1, y1, item_id):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.ground(x, y, item_id)

    def flag_rect(self, x0, y0, x1, y1, flags):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x, y) in self.cells:
                    self.cells[(x, y)].flags |= flags

    def walls(self, x0, y0, x1, y1, h_id, v_id, c_id, doors=()):
        """Desenha um retângulo de paredes; ``doors`` são posições substituídas."""
        doors = set(doors)
        for x in range(x0, x1 + 1):
            for y in (y0, y1):
                if (x, y) in doors:
                    continue
                self.clear_items(x, y)
                self.put(x, y, c_id if x in (x0, x1) else h_id)
        for y in range(y0 + 1, y1):
            for x in (x0, x1):
                if (x, y) in doors:
                    continue
                self.clear_items(x, y)
                self.put(x, y, v_id)

    def clear_rect(self, x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.clear_items(x, y)

    def building(self, x0, y0, x1, y1, floor_id, wood=True, doors=(), windows=()):
        self.clear_rect(x0, y0, x1, y1)
        self.fill(x0, y0, x1, y1, floor_id)
        h, v, c = (WOOD_WALL_H, WOOD_WALL_V, WOOD_WALL_C) if wood else \
                  (STONE_WALL_H, STONE_WALL_V, STONE_WALL_C)
        self.walls(x0, y0, x1, y1, h, v, c, doors=doors)
        for (wx, wy) in windows:
            self.clear_items(wx, wy)
            self.put(wx, wy, WOOD_WINDOW if wood else STONE_WALL_H)
        for (dx, dy) in doors:
            self.clear_items(dx, dy)
            door = DOOR_WOOD_H if wood else DOOR_STONE_H
            if dx in (x0, x1):
                door = DOOR_WOOD_V if wood else DOOR_STONE_V
            self.put(dx, dy, door)

    def blob(self, cx, cy, radius, item_ids, density, avoid=None):
        """Mancha circular de decoração (árvores/arbustos)."""
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 > radius * radius:
                    continue
                if (x, y) not in self.cells:
                    continue
                if avoid and avoid(x, y):
                    continue
                if self.cells[(x, y)].items:
                    continue
                if self.rng.random() < density:
                    self.put(x, y, item_ids)

    def path(self, x0, y0, x1, y1, item_id, width=1):
        """Trilha reta (horizontal ou vertical) de largura ``width``."""
        half = width // 2
        if x0 == x1:
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for dx in range(-half, width - half):
                    if self.is_protected(x0 + dx, y):
                        continue
                    self.ground(x0 + dx, y, item_id)
                    self.clear_items(x0 + dx, y)
        else:
            for x in range(min(x0, x1), max(x0, x1) + 1):
                for dy in range(-half, width - half):
                    if self.is_protected(x, y0 + dy):
                        continue
                    self.ground(x, y0 + dy, item_id)
                    self.clear_items(x, y0 + dy)


# ------------------------------------------------- prédios importados (tiles.json)
# Os tiles bld_* vêm de tools/spr/slice_buildings.py. Os server ids saem de
# assets-src/sprites/allocations.json e SÓ existem no items.otb depois de
# `.venv/bin/python tools/spr/build_assets.py` — por isso a validação de "id
# existe no OTB" é relaxada para ids >= 30000 que estejam em allocations.json
# (ver `synthetic_types`), com aviso na saída.

MIN_NEW_SERVER_ID = 30000


def load_imported():
    """Devolve (templates, sid_por_key, tipos_sinteticos)."""
    with open(BUILDINGS_JSON, encoding="utf-8") as fh:
        tpls = json.load(fh)["buildings"]
    with open(ALLOC_JSON, encoding="utf-8") as fh:
        alloc = json.load(fh)["by_key"]
    with open(TILES_JSON, encoding="utf-8") as fh:
        specs = {t["key"]: t for t in json.load(fh)["tiles"]}

    sid = {}
    types = {}
    for key, spec in specs.items():
        e = alloc.get(key)
        if e is None:
            continue
        s_id = e["server_id"]
        sid[key] = s_id
        if s_id < MIN_NEW_SERVER_ID:
            continue
        fl = spec.get("flags") or {}
        flags = 0 if fl.get("walkable", True) else FLAG_BLOCK_SOLID
        group = ITEM_GROUP_GROUND if spec["group"] == "ground" else 0
        types[s_id] = ItemType(s_id, e["client_id"], group, flags)
    return tpls, sid, types


def stamp_building(b, tpls, sid, key, x, y, ground=None):
    """Estampa o template ``key`` com o canto INFERIOR ESQUERDO em (x, y).

    A matriz de ``buildings.json`` é linhas x colunas do topo para a base, então
    a célula (col, row) cai em (x + col, y - (altura - 1 - row)).
    Limpa os itens de todo o retângulo e, se ``ground`` for dado, troca o chão.
    Devolve a posição absoluta da porta (ou None).
    """
    tpl = tpls[key]
    h, w = tpl["height"], tpl["width"]
    for row in range(h):
        for col in range(w):
            px, py = x + col, y - (h - 1 - row)
            b.clear_items(px, py)
            if ground is not None:
                b.ground(px, py, ground)
    for row in range(h):
        for col in range(w):
            tk = tpl["grid"][row][col]
            if tk is None:
                continue
            b.put(x + col, y - (h - 1 - row), sid[tk])
    if not tpl["door"]:
        return None
    dc, dr = tpl["door"]
    return (x + dc, y - (h - 1 - dr))


# --------------------------------------------------------------- construção

def in_village(x, y):
    return V_X0 <= x <= V_X1 and V_Y0 <= y <= V_Y1


def build(tpls, sid):
    b = Builder()
    rng = b.rng
    b.protect(V_X0, V_Y0, V_X1, V_Y1)                              # vila
    b.protect(TOWER[0], TOWER[1], TOWER[2], TOWER[3])              # torre
    b.protect(HUB[0] - 1, HUB[1] - 1, HUB[2] + 1, HUB[3] + 1)      # hub NPC
    b.protect(RIVER_X0 - 1, BRIDGE_Y0 - 1, RIVER_X1 + 1, BRIDGE_Y1 + 1)  # ponte
    b.protect(CAMP_CENTER[0] - 5, CAMP_CENTER[1] - 5,
              CAMP_CENTER[0] + 5, CAMP_CENTER[1] + 5)              # acampamento

    # 1. base: floresta (grama) a oeste do rio, pântano a leste
    for y in range(Y0, Y1 + 1):
        for x in range(X0, X1 + 1):
            if x >= DEATH_X0:
                b.ground(x, y, MUD)
            elif RIVER_X0 <= x <= RIVER_X1:
                b.ground(x, y, WATER)
            else:
                b.ground(x, y, GRASS)

    # 2. manchas densas de árvores na floresta (nunca na vila)
    forest_spots = []
    for _ in range(120):
        cx = rng.randint(X0 + 3, RIVER_X0 - 4)
        cy = rng.randint(Y0 + 3, Y1 - 3)
        if in_village(cx, cy):
            continue
        forest_spots.append((cx, cy, rng.randint(3, 7)))
    for (cx, cy, r) in forest_spots:
        b.blob(cx, cy, r, TREES, 0.45, avoid=lambda x, y: in_village(x, y))
    for _ in range(80):
        cx = rng.randint(X0 + 2, RIVER_X0 - 3)
        cy = rng.randint(Y0 + 2, Y1 - 2)
        if in_village(cx, cy):
            continue
        b.blob(cx, cy, 3, BUSHES, 0.25, avoid=lambda x, y: in_village(x, y))

    # 3. Floresta da Morte: árvores mortas, juncos e poças
    for _ in range(140):
        cx = rng.randint(DEATH_X0 + 2, X1 - 2)
        cy = rng.randint(Y0 + 2, Y1 - 2)
        b.blob(cx, cy, rng.randint(2, 5), DEAD_TREES, 0.40)
    for _ in range(70):
        cx = rng.randint(DEATH_X0 + 2, X1 - 2)
        cy = rng.randint(Y0 + 2, Y1 - 2)
        b.blob(cx, cy, 2, SWAMP_PLANTS, 0.30)
    puddles = 0
    for _ in range(60):
        cx = rng.randint(DEATH_X0 + 4, X1 - 4)
        cy = rng.randint(Y0 + 4, Y1 - 4)
        r = rng.randint(1, 2)
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    b.ground(x, y, WATER)
                    b.clear_items(x, y)
                    puddles += 1
    b.notes.append("pocas de agua na Floresta da Morte: %d tiles" % puddles)

    # 4. ponte sobre o rio
    for y in range(BRIDGE_Y0, BRIDGE_Y1 + 1):
        for x in range(RIVER_X0 - 1, RIVER_X1 + 2):
            b.ground(x, y, STONE_FLOOR)
            b.clear_items(x, y)
    for x in range(RIVER_X0 - 1, RIVER_X1 + 2):
        b.put(x, BRIDGE_Y0 - 1, FENCE_H)
        b.put(x, BRIDGE_Y1 + 1, FENCE_H)
    # limpa o rio sob os parapeitos para não bloquear visualmente a passagem
    for x in range(RIVER_X0, RIVER_X1 + 1):
        for y in (BRIDGE_Y0 - 1, BRIDGE_Y1 + 1):
            b.ground(x, y, WATER)

    # 5. trilhas de terra (anel ao redor da vila + eixos principais)
    b.path(1005, 1025, 1055, 1025, DIRT, width=2)
    b.path(1005, 1075, 1055, 1075, DIRT, width=2)
    b.path(1005, 1025, 1005, 1075, DIRT, width=2)
    b.path(1055, 1025, 1055, 1075, DIRT, width=2)
    b.path(1029, GATE_Y + 1, 1029, 1090, DIRT, width=3)
    b.path(1029, 1090, 1100, 1090, DIRT, width=3)
    b.path(1100, 1090, 1100, CAMP_CENTER[1], DIRT, width=3)
    b.path(1060, 1090, 1060, 1060, DIRT, width=3)
    b.path(1060, 1060, RIVER_X0 - 2, 1060, DIRT, width=3)
    b.path(RIVER_X1 + 2, 1060, HUB[0] - 1, 1060, DIRT, width=3)
    b.path(HUB[2] + 1, 1060, TOWER[0] - 1, 1060, DIRT, width=3)

    # 6. Vila da Folha ---------------------------------------------------
    b.fill(V_X0, V_Y0, V_X1, V_Y1, DIRT)

    gate_tiles = {(x, GATE_Y) for x in range(GATE_X[0], GATE_X[1] + 1)}
    b.walls(V_X0, V_Y0, V_X1, V_Y1, STONE_WALL_H, STONE_WALL_V, STONE_WALL_C,
            doors=gate_tiles)
    for (gx, gy) in gate_tiles:
        b.ground(gx, gy, COBBLE)
    # tochas na muralha, ao lado do portão
    b.put(GATE_X[0] - 1, GATE_Y, TORCH)
    b.put(GATE_X[1] + 1, GATE_Y, TORCH)

    # ruas
    for x in range(ROAD_V[0], ROAD_V[1] + 1):
        for y in range(V_Y0 + 1, V_Y1):
            if PLAZA[1] <= y <= PLAZA[3]:
                continue
            b.ground(x, y, COBBLE)
    for y in range(ROAD_H[0], ROAD_H[1] + 1):
        for x in range(V_X0 + 1, V_X1):
            b.ground(x, y, COBBLE)

    # praça central
    b.fill(PLAZA[0], PLAZA[1], PLAZA[2], PLAZA[3], STONE_FLOOR)

    # templo (zona de proteção)
    b.building(TEMPLE[0], TEMPLE[1], TEMPLE[2], TEMPLE[3], STONE_FLOOR,
               wood=False, doors=[TEMPLE_DOOR])
    b.flag_rect(PLAZA[0], PLAZA[1], PLAZA[2], PLAZA[3],
                TILEFLAG_PROTECTIONZONE)
    b.flag_rect(TEMPLE[0], TEMPLE[1], TEMPLE[2], TEMPLE[3],
                TILEFLAG_PROTECTIONZONE | TILEFLAG_NOLOGOUT)
    b.put(TEMPLE[0] + 1, TEMPLE[3] + 1, TORCH)
    b.put(TEMPLE[2] - 1, TEMPLE[3] + 1, TORCH)
    b.put(PLAZA[0] + 1, PLAZA[1] + 1, SIGN, text="Vila da Folha - Templo da Chama")

    # depósito, junto à praça
    b.put(PLAZA[0] + 2, PLAZA[3] - 1, DEPOT, depot_id=1)
    b.put(PLAZA[0] + 1, PLAZA[3] - 1, SIGN, text="Deposito da Vila")

    # --- prédios importados (village_buildings.png) ---------------------
    # Substituem as casas/lojas de parede de madeira vanilla. São FACHADAS:
    # tudo bloqueia menos a porta, e não há interior — por isso os NPCs de loja
    # ficam na RUA, um tile à frente da porta.
    npcs = []

    # torre do líder ao norte da praça (o templo continua sendo a PZ)
    tower_door = stamp_building(b, tpls, sid, "tower", 1027, 1036)
    b.put(1026, 1036, sid["bld_grass_patch_0_0"])
    b.put(1032, 1036, sid["bld_grass_patch_0_0"])

    # casas do anel norte
    stamp_building(b, tpls, sid, "big_house", 1013, 1036, ground=DIRT)
    stamp_building(b, tpls, sid, "house_green", 1040, 1036, ground=DIRT)

    # lojas com NPC (nome, template, x, y do canto inferior esquerdo)
    for (name, tpl_key, sx, sy) in [
            ("Ichiro, o Mercador", "newbie_shop", 1014, 1043),
            ("Mestre Hayato", "ramen_shop", 1040, 1044),
            ("Capitã Rin", "blue_shop", 1040, 1051)]:
        door = stamp_building(b, tpls, sid, tpl_key, sx, sy, ground=DIRT)
        b.clear_items(door[0], door[1] + 1)
        b.put(door[0] - 1, door[1] + 1, TORCH)
        npcs.append((name, (door[0], door[1] + 1)))

    # taverna, prisão e casas do anel sul
    stamp_building(b, tpls, sid, "prison", 1013, 1063, ground=DIRT)
    stamp_building(b, tpls, sid, "blue_house", 1021, 1063, ground=DIRT)
    stamp_building(b, tpls, sid, "tavern", 1032, 1063, ground=DIRT)
    stamp_building(b, tpls, sid, "roof_orange", 1037, 1063, ground=DIRT)
    stamp_building(b, tpls, sid, "blue_house", 1041, 1063, ground=DIRT)

    # postes e vegetação importada
    stamp_building(b, tpls, sid, "lamp_post", 1021, 1053)
    stamp_building(b, tpls, sid, "lamp_post", 1037, 1053)
    stamp_building(b, tpls, sid, "tree", 1017, 1045)
    stamp_building(b, tpls, sid, "bushes", 1022, 1053)
    stamp_building(b, tpls, sid, "bushes", 1034, 1053)
    stamp_building(b, tpls, sid, "bushes", 1025, 1067)

    b.notes.append("porta da torre do lider em %r" % (tower_door,))

    # campo de treino
    b.fill(1013, 1046, 1020, 1052, DIRT)
    for (dx, dy) in [(1014, 1047), (1017, 1047), (1020, 1047),
                     (1014, 1051), (1017, 1051), (1020, 1051)]:
        b.clear_items(dx, dy)
        b.put(dx, dy, DUMMY)
    b.put(1013, 1045, SIGN, text="Campo de treino dos Genin")

    # tochas nas ruas
    for y in range(V_Y0 + 4, V_Y1, 8):
        for x in (ROAD_V[0] - 1, ROAD_V[1] + 1):
            if not b.cells[(x, y)].items and not (PLAZA[1] <= y <= PLAZA[3]):
                b.put(x, y, TORCH)
    for x in range(V_X0 + 4, V_X1, 9):
        for y in (ROAD_H[0] - 1, ROAD_H[1] + 1):
            if not b.cells[(x, y)].items:
                b.put(x, y, TORCH)

    # 6b. muros e moitas importados fora do portão sul --------------------
    stamp_building(b, tpls, sid, "green_gate_b", 1023, 1073)
    stamp_building(b, tpls, sid, "green_gate_c", 1034, 1073)
    stamp_building(b, tpls, sid, "big_bush", 1019, 1074)
    stamp_building(b, tpls, sid, "gate_east", 1038, 1074)
    stamp_building(b, tpls, sid, "green_gate_a", 1015, 1078)

    # 7. hub de NPCs na entrada da Floresta da Morte ----------------------
    b.clear_rect(HUB[0] - 1, HUB[1] - 1, HUB[2] + 1, HUB[3] + 1)
    b.fill(HUB[0], HUB[1], HUB[2], HUB[3], STONE_FLOOR)
    b.put(HUB[0], HUB[1], TORCH)
    b.put(HUB[2], HUB[3], TORCH)
    b.put(HUB[0] + 1, HUB[1] + 1, SIGN,
          text="Floresta da Morte - viajante, volte enquanto pode")
    b.put(HUB[0] + 2, HUB[3] - 1, CAMPFIRE)
    stamp_building(b, tpls, sid, "shop_east", 1132, 1062, ground=STONE_FLOOR)
    npcs.append(("Velha Sumi", (HUB[0] + 2, HUB[1] + 2)))
    npcs.append(("Rastreador Goro", (HUB[0] + 4, HUB[1] + 3)))

    # 8. torre de pedra do Sapo Ancião ------------------------------------
    b.building(TOWER[0], TOWER[1], TOWER[2], TOWER[3], STONE_FLOOR,
               wood=False, doors=[TOWER_DOOR])
    # esplanada de acesso à porta (oeste), sem árvores mortas no caminho
    for yy in range(TOWER[1] - 1, TOWER[3] + 2):
        for xx in (TOWER[0] - 3, TOWER[0] - 2, TOWER[0] - 1):
            b.clear_items(xx, yy)
            b.ground(xx, yy, MUD)
    b.put(TOWER[0] - 1, TOWER[1] - 1, TORCH)
    b.put(TOWER[2] + 1, TOWER[3] + 1, TORCH)
    b.put(TOWER[0] - 2, TOWER[1] - 1, SIGN, text="Torre do Sapo Anciao")

    # 9. acampamento dos bandidos -----------------------------------------
    ccx, ccy = CAMP_CENTER
    for y in range(ccy - 7, ccy + 8):
        for x in range(ccx - 7, ccx + 8):
            if (x - ccx) ** 2 + (y - ccy) ** 2 <= 49:
                b.ground(x, y, DIRT)
                b.clear_items(x, y)
    b.put(ccx, ccy - 2, CAMPFIRE)
    for (tx, ty) in [(ccx - 4, ccy - 3), (ccx + 4, ccy - 3),
                     (ccx - 4, ccy + 3), (ccx + 4, ccy + 3)]:
        b.put(tx, ty, TENT)
    for (fx, fy) in [(ccx - 6, ccy), (ccx + 6, ccy)]:
        b.put(fx, fy, TORCH)
    b.put(ccx - 1, ccy + 5, SIGN, text="Acampamento dos Bandidos")
    # cerca parcial de troncos ao redor
    for x in range(ccx - 6, ccx + 7, 2):
        if x != ccx:
            b.put(x, ccy - 7, FENCE_H)

    return b, npcs


# --------------------------------------------------------------- clareiras

CLEARINGS = [
    # (nome, x, y, raio_clareira)
    ("Trilha dos Lobos", 1012, 1012, 5),
    ("Bosque Norte", 1050, 1010, 5),
    ("Clareira do Riacho", 1085, 1015, 5),
    ("Campina Oeste", 1006, 1050, 4),
    ("Clareira Central", 1070, 1040, 5),
    ("Bosque Leste", 1105, 1045, 5),
    ("Trilha Sul", 1015, 1090, 5),
    ("Clareira dos Bandidos", 1060, 1105, 5),
    ("Bosque Sudeste", 1112, 1075, 5),
    ("Mata Norte", 1005, 1005, 4),
]

DEATH_CLEARINGS = [
    ("Charco Norte", 1140, 1015, 5),
    ("Charco das Sanguessugas", 1170, 1020, 5),
    ("Lamaçal Central", 1145, 1040, 5),
    ("Charco Leste", 1185, 1050, 5),
    ("Lamaçal Sul", 1145, 1090, 5),
    ("Charco Profundo", 1180, 1095, 5),
    ("Ninho da Serpente", 1190, 1015, 5),
]


def carve_clearings(b):
    for (_, cx, cy, r) in CLEARINGS + DEATH_CLEARINGS:
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 > r * r:
                    continue
                if (x, y) not in b.cells or b.is_protected(x, y):
                    continue
                b.clear_items(x, y)
                if x >= DEATH_X0:
                    b.ground(x, y, MUD)
                else:
                    b.ground(x, y, GRASS)


def connect_clearings(b):
    """Liga cada clareira à trilha principal com um caminho em L."""
    for (_, cx, cy, _) in CLEARINGS:
        # liga verticalmente ao anel (y=1025 ao norte, y=1075 ao sul) …
        ring_y = 1025 if cy < 1050 else 1075
        b.path(cx, cy, cx, ring_y, DIRT, width=1)
        # … e horizontalmente até o eixo do anel mais próximo
        ring_x = 1005 if cx < 1030 else 1055
        b.path(cx, ring_y, ring_x, ring_y, DIRT, width=1)
    for (_, cx, cy, _) in DEATH_CLEARINGS:
        # desvia da torre: usa y=1050 ao norte dela e y=1070 ao sul
        lane = 1050 if cy <= 1060 else 1070
        b.path(cx, cy, cx, lane, MUD, width=1)
        b.path(cx, lane, HUB[2] + 2, lane, MUD, width=1)
        b.path(HUB[2] + 2, lane, HUB[2] + 2, 1060, MUD, width=1)


# ------------------------------------------------------------------ spawns

FOREST_SETS = [
    ("Lobo", 3, 60), ("Lobo", 4, 60), ("Cobra da Floresta", 3, 70),
    ("Bandido", 3, 80), ("Bandido Arqueiro", 2, 90), ("Lobo", 3, 60),
    ("Bandido", 4, 80), ("Cobra da Floresta", 4, 70),
    ("Bandido Arqueiro", 3, 90), ("Lobo", 2, 60),
]

DEATH_SETS = [
    ("Sanguessuga Gigante", 4, 70), ("Sanguessuga Gigante", 3, 70),
    ("Sapo Gigante", 3, 90), ("Ninja Renegado", 2, 120),
    ("Sapo Gigante", 4, 90), ("Ninja Renegado", 3, 120),
    ("Serpente Branca", 1, 3600),
]

OFFSETS = [(0, 0), (2, -1), (-2, 1), (1, 2), (-1, -2), (3, 0), (0, 3), (-3, -1)]


def build_spawns(b, npcs):
    sf = SpawnFile("GERADO por tools/map/build_valley.py. NAO EDITE A MAO.")
    extras = []

    for (name, cx, cy, _), (mon, count, stime) in zip(CLEARINGS, FOREST_SETS):
        g = sf.group(cx, cy, FLOOR, radius=4)
        for i in range(count):
            dx, dy = OFFSETS[i % len(OFFSETS)]
            g.add_monster(mon, dx, dy, spawntime=stime)
        extras.append((name, g))

    for (name, cx, cy, _), (mon, count, stime) in zip(DEATH_CLEARINGS, DEATH_SETS):
        g = sf.group(cx, cy, FLOOR, radius=4)
        for i in range(count):
            dx, dy = OFFSETS[i % len(OFFSETS)]
            g.add_monster(mon, dx, dy, spawntime=stime)
        extras.append((name, g))

    # boss dos bandidos no acampamento, cercado de bandidos
    ccx, ccy = CAMP_CENTER
    gb = sf.group(ccx, ccy, FLOOR, radius=3)
    gb.add_monster("Chefe dos Bandidos", 0, 0, spawntime=3600)
    sf.group(ccx - 3, ccy + 3, FLOOR, radius=3) \
        .add_monster("Bandido", 0, 0, spawntime=90) \
        .add_monster("Bandido", 2, 0, spawntime=90) \
        .add_monster("Bandido Arqueiro", 0, 2, spawntime=110)
    sf.group(ccx + 3, ccy + 3, FLOOR, radius=3) \
        .add_monster("Bandido", 0, 0, spawntime=90) \
        .add_monster("Bandido Arqueiro", 1, 1, spawntime=110)

    # boss da torre
    sf.group(TOWER_CENTER[0], TOWER_CENTER[1], FLOOR, radius=1) \
        .add_monster("Sapo Ancião", 0, 0, spawntime=3600)

    # NPCs
    for (name, (nx, ny)) in npcs:
        sf.group(nx, ny, FLOOR, radius=1).add_npc(name, 0, 0, spawntime=60)

    return sf


# ------------------------------------------------------- validação e saída

def walkable_map(b, types):
    """Conjunto de posições caminháveis (chão não-bloqueante, sem item sólido)."""
    walk = set()
    for (x, y), c in b.cells.items():
        if c.ground is None:
            continue
        gt = types.get(c.ground)
        if gt is None or not gt.is_ground or gt.blocking:
            continue
        blocked = False
        for it in c.items:
            if it.id in DOOR_IDS:
                continue
            t = types.get(it.id)
            if t is None or t.blocking:
                blocked = True
                break
        if not blocked:
            walk.add((x, y))
    return walk


def bfs(walk, start):
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) in walk and (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny))
    return seen


def validate(b, types, sf, npcs):
    problems = []

    # ids existem e chãos são chãos
    used_ground = {}
    used_item = {}
    for (x, y), c in b.cells.items():
        if c.ground is not None:
            used_ground[c.ground] = used_ground.get(c.ground, 0) + 1
        for it in c.items:
            used_item[it.id] = used_item.get(it.id, 0) + 1
    for gid in used_ground:
        t = types.get(gid)
        if t is None:
            problems.append("chão %d nao existe no items.otb" % gid)
        elif not t.is_ground:
            problems.append("item %d usado como chão mas nao e do grupo ground" % gid)
    for iid in used_item:
        if iid not in types:
            problems.append("item %d nao existe no items.otb" % iid)

    walk = walkable_map(b, types)
    start = (TEMPLE_POS[0], TEMPLE_POS[1])
    if start not in walk:
        problems.append("templo %r nao e caminhavel" % (start,))
        return problems, walk, set()
    reach = bfs(walk, start)

    for g in sf.groups:
        if (g.x, g.y) not in reach:
            problems.append("centro de spawn (%d,%d) inalcancavel" % (g.x, g.y))
        for (px, py, _) in g.positions:
            if (px, py) not in reach:
                problems.append("criatura em (%d,%d) inalcancavel" % (px, py))
    for (name, (nx, ny)) in npcs:
        if (nx, ny) not in reach:
            problems.append("NPC %s em (%d,%d) inalcancavel" % (name, nx, ny))
    return problems, walk, reach


def to_otbm(b):
    m = OtbmMap(width=MAP_W, height=MAP_H, version=2, major_items=3, minor_items=57)
    m.descriptions = [
        "Vale da Folha - Shinobi Legends",
        "GERADO por tools/map/build_valley.py. Nao edite a mao.",
    ]
    m.spawnfile = "valley-spawn.xml"
    m.housefile = "valley-house.xml"

    for (x, y), c in b.cells.items():
        if c.ground is None:
            continue
        t = m.tile(x, y, FLOOR)
        t.set_ground(c.ground)
        t.flags = c.flags
        for it in c.items:
            t.items.append(it)

    m.add_town(1, "Vila da Folha", *TEMPLE_POS)
    m.add_waypoint("Templo", *TEMPLE_POS)
    m.add_waypoint("Praca", 1029, 1050, FLOOR)
    m.add_waypoint("Portao Sul", 1029, GATE_Y, FLOOR)
    m.add_waypoint("Ponte", RIVER_X0 + 2, BRIDGE_Y0 + 1, FLOOR)
    m.add_waypoint("Torre", TOWER_CENTER[0], TOWER_CENTER[1], FLOOR)
    m.add_waypoint("Acampamento", CAMP_CENTER[0], CAMP_CENTER[1], FLOOR)
    m.add_waypoint("Hub Pantano", HUB[0] + 2, HUB[1] + 2, FLOOR)
    return m


def main():
    types = load_items_otb(ITEMS_OTB)
    tpls, sid, novos = load_imported()

    # RELAXAMENTO EXPLÍCITO: os tiles importados só entram no items.otb quando
    # `tools/spr/build_assets.py` roda. Até lá, aceitamos os ids >= 30000 que
    # estejam em allocations.json, usando as flags declaradas em tiles.json.
    ausentes = sorted(k for k in novos if k not in types)
    if ausentes:
        print("AVISO: %d server ids de tiles novos ainda NAO existem no items.otb"
              % len(ausentes))
        print("       faixa %d..%d — validando com as flags de tiles.json."
              % (ausentes[0], ausentes[-1]))
        print("       RODE `.venv/bin/python tools/spr/build_assets.py` ANTES de")
        print("       instalar este mapa, senao o TFS recusa os itens.")
        for k in ausentes:
            types[k] = novos[k]

    b, npcs = build(tpls, sid)
    carve_clearings(b)
    connect_clearings(b)
    sf = build_spawns(b, npcs)

    problems, walk, reach = validate(b, types, sf, npcs)
    if problems:
        print("BUILD FALHOU:")
        for p in problems[:40]:
            print("  -", p)
        print("  (%d problemas)" % len(problems))
        return 1

    m = to_otbm(b)
    os.makedirs(OUT_DIR, exist_ok=True)
    otbm_path = os.path.join(OUT_DIR, "valley.otbm")
    m.write(otbm_path)
    sf.write(os.path.join(OUT_DIR, "valley-spawn.xml"))
    write_empty_house_file(
        os.path.join(OUT_DIR, "valley-house.xml"),
        "GERADO por tools/map/build_valley.py. O Vale da Folha nao tem casas.")

    items_total = sum(len(c.items) for c in b.cells.values())
    print("Vale da Folha gerado em", OUT_DIR)
    print("  tiles ............ %d (andar %d)" % (len(m.tiles), FLOOR))
    print("  itens (sem chao) . %d" % items_total)
    print("  itens totais ..... %d" % sum(m.item_count_by_id().values()))
    print("  caminhaveis ...... %d  alcancaveis do templo: %d (%.1f%%)"
          % (len(walk), len(reach), 100.0 * len(reach) / len(walk)))
    print("  grupos de spawn .. %d" % len(sf.groups))
    print("  monstros ......... %d" % sf.monster_count())
    print("  NPCs ............. %d" % sf.npc_count())
    print("  towns/waypoints .. %d / %d" % (len(m.towns), len(m.waypoints)))
    print("  templo ........... %r" % (TEMPLE_POS,))
    for n in b.notes:
        print("  nota:", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
