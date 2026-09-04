#!/usr/bin/env python3
"""Mini-ObjectBuilder: gera Tibia.spr + Tibia.dat 10.98 a partir de
assets-src/sprites/manifest.json + PNGs.

Uso:
    .venv/bin/python tools/spr/build_assets.py
    .venv/bin/python tools/spr/build_assets.py --out client-otc/data/things/1098

Especificacao do formato: tools/spr/FORMATO.md
"""
import argparse
import hashlib
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

import imports as IMP  # noqa: E402
import sprformat as S  # noqa: E402
import tiles as T  # noqa: E402
from otb import parse_items_otb, write_items_otb  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CELL = 32

FLAGS = {
    "BLOCK_SOLID": 1 << 0, "BLOCK_PROJECTILE": 1 << 1, "BLOCK_PATHFIND": 1 << 2,
    "HAS_HEIGHT": 1 << 3, "USEABLE": 1 << 4, "PICKUPABLE": 1 << 5, "MOVEABLE": 1 << 6,
    "STACKABLE": 1 << 7, "ALWAYSONTOP": 1 << 13, "READABLE": 1 << 14,
    "ROTATABLE": 1 << 15, "HANGABLE": 1 << 16, "VERTICAL": 1 << 17,
    "HORIZONTAL": 1 << 18, "ALLOWDISTREAD": 1 << 20, "LOOKTHROUGH": 1 << 23,
    "ANIMATION": 1 << 24, "FULLTILE": 1 << 25, "FORCEUSE": 1 << 26,
}


# ------------------------------------------------------------ pool de sprites
class SpritePool:
    """Deduplica sprites 32x32 por conteudo. Sprite id 1..N; 0 = vazio."""

    def __init__(self):
        self.blobs = []
        self.by_hash = {}
        self.empty = 0

    def add(self, rgba_bytes):
        if not any(rgba_bytes[3::4]):
            self.empty += 1
            return 0
        h = hashlib.blake2b(bytes(rgba_bytes), digest_size=16).digest()
        got = self.by_hash.get(h)
        if got:
            return got
        blob = S.encode_sprite(rgba_bytes)
        self.blobs.append(blob)
        sid = len(self.blobs)
        self.by_hash[h] = sid
        return sid

    def add_image(self, img):
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        if img.size != (CELL, CELL):
            raise ValueError("sprite precisa ser 32x32, veio %s" % (img.size,))
        return self.add(bytearray(img.tobytes()))


# ------------------------------------------------------------- folhas de PNG
class SheetCache:
    def __init__(self, root):
        self.root = root
        self.cache = {}

    def get(self, rel):
        img = self.cache.get(rel)
        if img is None:
            path = os.path.join(self.root, rel)
            img = Image.open(path).convert("RGBA")
            self.cache[rel] = img
        return img

    def cell(self, rel, col, row, w_tiles, h_tiles):
        img = self.get(rel)
        x0 = col * w_tiles * CELL
        y0 = row * h_tiles * CELL
        box = (x0, y0, x0 + w_tiles * CELL, y0 + h_tiles * CELL)
        if box[2] > img.size[0] or box[3] > img.size[1]:
            raise ValueError("%s: celula (%d,%d) fora da imagem %s" % (rel, col, row, img.size))
        return img.crop(box)


def cell_sprites(cell_img, w_tiles, h_tiles, pool):
    """Devolve a lista de sprite ids na ordem interna do .dat: h externo, w interno.
    O cliente desenha o sprite (w,h) em ((width-1-w), (height-1-h))*32."""
    ids = []
    for h in range(h_tiles):
        for w in range(w_tiles):
            sx = (w_tiles - 1 - w) * CELL
            sy = (h_tiles - 1 - h) * CELL
            ids.append(pool.add_image(cell_img.crop((sx, sy, sx + CELL, sy + CELL))))
    return ids


# ------------------------------------------------------------------ regras
def flags_of(item):
    return item["flags"]


def rule_matches(rule, item):
    w = rule.get("when") or {}
    if "group" in w and item["group_name"] != w["group"]:
        return False
    if "group_in" in w and item["group_name"] not in w["group_in"]:
        return False
    f = flags_of(item)
    for name in w.get("flags_all", []):
        if not (f & FLAGS[name]):
            return False
    for name in w.get("flags_none", []):
        if f & FLAGS[name]:
            return False
    for name in w.get("flags_any", []):
        if f & FLAGS[name]:
            break
    else:
        if w.get("flags_any"):
            return False
    if "top_order" in w and item["top_order"] != w["top_order"]:
        return False
    return True


def resolve_sheet(rule, item, sheets):
    key = rule["sheet"]
    cid = item["client_id"]
    key = key.replace("{minimap_color}", str(item["minimap_color"]))
    for n in (3, 4, 6, 8):
        key = key.replace("{v%d}" % n, str(cid % n))
    if key not in sheets:
        key = rule.get("fallback_sheet", key)
    return sheets[key]


def item_attrs(item):
    """Traduz as flags do items.otb para atributos do .dat (ver FORMATO.md 3.1)."""
    f = item["flags"]
    attrs = []
    if item["group_name"] == "ground":
        attrs.append((S.A_GROUND, [item["speed"] or 100]))
    top = item["top_order"]
    if top == 1:
        attrs.append((S.A_GROUND_BORDER, []))
    elif top == 2:
        attrs.append((S.A_ON_BOTTOM, []))
    elif top == 3:
        attrs.append((S.A_ON_TOP, []))
    if item["group_name"] == "container":
        attrs.append((S.A_CONTAINER, []))
    if f & FLAGS["STACKABLE"]:
        attrs.append((S.A_STACKABLE, []))
    if f & FLAGS["FORCEUSE"]:
        attrs.append((S.A_FORCE_USE, []))
    if f & FLAGS["USEABLE"]:
        attrs.append((S.A_MULTI_USE, []))
    if item["group_name"] == "fluid":
        attrs.append((S.A_FLUID_CONTAINER, []))
    if item["group_name"] == "splash":
        attrs.append((S.A_SPLASH, []))
    if f & FLAGS["BLOCK_SOLID"]:
        attrs.append((S.A_NOT_WALKABLE, []))
    if not (f & FLAGS["MOVEABLE"]):
        attrs.append((S.A_NOT_MOVEABLE, []))
    if f & FLAGS["BLOCK_PROJECTILE"]:
        attrs.append((S.A_BLOCK_PROJECTILE, []))
    if f & FLAGS["BLOCK_PATHFIND"]:
        attrs.append((S.A_NOT_PATHABLE, []))
    if f & FLAGS["PICKUPABLE"]:
        attrs.append((S.A_PICKUPABLE, []))
    if f & FLAGS["HANGABLE"]:
        attrs.append((S.A_HANGABLE, []))
    if f & FLAGS["HORIZONTAL"]:
        attrs.append((S.A_HOOK_SOUTH, []))
    if f & FLAGS["VERTICAL"]:
        attrs.append((S.A_HOOK_EAST, []))
    if f & FLAGS["ROTATABLE"]:
        attrs.append((S.A_ROTATEABLE, []))
    if item["light_level"]:
        attrs.append((S.A_LIGHT, [item["light_level"], item["light_color"]]))
    if f & FLAGS["LOOKTHROUGH"]:
        attrs.append((S.A_TRANSLUCENT, []))
    if f & FLAGS["HAS_HEIGHT"]:
        attrs.append((S.A_ELEVATION, [8]))
    if item["minimap_color"]:
        attrs.append((S.A_MINIMAP_COLOR, [item["minimap_color"]]))
    if f & FLAGS["FULLTILE"]:
        attrs.append((S.A_FULL_GROUND, []))
    if f & FLAGS["READABLE"]:
        attrs.append((S.A_WRITABLE_ONCE, [255]))
    # atributos ordenados: o cliente aceita qualquer ordem, mas manter estavel
    # facilita diffs entre builds
    return attrs


# -------------------------------------------------------------------- build
def build_items(manifest, sheets_dir, pool, stats, otb_items, tile_by_cid=None):
    cfg = manifest["items"]
    tile_by_cid = tile_by_cid or {}

    by_cid = {}
    for it in otb_items:
        cid = it["client_id"]
        if cid and cid not in by_cid:
            by_cid[cid] = it
    max_id = max(by_cid)

    sheets = cfg["sheets"]
    # as chaves de overrides sao server ids do TFS; traduz para clientId
    overrides = {}
    faltando = []
    srv_to_cid = {it["server_id"]: it["client_id"] for it in otb_items if it["client_id"]}
    if cfg.get("override_id_space", "server") == "server":
        for key, ov in cfg["overrides"].items():
            cid = srv_to_cid.get(int(key))
            if not cid:
                faltando.append(key)
                continue
            overrides[str(cid)] = ov
    else:
        overrides = dict(cfg["overrides"])
    stats["overrides_sem_otb"] = faltando
    cache = SheetCache(sheets_dir)
    sprite_of_sheet = {}

    def sprite_for(rel):
        sid = sprite_of_sheet.get(rel)
        if sid is None:
            sid = pool.add_image(cache.cell(rel, 0, 0, 1, 1))
            sprite_of_sheet[rel] = sid
        return sid

    table = {}
    for cid in range(100, max_id + 1):
        item = by_cid.get(cid)
        if item is None:
            # id nao referenciado pelo OTB: grava um thing vazio para manter o
            # alinhamento sequencial do arquivo
            item = {"client_id": cid, "group_name": "none", "flags": 0, "speed": 0,
                    "minimap_color": 0, "light_level": 0, "light_color": 0, "top_order": 0}
            stats["itens_sem_otb"] += 1
        spec = tile_by_cid.get(cid)
        if spec:
            # item novo de cenario (assets-src/sprites/tiles.json): arte propria,
            # geometria propria, atributos derivados do proprio manifesto
            table[cid] = T.make_thing(spec, cid, item, cache, pool, item_attrs(item))
            stats["estilos"]["tile"] = stats["estilos"].get("tile", 0) + 1
            if item["flags"] & FLAGS["ANIMATION"]:
                stats["itens_animados"] += 1
            continue
        ov = overrides.get(str(cid))
        if ov:
            rel = ov["sheet"]
            style = "override"
        else:
            rule = next(r for r in cfg["rules"] if rule_matches(r, item))
            rel = resolve_sheet(rule, item, sheets)
            style = rule["style"]
        stats["estilos"][style] = stats["estilos"].get(style, 0) + 1

        # ------------------------------------------------------------------
        # Itens com FLAG_ANIMATION no OTB PRECISAM de mais de uma fase.
        # NetworkMessage::addItem (server/tfs/src/networkmessage.cpp:96) manda um
        # byte 0xFE extra quando `it.isAnimation`, e o cliente so consome esse byte
        # se o ThingType tiver getAnimationPhases() > 1
        # (client-otc/src/client/protocolgameparse.cpp:4345, feature
        # GameItemAnimationPhase, ativa desde 910). Com 1 fase sobra um byte e o
        # pacote de mapa inteiro desalinha -> "getThing: invalid thing id".
        # As duas fases usam o mesmo sprite: o que importa e a contagem.
        # ------------------------------------------------------------------
        animated = bool(item["flags"] & FLAGS["ANIMATION"])
        sid = sprite_for(rel)
        if animated:
            stats["itens_animados"] += 1
            g = S.FrameGroup(type=0, width=1, height=1, layers=1,
                             pattern_x=1, pattern_y=1, pattern_z=1, phases=2,
                             animation={"async_": True, "loop_count": 0,
                                        "start_phase": 0,
                                        "durations": [(500, 500), (500, 500)]},
                             sprites=[sid, sid])
        else:
            g = S.FrameGroup(type=0, width=1, height=1, layers=1,
                             pattern_x=1, pattern_y=1, pattern_z=1, phases=1,
                             sprites=[sid])
        table[cid] = S.Thing(S.CATEGORY_ITEM, cid, attrs=item_attrs(item), groups=[g])

    # --------------------------------------------------------------------
    # Conferencia 1:1 OTB -> .dat dos flags que fazem o servidor mandar bytes
    # extras. Qualquer divergencia desalinha o pacote.
    # --------------------------------------------------------------------
    esperado = {"stackable": 0, "fluid": 0, "splash": 0, "animation": 0}
    for cid in range(100, max_id + 1):
        it = by_cid.get(cid)
        if not it:
            continue
        if it["flags"] & FLAGS["STACKABLE"]:
            esperado["stackable"] += 1
        if it["group_name"] == "fluid":
            esperado["fluid"] += 1
        if it["group_name"] == "splash":
            esperado["splash"] += 1
        if it["flags"] & FLAGS["ANIMATION"]:
            esperado["animation"] += 1
    obtido = {"stackable": 0, "fluid": 0, "splash": 0, "animation": 0}
    for th in table.values():
        a = {x for x, _ in th.attrs}
        obtido["stackable"] += S.A_STACKABLE in a
        obtido["fluid"] += S.A_FLUID_CONTAINER in a
        obtido["splash"] += S.A_SPLASH in a
        obtido["animation"] += th.groups[0].phases > 1
    stats["conferencia"] = (esperado, obtido)
    return table


CAT_OF_NAME = {"item": S.CATEGORY_ITEM, "creature": S.CATEGORY_CREATURE,
               "effect": S.CATEGORY_EFFECT, "missile": S.CATEGORY_MISSILE}


def build_thing(spec, cache, pool):
    cat = CAT_OF_NAME[spec["category"]]
    w = spec.get("width", 1)
    h = spec.get("height", 1)
    layers = spec.get("layers", 1)
    px = spec.get("pattern_x", 1)
    py = spec.get("pattern_y", 1)
    pz = spec.get("pattern_z", 1)
    sheets = spec["sheets"]
    if len(sheets) != layers:
        raise ValueError("thing %s: %d folhas para %d camadas"
                         % (spec.get("name"), len(sheets), layers))

    groups = []
    phase_base = 0
    for gspec in spec["frame_groups"]:
        phases = gspec["phases"]
        g = S.FrameGroup(type=gspec.get("type", 0), width=w, height=h,
                         exact_size=spec.get("exact_size", 32), layers=layers,
                         pattern_x=px, pattern_y=py, pattern_z=pz, phases=phases)
        anim = gspec.get("animation")
        if anim:
            g.animation = {"async_": anim.get("async", True),
                           "loop_count": anim.get("loop_count", 0),
                           "start_phase": anim.get("start_phase", 0),
                           "durations": [tuple(d) for d in anim["durations"]]}
        sprites = []
        for a in range(phases):
            for z in range(pz):
                for y in range(py):
                    for x in range(px):
                        row = (((phase_base + a) * pz + z) * py + y)
                        for l in range(layers):
                            cell = cache.cell(sheets[l], x, row, w, h)
                            sprites.extend(cell_sprites(cell, w, h, pool))
        g.sprites = sprites
        groups.append(g)
        phase_base += phases

    attrs = []
    for a in spec.get("attrs", []):
        attrs.append((getattr(S, a[0]), a[1:] and list(a[1:]) or []))
    return cat, S.Thing(cat, spec["id"], name=spec.get("name", ""),
                        attrs=attrs, groups=groups)


def load_base_otb(otb_path):
    """Le o items.otb BASE. Se existir items.otb.vanilla (backup feito na
    primeira vez que gravamos itens novos), e ele o ponto de partida — assim o
    build e idempotente e nunca duplica os tiles ja adicionados."""
    vanilla = otb_path + ".vanilla"
    base = vanilla if os.path.exists(vanilla) else otb_path
    header, items = parse_items_otb(base)
    return base, header, items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="assets-src/sprites/manifest.json")
    ap.add_argument("--tiles", default="assets-src/sprites/tiles.json",
                    help="manifesto dos itens NOVOS de cenario")
    ap.add_argument("--allocations", default="assets-src/sprites/allocations.json")
    ap.add_argument("--imports", default="assets-src/sprites/imports.json",
                    help="mapeamento da arte importada (assets-src/import/extracted)")
    ap.add_argument("--no-imports", action="store_true")
    ap.add_argument("--items-xml", default="server/generated/items/items_tiles_naruto.xml")
    ap.add_argument("--out", default="client-otc/data/things/1098")
    ap.add_argument("--no-otb", action="store_true",
                    help="nao reescrever o items.otb (so .spr/.dat)")
    args = ap.parse_args()

    manifest_path = os.path.join(ROOT, args.manifest)
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    sheets_dir = os.path.join(ROOT, manifest["sheet_root"])

    # ------------------------------------------------- arte importada (imports.json)
    # Prioridade: import > override do placeholder. Entradas cujo PNG de origem
    # nao existir (o material fica fora do git) sao puladas com aviso.
    imp = None
    imports_path = os.path.join(ROOT, args.imports)
    if not args.no_imports and os.path.exists(imports_path):
        imp = IMP.apply(manifest, IMP.load(imports_path), ROOT, sheets_dir)
    out_dir = os.path.join(ROOT, args.out)
    os.makedirs(out_dir, exist_ok=True)

    otb_path = os.path.join(ROOT, manifest["items"]["otb"])
    base_otb, otb_header, otb_items = load_base_otb(otb_path)

    # ------------------------------------------------------ itens novos (tiles)
    tiles_path = os.path.join(ROOT, args.tiles)
    tile_cfg = None
    tile_by_cid = {}
    alloc = None
    novas = []
    novos_otb = []
    if os.path.exists(tiles_path):
        tile_cfg = T.load(tiles_path)
        alloc_path = os.path.join(ROOT, args.allocations)
        alloc, novas = T.allocate(tile_cfg, alloc_path, otb_items)
        for spec in tile_cfg["tiles"]:
            e = alloc["by_key"][spec["key"]]
            it = T.make_otb_item(spec, e["server_id"], e["client_id"])
            novos_otb.append(it)
            tile_by_cid[e["client_id"]] = spec
        otb_items = otb_items + novos_otb

    pool = SpritePool()
    stats = {"estilos": {}, "itens_sem_otb": 0, "overrides_sem_otb": [],
             "itens_animados": 0, "conferencia": None}
    cache = SheetCache(sheets_dir)

    tables = [{}, {}, {}, {}]
    tables[S.CATEGORY_ITEM] = build_items(manifest, sheets_dir, pool, stats,
                                          otb_items, tile_by_cid)
    for spec in manifest["things"]:
        cat, thing = build_thing(spec, cache, pool)
        tables[cat][thing.id] = thing

    # todo id de 1..max precisa existir; preenche buracos com thing vazio
    for cat in (S.CATEGORY_CREATURE, S.CATEGORY_EFFECT, S.CATEGORY_MISSILE):
        if not tables[cat]:
            continue
        for i in range(1, max(tables[cat]) + 1):
            if i not in tables[cat]:
                g = S.FrameGroup(sprites=[0])
                tables[cat][i] = S.Thing(cat, i, groups=[g])

    dat_sig = int(manifest["dat_signature"], 0)
    spr_sig = int(manifest["spr_signature"], 0)
    dat_path = os.path.join(out_dir, "Tibia.dat")
    spr_path = os.path.join(out_dir, "Tibia.spr")
    dat_size = S.write_dat(dat_path, dat_sig, tables)
    spr_size = S.write_spr(spr_path, spr_sig, pool.blobs)

    # --------------------------------------------------- items.otb + items.xml
    if novos_otb and not args.no_otb:
        vanilla = otb_path + ".vanilla"
        if not os.path.exists(vanilla):
            shutil.copy2(otb_path, vanilla)
            print("backup: %s (feito uma unica vez)" % vanilla)
        n = write_items_otb(otb_path, otb_items, otb_header)
        print("items.otb -> %s (%.1f KB, %d itens, base %s)"
              % (otb_path, n / 1024.0, len(otb_items), os.path.basename(base_otb)))

        xml_path = os.path.join(ROOT, args.items_xml)
        os.makedirs(os.path.dirname(xml_path), exist_ok=True)
        cab = ("<!-- GERADO por tools/spr/build_assets.py a partir de\n"
               "     assets-src/sprites/tiles.json + allocations.json. NAO EDITE A MAO.\n"
               "     Itens NOVOS de cenario: os ids ja estao no items.otb (idem gerado).\n"
               "     Injete este bloco em server/tfs/data/items/items.xml. -->")
        with open(xml_path, "w", encoding="utf-8") as fh:
            fh.write(T.render_items_xml(tile_cfg, alloc, cab))
        print("items.xml -> %s (%d itens)" % (xml_path, len(tile_cfg["tiles"])))
    elif novos_otb:
        print("(--no-otb) items.otb NAO reescrito; %d tiles ficaram so no .dat"
              % len(novos_otb))

    print("Tibia.dat -> %s (%.1f KB)" % (dat_path, dat_size / 1024.0))
    print("Tibia.spr -> %s (%.1f KB)" % (spr_path, spr_size / 1024.0))
    print("things: itens=%d (100..%d)  criaturas=%d  efeitos=%d  missiles=%d"
          % (len(tables[0]), max(tables[0]), len(tables[1]), len(tables[2]), len(tables[3])))
    print("sprites unicos: %d (celulas vazias reaproveitadas: %d)"
          % (len(pool.blobs), pool.empty))
    if imp is not None:
        print("imports.json: %d criaturas, %d efeitos, %d missiles, %d icones de item"
              % (imp.applied["creatures"], imp.applied["effects"],
                 imp.applied["missiles"], imp.applied["items"]))
        if imp.missing:
            print("AVISO: %d recortes de import nao encontrados (entradas ignoradas): %s"
                  % (len(imp.missing), ", ".join(sorted(set(imp.missing))[:8])))
    print("estilos de item: %s" % sorted(stats["estilos"].items(), key=lambda kv: -kv[1]))
    print("itens com 2 fases (FLAG_ANIMATION do OTB): %d" % stats["itens_animados"])
    if stats["conferencia"]:
        esp, obt = stats["conferencia"]
        ok = esp == obt
        print("conferencia OTB -> .dat (por clientId): %s" % ("OK" if ok else "DIVERGENCIA"))
        for k in ("stackable", "fluid", "splash", "animation"):
            print("   %-10s otb=%-6d dat=%-6d %s"
                  % (k, esp[k], obt[k], "ok" if esp[k] == obt[k] else "<<< DIVERGE"))
    if tile_cfg:
        print("tiles proprios: %d (serverId %s)"
              % (len(tile_cfg["tiles"]),
                 ", ".join(str(alloc["by_key"][t["key"]]["server_id"])
                           for t in tile_cfg["tiles"])))
        for key, sid, cid in novas:
            print("   NOVO id alocado: %-16s serverId=%d clientId=%d" % (key, sid, cid))
    if stats["overrides_sem_otb"]:
        print("AVISO: server ids do tfs_mapping sem entrada no items.otb: %s"
              % stats["overrides_sem_otb"])
    if stats["itens_sem_otb"]:
        print("ids sem entrada no OTB preenchidos: %d" % stats["itens_sem_otb"])


if __name__ == "__main__":
    main()
