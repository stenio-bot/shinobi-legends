-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/scripts/naruto/quests_kill.lua (revscriptsys carrega sozinho)
local killEvent = CreatureEvent("NarutoQuestKill")
function killEvent.onKill(player, target)
	if not target:isMonster() then return true end
	local name = target:getName()
	for _, q in ipairs(NarutoQuests.list) do
		if q.kind == 'kill' then
			-- NOVO (docs/sistemas/missoes.md): objective.any_of \x97 qualquer monstro da lista conta
			-- pro mesmo contador, al\xE9m do 'kill' \xFAnico de sempre.
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
			-- NOVO: objective.drops_from \x97 o TFS 1.4.2 n\xE3o tem "loot condicional por quest" no
			-- monster/*.xml (a tabela de loot n\xE3o enxerga o storage do jogador que matou), ent\xE3o o
			-- drop extra \xE9 concedido aqui. S\xF3 dropa enquanto a miss\xE3o est\xE1 ATIVA (aceita, storage
			-- >= 0, n\xE3o conclu\xEDda) e o jogador ainda n\xE3o tem o suficiente desse item (n\xE3o empilha
			-- al\xE9m do necess\xE1rio pra entrega).
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
		-- kind='keyword_quiz' NAO conta mortes (a etapa avan\xE7a s\xF3 respondendo a prova, palavra-
		-- chave {prova}); kind='talk_to' avan\xE7a s\xF3 falando com o NPC alvo; kind='reach' avan\xE7a s\xF3
		-- chegando no local (poll abaixo). Nenhum dos tr\xEAs tem q.monster/q.anyOf preenchido, ent\xE3o
		-- j\xE1 cairiam fora do primeiro `if q.kind == 'kill'` mesmo sem checagem expl\xEDcita \x97 mas o
		-- `if` j\xE1 deixa isso imposs\xEDvel de qualquer forma.
	end
	return true
end
killEvent:register()

-- NOVO (docs/sistemas/missoes.md): objective.kind='reach' completa a ETAPA (storage -> q.count)
-- quando o jogador est\xE1 a at\xE9 'radius' tiles (quadrado/Chebyshev: |dx|<=radius e |dy|<=radius, MESMO
-- z) de 'pos'. Escolha de implementa\xE7\xE3o: poll (igual ao GlobalEvent de conquistas,
-- server/generated/scripts/naruto/achievements.lua) em vez de onStepIn/actionid de tile (exigiria
-- editar o mapa por miss\xE3o, fora do escopo de tools/export_tfs.py) ou MoveEvent (mesmo motivo \x97
-- pediria uma entrada de tile por miss\xE3o em vez de s\xF3 um pos+radius no JSON). Poll PR\xD3PRIO (n\xE3o
-- reaproveita o de achievements.lua, arquivo/lib diferente) para manter naruto_quests autocontido.
-- Ao chegar, s\xF3 marca "pronto para entregar" \x97 a recompensa \xE9 dada ao falar {missao} com o NPC que
-- deu a miss\xE3o (mesmo fluxo de kill/any_of, narrativamente "volte e me conte").
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
	-- b\xF4nus de status do rank atual (docs/lore/progressao.md, ranks.json status_bonus): reaplica
	-- a cada login porque a condi\xE7\xE3o CONDITION_ATTRIBUTES n\xE3o persiste entre sess\xF5es no TFS.
	if NarutoRanks then NarutoRanks.applyBonus(player) end
	return true
end
login:register()
