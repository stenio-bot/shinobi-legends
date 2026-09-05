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
MANA_MULT = 1.1         # manamultiplier gerado por vocação (sem bônus de vila). FIX rodada 3
                        # (era 1.3 desde a rodada 1 — já uma melhoria sobre o 4.0 original, mas
                        # ainda maior que as outras skills): rodada 2 mediu maglevel preso em
                        # ~16-34 do L5 ao L100 com mult=1.3, quase reto (cresce só ~2x em 95
                        # níveis) enquanto o dano de arma cresce ~40x no mesmo intervalo — jutsu
                        # tier2/3 (que dependem de maglevel*skill_scale) não tinha como acompanhar.
                        # Com mult=1.1 (igual a SKILL_MULT das outras skills), maglevel cresce de
                        # ~23 (L5) a ~83 (L100) — mesma ordem de grandeza do taijutsu (skill ~40 a
                        # ~101) pela primeira vez. Ver docs/sistemas/balanceamento-relatorio-v3.md
                        # §1-2 pros números completos (curva antes/depois) e tools/export_tfs.py
                        # (gerador de vocations.xml) pro mesmo fix aplicado no jogo real.
MANA_BASE = 1600        # vocation.cpp:149 getReqMana: 1600 * mult^(magLevel-1)

# RODADA 5 (item 1 da missão, economia de chakra estrutural): a condição de regen aplicada no
# login (server/tfs/data/scripts/naruto/character_switch.lua, `CreatureEvent NarutoCharacterLogin`,
# subId 9020) deixou de usar os valores FIXOS de vocations.xml (gainhpamount=2/gainhpticks=5,
# gainmanaamount=3/gainmanaticks=5 — 0,6 chakra/s pra TODO level, o defeito estrutural medido na
# rodada 4 §5/§6: um custo de tier 1 proporcionalmente enorme contra o pool de L5-15 nunca
# recuperava a tempo). Agora a condição é recalculada em Lua puro (não vem mais de
# getManaGainAmount()/getManaGainTicks() da vocação) e REAPLICADA a cada level-up por um
# `CreatureEvent onAdvance` novo (`NarutoRegenAdvance`, mesmo padrão de `NarutoAchievementAdvance`
# que já existe pra achievements — ver tools/export_tfs.py) — mesmo subId 9020 sobrescreve a
# condição anterior (Creature::addCondition substitui condição de mesmo tipo+subId,
# `server/tfs/src/creature.cpp` addCondition). Chakra: ticks=2000ms (2s, mais granular que os 5s
# do HP — precisa disso pra não passar de ~85s a recuperação do pool inteiro em nenhum level, ver
# tabela do relatório v5 §1), amount = 3 + floor(level/4) (chakra/2s). HP: ticks=5000ms (inalterado
# — não é o alvo desta missão, só "análogo" citado no enunciado), amount = 2 + floor(level/10)
# (HP/5s) — em L1-9 isso reproduz EXATAMENTE o valor antigo (2/5s), então não muda a curva de
# sobrevivência já calibrada nas rodadas 1-4; só acelera regen de HP a partir de L10, quando o
# pool de HP (100+level*15) já cresceu o bastante pra o antigo valor fixo virar imperceptível
# também (mesmo raciocínio do achado de chakra da rodada 3/4, aplicado por simetria).
def chakra_regen_amount_per_tick(level):
    return 2 + level // 4

CHAKRA_REGEN_TICK_S = 2

def hp_regen_amount_per_tick(level):
    return 2 + level // 10

HP_REGEN_TICK_S = 5

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
    # RODADA 5 (item 1): era 50+level*10. O piso de chakra inicial aplicado uma vez no login
    # (character_switch.lua, `if firstTime and player:getMaxMana() < 60`) subiu de 60 para 110 —
    # como a vocação continua dando +10 de chakra por level (vocations.xml gainmana=10, inalterado),
    # o pool resultante em qualquer level é FLOOR(110) + (level-1)*10 = 100 + level*10. Ver relatório
    # v5 §1 pro raciocínio completo (por que 100 em vez de outro número: "Genin L1 consegue ≥4 casts
    # de tier 1" com folga, ver §1 tabela).
    return 100 + level * 10   # progression.json chakra_formula (atualizado na rodada 5)

def xp_to_next(level):
    return 100 * level + 100  # progression.json xp_formula, derivada (usado por tasks/dailies também)

def jutsu_chakra_cost(jutsu, chakra_max):
    """RODADA 5 (item 1c): tier 1 elemental agora custa uma PORCENTAGEM do chakra máximo do
    jogador (`chakra_cost_percent`, novo campo opcional em data/schemas/jutsu.schema.json),
    exportado como `manapercent` em vez de `mana` no spells.xml gerado (server/tfs/src/spells.cpp:
    466 `node.attribute("manapercent")`; spells.cpp:804 `Spell::getManaCost` prioriza `mana` se
    não-zero, senão usa `(maxMana*manaPercent)/100` — replicado aqui com a MESMA divisão inteira
    truncada, não arredondada, pra bater exatamente com o servidor). Isso resolve o problema
    estrutural da rodada 4 (§5/§6/§10 pendência 3): um `chakra_cost` FIXO não tem como ser barato
    o bastante pra sustentar uma hunt de L5-15 (pool pequeno) sem também ficar irrelevantemente
    barato em L60-100 (pool grande) — custo PROPORCIONAL ao pool escala junto automaticamente.
    Jutsus sem `chakra_cost_percent` continuam com `chakra_cost` absoluto (tier 2/3, personal),
    inalterado desta rodada."""
    pct = jutsu.get("chakra_cost_percent")
    if pct:
        return (chakra_max * pct) // 100
    return jutsu["chakra_cost"]

# RODADA 7 (item "métrica nova" da missão — Entregas): duas contas ANALÍTICAS (não precisam
# rodar `simulate_hunt`) que respondem direto às duas perguntas de design da missão: "quantos
# casts o pool cheio aguenta" e "quanto tempo parado até o pool voltar a encher".
def casts_per_full_pool(jutsu, chakra_max):
    """Quantos casts seguidos de `jutsu` o pool CHEIO aguenta, sem regen (pior caso, chão
    conservador; com regen ligado o número real de casts numa janela de tempo é maior, ver
    `simulate_hunt`/`chakra_spent_total`). `chakra_max // custo`, custo já truncado por
    `jutsu_chakra_cost` (mesma divisão inteira do servidor, ver docstring acima)."""
    cost = jutsu_chakra_cost(jutsu, chakra_max)
    return (chakra_max // cost) if cost > 0 else None

def time_to_refill_pool_s(level, chakra_max, from_amount=0):
    """Segundos parado (sem gastar) para o chakra ir de `from_amount` até `chakra_max`, usando
    a MESMA condição de regen contínua do servidor (`chakra_regen_amount_per_tick`/
    `CHAKRA_REGEN_TICK_S`, replicada em `SimPlayer.regen_tick`) — conta fechada (não
    Monte Carlo): regen é linear no tempo (sem RNG), `déficit / (amount/tick_s)`."""
    rate = chakra_regen_amount_per_tick(level) / CHAKRA_REGEN_TICK_S   # chakra/s
    if rate <= 0:
        return None
    return (chakra_max - from_amount) / rate

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
    """Inverte vocation.cpp:149 getReqMana: reqMana(ML) = 1600*mult^(ML-1).

    O teto de iteração (`ml > 300`) é só uma trava de segurança contra loop infinito — igual
    ao `skill > 200` de `_skill_from_tries` — NUNCA deve ser alcançado de verdade. FIX rodada 3:
    era `ml > 60`, um valor que não binda com `MANA_MULT=1.3` (maglevel real batia ~34 no L100,
    round 1/2) mas passou a truncar silenciosamente o maglevel real assim que `MANA_MULT` caiu
    pra 1.1 nesta rodada (maglevel real chega a ~83 no L100 — ver
    docs/sistemas/balanceamento-relatorio-v3.md §1) — um jogador L70+ tinha o magic level
    subestimado pelo simulador, o que teria feito a calibração de tier2/3 desta rodada
    inconsistente com o jogo real se não corrigido antes da validação final."""
    ml = 0
    remaining = total_mana
    while True:
        need = MANA_BASE * (MANA_MULT ** ml)   # custo para ir de ml -> ml+1
        if remaining < need or ml > 300:
            break
        remaining -= need
        ml += 1
    return ml

def typical_skills_split(level, taijutsu_frac=1.0, ninjutsu_frac=1.0):
    """Como typical_skills, mas pra builds que dividem o tempo de prática entre taijutsu e
    ninjutsu (build 'híbrido', ver simulate_group_fight/rodada 2 do balanceamento) — as tries/
    mana acumuladas são multiplicadas pela fração de tempo dedicada a cada trilha. NÃO vem de
    nenhuma fórmula do TFS (mesma premissa documentada de typical_skills, ver README); só
    generaliza a divisão de treino pra mais de uma trilha ao mesmo tempo."""
    hours = cum_hours_at(level)
    attacks_per_hour = (3600.0 / ATTACK_INTERVAL_S) * COMBAT_UPTIME
    taijutsu_tries = attacks_per_hour * SKILL_POINT_MELEE * RATE_SKILL * hours * taijutsu_frac
    shuriken_tries = attacks_per_hour * SKILL_POINT_RANGED * RATE_SKILL * hours * taijutsu_frac
    defense_tries = attacks_per_hour * 0.5 * RATE_SKILL * hours * taijutsu_frac
    casts_per_hour = (3600.0 / 1.8) * COMBAT_UPTIME
    # RODADA 5: tier 1 elemental usa chakra_cost_percent (~14-16% do pool, ver jutsu_chakra_cost) em
    # vez de custo fixo — a proxy de treino usa 0,15 * pool médio do level (era 14.0 fixo, calibrado
    # pro custo fixo antigo de 12-16; ver docs/sistemas/balanceamento-relatorio-v5.md §1).
    avg_chakra_cost = 0.15 * player_chakra(level)
    mana_spent = casts_per_hour * avg_chakra_cost * RATE_MAGIC * hours * ninjutsu_frac
    return {
        "taijutsu": _skill_from_tries(taijutsu_tries, SKILL_MULT["taijutsu"], SKILL_BASE["taijutsu"]),
        "shuriken": _skill_from_tries(shuriken_tries, SKILL_MULT["shuriken"], SKILL_BASE["shuriken"]),
        "defense": _skill_from_tries(defense_tries, SKILL_MULT["defense"], SKILL_BASE["defense"]),
        "ninjutsu": _maglevel_from_mana(mana_spent),
    }

# build "híbrido" (rodada 2): metade do tempo de combate treinando taijutsu, metade ninjutsu —
# não é média dos dois pura-raça, é um personagem que de fato joga assim (skills mais baixas
# nas duas trilhas que um especialista, mas com acesso pleno às duas).
# FIX rodada 4: era 0.5/0.5 desde a rodada 2 (modelo antigo, ação única — jutsu OU arma, e o
# jutsu só era usado se batesse o DPS de arma). Duas mudanças da rodada 4 turbinam o híbrido: (1)
# arma+jutsu em cadências independentes ("arma entre casts") e (2) o híbrido agora sempre lança o
# jutsu quando pronto/pagável (`no_fallback=True` fixo pro build hybrid — o jutsu é ADITIVO pro
# híbrido, não substituto, então "só usa se bate a arma" não faz sentido aqui, ver
# `simulate_fight`). Isso faz QUALQUER fração >0 deixar o híbrido sistematicamente à frente do
# melhor build puro (o objetivo "híbrido ≥ ambos" nunca falha por baixo com 0.4) — mas nenhuma
# fração testada (0.15–0.55) mantém TODOS os 6 bosses dentro do teto de +15% ao mesmo tempo (ver
# docs/sistemas/balanceamento-relatorio-v4.md §2/§10): frações maiores estouram o teto em mais
# bosses; frações menores derrubam o híbrido ABAIXO do melhor puro em alguns (viola "≥ambos").
# 0.4 foi escolhido por ser a maior fração testada em que NENHUM boss cai abaixo do melhor puro
# (prioriza "híbrido nunca pior que o melhor", o pendant mais grave) — o teto de +15% fica sem
# fechar em vários bosses (chega a +49%), pendência honesta desta rodada.
HYBRID_TAIJUTSU_FRAC = 0.4
HYBRID_NINJUTSU_FRAC = 0.4

# RODADA 6 (item 1 da missão, teto de híbrido +15%): a rodada 5 provou que NENHUM par de frações
# de skill fecha "híbrido nunca abaixo do melhor puro" e "híbrido nunca acima do teto" ao mesmo
# tempo — porque o termo dominante de todo jutsu (`level*level_scale`) não depende da skill
# treinada, só do level do personagem, então baixar a fração de treino de ninjutsu praticamente
# não reduz o dano do jutsu aditivo. Nerfar cooldown/dano jutsu por jutsu também não fecha: a
# escolha de "melhor dps/cooldown" (`pick_ninjutsu_jutsu`) sempre migra pro PRÓXIMO jutsu do kit
# assim que o escolhido atual é nerfado (testado: nerfar o "campeão" tier 2/3 de cada elemento faz
# o híbrido migrar pro tier 1 projétil; nerfar esse também migra pro tier 2 "housenka"-like — nunca
# fecha, só troca qual jutsu carrega o excedente).
# Fix estrutural da rodada 6 (não numérico por jutsu): esticar artificialmente o cooldown EFETIVO
# do jutsu escolhido por "melhor dps/cooldown" (`HYBRID_JUTSU_CADENCE_FRAC`, aplicado só ao build
# híbrido) — resolvia o teto de +15% contra boss, mas a rodada 7 mediu o preço: numa hunt de 30
# min o jutsu do híbrido virava raro demais pra QUALQUER custo criar pressão real de chakra
# (0,0% de tempo sem chakra em todos os níveis, ver relatório v7 §5 — "não existe UM valor de
# custo que empurre a razão gasto/regen perto de 1").
#
# RODADA 8 (substitui `HYBRID_JUTSU_CADENCE_FRAC` — item 2 da missão): modelo novo, "o jogador
# casta o tier 1 sempre que o cooldown libera E tem chakra" — é assim que o playtest da rodada 5
# mediu um jogador de verdade jogando híbrido (não uma seleção racional por "melhor dps/cooldown
# do kit já desbloqueado" com cadência artificialmente esticada por cima). Duas mudanças:
# (1) o jutsu do híbrido deixa de ser escolhido por `pick_ninjutsu_jutsu` (que migra pro tier 2/3
#     assim que desbloqueia, rodada 7 §3) — é SEMPRE o tier 1 do elemento com vantagem (índice 0
#     do kit, `ELEMENT_SETS[adv]["jutsus"][0]`), o "projétil barato" que a missão pede simular;
# (2) o cooldown EFETIVO volta a ser o cooldown REAL do jutsu (sem dividir por nenhuma fração) —
#     `HYBRID_JUTSU_CADENCE_FRAC` deixou de existir.
# Isso resolve os dois lados ao mesmo tempo: contra boss, tier 1 tem `level_scale` mais baixo que
# os campeões de tier 2/3 que o híbrido usava antes (calibrado desde a rodada 5 para ficar atrás
# do burst de tier 2/3), então castar mais vezes (cooldown real, sem esticar) não estoura o teto
# de +15% — ver recalibração de `chakra_cost_percent`/`cooldown_s` do tier 1 no relatório v8 §2
# se o teto ainda estourar (a missão pede ajustar ESSA alavanca, não voltar pro modelo antigo).
# Numa hunt de 30 min, o mesmo jutsu no cooldown real cria pressão de chakra de verdade (mesma
# curva que a rodada 7 já tinha medido pro ninjutsu puro com `force_tier1=True`, 33-72% sem
# pílula — ver relatório v7 §5 "segunda leitura"), o que finalmente dá uma alavanca (custo do
# tier 1) pra mirar a faixa 15-25% pedida — ver relatório v8 §2.

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
    # RODADA 5: ver mesmo comentário em typical_skills_split (custo agora é % do pool, não fixo).
    avg_chakra_cost = 0.15 * player_chakra(level)
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
    """Melhor item desbloqueado (required_level <= level) pro slot pedido, pelo maior
    ATRIBUTO relevante (attack pra arma, defense pra armadura) — NÃO pelo maior required_level.

    FIX (rodada 4): antes ordenava só por `required_level` e pegava o último — um jogador
    racional nunca trocaria uma arma melhor por uma pior só porque desbloqueou depois. Isso
    tinha um efeito real: `gloves_taijutsu` (req10, attack=14) tem required_level MAIOR que
    `tanto_steel` (req8, attack=16), mas attack MENOR — do L10 ao L19 o simulador vestia as
    luvas (mais fracas) em vez do tantō, piorando artificialmente o platô de arma L8→L20 (ver
    docs/sistemas/balanceamento-relatorio-v4.md §3). Para weapon, filtra por weapon_class
    (melee/ranged) quando informado."""
    candidates = [it for it in EQUIP_ITEMS if it.get("required_level", 0) <= level]
    if slot == "weapon":
        candidates = [it for it in candidates if it["type"] == "weapon" and
                      (weapon_class is None or it.get("weapon_class") == weapon_class)]
        if not candidates:
            return None
        return max(candidates, key=lambda it: it.get("attack", 0))
    else:
        candidates = [it for it in candidates if it["type"] == "armor" and it.get("slot") == slot]
        if not candidates:
            return None
        return max(candidates, key=lambda it: it.get("defense", 0))

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
        # 'attack'/'defense' em bonuses de acessório (ring_stone_will, strings_of_the_puppeteer)
        # agora SÃO exportados por tools/export_tfs.py items_xml() (FIX rodada 2 — items.cpp:22/25
        # registram "armor"/"attack" como atributos genéricos válidos em qualquer item, não só
        # weapon/armor; antes eram silenciosamente descartados, ver relatório rodada 1 item 10).
        return base + self.bonuses.get("attack", 0)

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
        if build == "hybrid":
            skills = typical_skills_split(level, HYBRID_TAIJUTSU_FRAC, HYBRID_NINJUTSU_FRAC)
        else:
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
        # RODADA 5: amount por tick agora é função do level (chakra_regen_amount_per_tick /
        # hp_regen_amount_per_tick), reaplicada de verdade no servidor a cada level-up
        # (NarutoRegenAdvance, ver tools/export_tfs.py e comentário de CHAKRA_REGEN_TICK_S acima).
        self.hp = min(self.hp_max, self.hp + hp_regen_amount_per_tick(self.level) * dt_s / HP_REGEN_TICK_S)
        self.chakra = min(self.chakra_max,
                           self.chakra + chakra_regen_amount_per_tick(self.level) * dt_s / CHAKRA_REGEN_TICK_S)

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

def estimate_weapon_dps(p, m_defense, m_armor):
    """Estimativa DETERMINÍSTICA (sem RNG) do DPS de arma pós-mitigação — usada só pra decidir
    ROTAÇÃO (jutsu vs taijutsu), nunca pra aplicar dano de verdade (isso continua sendo
    roll_weapon_damage + apply_mitigation, com RNG). Média de normal_random(0,max) = max/2
    (tools.cpp:299); média de cada estágio uniform(lo,hi) de creature.cpp:818 blockHit =
    (lo+hi)/2, com o estágio de defesa só acontecendo com prob. DEFENSE_TRIGGER_P."""
    avg_raw = p.weapon_max_damage() / 2.0
    mitig = 0.0
    if m_defense > 0:
        mitig += DEFENSE_TRIGGER_P * ((m_defense // 2 + m_defense) / 2.0)
    if m_armor > 3:
        mitig += (m_armor // 2 + (m_armor - (m_armor % 2 + 1))) / 2.0
    elif m_armor > 0:
        mitig += 1.0
    return max(0.0, avg_raw - mitig) / ATTACK_INTERVAL_S

# ============================================================== combate: 1 monstro x 1 player
def advantage_element(monster_element):
    """Elemento com VANTAGEM sobre `monster_element` no ciclo (mesma regra de
    `pick_ninjutsu_jutsu`/`element_kit`, extraída aqui pra reuso sem duplicar a seleção de jutsu
    — usado pelo build híbrido desde a rodada 8, que não passa mais por `pick_ninjutsu_jutsu`)."""
    if monster_element in ELEMENT_ORDER:
        i = ELEMENT_ORDER.index(monster_element)
        return ELEMENT_ORDER[(i - 1) % len(ELEMENT_ORDER)]
    return "katon"

def average_monster_dps_vs_player(monster, player_armor):
    """RODADA 8 (fúria de fase, summons como 'pull adicional simples' — ver docstring de
    `simulate_fight`): estimativa DETERMINÍSTICA (sem RNG, mesmo espírito de
    `estimate_weapon_dps`) do dano/segundo médio que UM summon causaria no jogador, pra somar
    como uma 'trickle' contínua de dano de fundo em vez de simular os summons um a um (que
    exigiria todo o aparato de multi-alvo de `simulate_group_fight`, fora do escopo desta
    simplificação). 'melee' sofre só a mitigação de armadura do jogador (defense=0 — nenhuma
    arma tem atributo defense/shield neste jogo, ver `simulate_fight`); elemental/projectile
    passam direto (só 'melee' seta blockArmor, monsters.cpp, mesma regra usada no dano real)."""
    total = 0.0
    for atk in monster.get("attacks", []):
        avg_raw = (atk["damage_min"] + atk["damage_max"]) / 2.0
        if atk["type"] == "melee":
            mitig = 0.0
            if player_armor > 3:
                mitig = (player_armor // 2 + (player_armor - (player_armor % 2 + 1))) / 2.0
            elif player_armor > 0:
                mitig = 1.0
            avg = max(0.0, avg_raw - mitig)
        else:
            avg = avg_raw
        total += avg / atk["cooldown_s"]
    return total

def boss_phase_state_init():
    """RODADA 8 (fúria real de fase — item 1 da missão): estado mutável de fase de um boss ao
    longo de UMA luta, `{'idx': próxima fase a checar, 'mult': multiplicador de dano ATUAL do
    boss}`. Espelha `fired[id]`/`NarutoBossPhases.state[id]` de `boss_phases.lua` (gerado por
    `tools/export_tfs.py`): o índice só AVANÇA (nunca volta pra trás mesmo que uma cura de fase
    empurre o HP de volta pra cima — mesmo comportamento do Lua real, que só compara pra frente)."""
    return {"idx": 0, "mult": 1.0}

def apply_boss_phase_tick(monster, monster_hp, monster_hp_max, state, extra_dps_ref, player_armor):
    """RODADA 8: replica `NarutoBossPhases.onHealthChange` (server/generated/scripts/naruto/
    boss_phases.lua) — chamar logo após CADA dano individual aplicado ao boss (um golpe de
    arma, um cast de jutsu), nunca uma vez só por tick de 0.1s (o hook real dispara por golpe).
    `pct` é um SNAPSHOT do HP pós-dano deste golpe e não é recalculado dentro do laço mesmo após
    a cura de fase — mesmo comportamento do Lua real (a variável `pct` é lida uma vez só antes
    do `while`), então um golpe grande o bastante pode cruzar mais de uma fase de uma vez.
    Por fase cruzada: (1) se tiver `attack_multiplier`, vira o multiplicador de dano ATUAL
    (fica valendo daqui pra frente) e aplica a cura pontual `+max_hp*(mult-1)*0,10` (mesma
    fórmula do Lua real: `math.floor(getMaxHealth()*(mult-1)*0.10)`, aqui sem o floor porque o
    HP do simulador já é tratado como float); (2) summons somam no 'DPS extra' de pull
    simplificado (`average_monster_dps_vs_player`) — ver docstring de `simulate_fight` pra por
    que summons não são simulados um a um. Retorna o `monster_hp` (pode ter subido pela cura,
    capado em `monster_hp_max`)."""
    phases = monster.get("phases")
    if not phases:
        return monster_hp
    pct = monster_hp * 100.0 / monster_hp_max
    while state["idx"] < len(phases) and pct <= phases[state["idx"]]["hp_percent"]:
        ph = phases[state["idx"]]
        state["idx"] += 1
        if "attack_multiplier" in ph:
            state["mult"] = ph["attack_multiplier"]
            heal = monster_hp_max * (ph["attack_multiplier"] - 1.0) * 0.10
            if heal > 0:
                monster_hp = min(monster_hp_max, monster_hp + heal)
        for s in ph.get("summons", []):
            sm = MONSTERS.get(s["monster_id"])
            if sm:
                extra_dps_ref[0] += average_monster_dps_vs_player(sm, player_armor) * s.get("count", 1)
    return monster_hp

def pick_ninjutsu_jutsu(monster_element, level, ninjutsu_skill, taijutsu_dps_est=0.0, no_fallback=False):
    """Escolhe, para o build ninjutsu/híbrido: (1) o set elemental com VANTAGEM sobre o monstro
    se existir (jogador escolheria isso na criação de personagem); senão katon (arbitrário —
    todo elemento tem exatamente 1 vantagem e 1 desvantagem, então sempre há uma vantagem real
    exceto p/ monstros 'none'); (2) dentro dos 4 jutsus do set, o de MAIOR dano por segundo
    (base+level*level_scale+maglevel*skill_scale, sobre o cooldown, ×multiplicador elemental)
    já desbloqueado (`required_level <= level`) — um jogador otimizando a rotação sempre usaria
    o jutsu mais forte disponível, não só o projétil tier 1.

    FIX (rodada 2 do balanceamento): o jutsu só é de fato usado se seu dps esperado superar
    `taijutsu_dps_est` (dps de arma pós-mitigação estimado, ver estimate_weapon_dps) — sem essa
    comparação, a rodada 1 usava QUALQUER jutsu sempre que havia chakra, mesmo quando ele fazia
    MENOS dano por segundo que simplesmente golpear com a arma (bug real: em bosses de nível
    alto, o único jutsu do elemento com vantagem já desbloqueado às vezes é pior que a arma, e
    'gastar' a ação nele natualmente PIORA o TTK ao invés de ajudar). Devolve jutsu=None quando
    nenhum candidato bate a arma — o build então luta como taijutsu puro pro resto da luta, o
    que é o que um jogador racional faria.

    `no_fallback` (rodada 3): desliga essa checagem — devolve sempre o melhor jutsu do kit
    (nunca `None`), mesmo que ele faça menos dano/s que a arma. Usado só para o DIAGNÓSTICO
    "curva pura de ninjutsu" (`--no-fallback`/`--build ninjutsu`) pedido na missão da rodada 3:
    mede o que a build ninjutsu FAZ quando obrigada a lutar 100% de jutsu (chakra permitindo),
    em vez de medir o que ela faz quando o jogador racionalmente desiste do jutsu — as duas
    perguntas são diferentes e a rodada 2 só respondia a segunda."""
    if monster_element in ELEMENT_ORDER:
        i = ELEMENT_ORDER.index(monster_element)
        adv_element = ELEMENT_ORDER[(i - 1) % len(ELEMENT_ORDER)]
    else:
        adv_element = "katon"
    eset = ELEMENT_SETS.get(adv_element)
    candidates = [JUTSUS[jid] for jid in eset["jutsus"] if JUTSUS[jid].get("required_level", 1) <= level
                  and JUTSUS[jid]["base_damage"] > 0]
    if not candidates:
        return adv_element, None
    mult = elemental_multiplier(adv_element, monster_element)
    best = max(candidates, key=lambda j: mult * (j["base_damage"] + level * j["level_scale"]
                                                  + ninjutsu_skill * j["skill_scale"]) / j["cooldown_s"])
    best_rate = mult * (best["base_damage"] + level * best["level_scale"]
                         + ninjutsu_skill * best["skill_scale"]) / best["cooldown_s"]
    if not no_fallback and best_rate <= taijutsu_dps_est:
        return adv_element, None
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

def simulate_fight(level, monster, build, rng, max_seconds=600.0, use_potions=True, no_fallback=False,
                    use_chakra_pills=False):
    """Simulação por eventos (dt discreto de 0.1s é suficiente pra granularidade de cooldowns
    de 1.5-12s deste jogo). Retorna dict com ttk_s, dmg_taken, chakra_spent, died(bool).

    `use_potions`: joga como um jogador de verdade jogaria — bebe a melhor poção de vida
    disponível pro nível quando HP cai abaixo de POTION_HEAL_THRESHOLD (loot e ryo do próprio
    monstro cobrem isso perto da faixa recomendada, ver relatório). Sem isso, TODO boss (que
    é justamente pensado para gastar poção) aparece como "mata o jogador" mesmo quando é uma
    luta perfeitamente normal com poções — ver docs/sistemas/monstros-e-pvm.md.

    `use_chakra_pills` (rodada 4, item 1/5 da missão — pendência da rodada 3): bebe a melhor
    pílula de chakra desbloqueada (`_CHAKRA_POTIONS`) quando o chakra não basta mais pro jutsu
    escolhido, mesma lógica de `hp_potion` acima (cooldown de 1s — aproximação documentada,
    não uma exhaustion real: `server/tfs/data/actions/scripts/other/potions.lua:onUse` não seta
    nenhuma `Condition`/exhaustion pro item, TFS 1.4.2 deixa beber poção tão rápido quanto o
    cliente manda o pacote; sem ALGUM cooldown o Monte Carlo bebe uma pilha inteira num só tick
    de 0.1s). Desligado por padrão (preserva a curva 1×1 de boss calibrada sem pílula desde a
    rodada 2); ligado por `simulate_hunt` (cenário de 30 min, onde a pergunta É "quantas pílulas
    isso consome").

    HÍBRIDO (rodada 4, "burst feel"): arma e jutsu correm em CADÊNCIAS INDEPENDENTES — o
    personagem ataca com a arma no intervalo normal (`ATTACK_INTERVAL_S`) e, por cima, lança o
    jutsu sempre que ele estiver pronto (cooldown 3-4s, ver `data/jutsus/*.json`) e pagável —
    isso é o "arma entre casts" pedido na missão, possível agora que o cooldown de tier 1 (3-4s)
    é maior que o intervalo de ataque do player (2,0s, `ATTACK_INTERVAL_S`), deixando uma janela
    ociosa real entre casts que um jogador de verdade preencheria com golpes de arma. NINJUTSU
    PURO continua no modelo de AÇÃO ÚNICA (jutsu OU arma, nunca os dois no mesmo intervalo) —
    é o "caster" que abre mão do ataque básico pra se concentrar em jutsu quando o jutsu vale a
    pena (mesma lógica de fallback da rodada 2/3: `pick_ninjutsu_jutsu`); é esse modelo exclusivo
    que mantém a curva −15%/+10% de paridade sustentada calibrada nas rodadas 2/3.

    FÚRIA DE BOSS (rodada 8, item 1 da missão — `phases[].attack_multiplier`/`summons` de
    `data/monsters/*.json`, antes ignorados aqui): replica `boss_phases.lua` gerado (ver
    `boss_phase_state_init`/`apply_boss_phase_tick`) — ao cruzar o `hp_percent` de uma fase, o
    multiplicador de dano do boss passa a valer de verdade sobre TODO ataque do boss (melee e
    elemental, nunca sobre summons) daqui pra frente, com a mesma cura pontual do Lua real
    (`+max_hp*(mult-1)*0,10`). `summons` viram uma trickle contínua de dano de fundo (ver
    `average_monster_dps_vs_player`) — aproximação deliberada ("pull adicional simples" pedido
    na missão): não simula os summons um a um (isso é o que `simulate_group_fight` já faz para
    pulls de verdade), só soma o DPS médio deles ao dano recebido pelo jogador pelo resto da
    luta."""
    p = SimPlayer(level, build, rng)
    monster_hp_max = monster["hp"]
    monster_hp = monster_hp_max
    boss_phase = boss_phase_state_init()   # RODADA 8: fúria real de fase, ver docstring acima
    extra_dps_summons = [0.0]              # RODADA 8: "pull adicional simples" dos summons
    m_defense = monster["defense"]
    m_armor = monster["defense"]  # export_tfs.py: <defenses armor=X defense=X/> (mesmo valor)
    attacks = monster["attacks"]
    next_monster_attack = [0.0] * len(attacks)
    player_element, jutsu = (None, None)
    if build == "ninjutsu":
        taijutsu_dps_est = estimate_weapon_dps(p, m_defense, m_armor)
        player_element, jutsu = pick_ninjutsu_jutsu(monster["element"], level, p.ninjutsu,
                                                      taijutsu_dps_est, no_fallback=no_fallback)
    elif build == "hybrid":
        # RODADA 8 (substitui a seleção por `pick_ninjutsu_jutsu` + `HYBRID_JUTSU_CADENCE_FRAC`
        # — ver comentário acima da constante removida): o híbrido sempre conjura o TIER 1 do
        # elemento com vantagem, no cooldown REAL, sempre que pronto e pagável — "castar o tier
        # 1 sempre que libera e tem chakra", o jeito que um jogador de verdade joga híbrido
        # (medido no playtest da rodada 5), não uma seleção racional por "melhor dps/cooldown do
        # kit já desbloqueado" com cadência artificialmente esticada por cima.
        player_element = advantage_element(monster["element"])
        eset = ELEMENT_SETS.get(player_element)
        jutsu = JUTSUS[eset["jutsus"][0]] if eset else None
    interleave = (build == "hybrid")   # ver docstring acima
    next_player_action = 0.0   # modo exclusivo (taijutsu/ninjutsu/shuriken)
    next_weapon_action = 0.0   # modo híbrido: cadência da arma
    next_jutsu_action = 0.0    # modo híbrido: cadência do jutsu (independente da arma)
    t = 0.0
    dt = 0.1  # granularidade suficiente p/ cooldowns de 1.5-12s deste jogo; mantém a matriz <120s
    dmg_taken_total = 0.0
    chakra_spent_total = 0.0
    jutsu_dmg_total = 0.0
    melee_swings = 0
    hp_potion = best_potion(level, _HP_POTIONS) if use_potions else None
    chakra_potion = best_potion(level, _CHAKRA_POTIONS) if use_chakra_pills else None
    potions_used = 0
    ryo_spent_potions = 0
    chakra_potions_used = 0
    next_potion_ok = 0.0
    next_chakra_potion_ok = 0.0

    def _result(died, timeout=False):
        return {
            "ttk_s": t, "dmg_taken": dmg_taken_total, "chakra_spent": chakra_spent_total,
            "died": died, "hp_left_pct": (0.0 if died else p.hp / p.hp_max),
            "melee_swings": melee_swings, "potions_used": potions_used,
            "ryo_spent_potions": ryo_spent_potions, "chakra_potions_used": chakra_potions_used,
            "jutsu_dmg_total": jutsu_dmg_total, **({"timeout": True} if timeout else {}),
        }

    while t < max_seconds:
        # regen contínuo (permanente desde a rodada 4 — CONDITION_REGENERATION ticks=-1 aplicada
        # no login, `server/tfs/data/scripts/naruto/character_switch.lua`; não depende de comida
        # nem é suspensa em combate, ver docs/sistemas/balanceamento.md)
        p.regen_tick(dt)
        if hp_potion and p.hp < POTION_HEAL_THRESHOLD * p.hp_max and t >= next_potion_ok:
            p.hp = min(p.hp_max, p.hp + hp_potion["effect"]["value"])
            potions_used += 1
            ryo_spent_potions += hp_potion["buy_price"]
            next_potion_ok = t + POTION_DRINK_COOLDOWN_S
        if (chakra_potion and jutsu and build in ("ninjutsu", "hybrid")
                and p.chakra < jutsu_chakra_cost(jutsu, p.chakra_max) and t >= next_chakra_potion_ok):
            p.chakra = min(p.chakra_max, p.chakra + chakra_potion["effect"]["value"])
            chakra_potions_used += 1
            ryo_spent_potions += chakra_potion["buy_price"]
            next_chakra_potion_ok = t + POTION_DRINK_COOLDOWN_S

        if interleave:
            # jutsu na sua própria cadência (não consome o turno da arma)
            if jutsu and t >= next_jutsu_action and p.chakra >= jutsu_chakra_cost(jutsu, p.chakra_max):
                p.chakra -= jutsu_chakra_cost(jutsu, p.chakra_max)
                chakra_spent_total += jutsu_chakra_cost(jutsu, p.chakra_max)
                mult = elemental_multiplier(player_element, monster["element"])
                dmg = jutsu_damage(rng, jutsu, level, p.ninjutsu, mult)
                monster_hp -= dmg
                jutsu_dmg_total += dmg
                monster_hp = apply_boss_phase_tick(monster, monster_hp, monster_hp_max, boss_phase,
                                                    extra_dps_summons, p.armor)
                # RODADA 8: cooldown REAL, sem esticamento (ver docstring/HYBRID_JUTSU_CADENCE_FRAC removida).
                next_jutsu_action = t + jutsu["cooldown_s"]
                if monster_hp <= 0:
                    return _result(died=False)
            # arma na sua própria cadência (independente do jutsu — "arma entre casts")
            if t >= next_weapon_action:
                raw = p.roll_weapon_damage()
                dmg = apply_mitigation(rng, raw, m_defense, m_armor)
                monster_hp -= dmg
                melee_swings += 1
                next_weapon_action = t + ATTACK_INTERVAL_S
                monster_hp = apply_boss_phase_tick(monster, monster_hp, monster_hp_max, boss_phase,
                                                    extra_dps_summons, p.armor)
                if monster_hp <= 0:
                    return _result(died=False)
        else:
            if t >= next_player_action:
                used_jutsu = False
                if build in ("ninjutsu", "hybrid") and jutsu and p.chakra >= jutsu_chakra_cost(jutsu, p.chakra_max):
                    p.chakra -= jutsu_chakra_cost(jutsu, p.chakra_max)
                    chakra_spent_total += jutsu_chakra_cost(jutsu, p.chakra_max)
                    mult = elemental_multiplier(player_element, monster["element"])
                    dmg = jutsu_damage(rng, jutsu, level, p.ninjutsu, mult)
                    monster_hp -= dmg
                    jutsu_dmg_total += dmg
                    monster_hp = apply_boss_phase_tick(monster, monster_hp, monster_hp_max, boss_phase,
                                                        extra_dps_summons, p.armor)
                    next_player_action = t + jutsu["cooldown_s"]
                    used_jutsu = True
                if not used_jutsu:
                    raw = p.roll_weapon_damage()
                    # weapons.cpp: WeaponMelee/WeaponDistance ambas setam params.blockedByArmor=
                    # true e blockedByShield=true -> mitigado pela armor/defense do MONSTRO
                    # (monster.h: getArmor()/getDefense() = mType->info.armor/defense, o mesmo
                    # m["defense"] do JSON usado nos dois atributos de <defenses>, ver
                    # tools/export_tfs.py:284).
                    dmg = apply_mitigation(rng, raw, m_defense, m_armor)
                    monster_hp -= dmg
                    melee_swings += 1
                    next_player_action = t + ATTACK_INTERVAL_S
                    monster_hp = apply_boss_phase_tick(monster, monster_hp, monster_hp_max, boss_phase,
                                                        extra_dps_summons, p.armor)
                if monster_hp <= 0:
                    return _result(died=False)
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
                if boss_phase["mult"] > 1.0:
                    # RODADA 8: fúria real — NarutoBossFury multiplica o dano recebido pelo
                    # jogador (arredondado, mesma conta do Lua: floor(abs(x)*mult+0.5)).
                    dmg = int(dmg * boss_phase["mult"] + 0.5)
                p.hp -= dmg
                dmg_taken_total += dmg
                if p.hp <= 0:
                    return _result(died=True)
        if extra_dps_summons[0] > 0:
            # RODADA 8: summons como "pull adicional simples" — trickle contínua de dano de
            # fundo (ver docstring/average_monster_dps_vs_player), não uma simulação por summon.
            dmg = extra_dps_summons[0] * dt
            p.hp -= dmg
            dmg_taken_total += dmg
            if p.hp <= 0:
                return _result(died=True)
        t += dt
    t = max_seconds
    return _result(died=False, timeout=True)

# ============================================================== agregação Monte Carlo
def simulate(level, monster_id, build, trials=60, seed=1234, no_fallback=False, use_chakra_pills=False):
    monster = MONSTERS[monster_id]
    rng = random.Random(seed)
    results = [simulate_fight(level, monster, build, rng, no_fallback=no_fallback,
                               use_chakra_pills=use_chakra_pills) for _ in range(trials)]
    kill_results = [r for r in results if not r["died"] and not r.get("timeout")]
    death_results = [r for r in results if r["died"]]
    dmg_taken = [r["dmg_taken"] for r in results]
    timeouts = sum(1 for r in results if r.get("timeout"))
    chakra_spent = [r["chakra_spent"] for r in kill_results if build in ("ninjutsu", "hybrid")]
    jutsu_dmg_total = sum(r.get("jutsu_dmg_total", 0.0) for r in kill_results)
    chakra_spent_sum = sum(chakra_spent)
    chakra_efficiency = (jutsu_dmg_total / chakra_spent_sum) if chakra_spent_sum > 0 else 0.0
    ttk_kill_mean = statistics.mean([r["ttk_s"] for r in kill_results]) if kill_results else None
    # "DPS só de jutsus" (rodada 3, item 1 da missão): dano feito só via jutsu / tempo de luta,
    # por tentativa vitoriosa — diferente de dividir jutsu_dmg_total pelo ttk médio agregado
    # (isso mistura fights com proporções de fallback diferentes). Com no_fallback=True e chakra
    # suficiente, tende a ttk_kill "quase só jutsu"; sem chakra, cai pro que sobrou de taijutsu
    # de qualquer forma (ver oom_s equivalente em simulate_group).
    jutsu_dps_per_fight = [r.get("jutsu_dmg_total", 0.0) / r["ttk_s"] for r in kill_results if r["ttk_s"] > 0]
    jutsu_dps_pure_mean = round(statistics.mean(jutsu_dps_per_fight), 2) if jutsu_dps_per_fight else 0.0
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
        "chakra_efficiency": round(chakra_efficiency, 2),
        "jutsu_dps_pure_mean": jutsu_dps_pure_mean,
        "potions_per_kill": round(potions_per_kill, 2),
        "xp_per_hour": round(xp_per_hour),
        "ryo_per_hour": round(ryo_per_hour_net),
        "ryo_per_hour_gross": round(ryo_per_hour_gross),
        "loot_value_per_kill": round(loot_value, 1),
    }

# ============================================================== matriz completa
MATRIX_LEVELS = [1, 3, 5, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100]

BUILDS = ("taijutsu", "ninjutsu", "hybrid")

def run_matrix(trials=40, seed=1234):
    out = []
    for level in MATRIX_LEVELS:
        for mid in MONSTERS:
            for build in BUILDS:
                out.append(simulate(level, mid, build, trials=trials, seed=seed))
    return out

# ============================================================== multi-alvo (rodada 2)
# Cenário "pull de N monstros" — mede o valor real de jutsus de área/beam contra grupos, que
# tools/balance/README.md (achado 6/pendência) apontava como o buraco do simulador da rodada 1
# (rotação 1x1 sempre escolhe o jutsu de cooldown mais curto, nunca testando área/beam de verdade).

def area_capacity(shape):
    """Número de casas afetadas por uma forma de área/beam — espelha exatamente
    tools/export_tfs.py:183 area_matrix() (mesmos nomes de forma: circle_rN, cross_rN, cone_N,
    line_N; mesma contagem de células, só sem desenhar a matriz). Usado só para decidir quantos
    alvos de um pull uma área/beam alcança (ver hits_for_jutsu)."""
    if not shape:
        return 1
    kind, n = shape.split("_")[0], int(shape.split("_")[1].lstrip("r"))
    if kind == "circle":
        size = 2 * n + 1
        return size * size - 1
    if kind == "cross":
        return 4 * n
    if kind == "line":
        return n
    if kind == "cone":
        return n * n
    return 1

def hits_for_jutsu(jutsu, n_alive):
    """Quantos dos N monstros vivos um jutsu atinge, na geometria simplificada do cenário
    multi-alvo (alvos adjacentes/em linha — ver simulate_group_fight): `target`/`projectile`
    sempre 1 (o de menor HP vivo — 'terminar o mais fraco'); `self` não causa dano a inimigo;
    `area`/`beam` atinge min(N, area_capacity(shape)). Como os pulls deste jogo têm 2-4
    monstros (ver GROUP_SCENARIOS/relatório v2 §1) e a menor área/beam do kit elemental já
    cobre 4+ casas (cross_r1=4, cone_2=4, line_5=5...), na prática isso é sempre N — a
    diferenciação por forma só passaria a importar se um pull tivesse >4 monstros."""
    t = jutsu["type"]
    if t == "self":
        return 0
    if t in ("target", "projectile"):
        return 1
    if t in ("area", "beam"):
        return min(n_alive, area_capacity(jutsu.get("shape")))
    return 1

def element_kit(monster_element, level):
    """Elemento com vantagem sobre o monstro (mesma escolha de pick_ninjutsu_jutsu) e a lista
    COMPLETA dos jutsus ofensivos daquele elemento já desbloqueados (required_level<=level) —
    a rotação multi-alvo escolhe a cada ação entre todos eles (cooldown própria por jutsu),
    diferente de pick_ninjutsu_jutsu (1x1), que escolhe UM jutsu só pra luta inteira porque a
    rotação 1x1 ótima sempre repete o de cooldown mais curto (achado da rodada 1)."""
    if monster_element in ELEMENT_ORDER:
        i = ELEMENT_ORDER.index(monster_element)
        adv_element = ELEMENT_ORDER[(i - 1) % len(ELEMENT_ORDER)]
    else:
        adv_element = "katon"
    eset = ELEMENT_SETS.get(adv_element)
    usable = [JUTSUS[jid] for jid in eset["jutsus"]
              if JUTSUS[jid].get("required_level", 1) <= level and JUTSUS[jid]["base_damage"] > 0]
    return adv_element, usable

def simulate_group_fight(level, monster, build, n_monsters, rng, max_seconds=300.0, use_potions=True):
    """Pull de N cópias do MESMO monstro comum de uma região (geometria simplificada: alvos
    adjacentes/em linha — qualquer área/beam do kit elemental cobre o pull inteiro, ver
    hits_for_jutsu). Chakra finito com regen real (mesmas constantes REGEN_CHAKRA_* de
    simulate_fight), poção de vida como em simulate_fight. Rotação (taijutsu/ninjutsu/híbrido):
    a cada ação, escolhe entre os jutsus do kit elemental prontos (cooldown) E pagáveis (chakra
    disponível) o de MAIOR DANO ESPERADO POR SEGUNDO (dano×alcance / cooldown_s — 'jutsu de
    maior dano/segundo por chakra disponível' pedido na missão) e usa taijutsu (sem custo de
    chakra) como filler sempre que nenhum jutsu do kit está pronto/pagável. Retorna também o
    dano total por jutsu (pra achar jutsu inútil/dominante, ver analyze_v2.py) e o instante em
    que o chakra deixou de bastar pra qualquer jutsu do kit pela última vez antes do fim da
    luta ('tempo até ficar sem chakra', oom_s — None se nunca faltou)."""
    p = SimPlayer(level, build, rng)
    hp_list = [float(monster["hp"])] * n_monsters
    m_defense = monster["defense"]
    m_armor = monster["defense"]
    attacks = monster["attacks"]
    next_monster_attack = [[0.0] * len(attacks) for _ in range(n_monsters)]
    kit = []
    adv_element = None
    if build in ("ninjutsu", "hybrid"):
        adv_element, kit = element_kit(monster["element"], level)
    cooldown_ready = {j["id"]: 0.0 for j in kit}
    next_player_action = 0.0
    t = 0.0
    dt = 0.1
    dmg_taken_total = 0.0
    chakra_spent_total = 0.0
    dmg_by_jutsu = {}
    melee_swings = 0
    hp_potion = best_potion(level, _HP_POTIONS) if use_potions else None
    potions_used = 0
    ryo_spent_potions = 0
    next_potion_ok = 0.0
    chakra_since_t = None   # instante em que o chakra deixou de bastar (reseta a cada cast ok)
    while t < max_seconds:
        p.regen_tick(dt)
        if hp_potion and p.hp < POTION_HEAL_THRESHOLD * p.hp_max and t >= next_potion_ok:
            p.hp = min(p.hp_max, p.hp + hp_potion["effect"]["value"])
            potions_used += 1
            ryo_spent_potions += hp_potion["buy_price"]
            next_potion_ok = t + POTION_DRINK_COOLDOWN_S
        n_alive = sum(1 for hp in hp_list if hp > 0)
        if n_alive == 0:
            return {"clear_s": t, "dmg_taken": dmg_taken_total, "chakra_spent": chakra_spent_total,
                    "died": False, "hp_left_pct": p.hp / p.hp_max, "melee_swings": melee_swings,
                    "potions_used": potions_used, "ryo_spent_potions": ryo_spent_potions,
                    "dmg_by_jutsu": dmg_by_jutsu, "oom_s": chakra_since_t}
        if t >= next_player_action:
            mult = elemental_multiplier(adv_element, monster["element"]) if adv_element else 1.0
            best_j, best_rate = None, -1.0
            for j in kit:
                if cooldown_ready[j["id"]] > t or p.chakra < jutsu_chakra_cost(j, p.chakra_max):
                    continue
                hits = hits_for_jutsu(j, n_alive)
                if hits <= 0:
                    continue
                avg_dmg = (j["base_damage"] + level * j["level_scale"] + p.ninjutsu * j["skill_scale"]) * mult
                rate = (avg_dmg * hits) / j["cooldown_s"]
                if rate > best_rate:
                    best_rate, best_j = rate, j
            if best_j is not None:
                p.chakra -= jutsu_chakra_cost(best_j, p.chakra_max)
                chakra_spent_total += jutsu_chakra_cost(best_j, p.chakra_max)
                hits = hits_for_jutsu(best_j, n_alive)
                targets = sorted((i for i, hp in enumerate(hp_list) if hp > 0),
                                  key=lambda i: hp_list[i])[:hits]
                for i in targets:
                    dmg = jutsu_damage(rng, best_j, level, p.ninjutsu, mult)
                    hp_list[i] -= dmg
                    dmg_by_jutsu[best_j["id"]] = dmg_by_jutsu.get(best_j["id"], 0.0) + dmg
                cooldown_ready[best_j["id"]] = t + best_j["cooldown_s"]
                next_player_action = t + best_j["cooldown_s"]
                chakra_since_t = None
            else:
                if kit:
                    if chakra_since_t is None:
                        chakra_since_t = t
                target_i = min((i for i, hp in enumerate(hp_list) if hp > 0), key=lambda i: hp_list[i])
                raw = p.roll_weapon_damage()
                dmg = apply_mitigation(rng, raw, m_defense, m_armor)
                hp_list[target_i] -= dmg
                dmg_by_jutsu["_taijutsu"] = dmg_by_jutsu.get("_taijutsu", 0.0) + dmg
                melee_swings += 1
                next_player_action = t + ATTACK_INTERVAL_S
        for mi in range(n_monsters):
            if hp_list[mi] <= 0:
                continue
            for i, atk in enumerate(attacks):
                if t >= next_monster_attack[mi][i]:
                    next_monster_attack[mi][i] = t + atk["cooldown_s"]
                    raw = _normal_random(rng, atk["damage_min"], atk["damage_max"])
                    dmg = apply_mitigation(rng, raw, 0, p.armor) if atk["type"] == "melee" else raw
                    p.hp -= dmg
                    dmg_taken_total += dmg
                    if p.hp <= 0:
                        return {"clear_s": t, "dmg_taken": dmg_taken_total,
                                "chakra_spent": chakra_spent_total, "died": True, "hp_left_pct": 0.0,
                                "melee_swings": melee_swings, "potions_used": potions_used,
                                "ryo_spent_potions": ryo_spent_potions, "dmg_by_jutsu": dmg_by_jutsu,
                                "oom_s": chakra_since_t}
        t += dt
    return {"clear_s": max_seconds, "dmg_taken": dmg_taken_total, "chakra_spent": chakra_spent_total,
            "died": False, "hp_left_pct": p.hp / p.hp_max, "melee_swings": melee_swings,
            "timeout": True, "potions_used": potions_used, "ryo_spent_potions": ryo_spent_potions,
            "dmg_by_jutsu": dmg_by_jutsu, "oom_s": chakra_since_t}

def simulate_group(level, monster_id, build, n_monsters, trials=20, seed=1234):
    monster = MONSTERS[monster_id]
    rng = random.Random(seed)
    results = [simulate_group_fight(level, monster, build, n_monsters, rng) for _ in range(trials)]
    clears = [r for r in results if not r["died"] and not r.get("timeout")]
    deaths = [r for r in results if r["died"]]
    total_time_s = sum(r["clear_s"] for r in results) + len(clears) * DOWNTIME_BETWEEN_KILLS_S
    xp_award = monster["xp"] * RATE_EXP * n_monsters
    total_xp = len(clears) * xp_award
    xp_per_hour = (total_xp / total_time_s) * 3600 if total_time_s > 0 else 0
    ryo_avg = (monster["ryo_min"] + monster["ryo_max"]) / 2
    loot_value = 0.0
    for l in monster.get("loot", []):
        item = ITEMS.get(l["item_id"])
        sell = item.get("sell_price", 0) if item else 0
        chance = min(1.0, l["chance"] * RATE_LOOT)
        avg_count = (l.get("min", 1) + l.get("max", 1)) / 2
        loot_value += chance * avg_count * sell
    total_ryo_gross = len(clears) * n_monsters * (ryo_avg + loot_value)
    total_ryo_potions = sum(r.get("ryo_spent_potions", 0) for r in results)
    ryo_per_hour_net = ((total_ryo_gross - total_ryo_potions) / total_time_s) * 3600 if total_time_s > 0 else 0
    chakra_spent = [r["chakra_spent"] for r in clears if build in ("ninjutsu", "hybrid")]
    total_chakra = sum(chakra_spent)
    total_dmg_via_jutsu = sum(
        sum(v for k, v in r.get("dmg_by_jutsu", {}).items() if k != "_taijutsu") for r in clears)
    chakra_efficiency = (total_dmg_via_jutsu / total_chakra) if total_chakra > 0 else 0.0
    oom_values = [r["oom_s"] for r in results if r.get("oom_s") is not None]
    dmg_by_jutsu_total = {}
    for r in results:
        for k, v in r.get("dmg_by_jutsu", {}).items():
            dmg_by_jutsu_total[k] = dmg_by_jutsu_total.get(k, 0.0) + v
    return {
        "level": level, "monster_id": monster_id, "monster_level": monster["level"],
        "build": build, "n_monsters": n_monsters, "trials": trials,
        "clear_s_mean": round(statistics.mean([r["clear_s"] for r in clears]), 2) if clears else None,
        "death_rate": round(len(deaths) / trials, 3),
        "timeout_rate": round(sum(1 for r in results if r.get("timeout")) / trials, 3),
        "chakra_spent_mean": round(statistics.mean(chakra_spent), 1) if chakra_spent else 0.0,
        "chakra_efficiency": round(chakra_efficiency, 2),
        "oom_s_mean": round(statistics.mean(oom_values), 1) if oom_values else None,
        "potions_per_clear": (round(sum(r.get("potions_used", 0) for r in results) / len(clears), 2)
                               if clears else 0.0),
        "xp_per_hour": round(xp_per_hour),
        "ryo_per_hour": round(ryo_per_hour_net),
        "dmg_by_jutsu": {k: round(v, 1) for k, v in
                          sorted(dmg_by_jutsu_total.items(), key=lambda kv: -kv[1])},
    }

# Cenários por região: monstros comuns representativos (nível real de data/monsters/*.json) +
# boss, e N do pull POR MONSTRO (não por região — FIX rodada 2, ver
# docs/sistemas/balanceamento-relatorio-v2.md §1). N vem de clustering real medido em
# data/maps/forest_valley.json (union-find, raio 10 tiles, mesma espécie — script de medição no
# relatório v2 §1) pras 4 regiões que já têm mapa jogável; `data/maps/spawns_lore.json` tem
# "spawns": [] de propósito (é um PEDIDO ao agente de mapa, não geometria real — só os
# "requests" com `count` por zona) então costa_das_mares/covil_da_nuvem_vermelha (regiões SEM
# mapa físico ainda, 0 spawns encontrados pro clustering) usam um placeholder conservador N=2
# (pull pequeno), não o `count` total da zona inteira (que mediria "quantos spawns cabem na
# região", não "quantos um jogador puxa de uma vez" — infla N sem necessidade).
# ACHADO (rodada 2): medindo o clustering real, leech/lesser_serpent (floresta_da_morte) NÃO
# têm nenhum par a <=10 tiles no mapa atual (spawns a 12-26 tiles um do outro) — n real = 1, ou
# seja essa região não tem cluster de 2+ jogável hoje (rodada 1 tinha usado n=3 pra toda a
# região sem medir; isso inflava artificialmente o "achado" de ninjutsu dominando ali, ver §1).
GROUP_SCENARIOS = [
    {"region": "floresta_da_vila", "commons": [("wolf", 2, 3), ("bandit", 5, 2)],
     "boss": ("boss_bandit_chief", 12)},
    {"region": "costa_das_mares", "commons": [("mercenary_bridge", 12, 2), ("mist_guardian", 16, 2)],
     "boss": ("boss_mist_swordsman", 19)},
    {"region": "floresta_da_morte", "commons": [("leech", 10, 1), ("lesser_serpent", 18, 1)],
     "boss": ("boss_white_serpent", 25)},
    {"region": "ruinas_do_cla_marionetista", "commons": [("ruin_puppet", 27, 3), ("curse_shaman", 44, 2)],
     "boss": ("boss_puppeteer", 50)},
    {"region": "montanha_do_trovao", "commons": [("thunder_eagle", 54, 3), ("storm_monk", 68, 2)],
     "boss": ("boss_ancestral_oni", 80)},
    {"region": "covil_da_nuvem_vermelha", "commons": [("white_clone", 82, 2), ("elite_cloud_guard", 88, 2)],
     "boss": ("boss_crimson_ancestor", 100)},
]

def run_group_matrix(trials=20, seed=1234):
    out = []
    for scen in GROUP_SCENARIOS:
        for mid, lvl, n in scen["commons"]:
            for build in BUILDS:
                out.append(simulate_group(lvl, mid, build, n, trials=trials, seed=seed))
    return out

def run_boss_matrix(trials=30, seed=1234):
    """1x1 nos bosses de cada região (reaproveita simulate() com build 'hybrid' incluso) —
    'luta longa' pra comparar taijutsu/ninjutsu/híbrido lado a lado com os cenários de grupo."""
    out = []
    for scen in GROUP_SCENARIOS:
        bid, lvl = scen["boss"]
        for build in BUILDS:
            out.append(simulate(lvl, bid, build, trials=trials, seed=seed))
    return out

# ============================================================== hunt de 30 min (rodada 4)
# Missão item 1: "medir chakra sustentável" numa SESSÃO DE CAÇA, não numa luta única — uma
# sequência de pulls do monstro comum mais próximo do nível pedido, com pausas realistas
# (5-15s: andar até o próximo alvo + lootar, ver DOWNTIME_BETWEEN_KILLS_S — aqui usamos a faixa
# pedida pela missão em vez do valor fixo de 3.0s do XP/h "throughput máximo") entre lutas, HP e
# CHAKRA persistindo (com regen contínuo) de uma luta pra outra. Mede a fração do tempo de caça
# em que o chakra fica ABAIXO do custo do tier 1 do elemento escolhido (jutsu índice 0 de
# `element_sets.json` — sempre o projétil básico, ver ELEMENT_SETS) — a pergunta literal da
# missão ("o híbrido não fica >20% do tempo sem chakra pro tier 1 sem pílulas").
DEATH_RECOVERY_S = 75.0   # docs/qa/playtest-l1-20-r3.md: ~25-30s desconectado + ~75s de viagem
                          # de volta ao spot médios de uma morte real — usamos o valor de viagem
                          # citado no playtest (mais conservador que o de contar só a desconexão)

def nearest_common_monster(level):
    """Monstro comum (não-boss) de `data/monsters/*.json` com nível mais próximo do pedido —
    usado pra escolher automaticamente o alvo de uma hunt/pull quando só o nível é informado
    (ver GROUP_SCENARIOS pra cenários com N de pull já medido por região)."""
    candidates = [m for m in MONSTERS.values() if not m["id"].startswith("boss_")]
    return min(candidates, key=lambda m: abs(m["level"] - level))["id"]

def simulate_hunt(level, monster_id, build, minutes=30, use_chakra_pills=False, seed=1234,
                   pause_min_s=5.0, pause_max_s=15.0, force_tier1=False):
    """Sequência de pulls 1x1 do mesmo monstro comum, HP/chakra do player persistindo (com
    regen contínuo) entre uma luta e a próxima — ver cabeçalho da seção acima. Cada pull reusa
    a MESMA lógica de ação de `simulate_fight` (híbrido intercalado / ninjutsu exclusivo, fúria
    de fase/summons desde a rodada 8 — ver `apply_boss_phase_tick`), só que sem recriar o
    SimPlayer a cada luta. Uma morte custa `DEATH_RECOVERY_S` + a pausa normal (o personagem
    volta com HP/chakra cheios, confirmado no playtest — reconectar no templo); fase de fúria e
    summons resetam a cada novo pull (kill ou morte), igual ao `onDeath` real de `boss_phases.lua`.

    RODADA 8 (item 2 da missão — substitui `HYBRID_JUTSU_CADENCE_FRAC`): o build 'hybrid' SEMPRE
    conjura o tier 1 (índice 0 do kit do elemento com vantagem) no cooldown REAL, sempre que
    pronto e pagável — não passa mais por `pick_ninjutsu_jutsu` nem por nenhuma cadência
    esticada (ver `simulate_fight`). `force_tier1` não tem mais efeito sobre o build 'hybrid'
    (já é sempre tier 1); ele continua servindo só o build 'ninjutsu' puro, mantendo a leitura de
    diagnóstico da rodada 7 (ver docstring abaixo e relatório v7 §5 "segunda leitura").

    `force_tier1` (RODADA 7, achado central da missão "chakra voltou a não ser um recurso",
    agora só relevante pro build 'ninjutsu'): sem isso, o jutsu de fato conjurado é o de
    `pick_ninjutsu_jutsu` (maior dano/segundo do kit JÁ DESBLOQUEADO), que abandona o tier 1
    assim que o primeiro tier 2 do elemento desbloqueia (`required_level` 12-26 conforme o
    elemento, ver `data/jutsus/*.json`). `force_tier1=True` conjura SEMPRE o projétil tier 1
    (índice 0 do kit elemental), ignorando a seleção por maior DPS."""
    rng = random.Random(seed)
    monster = MONSTERS[monster_id]
    p = SimPlayer(level, build, rng)
    m_defense = monster["defense"]
    m_armor = monster["defense"]
    player_element, jutsu = (None, None)
    if build == "ninjutsu":
        taijutsu_dps_est = estimate_weapon_dps(p, m_defense, m_armor)
        player_element, jutsu = pick_ninjutsu_jutsu(monster["element"], level, p.ninjutsu,
                                                      taijutsu_dps_est, no_fallback=force_tier1)
    elif build == "hybrid":
        # RODADA 8: sempre tier 1 (ver docstring) — não passa por pick_ninjutsu_jutsu.
        player_element = advantage_element(monster["element"])
    tier1 = None
    if player_element:
        eset = ELEMENT_SETS.get(player_element)
        if eset:
            tier1 = JUTSUS[eset["jutsus"][0]]   # índice 0 = sempre o projétil tier 1, ver header
    if build == "hybrid":
        jutsu = tier1
    elif force_tier1 and tier1:
        jutsu = tier1
    tier1_cost = jutsu_chakra_cost(tier1, p.chakra_max) if tier1 else None
    interleave = (build == "hybrid")
    hp_potion = best_potion(level, _HP_POTIONS)
    chakra_potion = best_potion(level, _CHAKRA_POTIONS) if use_chakra_pills else None

    total_s = minutes * 60.0
    dt = 0.1
    t = 0.0
    time_below_tier1 = 0.0
    kills = 0
    deaths = 0
    total_chakra_spent = 0.0
    total_jutsu_dmg = 0.0
    chakra_potions_used = 0
    ryo_spent_chakra_potions = 0
    hp_potions_used = 0
    ryo_spent_hp_potions = 0
    next_potion_ok = 0.0
    next_chakra_potion_ok = 0.0
    next_weapon_action = 0.0
    next_jutsu_action = 0.0
    next_player_action = 0.0
    monster_hp_max = monster["hp"]
    monster_hp = monster_hp_max
    boss_phase = boss_phase_state_init()   # RODADA 8: fúria real de fase, ver simulate_fight
    extra_dps_summons = [0.0]              # RODADA 8: "pull adicional simples" dos summons
    attacks = monster["attacks"]
    next_monster_attack = [0.0] * len(attacks)
    in_fight = True
    resume_at = 0.0
    while t < total_s:
        p.regen_tick(dt)
        if tier1_cost is not None and p.chakra < tier1_cost:
            time_below_tier1 += dt
        if hp_potion and p.hp < POTION_HEAL_THRESHOLD * p.hp_max and t >= next_potion_ok:
            p.hp = min(p.hp_max, p.hp + hp_potion["effect"]["value"])
            hp_potions_used += 1
            ryo_spent_hp_potions += hp_potion["buy_price"]
            next_potion_ok = t + POTION_DRINK_COOLDOWN_S
        if (chakra_potion and tier1_cost is not None and p.chakra < tier1_cost
                and t >= next_chakra_potion_ok):
            p.chakra = min(p.chakra_max, p.chakra + chakra_potion["effect"]["value"])
            chakra_potions_used += 1
            ryo_spent_chakra_potions += chakra_potion["buy_price"]
            next_chakra_potion_ok = t + POTION_DRINK_COOLDOWN_S

        if in_fight:
            died_this_tick = False
            if interleave:
                if jutsu and t >= next_jutsu_action and p.chakra >= jutsu_chakra_cost(jutsu, p.chakra_max):
                    p.chakra -= jutsu_chakra_cost(jutsu, p.chakra_max)
                    total_chakra_spent += jutsu_chakra_cost(jutsu, p.chakra_max)
                    mult = elemental_multiplier(player_element, monster["element"])
                    dmg = jutsu_damage(rng, jutsu, level, p.ninjutsu, mult)
                    monster_hp -= dmg
                    total_jutsu_dmg += dmg
                    monster_hp = apply_boss_phase_tick(monster, monster_hp, monster_hp_max, boss_phase,
                                                        extra_dps_summons, p.armor)
                    # RODADA 8: cooldown REAL, sem esticamento (ver docstring).
                    next_jutsu_action = t + jutsu["cooldown_s"]
                if monster_hp > 0 and t >= next_weapon_action:
                    raw = p.roll_weapon_damage()
                    dmg = apply_mitigation(rng, raw, m_defense, m_armor)
                    monster_hp -= dmg
                    next_weapon_action = t + ATTACK_INTERVAL_S
                    monster_hp = apply_boss_phase_tick(monster, monster_hp, monster_hp_max, boss_phase,
                                                        extra_dps_summons, p.armor)
            else:
                if t >= next_player_action:
                    used_jutsu = False
                    if build == "ninjutsu" and jutsu and p.chakra >= jutsu_chakra_cost(jutsu, p.chakra_max):
                        p.chakra -= jutsu_chakra_cost(jutsu, p.chakra_max)
                        total_chakra_spent += jutsu_chakra_cost(jutsu, p.chakra_max)
                        mult = elemental_multiplier(player_element, monster["element"])
                        dmg = jutsu_damage(rng, jutsu, level, p.ninjutsu, mult)
                        monster_hp -= dmg
                        total_jutsu_dmg += dmg
                        monster_hp = apply_boss_phase_tick(monster, monster_hp, monster_hp_max, boss_phase,
                                                            extra_dps_summons, p.armor)
                        next_player_action = t + jutsu["cooldown_s"]
                        used_jutsu = True
                    if not used_jutsu:
                        raw = p.roll_weapon_damage()
                        dmg = apply_mitigation(rng, raw, m_defense, m_armor)
                        monster_hp -= dmg
                        next_player_action = t + ATTACK_INTERVAL_S
                        monster_hp = apply_boss_phase_tick(monster, monster_hp, monster_hp_max, boss_phase,
                                                            extra_dps_summons, p.armor)
            if monster_hp <= 0:
                kills += 1
                in_fight = False
                resume_at = t + rng.uniform(pause_min_s, pause_max_s)
                monster_hp = monster_hp_max
                boss_phase = boss_phase_state_init()   # RODADA 8: reset por pull (onDeath real)
                extra_dps_summons = [0.0]
                next_monster_attack = [0.0] * len(attacks)
            else:
                for i, atk in enumerate(attacks):
                    if t >= next_monster_attack[i]:
                        next_monster_attack[i] = t + atk["cooldown_s"]
                        raw = _normal_random(rng, atk["damage_min"], atk["damage_max"])
                        dmg = apply_mitigation(rng, raw, 0, p.armor) if atk["type"] == "melee" else raw
                        if boss_phase["mult"] > 1.0:
                            dmg = int(dmg * boss_phase["mult"] + 0.5)
                        p.hp -= dmg
                        if p.hp <= 0:
                            deaths += 1
                            p.hp = p.hp_max     # relogin no templo: HP/chakra cheios (playtest)
                            p.chakra = p.chakra_max
                            in_fight = False
                            resume_at = t + rng.uniform(pause_min_s, pause_max_s) + DEATH_RECOVERY_S
                            monster_hp = monster_hp_max
                            boss_phase = boss_phase_state_init()   # RODADA 8: reset por pull
                            extra_dps_summons = [0.0]
                            next_monster_attack = [0.0] * len(attacks)
                            died_this_tick = True
                            break
                if not died_this_tick and extra_dps_summons[0] > 0:
                    dmg = extra_dps_summons[0] * dt
                    p.hp -= dmg
                    if p.hp <= 0:
                        deaths += 1
                        p.hp = p.hp_max
                        p.chakra = p.chakra_max
                        in_fight = False
                        resume_at = t + rng.uniform(pause_min_s, pause_max_s) + DEATH_RECOVERY_S
                        monster_hp = monster_hp_max
                        boss_phase = boss_phase_state_init()
                        extra_dps_summons = [0.0]
                        next_monster_attack = [0.0] * len(attacks)
            if died_this_tick:
                pass
        else:
            if t >= resume_at:
                in_fight = True
                next_weapon_action = t
                next_jutsu_action = max(next_jutsu_action, t)
                next_player_action = t
        t += dt
    pct_below = time_below_tier1 / t if t > 0 else 0.0
    # RODADA 7 (métrica nova pedida na missão): "casts por pool cheio" e "tempo até pool cheio"
    # são ANALÍTICOS (não dependem de rodar a hunt inteira) — ver funções abaixo, reusadas aqui
    # só para não duplicar a conta na tabela do relatório.
    casts_per_pool = casts_per_full_pool(tier1, p.chakra_max) if tier1 else None
    time_to_full_s = time_to_refill_pool_s(level, p.chakra_max) if tier1 else None
    return {
        "level": level, "monster_id": monster_id, "build": build, "minutes": minutes,
        "use_chakra_pills": use_chakra_pills, "force_tier1": force_tier1,
        "kills": kills, "deaths": deaths,
        "chakra_spent_total": round(total_chakra_spent, 1),
        "jutsu_dmg_total": round(total_jutsu_dmg, 1),
        "chakra_potions_used": chakra_potions_used,
        "ryo_spent_chakra_potions": ryo_spent_chakra_potions,
        "hp_potions_used": hp_potions_used,
        "ryo_spent_hp_potions": ryo_spent_hp_potions,
        "pct_time_without_chakra_for_tier1": round(pct_below, 3),
        "tier1_jutsu": tier1["id"] if tier1 else None,
        "tier1_chakra_cost": tier1_cost,
        "casts_per_full_pool": casts_per_pool,
        "time_to_full_pool_s": time_to_full_s,
    }

# RODADA 5: era [5, 15, 30, 60, 100] — a missão pede a meta de sustentabilidade verificada em
# TODOS os níveis 5..100, não só 5 amostras; de 5 em 5 (20 pontos) ainda roda em <1s (a hunt em
# si é ~0.05s/simulação) e já pega o único ponto fora da curva suave encontrado nesta rodada
# (L20-23, monstro `exam_rival_stone` com HP acima da média da faixa — ver relatório v5 §1).
HUNT_LEVELS = list(range(5, 101, 5))

def run_hunt_matrix(minutes=30, seed=1234, force_tier1=True):
    """Roda a hunt de 30 min em HUNT_LEVELS, build 'hybrid' (a build que a missão pede medir —
    'o jogador gerencia o chakra do tier 1'), com E sem pílula de chakra.

    `force_tier1=True` (RODADA 7, default — ver docstring de `simulate_hunt`): conjura sempre o
    projétil tier 1, não o "melhor DPS do kit" (que vira tier 2/3 a partir de L12-26 e torna a
    métrica de chakra do tier 1 um artefato de contabilidade, não uso real — achado desta
    rodada). `force_tier1=False` preserva o comportamento das rodadas 4-6 (métrica antiga,
    'tempo sem chakra pra QUALQUER coisa do kit', não só tier 1)."""
    out = []
    for level in HUNT_LEVELS:
        mid = nearest_common_monster(level)
        for use_pills in (False, True):
            out.append(simulate_hunt(level, mid, "hybrid", minutes=minutes,
                                      use_chakra_pills=use_pills, seed=seed,
                                      force_tier1=force_tier1))
    return out

# ============================================================== CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", action="store_true", help="roda level x monstro x build completo (1x1)")
    ap.add_argument("--group-matrix", action="store_true",
                     help="roda o cenário multi-alvo (pull por região) + bosses, builds taijutsu/ninjutsu/hybrid")
    ap.add_argument("--hunt", action="store_true",
                     help="rodada 4: cenário de caça de 30 min (sequência de pulls com pausas "
                          "5-15s) em vez de luta única — mede chakra sustentável de verdade. Com "
                          "--level/--monster/--build roda 1 hunt; sozinho roda HUNT_LEVELS x "
                          "build hybrid, com e sem pílula de chakra (--minutes ajusta a duração).")
    ap.add_argument("--minutes", type=float, default=30.0, help="duração da hunt (--hunt)")
    ap.add_argument("--chakra-pills", action="store_true",
                     help="--hunt/--level+--monster: simula o jogador bebendo pílula de chakra "
                          "quando não consegue pagar o tier 1 (ver _CHAKRA_POTIONS)")
    ap.add_argument("--no-force-tier1", action="store_true",
                     help="--hunt: RODADA 7, desliga force_tier1 (volta ao comportamento das "
                          "rodadas 4-6: conjura o melhor DPS do kit, não sempre o tier 1 — ver "
                          "docstring de simulate_hunt). Por padrão --hunt já roda com "
                          "force_tier1=True (sozinho e com --level/--monster).")
    ap.add_argument("--level", type=int)
    ap.add_argument("--monster")
    ap.add_argument("--n-monsters", type=int, default=1, help="tamanho do pull (--monster vira N cópias)")
    ap.add_argument("--build", choices=["taijutsu", "ninjutsu", "hybrid", "shuriken"], default="taijutsu")
    ap.add_argument("--no-fallback", action="store_true",
                     help="diagnóstico (rodada 3): força a build ninjutsu/híbrido a usar sempre o "
                          "melhor jutsu do kit elemental, mesmo quando ele faz menos dano/s que a "
                          "arma — mede a curva PURA de jutsu (chakra permitindo), não a decisão "
                          "racional de desistir do jutsu. Só afeta --level/--monster (1x1); "
                          "--matrix/--group-matrix continuam com a rotação racional (fallback).")
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

    if args.group_matrix:
        t0 = time.time()
        group_trials = args.trials if args.trials != 30 else 20
        boss_trials = args.trials if args.trials != 30 else 30
        group = run_group_matrix(trials=group_trials)
        boss = run_boss_matrix(trials=boss_trials)
        dt = time.time() - t0
        print(f"# group-matrix: {len(group)} grupo + {len(boss)} boss em {dt:.1f}s", file=sys.stderr)
        out = {"group": group, "boss": boss}
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=1)
            print(f"salvo em {args.json}", file=sys.stderr)
        else:
            print(json.dumps(out, ensure_ascii=False, indent=1))
        return

    if args.hunt:
        t0 = time.time()
        force_tier1 = not args.no_force_tier1
        if args.level and args.monster:
            mid = args.monster
            res = simulate_hunt(args.level, mid, args.build, minutes=args.minutes,
                                 use_chakra_pills=args.chakra_pills, force_tier1=force_tier1)
        else:
            res = run_hunt_matrix(minutes=args.minutes, force_tier1=force_tier1)
        dt = time.time() - t0
        print(f"# hunt: em {dt:.2f}s", file=sys.stderr)
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=1)
            print(f"salvo em {args.json}", file=sys.stderr)
        else:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        return

    if args.level and args.monster and args.n_monsters > 1:
        r = simulate_group(args.level, args.monster, args.build, args.n_monsters, trials=args.trials)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return

    if args.level and args.monster:
        r = simulate(args.level, args.monster, args.build, trials=args.trials, no_fallback=args.no_fallback,
                      use_chakra_pills=args.chakra_pills)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        if args.verbose:
            skills = typical_skills(args.level)
            print("skills típicos:", skills, file=sys.stderr)
        return

    ap.print_help()

if __name__ == "__main__":
    main()
