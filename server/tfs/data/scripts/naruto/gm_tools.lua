-- Ferramentas de GM do Shinobi Legends (revscriptsys). Só contas do tipo GOD (accounts.type = 6 no TFS 1.4.2).
-- /arena          teleporta para o tile livre mais próximo fora de zona de proteção
-- /tp x,y,z       teleporta para a posição
-- /lvl N          sobe/desce para o level N
-- /jutsus         aprende todos os jutsus
-- /full           vida e chakra cheios
-- /vila nome      troca de vila (vocação): folha, nevoa, nuvem, areia
-- /god            level 100, skills 100, todos os jutsus, 1 milhão de ryo, mochila com todos os itens, melhor equipamento vestido
-- /sl             lista estes comandos
local function isGod(player)
	return player:getGroup():getAccess() and player:getAccountType() >= ACCOUNT_TYPE_GOD
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
	-- jutsus
	if NarutoJutsus then for _, name in ipairs(NarutoJutsus) do player:learnSpell(name) end end
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
	player:sendTextMessage(MESSAGE_INFO_DESCR, string.format("Modo deus: level %d, skills 100, ninjutsu %d, %d jutsus, 1.000.000 ryo no banco, mochila cheia.",
		player:getLevel(), player:getBaseMagicLevel(), NarutoJutsus and #NarutoJutsus or 0))
end

local VILAS = { folha = 1, nevoa = 2, ["névoa"] = 2, nuvem = 3, areia = 4 }

local t = TalkAction("/arena", "/tp", "/lvl", "/jutsus", "/full", "/vila", "/sl", "/god")
function t.onSay(player, words, param)
	if not isGod(player) then return true end
	param = param and param:trim() or ""
	if words == "/sl" then
		player:sendTextMessage(MESSAGE_INFO_DESCR, "GM: /god (tudo no máximo), /arena, /tp x,y,z, /lvl N, /jutsus, /full, /vila folha|nevoa|nuvem|areia. Padrão TFS: /m nome, /i item, /goto jogador, /c jogador, /ghost, /reload.")
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
		if not Tile(pos) then player:sendCancelMessage("Posição inválida.") return false end
		player:teleportTo(pos)
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
		local n = 0
		if NarutoJutsus then
			for _, name in ipairs(NarutoJutsus) do
				player:learnSpell(name)
				n = n + 1
			end
		end
		player:sendTextMessage(MESSAGE_INFO_DESCR, n .. " jutsus aprendidos.")
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
