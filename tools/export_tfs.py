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
        region = os.path.splitext(os.path.basename(p))[0]
        for o in load(p):
            o.setdefault("_region", region)  # arquivo de origem = regiao (usado p/ escopo de lojas)
            out[o["id"]] = o
    return out

def write(rel, text):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)

M = load(os.path.join(DATA, "tfs_mapping.json"))

# ---------------------------------------------------- catalogo de efeitos/misseis
# assets-src/sprites/effects.json (gerado por tools/spr/gen_effects.py): ids
# numericos (u8, protocolo 10.98) dos efeitos/misseis proprios por jutsu, mais o
# alias `animation` (data/jutsus/*.json) -> chave do catalogo e o fallback por
# elemento. Ver docs/sistemas/combate-e-jutsus.md, secao "Efeitos e misseis".
_effects_cat = load(os.path.join(DATA, "..", "assets-src", "sprites", "effects.json"))
EFFECT_CATALOG = {e["key"]: e for e in _effects_cat["entries"]}
EFFECT_ALIASES = _effects_cat["aliases"]
EFFECT_ELEMENT_DEFAULTS = _effects_cat["element_defaults"]

def _catalog_id(key, kind):
    e = EFFECT_CATALOG.get(key)
    return e["id"] if e and e["kind"] == kind else None

def jutsu_effect_id(j):
    """Id numerico (CONST_ME_*) para COMBAT_PARAM_EFFECT deste jutsu.
    Projetil: efeito de IMPACTO generico do elemento (o `animation` do jutsu
    descreve o misseis em voo, nao o impacto). Demais tipos: o efeito
    especifico do jutsu via alias de `animation`, com fallback pro elemento."""
    el = j["element"] if j["element"] in EFFECT_ELEMENT_DEFAULTS else "none"
    if j["type"] == "projectile":
        return _catalog_id(EFFECT_ELEMENT_DEFAULTS[el]["effect"], "effect")
    key = EFFECT_ALIASES.get(j.get("animation"))
    eid = _catalog_id(key, "effect") if key else None
    return eid if eid is not None else _catalog_id(EFFECT_ELEMENT_DEFAULTS[el]["effect"], "effect")

def jutsu_missile_id(j):
    """Id numerico (CONST_ANI_*) para COMBAT_PARAM_DISTANCEEFFECT (so type=projectile)."""
    el = j["element"] if j["element"] in EFFECT_ELEMENT_DEFAULTS else "none"
    key = EFFECT_ALIASES.get(j.get("animation"))
    mid = _catalog_id(key, "missile") if key else None
    return mid if mid is not None else _catalog_id(EFFECT_ELEMENT_DEFAULTS[el]["missile"], "missile")

jutsus = load_folder("jutsus")
items = load_folder("items")
monsters = load_folder("monsters")
npcs = load_folder("npcs")
villages = {v["id"]: v for v in load(os.path.join(DATA, "villages.json"))}
elements = load(os.path.join(DATA, "elements.json"))
prog = load(os.path.join(DATA, "progression.json"))
maps = {m["id"]: m for m in (load(p) for p in glob.glob(os.path.join(DATA, "maps", "*.json")))}
characters = load(os.path.join(DATA, "characters.json"))
ranks_list = load(os.path.join(DATA, "ranks.json"))

def load_optional(rel):
    """data/tasks.json e data/dailies.json são opcionais: se não existirem, os sistemas
    correspondentes (NarutoTasks/NarutoDailies) simplesmente não são gerados (compat)."""
    p = os.path.join(DATA, rel)
    return load(p) if os.path.exists(p) else None

tasks_data = load_optional("tasks.json")
dailies_data = load_optional("dailies.json")
achievements_data = load_optional("achievements.json")

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

# teto de level por regiao (arquivo data/npcs/<regiao>.json) para o que cada mercador compra de volta
SHOP_LEVEL_CAP = {"leaf": 15, "coastal_tides": 25, "swamp": 30, "ruins": 55, "mountain": 85, "akatsuki_lair": 100}

def item_id(our_id):
    return int(M["items"].get(our_id, 0))

UNMAPPED_REWARD_ITEMS = set()

def reward_items_lua(item_ids_list):
    """Lua de {id=.., count=1} para uma lista de item ids de recompensa (quest/task/daily).
    Item sem id mapeado em data/tfs_mapping.json (item_id()==0) é OMITIDO (e listado no aviso
    final) em vez de virar `{id=0, ...}`, que faria player:addItem(0, 1) falhar silenciosamente
    (ou pior) em runtime — comum em conteúdo novo (ex.: troféus 'trophy_*') que ainda não tem
    entrada em tfs_mapping.json (fora do escopo desta missão editar esse arquivo)."""
    rows = []
    for our_id in item_ids_list:
        iid = item_id(our_id)
        if iid == 0:
            UNMAPPED_REWARD_ITEMS.add(our_id)
            continue
        rows.append(f"{{id = {iid}, count = 1}}")
    return ", ".join(rows)

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
    # SFX (docs/sistemas/audio.md): sem gancho client-side para "efeito visto na tela",
    # o servidor avisa o cliente via opcode 210 (NarutoJson.broadcastSfx) no cast.
    # `if NarutoJson.broadcastSfx then` blinda contra o `data/lib/*.lua` do processo
    # em memoria ainda ser o de ANTES desta funcao existir (libs so recarregam com
    # reinicio do servidor - /reload spells|scripts|all NAO os toca; achado real ao
    # testar sem reiniciar o servidor compartilhado, ver docs/sistemas/audio.md) -
    # sem a blindagem, o cast inteiro falhava com "attempt to call field
    # 'broadcastSfx' (a nil value)" em vez de so pular o som.
    sfx_call = (f'\n\tif NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(pos, "{j["sfx"]}") end'
                if j.get("sfx") else "")
    need_target = 1 if j["type"] in ("projectile", "target") else 0
    group = "healing" if j["type"] == "self" else "attack"
    # NOVO MODELO: jutsu não é mais filtrado por vila — quem controla o acesso é o
    # learnSpell/forgetSpell de NarutoCharacters.apply (personagem + elemento escolhidos).
    # Por isso TODAS as vocações entram no <instant>; o campo `villages` do JSON só sobrevive
    # como metadado de lore/cliente.
    voc_xml = "".join(f'\n\t<vocation name="{escape(voc_name(v))}"/>' for v in villages.keys())
    # RODADA 5 (economia de chakra, item 1c): jutsu com `chakra_cost_percent` (hoje só os 5
    # projéteis tier 1 elementais) usa `manapercent` em vez de `mana` — server/tfs/src/spells.cpp
    # configureSpell lê os dois atributos (linha ~462/466) e Spell::getManaCost (linha ~804)
    # prioriza `mana` se != 0, senão calcula `(maxMana * manaPercent) / 100` (mesma divisão
    # inteira truncada que tools/balance/sim.py replica em `jutsu_chakra_cost`). chakra_cost=0
    # no JSON para esses jutsus é o sinal (schema: mutuamente exclusivos).
    if j.get("chakra_cost_percent"):
        mana_attr = f'mana="0" manapercent="{int(j["chakra_cost_percent"])}"'
    else:
        mana_attr = f'mana="{j["chakra_cost"]}"'
    spells_xml.append(
        # spellid PRECISA ser único: sem ele, TFS 1.4.2 usa 0 para TODOS os instants
        # (spells.h: uint8_t spellId = 0) e o cooldown "cooldown_s" de QUALQUER jutsu
        # passa a bloquear TODOS os outros (mesmo de grupo/elemento diferente).
        f'<instant group="{group}" name="{escape(j["name"])}" words="{spell_words(j)}" lvl="{j["required_level"]}" '
        f'{mana_attr} prem="0" range="{max(1, j["range"])}" needtarget="{need_target}" blockwalls="1" '
        f'aggressive="{0 if group == "healing" else 1}" spellid="{spell_idx}" '
        f'cooldown="{int(j["cooldown_s"]*1000)}" groupcooldown="1000" needlearn="{0 if j["id"] in UNIVERSAL_JUTSU_IDS else 1}" '
        f'script="naruto/{j["id"]}.lua">{voc_xml}\n</instant>')

    lua = [HEADER_LUA, f"-- {j['name']}: {j.get('description','')}"]
    if j["type"] == "self":
        if j["id"] == "kawarimi":
            poof_id = jutsu_effect_id(j)  # fx_smoke_poof (catalogo em assets-src/sprites/effects.json)
            lua.append(f"""function onCastSpell(creature, variant)
	local pos = creature:getPosition(){sfx_call}
	local dir = creature:getDirection()
	local back = Position(pos)
	for _ = 1, 2 do
		back:getNextPosition(dir == DIRECTION_NORTH and DIRECTION_SOUTH or dir == DIRECTION_SOUTH and DIRECTION_NORTH or dir == DIRECTION_EAST and DIRECTION_WEST or DIRECTION_EAST)
	end
	local tile = Tile(back)
	if tile and tile:isWalkable() and not tile:hasFlag(TILESTATE_BLOCKSOLID) then
		pos:sendMagicEffect({poof_id})
		creature:teleportTo(back)
		back:sendMagicEffect({poof_id})
		local cond = Condition(CONDITION_INVISIBLE)
		cond:setParameter(CONDITION_PARAM_TICKS, 1000)
		creature:addCondition(cond)
		return true
	end
	creature:sendCancelMessage("Não há espaço para a substituição.")
	pos:sendMagicEffect({poof_id})
	return false
end""")
        elif j["id"] == "bunshin":
            clone_id = jutsu_effect_id(j)  # fx_shadow_clone (distinto do poof do kawarimi)
            lua.append(f"""-- TODO: criar monstro 'Clone' (cópia do outfit do jogador, 1 HP, some em 6s) e usar creature:addSummon.
function onCastSpell(creature, variant)
	local pos = creature:getPosition(){sfx_call}
	pos:sendMagicEffect({clone_id})
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
            buff_id = jutsu_effect_id(j)  # por jutsu via alias de `animation` (heal, aura, selo, armadura...)
            lua.append(f"""local condition = Condition(CONDITION_REGENERATION)
condition:setParameter(CONDITION_PARAM_SUBID, 1)
condition:setParameter(CONDITION_PARAM_TICKS, {d*1000})
condition:setParameter(CONDITION_PARAM_HEALTHGAIN, {v})
condition:setParameter(CONDITION_PARAM_HEALTHTICKS, 1000)

function onCastSpell(creature, variant)
	creature:addCondition(condition)
	local pos = creature:getPosition(){sfx_call}
	pos:sendMagicEffect({buff_id})
	return true
end""")
    else:
        lua.append(f"""local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, {el["combat"]})
combat:setParameter(COMBAT_PARAM_EFFECT, {jutsu_effect_id(j)})""")
        if j["type"] == "projectile":
            lua.append(f"combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, {jutsu_missile_id(j)})")
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
        combat_sfx_line = (f'\n\tif NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "{j["sfx"]}") end'
                           if j.get("sfx") else "")
        lua.append(f"""
function onCastSpell(creature, variant){combat_sfx_line}
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
                   "skill_genjutsu": "skillClub", "skill_defense": "skillShield",
                   # FIX (rodada 2 do balanceamento, item 10 da rodada 1): "attack"/"defense" de
                   # bonuses de acessório eram silenciosamente descartados aqui (ring_stone_will,
                   # strings_of_the_puppeteer) — items.cpp:22/25 registram "armor"/"attack" como
                   # atributos genéricos válidos em QUALQUER item, não só weapon/armor.
                   "attack": "attack", "defense": "armor"}.get(k)
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
# Multiplicador base = 1.1 para TODAS as skills treináveis (data/skills.json: "tries_formula":
# "50 * 1.1^(skill - 10)"). ANTES deste fix (tools/balance/, achado do simulador de balanceamento)
# o gerador usava 1.5-2.0 (copiado de um template de vocação padrão do TFS) — com mult=2.0 o
# custo em tentativas DOBRA por nível de skill, contradizendo o próprio data/skills.json e
# deixando taijutsu/shuriken praticamente parados (skill ~17-25 do nível 5 ao 100). O simulador
# (tools/balance/sim.py) mostrou que isso torna builds de taijutsu puro inviáveis (~100% de
# morte contra monstros do mesmo nível a partir de L5) porque o dano de arma
# (weapons.cpp:135 getMaxWeaponDamage) depende de `skill/4+1`, que fica baixo demais.
for vid, v in villages.items():
    vm = M["villages"][vid]
    mults = {0: 1.1, 1: 1.1, 2: 1.1, 3: 1.1, 4: 1.1, 5: 1.1, 6: 1.1}
    bonus = v["bonus_skill"]
    # manamultiplier: era 4.0 na versão original (padrão de vocação de mago do TFS/Tibia clássico,
    # nunca calibrado pra este jogo), depois 1.3 (rodada 1 do balanceamento). getReqMana(ML) =
    # 1600*mult^(ML-1) (vocation.cpp:149, base 1600 fixo no C++, não editável por aqui). FIX
    # RODADA 3: com mult=1.3, tools/balance/sim.py mediu o magic level crescendo de forma quase
    # RETA (~16 no L15 a ~34 no L100, menos de 2.2x em 85 níveis) enquanto o dano de arma
    # (weapons.cpp:135, depende de skill/4+1 × attack da arma de tier) cresce ~40x no mesmo
    # intervalo — magic level baixo estruturalmente impedia jutsu tier 2/3 (que dependem de
    # maglevel*skill_scale) de acompanhar a curva de arma em L50+, fazendo o build ninjutsu
    # degenerar em taijutsu puro nesse trecho (achado central da rodada 3, ver
    # docs/sistemas/balanceamento-relatorio-v3.md §1-2). mult=1.1 (igual às outras skills,
    # data/skills.json) faz o magic level crescer de ~23 (L5) a ~83 (L100) — mesma ordem de
    # grandeza do taijutsu (skill ~40 a ~101) pela primeira vez, permitindo que skill_scale volte
    # a ser um lever de verdade. O level_scale/skill_scale de cada jutsu tier 2/3 (data/jutsus/
    # *.json) foi recalibrado nesta rodada assumindo esse novo mult=1.1 — não troque um sem o
    # outro.
    mana_mult = 1.1
    if bonus in skill_ids:
        mults[skill_ids[bonus]] = round(mults[skill_ids[bonus]] / 1.2, 2)
    elif bonus == "ninjutsu":
        mana_mult = 1.1 / 1.2
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

-- ------------------------------------------------------------------ SFX (opcode 210, acao "sfx")
-- Gancho de audio do cliente (docs/sistemas/audio.md): o OTClient Redemment nao tem
-- callback Lua para "efeito magico visto na tela" (parseMagicEffect e' so C++, nao chama
-- callLuaField nenhum - conferido em src/client/protocolgameparse.cpp), entao o som de
-- jutsu e' avisado pelo SERVIDOR via opcode 210 para o conjurador + quem esta por perto.
-- modules/naruto_menu.lua (dono do opcode 210 no cliente) despacha type == 'sfx' para
-- modules/naruto_sounds.lua.
local SFX_OPCODE = 210

--- Manda {"type":"sfx","id":sfxId} para o conjurador e criaturas/jogadores num raio de
--- `radius` tiles (padrao 7, igual ao alcance de visao normal da tela) ao redor de `pos`.
--- So chega a clientes OTClient (sendExtended ja filtra isUsingOtClient); nao quebra nada
--- se sfxId vier nil (spell sem campo `sfx` no JSON).
function NarutoJson.broadcastSfx(pos, sfxId, radius)
	if not sfxId then return end
	radius = radius or 7
	local payload = NarutoJson.encode({type = 'sfx', id = sfxId})
	for _, spec in ipairs(Game.getSpectators(pos, false, false, radius, radius, radius, radius)) do
		if spec:isPlayer() then
			NarutoJson.sendExtended(spec, SFX_OPCODE, payload)
		end
	end
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

def jutsu_display_chakra_cost(j):
    """Custo de chakra pra exibição no cliente (telas estáticas: seleção de personagem, tooltip
    do spellbar) — os dois lugares SÓ mostram um número fixo, sem contexto de nível do jogador.
    Pra jutsu com `chakra_cost_percent` (RODADA 5, tier 1 elemental — custo real é dinâmico,
    `manapercent` no servidor, ver spells_xml acima), mostra o custo no nível em que o jutsu é
    desbloqueado (`required_level`, sempre 1 pros 5 tier 1) usando a MESMA fórmula de pool de
    data/progression.json (100+level*10) — aproximação cosmética, não o valor real em todo nível
    (o cliente não recalcula isso dinamicamente; fora do escopo desta rodada mexer no client-otc)."""
    pct = j.get("chakra_cost_percent")
    if pct:
        ref_level = max(1, j.get("required_level", 1))
        ref_pool = 100 + ref_level * 10
        return (ref_pool * int(pct)) // 100
    return int(j["chakra_cost"])

def jutsu_lua(jid):
    """Uma entrada de jutsu no formato que o cliente espera (opcode 210)."""
    j = jutsus[jid]
    return ("{id = %s, name = %s, words = %s, element = %s, type = %s, chakra = %d, cooldown_s = %s}" % (
        lua_q(j["id"]), lua_q(j["name"]), lua_q(spell_words(j)), lua_q(j.get("element", "none")),
        lua_q(j["type"]), jutsu_display_chakra_cost(j), repr(float(j["cooldown_s"]))))

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

	-- rank (docs/sistemas/progressao-servidor.md): discreto, so id/titulo/indice - o cliente
	-- mostra ao lado do nome/skills. NarutoRanks pode nao existir (compat); nesse caso null.
	local rankInfo = NarutoJson.null
	if NarutoRanks then
		local r = NarutoRanks.get(player)
		rankInfo = {id = r.rank, title = r.title, index = r.index}
	end

	local state = {
		type = 'state',
		first_time = firstTime == true,
		is_gm = isGm,
		character = char and char.id or NarutoJson.null,
		element = element and element.id or NarutoJson.null,
		level = player:getLevel(),
		village = villageIdOf(player) or NarutoJson.null,
		rank = rankInfo,
		characters = chars,
		elements = els,
		active_jutsus = active,
	}
	return NarutoJson.sendExtended(player, OPCODE, NarutoJson.encode(state))
end

-- ------------------------------------------------------------------ progresso (opcode 210,
-- acao get_progress) - aba Missoes do menu Shinobi: rank + proximo rank (requisitos
-- pendentes), tarefas ativas, diarias do dia e missoes de historia com status.
-- NarutoRanks/NarutoQuests/NarutoTasks/NarutoDailies sao globais definidos em outras libs
-- (data/lib/naruto_ranks.lua, naruto_quests.lua, naruto_tasks.lua, naruto_dailies.lua) - todas
-- ja carregadas por dofile em data/lib/lib.lua antes de qualquer jogador logar; guardas `if X
-- then` sao so para o caso raro de uma delas nao existir (compat, ex.: sem data/tasks.json).
local function nextRankRequirements(player, nextRank)
	local reqs = NarutoJson.array({})
	if not NarutoQuests or not nextRank then return reqs end
	local group = NarutoQuests.rankGroups[nextRank.rank]
	if not group then return reqs end
	for _, storage in ipairs(group) do
		local q = NarutoQuests.byStorage and NarutoQuests.byStorage[storage]
		if q then
			reqs[#reqs + 1] = {
				name = q.name,
				npc = q.npcName or q.npc,
				done = player:getStorageValue(storage) == NarutoQuests.DONE,
			}
		end
	end
	return reqs
end

local function rankProgressJson(player)
	if not NarutoRanks then return NarutoJson.null end
	local cur = NarutoRanks.get(player)
	local out = {id = cur.rank, title = cur.title, index = cur.index}
	local nextRank = NarutoRanks.byIndex[cur.index + 1]
	if nextRank then
		out.next = {
			id = nextRank.rank, title = nextRank.title, index = nextRank.index,
			minLevel = nextRank.minLevel, requirements = nextRankRequirements(player, nextRank),
		}
	else
		out.next = NarutoJson.null
	end
	return out
end

local function tasksProgressJson(player)
	local out = NarutoJson.array({})
	if not NarutoTasks then return out end
	local now = os.time()
	for _, t in ipairs(NarutoTasks.list) do
		local prog = player:getStorageValue(t.progressStorage)
		if prog >= 0 then
			local cooldownUntil = player:getStorageValue(t.cooldownStorage)
			local remaining = 0
			if cooldownUntil and cooldownUntil > now then
				remaining = math.ceil((cooldownUntil - now) / 60)
			end
			out[#out + 1] = {
				id = t.id, name = t.name, npc = t.npcName, monster = t.monster,
				progress = prog, count = t.count, ready = prog >= t.count,
				cooldownRemainingMin = remaining,
			}
		end
	end
	return out
end

local function dailiesProgressJson(player)
	local out = NarutoJson.array({})
	if not NarutoDailies then return out end
	NarutoDailies.rollIfNeeded(player)
	for slot = 1, 3 do
		local entry = NarutoDailies.slotEntry(player, slot)
		if entry then
			local prog = NarutoDailies.slotProgress(player, slot)
			local status
			if prog > entry.count then
				status = 'delivered'
			elseif prog == entry.count then
				status = 'ready'
			else
				status = 'progress'
			end
			out[#out + 1] = {
				slot = slot, id = entry.id, name = entry.name, monster = entry.monster,
				progress = math.max(prog, 0), count = entry.count, status = status,
			}
		end
	end
	return out
end

local function missionsProgressJson(player)
	local out = NarutoJson.array({})
	if not NarutoQuests then return out end
	for _, q in ipairs(NarutoQuests.list) do
		local st = player:getStorageValue(q.storage)
		local status
		if st == NarutoQuests.DONE then
			status = 'done'
		elseif st < 0 then
			status = 'available'
		else
			status = 'in_progress'
		end
		-- NOVO (docs/sistemas/missoes.md, requisito 8 da extensão de tipos de missão): 'kind' e
		-- 'progress' (texto curto, "3/5 itens"/"Chegou!"/etc. — NarutoQuests.progressText) para a
		-- aba Missões do menu Shinobi mostrar o tipo/progresso sem precisar falar com o NPC.
		-- 'boss' só existe (e só é true) em quests kind='kill' com objective.boss — ausente nas
		-- demais, então um cliente antigo que ignora o campo continua funcionando igual.
		out[#out + 1] = {
			id = q.id, name = q.name, npc = q.npcName or q.npc, status = status,
			kind = q.kind, progress = NarutoQuests.progressText(player, q), boss = q.boss or false,
		}
	end
	return out
end

--- Conquistas (NarutoAchievements, data/lib/naruto_achievements.lua): delega tudo para
--- NarutoAchievements.progressJson (lá mora a lista/categoria/progresso de cada uma) -
--- guarda `if` só para o caso raro de rodar sem data/achievements.json (compat).
local function achievementsProgressJson(player)
	if not NarutoAchievements then return NarutoJson.array({}) end
	return NarutoAchievements.progressJson(player)
end

--- Monta e envia o `progress` para o cliente (opcode 210, buffer JSON) - aba Missoes.
function NarutoCharacters.sendProgress(player)
	if not player or not player:isPlayer() then return false end
	local progress = {
		type = 'progress',
		rank = rankProgressJson(player),
		tasks = tasksProgressJson(player),
		dailies = dailiesProgressJson(player),
		missions = missionsProgressJson(player),
		achievements = achievementsProgressJson(player),
	}
	return NarutoJson.sendExtended(player, OPCODE, NarutoJson.encode(progress))
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
	elseif msg.type == 'get_progress' then
		NarutoCharacters.sendProgress(player)
	end
	return true
end
opcodeEvent:register()

-- kit inicial por vocacao (gerado de data/villages.json + tfs_mapping.items)
local STARTING_KIT = {STARTING_KIT_LUA}

-- ------------------------------------------------------------------ regen (rodada 5)
-- Regen de HP/chakra escalando com o level (rodada 5, item 1a da missao de balanceamento —
-- docs/sistemas/balanceamento-relatorio-v5.md par. 1): a rodada 4 usava os valores FIXOS da
-- vocacao (vocations.xml gainhp/gainmana, gerados por tools/export_tfs.py ~linha 571 -- 0,4
-- HP/s e 0,6 chakra/s pra QUALQUER level) -- contra um pool de chakra que cresce (100+level*10),
-- 0,6/s virava irrelevante ja em L15 (achado da rodada 4 secao 5: 93-98% do tempo de uma hunt de
-- 30min sem chakra pro tier 1 em L5/L15). NarutoRegen.apply reaplica a condicao (mesmo subId
-- 9020 -- server/tfs/src/creature.cpp Creature::addCondition substitui condicao de mesmo
-- tipo+subId) com o valor calculado pro level ATUAL -- chamada no login e a cada level-up
-- (CreatureEvent NarutoRegenAdvance abaixo, mesmo padrao onAdvance(player,skill,old,new) que
-- NarutoAchievementAdvance ja usa pra SKILL_LEVEL). Formulas (replicadas em
-- tools/balance/sim.py chakra_regen_amount_per_tick/hp_regen_amount_per_tick, tunadas por
-- simulacao -- ver relatorio v5): chakra +[3+floor(level/4)] a cada 2s (era +3 a cada 5s pra
-- TODO level); HP +[2+floor(level/10)] a cada 5s (em L1-9 e EXATAMENTE o valor antigo, so
-- acelera a partir de L10 -- pool de HP tambem cresce e o valor fixo ficaria imperceptivel
-- tarde no jogo pelo mesmo motivo do chakra).
local NarutoRegen = {}
function NarutoRegen.apply(player)
	local level = player:getLevel()
	local regen = Condition(CONDITION_REGENERATION, CONDITIONID_DEFAULT)
	regen:setParameter(CONDITION_PARAM_SUBID, 9020)
	regen:setParameter(CONDITION_PARAM_TICKS, -1)
	regen:setParameter(CONDITION_PARAM_HEALTHGAIN, 2 + math.floor(level / 10))
	regen:setParameter(CONDITION_PARAM_HEALTHTICKS, 5000)
	regen:setParameter(CONDITION_PARAM_MANAGAIN, 3 + math.floor(level / 4))
	regen:setParameter(CONDITION_PARAM_MANATICKS, 2000)
	player:addCondition(regen)
end

local regenAdvance = CreatureEvent("NarutoRegenAdvance")
function regenAdvance.onAdvance(player, skill, oldLevel, newLevel)
	if skill == SKILL_LEVEL then
		NarutoRegen.apply(player)
	end
	return true
end
regenAdvance:register()

-- ------------------------------------------------------------------ login
local login = CreatureEvent("NarutoCharacterLogin")
function login.onLogin(player)
	player:registerEvent("NarutoOpcode")
	player:registerEvent("NarutoRegenAdvance")
	local firstTime = player:getStorageValue(STORAGE_ONBOARDED) < 1
	-- Reserva de chakra inicial: o TFS cria o jogador com 0 de mana e as vocacoes dao +10/level,
	-- mas os jutsus tier 1 custam 2,5-3,0% do pool (chakra_cost_percent, rodada 5) -- sem isso
	-- um Genin novo nao consegue lancar NADA ate o level 3. Piso de 110 de chakra (rodada 5, era
	-- 60 -- combinado com o gainmana=10/level da vocacao (inalterado) reproduz exatamente a
	-- curva 100+level*10 de data/progression.json em qualquer level, nao so' no L1). 110*0,03=
	-- ~3 de custo por cast, 36+ casts do pool inicial -- folga generosa sobre o minimo de 4
	-- pedido pela missao — ver relatorio v5 §1.
	if firstTime and player:getMaxMana() < 110 then
		player:setMaxMana(110)
		player:addMana(110)
	end
	-- Regeneracao natural de HP/chakra (playtest r3, 2026-09-05): no TFS a regeneracao so' roda
	-- enquanto o jogador tem comida (Player.feed em lib/core/player.lua). Num jogo de ninja o
	-- chakra volta sozinho -- ver NarutoRegen.apply acima (rodada 5: agora escala com level).
	NarutoRegen.apply(player)
	-- Kit inicial da vila (data/villages.json starting_items): o AAC/TFS criam o jogador so' com
	-- o kit vanilla (bag/jacket). Sem arma o Genin novo morre pros 3 lobos da trilha (playtest
	-- 2026-09-05). addItem com slot WHEREEVER equipa automaticamente o que couber no slot.
	if firstTime then
		local kit = STARTING_KIT[player:getVocation():getId()]
		if kit then
			for _, itemId in ipairs(kit) do player:addItem(itemId, 1) end
		end
	end
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
# kit inicial por vocacao: data/villages.json starting_items -> ids TFS (tfs_mapping.items); ids sem
# mapeamento sao pulados com aviso (nao pode quebrar o login).
_kit_rows = []
for _vid, _v in villages.items():
    _voc = M["villages"][_vid]["vocation_id"]
    _ids = []
    for _iid in _v.get("starting_items", []):
        if item_id(_iid):
            _ids.append(str(item_id(_iid)))
        else:
            print(f"AVISO: starting_item '{_iid}' da vila {_vid} sem id em tfs_mapping.json (pulado)")
    _kit_rows.append(f"[{_voc}] = {{{', '.join(_ids)}}}")
character_switch_script = character_switch_script.replace("{STARTING_KIT_LUA}", "{" + ", ".join(_kit_rows) + "}")
write("scripts/naruto/character_switch.lua", character_switch_script)

# ---------------------------------------------------------------- NPCs
NPC_QUIZ_NORMALIZE = """local function normalizeQuiz(s)
	s = tostring(s):lower()
	local map = {['\\195\\161']='a', ['\\195\\160']='a', ['\\195\\163']='a', ['\\195\\162']='a',
		['\\195\\169']='e', ['\\195\\170']='e', ['\\195\\173']='i', ['\\195\\179']='o',
		['\\195\\181']='o', ['\\195\\180']='o', ['\\195\\186']='u', ['\\195\\167']='c'}
	for accented, plain in pairs(map) do s = s:gsub(accented, plain) end
	return s
end"""

def npc_files(n):
    o = M["npc_outfits"].get(n["id"], {"type": 128, "head": 0, "body": 0, "legs": 0, "feet": 0})
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n' + HEADER_XML +
           f'<npc name="{escape(n["name"])}" script="naruto/{n["id"]}.lua" walkinterval="2000" floorchange="0">\n'
           f'\t<health now="100" max="100"/>\n\t<look type="{o["type"]}" head="{o["head"]}" body="{o["body"]}" legs="{o["legs"]}" feet="{o["feet"]}"/>\n</npc>\n')
    lua = [HEADER_LUA, "local keywordHandler = KeywordHandler:new()", "local npcHandler = NpcHandler:new(keywordHandler)",
           "NpcSystem.parseParameters(npcHandler)", "",
           "function onCreatureAppear(cid) npcHandler:onCreatureAppear(cid) end",
           "function onCreatureDisappear(cid) npcHandler:onCreatureDisappear(cid) end",
           "function onThink() npcHandler:onThink() end", ""]
    # NOVO (docs/sistemas/missoes.md): objective.kind='talk_to' completa quando o jogador fala a
    # keyword (default 'missao') com o NPC ALVO (obj.npc), que pode ser QUALQUER npc do jogo (shop,
    # tasks, dailies, quest...), não só o NPC que deu a missão — por isso este bloco entra em TODO
    # npc gerado, não só nos type='quest'. NarutoQuests.list já está populado quando este script
    # carrega (dofile de data/lib/naruto_quests.lua roda antes de data/npc/scripts/naruto/*.lua no
    # boot do TFS — ver docs/03-decisoes-tecnicas.md/armadilhas do CLAUDE.md), então o filtro abaixo
    # roda uma vez, na carga do script. Se nenhuma quest do jogo mirar este npc (sempre o caso hoje,
    # nenhuma quest real usa talk_to ainda), TALK_TO_QUESTS fica vazio e NADA é registrado — zero
    # mudança de comportamento pros NPCs existentes.
    lua.append(f"""local TALK_TO_QUESTS = {{}}
if NarutoQuests then
	for _, q in ipairs(NarutoQuests.list) do
		if q.kind == 'talk_to' and q.targetNpc == {lua_q(n['id'])} then
			TALK_TO_QUESTS[#TALK_TO_QUESTS + 1] = q
		end
	end
end
if #TALK_TO_QUESTS > 0 then
	local function narutoTalkToCallback(cid, message, keywords, parameters, node)
		if not npcHandler:isFocused(cid) then return false end
		local player = Player(cid)
		if not player then return false end
		for _, q in ipairs(TALK_TO_QUESTS) do
			local msg = NarutoQuests.completeTalkTo(player, q)
			if msg then
				npcHandler:say(msg, cid)
				return true
			end
		end
		return false
	end
	local narutoTalkToSeen = {{}}
	for _, q in ipairs(TALK_TO_QUESTS) do
		local kw = q.keyword or 'missao'
		if not narutoTalkToSeen[kw] then
			narutoTalkToSeen[kw] = true
			keywordHandler:addKeyword({{kw}}, narutoTalkToCallback, {{}})
		end
	end
end""")
    needs_custom_say = False
    if n["type"] == "shop":
        lua.append("local shopModule = ShopModule:new()\nnpcHandler:addModule(shopModule)")
        for iid in n.get("sells", []):
            it = items[iid]
            lua.append(f"shopModule:addBuyableItem({{'{it['name'].lower()}'}}, {item_id(iid)}, {it['buy_price']}, 1, '{it['name'].lower()}')")
        # Escopo do que o mercador compra de volta: só itens ate' o teto de level da regiao do NPC
        # (playtest 2026-09-05: o mercador da Folha comprava troféus de boss final e sets Anbu —
        # ~130 entradas — e a lista com buy=-1 estourava o range check do openShopWindow).
        cap = SHOP_LEVEL_CAP.get(n.get("_region"), 100)
        for it in items.values():
            # NOVO (docs/sistemas/missoes.md): item quest_item=true (usado num objective.kind=
            # 'collect_item') nunca entra na lista de venda de nenhum mercador, mesmo se o tipo
            # dele estiver em buys_types — senão o jogador venderia o item antes de entregar.
            if it["type"] in n.get("buys_types", []) and it["sell_price"] > 0 and item_id(it["id"]) \
                    and it.get("required_level", 0) <= cap and not it["id"].startswith("trophy_") \
                    and not it.get("quest_item"):
                lua.append(f"shopModule:addSellableItem({{'{it['name'].lower()}'}}, {item_id(it['id'])}, {it['sell_price']}, '{it['name'].lower()}')")
        lua.append(f'npcHandler:setMessage(MESSAGE_GREET, "Olá, |PLAYERNAME|. Diga {{trade}} para ver o que tenho.")')
    elif n["type"] == "quest":
        # NOVO (docs/lore/progressao.md, docs/sistemas/progressao-servidor.md): além do fluxo
        # 'missao' de sempre, quests com objective.kind='keyword_quiz' (ex.: exam_chunin_1_teoria)
        # abrem uma prova por palavra-chave (NPC pergunta, jogador responde livre, N perguntas
        # em sequência; acertos >= quizMin aprovam). Estado da prova é por cid (em memória: se o
        # jogador desconectar no meio, a prova reseta — ver pendências).
        lua.append("local QUESTS = NarutoQuests.byNpc['%s']" % n["id"])
        lua.append(NPC_QUIZ_NORMALIZE)
        lua.append("""
local quizState = {}  -- cid -> {quest = q, idx = 1, correct = 0}

local function findActiveQuiz(player)
	for _, q in ipairs(QUESTS) do
		if q.kind == 'keyword_quiz' then
			local st = player:getStorageValue(q.storage)
			if st ~= NarutoQuests.DONE and st >= 0 and st < q.count then return q end
		end
	end
	return nil
end

-- IMPORTANTE (2 achados de teste in-game, ver docs/sistemas/progressao-servidor.md):
-- 1) 'cid' recebido pelo onCreatureSay GLOBAL (o do topo do arquivo, chamado direto pelo core
--    do TFS) NÃO é um id estável — é um userdata Player NOVO a cada mensagem (endereço muda
--    sempre, mesmo mensagens seguidas do mesmo jogador). Usá-lo como chave de tabela
--    (quizState[cid]) falha sempre da 2a mensagem em diante. Já dentro do keywordHandler
--    (questCallback/quizCallback) o 'cid' É um inteiro estável, porque npchandler.lua faz
--    `local cid = creature:getId()` antes de chamar processMessage — só o onCreatureSay
--    GLOBAL (nosso override, que roda ANTES de delegar pro npcHandler) recebe o userdata cru.
-- 2) Passar esse userdata cru como 2º argumento de npcHandler:say(msg, cid) quebra em runtime
--    ("Lua Script Error: luaAddEvent(). Argument #5 is unsafe"): say() agenda a resposta via
--    addEvent (fila de 1s do NPC), que não aceita userdata (só tipos primitivos serializáveis).
-- Correção: resolve 'cid' para o Player e usa SEMPRE player:getId() (inteiro) daqui pra baixo —
-- como chave de quizState e como alvo de npcHandler:say().
local function playerIdOf(cid)
	local player = Player(cid)
	return player and player:getId() or nil
end

local function askQuestion(pid, q, idx)
	npcHandler:say(q.quiz[idx].question, pid)
end

local function startQuiz(cid, q)
	local pid = playerIdOf(cid)
	if not pid then return end
	quizState[pid] = {quest = q, idx = 1, correct = 0}
	askQuestion(pid, q, 1)
end

--- Retorna true se a mensagem foi consumida pela prova em andamento (jogador tem quiz ativo).
local function handleQuizAnswer(cid, msg)
	local pid = playerIdOf(cid)
	local st = pid and quizState[pid]
	if not st then return false end
	local q = st.quest
	local question = q.quiz[st.idx]
	local m = normalizeQuiz(msg)
	local hit = false
	for _, kw in ipairs(question.keywords) do
		if m:find(normalizeQuiz(kw), 1, true) then hit = true break end
	end
	if hit then st.correct = st.correct + 1 end
	st.idx = st.idx + 1
	local player = Player(pid)
	if st.idx > #q.quiz then
		local total = #q.quiz
		local correct = st.correct
		quizState[pid] = nil
		if correct >= q.quizMin then
			player:setStorageValue(q.storage, q.count)
			local reply = NarutoQuests.talk(player, QUESTS)
			npcHandler:say(string.format('Prova encerrada: %d/%d certas. %s', correct, total, reply), pid)
		else
			player:setStorageValue(q.storage, 0)
			npcHandler:say(string.format('Prova encerrada: so %d/%d certas (precisa de %d). Diga {prova} para tentar de novo.', correct, total, q.quizMin), pid)
		end
	else
		npcHandler:say((hit and 'Correto! ' or 'Nao e bem isso. ') .. q.quiz[st.idx].question, pid)
	end
	return true
end

local function questCallback(cid, message, keywords, parameters, node)
	if not npcHandler:isFocused(cid) then return false end
	local player = Player(cid)
	local reply, _ = NarutoQuests.talk(player, QUESTS)
	npcHandler:say(reply, cid)
	return true
end
keywordHandler:addKeyword({'missao'}, questCallback, {})
keywordHandler:addKeyword({'mission'}, questCallback, {})
keywordHandler:addKeyword({'quest'}, questCallback, {})

local function quizCallback(cid, message, keywords, parameters, node)
	if not npcHandler:isFocused(cid) then return false end
	local player = Player(cid)
	local q = findActiveQuiz(player)
	if not q then
		npcHandler:say('Nada de prova por agora. Diga {missao} para ver o que tenho.', cid)
		return true
	end
	startQuiz(cid, q)
	return true
end
keywordHandler:addKeyword({'prova'}, quizCallback, {})
keywordHandler:addKeyword({'quiz'}, quizCallback, {})""")
        lua.append(f'npcHandler:setMessage(MESSAGE_GREET, "Olá, |PLAYERNAME|. Diga {{missao}} se quiser trabalho.")')
        needs_custom_say = True
    elif n["type"] == "tasks":
        # NOVO (docs/sistemas/progressao-servidor.md): tarefas repetíveis (data/tasks.json).
        lua.append("local TASKS = NarutoTasks.byNpc['%s'] or {}" % n["id"])
        lua.append("""
local function taskStatusLine(player, t)
	local prog = player:getStorageValue(t.progressStorage)
	if prog < 0 then
		local cd = player:getStorageValue(t.cooldownStorage)
		if cd and cd > os.time() then
			return t.name .. ': em espera (' .. math.ceil((cd - os.time()) / 60) .. ' min)'
		end
		return t.name .. ': disponivel (diga {tarefa})'
	elseif prog < t.count then
		return t.name .. ': ' .. prog .. '/' .. t.count .. ' ' .. t.monster
	else
		return t.name .. ': PRONTA (diga {entregar})'
	end
end

local function listCallback(cid, message, keywords, parameters, node)
	if not npcHandler:isFocused(cid) then return false end
	local player = Player(cid)
	local lines = {}
	for _, t in ipairs(TASKS) do
		if player:getLevel() >= t.minLevel then lines[#lines + 1] = taskStatusLine(player, t) end
	end
	npcHandler:say(#lines > 0 and table.concat(lines, ' | ') or 'Nenhuma tarefa liberada para o seu level ainda.', cid)
	return true
end
keywordHandler:addKeyword({'tarefas'}, listCallback, {})
keywordHandler:addKeyword({'lista'}, listCallback, {})

local function acceptCallback(cid, message, keywords, parameters, node)
	if not npcHandler:isFocused(cid) then return false end
	local player = Player(cid)
	for _, t in ipairs(TASKS) do
		if player:getLevel() >= t.minLevel then
			local prog = player:getStorageValue(t.progressStorage)
			if prog < 0 then
				local cd = player:getStorageValue(t.cooldownStorage)
				if not cd or cd <= os.time() then
					player:setStorageValue(t.progressStorage, 0)
					npcHandler:say('Tarefa aceita: ' .. t.name .. '. Mate ' .. t.count .. ' ' .. t.monster .. '.', cid)
					return true
				end
			end
		end
	end
	npcHandler:say('Nenhuma tarefa nova disponivel agora (level baixo demais ou tudo em espera/em andamento). Diga {tarefas} para ver.', cid)
	return true
end
keywordHandler:addKeyword({'tarefa'}, acceptCallback, {})
keywordHandler:addKeyword({'aceitar'}, acceptCallback, {})

local function deliverCallback(cid, message, keywords, parameters, node)
	if not npcHandler:isFocused(cid) then return false end
	local player = Player(cid)
	for _, t in ipairs(TASKS) do
		local prog = player:getStorageValue(t.progressStorage)
		if prog >= t.count then
			player:setStorageValue(t.progressStorage, -1)
			player:setStorageValue(t.cooldownStorage, os.time() + t.cooldownMin * 60)
			local xp = NarutoRewards.scaledXp(player, t.reward.xp)
			player:addExperience(xp, true)
			if t.reward.ryo > 0 then player:addItem(NarutoQuests.RYO_ID, t.reward.ryo) end
			for _, it in ipairs(t.reward.items) do player:addItem(it.id, it.count) end
			if NarutoAchievements then NarutoAchievements.onTaskDelivered(player) end
			npcHandler:say('Tarefa entregue: ' .. t.name .. '. +' .. xp .. ' xp, +' .. t.reward.ryo .. ' ryo.', cid)
			return true
		end
	end
	npcHandler:say('Nenhuma tarefa pronta para entregar.', cid)
	return true
end
keywordHandler:addKeyword({'entregar'}, deliverCallback, {})""")
        lua.append(f'npcHandler:setMessage(MESSAGE_GREET, "Olá, |PLAYERNAME|. Diga {{tarefas}} (lista), {{tarefa}} (aceitar) ou {{entregar}}.")')
    elif n["type"] == "dailies":
        # NOVO: "Quadro de Missões" — mesma API de NarutoDailies usada por !diaria.
        lua.append("""
local function dailyLines(player)
	NarutoDailies.rollIfNeeded(player)
	local lines = {}
	for slot = 1, 3 do
		local entry = NarutoDailies.slotEntry(player, slot)
		if entry then
			local prog = NarutoDailies.slotProgress(player, slot)
			if prog < entry.count then
				lines[#lines + 1] = slot .. ') ' .. entry.name .. ': ' .. math.max(prog, 0) .. '/' .. entry.count .. ' ' .. entry.monster
			elseif prog == entry.count then
				lines[#lines + 1] = slot .. ') ' .. entry.name .. ': PRONTA (diga {entregar})'
			else
				lines[#lines + 1] = slot .. ') ' .. entry.name .. ': ja entregue hoje'
			end
		end
	end
	return lines
end

local function showCallback(cid, message, keywords, parameters, node)
	if not npcHandler:isFocused(cid) then return false end
	local player = Player(cid)
	local lines = dailyLines(player)
	npcHandler:say(#lines > 0 and table.concat(lines, ' | ') or 'Nenhuma diaria disponivel para o seu level hoje.', cid)
	return true
end
keywordHandler:addKeyword({'diaria'}, showCallback, {})
keywordHandler:addKeyword({'diarias'}, showCallback, {})

local function deliverCallback(cid, message, keywords, parameters, node)
	if not npcHandler:isFocused(cid) then return false end
	local player = Player(cid)
	local ok, xp, ryo = NarutoDailies.deliver(player)
	if ok then
		npcHandler:say(string.format('Diarias entregues: +%d xp, +%d ryo.', xp, ryo), cid)
	else
		npcHandler:say('Nenhuma diaria pronta para entregar.', cid)
	end
	return true
end
keywordHandler:addKeyword({'entregar'}, deliverCallback, {})""")
        lua.append(f'npcHandler:setMessage(MESSAGE_GREET, "Olá, |PLAYERNAME|. Diga {{diaria}} para ver as 3 missões de hoje.")')
    if needs_custom_say:
        lua.append("""function onCreatureSay(cid, type, msg)
	if handleQuizAnswer(cid, msg) then return end
	npcHandler:onCreatureSay(cid, type, msg)
end""")
    else:
        lua.append("function onCreatureSay(cid, type, msg) npcHandler:onCreatureSay(cid, type, msg) end")
    lua.append("npcHandler:addModule(FocusModule:new())")
    return xml, "\n".join(lua) + "\n"

for n in npcs.values():
    xml, lua = npc_files(n)
    write(f"npc/{n['name']}.xml", xml)          # TFS instancia por nome: data/npc/<Nome>.xml
    write(f"npc/scripts/naruto/{n['id']}.lua", lua)  # script="naruto/<id>.lua" é relativo a data/npc/scripts/

# ---------------------------------------------------------------- lib + quests (revscriptsys)
base = int(M["storage_base"])
quest_defs = []
rank_groups = {}  # rank -> [storage, ...] (docs/lore/progressao.md: grants_rank/grants_rank_progress)
qi = 0
for n in npcs.values():
    for q in n.get("quests", []):
        qi += 1
        storage = base + qi
        items_lua = reward_items_lua(q["reward"].get("items", []))
        obj = q["objective"]
        kind = obj.get("kind", "kill")
        grants_rank = q.get("grants_rank")
        grants_rank_progress = q.get("grants_rank_progress")
        for r in (grants_rank, grants_rank_progress):
            if r:
                rank_groups.setdefault(r, []).append(storage)
        extra_field = ""
        monster_name = ""
        count = 0
        if kind == "keyword_quiz":
            quiz = obj.get("quiz", [])
            quiz_min = max(1, math.ceil(len(quiz) * 0.6))
            quiz_lua_rows = []
            for qq in quiz:
                kws = ", ".join(lua_q(k) for k in qq.get("keywords", []))
                quiz_lua_rows.append(f"{{question = {lua_q(qq['question'])}, keywords = {{{kws}}}}}")
            count = quiz_min  # para keyword_quiz, 'count' = mínimo de acertos (ver NPC gerado / npc_files)
            extra_field = f", quiz = {{{', '.join(quiz_lua_rows)}}}, quizMin = {quiz_min}"
        elif kind == "collect_item":
            # entrega de itens (docs/sistemas/missoes.md): sem contador de mortes — a etapa checa,
            # na hora de falar {missao}, se o jogador TEM os itens.
            col_rows = []
            for it in obj.get("items", []):
                iid = item_id(it["item_id"])
                nm = items[it["item_id"]]["name"] if it["item_id"] in items else it["item_id"]
                col_rows.append(f"{{id = {iid}, count = {it['count']}, name = {lua_q(nm)}, itemKey = {lua_q(it['item_id'])}}}")
            count = 0
            extra_field = f", collectItems = {{{', '.join(col_rows)}}}"
            # NOVO (docs/sistemas/missoes.md): objective.drops_from — o TFS 1.4.2 não tem "loot
            # condicional por quest" nativo em monster/*.xml (a tabela de loot é fixa por monstro,
            # sem acesso ao storage do jogador que o matou); implementado em onKill
            # (scripts/naruto/quests_kill.lua), não no monstro. 'itemKey' identifica qual entrada
            # de collectItems o drop alimenta.
            drops = obj.get("drops_from", [])
            if drops:
                drop_rows = [
                    f"{{itemKey = {lua_q(d['item_id'])}, monster = {lua_q(monsters[d['monster_id']]['name'])}, chance = {float(d['chance'])}}}"
                    for d in drops
                ]
                extra_field += f", dropsFrom = {{{', '.join(drop_rows)}}}"
        elif kind == "talk_to":
            # NOVO: completa ao dizer a keyword (default 'missao') para OUTRO npc (obj.npc) — ver
            # bloco TALK_TO_QUESTS injetado em TODO npc gerado (npc_files()) e
            # NarutoQuests.completeTalkTo abaixo.
            target = obj["npc"]
            target_name = npcs[target]["name"] if target in npcs else target
            keyword = obj.get("keyword", "missao")
            count = 1
            extra_field = f", targetNpc = {lua_q(target)}, targetNpcName = {lua_q(target_name)}, keyword = {lua_q(keyword)}"
        elif kind == "reach":
            # NOVO: completa ao chegar perto de objective.pos (poll de 7s, scripts/naruto/
            # quests_kill.lua) — raio quadrado (Chebyshev), ver docs/sistemas/missoes.md.
            pos = obj["pos"]
            radius = int(obj.get("radius", 1))
            count = 1
            extra_field = f", pos = {{x = {int(pos['x'])}, y = {int(pos['y'])}, z = {int(pos['z'])}}}, radius = {radius}"
        else:
            # kind == 'kill' (default, compat): objective.kill (um monstro) OU objective.any_of
            # (NOVO: lista — qualquer um conta). objective.boss (NOVO) é só metadado de UI.
            count = obj["count"]
            any_of = obj.get("any_of")
            if any_of:
                any_names = [monsters[m]["name"] for m in any_of]
                monster_name = " ou ".join(any_names)
                extra_field += ", anyOf = {" + ", ".join(lua_q(nm) for nm in any_names) + "}"
            else:
                monster_name = monsters[obj["kill"]]["name"]
            if obj.get("boss"):
                extra_field += ", boss = true"
        rank_fields = ""
        if grants_rank:
            rank_fields += f", grantsRank = {lua_q(grants_rank)}"
        if grants_rank_progress:
            rank_fields += f", grantsRankProgress = {lua_q(grants_rank_progress)}"
        # NOVO (docs/sistemas/missoes.md): diálogo condicionado (fallback = comportamento de hoje
        # quando ausente, ver NarutoQuests.talk/renderTemplate) e pré-requisitos cross-NPC.
        text_fields = ""
        if q.get("progress_text"):
            text_fields += f", progressText = {lua_q(q['progress_text'])}"
        if q.get("done_text"):
            text_fields += f", doneText = {lua_q(q['done_text'])}"
        if q.get("locked_text"):
            text_fields += f", lockedText = {lua_q(q['locked_text'])}"
        requires = q.get("requires")
        if requires:
            req_parts = []
            if requires.get("level"):
                req_parts.append(f"level = {int(requires['level'])}")
            if requires.get("rank"):
                req_parts.append(f"rank = {lua_q(requires['rank'])}")
            if requires.get("quests"):
                req_parts.append("quests = {" + ", ".join(lua_q(qid) for qid in requires["quests"]) + "}")
            text_fields += f", requires = {{{', '.join(req_parts)}}}"
        # NOVO: reward.storage/outfit/addon/title (fora de xp/ryo/items já existentes).
        reward_extra = ""
        rew_storage = q["reward"].get("storage")
        if rew_storage:
            reward_extra += f", storageKey = {int(rew_storage['key'])}, storageValue = {int(rew_storage['value'])}"
        if q["reward"].get("outfit"):
            reward_extra += f", outfit = {int(q['reward']['outfit'])}"
        if q["reward"].get("addon"):
            reward_extra += f", addon = {int(q['reward']['addon'])}"
        if q["reward"].get("title"):
            reward_extra += f", title = {lua_q(q['reward']['title'])}"
        quest_defs.append(
            f"\t{{id = {lua_q(q['id'])}, npc = {lua_q(n['id'])}, npcName = {lua_q(n['name'])}, "
            f"name = {lua_q(q['name'])}, text = {lua_q(q['text'])}, "
            f"kind = {lua_q(kind)}, monster = {lua_q(monster_name)}, count = {count}, "
            f"storage = {storage}, reward = {{xp = {q['reward'].get('xp', 0)}, ryo = {q['reward'].get('ryo', 0)}, items = {{{items_lua}}}{reward_extra}}}"
            f"{extra_field}{rank_fields}{text_fields}}},")
rank_groups_lua = "{\n" + "\n".join(
    f"\t['{r}'] = {{{', '.join(str(s) for s in storages)}}}," for r, storages in rank_groups.items()
) + "\n}"
lib = HEADER_LUA + f"""-- Coloque em data/lib/naruto_quests.lua e adicione `dofile('data/lib/naruto_quests.lua')` em data/lib/lib.lua
-- Storage: -1/ausente = não iniciada, 0..count-1 = progresso (ou 0..quizMin-1 no quiz), count/quizMin = pronta,
-- {base + 500} = entregue (marcador). kind='kill' (padrão) conta mortes (scripts/naruto/quests_kill.lua);
-- kind='keyword_quiz' conta acertos da prova (ver npc/scripts/naruto/<npc>.lua, palavra-chave {{prova}}).
NarutoQuests = {{}}
NarutoQuests.RYO_ID = {item_id('ryo')}
NarutoQuests.DONE = {base + 500}
-- rank -> lista de storages das quests com grants_rank/grants_rank_progress daquele rank
-- (docs/lore/progressao.md). Promoção só acontece quando TODAS estiverem DONE — ver
-- NarutoRanks.checkProgress, chamado por NarutoQuests.talk ao concluir qualquer uma delas.
NarutoQuests.rankGroups = {rank_groups_lua}
NarutoQuests.list = {{
{chr(10).join(quest_defs)}
}}
NarutoQuests.byNpc = {{}}
-- storage -> quest (índice reverso usado pela aba Missões do menu Shinobi, opcode 210
-- get_progress, para listar os requisitos pendentes do próximo rank por nome/NPC).
NarutoQuests.byStorage = {{}}
-- NOVO (docs/sistemas/missoes.md): índice por id da quest — usado por requires.quests (pré-
-- requisito cruzando NPCs) e por NarutoQuests.completeTalkTo (achar a quest pelo storage já
-- basta lá, mas byId fica disponível pra qualquer outro script que precise).
NarutoQuests.byId = {{}}
for _, q in ipairs(NarutoQuests.list) do
	NarutoQuests.byNpc[q.npc] = NarutoQuests.byNpc[q.npc] or {{}}
	table.insert(NarutoQuests.byNpc[q.npc], q)
	NarutoQuests.byStorage[q.storage] = q
	NarutoQuests.byId[q.id] = q
end

--- NOVO (docs/sistemas/missoes.md): placeholders {{count}}/{{needed}}/{{player}} em text/
--- progress_text/done_text/locked_text. tpl nil (campo não usado na quest) retorna nil — quem
--- chama decide o texto padrão (fallback). Sem nenhum placeholder no texto, gsub não altera nada
--- (no-op seguro para todo texto de quest já existente, que nunca usa essas chaves).
local function renderTemplate(tpl, player, q, count)
	if not tpl then return nil end
	local out = tpl:gsub('{{count}}', tostring(count or 0)):gsub('{{needed}}', tostring(q.count or 0))
	if player then out = out:gsub('{{player}}', player:getName()) end
	return out
end

--- NOVO: requires.level/rank/quests (docs/sistemas/missoes.md). Sem 'requires' (todas as quests
--- de hoje), retorna sempre true — zero mudança de comportamento pras quests existentes.
local function requirementsMet(player, q)
	local req = q.requires
	if not req then return true end
	if req.level and player:getLevel() < req.level then return false end
	if req.rank and NarutoRanks then
		local cur = NarutoRanks.get(player)
		local needed = NarutoRanks.byRank[req.rank]
		if needed and cur.index < needed.index then return false end
	end
	if req.quests then
		for _, qid in ipairs(req.quests) do
			local rq = NarutoQuests.byId[qid]
			if rq and player:getStorageValue(rq.storage) ~= NarutoQuests.DONE then return false end
		end
	end
	return true
end

--- NOVO: fala padrão pt-BR quando 'requires' não foi satisfeito e a quest não definiu
--- locked_text — lista o que falta (nível/rank/missões anteriores) de forma genérica.
local function defaultLockedText(q)
	local req = q.requires or {{}}
	local parts = {{}}
	if req.level then parts[#parts + 1] = "level " .. req.level end
	if req.rank and NarutoRanks and NarutoRanks.byRank[req.rank] then
		parts[#parts + 1] = "rank " .. NarutoRanks.byRank[req.rank].title
	end
	if req.quests and #req.quests > 0 then
		parts[#parts + 1] = #req.quests .. " missão(ões) anterior(es)"
	end
	local falta = #parts > 0 and table.concat(parts, ", ") or "cumprir os requisitos"
	return "Volte quando estiver pronto: falta " .. falta .. "."
end

--- Checa progressão de rank (grants_rank/grants_rank_progress) depois de marcar uma quest
--- DONE. Retorna a mensagem extra de promoção, ou nil.
local function grantQuestRankIfReady(player, q)
	local rank = q.grantsRank or q.grantsRankProgress
	if not rank or not NarutoRanks then return nil end
	local group = NarutoQuests.rankGroups[rank]
	if not group then return nil end
	for _, storage in ipairs(group) do
		if player:getStorageValue(storage) ~= NarutoQuests.DONE then return nil end
	end
	if NarutoRanks.promote(player, rank) then
		return "Você agora é " .. NarutoRanks.byRank[rank].title .. "!"
	end
	return nil
end

--- Marca a quest DONE, aplica a recompensa (xp/ryo/items + NOVO storage/outfit/addon, ver
--- reward.storage/outfit/addon do schema) e checa rank. Usada por TODAS as formas de conclusão
--- (kill, keyword_quiz, collect_item, reach, talk_to) para não duplicar a lógica de recompensa.
local function completeQuest(player, q)
	player:setStorageValue(q.storage, NarutoQuests.DONE)
	local xp = q.reward.xp
	if xp > 0 then player:addExperience(xp, true) end
	if q.reward.ryo > 0 then player:addItem(NarutoQuests.RYO_ID, q.reward.ryo) end
	for _, it in ipairs(q.reward.items) do player:addItem(it.id, it.count) end
	-- NOVO: reward.storage (destrava diálogo/gate) e reward.outfit/addon.
	if q.reward.storageKey then player:setStorageValue(q.reward.storageKey, q.reward.storageValue) end
	if q.reward.outfit then
		player:addOutfit(q.reward.outfit)
		if q.reward.addon and q.reward.addon > 0 then player:addOutfitAddon(q.reward.outfit, q.reward.addon) end
	end
	-- NOVO: done_text (fallback = mensagem padrão de sempre).
	local msg = renderTemplate(q.doneText, player, q) or ("Bom trabalho, ninja. Missão '" .. q.name .. "' concluída.")
	local rankMsg = grantQuestRankIfReady(player, q)
	if rankMsg then msg = msg .. " " .. rankMsg end
	-- conquista quest_chain_complete (docs/sistemas/progressao-servidor.md): só quando TODAS as
	-- quests desse NPC (a cadeia inteira da região) já estiverem DONE, não só esta.
	if NarutoAchievements then
		local allDone = true
		for _, qq in ipairs(NarutoQuests.byNpc[q.npc] or {{}}) do
			if player:getStorageValue(qq.storage) ~= NarutoQuests.DONE then allDone = false end
		end
		if allDone then NarutoAchievements.onQuestChainComplete(player, q.npc) end
	end
	return msg
end

--- NOVO: usada pelo NPC ALVO de objective.kind='talk_to' (bloco TALK_TO_QUESTS injetado em TODO
--- npc gerado, ver npc_files() em tools/export_tfs.py). Retorna a mensagem de conclusão, ou nil
--- se não há nada a fazer aqui (deixa a keyword cair pro próximo handler desse NPC — ex.: o
--- 'missao' normal, se o NPC alvo também for um NPC de quests).
function NarutoQuests.completeTalkTo(player, q)
	local st = player:getStorageValue(q.storage)
	if st == NarutoQuests.DONE or st < 0 then return nil end
	return completeQuest(player, q)
end

function NarutoQuests.talk(player, quests)
	for _, q in ipairs(quests) do
		local st = player:getStorageValue(q.storage)
		if st ~= NarutoQuests.DONE then
			-- NOVO: requires só é checado ao ACEITAR (st < 0) — sem 'requires' (compat: nenhuma
			-- quest de hoje usa o campo), requirementsMet sempre retorna true e este bloco nunca
			-- dispara.
			if st < 0 and not requirementsMet(player, q) then
				return renderTemplate(q.lockedText, player, q) or defaultLockedText(q), false
			end
			if q.kind == 'keyword_quiz' then
				if st < 0 then
					player:setStorageValue(q.storage, 0)
					return (renderTemplate(q.text, player, q) or q.text) .. " (Missão aceita: " .. q.name .. "). Diga {{prova}} quando estiver pronto para responder.", false
				elseif st < q.count then
					return renderTemplate(q.progressText, player, q, st) or ("Prova ainda não feita. Diga {{prova}} para começar: " .. q.name .. "."), false
				else
					return completeQuest(player, q), true
				end
			elseif q.kind == 'collect_item' then
				if st < 0 then
					player:setStorageValue(q.storage, 0)
					return (renderTemplate(q.text, player, q) or q.text) .. " (Missão aceita: " .. q.name .. ")", false
				end
				local missing = {{}}
				for _, it in ipairs(q.collectItems) do
					if player:getItemCount(it.id) < it.count then
						missing[#missing + 1] = it.count .. "x " .. it.name
					end
				end
				if #missing > 0 then
					return renderTemplate(q.progressText, player, q, #missing) or ("Ainda falta trazer: " .. table.concat(missing, ", ") .. "."), false
				end
				for _, it in ipairs(q.collectItems) do player:removeItem(it.id, it.count) end
				return completeQuest(player, q), true
			elseif st >= q.count then
				return completeQuest(player, q), true
			elseif st >= 0 then
				-- NOVO: progress_text (fallback por kind) — reach/talk_to nunca tinham mensagem
				-- própria antes (não existiam), kill/any_of mantém a mensagem padrão de sempre.
				if q.progressText then
					return renderTemplate(q.progressText, player, q, st), false
				elseif q.kind == 'reach' then
					return "Ainda não chegou lá. Vá até o local indicado.", false
				elseif q.kind == 'talk_to' then
					return "Vá falar com " .. (q.targetNpcName or "a pessoa certa") .. ".", false
				else
					return "Ainda não terminou? " .. q.name .. ": " .. st .. "/" .. q.count .. " " .. q.monster .. ".", false
				end
			else
				player:setStorageValue(q.storage, 0)
				return (renderTemplate(q.text, player, q) or q.text) .. " (Missão aceita: " .. q.name .. ")", false
			end
		end
	end
	return "Não tenho mais nada para você por enquanto.", false
end

--- NOVO (docs/sistemas/missoes.md, requisito 8): texto curto de progresso pro cliente (aba
--- Missões, opcode 210 get_progress — ver missionsProgressJson em scripts/naruto/
--- character_switch.lua) — "3/5 itens", "Chegou!", etc. Não usado pelo diálogo do NPC (que usa
--- NarutoQuests.talk/progress_text acima); é só para a UI mostrar progresso sem precisar falar
--- com o NPC.
function NarutoQuests.progressText(player, q)
	local st = player:getStorageValue(q.storage)
	if st == NarutoQuests.DONE then return "Concluída" end
	if st < 0 then return "Disponível" end
	if q.kind == 'collect_item' then
		local have = 0
		for _, it in ipairs(q.collectItems) do
			if player:getItemCount(it.id) >= it.count then have = have + 1 end
		end
		return have .. "/" .. #q.collectItems .. " itens"
	elseif q.kind == 'keyword_quiz' then
		return st .. "/" .. q.count .. " acertos"
	elseif q.kind == 'reach' then
		return (st >= q.count) and "Chegou! Fale com o NPC" or "A caminho"
	elseif q.kind == 'talk_to' then
		return "Fale com " .. (q.targetNpcName or "?")
	else
		return st .. "/" .. q.count .. (q.boss and " (chefe)" or "")
	end
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
		if q.kind == 'kill' then
			-- NOVO (docs/sistemas/missoes.md): objective.any_of — qualquer monstro da lista conta
			-- pro mesmo contador, além do 'kill' único de sempre.
			local matches = q.monster == name
			if not matches and q.anyOf then
				for _, mn in ipairs(q.anyOf) do
					if mn == name then matches = true break end
				end
			end
			if matches then
				local st = player:getStorageValue(q.storage)
				if st >= 0 and st < q.count then
					player:setStorageValue(q.storage, st + 1)
					player:sendTextMessage(MESSAGE_EVENT_ADVANCE, q.name .. ": " .. (st + 1) .. "/" .. q.count)
				end
			end
		elseif q.kind == 'collect_item' and q.dropsFrom then
			-- NOVO: objective.drops_from — o TFS 1.4.2 não tem "loot condicional por quest" no
			-- monster/*.xml (a tabela de loot não enxerga o storage do jogador que matou), então o
			-- drop extra é concedido aqui. Só dropa enquanto a missão está ATIVA (aceita, storage
			-- >= 0, não concluída) e o jogador ainda não tem o suficiente desse item (não empilha
			-- além do necessário pra entrega).
			local st = player:getStorageValue(q.storage)
			if st >= 0 then
				for _, drop in ipairs(q.dropsFrom) do
					if drop.monster == name then
						for _, it in ipairs(q.collectItems) do
							if it.itemKey == drop.itemKey and player:getItemCount(it.id) < it.count and math.random() <= drop.chance then
								player:addItem(it.id, 1)
								player:sendTextMessage(MESSAGE_EVENT_ADVANCE, it.name .. " obtido(a)! (" .. q.name .. ")")
							end
						end
					end
				end
			end
		end
		-- kind='keyword_quiz' NAO conta mortes (a etapa avança só respondendo a prova, palavra-
		-- chave {prova}); kind='talk_to' avança só falando com o NPC alvo; kind='reach' avança só
		-- chegando no local (poll abaixo). Nenhum dos três tem q.monster/q.anyOf preenchido, então
		-- já cairiam fora do primeiro `if q.kind == 'kill'` mesmo sem checagem explícita — mas o
		-- `if` já deixa isso impossível de qualquer forma.
	end
	return true
end
killEvent:register()

-- NOVO (docs/sistemas/missoes.md): objective.kind='reach' completa a ETAPA (storage -> q.count)
-- quando o jogador está a até 'radius' tiles (quadrado/Chebyshev: |dx|<=radius e |dy|<=radius, MESMO
-- z) de 'pos'. Escolha de implementação: poll (igual ao GlobalEvent de conquistas,
-- server/generated/scripts/naruto/achievements.lua) em vez de onStepIn/actionid de tile (exigiria
-- editar o mapa por missão, fora do escopo de tools/export_tfs.py) ou MoveEvent (mesmo motivo —
-- pediria uma entrada de tile por missão em vez de só um pos+radius no JSON). Poll PRÓPRIO (não
-- reaproveita o de achievements.lua, arquivo/lib diferente) para manter naruto_quests autocontido.
-- Ao chegar, só marca "pronto para entregar" — a recompensa é dada ao falar {missao} com o NPC que
-- deu a missão (mesmo fluxo de kill/any_of, narrativamente "volte e me conte").
local function narutoQuestPollReach(player)
	for _, q in ipairs(NarutoQuests.list) do
		if q.kind == 'reach' then
			local st = player:getStorageValue(q.storage)
			if st >= 0 and st < q.count then
				local pos = player:getPosition()
				if pos.z == q.pos.z and math.abs(pos.x - q.pos.x) <= q.radius and math.abs(pos.y - q.pos.y) <= q.radius then
					player:setStorageValue(q.storage, q.count)
					player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Chegou ao destino: " .. q.name .. " (diga {missao} para reportar)")
				end
			end
		end
	end
end

local reachPoll = GlobalEvent("NarutoQuestReachPoll")
function reachPoll.onThink(interval, lastExecution)
	if not NarutoQuests then return true end
	for _, player in ipairs(Game.getPlayers()) do
		narutoQuestPollReach(player)
	end
	return true
end
reachPoll:interval(7000)
reachPoll:register()

local login = CreatureEvent("NarutoQuestKillLogin")
function login.onLogin(player)
	player:registerEvent("NarutoQuestKill")
	player:registerEvent("NarutoBossPhases")
	-- bônus de status do rank atual (docs/lore/progressao.md, ranks.json status_bonus): reaplica
	-- a cada login porque a condição CONDITION_ATTRIBUTES não persiste entre sessões no TFS.
	if NarutoRanks then NarutoRanks.applyBonus(player) end
	return true
end
login:register()
"""
write("scripts/naruto/quests_kill.lua", scripts)

# ---------------------------------------------------------------- ranks (Genin -> Kage)
# docs/lore/progressao.md + data/ranks.json. Storage único com o rank ATUAL do jogador.
RANK_ORDER = ["genin", "chunin", "jonin", "anbu", "kage"]
ranks_by_id = {r["rank"]: r for r in ranks_list}
rank_lua_rows = []
zone_min_index = {}
for idx, rid in enumerate(RANK_ORDER, start=1):
    r = ranks_by_id[rid]
    u = r["unlocks"]
    for area in u["areas"]:
        zone_min_index.setdefault(area, idx)
    areas_lua = ", ".join(f"'{a}'" for a in u["areas"])
    sb = u.get("status_bonus", {})
    rank_lua_rows.append(
        f"\t{{rank = '{rid}', index = {idx}, minLevel = {r['min_level']}, "
        f"title = '{u['title'].replace(chr(39), chr(92)+chr(39))}', areas = {{{areas_lua}}}, jutsuTier = {u['jutsu_tier']}, "
        f"statusBonus = {{maxHp = {sb.get('max_hp', 0)}, maxChakra = {sb.get('max_chakra', 0)}, defense = {sb.get('defense', 0)}}}}},")
zone_min_lua = "{\n" + "\n".join(f"\t['{z}'] = {i}," for z, i in zone_min_index.items()) + "\n}"
ranks_lua = HEADER_LUA + f"""-- Coloque em data/lib/naruto_ranks.lua e adicione `dofile('data/lib/naruto_ranks.lua')`
-- em data/lib/lib.lua (antes de naruto_quests.lua não é obrigatório: lookups são em runtime).
--
-- BÔNUS DE STATUS (status_bonus de data/ranks.json): o TFS 1.4.2 não tem setter direto de
-- max HP/chakra/defesa. Escolha desta implementação: condição permanente CONDITION_ATTRIBUTES
-- (ticks = -1) com subId fixo (NarutoRanks.BONUS_SUBID). CONDITION_PARAM_STAT_MAXHITPOINTS e
-- _MAXMANAPOINTS somam diretamente ao HP/chakra máximo (suporte nativo do TFS, ver
-- server/tfs/src/condition.cpp). 'defense' NÃO tem stat próprio (armor só vem de itens no TFS)
-- — aproximado com CONDITION_PARAM_SKILL_SHIELD (pontos de skill Shield, que entram no cálculo
-- de bloqueio/defesa). A condição é removida e recriada do zero a cada login/promoção para
-- nunca acumular: o bônus ativo é sempre o do rank ATUAL, nunca a soma de ranks anteriores.
NarutoRanks = {{}}
NarutoRanks.STORAGE = 60010
NarutoRanks.BONUS_SUBID = 9010
NarutoRanks.list = {{
{chr(10).join(rank_lua_rows)}
}}
NarutoRanks.byRank, NarutoRanks.byIndex = {{}}, {{}}
for _, r in ipairs(NarutoRanks.list) do
	NarutoRanks.byRank[r.rank] = r
	NarutoRanks.byIndex[r.index] = r
end
NarutoRanks.FIRST = NarutoRanks.byIndex[1]

-- área (docs/lore/mundo.md) -> índice mínimo de rank para entrar (de ranks.json unlocks.areas)
NarutoRanks.zoneMinIndex = {zone_min_lua}

--- Rank atual do jogador (storage NarutoRanks.STORAGE; ausente/inválido = Genin).
function NarutoRanks.get(player)
	local idx = player:getStorageValue(NarutoRanks.STORAGE)
	if not idx or idx < 1 then idx = 1 end
	return NarutoRanks.byIndex[idx] or NarutoRanks.FIRST
end

--- true se o rank atual do jogador já é suficiente para a área nomeada (docs/lore/mundo.md).
--- Zona sem gate conhecida (não listada em nenhum unlocks.areas) é sempre livre.
function NarutoRanks.canEnter(player, zone)
	local need = NarutoRanks.zoneMinIndex[zone]
	if not need then return true end
	return NarutoRanks.get(player).index >= need
end

--- Remove e reaplica do zero a condição de bônus de status do rank ATUAL. Chamar no login
--- (scripts/naruto/quests_kill.lua) e logo após NarutoRanks.promote.
function NarutoRanks.applyBonus(player)
	player:removeCondition(CONDITION_ATTRIBUTES, CONDITIONID_DEFAULT, NarutoRanks.BONUS_SUBID)
	local b = NarutoRanks.get(player).statusBonus
	if (b.maxHp or 0) == 0 and (b.maxChakra or 0) == 0 and (b.defense or 0) == 0 then return end
	local cond = Condition(CONDITION_ATTRIBUTES, CONDITIONID_DEFAULT)
	cond:setParameter(CONDITION_PARAM_TICKS, -1)
	cond:setParameter(CONDITION_PARAM_SUBID, NarutoRanks.BONUS_SUBID)
	if b.maxHp ~= 0 then cond:setParameter(CONDITION_PARAM_STAT_MAXHITPOINTS, b.maxHp) end
	if b.maxChakra ~= 0 then cond:setParameter(CONDITION_PARAM_STAT_MAXMANAPOINTS, b.maxChakra) end
	if b.defense ~= 0 then cond:setParameter(CONDITION_PARAM_SKILL_SHIELD, b.defense) end
	player:addCondition(cond)
end

--- Promove o jogador para 'rankId' se ele ainda não tiver esse rank ou superior. Aplica bônus
--- de status, título e efeito. Retorna true se promoveu (false se já era esse rank ou maior).
--- Empurra o `state` do opcode 210 (com o novo rank) para o cliente na hora - é assim que o
--- rótulo "Rank: X" do menu Shinobi/status atualiza sem precisar relogar (docs/sistemas/
--- cliente-ux.md). NarutoCharacters pode ainda não ter sido carregado (ordem de dofile em
--- data/lib/lib.lua não é garantida entre libs "naruto_*"); a chamada só ACONTECE em runtime
--- (login/talkaction/GM), quando todas as libs já terminaram de carregar - a guarda `if` é só
--- para o caso raro de rodar sem naruto_characters.lua instalado.
function NarutoRanks.promote(player, rankId)
	local target = NarutoRanks.byRank[rankId]
	if not target then return false end
	if target.index <= NarutoRanks.get(player).index then return false end
	player:setStorageValue(NarutoRanks.STORAGE, target.index)
	NarutoRanks.applyBonus(player)
	player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Parabéns! Você agora é " .. target.title .. "!")
	player:getPosition():sendMagicEffect(CONST_ME_FIREWORK_YELLOW)
	if NarutoCharacters and NarutoCharacters.sendState then
		NarutoCharacters.sendState(player)
	end
	if NarutoAchievements then NarutoAchievements.onRankPromoted(player, rankId) end
	return true
end
"""
write("lib/naruto_ranks.lua", ranks_lua)

rank_gate_lua = HEADER_LUA + """-- Coloque em data/scripts/naruto/rank_gate.lua (revscriptsys carrega sozinho).
-- Gate de área por rank (docs/lore/progressao.md): tiles com actionid 45001..45005 (= rank
-- mínimo 1 Genin..5 Kage) barram quem não tem o rank. O agente de mapa aplica o actionid certo
-- nos teleportes/portas de cada zona nova; sem isso o tile funciona normalmente (fallback: no-op).
local gate = MoveEvent()
gate:type("stepin")

function gate.onStepIn(player, item, position, fromPosition)
	-- ACHADO (missão de mapa v3, 1a vez que um actionid de gate foi colocado
	-- num tile de verdade): monstros perseguindo o jogador podem pisar no
	-- mesmo tile do gate (ele é walkable, só o jogador é barrado) — sem essa
	-- checagem, `player:getStorageValue` explode com "attempt to call method
	-- 'getStorageValue' (a nil value)" porque Creature/Monster não tem esse
	-- método (só Player tem). Gate nunca deve barrar monstro.
	if not player:isPlayer() then return true end
	local need = item:getActionId() - 45000
	if need < 1 or need > 5 then return true end
	if not NarutoRanks or NarutoRanks.get(player).index >= need then return true end
	local reqRank = NarutoRanks.byIndex[need]
	player:sendCancelMessage("Você precisa ser " .. (reqRank and reqRank.title or "de rank superior") .. " para entrar aqui.")
	player:teleportTo(fromPosition, true)
	fromPosition:sendMagicEffect(CONST_ME_POFF)
	return true
end

gate:aid(45001, 45002, 45003, 45004, 45005)
gate:register()
"""
write("scripts/naruto/rank_gate.lua", rank_gate_lua)

rank_look_lua = HEADER_LUA + """-- Coloque em data/scripts/naruto/rank_look.lua (revscriptsys carrega sozinho).
-- Título de rank no /look (docs/lore/progressao.md): usa o EventCallback nativo do TFS 1.4.2
-- (data/scripts/lib/event_callbacks.lua, mesmo padrão de
-- data/scripts/eventcallbacks/player/default_onLook.lua) em vez de editar
-- data/events/scripts/player.lua à mão — o default_onLook roda primeiro (ordem alfabética de
-- pasta) e monta "You see ...", este só acrescenta uma linha com o rank.
--
-- Título de conquista (opcional, docs/sistemas/progressao-servidor.md seção Conquistas): sem
-- UI de seleção (fora do escopo desta missão), mostra o título da ÚLTIMA conquista desbloqueada
-- (NarutoAchievements.LAST_UNLOCKED) se houver uma — simplificação deliberada e documentada.
local ec = EventCallback
ec.onLook = function(self, thing, position, distance, description)
	if NarutoRanks and thing:isCreature() and thing:isPlayer() then
		local rank = NarutoRanks.get(thing)
		description = description .. "\\nRank: " .. rank.title .. "."
	end
	if NarutoAchievements and thing:isCreature() and thing:isPlayer() then
		local idx = thing:getStorageValue(NarutoAchievements.LAST_UNLOCKED)
		local a = (idx and idx > 0) and NarutoAchievements.list[idx] or nil
		if a then
			description = description .. "\\nTítulo: " .. a.title .. "."
		end
	end
	return description
end
ec:register()
"""
write("scripts/naruto/rank_look.lua", rank_look_lua)

# ---------------------------------------------------------------- NarutoRewards (XP escalada)
rewards_lua = HEADER_LUA + """-- Coloque em data/lib/naruto_rewards.lua e adicione dofile em data/lib/lib.lua.
-- XP escalada por level (docs/sistemas/progressao-servidor.md; docs/sistemas/balanceamento.md:
-- 'XP p/ subir de level = 100*L + 100', ~5,5 kills por level em média no conteúdo já existente).
--
-- Usada por TAREFAS (data/tasks.json) e DIÁRIAS (data/dailies.json): seu 'reward.xp' é um
-- número de KILLS EQUIVALENTES (tipicamente 5-8), não XP absoluto, convertido aqui para o
-- level ATUAL de quem entrega — a entrega vale sempre ~o mesmo tanto de kills, não um valor
-- fixo que fica trivial (jogador alto level) ou impossível (jogador baixo level) com o tempo.
-- Missões de história (data/npcs/*.json) continuam com reward.xp absoluto e hand-tuned
-- (docs/sistemas/balanceamento.md) e NÃO passam por esta função — decisão documentada em
-- docs/sistemas/progressao-servidor.md para não destuning números de quest já balanceados.
NarutoRewards = {}
NarutoRewards.XP_PER_KILL_DIVISOR = 5.5  -- kills médios por level, ver balanceamento.md

function NarutoRewards.xpToNextLevel(level)
	return 100 * level + 100
end

function NarutoRewards.scaledXp(player, killsEquivalent)
	local level = math.max(1, player:getLevel())
	local xpPerKill = NarutoRewards.xpToNextLevel(level) / NarutoRewards.XP_PER_KILL_DIVISOR
	return math.floor(xpPerKill * (killsEquivalent or 0))
end
"""
write("lib/naruto_rewards.lua", rewards_lua)

# ---------------------------------------------------------------- tarefas (Tibia tasks, repetíveis)
if tasks_data is not None:
    npc_name_by_id = {n["id"]: n["name"] for n in npcs.values()}
    TASK_PROGRESS_BASE = 61000
    TASK_COOLDOWN_BASE = 63000
    task_defs = []
    for i, t in enumerate(tasks_data, start=1):
        items_lua = reward_items_lua(t["reward"].get("items", []))
        mon = monsters.get(t["monster_id"])
        mon_name = mon["name"] if mon else t["monster_id"]
        npc_name = npc_name_by_id.get(t["npc"], t["npc"])
        task_defs.append(
            f"\t{{id = '{t['id']}', npc = '{t['npc']}', npcName = '{npc_name}', "
            f"name = '{t['name'].replace(chr(39), chr(92)+chr(39))}', monster = '{mon_name}', count = {t['count']}, "
            f"minLevel = {t.get('min_level', 1)}, cooldownMin = {t.get('cooldown_min', 0)}, "
            f"progressStorage = {TASK_PROGRESS_BASE + i}, cooldownStorage = {TASK_COOLDOWN_BASE + i}, "
            f"reward = {{xp = {t['reward'].get('xp', 0)}, ryo = {t['reward'].get('ryo', 0)}, items = {{{items_lua}}}}}}},")
    tasks_lib = HEADER_LUA + f"""-- Coloque em data/lib/naruto_tasks.lua e adicione dofile em data/lib/lib.lua.
-- Tarefas repetíveis estilo Tibia tasks (data/tasks.json, docs/sistemas/progressao-servidor.md).
-- progressStorage: -1 não aceita, 0..count-1 em andamento, count = pronta para entregar.
-- cooldownStorage: epoch (os.time()) até quando a tarefa fica bloqueada após a última entrega.
NarutoTasks = {{}}
NarutoTasks.list = {{
{chr(10).join(task_defs)}
}}
NarutoTasks.byNpc = {{}}
for _, t in ipairs(NarutoTasks.list) do
	NarutoTasks.byNpc[t.npc] = NarutoTasks.byNpc[t.npc] or {{}}
	table.insert(NarutoTasks.byNpc[t.npc], t)
end
"""
    write("lib/naruto_tasks.lua", tasks_lib)

    tasks_script = HEADER_LUA + """-- Coloque em data/scripts/naruto/tasks.lua (revscriptsys carrega sozinho).
local killEvent = CreatureEvent("NarutoTaskKill")
function killEvent.onKill(player, target)
	if not target:isMonster() then return true end
	local name = target:getName()
	for _, t in ipairs(NarutoTasks.list) do
		if t.monster == name then
			local prog = player:getStorageValue(t.progressStorage)
			if prog >= 0 and prog < t.count then
				player:setStorageValue(t.progressStorage, prog + 1)
				player:sendTextMessage(MESSAGE_EVENT_ADVANCE, t.name .. ": " .. (prog + 1) .. "/" .. t.count)
			end
		end
	end
	return true
end
killEvent:register()

local login = CreatureEvent("NarutoTaskLogin")
function login.onLogin(player)
	player:registerEvent("NarutoTaskKill")
	return true
end
login:register()

--- !tarefas: lista só as tarefas ATIVAS (aceitas) do jogador, com progresso. Para aceitar/
--- entregar, fale com o Mestre de Tarefas da região (palavras-chave {tarefa}/{entregar}).
local talk = TalkAction("!tarefas")
function talk.onSay(player, words, param)
	local lines = {}
	for _, t in ipairs(NarutoTasks.list) do
		local prog = player:getStorageValue(t.progressStorage)
		if prog >= 0 then
			if prog < t.count then
				lines[#lines + 1] = t.name .. ": " .. prog .. "/" .. t.count .. " " .. t.monster
			else
				lines[#lines + 1] = t.name .. ": PRONTA (entregue com " .. t.npcName .. ")"
			end
		end
	end
	if #lines == 0 then
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Nenhuma tarefa ativa. Fale com um Mestre de Tarefas da região e diga {tarefa} para aceitar uma.")
	else
		player:sendTextMessage(MESSAGE_INFO_DESCR, table.concat(lines, " | "))
	end
	return false
end
talk:separator(" ")
talk:register()
"""
    write("scripts/naruto/tasks.lua", tasks_script)
else:
    WARNINGS.append("data/tasks.json não existe: sistema de tarefas NÃO gerado (compat).")

# ---------------------------------------------------------------- diárias
if dailies_data is not None:
    daily_defs = []
    for d in dailies_data:
        items_lua = reward_items_lua(d["reward"].get("items", []))
        mon = monsters.get(d["monster_id"])
        mon_name = mon["name"] if mon else d["monster_id"]
        daily_defs.append(
            f"\t{{id = '{d['id']}', name = '{d['name'].replace(chr(39), chr(92)+chr(39))}', "
            f"text = '{d['text'].replace(chr(39), chr(92)+chr(39))}', monster = '{mon_name}', count = {d['count']}, "
            f"levelMin = {d['level_min']}, levelMax = {d['level_max']}, "
            f"reward = {{xp = {d['reward'].get('xp', 0)}, ryo = {d['reward'].get('ryo', 0)}, items = {{{items_lua}}}}}}},")
    dailies_lib = HEADER_LUA + f"""-- Coloque em data/lib/naruto_dailies.lua e adicione dofile em data/lib/lib.lua.
-- Missões diárias (data/dailies.json, docs/sistemas/progressao-servidor.md): a cada dia, 3
-- entradas são sorteadas do pool cuja faixa [levelMin,levelMax] contém o level do jogador (na
-- hora do sorteio). Simplificação vs. o pedido original: as 3 diárias do dia já ficam
-- AUTO-ACEITAS (contam kills desde o sorteio, sem passo extra de 'aceitar por número') —
-- '!diaria' mostra e '!diaria entregar' entrega; ver pendências no relatório da missão.
-- SLOT_PROGRESS: -1 sem entrada nesse slot hoje, 0..count-1 em andamento, count = pronta,
-- count+1 = já entregue hoje.
NarutoDailies = {{}}
NarutoDailies.DAY = 60020
NarutoDailies.SLOT_POOL = {{60021, 60022, 60023}}
NarutoDailies.SLOT_PROGRESS = {{60024, 60025, 60026}}
NarutoDailies.pool = {{
{chr(10).join(daily_defs)}
}}

local function today()
	local t = os.date('*t')
	return t.year * 400 + t.yday
end

local function bracketPool(level)
	local out = {{}}
	for i, d in ipairs(NarutoDailies.pool) do
		if level >= d.levelMin and level <= d.levelMax then out[#out + 1] = i end
	end
	return out
end

--- Sorteia as 3 diárias do dia se ainda não sorteou hoje para este jogador (chamado no login,
--- em !diaria e em qualquer kill, então nunca precisa ser chamado manualmente por fora).
function NarutoDailies.rollIfNeeded(player)
	if player:getStorageValue(NarutoDailies.DAY) == today() then return end
	local pool = bracketPool(player:getLevel())
	for i = #pool, 2, -1 do
		local j = math.random(i)
		pool[i], pool[j] = pool[j], pool[i]
	end
	for slot = 1, 3 do
		local idx = pool[slot] or -1
		player:setStorageValue(NarutoDailies.SLOT_POOL[slot], idx)
		player:setStorageValue(NarutoDailies.SLOT_PROGRESS[slot], idx > 0 and 0 or -1)
	end
	player:setStorageValue(NarutoDailies.DAY, today())
end

function NarutoDailies.slotEntry(player, slot)
	local idx = player:getStorageValue(NarutoDailies.SLOT_POOL[slot])
	if not idx or idx < 1 then return nil end
	return NarutoDailies.pool[idx]
end

function NarutoDailies.slotProgress(player, slot)
	return player:getStorageValue(NarutoDailies.SLOT_PROGRESS[slot])
end

function NarutoDailies.onKill(player, monsterName)
	NarutoDailies.rollIfNeeded(player)
	for slot = 1, 3 do
		local entry = NarutoDailies.slotEntry(player, slot)
		if entry and entry.monster == monsterName then
			local prog = NarutoDailies.slotProgress(player, slot)
			if prog >= 0 and prog < entry.count then
				player:setStorageValue(NarutoDailies.SLOT_PROGRESS[slot], prog + 1)
				player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Diária " .. entry.name .. ": " .. (prog + 1) .. "/" .. entry.count)
			end
		end
	end
end

--- Entrega TODAS as diárias do dia que já estão prontas. Retorna (algumaEntregue, xpTotal, ryoTotal).
function NarutoDailies.deliver(player)
	NarutoDailies.rollIfNeeded(player)
	local totalXp, totalRyo, any = 0, 0, false
	for slot = 1, 3 do
		local entry = NarutoDailies.slotEntry(player, slot)
		if entry then
			local prog = NarutoDailies.slotProgress(player, slot)
			if prog == entry.count then
				any = true
				local xp = NarutoRewards.scaledXp(player, entry.reward.xp)
				player:addExperience(xp, true)
				totalXp = totalXp + xp
				if entry.reward.ryo > 0 then player:addItem(NarutoQuests.RYO_ID, entry.reward.ryo) end
				totalRyo = totalRyo + entry.reward.ryo
				for _, it in ipairs(entry.reward.items) do player:addItem(it.id, it.count) end
				player:setStorageValue(NarutoDailies.SLOT_PROGRESS[slot], entry.count + 1)
				if NarutoAchievements then NarutoAchievements.onDailyDelivered(player) end
			end
		end
	end
	return any, totalXp, totalRyo
end
"""
    write("lib/naruto_dailies.lua", dailies_lib)

    dailies_script = HEADER_LUA + """-- Coloque em data/scripts/naruto/dailies.lua (revscriptsys carrega sozinho).
local killEvent = CreatureEvent("NarutoDailyKill")
function killEvent.onKill(player, target)
	if not target:isMonster() then return true end
	NarutoDailies.onKill(player, target:getName())
	return true
end
killEvent:register()

local login = CreatureEvent("NarutoDailyLogin")
function login.onLogin(player)
	player:registerEvent("NarutoDailyKill")
	NarutoDailies.rollIfNeeded(player)
	return true
end
login:register()

--- !diaria: mostra as 3 diárias do dia (já auto-aceitas, ver naruto_dailies.lua) e progresso.
--- !diaria entregar: entrega todas as que já estiverem prontas.
local talk = TalkAction("!diaria")
function talk.onSay(player, words, param)
	NarutoDailies.rollIfNeeded(player)
	param = param and param:trim() or ""
	if param == "entregar" then
		local ok, xp, ryo = NarutoDailies.deliver(player)
		if ok then
			player:sendTextMessage(MESSAGE_EVENT_ADVANCE, string.format("Diárias entregues: +%d xp, +%d ryo.", xp, ryo))
		else
			player:sendCancelMessage("Nenhuma diária pronta para entregar.")
		end
		return false
	end
	local lines = {}
	for slot = 1, 3 do
		local entry = NarutoDailies.slotEntry(player, slot)
		if entry then
			local prog = NarutoDailies.slotProgress(player, slot)
			if prog < entry.count then
				lines[#lines + 1] = string.format("%d) %s: %d/%d %s", slot, entry.name, math.max(prog, 0), entry.count, entry.monster)
			elseif prog == entry.count then
				lines[#lines + 1] = string.format("%d) %s: PRONTA (!diaria entregar)", slot, entry.name)
			else
				lines[#lines + 1] = string.format("%d) %s: já entregue hoje", slot, entry.name)
			end
		end
	end
	player:sendTextMessage(MESSAGE_INFO_DESCR, #lines > 0 and table.concat(lines, " | ") or "Nenhuma diária disponível para o seu level hoje.")
	return false
end
talk:separator(" ")
talk:register()
"""
    write("scripts/naruto/dailies.lua", dailies_script)
else:
    WARNINGS.append("data/dailies.json não existe: sistema de diárias NÃO gerado (compat).")

# ---------------------------------------------------------------- conquistas (data/achievements.json)
# docs/sistemas/progressao-servidor.md, seção "Conquistas". Storages novos (nenhum colide com os
# já reservados: 45001-45005 gates, 50000-50500 quests, 60000-60026 personagem/elemento/rank/
# diárias, 61000+/63000+ tarefas):
#   64000+i  = "desbloqueada" (i = índice 1-based na ordem de data/achievements.json; 1 = sim).
#   65000    = contador global de mortes (qualquer monstro) — NÃO existia antes desta missão.
#   65001    = contador global de tarefas entregues (qualquer NPC "Mestre de Tarefas").
#   65002    = contador global de diárias entregues (apesar do nome "daily_streak" no schema, o
#              texto das 3 conquistas é "no total", não "dias seguidos" — implementado como total).
#   65003    = índice (NarutoAchievements.list) da última conquista desbloqueada, só para could
#              mostrar um "título" no /look (rank_look.lua) sem precisar de UI de seleção.
if achievements_data is not None:
    ACH_UNLOCK_BASE = 64000
    ACH_EFFECT_ID = _catalog_id("fx_seal_glow", "effect") or 222  # assets-src/sprites/effects.json

    ach_defs = []
    for i, a in enumerate(achievements_data, start=1):
        cond = a.get("condition") or {}
        kind = cond.get("kind", "")
        target = cond.get("target", "")
        count = int(cond.get("count") or 0)
        extra = ""
        if kind == "kill_specific":
            mon = monsters.get(target)
            extra = f", monsterName = {lua_q(mon['name'] if mon else target)}"
        elif kind == "collect_set":
            tier = int(target.split("_")[-1]) if target.startswith("tier_") else 0
            extra = f", tier = {tier}"
        elif kind == "collect_item_count":
            prefix = target[:-1] if target.endswith("*") else target
            extra = f", itemPrefix = {lua_q(prefix)}"
        ach_defs.append(
            f"\t{{idx = {i}, id = {lua_q(a['id'])}, name = {lua_q(a['name'])}, "
            f"description = {lua_q(a['description'])}, category = {lua_q(a['category'])}, "
            f"kind = {lua_q(kind)}, target = {lua_q(target)}, count = {count}, "
            f"title = {lua_q(a['reward']['title'])}, ryo = {int(a['reward'].get('ryo', 0))}, "
            f"storage = {ACH_UNLOCK_BASE + i}{extra}}},")

    # conjuntos de equipamento por tier (collect_set): slot -> ids TFS de qualquer item de
    # data/items/*.json com required_level == tier nesse slot (várias armas por tier contam
    # igual — ver gloves_taijutsu/senbon_de_ferro no tier 10, por exemplo). tier_20 fica sem
    # 'accessory' porque não existe nenhum item nessa faixa — gap de dado real (documentado no
    # relatório da missão), não um bug do exportador: o requisito dessa conquista some com 5
    # dos 6 slots em vez de 6.
    GEAR_SLOTS = ["head", "body", "legs", "feet", "accessory", "weapon"]
    gear_tiers = sorted({int(a["condition"]["target"].split("_")[-1]) for a in achievements_data
                          if a["condition"]["kind"] == "collect_set" and a["condition"]["target"].startswith("tier_")})
    gear_lua_rows = []
    for tier in gear_tiers:
        by_slot = {}
        for it in items.values():
            if it.get("required_level") == tier and it.get("slot") in GEAR_SLOTS:
                iid = item_id(it["id"])
                if iid:
                    by_slot.setdefault(it["slot"], []).append(iid)
        if not by_slot:
            continue
        slot_parts = [f"{slot} = {{{', '.join(str(x) for x in ids)}}}" for slot, ids in by_slot.items()]
        gear_lua_rows.append(f"\t[{tier}] = {{{', '.join(slot_parts)}}},")

    # ids de item por prefixo (collect_item_count, ex. 'trophy_' -> os 38 troféus de
    # data/items/trophies.json, já concedidos como recompensa da tarefa "Lendária" de cada
    # monstro — ver tasks.json). Genérico: funciona para qualquer prefixo futuro, não só troféu.
    collect_prefixes = sorted({(a["condition"]["target"][:-1] if a["condition"]["target"].endswith("*") else a["condition"]["target"])
                                for a in achievements_data if a["condition"]["kind"] == "collect_item_count"})
    prefix_items_lua_rows = []
    for prefix in collect_prefixes:
        ids = sorted({item_id(it["id"]) for it in items.values() if it["id"].startswith(prefix) and item_id(it["id"])})
        prefix_items_lua_rows.append(f"\t[{lua_q(prefix)}] = {{{', '.join(str(x) for x in ids)}}},")

    achievements_lib_template = HEADER_LUA + """-- Coloque em data/lib/naruto_achievements.lua e adicione dofile em data/lib/lib.lua.
-- Conquistas (data/achievements.json, docs/sistemas/progressao-servidor.md, seção
-- "Conquistas"). Cada conquista tem UM storage de "desbloqueada" (NarutoAchievements.
-- UNLOCK_BASE + índice); os únicos contadores NOVOS são TOTAL_KILLS/TOTAL_TASKS/TOTAL_DAILIES
-- (nada preexistente contava "mortes/tarefas/diárias de qualquer tipo, somadas" antes desta
-- missão — os storages de tasks/dailies são por-tarefa/por-slot, não um total).
NarutoAchievements = {}
NarutoAchievements.UNLOCK_BASE = 64000
NarutoAchievements.TOTAL_KILLS = 65000
NarutoAchievements.TOTAL_TASKS = 65001
NarutoAchievements.TOTAL_DAILIES = 65002
NarutoAchievements.LAST_UNLOCKED = 65003
NarutoAchievements.EFFECT_ID = __EFFECT_ID__

NarutoAchievements.list = {
__ACH_DEFS__
}
NarutoAchievements.byId = {}
NarutoAchievements.byKind = {}
for _, a in ipairs(NarutoAchievements.list) do
	NarutoAchievements.byId[a.id] = a
	NarutoAchievements.byKind[a.kind] = NarutoAchievements.byKind[a.kind] or {}
	table.insert(NarutoAchievements.byKind[a.kind], a)
end

NarutoAchievements.gearSets = {
__GEAR_SETS__
}
NarutoAchievements.SLOT_CONST = {head = CONST_SLOT_HEAD, body = CONST_SLOT_ARMOR, legs = CONST_SLOT_LEGS, feet = CONST_SLOT_FEET, accessory = CONST_SLOT_RING}

NarutoAchievements.itemPrefixIds = {
__PREFIX_ITEMS__
}

-- Zonas: aproximação por retângulo de posição (o TFS não tem "zona" em runtime, só os
-- retângulos que tools/map/build_valley.py (X0/Y0=1000/1000, DEATH_X0=1130) e
-- tools/map/build_regions.py (COAST_*/RUINS_*/MOUNT_*/LAIR_*) usaram para desenhar o mapa —
-- reaproveitados aqui verbatim). Boa o suficiente para "visitou pela 1a vez"; os 6 retângulos
-- não se sobrepõem.
NarutoAchievements.zoneBounds = {
	floresta_da_vila = {1000, 1000, 1129, 1119},
	floresta_da_morte = {1130, 1000, 1199, 1119},
	costa_das_mares = {1000, 1120, 1049, 1169},
	ruinas_do_cla_marionetista = {1200, 1000, 1249, 1049},
	montanha_do_trovao = {1200, 1060, 1249, 1109},
	covil_nuvem_vermelha = {1400, 1000, 1449, 1049},
}

-- Dentro da muralha da Vila da Folha (build_valley.py V_X0..V_Y1 = 1010,1030..1049,1069) NAO conta
-- como "pisou na Floresta da Vila" (playtest r4: a conquista destravava no login, na praca).
NarutoAchievements.zoneExclude = { {1010, 1030, 1049, 1069} }

function NarutoAchievements.zoneAt(pos)
	for _, e in ipairs(NarutoAchievements.zoneExclude) do
		if pos.x >= e[1] and pos.x <= e[3] and pos.y >= e[2] and pos.y <= e[4] then
			return nil
		end
	end
	for zone, b in pairs(NarutoAchievements.zoneBounds) do
		if pos.x >= b[1] and pos.x <= b[3] and pos.y >= b[2] and pos.y <= b[4] then
			return zone
		end
	end
	return nil
end

function NarutoAchievements.isUnlocked(player, a)
	return player:getStorageValue(a.storage) == 1
end

--- Concede a conquista `a`: marca o storage, manda mensagem de sistema + efeito visual + ryo.
--- Idempotente (retorna false sem fazer nada se já estava desbloqueada).
function NarutoAchievements.grant(player, a)
	if NarutoAchievements.isUnlocked(player, a) then return false end
	player:setStorageValue(a.storage, 1)
	player:setStorageValue(NarutoAchievements.LAST_UNLOCKED, a.idx)
	player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Conquista desbloqueada: " .. a.name .. "!")
	player:getPosition():sendMagicEffect(NarutoAchievements.EFFECT_ID)
	if a.ryo and a.ryo > 0 and NarutoQuests then
		player:addItem(NarutoQuests.RYO_ID, a.ryo)
	end
	return true
end

--- true se o jogador tem TODOS os slots do tier vestidos ao mesmo tempo (arma aceita qualquer
--- id da lista — ex. tier 1 aceita kunai OU shuriken de ferro).
function NarutoAchievements.hasGearSet(player, tier)
	local set = NarutoAchievements.gearSets[tier]
	if not set then return false end
	for slot, ids in pairs(set) do
		if slot == 'weapon' then
			local left = player:getSlotItem(CONST_SLOT_LEFT)
			local right = player:getSlotItem(CONST_SLOT_RIGHT)
			local leftId = left and left:getId() or 0
			local rightId = right and right:getId() or 0
			local ok = false
			for _, iid in ipairs(ids) do
				if leftId == iid or rightId == iid then ok = true end
			end
			if not ok then return false end
		else
			local slotConst = NarutoAchievements.SLOT_CONST[slot]
			local it = slotConst and player:getSlotItem(slotConst)
			local itemId = it and it:getId() or 0
			local ok = false
			for _, iid in ipairs(ids) do
				if itemId == iid then ok = true end
			end
			if not ok then return false end
		end
	end
	return true
end

function NarutoAchievements.prefixItemCount(player, prefix)
	local ids = NarutoAchievements.itemPrefixIds[prefix]
	if not ids then return 0 end
	local n = 0
	for _, iid in ipairs(ids) do
		if player:getItemCount(iid) > 0 then n = n + 1 end
	end
	return n
end

-- ------------------------------------------------------------------ hooks por tipo de evento
-- (chamados de dentro de scripts/naruto/achievements.lua e dos módulos já existentes —
-- naruto_ranks.lua/NarutoRanks.promote, naruto_quests.lua/completeQuest, e o "tasks"/deliverCallback
-- gerado por npc_files() — NUNCA duplicando um contador que já existe).

function NarutoAchievements.onKill(player, monsterName)
	local total = player:getStorageValue(NarutoAchievements.TOTAL_KILLS)
	if total < 0 then total = 0 end
	total = total + 1
	player:setStorageValue(NarutoAchievements.TOTAL_KILLS, total)
	for _, a in ipairs(NarutoAchievements.byKind['kill_count'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and total >= a.count then
			NarutoAchievements.grant(player, a)
		end
	end
	for _, a in ipairs(NarutoAchievements.byKind['kill_specific'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and a.monsterName == monsterName then
			NarutoAchievements.grant(player, a)
		end
	end
end

function NarutoAchievements.onTaskDelivered(player)
	local total = player:getStorageValue(NarutoAchievements.TOTAL_TASKS)
	if total < 0 then total = 0 end
	total = total + 1
	player:setStorageValue(NarutoAchievements.TOTAL_TASKS, total)
	for _, a in ipairs(NarutoAchievements.byKind['task_count'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and total >= a.count then
			NarutoAchievements.grant(player, a)
		end
	end
end

function NarutoAchievements.onDailyDelivered(player)
	local total = player:getStorageValue(NarutoAchievements.TOTAL_DAILIES)
	if total < 0 then total = 0 end
	total = total + 1
	player:setStorageValue(NarutoAchievements.TOTAL_DAILIES, total)
	for _, a in ipairs(NarutoAchievements.byKind['daily_streak'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and total >= a.count then
			NarutoAchievements.grant(player, a)
		end
	end
end

function NarutoAchievements.onRankPromoted(player, rankId)
	for _, a in ipairs(NarutoAchievements.byKind['grants_rank'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and a.target == rankId then
			NarutoAchievements.grant(player, a)
		end
	end
end

function NarutoAchievements.onQuestChainComplete(player, npcId)
	for _, a in ipairs(NarutoAchievements.byKind['quest_chain_complete'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and a.target == npcId then
			NarutoAchievements.grant(player, a)
		end
	end
end

function NarutoAchievements.onLevelReached(player, newLevel)
	for _, a in ipairs(NarutoAchievements.byKind['level_reached'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and newLevel >= a.count then
			NarutoAchievements.grant(player, a)
		end
	end
end

--- Checagens sem evento dedicado (posição/equipamento/itens): chamada no login e por um
--- GlobalEvent periódico (scripts/naruto/achievements.lua) — o TFS 1.4.2 não tem onEquip nem
--- "entrou na zona X" genéricos sem editar item por item ou o mapa; poll é a solução mais
--- simples que cobre os 55 sem tocar nesses dois (ver limitação no relatório da missão).
function NarutoAchievements.pollPlayer(player)
	local zone = NarutoAchievements.zoneAt(player:getPosition())
	if zone then
		for _, a in ipairs(NarutoAchievements.byKind['visit_zone'] or {}) do
			if not NarutoAchievements.isUnlocked(player, a) and a.target == zone then
				NarutoAchievements.grant(player, a)
			end
		end
	end
	for _, a in ipairs(NarutoAchievements.byKind['collect_set'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and NarutoAchievements.hasGearSet(player, a.tier) then
			NarutoAchievements.grant(player, a)
		end
	end
	for _, a in ipairs(NarutoAchievements.byKind['collect_item_count'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) then
			local n = NarutoAchievements.prefixItemCount(player, a.itemPrefix)
			if n >= a.count then
				NarutoAchievements.grant(player, a)
			end
		end
	end
end

--- JSON para a aba Missões (seção Conquistas, opcode 210 get_progress) — ver
--- character_switch.lua/achievementsProgressJson. Contáveis ganham progress/count; as demais
--- (kill_specific/quest_chain_complete/grants_rank/visit_zone/collect_set) só unlocked.
function NarutoAchievements.progressJson(player)
	local out = NarutoJson.array({})
	for _, a in ipairs(NarutoAchievements.list) do
		local entry = {
			id = a.id, name = a.name, description = a.description,
			category = a.category, title = a.title, unlocked = NarutoAchievements.isUnlocked(player, a),
		}
		if a.kind == 'kill_count' then
			entry.progress = math.min(math.max(player:getStorageValue(NarutoAchievements.TOTAL_KILLS), 0), a.count)
			entry.count = a.count
		elseif a.kind == 'task_count' then
			entry.progress = math.min(math.max(player:getStorageValue(NarutoAchievements.TOTAL_TASKS), 0), a.count)
			entry.count = a.count
		elseif a.kind == 'daily_streak' then
			entry.progress = math.min(math.max(player:getStorageValue(NarutoAchievements.TOTAL_DAILIES), 0), a.count)
			entry.count = a.count
		elseif a.kind == 'level_reached' then
			entry.progress = math.min(player:getLevel(), a.count)
			entry.count = a.count
		elseif a.kind == 'collect_item_count' then
			entry.progress = math.min(NarutoAchievements.prefixItemCount(player, a.itemPrefix), a.count)
			entry.count = a.count
		end
		out[#out + 1] = entry
	end
	return out
end
"""
    achievements_lib = (achievements_lib_template
                         .replace("__EFFECT_ID__", str(ACH_EFFECT_ID))
                         .replace("__ACH_DEFS__", "\n".join(ach_defs))
                         .replace("__GEAR_SETS__", "\n".join(gear_lua_rows))
                         .replace("__PREFIX_ITEMS__", "\n".join(prefix_items_lua_rows)))
    write("lib/naruto_achievements.lua", achievements_lib)

    achievements_script = HEADER_LUA + """-- Coloque em data/scripts/naruto/achievements.lua (revscriptsys carrega sozinho).
-- `if not NarutoAchievements then return true end` em TODO gancho (achado real ao testar
-- audio, docs/sistemas/audio.md): data/lib/naruto_achievements.lua so entra em memoria com
-- REINICIO do servidor (dofile em data/lib/lib.lua, so roda no boot - nenhum /reload toca
-- libs); esta script (revscriptsys) já recarrega com /reload scripts|all. Sem a blindagem,
-- um servidor que já tinha os HOOKS mas ainda nao tinha a LIB (ex.: logo apos um /reload sem
-- reiniciar) derrubava o onLogin de todo mundo com "attempt to index global
-- 'NarutoAchievements' (a nil value)".
local killEvent = CreatureEvent("NarutoAchievementKill")
function killEvent.onKill(player, target)
	if not NarutoAchievements then return true end
	if not target:isMonster() then return true end
	NarutoAchievements.onKill(player, target:getName())
	return true
end
killEvent:register()

local advanceEvent = CreatureEvent("NarutoAchievementAdvance")
function advanceEvent.onAdvance(player, skill, oldLevel, newLevel)
	if NarutoAchievements and skill == SKILL_LEVEL then
		NarutoAchievements.onLevelReached(player, newLevel)
	end
	return true
end
advanceEvent:register()

local login = CreatureEvent("NarutoAchievementLogin")
function login.onLogin(player)
	player:registerEvent("NarutoAchievementKill")
	player:registerEvent("NarutoAchievementAdvance")
	if NarutoAchievements then NarutoAchievements.pollPlayer(player) end
	return true
end
login:register()

-- Sem onEquip/"entrou na zona" genérico no TFS 1.4.2: um GlobalEvent periódico cobre visit_zone
-- e collect_set para todos os jogadores online (NarutoAchievements.pollPlayer). 7s é baixo o
-- bastante pra não demorar perceptivelmente depois de vestir o conjunto/entrar numa zona nova,
-- e alto o bastante pra não pesar com a contagem de jogadores esperada do projeto.
local poll = GlobalEvent("NarutoAchievementPoll")
function poll.onThink(interval, lastExecution)
	if not NarutoAchievements then return true end
	for _, player in ipairs(Game.getPlayers()) do
		NarutoAchievements.pollPlayer(player)
	end
	return true
end
poll:interval(7000)
poll:register()

--- !conquistas: resumo (desbloqueadas/total) por categoria no chat.
local talk = TalkAction("!conquistas")
function talk.onSay(player, words, param)
	if not NarutoAchievements then
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Conquistas ainda não carregadas neste servidor (precisa reiniciar).")
		return false
	end
	local total, unlocked = #NarutoAchievements.list, 0
	local byCat, catOrder = {}, {}
	for _, a in ipairs(NarutoAchievements.list) do
		local done = NarutoAchievements.isUnlocked(player, a)
		if done then unlocked = unlocked + 1 end
		if not byCat[a.category] then
			byCat[a.category] = {0, 0}
			catOrder[#catOrder + 1] = a.category
		end
		byCat[a.category][2] = byCat[a.category][2] + 1
		if done then byCat[a.category][1] = byCat[a.category][1] + 1 end
	end
	local parts = {"Conquistas: " .. unlocked .. "/" .. total}
	for _, cat in ipairs(catOrder) do
		parts[#parts + 1] = cat .. " " .. byCat[cat][1] .. "/" .. byCat[cat][2]
	end
	player:sendTextMessage(MESSAGE_INFO_DESCR, table.concat(parts, " | "))
	return false
end
talk:separator(" ")
talk:register()
"""
    write("scripts/naruto/achievements.lua", achievements_script)
else:
    WARNINGS.append("data/achievements.json não existe: sistema de conquistas NÃO gerado (compat).")

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
| `lib/naruto_ranks.lua` | `data/lib/` + `dofile` em `lib.lua` | docs/lore/progressao.md |
| `lib/naruto_rewards.lua` | `data/lib/` + `dofile` em `lib.lua` | XP escalada (tarefas/diárias) |
| `lib/naruto_tasks.lua` | `data/lib/` + `dofile` em `lib.lua` | só se `data/tasks.json` existir |
| `lib/naruto_dailies.lua` | `data/lib/` + `dofile` em `lib.lua` | só se `data/dailies.json` existir |
| `scripts/naruto/*.lua` | `data/scripts/naruto/` | revscriptsys carrega sozinho (rank_gate, rank_look, tasks, dailies inclusos) |
| `world/*-spawn.xml` | referência para o Remere's Map Editor | manual |

Totais: {len(monsters)} monstros, {len(jutsus)} jutsus, {len(items)} itens, {len(npcs)} NPCs, {qi} missões, {len(villages)} vocações, {len(ranks_list)} ranks, {len(tasks_data) if tasks_data is not None else 0} tarefas, {len(dailies_data) if dailies_data is not None else 0} diárias (pool).
""")
print(f"OK: {len(monsters)} monstros, {len(jutsus)} jutsus, {len(items)} itens, {len(npcs)} NPCs, {qi} missões, {len(ranks_list)} ranks, "
      f"{len(tasks_data) if tasks_data is not None else 0} tarefas, {len(dailies_data) if dailies_data is not None else 0} diárias → server/generated/")
if SKIPPED_ITEM_IDS:
    print(f"\nAVISO: {len(SKIPPED_ITEM_IDS)} itens NÃO foram emitidos em items_naruto.xml porque o id do")
    print("mapping já existe no items.xml original do TFS (evita 'Duplicate item with id').")
    print("Troque esses ids em data/tfs_mapping.json por ids livres quando houver sprite próprio:")
    for our_id, iid in sorted(SKIPPED_ITEM_IDS, key=lambda x: x[1]):
        print(f"  - {our_id}: id {iid} SUBSTITUI o item vanilla (installer remove a entrada original)")
elif not VANILLA_ITEM_IDS:
    print("AVISO: server/tfs/data/items/items.xml não encontrado; ids duplicados não foram verificados.")
if UNMAPPED_REWARD_ITEMS:
    print(f"\nAVISO: {len(UNMAPPED_REWARD_ITEMS)} itens de recompensa (quests/tarefas/diárias) sem id em")
    print("data/tfs_mapping.json ('items') foram OMITIDOS da recompensa (não editável por esta missão):")
    print("  " + ", ".join(sorted(UNMAPPED_REWARD_ITEMS)))

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
            int(j["required_level"]), jutsu_display_chakra_cost(j), lua_str(j["id"]), i, group_id,
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
