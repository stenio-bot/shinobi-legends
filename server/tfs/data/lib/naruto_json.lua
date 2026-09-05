-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/lib/naruto_json.lua e adicione
-- `dofile('data/lib/naruto_json.lua')` em data/lib/lib.lua.
--
-- NarutoJson.encode(valor) -> string   |  NarutoJson.decode(string) -> valor, err
-- Arrays vs objetos: uma table com t[1] ~= nil vira array; table vazia vira {} (objeto).
-- Use NarutoJson.array({}) para forçar array vazio ([]).
NarutoJson = {}

local ARRAY_MT = {__jsonarray = true}
function NarutoJson.array(t)
	return setmetatable(t or {}, ARRAY_MT)
end

--- Sentinela para emitir `null` explicito (Lua nao guarda nil dentro de table).
NarutoJson.null = setmetatable({}, {__tostring = function() return 'null' end})

local ESC = {['"'] = '\\"', ['\\'] = '\\\\', ['\b'] = '\\b', ['\f'] = '\\f',
	['\n'] = '\\n', ['\r'] = '\\r', ['\t'] = '\\t'}

local function escapeChar(c)
	return ESC[c] or string.format('\\u%04x', string.byte(c))
end

local function encodeString(s)
	return '"' .. s:gsub('[%z\1-\31\\"]', escapeChar) .. '"'
end

local function isArray(t)
	if getmetatable(t) == ARRAY_MT then return true end
	if next(t) == nil then return false end
	local n = 0
	for k in pairs(t) do
		if type(k) ~= 'number' then return false end
		n = n + 1
	end
	return n == #t
end

local encodeValue

local function encodeNumber(v)
	if v ~= v or v == math.huge or v == -math.huge then return 'null' end
	if v == math.floor(v) and math.abs(v) < 1e15 then return string.format('%d', v) end
	return string.format('%.6g', v)
end

encodeValue = function(v, out)
	local t = type(v)
	if v == nil or v == NarutoJson.null then
		out[#out + 1] = 'null'
	elseif t == 'boolean' then
		out[#out + 1] = v and 'true' or 'false'
	elseif t == 'number' then
		out[#out + 1] = encodeNumber(v)
	elseif t == 'string' then
		out[#out + 1] = encodeString(v)
	elseif t == 'table' then
		if isArray(v) then
			out[#out + 1] = '['
			for i = 1, #v do
				if i > 1 then out[#out + 1] = ',' end
				encodeValue(v[i], out)
			end
			out[#out + 1] = ']'
		else
			out[#out + 1] = '{'
			local first = true
			-- ordena as chaves: saída determinística (facilita diff de log/teste)
			local keys = {}
			for k in pairs(v) do keys[#keys + 1] = tostring(k) end
			table.sort(keys)
			for _, k in ipairs(keys) do
				local val = v[k]
				if val == nil then val = v[tonumber(k)] end
				if not first then out[#out + 1] = ',' end
				first = false
				out[#out + 1] = encodeString(k)
				out[#out + 1] = ':'
				encodeValue(val, out)
			end
			out[#out + 1] = '}'
		end
	else
		out[#out + 1] = 'null'
	end
end

function NarutoJson.encode(v)
	local out = {}
	encodeValue(v, out)
	return table.concat(out)
end

-- ------------------------------------------------------------------ decode
local function skipWhitespace(s, i)
	local _, j = s:find('^[ \t\r\n]*', i)
	return j + 1
end

local parseValue

local UNESC = {['"'] = '"', ['\\'] = '\\', ['/'] = '/', b = '\b', f = '\f', n = '\n', r = '\r', t = '\t'}

local function parseString(s, i)
	i = i + 1  -- pula a aspa inicial
	local buf = {}
	while true do
		local c = s:sub(i, i)
		if c == '' then return nil, i, 'string sem fechamento' end
		if c == '"' then return table.concat(buf), i + 1 end
		if c == '\\' then
			local e = s:sub(i + 1, i + 1)
			if e == 'u' then
				local hex = s:sub(i + 2, i + 5)
				local code = tonumber(hex, 16)
				if not code then return nil, i, 'escape \\u invalido' end
				-- UTF-8 (o TFS trafega bytes; o cliente decodifica)
				if code < 0x80 then
					buf[#buf + 1] = string.char(code)
				elseif code < 0x800 then
					buf[#buf + 1] = string.char(0xC0 + math.floor(code / 0x40), 0x80 + code % 0x40)
				else
					buf[#buf + 1] = string.char(0xE0 + math.floor(code / 0x1000),
						0x80 + math.floor(code % 0x1000 / 0x40), 0x80 + code % 0x40)
				end
				i = i + 6
			else
				local u = UNESC[e]
				if not u then return nil, i, 'escape invalido: \\' .. e end
				buf[#buf + 1] = u
				i = i + 2
			end
		else
			local nextEsc = s:find('[\\"]', i)
			buf[#buf + 1] = s:sub(i, (nextEsc or (#s + 1)) - 1)
			i = nextEsc or (#s + 1)
		end
	end
end

local function parseNumber(s, i)
	local _, j = s:find('^-?%d+%.?%d*[eE]?[-+]?%d*', i)
	local n = tonumber(s:sub(i, j))
	if not n then return nil, i, 'numero invalido' end
	return n, j + 1
end

parseValue = function(s, i)
	i = skipWhitespace(s, i)
	local c = s:sub(i, i)
	if c == '' then return nil, i, 'fim inesperado' end
	if c == '{' then
		local obj = {}
		i = skipWhitespace(s, i + 1)
		if s:sub(i, i) == '}' then return obj, i + 1 end
		while true do
			i = skipWhitespace(s, i)
			if s:sub(i, i) ~= '"' then return nil, i, 'chave esperada' end
			local k, err
			k, i, err = parseString(s, i)
			if err then return nil, i, err end
			i = skipWhitespace(s, i)
			if s:sub(i, i) ~= ':' then return nil, i, '":" esperado' end
			local v
			v, i, err = parseValue(s, i + 1)
			if err then return nil, i, err end
			obj[k] = v
			i = skipWhitespace(s, i)
			local d = s:sub(i, i)
			if d == '}' then return obj, i + 1 end
			if d ~= ',' then return nil, i, '"," ou "}" esperado' end
			i = i + 1
		end
	elseif c == '[' then
		local arr = NarutoJson.array({})
		i = skipWhitespace(s, i + 1)
		if s:sub(i, i) == ']' then return arr, i + 1 end
		while true do
			local v, err
			v, i, err = parseValue(s, i)
			if err then return nil, i, err end
			arr[#arr + 1] = v
			i = skipWhitespace(s, i)
			local d = s:sub(i, i)
			if d == ']' then return arr, i + 1 end
			if d ~= ',' then return nil, i, '"," ou "]" esperado' end
			i = i + 1
		end
	elseif c == '"' then
		return parseString(s, i)
	elseif s:sub(i, i + 3) == 'true' then
		return true, i + 4
	elseif s:sub(i, i + 4) == 'false' then
		return false, i + 5
	elseif s:sub(i, i + 3) == 'null' then
		return nil, i + 4
	else
		return parseNumber(s, i)
	end
end

--- Decodifica. Devolve (valor) em caso de sucesso ou (nil, mensagem) em caso de erro.
function NarutoJson.decode(str)
	if type(str) ~= 'string' then return nil, 'esperava string' end
	local ok, v, i, err = pcall(parseValue, str, 1)
	if not ok then return nil, tostring(v) end
	if err then return nil, err end
	return v
end

-- ------------------------------------------------------------------ envio (opcode estendido)
-- ARMADILHA do TFS 1.4.2: NetworkMessage::addString (src/networkmessage.cpp) DESCARTA em
-- silencio qualquer string com mais de 8192 bytes. Como Player.sendExtendedOpcode
-- (data/lib/core/player.lua) usa addString, um buffer JSON grande (ex.: o `state` de um GM,
-- que lista TODOS os personagens) chegava ao cliente como um 0x32 sem corpo -- e o OTClient
-- logava "ProtocolGame parse message exception ... InputMessage eof reached".
-- Acima de 8192 bytes escrevemos o u16 de tamanho e os bytes na mao (addByte so checa
-- MAX_BODY_LENGTH = 24576).
local EXTENDED_OPCODE_HEADER = 0x32
local ADDSTRING_LIMIT = 8192
local MAX_BODY = 24000  -- margem sob MAX_BODY_LENGTH (24576)

function NarutoJson.sendExtended(player, opcode, str)
	if not player or not player:isUsingOtClient() then return false end
	local len = #str
	if len > MAX_BODY then
		print(string.format("[naruto] opcode %d: buffer de %d bytes excede o limite do NetworkMessage (%d)",
			opcode, len, MAX_BODY))
		return false
	end
	if len <= ADDSTRING_LIMIT then
		return player:sendExtendedOpcode(opcode, str)
	end
	local msg = NetworkMessage()
	msg:addByte(EXTENDED_OPCODE_HEADER)
	msg:addByte(opcode)
	msg:addU16(len)
	local byte = string.byte
	for i = 1, len do
		msg:addByte(byte(str, i))
	end
	msg:sendToPlayer(player)
	msg:delete()
	return true
end

-- ------------------------------------------------------------------ SFX (opcode 210, acao "sfx")
-- Gancho de audio do cliente (docs/sistemas/audio.md): o OTClient Redemment nao tem
-- callback Lua para "efeito magico visto na tela" (parseMagicEffect e' so C++, nao chama
-- callLuaField nenhum - conferido em src/client/protocolgameparse.cpp), entao o som de
-- jutsu e' avisado pelo SERVIDOR via opcode 210 para o conjurador + quem esta por perto.
-- modules/naruto_menu.lua (dono do opcode 210 no cliente) despacha type == 'sfx' para
-- modules/naruto_sounds.lua.
local SFX_OPCODE = 210

--- Manda {"type":"sfx","id":sfxId} para o conjurador e criaturas/jogadores num raio de
--- `radius` tiles (padrao 7, igual ao alcance de visao normal da tela) ao redor de `pos`.
--- So chega a clientes OTClient (sendExtended ja filtra isUsingOtClient); nao quebra nada
--- se sfxId vier nil (spell sem campo `sfx` no JSON).
function NarutoJson.broadcastSfx(pos, sfxId, radius)
	if not sfxId then return end
	radius = radius or 7
	local payload = NarutoJson.encode({type = 'sfx', id = sfxId})
	for _, spec in ipairs(Game.getSpectators(pos, false, false, radius, radius, radius, radius)) do
		if spec:isPlayer() then
			NarutoJson.sendExtended(spec, SFX_OPCODE, payload)
		end
	end
end
