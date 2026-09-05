-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

local keywordHandler = KeywordHandler:new()
local npcHandler = NpcHandler:new(keywordHandler)
NpcSystem.parseParameters(npcHandler)

function onCreatureAppear(cid) npcHandler:onCreatureAppear(cid) end
function onCreatureDisappear(cid) npcHandler:onCreatureDisappear(cid) end
function onThink() npcHandler:onThink() end

local TALK_TO_QUESTS = {}
if NarutoQuests then
	for _, q in ipairs(NarutoQuests.list) do
		if q.kind == 'talk_to' and q.targetNpc == 'quest_giver_akatsuki_lair' then
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
	local narutoTalkToSeen = {}
	for _, q in ipairs(TALK_TO_QUESTS) do
		local kw = q.keyword or 'missao'
		if not narutoTalkToSeen[kw] then
			narutoTalkToSeen[kw] = true
			keywordHandler:addKeyword({kw}, narutoTalkToCallback, {})
		end
	end
end
local QUESTS = NarutoQuests.byNpc['quest_giver_akatsuki_lair']
local function normalizeQuiz(s)
	s = tostring(s):lower()
	local map = {['\195\161']='a', ['\195\160']='a', ['\195\163']='a', ['\195\162']='a',
		['\195\169']='e', ['\195\170']='e', ['\195\173']='i', ['\195\179']='o',
		['\195\181']='o', ['\195\180']='o', ['\195\186']='u', ['\195\167']='c'}
	for accented, plain in pairs(map) do s = s:gsub(accented, plain) end
	return s
end

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
--    do TFS) N\xC3O \xE9 um id est\xE1vel \x97 \xE9 um userdata Player NOVO a cada mensagem (endere\xE7o muda
--    sempre, mesmo mensagens seguidas do mesmo jogador). Us\xE1-lo como chave de tabela
--    (quizState[cid]) falha sempre da 2a mensagem em diante. J\xE1 dentro do keywordHandler
--    (questCallback/quizCallback) o 'cid' \xC9 um inteiro est\xE1vel, porque npchandler.lua faz
--    `local cid = creature:getId()` antes de chamar processMessage \x97 s\xF3 o onCreatureSay
--    GLOBAL (nosso override, que roda ANTES de delegar pro npcHandler) recebe o userdata cru.
-- 2) Passar esse userdata cru como 2\xBA argumento de npcHandler:say(msg, cid) quebra em runtime
--    ("Lua Script Error: luaAddEvent(). Argument #5 is unsafe"): say() agenda a resposta via
--    addEvent (fila de 1s do NPC), que n\xE3o aceita userdata (s\xF3 tipos primitivos serializ\xE1veis).
-- Corre\xE7\xE3o: resolve 'cid' para o Player e usa SEMPRE player:getId() (inteiro) daqui pra baixo \x97
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
keywordHandler:addKeyword({'quiz'}, quizCallback, {})
npcHandler:setMessage(MESSAGE_GREET, "Ol\xE1, |PLAYERNAME|. Diga {missao} se quiser trabalho.")
function onCreatureSay(cid, type, msg)
	if handleQuizAnswer(cid, msg) then return end
	npcHandler:onCreatureSay(cid, type, msg)
end
npcHandler:addModule(FocusModule:new())
