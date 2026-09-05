#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.1: preenchimento da Vila da Folha (ressalvas do orquestrador) + regioes
novas do mundo (Costa das Mares, Ruinas do Cla Marionetista compacta,
Montanha do Trovao compacta, Covil da Nuvem Vermelha).

Modulo PURO no mesmo estilo de `tools/map/decor.py`: so IMPORTA
`build_valley`, nunca o edita (build_valley.py so ganhou 2 hooks minimos:
capturar as portas dos predios em `b.v21` e chamar `build_all()` do main()).

    build_all(b, sid, tpls) -> (npcs, add_spawns_fn, notes)

``npcs``          lista [(nome, (x,y))] para anexar aos NPCs de build_valley.
``add_spawns_fn`` callable(sf) que registra os grupos de spawn das regioes
                   novas (chamado DEPOIS de build_valley.build_spawns(), pois
                   e' quem cria o SpawnFile).
``notes``          strings para o relatorio do build (b.notes).

Coordenadas de todas as regioes novas ficam em x>=1200 ou y>=1120 (fora do
retangulo do mundo aberto atual, x1000-1199/y1000-1119), respeitando o pedido
da missao. O Covil da Nuvem Vermelha fica ISOLADO (sem trilha a pe'), so'
alcancavel pelo teleporte gated no topo da Montanha (actionid 45004).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_valley as BV

FLOOR = BV.FLOOR


# ============================================================ helpers gerais

def door_rect(tpls, key, x, y):
    """(x0,y0,x1,y1) absoluto do template ``key`` ancorado em (x,y) — mesma
    convencao de build_valley.stamp_building (canto inferior esquerdo)."""
    tpl = tpls[key]
    h, w = tpl["height"], tpl["width"]
    return (x, y - (h - 1), x + w - 1, y)


def sign(b, x, y, text):
    c = b.cells.get((x, y))
    if c is not None and not c.items:
        b.put(x, y, BV.SIGN, text=text)
        return True
    return False


def cobble_row(b, y, x0, x1, skip=()):
    """Pinta uma faixa leste-oeste de cobblestone em ``y``, pulando os
    intervalos ``skip`` (ja pavimentados por outra coisa, ex.: a praca)."""
    n = 0
    for x in range(x0, x1 + 1):
        if any(a <= x <= bb for (a, bb) in skip):
            continue
        b.ground(x, y, BV.COBBLE)
        n += 1
    return n


def rect_overlaps(r1, r2):
    x0, y0, x1, y1 = r1
    a0, b0, a1, b1 = r2
    return not (x1 < a0 or a1 < x0 or y1 < b0 or b1 < y0)


def in_rect(x, y, r):
    x0, y0, x1, y1 = r
    return x0 <= x <= x1 and y0 <= y <= y1


class SpawnSpec:
    """Um grupo de spawn adiado — vira ``sf.group(...)`` quando
    ``add_spawns_fn(sf)`` roda (o SpawnFile so existe depois de
    build_valley.build_spawns())."""

    def __init__(self):
        self.groups = []

    def group(self, x, y, radius=3):
        g = {"x": x, "y": y, "radius": radius, "creatures": []}
        self.groups.append(g)
        return _SpecGroup(g)

    def apply(self, sf):
        n_m = n_n = 0
        for g in self.groups:
            sg = sf.group(g["x"], g["y"], FLOOR, radius=g["radius"])
            for (kind, name, dx, dy, stime) in g["creatures"]:
                if kind == "monster":
                    sg.add_monster(name, dx, dy, spawntime=stime)
                    n_m += 1
                else:
                    sg.add_npc(name, dx, dy, spawntime=stime)
                    n_n += 1
        return n_m, n_n


class _SpecGroup:
    def __init__(self, g):
        self.g = g

    def add_monster(self, name, dx=0, dy=0, spawntime=60):
        self.g["creatures"].append(("monster", name, dx, dy, spawntime))
        return self

    def add_npc(self, name, dx=0, dy=0, spawntime=60):
        self.g["creatures"].append(("npc", name, dx, dy, spawntime))
        return self


# =================================================================
# PARTE 1 — Vila da Folha v2.1 (ressalvas do orquestrador)
# =================================================================

# Predios ja estampados por build_valley.build() (mesmos anchors) — usados so
# para computar retangulos de exclusao do preenchimento de quintal.
EXISTING_STAMPS = [
    ("tower", 1027, 1036), ("big_house", 1013, 1036), ("house_green", 1040, 1036),
    ("newbie_shop", 1037, 1053), ("ramen_shop", 1042, 1053), ("blue_shop", 1046, 1053),
    ("prison", 1013, 1063), ("tavern", 1032, 1063), ("roof_orange", 1037, 1063),
    ("blue_house", 1021, 1063), ("blue_house", 1041, 1063),
]

# Casas NOVAS da v2.1 — preenchem os 2 maiores vazios de terra batida dentro
# da muralha (norte, entre big_house/torre/house_green; sul, entre
# prisao/tavern e a muralha leste). Ancoradas na MESMA linha de porta (sul)
# dos predios vizinhos, para a nova rua de fundo (ver `_lanes`) tocar todas.
NEW_HOUSES = [
    ("house_green", 1021, 1036),   # vazio norte-oeste (entre big_house e a torre)
    ("blue_house", 1045, 1036),    # vazio norte-leste (entre house_green e a muralha)
    ("blue_house", 1017, 1063),    # vazio sul-oeste (entre a prisao e a blue_house existente)
    ("house_green", 1045, 1063),   # vazio sul-leste (entre a blue_house leste e a muralha)
]

NORTH_LANE_Y = BV.RESIDENTIAL_NORTH[0][1] + 1     # 1037 — uma linha ao sul das portas norte
SOUTH_LANE_Y = BV.PRISON_XY[1] + 1                # 1064 — uma linha ao sul das portas sul

TAVERN_INT = (1300, 1008, 1306, 1013)
PRISON_INT = (1310, 1008, 1315, 1013)

_YARD_POOL_FLOWER = ("wildflower_yellow", "wildflower_pink", "wildflower_white")
_YARD_POOL_GRASS = ("tall_grass_0", "tall_grass_1", "tall_grass_2")
_YARD_POOL_MISC = ("mushroom_brown", "tree_stump_0", "wood_barrel", "wood_crate")


def upgrade_village(b, sid, tpls, rng):
    """Aplica as 5 ressalvas do orquestrador na Vila da Folha v2."""
    notes = []
    v21 = getattr(b, "v21", {})

    # -- (1)/(2) casas novas + ruas de fundo ligando toda porta a uma rua ---
    new_doors = []
    for (key, x, y) in NEW_HOUSES:
        d = BV.stamp_building(b, tpls, sid, key, x, y, ground=BV.DIRT)
        new_doors.append(d)

    skip_plaza = [(BV.PLAZA[0], BV.PLAZA[2])]
    n_lane = 0
    n_lane += cobble_row(b, NORTH_LANE_Y, BV.V_X0 + 1, BV.V_X1 - 1, skip=skip_plaza)
    n_lane += cobble_row(b, SOUTH_LANE_Y, BV.V_X0 + 1, BV.V_X1 - 1)
    notes.append("vila v2.1: 2 ruas de fundo novas (norte y=%d, sul y=%d), %d tiles — "
                 "toda porta de casa/taverna/prisao agora toca cobblestone"
                 % (NORTH_LANE_Y, SOUTH_LANE_Y, n_lane))

    # -- (5) placa individual em cada loja (alem da placa geral da rua) -----
    n_signs = 0
    for (name, _npc_id, _tpl, sx) in BV.SHOPS:
        door = v21.get("shop_doors", {}).get(name)
        if door is None:
            continue
        if sign(b, door[0] + 1, BV.ROAD_H[0], "Loja - %s" % name):
            n_signs += 1
    if sign(b, BV.TEMPLE_DOOR[0], BV.TEMPLE_DOOR[1] + 1, "Templo"):
        n_signs += 1
    notes.append("vila v2.1: %d placas novas com texto (lojas + templo)" % n_signs)

    # -- (4) templo: altar + estatua + lanternas, sem tampar a posicao da
    # town ----------------------------------------------------------------
    # NOTA (historico): a 1a tentativa usou BV.STATUE (1442, "statue"
    # vanilla) — o tour in-game (screenshots/mapa_v21_03_templo_altar.png)
    # mostrou que esse item NAO renderiza neste build do Tibia.dat/.spr do
    # projeto. Causa raiz encontrada (nao so' suspeita): o thing do 1442
    # existe no .dat, mas o SPRITE que ele referencia e' um placeholder
    # quase vazio (so' 25 de 1024px opacos, um pontinho de 2px — visto
    # exportando com sprformat.py/dump_dat.py), nao um buraco de cobertura.
    # A cadeira vanilla 1650 tinha o MESMO sprite quase-vazio. Corrigido de
    # vez com itens NOVOS (tools/spr/gen_decor.py): shrine_statue (estatua de
    # guardiao de pedra) no lugar do 1442, + 2 stone_lantern (toro aceso)
    # flanqueando. A CAMPFIRE (1428) que substituiu o 1442 v2.1 continua —
    # ja' confirmada renderizando e "chama eterna diante do guardiao" encaixa
    # bem no nome do templo ("Templo da Chama").
    altar = (BV.TEMPLE_POS[0], BV.TEMPLE_POS[1] - 1)
    if altar != (BV.TEMPLE_POS[0], BV.TEMPLE_POS[1]):
        statue_pos = (altar[0], altar[1] - 1)
        c = b.cells.get(statue_pos)
        if c is not None and not c.items:
            b.put(statue_pos[0], statue_pos[1], sid["shrine_statue_gray"])
        b.clear_items(*altar)
        b.put(altar[0], altar[1], BV.CAMPFIRE)
        for lx in (altar[0] - 2, altar[0] + 2):
            c = b.cells.get((lx, altar[1]))
            if c is not None:
                b.clear_items(lx, altar[1])
                b.put(lx, altar[1], sid["stone_lantern"])
    notes.append("vila v2.1: altar (estatua de guardiao + chama eterna + 2 lanternas de "
                 "pedra) dentro do templo em %r" % (altar,))

    # -- (3) interior da Taverna (mesas, cadeiras, balcao, barris) ----------
    tavern_door = v21.get("tavern_door")
    if tavern_door:
        build_tavern_interior(b, sid, TAVERN_INT, tavern_door)
        notes.append("vila v2.1: interior da Taverna em %r, teleporte na porta %r"
                     % (TAVERN_INT, tavern_door))

    # -- (3) interior da Prisao (celas com grades + cama) -------------------
    prison_door = v21.get("prison_door")
    if prison_door:
        build_prison_interior(b, sid, PRISON_INT, prison_door)
        notes.append("vila v2.1: interior da Prisao em %r, teleporte na porta %r"
                     % (PRISON_INT, prison_door))

    # -- (1) quintais + becos: preenche o "descampado" de terra batida ------
    exclude = []
    for (key, x, y) in EXISTING_STAMPS + NEW_HOUSES:
        exclude.append(door_rect(tpls, key, x, y))
    exclude.append(BV.ACADEMY)
    exclude.append(BV.PLAZA)
    exclude.append(BV.TEMPLE)

    def excluded(x, y):
        return any(in_rect(x, y, r) for r in exclude)

    def near_building(x, y, radius=2):
        for r in exclude[:len(EXISTING_STAMPS) + len(NEW_HOUSES)]:
            x0, y0, x1, y1 = r
            if x0 - radius <= x <= x1 + radius and y0 - radius <= y <= y1 + radius:
                return True
        return False

    flower_pool = [sid[k] for k in _YARD_POOL_FLOWER if k in sid]
    grass_pool = [sid[k] for k in _YARD_POOL_GRASS if k in sid]
    misc_pool = [sid[k] for k in _YARD_POOL_MISC if k in sid]

    n_yard = n_alley = 0
    for y in range(BV.V_Y0 + 1, BV.V_Y1):
        for x in range(BV.V_X0 + 1, BV.V_X1):
            c = b.cells.get((x, y))
            if c is None or c.ground not in BV._DIRT_SET or c.items:
                continue
            if excluded(x, y):
                continue
            r = rng.random()
            if near_building(x, y):
                # quintal: grama + canteiro/arbusto/cerca/barril
                if r < 0.55:
                    b.ground(x, y, BV.GRASS)
                    r2 = rng.random()
                    if r2 < 0.35 and flower_pool:
                        b.put(x, y, rng.choice(flower_pool))
                    elif r2 < 0.55 and grass_pool:
                        b.put(x, y, rng.choice(grass_pool))
                    elif r2 < 0.68:
                        b.put(x, y, rng.choice(BV.BUSHES))
                    elif r2 < 0.74:
                        b.put(x, y, sid["wood_fence_h"] if rng.random() < 0.5 else sid["wood_fence_v"])
                    elif r2 < 0.80 and misc_pool:
                        b.put(x, y, rng.choice(misc_pool))
                    n_yard += 1
            else:
                # beco de terra estreito: quase vazio, so' uma pontinha de uso
                if r < 0.08:
                    b.put(x, y, sid[rng.choice(["wood_barrel", "wood_crate"])])
                    n_alley += 1
    notes.append("vila v2.1: quintais preenchidos (%d tiles grama+canteiro/cerca/barril), "
                 "%d itens esparsos nos becos de terra" % (n_yard, n_alley))

    return notes


def build_tavern_interior(b, sid, rect, door):
    """Sala fechada com mesas, cadeiras, balcao e barris — mesmo padrao de
    build_valley.build_shop_interior, mas sem NPC (nao existe taverneiro em
    data/npcs ainda; so' mobilia)."""
    x0, y0, x1, y1 = rect
    b.clear_rect(x0, y0, x1, y1)
    b.fill(x0, y0, x1, y1, sid["tatami_floor"])
    for x in range(x0, x1 + 1):
        for y in (y0, y1):
            b.clear_items(x, y)
            b.put(x, y, sid["wood_wall_h"])
    for y in range(y0 + 1, y1):
        for x in (x0, x1):
            b.clear_items(x, y)
            b.put(x, y, sid["wood_wall_v"])

    counter_y = y0 + 1
    for x in range(x0 + 1, x1):
        b.clear_items(x, counter_y)
        b.put(x, counter_y, BV.COUNTER)
    # 2 mesas com cadeiras + barris de decoracao
    for (tx, ty) in ((x0 + 2, y1 - 2), (x1 - 2, y1 - 2)):
        b.clear_items(tx, ty)
        b.put(tx, ty, BV.SHOP_TABLE)
        # cadeira NOVA (tools/spr/gen_decor.py chair) virada para a mesa: a
        # vanilla 1650 "wooden chair" tem thing no Tibia.dat mas o sprite e'
        # um placeholder quase vazio (25 de 1024px opacos — visto exportando
        # com sprformat.py) e ficava invisivel no cliente, ver docs/sistemas/
        # mapas.md#pendências-da-v21.
        for (cx, cy, key) in ((tx - 1, ty, "wood_chair_east"), (tx + 1, ty, "wood_chair_west")):
            c = b.cells.get((cx, cy))
            if c is not None and not c.items:
                b.put(cx, cy, sid[key])
    for (bx, by) in ((x0 + 1, y1 - 1), (x1 - 1, y1 - 1)):
        c = b.cells.get((bx, by))
        if c is not None and not c.items:
            b.put(bx, by, sid["wood_barrel"])

    # linha livre entre o balcao (y0+1) e as mesas (y1-2)
    free_y = y0 + 2
    for (fx, txt) in ((x0 + 1, None), (x1 - 1, None)):
        c = b.cells.get((fx, free_y))
        if c is not None and not c.items:
            b.put(fx, free_y, sid["paper_lantern"])
    c = b.cells.get((x0 + 2, free_y))
    if c is not None and not c.items:
        b.put(x0 + 2, free_y, BV.SIGN, text="Taverna do Vale - entre e sente")

    outside_front = (door[0], door[1] + 1)
    landing = ((x0 + x1) // 2, y1 - 1)
    exitpad = (landing[0] - 1, landing[1])
    b.clear_items(*exitpad)
    b.put(exitpad[0], exitpad[1], BV.TELEPORT_ITEM,
          tele_dest=(outside_front[0], outside_front[1], FLOOR))
    b.clear_items(*landing)
    b.put(door[0], door[1], BV.TELEPORT_ITEM, tele_dest=(landing[0], landing[1], FLOOR))


def build_prison_interior(b, sid, rect, door):
    """2 celas (grades = wooden bars) com cama cada, separadas por um
    corredor central."""
    x0, y0, x1, y1 = rect
    b.clear_rect(x0, y0, x1, y1)
    b.fill(x0, y0, x1, y1, BV.STONE_FLOOR)
    for x in range(x0, x1 + 1):
        for y in (y0, y1):
            b.clear_items(x, y)
            b.put(x, y, BV.STONE_WALL_H)
    for y in range(y0 + 1, y1):
        for x in (x0, x1):
            b.clear_items(x, y)
            b.put(x, y, BV.STONE_WALL_V)

    # grade (wooden bars) separando 1 coluna leste como cela isolada; o
    # resto da sala (oeste) e' onde o jogador chega/sai.
    bars_x = x1 - 2
    for y in range(y0 + 2, y1 - 1):
        c = b.cells.get((bars_x, y))
        if c is not None and not c.items:
            b.put(bars_x, y, 3798)   # wooden bars — grade da cela
    b.clear_items(bars_x + 1, y1 - 2)
    b.put(bars_x + 1, y1 - 2, 1754)          # cama na cela (leste, atras da grade)
    b.clear_items(x0 + 1, y1 - 2)
    b.put(x0 + 1, y1 - 2, 1754)              # 2a cama, corredor oeste

    outside_front = (door[0], door[1] + 1)
    landing = (bars_x - 1, y0 + 2)
    exitpad = (bars_x - 1, y0 + 3)
    b.clear_items(*exitpad)
    b.put(exitpad[0], exitpad[1], BV.TELEPORT_ITEM,
          tele_dest=(outside_front[0], outside_front[1], FLOOR))
    b.clear_items(*landing)
    b.put(door[0], door[1], BV.TELEPORT_ITEM, tele_dest=(landing[0], landing[1], FLOOR))
    c = b.cells.get((x0 + 1, y0 + 1))
    if c is not None and not c.items:
        b.put(x0 + 1, y0 + 1, BV.SIGN, text="Prisao da Vila - celas")


# =================================================================
# PARTE 2 — regioes novas do mundo
# =================================================================

# ---------------------------------------------------------- Costa das Mares
COAST_X0, COAST_Y0, COAST_X1, COAST_Y1 = 1000, 1120, 1049, 1169
COAST_PATH_X = 1029


def build_coastal_tides(b, sid, tpls, rng):
    notes = []
    x0, y0, x1, y1 = COAST_X0, COAST_Y0, COAST_X1, COAST_Y1

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if y >= 1155:
                b.ground(x, y, BV.WATER)
            elif y >= 1140:
                b.ground(x, y, BV.SAND)                # areia (vanilla)
            else:
                b.ground(x, y, BV.GRASS)

    # liga a trilha sul da vila (que hoje vira pro acampamento em y=1090) ate
    # a Costa: continua reto pro sul em x=1029.
    b.path(COAST_PATH_X, 1090, COAST_PATH_X, 1142, BV.DIRT, width=3)
    sign(b, COAST_PATH_X - 4, 1091,
         "<- Vila da Folha  |  Costa das Mares ->")

    # vila de pescadores: 4 cabanas (blue_house) em volta de um patio de areia
    cabins = [
        ("blue_house", COAST_PATH_X - 8, 1143),
        ("blue_house", COAST_PATH_X - 8, 1150),
        ("blue_house", COAST_PATH_X + 6, 1143),
        ("blue_house", COAST_PATH_X + 6, 1150),
    ]
    for (key, cx, cy) in cabins:
        BV.stamp_building(b, tpls, sid, key, cx, cy, ground=BV.SAND[:2])
        # redes/caixotes de pesca encostados em cada cabana (nao ha item
        # "rede de pesca" vanilla catalogado; caixote/barril fazem o papel
        # de equipamento de pesca guardado, como pedido na missao)
        for (rx, ry) in ((cx - 1, cy), (cx + 3, cy)):
            c = b.cells.get((rx, ry))
            if c is not None and not c.items:
                b.put(rx, ry, sid[rng.choice(["wood_barrel", "wood_crate"])])
    sign(b, COAST_PATH_X - 2, 1136, "Costa das Mares - vila de pescadores (nivel 12-19)")

    # barcos pequenos (item vanilla 3587, "small boat", nao bloqueia) puxados
    # na areia perto da agua — decoracao pedida na missao.
    for (bx, by) in ((COAST_PATH_X - 12, 1157), (COAST_PATH_X + 10, 1156)):
        c = b.cells.get((bx, by))
        if c is not None and not c.items:
            b.put(bx, by, 3587)

    # decor de praia (conchas/pedra molhada/madeira encalhada) espalhados pela
    # areia — mesmo padrao de densidade esparsa de tools/map/decor.py
    # place_forest_decor (rng.random() < densidade, por tile elegivel, evita
    # tile com item). A praia estava "lisa" (so' areia + 2 cabanas) segundo o
    # tour in-game; aqui NAO mexe em layout/spawn/NPC, so' decoracao solta.
    _BEACH_POOL = [sid[k] for k in ("seashell_spiral", "seashell_fan", "wet_rock", "driftwood")]
    _BEACH_DENSITY = 0.05
    n_beach = 0
    for y in range(1140, 1155):
        for x in range(x0, x1 + 1):
            c = b.cells.get((x, y))
            if c is None or c.ground not in BV._SAND_SET or c.items:
                continue
            if rng.random() < _BEACH_DENSITY:
                b.put(x, y, rng.choice(_BEACH_POOL))
                n_beach += 1
    # postes de amarracao (bloqueiam 1 tile) junto ao cais, sem tampar a
    # faixa central por onde se anda (COAST_PATH_X, que vira o cais, fica
    # livre — o pier propriamente dito e' construido mais abaixo nesta
    # funcao, mas usa a MESMA coordenada COAST_PATH_X).
    for (px, py) in ((COAST_PATH_X - 2, 1149), (COAST_PATH_X + 2, 1149),
                     (COAST_PATH_X - 2, 1160), (COAST_PATH_X + 2, 1160)):
        c = b.cells.get((px, py))
        if c is not None and not c.items and c.ground in BV._SAND_SET:
            b.put(px, py, sid["mooring_post"])
            n_beach += 1
    notes.append("costa das mares: %d itens de decor de praia (conchas/pedra molhada/"
                 "madeira encalhada/postes de amarracao)" % n_beach)

    npcs = [
        ("Mercador Itsuki", (COAST_PATH_X - 3, 1145)),
        ("Ancião Tazu", (COAST_PATH_X + 3, 1145)),
    ]
    for (_, (nx, ny)) in npcs:
        b.clear_items(nx, ny)

    # cais/pier de madeira (reaproveita a ponte de madeira) ate a arena do
    # boss, numa plataforma de pedra sobre a agua.
    pier_x = COAST_PATH_X
    for y in range(1148, 1163):
        c = b.cells.get((pier_x, y))
        if c is not None:
            b.clear_items(pier_x, y)
            b.ground(pier_x, y, sid["bridge_wood_center"])
    ax0, ay0, ax1, ay1 = pier_x - 4, 1163, pier_x + 4, 1168
    b.fill(ax0, ay0, ax1, ay1, BV.STONE_FLOOR)
    for x in range(ax0, ax1 + 1):
        for y in (ay0, ay1):
            b.clear_items(x, y)
    for y in range(ay0, ay1 + 1):
        for x in (ax0, ax1):
            b.clear_items(x, y)
    b.put(ax0 + 1, ay0 + 1, BV.TORCH)
    b.put(ax1 - 1, ay0 + 1, BV.TORCH)
    b.put(pier_x, (ay0 + ay1) // 2, BV.SIGN,
          text="Arena do Espadachim da Nevoa - ponte inacabada")
    boss_pos = (pier_x, (ay0 + ay1) // 2 + 1)
    notes.append("costa das mares: cais + plataforma do boss em (%d,%d)-(%d,%d)"
                 % (ax0, ay0, ax1, ay1))

    # ponte inacabada (obra sabotada): outro trecho que so termina no meio da
    # agua, sem destino nenhum — pura cenografia/lore.
    unfin_x = x0 + 8
    for y in range(1148, 1158):
        c = b.cells.get((unfin_x, y))
        if c is not None:
            b.clear_items(unfin_x, y)
            b.ground(unfin_x, y, sid["bridge_wood_center"])
    sign(b, unfin_x + 1, 1150, "Obra da ponte - sabotada pelos mercenarios da guilda rival")

    notes.append("costa das mares: fronteira grama/areia e areia/agua agora tem "
                 "autoborder proprio (border_grass_sand_*/border_sand_water_*, "
                 "tools/spr/gen_borders.py) — aplicado pelo passe apply_borders() "
                 "do build_valley.py, nao aqui")

    # -- spawns ---------------------------------------------------------
    spec = SpawnSpec()
    off = [(0, 0), (2, -1), (-2, 1), (1, 2), (-1, -2), (3, 0)]
    g = spec.group(x0 + 10, 1150, radius=6)
    for i in range(6):
        dx, dy = off[i % len(off)]
        g.add_monster("Mercenário da Ponte", dx, dy, spawntime=45)
    g2 = spec.group(COAST_PATH_X - 6, 1130, radius=6)
    for i in range(4):
        dx, dy = off[i % len(off)]
        g2.add_monster("Batedor da Névoa", dx, dy, spawntime=50)
    g3 = spec.group(COAST_PATH_X, 1139, radius=4)
    for i in range(3):
        dx, dy = off[i % len(off)]
        g3.add_monster("Guardião da Neblina", dx, dy, spawntime=60)
    spec.group(*boss_pos, radius=2).add_monster("Espadachim da Névoa", 0, 0, spawntime=7200)

    # NPCs vao SO' na lista `npcs` devolvida (build_valley.build_spawns ja os
    # registra) — nao duplicar aqui, senao cada NPC aparece 2x no spawn.xml.
    return npcs, spec, notes


# ------------------------------------------------ Ruinas do Cla Marionetista
RUINS_X0, RUINS_Y0, RUINS_X1, RUINS_Y1 = 1200, 1000, 1249, 1049
RUINS_GATE_Y = (1020, 1021)


def build_ruins(b, sid, tpls, rng):
    notes = []
    x0, y0, x1, y1 = RUINS_X0, RUINS_Y0, RUINS_X1, RUINS_Y1
    b.fill(x0, y0, x1, y1, BV.DIRT)

    # abre um portao no muro leste da Floresta da Morte, alinhado a esta zona
    for y in RUINS_GATE_Y:
        c = b.cells.get((BV.DEATH_WALL[2], y))
        if c is not None:
            b.clear_items(BV.DEATH_WALL[2], y)
            b.ground(BV.DEATH_WALL[2], y, BV.MUD)
    b.put(BV.DEATH_WALL[2], RUINS_GATE_Y[0] - 1, BV.TORCH)
    b.put(BV.DEATH_WALL[2], RUINS_GATE_Y[1] + 1, BV.TORCH)
    sign(b, BV.DEATH_WALL[2] - 1, RUINS_GATE_Y[0] - 1,
         "<- Floresta da Morte  |  Ruinas do Cla Marionetista ->")
    b.path(BV.DEATH_WALL[2] + 1, RUINS_GATE_Y[0], x0 + 4, RUINS_GATE_Y[0], BV.DIRT, width=2)

    sign(b, x0 + 5, y0 + 2, "Ruinas do Cla Marionetista (nivel 25-50)")

    # muros de pedra QUEBRADOS: retangulos parciais (so' norte+oeste, o
    # "quebrado" e' o proprio buraco onde leste/sul deveriam fechar) + um
    # trecho de parede interna solta (parede sem cantos, tipo cota que
    # desabou) + entulho (pedras/tocos/galhos) espalhado ao redor — pra ler
    # como um patio arruinado de verdade, nao só cantos isolados no vazio.
    broken = [
        (x0 + 4, y0 + 6, x0 + 14, y0 + 16),
        (x0 + 18, y0 + 20, x0 + 30, y0 + 30),
        (x0 + 2, y0 + 30, x0 + 12, y0 + 40),
        (x0 + 20, y0 + 4, x0 + 28, y0 + 12),
        (x0 + 6, y0 + 20, x0 + 14, y0 + 28),
    ]
    loose_walls = [
        (x0 + 30, y0 + 6, x0 + 30, y0 + 14),   # trecho de parede solta (so' 1 lado)
        (x0 + 16, y0 + 32, x0 + 24, y0 + 32),
    ]
    rubble_pool = [sid[k] for k in ("rock_medium", "rock_large", "tree_stump_0",
                                     "tree_stump_1", "fallen_branch")
                   if k in sid]
    for (bx0, by0, bx1, by1) in broken:
        for x in range(bx0, bx1 + 1):
            b.clear_items(x, by0)
            b.put(x, by0, BV.STONE_WALL_H)
        for yy in range(by0, by1 + 1):
            c = b.cells.get((bx0, yy))
            if c is not None:
                b.clear_items(bx0, yy)
                b.put(bx0, yy, BV.STONE_WALL_V)
        # o lado leste e o sul ficam abertos (parede desabada) — nao fecha
        for x in range(bx0 + 3, bx1 - 2):
            b.clear_items(x, by0)   # reabre um trecho da parede norte tb
        # entulho encostado nas paredes (fora do retangulo, no patio aberto)
        if rubble_pool:
            for (rx, ry) in ((bx0 - 1, by0 + 2), (bx1 + 1, by0 + 1),
                              (bx0 + 2, by1 + 1), (bx1 - 1, by1 + 1)):
                c = b.cells.get((rx, ry))
                if c is not None and not c.items and c.ground in BV._DIRT_SET:
                    b.put(rx, ry, rng.choice(rubble_pool))
    for (lx0, ly0, lx1, ly1) in loose_walls:
        if ly0 == ly1:
            for x in range(lx0, lx1 + 1):
                c = b.cells.get((x, ly0))
                if c is not None and not c.items:
                    b.put(x, ly0, BV.STONE_WALL_H)
        else:
            for yy in range(ly0, ly1 + 1):
                c = b.cells.get((lx0, yy))
                if c is not None and not c.items:
                    b.put(lx0, yy, BV.STONE_WALL_V)

    # salao do Marionetista, intacto, no fundo (leste)
    hall = (x1 - 13, y0 + 15, x1 - 1, y0 + 35)
    hx0, hy0, hx1, hy1 = hall
    b.fill(hx0, hy0, hx1, hy1, BV.STONE_FLOOR)
    b.walls(hx0, hy0, hx1, hy1, BV.STONE_WALL_H, BV.STONE_WALL_V, BV.STONE_WALL_C,
            doors=[(hx0, (hy0 + hy1) // 2)])
    b.put(hx0 + 2, hy0 + 2, BV.TORCH)
    b.put(hx1 - 2, hy0 + 2, BV.TORCH)
    hall_door = (hx0, (hy0 + hy1) // 2)
    b.path(hall_door[0] - 6, hall_door[1], hall_door[0] - 1, hall_door[1], BV.DIRT, width=2)
    sign(b, hx0 + 1, hy0 + 1, "Salao do Marionetista")
    boss_pos = ((hx0 + hx1) // 2, (hy0 + hy1) // 2)

    notes.append("ruinas do cla marionetista: complexo compacto x%d-%d,y%d-%d, "
                 "3 paredes quebradas + salao do marionetista em %r"
                 % (x0, x1, y0, y1, hall))

    spec = SpawnSpec()
    off = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1)]
    # centros escolhidos a dedo, bem no MEIO de cada patio (>=5 tiles de
    # qualquer parede quebrada) — evita cair em cima de uma parede/canto.
    monster_centers = [
        ("Marionete de Combate", 6, 70, (1209, 1011)),
        ("Sentinela de Pedra", 4, 90, (1224, 1025)),
        ("Guerreiro Espectral", 3, 100, (1207, 1035)),
        ("Xamã da Maldição", 3, 110, (1240, 1010)),
    ]
    for (mon, count, stime, (cx, cy)) in monster_centers:
        g = spec.group(cx, cy, radius=3)
        for i in range(count):
            dx, dy = off[i % len(off)]
            g.add_monster(mon, dx, dy, spawntime=stime)
    spec.group(hall_door[0] - 4, hall_door[1], radius=2) \
        .add_monster("Desertor de Elite", 0, 0, spawntime=1800)
    spec.group(*boss_pos, radius=3).add_monster("Marionetista das Ruínas", 0, 0, spawntime=7200)

    return [], spec, notes


# --------------------------------------------------------- Montanha do Trovao
MOUNT_X0, MOUNT_Y0, MOUNT_X1, MOUNT_Y1 = 1200, 1060, 1249, 1109
MOUNT_TRAIL_X = 1225
COVIL_GATE_ACTIONID = 45004


def build_mountain(b, sid, tpls, rng):
    notes = []
    x0, y0, x1, y1 = MOUNT_X0, MOUNT_Y0, MOUNT_X1, MOUNT_Y1
    b.fill(x0, y0, x1, y1, BV.STONE_FLOOR)

    # corredor ligando o fim das Ruinas (y=1049) ate aqui, contornando o gap
    # y1050-1059 (nenhuma das duas zonas usa essa faixa).
    b.path(MOUNT_TRAIL_X, RUINS_Y1, MOUNT_TRAIL_X, y0, BV.DIRT, width=3)
    sign(b, MOUNT_TRAIL_X - 3, RUINS_Y1 + 1,
         "<- Ruinas do Cla Marionetista  |  Montanha do Trovao ->")

    # trilha de pedra sinuosa flanqueada por abismo (agua) — penhascos.
    # trail_w cobre o pior caso (deslocamento da curva +- 3) + o maior offset
    # de spawn (+-3) com folga, senao um monstro podia cair no "abismo".
    trail_w = 8
    for y in range(y0, y1 + 1):
        wobble = int(3 * ((y - y0) % 14) / 14) - 1
        cx = MOUNT_TRAIL_X + wobble * 3
        for x in range(x0, x1 + 1):
            if cx - trail_w <= x <= cx + trail_w:
                continue
            b.ground(x, y, BV.WATER)
            b.clear_items(x, y)

    sign(b, MOUNT_TRAIL_X, y0 + 2, "Montanha do Trovao (nivel 50-80) - cuidado com o abismo")

    # planalto do topo (sul) — os 2 bosses + o portal gated pro Covil
    plateau = (MOUNT_TRAIL_X - 10, y1 - 10, MOUNT_TRAIL_X + 10, y1)
    px0, py0, px1, py1 = plateau
    for y in range(py0, py1 + 1):
        for x in range(px0, px1 + 1):
            c = b.cells.get((x, y))
            if c is not None:
                b.ground(x, y, BV.STONE_FLOOR)
                b.clear_items(x, y)
    b.put(px0 + 1, py0 + 1, BV.TORCH)
    b.put(px1 - 1, py0 + 1, BV.TORCH)
    sign(b, px0 + 1, py0 + 2, "Topo da Montanha - a Dupla Imortal")

    partner_pos = (MOUNT_TRAIL_X - 4, py1 - 3)
    oni_pos = (MOUNT_TRAIL_X + 4, py1 - 3)

    gate_pos = (MOUNT_TRAIL_X, py1 - 6)
    b.clear_items(*gate_pos)
    b.put(gate_pos[0], gate_pos[1], BV.TELEPORT_ITEM,
          tele_dest=(0, 0, FLOOR),      # ajustado por link_mountain_to_lair()
          action_id=COVIL_GATE_ACTIONID)
    sign(b, gate_pos[0] + 1, gate_pos[1],
         "Portal do Covil da Nuvem Vermelha - requer rank Anbu "
         "(gate actionid %d, ver sistema de rank)" % COVIL_GATE_ACTIONID)

    notes.append("montanha do trovao: complexo compacto x%d-%d,y%d-%d, trilha "
                 "sinuosa com abismo de agua, planalto do topo em %r, portal "
                 "gated (actionid %d) em %r" % (x0, x1, y0, y1, plateau,
                                                 COVIL_GATE_ACTIONID, gate_pos))

    spec = SpawnSpec()
    off = [(0, 0), (2, -1), (-2, 1), (1, 2), (-1, -2), (3, 0)]
    counts = [("Águia do Trovão", 5, 70), ("Oni da Geleira", 4, 90),
              ("Monge da Tempestade", 3, 100), ("Serpente de Magma", 3, 100)]
    cy = y0 + 8
    for (mon, count, stime) in counts:
        g = spec.group(MOUNT_TRAIL_X, cy, radius=4)
        for i in range(count):
            dx, dy = off[i % len(off)]
            g.add_monster(mon, dx, dy, spawntime=stime)
        cy += 9
    spec.group(*partner_pos, radius=2).add_monster("O Sócio Eterno", 0, 0, spawntime=7200)
    spec.group(*oni_pos, radius=2).add_monster("Oni Ancestral", 0, 0, spawntime=7200)

    return [], spec, notes, gate_pos


# ---------------------------------------------------- Covil da Nuvem Vermelha
LAIR_X0, LAIR_Y0, LAIR_X1, LAIR_Y1 = 1400, 1000, 1449, 1049
LAIR_HALL = (1400, 1005, 1409, 1019)
LAIR_CORRIDOR_Y = (1011, 1013)
LAIR_ROOM1 = (1412, 1004, 1417, 1010)
LAIR_ROOM2 = (1420, 1014, 1425, 1020)
LAIR_ROOM3 = (1428, 1004, 1433, 1010)
LAIR_FINAL = (1436, 1000, 1449, 1024)


def build_akatsuki_lair(b, sid, tpls, rng):
    """Masmorra final, ISOLADA (sem trilha a pe): so' alcancavel pelo
    teleporte gated no topo da Montanha (ver build_mountain/link_mountain)."""
    notes = []
    x0, y0, x1, y1 = LAIR_X0, LAIR_Y0, LAIR_X1, LAIR_Y1
    b.fill(x0, y0, x1, y1, BV.STONE_FLOOR)

    hx0, hy0, hx1, hy1 = LAIR_HALL
    b.walls(hx0, hy0, hx1, hy1, BV.STONE_WALL_H, BV.STONE_WALL_V, BV.STONE_WALL_C,
            doors=[(hx1, y) for y in range(LAIR_CORRIDOR_Y[0], LAIR_CORRIDOR_Y[1] + 1)])
    for x in range(hx0, hx1 + 1):
        for y in (hy0, hy1):
            c = b.cells.get((x, y))
            if c is not None and not c.items:
                b.put(x, y, BV.TORCH)

    landing = (hx0 + 4, hy0 + 3)
    exitpad = (hx0 + 2, hy0 + 3)
    b.clear_items(*landing)
    b.clear_items(*exitpad)
    # tele_dest do pad de saida e' ajustado por link_mountain_to_lair()
    b.put(exitpad[0], exitpad[1], BV.TELEPORT_ITEM, tele_dest=(0, 0, FLOOR))
    sign(b, hx0 + 1, hy0 + 1, "Covil da Nuvem Vermelha - Anbu/Kage, nivel 80-100")

    npcs = [
        ("Capitã Anbu Suzu", (hx0 + 6, hy0 + 5)),
        ("Fornecedor Enji", (hx0 + 6, hy0 + 7)),
    ]

    # corredor principal (piso primeiro; a parede do corredor so' e' fechada
    # DEPOIS que as salas abrem suas proprias portas — ver door_gaps abaixo —
    # senao a parede do corredor "vence" e a porta da sala nunca abre de
    # verdade, so' fica vazia por fora sem ligar com o corredor).
    for y in range(LAIR_CORRIDOR_Y[0], LAIR_CORRIDOR_Y[1] + 1):
        for x in range(hx1 + 1, LAIR_FINAL[0]):
            b.ground(x, y, BV.STONE_FLOOR)
            b.clear_items(x, y)

    door_gaps = set()

    def build_room(rect, door_x, boss_name, level, from_north):
        rx0, ry0, rx1, ry1 = rect
        b.fill(rx0, ry0, rx1, ry1, BV.STONE_FLOOR)
        door_y = ry1 if from_north else ry0
        b.walls(rx0, ry0, rx1, ry1, BV.STONE_WALL_H, BV.STONE_WALL_V, BV.STONE_WALL_C,
                doors=[(door_x, door_y)])
        door_gaps.add((door_x, door_y))
        for (tx, ty) in ((rx0 + 1, ry0 + 1), (rx1 - 1, ry0 + 1)):
            c = b.cells.get((tx, ty))
            if c is not None and not c.items:
                b.put(tx, ty, BV.TORCH)
        center = ((rx0 + rx1) // 2, (ry0 + ry1) // 2)
        sign(b, rx0 + 1, ry1 - 1 if from_north else ry0 + 1,
             "%s (nivel %d)" % (boss_name, level))
        return center

    c1 = build_room(LAIR_ROOM1, 1414, "O Vigia Ilusório", 85, from_north=True)
    c2 = build_room(LAIR_ROOM2, 1422, "O Mascarado das Sombras", 90, from_north=False)
    c3 = build_room(LAIR_ROOM3, 1430, "O Portador dos Seis Caminhos", 95, from_north=True)

    for x in range(hx1 + 1, LAIR_FINAL[0]):
        for y in (LAIR_CORRIDOR_Y[0] - 1, LAIR_CORRIDOR_Y[1] + 1):
            if (x, y) in door_gaps:
                continue
            c = b.cells.get((x, y))
            if c is not None and not c.items:
                b.put(x, y, BV.STONE_WALL_H)

    # sala final, grande, no extremo leste
    fx0, fy0, fx1, fy1 = LAIR_FINAL
    b.fill(fx0, fy0, fx1, fy1, BV.STONE_FLOOR)
    b.walls(fx0, fy0, fx1, fy1, BV.STONE_WALL_H, BV.STONE_WALL_V, BV.STONE_WALL_C,
            doors=[(fx0, y) for y in range(LAIR_CORRIDOR_Y[0], LAIR_CORRIDOR_Y[1] + 1)])
    for (tx, ty) in ((fx0 + 2, fy0 + 2), (fx1 - 2, fy0 + 2),
                     (fx0 + 2, fy1 - 2), (fx1 - 2, fy1 - 2)):
        c = b.cells.get((tx, ty))
        if c is not None and not c.items:
            b.put(tx, ty, BV.TORCH)
    b.put(fx0 + 2, fy0 + 1, BV.SIGN, text="O Ancestral da Nuvem Vermelha (nivel 100) - sala final")
    c4 = ((fx0 + fx1) // 2, (fy0 + fy1) // 2)

    notes.append("covil da nuvem vermelha: masmorra ISOLADA x%d-%d,y%d-%d, 4 salas de "
                 "boss sequenciais + sala final, entrada so por teleporte gated "
                 "(ver montanha do trovao)" % (x0, x1, y0, y1))

    spec = SpawnSpec()
    # corredor: SO' dy em {-1,0,1} (linha do meio = 1012) — as 3 linhas do
    # corredor nunca cruzam a parede das salas (que ficam em y<=1010 ou
    # y>=1014), entao qualquer dx dentro do corredor e' seguro.
    corridor_mid_x = (hx1 + 1 + LAIR_FINAL[0] - 1) // 2
    corridor_half = (LAIR_FINAL[0] - 1 - (hx1 + 1)) // 2
    g1 = spec.group(corridor_mid_x, 1012, radius=max(corridor_half, 3))
    for i in range(10):
        dx = int(-corridor_half + 1 + (2 * corridor_half - 2) * i / 9)
        dy = (i % 3) - 1
        g1.add_monster("Clone Branco", dx, dy, spawntime=90)
    g2 = spec.group(corridor_mid_x, 1012, radius=max(corridor_half, 3))
    for i in range(6):
        dx = int(-corridor_half + 2 + (2 * corridor_half - 4) * i / 5)
        dy = (i % 3) - 1
        g2.add_monster("Ninja Elite da Aurora", dx, dy, spawntime=110)
    spec.group(*c1, radius=2).add_monster("O Vigia Ilusório", 0, 0, spawntime=7200)
    spec.group(*c2, radius=2).add_monster("O Mascarado das Sombras", 0, 0, spawntime=7200)
    spec.group(*c3, radius=2).add_monster("O Portador dos Seis Caminhos", 0, 0, spawntime=7200)
    spec.group(*c4, radius=3).add_monster("O Ancestral da Nuvem Vermelha", 0, 0, spawntime=7200)

    # NPCs vao SO' na lista `npcs` devolvida (build_valley.build_spawns ja os
    # registra) — nao duplicar aqui, senao cada NPC aparece 2x no spawn.xml.
    return npcs, spec, notes, landing, exitpad


def link_mountain_to_lair(b, gate_pos, lair_landing, lair_exitpad):
    """Fecha o par de teleportes gate<->covil (regra anti-loop: o pouso de
    cada lado nunca pode ter, ele mesmo, outro teleporte por cima)."""
    gx, gy = gate_pos
    for it in b.cells[(gx, gy)].items:
        if it.id == BV.TELEPORT_ITEM and it.action_id == COVIL_GATE_ACTIONID:
            it.tele_dest = (lair_landing[0], lair_landing[1], FLOOR)
    lx, ly = lair_exitpad
    for it in b.cells[(lx, ly)].items:
        if it.id == BV.TELEPORT_ITEM:
            it.tele_dest = (gx, gy - 1, FLOOR)
    ret_landing = (gx, gy - 1)
    c = b.cells.get(ret_landing)
    if c is not None:
        b.clear_items(*ret_landing)


# =================================================================
# coordenador
# =================================================================

def build_all(b, sid, tpls):
    rng = b.rng
    notes = []
    npcs = []

    notes.extend(upgrade_village(b, sid, tpls, rng))

    c_npcs, c_spec, c_notes = build_coastal_tides(b, sid, tpls, rng)
    npcs += c_npcs
    notes.extend(c_notes)

    r_npcs, r_spec, r_notes = build_ruins(b, sid, tpls, rng)
    npcs += r_npcs
    notes.extend(r_notes)

    m_npcs, m_spec, m_notes, gate_pos = build_mountain(b, sid, tpls, rng)
    npcs += m_npcs
    notes.extend(m_notes)

    l_npcs, l_spec, l_notes, lair_landing, lair_exitpad = build_akatsuki_lair(b, sid, tpls, rng)
    npcs += l_npcs
    notes.extend(l_notes)

    link_mountain_to_lair(b, gate_pos, lair_landing, lair_exitpad)

    specs = [c_spec, r_spec, m_spec, l_spec]

    def add_spawns(sf):
        tm = tn = 0
        for s in specs:
            m, n = s.apply(sf)
            tm += m
            tn += n
        notes.append("regioes novas: %d monstros + %d NPCs em spawn groups" % (tm, tn))

    return npcs, add_spawns, notes
