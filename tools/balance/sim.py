#!/usr/bin/env python3
"""Simulador de balanceamento PvM — Shinobi Legends.

Python puro, sem servidor. Reproduz as fórmulas REAIS do TFS 1.4.2 (citadas no código,
arquivo:linha de `server/tfs/src/`) para dano de arma, dano de jutsu, defesa/armadura,
regen de HP/chakra e progressão de skill/magic level — e as regras de `server/tfs/config.lua`
(rateExp, rateSkill, rateMagic, rateLoot). Não inventa fórmula: onde o TFS usa RNG (ex.:
`normal_random`), o simulador usa a MESMA distribuição (ver `_normal_random`).

Uso:
    python3 tools/balance/sim.py --matrix --json /tmp/matrix.json     # roda a matriz completa
    python3 tools/balance/sim.py --level 25 --monster boss_white_serpent --build ninjutsu -v
    python3 tools/balance/sim.py --report /tmp/matrix.json            # (via report.py, ver README)

Ver tools/balance/README.md para a lista de premissas documentadas (curva de skill,
uptime de combate) que não vêm de nenhum arquivo do jogo.
"""
import json, os, glob, math, random, argparse, statistics, time, sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DATA = os.path.join(ROOT, "data")

# ============================================================== carregamento de dados
def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def _load_folder(folder):
    out = {}
    for p in sorted(glob.glob(os.path.join(DATA, folder, "*.json"))):
        for o in _load(p):
            out[o["id"]] = o
    return out

MONSTERS = _load_folder("monsters")
JUTSUS = _load_folder("jutsus")
ITEMS = {}
for _f in sorted(glob.glob(os.path.join(DATA, "items", "*.json"))):
    for _o in _load(_f):
        ITEMS[_o["id"]] = _o
ELEMENT_SETS = {s["id"]: s for s in _load(os.path.join(DATA, "element_sets.json"))}
CHARACTERS = _load(os.path.join(DATA, "characters.json"))
ELEMENTS = _load(os.path.join(DATA, "elements.json"))
PROGRESSION = _load(os.path.join(DATA, "progression.json"))
SKILLS_DOC = _load(os.path.join(DATA, "skills.json"))

ELEMENT_ORDER = ELEMENTS["order"]                 # ["katon","fuuton","raiton","doton","suiton"]
ADV_MULT = ELEMENTS["advantage_multiplier"]        # 1.5
DIS_MULT = ELEMENTS["disadvantage_multiplier"]     # 0.75

# ============================================================== constantes do servidor (REAIS)
# server/tfs/config.lua: rateSkill=3, rateMagic=3, rateLoot=2, rateExp=1 (FIX aplicado nesta
# sessão de balanceamento — era rateExp=5 com `experienceStages` ainda ativo por baixo, ver
# comentário grande em server/tfs/config.lua; docs/sistemas/balanceamento.md §2 e
# docs/sistemas/progressao-jogador.md foram calibrados com XP crua do monstro, sem
# multiplicador de rate/stage — confirmado batendo as "kills por level" hand-tuned do doc).
RATE_EXP = 1
RATE_SKILL = 3
RATE_MAGIC = 3
RATE_LOOT = 2

# tools/export_tfs.py, geração de XML/vocations.xml (~linha 484): multiplicador de skill por
# id (0 fist,1 club/genjutsu,2 sword/taijutsu,3 axe,4 distance/shuriken,5 shield/defense,6 fish).
# Vila com bonus_skill divide o multiplicador dela por 1.2 (mais rápido). Usamos os valores
# SEM bonus de vila (build "média"; ver README sobre a vila bônus não entrar no build genérico).
# FIX aplicado nesta sessão: era 2.0/1.5 (template padrão do TFS, nunca ajustado); agora 1.1
# para bater com data/skills.json ("tries_formula": "50 * 1.1^(skill - 10)") — com 2.0 a skill
# taijutsu ficava presa em ~17-25 do nível 5 ao 100 e builds de taijutsu puro morriam ~100% das
# vezes contra monstros do próprio nível (achado do simulador, ver relatório).
SKILL_MULT = {"taijutsu": 1.1, "shuriken": 1.1, "defense": 1.1}   # sword, distance, shield
SKILL_BASE = {"taijutsu": 50, "shuriken": 50, "defense": 100}     # skillBase[] em vocation.cpp:139
MIN_SKILL = 10          # server/tfs/src/const.h MINIMUM_SKILL_LEVEL (mesmo valor do Tibia clássico)
MANA_MULT = 1.3         # manamultiplier gerado por vocação (sem bônus de vila). FIX nesta sessão:
                        # era 4.0 (padrão TFS de mago nunca calibrado); com maglevel travado em
                        # single-digit por 1000h, ninjutsu tier2/3 ficava pior que taijutsu já
                        # em ~L15-20 (achado do simulador, ver tools/export_tfs.py e relatório).
MANA_BASE = 1600        # vocation.cpp:149 getReqMana: 1600 * mult^(magLevel-1)

# vocations.xml gerado: gainhpticks=5 gainhpamount=2, gainmanaticks=5 gainmanaamount=3, para
# TODAS as vilas (tools/export_tfs.py ~linha 493). Aplicado via CONDITION_REGENERATION
# (player.cpp:4602 updateRegeneration) — ticks em segundos * 1000.
REGEN_HP_PER_TICK = 2
REGEN_HP_TICK_S = 5
REGEN_CHAKRA_PER_TICK = 3
REGEN_CHAKRA_TICK_S = 5

ATTACK_INTERVAL_S = 2.0   # vocations.xml attackspeed="2000" (nenhum item seta attackSpeed próprio)

# ============================================================== premissas documentadas (fora do jogo)
# Estas NÃO vêm de nenhuma fórmula do TFS — são o "jogador médio" pedido na missão. Calibradas
# para que o XP/h simulado bata (ordem de grandeza) com docs/sistemas/progressao-jogador.md.
# Ver tools/balance/README.md.
COMBAT_UPTIME = 0.55        # fração do tempo "jogando" realmente trocando golpes (resto = andar/lootar)
DOWNTIME_BETWEEN_KILLS_S = 3.0   # andar até o próximo alvo + looting (por kill)
SKILL_POINT_MELEE = 1.0     # weapons.cpp:548 WeaponMelee::getSkillType -> skillpoint=1 por acerto
SKILL_POINT_RANGED = 1.7    # weapons.cpp:856/862 -> 2 (acerto limpo) ou 1 (bloqueado); média
DEFENSE_TRIGGER_P = 0.9     # creature.cpp:130 blockCount regenera 1/1000ms, mais rápido que o
                            # intervalo de ataque do player (2000ms) -> quase sempre disponível

CUM_HOURS = {  # docs/sistemas/progressao-jogador.md, coluna "Horas acumuladas"
    1: 0.0, 5: 2.8, 10: 5.9, 15: 9.6, 20: 14.5, 25: 21.2, 30: 30.4, 35: 42.9, 40: 59.5,
    45: 81.2, 50: 109.1, 55: 144.2, 60: 187.7, 65: 240.8, 70: 304.9, 75: 381.3, 80: 471.4,
    85: 576.8, 90: 698.9, 95: 839.4, 100: 1000.0,
}

def cum_hours_at(level):
    levels = sorted(CUM_HOURS)
    if level <= levels[0]:
        return CUM_HOURS[levels[0]]
    if level >= levels[-1]:
        return CUM_HOURS[levels[-1]]
    for a, b in zip(levels, levels[1:]):
        if a <= level <= b:
            fa, fb = CUM_HOURS[a], CUM_HOURS[b]
            t = (level - a) / (b - a)
            return fa + t * (fb - fa)
    return CUM_HOURS[levels[-1]]

# ============================================================== RNG idêntico ao TFS
def _normal_random(rng, mn, mx):
    """server/tfs/src/tools.cpp:299 normal_random(min,max): Normal(0.5,0.25) clipado em [0,1],
    increment = round(v*diff), devolve min+increment. Média = (min+max)/2, mais concentrado no
    centro que uniforme."""
    if mn == mx:
        return mn
    if mn > mx:
        mn, mx = mx, mn
    diff = mx - mn
    v = rng.gauss(0.5, 0.25)
    if v < 0.0:
        increment = diff // 2
    elif v > 1.0:
        increment = (diff + 1) // 2
    else:
        increment = round(v * diff)
    return mn + increment

def _uniform_random(rng, mn, mx):
    if mn == mx:
        return mn
    if mn > mx:
        mn, mx = mx, mn
    return rng.randint(mn, mx)

# ============================================================== progressão (HP/chakra/XP)
def player_hp(level):
    return 100 + level * 15   # progression.json hp_formula

def player_chakra(level):
    return 50 + level * 10    # progression.json chakra_formula

def xp_to_next(level):
    return 100 * level + 100  # progression.json xp_formula, derivada (usado por tasks/dailies também)

# ============================================================== skill "jogador médio" no nível L
def _skill_from_tries(total_tries, mult, base):
    """Inverte vocation.cpp:141 getReqSkillTries: reqTries(L->L+1) = base*mult^(L-10) para L>=10.
    Itera (valores ficam baixos nesse jogo por causa do mult=2.0 — ver README/relatório)."""
    skill = MIN_SKILL
    remaining = total_tries
    while True:
        need = base * (mult ** (skill - MIN_SKILL))
        if remaining < need or skill > 200:
            break
        remaining -= need
        skill += 1
    return skill

def _maglevel_from_mana(total_mana):
    """Inverte vocation.cpp:149 getReqMana: reqMana(ML) = 1600*4^(ML-1)."""
    ml = 0
    remaining = total_mana
    while True:
        need = MANA_BASE * (MANA_MULT ** ml)   # custo para ir de ml -> ml+1
        if remaining < need or ml > 60:
            break
        remaining -= need
        ml += 1
    return ml

def typical_skills(level):
    """Skill 'típico' de um jogador médio no nível L: tries acumuladas = horas jogadas até esse
    nível (progressao-jogador.md) x ataques/hora x pontos/ataque x rateSkill (ou rateMagic para
    ninjutsu). Ver COMBAT_UPTIME/SKILL_POINT_* acima — é a única parte do simulador que não vem
    de uma fórmula do jogo (documentado em tools/balance/README.md)."""
    hours = cum_hours_at(level)
    attacks_per_hour = (3600.0 / ATTACK_INTERVAL_S) * COMBAT_UPTIME
    taijutsu_tries = attacks_per_hour * SKILL_POINT_MELEE * RATE_SKILL * hours
    shuriken_tries = attacks_per_hour * SKILL_POINT_RANGED * RATE_SKILL * hours
    defense_tries = attacks_per_hour * 0.5 * RATE_SKILL * hours   # hit_received, ~metade da cadência
    # ninjutsu: cadência de cast limitada pelo cooldown do jutsu básico (~1.8s) com o mesmo uptime
    casts_per_hour = (3600.0 / 1.8) * COMBAT_UPTIME
    avg_chakra_cost = 14.0   # média dos projéteis tier 1 (docs/sistemas/balanceamento.md: 12-16)
    mana_spent = casts_per_hour * avg_chakra_cost * RATE_MAGIC * hours
    return {
        "taijutsu": _skill_from_tries(taijutsu_tries, SKILL_MULT["taijutsu"], SKILL_BASE["taijutsu"]),
        "shuriken": _skill_from_tries(shuriken_tries, SKILL_MULT["shuriken"], SKILL_BASE["shuriken"]),
        "defense": _skill_from_tries(defense_tries, SKILL_MULT["defense"], SKILL_BASE["defense"]),
        "ninjutsu": _maglevel_from_mana(mana_spent),
    }

# ============================================================== equipamento típico por nível
_EQUIP_CACHE = {}

def _equippable_items():
    """Itens de equipamento (weapon/armor/accessory) com required_level, dos arquivos de
    data/items/*.json (inclui tiers.json, armor.json, weapons.json, mountain.json, ruins.json)."""
    out = []
    for it in ITEMS.values():
        if it["type"] in ("weapon", "armor", "accessory") and "required_level" in it:
            out.append(it)
    return out

EQUIP_ITEMS = _equippable_items()

def best_item_for_slot(level, slot, weapon_class=None):
    """Melhor item (maior required_level <= level) para o slot pedido. Para weapon, filtra por
    weapon_class (melee/ranged) quando informado."""
    candidates = [it for it in EQUIP_ITEMS if it.get("required_level", 0) <= level]
    if slot == "weapon":
        candidates = [it for it in candidates if it["type"] == "weapon" and
                      (weapon_class is None or it.get("weapon_class") == weapon_class)]
    else:
        candidates = [it for it in candidates if it["type"] == "armor" and it.get("slot") == slot]
    if not candidates:
        return None
    candidates.sort(key=lambda it: it["required_level"])
    return candidates[-1]

def best_accessories(level, n=2):
    candidates = [it for it in EQUIP_ITEMS if it["type"] == "accessory" and it.get("required_level", 0) <= level]
    candidates.sort(key=lambda it: it["required_level"])
    return candidates[-n:] if candidates else []

class Loadout:
    def __init__(self, level, weapon_class):
        self.level = level
        self.weapon_class = weapon_class
        self.weapon = best_item_for_slot(level, "weapon", weapon_class)
        self.armor = {s: best_item_for_slot(level, s) for s in ("head", "body", "legs", "feet")}
        self.accessories = best_accessories(level, 2)
        self.bonuses = {}
        pieces = [self.weapon] + list(self.armor.values()) + self.accessories
        for it in pieces:
            if not it:
                continue
            for k, v in it.get("bonuses", {}).items():
                self.bonuses[k] = self.bonuses.get(k, 0) + v

    @property
    def attack(self):
        base = self.weapon["attack"] if self.weapon else 0
        return base + self.bonuses.get("attack", 0)   # nota: 'attack' em bonuses de acessório
        # NÃO é exportado pelo tools/export_tfs.py (ver README/relatório) — incluído aqui só
        # para descrever a intenção de design; o jogo real ignora esse bônus.

    @property
    def armor_value(self):
        # Player::getArmor() (player.cpp:275): soma head+necklace+armor(body)+legs+feet+ring,
        # x armorMultiplier (sempre 1.0 nas vocações geradas).
        total = 0
        for it in self.armor.values():
            if it:
                total += it.get("defense", 0)
        return total

    def bonus_skill(self, name):
        return self.bonuses.get(f"skill_{name}", 0)

    @property
    def extra_hp(self):
        return self.bonuses.get("hp", 0)

    @property
    def extra_chakra(self):
        return self.bonuses.get("chakra", 0)

# ============================================================== jogador (modelo de combate)
class SimPlayer:
    def __init__(self, level, build, rng):
        self.level = level
        self.build = build            # "taijutsu" ou "ninjutsu"
        self.rng = rng
        weapon_class = "ranged" if build == "shuriken" else "melee"
        self.gear = Loadout(level, weapon_class)
        skills = typical_skills(level)
        self.taijutsu = skills["taijutsu"] + self.gear.bonus_skill("taijutsu")
        self.shuriken = skills["shuriken"] + self.gear.bonus_skill("shuriken")
        self.ninjutsu = skills["ninjutsu"] + self.gear.bonus_skill("ninjutsu")
        self.hp_max = player_hp(level) + self.gear.extra_hp
        self.chakra_max = player_chakra(level) + self.gear.extra_chakra
        self.hp = self.hp_max
        self.chakra = self.chakra_max
        self.armor = self.gear.armor_value
    def weapon_attack_value(self):
        return self.gear.attack

    def weapon_max_damage(self):
        """weapons.cpp:135 Weapons::getMaxWeaponDamage (attackFactor=1.0, modo ATAQUE)."""
        skill = self.shuriken if self.build == "shuriken" else self.taijutsu
        attack_value = max(0, self.weapon_attack_value())
        return round((self.level / 5) + (((skill / 4. + 1) * (attack_value / 3.)) * 1.03) / 1.0)

    def roll_weapon_damage(self, vs_player=False):
        mx = self.weapon_max_damage()
        if self.build == "shuriken":
            mn = math.ceil(self.level * (0.1 if vs_player else 0.2))
            return _normal_random(self.rng, mn, mx)
        return _normal_random(self.rng, 0, mx)

    def regen_tick(self, dt_s):
        # aproximação contínua da condição CONDITION_REGENERATION (discretiza pouco importa p/ média)
        self.hp = min(self.hp_max, self.hp + REGEN_HP_PER_TICK * dt_s / REGEN_HP_TICK_S)
        self.chakra = min(self.chakra_max, self.chakra + REGEN_CHAKRA_PER_TICK * dt_s / REGEN_CHAKRA_TICK_S)

# ============================================================== dano de jutsu
def jutsu_damage(rng, jutsu, level, ninjutsu_skill, elemental_mult):
    base = jutsu["base_damage"] + level * jutsu["level_scale"] + ninjutsu_skill * jutsu["skill_scale"]
    # export_tfs.py: -floor(base*0.9), -floor(base*1.1); normal_random(min,max) em combat.cpp:1154
    mn, mx = math.floor(base * 0.9), math.floor(base * 1.1)
    raw = _normal_random(rng, mn, mx)
    return raw * elemental_mult

def elemental_multiplier(attacker_element, target_element):
    """tools/export_tfs.py element_percents(): monstro de elemento E é vulnerável (x1.5) ao
    elemento ANTERIOR de E no ciclo, resistente (x0.75) ao elemento SEGUINTE."""
    if attacker_element == "none" or target_element == "none" or target_element not in ELEMENT_ORDER:
        return 1.0
    i = ELEMENT_ORDER.index(target_element)
    prev_el = ELEMENT_ORDER[(i - 1) % len(ELEMENT_ORDER)]
    next_el = ELEMENT_ORDER[(i + 1) % len(ELEMENT_ORDER)]
    if attacker_element == prev_el:
        return ADV_MULT
    if attacker_element == next_el:
        return DIS_MULT
    return 1.0

# ============================================================== mitigação (blockHit real)
def apply_mitigation(rng, damage, defense, armor, defense_trigger_p=DEFENSE_TRIGGER_P):
    """creature.cpp:818 Creature::blockHit — defesa (blockCount) reduz por uniform(D/2,D),
    depois armadura reduz por uniform(A/2, A-(A%2+1)) se A>3, senão -1 se A>0."""
    dmg = damage
    if defense > 0 and rng.random() < defense_trigger_p:
        dmg -= _uniform_random(rng, defense // 2, defense)
        if dmg <= 0:
            return 0
    if armor > 3:
        dmg -= _uniform_random(rng, armor // 2, armor - (armor % 2 + 1))
    elif armor > 0:
        dmg -= 1
    return max(dmg, 0)

# ============================================================== combate: 1 monstro x 1 player
def pick_ninjutsu_jutsu(monster_element, level, ninjutsu_skill):
    """Escolhe, para o build ninjutsu: (1) o set elemental com VANTAGEM sobre o monstro se
    existir (jogador escolheria isso na criação de personagem); senão katon (arbitrário — todo
    elemento tem exatamente 1 vantagem e 1 desvantagem, então sempre há uma vantagem real
    exceto p/ monstros 'none'); (2) dentro dos 4 jutsus do set, o de MAIOR dano por segundo
    (base+level*level_scale+maglevel*skill_scale, sobre o cooldown) já desbloqueado
    (`required_level <= level`) — um jogador otimizando a rotação sempre usaria o jutsu mais
    forte disponível, não só o projétil tier 1 (que era o comportamento do simulador antes
    desta correção, e mascarava o dano real dos jutsus de tier 2/3 nos resultados)."""
    if monster_element in ELEMENT_ORDER:
        i = ELEMENT_ORDER.index(monster_element)
        adv_element = ELEMENT_ORDER[(i - 1) % len(ELEMENT_ORDER)]
    else:
        adv_element = "katon"
    eset = ELEMENT_SETS.get(adv_element)
    candidates = [JUTSUS[jid] for jid in eset["jutsus"] if JUTSUS[jid].get("required_level", 1) <= level
                  and JUTSUS[jid]["base_damage"] > 0]
    if not candidates:
        candidates = [JUTSUS[eset["jutsus"][0]]]
    best = max(candidates, key=lambda j: (j["base_damage"] + level * j["level_scale"]
                                           + ninjutsu_skill * j["skill_scale"]) / j["cooldown_s"])
    return adv_element, best

def _consumables_by_effect(effect_type):
    out = [it for it in ITEMS.values() if it.get("type") == "consumable"
           and it.get("effect", {}).get("type") == effect_type]
    out.sort(key=lambda it: it.get("required_level", 0))
    return out

_HP_POTIONS = _consumables_by_effect("heal_hp")
_CHAKRA_POTIONS = _consumables_by_effect("heal_chakra")

def best_potion(level, potions):
    candidates = [it for it in potions if it.get("required_level", 0) <= level]
    return candidates[-1] if candidates else None

POTION_HEAL_THRESHOLD = 0.35   # bebe poção de HP quando abaixo de 35% da vida máxima
POTION_DRINK_COOLDOWN_S = 1.0  # exhaustion de consumível (aproximação; TFS usa ~1s)

def simulate_fight(level, monster, build, rng, max_seconds=600.0, use_potions=True):
    """Simulação por eventos (dt discreto de 0.1s é suficiente pra granularidade de cooldowns
    de 1.5-10s deste jogo). Retorna dict com ttk_s, dmg_taken, chakra_spent, died(bool).

    `use_potions`: joga como um jogador de verdade jogaria — bebe a melhor poção de vida
    disponível pro nível quando HP cai abaixo de POTION_HEAL_THRESHOLD (loot e ryo do próprio
    monstro cobrem isso perto da faixa recomendada, ver relatório). Sem isso, TODO boss (que
    é justamente pensado para gastar poção) aparece como "mata o jogador" mesmo quando é uma
    luta perfeitamente normal com poções — ver docs/sistemas/monstros-e-pvm.md."""
    p = SimPlayer(level, build, rng)
    monster_hp = monster["hp"]
    m_defense = monster["defense"]
    m_armor = monster["defense"]  # export_tfs.py: <defenses armor=X defense=X/> (mesmo valor)
    attacks = monster["attacks"]
    next_monster_attack = [0.0] * len(attacks)
    player_element, jutsu = (None, None)
    if build == "ninjutsu":
        player_element, jutsu = pick_ninjutsu_jutsu(monster["element"], level, p.ninjutsu)
    next_player_action = 0.0
    t = 0.0
    dt = 0.1  # granularidade suficiente p/ cooldowns de 1.5-10s deste jogo; mantém a matriz <60s
    dmg_taken_total = 0.0
    chakra_spent_total = 0.0
    melee_swings = 0
    hp_potion = best_potion(level, _HP_POTIONS) if use_potions else None
    potions_used = 0
    ryo_spent_potions = 0
    next_potion_ok = 0.0
    while t < max_seconds:
        # regen contínuo
        p.regen_tick(dt)
        if hp_potion and p.hp < POTION_HEAL_THRESHOLD * p.hp_max and t >= next_potion_ok:
            p.hp = min(p.hp_max, p.hp + hp_potion["effect"]["value"])
            potions_used += 1
            ryo_spent_potions += hp_potion["buy_price"]
            next_potion_ok = t + POTION_DRINK_COOLDOWN_S
        # ataque do player
        if t >= next_player_action:
            used_jutsu = False
            if build == "ninjutsu" and jutsu and p.chakra >= jutsu["chakra_cost"]:
                p.chakra -= jutsu["chakra_cost"]
                chakra_spent_total += jutsu["chakra_cost"]
                mult = elemental_multiplier(player_element, monster["element"])
                dmg = jutsu_damage(rng, jutsu, level, p.ninjutsu, mult)
                monster_hp -= dmg
                next_player_action = t + jutsu["cooldown_s"]
                used_jutsu = True
            if not used_jutsu:
                raw = p.roll_weapon_damage()
                # weapons.cpp: WeaponMelee/WeaponDistance ambas setam params.blockedByArmor=true
                # e blockedByShield=true -> mitigado pela armor/defense do MONSTRO (monster.h:
                # getArmor()/getDefense() = mType->info.armor/defense, o mesmo m["defense"] do
                # JSON usado nos dois atributos de <defenses>, ver tools/export_tfs.py:284).
                dmg = apply_mitigation(rng, raw, m_defense, m_armor)
                monster_hp -= dmg
                melee_swings += 1
                next_player_action = t + ATTACK_INTERVAL_S
            if monster_hp <= 0:
                return {
                    "ttk_s": t, "dmg_taken": dmg_taken_total, "chakra_spent": chakra_spent_total,
                    "died": False, "hp_left_pct": p.hp / p.hp_max, "melee_swings": melee_swings,
                    "potions_used": potions_used, "ryo_spent_potions": ryo_spent_potions,
                }
        # ataques do monstro
        for i, atk in enumerate(attacks):
            if t >= next_monster_attack[i]:
                next_monster_attack[i] = t + atk["cooldown_s"]
                raw = _normal_random(rng, atk["damage_min"], atk["damage_max"])
                if atk["type"] == "melee":
                    # monsters.cpp: 'melee' seta COMBAT_PARAM_BLOCKARMOR=1 e BLOCKSHIELD=1.
                    # O componente "defesa/shield" do player é ~0 neste jogo (nenhuma arma tem
                    # atributo 'defense', não há itens de shield — ver README), então só a
                    # armadura mitiga na prática; passamos defense=0 para refletir isso.
                    dmg = apply_mitigation(rng, raw, 0, p.armor)
                else:
                    dmg = raw  # elemental: ignora armadura (monsters.cpp: só 'melee' seta BLOCKARMOR)
                p.hp -= dmg
                dmg_taken_total += dmg
                if p.hp <= 0:
                    return {
                        "ttk_s": t, "dmg_taken": dmg_taken_total, "chakra_spent": chakra_spent_total,
                        "died": True, "hp_left_pct": 0.0, "melee_swings": melee_swings,
                        "potions_used": potions_used, "ryo_spent_potions": ryo_spent_potions,
                    }
        t += dt
    return {
        "ttk_s": max_seconds, "dmg_taken": dmg_taken_total, "chakra_spent": chakra_spent_total,
        "died": False, "hp_left_pct": p.hp / p.hp_max, "melee_swings": melee_swings, "timeout": True,
        "potions_used": potions_used, "ryo_spent_potions": ryo_spent_potions,
    }

# ============================================================== agregação Monte Carlo
def simulate(level, monster_id, build, trials=60, seed=1234):
    monster = MONSTERS[monster_id]
    rng = random.Random(seed)
    results = [simulate_fight(level, monster, build, rng) for _ in range(trials)]
    kill_results = [r for r in results if not r["died"] and not r.get("timeout")]
    death_results = [r for r in results if r["died"]]
    dmg_taken = [r["dmg_taken"] for r in results]
    timeouts = sum(1 for r in results if r.get("timeout"))
    chakra_spent = [r["chakra_spent"] for r in kill_results if build == "ninjutsu"]
    ttk_kill_mean = statistics.mean([r["ttk_s"] for r in kill_results]) if kill_results else None
    # XP/h real: soma o tempo de TODAS as tentativas (mortes incluídas, que custam tempo e não
    # dão XP) + downtime só nos kills bem-sucedidos; se o jogador morre sempre, xp/h -> 0 (não
    # "explode" com um ttk curto de morte, que seria o bug óbvio de só usar ttk_mean).
    total_time_s = sum(r["ttk_s"] for r in results) + len(kill_results) * DOWNTIME_BETWEEN_KILLS_S
    xp_award = monster["xp"] * RATE_EXP
    total_xp = len(kill_results) * xp_award
    xp_per_hour = (total_xp / total_time_s) * 3600 if total_time_s > 0 else 0
    ryo_avg = (monster["ryo_min"] + monster["ryo_max"]) / 2
    loot_value = 0.0
    for l in monster.get("loot", []):
        item = ITEMS.get(l["item_id"])
        sell = item.get("sell_price", 0) if item else 0
        chance = min(1.0, l["chance"] * RATE_LOOT)
        avg_count = (l.get("min", 1) + l.get("max", 1)) / 2
        loot_value += chance * avg_count * sell
    total_ryo_gross = len(kill_results) * (ryo_avg + loot_value)
    total_ryo_potions = sum(r.get("ryo_spent_potions", 0) for r in results)
    ryo_per_hour_gross = (total_ryo_gross / total_time_s) * 3600 if total_time_s > 0 else 0
    ryo_per_hour_net = ((total_ryo_gross - total_ryo_potions) / total_time_s) * 3600 if total_time_s > 0 else 0
    potions_per_kill = (sum(r.get("potions_used", 0) for r in results) / len(kill_results)
                        if kill_results else (sum(r.get("potions_used", 0) for r in results) / trials))
    deaths = len(death_results)
    return {
        "level": level, "monster_id": monster_id, "monster_level": monster["level"],
        "build": build, "trials": trials,
        "ttk_s_mean": round(ttk_kill_mean, 2) if ttk_kill_mean is not None else None,
        "ttk_s_p10": (round(statistics.quantiles([r["ttk_s"] for r in kill_results], n=10)[0], 2)
                      if len(kill_results) >= 10 else
                      (round(min(r["ttk_s"] for r in kill_results), 2) if kill_results else None)),
        "dmg_taken_mean": round(statistics.mean(dmg_taken), 1),
        "death_rate": round(deaths / trials, 3),
        "timeout_rate": round(timeouts / trials, 3),
        "chakra_spent_mean": round(statistics.mean(chakra_spent), 1) if chakra_spent else 0.0,
        "potions_per_kill": round(potions_per_kill, 2),
        "xp_per_hour": round(xp_per_hour),
        "ryo_per_hour": round(ryo_per_hour_net),
        "ryo_per_hour_gross": round(ryo_per_hour_gross),
        "loot_value_per_kill": round(loot_value, 1),
    }

# ============================================================== matriz completa
MATRIX_LEVELS = [1, 3, 5, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100]

def run_matrix(trials=40, seed=1234):
    out = []
    for level in MATRIX_LEVELS:
        for mid in MONSTERS:
            for build in ("taijutsu", "ninjutsu"):
                out.append(simulate(level, mid, build, trials=trials, seed=seed))
    return out

# ============================================================== CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", action="store_true", help="roda level x monstro x build completo")
    ap.add_argument("--level", type=int)
    ap.add_argument("--monster")
    ap.add_argument("--build", choices=["taijutsu", "ninjutsu"], default="taijutsu")
    ap.add_argument("--trials", type=int, default=30)
    ap.add_argument("--json", help="salva resultado em arquivo JSON")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if args.matrix:
        t0 = time.time()
        res = run_matrix(trials=args.trials)
        dt = time.time() - t0
        print(f"# matriz: {len(res)} simulações em {dt:.1f}s", file=sys.stderr)
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=1)
            print(f"salvo em {args.json}", file=sys.stderr)
        else:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        return

    if args.level and args.monster:
        r = simulate(args.level, args.monster, args.build, trials=args.trials)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        if args.verbose:
            skills = typical_skills(args.level)
            print("skills típicos:", skills, file=sys.stderr)
        return

    ap.print_help()

if __name__ == "__main__":
    main()
