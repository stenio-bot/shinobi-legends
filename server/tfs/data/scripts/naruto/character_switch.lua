-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/scripts/naruto/character_switch.lua (revscriptsys carrega sozinho).
-- Depende de NarutoCharacters/NarutoElements (data/lib/naruto_characters.lua) e de
-- NarutoJson (data/lib/naruto_json.lua). Ambos entram via dofile em data/lib/lib.lua
-- (tools/install_generated.sh faz isso).
--
-- MODELO: o jogador escolhe PERSONAGEM (4 jutsus pessoais) + ELEMENTO (4 jutsus do set).
-- Os 8 jutsus sao aprendidos na hora; todo o resto e esquecido. Jutsus elementais NAO sao
-- filtrados por vila; personagens SIM (menos para GM).
--
-- PROTOCOLO com o cliente: opcode estendido 210, buffer = JSON.
--   servidor -> cliente: {"type":"state", ...}   (ver NarutoCharacters.sendState)
--   cliente -> servidor: {"type":"select","character":"id|null","element":"id|null"}
--                        {"type":"get_state"}
local OPCODE = 210
local STORAGE_ONBOARDED = 60000  -- 1 depois da primeira aplicacao (outfits liberados)
local STORAGE_CHARACTER = 60001  -- looktype do personagem atual
local STORAGE_ELEMENT   = 60002  -- indice do elemento em NarutoElements.order

local function isGodPlayer(player)
	return player:getGroup():getAccess() and player:getAccountType() >= ACCOUNT_TYPE_GOD
end

local function villageIdOf(player)
	local v = NarutoVillages and NarutoVillages[player:getVocation():getId()]
	return v and v.id or nil
end

--- Personagem atual (storage) ou, se nao houver, o primeiro da vila do jogador.
function NarutoCharacters.current(player)
	local look = player:getStorageValue(STORAGE_CHARACTER)
	if look and look > 0 and NarutoCharacters.byLook[look] then
		return NarutoCharacters.byLook[look]
	end
	return nil
end

function NarutoCharacters.defaultFor(player)
	local list = NarutoCharacters.byVillage[player:getVocation():getId()]
	return list and list[1] or NarutoCharacters.list[1]
end

--- Elemento atual (storage 60002 = indice) ou nil.
function NarutoCharacters.currentElement(player)
	local idx = player:getStorageValue(STORAGE_ELEMENT)
	if idx and idx > 0 then
		return NarutoElements.list[idx]
	end
	return nil
end

--- Resolve um elemento por id ('katon'), por indice numerico, ou nil.
local function resolveElement(elementId)
	if elementId == nil then return nil end
	if type(elementId) == 'number' then return NarutoElements.list[elementId] end
	return NarutoElements.byId[tostring(elementId)]
end

--- Resolve um personagem por id ('genin_uchiha') ou por looktype numerico.
local function resolveCharacter(characterId)
	if characterId == nil then return nil end
	if type(characterId) == 'number' then return NarutoCharacters.byLook[characterId] end
	return NarutoCharacters.byId[tostring(characterId)] or NarutoCharacters.byLook[tonumber(characterId) or -1]
end

--- Aplica personagem + elemento. Qualquer um dos dois pode vir nil = manter o atual
--- (ou cair no padrao: personagem da vila / elemento padrao do personagem).
--- opts.force ignora a validacao de vila, opts.silent nao manda mensagem.
--- Retorna true, ou false + mensagem de erro.
function NarutoCharacters.apply(player, characterId, elementId, opts)
	opts = opts or {}
	local char = resolveCharacter(characterId) or NarutoCharacters.current(player) or NarutoCharacters.defaultFor(player)
	if not char then
		return false, "Personagem desconhecido."
	end
	if characterId ~= nil and not resolveCharacter(characterId) then
		return false, "Personagem desconhecido."
	end
	if not opts.force and not isGodPlayer(player) and char.village_vocation ~= player:getVocation():getId() then
		return false, "Esse personagem nao e da sua vila."
	end
	local element = resolveElement(elementId)
	if elementId ~= nil and not element then
		return false, "Elemento desconhecido."
	end
	element = element or NarutoCharacters.currentElement(player) or NarutoElements.byId[char.default_element] or NarutoElements.list[1]
	if not element then
		return false, "Nenhum elemento configurado no servidor."
	end

	-- libera os trajes da vila na primeira vez
	if player:getStorageValue(STORAGE_ONBOARDED) < 1 then
		local village = NarutoVillages and NarutoVillages[player:getVocation():getId()]
		if village then
			for _, look in ipairs(village.outfits) do
				player:addOutfit(look)
			end
		end
	end
	-- personagem de outra vila (GM): garante que o outfit e vestivel
	player:addOutfit(char.looktype)

	for jname in pairs(NarutoCharacters.allJutsuNames) do
		player:forgetSpell(jname)
	end
	local learned = {}
	for _, j in ipairs(char.jutsus) do
		player:learnSpell(j.name)
		learned[#learned + 1] = j.name
	end
	for _, j in ipairs(element.jutsus) do
		player:learnSpell(j.name)
		learned[#learned + 1] = j.name
	end

	local outfit = player:getOutfit()
	outfit.lookType = char.looktype
	player:setOutfit(outfit)

	player:setStorageValue(STORAGE_CHARACTER, char.looktype)
	player:setStorageValue(STORAGE_ELEMENT, element.index)
	player:setStorageValue(STORAGE_ONBOARDED, 1)

	if not opts.silent then
		player:sendTextMessage(MESSAGE_INFO_DESCR, string.format(
			"Personagem: %s | Elemento: %s. Jutsus: %s.", char.name, element.name, table.concat(learned, ", ")))
		player:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
	end
	if not opts.noState then
		NarutoCharacters.sendState(player)
	end
	return true
end

-- ------------------------------------------------------------------ estado (opcode 210)
local function jutsuJson(j)
	return {id = j.id, name = j.name, words = j.words, element = j.element,
		type = j.type, chakra = j.chakra, cooldown_s = j.cooldown_s}
end

local function jutsuListJson(list)
	local out = NarutoJson.array({})
	for i, j in ipairs(list) do out[i] = jutsuJson(j) end
	return out
end

--- Monta e envia o `state` para o cliente (opcode 210, buffer JSON).
function NarutoCharacters.sendState(player, firstTime)
	if not player or not player:isPlayer() then return false end
	local isGm = isGodPlayer(player)
	local char = NarutoCharacters.current(player)
	local element = NarutoCharacters.currentElement(player)

	local chars = NarutoJson.array({})
	for _, c in ipairs(NarutoCharacters.list) do
		if isGm or c.village_vocation == player:getVocation():getId() then
			chars[#chars + 1] = {
				id = c.id, name = c.name, description = c.description, looktype = c.looktype,
				village = c.village, default_element = c.default_element,
				jutsus = jutsuListJson(c.jutsus),
			}
		end
	end

	local els = NarutoJson.array({})
	for i, e in ipairs(NarutoElements.list) do
		els[i] = {id = e.id, name = e.name, jutsus = jutsuListJson(e.jutsus)}
	end

	local active = NarutoJson.array({})
	if char then for _, j in ipairs(char.jutsus) do active[#active + 1] = jutsuJson(j) end end
	if element then for _, j in ipairs(element.jutsus) do active[#active + 1] = jutsuJson(j) end end

	-- rank (docs/sistemas/progressao-servidor.md): discreto, so id/titulo/indice - o cliente
	-- mostra ao lado do nome/skills. NarutoRanks pode nao existir (compat); nesse caso null.
	local rankInfo = NarutoJson.null
	if NarutoRanks then
		local r = NarutoRanks.get(player)
		rankInfo = {id = r.rank, title = r.title, index = r.index}
	end

	local state = {
		type = 'state',
		first_time = firstTime == true,
		is_gm = isGm,
		character = char and char.id or NarutoJson.null,
		element = element and element.id or NarutoJson.null,
		level = player:getLevel(),
		village = villageIdOf(player) or NarutoJson.null,
		rank = rankInfo,
		characters = chars,
		elements = els,
		active_jutsus = active,
	}
	return NarutoJson.sendExtended(player, OPCODE, NarutoJson.encode(state))
end

-- ------------------------------------------------------------------ progresso (opcode 210,
-- acao get_progress) - aba Missoes do menu Shinobi: rank + proximo rank (requisitos
-- pendentes), tarefas ativas, diarias do dia e missoes de historia com status.
-- NarutoRanks/NarutoQuests/NarutoTasks/NarutoDailies sao globais definidos em outras libs
-- (data/lib/naruto_ranks.lua, naruto_quests.lua, naruto_tasks.lua, naruto_dailies.lua) - todas
-- ja carregadas por dofile em data/lib/lib.lua antes de qualquer jogador logar; guardas `if X
-- then` sao so para o caso raro de uma delas nao existir (compat, ex.: sem data/tasks.json).
local function nextRankRequirements(player, nextRank)
	local reqs = NarutoJson.array({})
	if not NarutoQuests or not nextRank then return reqs end
	local group = NarutoQuests.rankGroups[nextRank.rank]
	if not group then return reqs end
	for _, storage in ipairs(group) do
		local q = NarutoQuests.byStorage and NarutoQuests.byStorage[storage]
		if q then
			reqs[#reqs + 1] = {
				name = q.name,
				npc = q.npcName or q.npc,
				done = player:getStorageValue(storage) == NarutoQuests.DONE,
			}
		end
	end
	return reqs
end

local function rankProgressJson(player)
	if not NarutoRanks then return NarutoJson.null end
	local cur = NarutoRanks.get(player)
	local out = {id = cur.rank, title = cur.title, index = cur.index}
	local nextRank = NarutoRanks.byIndex[cur.index + 1]
	if nextRank then
		out.next = {
			id = nextRank.rank, title = nextRank.title, index = nextRank.index,
			minLevel = nextRank.minLevel, requirements = nextRankRequirements(player, nextRank),
		}
	else
		out.next = NarutoJson.null
	end
	return out
end

local function tasksProgressJson(player)
	local out = NarutoJson.array({})
	if not NarutoTasks then return out end
	local now = os.time()
	for _, t in ipairs(NarutoTasks.list) do
		local prog = player:getStorageValue(t.progressStorage)
		if prog >= 0 then
			local cooldownUntil = player:getStorageValue(t.cooldownStorage)
			local remaining = 0
			if cooldownUntil and cooldownUntil > now then
				remaining = math.ceil((cooldownUntil - now) / 60)
			end
			out[#out + 1] = {
				id = t.id, name = t.name, npc = t.npcName, monster = t.monster,
				progress = prog, count = t.count, ready = prog >= t.count,
				cooldownRemainingMin = remaining,
			}
		end
	end
	return out
end

local function dailiesProgressJson(player)
	local out = NarutoJson.array({})
	if not NarutoDailies then return out end
	NarutoDailies.rollIfNeeded(player)
	for slot = 1, 3 do
		local entry = NarutoDailies.slotEntry(player, slot)
		if entry then
			local prog = NarutoDailies.slotProgress(player, slot)
			local status
			if prog > entry.count then
				status = 'delivered'
			elseif prog == entry.count then
				status = 'ready'
			else
				status = 'progress'
			end
			out[#out + 1] = {
				slot = slot, id = entry.id, name = entry.name, monster = entry.monster,
				progress = math.max(prog, 0), count = entry.count, status = status,
			}
		end
	end
	return out
end

local function missionsProgressJson(player)
	local out = NarutoJson.array({})
	if not NarutoQuests then return out end
	for _, q in ipairs(NarutoQuests.list) do
		local st = player:getStorageValue(q.storage)
		local status
		if st == NarutoQuests.DONE then
			status = 'done'
		elseif st < 0 then
			status = 'available'
		else
			status = 'in_progress'
		end
		out[#out + 1] = {id = q.id, name = q.name, npc = q.npcName or q.npc, status = status}
	end
	return out
end

--- Conquistas (NarutoAchievements, data/lib/naruto_achievements.lua): delega tudo para
--- NarutoAchievements.progressJson (lá mora a lista/categoria/progresso de cada uma) -
--- guarda `if` só para o caso raro de rodar sem data/achievements.json (compat).
local function achievementsProgressJson(player)
	if not NarutoAchievements then return NarutoJson.array({}) end
	return NarutoAchievements.progressJson(player)
end

--- Monta e envia o `progress` para o cliente (opcode 210, buffer JSON) - aba Missoes.
function NarutoCharacters.sendProgress(player)
	if not player or not player:isPlayer() then return false end
	local progress = {
		type = 'progress',
		rank = rankProgressJson(player),
		tasks = tasksProgressJson(player),
		dailies = dailiesProgressJson(player),
		missions = missionsProgressJson(player),
		achievements = achievementsProgressJson(player),
	}
	return NarutoJson.sendExtended(player, OPCODE, NarutoJson.encode(progress))
end

-- ------------------------------------------------------------------ cliente -> servidor
local opcodeEvent = CreatureEvent("NarutoOpcode")
function opcodeEvent.onExtendedOpcode(player, opcode, buffer)
	if opcode ~= OPCODE then return true end
	local msg, err = NarutoJson.decode(buffer)
	if type(msg) ~= 'table' then
		print("[naruto] opcode 210: JSON invalido (" .. tostring(err) .. ")")
		return true
	end
	if msg.type == 'get_state' then
		NarutoCharacters.sendState(player)
	elseif msg.type == 'select' then
		local ok, e = NarutoCharacters.apply(player, msg.character, msg.element, {noState = true})
		if not ok then
			player:sendCancelMessage(e or "Selecao invalida.")
		end
		NarutoCharacters.sendState(player)
	elseif msg.type == 'get_progress' then
		NarutoCharacters.sendProgress(player)
	end
	return true
end
opcodeEvent:register()

-- kit inicial por vocacao (gerado de data/villages.json + tfs_mapping.items)
local STARTING_KIT = {[1] = {2404, 2467, 2649, 2643, 2480}, [2] = {2404, 2467, 2649, 2643, 2480}, [3] = {7378, 2404, 2467, 2649, 2643, 2480}, [4] = {2404, 2467, 2649, 2643, 2480}}

-- ------------------------------------------------------------------ regen (rodada 5)
-- Regen de HP/chakra escalando com o level (rodada 5, item 1a da missao de balanceamento —
-- docs/sistemas/balanceamento-relatorio-v5.md par. 1): a rodada 4 usava os valores FIXOS da
-- vocacao (vocations.xml gainhp/gainmana, gerados por tools/export_tfs.py ~linha 571 -- 0,4
-- HP/s e 0,6 chakra/s pra QUALQUER level) -- contra um pool de chakra que cresce (100+level*10),
-- 0,6/s virava irrelevante ja em L15 (achado da rodada 4 secao 5: 93-98% do tempo de uma hunt de
-- 30min sem chakra pro tier 1 em L5/L15). NarutoRegen.apply reaplica a condicao (mesmo subId
-- 9020 -- server/tfs/src/creature.cpp Creature::addCondition substitui condicao de mesmo
-- tipo+subId) com o valor calculado pro level ATUAL -- chamada no login e a cada level-up
-- (CreatureEvent NarutoRegenAdvance abaixo, mesmo padrao onAdvance(player,skill,old,new) que
-- NarutoAchievementAdvance ja usa pra SKILL_LEVEL). Formulas (replicadas em
-- tools/balance/sim.py chakra_regen_amount_per_tick/hp_regen_amount_per_tick, tunadas por
-- simulacao -- ver relatorio v5): chakra +[3+floor(level/4)] a cada 2s (era +3 a cada 5s pra
-- TODO level); HP +[2+floor(level/10)] a cada 5s (em L1-9 e EXATAMENTE o valor antigo, so
-- acelera a partir de L10 -- pool de HP tambem cresce e o valor fixo ficaria imperceptivel
-- tarde no jogo pelo mesmo motivo do chakra).
local NarutoRegen = {}
function NarutoRegen.apply(player)
	local level = player:getLevel()
	local regen = Condition(CONDITION_REGENERATION, CONDITIONID_DEFAULT)
	regen:setParameter(CONDITION_PARAM_SUBID, 9020)
	regen:setParameter(CONDITION_PARAM_TICKS, -1)
	regen:setParameter(CONDITION_PARAM_HEALTHGAIN, 2 + math.floor(level / 10))
	regen:setParameter(CONDITION_PARAM_HEALTHTICKS, 5000)
	regen:setParameter(CONDITION_PARAM_MANAGAIN, 3 + math.floor(level / 4))
	regen:setParameter(CONDITION_PARAM_MANATICKS, 2000)
	player:addCondition(regen)
end

local regenAdvance = CreatureEvent("NarutoRegenAdvance")
function regenAdvance.onAdvance(player, skill, oldLevel, newLevel)
	if skill == SKILL_LEVEL then
		NarutoRegen.apply(player)
	end
	return true
end
regenAdvance:register()

-- ------------------------------------------------------------------ login
local login = CreatureEvent("NarutoCharacterLogin")
function login.onLogin(player)
	player:registerEvent("NarutoOpcode")
	player:registerEvent("NarutoRegenAdvance")
	local firstTime = player:getStorageValue(STORAGE_ONBOARDED) < 1
	-- Reserva de chakra inicial: o TFS cria o jogador com 0 de mana e as vocacoes dao +10/level,
	-- mas os jutsus tier 1 custam 2,5-3,0% do pool (chakra_cost_percent, rodada 5) -- sem isso
	-- um Genin novo nao consegue lancar NADA ate o level 3. Piso de 110 de chakra (rodada 5, era
	-- 60 -- combinado com o gainmana=10/level da vocacao (inalterado) reproduz exatamente a
	-- curva 100+level*10 de data/progression.json em qualquer level, nao so' no L1). 110*0,03=
	-- ~3 de custo por cast, 36+ casts do pool inicial -- folga generosa sobre o minimo de 4
	-- pedido pela missao — ver relatorio v5 §1.
	if firstTime and player:getMaxMana() < 110 then
		player:setMaxMana(110)
		player:addMana(110)
	end
	-- Regeneracao natural de HP/chakra (playtest r3, 2026-09-05): no TFS a regeneracao so' roda
	-- enquanto o jogador tem comida (Player.feed em lib/core/player.lua). Num jogo de ninja o
	-- chakra volta sozinho -- ver NarutoRegen.apply acima (rodada 5: agora escala com level).
	NarutoRegen.apply(player)
	-- Kit inicial da vila (data/villages.json starting_items): o AAC/TFS criam o jogador so' com
	-- o kit vanilla (bag/jacket). Sem arma o Genin novo morre pros 3 lobos da trilha (playtest
	-- 2026-09-05). addItem com slot WHEREEVER equipa automaticamente o que couber no slot.
	if firstTime then
		local kit = STARTING_KIT[player:getVocation():getId()]
		if kit then
			for _, itemId in ipairs(kit) do player:addItem(itemId, 1) end
		end
	end
	NarutoCharacters.apply(player, nil, nil, {silent = true, force = true, noState = true})
	local pid = player:getId()
	-- ~1s depois de entrar: o cliente ja carregou os modulos e escuta o opcode 210
	addEvent(function()
		local p = Player(pid)
		if p then NarutoCharacters.sendState(p, firstTime) end
	end, 1000)
	return true
end
login:register()

-- ------------------------------------------------------------------ talkactions
--- Normaliza para comparar nomes/ids sem acento e sem espaco (!personagem "genin uchiha").
local function normalize(s)
	s = tostring(s):lower():gsub("%s+", "_")
	local map = { ['\195\161']='a', ['\195\160']='a', ['\195\163']='a', ['\195\162']='a',
		['\195\169']='e', ['\195\170']='e', ['\195\173']='i', ['\195\179']='o',
		['\195\181']='o', ['\195\180']='o', ['\195\186']='u', ['\195\167']='c' }
	for accented, plain in pairs(map) do s = s:gsub(accented, plain) end
	return s
end

local function findByQuery(candidates, query)
	local q = normalize(query)
	for _, c in ipairs(candidates) do
		if normalize(c.id) == q or normalize(c.name) == q then return c end
	end
	return nil
end

--- !personagem [nome|id]: jogadores trocam entre os personagens DA PROPRIA vila (GM: qualquer).
local talkChar = TalkAction("!personagem")
function talkChar.onSay(player, words, param)
	local list = NarutoCharacters.list
	if not isGodPlayer(player) then
		list = NarutoCharacters.byVillage[player:getVocation():getId()] or {}
	end
	param = param and param:trim() or ""
	if param == "" then
		local names = {}
		for _, c in ipairs(list) do names[#names + 1] = c.name .. " (" .. c.id .. ")" end
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Personagens: " .. table.concat(names, ", ") .. ". Use !personagem <nome>.")
		return false
	end
	local char = findByQuery(list, param)
	if not char then
		player:sendCancelMessage("Personagem nao encontrado. Use !personagem para ver a lista.")
		return false
	end
	local ok, err = NarutoCharacters.apply(player, char.id, nil, {force = isGodPlayer(player)})
	if not ok then player:sendCancelMessage(err) end
	return false
end
talkChar:separator(" ")
talkChar:register()

--- !elemento [katon|suiton|raiton|doton|fuuton]
local talkElement = TalkAction("!elemento")
function talkElement.onSay(player, words, param)
	param = param and param:trim() or ""
	if param == "" then
		local names = {}
		for _, e in ipairs(NarutoElements.list) do names[#names + 1] = e.id end
		local cur = NarutoCharacters.currentElement(player)
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Elemento atual: " .. (cur and cur.name or "nenhum") ..
			". Disponiveis: " .. table.concat(names, ", ") .. ". Use !elemento <nome>.")
		return false
	end
	local el = findByQuery(NarutoElements.list, param)
	if not el then
		player:sendCancelMessage("Elemento nao encontrado. Use !elemento para ver a lista.")
		return false
	end
	local ok, err = NarutoCharacters.apply(player, nil, el.id, {force = true})
	if not ok then player:sendCancelMessage(err) end
	return false
end
talkElement:separator(" ")
talkElement:register()
