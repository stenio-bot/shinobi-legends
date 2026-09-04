"""Leitor mínimo do items.otb do TFS (formato OTB nó-a-nó).

Referência: server/tfs/src/fileloader.cpp (OTB::Loader::parseTree) e
server/tfs/src/items.cpp (Items::loadFromOtb).
"""
import struct

NODE_START = 0xFE
NODE_END = 0xFF
NODE_ESCAPE = 0xFD

ITEM_ATTR_SERVERID = 0x10
ITEM_ATTR_CLIENTID = 0x11

ITEM_GROUP_NAMES = [
    "none", "ground", "container", "weapon", "ammunition", "armor", "charges",
    "teleport", "magicfield", "writeable", "key", "splash", "fluid", "door",
    "deprecated", "podium",
]

# itemflags_t (server/tfs/src/itemloader.h)
FLAG_BLOCK_SOLID = 1 << 0
FLAG_BLOCK_PROJECTILE = 1 << 1
FLAG_BLOCK_PATHFIND = 1 << 2
FLAG_HAS_HEIGHT = 1 << 3
FLAG_USEABLE = 1 << 4
FLAG_PICKUPABLE = 1 << 5
FLAG_MOVEABLE = 1 << 6
FLAG_STACKABLE = 1 << 7
FLAG_ALWAYSONTOP = 1 << 13
FLAG_READABLE = 1 << 14
FLAG_ROTATABLE = 1 << 15
FLAG_HANGABLE = 1 << 16
FLAG_VERTICAL = 1 << 17
FLAG_HORIZONTAL = 1 << 18
FLAG_ALLOWDISTREAD = 1 << 20
FLAG_LOOKTHROUGH = 1 << 23
FLAG_ANIMATION = 1 << 24
FLAG_FULLTILE = 1 << 25
FLAG_FORCEUSE = 1 << 26


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


def parse_items_otb(path):
    """Devolve (header, [item, ...]) com item = dict(group, flags, server_id, client_id, ...)."""
    with open(path, "rb") as fh:
        data = fh.read()

    # 4 bytes de identificador ("OTBI" ou 0000) + nó raiz
    pos = 4
    assert data[pos] == NODE_START, "OTB inválido: falta NODE_START"
    pos += 1
    root_type = data[pos]
    pos += 1

    # props da raiz vão até o primeiro NODE_START/NODE_END
    def read_props(start):
        i = start
        raw = bytearray()
        while i < len(data):
            b = data[i]
            if b == NODE_ESCAPE:
                raw.append(data[i])
                raw.append(data[i + 1])
                i += 2
                continue
            if b in (NODE_START, NODE_END):
                break
            raw.append(b)
            i += 1
        return _unescape(bytes(raw)), i

    root_props, pos = read_props(pos)
    header = {"root_type": root_type}
    if len(root_props) >= 5:
        flags, attr = struct.unpack_from("<IB", root_props, 0)
        if attr == 0x01:
            (datalen,) = struct.unpack_from("<H", root_props, 5)
            major, minor, build = struct.unpack_from("<III", root_props, 7)
            header.update(major=major, minor=minor, build=build)

    items = []
    while pos < len(data):
        b = data[pos]
        if b == NODE_START:
            pos += 1
            node_type = data[pos]
            pos += 1
            props, pos = read_props(pos)
            items.append(_parse_item(node_type, props))
        elif b == NODE_END:
            pos += 1
        else:
            pos += 1
    return header, items


def _parse_item(node_type, props):
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
        elif attrib == 0x14 and datalen == 2:  # SPEED
            (item["speed"],) = struct.unpack("<H", payload)
        elif attrib == 0x21 and datalen == 2:  # MINIMAPCOLOR
            (item["minimap_color"],) = struct.unpack("<H", payload)
        elif attrib == 0x2A and datalen == 4:  # LIGHT2
            lvl, col = struct.unpack("<HH", payload)
            item["light_level"], item["light_color"] = lvl, col
        elif attrib == 0x2B and datalen == 1:  # TOPORDER
            item["top_order"] = payload[0]
    return item


if __name__ == "__main__":
    import sys
    h, items = parse_items_otb(sys.argv[1])
    print(h, len(items))
    cids = [i["client_id"] for i in items if i["client_id"]]
    print("client ids:", len(cids), "min", min(cids), "max", max(cids), "unicos", len(set(cids)))
