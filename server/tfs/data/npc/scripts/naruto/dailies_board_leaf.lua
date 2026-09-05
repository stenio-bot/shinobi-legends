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
		if q.kind == 'talk_to' and q.targetNpc == 'dailies_board_leaf' then
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
keywordHandler:addKeyword({'entregar'}, deliverCallback, {})
npcHandler:setMessage(MESSAGE_GREET, "Ol\xE1, |PLAYERNAME|. Diga {diaria} para ver as 3 miss\xF5es de hoje.")
function onCreatureSay(cid, type, msg) npcHandler:onCreatureSay(cid, type, msg) end
npcHandler:addModule(FocusModule:new())
