-- Testes headless (luajit puro, sem TFS/servidor) da extensão de tipos de missão
-- (docs/sistemas/missoes.md). Roda contra os arquivos REAIS gerados por tools/export_tfs.py em
-- server/generated/ (lib/naruto_quests.lua, lib/naruto_ranks.lua, scripts/naruto/quests_kill.lua,
-- npc/scripts/naruto/merchant_leaf.lua) usando um stub das APIs do TFS (tfs_stub.lua) — mesmo
-- padrão descrito na missão de Conquistas (git log --grep=Conquistas), que testou headless mas
-- não deixou o arquivo de teste no repo; este fica.
--
-- Duas frentes:
--  1) REGRESSÃO: usa NarutoQuests.list/byNpc REAIS (carregados do JSON de verdade) para provar
--     que quests kind=kill/collect_item/keyword_quiz continuam produzindo as MESMAS mensagens/
--     efeitos de antes (nenhuma quest do jogo foi alterada por esta extensão).
--  2) NOVOS TIPOS: injeta quests FIXTURE (não vêm de data/npcs/*.json — a missão pediu para não
--     alterar dados de missões reais) diretamente em NarutoQuests.list/byNpc/byStorage/byId, no
--     MESMO formato que tools/export_tfs.py geraria, e exercita a lib/scripts REAIS contra elas:
--     collect_item+drops_from, talk_to, reach, kill+any_of+boss, requires (level/rank/quests),
--     locked_text, reward.storage/outfit/addon, progress_text/done_text (placeholders) e
--     NarutoQuests.progressText (cliente, aba Missões).
--
-- Rodar: luajit tools/tests/test_quests_headless.lua  (ou tools/tests/run_quests_tests.sh)

local scriptDir = (arg and arg[0] or "tools/tests/test_quests_headless.lua"):match("(.*/)") or "./"
local ROOT = scriptDir .. "../../"
local GEN = ROOT .. "server/generated/"

local stub = dofile(scriptDir .. "tfs_stub.lua")

-- ---------------------------------------------------------------- framework de teste mínimo
local results = {}
local function check(name, cond, detail)
	results[#results + 1] = {name = name, ok = cond and true or false, detail = detail}
end
-- O Lua gerado sai com acentos em cp1252 (tools/export_tfs.py::_lua_cp1252); os textos esperados
-- neste arquivo estao em UTF-8, entao convertemos o esperado antes de comparar.
local function utf8ToCp1252(str)
  if type(str) ~= 'string' then return str end
  local out, i, n = {}, 1, #str
  while i <= n do
    local b = str:byte(i)
    local cp, len
    local function cont(k) local c = str:byte(k); return c and c >= 0x80 and c <= 0xBF end
    if b < 0x80 then cp, len = b, 1
    elseif b >= 0xC2 and b <= 0xDF and cont(i + 1) then cp, len = (b - 0xC0) * 0x40 + (str:byte(i + 1) - 0x80), 2
    elseif b >= 0xE0 and b <= 0xEF and cont(i + 1) and cont(i + 2) then cp, len = (b - 0xE0) * 0x1000 + (str:byte(i + 1) - 0x80) * 0x40 + (str:byte(i + 2) - 0x80), 3
    else cp, len = b, 1 end -- byte solto (ja cp1252): passa direto
    local map = {[0x2013]=0x96,[0x2014]=0x97,[0x2018]=0x91,[0x2019]=0x92,[0x201C]=0x93,[0x201D]=0x94,[0x2026]=0x85}
    if cp < 0 then cp, len = b, 1 end
    if cp < 0x100 then out[#out+1] = string.char(cp)
    elseif map[cp] then out[#out+1] = string.char(map[cp])
    else out[#out+1] = '?' end
    i = i + len
  end
  return table.concat(out)
end

local function eq(name, got, want)
  -- fixtures definidas neste arquivo ficam em UTF-8; o Lua gerado, em cp1252: normalizamos os dois lados
  want = utf8ToCp1252(want); got = utf8ToCp1252(got)
	check(name, got == want, "esperado " .. tostring(want) .. ", veio " .. tostring(got))
end

local function fakeMonster(name)
	return {isMonster = function() return true end, getName = function() return name end}
end

-- ---------------------------------------------------------------- carrega as libs REAIS geradas
dofile(GEN .. "lib/naruto_json.lua")      -- NarutoText (utf8ToCp1252/cp1252ToUtf8) -- quests_kill.lua usa
dofile(GEN .. "lib/naruto_ranks.lua")     -- NarutoRanks (requires.rank precisa disso)
dofile(GEN .. "lib/naruto_quests.lua")    -- NarutoQuests com os dados REAIS de data/npcs/*.json
-- Carrega ANTES de qualquer teste (regressão ou fixture) que chame onKill/o poll de reach:
-- killEvent.onKill e o GlobalEvent de reach leem NarutoQuests.list em TEMPO DE CHAMADA (não no
-- load), então a ordem de dofile em relação às fixtures não importa — só precisa vir antes do
-- primeiro onKill/onThink chamado abaixo.
dofile(GEN .. "scripts/naruto/quests_kill.lua")  -- registra killEvent/login/reachPoll

local realQuestCount = #NarutoQuests.list
check("naruto_quests.lua carregou com quests reais", realQuestCount > 0, "count=" .. realQuestCount)

-- ================================================================== 1) REGRESSÃO (dados reais)

do
	-- kind='kill' real: q_wolves_1 (quest_giver_leaf) — ver data/npcs/leaf.json.
	local q = NarutoQuests.byId["q_wolves_1"]
	check("quest real q_wolves_1 existe", q ~= nil)
	if q then
		local p = stub.newPlayer("Regress1")
		local msg1, done1 = NarutoQuests.talk(p, NarutoQuests.byNpc[q.npc])
		eq("kill real: aceitar produz texto padrão", msg1, q.text .. " (Missão aceita: " .. q.name .. ")")
		eq("kill real: aceitar não completa", done1, false)
		eq("kill real: storage vira 0 ao aceitar", p:getStorageValue(q.storage), 0)

		-- mata o monstro certo (q.count - 1) vezes: ainda em progresso
		local monster = fakeMonster(q.monster)
		for i = 1, q.count - 1 do
			stub.creatureEvents["NarutoQuestKill"].onKill(p, monster)
		end
		eq("kill real: progresso incrementa por onKill", p:getStorageValue(q.storage), q.count - 1)
		local msg2 = NarutoQuests.talk(p, NarutoQuests.byNpc[q.npc])
		eq("kill real: mensagem de progresso padrão (byte-igual à de antes desta extensão)",
			msg2, "Ainda não terminou? " .. q.name .. ": " .. (q.count - 1) .. "/" .. q.count .. " " .. q.monster .. ".")

		-- último abate completa a etapa; falar de novo entrega
		stub.creatureEvents["NarutoQuestKill"].onKill(p, monster)
		local xpBefore = p._exp
		local msg3, done3 = NarutoQuests.talk(p, NarutoQuests.byNpc[q.npc])
		eq("kill real: completa na entrega", done3, true)
		eq("kill real: mensagem de conclusão padrão (byte-igual)", msg3, "Bom trabalho, ninja. Missão '" .. q.name .. "' concluída.")
		eq("kill real: storage vira DONE", p:getStorageValue(q.storage), NarutoQuests.DONE)
		check("kill real: xp da recompensa foi creditado", p._exp > xpBefore or q.reward.xp == 0)
	end
end

do
	-- kind='collect_item' real: q_forest_supplies (5x wolf_pelt) — data/npcs/leaf.json.
	local q = NarutoQuests.byId["q_forest_supplies"]
	check("quest real q_forest_supplies existe", q ~= nil)
	if q then
		local p = stub.newPlayer("Regress2")
		-- a cadeia é sequencial por NPC (NarutoQuests.talk sempre pega a PRIMEIRA quest não-
		-- DONE da lista do npc) -- fast-forward das etapas anteriores pra chegar em
		-- q_forest_supplies, mesmo truque de /storage usado nos playtests reais (ver
		-- docs/sistemas/progressao-servidor.md).
		for _, qq in ipairs(NarutoQuests.byNpc[q.npc]) do
			if qq.id == q.id then break end
			p:setStorageValue(qq.storage, NarutoQuests.DONE)
		end
		NarutoQuests.talk(p, NarutoQuests.byNpc[q.npc]) -- aceita
		local it = q.collectItems[1]
		local msgMissing = NarutoQuests.talk(p, NarutoQuests.byNpc[q.npc])
		eq("collect_item real: mensagem 'falta trazer' byte-igual",
			msgMissing, "Ainda falta trazer: " .. it.count .. "x " .. it.name .. ".")
		p:addItem(it.id, it.count)
		local msgDone, done = NarutoQuests.talk(p, NarutoQuests.byNpc[q.npc])
		eq("collect_item real: completa quando tem os itens", done, true)
		eq("collect_item real: itens são removidos ao entregar", p:getItemCount(it.id), 0)
	end
end

do
	-- kind='keyword_quiz' real: exam_chunin_1_teoria — aceitar dá a fala com {prova}.
	local q = NarutoQuests.byId["exam_chunin_1_teoria"]
	check("quest real exam_chunin_1_teoria existe", q ~= nil)
	if q then
		local p = stub.newPlayer("Regress3")
		local msg = NarutoQuests.talk(p, NarutoQuests.byNpc[q.npc])
		local expected = q.text .. " (Missão aceita: " .. q.name .. "). Diga {prova} quando estiver pronto para responder."
		eq("keyword_quiz real: aceitar byte-igual (com {prova})", msg, expected)
		-- simula acertos suficientes (o fluxo de perguntas em si é do npc gerado, fora do escopo
		-- desta lib) e confirma que a conclusão passa pelo mesmo completeQuest.
		p:setStorageValue(q.storage, q.count)
		local msgDone, done = NarutoQuests.talk(p, NarutoQuests.byNpc[q.npc])
		eq("keyword_quiz real: completa quando storage>=quizMin", done, true)
	end
end

-- ================================================================== 2) NOVOS TIPOS (fixtures)
-- Formato IDÊNTICO ao que tools/export_tfs.py gera (mesmos nomes de campo) — ver seção
-- "lib + quests" de tools/export_tfs.py e docs/sistemas/missoes.md.

local FIXTURE_BASE = 900000
local function addFixture(q)
	NarutoQuests.list[#NarutoQuests.list + 1] = q
	NarutoQuests.byStorage[q.storage] = q
	NarutoQuests.byId[q.id] = q
	NarutoQuests.byNpc[q.npc] = NarutoQuests.byNpc[q.npc] or {}
	table.insert(NarutoQuests.byNpc[q.npc], q)
	return q
end

-- B1: kill + any_of + boss
local qBoss = addFixture({
	id = "fx_boss_hunt", npc = "fixture_npc", npcName = "Fixture NPC",
	name = "Caçada ao Chefe", text = "Mate o chefe ou seus tenentes.",
	kind = "kill", monster = "tenente a ou tenente b", count = 2, storage = FIXTURE_BASE + 1,
	reward = {xp = 100, ryo = 10, items = {}},
	anyOf = {"tenente a", "tenente b"}, boss = true,
})

do
	local p = stub.newPlayer("Fixture1")
	local msg1 = NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc"])
	eq("kill any_of: aceita normalmente", msg1, qBoss.text .. " (Missão aceita: " .. qBoss.name .. ")")
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("tenente a"))
	eq("kill any_of: 'tenente a' conta pro contador", p:getStorageValue(qBoss.storage), 1)
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("tenente b"))
	eq("kill any_of: 'tenente b' (outro id da lista) também conta", p:getStorageValue(qBoss.storage), 2)
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("um monstro qualquer"))
	eq("kill any_of: monstro fora da lista não conta além do count", p:getStorageValue(qBoss.storage), 2)
	local _, done = NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc"])
	eq("kill any_of: completa ao atingir count via qualquer combinação", done, true)
	eq("boss: NarutoQuests.progressText marca '(chefe)' numa quest kill em progresso", (function()
		local p2 = stub.newPlayer("FixtureBossProg")
		NarutoQuests.talk(p2, NarutoQuests.byNpc["fixture_npc"])
		stub.creatureEvents["NarutoQuestKill"].onKill(p2, fakeMonster("tenente a"))
		return NarutoQuests.progressText(p2, qBoss)
	end)(), "1/2 (chefe)")
end

-- B2: collect_item + drops_from (chance=1.0 determinística)
local qDrop = addFixture({
	id = "fx_collect_drop", npc = "fixture_npc2", npcName = "Fixture NPC 2",
	name = "Escamas Raras", text = "Traga 2 escamas raras.",
	kind = "collect_item", monster = "", count = 0, storage = FIXTURE_BASE + 2,
	reward = {xp = 50, ryo = 5, items = {}},
	collectItems = {{id = 77001, count = 2, name = "Escama Rara", itemKey = "rare_scale"}},
	dropsFrom = {{itemKey = "rare_scale", monster = "dragao_fixture", chance = 1.0}},
})

do
	local p = stub.newPlayer("Fixture2")
	NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc2"]) -- aceita
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("dragao_fixture"))
	eq("collect_item+drops_from: dropa 1 escama (chance=1.0)", p:getItemCount(77001), 1)
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("dragao_fixture"))
	eq("collect_item+drops_from: dropa a 2a escama", p:getItemCount(77001), 2)
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("dragao_fixture"))
	eq("collect_item+drops_from: NÃO empilha além do necessário", p:getItemCount(77001), 2)
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("outro_monstro"))
	eq("collect_item+drops_from: monstro errado não dropa", p:getItemCount(77001), 2)
	local _, done = NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc2"])
	eq("collect_item+drops_from: completa e remove os itens", done, true)
	eq("collect_item+drops_from: itens removidos na entrega", p:getItemCount(77001), 0)
end

-- B3: talk_to (alvo = merchant_leaf, um NPC 'shop' de verdade) — precisa existir ANTES do dofile
-- do script do npc alvo (o bloco TALK_TO_QUESTS injetado por npc_files() roda no LOAD do script).
local qTalk = addFixture({
	id = "fx_talk_to_merchant", npc = "fixture_npc3", npcName = "Fixture NPC 3",
	name = "Recado para o Mercador", text = "Vá falar com o mercador da vila.",
	kind = "talk_to", monster = "", count = 1, storage = FIXTURE_BASE + 3,
	reward = {xp = 20, ryo = 0, items = {}},
	targetNpc = "merchant_leaf", targetNpcName = "Ichiro, o Mercador", keyword = "missao",
})

dofile(GEN .. "npc/scripts/naruto/merchant_leaf.lua")  -- TALK_TO_QUESTS vê fx_talk_to_merchant

do
	local p = stub.newPlayer("Fixture3")
	local msgAccept = NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc3"])
	eq("talk_to: aceita no NPC de origem", msgAccept, qTalk.text .. " (Missão aceita: " .. qTalk.name .. ")")
	eq("talk_to: storage=0 (aceita, não concluída)", p:getStorageValue(qTalk.storage), 0)
	local progressMsg = NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc3"])
	eq("talk_to: mensagem de progresso manda falar com o alvo", progressMsg, "Vá falar com Ichiro, o Mercador.")

	local consumed = stub.sayKeyword(stub.lastKeywordHandler, "missao", p:getId())
	eq("talk_to: dizer 'missao' pro NPC alvo é consumido (completa)", consumed, true)
	eq("talk_to: storage vira DONE ao falar com o alvo", p:getStorageValue(qTalk.storage), NarutoQuests.DONE)
	eq("talk_to: mensagem de conclusão foi dita pelo npc alvo",
		stub.lastNpcHandler.lastSaid[p:getId()], "Bom trabalho, ninja. Missão '" .. qTalk.name .. "' concluída.")

	-- jogador SEM essa quest ativa: falar 'missao' com o mercador não deve fazer nada (cai pro
	-- handler seguinte, que nesse NPC shop não existe -> retorna false, sem erro).
	local p2 = stub.newPlayer("FixtureNoQuest")
	local consumed2 = stub.sayKeyword(stub.lastKeywordHandler, "missao", p2:getId())
	eq("talk_to: jogador sem a quest ativa não aciona nada", consumed2, false)
end

-- B4: reach (poll de 7s, GlobalEvent NarutoQuestReachPoll)
local qReach = addFixture({
	id = "fx_reach_spot", npc = "fixture_npc4", npcName = "Fixture NPC 4",
	name = "O Mirante", text = "Vá até o mirante na montanha.",
	kind = "reach", monster = "", count = 1, storage = FIXTURE_BASE + 4,
	reward = {xp = 30, ryo = 0, items = {}},
	pos = {x = 500, y = 500, z = 7}, radius = 3,
})

do
	check("reach: GlobalEvent NarutoQuestReachPoll foi registrado", stub.globalEvents["NarutoQuestReachPoll"] ~= nil)
	eq("reach: intervalo configurado em 7000ms", stub.globalEvents["NarutoQuestReachPoll"].interval_ms, 7000)

	local pFar = stub.newPlayer("FixtureReachFar", {pos = {x = 0, y = 0, z = 7}})
	NarutoQuests.talk(pFar, NarutoQuests.byNpc["fixture_npc4"]) -- aceita, storage=0
	stub.globalEvents["NarutoQuestReachPoll"].onThink(7000, 0)
	eq("reach: longe do alvo não completa a etapa", pFar:getStorageValue(qReach.storage), 0)

	local pNear = stub.newPlayer("FixtureReachNear", {pos = {x = 502, y = 498, z = 7}})
	NarutoQuests.talk(pNear, NarutoQuests.byNpc["fixture_npc4"]) -- aceita, storage=0
	stub.globalEvents["NarutoQuestReachPoll"].onThink(7000, 0)
	eq("reach: dentro do raio quadrado marca pronto (storage=count)", pNear:getStorageValue(qReach.storage), qReach.count)
	local _, done = NarutoQuests.talk(pNear, NarutoQuests.byNpc["fixture_npc4"])
	eq("reach: falar com o NPC de origem entrega a recompensa", done, true)

	local pWrongZ = stub.newPlayer("FixtureReachWrongZ", {pos = {x = 500, y = 500, z = 8}})
	NarutoQuests.talk(pWrongZ, NarutoQuests.byNpc["fixture_npc4"])
	stub.globalEvents["NarutoQuestReachPoll"].onThink(7000, 0)
	eq("reach: z diferente não completa mesmo com x/y iguais", pWrongZ:getStorageValue(qReach.storage), 0)
end

-- B5: requires (level, rank, quests) + locked_text
local qPrereq = addFixture({
	id = "fx_prereq_done", npc = "fixture_npc5", npcName = "Fixture NPC 5",
	name = "Pré-requisito", text = "Etapa simples.", kind = "kill", monster = "coelho_fixture",
	count = 1, storage = FIXTURE_BASE + 5, reward = {xp = 1, ryo = 0, items = {}},
})
local qLevel = addFixture({
	id = "fx_requires_level", npc = "fixture_npc6", npcName = "Fixture NPC 6",
	name = "Missão de Elite", text = "Só para os fortes.", kind = "kill", monster = "coelho_fixture",
	count = 1, storage = FIXTURE_BASE + 6, reward = {xp = 1, ryo = 0, items = {}},
	requires = {level = 50},
})
local qCross = addFixture({
	id = "fx_requires_cross_npc", npc = "fixture_npc7", npcName = "Fixture NPC 7",
	name = "Depende de Outro NPC", text = "Só depois do pré-requisito.", kind = "kill",
	monster = "coelho_fixture", count = 1, storage = FIXTURE_BASE + 7,
	reward = {xp = 1, ryo = 0, items = {}}, requires = {quests = {"fx_prereq_done"}},
})
local qLocked = addFixture({
	id = "fx_requires_locked_text", npc = "fixture_npc8", npcName = "Fixture NPC 8",
	name = "Com Fala Própria", text = "...", kind = "kill", monster = "coelho_fixture", count = 1,
	storage = FIXTURE_BASE + 8, reward = {xp = 1, ryo = 0, items = {}},
	requires = {level = 999}, lockedText = "Volte mais forte, {player}.",
})

do
	local p = stub.newPlayer("FixtureLevel1", {level = 1})
	local msg, done = NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc6"])
	eq("requires.level: bloqueia jogador abaixo do nível", done, false)
	eq("requires.level: NÃO aceita a quest (storage continua -1)", p:getStorageValue(qLevel.storage), -1)
	check("requires.level: usa a fala padrão (menciona 'Volte quando estiver pronto')",
		msg:find("Volte quando estiver pronto", 1, true) ~= nil, msg)

	local p2 = stub.newPlayer("FixtureLevel50", {level = 50})
	local msg2, done2 = NarutoQuests.talk(p2, NarutoQuests.byNpc["fixture_npc6"])
	eq("requires.level: libera no nível exigido", msg2, qLevel.text .. " (Missão aceita: " .. qLevel.name .. ")")
	eq("requires.level: aceita normalmente (storage=0)", p2:getStorageValue(qLevel.storage), 0)

	-- requires.quests cruzando NPCs
	local p3 = stub.newPlayer("FixtureCrossNotDone")
	local _, done3 = NarutoQuests.talk(p3, NarutoQuests.byNpc["fixture_npc7"])
	eq("requires.quests: bloqueia enquanto o pré-requisito (outro NPC) não está DONE", done3, false)
	eq("requires.quests: não aceita (storage -1)", p3:getStorageValue(qCross.storage), -1)
	-- conclui o pré-requisito (fx_prereq_done, fixture_npc5) e tenta de novo
	NarutoQuests.talk(p3, NarutoQuests.byNpc["fixture_npc5"])
	stub.creatureEvents["NarutoQuestKill"].onKill(p3, fakeMonster("coelho_fixture"))
	NarutoQuests.talk(p3, NarutoQuests.byNpc["fixture_npc5"]) -- completa fx_prereq_done
	eq("requires.quests: pré-requisito ficou DONE", p3:getStorageValue(qPrereq.storage), NarutoQuests.DONE)
	local msg4 = NarutoQuests.talk(p3, NarutoQuests.byNpc["fixture_npc7"])
	eq("requires.quests: libera depois do pré-requisito DONE", msg4, qCross.text .. " (Missão aceita: " .. qCross.name .. ")")

	-- locked_text customizado com placeholder {player}
	local p4 = stub.newPlayer("FixtureLockedText", {level = 1})
	local msg5 = NarutoQuests.talk(p4, NarutoQuests.byNpc["fixture_npc8"])
	eq("locked_text: usa o texto customizado com {player} substituído", msg5, "Volte mais forte, FixtureLockedText.")
end

-- B6: reward.storage / outfit / addon
local qRewardExtra = addFixture({
	id = "fx_reward_extra", npc = "fixture_npc9", npcName = "Fixture NPC 9",
	name = "Traje Especial", text = "Uma tarefa simples.", kind = "kill", monster = "coelho_fixture",
	count = 1, storage = FIXTURE_BASE + 9,
	reward = {xp = 5, ryo = 0, items = {}, storageKey = 66123, storageValue = 1, outfit = 950, addon = 3},
})

do
	local p = stub.newPlayer("FixtureReward")
	NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc9"])
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("coelho_fixture"))
	NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc9"])
	eq("reward.storage: grava o storage arbitrário", p:getStorageValue(66123), 1)
	check("reward.outfit: concede o looktype", p._outfits[950] == true)
	eq("reward.addon: aplica o addon do looktype concedido", p._addons[950], 3)
end

-- B7: progress_text / done_text com placeholders {count}/{needed}/{player}
local qTemplates = addFixture({
	id = "fx_templates", npc = "fixture_npc10", npcName = "Fixture NPC 10",
	name = "Textos Customizados", text = "Traga o que for preciso.",
	kind = "kill", monster = "coelho_fixture", count = 3, storage = FIXTURE_BASE + 10,
	reward = {xp = 1, ryo = 0, items = {}},
	progressText = "{player}, faltam {count}/{needed}!",
	doneText = "Valeu, {player}! Você terminou.",
})

do
	local p = stub.newPlayer("FixtureTemplates")
	NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc10"])
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("coelho_fixture"))
	local msgProg = NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc10"])
	eq("progress_text: placeholders {count}/{needed}/{player} substituídos", msgProg,
		"FixtureTemplates, faltam 1/3!")
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("coelho_fixture"))
	stub.creatureEvents["NarutoQuestKill"].onKill(p, fakeMonster("coelho_fixture"))
	local msgDone = NarutoQuests.talk(p, NarutoQuests.byNpc["fixture_npc10"])
	eq("done_text: placeholder {player} substituído", msgDone, "Valeu, FixtureTemplates! Você terminou.")
end

-- B8: NarutoQuests.progressText (cliente — aba Missões) por kind
do
	local pFresh = stub.newPlayer("FixtureProgressText")
	eq("progressText: quest não aceita = 'Disponível'", NarutoQuests.progressText(pFresh, qDrop), "Disponível")

	local pCollect = stub.newPlayer("FixtureProgressCollect")
	NarutoQuests.talk(pCollect, NarutoQuests.byNpc["fixture_npc2"])
	pCollect:addItem(77001, 1)
	eq("progressText: collect_item mostra 'X/Y itens'", NarutoQuests.progressText(pCollect, qDrop), "1/2 itens")

	local pReach = stub.newPlayer("FixtureProgressReach", {pos = {x = 0, y = 0, z = 7}})
	NarutoQuests.talk(pReach, NarutoQuests.byNpc["fixture_npc4"])
	eq("progressText: reach em andamento = 'A caminho'", NarutoQuests.progressText(pReach, qReach), "A caminho")

	local pTalk = stub.newPlayer("FixtureProgressTalk")
	NarutoQuests.talk(pTalk, NarutoQuests.byNpc["fixture_npc3"])
	eq("progressText: talk_to mostra o nome do alvo", NarutoQuests.progressText(pTalk, qTalk), "Fale com Ichiro, o Mercador")

	local pDone = stub.newPlayer("FixtureProgressDone")
	NarutoQuests.talk(pDone, NarutoQuests.byNpc["fixture_npc5"])
	stub.creatureEvents["NarutoQuestKill"].onKill(pDone, fakeMonster("coelho_fixture"))
	NarutoQuests.talk(pDone, NarutoQuests.byNpc["fixture_npc5"])
	eq("progressText: quest DONE = 'Concluída'", NarutoQuests.progressText(pDone, qPrereq), "Concluída")
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
