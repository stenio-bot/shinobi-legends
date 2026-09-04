#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Leitor/gravador de mapas OTBM compatíveis com TFS 1.4.2 e Remere's Map Editor.

Formato (ver server/tfs/src/iomap.cpp e fileloader.cpp):

    <identificador 4 bytes> 0xFE <tipo> <props...> [ filhos ] 0xFF

Dentro de <props> os bytes 0xFD/0xFE/0xFF são escapados com 0xFD.

Árvore:
    ROOT (tipo 0)                 props: OTBM_root_header
      OTBM_MAP_DATA (2)           props: DESCRIPTION / EXT_SPAWN_FILE / EXT_HOUSE_FILE
        OTBM_TILE_AREA (4)        props: x,y (uint16) z (uint8)
          OTBM_TILE (5) / OTBM_HOUSETILE (14)
                                  props: dx,dy (uint8) [houseid uint32] atributos
            OTBM_ITEM (6)         props: id (uint16) atributos
        OTBM_TOWNS (12) -> OTBM_TOWN (13)
        OTBM_WAYPOINTS (15) -> OTBM_WAYPOINT (16)

Uso típico:
    m = OtbmMap.read("forgotten.otbm")
    m.write("copia.otbm")

    m = OtbmMap(width=1024, height=1024)
    t = m.tile(1000, 1000, 7)
    t.set_ground(4526)
    t.add_item(Item(2700))
"""

from __future__ import annotations

import struct
from collections import OrderedDict

# ---------------------------------------------------------------- constantes

NODE_ESCAPE = 0xFD
NODE_START = 0xFE
NODE_END = 0xFF

OTBM_ROOTV1 = 1
OTBM_MAP_DATA = 2
OTBM_ITEM_DEF = 3
OTBM_TILE_AREA = 4
OTBM_TILE = 5
OTBM_ITEM = 6
OTBM_TILE_SQUARE = 7
OTBM_TILE_REF = 8
OTBM_SPAWNS = 9
OTBM_SPAWN_AREA = 10
OTBM_MONSTER = 11
OTBM_TOWNS = 12
OTBM_TOWN = 13
OTBM_HOUSETILE = 14
OTBM_WAYPOINTS = 15
OTBM_WAYPOINT = 16

OTBM_ATTR_DESCRIPTION = 1
OTBM_ATTR_EXT_FILE = 2
OTBM_ATTR_TILE_FLAGS = 3
OTBM_ATTR_ACTION_ID = 4
OTBM_ATTR_UNIQUE_ID = 5
OTBM_ATTR_TEXT = 6
OTBM_ATTR_DESC = 7
OTBM_ATTR_TELE_DEST = 8
OTBM_ATTR_ITEM = 9
OTBM_ATTR_DEPOT_ID = 10
OTBM_ATTR_EXT_SPAWN_FILE = 11
OTBM_ATTR_RUNE_CHARGES = 12
OTBM_ATTR_EXT_HOUSE_FILE = 13
OTBM_ATTR_HOUSEDOORID = 14
OTBM_ATTR_COUNT = 15
OTBM_ATTR_DURATION = 16
OTBM_ATTR_DECAYING_STATE = 17
OTBM_ATTR_WRITTENDATE = 18
OTBM_ATTR_WRITTENBY = 19
OTBM_ATTR_SLEEPERGUID = 20
OTBM_ATTR_SLEEPSTART = 21
OTBM_ATTR_CHARGES = 22
OTBM_ATTR_CONTAINER_ITEMS = 23
OTBM_ATTR_NAME = 24
OTBM_ATTR_ARTICLE = 25
OTBM_ATTR_PLURALNAME = 26
OTBM_ATTR_WEIGHT = 27
OTBM_ATTR_ATTACK = 28
OTBM_ATTR_DEFENSE = 29
OTBM_ATTR_EXTRADEFENSE = 30
OTBM_ATTR_ARMOR = 31
OTBM_ATTR_HITCHANCE = 32
OTBM_ATTR_SHOOTRANGE = 33
OTBM_ATTR_CUSTOM_ATTRIBUTES = 34
OTBM_ATTR_DECAYTO = 35
OTBM_ATTR_WRAPID = 36
OTBM_ATTR_STOREITEM = 37
OTBM_ATTR_ATTACK_SPEED = 38
OTBM_ATTR_OPENCONTAINER = 39
OTBM_ATTR_PODIUMOUTFIT = 40
OTBM_ATTR_TIER = 41

TILEFLAG_NONE = 0
TILEFLAG_PROTECTIONZONE = 1 << 0
TILEFLAG_NOPVPZONE = 1 << 2
TILEFLAG_NOLOGOUT = 1 << 3
TILEFLAG_PVPZONE = 1 << 4

#: tamanho fixo (em bytes) de cada atributo de item; ``None`` = string prefixada
#: por uint16, ``"custom"`` = bloco OTBM_ATTR_CUSTOM_ATTRIBUTES.
ITEM_ATTR_SIZES = {
    OTBM_ATTR_COUNT: 1,
    OTBM_ATTR_RUNE_CHARGES: 1,
    OTBM_ATTR_ACTION_ID: 2,
    OTBM_ATTR_UNIQUE_ID: 2,
    OTBM_ATTR_TEXT: None,
    OTBM_ATTR_DESC: None,
    OTBM_ATTR_WRITTENDATE: 4,
    OTBM_ATTR_WRITTENBY: None,
    OTBM_ATTR_CHARGES: 2,
    OTBM_ATTR_DURATION: 4,
    OTBM_ATTR_DECAYING_STATE: 1,
    OTBM_ATTR_NAME: None,
    OTBM_ATTR_ARTICLE: None,
    OTBM_ATTR_PLURALNAME: None,
    OTBM_ATTR_WEIGHT: 4,
    OTBM_ATTR_ATTACK: 4,
    OTBM_ATTR_ATTACK_SPEED: 4,
    OTBM_ATTR_DEFENSE: 4,
    OTBM_ATTR_EXTRADEFENSE: 4,
    OTBM_ATTR_ARMOR: 4,
    OTBM_ATTR_HITCHANCE: 1,
    OTBM_ATTR_SHOOTRANGE: 1,
    OTBM_ATTR_DECAYTO: 4,
    OTBM_ATTR_WRAPID: 2,
    OTBM_ATTR_STOREITEM: 1,
    OTBM_ATTR_OPENCONTAINER: 1,
    OTBM_ATTR_TIER: 1,
    OTBM_ATTR_PODIUMOUTFIT: 15,
    OTBM_ATTR_DEPOT_ID: 2,
    OTBM_ATTR_HOUSEDOORID: 1,
    OTBM_ATTR_SLEEPERGUID: 4,
    OTBM_ATTR_SLEEPSTART: 4,
    OTBM_ATTR_TELE_DEST: 5,
    OTBM_ATTR_CONTAINER_ITEMS: 4,
    OTBM_ATTR_CUSTOM_ATTRIBUTES: "custom",
}


class OtbmError(Exception):
    """Erro de formato/uso do OTBM."""


# ---------------------------------------------------------------- nó cru OTB

class Node:
    """Nó cru da árvore OTB: tipo, bytes de propriedade e filhos."""

    __slots__ = ("type", "props", "children")

    def __init__(self, type_, props=b"", children=None):
        self.type = type_
        self.props = props
        self.children = children if children is not None else []

    def __repr__(self):  # pragma: no cover - debug
        return "Node(type=%d, props=%d bytes, children=%d)" % (
            self.type, len(self.props), len(self.children))


def _unescape(raw):
    out = bytearray()
    i = 0
    n = len(raw)
    while i < n:
        b = raw[i]
        if b == NODE_ESCAPE:
            i += 1
            if i >= n:
                raise OtbmError("escape no fim do buffer")
            out.append(raw[i])
        else:
            out.append(b)
        i += 1
    return bytes(out)


def _escape(data):
    out = bytearray()
    for b in data:
        if b in (NODE_ESCAPE, NODE_START, NODE_END):
            out.append(NODE_ESCAPE)
        out.append(b)
    return bytes(out)


def read_otb(path):
    """Lê um arquivo OTB/OTBM cru. Retorna ``(identificador, nó raiz)``."""
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < 8:
        raise OtbmError("arquivo pequeno demais")
    identifier = data[0:4]
    if data[4] != NODE_START:
        raise OtbmError("byte inicial de nó ausente")

    root = Node(data[5])
    stack = [root]
    buf = bytearray()
    i = 6
    n = len(data)
    while i < n:
        b = data[i]
        if b == NODE_START:
            if stack:
                # o buffer acumulado pertence ao nó no topo (só antes do 1o filho)
                if not stack[-1].children:
                    stack[-1].props = _unescape(bytes(buf))
                buf = bytearray()
            i += 1
            if i >= n:
                raise OtbmError("nó truncado")
            child = Node(data[i])
            stack[-1].children.append(child)
            stack.append(child)
        elif b == NODE_END:
            if not stack:
                raise OtbmError("NODE_END sem nó aberto")
            if not stack[-1].children:
                stack[-1].props = _unescape(bytes(buf))
            buf = bytearray()
            stack.pop()
        elif b == NODE_ESCAPE:
            buf.append(b)
            i += 1
            if i >= n:
                raise OtbmError("escape truncado")
            buf.append(data[i])
        else:
            buf.append(b)
        i += 1

    if stack:
        raise OtbmError("nós não fechados: %d" % len(stack))
    return identifier, root


def _write_node(out, node):
    out.append(NODE_START)
    out.append(node.type)
    out += _escape(node.props)
    for child in node.children:
        _write_node(out, child)
    out.append(NODE_END)


def write_otb(path, identifier, root):
    """Grava a árvore OTB crua em ``path``."""
    out = bytearray()
    out += identifier
    _write_node(out, root)
    with open(path, "wb") as fh:
        fh.write(bytes(out))


# ---------------------------------------------------------- leitura de props

class _Props:
    """Leitor sequencial sobre os bytes de propriedade de um nó."""

    def __init__(self, data):
        self.data = data
        self.pos = 0

    def remaining(self):
        return len(self.data) - self.pos

    def read(self, n):
        if self.remaining() < n:
            raise OtbmError("props truncadas (pediu %d, tem %d)" % (n, self.remaining()))
        chunk = self.data[self.pos:self.pos + n]
        self.pos += n
        return chunk

    def u8(self):
        return self.read(1)[0]

    def u16(self):
        return struct.unpack("<H", self.read(2))[0]

    def u32(self):
        return struct.unpack("<I", self.read(4))[0]

    def u64(self):
        return struct.unpack("<Q", self.read(8))[0]

    def string(self):
        length = self.u16()
        return self.read(length).decode("utf-8", "replace")


def _pack_string(text):
    raw = text.encode("utf-8")
    if len(raw) > 0xFFFF:
        raise OtbmError("string longa demais")
    return struct.pack("<H", len(raw)) + raw


def _read_custom_attributes(props):
    """Consome um bloco OTBM_ATTR_CUSTOM_ATTRIBUTES e devolve os bytes crus."""
    start = props.pos
    count = props.u64()
    for _ in range(count):
        props.string()          # chave
        vtype = props.u8()      # tipo do valor
        if vtype == 1:          # string
            props.string()
        elif vtype == 2:        # int64
            props.read(8)
        elif vtype == 3:        # double
            props.read(8)
        elif vtype == 4:        # bool
            props.read(1)
        else:
            raise OtbmError("tipo de custom attribute desconhecido: %d" % vtype)
    return props.data[start:props.pos]


# ------------------------------------------------------------------- modelos

class Item:
    """Item de um tile. Atributos crus preservados para round-trip fiel."""

    __slots__ = ("id", "attrs", "children")

    def __init__(self, item_id, count=None, action_id=None, unique_id=None,
                 text=None, tele_dest=None, depot_id=None, door_id=None,
                 description=None):
        self.id = int(item_id)
        #: lista ordenada de ``(attr_id, bytes)``
        self.attrs = []
        #: itens dentro de containers
        self.children = []
        if count is not None:
            self.count = count
        if action_id is not None:
            self.action_id = action_id
        if unique_id is not None:
            self.unique_id = unique_id
        if text is not None:
            self.text = text
        if description is not None:
            self.set_attr(OTBM_ATTR_DESC, _pack_string(description))
        if tele_dest is not None:
            self.tele_dest = tele_dest
        if depot_id is not None:
            self.set_attr(OTBM_ATTR_DEPOT_ID, struct.pack("<H", depot_id))
        if door_id is not None:
            self.set_attr(OTBM_ATTR_HOUSEDOORID, struct.pack("<B", door_id))

    # -- atributos crus -----------------------------------------------------
    def get_attr(self, attr_id):
        for aid, raw in self.attrs:
            if aid == attr_id:
                return raw
        return None

    def set_attr(self, attr_id, raw):
        for idx, (aid, _) in enumerate(self.attrs):
            if aid == attr_id:
                self.attrs[idx] = (attr_id, raw)
                return
        self.attrs.append((attr_id, raw))

    @property
    def simple(self):
        """True se o item não tem atributos nem filhos (cabe em OTBM_ATTR_ITEM)."""
        return not self.attrs and not self.children

    # -- acessores amigáveis ------------------------------------------------
    @property
    def count(self):
        raw = self.get_attr(OTBM_ATTR_COUNT)
        return raw[0] if raw else None

    @count.setter
    def count(self, value):
        self.set_attr(OTBM_ATTR_COUNT, struct.pack("<B", int(value) & 0xFF))

    @property
    def action_id(self):
        raw = self.get_attr(OTBM_ATTR_ACTION_ID)
        return struct.unpack("<H", raw)[0] if raw else None

    @action_id.setter
    def action_id(self, value):
        self.set_attr(OTBM_ATTR_ACTION_ID, struct.pack("<H", int(value)))

    @property
    def unique_id(self):
        raw = self.get_attr(OTBM_ATTR_UNIQUE_ID)
        return struct.unpack("<H", raw)[0] if raw else None

    @unique_id.setter
    def unique_id(self, value):
        self.set_attr(OTBM_ATTR_UNIQUE_ID, struct.pack("<H", int(value)))

    @property
    def text(self):
        raw = self.get_attr(OTBM_ATTR_TEXT)
        if raw is None:
            return None
        return raw[2:].decode("utf-8", "replace")

    @text.setter
    def text(self, value):
        self.set_attr(OTBM_ATTR_TEXT, _pack_string(value))

    @property
    def tele_dest(self):
        raw = self.get_attr(OTBM_ATTR_TELE_DEST)
        if raw is None:
            return None
        return struct.unpack("<HHB", raw)

    @tele_dest.setter
    def tele_dest(self, value):
        x, y, z = value
        self.set_attr(OTBM_ATTR_TELE_DEST, struct.pack("<HHB", x, y, z))

    @property
    def depot_id(self):
        raw = self.get_attr(OTBM_ATTR_DEPOT_ID)
        return struct.unpack("<H", raw)[0] if raw else None

    def __repr__(self):  # pragma: no cover - debug
        return "Item(%d)" % self.id


class Tile:
    """Tile do mapa. ``house_id`` != None marca OTBM_HOUSETILE."""

    __slots__ = ("x", "y", "z", "flags", "house_id", "attr_items", "items", "extra_attrs")

    def __init__(self, x, y, z, house_id=None):
        self.x = x
        self.y = y
        self.z = z
        self.flags = TILEFLAG_NONE
        self.house_id = house_id
        #: itens gravados como OTBM_ATTR_ITEM nas props do tile (normalmente o chão)
        self.attr_items = []
        #: itens gravados como nós OTBM_ITEM filhos, na ordem de empilhamento
        self.items = []
        #: atributos de tile desconhecidos, preservados como ``(attr_id, bytes)``
        self.extra_attrs = []

    # -- API de construção --------------------------------------------------
    def set_ground(self, item_or_id):
        """Define o chão. Item simples vira OTBM_ATTR_ITEM (como o Remere's)."""
        item = item_or_id if isinstance(item_or_id, Item) else Item(item_or_id)
        if item.simple:
            self.attr_items = [item]
        else:
            self.attr_items = []
            self.items.insert(0, item)
        return item

    def add_item(self, item_or_id):
        item = item_or_id if isinstance(item_or_id, Item) else Item(item_or_id)
        self.items.append(item)
        return item

    @property
    def ground(self):
        if self.attr_items:
            return self.attr_items[0]
        return self.items[0] if self.items else None

    @property
    def all_items(self):
        return list(self.attr_items) + list(self.items)

    @property
    def pos(self):
        return (self.x, self.y, self.z)

    def __repr__(self):  # pragma: no cover - debug
        return "Tile(%d,%d,%d)" % (self.x, self.y, self.z)


class Town:
    __slots__ = ("id", "name", "x", "y", "z")

    def __init__(self, town_id, name, x, y, z):
        self.id = int(town_id)
        self.name = name
        self.x, self.y, self.z = int(x), int(y), int(z)


class Waypoint:
    __slots__ = ("name", "x", "y", "z")

    def __init__(self, name, x, y, z):
        self.name = name
        self.x, self.y, self.z = int(x), int(y), int(z)


# ---------------------------------------------------------------- mapa OTBM

class OtbmMap:
    """Mapa OTBM completo, com leitura e escrita."""

    def __init__(self, width=1024, height=1024, version=2,
                 major_items=3, minor_items=57):
        self.identifier = b"\x00\x00\x00\x00"
        self.root_type = 0
        self.version = version
        self.width = width
        self.height = height
        self.major_items = major_items
        self.minor_items = minor_items
        self.descriptions = []
        self.spawnfile = ""
        self.housefile = ""
        #: ``{(x, y, z): Tile}``
        self.tiles = OrderedDict()
        self.towns = []
        self.waypoints = []

    # -- construção ---------------------------------------------------------
    def tile(self, x, y, z, house_id=None):
        """Devolve (criando se preciso) o tile em ``(x, y, z)``."""
        key = (x, y, z)
        t = self.tiles.get(key)
        if t is None:
            t = Tile(x, y, z, house_id)
            self.tiles[key] = t
        elif house_id is not None:
            t.house_id = house_id
        return t

    def get(self, x, y, z):
        return self.tiles.get((x, y, z))

    def add_town(self, town_id, name, x, y, z):
        self.towns.append(Town(town_id, name, x, y, z))

    def add_waypoint(self, name, x, y, z):
        self.waypoints.append(Waypoint(name, x, y, z))

    # -- estatísticas -------------------------------------------------------
    def tile_count_by_floor(self):
        counts = {}
        for (_, _, z) in self.tiles:
            counts[z] = counts.get(z, 0) + 1
        return counts

    def item_count_by_id(self):
        counts = {}

        def walk(items):
            for it in items:
                counts[it.id] = counts.get(it.id, 0) + 1
                if it.children:
                    walk(it.children)

        for t in self.tiles.values():
            walk(t.all_items)
        return counts

    # -- leitura ------------------------------------------------------------
    @classmethod
    def read(cls, path):
        identifier, root = read_otb(path)
        m = cls()
        m.identifier = identifier
        m.root_type = root.type

        props = _Props(root.props)
        m.version = props.u32()
        m.width = props.u16()
        m.height = props.u16()
        m.major_items = props.u32()
        m.minor_items = props.u32()

        if len(root.children) != 1 or root.children[0].type != OTBM_MAP_DATA:
            raise OtbmError("nó OTBM_MAP_DATA ausente")
        map_node = root.children[0]

        p = _Props(map_node.props)
        while p.remaining() > 0:
            attr = p.u8()
            if attr == OTBM_ATTR_DESCRIPTION:
                m.descriptions.append(p.string())
            elif attr == OTBM_ATTR_EXT_SPAWN_FILE:
                m.spawnfile = p.string()
            elif attr == OTBM_ATTR_EXT_HOUSE_FILE:
                m.housefile = p.string()
            else:
                raise OtbmError("atributo de cabeçalho desconhecido: %d" % attr)

        for node in map_node.children:
            if node.type == OTBM_TILE_AREA:
                m._read_tile_area(node)
            elif node.type == OTBM_TOWNS:
                m._read_towns(node)
            elif node.type == OTBM_WAYPOINTS:
                m._read_waypoints(node)
            else:
                raise OtbmError("nó de mapa desconhecido: %d" % node.type)
        return m

    def _read_tile_area(self, node):
        p = _Props(node.props)
        base_x = p.u16()
        base_y = p.u16()
        z = p.u8()

        for tile_node in node.children:
            if tile_node.type not in (OTBM_TILE, OTBM_HOUSETILE):
                raise OtbmError("nó de tile desconhecido: %d" % tile_node.type)
            tp = _Props(tile_node.props)
            x = base_x + tp.u8()
            y = base_y + tp.u8()
            house_id = tp.u32() if tile_node.type == OTBM_HOUSETILE else None

            tile = Tile(x, y, z, house_id)
            while tp.remaining() > 0:
                attr = tp.u8()
                if attr == OTBM_ATTR_TILE_FLAGS:
                    tile.flags = tp.u32()
                elif attr == OTBM_ATTR_ITEM:
                    tile.attr_items.append(Item(tp.u16()))
                else:
                    raise OtbmError("atributo de tile desconhecido: %d em (%d,%d,%d)"
                                    % (attr, x, y, z))

            for item_node in tile_node.children:
                if item_node.type != OTBM_ITEM:
                    raise OtbmError("nó filho de tile inesperado: %d" % item_node.type)
                tile.items.append(_read_item_node(item_node))

            self.tiles[(x, y, z)] = tile

    def _read_towns(self, node):
        for town_node in node.children:
            if town_node.type != OTBM_TOWN:
                raise OtbmError("nó de town desconhecido: %d" % town_node.type)
            p = _Props(town_node.props)
            town_id = p.u32()
            name = p.string()
            x = p.u16()
            y = p.u16()
            z = p.u8()
            self.towns.append(Town(town_id, name, x, y, z))

    def _read_waypoints(self, node):
        for wp_node in node.children:
            if wp_node.type != OTBM_WAYPOINT:
                raise OtbmError("nó de waypoint desconhecido: %d" % wp_node.type)
            p = _Props(wp_node.props)
            name = p.string()
            x = p.u16()
            y = p.u16()
            z = p.u8()
            self.waypoints.append(Waypoint(name, x, y, z))

    # -- escrita ------------------------------------------------------------
    def write(self, path):
        root = Node(self.root_type)
        root.props = struct.pack("<IHHII", self.version, self.width, self.height,
                                 self.major_items, self.minor_items)

        map_node = Node(OTBM_MAP_DATA)
        head = bytearray()
        for desc in self.descriptions:
            head.append(OTBM_ATTR_DESCRIPTION)
            head += _pack_string(desc)
        if self.spawnfile:
            head.append(OTBM_ATTR_EXT_SPAWN_FILE)
            head += _pack_string(self.spawnfile)
        if self.housefile:
            head.append(OTBM_ATTR_EXT_HOUSE_FILE)
            head += _pack_string(self.housefile)
        map_node.props = bytes(head)
        root.children.append(map_node)

        # tiles agrupados em áreas de 256x256 por andar
        areas = OrderedDict()
        for key in sorted(self.tiles.keys(), key=lambda k: (k[2], k[1], k[0])):
            tile = self.tiles[key]
            akey = (tile.x & 0xFF00, tile.y & 0xFF00, tile.z)
            areas.setdefault(akey, []).append(tile)

        for (bx, by, bz), tiles in areas.items():
            area = Node(OTBM_TILE_AREA, struct.pack("<HHB", bx, by, bz))
            for tile in tiles:
                area.children.append(_write_tile_node(tile, bx, by))
            map_node.children.append(area)

        if self.towns:
            towns_node = Node(OTBM_TOWNS)
            for town in self.towns:
                props = struct.pack("<I", town.id) + _pack_string(town.name) \
                    + struct.pack("<HHB", town.x, town.y, town.z)
                towns_node.children.append(Node(OTBM_TOWN, props))
            map_node.children.append(towns_node)

        if self.waypoints and self.version > 1:
            wp_node = Node(OTBM_WAYPOINTS)
            for wp in self.waypoints:
                props = _pack_string(wp.name) + struct.pack("<HHB", wp.x, wp.y, wp.z)
                wp_node.children.append(Node(OTBM_WAYPOINT, props))
            map_node.children.append(wp_node)

        write_otb(path, self.identifier, root)


def _read_item_node(node):
    p = _Props(node.props)
    item = Item(p.u16())
    while p.remaining() > 0:
        attr = p.u8()
        size = ITEM_ATTR_SIZES.get(attr)
        if size is None and attr not in ITEM_ATTR_SIZES:
            raise OtbmError("atributo de item desconhecido: %d (item %d)" % (attr, item.id))
        if size is None:                      # string
            start = p.pos
            p.string()
            raw = p.data[start:p.pos]
        elif size == "custom":
            raw = _read_custom_attributes(p)
        else:
            raw = p.read(size)
        item.attrs.append((attr, raw))
    for child in node.children:
        if child.type != OTBM_ITEM:
            raise OtbmError("nó filho de item inesperado: %d" % child.type)
        item.children.append(_read_item_node(child))
    return item


def _write_item_node(item):
    props = bytearray(struct.pack("<H", item.id))
    for attr_id, raw in item.attrs:
        props.append(attr_id)
        props += raw
    node = Node(OTBM_ITEM, bytes(props))
    for child in item.children:
        node.children.append(_write_item_node(child))
    return node


def _write_tile_node(tile, base_x, base_y):
    dx = tile.x - base_x
    dy = tile.y - base_y
    if not (0 <= dx <= 255 and 0 <= dy <= 255):
        raise OtbmError("tile fora da área: %r" % (tile.pos,))

    node_type = OTBM_HOUSETILE if tile.house_id is not None else OTBM_TILE
    props = bytearray(struct.pack("<BB", dx, dy))
    if tile.house_id is not None:
        props += struct.pack("<I", tile.house_id)
    if tile.flags:
        props.append(OTBM_ATTR_TILE_FLAGS)
        props += struct.pack("<I", tile.flags)
    for attr_id, raw in tile.extra_attrs:
        props.append(attr_id)
        props += raw
    for item in tile.attr_items:
        props.append(OTBM_ATTR_ITEM)
        props += struct.pack("<H", item.id)

    node = Node(node_type, bytes(props))
    for item in tile.items:
        node.children.append(_write_item_node(item))
    return node


__all__ = [
    "OtbmMap", "Tile", "Item", "Town", "Waypoint", "Node", "OtbmError",
    "read_otb", "write_otb",
    "TILEFLAG_PROTECTIONZONE", "TILEFLAG_NOPVPZONE", "TILEFLAG_NOLOGOUT",
    "TILEFLAG_PVPZONE",
]


if __name__ == "__main__":  # diagnóstico rápido: python3 otbm.py mapa.otbm
    import sys
    src = sys.argv[1]
    mp = OtbmMap.read(src)
    print("mapa %dx%d otbm v%d itens %d.%d" % (mp.width, mp.height, mp.version,
                                               mp.major_items, mp.minor_items))
    print("descricoes:", mp.descriptions)
    print("spawnfile:", mp.spawnfile, "housefile:", mp.housefile)
    print("tiles:", len(mp.tiles), "por andar:", sorted(mp.tile_count_by_floor().items()))
    print("towns:", len(mp.towns), "waypoints:", len(mp.waypoints))
    print("itens:", sum(mp.item_count_by_id().values()))
