-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/scripts/naruto/quests_kill.lua (revscriptsys carrega sozinho)
local killEvent = CreatureEvent("NarutoQuestKill")
function killEvent.onKill(player, target)
	if not target:isMonster() then return true end
	local name = target:getName()
	for _, q in ipairs(NarutoQuests.list) do
		-- kind='keyword_quiz' NAO conta mortes: a etapa avança só respondendo a prova (ver
		-- npc/scripts/naruto/<npc>.lua, palavra-chave {prova}) — evita que matar o monstro
		-- 'decorativo' do objective.kill de compat destrave a prova sem responder nada.
		if q.kind ~= 'keyword_quiz' and q.monster == name then
			local st = player:getStorageValue(q.storage)
			if st >= 0 and st < q.count then
				player:setStorageValue(q.storage, st + 1)
				player:sendTextMessage(MESSAGE_EVENT_ADVANCE, q.name .. ": " .. (st + 1) .. "/" .. q.count)
			end
		end
	end
	return true
end
killEvent:register()

local login = CreatureEvent("NarutoQuestKillLogin")
function login.onLogin(player)
	player:registerEvent("NarutoQuestKill")
	player:registerEvent("NarutoBossPhases")
	-- bônus de status do rank atual (docs/lore/progressao.md, ranks.json status_bonus): reaplica
	-- a cada login porque a condição CONDITION_ATTRIBUTES não persiste entre sessões no TFS.
	if NarutoRanks then NarutoRanks.applyBonus(player) end
	return true
end
login:register()
