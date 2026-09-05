-- Teste headless (luajit puro, sem TFS/servidor) da fase de "fúria" de boss multiplicando dano
-- de verdade (docs/sistemas/monstros-e-pvm.md §Bosses, docs/sistemas/balanceamento-relatorio-v6.md
-- meta 4). Roda contra o Lua REAL gerado por tools/export_tfs.py
-- (server/generated/scripts/naruto/boss_phases.lua), sem editar nenhum data/monsters/*.json: um
-- boss FICTÍCIO ('TestBossFury', fases {100%: mult 1.0, 50%: mult 1.5}) é injetado por
-- string.gsub direto no texto da tabela `PHASES` (que é `local` no arquivo gerado — não dá pra
-- injetar depois de executá-lo) antes de dar load() nele. Isso testa as funções de verdade
-- (CreatureEvent NarutoBossPhases/NarutoBossFury/NarutoBossReset) e não uma reimplementação.
--
-- Rodar: luajit tools/tests/test_boss_fury_headless.lua  (ou tools/tests/run_boss_fury_tests.sh)

local scriptDir = (arg and arg[0] or "tools/tests/test_boss_fury_headless.lua"):match("(.*/)") or "./"
local ROOT = scriptDir .. "../../"
local GEN = ROOT .. "server/generated/"

local stub = dofile(scriptDir .. "tfs_stub.lua")

-- NarutoText (utf8ToCp1252/cp1252ToUtf8): boss_phases.lua usa pra casar PHASES[creature:getName()]
-- (getName() vem em UTF-8, as chaves de PHASES saem cp1252 -- ver tools/export_tfs.py).
dofile(GEN .. "lib/naruto_json.lua")

-- ---------------------------------------------------------------- framework de teste mínimo
local results = {}
local function check(name, cond, detail)
	results[#results + 1] = {name = name, ok = cond and true or false, detail = detail}
end
local function eq(name, got, want)
	check(name, got == want, "esperado " .. tostring(want) .. ", veio " .. tostring(got))
end

-- ---------------------------------------------------------------- carrega boss_phases.lua REAL,
-- com um boss fictício injetado na tabela PHASES (local, só dá pra injetar via texto).
local path = GEN .. "scripts/naruto/boss_phases.lua"
local f = assert(io.open(path, "rb"))
local src = f:read("*a")
f:close()

local FIXTURE_BOSS = "TestBossFury"
local FIXTURE_INJECT = "local PHASES = {\n\t['" .. FIXTURE_BOSS .. "'] = {\n" ..
	"\t\t{hp = 100, mult = 1.0, message = '', summons = {}},\n" ..
	"\t\t{hp = 50, mult = 1.5, message = '', summons = {}},\n" ..
	"\t},"
local newSrc, nSubs = src:gsub("local PHASES = {", FIXTURE_INJECT, 1)
assert(nSubs == 1, "não achou 'local PHASES = {' no arquivo gerado (mudou o template?)")

local chunk = assert(load(newSrc, "=boss_phases_test"))
chunk()

local phasesEv = assert(stub.creatureEvents["NarutoBossPhases"], "CreatureEvent NarutoBossPhases não registrado")
local furyEv = assert(stub.creatureEvents["NarutoBossFury"], "CreatureEvent NarutoBossFury não registrado")
local resetEv = assert(stub.creatureEvents["NarutoBossReset"], "CreatureEvent NarutoBossReset não registrado")
assert(phasesEv.onHealthChange, "NarutoBossPhases.onHealthChange ausente")
assert(furyEv.onHealthChange, "NarutoBossFury.onHealthChange ausente")
assert(resetEv.onDeath, "NarutoBossReset.onDeath ausente")

-- ---------------------------------------------------------------- cenário
local boss = stub.newMonster(FIXTURE_BOSS, {health = 1000, maxHealth = 1000, baseSpeed = 200})
local player = stub.newPlayer("Jogador")
local otherMonster = stub.newMonster("Lobo Comum", {health = 100, maxHealth = 100})

-- 1) primeiro hit no boss: pct = (1000-100)*100/1000 = 90 <= 100 -> dispara fase 1 (mult 1.0)
local p1, t1, s1, st1 = phasesEv.onHealthChange(boss, player, 100, COMBAT_PHYSICALDAMAGE, 0, COMBAT_NONE, ORIGIN_MELEE)
boss._health = boss._health - 100
eq("fase 1: onHealthChange devolve o dano inalterado (o dano do BOSS não muda aqui)", p1, 100)
eq("fase 1: NarutoBossPhases.state guarda mult 1.0", NarutoBossPhases.state[boss:getId()].mult, 1.0)

-- 2) jogador apanha do boss ANTES de cruzar 50%: fase atual tem mult 1.0 -> dano não muda
local dmgBefore, _, secBefore = furyEv.onHealthChange(player, boss, 40, COMBAT_PHYSICALDAMAGE, 10, COMBAT_PHYSICALDAMAGE, ORIGIN_MELEE)
eq("fase 1 (mult 1.0): dano melee do boss no jogador não muda", dmgBefore, 40)
eq("fase 1 (mult 1.0): dano secundário do boss no jogador não muda", secBefore, 10)

-- 3) dano que cruza 50% (1000 -> 900 -> 450, pct = 45 <= 50): dispara fase 2 (mult 1.5)
local prevSpeedChanges = #boss._speedChanges
phasesEv.onHealthChange(boss, player, 450, COMBAT_PHYSICALDAMAGE, 0, COMBAT_NONE, ORIGIN_MELEE)
boss._health = boss._health - 450
eq("fase 2 (50%): NarutoBossPhases.state passa a guardar mult 1.5", NarutoBossPhases.state[boss:getId()].mult, 1.5)
-- saúde no momento da chamada era 900 (ainda não tinha sofrido os 450 de dano deste hit);
-- heal = floor(1000*0.5*0.10) = 50 é somado por addHealth() ANTES do dano ser aplicado
-- (mesma ordem do TFS real: o evento roda antes do drainHealth) -> 900 + 50 - 450 = 500.
eq("fase 2: cura pontual de compensação ainda acontece (900 + 50 heal - 450 dano = 500)",
	boss:getHealth(), 500)
check("fase 2: velocidade do boss aumenta (changeSpeed chamado)", #boss._speedChanges > prevSpeedChanges)

-- 4) jogador apanha do boss DEPOIS de cruzar 50% (fase de fúria): dano melee E de "spell"
--    (ambos chegam por onHealthChange com attacker = o boss) devem vir ×1.5, arredondado.
local dmgAfter, typeAfter, secAfter, secTypeAfter = furyEv.onHealthChange(
	player, boss, 50, COMBAT_PHYSICALDAMAGE, 20, COMBAT_PHYSICALDAMAGE, ORIGIN_MELEE)
eq("fase 2 (mult 1.5): dano primário ×1.5 arredondado (50 -> 75)", dmgAfter, 75)
eq("fase 2 (mult 1.5): dano secundário ×1.5 arredondado (20 -> 30)", secAfter, 30)
eq("fase 2 (mult 1.5): primaryType passa intacto", typeAfter, COMBAT_PHYSICALDAMAGE)
eq("fase 2 (mult 1.5): secondaryType passa intacto", secTypeAfter, COMBAT_PHYSICALDAMAGE)

-- arredondamento (floor(x*mult+0.5)): 21*1.5=31.5 -> 32 (não 31, que seria floor puro)
local dmgRound = furyEv.onHealthChange(player, boss, 21, COMBAT_PHYSICALDAMAGE, 0, COMBAT_NONE, ORIGIN_MELEE)
eq("arredondamento: floor(x*mult+0.5), não floor puro (21×1.5=31.5 -> 32)", dmgRound, 32)

-- 5) summons NÃO herdam o mult: um summon (monstro comum, nunca passou por onHealthChange como
--    boss) batendo no jogador não deve ter NENHUMA entrada em NarutoBossPhases.state.
local summon = stub.newMonster("Serpente Menor", {health = 200, maxHealth = 200})
local dmgSummon = furyEv.onHealthChange(player, summon, 30, COMBAT_PHYSICALDAMAGE, 0, COMBAT_NONE, ORIGIN_MELEE)
eq("summon invocado na fase: dano não é multiplicado (sem entrada em state)", dmgSummon, 30)

-- 6) outro monstro (não-boss, nome fora da tabela PHASES) tomando dano: onHealthChange do
--    NarutoBossPhases (lado monstro) devolve o dano intacto e não cria estado nenhum pra ele.
local otherDmg = phasesEv.onHealthChange(otherMonster, player, 30, COMBAT_PHYSICALDAMAGE, 0, COMBAT_NONE, ORIGIN_MELEE)
eq("monstro comum: onHealthChange (lado monstro) devolve dano intacto", otherDmg, 30)
check("monstro comum: nenhuma entrada criada em NarutoBossPhases.state", NarutoBossPhases.state[otherMonster:getId()] == nil)

-- 7) o próprio 'other monster' batendo no jogador nunca deveria ser multiplicado (não é boss)
local dmgOther = furyEv.onHealthChange(player, otherMonster, 30, COMBAT_PHYSICALDAMAGE, 0, COMBAT_NONE, ORIGIN_MELEE)
eq("outro monstro batendo no jogador: dano não é afetado pela fúria do boss", dmgOther, 30)

-- 8) limpeza no onDeath: depois que o boss morre, o estado tem que sumir (não pode vazar mult
--    pra quem quer que reuse esse cid depois).
resetEv.onDeath(boss)
check("onDeath: NarutoBossPhases.state[id] limpo", NarutoBossPhases.state[boss:getId()] == nil)
local dmgAfterDeath = furyEv.onHealthChange(player, boss, 50, COMBAT_PHYSICALDAMAGE, 0, COMBAT_NONE, ORIGIN_MELEE)
eq("depois do onDeath: mesmo cid do boss morto não multiplica mais dano", dmgAfterDeath, 50)

-- 9) proteção contra cid reciclado: se por algum motivo sobrasse state[id] com o mult antigo, mas
--    o cid foi reaproveitado por OUTRO monstro (nome diferente), o nome tem que ser revalidado.
NarutoBossPhases.state[boss:getId()] = {name = FIXTURE_BOSS, mult = 1.5}
local recycled = stub.newMonster("Bandido Qualquer", {id = boss:getId(), health = 50, maxHealth = 50})
local dmgRecycled = furyEv.onHealthChange(player, recycled, 40, COMBAT_PHYSICALDAMAGE, 0, COMBAT_NONE, ORIGIN_MELEE)
eq("cid reciclado por outro monstro: nome não bate -> dano não multiplica", dmgRecycled, 40)

-- ---------------------------------------------------------------- relatório final
local passed, failed = 0, 0
for _, r in ipairs(results) do
	if r.ok then passed = passed + 1
	else
		failed = failed + 1
		print("FALHOU: " .. r.name .. (r.detail and (" -- " .. tostring(r.detail)) or ""))
	end
end
print(string.format("\n%d/%d testes passaram (%d falharam)", passed, passed + failed, failed))
os.exit(failed == 0 and 0 or 1)
