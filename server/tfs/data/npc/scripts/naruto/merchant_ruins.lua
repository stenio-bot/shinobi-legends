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
		if q.kind == 'talk_to' and q.targetNpc == 'merchant_ruins' then
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
shopModule:addBuyableItem({'po\xE7\xE3o de vida m\xE9dia'}, 7588, 200, 1, 'po\xE7\xE3o de vida m\xE9dia')
shopModule:addBuyableItem({'p\xEDlula de chakra grande'}, 7590, 250, 1, 'p\xEDlula de chakra grande')
shopModule:addBuyableItem({'ant\xEDdoto'}, 8473, 40, 1, 'ant\xEDdoto')
shopModule:addBuyableItem({'kodachi das ru\xEDnas'}, 2383, 6200, 1, 'kodachi das ru\xEDnas')
shopModule:addBuyableItem({'katana aprimorada'}, 2397, 7200, 1, 'katana aprimorada')
shopModule:addBuyableItem({'kunai com corrente'}, 2410, 7200, 1, 'kunai com corrente')
shopModule:addBuyableItem({'m\xE1scara do cl\xE3 perdido'}, 2457, 2900, 1, 'm\xE1scara do cl\xE3 perdido')
shopModule:addBuyableItem({'manto do cl\xE3 perdido'}, 2465, 7200, 1, 'manto do cl\xE3 perdido')
shopModule:addBuyableItem({'grevas do cl\xE3 perdido'}, 2478, 4300, 1, 'grevas do cl\xE3 perdido')
shopModule:addBuyableItem({'botas do cl\xE3 perdido'}, 2645, 2200, 1, 'botas do cl\xE3 perdido')
shopModule:addBuyableItem({'amuleto do selo antigo'}, 2131, 6000, 1, 'amuleto do selo antigo')
shopModule:addBuyableItem({'anel da vontade de pedra'}, 2164, 6500, 1, 'anel da vontade de pedra')
shopModule:addBuyableItem({'pergaminho: anel de chamas'}, 1953, 6000, 1, 'pergaminho: anel de chamas')
shopModule:addBuyableItem({'pergaminho: pris\xE3o de \xE1gua'}, 1967, 8000, 1, 'pergaminho: pris\xE3o de \xE1gua')
shopModule:addBuyableItem({'pergaminho: estacas de terra'}, 4857, 8000, 1, 'pergaminho: estacas de terra')
shopModule:addSellableItem({'bandana da vila'}, 2480, 12, 'bandana da vila')
shopModule:addSellableItem({'colete de genin'}, 2467, 48, 'colete de genin')
shopModule:addSellableItem({'colete de chuunin'}, 2464, 1200, 'colete de chuunin')
shopModule:addSellableItem({'cal\xE7a ninja'}, 2649, 32, 'cal\xE7a ninja')
shopModule:addSellableItem({'sand\xE1lias ninja'}, 2643, 24, 'sand\xE1lias ninja')
shopModule:addSellableItem({'m\xE1scara anbu'}, 2497, 10000, 'm\xE1scara anbu')
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
shopModule:addSellableItem({'katana do trov\xE3o'}, 7382, 9680, 'katana do trov\xE3o')
shopModule:addSellableItem({'pena do trov\xE3o'}, 5891, 280, 'pena do trov\xE3o')
shopModule:addSellableItem({'estilha\xE7o de geleira'}, 2158, 320, 'estilha\xE7o de geleira')
shopModule:addSellableItem({'chifre de oni'}, 5893, 380, 'chifre de oni')
shopModule:addSellableItem({'escama de magma'}, 5889, 420, 'escama de magma')
shopModule:addSellableItem({'kodachi das ru\xEDnas'}, 2383, 2480, 'kodachi das ru\xEDnas')
shopModule:addSellableItem({'katana aprimorada'}, 2397, 2880, 'katana aprimorada')
shopModule:addSellableItem({'l\xE2mina de marionete'}, 7385, 3920, 'l\xE2mina de marionete')
shopModule:addSellableItem({'kunai com corrente'}, 2410, 2880, 'kunai com corrente')
shopModule:addSellableItem({'m\xE1scara do cl\xE3 perdido'}, 2457, 1160, 'm\xE1scara do cl\xE3 perdido')
shopModule:addSellableItem({'manto do cl\xE3 perdido'}, 2465, 2880, 'manto do cl\xE3 perdido')
shopModule:addSellableItem({'grevas do cl\xE3 perdido'}, 2478, 1720, 'grevas do cl\xE3 perdido')
shopModule:addSellableItem({'botas do cl\xE3 perdido'}, 2645, 880, 'botas do cl\xE3 perdido')
shopModule:addSellableItem({'junta de marionete'}, 5901, 120, 'junta de marionete')
shopModule:addSellableItem({'n\xFAcleo de granito'}, 5892, 150, 'n\xFAcleo de granito')
shopModule:addSellableItem({'cinza espectral'}, 5905, 180, 'cinza espectral')
shopModule:addSellableItem({'talism\xE3 amaldi\xE7oado'}, 5884, 220, 'talism\xE3 amaldi\xE7oado')
shopModule:addSellableItem({'capuz do batedor'}, 7458, 128, 'capuz do batedor')
shopModule:addSellableItem({'cal\xE7a do batedor'}, 9928, 192, 'cal\xE7a do batedor')
shopModule:addSellableItem({'senbon de ferro'}, 2399, 96, 'senbon de ferro')
shopModule:addSellableItem({'bandana de chunin'}, 5917, 512, 'bandana de chunin')
shopModule:addSellableItem({'cal\xE7a de chunin'}, 2648, 768, 'cal\xE7a de chunin')
shopModule:addSellableItem({'sand\xE1lia de chunin'}, 2642, 384, 'sand\xE1lia de chunin')
shopModule:addSellableItem({'m\xE1scara do rastreador sombrio'}, 3967, 2048, 'm\xE1scara do rastreador sombrio')
shopModule:addSellableItem({'manto do rastreador sombrio'}, 8870, 5120, 'manto do rastreador sombrio')
shopModule:addSellableItem({'cal\xE7a do rastreador sombrio'}, 15409, 3072, 'cal\xE7a do rastreador sombrio')
shopModule:addSellableItem({'botas do rastreador sombrio'}, 11303, 1536, 'botas do rastreador sombrio')
shopModule:addSellableItem({'adaga sombria'}, 2402, 5120, 'adaga sombria')
shopModule:addSellableItem({'shuriken sombria'}, 7366, 4608, 'shuriken sombria')
shopModule:addSellableItem({'colete de jonin'}, 2476, 8000, 'colete de jonin')
shopModule:addSellableItem({'cal\xE7a de jonin'}, 2647, 4800, 'cal\xE7a de jonin')
shopModule:addSellableItem({'botas de jonin'}, 6132, 2400, 'botas de jonin')
shopModule:addSellableItem({'tant\x3F de jonin'}, 2406, 8000, 'tant\x3F de jonin')
shopModule:addSellableItem({'senbon de jonin'}, 3965, 7600, 'senbon de jonin')
shopModule:addSellableItem({'kunai de ferro'}, 2404, 20, 'kunai de ferro')
shopModule:addSellableItem({'adaga de genin'}, 23801, 80, 'adaga de genin')
shopModule:addSellableItem({'tant\x3F de a\xE7o'}, 2379, 160, 'tant\x3F de a\xE7o')
shopModule:addSellableItem({'luvas de combate'}, 2172, 480, 'luvas de combate')
shopModule:addSellableItem({'wakizashi temperado'}, 2384, 720, 'wakizashi temperado')
shopModule:addSellableItem({'katana do ronin'}, 2412, 1000, 'katana do ronin')
shopModule:addSellableItem({'espad\xE3o de a\xE7o'}, 2413, 2000, 'espad\xE3o de a\xE7o')
shopModule:addSellableItem({'shuriken de ferro'}, 7378, 1, 'shuriken de ferro')
shopModule:addSellableItem({'f\x3Fma shuriken'}, 7368, 2400, 'f\x3Fma shuriken')
npcHandler:setMessage(MESSAGE_GREET, "Ol\xE1, |PLAYERNAME|. Diga {trade} para ver o que tenho.")
function onCreatureSay(cid, type, msg) npcHandler:onCreatureSay(cid, type, msg) end
npcHandler:addModule(FocusModule:new())
