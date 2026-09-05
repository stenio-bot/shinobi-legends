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
		if q.kind == 'talk_to' and q.targetNpc == 'merchant_mountain' then
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
shopModule:addBuyableItem({'po\xE7\xE3o de vida grande'}, 7591, 800, 1, 'po\xE7\xE3o de vida grande')
shopModule:addBuyableItem({'p\xEDlula do soldado'}, 8472, 900, 1, 'p\xEDlula do soldado')
shopModule:addBuyableItem({'p\xEDlula de chakra grande'}, 7590, 250, 1, 'p\xEDlula de chakra grande')
shopModule:addBuyableItem({'katana do trov\xE3o'}, 7382, 24200, 1, 'katana do trov\xE3o')
shopModule:addBuyableItem({'kanab\x3F de oni'}, 2421, 39200, 1, 'kanab\x3F de oni')
shopModule:addBuyableItem({'shuriken l\xE2mina de vento'}, 7367, 28800, 1, 'shuriken l\xE2mina de vento')
shopModule:addBuyableItem({'elmo do bramido'}, 2491, 11500, 1, 'elmo do bramido')
shopModule:addBuyableItem({'cota do bramido'}, 2492, 28800, 1, 'cota do bramido')
shopModule:addBuyableItem({'grevas do bramido'}, 2477, 17300, 1, 'grevas do bramido')
shopModule:addBuyableItem({'botas do bramido'}, 2646, 8600, 1, 'botas do bramido')
shopModule:addBuyableItem({'colar presa da tempestade'}, 2136, 24000, 1, 'colar presa da tempestade')
shopModule:addBuyableItem({'anel ancestral'}, 2169, 27000, 1, 'anel ancestral')
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
shopModule:addSellableItem({'kanab\x3F de oni'}, 2421, 15680, 'kanab\x3F de oni')
shopModule:addSellableItem({'shuriken l\xE2mina de vento'}, 7367, 11520, 'shuriken l\xE2mina de vento')
shopModule:addSellableItem({'elmo do bramido'}, 2491, 4600, 'elmo do bramido')
shopModule:addSellableItem({'cota do bramido'}, 2492, 11520, 'cota do bramido')
shopModule:addSellableItem({'grevas do bramido'}, 2477, 6920, 'grevas do bramido')
shopModule:addSellableItem({'botas do bramido'}, 2646, 3440, 'botas do bramido')
shopModule:addSellableItem({'pena do trov\xE3o'}, 5891, 280, 'pena do trov\xE3o')
shopModule:addSellableItem({'estilha\xE7o de geleira'}, 2158, 320, 'estilha\xE7o de geleira')
shopModule:addSellableItem({'chifre de oni'}, 5893, 380, 'chifre de oni')
shopModule:addSellableItem({'escama de magma'}, 5889, 420, 'escama de magma')
shopModule:addSellableItem({'l\xE2mina presa de oni'}, 7418, 80000, 'l\xE2mina presa de oni')
shopModule:addSellableItem({'kodachi das ru\xEDnas'}, 2383, 2480, 'kodachi das ru\xEDnas')
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
shopModule:addSellableItem({'elmo do ca\xE7ador de onis'}, 2496, 6272, 'elmo do ca\xE7ador de onis')
shopModule:addSellableItem({'coura\xE7a do ca\xE7ador de onis'}, 2494, 15680, 'coura\xE7a do ca\xE7ador de onis')
shopModule:addSellableItem({'grevas do ca\xE7ador de onis'}, 7894, 9408, 'grevas do ca\xE7ador de onis')
shopModule:addSellableItem({'botas do ca\xE7ador de onis'}, 7891, 4704, 'botas do ca\xE7ador de onis')
shopModule:addSellableItem({'shuriken congelante'}, 7438, 15680, 'shuriken congelante')
shopModule:addSellableItem({'capuz anbu negro'}, 2490, 8192, 'capuz anbu negro')
shopModule:addSellableItem({'manto anbu negro'}, 2489, 20480, 'manto anbu negro')
shopModule:addSellableItem({'cal\xE7a anbu negra'}, 11304, 12288, 'cal\xE7a anbu negra')
shopModule:addSellableItem({'botas anbu negras'}, 11240, 6144, 'botas anbu negras')
shopModule:addSellableItem({'senbon anbu negro'}, 8849, 20480, 'senbon anbu negro')
shopModule:addSellableItem({'kunai de ferro'}, 2404, 20, 'kunai de ferro')
shopModule:addSellableItem({'tant\x3F de a\xE7o'}, 2379, 160, 'tant\x3F de a\xE7o')
shopModule:addSellableItem({'wakizashi temperado'}, 2384, 720, 'wakizashi temperado')
shopModule:addSellableItem({'katana do ronin'}, 2412, 1000, 'katana do ronin')
shopModule:addSellableItem({'shuriken de ferro'}, 7378, 1, 'shuriken de ferro')
shopModule:addSellableItem({'f\x3Fma shuriken'}, 7368, 2400, 'f\x3Fma shuriken')
shopModule:addSellableItem({'luvas de combate'}, 2172, 480, 'luvas de combate')
npcHandler:setMessage(MESSAGE_GREET, "Ol\xE1, |PLAYERNAME|. Diga {trade} para ver o que tenho.")
function onCreatureSay(cid, type, msg) npcHandler:onCreatureSay(cid, type, msg) end
npcHandler:addModule(FocusModule:new())
