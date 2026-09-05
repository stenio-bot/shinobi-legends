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
		if q.kind == 'talk_to' and q.targetNpc == 'merchant_coastal' then
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
shopModule:addBuyableItem({'poção de vida pequena'}, 7618, 50, 1, 'poção de vida pequena')
shopModule:addBuyableItem({'poção de vida média'}, 7588, 200, 1, 'poção de vida média')
shopModule:addBuyableItem({'pílula de chakra pequena'}, 7620, 30, 1, 'pílula de chakra pequena')
shopModule:addBuyableItem({'antídoto'}, 8473, 40, 1, 'antídoto')
shopModule:addBuyableItem({'shuriken de ferro'}, 7378, 5, 1, 'shuriken de ferro')
shopModule:addBuyableItem({'kunai de ferro'}, 2404, 50, 1, 'kunai de ferro')
shopModule:addBuyableItem({'colete de genin'}, 2467, 120, 1, 'colete de genin')
shopModule:addBuyableItem({'wakizashi temperado'}, 2384, 1800, 1, 'wakizashi temperado')
shopModule:addSellableItem({'bandana da vila'}, 2480, 12, 'bandana da vila')
shopModule:addSellableItem({'colete de genin'}, 2467, 48, 'colete de genin')
shopModule:addSellableItem({'colete de chuunin'}, 2464, 1200, 'colete de chuunin')
shopModule:addSellableItem({'calça ninja'}, 2649, 32, 'calça ninja')
shopModule:addSellableItem({'sandálias ninja'}, 2643, 24, 'sandálias ninja')
shopModule:addSellableItem({'colete de pele de sapo'}, 2463, 880, 'colete de pele de sapo')
shopModule:addSellableItem({'botas do pântano'}, 2195, 600, 'botas do pântano')
shopModule:addSellableItem({'pele de lobo'}, 5897, 15, 'pele de lobo')
shopModule:addSellableItem({'presa de cobra'}, 5898, 40, 'presa de cobra')
shopModule:addSellableItem({'emblema de bandido'}, 2229, 8, 'emblema de bandido')
shopModule:addSellableItem({'glândula de sanguessuga'}, 5876, 35, 'glândula de sanguessuga')
shopModule:addSellableItem({'pele de sapo'}, 5880, 60, 'pele de sapo')
shopModule:addSellableItem({'óleo de sapo'}, 5881, 150, 'óleo de sapo')
shopModule:addSellableItem({'bandana riscada'}, 10289, 45, 'bandana riscada')
shopModule:addSellableItem({'presa da serpente branca'}, 5895, 340, 'presa da serpente branca')
shopModule:addSellableItem({'presa do espadachim da névoa'}, 6352, 260, 'presa do espadachim da névoa')
shopModule:addSellableItem({'máscara do aprendiz'}, 6554, 80, 'máscara do aprendiz')
shopModule:addSellableItem({'selo do desertor'}, 6555, 620, 'selo do desertor')
shopModule:addSellableItem({'coração amaldiçoado'}, 6559, 950, 'coração amaldiçoado')
shopModule:addSellableItem({'emblema da nuvem vermelha'}, 6868, 380, 'emblema da nuvem vermelha')
shopModule:addSellableItem({'fragmento do anel escarlate'}, 6938, 1280, 'fragmento do anel escarlate')
shopModule:addSellableItem({'pena do trovão'}, 5891, 280, 'pena do trovão')
shopModule:addSellableItem({'estilhaço de geleira'}, 2158, 320, 'estilhaço de geleira')
shopModule:addSellableItem({'chifre de oni'}, 5893, 380, 'chifre de oni')
shopModule:addSellableItem({'escama de magma'}, 5889, 420, 'escama de magma')
shopModule:addSellableItem({'junta de marionete'}, 5901, 120, 'junta de marionete')
shopModule:addSellableItem({'núcleo de granito'}, 5892, 150, 'núcleo de granito')
shopModule:addSellableItem({'cinza espectral'}, 5905, 180, 'cinza espectral')
shopModule:addSellableItem({'talismã amaldiçoado'}, 5884, 220, 'talismã amaldiçoado')
shopModule:addSellableItem({'capuz do batedor'}, 7458, 128, 'capuz do batedor')
shopModule:addSellableItem({'calça do batedor'}, 9928, 192, 'calça do batedor')
shopModule:addSellableItem({'senbon de ferro'}, 2399, 96, 'senbon de ferro')
shopModule:addSellableItem({'bandana de chunin'}, 5917, 512, 'bandana de chunin')
shopModule:addSellableItem({'calça de chunin'}, 2648, 768, 'calça de chunin')
shopModule:addSellableItem({'sandália de chunin'}, 2642, 384, 'sandália de chunin')
shopModule:addSellableItem({'kunai de ferro'}, 2404, 20, 'kunai de ferro')
shopModule:addSellableItem({'tantō de aço'}, 2379, 160, 'tantō de aço')
shopModule:addSellableItem({'wakizashi temperado'}, 2384, 720, 'wakizashi temperado')
shopModule:addSellableItem({'katana do ronin'}, 2412, 1000, 'katana do ronin')
shopModule:addSellableItem({'shuriken de ferro'}, 7378, 1, 'shuriken de ferro')
shopModule:addSellableItem({'fūma shuriken'}, 7368, 2400, 'fūma shuriken')
shopModule:addSellableItem({'luvas de combate'}, 2172, 480, 'luvas de combate')
npcHandler:setMessage(MESSAGE_GREET, "Olá, |PLAYERNAME|. Diga {trade} para ver o que tenho.")
function onCreatureSay(cid, type, msg) npcHandler:onCreatureSay(cid, type, msg) end
npcHandler:addModule(FocusModule:new())
