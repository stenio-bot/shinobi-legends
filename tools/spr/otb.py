"""Leitura E escrita do items.otb do TFS (formato OTB no-a-no).

Referencia: server/tfs/src/fileloader.cpp (OTB::Loader::parseTree),
server/tfs/src/items.cpp (Items::loadFromOtb) e
server/tfs/src/itemloader.h (itemgroup_t, itemattrib_t, itemflags_t).

Layout do arquivo
-----------------
    <4 bytes identificador>            "OTBI" ou 00 00 00 00 (wildcard)
    FE <tipo=0> <props da raiz>        raiz: flags u32 + ROOT_ATTR_VERSION
      FE <grupo> <props do item> FF    um no por item
      ...
    FF                                 fecha a raiz

Props da raiz:
    u32 flags (0) | u8 0x01 | u16 datalen (140) | VERSIONINFO
    VERSIONINFO = u32 major (3) + u32 minor (57 = 10.98) + u32 build + 128 bytes

Props de um item:
    u32 flags (itemflags_t) | (u8 attrib + u16 datalen + payload)*

Dentro dos props, os bytes FD/FE/FF sao escapados com o prefixo FD (0xFD).

O parse guarda os props CRUS (ainda escapados) de cada no em `raw_props`, e
`write_items_otb` os regrava sem tocar: reescrever um items.otb lido resulta em
um arquivo byte a byte identico (ver tools/spr/test_otb_roundtrip.py).
"""
import struct

NODE_START = 0xFE
NODE_END = 0xFF
NODE_ESCAPE = 0xFD

ROOT_ATTR_VERSION = 0x01

ITEM_ATTR_SERVERID = 0x10
ITEM_ATTR_CLIENTID = 0x11
ITEM_ATTR_NAME = 0x12
ITEM_ATTR_DESCR = 0x13
ITEM_ATTR_SPEED = 0x14
ITEM_ATTR_SPRITEHASH = 0x20
ITEM_ATTR_MINIMAPCOLOR = 0x21
ITEM_ATTR_LIGHT2 = 0x2A
ITEM_ATTR_TOPORDER = 0x2B
ITEM_ATTR_WAREID = 0x2D
ITEM_ATTR_CLASSIFICATION = 0x2E

# itemgroup_t (server/tfs/src/itemloader.h). O TFS so ACEITA estes grupos em
# loadFromOtb: none, ground, container, splash, fluid, charges, deprecated,
# podium, door, magicfield, teleport. Qualquer outro faz o load retornar false.
ITEM_GROUP_NAMES = [
    "none", "ground", "container", "weapon", "ammunition", "armor", "charges",
    "teleport", "magicfield", "writeable", "key", "splash", "fluid", "door",
    "deprecated", "podium",
]
ITEM_GROUP_IDS = {name: i for i, name in enumerate(ITEM_GROUP_NAMES)}

# grupos que Items::loadFromOtb aceita sem `return false`
ITEM_GROUPS_ACEITOS = {
    "none", "ground", "container", "splash", "fluid", "charges", "deprecated",
    "podium", "door", "magicfield", "teleport",
}

# itemflags_t (server/tfs/src/itemloader.h). Os marcados "unused" o TFS 1.4.2 nao
# le, mas sao gravados assim mesmo para compatibilidade com editores de mapa.
FLAG_BLOCK_SOLID = 1 << 0
FLAG_BLOCK_PROJECTILE = 1 << 1
FLAG_BLOCK_PATHFIND = 1 << 2
FLAG_HAS_HEIGHT = 1 << 3
FLAG_USEABLE = 1 << 4
FLAG_PICKUPABLE = 1 << 5
FLAG_MOVEABLE = 1 << 6
FLAG_STACKABLE = 1 << 7
FLAG_FLOORCHANGEDOWN = 1 << 8
FLAG_FLOORCHANGENORTH = 1 << 9
FLAG_FLOORCHANGEEAST = 1 << 10
FLAG_FLOORCHANGESOUTH = 1 << 11
FLAG_FLOORCHANGEWEST = 1 << 12
FLAG_ALWAYSONTOP = 1 << 13
FLAG_READABLE = 1 << 14
FLAG_ROTATABLE = 1 << 15
FLAG_HANGABLE = 1 << 16
FLAG_VERTICAL = 1 << 17
FLAG_HORIZONTAL = 1 << 18
FLAG_CANNOTDECAY = 1 << 19
FLAG_ALLOWDISTREAD = 1 << 20
FLAG_UNUSED = 1 << 21
FLAG_CLIENTCHARGES = 1 << 22
FLAG_LOOKTHROUGH = 1 << 23
FLAG_ANIMATION = 1 << 24
FLAG_FULLTILE = 1 << 25
FLAG_FORCEUSE = 1 << 26
FLAG_AMMO = 1 << 27
FLAG_REPORTABLE = 1 << 28

FLAG_NAMES = {
    "blockSolid": FLAG_BLOCK_SOLID,
    "blockProjectile": FLAG_BLOCK_PROJECTILE,
    "blockPathfind": FLAG_BLOCK_PATHFIND,
    "hasHeight": FLAG_HAS_HEIGHT,
    "useable": FLAG_USEABLE,
    "pickupable": FLAG_PICKUPABLE,
    "moveable": FLAG_MOVEABLE,
    "stackable": FLAG_STACKABLE,
    "floorChangeDown": FLAG_FLOORCHANGEDOWN,
    "floorChangeNorth": FLAG_FLOORCHANGENORTH,
    "floorChangeEast": FLAG_FLOORCHANGEEAST,
    "floorChangeSouth": FLAG_FLOORCHANGESOUTH,
    "floorChangeWest": FLAG_FLOORCHANGEWEST,
    "alwaysOnTop": FLAG_ALWAYSONTOP,
    "readable": FLAG_READABLE,
    "rotatable": FLAG_ROTATABLE,
    "hangable": FLAG_HANGABLE,
    "vertical": FLAG_VERTICAL,
    "horizontal": FLAG_HORIZONTAL,
    "cannotDecay": FLAG_CANNOTDECAY,
    "allowDistRead": FLAG_ALLOWDISTREAD,
    "unused": FLAG_UNUSED,
    "clientCharges": FLAG_CLIENTCHARGES,
    "lookThrough": FLAG_LOOKTHROUGH,
    "animation": FLAG_ANIMATION,
    "fullTile": FLAG_FULLTILE,
    "forceUse": FLAG_FORCEUSE,
    "ammo": FLAG_AMMO,
    "reportable": FLAG_REPORTABLE,
}


def flags_from_names(names):
    """['blockSolid', 'hasHeight'] -> inteiro de itemflags_t."""
    v = 0
    for n in names:
        if n not in FLAG_NAMES:
            raise KeyError("flag de OTB desconhecida: %r" % (n,))
        v |= FLAG_NAMES[n]
    return v


def names_from_flags(flags):
    return [n for n, bit in FLAG_NAMES.items() if flags & bit]


# ------------------------------------------------------------------ escapes
def _unescape(buf):
    out = bytearray()
    i = 0
    n = len(buf)
    while i < n:
        b = buf[i]
        if b == NODE_ESCAPE:
            i += 1
            if i < n:
                out.append(buf[i])
        else:
            out.append(b)
        i += 1
    return bytes(out)


def escape(buf):
    """Insere o prefixo 0xFD antes de todo byte FD/FE/FF."""
    out = bytearray()
    for b in buf:
        if b in (NODE_START, NODE_END, NODE_ESCAPE):
            out.append(NODE_ESCAPE)
        out.append(b)
    return bytes(out)


# ------------------------------------------------------------------ leitura
def parse_items_otb(path):
    """Devolve (header, [item, ...]).

    header: dict(identifier=bytes(4), root_type, raw_props=bytes, major, minor,
                 build, csd_version)
    item:   dict(group, group_name, flags, server_id, client_id, speed,
                 light_level, light_color, top_order, minimap_color, ware_id,
                 name, sprite_hash, raw_props)

    `raw_props` sao os bytes AINDA ESCAPADOS, do jeito que estao no arquivo:
    e o que permite reescrever byte a byte.
    """
    with open(path, "rb") as fh:
        data = fh.read()

    identifier = data[:4]
    pos = 4
    if data[pos] != NODE_START:
        raise ValueError("OTB invalido: falta NODE_START")
    pos += 1
    root_type = data[pos]
    pos += 1

    def read_props(start):
        i = start
        while i < len(data):
            b = data[i]
            if b == NODE_ESCAPE:
                i += 2
                continue
            if b in (NODE_START, NODE_END):
                break
            i += 1
        return data[start:i], i

    root_raw, pos = read_props(pos)
    root_props = _unescape(root_raw)
    header = {"identifier": identifier, "root_type": root_type,
              "raw_props": root_raw, "major": 0xFFFFFFFF, "minor": 0,
              "build": 0, "csd_version": b""}
    if len(root_props) >= 5:
        (flags,) = struct.unpack_from("<I", root_props, 0)
        header["flags"] = flags
        attr = root_props[4]
        if attr == ROOT_ATTR_VERSION:
            (datalen,) = struct.unpack_from("<H", root_props, 5)
            major, minor, build = struct.unpack_from("<III", root_props, 7)
            header.update(major=major, minor=minor, build=build,
                          csd_version=root_props[19:7 + datalen])

    items = []
    while pos < len(data):
        b = data[pos]
        if b == NODE_START:
            pos += 1
            node_type = data[pos]
            pos += 1
            raw, pos = read_props(pos)
            items.append(_parse_item(node_type, raw))
        elif b == NODE_END:
            pos += 1
        else:
            pos += 1
    return header, items


def _parse_item(node_type, raw_props):
    props = _unescape(raw_props)
    item = {
        "group": node_type,
        "group_name": ITEM_GROUP_NAMES[node_type] if node_type < len(ITEM_GROUP_NAMES) else str(node_type),
        "flags": 0,
        "server_id": 0,
        "client_id": 0,
        "speed": 0,
        "light_level": 0,
        "light_color": 0,
        "top_order": 0,
        "minimap_color": 0,
        "ware_id": 0,
        "name": "",
        "sprite_hash": b"",
        "raw_props": raw_props,
    }
    if len(props) < 4:
        return item
    (item["flags"],) = struct.unpack_from("<I", props, 0)
    i = 4
    while i + 3 <= len(props):
        attrib = props[i]
        (datalen,) = struct.unpack_from("<H", props, i + 1)
        i += 3
        payload = props[i:i + datalen]
        i += datalen
        if attrib == ITEM_ATTR_SERVERID and datalen == 2:
            (item["server_id"],) = struct.unpack("<H", payload)
        elif attrib == ITEM_ATTR_CLIENTID and datalen == 2:
            (item["client_id"],) = struct.unpack("<H", payload)
        elif attrib == ITEM_ATTR_SPEED and datalen == 2:
            (item["speed"],) = struct.unpack("<H", payload)
        elif attrib == ITEM_ATTR_NAME:
            item["name"] = payload.decode("latin-1")
        elif attrib == ITEM_ATTR_SPRITEHASH:
            item["sprite_hash"] = payload
        elif attrib == ITEM_ATTR_MINIMAPCOLOR and datalen == 2:
            (item["minimap_color"],) = struct.unpack("<H", payload)
        elif attrib == ITEM_ATTR_LIGHT2 and datalen == 4:
            lvl, col = struct.unpack("<HH", payload)
            item["light_level"], item["light_color"] = lvl, col
        elif attrib == ITEM_ATTR_TOPORDER and datalen == 1:
            item["top_order"] = payload[0]
        elif attrib == ITEM_ATTR_WAREID and datalen == 2:
            (item["ware_id"],) = struct.unpack("<H", payload)
    return item


# ------------------------------------------------------------------ escrita
def _attr(code, payload):
    return struct.pack("<BH", code, len(payload)) + payload


def build_item_props(item):
    """Monta os props (JA ESCAPADOS) de um item novo a partir do dict.

    Ordem dos atributos: a mesma que o items.otb original usa
    (serverid, clientid, spritehash?, light2?, speed?, toporder?, wareid?),
    para o diff entre builds ficar estavel. O TFS le em qualquer ordem.
    """
    props = struct.pack("<I", item.get("flags", 0) & 0xFFFFFFFF)
    props += _attr(ITEM_ATTR_SERVERID, struct.pack("<H", item["server_id"]))
    if item.get("client_id"):
        props += _attr(ITEM_ATTR_CLIENTID, struct.pack("<H", item["client_id"]))
    if item.get("sprite_hash"):
        props += _attr(ITEM_ATTR_SPRITEHASH, bytes(item["sprite_hash"]))
    if item.get("light_level") or item.get("light_color"):
        props += _attr(ITEM_ATTR_LIGHT2,
                       struct.pack("<HH", item.get("light_level", 0),
                                   item.get("light_color", 0)))
    if item.get("group_name") == "ground" or item.get("speed"):
        props += _attr(ITEM_ATTR_SPEED, struct.pack("<H", item.get("speed", 0)))
    if item.get("top_order"):
        props += _attr(ITEM_ATTR_TOPORDER, struct.pack("<B", item["top_order"]))
    if item.get("minimap_color"):
        props += _attr(ITEM_ATTR_MINIMAPCOLOR,
                       struct.pack("<H", item["minimap_color"]))
    if item.get("ware_id"):
        props += _attr(ITEM_ATTR_WAREID, struct.pack("<H", item["ware_id"]))
    return escape(props)


def build_root_props(header):
    """Monta os props da raiz a partir de major/minor/build/csd_version."""
    csd = bytes(header.get("csd_version", b""))[:128].ljust(128, b"\0")
    payload = struct.pack("<III", header.get("major", 3),
                          header.get("minor", 57), header.get("build", 0)) + csd
    props = struct.pack("<I", header.get("flags", 0))
    props += struct.pack("<BH", ROOT_ATTR_VERSION, len(payload)) + payload
    return escape(props)


def write_items_otb(path, items, header):
    """Escreve um items.otb completo.

    `items` e a lista devolvida por parse_items_otb, opcionalmente com entradas
    novas no fim. Cada item usa `raw_props` se existir (preserva byte a byte o
    que veio do arquivo original); senao os props sao montados por
    build_item_props(). O mesmo vale para header['raw_props'].
    """
    out = bytearray()
    out += bytes(header.get("identifier", b"\0\0\0\0"))[:4].ljust(4, b"\0")
    out.append(NODE_START)
    out.append(header.get("root_type", 0))
    out += header.get("raw_props") or build_root_props(header)

    vistos = set()
    for item in items:
        sid = item.get("server_id", 0)
        if sid in vistos:
            raise ValueError("server id duplicado no items.otb: %d" % sid)
        vistos.add(sid)
        group = item.get("group")
        if group is None:
            group = ITEM_GROUP_IDS[item.get("group_name", "none")]
        name = ITEM_GROUP_NAMES[group] if group < len(ITEM_GROUP_NAMES) else str(group)
        if name not in ITEM_GROUPS_ACEITOS:
            raise ValueError("grupo %r nao e aceito por Items::loadFromOtb (item %d)"
                             % (name, sid))
        out.append(NODE_START)
        out.append(group)
        out += item.get("raw_props") or build_item_props(item)
        out.append(NODE_END)

    out.append(NODE_END)
    with open(path, "wb") as fh:
        fh.write(out)
    return len(out)


def new_item(server_id, client_id, group_name="none", flags=0, speed=0,
             light_level=0, light_color=0, top_order=0, minimap_color=0,
             ware_id=0, name=""):
    """Cria o dict de um item NOVO (sem raw_props, entao sera serializado)."""
    if group_name not in ITEM_GROUP_IDS:
        raise KeyError("grupo desconhecido: %r" % (group_name,))
    return {
        "group": ITEM_GROUP_IDS[group_name],
        "group_name": group_name,
        "flags": flags,
        "server_id": server_id,
        "client_id": client_id,
        "speed": speed,
        "light_level": light_level,
        "light_color": light_color,
        "top_order": top_order,
        "minimap_color": minimap_color,
        "ware_id": ware_id,
        "name": name,
        "sprite_hash": b"",
        "raw_props": None,
    }


# ------------------------------------------------------------------ palette
def rgb_to_tibia_color(r, g, b):
    """RGB -> indice 0..215 da paleta 6x6x6 do cliente (Color::from8bit)."""
    def q(v):
        return max(0, min(5, int(round(max(0, min(255, v)) / 51.0))))
    return q(r) * 36 + q(g) * 6 + q(b)


def tibia_color_to_rgb(c):
    c = max(0, min(215, int(c)))
    return ((c // 36) % 6 * 51, (c // 6) % 6 * 51, c % 6 * 51)


if __name__ == "__main__":
    import sys
    h, items = parse_items_otb(sys.argv[1])
    print({k: v for k, v in h.items() if k != "raw_props"}, len(items))
    cids = [i["client_id"] for i in items if i["client_id"]]
    sids = [i["server_id"] for i in items]
    print("client ids:", len(cids), "min", min(cids), "max", max(cids), "unicos", len(set(cids)))
    print("server ids: min", min(sids), "max", max(sids), "unicos", len(set(sids)))
