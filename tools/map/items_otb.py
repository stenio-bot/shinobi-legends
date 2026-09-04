#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Leitor mínimo de items.otb (TFS 1.4.2) para validar ids usados no mapa.

Só precisamos de: quais server ids existem, o grupo (chão? container?) e as
flags (bloqueia? empilhável?). Ver server/tfs/src/items.cpp::loadFromOtb.
"""

from __future__ import annotations

import struct

from otbm import read_otb

ITEM_GROUP_NONE = 0
ITEM_GROUP_GROUND = 1
ITEM_GROUP_CONTAINER = 2
ITEM_GROUP_SPLASH = 11
ITEM_GROUP_FLUID = 12
ITEM_GROUP_DEPRECATED = 14

FLAG_BLOCK_SOLID = 1 << 0
FLAG_BLOCK_PROJECTILE = 1 << 1
FLAG_BLOCK_PATHFIND = 1 << 2
FLAG_HAS_HEIGHT = 1 << 3
FLAG_PICKUPABLE = 1 << 5
FLAG_MOVEABLE = 1 << 6
FLAG_STACKABLE = 1 << 7
FLAG_ALWAYSONTOP = 1 << 13

ITEM_ATTR_SERVERID = 0x10
ITEM_ATTR_CLIENTID = 0x11


class ItemType:
    __slots__ = ("server_id", "client_id", "group", "flags")

    def __init__(self, server_id, client_id, group, flags):
        self.server_id = server_id
        self.client_id = client_id
        self.group = group
        self.flags = flags

    @property
    def is_ground(self):
        return self.group == ITEM_GROUP_GROUND

    @property
    def is_deprecated(self):
        return self.group == ITEM_GROUP_DEPRECATED

    @property
    def blocking(self):
        return bool(self.flags & FLAG_BLOCK_SOLID)

    @property
    def stackable(self):
        return bool(self.flags & FLAG_STACKABLE)

    @property
    def movable(self):
        return bool(self.flags & FLAG_MOVEABLE)

    def __repr__(self):  # pragma: no cover - debug
        return "ItemType(sid=%d, cid=%d, group=%d, flags=0x%x)" % (
            self.server_id, self.client_id, self.group, self.flags)


def load_items_otb(path):
    """Devolve ``{server_id: ItemType}``."""
    _, root = read_otb(path)
    types = {}
    for node in root.children:
        props = node.props
        if len(props) < 4:
            continue
        flags = struct.unpack_from("<I", props, 0)[0]
        pos = 4
        server_id = client_id = 0
        while pos + 3 <= len(props):
            attr = props[pos]
            datalen = struct.unpack_from("<H", props, pos + 1)[0]
            pos += 3
            data = props[pos:pos + datalen]
            pos += datalen
            if attr == ITEM_ATTR_SERVERID and datalen == 2:
                server_id = struct.unpack("<H", data)[0]
            elif attr == ITEM_ATTR_CLIENTID and datalen == 2:
                client_id = struct.unpack("<H", data)[0]
        types[server_id] = ItemType(server_id, client_id, node.type, flags)
    return types


if __name__ == "__main__":  # python3 items_otb.py items.otb 4526 2700 ...
    import sys
    tps = load_items_otb(sys.argv[1])
    print("itens em items.otb:", len(tps))
    for arg in sys.argv[2:]:
        sid = int(arg)
        it = tps.get(sid)
        if not it:
            print(sid, "AUSENTE")
        else:
            print(sid, "grupo=%d" % it.group, "chao" if it.is_ground else "",
                  "bloqueia" if it.blocking else "", "empilhavel" if it.stackable else "",
                  "movivel" if it.movable else "", "DEPRECADO" if it.is_deprecated else "")
