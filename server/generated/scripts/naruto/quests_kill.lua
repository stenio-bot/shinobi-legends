-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/scripts/naruto/quests_kill.lua (revscriptsys carrega sozinho)
local killEvent = CreatureEvent("NarutoQuestKill")
function killEvent.onKill(player, target)
	if not target:isMonster() then return true end
	local name = target:getName()
	for _, q in ipairs(NarutoQuests.list) do
		if q.kind == 'kill' then
			-- NOVO (docs/sistemas/missoes.md): objective.any_of — qualquer monstro da lista conta
			-- pro mesmo contador, além do 'kill' único de sempre.
			local matches = q.monster == name
			if not matches and q.anyOf then
				for _, mn in ipairs(q.anyOf) do
					if mn == name then matches = true break end
				end
			end
			if matches then
				local st = player:getStorageValue(q.storage)
				if st >= 0 and st < q.count then
					player:setStorageValue(q.storage, st + 1)
					player:sendTextMessage(MESSAGE_EVENT_ADVANCE, q.name .. ": " .. (st + 1) .. "/" .. q.count)
				end
			end
		elseif q.kind == 'collect_item' and q.dropsFrom then
			-- NOVO: objective.drops_from — o TFS 1.4.2 não tem "loot condicional por quest" no
			-- monster/*.xml (a tabela de loot não enxerga o storage do jogador que matou), então o
			-- drop extra é concedido aqui. Só dropa enquanto a missão está ATIVA (aceita, storage
			-- >= 0, não concluída) e o jogador ainda não tem o suficiente desse item (não empilha
			-- além do necessário pra entrega).
			local st = player:getStorageValue(q.storage)
			if st >= 0 then
				for _, drop in ipairs(q.dropsFrom) do
					if drop.monster == name then
						for _, it in ipairs(q.collectItems) do
							if it.itemKey == drop.itemKey and player:getItemCount(it.id) < it.count and math.random() <= drop.chance then
								player:addItem(it.id, 1)
								player:sendTextMessage(MESSAGE_EVENT_ADVANCE, it.name .. " obtido(a)! (" .. q.name .. ")")
							end
						end
					end
				end
			end
		end
		-- kind='keyword_quiz' NAO conta mortes (a etapa avança só respondendo a prova, palavra-
		-- chave {prova}); kind='talk_to' avança só falando com o NPC alvo; kind='reach' avança só
		-- chegando no local (poll abaixo). Nenhum dos três tem q.monster/q.anyOf preenchido, então
		-- já cairiam fora do primeiro `if q.kind == 'kill'` mesmo sem checagem explícita — mas o
		-- `if` já deixa isso impossível de qualquer forma.
	end
	return true
end
killEvent:register()

-- NOVO (docs/sistemas/missoes.md): objective.kind='reach' completa a ETAPA (storage -> q.count)
-- quando o jogador está a até 'radius' tiles (quadrado/Chebyshev: |dx|<=radius e |dy|<=radius, MESMO
-- z) de 'pos'. Escolha de implementação: poll (igual ao GlobalEvent de conquistas,
-- server/generated/scripts/naruto/achievements.lua) em vez de onStepIn/actionid de tile (exigiria
-- editar o mapa por missão, fora do escopo de tools/export_tfs.py) ou MoveEvent (mesmo motivo —
-- pediria uma entrada de tile por missão em vez de só um pos+radius no JSON). Poll PRÓPRIO (não
-- reaproveita o de achievements.lua, arquivo/lib diferente) para manter naruto_quests autocontido.
-- Ao chegar, só marca "pronto para entregar" — a recompensa é dada ao falar {missao} com o NPC que
-- deu a missão (mesmo fluxo de kill/any_of, narrativamente "volte e me conte").
local function narutoQuestPollReach(player)
	for _, q in ipairs(NarutoQuests.list) do
		if q.kind == 'reach' then
			local st = player:getStorageValue(q.storage)
			if st >= 0 and st < q.count then
				local pos = player:getPosition()
				if pos.z == q.pos.z and math.abs(pos.x - q.pos.x) <= q.radius and math.abs(pos.y - q.pos.y) <= q.radius then
					player:setStorageValue(q.storage, q.count)
					player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Chegou ao destino: " .. q.name .. " (diga {missao} para reportar)")
				end
			end
		end
	end
end

local reachPoll = GlobalEvent("NarutoQuestReachPoll")
function reachPoll.onThink(interval, lastExecution)
	if not NarutoQuests then return true end
	for _, player in ipairs(Game.getPlayers()) do
		narutoQuestPollReach(player)
	end
	return true
end
reachPoll:interval(7000)
reachPoll:register()

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
