#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gravador do <mapa>-spawn.xml no formato do TFS 1.4.2.

Formato (ver server/tfs/src/spawn.cpp::Spawns::loadFromXml e o exemplo
server/tfs/data/world/forgotten-spawn.xml):

    <spawns>
        <spawn centerx="..." centery="..." centerz="..." radius="...">
            <monster name="..." x="0" y="0" z="7" spawntime="60"/>
            <npc name="..." x="0" y="0" z="7" spawntime="60"/>
        </spawn>
    </spawns>

``x``/``y`` das criaturas são OFFSETS relativos ao centro; ``z`` é absoluto.
O TFS avisa se ``radius`` > 30 ou se ``spawntime`` < 10s.
"""

from __future__ import annotations

from xml.sax.saxutils import quoteattr

MIN_SPAWNTIME = 10       # segundos (MINSPAWN_INTERVAL no TFS)
MAX_RADIUS = 30


class SpawnError(Exception):
    pass


class SpawnGroup:
    """Um <spawn> com N criaturas em offsets relativos ao centro."""

    def __init__(self, x, y, z, radius=3):
        if radius > MAX_RADIUS:
            raise SpawnError("radius %d > %d (o TFS reclama)" % (radius, MAX_RADIUS))
        self.x, self.y, self.z = int(x), int(y), int(z)
        self.radius = int(radius)
        #: lista de ``(kind, name, dx, dy, z, spawntime)``
        self.creatures = []

    def add_monster(self, name, dx=0, dy=0, spawntime=60, z=None):
        self._add("monster", name, dx, dy, spawntime, z)
        return self

    def add_npc(self, name, dx=0, dy=0, spawntime=60, z=None):
        self._add("npc", name, dx, dy, spawntime, z)
        return self

    def _add(self, kind, name, dx, dy, spawntime, z):
        if spawntime < MIN_SPAWNTIME:
            raise SpawnError("spawntime %d < %d s" % (spawntime, MIN_SPAWNTIME))
        if abs(dx) > self.radius or abs(dy) > self.radius:
            raise SpawnError("offset (%d,%d) fora do radius %d" % (dx, dy, self.radius))
        self.creatures.append((kind, name, int(dx), int(dy),
                               self.z if z is None else int(z), int(spawntime)))

    @property
    def positions(self):
        """Posições absolutas das criaturas do grupo."""
        return [(self.x + dx, self.y + dy, cz)
                for (_, _, dx, dy, cz, _) in self.creatures]


class SpawnFile:
    """Coleção de grupos de spawn, serializável para XML."""

    def __init__(self, header_comment=None):
        self.groups = []
        self.header_comment = header_comment

    def group(self, x, y, z, radius=3):
        g = SpawnGroup(x, y, z, radius)
        self.groups.append(g)
        return g

    def monster_count(self):
        return sum(1 for g in self.groups for c in g.creatures if c[0] == "monster")

    def npc_count(self):
        return sum(1 for g in self.groups for c in g.creatures if c[0] == "npc")

    def to_xml(self):
        out = ['<?xml version="1.0" encoding="UTF-8"?>']
        if self.header_comment:
            out.append("<!-- %s -->" % self.header_comment)
        out.append("<spawns>")
        for g in self.groups:
            if not g.creatures:
                continue        # o TFS avisa "Empty spawn"
            out.append('\t<spawn centerx="%d" centery="%d" centerz="%d" radius="%d">'
                       % (g.x, g.y, g.z, g.radius))
            for kind, name, dx, dy, cz, spawntime in g.creatures:
                out.append('\t\t<%s name=%s x="%d" y="%d" z="%d" spawntime="%d"/>'
                           % (kind, quoteattr(name), dx, dy, cz, spawntime))
            out.append("\t</spawn>")
        out.append("</spawns>")
        out.append("")
        return "\n".join(out)

    def write(self, path):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.to_xml())


def write_empty_house_file(path, comment=None):
    """Grava um ``<mapa>-house.xml`` vazio porém válido para o TFS."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    if comment:
        lines.append("<!-- %s -->" % comment)
    lines.append("<houses>")
    lines.append("</houses>")
    lines.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


__all__ = ["SpawnFile", "SpawnGroup", "SpawnError", "write_empty_house_file"]
