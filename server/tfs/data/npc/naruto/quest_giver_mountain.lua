-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

local keywordHandler = KeywordHandler:new()
local npcHandler = NpcHandler:new(keywordHandler)
NpcSystem.parseParameters(npcHandler)

function onCreatureAppear(cid) npcHandler:onCreatureAppear(cid) end
function onCreatureDisappear(cid) npcHandler:onCreatureDisappear(cid) end
function onCreatureSay(cid, type, msg) npcHandler:onCreatureSay(cid, type, msg) end
function onThink() npcHandler:onThink() end

local QUESTS = NarutoQuests.byNpc['quest_giver_mountain']

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
npcHandler:setMessage(MESSAGE_GREET, "Olá, |PLAYERNAME|. Diga {missao} se quiser trabalho.")
npcHandler:addModule(FocusModule:new())
