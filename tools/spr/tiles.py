"""Itens NOVOS de cenario: manifesto -> items.otb + thing do .dat + items.xml.

Le `assets-src/sprites/tiles.json`, aloca ids ESTAVEIS em
`assets-src/sprites/allocations.json` e devolve, para cada tile:

  * um item de OTB (grupo + itemflags_t + serverId/clientId + speed/light/...)
  * um S.Thing do .dat (geometria width/height, fases, atributos de render)
  * uma entrada `<item>` para o items.xml do servidor

Regras de id (ver docs/sistemas/arte-e-sprites.md):
  * server id a partir de `server_id_base` (30000; o items.otb vanilla vai ate 26381)
  * client id a partir de `client_id_base` (23726; o vanilla vai ate 23725, entao
    a faixa continua CONTIGUA — obrigatorio, o .dat e lido sequencialmente)
  * uma vez alocado, um id NUNCA e reaproveitado nem renumerado: allocations.json
    e append-only. Remover um tile do tiles.json deixa o id aposentado.
  * `server_id` fixo no tile force aquele id (util para itens ja no mapa).
"""
import json
import os

import sprformat as S
import otb

CELL = 32

# group do manifesto -> grupo do OTB (itemgroup_t)
GROUP_TO_OTB = {
    "ground": "ground",
    "container": "container",
    "wall": "none",
    "door": "none",       # o TFS 1.4.2 marca porta pelo items.xml (type="door")
    "decoration": "none",
    "furniture": "none",
}

# flag de alto nivel -> nome de itemflags_t
FLAG_ALIAS = {
    "blocks_projectile": "blockProjectile",
    "blocks_pathfind": "blockPathfind",
    "has_height": "hasHeight",
    "useable": "useable",
    "pickupable": "pickupable",
    "movable": "moveable",
    "stackable": "stackable",
    "on_top": "alwaysOnTop",
    "readable": "readable",
    "rotatable": "rotatable",
    "hangable": "hangable",
    "vertical": "vertical",
    "horizontal": "horizontal",
    "cannot_decay": "cannotDecay",
    "allow_dist_read": "allowDistRead",
    "look_through": "lookThrough",
    "force_use": "forceUse",
    "full_tile": "fullTile",
}


# ------------------------------------------------------------------ manifesto
def load(path):
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    vistos = set()
    for t in cfg["tiles"]:
        k = t["key"]
        if k in vistos:
            raise ValueError("tiles.json: key duplicada %r" % k)
        vistos.add(k)
        if t.get("group") not in GROUP_TO_OTB:
            raise ValueError("tiles.json: %s tem group %r (use %s)"
                             % (k, t.get("group"), "/".join(sorted(GROUP_TO_OTB))))
        if not t.get("frames"):
            raise ValueError("tiles.json: %s sem 'frames'" % k)
    return cfg


# ------------------------------------------------------------------ alocacao
def allocate(cfg, alloc_path, otb_items):
    """Aloca (server_id, client_id) por key, de forma estavel entre builds.

    Grava/atualiza allocations.json. Nunca renumera uma key ja alocada.
    """
    alloc = {"format": 1,
             "_doc": "Alocacao PERMANENTE de ids para os tiles de "
                     "assets-src/sprites/tiles.json. Nunca edite nem apague uma "
                     "entrada: o id ficaria orfao em mapas e saves ja gravados. "
                     "Gerado por tools/spr/build_assets.py.",
             "next_server_id": cfg.get("server_id_base", 30000),
             "next_client_id": cfg.get("client_id_base", 23726),
             "by_key": {}}
    if os.path.exists(alloc_path):
        with open(alloc_path, encoding="utf-8") as fh:
            disco = json.load(fh)
        alloc["next_server_id"] = disco.get("next_server_id", alloc["next_server_id"])
        alloc["next_client_id"] = disco.get("next_client_id", alloc["next_client_id"])
        alloc["by_key"] = dict(disco.get("by_key", {}))

    usados_sid = {it["server_id"] for it in otb_items}
    usados_cid = {it["client_id"] for it in otb_items if it["client_id"]}
    for e in alloc["by_key"].values():
        usados_sid.discard(e["server_id"])
        usados_cid.discard(e["client_id"])

    novas = []
    for t in cfg["tiles"]:
        key = t["key"]
        got = alloc["by_key"].get(key)
        if got:
            if t.get("server_id") and t["server_id"] != got["server_id"]:
                raise ValueError(
                    "tiles.json: %s pede server_id %d mas allocations.json ja "
                    "fixou %d. Um id alocado nunca muda; use outra key."
                    % (key, t["server_id"], got["server_id"]))
            continue
        sid = t.get("server_id")
        if sid is None:
            sid = alloc["next_server_id"]
            while sid in usados_sid:
                sid += 1
            alloc["next_server_id"] = sid + 1
        elif sid in usados_sid:
            raise ValueError("tiles.json: %s pede server_id %d, ja ocupado" % (key, sid))
        cid = t.get("client_id")
        if cid is None:
            cid = alloc["next_client_id"]
            while cid in usados_cid:
                cid += 1
            alloc["next_client_id"] = cid + 1
        elif cid in usados_cid:
            raise ValueError("tiles.json: %s pede client_id %d, ja ocupado" % (key, cid))
        usados_sid.add(sid)
        usados_cid.add(cid)
        alloc["by_key"][key] = {"server_id": sid, "client_id": cid}
        novas.append((key, sid, cid))

    with open(alloc_path, "w", encoding="utf-8") as fh:
        json.dump(alloc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return alloc, novas


# ------------------------------------------------------------------- OTB item
def otb_flags(spec):
    f = 0
    fl = spec.get("flags") or {}
    walkable = fl.get("walkable", True)
    if not walkable:
        f |= otb.FLAG_BLOCK_SOLID
        # por padrao o que bloqueia passagem tambem bloqueia pathfind
        if fl.get("blocks_pathfind", True):
            f |= otb.FLAG_BLOCK_PATHFIND
    elif fl.get("blocks_pathfind"):
        f |= otb.FLAG_BLOCK_PATHFIND
    for alias, name in FLAG_ALIAS.items():
        if alias in ("blocks_pathfind",):
            continue
        if fl.get(alias):
            f |= otb.FLAG_NAMES[name]
    if len(spec["frames"]) > 1:
        # FLAG_ANIMATION do OTB PRECISA casar com animationPhases>1 no .dat
        f |= otb.FLAG_ANIMATION
    for name in spec.get("otb_flags", []):
        f |= otb.FLAG_NAMES[name]
    return f


def light_of(spec):
    lt = spec.get("light") or {}
    lvl = int(lt.get("level", 0))
    if not lvl:
        return 0, 0
    if "color" in lt:
        return lvl, int(lt["color"])
    return lvl, otb.rgb_to_tibia_color(lt.get("r", 255), lt.get("g", 255), lt.get("b", 255))


def make_otb_item(spec, sid, cid):
    lvl, col = light_of(spec)
    mm = spec.get("minimap_color", 0)
    if not mm and spec.get("minimap_rgb"):
        mm = otb.rgb_to_tibia_color(*spec["minimap_rgb"])
    group = GROUP_TO_OTB[spec["group"]]
    it = otb.new_item(sid, cid, group_name=group, flags=otb_flags(spec),
                      speed=spec.get("speed", 0), light_level=lvl, light_color=col,
                      top_order=spec.get("top_order", 0), minimap_color=mm,
                      name=spec.get("name", ""))
    return it


# ------------------------------------------------------------------ .dat thing
def make_thing(spec, cid, item, cache, pool, base_attrs):
    """base_attrs = build_assets.item_attrs(item) (traducao OTB -> atributos do .dat)."""
    w, h = spec.get("size", [1, 1])
    frames = spec["frames"]
    phases = len(frames)

    sprites = []
    for rel in frames:
        img = cache.get(rel)
        if img.size != (w * CELL, h * CELL):
            raise ValueError("%s: PNG %s tem %s, esperado %dx%d (size %dx%d tiles)"
                             % (spec["key"], rel, img.size, w * CELL, h * CELL, w, h))
        # ordem interna do .dat: h externo, w interno; o cliente desenha o
        # sprite (w,h) em ((width-1-w), (height-1-h))*32
        for hy in range(h):
            for wx in range(w):
                sx = (w - 1 - wx) * CELL
                sy = (h - 1 - hy) * CELL
                sprites.append(pool.add_image(img.crop((sx, sy, sx + CELL, sy + CELL))))

    g = S.FrameGroup(type=0, width=w, height=h, exact_size=CELL * max(w, h),
                     layers=1, pattern_x=1, pattern_y=1, pattern_z=1, phases=phases,
                     sprites=sprites)
    if phases > 1:
        anim = spec.get("animation") or {}
        durs = anim.get("durations") or [[500, 500]] * phases
        if len(durs) != phases:
            raise ValueError("%s: %d duracoes para %d fases"
                             % (spec["key"], len(durs), phases))
        g.animation = {"async_": anim.get("async", True),
                       "loop_count": anim.get("loop_count", 0),
                       "start_phase": anim.get("start_phase", 0),
                       "durations": [tuple(d) for d in durs]}

    attrs = [(a, list(v)) for a, v in base_attrs]
    if spec.get("elevation") is not None:
        attrs = [(a, v) for a, v in attrs if a != S.A_ELEVATION]
        if spec["elevation"]:
            attrs.append((S.A_ELEVATION, [int(spec["elevation"])]))
    if spec.get("displacement"):
        dx, dy = spec["displacement"]
        attrs.append((S.A_DISPLACEMENT, [int(dx), int(dy)]))
    if spec.get("dont_hide"):
        attrs.append((S.A_DONT_HIDE, []))
    return S.Thing(S.CATEGORY_ITEM, cid, name=spec.get("name", ""),
                   attrs=attrs, groups=[g])


# ------------------------------------------------------------------ items.xml
def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render_items_xml(cfg, alloc, header_comment):
    """Bloco <item> para injetar em server/tfs/data/items/items.xml."""
    out = [header_comment, ""]
    for spec in cfg["tiles"]:
        e = alloc["by_key"][spec["key"]]
        sid = e["server_id"]
        xml = dict(spec.get("xml") or {})
        article = xml.pop("article", None)
        plural = xml.pop("plural", None)
        head = '<item id="%d" name="%s"' % (sid, _esc(spec.get("name", spec["key"])))
        if article:
            head += ' article="%s"' % _esc(article)
        if plural:
            head += ' plural="%s"' % _esc(plural)
        head += '>  <!-- %s (%s, clientId %d) -->' % (spec["key"], spec["group"], e["client_id"])
        out.append(head)

        # atributos derivados do manifesto
        attrs = []
        fl = spec.get("flags") or {}
        if spec["group"] == "container":
            attrs.append(("containerSize", spec.get("container_size", 8)))
        if spec["group"] == "door" and "type" not in xml:
            attrs.append(("type", "door"))
        if spec.get("floorchange"):
            attrs.append(("floorchange", spec["floorchange"]))
        if fl.get("readable"):
            attrs.append(("readable", "1"))
            attrs.append(("maxTextLen", spec.get("max_text_len", 128)))
        if spec.get("weight") is not None:
            attrs.append(("weight", spec["weight"]))
        for k, v in xml.items():
            attrs.append((k, v))
        for k, v in attrs:
            out.append('\t<attribute key="%s" value="%s"/>' % (_esc(k), _esc(v)))
        out.append("</item>")
    out.append("")
    return "\n".join(out)
