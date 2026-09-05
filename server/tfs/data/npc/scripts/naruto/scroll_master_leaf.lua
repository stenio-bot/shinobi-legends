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
		if q.kind == 'talk_to' and q.targetNpc == 'scroll_master_leaf' then
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
local shopModule = ShopModule:new()
npcHandler:addModule(shopModule)
shopModule:addBuyableItem({'pergaminho: sopro de brasas'}, 1951, 500, 1, 'pergaminho: sopro de brasas')
shopModule:addBuyableItem({'pergaminho: flores de fênix'}, 1952, 5000, 1, 'pergaminho: flores de fênix')
shopModule:addBuyableItem({'pergaminho: dragão de fogo'}, 1954, 25000, 1, 'pergaminho: dragão de fogo')
shopModule:addBuyableItem({'pergaminho: palma curativa'}, 1950, 3000, 1, 'pergaminho: palma curativa')
shopModule:addBuyableItem({'pergaminho: kawarimi'}, 1949, 800, 1, 'pergaminho: kawarimi')
shopModule:addBuyableItem({'pergaminho: bunshin'}, 1948, 1200, 1, 'pergaminho: bunshin')
npcHandler:setMessage(MESSAGE_GREET, "Olá, |PLAYERNAME|. Diga {trade} para ver o que tenho.")
function onCreatureSay(cid, type, msg) npcHandler:onCreatureSay(cid, type, msg) end
npcHandler:addModule(FocusModule:new())
