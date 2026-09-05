#!/usr/bin/env python3
"""Gera conteúdo do The Forgotten Server 1.4.2 a partir de data/*.json.
Saída em server/generated/ (copie para server/tfs/data/ conforme docs/04-setup-ot.md).
Uso: python3 tools/export_tfs.py
"""
import json, os, glob, shutil, math, unicodedata
from xml.sax.saxutils import escape

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "server", "generated")
HEADER_XML = "<!-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO. -->\n"
HEADER_LUA = "-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.\n"

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def load_folder(folder):
    out = {}
    for p in sorted(glob.glob(os.path.join(DATA, folder, "*.json"))):
        for o in load(p):
            out[o["id"]] = o
    return out

def write(rel, text):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)

M = load(os.path.join(DATA, "tfs_mapping.json"))
jutsus = load_folder("jutsus")
items = load_folder("items")
monsters = load_folder("monsters")
npcs = load_folder("npcs")
villages = {v["id"]: v for v in load(os.path.join(DATA, "villages.json"))}
elements = load(os.path.join(DATA, "elements.json"))
prog = load(os.path.join(DATA, "progression.json"))
maps = {m["id"]: m for m in (load(p) for p in glob.glob(os.path.join(DATA, "maps", "*.json")))}
characters = load(os.path.join(DATA, "characters.json"))

# Jutsus universais (needlearn="0"): conhecidos por qualquer personagem, sem precisar estar no
# kit do personagem atual. Todo o resto exige learnSpell (ver naruto_characters.lua/character_switch.lua).
UNIVERSAL_JUTSU_IDS = {"kawarimi"}

WARNINGS = []

# ---------------------------------------------------------------- modelo personagem + elemento
# Ao entrar, o jogador escolhe PERSONAGEM (4 jutsus pessoais) e ELEMENTO (4 jutsus do set).
# Jutsus elementais NÃO são mais filtrados por vila.
PERSONAL_JUTSU_COUNT = 4
ELEMENT_JUTSU_COUNT = 4
ELEMENT_ORDER = ["katon", "suiton", "raiton", "doton", "fuuton"]
ELEMENT_NAMES = {
    "katon": "Katon (Fogo)", "suiton": "Suiton (Água)", "raiton": "Raiton (Raio)",
    "doton": "Doton (Terra)", "fuuton": "Fuuton (Vento)",
}

def personal_jutsu_ids(c):
    """data/characters.json: campo `personal_jutsus` (novo) ou `jutsus` (legado)."""
    ids = c.get("personal_jutsus") or c.get("jutsus") or []
    ids = [jid for jid in ids if jid in jutsus]
    if len(ids) > PERSONAL_JUTSU_COUNT:
        WARNINGS.append(f"personagem {c['id']} tem {len(ids)} jutsus pessoais; usando os {PERSONAL_JUTSU_COUNT} primeiros")
        ids = ids[:PERSONAL_JUTSU_COUNT]
    elif len(ids) < PERSONAL_JUTSU_COUNT:
        WARNINGS.append(f"personagem {c['id']} tem só {len(ids)} jutsus pessoais (esperado {PERSONAL_JUTSU_COUNT})")
    return ids

def default_element_of(c):
    """`default_element` do JSON; senão o elemento mais frequente entre os jutsus pessoais;
    senão o elemento da vila."""
    el = c.get("default_element")
    if el in ELEMENT_ORDER:
        return el
    counts = {}
    for jid in personal_jutsu_ids(c):
        e = jutsus[jid].get("element", "none")
        if e in ELEMENT_ORDER:
            counts[e] = counts.get(e, 0) + 1
    if counts:
        return max(sorted(counts), key=lambda e: counts[e])
    return villages[c["village"]].get("element", ELEMENT_ORDER[0])

def load_element_sets():
    """data/element_sets.json: [{id, name, jutsus: [4 ids]}]. Se o arquivo ainda não existir
    (outro agente está criando), gera um placeholder: os jutsus do elemento por level, e se
    faltar completa com os neutros (element == 'none')."""
    p = os.path.join(DATA, "element_sets.json")
    if os.path.exists(p):
        sets = {s["id"]: s for s in load(p)}
        out = []
        for eid in ELEMENT_ORDER:
            s = sets.get(eid)
            if not s:
                WARNINGS.append(f"element_sets.json sem o elemento '{eid}'")
                continue
            ids = [jid for jid in s.get("jutsus", []) if jid in jutsus]
            if len(ids) != ELEMENT_JUTSU_COUNT:
                WARNINGS.append(f"element_sets.json: '{eid}' tem {len(ids)} jutsus válidos (esperado {ELEMENT_JUTSU_COUNT})")
            out.append({"id": eid, "name": s.get("name") or ELEMENT_NAMES[eid], "jutsus": ids})
        return out
    WARNINGS.append("data/element_sets.json NÃO existe: gerando sets PLACEHOLDER a partir de "
                    "data/jutsus/*.json (complete com o arquivo real e regenere)")
    def by_level(js):
        return sorted(js, key=lambda j: (int(j.get("tier", 1)), int(j["required_level"]), j["id"]))
    neutral = by_level([j for j in jutsus.values() if j.get("element", "none") == "none"])
    out = []
    for eid in ELEMENT_ORDER:
        own = by_level([j for j in jutsus.values() if j.get("element") == eid])
        picked = [j["id"] for j in own[:ELEMENT_JUTSU_COUNT]]
        for j in neutral:
            if len(picked) >= ELEMENT_JUTSU_COUNT:
                break
            if j["id"] not in picked:
                picked.append(j["id"])
        out.append({"id": eid, "name": ELEMENT_NAMES[eid], "jutsus": picked})
    return out

element_sets = load_element_sets()

def item_id(our_id):
    return int(M["items"].get(our_id, 0))

# Ids que o items.xml original do TFS já usa. O mapping (data/tfs_mapping.json, de outro
# agente) reaproveita ids vanilla como placeholder; se emitirmos uma segunda <item> com o
# mesmo id o TFS avisa "Duplicate item with id" e o item vanilla vence. Então pulamos esses
# ids aqui e listamos no aviso final.
VANILLA_ITEMS_XML = os.path.join(ROOT, "server", "tfs", "data", "items", "items.xml")
SKIPPED_ITEM_IDS = []

def vanilla_item_ids():
    """Ids declarados no items.xml do TFS, ignorando o nosso bloco NARUTO:BEGIN/END."""
    if not os.path.exists(VANILLA_ITEMS_XML):
        return set()
    import re as _re
    with open(VANILLA_ITEMS_XML, encoding="utf-8", errors="surrogateescape") as f:
        raw = f.read()
    raw = _re.sub(r"<!-- NARUTO:BEGIN -->.*?<!-- NARUTO:END -->", "", raw, flags=_re.S)
    ids = set()
    for m in _re.finditer(r'<item\b[^>]*?\bid="(\d+)"', raw):
        ids.add(int(m.group(1)))
    for m in _re.finditer(r'<item\b[^>]*?\bfromid="(\d+)"[^>]*?\btoid="(\d+)"', raw):
        a, b = int(m.group(1)), int(m.group(2))
        if b - a <= 5000:
            ids.update(range(a, b + 1))
    return ids

VANILLA_ITEM_IDS = vanilla_item_ids()

def voc_name(vid):
    return villages[vid]["name"]

# ---------------------------------------------------------------- áreas
def area_matrix(shape):
    """Matriz TFS (0 vazio, 1 afetado, 2 centro sem dano, 3 centro com dano) virada para o norte."""
    kind, n = shape.split("_")[0], int(shape.split("_")[1].lstrip("r"))
    if kind == "circle":
        size = 2 * n + 1
        m = [[1] * size for _ in range(size)]
        m[n][n] = 2
        return m
    if kind == "cross":
        size = 2 * n + 1
        m = [[0] * size for _ in range(size)]
        for i in range(size):
            m[n][i] = 1
            m[i][n] = 1
        m[n][n] = 2
        return m
    if kind == "line":
        m = [[1] for _ in range(n)] + [[2]]
        return m
    if kind == "cone":
        width = 2 * n - 1
        m = []
        for k in range(n, 0, -1):  # linha mais longe primeiro
            row = [0] * width
            half = k - 1
            for w in range(-half, half + 1):
                row[n - 1 + w] = 1
            m.append(row)
        last = [0] * width
        last[n - 1] = 2
        m.append(last)
        return m
    return [[3]]

def area_lua(shape):
    m = area_matrix(shape)
    rows = ",\n".join("\t{" + ", ".join(str(v) for v in row) + "}" for row in m)
    return "{\n" + rows + "\n}"

# ---------------------------------------------------------------- monstros
def speed_from_tiles(tps):
    return int(round(tps * 100))

def element_percents(el):
    """Nosso ciclo: quem vem antes no ciclo causa 150%, quem vem depois causa 75%."""
    order = elements["order"]
    if el not in order:
        return {}
    i = order.index(el)
    prev_el = order[(i - 1) % len(order)]
    next_el = order[(i + 1) % len(order)]
    return {M["elements"][prev_el]["xml"]: -50, M["elements"][next_el]["xml"]: 25}

def monster_xml(m):
    mp = M["monsters"].get(m["id"], {"looktype": 128, "corpse": 3058, "race": "blood"})
    look = f'<look type="{mp["looktype"]}"'
    for k in ("head", "body", "legs", "feet", "addons"):
        if k in mp:
            look += f' {k}="{mp[k]}"'
    look += f' corpse="{mp["corpse"]}"/>'
    hostile = 0 if m["behavior"] == "passive" else 1
    targetdist = m["attack_range"] if m["behavior"] == "ranged" else 1
    runonhealth = int(m["hp"] * 0.2) if m["behavior"] == "cowardly" else 0
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', HEADER_XML.rstrip("\n"),
             f'<monster name="{escape(m["name"])}" nameDescription="{escape(m.get("article", "um") + " " + m["name"].lower())}" race="{mp["race"]}" experience="{m["xp"]}" speed="{speed_from_tiles(m["speed"])}" manacost="0">',
             f'\t<health now="{m["hp"]}" max="{m["hp"]}"/>', f'\t{look}',
             '\t<targetchange interval="4000" chance="10"/>', '\t<flags>',
             f'\t\t<flag summonable="0"/>\n\t\t<flag attackable="1"/>\n\t\t<flag hostile="{hostile}"/>\n\t\t<flag illusionable="0"/>\n\t\t<flag convinceable="0"/>\n\t\t<flag pushable="0"/>\n\t\t<flag canpushitems="1"/>\n\t\t<flag canpushcreatures="0"/>\n\t\t<flag targetdistance="{targetdist}"/>\n\t\t<flag staticattack="90"/>\n\t\t<flag runonhealth="{runonhealth}"/>',
             '\t</flags>', '\t<attacks>']
    for a in m["attacks"]:
        interval = int(a["cooldown_s"] * 1000)
        mn, mx = -int(a["damage_min"]), -int(a["damage_max"])
        conds = ""
        eff_attrs = ""
        for e in a.get("effects", []):
            t = e["type"]
            total = int(e.get("value", 0) * e.get("duration_s", 0))
            if t == "poison":
                eff_attrs += f' poison="{total}"'
            elif t == "burn":
                eff_attrs += f' fire="{total}"'
            elif t in ("slow", "stun", "paralyze"):
                change = -1000 if t != "slow" else -int(400 * e.get("value", 0.3))
                conds += f'\t\t<attack name="speed" interval="{interval}" chance="{int(e["chance"]*100)}" speedchange="{change}" duration="{int(e["duration_s"]*1000)}" range="{m["attack_range"]}" target="1"/>\n'
        if a["type"] == "melee":
            lines.append(f'\t\t<attack name="melee" interval="{interval}" min="{mn}" max="{mx}"{eff_attrs}/>')
        elif a["type"] == "projectile":
            el = M["elements"][m["element"] if m["element"] != "none" else "none"]
            lines.append(f'\t\t<attack name="{el["xml"]}" interval="{interval}" chance="60" range="{m["attack_range"]}" target="1" min="{mn}" max="{mx}">')
            lines.append(f'\t\t\t<attribute key="shootEffect" value="{el["shoot"].replace("CONST_ANI_", "").lower()}"/>')
            lines.append('\t\t</attack>')
        elif a["type"] == "area":
            el = M["elements"][m["element"] if m["element"] != "none" else "none"]
            shape = a.get("shape", "circle_r1")
            radius = int(shape.split("_")[1].lstrip("r")) + 1 if shape.startswith("circle") else 2
            lines.append(f'\t\t<attack name="{el["xml"]}" interval="{interval}" chance="40" radius="{radius}" target="0" min="{mn}" max="{mx}">')
            lines.append(f'\t\t\t<attribute key="areaEffect" value="{el["area_effect"].replace("CONST_ME_", "").lower()}"/>')
            lines.append('\t\t</attack>')
        if conds:
            lines.append(conds.rstrip("\n"))
    lines.append('\t</attacks>')
    lines.append(f'\t<defenses armor="{m["defense"]}" defense="{m["defense"]}"/>')
    ep = element_percents(m["element"])
    if ep:
        lines.append('\t<elements>')
        for k, v in ep.items():
            lines.append(f'\t\t<element {k}Percent="{v}"/>')
        lines.append('\t</elements>')
    if m.get("boss"):
        lines.append('\t<script>')
        lines.append(f'\t\t<event name="NarutoBossPhases"/>')
        lines.append('\t</script>')
    lines.append('\t<loot>')
    lines.append(f'\t\t<item id="{item_id("ryo")}" countmax="{m["ryo_max"]}" chance="100000"/>')
    for l in m["loot"]:
        iid = item_id(l["item_id"])
        cm = f' countmax="{l["max"]}"' if l.get("max", 1) > 1 else ""
        lines.append(f'\t\t<item id="{iid}"{cm} chance="{int(l["chance"]*100000)}"/>  <!-- {l["item_id"]} -->')
    lines.append('\t</loot>')
    lines.append('</monster>')
    return "\n".join(lines) + "\n"

for m in monsters.values():
    write(f"monster/naruto/{m['id']}.xml", monster_xml(m))
write("monster/monsters_naruto.xml", HEADER_XML + "<!-- Cole dentro de <monsters> em data/monster/monsters.xml -->\n" +
      "".join(f'<monster name="{escape(m["name"])}" file="naruto/{m["id"]}.xml"/>\n' for m in monsters.values()))

# ---------------------------------------------------------------- jutsus (spells)
def spell_words(j):
    return j["id"].replace("_", " ")

spells_xml = [HEADER_XML, "<!-- Cole dentro de <spells> em data/spells/spells.xml -->"]
for spell_idx, j in enumerate(jutsus.values(), start=1):
    el = M["elements"][j["element"]]
    need_target = 1 if j["type"] in ("projectile", "target") else 0
    group = "healing" if j["type"] == "self" else "attack"
    # NOVO MODELO: jutsu não é mais filtrado por vila — quem controla o acesso é o
    # learnSpell/forgetSpell de NarutoCharacters.apply (personagem + elemento escolhidos).
    # Por isso TODAS as vocações entram no <instant>; o campo `villages` do JSON só sobrevive
    # como metadado de lore/cliente.
    voc_xml = "".join(f'\n\t<vocation name="{escape(voc_name(v))}"/>' for v in villages.keys())
    spells_xml.append(
        # spellid PRECISA ser único: sem ele, TFS 1.4.2 usa 0 para TODOS os instants
        # (spells.h: uint8_t spellId = 0) e o cooldown "cooldown_s" de QUALQUER jutsu
        # passa a bloquear TODOS os outros (mesmo de grupo/elemento diferente).
        f'<instant group="{group}" name="{escape(j["name"])}" words="{spell_words(j)}" lvl="{j["required_level"]}" '
        f'mana="{j["chakra_cost"]}" prem="0" range="{max(1, j["range"])}" needtarget="{need_target}" blockwalls="1" '
        f'aggressive="{0 if group == "healing" else 1}" spellid="{spell_idx}" '
        f'cooldown="{int(j["cooldown_s"]*1000)}" groupcooldown="1000" needlearn="{0 if j["id"] in UNIVERSAL_JUTSU_IDS else 1}" '
        f'script="naruto/{j["id"]}.lua">{voc_xml}\n</instant>')

    lua = [HEADER_LUA, f"-- {j['name']}: {j.get('description','')}"]
    if j["type"] == "self":
        if j["id"] == "kawarimi":
            lua.append("""function onCastSpell(creature, variant)
	local pos = creature:getPosition()
	local dir = creature:getDirection()
	local back = Position(pos)
	for _ = 1, 2 do
		back:getNextPosition(dir == DIRECTION_NORTH and DIRECTION_SOUTH or dir == DIRECTION_SOUTH and DIRECTION_NORTH or dir == DIRECTION_EAST and DIRECTION_WEST or DIRECTION_EAST)
	end
	local tile = Tile(back)
	if tile and tile:isWalkable() and not tile:hasFlag(TILESTATE_BLOCKSOLID) then
		pos:sendMagicEffect(CONST_ME_POFF)
		creature:teleportTo(back)
		back:sendMagicEffect(CONST_ME_POFF)
		local cond = Condition(CONDITION_INVISIBLE)
		cond:setParameter(CONDITION_PARAM_TICKS, 1000)
		creature:addCondition(cond)
		return true
	end
	creature:sendCancelMessage("Não há espaço para a substituição.")
	pos:sendMagicEffect(CONST_ME_POFF)
	return false
end""")
        elif j["id"] == "bunshin":
            lua.append("""-- TODO: criar monstro 'Clone' (cópia do outfit do jogador, 1 HP, some em 6s) e usar creature:addSummon.
function onCastSpell(creature, variant)
	local pos = creature:getPosition()
	pos:sendMagicEffect(CONST_ME_POFF)
	for _, spec in ipairs(Game.getSpectators(pos, false, false, 8, 8, 8, 8)) do
		if spec:isMonster() and spec:getTarget() == creature then
			spec:setTarget(nil)  -- distrai por um instante; o monstro reavalia alvo depois
		end
	end
	return true
end""")
        else:
            hot = next((e for e in j.get("effects", []) if e["type"] == "heal_over_time"), None)
            v, d = (int(hot["value"]), int(hot["duration_s"])) if hot else (8, 5)
            lua.append(f"""local condition = Condition(CONDITION_REGENERATION)
condition:setParameter(CONDITION_PARAM_SUBID, 1)
condition:setParameter(CONDITION_PARAM_TICKS, {d*1000})
condition:setParameter(CONDITION_PARAM_HEALTHGAIN, {v})
condition:setParameter(CONDITION_PARAM_HEALTHTICKS, 1000)

function onCastSpell(creature, variant)
	creature:addCondition(condition)
	creature:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
	return true
end""")
    else:
        lua.append(f"""local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, {el["combat"]})
combat:setParameter(COMBAT_PARAM_EFFECT, {el["area_effect"]})""")
        if j["type"] == "projectile":
            lua.append(f"combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, {el['shoot']})")
        if j["type"] in ("area", "beam"):
            lua.append(f"local area = {area_lua(j.get('shape', 'circle_r1'))}\ncombat:setArea(createCombatArea(area))")
        # fórmula: base + level*ls + maglevel*ss, variação ±10%, elemento tratado pelo servidor
        lua.append(f"""
function onGetFormulaValues(player, level, maglevel)
	local base = {j["base_damage"]} + level * {j["level_scale"]} + maglevel * {j["skill_scale"]}
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")""")
        for e in j.get("effects", []):
            t = e["type"]
            if t in ("burn", "poison"):
                ct = "CONDITION_FIRE" if t == "burn" else "CONDITION_POISON"
                lua.append(f"""
local condition = Condition({ct})
condition:setParameter(CONDITION_PARAM_DELAYED, 1)
condition:addDamage({int(e["duration_s"])}, 1000, -{int(e.get("value", 1))})
combat:addCondition(condition)  -- chance {e["chance"]}: TODO aplicar chance via callback""")
            elif t in ("slow", "stun", "paralyze"):
                change = -0.9 if t != "slow" else -float(e.get("value", 0.3))
                lua.append(f"""
local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, {int(e["duration_s"]*1000)})
condition:setFormula({change}, 0, {change}, 0)
combat:addCondition(condition)  -- {t}, chance {e["chance"]}""")
        lua.append("""
function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end""")
    write(f"spells/scripts/naruto/{j['id']}.lua", "\n".join(lua) + "\n")
write("spells/spells_naruto.xml", "\n".join(spells_xml) + "\n")

# ---------------------------------------------------------------- itens
def items_xml():
    out = [HEADER_XML, "<!-- Entradas para data/items/items.xml. Os ids são placeholders de data/tfs_mapping.json; itens vanilla com o mesmo id JÁ EXISTEM no items.xml — remova a entrada antiga ou troque o id quando tiver sprite próprio. -->"]
    for it in items.values():
        iid = item_id(it["id"])
        if iid == 0 or it["type"] == "currency":
            continue
        if iid in VANILLA_ITEM_IDS:
            # modo OVERRIDE: nosso item substitui o vanilla de mesmo id (o installer remove a entrada vanilla)
            SKIPPED_ITEM_IDS.append((it["id"], iid))
        attrs = [f'<attribute key="weight" value="{int(float(it.get("weight", 0)) * 100)}"/>',
                 f'<attribute key="description" value="{escape(it.get("description", ""))}"/>']
        t = it["type"]
        if t == "weapon":
            attrs.append(f'<attribute key="attack" value="{it.get("attack", 0)}"/>')
            if it.get("weapon_class") == "ranged":
                attrs.append('<attribute key="weaponType" value="distance"/>')
                attrs.append(f'<attribute key="range" value="{it.get("weapon_range", 4)}"/>')
                if int(it.get("stack_max", 1)) > 1:
                    attrs.append('<attribute key="ammoType" value="throwingstar"/>')
                    attrs.append('<attribute key="shootType" value="throwingstar"/>')
            else:
                attrs.append('<attribute key="weaponType" value="sword"/>')  # taijutsu = sword no TFS
            attrs.append('<attribute key="slotType" value="hand"/>')
        elif t == "armor":
            attrs.append(f'<attribute key="armor" value="{it.get("defense", 0)}"/>')
            attrs.append(f'<attribute key="slotType" value="{it["slot"]}"/>')
        elif t == "accessory":
            slot = {"accessory": "ring", "back": "backpack"}.get(it.get("slot"), "necklace")
            attrs.append(f'<attribute key="slotType" value="{slot}"/>')
        for k, v in it.get("bonuses", {}).items():
            key = {"hp": "maxhitpoints", "chakra": "maxmanapoints", "speed": "speed",
                   "skill_taijutsu": "skillSword", "skill_shuriken": "skillDist", "skill_ninjutsu": "magiclevelpoints",
                   "skill_genjutsu": "skillClub", "skill_defense": "skillShield"}.get(k)
            if key:
                val = int(v * 100) if k == "speed" else int(v)
                attrs.append(f'<attribute key="{key}" value="{val}"/>')
            elif k.startswith("element_resist_"):
                el = M["elements"].get(k.split("_")[-1], {}).get("xml")
                if el:
                    attrs.append(f'<attribute key="absorbPercent{el.capitalize()}" value="{int(v*100)}"/>')
        if it.get("required_level"):
            attrs.append(f'<!-- required_level {it["required_level"]}: aplicar via movements.xml (level) -->')
        out.append(f'<item id="{iid}" name="{escape(it["name"].lower())}">  <!-- {it["id"]} ({it["rarity"]}) -->')
        out += ["\t" + a for a in attrs]
        out.append('</item>')
    return "\n".join(out) + "\n"
write("items/items_naruto.xml", items_xml())

# ---------------------------------------------------------------- vocações
voc = ['<?xml version="1.0" encoding="UTF-8"?>', HEADER_XML.rstrip("\n"), '<vocations>',
       '\t<vocation id="0" clientid="0" name="Sem vila" description="um viajante sem vila" gaincap="10" gainhp="5" gainmana="5" gainhpticks="6" gainhpamount="1" gainmanaticks="6" gainmanaamount="2" manamultiplier="4.0" attackspeed="2000" basespeed="220" soulmax="100" gainsoulticks="120" fromvoc="0">',
       '\t\t<formula meleeDamage="1.0" distDamage="1.0" defense="1.0" armor="1.0"/>',
       '\t\t<skill id="0" multiplier="1.5"/><skill id="1" multiplier="2.0"/><skill id="2" multiplier="2.0"/><skill id="3" multiplier="2.0"/><skill id="4" multiplier="2.0"/><skill id="5" multiplier="1.5"/><skill id="6" multiplier="1.1"/>',
       '\t</vocation>']
skill_ids = {"taijutsu": 2, "genjutsu": 1, "shuriken": 4, "defense": 5}
for vid, v in villages.items():
    vm = M["villages"][vid]
    mults = {0: 1.5, 1: 2.0, 2: 2.0, 3: 2.0, 4: 2.0, 5: 1.5, 6: 1.1}
    bonus = v["bonus_skill"]
    mana_mult = 4.0
    if bonus in skill_ids:
        mults[skill_ids[bonus]] = round(mults[skill_ids[bonus]] / 1.2, 2)
    elif bonus == "ninjutsu":
        mana_mult = 4.0 / 1.2
    voc.append(f'\t<vocation id="{vm["vocation_id"]}" clientid="{vm["vocation_id"]}" name="{escape(v["name"])}" description="um ninja da {escape(v["name"])}" gaincap="5" gainhp="15" gainmana="10" gainhpticks="5" gainhpamount="2" gainmanaticks="5" gainmanaamount="3" manamultiplier="{mana_mult:.2f}" attackspeed="2000" basespeed="220" soulmax="100" gainsoulticks="120" fromvoc="{vm["vocation_id"]}">')
    voc.append('\t\t<formula meleeDamage="1.0" distDamage="1.0" defense="1.0" armor="1.0"/>')
    voc.append("\t\t" + "".join(f'<skill id="{i}" multiplier="{m}"/>' for i, m in mults.items()))
    voc.append('\t</vocation>')
voc.append('</vocations>')
write("XML/vocations.xml", "\n".join(voc) + "\n")

# ---------------------------------------------------------------- outfits de vila (ADR-002: nomes
# próprios de traje, nunca nome de personagem do anime) + storage inicial por vocação/vila.
# Looktypes fixos 900-926 vêm de assets-src/sprites/mugen_looktypes.json (outro agente gera o
# sprite); aqui só decidimos QUAIS looktypes cada vila oferece e como o outfit.xml os nomeia.
OUTFIT_NAMES = {
    900: "Traje Genin Laranja",
    901: "Traje Genin Azul",
    902: "Traje Genin Rosa",
    903: "Traje Kunoichi Branco",
    904: "Traje Verde de Treino",
    905: "Traje Marrom de Viajante",
    907: "Traje Amarelo do Sábio",
    908: "Traje Branco Cerimonial",
    909: "Traje Listrado da Nuvem",
}

def village_outfits():
    """{vocation_id: {name, default_outfit, outfits: [...]}} a partir de tfs_mapping.villages."""
    out = {}
    for vid, v in villages.items():
        vm = M["villages"][vid]
        out[vm["vocation_id"]] = {
            "id": vid,
            "name": v["name"],
            "default_outfit": int(vm["default_outfit"]),
            "outfits": [int(o) for o in vm["outfits"]],
        }
    return out

VOC_OUTFITS = village_outfits()
ALL_VILLAGE_LOOKTYPES = sorted({look for vo in VOC_OUTFITS.values() for look in vo["outfits"]})

outfits_xml = ['<?xml version="1.0" encoding="UTF-8"?>', HEADER_XML.rstrip("\n"), '<outfits>',
               '\t<!-- Trajes das vilas (looktypes 900-926, ver assets-src/sprites/mugen_looktypes.json). -->']
for sex in (0, 1):
    outfits_xml.append(f'\t<!-- type {sex} ({"feminino" if sex == 0 else "masculino"}) -->')
    for look in ALL_VILLAGE_LOOKTYPES:
        name = escape(OUTFIT_NAMES.get(look, f"Traje {look}"))
        outfits_xml.append(f'\t<outfit type="{sex}" looktype="{look}" name="{name}" enabled="1"/>')
outfits_xml.append('</outfits>')
write("XML/outfits.xml", "\n".join(outfits_xml) + "\n")

villages_lua = [HEADER_LUA, "-- Coloque em data/lib/naruto_villages.lua e adicione",
                "-- `dofile('data/lib/naruto_villages.lua')` em data/lib/lib.lua (ANTES de scripts/naruto/village_outfit.lua)",
                "NarutoVillages = {"]
for voc_id in sorted(VOC_OUTFITS):
    vo = VOC_OUTFITS[voc_id]
    outfits_lua = ", ".join(str(o) for o in vo["outfits"])
    villages_lua.append(f"\t[{voc_id}] = {{id = '{vo['id']}', name = '{escape(vo['name'])}', default_outfit = {vo['default_outfit']}, outfits = {{{outfits_lua}}}}},")
villages_lua.append("}")
write("lib/naruto_villages.lua", "\n".join(villages_lua) + "\n")

# ---------------------------------------------------------------- lib JSON em Lua
# O TFS 1.4.2 não traz biblioteca JSON (data/lib/core/ não tem nada do gênero) e o protocolo
# do opcode estendido 210 usa JSON como buffer. Encoder/decoder puro em Lua, compacto.
NARUTO_JSON_LUA = HEADER_LUA + r"""-- Coloque em data/lib/naruto_json.lua e adicione
-- `dofile('data/lib/naruto_json.lua')` em data/lib/lib.lua.
--
-- NarutoJson.encode(valor) -> string   |  NarutoJson.decode(string) -> valor, err
-- Arrays vs objetos: uma table com t[1] ~= nil vira array; table vazia vira {} (objeto).
-- Use NarutoJson.array({}) para forçar array vazio ([]).
NarutoJson = {}

local ARRAY_MT = {__jsonarray = true}
function NarutoJson.array(t)
	return setmetatable(t or {}, ARRAY_MT)
end

--- Sentinela para emitir `null` explicito (Lua nao guarda nil dentro de table).
NarutoJson.null = setmetatable({}, {__tostring = function() return 'null' end})

local ESC = {['"'] = '\\"', ['\\'] = '\\\\', ['\b'] = '\\b', ['\f'] = '\\f',
	['\n'] = '\\n', ['\r'] = '\\r', ['\t'] = '\\t'}

local function escapeChar(c)
	return ESC[c] or string.format('\\u%04x', string.byte(c))
end

local function encodeString(s)
	return '"' .. s:gsub('[%z\1-\31\\"]', escapeChar) .. '"'
end

local function isArray(t)
	if getmetatable(t) == ARRAY_MT then return true end
	if next(t) == nil then return false end
	local n = 0
	for k in pairs(t) do
		if type(k) ~= 'number' then return false end
		n = n + 1
	end
	return n == #t
end

local encodeValue

local function encodeNumber(v)
	if v ~= v or v == math.huge or v == -math.huge then return 'null' end
	if v == math.floor(v) and math.abs(v) < 1e15 then return string.format('%d', v) end
	return string.format('%.6g', v)
end

encodeValue = function(v, out)
	local t = type(v)
	if v == nil or v == NarutoJson.null then
		out[#out + 1] = 'null'
	elseif t == 'boolean' then
		out[#out + 1] = v and 'true' or 'false'
	elseif t == 'number' then
		out[#out + 1] = encodeNumber(v)
	elseif t == 'string' then
		out[#out + 1] = encodeString(v)
	elseif t == 'table' then
		if isArray(v) then
			out[#out + 1] = '['
			for i = 1, #v do
				if i > 1 then out[#out + 1] = ',' end
				encodeValue(v[i], out)
			end
			out[#out + 1] = ']'
		else
			out[#out + 1] = '{'
			local first = true
			-- ordena as chaves: saída determinística (facilita diff de log/teste)
			local keys = {}
			for k in pairs(v) do keys[#keys + 1] = tostring(k) end
			table.sort(keys)
			for _, k in ipairs(keys) do
				local val = v[k]
				if val == nil then val = v[tonumber(k)] end
				if not first then out[#out + 1] = ',' end
				first = false
				out[#out + 1] = encodeString(k)
				out[#out + 1] = ':'
				encodeValue(val, out)
			end
			out[#out + 1] = '}'
		end
	else
		out[#out + 1] = 'null'
	end
end

function NarutoJson.encode(v)
	local out = {}
	encodeValue(v, out)
	return table.concat(out)
end

-- ------------------------------------------------------------------ decode
local function skipWhitespace(s, i)
	local _, j = s:find('^[ \t\r\n]*', i)
	return j + 1
end

local parseValue

local UNESC = {['"'] = '"', ['\\'] = '\\', ['/'] = '/', b = '\b', f = '\f', n = '\n', r = '\r', t = '\t'}

local function parseString(s, i)
	i = i + 1  -- pula a aspa inicial
	local buf = {}
	while true do
		local c = s:sub(i, i)
		if c == '' then return nil, i, 'string sem fechamento' end
		if c == '"' then return table.concat(buf), i + 1 end
		if c == '\\' then
			local e = s:sub(i + 1, i + 1)
			if e == 'u' then
				local hex = s:sub(i + 2, i + 5)
				local code = tonumber(hex, 16)
				if not code then return nil, i, 'escape \\u invalido' end
				-- UTF-8 (o TFS trafega bytes; o cliente decodifica)
				if code < 0x80 then
					buf[#buf + 1] = string.char(code)
				elseif code < 0x800 then
					buf[#buf + 1] = string.char(0xC0 + math.floor(code / 0x40), 0x80 + code % 0x40)
				else
					buf[#buf + 1] = string.char(0xE0 + math.floor(code / 0x1000),
						0x80 + math.floor(code % 0x1000 / 0x40), 0x80 + code % 0x40)
				end
				i = i + 6
			else
				local u = UNESC[e]
				if not u then return nil, i, 'escape invalido: \\' .. e end
				buf[#buf + 1] = u
				i = i + 2
			end
		else
			local nextEsc = s:find('[\\"]', i)
			buf[#buf + 1] = s:sub(i, (nextEsc or (#s + 1)) - 1)
			i = nextEsc or (#s + 1)
		end
	end
end

local function parseNumber(s, i)
	local _, j = s:find('^-?%d+%.?%d*[eE]?[-+]?%d*', i)
	local n = tonumber(s:sub(i, j))
	if not n then return nil, i, 'numero invalido' end
	return n, j + 1
end

parseValue = function(s, i)
	i = skipWhitespace(s, i)
	local c = s:sub(i, i)
	if c == '' then return nil, i, 'fim inesperado' end
	if c == '{' then
		local obj = {}
		i = skipWhitespace(s, i + 1)
		if s:sub(i, i) == '}' then return obj, i + 1 end
		while true do
			i = skipWhitespace(s, i)
			if s:sub(i, i) ~= '"' then return nil, i, 'chave esperada' end
			local k, err
			k, i, err = parseString(s, i)
			if err then return nil, i, err end
			i = skipWhitespace(s, i)
			if s:sub(i, i) ~= ':' then return nil, i, '":" esperado' end
			local v
			v, i, err = parseValue(s, i + 1)
			if err then return nil, i, err end
			obj[k] = v
			i = skipWhitespace(s, i)
			local d = s:sub(i, i)
			if d == '}' then return obj, i + 1 end
			if d ~= ',' then return nil, i, '"," ou "}" esperado' end
			i = i + 1
		end
	elseif c == '[' then
		local arr = NarutoJson.array({})
		i = skipWhitespace(s, i + 1)
		if s:sub(i, i) == ']' then return arr, i + 1 end
		while true do
			local v, err
			v, i, err = parseValue(s, i)
			if err then return nil, i, err end
			arr[#arr + 1] = v
			i = skipWhitespace(s, i)
			local d = s:sub(i, i)
			if d == ']' then return arr, i + 1 end
			if d ~= ',' then return nil, i, '"," ou "]" esperado' end
			i = i + 1
		end
	elseif c == '"' then
		return parseString(s, i)
	elseif s:sub(i, i + 3) == 'true' then
		return true, i + 4
	elseif s:sub(i, i + 4) == 'false' then
		return false, i + 5
	elseif s:sub(i, i + 3) == 'null' then
		return nil, i + 4
	else
		return parseNumber(s, i)
	end
end

--- Decodifica. Devolve (valor) em caso de sucesso ou (nil, mensagem) em caso de erro.
function NarutoJson.decode(str)
	if type(str) ~= 'string' then return nil, 'esperava string' end
	local ok, v, i, err = pcall(parseValue, str, 1)
	if not ok then return nil, tostring(v) end
	if err then return nil, err end
	return v
end

-- ------------------------------------------------------------------ envio (opcode estendido)
-- ARMADILHA do TFS 1.4.2: NetworkMessage::addString (src/networkmessage.cpp) DESCARTA em
-- silencio qualquer string com mais de 8192 bytes. Como Player.sendExtendedOpcode
-- (data/lib/core/player.lua) usa addString, um buffer JSON grande (ex.: o `state` de um GM,
-- que lista TODOS os personagens) chegava ao cliente como um 0x32 sem corpo -- e o OTClient
-- logava "ProtocolGame parse message exception ... InputMessage eof reached".
-- Acima de 8192 bytes escrevemos o u16 de tamanho e os bytes na mao (addByte so checa
-- MAX_BODY_LENGTH = 24576).
local EXTENDED_OPCODE_HEADER = 0x32
local ADDSTRING_LIMIT = 8192
local MAX_BODY = 24000  -- margem sob MAX_BODY_LENGTH (24576)

function NarutoJson.sendExtended(player, opcode, str)
	if not player or not player:isUsingOtClient() then return false end
	local len = #str
	if len > MAX_BODY then
		print(string.format("[naruto] opcode %d: buffer de %d bytes excede o limite do NetworkMessage (%d)",
			opcode, len, MAX_BODY))
		return false
	end
	if len <= ADDSTRING_LIMIT then
		return player:sendExtendedOpcode(opcode, str)
	end
	local msg = NetworkMessage()
	msg:addByte(EXTENDED_OPCODE_HEADER)
	msg:addByte(opcode)
	msg:addU16(len)
	local byte = string.byte
	for i = 1, len do
		msg:addByte(byte(str, i))
	end
	msg:sendToPlayer(player)
	msg:delete()
	return true
end
"""
write("lib/naruto_json.lua", NARUTO_JSON_LUA)

# ---------------------------------------------------------------- personagens + elementos
# NOVO MODELO: o jogador escolhe PERSONAGEM (4 jutsus pessoais) e ELEMENTO (4 jutsus do set,
# data/element_sets.json). Sem filtro de vila nos jutsus elementais. O cliente conversa pelo
# opcode estendido 210 (ver docs/sistemas/combate-e-jutsus.md).
def lua_esc(s):
    return str(s).replace("\\", "\\\\").replace("'", "\\'")

def lua_q(s):
    return "'" + lua_esc(s) + "'"

CHAR_VOC_ID = {c["id"]: M["villages"][c["village"]]["vocation_id"] for c in characters}

def jutsu_lua(jid):
    """Uma entrada de jutsu no formato que o cliente espera (opcode 210)."""
    j = jutsus[jid]
    return ("{id = %s, name = %s, words = %s, element = %s, type = %s, chakra = %d, cooldown_s = %s}" % (
        lua_q(j["id"]), lua_q(j["name"]), lua_q(spell_words(j)), lua_q(j.get("element", "none")),
        lua_q(j["type"]), int(j["chakra_cost"]), repr(float(j["cooldown_s"]))))

def jutsu_list_lua(ids):
    return "{" + ", ".join(jutsu_lua(jid) for jid in ids) + "}"

chars_lua = [HEADER_LUA,
             "-- Personagens jogaveis (4 jutsus pessoais cada) e SETS DE ELEMENTO (4 jutsus cada).",
             "-- Gerado a partir de data/characters.json + data/element_sets.json + data/jutsus/*.json.",
             "-- A logica (NarutoCharacters.apply / .sendState) fica em",
             "-- server/generated/scripts/naruto/character_switch.lua.",
             "NarutoCharacters = { list = {}, byLook = {}, byId = {}, byVillage = {}, allJutsuNames = {} }",
             "NarutoElements = { list = {}, byId = {}, order = {} }"]
for c in characters:
    ids = personal_jutsu_ids(c)
    chars_lua.append(
        "table.insert(NarutoCharacters.list, {id = %s, name = %s, description = %s, looktype = %d, "
        "village = %s, village_vocation = %d, default_element = %s, jutsus = %s})" % (
            lua_q(c["id"]), lua_q(c["name"]), lua_q(c.get("description", "")), int(c["looktype"]),
            lua_q(c["village"]), CHAR_VOC_ID[c["id"]], lua_q(default_element_of(c)), jutsu_list_lua(ids)))
for es in element_sets:
    chars_lua.append("table.insert(NarutoElements.list, {id = %s, name = %s, jutsus = %s})" % (
        lua_q(es["id"]), lua_q(es["name"]), jutsu_list_lua(es["jutsus"])))
chars_lua.append("""
for _, c in ipairs(NarutoCharacters.list) do
	NarutoCharacters.byLook[c.looktype] = c
	NarutoCharacters.byId[c.id] = c
	NarutoCharacters.byVillage[c.village_vocation] = NarutoCharacters.byVillage[c.village_vocation] or {}
	table.insert(NarutoCharacters.byVillage[c.village_vocation], c)
	for _, j in ipairs(c.jutsus) do
		NarutoCharacters.allJutsuNames[j.name] = true
	end
end
for i, e in ipairs(NarutoElements.list) do
	e.index = i
	NarutoElements.byId[e.id] = e
	NarutoElements.order[i] = e.id
	-- jutsus de elemento tambem entram no "esquece tudo" de NarutoCharacters.apply
	for _, j in ipairs(e.jutsus) do
		NarutoCharacters.allJutsuNames[j.name] = true
	end
end""")
for uj in UNIVERSAL_JUTSU_IDS:
    if uj in jutsus:
        chars_lua.append("NarutoCharacters.allJutsuNames[%s] = nil  -- universal, nunca esquecido" %
                         lua_q(jutsus[uj]["name"]))
write("lib/naruto_characters.lua", "\n".join(chars_lua) + "\n")

# village_outfit.lua deixou de existir: a lógica de "1º login" foi absorvida pelo onLogin de
# character_switch.lua (não duplicar). Remove a cópia velha do pacote gerado.
_old_vo = os.path.join(OUT, "scripts", "naruto", "village_outfit.lua")
if os.path.exists(_old_vo):
    os.remove(_old_vo)

# ---------------------------------------------------------------- troca de personagem/elemento
character_switch_script = HEADER_LUA + """-- Coloque em data/scripts/naruto/character_switch.lua (revscriptsys carrega sozinho).
-- Depende de NarutoCharacters/NarutoElements (data/lib/naruto_characters.lua) e de
-- NarutoJson (data/lib/naruto_json.lua). Ambos entram via dofile em data/lib/lib.lua
-- (tools/install_generated.sh faz isso).
--
-- MODELO: o jogador escolhe PERSONAGEM (4 jutsus pessoais) + ELEMENTO (4 jutsus do set).
-- Os 8 jutsus sao aprendidos na hora; todo o resto e esquecido. Jutsus elementais NAO sao
-- filtrados por vila; personagens SIM (menos para GM).
--
-- PROTOCOLO com o cliente: opcode estendido 210, buffer = JSON.
--   servidor -> cliente: {"type":"state", ...}   (ver NarutoCharacters.sendState)
--   cliente -> servidor: {"type":"select","character":"id|null","element":"id|null"}
--                        {"type":"get_state"}
local OPCODE = 210
local STORAGE_ONBOARDED = 60000  -- 1 depois da primeira aplicacao (outfits liberados)
local STORAGE_CHARACTER = 60001  -- looktype do personagem atual
local STORAGE_ELEMENT   = 60002  -- indice do elemento em NarutoElements.order

local function isGodPlayer(player)
	return player:getGroup():getAccess() and player:getAccountType() >= ACCOUNT_TYPE_GOD
end

local function villageIdOf(player)
	local v = NarutoVillages and NarutoVillages[player:getVocation():getId()]
	return v and v.id or nil
end

--- Personagem atual (storage) ou, se nao houver, o primeiro da vila do jogador.
function NarutoCharacters.current(player)
	local look = player:getStorageValue(STORAGE_CHARACTER)
	if look and look > 0 and NarutoCharacters.byLook[look] then
		return NarutoCharacters.byLook[look]
	end
	return nil
end

function NarutoCharacters.defaultFor(player)
	local list = NarutoCharacters.byVillage[player:getVocation():getId()]
	return list and list[1] or NarutoCharacters.list[1]
end

--- Elemento atual (storage 60002 = indice) ou nil.
function NarutoCharacters.currentElement(player)
	local idx = player:getStorageValue(STORAGE_ELEMENT)
	if idx and idx > 0 then
		return NarutoElements.list[idx]
	end
	return nil
end

--- Resolve um elemento por id ('katon'), por indice numerico, ou nil.
local function resolveElement(elementId)
	if elementId == nil then return nil end
	if type(elementId) == 'number' then return NarutoElements.list[elementId] end
	return NarutoElements.byId[tostring(elementId)]
end

--- Resolve um personagem por id ('genin_uchiha') ou por looktype numerico.
local function resolveCharacter(characterId)
	if characterId == nil then return nil end
	if type(characterId) == 'number' then return NarutoCharacters.byLook[characterId] end
	return NarutoCharacters.byId[tostring(characterId)] or NarutoCharacters.byLook[tonumber(characterId) or -1]
end

--- Aplica personagem + elemento. Qualquer um dos dois pode vir nil = manter o atual
--- (ou cair no padrao: personagem da vila / elemento padrao do personagem).
--- opts.force ignora a validacao de vila, opts.silent nao manda mensagem.
--- Retorna true, ou false + mensagem de erro.
function NarutoCharacters.apply(player, characterId, elementId, opts)
	opts = opts or {}
	local char = resolveCharacter(characterId) or NarutoCharacters.current(player) or NarutoCharacters.defaultFor(player)
	if not char then
		return false, "Personagem desconhecido."
	end
	if characterId ~= nil and not resolveCharacter(characterId) then
		return false, "Personagem desconhecido."
	end
	if not opts.force and not isGodPlayer(player) and char.village_vocation ~= player:getVocation():getId() then
		return false, "Esse personagem nao e da sua vila."
	end
	local element = resolveElement(elementId)
	if elementId ~= nil and not element then
		return false, "Elemento desconhecido."
	end
	element = element or NarutoCharacters.currentElement(player) or NarutoElements.byId[char.default_element] or NarutoElements.list[1]
	if not element then
		return false, "Nenhum elemento configurado no servidor."
	end

	-- libera os trajes da vila na primeira vez
	if player:getStorageValue(STORAGE_ONBOARDED) < 1 then
		local village = NarutoVillages and NarutoVillages[player:getVocation():getId()]
		if village then
			for _, look in ipairs(village.outfits) do
				player:addOutfit(look)
			end
		end
	end
	-- personagem de outra vila (GM): garante que o outfit e vestivel
	player:addOutfit(char.looktype)

	for jname in pairs(NarutoCharacters.allJutsuNames) do
		player:forgetSpell(jname)
	end
	local learned = {}
	for _, j in ipairs(char.jutsus) do
		player:learnSpell(j.name)
		learned[#learned + 1] = j.name
	end
	for _, j in ipairs(element.jutsus) do
		player:learnSpell(j.name)
		learned[#learned + 1] = j.name
	end

	local outfit = player:getOutfit()
	outfit.lookType = char.looktype
	player:setOutfit(outfit)

	player:setStorageValue(STORAGE_CHARACTER, char.looktype)
	player:setStorageValue(STORAGE_ELEMENT, element.index)
	player:setStorageValue(STORAGE_ONBOARDED, 1)

	if not opts.silent then
		player:sendTextMessage(MESSAGE_INFO_DESCR, string.format(
			"Personagem: %s | Elemento: %s. Jutsus: %s.", char.name, element.name, table.concat(learned, ", ")))
		player:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
	end
	if not opts.noState then
		NarutoCharacters.sendState(player)
	end
	return true
end

-- ------------------------------------------------------------------ estado (opcode 210)
local function jutsuJson(j)
	return {id = j.id, name = j.name, words = j.words, element = j.element,
		type = j.type, chakra = j.chakra, cooldown_s = j.cooldown_s}
end

local function jutsuListJson(list)
	local out = NarutoJson.array({})
	for i, j in ipairs(list) do out[i] = jutsuJson(j) end
	return out
end

--- Monta e envia o `state` para o cliente (opcode 210, buffer JSON).
function NarutoCharacters.sendState(player, firstTime)
	if not player or not player:isPlayer() then return false end
	local isGm = isGodPlayer(player)
	local char = NarutoCharacters.current(player)
	local element = NarutoCharacters.currentElement(player)

	local chars = NarutoJson.array({})
	for _, c in ipairs(NarutoCharacters.list) do
		if isGm or c.village_vocation == player:getVocation():getId() then
			chars[#chars + 1] = {
				id = c.id, name = c.name, description = c.description, looktype = c.looktype,
				village = c.village, default_element = c.default_element,
				jutsus = jutsuListJson(c.jutsus),
			}
		end
	end

	local els = NarutoJson.array({})
	for i, e in ipairs(NarutoElements.list) do
		els[i] = {id = e.id, name = e.name, jutsus = jutsuListJson(e.jutsus)}
	end

	local active = NarutoJson.array({})
	if char then for _, j in ipairs(char.jutsus) do active[#active + 1] = jutsuJson(j) end end
	if element then for _, j in ipairs(element.jutsus) do active[#active + 1] = jutsuJson(j) end end

	local state = {
		type = 'state',
		first_time = firstTime == true,
		is_gm = isGm,
		character = char and char.id or NarutoJson.null,
		element = element and element.id or NarutoJson.null,
		level = player:getLevel(),
		village = villageIdOf(player) or NarutoJson.null,
		characters = chars,
		elements = els,
		active_jutsus = active,
	}
	return NarutoJson.sendExtended(player, OPCODE, NarutoJson.encode(state))
end

-- ------------------------------------------------------------------ cliente -> servidor
local opcodeEvent = CreatureEvent("NarutoOpcode")
function opcodeEvent.onExtendedOpcode(player, opcode, buffer)
	if opcode ~= OPCODE then return true end
	local msg, err = NarutoJson.decode(buffer)
	if type(msg) ~= 'table' then
		print("[naruto] opcode 210: JSON invalido (" .. tostring(err) .. ")")
		return true
	end
	if msg.type == 'get_state' then
		NarutoCharacters.sendState(player)
	elseif msg.type == 'select' then
		local ok, e = NarutoCharacters.apply(player, msg.character, msg.element, {noState = true})
		if not ok then
			player:sendCancelMessage(e or "Selecao invalida.")
		end
		NarutoCharacters.sendState(player)
	end
	return true
end
opcodeEvent:register()

-- ------------------------------------------------------------------ login
local login = CreatureEvent("NarutoCharacterLogin")
function login.onLogin(player)
	player:registerEvent("NarutoOpcode")
	local firstTime = player:getStorageValue(STORAGE_ONBOARDED) < 1
	NarutoCharacters.apply(player, nil, nil, {silent = true, force = true, noState = true})
	local pid = player:getId()
	-- ~1s depois de entrar: o cliente ja carregou os modulos e escuta o opcode 210
	addEvent(function()
		local p = Player(pid)
		if p then NarutoCharacters.sendState(p, firstTime) end
	end, 1000)
	return true
end
login:register()

-- ------------------------------------------------------------------ talkactions
--- Normaliza para comparar nomes/ids sem acento e sem espaco (!personagem "genin uchiha").
local function normalize(s)
	s = tostring(s):lower():gsub("%s+", "_")
	local map = { ['\\195\\161']='a', ['\\195\\160']='a', ['\\195\\163']='a', ['\\195\\162']='a',
		['\\195\\169']='e', ['\\195\\170']='e', ['\\195\\173']='i', ['\\195\\179']='o',
		['\\195\\181']='o', ['\\195\\180']='o', ['\\195\\186']='u', ['\\195\\167']='c' }
	for accented, plain in pairs(map) do s = s:gsub(accented, plain) end
	return s
end

local function findByQuery(candidates, query)
	local q = normalize(query)
	for _, c in ipairs(candidates) do
		if normalize(c.id) == q or normalize(c.name) == q then return c end
	end
	return nil
end

--- !personagem [nome|id]: jogadores trocam entre os personagens DA PROPRIA vila (GM: qualquer).
local talkChar = TalkAction("!personagem")
function talkChar.onSay(player, words, param)
	local list = NarutoCharacters.list
	if not isGodPlayer(player) then
		list = NarutoCharacters.byVillage[player:getVocation():getId()] or {}
	end
	param = param and param:trim() or ""
	if param == "" then
		local names = {}
		for _, c in ipairs(list) do names[#names + 1] = c.name .. " (" .. c.id .. ")" end
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Personagens: " .. table.concat(names, ", ") .. ". Use !personagem <nome>.")
		return false
	end
	local char = findByQuery(list, param)
	if not char then
		player:sendCancelMessage("Personagem nao encontrado. Use !personagem para ver a lista.")
		return false
	end
	local ok, err = NarutoCharacters.apply(player, char.id, nil, {force = isGodPlayer(player)})
	if not ok then player:sendCancelMessage(err) end
	return false
end
talkChar:separator(" ")
talkChar:register()

--- !elemento [katon|suiton|raiton|doton|fuuton]
local talkElement = TalkAction("!elemento")
function talkElement.onSay(player, words, param)
	param = param and param:trim() or ""
	if param == "" then
		local names = {}
		for _, e in ipairs(NarutoElements.list) do names[#names + 1] = e.id end
		local cur = NarutoCharacters.currentElement(player)
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Elemento atual: " .. (cur and cur.name or "nenhum") ..
			". Disponiveis: " .. table.concat(names, ", ") .. ". Use !elemento <nome>.")
		return false
	end
	local el = findByQuery(NarutoElements.list, param)
	if not el then
		player:sendCancelMessage("Elemento nao encontrado. Use !elemento para ver a lista.")
		return false
	end
	local ok, err = NarutoCharacters.apply(player, nil, el.id, {force = true})
	if not ok then player:sendCancelMessage(err) end
	return false
end
talkElement:separator(" ")
talkElement:register()
"""
write("scripts/naruto/character_switch.lua", character_switch_script)

# ---------------------------------------------------------------- NPCs
def npc_files(n):
    o = M["npc_outfits"].get(n["id"], {"type": 128, "head": 0, "body": 0, "legs": 0, "feet": 0})
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n' + HEADER_XML +
           f'<npc name="{escape(n["name"])}" script="naruto/{n["id"]}.lua" walkinterval="2000" floorchange="0">\n'
           f'\t<health now="100" max="100"/>\n\t<look type="{o["type"]}" head="{o["head"]}" body="{o["body"]}" legs="{o["legs"]}" feet="{o["feet"]}"/>\n</npc>\n')
    lua = [HEADER_LUA, "local keywordHandler = KeywordHandler:new()", "local npcHandler = NpcHandler:new(keywordHandler)",
           "NpcSystem.parseParameters(npcHandler)", "",
           "function onCreatureAppear(cid) npcHandler:onCreatureAppear(cid) end",
           "function onCreatureDisappear(cid) npcHandler:onCreatureDisappear(cid) end",
           "function onCreatureSay(cid, type, msg) npcHandler:onCreatureSay(cid, type, msg) end",
           "function onThink() npcHandler:onThink() end", ""]
    if n["type"] == "shop":
        lua.append("local shopModule = ShopModule:new()\nnpcHandler:addModule(shopModule)")
        for iid in n.get("sells", []):
            it = items[iid]
            lua.append(f"shopModule:addBuyableItem({{'{it['name'].lower()}'}}, {item_id(iid)}, {it['buy_price']}, 1, '{it['name'].lower()}')")
        for it in items.values():
            if it["type"] in n.get("buys_types", []) and it["sell_price"] > 0 and item_id(it["id"]):
                lua.append(f"shopModule:addSellableItem({{'{it['name'].lower()}'}}, {item_id(it['id'])}, {it['sell_price']}, '{it['name'].lower()}')")
        lua.append(f'npcHandler:setMessage(MESSAGE_GREET, "Olá, |PLAYERNAME|. Diga {{trade}} para ver o que tenho.")')
    elif n["type"] == "quest":
        lua.append("local QUESTS = NarutoQuests.byNpc['%s']" % n["id"])
        lua.append("""
local function questCallback(cid, message, keywords, parameters, node)
	if not npcHandler:isFocused(cid) then return false end
	local player = Player(cid)
	local reply, _ = NarutoQuests.talk(player, QUESTS)
	npcHandler:say(reply, cid)
	return true
end
keywordHandler:addKeyword({'missao'}, questCallback, {})
keywordHandler:addKeyword({'mission'}, questCallback, {})
keywordHandler:addKeyword({'quest'}, questCallback, {})""")
        lua.append(f'npcHandler:setMessage(MESSAGE_GREET, "Olá, |PLAYERNAME|. Diga {{missao}} se quiser trabalho.")')
    lua.append("npcHandler:addModule(FocusModule:new())")
    return xml, "\n".join(lua) + "\n"

for n in npcs.values():
    xml, lua = npc_files(n)
    write(f"npc/{n['name']}.xml", xml)          # TFS instancia por nome: data/npc/<Nome>.xml
    write(f"npc/scripts/naruto/{n['id']}.lua", lua)  # script="naruto/<id>.lua" é relativo a data/npc/scripts/

# ---------------------------------------------------------------- lib + quests (revscriptsys)
base = int(M["storage_base"])
quest_defs = []
qi = 0
for n in npcs.values():
    for q in n.get("quests", []):
        qi += 1
        items_lua = ", ".join(f"{{id = {item_id(i)}, count = 1}}" for i in q["reward"].get("items", []))
        quest_defs.append(
            f"\t{{id = '{q['id']}', npc = '{n['id']}', name = '{q['name']}', text = '{q['text'].replace(chr(39), chr(92)+chr(39))}', "
            f"monster = '{monsters[q['objective']['kill']]['name']}', count = {q['objective']['count']}, "
            f"storage = {base + qi}, reward = {{xp = {q['reward'].get('xp', 0)}, ryo = {q['reward'].get('ryo', 0)}, items = {{{items_lua}}}}}}},")
lib = HEADER_LUA + f"""-- Coloque em data/lib/naruto_quests.lua e adicione `dofile('data/lib/naruto_quests.lua')` em data/lib/lib.lua
-- Storage: -1/ausente = não iniciada, 0..count-1 = progresso, count = pronta, {base + 500} = entregue (marcador)
NarutoQuests = {{}}
NarutoQuests.RYO_ID = {item_id('ryo')}
NarutoQuests.DONE = {base + 500}
NarutoQuests.list = {{
{chr(10).join(quest_defs)}
}}
NarutoQuests.byNpc = {{}}
for _, q in ipairs(NarutoQuests.list) do
	NarutoQuests.byNpc[q.npc] = NarutoQuests.byNpc[q.npc] or {{}}
	table.insert(NarutoQuests.byNpc[q.npc], q)
end

function NarutoQuests.talk(player, quests)
	for _, q in ipairs(quests) do
		local st = player:getStorageValue(q.storage)
		if st ~= NarutoQuests.DONE then
			if st >= q.count then
				player:setStorageValue(q.storage, NarutoQuests.DONE)
				player:addExperience(q.reward.xp, true)
				if q.reward.ryo > 0 then player:addItem(NarutoQuests.RYO_ID, q.reward.ryo) end
				for _, it in ipairs(q.reward.items) do player:addItem(it.id, it.count) end
				return "Bom trabalho, ninja. Missão '" .. q.name .. "' concluída.", true
			elseif st >= 0 then
				return "Ainda não terminou? " .. q.name .. ": " .. st .. "/" .. q.count .. " " .. q.monster .. ".", false
			else
				player:setStorageValue(q.storage, 0)
				return q.text .. " (Missão aceita: " .. q.name .. ")", false
			end
		end
	end
	return "Não tenho mais nada para você por enquanto.", false
end
"""
write("lib/naruto_quests.lua", lib)
# lista de itens para o /god do GM: {id=server id, key, type, slot, level, stack}
items_lua = HEADER_LUA + "NarutoItems = {\n"
for it in items.values():
    iid = item_id(it["id"])
    if iid == 0 or it["type"] == "currency":
        continue
    slot = it.get("slot", "")
    items_lua += f"\t{{id = {iid}, key = '{it['id']}', type = '{it['type']}', slot = '{slot}', level = {int(it.get('required_level', 1))}, stack = {int(it.get('stack_max', 1))}, atk = {int(it.get('attack', 0))}, def_ = {int(it.get('defense', 0))}}},\n"
items_lua += "}\n"
write("lib/naruto_items.lua", items_lua)
write("lib/naruto_jutsus.lua", HEADER_LUA + "-- nomes de todos os jutsus (para /jutsus do GM)\nNarutoJutsus = {\n" + "".join(f"\t\"{j['name']}\",\n" for j in jutsus.values()) + "}\n")

scripts = HEADER_LUA + """-- Coloque em data/scripts/naruto/quests_kill.lua (revscriptsys carrega sozinho)
local killEvent = CreatureEvent("NarutoQuestKill")
function killEvent.onKill(player, target)
	if not target:isMonster() then return true end
	local name = target:getName()
	for _, q in ipairs(NarutoQuests.list) do
		if q.monster == name then
			local st = player:getStorageValue(q.storage)
			if st >= 0 and st < q.count then
				player:setStorageValue(q.storage, st + 1)
				player:sendTextMessage(MESSAGE_EVENT_ADVANCE, q.name .. ": " .. (st + 1) .. "/" .. q.count)
			end
		end
	end
	return true
end
killEvent:register()

local login = CreatureEvent("NarutoQuestKillLogin")
function login.onLogin(player)
	player:registerEvent("NarutoQuestKill")
	player:registerEvent("NarutoBossPhases")
	return true
end
login:register()
"""
write("scripts/naruto/quests_kill.lua", scripts)

# bosses: fases via onHealthChange
phases = [HEADER_LUA, "-- Coloque em data/scripts/naruto/boss_phases.lua", "local PHASES = {"]
for m in monsters.values():
    if not m.get("boss"):
        continue
    phases.append(f"\t['{m['name']}'] = {{")
    for ph in m.get("phases", []):
        summons = ", ".join(f"{{name = '{monsters[s['monster_id']]['name']}', count = {s.get('count', 1)}}}" for s in ph.get("summons", []))
        msg = ph.get("message", "").replace("'", "\\'")
        look = f", looktype = {int(ph['looktype'])}" if ph.get("looktype") else ""
        phases.append(f"\t\t{{hp = {ph['hp_percent']}, mult = {ph.get('attack_multiplier', 1.0)}, message = '{msg}'{look}, summons = {{{summons}}}}},")
    phases.append("\t},")
phases.append("}")
phases.append("""
local fired = {}  -- monsterId -> índice da última fase disparada
local ev = CreatureEvent("NarutoBossPhases")
function ev.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)
	local list = PHASES[creature:getName()]
	if not list then return primaryDamage, primaryType, secondaryDamage, secondaryType end
	local id = creature:getId()
	local pct = (creature:getHealth() - primaryDamage) * 100 / creature:getMaxHealth()
	local idx = fired[id] or 0
	while idx < #list and pct <= list[idx + 1].hp do
		idx = idx + 1
		local ph = list[idx]
		if ph.message ~= '' then creature:say(ph.message, TALKTYPE_MONSTER_YELL) end
		for _, s in ipairs(ph.summons) do
			for _ = 1, s.count do
				local pos = creature:getPosition()
				pos.x = pos.x + math.random(-2, 2); pos.y = pos.y + math.random(-2, 2)
				local mon = Game.createMonster(s.name, pos, false, true)
				if mon and attacker then mon:setTarget(attacker) end
			end
		end
		if ph.looktype then
			-- transformação: troca o outfit do boss (ex.: humano -> serpente 2x2)
			local out = creature:getOutfit()
			out.lookType = ph.looktype
			out.lookHead, out.lookBody, out.lookLegs, out.lookFeet, out.lookAddons = 0, 0, 0, 0, 0
			creature:setOutfit(out)
			creature:getPosition():sendMagicEffect(CONST_ME_MAGIC_GREEN)
		end
		if ph.mult > 1.0 then
			-- LIMITAÇÃO: o onHealthChange não consegue alterar o dano dos <attack> do monstro
			-- em runtime (o TFS 1.4.2 lê a spell list uma vez, no carregamento do XML). A fase
			-- de "fúria" é aproximada por: (1) cura percentual, (2) aumento de velocidade, que
			-- faz o boss alcançar e bater mais vezes por minuto, e (3) registro em NarutoBossMult
			-- para quem quiser ler o multiplicador de fora (nenhum onThink é necessário).
			NarutoBossMult = NarutoBossMult or {}
			NarutoBossMult[id] = ph.mult
			local heal = math.floor(creature:getMaxHealth() * (ph.mult - 1.0) * 0.10)
			if heal > 0 then creature:addHealth(heal) end
			creature:changeSpeed(math.floor(creature:getBaseSpeed() * (ph.mult - 1.0) * 0.5))
			creature:getPosition():sendMagicEffect(CONST_ME_MAGIC_RED)
		end
	end
	fired[id] = idx
	return primaryDamage, primaryType, secondaryDamage, secondaryType
end
ev:register()

local reset = CreatureEvent("NarutoBossReset")
function reset.onDeath(creature) fired[creature:getId()] = nil return true end
reset:register()
""")
write("scripts/naruto/boss_phases.lua", "\n".join(phases) + "\n")

# ---------------------------------------------------------------- spawns (para o RME / spawns.xml)
for mp in maps.values():
    sp = ['<?xml version="1.0" encoding="UTF-8"?>', HEADER_XML.rstrip("\n"), '<!-- Referência de spawns. Coordenadas do protótipo (x,y) + offset; ajuste ao mapa .otbm real. -->', '<spawns>']
    for s in mp["spawns"]:
        m = monsters[s["monster_id"]]
        sp.append(f'\t<spawn centerx="{1000 + s["x"]}" centery="{1000 + s["y"]}" centerz="7" radius="3">')
        sp.append(f'\t\t<monster name="{escape(m["name"])}" x="0" y="0" z="7" spawntime="{m["respawn_s"]}"/>')
        sp.append('\t</spawn>')
    sp.append('</spawns>')
    write(f"world/{mp['id']}-spawn.xml", "\n".join(sp) + "\n")

# ---------------------------------------------------------------- README
write("README.md", f"""# server/generated — conteúdo gerado do TFS 1.4.2

Gerado por `tools/export_tfs.py` a partir de `data/*.json`. **Não edite à mão**; edite o JSON e regenere.

| Pasta | Destino no TFS | Como instalar |
|---|---|---|
| `monster/naruto/*.xml` | `data/monster/naruto/` | copiar a pasta |
| `monster/monsters_naruto.xml` | `data/monster/monsters.xml` | colar as linhas dentro de `<monsters>` |
| `spells/spells_naruto.xml` | `data/spells/spells.xml` | colar dentro de `<spells>` |
| `spells/scripts/naruto/*.lua` | `data/spells/scripts/naruto/` | copiar a pasta |
| `items/items_naruto.xml` | `data/items/items.xml` | colar (ids placeholder: ver `data/tfs_mapping.json`) |
| `XML/vocations.xml` | `data/XML/vocations.xml` | substituir o arquivo |
| `XML/outfits.xml` | `data/XML/outfits.xml` | substituir o arquivo (PENDENTE no install_generated.sh, ver relatório) |
| `lib/naruto_json.lua` | `data/lib/` + `dofile` em `lib.lua` | JSON puro em Lua (protocolo do opcode 210) |
| `lib/naruto_villages.lua` | `data/lib/` + `dofile` em `lib.lua` | `tools/install_generated.sh` |
| `lib/naruto_characters.lua` | `data/lib/` + `dofile` em `lib.lua` (depois de naruto_villages.lua e naruto_json.lua) | `tools/install_generated.sh` |
| `npc/naruto/*` | `data/npc/naruto/` | copiar a pasta |
| `lib/naruto_quests.lua` | `data/lib/` + `dofile` em `lib.lua` | ver cabeçalho |
| `scripts/naruto/*.lua` | `data/scripts/naruto/` | revscriptsys carrega sozinho |
| `world/*-spawn.xml` | referência para o Remere's Map Editor | manual |

Totais: {len(monsters)} monstros, {len(jutsus)} jutsus, {len(items)} itens, {len(npcs)} NPCs, {qi} missões, {len(villages)} vocações.
""")
print(f"OK: {len(monsters)} monstros, {len(jutsus)} jutsus, {len(items)} itens, {len(npcs)} NPCs, {qi} missões → server/generated/")
if SKIPPED_ITEM_IDS:
    print(f"\nAVISO: {len(SKIPPED_ITEM_IDS)} itens NÃO foram emitidos em items_naruto.xml porque o id do")
    print("mapping já existe no items.xml original do TFS (evita 'Duplicate item with id').")
    print("Troque esses ids em data/tfs_mapping.json por ids livres quando houver sprite próprio:")
    for our_id, iid in sorted(SKIPPED_ITEM_IDS, key=lambda x: x[1]):
        print(f"  - {our_id}: id {iid} SUBSTITUI o item vanilla (installer remove a entrada original)")
elif not VANILLA_ITEM_IDS:
    print("AVISO: server/tfs/data/items/items.xml não encontrado; ids duplicados não foram verificados.")

# ---------------------------------------------------------------- cliente: jutsus_data.lua
# O OTClient só conhece as spells da Tibia (modules/gamelib/spells.lua). Geramos aqui um
# perfil próprio de spelllist ("Shinobi") com os 25 jutsus, no MESMO formato de SpellInfo,
# carregado por modules/naruto_theme. Com isso a "Lista de Jutsus" e a barra de ação passam
# a conhecer e desenhar os jutsus. Os ícones vêm de tools/spr/gen_jutsu_icons.py.
CLIENT_MODULE = os.path.join(ROOT, "client-otc", "modules", "naruto_theme")
HEADER_CLIENT_LUA = (
    "-- GERADO por tools/export_tfs.py a partir de data/jutsus/*.json. NAO EDITE A MAO.\n"
    "-- Regenerar: python3 tools/export_tfs.py (e .venv/bin/python tools/spr/gen_jutsu_icons.py\n"
    "-- para a folha client-otc/data/images/game/spells/jutsus.png, que precisa da MESMA ordem).\n"
    "--\n"
    "-- ENCODING: arquivo ASCII puro. As fontes do OTClient sao bitmaps indexados por byte,\n"
    "-- entao acentos vao como escapes \\xNN em cp1252 (mesma regra de naruto_theme.lua).\n"
)

# Ordem dos icones na folha: PRECISA bater com jutsu_icon_order de tools/spr/gen_jutsu_icons.py.
ICON_ELEMENT_ORDER = ["katon", "suiton", "raiton", "doton", "fuuton", "none"]

def jutsu_icon_order(js):
    def key(j):
        el = j.get("element", "none")
        return (ICON_ELEMENT_ORDER.index(el) if el in ICON_ELEMENT_ORDER else len(ICON_ELEMENT_ORDER),
                int(j.get("tier", 1)), int(j.get("required_level", 1)), j["id"])
    return sorted(js, key=key)

# vocation_id (= clientid que o TFS manda no login) -> vocação "base" da Tibia que o OTClient usa.
# Cadeia: player:getVocation() devolve o clientid; modules/game_actionbar/logics/const.lua
# (translateVocation) e game_spelllist (selectDefaultVocation) mapeiam VocationsClient
# (Knight=1, Paladin=2, Sorcerer=3, Druid=4, Monk=5) para VocationsServer (base e base+4).
# Emitimos {base, base+4} para que tanto o filtro da Lista de Jutsus quanto o "posso usar?"
# da barra de ação aceitem o jutsu da vila certa — e só dela.
CLIENT_VOC_TO_TIBIA_BASE = {1: 4, 2: 3, 3: 1, 4: 2, 5: 9}

def lua_str(s):
    """String Lua em ASCII: acentos viram \\xNN no byte cp1252 (ver naruto_theme.lua)."""
    out = []
    for ch in str(s):
        if ch == "\\":
            out.append("\\\\")
        elif ch == "'":
            out.append("\\'")
        elif ch == "\n":
            out.append("\\n")
        elif 32 <= ord(ch) < 127:
            out.append(ch)
        else:
            for b in ch.encode("cp1252", errors="replace"):
                out.append("\\x%02X" % b)
    return "'" + "".join(out) + "'"

def jutsu_vocations(j):
    if not j["villages"]:
        vids = [vm["vocation_id"] for vm in M["villages"].values()]
    else:
        vids = [M["villages"][v]["vocation_id"] for v in j["villages"]]
    out = set()
    for vid in vids:
        base = CLIENT_VOC_TO_TIBIA_BASE.get(vid, vid)
        out.add(base)
        out.add(base + 4)
    return sorted(out)

ordered_jutsus = jutsu_icon_order(list(jutsus.values()))
cl = [HEADER_CLIENT_LUA,
      "-- Ajustes da folha de icones (mesmo formato de SpelllistSettings em gamelib/spells.lua).",
      "NarutoSpelllistProfile = 'Shinobi'",
      "NarutoSpelllistSettings = {",
      "    iconFile = '/images/game/spells/jutsus',",
      "    iconsForGameCooldown = '/images/game/spells/jutsus',",
      "    iconSize = { width = 32, height = 32 },",
      "    iconSizeCooldown = { width = 32, height = 32 },",
      "    spellListWidth = 210,",
      "    spellWindowWidth = 550,",
      "}",
      "",
      "-- [nome do jutsu] = posicao na folha jutsus.png; x = indice * 32, y = 0.",
      "NarutoSpellIcons = {"]
for i, j in enumerate(ordered_jutsus):
    cl.append("    [%s] = { x = %d, y = 0, index = %d }," % (lua_str(j["name"]), i * 32, i))
cl.append("}")
cl.append("")
cl.append("-- Mesmo formato de SpellInfo['Default']. 'words' sao os selos (= words do spells.xml).")
cl.append("NarutoSpellInfo = {")
for i, j in enumerate(ordered_jutsus):
    is_self = j["type"] == "self"
    group_id = 2 if is_self else 1
    need_target = "true" if j["type"] in ("projectile", "target") else "false"
    cl.append(
        "    [%s] = { id = %d, name = %s, words = %s, type = 'Instant', level = %d, mana = %d, "
        "soul = 0, maglevel = 0, icon = %s, clientId = %d, group = { [%d] = 1000 }, needTarget = %s, "
        "parameter = false, range = %d, exhaustion = %d, premium = false, vocations = { %s }, "
        "special = false, source = 0, description = %s }," % (
            lua_str(j["name"]), 900 + i, lua_str(j["name"]), lua_str(spell_words(j)),
            int(j["required_level"]), int(j["chakra_cost"]), lua_str(j["id"]), i, group_id,
            need_target, max(1, int(j["range"])), int(j["cooldown_s"] * 1000),
            ", ".join(str(v) for v in jutsu_vocations(j)), lua_str(j.get("description", "")),
        ))
cl.append("}")
cl.append("")
cl.append("-- Vilas por vocation_id (o que player:getVocation() devolve). setName e o nome do")
cl.append("-- conjunto de hotkeys do game_actionbar: ASCII puro, porque vira chave no JSON.")
cl.append("NarutoVillages = {")
for _v in load(os.path.join(DATA, "villages.json")):
    _vm = M["villages"][_v["id"]]
    _ascii = unicodedata.normalize("NFKD", _v["name"]).encode("ascii", "ignore").decode("ascii")
    cl.append("    [%d] = { id = %s, name = %s, setName = %s, element = %s }," % (
        _vm["vocation_id"], lua_str(_v["id"]), lua_str(_v["name"]), lua_str(_ascii), lua_str(_v["element"])))
cl.append("}")
cl.append("")
cl.append("-- Ordem sugerida da barra de acao: por level exigido, depois nome.")
cl.append("NarutoJutsuOrder = {")
for j in sorted(ordered_jutsus, key=lambda x: (int(x["required_level"]), x["name"])):
    cl.append("    %s," % lua_str(j["name"]))
cl.append("}")
cl.append("")
cl.append("-- Jutsus por PERSONAGEM (looktype 900-909): ver data/characters.json. Preenche a barra")
cl.append("-- de acao quando o jogador troca de personagem (naruto_jutsus.lua, onOutfitChange).")
cl.append("NarutoCharacterJutsus = {")
for c in characters:
    char_jutsus = [jutsus[jid] for jid in personal_jutsu_ids(c)]
    words_lua = ", ".join(lua_str(spell_words(j)) for j in char_jutsus)
    cl.append("    [%d] = { id = %s, name = %s, village = %s, words = { %s } }," % (
        int(c["looktype"]), lua_str(c["id"]), lua_str(c["name"]), lua_str(c["village"]), words_lua))
cl.append("}")
os.makedirs(CLIENT_MODULE, exist_ok=True)
with open(os.path.join(CLIENT_MODULE, "jutsus_data.lua"), "w", encoding="ascii") as f:
    f.write("\n".join(cl) + "\n")
print(f"OK: {len(ordered_jutsus)} jutsus -> client-otc/modules/naruto_theme/jutsus_data.lua")
print(f"OK: {len(characters)} personagens, {len(element_sets)} sets de elemento -> lib/naruto_characters.lua")
for _w in dict.fromkeys(WARNINGS):
    print("AVISO:", _w)
