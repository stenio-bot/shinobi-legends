-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/lib/naruto_ranks.lua e adicione `dofile('data/lib/naruto_ranks.lua')`
-- em data/lib/lib.lua (antes de naruto_quests.lua n\xE3o \xE9 obrigat\xF3rio: lookups s\xE3o em runtime).
--
-- B\xD4NUS DE STATUS (status_bonus de data/ranks.json): o TFS 1.4.2 n\xE3o tem setter direto de
-- max HP/chakra/defesa. Escolha desta implementa\xE7\xE3o: condi\xE7\xE3o permanente CONDITION_ATTRIBUTES
-- (ticks = -1) com subId fixo (NarutoRanks.BONUS_SUBID). CONDITION_PARAM_STAT_MAXHITPOINTS e
-- _MAXMANAPOINTS somam diretamente ao HP/chakra m\xE1ximo (suporte nativo do TFS, ver
-- server/tfs/src/condition.cpp). 'defense' N\xC3O tem stat pr\xF3prio (armor s\xF3 vem de itens no TFS)
-- \x97 aproximado com CONDITION_PARAM_SKILL_SHIELD (pontos de skill Shield, que entram no c\xE1lculo
-- de bloqueio/defesa). A condi\xE7\xE3o \xE9 removida e recriada do zero a cada login/promo\xE7\xE3o para
-- nunca acumular: o b\xF4nus ativo \xE9 sempre o do rank ATUAL, nunca a soma de ranks anteriores.
NarutoRanks = {}
NarutoRanks.STORAGE = 60010
NarutoRanks.BONUS_SUBID = 9010
NarutoRanks.list = {
	{rank = 'genin', index = 1, minLevel = 1, title = 'Genin da vila', areas = {'floresta_da_vila', 'costa_das_mares'}, jutsuTier = 1, statusBonus = {maxHp = 0, maxChakra = 0, defense = 0}},
	{rank = 'chunin', index = 2, minLevel = 20, title = 'Chunin \x97 aprovado no Exame Chunin', areas = {'floresta_da_morte', 'ruinas_do_cla_marionetista'}, jutsuTier = 2, statusBonus = {maxHp = 30, maxChakra = 15, defense = 0}},
	{rank = 'jonin', index = 3, minLevel = 50, title = 'Jonin \x97 venceu o Espadachim da N\xE9voa e o Marionetista das Ru\xEDnas', areas = {'montanha_do_trovao'}, jutsuTier = 3, statusBonus = {maxHp = 80, maxChakra = 40, defense = 5}},
	{rank = 'anbu', index = 4, minLevel = 80, title = 'Anbu \x97 venceu a Dupla Imortal e a guarda externa do Covil', areas = {'covil_nuvem_vermelha'}, jutsuTier = 3, statusBonus = {maxHp = 150, maxChakra = 70, defense = 10}},
	{rank = 'kage', index = 5, minLevel = 100, title = 'Kage \x97 derrotou os l\xEDderes da Organiza\xE7\xE3o Nuvem Vermelha', areas = {}, jutsuTier = 3, statusBonus = {maxHp = 300, maxChakra = 150, defense = 20}},
}
NarutoRanks.byRank, NarutoRanks.byIndex = {}, {}
for _, r in ipairs(NarutoRanks.list) do
	NarutoRanks.byRank[r.rank] = r
	NarutoRanks.byIndex[r.index] = r
end
NarutoRanks.FIRST = NarutoRanks.byIndex[1]

-- \xE1rea (docs/lore/mundo.md) -> \xEDndice m\xEDnimo de rank para entrar (de ranks.json unlocks.areas)
NarutoRanks.zoneMinIndex = {
	['floresta_da_vila'] = 1,
	['costa_das_mares'] = 1,
	['floresta_da_morte'] = 2,
	['ruinas_do_cla_marionetista'] = 2,
	['montanha_do_trovao'] = 3,
	['covil_nuvem_vermelha'] = 4,
}

--- Rank atual do jogador (storage NarutoRanks.STORAGE; ausente/inv\xE1lido = Genin).
function NarutoRanks.get(player)
	local idx = player:getStorageValue(NarutoRanks.STORAGE)
	if not idx or idx < 1 then idx = 1 end
	return NarutoRanks.byIndex[idx] or NarutoRanks.FIRST
end

--- true se o rank atual do jogador j\xE1 \xE9 suficiente para a \xE1rea nomeada (docs/lore/mundo.md).
--- Zona sem gate conhecida (n\xE3o listada em nenhum unlocks.areas) \xE9 sempre livre.
function NarutoRanks.canEnter(player, zone)
	local need = NarutoRanks.zoneMinIndex[zone]
	if not need then return true end
	return NarutoRanks.get(player).index >= need
end

--- Remove e reaplica do zero a condi\xE7\xE3o de b\xF4nus de status do rank ATUAL. Chamar no login
--- (scripts/naruto/quests_kill.lua) e logo ap\xF3s NarutoRanks.promote.
function NarutoRanks.applyBonus(player)
	player:removeCondition(CONDITION_ATTRIBUTES, CONDITIONID_DEFAULT, NarutoRanks.BONUS_SUBID)
	local b = NarutoRanks.get(player).statusBonus
	if (b.maxHp or 0) == 0 and (b.maxChakra or 0) == 0 and (b.defense or 0) == 0 then return end
	local cond = Condition(CONDITION_ATTRIBUTES, CONDITIONID_DEFAULT)
	cond:setParameter(CONDITION_PARAM_TICKS, -1)
	cond:setParameter(CONDITION_PARAM_SUBID, NarutoRanks.BONUS_SUBID)
	if b.maxHp ~= 0 then cond:setParameter(CONDITION_PARAM_STAT_MAXHITPOINTS, b.maxHp) end
	if b.maxChakra ~= 0 then cond:setParameter(CONDITION_PARAM_STAT_MAXMANAPOINTS, b.maxChakra) end
	if b.defense ~= 0 then cond:setParameter(CONDITION_PARAM_SKILL_SHIELD, b.defense) end
	player:addCondition(cond)
end

--- Promove o jogador para 'rankId' se ele ainda n\xE3o tiver esse rank ou superior. Aplica b\xF4nus
--- de status, t\xEDtulo e efeito. Retorna true se promoveu (false se j\xE1 era esse rank ou maior).
--- Empurra o `state` do opcode 210 (com o novo rank) para o cliente na hora - \xE9 assim que o
--- r\xF3tulo "Rank: X" do menu Shinobi/status atualiza sem precisar relogar (docs/sistemas/
--- cliente-ux.md). NarutoCharacters pode ainda n\xE3o ter sido carregado (ordem de dofile em
--- data/lib/lib.lua n\xE3o \xE9 garantida entre libs "naruto_*"); a chamada s\xF3 ACONTECE em runtime
--- (login/talkaction/GM), quando todas as libs j\xE1 terminaram de carregar - a guarda `if` \xE9 s\xF3
--- para o caso raro de rodar sem naruto_characters.lua instalado.
function NarutoRanks.promote(player, rankId)
	local target = NarutoRanks.byRank[rankId]
	if not target then return false end
	if target.index <= NarutoRanks.get(player).index then return false end
	player:setStorageValue(NarutoRanks.STORAGE, target.index)
	NarutoRanks.applyBonus(player)
	player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Parab\xE9ns! Voc\xEA agora \xE9 " .. target.title .. "!")
	player:getPosition():sendMagicEffect(CONST_ME_FIREWORK_YELLOW)
	if NarutoCharacters and NarutoCharacters.sendState then
		NarutoCharacters.sendState(player)
	end
	if NarutoAchievements then NarutoAchievements.onRankPromoted(player, rankId) end
	return true
end
