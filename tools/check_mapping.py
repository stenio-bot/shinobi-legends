#!/usr/bin/env python3
"""Checa a consistência de data/tfs_mapping.json (seção `items`) contra data/items/*.json.

Falha (exit 1) se:
  - algum item de data/items/*.json não tiver entrada em tfs_mapping.json['items'];
  - algum id do Tibia vanilla em tfs_mapping.json['items'] estiver duplicado (dois dos
    nossos itens compartilhando o mesmo id vanilla — o exportador emitiria dois <item>
    com o mesmo id no items.xml, e o TFS usaria só o último).

Uso: python3 tools/check_mapping.py
"""
import json, sys, glob, os
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data")

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

errors = []

mapping = load(os.path.join(DATA, "tfs_mapping.json"))
item_map = mapping.get("items", {})

# --- 1) todo item de data/items/*.json precisa ter entrada no mapping ---------------
all_item_ids = []
for path in sorted(glob.glob(os.path.join(DATA, "items", "*.json"))):
    for obj in load(path):
        all_item_ids.append((obj["id"], path))

seen = set()
for our_id, path in all_item_ids:
    if our_id in seen:
        errors.append(f"{path}: id de item duplicado em data/items '{our_id}'")
        continue
    seen.add(our_id)
    if our_id not in item_map:
        errors.append(f"{path}: item '{our_id}' sem entrada em data/tfs_mapping.json (seção 'items')")

# --- 2) nenhum id vanilla pode ser reaproveitado por dois itens nossos --------------
by_vanilla_id = defaultdict(list)
for our_id, vanilla_id in item_map.items():
    by_vanilla_id[int(vanilla_id)].append(our_id)

for vanilla_id, our_ids in sorted(by_vanilla_id.items()):
    if len(our_ids) > 1:
        errors.append(
            f"id vanilla {vanilla_id} duplicado entre os nossos itens: {', '.join(sorted(our_ids))}"
        )

if errors:
    print(f"FALHOU — {len(errors)} problema(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"OK — {len(seen)} itens de data/items/*.json, todos mapeados em data/tfs_mapping.json "
      f"({len(item_map)} entradas, {len(by_vanilla_id)} ids vanilla únicos).")
