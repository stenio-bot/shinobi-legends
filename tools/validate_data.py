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

characters = load(os.path.join(ROOT, "characters.json"))
char_ids = set()
char_schema = load(os.path.join(ROOT, "schemas", "character.schema.json"))
for c in characters:
    if V:
        for e in V(char_schema).iter_errors(c):
            errors.append(f"data/characters.json [{c.get('id','?')}]: {e.message}")
    if c["id"] in char_ids: errors.append(f"characters.json: id duplicado '{c['id']}'")
    char_ids.add(c["id"])

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
jutsu_by_id = {j["id"]: j for j in jutsus}

# element_sets.json: 4 jutsus por elemento, existentes, unicos, do elemento certo.
# NOTA (novo modelo personagem+elemento): vila nao filtra mais jutsu, entao aqui so
# validamos que o set pertence ao elemento certo, nao a vila.
element_sets = load(os.path.join(ROOT, "element_sets.json"))
element_set_schema = load(os.path.join(ROOT, "schemas", "element_set.schema.json"))
valid_elements = {"katon", "suiton", "doton", "fuuton", "raiton"}
element_set_ids = set()
for es in element_sets:
    if V:
        for e in V(element_set_schema).iter_errors(es):
            errors.append(f"data/element_sets.json [{es.get('id','?')}]: {e.message}")
    if es["id"] in element_set_ids:
        errors.append(f"element_sets.json: id duplicado '{es['id']}'")
    element_set_ids.add(es["id"])
    jids = es.get("jutsus", [])
    if len(jids) != 4:
        errors.append(f"element_set {es['id']}: precisa de exatamente 4 jutsus (tem {len(jids)})")
    if len(set(jids)) != len(jids):
        errors.append(f"element_set {es['id']}: jutsus duplicados em {jids}")
    for jid in jids:
        if jid not in jutsu_ids:
            errors.append(f"element_set {es['id']}: jutsu desconhecido '{jid}'")
            continue
        jel = jutsu_by_id[jid]["element"]
        if jel != es["id"]:
            errors.append(f"element_set {es['id']}: jutsu '{jid}' tem elemento '{jel}', esperado '{es['id']}'")
for el in valid_elements:
    if el not in element_set_ids:
        errors.append(f"element_sets.json: falta o set do elemento '{el}'")

# characters.json: 4 personal_jutsus por personagem, existentes e unicos.
# 'jutsus' (alias legado lido por tools/export_tfs.py) deve ter o mesmo conteudo.
for c in characters:
    if c["village"] not in village_ids:
        errors.append(f"personagem {c['id']}: vila desconhecida '{c['village']}'")
    pj = c.get("personal_jutsus", [])
    if len(pj) != 4:
        errors.append(f"personagem {c['id']}: precisa de exatamente 4 personal_jutsus (tem {len(pj)})")
    if len(set(pj)) != len(pj):
        errors.append(f"personagem {c['id']}: personal_jutsus duplicados em {pj}")
    for jid in pj:
        if jid not in jutsu_ids:
            errors.append(f"personagem {c['id']}: jutsu desconhecido '{jid}'")
    if "jutsus" in c and c["jutsus"] != pj:
        errors.append(f"personagem {c['id']}: campo legado 'jutsus' diverge de 'personal_jutsus'")

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

# ids de todos os NPCs (para validar data/tasks.json 'npc' e checagens gerais)
npc_ids = set()
for path in glob.glob(os.path.join(ROOT, "npcs", "*.json")):
    for n in load(path):
        npc_ids.add(n["id"])

# data/ranks.json (docs/lore/progressao.md): progressão Genin->Kage. Documentário + consumido
# por tools/export_tfs.py (NarutoRanks). Valida contra rank.schema.json e referências de área.
ranks_path = os.path.join(ROOT, "ranks.json")
rank_ids = set()
if os.path.exists(ranks_path):
    ranks = load(ranks_path)
    rank_schema = load(os.path.join(ROOT, "schemas", "rank.schema.json"))
    for r in ranks:
        if V:
            for e in V(rank_schema).iter_errors(r):
                errors.append(f"data/ranks.json [{r.get('rank','?')}]: {e.message}")
        if r["rank"] in rank_ids:
            errors.append(f"ranks.json: rank duplicado '{r['rank']}'")
        rank_ids.add(r["rank"])
    RANK_ORDER = ["genin", "chunin", "jonin", "anbu", "kage"]
    if sorted(rank_ids) != sorted(RANK_ORDER) or len(ranks) != len(RANK_ORDER):
        errors.append(f"ranks.json: esperado exatamente {RANK_ORDER}, achou {sorted(rank_ids)}")

# grants_rank / grants_rank_progress nas quests dos NPCs devem apontar para um rank válido
for path in glob.glob(os.path.join(ROOT, "npcs", "*.json")):
    for n in load(path):
        for q in n.get("quests", []):
            for field in ("grants_rank", "grants_rank_progress"):
                r = q.get(field)
                if r and rank_ids and r not in rank_ids:
                    errors.append(f"quest {q['id']}: {field} desconhecido '{r}'")
            obj = q.get("objective", {})
            if obj.get("kind") == "keyword_quiz":
                quiz = obj.get("quiz", [])
                if len(quiz) < 1:
                    errors.append(f"quest {q['id']}: keyword_quiz sem perguntas em objective.quiz")
                for i, qq in enumerate(quiz):
                    if not qq.get("keywords"):
                        errors.append(f"quest {q['id']}: pergunta {i+1} do quiz sem 'keywords'")

# data/tasks.json (docs/sistemas/progressao-servidor.md): tarefas repetíveis estilo Tibia tasks.
# Arquivo opcional (tools/export_tfs.py ignora o sistema de tarefas se não existir).
tasks_path = os.path.join(ROOT, "tasks.json")
if os.path.exists(tasks_path):
    tasks = load(tasks_path)
    task_schema = load(os.path.join(ROOT, "schemas", "task.schema.json"))
    task_ids = set()
    for t in tasks:
        if V:
            for e in V(task_schema).iter_errors(t):
                errors.append(f"data/tasks.json [{t.get('id','?')}]: {e.message}")
        if t["id"] in task_ids:
            errors.append(f"tasks.json: id duplicado '{t['id']}'")
        task_ids.add(t["id"])
        if t.get("npc") and t["npc"] not in npc_ids:
            errors.append(f"task {t['id']}: npc desconhecido '{t['npc']}'")
        if t.get("monster_id") and t["monster_id"] not in monster_ids:
            errors.append(f"task {t['id']}: monstro desconhecido '{t['monster_id']}'")
        for i in t.get("reward", {}).get("items", []):
            if i not in item_ids:
                errors.append(f"task {t['id']}: item de recompensa desconhecido '{i}'")

# data/dailies.json (docs/sistemas/progressao-servidor.md): pool de missões diárias por faixa de level.
dailies_path = os.path.join(ROOT, "dailies.json")
if os.path.exists(dailies_path):
    dailies = load(dailies_path)
    daily_schema = load(os.path.join(ROOT, "schemas", "daily.schema.json"))
    daily_ids = set()
    for d in dailies:
        if V:
            for e in V(daily_schema).iter_errors(d):
                errors.append(f"data/dailies.json [{d.get('id','?')}]: {e.message}")
        if d["id"] in daily_ids:
            errors.append(f"dailies.json: id duplicado '{d['id']}'")
        daily_ids.add(d["id"])
        if d.get("monster_id") and d["monster_id"] not in monster_ids:
            errors.append(f"daily {d['id']}: monstro desconhecido '{d['monster_id']}'")
        if d.get("level_min", 1) > d.get("level_max", 1):
            errors.append(f"daily {d['id']}: level_min > level_max")
        for i in d.get("reward", {}).get("items", []):
            if i not in item_ids:
                errors.append(f"daily {d['id']}: item de recompensa desconhecido '{i}'")

# data/achievements.json: conquistas (kills, missões, exames, exploração). Só dados
# nesta missão de conteúdo (o servidor ainda não concede conquistas) — validação aditiva
# de schema + referências que já existem (npc/monstro/rank), sem exigir o arquivo.
achievements_path = os.path.join(ROOT, "achievements.json")
if os.path.exists(achievements_path):
    achievements = load(achievements_path)
    achievement_schema = load(os.path.join(ROOT, "schemas", "achievement.schema.json"))
    achievement_ids = set()
    for a in achievements:
        if V:
            for e in V(achievement_schema).iter_errors(a):
                errors.append(f"data/achievements.json [{a.get('id','?')}]: {e.message}")
        if a["id"] in achievement_ids:
            errors.append(f"achievements.json: id duplicado '{a['id']}'")
        achievement_ids.add(a["id"])
        cond = a.get("condition", {})
        target = cond.get("target")
        if cond.get("kind") == "kill_specific" and target and target not in monster_ids:
            errors.append(f"achievement {a['id']}: monstro desconhecido '{target}'")
        if cond.get("kind") == "quest_chain_complete" and target and target not in npc_ids:
            errors.append(f"achievement {a['id']}: npc desconhecido '{target}'")
        if cond.get("kind") == "grants_rank" and target and rank_ids and target not in rank_ids:
            errors.append(f"achievement {a['id']}: rank desconhecido '{target}'")

print(f"{len(jutsus)} jutsus, {len(items)} itens, {len(monsters)} monstros, {len(villages)} vilas, {len(characters)} personagens, {len(element_sets)} sets elementais")
if os.path.exists(ranks_path): print(f"{len(rank_ids)} ranks")
if os.path.exists(tasks_path): print(f"{len(task_ids)} tarefas")
if os.path.exists(dailies_path): print(f"{len(daily_ids)} diárias (pool)")
if os.path.exists(achievements_path): print(f"{len(achievement_ids)} conquistas")
if errors:
    print("\n".join("ERRO " + e for e in errors)); sys.exit(1)
print("OK — tudo válido")
