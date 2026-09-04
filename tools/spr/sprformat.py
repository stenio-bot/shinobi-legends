"""Leitura/escrita dos formatos Tibia.spr e Tibia.dat versao 10.98.

A especificacao esta em tools/spr/FORMATO.md (derivada do codigo do OTClient
Redemption em client-otc/src/client/).
"""
import struct

SPRITE_SIZE = 32
SPRITE_PIXELS = SPRITE_SIZE * SPRITE_SIZE

# ---------------------------------------------------------------- atributos
# enum ThingAttr de client-otc/src/client/const.h:1180
A_GROUND = 0
A_GROUND_BORDER = 1
A_ON_BOTTOM = 2
A_ON_TOP = 3
A_CONTAINER = 4
A_STACKABLE = 5
A_FORCE_USE = 6
A_MULTI_USE = 7
A_WRITABLE = 8
A_WRITABLE_ONCE = 9
A_FLUID_CONTAINER = 10
A_SPLASH = 11
A_NOT_WALKABLE = 12
A_NOT_MOVEABLE = 13
A_BLOCK_PROJECTILE = 14
A_NOT_PATHABLE = 15
A_PICKUPABLE = 16
A_HANGABLE = 17
A_HOOK_SOUTH = 18
A_HOOK_EAST = 19
A_ROTATEABLE = 20
A_LIGHT = 21
A_DONT_HIDE = 22
A_TRANSLUCENT = 23
A_DISPLACEMENT = 24
A_ELEVATION = 25
A_LYING_CORPSE = 26
A_ANIMATE_ALWAYS = 27
A_MINIMAP_COLOR = 28
A_LENS_HELP = 29
A_FULL_GROUND = 30
A_LOOK = 31
A_CLOTH = 32
A_MARKET = 33
A_USABLE = 34
A_DEFAULT_ACTION = 251
A_NO_MOVE_ANIMATION = 253
A_LAST = 255

ATTR_NAMES = {v: k for k, v in list(globals().items()) if k.startswith("A_")}

# atributos que carregam payload: nome -> lista de tipos ("U16" / "STR")
ATTR_PAYLOAD = {
    A_GROUND: ["U16"],
    A_WRITABLE: ["U16"],
    A_WRITABLE_ONCE: ["U16"],
    A_LIGHT: ["U16", "U16"],
    A_DISPLACEMENT: ["U16", "U16"],
    A_ELEVATION: ["U16"],
    A_MINIMAP_COLOR: ["U16"],
    A_LENS_HELP: ["U16"],
    A_CLOTH: ["U16"],
    A_DEFAULT_ACTION: ["U16"],
    A_MARKET: ["U16", "U16", "U16", "STR", "U16", "U16"],
}

CATEGORY_ITEM, CATEGORY_CREATURE, CATEGORY_EFFECT, CATEGORY_MISSILE = range(4)
CATEGORY_NAMES = ["item", "creature", "effect", "missile"]
CATEGORY_FIRST_ID = [100, 1, 1, 1]


def attr_to_file_byte(attr):
    """Inverso do remapeamento de ThingType::unserialize para clientVersion >= 1000."""
    if attr == A_NO_MOVE_ANIMATION:
        return 16
    if attr == A_DEFAULT_ACTION:
        return 35
    if attr == A_USABLE:
        return 254
    if attr <= 15:
        return attr
    if attr > 250:
        raise ValueError("atributo %d nao suportado em 1098" % attr)
    return attr + 1


def file_byte_to_attr(f):
    if f == 16:
        return A_NO_MOVE_ANIMATION
    if f == 254:
        return A_USABLE
    if f == 35:
        return A_DEFAULT_ACTION
    if f > 16:
        return f - 1
    return f


# ------------------------------------------------------------------ writer
class BinWriter:
    def __init__(self):
        self.buf = bytearray()

    def u8(self, v):
        self.buf.append(v & 0xFF)

    def s8(self, v):
        self.buf += struct.pack("<b", v)

    def u16(self, v):
        self.buf += struct.pack("<H", v)

    def u32(self, v):
        self.buf += struct.pack("<I", v)

    def s32(self, v):
        self.buf += struct.pack("<i", v)

    def string(self, s):
        b = s.encode("utf-8")
        self.u16(len(b))
        self.buf += b

    def tell(self):
        return len(self.buf)


class BinReader:
    def __init__(self, data):
        self.d = data
        self.p = 0

    def seek(self, p):
        self.p = p

    def tell(self):
        return self.p

    def u8(self):
        v = self.d[self.p]
        self.p += 1
        return v

    def s8(self):
        v = struct.unpack_from("<b", self.d, self.p)[0]
        self.p += 1
        return v

    def u16(self):
        v = struct.unpack_from("<H", self.d, self.p)[0]
        self.p += 2
        return v

    def u32(self):
        v = struct.unpack_from("<I", self.d, self.p)[0]
        self.p += 4
        return v

    def s32(self):
        v = struct.unpack_from("<i", self.d, self.p)[0]
        self.p += 4
        return v

    def string(self):
        n = self.u16()
        v = self.d[self.p:self.p + n].decode("utf-8", "replace")
        self.p += n
        return v


# ------------------------------------------------------------------- .spr
def encode_sprite(rgba):
    """rgba: bytes/bytearray com 32*32*4 bytes (RGBA). Devolve o blob RLE (sem os
    3 bytes de cor-chave nem o U16 de tamanho)."""
    out = bytearray()
    i = 0
    n = SPRITE_PIXELS
    while i < n:
        # conta transparentes
        t = 0
        while i < n and rgba[i * 4 + 3] < 128:
            t += 1
            i += 1
        if i >= n:
            break  # cauda transparente nao precisa ser gravada
        start = i
        while i < n and rgba[i * 4 + 3] >= 128:
            i += 1
        colored = i - start
        out += struct.pack("<HH", t, colored)
        for p in range(start, i):
            out += bytes((rgba[p * 4], rgba[p * 4 + 1], rgba[p * 4 + 2]))
    return bytes(out)


def decode_sprite(blob):
    """Inverso de encode_sprite: devolve bytearray RGBA de 32*32*4."""
    px = bytearray(SPRITE_PIXELS * 4)
    off = 0
    write = 0
    n = len(blob)
    while off + 4 <= n and write < SPRITE_PIXELS:
        transparent, colored = struct.unpack_from("<HH", blob, off)
        off += 4
        write += transparent
        for _ in range(colored):
            if off + 3 > n or write >= SPRITE_PIXELS:
                break
            px[write * 4 + 0] = blob[off]
            px[write * 4 + 1] = blob[off + 1]
            px[write * 4 + 2] = blob[off + 2]
            px[write * 4 + 3] = 255
            off += 3
            write += 1
    return px


def write_spr(path, signature, sprite_blobs):
    """sprite_blobs: lista de blobs (bytes) na ordem dos ids 1..N. blob None/vazio
    grava offset 0 (sprite inexistente)."""
    count = len(sprite_blobs)
    header = BinWriter()
    header.u32(signature)
    header.u32(count)  # GameSpritesU32 ligada em 1098
    table_off = header.tell()
    body = bytearray()
    offsets = []
    base = table_off + 4 * count
    for blob in sprite_blobs:
        if not blob:
            offsets.append(0)
            continue
        offsets.append(base + len(body))
        body += b"\xFF\x00\xFF"           # cor-chave transparente (ignorada pelo cliente)
        body += struct.pack("<H", len(blob))
        body += blob
    out = bytearray(header.buf)
    for o in offsets:
        out += struct.pack("<I", o)
    out += body
    with open(path, "wb") as fh:
        fh.write(out)
    return len(out)


def read_spr(path):
    with open(path, "rb") as fh:
        data = fh.read()
    r = BinReader(data)
    signature = r.u32()
    count = r.u32()
    table = r.tell()
    offsets = [struct.unpack_from("<I", data, table + 4 * i)[0] for i in range(count)]
    return {"signature": signature, "count": count, "offsets": offsets, "data": data}


def spr_get_sprite(spr, sprite_id):
    """Devolve RGBA (bytearray) ou None."""
    if sprite_id <= 0 or sprite_id > spr["count"]:
        return None
    off = spr["offsets"][sprite_id - 1]
    if off == 0:
        return None
    data = spr["data"]
    size = struct.unpack_from("<H", data, off + 3)[0]
    return decode_sprite(data[off + 5: off + 5 + size])


# ------------------------------------------------------------------- .dat
class Thing:
    """Descricao de um ThingType pronto para serializar."""

    __slots__ = ("category", "id", "name", "attrs", "groups")

    def __init__(self, category, id_, name="", attrs=None, groups=None):
        self.category = category
        self.id = id_
        self.name = name
        self.attrs = attrs if attrs is not None else []   # [(attr, [args...]), ...]
        self.groups = groups or []                        # [FrameGroup, ...]


class FrameGroup:
    __slots__ = ("type", "width", "height", "exact_size", "layers",
                 "pattern_x", "pattern_y", "pattern_z", "phases",
                 "animation", "sprites")

    def __init__(self, type=0, width=1, height=1, exact_size=32, layers=1,
                 pattern_x=1, pattern_y=1, pattern_z=1, phases=1,
                 animation=None, sprites=None):
        self.type = type
        self.width = width
        self.height = height
        self.exact_size = exact_size
        self.layers = layers
        self.pattern_x = pattern_x
        self.pattern_y = pattern_y
        self.pattern_z = pattern_z
        self.phases = phases
        self.animation = animation   # dict(async_, loop_count, start_phase, durations=[(min,max)])
        self.sprites = sprites or []

    def sprite_count(self):
        return (self.width * self.height * self.layers * self.pattern_x
                * self.pattern_y * self.pattern_z * self.phases)


def _write_thing(w, thing, has_frame_groups):
    for attr, args in thing.attrs:
        w.u8(attr_to_file_byte(attr))
        types = ATTR_PAYLOAD.get(attr, [])
        if len(types) != len(args):
            raise ValueError("payload errado para atributo %d" % attr)
        for t, v in zip(types, args):
            if t == "U16":
                w.u16(v)
            else:
                w.string(v)
    w.u8(A_LAST)

    if has_frame_groups:
        w.u8(len(thing.groups))
    elif len(thing.groups) != 1:
        raise ValueError("categoria %d aceita apenas 1 frame group" % thing.category)

    for g in thing.groups:
        if has_frame_groups:
            w.u8(g.type)
        w.u8(g.width)
        w.u8(g.height)
        if g.width > 1 or g.height > 1:
            w.u8(g.exact_size)
        w.u8(g.layers)
        w.u8(g.pattern_x)
        w.u8(g.pattern_y)
        w.u8(g.pattern_z)     # clientVersion >= 755
        w.u8(g.phases)
        if g.phases > 1:      # GameEnhancedAnimations ligada em 1098
            a = g.animation or {}
            w.u8(0 if a.get("async_", True) else 1)
            w.s32(a.get("loop_count", 0))
            w.s8(a.get("start_phase", 0))
            durs = a.get("durations") or [(300, 300)] * g.phases
            for mn, mx in durs:
                w.u32(mn)
                w.u32(mx)
        expected = g.sprite_count()
        if len(g.sprites) != expected:
            raise ValueError("thing %d/%d: %d sprites, esperado %d"
                             % (thing.category, thing.id, len(g.sprites), expected))
        for s in g.sprites:
            w.u32(s)          # GameSpritesU32 ligada em 1098


def write_dat(path, signature, things_by_category):
    """things_by_category: lista de 4 dicts {id: Thing}, na ordem
    item/creature/effect/missile. Todos os ids de first_id..max precisam existir."""
    w = BinWriter()
    w.u32(signature)
    maxima = []
    for cat in range(4):
        m = max(things_by_category[cat]) if things_by_category[cat] else CATEGORY_FIRST_ID[cat] - 1
        maxima.append(m)
        w.u16(m)
    for cat in range(4):
        has_groups = (cat == CATEGORY_CREATURE)  # GameIdleAnimations ligada em 1098
        table = things_by_category[cat]
        for id_ in range(CATEGORY_FIRST_ID[cat], maxima[cat] + 1):
            t = table.get(id_)
            if t is None:
                raise ValueError("faltando thing %s id %d" % (CATEGORY_NAMES[cat], id_))
            _write_thing(w, t, has_groups)
    with open(path, "wb") as fh:
        fh.write(w.buf)
    return len(w.buf)


def read_dat(path):
    """Le um .dat 10.98 e devolve (signature, [dict{id: Thing} por categoria])."""
    with open(path, "rb") as fh:
        data = fh.read()
    r = BinReader(data)
    signature = r.u32()
    maxima = [r.u16() for _ in range(4)]
    out = []
    for cat in range(4):
        table = {}
        has_groups = (cat == CATEGORY_CREATURE)
        for id_ in range(CATEGORY_FIRST_ID[cat], maxima[cat] + 1):
            t = Thing(cat, id_)
            for _ in range(256):
                f = r.u8()
                if f == A_LAST:
                    break
                attr = file_byte_to_attr(f)
                args = []
                for ty in ATTR_PAYLOAD.get(attr, []):
                    args.append(r.u16() if ty == "U16" else r.string())
                t.attrs.append((attr, args))
            else:
                raise ValueError("dado corrompido em %s id %d (offset %d)"
                                 % (CATEGORY_NAMES[cat], id_, r.tell()))
            ngroups = r.u8() if has_groups else 1
            for _ in range(ngroups):
                g = FrameGroup()
                g.type = r.u8() if has_groups else 0
                g.width = r.u8()
                g.height = r.u8()
                if g.width > 1 or g.height > 1:
                    g.exact_size = r.u8()
                g.layers = r.u8()
                g.pattern_x = r.u8()
                g.pattern_y = r.u8()
                g.pattern_z = r.u8()
                g.phases = r.u8()
                if g.phases > 1:
                    a = {"async_": r.u8() == 0, "loop_count": r.s32(),
                         "start_phase": r.s8(), "durations": []}
                    for _ in range(g.phases):
                        a["durations"].append((r.u32(), r.u32()))
                    g.animation = a
                g.sprites = [r.u32() for _ in range(g.sprite_count())]
                t.groups.append(g)
            table[id_] = t
        out.append(table)
    if r.tell() != len(data):
        raise ValueError("sobraram %d bytes no fim do .dat" % (len(data) - r.tell()))
    return signature, out
