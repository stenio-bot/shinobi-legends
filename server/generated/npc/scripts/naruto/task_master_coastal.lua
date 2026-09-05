-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

local keywordHandler = KeywordHandler:new()
local npcHandler = NpcHandler:new(keywordHandler)
NpcSystem.parseParameters(npcHandler)

function onCreatureAppear(cid) npcHandler:onCreatureAppear(cid) end
function onCreatureDisappear(cid) npcHandler:onCreatureDisappear(cid) end
function onThink() npcHandler:onThink() end

local TALK_TO_QUESTS = {}
if NarutoQuests then
	for _, q in ipairs(NarutoQuests.list) do
		if q.kind == 'talk_to' and q.targetNpc == 'task_master_coastal' then
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
local TASKS = NarutoTasks.byNpc['task_master_coastal'] or {}

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
keywordHandler:addKeyword({'entregar'}, deliverCallback, {})
npcHandler:setMessage(MESSAGE_GREET, "Olá, |PLAYERNAME|. Diga {tarefas} (lista), {tarefa} (aceitar) ou {entregar}.")
function onCreatureSay(cid, type, msg) npcHandler:onCreatureSay(cid, type, msg) end
npcHandler:addModule(FocusModule:new())
