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
		if q.kind == 'talk_to' and q.targetNpc == 'merchant_leaf' then
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
shopModule:addBuyableItem({'kunai de ferro'}, 2404, 50, 1, 'kunai de ferro')
shopModule:addBuyableItem({'adaga de genin'}, 23801, 200, 1, 'adaga de genin')
shopModule:addBuyableItem({'tant\x3F de a\xE7o'}, 2379, 400, 1, 'tant\x3F de a\xE7o')
shopModule:addBuyableItem({'luvas de combate'}, 2172, 1200, 1, 'luvas de combate')
shopModule:addBuyableItem({'shuriken de ferro'}, 7378, 5, 1, 'shuriken de ferro')
shopModule:addBuyableItem({'colete de genin'}, 2467, 120, 1, 'colete de genin')
shopModule:addBuyableItem({'cal\xE7a ninja'}, 2649, 80, 1, 'cal\xE7a ninja')
shopModule:addBuyableItem({'sand\xE1lias ninja'}, 2643, 60, 1, 'sand\xE1lias ninja')
shopModule:addBuyableItem({'bandana da vila'}, 2480, 30, 1, 'bandana da vila')
shopModule:addBuyableItem({'onigiri'}, 2666, 10, 1, 'onigiri')
shopModule:addBuyableItem({'p\xEDlula de chakra pequena'}, 7620, 30, 1, 'p\xEDlula de chakra pequena')
shopModule:addBuyableItem({'po\xE7\xE3o de vida pequena'}, 7618, 50, 1, 'po\xE7\xE3o de vida pequena')
shopModule:addBuyableItem({'ant\xEDdoto'}, 8473, 40, 1, 'ant\xEDdoto')
shopModule:addBuyableItem({'mochila de couro'}, 1988, 900, 1, 'mochila de couro')
shopModule:addSellableItem({'bandana da vila'}, 2480, 12, 'bandana da vila')
shopModule:addSellableItem({'colete de genin'}, 2467, 48, 'colete de genin')
shopModule:addSellableItem({'cal\xE7a ninja'}, 2649, 32, 'cal\xE7a ninja')
shopModule:addSellableItem({'sand\xE1lias ninja'}, 2643, 24, 'sand\xE1lias ninja')
shopModule:addSellableItem({'colete de pele de sapo'}, 2463, 880, 'colete de pele de sapo')
shopModule:addSellableItem({'botas do p\xE2ntano'}, 2195, 600, 'botas do p\xE2ntano')
shopModule:addSellableItem({'pele de lobo'}, 5897, 15, 'pele de lobo')
shopModule:addSellableItem({'presa de cobra'}, 5898, 40, 'presa de cobra')
shopModule:addSellableItem({'emblema de bandido'}, 2229, 8, 'emblema de bandido')
shopModule:addSellableItem({'gl\xE2ndula de sanguessuga'}, 5876, 35, 'gl\xE2ndula de sanguessuga')
shopModule:addSellableItem({'pele de sapo'}, 5880, 60, 'pele de sapo')
shopModule:addSellableItem({'\xF3leo de sapo'}, 5881, 150, '\xF3leo de sapo')
shopModule:addSellableItem({'bandana riscada'}, 10289, 45, 'bandana riscada')
shopModule:addSellableItem({'presa da serpente branca'}, 5895, 340, 'presa da serpente branca')
shopModule:addSellableItem({'presa do espadachim da n\xE9voa'}, 6352, 260, 'presa do espadachim da n\xE9voa')
shopModule:addSellableItem({'m\xE1scara do aprendiz'}, 6554, 80, 'm\xE1scara do aprendiz')
shopModule:addSellableItem({'selo do desertor'}, 6555, 620, 'selo do desertor')
shopModule:addSellableItem({'cora\xE7\xE3o amaldi\xE7oado'}, 6559, 950, 'cora\xE7\xE3o amaldi\xE7oado')
shopModule:addSellableItem({'emblema da nuvem vermelha'}, 6868, 380, 'emblema da nuvem vermelha')
shopModule:addSellableItem({'fragmento do anel escarlate'}, 6938, 1280, 'fragmento do anel escarlate')
shopModule:addSellableItem({'pena do trov\xE3o'}, 5891, 280, 'pena do trov\xE3o')
shopModule:addSellableItem({'estilha\xE7o de geleira'}, 2158, 320, 'estilha\xE7o de geleira')
shopModule:addSellableItem({'chifre de oni'}, 5893, 380, 'chifre de oni')
shopModule:addSellableItem({'escama de magma'}, 5889, 420, 'escama de magma')
shopModule:addSellableItem({'junta de marionete'}, 5901, 120, 'junta de marionete')
shopModule:addSellableItem({'n\xFAcleo de granito'}, 5892, 150, 'n\xFAcleo de granito')
shopModule:addSellableItem({'cinza espectral'}, 5905, 180, 'cinza espectral')
shopModule:addSellableItem({'talism\xE3 amaldi\xE7oado'}, 5884, 220, 'talism\xE3 amaldi\xE7oado')
shopModule:addSellableItem({'capuz do batedor'}, 7458, 128, 'capuz do batedor')
shopModule:addSellableItem({'cal\xE7a do batedor'}, 9928, 192, 'cal\xE7a do batedor')
shopModule:addSellableItem({'senbon de ferro'}, 2399, 96, 'senbon de ferro')
shopModule:addSellableItem({'kunai de ferro'}, 2404, 20, 'kunai de ferro')
shopModule:addSellableItem({'adaga de genin'}, 23801, 80, 'adaga de genin')
shopModule:addSellableItem({'tant\x3F de a\xE7o'}, 2379, 160, 'tant\x3F de a\xE7o')
shopModule:addSellableItem({'luvas de combate'}, 2172, 480, 'luvas de combate')
shopModule:addSellableItem({'wakizashi temperado'}, 2384, 720, 'wakizashi temperado')
shopModule:addSellableItem({'shuriken de ferro'}, 7378, 1, 'shuriken de ferro')
npcHandler:setMessage(MESSAGE_GREET, "Ol\xE1, |PLAYERNAME|. Diga {trade} para ver o que tenho.")
function onCreatureSay(cid, type, msg) npcHandler:onCreatureSay(cid, type, msg) end
npcHandler:addModule(FocusModule:new())
