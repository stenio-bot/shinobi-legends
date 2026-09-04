#!/usr/bin/env python3
"""Gera conteúdo do The Forgotten Server 1.4.2 a partir de data/*.json.
Saída em server/generated/ (copie para server/tfs/data/ conforme docs/04-setup-ot.md).
Uso: python3 tools/export_tfs.py
"""
import json, os, glob, shutil, math
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
for j in jutsus.values():
    el = M["elements"][j["element"]]
    need_target = 1 if j["type"] in ("projectile", "target") else 0
    group = "healing" if j["type"] == "self" else "attack"
    vocs = j["villages"] or list(villages.keys())
    voc_xml = "".join(f'\n\t<vocation name="{escape(voc_name(v))}"/>' for v in vocs)
    spells_xml.append(
        f'<instant group="{group}" name="{escape(j["name"])}" words="{spell_words(j)}" lvl="{j["required_level"]}" '
        f'mana="{j["chakra_cost"]}" prem="0" range="{max(1, j["range"])}" needtarget="{need_target}" blockwalls="1" '
        f'cooldown="{int(j["cooldown_s"]*1000)}" groupcooldown="1000" needlearn="{0 if int(j.get("tier",1)) == 1 else 1}" '
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
    villages_lua.append(f"\t[{voc_id}] = {{name = '{escape(vo['name'])}', default_outfit = {vo['default_outfit']}, outfits = {{{outfits_lua}}}}},")
villages_lua.append("}")
write("lib/naruto_villages.lua", "\n".join(villages_lua) + "\n")

village_outfit_script = HEADER_LUA + """-- Coloque em data/scripts/naruto/village_outfit.lua (revscriptsys carrega sozinho).
-- Na 1ª vez que o jogador loga, aplica o outfit padrão da vila (vocação) e libera os
-- outfits escolhíveis daquela vila (NarutoVillages, definido em data/lib/naruto_villages.lua).
local STORAGE_VILLAGE_OUTFIT = 60000

local ev = CreatureEvent("NarutoVillageOutfit")
function ev.onLogin(player)
	if player:getStorageValue(STORAGE_VILLAGE_OUTFIT) < 1 then
		local village = NarutoVillages[player:getVocation():getId()]
		if village then
			player:setOutfit({lookType = village.default_outfit})
			for _, look in ipairs(village.outfits) do
				player:addOutfit(look)
			end
		end
		player:setStorageValue(STORAGE_VILLAGE_OUTFIT, 1)
	end
	return true
end
ev:register()
"""
write("scripts/naruto/village_outfit.lua", village_outfit_script)

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
| `lib/naruto_villages.lua` | `data/lib/` + `dofile` em `lib.lua` | PENDENTE no install_generated.sh, ver relatório |
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
