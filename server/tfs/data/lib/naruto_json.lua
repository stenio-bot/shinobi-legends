-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/lib/naruto_json.lua e adicione
-- `dofile('data/lib/naruto_json.lua')` em data/lib/lib.lua.
--
-- NarutoJson.encode(valor) -> string   |  NarutoJson.decode(string) -> valor, err
-- Arrays vs objetos: uma table com t[1] ~= nil vira array; table vazia vira {} (objeto).
-- Use NarutoJson.array({}) para for\xE7ar array vazio ([]).
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
			-- ordena as chaves: sa\xEDda determin\xEDstica (facilita diff de log/teste)
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

-- ------------------------------------------------------------------ NarutoText (ponte de encoding)
-- Regressao critica do playtest de historia (2026-09-05, docs/qa/playtest-historia-arcos4-6.md):
-- todo Lua GERADO por este script sai em cp1252 (ver _lua_cp1252 no topo do arquivo Python -- o
-- OTClient renderiza os baloes/chat lendo os bytes das strings Lua como cp1252). Mas os nomes que
-- chegam de dentro do TFS em tempo de execucao (creature:getName(), attacker:getName(),
-- target:getName(), monster:getName()) vem dos atributos `name=` dos XML de monstro/npc, que
-- CONTINUAM em UTF-8 (nunca reescritos por _lua_cp1252 -- so o Lua gerado passa por ele). Ou seja,
-- duas sequencias de bytes diferentes para o mesmo texto visual (ex.: "Aguia do Trovao" com acento
-- vira '\xC1guia do Trov\xE3o' no Lua gerado mas continua '\xC3\x81guia do Trov\xc3\xa3o' -- UTF-8
-- -- vindo de target:getName()); qualquer comparacao byte-a-byte (q.monster == name,
-- PHASES[creature:getName()], etc.) nunca bate para nomes acentuados.
--
-- REGRA (documentada tambem em docs/sistemas/cliente-ux.md): Lua gerado = cp1252 para exibicao;
-- nomes que vem do jogo chegam em UTF-8 -> sempre passar por NarutoText.utf8ToCp1252(...) ANTES de
-- comparar/indexar contra um literal gerado (q.monster, PHASES, t.monster, entry.monster,
-- a.monsterName etc.). Na direcao inversa -- um nome gerado (cp1252) que precisa voltar pro TFS,
-- ex. Game.createMonster(nome) de um summon com acento -- usar NarutoText.cp1252ToUtf8(...) (o TFS
-- casa nomes de monstro por bytes; um nome cp1252 nao acha o MonsterType cujo `name=` e' UTF-8).
--
-- Implementacao em Lua 5.1/LuaJIT puro (sem a lib `utf8`, que so existe a partir do Lua 5.3):
-- decodifica/codifica byte a byte, validando os bytes de continuacao UTF-8 (10xxxxxx) -- um byte
-- que nao forma uma sequencia UTF-8 valida (ex.: uma string JA em cp1252, como os literais gerados
-- passados de volta por engano) passa direto, sem alterar. Code points sem par exato em cp1252
-- (fora de U+00A0-U+00FF e fora da tabela de pontuacao "esperta" abaixo) viram '?' (mesmo fallback
-- de `str.encode('cp1252', errors='replace')` do lado Python). NAO mexe nas mensagens exibidas
-- (essas continuam cp1252 puro, geradas por _lua_cp1252 -- ver topo do arquivo).
NarutoText = {}

-- Bloco 0x80-0x9F de cp1252 diverge de Latin-1/UTF-8 direto (sao os "C1 controls" do Unicode ali
-- substituidos por pontuacao tipografica); os demais bytes acentuados (0xA0-0xFF) sao identicos ao
-- code point Unicode (Latin-1). So' esta tabela extra precisa de mapeamento explicito nos dois
-- sentidos.
local NARUTO_TEXT_UNICODE_TO_CP1252 = {
	[0x2013] = 0x96, [0x2014] = 0x97,
	[0x2018] = 0x91, [0x2019] = 0x92,
	[0x201C] = 0x93, [0x201D] = 0x94,
	[0x2026] = 0x85,
}
local NARUTO_TEXT_CP1252_TO_UNICODE = {
	[0x96] = 0x2013, [0x97] = 0x2014,
	[0x91] = 0x2018, [0x92] = 0x2019,
	[0x93] = 0x201C, [0x94] = 0x201D,
	[0x85] = 0x2026,
}

--- Decodifica `s` (bytes UTF-8, ex.: vindo de creature:getName()) para bytes cp1252 (o encoding
--- dos literais deste Lua gerado). Idempotente o suficiente pra aceitar por engano uma string que
--- ja estava em cp1252 (os bytes acentuados de cp1252, todos >= 0xA0, quase nunca formam uma
--- sequencia de continuacao UTF-8 valida -- ver bytes soltos abaixo).
function NarutoText.utf8ToCp1252(s)
	if type(s) ~= 'string' then return s end
	local byte, char = string.byte, string.char
	local out, i, n = {}, 1, #s
	while i <= n do
		local b1 = byte(s, i)
		local cp, len
		if b1 < 0x80 then
			cp, len = b1, 1
		elseif b1 >= 0xC2 and b1 <= 0xDF and i + 1 <= n then
			local b2 = byte(s, i + 1)
			if b2 and b2 >= 0x80 and b2 <= 0xBF then
				cp, len = (b1 - 0xC0) * 0x40 + (b2 - 0x80), 2
			end
		elseif b1 >= 0xE0 and b1 <= 0xEF and i + 2 <= n then
			local b2, b3 = byte(s, i + 1), byte(s, i + 2)
			if b2 and b3 and b2 >= 0x80 and b2 <= 0xBF and b3 >= 0x80 and b3 <= 0xBF then
				cp, len = (b1 - 0xE0) * 0x1000 + (b2 - 0x80) * 0x40 + (b3 - 0x80), 3
			end
		elseif b1 >= 0xF0 and b1 <= 0xF4 and i + 3 <= n then
			local b2, b3, b4 = byte(s, i + 1), byte(s, i + 2), byte(s, i + 3)
			if b2 and b3 and b4 and b2 >= 0x80 and b2 <= 0xBF and b3 >= 0x80 and b3 <= 0xBF and b4 >= 0x80 and b4 <= 0xBF then
				cp, len = 0x10000, 4  -- >= 0x10000: fora do BMP, sem representacao em cp1252 -> '?'
			end
		end
		if not cp then
			-- lead byte invalido ou continuacao faltando: byte solto (provavelmente ja cp1252
			-- ou puro ASCII de controle) -- passa direto, sem tentar reinterpretar.
			out[#out + 1] = char(b1)
			i = i + 1
		else
			if cp < 0x80 or (cp >= 0xA0 and cp <= 0xFF) then
				out[#out + 1] = char(cp)
			else
				local specialByte = NARUTO_TEXT_UNICODE_TO_CP1252[cp]
				out[#out + 1] = specialByte and char(specialByte) or '?'
			end
			i = i + len
		end
	end
	return table.concat(out)
end

--- Inversa: bytes cp1252 (ex.: um nome vindo de uma tabela gerada, como PHASES[...].summons[i].name)
--- para bytes UTF-8 (o encoding que o TFS espera pra casar com o `name=` do monster/npc XML, ex.
--- Game.createMonster).
function NarutoText.cp1252ToUtf8(s)
	if type(s) ~= 'string' then return s end
	local byte, char = string.byte, string.char
	local out, i, n = {}, 1, #s
	while i <= n do
		local b = byte(s, i)
		local special = NARUTO_TEXT_CP1252_TO_UNICODE[b]
		if special then
			out[#out + 1] = char(0xE0 + math.floor(special / 0x1000),
				0x80 + math.floor(special % 0x1000 / 0x40), 0x80 + special % 0x40)
		elseif b < 0x80 then
			out[#out + 1] = char(b)
		elseif b >= 0xA0 and b <= 0xFF then
			out[#out + 1] = char(0xC0 + math.floor(b / 0x40), 0x80 + b % 0x40)
		else
			-- 0x80-0x9F fora da tabela especial: nao usado pelos textos deste jogo -- mantem o
			-- byte cru em vez de arriscar um par UTF-8 errado.
			out[#out + 1] = char(b)
		end
		i = i + 1
	end
	return table.concat(out)
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
