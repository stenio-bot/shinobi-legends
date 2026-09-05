-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/scripts/naruto/character_switch.lua (revscriptsys carrega sozinho).
-- Depende de NarutoCharacters (data/lib/naruto_characters.lua, copiado junto com
-- naruto_villages.lua -- ver README.md deste pacote se faltar no seu data/lib/).
--
-- NarutoCharacters.apply(player, looktype, opts): troca de PERSONAGEM (não de vila/vocação).
--   Valida que o looktype pertence à vila (vocação) do jogador, a menos que opts.force (GM)
--   ou o jogador seja GM (ACCOUNT_TYPE_GOD). Esquece os jutsus de TODOS os personagens
--   (exceto os universais, ex. kawarimi) e aprende só os do personagem escolhido.
local STORAGE_CHARACTER = 60001

local function isGodPlayer(player)
	return player:getGroup():getAccess() and player:getAccountType() >= ACCOUNT_TYPE_GOD
end

function NarutoCharacters.apply(player, looktype, opts)
	opts = opts or {}
	local char = NarutoCharacters.byLook[looktype]
	if not char then
		return false, "Personagem desconhecido."
	end
	if not opts.force and not isGodPlayer(player) and char.village_vocation ~= player:getVocation():getId() then
		return false, "Esse personagem não é da sua vila."
	end
	for jname, _ in pairs(NarutoCharacters.allJutsuNames) do
		player:forgetSpell(jname)
	end
	for _, jname in ipairs(char.jutsus) do
		player:learnSpell(jname)
	end
	local outfit = player:getOutfit()
	outfit.lookType = char.looktype
	player:setOutfit(outfit)
	player:setStorageValue(STORAGE_CHARACTER, char.looktype)
	if not opts.silent then
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Personagem: " .. char.name .. ". Jutsus: " .. table.concat(char.jutsus, ", ") .. ".")
		player:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
	end
	return true
end

--- Reaplica o personagem salvo (storage) no login; se vazio, deixa o village_outfit.lua
--- (que roda no mesmo evento onLogin, tipo "login" é global) aplicar o padrão da vila.
local ev = CreatureEvent("NarutoCharacterLogin")
function ev.onLogin(player)
	local look = player:getStorageValue(STORAGE_CHARACTER)
	if look and look > 0 and NarutoCharacters.byLook[look] then
		NarutoCharacters.apply(player, look, {silent = true, force = true})
	end
	return true
end
ev:register()

--- Normaliza para comparar nomes/ids sem acento e sem espaço (!personagem "genin uchiha").
local function normalize(s)
	s = s:lower():gsub("%s+", "_")
	local map = { ['á']='a', ['à']='a', ['ã']='a', ['â']='a', ['é']='e', ['ê']='e', ['í']='i',
		['ó']='o', ['õ']='o', ['ô']='o', ['ú']='u', ['ç']='c' }
	for accented, plain in pairs(map) do s = s:gsub(accented, plain) end
	return s
end

local function findCharacterByQuery(candidates, query)
	local q = normalize(query)
	for _, c in ipairs(candidates) do
		if normalize(c.id) == q or normalize(c.name) == q then return c end
	end
	return nil
end

--- !personagem [nome|id]: jogadores trocam entre os personagens DA PRÓPRIA vila.
local talk = TalkAction("!personagem")
function talk.onSay(player, words, param)
	local list = NarutoCharacters.byVillage[player:getVocation():getId()] or {}
	param = param and param:trim() or ""
	if param == "" then
		local names = {}
		for _, c in ipairs(list) do table.insert(names, c.name .. " (" .. c.id .. ")") end
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Personagens da sua vila: " .. table.concat(names, ", ") .. ". Use !personagem <nome>.")
		return false
	end
	local char = findCharacterByQuery(list, param)
	if not char then
		player:sendCancelMessage("Personagem não encontrado na sua vila. Use !personagem para ver a lista.")
		return false
	end
	local ok, err = NarutoCharacters.apply(player, char.looktype)
	if not ok then player:sendCancelMessage(err) end
	return false
end
talk:separator(" ")
talk:register()
