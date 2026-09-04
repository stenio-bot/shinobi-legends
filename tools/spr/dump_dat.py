#!/usr/bin/env python3
"""Le um par Tibia.dat/Tibia.spr 10.98 e imprime estatisticas; opcionalmente
exporta sprites para PNG (valida o round-trip do encoder RLE).

Uso:
    .venv/bin/python tools/spr/dump_dat.py
    .venv/bin/python tools/spr/dump_dat.py --thing creature:129 --thing item:2404
    .venv/bin/python tools/spr/dump_dat.py --export-dir /tmp/dump --export 40
"""
import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sprformat as S  # noqa: E402
from otb import parse_items_otb, FLAG_STACKABLE, FLAG_ANIMATION  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ATTR_LABEL = {getattr(S, n): n[2:].lower() for n in dir(S)
              if n.startswith("A_") and isinstance(getattr(S, n), int)}


def describe(thing):
    g = thing.groups[0]
    attrs = ",".join(ATTR_LABEL.get(a, str(a)) + (("=" + "/".join(map(str, v))) if v else "")
                     for a, v in thing.attrs) or "-"
    grp = " | ".join(
        "grupo%d %dx%d L%d pat %dx%dx%d fases %d sprites %d"
        % (x.type, x.width, x.height, x.layers, x.pattern_x, x.pattern_y,
           x.pattern_z, x.phases, len(x.sprites))
        for x in thing.groups)
    return "%s | %s | 1o sprite id %d" % (attrs, grp, g.sprites[0] if g.sprites else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="client-otc/data/things/1098")
    ap.add_argument("--thing", action="append", default=[],
                    help="categoria:id para detalhar, ex.: creature:129")
    ap.add_argument("--export", type=int, default=0, help="quantos sprites exportar")
    ap.add_argument("--export-dir", default="")
    ap.add_argument("--otb", default="server/tfs/data/items/items.otb",
                    help="items.otb para conferir os flags item a item")
    args = ap.parse_args()

    d = os.path.join(ROOT, args.dir) if not os.path.isabs(args.dir) else args.dir
    dat_path = os.path.join(d, "Tibia.dat")
    spr_path = os.path.join(d, "Tibia.spr")

    sig, tables = S.read_dat(dat_path)
    spr = S.read_spr(spr_path)

    print("== %s" % dat_path)
    print("assinatura .dat: 0x%08X (contentRevision %d)" % (sig, sig & 0xFFFF))
    print("== %s" % spr_path)
    print("assinatura .spr: 0x%08X | sprites: %d | vazios: %d | tamanho: %.1f KB"
          % (spr["signature"], spr["count"],
             sum(1 for o in spr["offsets"] if o == 0),
             os.path.getsize(spr_path) / 1024.0))
    print()

    used = set()
    for cat in range(4):
        t = tables[cat]
        if not t:
            print("%-9s vazio" % S.CATEGORY_NAMES[cat])
            continue
        ids = sorted(t)
        sprite_ids = set()
        attr_count = Counter()
        sizes = Counter()
        layers = Counter()
        phases = Counter()
        com_sprite = 0
        for th in t.values():
            has = False
            for g in th.groups:
                sizes["%dx%d" % (g.width, g.height)] += 1
                layers[g.layers] += 1
                phases[g.phases] += 1
                for s in g.sprites:
                    if s:
                        sprite_ids.add(s)
                        has = True
            com_sprite += 1 if has else 0
            for a, _ in th.attrs:
                attr_count[ATTR_LABEL.get(a, a)] += 1
        used |= sprite_ids
        print("%-9s %6d things  ids %d..%d  com sprite: %d  sprite ids distintos: %d"
              % (S.CATEGORY_NAMES[cat], len(t), ids[0], ids[-1], com_sprite, len(sprite_ids)))
        print("          tamanhos %s  camadas %s  fases %s"
              % (dict(sizes), dict(layers), dict(phases)))
        print("          atributos mais comuns: %s" % attr_count.most_common(8))
    print()
    print("sprites referenciados por algum thing: %d de %d (%.1f%%)"
          % (len(used), spr["count"], 100.0 * len(used) / max(1, spr["count"])))
    orfaos = [i for i in range(1, spr["count"] + 1) if i not in used]
    if orfaos:
        print("sprites orfaos: %d (primeiros: %s)" % (len(orfaos), orfaos[:10]))

    # ------------------------------------------------------------ validacoes
    problemas = []
    conhecidos = set(ATTR_LABEL)
    for cat in range(4):
        for th in tables[cat].values():
            total = 0
            for a, _ in th.attrs:
                if a not in conhecidos:
                    problemas.append("%s %d: atributo desconhecido %d"
                                     % (S.CATEGORY_NAMES[cat], th.id, a))
            for g in th.groups:
                total += len(g.sprites)
                for sp in g.sprites:
                    if sp > spr["count"]:
                        problemas.append("%s %d: sprite id %d > total do .spr (%d)"
                                         % (S.CATEGORY_NAMES[cat], th.id, sp, spr["count"]))
                if (g.width > 1 or g.height > 1) and not (1 <= g.exact_size <= 255):
                    problemas.append("%s %d: exactSize invalido" % (S.CATEGORY_NAMES[cat], th.id))
            if total > 4096:
                problemas.append("%s %d: %d sprites (limite do cliente e 4096)"
                                 % (S.CATEGORY_NAMES[cat], th.id, total))
    # Conferencia item a item contra o items.otb. O TFS decide os bytes extras do
    # pacote pelo OTB (networkmessage.cpp addItem) e o cliente decide quantos ler
    # pelo .dat (protocolgameparse.cpp getItem). Divergir = pacote desalinhado.
    otb_path = args.otb if os.path.isabs(args.otb) else os.path.join(ROOT, args.otb)
    if os.path.exists(otb_path):
        _, otb_items = parse_items_otb(otb_path)
        by_cid = {}
        for it in otb_items:
            if it["client_id"] and it["client_id"] not in by_cid:
                by_cid[it["client_id"]] = it
        div = {"stackable": 0, "fluid": 0, "splash": 0, "animation": 0, "sem_thing": 0}
        for cid, it in by_cid.items():
            th = tables[S.CATEGORY_ITEM].get(cid)
            if th is None:
                div["sem_thing"] += 1
                continue
            attrs = {a for a, _ in th.attrs}
            quer = {
                "stackable": bool(it["flags"] & FLAG_STACKABLE),
                "fluid": it["group_name"] == "fluid",
                "splash": it["group_name"] == "splash",
                "animation": bool(it["flags"] & FLAG_ANIMATION),
            }
            tem = {
                "stackable": S.A_STACKABLE in attrs,
                "fluid": S.A_FLUID_CONTAINER in attrs,
                "splash": S.A_SPLASH in attrs,
                "animation": th.groups[0].phases > 1,
            }
            for k in quer:
                if quer[k] != tem[k]:
                    div[k] += 1
                    problemas.append("item %d: %s otb=%s dat=%s" % (cid, k, quer[k], tem[k]))
        print("\nconferencia contra %s (%d clientIds):" % (os.path.relpath(otb_path, ROOT), len(by_cid)))
        for k in ("stackable", "fluid", "splash", "animation"):
            n = sum(1 for it in by_cid.values()
                    if (bool(it["flags"] & FLAG_STACKABLE) if k == "stackable" else
                        it["group_name"] == "fluid" if k == "fluid" else
                        it["group_name"] == "splash" if k == "splash" else
                        bool(it["flags"] & FLAG_ANIMATION)))
            print("   %-10s otb=%-6d divergencias=%d" % (k, n, div[k]))
        if div["sem_thing"]:
            print("   !! %d clientIds do OTB sem thing no .dat" % div["sem_thing"])

    print("\nvalidacao: %s" % ("OK" if not problemas else "%d problema(s)" % len(problemas)))
    for msg in problemas[:20]:
        print("  !! %s" % msg)

    for spec in args.thing:
        cname, _, sid = spec.partition(":")
        cat = S.CATEGORY_NAMES.index(cname)
        th = tables[cat].get(int(sid))
        if not th:
            print("!! %s nao existe" % spec)
            continue
        print("\n-- %s --\n%s" % (spec, describe(th)))
        print("   sprite ids: %s" % th.groups[0].sprites[:16])

    if args.export:
        from PIL import Image
        outdir = args.export_dir or os.path.join(ROOT, "assets-src", "sprites", "_dump")
        os.makedirs(outdir, exist_ok=True)
        step = max(1, spr["count"] // args.export)
        n = 0
        for sid in range(1, spr["count"] + 1, step):
            px = S.spr_get_sprite(spr, sid)
            if px is None:
                continue
            img = Image.frombytes("RGBA", (32, 32), bytes(px))
            img.save(os.path.join(outdir, "sprite_%05d.png" % sid))
            n += 1
            if n >= args.export:
                break
        print("\n%d sprites exportados em %s" % (n, outdir))


if __name__ == "__main__":
    main()
