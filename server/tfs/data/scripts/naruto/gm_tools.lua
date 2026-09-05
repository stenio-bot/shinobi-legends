-- Ferramentas de GM do Shinobi Legends (revscriptsys). Só contas do tipo GOD (accounts.type = 6 no TFS 1.4.2).
-- /arena          teleporta para o tile livre mais próximo fora de zona de proteção
-- /tp x,y,z       teleporta para a posição
-- /lvl N          sobe/desce para o level N
-- /jutsus         aprende os 8 jutsus ATUAIS (4 do personagem + 4 do elemento)
-- /personagem id  troca de personagem (qualquer um, ignora vila; ver !personagem para jogadores)
-- /elemento id    troca de elemento (katon|suiton|raiton|doton|fuuton; ver !elemento)
-- /full           vida e chakra cheios
-- /vila nome      troca de vila (vocação): folha, nevoa, nuvem, areia
-- /god            level 100, skills 100, todos os jutsus, 1 milhão de ryo, mochila com todos os itens, melhor equipamento vestido
-- /pvm            alterna entre o grupo God (ignorado por monstros) e God Vulnerável (id 7, pode ser atacado) — para testar PvM como GM
-- /npc nome       invoca um NPC pelo nome exato (data/npc/<Nome>.xml) do lado do GM — útil para
--                 testar diálogo de NPCs ainda sem posição definitiva no mapa físico
-- /sl             lista estes comandos
local GROUP_GOD = 6
local GROUP_GOD_PVM = 7

local function isGod(player)
	return player:getGroup():getAccess() and player:getAccountType() >= ACCOUNT_TYPE_GOD
end

-- Personagem atual do jogador (storage 60001, ver character_switch.lua); se não escolheu
-- nenhum ainda, cai no primeiro personagem da vila (vocação) dele.
local function currentCharacter(player)
	if not NarutoCharacters then return nil end
	local look = player:getStorageValue(60001)
	if look and look > 0 and NarutoCharacters.byLook[look] then
		return NarutoCharacters.byLook[look]
	end
	local list = NarutoCharacters.byVillage and NarutoCharacters.byVillage[player:getVocation():getId()]
	return list and list[1] or nil
end

-- Elemento atual (storage 60002 = índice em NarutoElements.list).
local function currentElement(player)
	if not NarutoElements then return nil end
	local idx = player:getStorageValue(60002)
	if idx and idx > 0 and NarutoElements.list[idx] then
		return NarutoElements.list[idx]
	end
	local char = currentCharacter(player)
	return char and NarutoElements.byId[char.default_element] or NarutoElements.list[1]
end

-- Os 8 jutsus atuais: 4 do personagem + 4 do elemento (nomes, na ordem do protocolo 210).
local function activeJutsuNames(player)
	local names = {}
	local char = currentCharacter(player)
	if char then for _, j in ipairs(char.jutsus) do names[#names + 1] = j.name end end
	local el = currentElement(player)
	if el then for _, j in ipairs(el.jutsus) do names[#names + 1] = j.name end end
	return names, char, el
end

local function findArena(from)
	for r = 1, 40 do
		for dx = -r, r do
			for dy = -r, r do
				if math.abs(dx) == r or math.abs(dy) == r then
					local pos = Position(from.x + dx, from.y + dy, from.z)
					local tile = Tile(pos)
					if tile and tile:isWalkable() and not tile:hasFlag(TILESTATE_PROTECTIONZONE)
						and not tile:hasFlag(TILESTATE_BLOCKSOLID) and not tile:getTopCreature()
						and tile:getGround() and not tile:hasFlag(TILESTATE_FLOORCHANGE) then
						-- exige 3x3 livre em volta para caber monstros
						local ok = true
						for ex = -1, 1 do
							for ey = -1, 1 do
								local t2 = Tile(Position(pos.x + ex, pos.y + ey, pos.z))
								if not t2 or not t2:isWalkable() or t2:hasFlag(TILESTATE_BLOCKSOLID) then ok = false end
							end
						end
						if ok then return pos end
					end
				end
			end
		end
	end
	return nil
end


local SLOT_BY_NAME = { head = CONST_SLOT_HEAD, body = CONST_SLOT_ARMOR, legs = CONST_SLOT_LEGS, feet = CONST_SLOT_FEET,
	weapon = CONST_SLOT_LEFT, offhand = CONST_SLOT_RIGHT, accessory = CONST_SLOT_RING, back = CONST_SLOT_BACKPACK }

local function raiseSkillTo(player, skill, target)
	-- addSkillTries sobe quantos níveis forem necessários; blocos grandes evitam depender de getRequiredSkillTries
	local guard = 0
	while player:getSkillLevel(skill) < target and guard < 5000 do
		player:addSkillTries(skill, 1000000)
		guard = guard + 1
	end
end

local function godMode(player)
	-- level
	local need = Game.getExperienceForLevel(100) - player:getExperience()
	if need > 0 then player:addExperience(need, false) end
	-- skills físicas 100 e Ninjutsu (magic level) 100
	for _, sk in ipairs({SKILL_FIST, SKILL_CLUB, SKILL_SWORD, SKILL_AXE, SKILL_DISTANCE, SKILL_SHIELD, SKILL_FISHING}) do
		raiseSkillTo(player, sk, 100)
	end
	-- grupos de GM têm a flag NotGainMana: troca temporariamente para o grupo 1 para o ML subir
	local group = player:getGroup()
	player:setGroup(Group(1))
	local guard = 0
	-- mana necessária cresce 4x por nível (manamultiplier); ML ~30 é o teto prático antes do overflow do TFS
	while player:getBaseMagicLevel() < 30 and guard < 500 do
		player:addManaSpent(1000000000000000)
		guard = guard + 1
	end
	player:setGroup(group)
	-- jutsus: os 8 ATUAIS (4 do personagem + 4 do elemento). Use /personagem e /elemento antes.
	local names, char = activeJutsuNames(player)
	local jutsuCount = 0
	if #names > 0 then
		for _, name in ipairs(names) do player:learnSpell(name) jutsuCount = jutsuCount + 1 end
	elseif NarutoJutsus then
		for _, name in ipairs(NarutoJutsus) do player:learnSpell(name) end
		jutsuCount = #NarutoJutsus
	end
	-- ryo
	player:addItem(NarutoQuests and NarutoQuests.RYO_ID or 2148, 100)  -- 1 pilha visível
	player:setBankBalance(player:getBankBalance() + 1000000)
	-- itens: uma mochila com tudo, e o melhor equipamento vestido
	if NarutoItems then
		local best = {}
		for _, it in ipairs(NarutoItems) do
			if it.slot ~= "" then
				local key = it.slot
				local score = it.atk + it.def_ + it.level
				if not best[key] or score > best[key].score then best[key] = { id = it.id, score = score } end
			end
		end
		for slotName, b in pairs(best) do
			local slot = SLOT_BY_NAME[slotName]
			if slot then
				local old = player:getSlotItem(slot)
				if old then old:remove() end
				player:addItemEx(Game.createItem(b.id, 1), true, slot)
			end
		end
		local bp = player:getSlotItem(CONST_SLOT_BACKPACK)
		if not bp then
			player:addItemEx(Game.createItem(1988, 1), true, CONST_SLOT_BACKPACK)
			bp = player:getSlotItem(CONST_SLOT_BACKPACK)
		end
		local box = Game.createItem(1988, 1)  -- mochila interna para o resto
		if bp and box then
			bp:addItemEx(box)
			local n = 0
			for _, it in ipairs(NarutoItems) do
				local count = (it.stack > 1) and math.min(it.stack, 50) or 1
				local target = (n < 18) and box or bp
				if target:addItem(it.id, count) then n = n + 1 end
			end
		end
	end
	player:addHealth(player:getMaxHealth())
	player:addMana(player:getMaxMana())
	player:getPosition():sendMagicEffect(CONST_ME_FIREWORK_YELLOW)
	player:sendTextMessage(MESSAGE_INFO_DESCR, string.format("Modo deus: level %d, skills 100, ninjutsu %d, %d jutsus (personagem: %s), 1.000.000 ryo no banco, mochila cheia.",
		player:getLevel(), player:getBaseMagicLevel(), jutsuCount, char and char.name or "nenhum"))
end

local VILAS = { folha = 1, nevoa = 2, ["névoa"] = 2, nuvem = 3, areia = 4 }

local t = TalkAction("/arena", "/tp", "/lvl", "/jutsus", "/full", "/vila", "/sl", "/god", "/pvm", "/personagem", "/elemento")
function t.onSay(player, words, param)
	if not isGod(player) then return true end
	param = param and param:trim() or ""
	if words == "/sl" then
		player:sendTextMessage(MESSAGE_INFO_DESCR, "GM: /god (tudo no máximo), /arena, /tp x,y,z, /lvl N, /jutsus (os 8 atuais), /full, /vila folha|nevoa|nuvem|areia, /personagem id|nome (troca de personagem, qualquer vila), /elemento katon|suiton|raiton|doton|fuuton, /pvm (liga/desliga ser atacado por monstros). Padrão TFS: /m nome, /i item, /goto jogador, /c jogador, /ghost, /reload.")
	elseif words == "/personagem" then
		if not NarutoCharacters or not NarutoCharacters.apply then
			player:sendCancelMessage("Personagens não carregados (rode tools/export_tfs.py e reinstale).")
			return false
		end
		if param == "" then
			local names = {}
			for _, c in ipairs(NarutoCharacters.list) do table.insert(names, c.name .. " (" .. c.id .. ")") end
			player:sendTextMessage(MESSAGE_INFO_DESCR, "Personagens: " .. table.concat(names, ", ") .. ". Uso: /personagem <id|nome>")
			return false
		end
		local q, target = param:lower(), nil
		for _, c in ipairs(NarutoCharacters.list) do
			if c.id:lower() == q or c.name:lower() == q then target = c break end
		end
		if not target then
			player:sendCancelMessage("Personagem não encontrado. Use /personagem para ver a lista.")
			return false
		end
		local ok, err = NarutoCharacters.apply(player, target.id, nil, {force = true})
		if not ok then player:sendCancelMessage(err) end
	elseif words == "/elemento" then
		if not NarutoElements or not NarutoCharacters or not NarutoCharacters.apply then
			player:sendCancelMessage("Elementos não carregados (rode tools/install_generated.sh).")
			return false
		end
		if param == "" then
			local names = {}
			for _, e in ipairs(NarutoElements.list) do names[#names + 1] = e.id .. " (" .. e.name .. ")" end
			local cur = currentElement(player)
			player:sendTextMessage(MESSAGE_INFO_DESCR, "Elemento atual: " .. (cur and cur.name or "nenhum") ..
				". Disponíveis: " .. table.concat(names, ", ") .. ". Uso: /elemento <id>")
			return false
		end
		local q, target = param:lower(), nil
		for _, e in ipairs(NarutoElements.list) do
			if e.id:lower() == q or e.name:lower() == q then target = e break end
		end
		if not target then
			player:sendCancelMessage("Elemento não encontrado. Use /elemento para ver a lista.")
			return false
		end
		local ok, err = NarutoCharacters.apply(player, nil, target.id, {force = true})
		if not ok then player:sendCancelMessage(err) end
	elseif words == "/pvm" then
		local currentId = player:getGroup():getId()
		if currentId == GROUP_GOD_PVM then
			player:setGroup(Group(GROUP_GOD))
			player:sendTextMessage(MESSAGE_INFO_DESCR, "PvM desligado: monstros não vão te atacar (grupo God normal).")
		else
			player:setGroup(Group(GROUP_GOD_PVM))
			player:sendTextMessage(MESSAGE_INFO_DESCR, "PvM ligado: monstros vão te atacar (grupo God Vulnerável).")
		end
	elseif words == "/arena" then
		local pos = findArena(player:getPosition())
		if pos then
			player:teleportTo(pos)
			pos:sendMagicEffect(CONST_ME_TELEPORT)
			player:sendTextMessage(MESSAGE_INFO_DESCR, string.format("Arena em %d,%d,%d. Use /m Lobo para invocar.", pos.x, pos.y, pos.z))
		else
			player:sendCancelMessage("Nenhum tile livre fora de PZ por perto.")
		end
	elseif words == "/tp" then
		local x, y, z = param:match("^(%d+)%s*,%s*(%d+)%s*,%s*(%d+)$")
		if not x then player:sendCancelMessage("Uso: /tp x,y,z") return false end
		local pos = Position(tonumber(x), tonumber(y), tonumber(z))
		if not Tile(pos) then player:sendCancelMessage("Posição inválida (não existe tile aí).") return false end
		-- pushMovement = false: teleporta para QUALQUER tile existente, mesmo bloqueado/PZ
		player:teleportTo(pos, false)
		pos:sendMagicEffect(CONST_ME_TELEPORT)
	elseif words == "/lvl" then
		local target = tonumber(param)
		if not target or target < 1 or target > 500 then player:sendCancelMessage("Uso: /lvl N") return false end
		local need = Game.getExperienceForLevel(target) - player:getExperience()
		if need > 0 then player:addExperience(need, false) else player:removeExperience(-need, false) end
		player:addHealth(player:getMaxHealth())
		player:addMana(player:getMaxMana())
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Level " .. player:getLevel() .. ".")
	elseif words == "/jutsus" then
		local names, char, el = activeJutsuNames(player)
		local n = 0
		if #names > 0 then
			for _, name in ipairs(names) do
				player:learnSpell(name)
				n = n + 1
			end
			player:sendTextMessage(MESSAGE_INFO_DESCR, string.format("%d jutsus aprendidos (personagem: %s, elemento: %s).",
				n, char and char.name or "?", el and el.name or "?"))
			if NarutoCharacters and NarutoCharacters.sendState then NarutoCharacters.sendState(player) end
		elseif NarutoJutsus then
			for _, name in ipairs(NarutoJutsus) do
				player:learnSpell(name)
				n = n + 1
			end
			player:sendTextMessage(MESSAGE_INFO_DESCR, n .. " jutsus aprendidos (todos, sem personagem definido).")
		end
	elseif words == "/god" then
		godMode(player)
	elseif words == "/full" then
		player:addHealth(player:getMaxHealth())
		player:addMana(player:getMaxMana())
		player:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
	elseif words == "/vila" then
		local id = VILAS[param:lower()]
		if not id then player:sendCancelMessage("Uso: /vila folha|nevoa|nuvem|areia") return false end
		player:setVocation(id)
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Vila: " .. player:getVocation():getName() .. ".")
	end
	return false
end
t:separator(" ")
t:register()

-- ------------------------------------------------------------------------------------------
-- Ferramentas de debug dos sistemas de progressão (docs/sistemas/progressao-servidor.md).
-- /storage key [value]   lê (sem value) ou grava (com value) um storage do jogador.
-- /rank [rankId]         mostra o rank atual (com HP/chakra/bônus) ou força uma promoção
--                        (para teste — bypassa NarutoRanks.checkProgress/rankGroups).
-- /zonecheck zona        mostra se o rank atual deixaria entrar na área nomeada
--                        (docs/lore/mundo.md; ver NarutoRanks.canEnter).
-- /conquista [id]         sem id: lista os ids de data/achievements.json ainda bloqueados
--                        (para copiar/colar). Com id: força o desbloqueio (ignora a condição
--                        de verdade) para teste — ver NarutoAchievements.grant.
local debugCmds = TalkAction("/storage", "/rank", "/zonecheck", "/npc", "/conquista")
function debugCmds.onSay(player, words, param)
	if not isGod(player) then return true end
	param = param and param:trim() or ""
	if words == "/npc" then
		if param == "" then player:sendCancelMessage("Uso: /npc Nome Exato (data/npc/<Nome>.xml)") return false end
		local pos = player:getPosition()
		local dir = player:getDirection()
		local front = Position(pos)
		front:getNextPosition(dir)
		local npc = Game.createNpc(param, Tile(front) and front or pos, false, true)
		if not npc then
			player:sendCancelMessage("NPC '" .. param .. "' não encontrado (data/npc/" .. param .. ".xml existe?).")
		else
			player:sendTextMessage(MESSAGE_INFO_DESCR, "NPC '" .. param .. "' invocado.")
		end
	elseif words == "/storage" then
		local key, value = param:match("^(%-?%d+)%s*(%-?%d*)$")
		if not key then player:sendCancelMessage("Uso: /storage key [value]") return false end
		key = tonumber(key)
		if value and value ~= "" then
			player:setStorageValue(key, tonumber(value))
			player:sendTextMessage(MESSAGE_INFO_DESCR, "storage " .. key .. " = " .. value)
		else
			player:sendTextMessage(MESSAGE_INFO_DESCR, "storage " .. key .. " = " .. tostring(player:getStorageValue(key)))
		end
	elseif words == "/rank" then
		if not NarutoRanks then player:sendCancelMessage("NarutoRanks não carregado.") return false end
		if param == "" then
			local r = NarutoRanks.get(player)
			player:sendTextMessage(MESSAGE_INFO_DESCR, string.format("Rank: %s (%s). HP %d/%d, Chakra %d/%d.",
				r.rank, r.title, player:getHealth(), player:getMaxHealth(), player:getMana(), player:getMaxMana()))
		else
			local ok = NarutoRanks.promote(player, param:lower())
			if not ok then player:sendCancelMessage("Não promoveu (rank inválido, ou já é esse rank ou maior). Use /storage 60010 <indice> para forçar.") end
		end
	elseif words == "/zonecheck" then
		if not NarutoRanks then player:sendCancelMessage("NarutoRanks não carregado.") return false end
		if param == "" then player:sendCancelMessage("Uso: /zonecheck zona") return false end
		local ok = NarutoRanks.canEnter(player, param)
		player:sendTextMessage(MESSAGE_INFO_DESCR, "canEnter('" .. param .. "') = " .. tostring(ok) .. " (rank atual: " .. NarutoRanks.get(player).rank .. ")")
	elseif words == "/conquista" then
		if not NarutoAchievements then player:sendCancelMessage("NarutoAchievements não carregado.") return false end
		if param == "" then
			local ids = {}
			for _, a in ipairs(NarutoAchievements.list) do
				if not NarutoAchievements.isUnlocked(player, a) then ids[#ids + 1] = a.id end
			end
			player:sendTextMessage(MESSAGE_INFO_DESCR, #ids .. " bloqueadas: " .. table.concat(ids, ", "))
		else
			local a = NarutoAchievements.byId[param]
			if not a then
				player:sendCancelMessage("Id desconhecido. Use /conquista sem parâmetro para listar os ids bloqueados.")
			elseif NarutoAchievements.isUnlocked(player, a) then
				player:sendCancelMessage("Já desbloqueada.")
			else
				NarutoAchievements.grant(player, a)
			end
		end
	end
	return false
end
debugCmds:separator(" ")
debugCmds:register()
