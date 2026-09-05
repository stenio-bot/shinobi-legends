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

	local state = {
		type = 'state',
		first_time = firstTime == true,
		is_gm = isGm,
		character = char and char.id or NarutoJson.null,
		element = element and element.id or NarutoJson.null,
		level = player:getLevel(),
		village = villageIdOf(player) or NarutoJson.null,
		characters = chars,
		elements = els,
		active_jutsus = active,
	}
	return NarutoJson.sendExtended(player, OPCODE, NarutoJson.encode(state))
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
	end
	return true
end
opcodeEvent:register()

-- ------------------------------------------------------------------ login
local login = CreatureEvent("NarutoCharacterLogin")
function login.onLogin(player)
	player:registerEvent("NarutoOpcode")
	local firstTime = player:getStorageValue(STORAGE_ONBOARDED) < 1
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
