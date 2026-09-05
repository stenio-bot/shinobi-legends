-- Stub mínimo das APIs do TFS 1.4.2 (revscriptsys + npcsystem) usado pelos testes headless em
-- tools/tests/test_quests_headless.lua. Roda em luajit puro (sem TFS de verdade instalado) —
-- mesmo espírito dos testes headless da missão de Conquistas (git log --grep=Conquistas), que
-- não deixaram um arquivo de teste no repo; este é o primeiro a ficar comitado.
--
-- Objetivo: dofile() os arquivos REAIS gerados por tools/export_tfs.py (server/generated/lib/
-- naruto_quests.lua, scripts/naruto/quests_kill.lua, um npc/scripts/naruto/*.lua) sem precisar do
-- servidor rodando, capturando os CreatureEvent/GlobalEvent/TalkAction/keywords registrados para
-- poder chamá-los diretamente nos testes.

local M = {}

-- ------------------------------------------------------------------ registros (pra teste chamar)
M.creatureEvents = {}   -- name -> {onKill=fn, onLogin=fn, onAdvance=fn}
M.globalEvents = {}     -- name -> {onThink=fn, interval=n}
M.talkActions = {}      -- words -> {onSay=fn}
M.players = {}          -- id -> player stub (Player(id) resolve por aqui)

-- ------------------------------------------------------------------ Player stub
local PlayerMeta = {}
PlayerMeta.__index = PlayerMeta

local nextPlayerId = 1

function M.newPlayer(name, opts)
	opts = opts or {}
	local id = nextPlayerId
	nextPlayerId = nextPlayerId + 1
	local p = setmetatable({
		_id = id, _name = name or ("Player" .. id), _level = opts.level or 1,
		_storage = {}, _items = {}, _pos = opts.pos or {x = 1000, y = 1000, z = 7},
		_outfits = {}, _addons = {}, _messages = {}, _exp = 0, _ryo = 0,
	}, PlayerMeta)
	M.players[id] = p
	return p
end

function PlayerMeta:getId() return self._id end
function PlayerMeta:getName() return self._name end
function PlayerMeta:getLevel() return self._level end
function PlayerMeta:isPlayer() return true end
function PlayerMeta:isMonster() return false end

function PlayerMeta:getStorageValue(key)
	local v = self._storage[key]
	if v == nil then return -1 end
	return v
end
function PlayerMeta:setStorageValue(key, value) self._storage[key] = value end

function PlayerMeta:getItemCount(id) return self._items[id] or 0 end
function PlayerMeta:addItem(id, count)
	count = count or 1
	self._items[id] = (self._items[id] or 0) + count
	return true
end
function PlayerMeta:removeItem(id, count)
	count = count or 1
	self._items[id] = math.max(0, (self._items[id] or 0) - count)
	return true
end

function PlayerMeta:addExperience(amount) self._exp = self._exp + amount end
function PlayerMeta:addOutfit(looktype) self._outfits[looktype] = true end
function PlayerMeta:addOutfitAddon(looktype, addon) self._addons[looktype] = addon end

function PlayerMeta:getPosition() return self._pos end
function PlayerMeta:setPosition(pos) self._pos = pos end

function PlayerMeta:sendTextMessage(kind, msg) self._messages[#self._messages + 1] = msg end
function PlayerMeta:sendCancelMessage(msg) self._messages[#self._messages + 1] = msg end

function PlayerMeta:addCondition(cond) self._lastCondition = cond end
function PlayerMeta:removeCondition() end
function PlayerMeta:registerEvent(name) end
function PlayerMeta:getVocation() return {getId = function() return 1 end} end

-- posição também precisa responder sendMagicEffect (NarutoRanks.promote chama
-- player:getPosition():sendMagicEffect(...)) — anexa no próprio objeto de posição.
local function withMagicEffect(pos)
	pos.sendMagicEffect = function() end
	return pos
end
local origNewPlayer = M.newPlayer
function M.newPlayer(name, opts)
	local p = origNewPlayer(name, opts)
	withMagicEffect(p._pos)
	return p
end

-- ------------------------------------------------------------------ globais do TFS usados aqui
function Player(idOrCid)
	return M.players[idOrCid]
end

function Condition(kind, id)
	return {kind = kind, id = id, params = {}, setParameter = function(self, k, v) self.params[k] = v end}
end

CONDITION_ATTRIBUTES = 1
CONDITIONID_DEFAULT = 1
CONDITION_PARAM_TICKS = 1
CONDITION_PARAM_SUBID = 2
CONDITION_PARAM_STAT_MAXHITPOINTS = 3
CONDITION_PARAM_STAT_MAXMANAPOINTS = 4
CONDITION_PARAM_SKILL_SHIELD = 5
MESSAGE_EVENT_ADVANCE = 1
MESSAGE_INFO_DESCR = 2
MESSAGE_GREET = 3
CONST_ME_FIREWORK_YELLOW = 1

function CreatureEvent(name)
	local ev = {}
	function ev:register() M.creatureEvents[name] = self end
	return ev
end

function GlobalEvent(name)
	local ev = {interval_ms = 0}
	function ev:interval(ms) self.interval_ms = ms end
	function ev:register() M.globalEvents[name] = self end
	return ev
end

function TalkAction(word)
	local ta = {}
	function ta:separator() end
	function ta:register() M.talkActions[word] = self end
	return ta
end

Game = {getPlayers = function()
	local list = {}
	for _, p in pairs(M.players) do list[#list + 1] = p end
	return list
end}

-- ------------------------------------------------------------------ npcsystem stub (bem simples:
-- só o suficiente pra dofile de npc/scripts/naruto/*.lua funcionar e capturar callbacks de
-- keyword pra chamar direto nos testes).
NpcSystem = {parseParameters = function() end}

FocusModule = {new = function() return {} end}

ShopModule = {}
function ShopModule:new()
	return setmetatable({}, {__index = {
		addBuyableItem = function() end,
		addSellableItem = function() end,
	}})
end

-- Cada npc/scripts/naruto/<id>.lua gerado cria SEU PRÓPRIO `local keywordHandler`/`npcHandler` no
-- topo do arquivo (não exposto globalmente) — como os testes fazem dofile() de UM script de npc
-- por vez, o stub guarda a ÚLTIMA instância criada em M.lastKeywordHandler/lastNpcHandler logo
-- após o dofile retornar, e o teste lê essas globais pra disparar keywords diretamente.
KeywordHandler = {}
function KeywordHandler:new()
	local obj = setmetatable({keywords = {}}, {__index = {
		addKeyword = function(self, keys, callback, params)
			local kw = keys[1]
			self.keywords[kw] = self.keywords[kw] or {}
			table.insert(self.keywords[kw], callback)
		end,
	}})
	M.lastKeywordHandler = obj
	return obj
end

NpcHandler = {}
function NpcHandler:new(kh)
	local obj = setmetatable({keywordHandler = kh, focused = true, lastSaid = {}}, {__index = {
		isFocused = function(self) return self.focused end,
		say = function(self, msg, cid) self.lastSaid[cid or 0] = msg end,
		setMessage = function() end,
		addModule = function() end,
		onCreatureAppear = function() end,
		onCreatureDisappear = function() end,
		onThink = function() end,
		onCreatureSay = function(self, cid, kind, msg)
			local kws = self.keywordHandler.keywords[msg]
			if kws then
				for _, cb in ipairs(kws) do
					if cb(cid, msg, {msg}, {}, nil) then return true end
				end
			end
			return false
		end,
	}})
	M.lastNpcHandler = obj
	return obj
end

--- Helper de teste: dispara a keyword `word` no keywordHandler capturado (M.lastKeywordHandler
--- logo após o dofile do script do npc) — chama, em ordem, cada callback registrado para essa
--- keyword até um retornar true (mesma semântica de fallthrough do keywordhandler.lua real do
--- TFS, ver server/tfs/data/npc/lib/npcsystem/keywordhandler.lua:processNodeMessage).
function M.sayKeyword(keywordHandlerObj, word, cid)
	local kws = keywordHandlerObj.keywords[word]
	if not kws then return nil end
	for _, cb in ipairs(kws) do
		local ok = cb(cid, word, {word}, {}, nil)
		if ok then return true end
	end
	return false
end

return M
