#!/usr/bin/env python3
"""Round-trip do items.otb: ler + reescrever precisa dar o MESMO arquivo.

    .venv/bin/python tools/spr/test_otb_roundtrip.py
    .venv/bin/python tools/spr/test_otb_roundtrip.py --otb outro/items.otb

Compara (a) byte a byte e (b) campo a campo os dois parses. Sai com codigo 0 se
tudo bate. Tambem testa que build_item_props/build_root_props reconstroem props
equivalentes aos originais (mesmos campos apos o parse), o caminho usado pelos
itens novos.
"""
import argparse
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import otb  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CAMPOS = ("group", "group_name", "flags", "server_id", "client_id", "speed",
          "light_level", "light_color", "top_order", "minimap_color", "ware_id",
          "name", "sprite_hash")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--otb", default="server/tfs/data/items/items.otb")
    args = ap.parse_args()
    path = os.path.join(ROOT, args.otb)
    if not os.path.exists(path):
        print("nao encontrei %s" % path)
        return 1

    header, items = otb.parse_items_otb(path)
    print("origem: %s" % path)
    print("header: otb v%d, client %d, build %d, %d itens"
          % (header["major"], header["minor"], header["build"], len(items)))

    falhas = 0
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "items.otb")
        otb.write_items_otb(out, items, header)

        a = open(path, "rb").read()
        b = open(out, "rb").read()
        if a == b:
            print("[1] byte a byte: IDENTICO (%d bytes)" % len(a))
        else:
            falhas += 1
            print("[1] byte a byte: DIVERGE (orig=%d bytes, novo=%d bytes)"
                  % (len(a), len(b)))
            for i in range(min(len(a), len(b))):
                if a[i] != b[i]:
                    print("    primeiro byte diferente em 0x%X: %02X != %02X"
                          % (i, a[i], b[i]))
                    break

        header2, items2 = otb.parse_items_otb(out)
        if len(items) != len(items2):
            falhas += 1
            print("[2] campo a campo: contagem diferente %d != %d"
                  % (len(items), len(items2)))
        else:
            diffs = 0
            for x, y in zip(items, items2):
                for c in CAMPOS:
                    if x[c] != y[c]:
                        diffs += 1
                        if diffs <= 10:
                            print("    item sid=%s campo %s: %r != %r"
                                  % (x["server_id"], c, x[c], y[c]))
            for c in ("major", "minor", "build", "csd_version", "root_type",
                      "identifier"):
                if header[c] != header2[c]:
                    diffs += 1
                    print("    header %s: %r != %r" % (c, header[c], header2[c]))
            if diffs:
                falhas += 1
                print("[2] campo a campo: %d divergencias" % diffs)
            else:
                print("[2] campo a campo: OK (%d itens x %d campos)"
                      % (len(items), len(CAMPOS)))

        # [3] serializacao "do zero": descarta raw_props e confere que os
        # campos que o TFS le sobrevivem. Nao e byte a byte (o original tem
        # atributos que nao reserializamos, ex. DESCR), mas e o caminho dos
        # itens novos.
        rebuild = []
        for it in items:
            n = dict(it)
            n["raw_props"] = None
            rebuild.append(n)
        out2 = os.path.join(tmp, "items_rebuild.otb")
        h2 = dict(header)
        h2["raw_props"] = None
        otb.write_items_otb(out2, rebuild, h2)
        header3, items3 = otb.parse_items_otb(out2)
        lidos = ("group", "flags", "server_id", "client_id", "speed",
                 "light_level", "light_color", "top_order", "ware_id")
        diffs = 0
        for x, y in zip(items, items3):
            for c in lidos:
                if x[c] != y[c]:
                    diffs += 1
                    if diffs <= 10:
                        print("    rebuild sid=%s campo %s: %r != %r"
                              % (x["server_id"], c, x[c], y[c]))
        for c in ("major", "minor", "build", "csd_version"):
            if header[c] != header3[c]:
                diffs += 1
                print("    rebuild header %s: %r != %r" % (c, header[c], header3[c]))
        if diffs:
            falhas += 1
            print("[3] serializacao do zero: %d divergencias" % diffs)
        else:
            print("[3] serializacao do zero: OK (campos lidos por "
                  "Items::loadFromOtb preservados em %d itens)" % len(items))

    print("RESULTADO: %s" % ("OK" if falhas == 0 else "%d FALHA(S)" % falhas))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
