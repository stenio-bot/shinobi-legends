#!/usr/bin/env python3
"""Valida todo o conteúdo em data/ contra os schemas e checa referências cruzadas.
Uso: python3 tools/validate_data.py
Requer: pip install jsonschema  (sem ele, faz só checagens básicas)
"""
import json, sys, glob, os
ROOT = os.path.join(os.path.dirname(__file__), "..", "data")
errors = []

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

try:
    from jsonschema import Draft202012Validator as V
except ImportError:
    V = None
    print("aviso: jsonschema não instalado (pip install jsonschema); validando só referências")

def validate_folder(folder, schema_name):
    schema = load(os.path.join(ROOT, "schemas", schema_name))
    items, ids = [], set()
    for path in sorted(glob.glob(os.path.join(ROOT, folder, "*.json"))):
        for obj in load(path):
            if V:
                for e in V(schema).iter_errors(obj):
                    errors.append(f"{path} [{obj.get('id','?')}]: {e.message}")
            if obj["id"] in ids:
                errors.append(f"{path}: id duplicado '{obj['id']}'")
            ids.add(obj["id"]); items.append(obj)
    return items, ids

jutsus, jutsu_ids = validate_folder("jutsus", "jutsu.schema.json")
items, item_ids = validate_folder("items", "item.schema.json")
monsters, monster_ids = validate_folder("monsters", "monster.schema.json")
villages = load(os.path.join(ROOT, "villages.json"))
village_ids = {v["id"] for v in villages}

for j in jutsus:
    for v in j["villages"]:
        if v not in village_ids: errors.append(f"jutsu {j['id']}: vila desconhecida '{v}'")
for it in items:
    if it.get("teaches_jutsu") and it["teaches_jutsu"] not in jutsu_ids:
        errors.append(f"item {it['id']}: jutsu desconhecido '{it['teaches_jutsu']}'")
    if it.get("required_village") and it["required_village"] not in village_ids:
        errors.append(f"item {it['id']}: vila desconhecida '{it['required_village']}'")
    if it["type"] in ("weapon","armor","accessory") and "slot" not in it:
        errors.append(f"item {it['id']}: equipamento sem slot")
for m in monsters:
    for l in m["loot"]:
        if l["item_id"] not in item_ids: errors.append(f"monstro {m['id']}: item desconhecido '{l['item_id']}'")
    for ph in m.get("phases", []):
        for s in ph.get("summons", []):
            if s["monster_id"] not in monster_ids: errors.append(f"monstro {m['id']}: summon desconhecido '{s['monster_id']}'")
    if m["ryo_min"] > m["ryo_max"]: errors.append(f"monstro {m['id']}: ryo_min > ryo_max")
for v in villages:
    for j in v["starting_jutsus"]:
        if j not in jutsu_ids: errors.append(f"vila {v['id']}: jutsu desconhecido '{j}'")
    for i in v["starting_items"]:
        if i not in item_ids: errors.append(f"vila {v['id']}: item desconhecido '{i}'")
for path in glob.glob(os.path.join(ROOT, "npcs", "*.json")):
    for n in load(path):
        for i in n.get("sells", []):
            if i not in item_ids: errors.append(f"npc {n['id']}: item desconhecido '{i}'")
        for q in n.get("quests", []):
            k = q["objective"].get("kill")
            if k and k not in monster_ids: errors.append(f"quest {q['id']}: monstro desconhecido '{k}'")

for path in glob.glob(os.path.join(ROOT, "maps", "*.json")):
    m = load(path)
    for sp in m["spawns"]:
        if sp["monster_id"] not in monster_ids: errors.append(f"mapa {m['id']}: monstro desconhecido '{sp['monster_id']}'")
        if not (0 <= sp["x"] < m["width"] and 0 <= sp["y"] < m["height"]): errors.append(f"mapa {m['id']}: spawn fora do mapa {sp}")
for path in glob.glob(os.path.join(ROOT, "npcs", "*.json")):
    for n in load(path):
        for q in n.get("quests", []):
            for i in q["reward"].get("items", []):
                if i not in item_ids: errors.append(f"quest {q['id']}: item de recompensa desconhecido '{i}'")

print(f"{len(jutsus)} jutsus, {len(items)} itens, {len(monsters)} monstros, {len(villages)} vilas")
if errors:
    print("\n".join("ERRO " + e for e in errors)); sys.exit(1)
print("OK — tudo válido")
