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


# ==================================================== gates de rank (Missão A.2)
# actionid 45001..45005 = rank minimo 1 Genin..5 Kage (data/ranks.json,
# server/generated/scripts/naruto/rank_gate.lua). Os indices batem com
# NarutoRanks.zoneMinIndex (server/tfs/data/lib/naruto_ranks.lua), ja
# gerado a partir de data/ranks.json/progressao.md: floresta_da_morte=2,
# costa_das_mares=2, ruinas_do_cla_marionetista=2, montanha_do_trovao=3,
# covil_nuvem_vermelha=4. Floresta da Morte fica DE PROPOSITO sem gate fisico
# aqui (ver docs/sistemas/mapas.md): o Exame Chunin em si roda dentro dela
# (Instrutora Ibuki manda matar o Sapo Anciao/Serpente Branca, os DOIS la
# dentro) — gatear a entrada por Chunin criaria um paradoxo (precisa entrar
# pra virar Chunin, mas so Chunin entra). As outras 3 regioes sao destino
# de PROVA, nao de exame-em-andamento, entao o gate de zoneMinIndex vale.
#
# ACHADO #1 da auditoria de historia (docs/design/auditoria-historia.md, item
# A1, Lote M): a Costa das Mares (nivel 12-19, pensada pra Genin recem-saido
# da Floresta da Vila) estava com o MESMO gate de rank Chunin das Ruinas —
# um Genin L12-19 (sem ainda ter feito o Exame Chunin, que so acontece DEPOIS
# na Floresta da Morte) era barrado na entrada e nunca conseguia caçar la.
# O item de mapa (`gate_marker`, actionid) e o unico ponto de imposicao real
# (rank_gate.lua confere so o actionid do item, NAO consulta
# NarutoRanks.zoneMinIndex/data/ranks.json — ver server/generated/scripts/
# naruto/rank_gate.lua) — por isso ajustar aqui basta pra desbloquear o
# jogo, mesmo com data/ranks.json ainda listando costa_das_mares em
# unlocks.areas do Chunin (inconsistencia de dados fora do escopo desta
# missao de mapa; NAO editado aqui). Corrigido: a Costa usa actionid do gate
# "genin" (45001) — todo jogador ja nasce rank Genin (NarutoRanks.get()
# retorna indice 1 por padrao), entao o gate fica fisicamente presente
# (paridade visual com Ruinas/Montanha) mas NUNCA barra ninguem — equivalente
# a nao ter gate, sem precisar remover o item.
RANK_GATE_ACTIONID = {
    "genin": 45001, "chunin": 45002, "jonin": 45003, "anbu": 45004, "kage": 45005,
}


def place_rank_gate(b, sid, positions, rank, text=None, sign_pos=None):
    """Estampa o item `gate_marker` (walkable, carrega o actionid do rank) em
    TODAS as celulas de `positions` — o gate precisa cobrir a largura inteira
    da entrada, senao da pra contornar andando por uma trilha ao lado que nao
    tem o item. Nao apaga o chao (so empilha por cima, como toda decoracao).
    `text`/`sign_pos`: placa extra (so se a regiao ainda nao tiver uma placa
    de bifurcacao explicando o requisito de rank)."""
    aid = RANK_GATE_ACTIONID[rank]
    n = 0
    for (x, y) in positions:
        c = b.cells.get((x, y))
        if c is None:
            continue
        b.put(x, y, sid["gate_marker"], action_id=aid)
        n += 1
    if text and positions:
        px, py = sign_pos if sign_pos else positions[0]
        sign(b, px, py, text)
    return n


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

    # gate de rank (Achado #1 / item A1 da auditoria de historia, Lote M): a
    # Costa e a PRIMEIRA regiao pos-tutorial (nivel 12-19, Genin) — nao pode
    # exigir Chunin (so obtido no Exame Chunin, que roda DEPOIS na Floresta
    # da Morte). Gate trocado de "chunin" pra "genin" (todo jogador ja tem):
    # o item fisico continua la (mesma largura width=3, mesma posicao), so
    # nao barra mais ninguem — ver comentario longo em RANK_GATE_ACTIONID.
    n_gate_costa = place_rank_gate(
        b, sid, [(COAST_PATH_X - 1, y0), (COAST_PATH_X, y0), (COAST_PATH_X + 1, y0)],
        "genin", text="Costa das Mares - nivel recomendado 12+.",
        sign_pos=(COAST_PATH_X - 2, y0))

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
        # Mestre de Tarefas Umi (task_master_coastal, data/npcs/coastal_tides.json)
        # — na entrada segura da vila de pescadores (mesmo x/y ja gravado no
        # JSON; so faltava o spawn no mapa, ver docs/sistemas/mapas.md).
        ("Mestre de Tarefas Umi", (COAST_PATH_X, 1147)),
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
    notes.append("costa das mares: gate de rank Genin (actionid %d, nunca barra "
                 "ninguem — Achado #1/A1, era Chunin) — %d marcadores em (%d,%d)"
                 % (RANK_GATE_ACTIONID["genin"], n_gate_costa, COAST_PATH_X, y0))

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

    # Item A2 da auditoria de historia (Lote M): Aprendiz Mascarado (masked_
    # apprentice) nao tinha NENHUM spawn solto na Costa — so aparecia como
    # reforco invocado na fase 60% HP do Espadachim (data/monsters/
    # coastal_tides.json), o que tornava `q_coastal_apprentice` (matar 6)
    # praticamente impossivel sem repetir a luta do boss 6x. 3 unidades numa
    # praia aberta ENTRE o grupo do Guardiao da Neblina (y=1139, acima) e a
    # arena do boss (boss_pos, y~1166, abaixo) — areia caminhavel (y<1155),
    # longe das 4 cabanas (x 1021-1023/1035-1037) e dos postes de amarracao
    # (x=1027/1031, y=1149/1160) pra nao empilhar em cima de item bloqueante.
    _apprentice_pts = [(-4, -1), (3, 0), (1, 1)]  # -> (1025,1152)/(1032,1153)/(1030,1154)
    g4 = spec.group(COAST_PATH_X, 1153, radius=5)
    for (dx, dy) in _apprentice_pts:
        b.clear_items(COAST_PATH_X + dx, 1153 + dy)
        g4.add_monster("Aprendiz Mascarado", dx, dy, spawntime=90)
    notes.append("costa das mares: Aprendiz Mascarado agora tem spawn solto (%d unidades, "
                 "respawn 90s) entre o Guardiao da Neblina e a arena do boss — Achado/A2"
                 % len(_apprentice_pts))

    spec.group(*boss_pos, radius=2).add_monster("Espadachim da Névoa", 0, 0, spawntime=7200)

    # NPCs vao SO' na lista `npcs` devolvida (build_valley.build_spawns ja os
    # registra) — nao duplicar aqui, senao cada NPC aparece 2x no spawn.xml.
    return npcs, spec, notes


# ------------------------------------------------ Ruinas do Cla Marionetista
RUINS_X0, RUINS_Y0, RUINS_X1, RUINS_Y1 = 1200, 1000, 1249, 1049
RUINS_GATE_Y = (1020, 1021)


def ruin_room(b, sid, rng, rect, doors, weather=0.3):
    """Sala fechada das Ruinas: piso `ruins_floor_*`, paredes de pedra
    intactas (b.walls, com um vao real em `doors` — celulas sem item, floor
    aberto) e ~`weather` fracao das paredes trocadas por `ruin_wall_broken`
    (mesma silhueta quebrada, ainda bloqueia) pra ler como ruina de verdade,
    nao um predio novo."""
    x0, y0, x1, y1 = rect
    doors = set(doors)
    ruins_floor = [sid[k] for k in ("ruins_floor_0", "ruins_floor_1", "ruins_floor_2") if k in sid]
    b.fill(x0, y0, x1, y1, ruins_floor or BV.STONE_FLOOR)
    b.walls(x0, y0, x1, y1, BV.STONE_WALL_H, BV.STONE_WALL_V, BV.STONE_WALL_C, doors=doors)
    wall_cells = ([(x, y0) for x in range(x0 + 1, x1)] + [(x, y1) for x in range(x0 + 1, x1)] +
                  [(x0, y) for y in range(y0 + 1, y1)] + [(x1, y) for y in range(y0 + 1, y1)])
    broken_id = sid.get("ruin_wall_broken")
    if broken_id:
        for (wx, wy) in wall_cells:
            if (wx, wy) in doors:
                continue
            if rng.random() < weather:
                b.clear_items(wx, wy)
                b.put(wx, wy, broken_id)
    return rect


def build_ruins(b, sid, tpls, rng):
    notes = []
    x0, y0, x1, y1 = RUINS_X0, RUINS_Y0, RUINS_X1, RUINS_Y1
    ruins_floor = [sid[k] for k in ("ruins_floor_0", "ruins_floor_1", "ruins_floor_2") if k in sid]
    b.fill(x0, y0, x1, y1, ruins_floor or BV.DIRT)
    # terra invadindo (pedido da missão): manchas de BV.DIRT substituindo o
    # chao de pedra rachada em algumas manchas circulares — a mesma ideia do
    # par grass_dirt, aplicada manualmente ao GROUND (Builder.blob() poe
    # ITENS, nao troca o chao, entao nao serve aqui).
    for _ in range(9):
        cx = x0 + 4 + rng.randrange(x1 - x0 - 8)
        cy = y0 + 4 + rng.randrange(y1 - y0 - 8)
        r = 2.0 + rng.random() * 2.0
        ri = int(r) + 1
        for dy in range(-ri, ri + 1):
            for dx in range(-ri, ri + 1):
                if dx * dx + (dy * 1.3) ** 2 > r * r:
                    continue
                c = b.cells.get((cx + dx, cy + dy))
                if c is not None and c.ground in (ruins_floor if isinstance(ruins_floor, list) else []):
                    b.ground(cx + dx, cy + dy, BV.DIRT)

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
    # corredor de entrada, estreito (largura 2) — primeiro trecho legivel
    # como CORREDOR antes do patio abrir (pedido da missao: "corredores,
    # salas menores, um patio central", nao um salao unico).
    b.path(BV.DEATH_WALL[2] + 1, RUINS_GATE_Y[0], x0 + 8, RUINS_GATE_Y[0], BV.DIRT, width=2)
    # gate de rank (ranks.json: ruinas_do_cla_marionetista exige Chunin) —
    # logo depois do portao, cobrindo a largura do corredor.
    n_gate_ruins = place_rank_gate(
        b, sid, [(x0, RUINS_GATE_Y[0]), (x0, RUINS_GATE_Y[1])], "chunin")
    # Mestre de Tarefas Dokan (task_master_ruins, data/npcs/ruins.json) — base
    # segura logo apos o gate, antes do patio.
    dokan_pos = (x0 + 2, RUINS_GATE_Y[0])
    b.clear_items(*dokan_pos)

    # Item B1 da auditoria de historia (Lote M): Ancião Kaito (quest_giver_
    # ruins) e Tsubaki, a Escavadora (merchant_ruins) NUNCA tinham sido
    # posicionados no mapa (so existiam em data/npcs/ruins.json, sem spawn) —
    # bloqueava as 7 missoes das Ruinas e metade do Exame Jonin. Mesmo padrao
    # do Dokan (perto do gate/entrada), 2 tiles a mais no eixo x e y=+2 pra
    # sair do corredor estreito (largura 2, so' cobre y=1019-1020) e cair no
    # chao aberto do patio (ruins_floor, sem parede por perto — room_a comeca
    # em y0+4=1004, bem ao norte) — tile livre, alcancavel, nao bloqueia a
    # passagem (o corredor em si continua livre em y=1019-1020).
    kaito_pos = (x0 + 5, RUINS_GATE_Y[0] + 2)
    tsubaki_pos = (x0 + 7, RUINS_GATE_Y[0] + 2)
    b.clear_items(*kaito_pos)
    b.clear_items(*tsubaki_pos)

    sign(b, x0 + 9, RUINS_GATE_Y[0] - 1, "Ruinas do Cla Marionetista (nivel 25-50)")

    # -- 3 SALAS MENORES fechadas (piso proprio + paredes com trechos
    # quebrados), cada uma abrindo pro patio central por um vao real --------
    room_a = ruin_room(b, sid, rng, (x0 + 4, y0 + 4, x0 + 14, y0 + 14),
                        doors=[(x0 + 8, y0 + 14), (x0 + 9, y0 + 14)])
    sign(b, x0 + 5, y0 + 5, "Camara Norte")
    # porta a OESTE (nao ao sul): ao sul dessa sala fica a parede norte do
    # salao do boss (hx0=x1-13=x0+36..x1, hy0=y0+15) — uma porta ao sul
    # bateria direto nela e isolaria a sala (achado do 1o build/BFS).
    room_b = ruin_room(b, sid, rng, (x0 + 34, y0 + 4, x0 + 45, y0 + 14),
                        doors=[(x0 + 34, y0 + 8), (x0 + 34, y0 + 9)])
    sign(b, x0 + 35, y0 + 5, "Camara do Xama")
    room_c = ruin_room(b, sid, rng, (x0 + 2, y0 + 30, x0 + 13, y0 + 41),
                        doors=[(x0 + 6, y0 + 30), (x0 + 7, y0 + 30)])
    sign(b, x0 + 3, y0 + 31, "Camara Sul")

    # -- patio CENTRAL, marcado e decorado (pilares caidos + entulho em anel,
    # nao espalhado ao acaso) ------------------------------------------------
    patio_c = (x0 + 22, y0 + 24)
    sign(b, patio_c[0] - 3, patio_c[1] - 7, "Patio Central das Ruinas")
    rubble_pool = [sid[k] for k in ("rock_medium", "rock_large", "tree_stump_0",
                                     "tree_stump_1", "fallen_branch", "pillar_fallen",
                                     "broken_puppet")
                   if k in sid]
    if rubble_pool:
        ring = [(-6, -3), (6, -3), (-6, 3), (6, 3), (0, -6), (0, 6), (-4, 5), (4, -5)]
        for (dx, dy) in ring:
            rx, ry = patio_c[0] + dx, patio_c[1] + dy
            c = b.cells.get((rx, ry))
            if c is not None and not c.items:
                b.put(rx, ry, rng.choice(rubble_pool))

    # -- 1 trecho de parede solta (cota desabada, so' 1 lado) perto do patio,
    # pura atmosfera — mistura ruin_wall_broken pra variar a silhueta --------
    loose_x = x0 + 30
    for yy in range(y0 + 22, y0 + 30):
        c = b.cells.get((loose_x, yy))
        if c is not None and not c.items:
            wid = sid.get("ruin_wall_broken") if rng.random() < 0.5 else BV.STONE_WALL_V
            b.put(loose_x, yy, wid)
    if rubble_pool:
        for (rx, ry) in ((loose_x - 1, y0 + 24), (loose_x + 1, y0 + 27)):
            c = b.cells.get((rx, ry))
            if c is not None and not c.items:
                b.put(rx, ry, rng.choice(rubble_pool))

    # salao do Marionetista, intacto, no fundo (leste) — 2 pilares de pe +
    # marionetes quebradas (pedido da missao: sala do boss com identidade)
    hall = (x1 - 13, y0 + 15, x1 - 1, y0 + 35)
    hx0, hy0, hx1, hy1 = hall
    b.fill(hx0, hy0, hx1, hy1, ruins_floor or BV.STONE_FLOOR)
    b.walls(hx0, hy0, hx1, hy1, BV.STONE_WALL_H, BV.STONE_WALL_V, BV.STONE_WALL_C,
            doors=[(hx0, (hy0 + hy1) // 2)])
    b.put(hx0 + 2, hy0 + 2, BV.TORCH)
    b.put(hx1 - 2, hy0 + 2, BV.TORCH)
    hall_door = (hx0, (hy0 + hy1) // 2)
    b.path(hall_door[0] - 6, hall_door[1], hall_door[0] - 1, hall_door[1], BV.DIRT, width=2)
    sign(b, hx0 + 1, hy0 + 1, "Salao do Marionetista")
    boss_pos = ((hx0 + hx1) // 2, (hy0 + hy1) // 2)
    pillar_id = sid.get("pillar_standing")
    if pillar_id:
        for (px, py) in ((boss_pos[0] - 4, boss_pos[1] - 3), (boss_pos[0] + 4, boss_pos[1] + 3)):
            c = b.cells.get((px, py))
            if c is not None and not c.items:
                b.put(px, py, pillar_id)
    puppet_id = sid.get("broken_puppet")
    if puppet_id:
        for (px, py) in ((hx0 + 3, hy1 - 2), (hx1 - 3, hy0 + 5)):
            c = b.cells.get((px, py))
            if c is not None and not c.items:
                b.put(px, py, puppet_id)

    notes.append("ruinas do cla marionetista v3: corredor de entrada + 3 salas fechadas "
                 "(%r, %r, %r) + patio central em %r + salao do boss com 2 pilares de pe, "
                 "piso proprio ruins_floor_0/1/2 (era stone_floor generico)"
                 % (room_a, room_b, room_c, patio_c))
    notes.append("ruinas: gate de rank Chunin (actionid %d), %d marcadores em x=%d"
                 % (RANK_GATE_ACTIONID["chunin"], n_gate_ruins, x0))

    spec = SpawnSpec()
    off = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1)]
    # centros dentro das SALAS/patio novos (substituem os antigos "no meio do
    # dirt aberto" — mantém a MESMA lista de monstros/quantidades da missão
    # anterior, só reposicionados pra dentro da geometria nova).
    monster_centers = [
        ("Marionete de Combate", 6, 70, (room_a[0] + 5, room_a[1] + 5)),
        ("Sentinela de Pedra", 4, 90, patio_c),
        ("Guerreiro Espectral", 3, 100, (room_c[0] + 5, room_c[1] + 5)),
        ("Xamã da Maldição", 3, 110, (room_b[0] + 5, room_b[1] + 5)),
    ]
    for (mon, count, stime, (cx, cy)) in monster_centers:
        g = spec.group(cx, cy, radius=3)
        for i in range(count):
            dx, dy = off[i % len(off)]
            g.add_monster(mon, dx, dy, spawntime=stime)
    spec.group(hall_door[0] - 4, hall_door[1], radius=2) \
        .add_monster("Desertor de Elite", 0, 0, spawntime=1800)
    spec.group(*boss_pos, radius=3).add_monster("Marionetista das Ruínas", 0, 0, spawntime=7200)

    npcs = [
        ("Mestre de Tarefas Dokan", dokan_pos),
        ("Ancião Kaito", kaito_pos),
        ("Tsubaki, a Escavadora", tsubaki_pos),
    ]
    return npcs, spec, notes


# --------------------------------------------------------- Montanha do Trovao
MOUNT_X0, MOUNT_Y0, MOUNT_X1, MOUNT_Y1 = 1200, 1060, 1249, 1109
MOUNT_TRAIL_X = 1225
COVIL_GATE_ACTIONID = 45004

#: registrado por `_install_snow_rock_border` — usado só pra log/relatorio.
_SNOW_ROCK_INSTALLED = [False]


def _install_snow_rock_border(sid):
    """Registra 'rock'/'snow' no autoborder GENERICO de build_valley.py (mesma
    maquinaria de grass_dirt/cobble_dirt/etc — ver docs/sistemas/mapas.md).
    Puramente ADITIVO: os ids novos (>=30386) nao colidem com nenhum dos
    conjuntos GRASS/DIRT/COBBLE/MUD/WATER/SAND ja existentes, entao nenhuma
    outra regiao do mapa e afetada. Precisa rodar ANTES de apply_borders()
    (chamado por build_all(), que roda antes de apply_borders() no main())."""
    rock_ids = {sid[k] for k in ("mountain_rock_0", "mountain_rock_1") if k in sid}
    snow_ids = {sid[k] for k in ("mountain_snow_0",) if k in sid}
    if not rock_ids or not snow_ids:
        return False
    orig_classify = BV.classify_ground

    def classify_ground2(gid):
        if gid in rock_ids:
            return "rock"
        if gid in snow_ids:
            return "snow"
        return orig_classify(gid)

    BV.classify_ground = classify_ground2
    BV.BORDER_INVADERS = dict(BV.BORDER_INVADERS)
    BV.BORDER_INVADERS["rock"] = ("snow",)
    BV.BORDER_PAIR_KEY = dict(BV.BORDER_PAIR_KEY)
    BV.BORDER_PAIR_KEY[("snow", "rock")] = "snow_rock"
    BV._MATERIAL_RANK = dict(BV._MATERIAL_RANK)
    BV._MATERIAL_RANK["snow"] = 6
    _SNOW_ROCK_INSTALLED[0] = True
    return True


def build_mountain(b, sid, tpls, rng):
    notes = []
    x0, y0, x1, y1 = MOUNT_X0, MOUNT_Y0, MOUNT_X1, MOUNT_Y1
    rock_floor = [sid[k] for k in ("mountain_rock_0", "mountain_rock_1") if k in sid]
    snow_id = sid.get("mountain_snow_0")
    ice_id = sid.get("frozen_lake")
    _install_snow_rock_border(sid)
    b.fill(x0, y0, x1, y1, rock_floor or BV.STONE_FLOOR)

    # corredor ligando o fim das Ruinas (y=1049) ate aqui, contornando o gap
    # y1050-1059 (nenhuma das duas zonas usa essa faixa).
    b.path(MOUNT_TRAIL_X, RUINS_Y1, MOUNT_TRAIL_X, y0, BV.DIRT, width=3)
    sign(b, MOUNT_TRAIL_X - 3, RUINS_Y1 + 1,
         "<- Ruinas do Cla Marionetista  |  Montanha do Trovao ->")

    # Item C1 da auditoria de historia (Lote M): Mestra Yuki (quest_giver_
    # mountain) e Ferreiro Genzo (merchant_mountain) NUNCA tinham sido
    # posicionados — bloqueava as 7 missoes da Montanha e as 2 metades do
    # Exame Anbu. AO CONTRARIO do Mestre de Tarefas Kaji (colocado DEPOIS do
    # gate, ja dentro da zona Jonin — ok pra ele, so' um quadro de tarefas
    # repetiveis), o dador de missao/mercador precisa ficar acessivel a quem
    # ainda NAO tem rank Jonin: e a missao de Yuki que guia o jogador ate o
    # Exame Anbu, entao ela nao pode depender do proprio gate que a missao
    # dela ajuda a superar (mesmo paradoxo que a Floresta da Morte evita com
    # Chunin). Alarga um pequeno patamar (7 tiles, largura da trilha 3 vezes
    # o normal) 3 tiles ANTES do gate (fora da zona gateada, lado Ruinas) so'
    # pra caber os 2 NPCs lado a lado sem bloquear a passagem central.
    PRE_GATE_Y0, PRE_GATE_Y1 = y0 - 3, y0 - 1
    b.fill(MOUNT_TRAIL_X - 3, PRE_GATE_Y0, MOUNT_TRAIL_X + 3, PRE_GATE_Y1, BV.DIRT)
    for _yy in range(PRE_GATE_Y0, PRE_GATE_Y1 + 1):
        for _xx in range(MOUNT_TRAIL_X - 3, MOUNT_TRAIL_X + 4):
            b.clear_items(_xx, _yy)
    yuki_pos = (MOUNT_TRAIL_X - 3, y0 - 2)
    genzo_pos = (MOUNT_TRAIL_X + 3, y0 - 2)
    b.clear_items(*yuki_pos)
    b.clear_items(*genzo_pos)
    sign(b, MOUNT_TRAIL_X - 1, PRE_GATE_Y0, "Posto avancado da Montanha do Trovao")

    # gate de rank (ranks.json: montanha_do_trovao exige Jonin) — na entrada,
    # cobrindo a largura do corredor (width=3).
    n_gate_mount = place_rank_gate(
        b, sid, [(MOUNT_TRAIL_X - 1, y0), (MOUNT_TRAIL_X, y0), (MOUNT_TRAIL_X + 1, y0)],
        "jonin", text="Alem daqui: nivel Jonin ou superior.",
        sign_pos=(MOUNT_TRAIL_X - 4, y0 + 1))
    # Mestre de Tarefas Kaji (task_master_mountain, data/npcs/mountain.json) —
    # base segura logo apos o gate, no pe da trilha.
    kaji_pos = (MOUNT_TRAIL_X + 3, y0 + 2)
    b.clear_items(*kaji_pos)

    # trilha de pedra sinuosa flanqueada por abismo (agua) — penhascos. Vai so
    # ate o pe do planalto (PLATEAU_Y0); o planalto e' plano, tratado a parte.
    PLATEAU_Y0 = y1 - 24
    trail_w = 8
    for y in range(y0, PLATEAU_Y0):
        wobble = int(3 * ((y - y0) % 14) / 14) - 1
        cx = MOUNT_TRAIL_X + wobble * 3
        for x in range(x0, x1 + 1):
            if cx - trail_w <= x <= cx + trail_w:
                continue
            b.ground(x, y, BV.WATER)
            b.clear_items(x, y)
        # neve nas bordas da trilha, so no ultimo trecho antes do planalto
        # (pedido da missao: "neve nas bordas/topo") — 2 tiles de cada lado,
        # por cima da rocha (nao do abismo).
        if snow_id and y >= PLATEAU_Y0 - 10:
            for sx in (cx - trail_w, cx - trail_w + 1, cx + trail_w - 1, cx + trail_w):
                c = b.cells.get((sx, y))
                if c is not None and c.ground in (rock_floor if isinstance(rock_floor, list) else []):
                    b.ground(sx, y, snow_id)

    sign(b, MOUNT_TRAIL_X, y0 + 2, "Montanha do Trovao (nivel 50-80) - cuidado com o abismo")

    # -- 2 PATAMARES (muros de rocha + passagem estreita, alternando o lado —
    # simula a subida em zigue-zague pedida na missao, ja que o z nao muda) --
    def _band_at(y):
        wobble = int(3 * ((y - y0) % 14) / 14) - 1
        cx = MOUNT_TRAIL_X + wobble * 3
        return cx - trail_w, cx + trail_w

    terrace_ys = [y0 + 14, y0 + 22]
    terrace_gap_side = [-1, 1]     # alterna oeste/leste a cada patamar
    for ti, ty in enumerate(terrace_ys):
        lo0, hi0 = _band_at(ty)
        # ACHADO (build/BFS): a trilha "balanca" de largura (`wobble`, periodo
        # 14) e o patamar y0+14 cai EXATAMENTE numa transicao de periodo — o
        # gap escolhido so' a partir da banda da PROPRIA linha podia ficar
        # fora da banda da linha vizinha (norte OU sul), tornando a "unica
        # passagem" um beco sem saida (o muro virava intransponivel de
        # verdade, nao so' visualmente). Corrigido: o gap so' pode ficar na
        # INTERSECAO das bandas de ty-1/ty/ty+1, garantindo que a passagem
        # sempre conecta os dois lados de verdade.
        lo_prev, hi_prev = _band_at(ty - 1)
        lo_next, hi_next = _band_at(ty + 1)
        safe_lo = max(lo0, lo_prev, lo_next)
        safe_hi = min(hi0, hi_prev, hi_next)
        mid = (safe_lo + safe_hi) // 2
        bias = terrace_gap_side[ti] * max(0, min(2, (safe_hi - safe_lo) // 2 - 1))
        gap_cx = max(safe_lo + 1, min(safe_hi - 1, mid + bias))
        for x in range(lo0, hi0 + 1):
            if gap_cx - 1 <= x <= gap_cx + 1:
                continue
            c = b.cells.get((x, ty))
            if c is not None:
                b.clear_items(x, ty)
                b.put(x, ty, BV.STONE_WALL_H)
        c = b.cells.get((gap_cx, ty - 1))
        if c is not None and not c.items:
            b.put(gap_cx, ty - 1, BV.TORCH)

    # -- lago gelado pequeno, num trecho largo da trilha entre os 2 patamares.
    # So' o lado LESTE de cada linha vira gelo (calculado por linha, com
    # _band_at, nao um cx fixo — a banda "balanca" por causa do wobble
    # periodico, um cx fixo podia sobrar fora da banda real de uma linha e
    # deixar um buraco sem chao ali); o lado OESTE (>= 3 tiles) fica sempre
    # rocha caminhavel, garantindo uma faixa continua ao longo de toda a
    # extensao do lago (mesmo achado do bug dos patamares acima).
    lake_y0, lake_y1 = terrace_ys[0] + 2, terrace_ys[1] - 2
    if ice_id:
        for ly in range(lake_y0, lake_y1 + 1):
            lo, hi = _band_at(ly)
            for lx in range(lo + 5, hi - 1):
                c = b.cells.get((lx, ly))
                if c is not None:
                    b.clear_items(lx, ly)
                    b.ground(lx, ly, ice_id)
        lo_sign, _ = _band_at(lake_y0)
        sign(b, lo_sign + 1, lake_y0 - 1, "Lago Gelado - gelo fino, nao ande sobre ele")
        notes.append("montanha: lago gelado em y=%d-%d (lado leste da trilha, lado "
                     "oeste sempre livre)" % (lake_y0, lake_y1))

    # ===================================================================
    # PLANALTO DO TOPO — dividido em 2: SANTUARIO (norte, O Socio Eterno)
    # e ARENA (sul, Oni Ancestral + portal do Covil), separados por uma
    # parede com 1 passagem estreita — nunca aparecem juntos na mesma tela
    # (achado do tour in-game v2.1: ficavam a so' 8 tiles um do outro).
    # ===================================================================
    plateau = (MOUNT_TRAIL_X - 10, PLATEAU_Y0, MOUNT_TRAIL_X + 10, y1)
    px0, py0, px1, py1 = plateau
    for y in range(py0, py1 + 1):
        for x in range(px0, px1 + 1):
            c = b.cells.get((x, y))
            if c is not None:
                b.ground(x, y, rock_floor or BV.STONE_FLOOR)
                b.clear_items(x, y)
    # neve no TOPO (perimetro inteiro do planalto, pedido da missao)
    if snow_id:
        for x in range(px0, px1 + 1):
            for y in (py0, py1):
                b.ground(x, y, snow_id)
        for y in range(py0, py1 + 1):
            for x in (px0, px1):
                b.ground(x, y, snow_id)

    SHRINE_Y1 = py0 + 7
    DIVIDER_Y = SHRINE_Y1 + 1
    shrine = (px0, py0, px1, SHRINE_Y1)
    arena = (px0, DIVIDER_Y + 1, px1, py1)

    # parede divisoria com 1 passagem estreita (3 tiles) no meio
    gap_x = (px0 + px1) // 2
    for x in range(px0 + 1, px1):
        if gap_x - 1 <= x <= gap_x + 1:
            continue
        c = b.cells.get((x, DIVIDER_Y))
        if c is not None:
            b.clear_items(x, DIVIDER_Y)
            b.put(x, DIVIDER_Y, BV.STONE_WALL_H)
    for tx in (gap_x - 2, gap_x + 2):
        c = b.cells.get((tx, DIVIDER_Y - 1))
        if c is not None and not c.items:
            b.put(tx, DIVIDER_Y - 1, BV.TORCH)
    sign(b, gap_x - 1, DIVIDER_Y - 2, "Santuario do Socio Eterno ->  <- Arena do Oni Ancestral")

    # -- santuario (norte): O Socio Eterno + mobilia de santuario (mesmos
    # itens da decor v2 do templo — estatua/lanterna — pra dar leitura clara
    # de "lugar sagrado", nao so um boss solto) + bandeiras de oracao --------
    partner_pos = (MOUNT_TRAIL_X, shrine[1] + 5)
    statue_id, lantern_id, flag_id = sid.get("shrine_statue_mossy"), sid.get("stone_lantern"), sid.get("prayer_flag_post")
    if statue_id:
        c = b.cells.get((partner_pos[0], partner_pos[1] - 2))
        if c is not None and not c.items:
            b.put(partner_pos[0], partner_pos[1] - 2, statue_id)
    for (lx, ly) in ((partner_pos[0] - 3, partner_pos[1] - 1), (partner_pos[0] + 3, partner_pos[1] - 1)):
        if lantern_id:
            c = b.cells.get((lx, ly))
            if c is not None and not c.items:
                b.put(lx, ly, lantern_id)
    if flag_id:
        for (fx, fy) in ((shrine[0] + 2, shrine[1] + 2), (shrine[2] - 2, shrine[1] + 2),
                          (shrine[0] + 2, shrine[3] - 1), (shrine[2] - 2, shrine[3] - 1)):
            c = b.cells.get((fx, fy))
            if c is not None and not c.items:
                b.put(fx, fy, flag_id)
    sign(b, shrine[0] + 1, shrine[1] + 1, "Santuario do Socio Eterno")

    # -- arena (sul): Oni Ancestral + portal gated pro Covil ----------------
    oni_pos = (MOUNT_TRAIL_X, arena[3] - 3)
    if flag_id:
        for (fx, fy) in ((arena[0] + 2, arena[1] + 1), (arena[2] - 2, arena[1] + 1)):
            c = b.cells.get((fx, fy))
            if c is not None and not c.items:
                b.put(fx, fy, flag_id)
    sign(b, arena[0] + 1, arena[1] + 1, "Arena do Oni Ancestral")

    gate_pos = (MOUNT_TRAIL_X, arena[3] - 6)
    b.clear_items(*gate_pos)
    b.put(gate_pos[0], gate_pos[1], BV.TELEPORT_ITEM,
          tele_dest=(0, 0, FLOOR),      # ajustado por link_mountain_to_lair()
          action_id=COVIL_GATE_ACTIONID)
    sign(b, gate_pos[0] + 1, gate_pos[1],
         "Portal do Covil da Nuvem Vermelha - requer rank Anbu "
         "(gate actionid %d, ver sistema de rank)" % COVIL_GATE_ACTIONID)

    notes.append("montanha do trovao v3: patio dividido em SANTUARIO %r (O Socio Eterno) "
                 "e ARENA %r (Oni Ancestral + portal do Covil), separados por parede+vao "
                 "estreito em y=%d — distancia entre os 2 bosses agora %d tiles (era 8)"
                 % (shrine, arena, DIVIDER_Y, abs(oni_pos[1] - partner_pos[1])))
    notes.append("montanha: 2 patamares (muros de rocha + passagem estreita alternando "
                 "lado) simulando subida em zigue-zague, piso proprio mountain_rock_0/1 "
                 "+ neve mountain_snow_0/border_snow_rock_* (era stone_floor generico)")
    notes.append("montanha: gate de rank Jonin (actionid %d), %d marcadores em y=%d"
                 % (RANK_GATE_ACTIONID["jonin"], n_gate_mount, y0))
    notes.append("montanha: Mestra Yuki %r e Ferreiro Genzo %r posicionados ANTES do "
                 "gate (posto avancado, y=%d-%d) — acessiveis sem precisar ja ser Jonin, "
                 "ao contrario do Kaji que fica depois — Achado/C1" % (yuki_pos, genzo_pos,
                 PRE_GATE_Y0, PRE_GATE_Y1))

    # linhas-perigo (patamar OU lago) + 1 de margem — nenhum centro/offset de
    # spawn pode cair nelas (achado do build/BFS: varios grupos cravavam
    # criaturas em cima do gelo/muro novo, que agora BLOQUEIAM de verdade).
    hazard_rows = set(terrace_ys) | set(range(lake_y0, lake_y1 + 1))

    def safe_cy(y):
        return all((y + d) not in hazard_rows for d in (-1, 0, 1))

    spec = SpawnSpec()
    off = [(0, 0), (2, 0), (-2, 0), (1, 1), (-1, -1), (3, 0)]   # dy so' -1..1
    counts = [("Águia do Trovão", 5, 70), ("Oni da Geleira", 4, 90),
              ("Monge da Tempestade", 3, 100), ("Serpente de Magma", 3, 100)]
    cy = y0 + 6
    for (mon, count, stime) in counts:
        while not safe_cy(cy) and cy < PLATEAU_Y0 - 1:
            cy += 1
        cy = min(cy, PLATEAU_Y0 - 2)
        while not safe_cy(cy) and cy > y0 + 6:
            cy -= 1
        g = spec.group(MOUNT_TRAIL_X, cy, radius=3)
        for i in range(count):
            dx, dy = off[i % len(off)]
            g.add_monster(mon, dx, dy, spawntime=stime)
        cy += 5
    spec.group(*partner_pos, radius=2).add_monster("O Sócio Eterno", 0, 0, spawntime=7200)
    spec.group(*oni_pos, radius=2).add_monster("Oni Ancestral", 0, 0, spawntime=7200)

    npcs = [
        ("Mestre de Tarefas Kaji", kaji_pos),
        ("Mestra Yuki", yuki_pos),
        ("Ferreiro Genzo", genzo_pos),
    ]
    return npcs, spec, notes, gate_pos


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
    teleporte gated no topo da Montanha (ver build_mountain/link_mountain).

    v2 (Missão B — identidade visual): piso/paredes de basalto (`lair_basalt_*`/
    `basalt_wall_*`, tools/spr/gen_terrain.py), tochas VERMELHAS (`red_torch`)
    no lugar da tocha branca vanilla, poças de sangue/lava fria como decor NAO
    caminhavel (nunca em cima de um tile usado por NPC/porta/spawn-center) e
    uma ANTECAMARA de 1-2 tiles antes de CADA uma das 4 salas de boss (parede
    extra + porta propria, separada da sala do boss em si) — pedido explicito
    da missao ("antecamaras antes de cada um dos 4 bosses finais")."""
    notes = []
    x0, y0, x1, y1 = LAIR_X0, LAIR_Y0, LAIR_X1, LAIR_Y1
    floor = [sid[k] for k in ("lair_basalt_0", "lair_basalt_1") if k in sid] or BV.STONE_FLOOR
    wall_h = sid.get("basalt_wall_h", BV.STONE_WALL_H)
    wall_v = sid.get("basalt_wall_v", BV.STONE_WALL_V)
    wall_c = sid.get("basalt_wall_c", BV.STONE_WALL_C)
    torch_id = sid.get("red_torch", BV.TORCH)
    blood_id = sid.get("blood_pool")
    lava_id = sid.get("lava_pool_cold")
    b.fill(x0, y0, x1, y1, floor)

    def scatter_gore(cells):
        """Poça de sangue/lava fria em células dadas — só se vazias (nunca
        em cima de NPC/porta/pad/centro de spawn, o chamador já filtra isso
        passando só cantos/cantos de sala)."""
        for i, (gx, gy) in enumerate(cells):
            c = b.cells.get((gx, gy))
            if c is None or c.items:
                continue
            item = lava_id if (i % 3 == 2 and lava_id) else blood_id
            if item:
                b.put(gx, gy, item)

    hx0, hy0, hx1, hy1 = LAIR_HALL
    b.walls(hx0, hy0, hx1, hy1, wall_h, wall_v, wall_c,
            doors=[(hx1, y) for y in range(LAIR_CORRIDOR_Y[0], LAIR_CORRIDOR_Y[1] + 1)])
    for x in range(hx0, hx1 + 1):
        for y in (hy0, hy1):
            c = b.cells.get((x, y))
            if c is not None and not c.items:
                b.put(x, y, torch_id)

    landing = (hx0 + 4, hy0 + 3)
    exitpad = (hx0 + 2, hy0 + 3)
    b.clear_items(*landing)
    b.clear_items(*exitpad)
    # tele_dest do pad de saida e' ajustado por link_mountain_to_lair()
    b.put(exitpad[0], exitpad[1], BV.TELEPORT_ITEM, tele_dest=(0, 0, FLOOR))
    sign(b, hx0 + 1, hy0 + 1, "Covil da Nuvem Vermelha - Anbu/Kage, nivel 80-100")

    # Mestre de Tarefas Kuro (task_master_lair, data/npcs/akatsuki_lair.json,
    # x/y ja documentado la: 1406,1014) — no hall, base segura antes do
    # corredor patrulhado.
    kuro_pos = (hx0 + 6, hy0 + 9)
    b.clear_items(*kuro_pos)
    npcs = [
        ("Capitã Anbu Suzu", (hx0 + 6, hy0 + 5)),
        ("Fornecedor Enji", (hx0 + 6, hy0 + 7)),
        ("Mestre de Tarefas Kuro", kuro_pos),
    ]
    scatter_gore([(hx0 + 2, hy0 + 12), (hx1 - 2, hy0 + 13), (hx0 + 3, hy1 - 2)])

    # corredor principal (piso primeiro; a parede do corredor so' e' fechada
    # DEPOIS que as salas abrem suas proprias portas — ver door_gaps abaixo —
    # senao a parede do corredor "vence" e a porta da sala nunca abre de
    # verdade, so' fica vazia por fora sem ligar com o corredor).
    for y in range(LAIR_CORRIDOR_Y[0], LAIR_CORRIDOR_Y[1] + 1):
        for x in range(hx1 + 1, LAIR_FINAL[0]):
            b.ground(x, y, floor)
            b.clear_items(x, y)

    door_gaps = set()

    def build_room(rect, door_x, boss_name, level, from_north):
        """Sala do boss + ANTECAMARA de 1 tile logo depois da porta externa,
        separada por uma 2a parede (com porta propria no MESMO door_x, pra
        manter a linha de visao reta corredor->antecamara->camara) — o
        "achado" da missao (rooms rasos, so 5 tiles de profundidade) exigiu
        antecamara FINA (1 tile) em vez dos 2 tiles originalmente cogitados,
        senao a camara do boss ficava profunda demais pro raio de spawn."""
        rx0, ry0, rx1, ry1 = rect
        b.fill(rx0, ry0, rx1, ry1, floor)
        door_y = ry1 if from_north else ry0
        b.walls(rx0, ry0, rx1, ry1, wall_h, wall_v, wall_c, doors=[(door_x, door_y)])
        door_gaps.add((door_x, door_y))
        # -- antecamara: parede interna paralela a parede externa, 2 tiles
        # pra dentro (1 tile de antecamara entre as duas) ------------------
        inner_y = ry1 - 2 if from_north else ry0 + 2
        ante_y = ry1 - 1 if from_north else ry0 + 1
        for x in range(rx0, rx1 + 1):
            if x == door_x:
                continue
            c = b.cells.get((x, inner_y))
            if c is not None:
                b.clear_items(x, inner_y)
                b.put(x, inner_y, wall_c if x in (rx0, rx1) else wall_h)
        for (tx, ty) in ((rx0 + 1, ante_y), (rx1 - 1, ante_y)):
            c = b.cells.get((tx, ty))
            if c is not None and not c.items:
                b.put(tx, ty, torch_id)
        sign(b, rx0 + 1 if door_x - rx0 > rx1 - door_x else rx1 - 2, ante_y,
             "Antecamara - alem, %s" % boss_name)
        # câmara do boss, do outro lado da antecamara
        chamber_y0 = ry0 + 1 if from_north else inner_y + 1
        chamber_y1 = inner_y - 1 if from_north else ry1 - 1
        for (tx, ty) in ((rx0 + 1, chamber_y0), (rx1 - 1, chamber_y0)):
            c = b.cells.get((tx, ty))
            if c is not None and not c.items:
                b.put(tx, ty, torch_id)
        scatter_gore([(rx0 + 1, chamber_y1), (rx1 - 1, chamber_y0)])
        center = (rx0 + rx1) // 2, (chamber_y0 + chamber_y1) // 2
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
                b.put(x, y, wall_h)

    # sala final, grande, no extremo leste — com antecamara propria (foyer
    # 4x5 logo apos a porta do corredor, parede+porta separando do salao
    # grande do boss) antes do Ancestral da Nuvem Vermelha.
    fx0, fy0, fx1, fy1 = LAIR_FINAL
    b.fill(fx0, fy0, fx1, fy1, floor)
    b.walls(fx0, fy0, fx1, fy1, wall_h, wall_v, wall_c,
            doors=[(fx0, y) for y in range(LAIR_CORRIDOR_Y[0], LAIR_CORRIDOR_Y[1] + 1)])
    ante_x1 = fx0 + 4
    ante_gap_y = (LAIR_CORRIDOR_Y[0] + LAIR_CORRIDOR_Y[1]) // 2
    b.walls(fx0 + 1, LAIR_CORRIDOR_Y[0] - 1, ante_x1, LAIR_CORRIDOR_Y[1] + 1,
            wall_h, wall_v, wall_c,
            doors=[(fx0 + 1, y) for y in range(LAIR_CORRIDOR_Y[0] - 1, LAIR_CORRIDOR_Y[1] + 2)] +
                  [(ante_x1, ante_gap_y)])
    for (tx, ty) in ((fx0 + 2, LAIR_CORRIDOR_Y[0]), (fx0 + 2, LAIR_CORRIDOR_Y[1])):
        c = b.cells.get((tx, ty))
        if c is not None and not c.items:
            b.put(tx, ty, torch_id)
    sign(b, fx0 + 2, ante_gap_y, "Antecamara - alem, O Ancestral da Nuvem Vermelha")
    for (tx, ty) in ((fx0 + 2, fy0 + 2), (fx1 - 2, fy0 + 2),
                     (fx0 + 2, fy1 - 2), (fx1 - 2, fy1 - 2)):
        c = b.cells.get((tx, ty))
        if c is not None and not c.items:
            b.put(tx, ty, torch_id)
    scatter_gore([(fx0 + 6, fy0 + 3), (fx1 - 3, fy0 + 3), (fx0 + 6, fy1 - 3), (fx1 - 3, fy1 - 3)])
    b.put(fx0 + 2, fy0 + 1, BV.SIGN, text="O Ancestral da Nuvem Vermelha (nivel 100) - sala final")
    c4 = ((ante_x1 + fx1) // 2, (fy0 + fy1) // 2)

    notes.append("covil da nuvem vermelha v2: piso/paredes de basalto (lair_basalt_0/1, "
                 "basalt_wall_h/v/c — era stone_floor/stone_wall generico), tochas "
                 "vermelhas (red_torch) no lugar da tocha branca, pocas de sangue/lava "
                 "fria (blood_pool/lava_pool_cold) como decor nao caminhavel em cantos "
                 "vazios, ANTECAMARA de 1 tile (com parede+porta propria) antes de cada "
                 "uma das 4 salas de boss (pedido explicito da missao)")
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
    # raio 1 (era 2): a camara do boss ficou mais rasa depois da antecamara
    # nova (3 linhas de profundidade em vez de 5) — radius=2 ainda funcionaria
    # (paredes bloqueiam o monstro de qualquer jeito), mas 1 e' mais fiel ao
    # tamanho real da sala.
    spec.group(*c1, radius=1).add_monster("O Vigia Ilusório", 0, 0, spawntime=7200)
    spec.group(*c2, radius=1).add_monster("O Mascarado das Sombras", 0, 0, spawntime=7200)
    spec.group(*c3, radius=1).add_monster("O Portador dos Seis Caminhos", 0, 0, spawntime=7200)
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
