-- Teste headless (luajit puro, sem TFS/servidor) da PONTE DE ENCODING (NarutoText, data/lib/
-- naruto_json.lua) que corrige a regressão crítica do playtest de história de 2026-09-05
-- (docs/qa/playtest-historia-arcos4-6.md, "Achado de jogo #2"): o Lua GERADO por
-- tools/export_tfs.py sai em cp1252 (_lua_cp1252), mas os nomes que vêm de dentro do TFS em tempo
-- de execução (creature:getName(), attacker:getName()) vêm do atributo `name=` do XML de monstro
-- (server/tfs/data/monster/naruto/*.xml), que CONTINUA em UTF-8 — sem converter antes de comparar,
-- matar um monstro com nome acentuado (ex. "Águia do Trovão") nunca contava para nenhuma missão/
-- tarefa/diária/conquista, e PHASES[creature:getName()] (boss_phases.lua) nunca achava a lista de
-- fases de um boss acentuado (ex. "O Sócio Eterno").
--
-- Roda contra os arquivos REAIS gerados por tools/export_tfs.py a partir de data/*.json (nenhuma
-- quest/tarefa/diária/conquista/monstro real foi alterada para este teste — todos os fixtures
-- abaixo usam ids/nomes que já existem em data/monsters/mountain.json, data/npcs/mountain.json,
-- data/tasks.json, data/dailies.json e data/achievements.json).
--
-- Quatro frentes (ver missão):
--  a) kill de "Águia do Trovão" (nome UTF-8, como um creature:getName() de verdade devolveria)
--     conta pra quest q_mountain_eagles, pra tarefa task_thunder_eagle_1 e pra diária
--     daily_kill_thunder_eagle_046b; kill de "O Sócio Eterno" desbloqueia a conquista
--     boss_boss_curse_partner (kill_specific) — mesmo monstro do achado crítico do playtest
--     (bloqueava a metade "Montanha" do Exame Anbu).
--  b) PHASES["O Sócio Eterno"] (boss_phases.lua) é encontrada quando creature:getName() devolve
--     UTF-8 (antes do fix, a chave gerada é cp1252 e a busca sempre vinha nil).
--  c) summon com acento (Oni Ancestral invoca "Águia do Trovão" a 70% HP, dado real de
--     data/monsters/mountain.json) chama Game.createMonster com o nome em UTF-8 válido — o stub
--     (tools/tests/tfs_stub.lua) grava a chamada pro teste inspecionar.
--  d) roundtrip utf8ToCp1252 -> cp1252ToUtf8 preserva frases com á ã ç é ó – — " ".
--
-- Rodar: luajit tools/tests/test_encoding_headless.lua (ou tools/tests/run_quests_tests.sh, que
-- já reexporta antes de rodar os testes headless).

local scriptDir = (arg and arg[0] or "tools/tests/test_encoding_headless.lua"):match("(.*/)") or "./"
local ROOT = scriptDir .. "../../"
local GEN = ROOT .. "server/generated/"

local stub = dofile(scriptDir .. "tfs_stub.lua")

-- ---------------------------------------------------------------- framework de teste mínimo
local results = {}
local function check(name, cond, detail)
	results[#results + 1] = {name = name, ok = cond and true or false, detail = detail}
end
local function eq(name, got, want)
	check(name, got == want, "esperado " .. tostring(want) .. ", veio " .. tostring(got))
end

local function fakeMonster(name)
	return {isMonster = function() return true end, getName = function() return name end}
end

--- Validação simples de UTF-8 (sem depender de NarutoText): true se `s` é uma sequência de bytes
--- UTF-8 bem formada (todo lead byte multibyte tem os bytes de continuação certos, sem sobra).
local function isValidUtf8(s)
	local i, n = 1, #s
	while i <= n do
		local b1 = s:byte(i)
		local len
		if b1 < 0x80 then len = 1
		elseif b1 >= 0xC2 and b1 <= 0xDF then len = 2
		elseif b1 >= 0xE0 and b1 <= 0xEF then len = 3
		elseif b1 >= 0xF0 and b1 <= 0xF4 then len = 4
		else return false end
		if i + len - 1 > n then return false end
		for k = 1, len - 1 do
			local bk = s:byte(i + k)
			if not bk or bk < 0x80 or bk > 0xBF then return false end
		end
		i = i + len
	end
	return true
end

-- ---------------------------------------------------------------- carrega as libs/scripts REAIS
-- geradas (ordem que importa só por causa dos comentários de load-order do lib.lua real; onKill/
-- onHealthChange leem as tabelas em TEMPO DE CHAMADA, não no load).
dofile(GEN .. "lib/naruto_json.lua")         -- NarutoText (o alvo deste teste)
dofile(GEN .. "lib/naruto_ranks.lua")
dofile(GEN .. "lib/naruto_rewards.lua")
dofile(GEN .. "lib/naruto_quests.lua")
dofile(GEN .. "lib/naruto_tasks.lua")
dofile(GEN .. "lib/naruto_dailies.lua")
dofile(GEN .. "lib/naruto_achievements.lua")
dofile(GEN .. "scripts/naruto/quests_kill.lua")
dofile(GEN .. "scripts/naruto/tasks.lua")
dofile(GEN .. "scripts/naruto/dailies.lua")
dofile(GEN .. "scripts/naruto/achievements.lua")
dofile(GEN .. "scripts/naruto/boss_phases.lua")

check("NarutoText carregou (utf8ToCp1252)", type(NarutoText) == 'table' and type(NarutoText.utf8ToCp1252) == 'function')
check("NarutoText carregou (cp1252ToUtf8)", type(NarutoText.cp1252ToUtf8) == 'function')

-- ================================================================== a) kill conta pra quest,
-- tarefa, diária e conquista (nome UTF-8 vindo do "creature:getName()" do stub)

do
	local p = stub.newPlayer("Encoding1", {level = 60})

	-- quest real: q_mountain_eagles (Mestra Yuki, Montanha) — data/npcs/mountain.json.
	local q = NarutoQuests.byId["q_mountain_eagles"]
	check("quest real q_mountain_eagles existe", q ~= nil)
	if q then
		p:setStorageValue(q.storage, 0)  -- simula "aceita, 0 de progresso" (pula o diálogo do NPC)
		stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("Águia do Trovão"))
		eq("quest q_mountain_eagles: kill de \"Águia do Trovão\" (UTF-8) incrementa o storage", p:getStorageValue(q.storage), 1)
	end

	-- tarefa real: task_thunder_eagle_1 (Mestre de Tarefas Kaji, Montanha) — data/tasks.json.
	local t
	for _, tt in ipairs(NarutoTasks.list) do
		if tt.id == "task_thunder_eagle_1" then t = tt break end
	end
	check("tarefa real task_thunder_eagle_1 existe", t ~= nil)
	if t then
		p:setStorageValue(t.progressStorage, 0)
		stub.creatureEvents["NarutoTaskKill"].onKill(p, fakeMonster("Águia do Trovão"))
		eq("tarefa task_thunder_eagle_1: kill de \"Águia do Trovão\" (UTF-8) incrementa o progresso", p:getStorageValue(t.progressStorage), 1)
	end

	-- diária real: daily_kill_thunder_eagle_046b (pool de data/dailies.json) — força ela pro
	-- slot 1 (em vez de depender do sorteio aleatório de NarutoDailies.rollIfNeeded).
	local dailyIdx
	for idx, entry in ipairs(NarutoDailies.pool) do
		if entry.id == "daily_kill_thunder_eagle_046b" then dailyIdx = idx break end
	end
	check("diária real daily_kill_thunder_eagle_046b existe no pool", dailyIdx ~= nil)
	if dailyIdx then
		local function today() local d = os.date('*t'); return d.year * 400 + d.yday end
		p:setStorageValue(NarutoDailies.DAY, today())  -- já "sorteado hoje": rollIfNeeded não mexe
		p:setStorageValue(NarutoDailies.SLOT_POOL[1], dailyIdx)
		p:setStorageValue(NarutoDailies.SLOT_PROGRESS[1], 0)
		stub.creatureEvents["NarutoDailyKill"].onKill(p, fakeMonster("Águia do Trovão"))
		eq("diária daily_kill_thunder_eagle_046b: kill de \"Águia do Trovão\" (UTF-8) incrementa o slot",
			p:getStorageValue(NarutoDailies.SLOT_PROGRESS[1]), 1)
	end

	-- conquista real: boss_boss_curse_partner (kill_specific, target=boss_curse_partner, "O Sócio
	-- Eterno") — um dos 3 bosses acentuados citados no achado crítico do playtest (bloqueava a
	-- metade "Montanha" do Exame Anbu).
	local a
	for _, aa in ipairs(NarutoAchievements.list) do
		if aa.id == "boss_boss_curse_partner" then a = aa break end
	end
	check("conquista real boss_boss_curse_partner existe", a ~= nil)
	if a then
		check("conquista boss_boss_curse_partner começa bloqueada", not NarutoAchievements.isUnlocked(p, a))
		stub.creatureEvents["NarutoAchievementKill"].onKill(p, fakeMonster("O Sócio Eterno"))
		check("conquista boss_boss_curse_partner: kill de \"O Sócio Eterno\" (UTF-8) desbloqueia", NarutoAchievements.isUnlocked(p, a))
	end
end

-- ================================================================== b) PHASES de boss acentuado
-- é encontrada quando getName() devolve UTF-8 (boss_curse_partner, "O Sócio Eterno", hp real 7000)

do
	local boss = stub.newMonster("O Sócio Eterno", {health = 7000, maxHealth = 7000, baseSpeed = 200})
	local attacker = stub.newPlayer("Encoding2")
	check("NarutoBossPhases.state vazio pro boss antes do primeiro hit", NarutoBossPhases.state[boss:getId()] == nil)
	-- dano suficiente pra cruzar a fase de 75% E a de 50% (pct = (7000-3850)*100/7000 = 45): se
	-- PHASES["O Sócio Eterno"] (chave cp1252 gerada) não fosse encontrada por causa do encoding,
	-- a função retornaria cedo (ver `if not list then return ... end`) e NUNCA criaria esta
	-- entrada em NarutoBossPhases.state — a checagem abaixo prova a busca bateu.
	stub.creatureEvents["NarutoBossPhases"].onHealthChange(boss, attacker, 3850, COMBAT_PHYSICALDAMAGE, 0, COMBAT_NONE, ORIGIN_MELEE)
	check("PHASES[\"O Sócio Eterno\"] (UTF-8 -> cp1252) foi encontrada: state criado", NarutoBossPhases.state[boss:getId()] ~= nil)
	check("fase de 50%: mult 1.3 (data/monsters/mountain.json) foi lida", NarutoBossPhases.state[boss:getId()] and NarutoBossPhases.state[boss:getId()].mult == 1.3)
	-- a MENSAGEM continua cp1252 (não é alvo deste fix — ver regra em docs/sistemas/cliente-ux.md):
	-- boss._said[1].msg vem direto do literal gerado, então comparamos convertendo o esperado.
	check("fase 75%: mensagem \"Mais um coração ainda bate.\" disparada (cp1252, como sempre foi)",
		#boss._said >= 1 and boss._said[1].msg == NarutoText.utf8ToCp1252("Mais um coração ainda bate."))
end

-- ================================================================== c) summon acentuado é criado
-- com nome UTF-8 (Oni Ancestral, hp real 20500, invoca 3x Águia do Trovão a 70% HP)

do
	local boss = stub.newMonster("Oni Ancestral", {health = 20500, maxHealth = 20500, baseSpeed = 200})
	local attacker = stub.newPlayer("Encoding3")
	local callsBefore = #stub.createMonsterCalls
	-- pct = (20500-6200)*100/20500 ≈ 69.76 <= 70 (fase de 70%), não cruza a de 40%.
	stub.creatureEvents["NarutoBossPhases"].onHealthChange(boss, attacker, 6200, COMBAT_PHYSICALDAMAGE, 0, COMBAT_NONE, ORIGIN_MELEE)
	local newCalls = #stub.createMonsterCalls - callsBefore
	eq("fase 70% de Oni Ancestral invoca 3 summons (data/monsters/mountain.json)", newCalls, 3)
	for i = callsBefore + 1, #stub.createMonsterCalls do
		local call = stub.createMonsterCalls[i]
		check("Game.createMonster #" .. i .. ": nome recebido é UTF-8 válido", isValidUtf8(call.name), call.name)
		eq("Game.createMonster #" .. i .. ": nome é \"Águia do Trovão\" em UTF-8 (não cp1252)", call.name, "Águia do Trovão")
	end
end

-- ================================================================== d) roundtrip utf8 -> cp1252
-- -> utf8 preserva á ã ç é ó – — " "

do
	local phrases = {
		"Águia do Trovão", "Xamã da Maldição", "Marionetista das Ruínas",
		"café com ração", "maçã amarela", "não é assim",
		"pausa – depois continua", "tudo — ou nada", "ela disse “oi” e sumiu",
	}
	for _, phrase in ipairs(phrases) do
		local cp1252 = NarutoText.utf8ToCp1252(phrase)
		local backToUtf8 = NarutoText.cp1252ToUtf8(cp1252)
		eq("roundtrip utf8->cp1252->utf8: \"" .. phrase .. "\"", backToUtf8, phrase)
		check("\"" .. phrase .. "\": forma cp1252 não é mais UTF-8 (bytes diferentes quando há acento)",
			cp1252 == phrase or not isValidUtf8(cp1252))
	end

	-- caractere isolado por code point (útil pra depurar qual falhou, se falhar):
	eq("á isolado", NarutoText.cp1252ToUtf8(NarutoText.utf8ToCp1252("á")), "á")
	eq("ã isolado", NarutoText.cp1252ToUtf8(NarutoText.utf8ToCp1252("ã")), "ã")
	eq("ç isolado", NarutoText.cp1252ToUtf8(NarutoText.utf8ToCp1252("ç")), "ç")
	eq("é isolado", NarutoText.cp1252ToUtf8(NarutoText.utf8ToCp1252("é")), "é")
	eq("ó isolado", NarutoText.cp1252ToUtf8(NarutoText.utf8ToCp1252("ó")), "ó")
	eq("– (en dash) isolado", NarutoText.cp1252ToUtf8(NarutoText.utf8ToCp1252("–")), "–")
	eq("— (em dash) isolado", NarutoText.cp1252ToUtf8(NarutoText.utf8ToCp1252("—")), "—")
	eq("“ (aspa curva esquerda) isolada", NarutoText.cp1252ToUtf8(NarutoText.utf8ToCp1252("“")), "“")
	eq("” (aspa curva direita) isolada", NarutoText.cp1252ToUtf8(NarutoText.utf8ToCp1252("”")), "”")

	-- bytes já cp1252 (ex.: um literal deste próprio Lua gerado) passam direto por utf8ToCp1252 —
	-- idempotência que os sites de fix (quests_kill.lua etc.) dependem implicitamente.
	local alreadyCp1252 = "\xC1guia do Trov\xE3o"  -- 'Águia do Trovão' já em cp1252 (bytes crus)
	eq("string já cp1252 passa direto por utf8ToCp1252 (idempotente)",
		NarutoText.utf8ToCp1252(alreadyCp1252), alreadyCp1252)

	-- ASCII puro é idempotente nos dois sentidos (nenhuma quest/tarefa sem acento pode quebrar).
	eq("ASCII puro: utf8ToCp1252 não mexe", NarutoText.utf8ToCp1252("Sentinela de Pedra"), "Sentinela de Pedra")
	eq("ASCII puro: cp1252ToUtf8 não mexe", NarutoText.cp1252ToUtf8("Sentinela de Pedra"), "Sentinela de Pedra")
end

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
