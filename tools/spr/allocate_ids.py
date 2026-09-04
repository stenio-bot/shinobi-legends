#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aloca (server_id, client_id) para as keys de tiles.json SEM construir nada.

`build_assets.py` faz isso como efeito colateral de reescrever o `items.otb`, o
`Tibia.dat` e o `Tibia.spr`. Às vezes só queremos os IDS — por exemplo para o
`tools/map/build_valley.py` conseguir estampar os prédios importados antes de o
OTB ser regravado (ou enquanto outra pessoa está rodando o build de assets).

Este script:
  * lê `assets-src/sprites/tiles.json`;
  * lê/atualiza `assets-src/sprites/allocations.json`, seguindo EXATAMENTE a
    mesma regra sequencial de `tools/spr/tiles.py::allocate` (append-only,
    server id a partir de 30000, client id a partir de 23726, nunca renumera);
  * NÃO toca no `items.otb`, no `.dat`/`.spr` nem no `items.xml`.

Diferença deliberada em relação a `tiles.py::allocate`: aquele recebe a lista de
itens do `items.otb` para evitar colisão. Aqui o `items.otb` NÃO é lido — ele
pode estar sendo reescrito neste exato momento por `build_assets.py`. Como o OTB
vanilla vai até o server id 26381 e os client ids até 23725, e as bases são
30000/23726, não há colisão possível.

    .venv/bin/python tools/spr/allocate_ids.py
    .venv/bin/python tools/spr/allocate_ids.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TILES_JSON = os.path.join(ROOT, "assets-src", "sprites", "tiles.json")
ALLOC_JSON = os.path.join(ROOT, "assets-src", "sprites", "allocations.json")

DOC = ("Alocacao PERMANENTE de ids para os tiles de "
       "assets-src/sprites/tiles.json. Nunca edite nem apague uma entrada: o id "
       "ficaria orfao em mapas e saves ja gravados. Gerado por "
       "tools/spr/build_assets.py ou tools/spr/allocate_ids.py.")


def load_alloc(cfg):
    alloc = {"format": 1, "_doc": DOC,
             "next_server_id": cfg.get("server_id_base", 30000),
             "next_client_id": cfg.get("client_id_base", 23726),
             "by_key": {}}
    if os.path.exists(ALLOC_JSON):
        with open(ALLOC_JSON, encoding="utf-8") as fh:
            disco = json.load(fh)
        alloc["next_server_id"] = disco.get("next_server_id", alloc["next_server_id"])
        alloc["next_client_id"] = disco.get("next_client_id", alloc["next_client_id"])
        alloc["by_key"] = dict(disco.get("by_key", {}))
    return alloc


def allocate(cfg, alloc):
    usados_sid = {e["server_id"] for e in alloc["by_key"].values()}
    usados_cid = {e["client_id"] for e in alloc["by_key"].values()}
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
    return novas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(TILES_JSON, encoding="utf-8") as fh:
        cfg = json.load(fh)
    alloc = load_alloc(cfg)
    antes = len(alloc["by_key"])
    novas = allocate(cfg, alloc)

    print("tiles.json: %d tiles" % len(cfg["tiles"]))
    print("allocations.json: %d keys antes, %d depois (+%d)"
          % (antes, len(alloc["by_key"]), len(novas)))
    if novas:
        print("  server ids %d..%d   client ids %d..%d"
              % (novas[0][1], novas[-1][1], novas[0][2], novas[-1][2]))
    if args.dry_run:
        print("(--dry-run: nada gravado)")
        return 0

    alloc["_doc"] = DOC
    with open(ALLOC_JSON, "w", encoding="utf-8") as fh:
        json.dump(alloc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("gravado:", ALLOC_JSON)
    print("LEMBRE: os ids so passam a existir no items.otb/.dat/.spr depois de")
    print("        .venv/bin/python tools/spr/build_assets.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
