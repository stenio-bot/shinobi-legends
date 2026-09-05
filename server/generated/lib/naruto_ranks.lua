-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/lib/naruto_ranks.lua e adicione `dofile('data/lib/naruto_ranks.lua')`
-- em data/lib/lib.lua (antes de naruto_quests.lua não é obrigatório: lookups são em runtime).
--
-- BÔNUS DE STATUS (status_bonus de data/ranks.json): o TFS 1.4.2 não tem setter direto de
-- max HP/chakra/defesa. Escolha desta implementação: condição permanente CONDITION_ATTRIBUTES
-- (ticks = -1) com subId fixo (NarutoRanks.BONUS_SUBID). CONDITION_PARAM_STAT_MAXHITPOINTS e
-- _MAXMANAPOINTS somam diretamente ao HP/chakra máximo (suporte nativo do TFS, ver
-- server/tfs/src/condition.cpp). 'defense' NÃO tem stat próprio (armor só vem de itens no TFS)
-- — aproximado com CONDITION_PARAM_SKILL_SHIELD (pontos de skill Shield, que entram no cálculo
-- de bloqueio/defesa). A condição é removida e recriada do zero a cada login/promoção para
-- nunca acumular: o bônus ativo é sempre o do rank ATUAL, nunca a soma de ranks anteriores.
NarutoRanks = {}
NarutoRanks.STORAGE = 60010
NarutoRanks.BONUS_SUBID = 9010
NarutoRanks.list = {
	{rank = 'genin', index = 1, minLevel = 1, title = 'Genin da vila', areas = {'floresta_da_vila', 'costa_das_mares'}, jutsuTier = 1, statusBonus = {maxHp = 0, maxChakra = 0, defense = 0}},
	{rank = 'chunin', index = 2, minLevel = 20, title = 'Chunin — aprovado no Exame Chunin', areas = {'floresta_da_morte', 'ruinas_do_cla_marionetista'}, jutsuTier = 2, statusBonus = {maxHp = 30, maxChakra = 15, defense = 0}},
	{rank = 'jonin', index = 3, minLevel = 50, title = 'Jonin — venceu o Espadachim da Névoa e o Marionetista das Ruínas', areas = {'montanha_do_trovao'}, jutsuTier = 3, statusBonus = {maxHp = 80, maxChakra = 40, defense = 5}},
	{rank = 'anbu', index = 4, minLevel = 80, title = 'Anbu — venceu a Dupla Imortal e a guarda externa do Covil', areas = {'covil_nuvem_vermelha'}, jutsuTier = 3, statusBonus = {maxHp = 150, maxChakra = 70, defense = 10}},
	{rank = 'kage', index = 5, minLevel = 100, title = 'Kage — derrotou os líderes da Organização Nuvem Vermelha', areas = {}, jutsuTier = 3, statusBonus = {maxHp = 300, maxChakra = 150, defense = 20}},
}
NarutoRanks.byRank, NarutoRanks.byIndex = {}, {}
for _, r in ipairs(NarutoRanks.list) do
	NarutoRanks.byRank[r.rank] = r
	NarutoRanks.byIndex[r.index] = r
end
NarutoRanks.FIRST = NarutoRanks.byIndex[1]

-- área (docs/lore/mundo.md) -> índice mínimo de rank para entrar (de ranks.json unlocks.areas)
NarutoRanks.zoneMinIndex = {
	['floresta_da_vila'] = 1,
	['costa_das_mares'] = 1,
	['floresta_da_morte'] = 2,
	['ruinas_do_cla_marionetista'] = 2,
	['montanha_do_trovao'] = 3,
	['covil_nuvem_vermelha'] = 4,
}

--- Rank atual do jogador (storage NarutoRanks.STORAGE; ausente/inválido = Genin).
function NarutoRanks.get(player)
	local idx = player:getStorageValue(NarutoRanks.STORAGE)
	if not idx or idx < 1 then idx = 1 end
	return NarutoRanks.byIndex[idx] or NarutoRanks.FIRST
end

--- true se o rank atual do jogador já é suficiente para a área nomeada (docs/lore/mundo.md).
--- Zona sem gate conhecida (não listada em nenhum unlocks.areas) é sempre livre.
function NarutoRanks.canEnter(player, zone)
	local need = NarutoRanks.zoneMinIndex[zone]
	if not need then return true end
	return NarutoRanks.get(player).index >= need
end

--- Remove e reaplica do zero a condição de bônus de status do rank ATUAL. Chamar no login
--- (scripts/naruto/quests_kill.lua) e logo após NarutoRanks.promote.
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

--- Promove o jogador para 'rankId' se ele ainda não tiver esse rank ou superior. Aplica bônus
--- de status, título e efeito. Retorna true se promoveu (false se já era esse rank ou maior).
--- Empurra o `state` do opcode 210 (com o novo rank) para o cliente na hora - é assim que o
--- rótulo "Rank: X" do menu Shinobi/status atualiza sem precisar relogar (docs/sistemas/
--- cliente-ux.md). NarutoCharacters pode ainda não ter sido carregado (ordem de dofile em
--- data/lib/lib.lua não é garantida entre libs "naruto_*"); a chamada só ACONTECE em runtime
--- (login/talkaction/GM), quando todas as libs já terminaram de carregar - a guarda `if` é só
--- para o caso raro de rodar sem naruto_characters.lua instalado.
function NarutoRanks.promote(player, rankId)
	local target = NarutoRanks.byRank[rankId]
	if not target then return false end
	if target.index <= NarutoRanks.get(player).index then return false end
	player:setStorageValue(NarutoRanks.STORAGE, target.index)
	NarutoRanks.applyBonus(player)
	player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Parabéns! Você agora é " .. target.title .. "!")
	player:getPosition():sendMagicEffect(CONST_ME_FIREWORK_YELLOW)
	if NarutoCharacters and NarutoCharacters.sendState then
		NarutoCharacters.sendState(player)
	end
	if NarutoAchievements then NarutoAchievements.onRankPromoted(player, rankId) end
	return true
end
