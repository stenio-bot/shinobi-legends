-- 4a rodada: só termina O Vigia Ilusório (q_lair_1_illusive_eye, storage 50003),
-- que sobreviveu ao timeout de 45s da rodada 3 (chegou a 59% HP, boss claramente
-- mais resistente que a Marionetista das Ruínas). O boss meio-morto da rodada 3
-- ainda deve estar vivo no canto (1449,1005,7) do Covil -- ataca o que já está lá
-- em vez de invocar outro (evita 2 bosses simultâneos no mesmo canto). timeout
-- generoso (150s) e cura o jogador sempre que precisar (HP alto -- só "farm" de
-- paciência, boss não é ameaça real pro personagem em modo deus).
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('qkfix4_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('QKFIX4: ' .. tostring(m)) end

scheduleEvent(function()
  g_settings.set('autoReconnect', true)
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT)
  field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin()
  log('doLogin ' .. ACCOUNT)
end, 2500)
scheduleEvent(function()
  if not g_game.isOnline() then pcall(CharacterList.doLogin) end
end, 7000)

local queue = {}
local function enqueue(fn) table.insert(queue, fn) end
local function runNext()
  if #queue == 0 then log('SEQUENCIA COMPLETA'); scheduleEvent(function() g_app.exit() end, 3000); return end
  local fn = table.remove(queue, 1)
  local ok, err = pcall(fn, runNext)
  if not ok then log('ERRO no passo: ' .. tostring(err)); scheduleEvent(runNext, 300) end
end

local function say(msg, delay) return function(nextFn) g_game.talk(msg); log('talk: ' .. msg); scheduleEvent(nextFn, delay or 500) end end
local function sayNpc(msg, delay) return function(nextFn) g_game.talkChannel(MessageModes.NpcTo, 0, msg); log('npc: ' .. msg); scheduleEvent(nextFn, delay or 1000) end end
local function shotStep(name, delay) return function(nextFn) shot(name); scheduleEvent(nextFn, delay or 200) end end
local function tp(x, y, z) return say('/tp ' .. x .. ',' .. y .. ',' .. z, 900) end
local function readStorage(id, delay) return say('/storage ' .. id, delay or 1000) end

--- Ataca qualquer monstro visível perto do jogador (deve haver só 1: o Vigia
--- Ilusório meio-morto da rodada anterior). Se não achar nenhum, tenta /m 1x
--- (caso tenha expirado/sumido) antes de desistir.
local function killAnyNearbyMonster(tag, fallbackSpawnName, timeoutMs)
  return function(nextFn)
    local function findAny()
      local p = g_game.getLocalPlayer()
      if not p then return nil end
      for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
        if c:isMonster() then return c end
      end
      return nil
    end
    local function fight(lockedId)
      local elapsed = 0
      local lastLog = 0
      local function poll()
        local m = g_map.getCreatureById(lockedId)
        local p = g_game.getLocalPlayer()
        if not p then log(tag .. ': jogador nil'); nextFn(); return end
        if p:getHealthPercent() < 50 then g_game.talk('/full') end
        if not m then log(tag .. ': alvo morto/sumiu apos ' .. elapsed .. 'ms'); scheduleEvent(nextFn, 1000); return end
        g_game.attack(m)
        elapsed = elapsed + 500
        if elapsed - lastLog >= 5000 then
          lastLog = elapsed
          log(string.format('%s: alvo hp%%=%s | player hp=%d/%d', tag, tostring(m:getHealthPercent()), p:getHealth(), p:getMaxHealth()))
        end
        if elapsed >= (timeoutMs or 150000) then log(tag .. ': TIMEOUT (alvo ainda vivo, hp%=' .. tostring(m:getHealthPercent()) .. ')'); nextFn(); return end
        scheduleEvent(poll, 500)
      end
      poll()
    end
    local existing = findAny()
    if existing then
      log(tag .. ': alvo ja presente (sobrevivente da rodada anterior), id=' .. existing:getId())
      fight(existing:getId())
      return
    end
    log(tag .. ': nenhum monstro por perto -- tentando /m ' .. fallbackSpawnName)
    local before = {}
    do
      local p = g_game.getLocalPlayer()
      if p then for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do if c:isMonster() then before[c:getId()] = true end end end
    end
    g_game.talk('/m ' .. fallbackSpawnName)
    scheduleEvent(function()
      local p = g_game.getLocalPlayer()
      local newId = nil
      if p then
        for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
          if c:isMonster() and not before[c:getId()] then newId = c:getId() break end
        end
      end
      if newId then log(tag .. ': spawnou id=' .. newId); fight(newId)
      else log(tag .. ': nao encontrou nem conseguiu spawnar -- desistindo'); nextFn() end
    end, 1300)
  end
end

connect(g_game, {
  onGameStart = function()
    log('em jogo')
    enqueue(say('/god', 900))
    enqueue(say('/full', 600))
    enqueue(tp(1449, 1005, 7))
    enqueue(shotStep('00_chegada_covil'))
    enqueue(readStorage(50003))
    enqueue(killAnyNearbyMonster('illusive_eye', 'O Vigia Ilusório', 150000))
    enqueue(function(nextFn) scheduleEvent(nextFn, 1500) end)
    enqueue(readStorage(50003))
    enqueue(shotStep('01_illusive_eye_pos_kill'))

    enqueue(tp(1407, 1010, 7))
    enqueue(say('hi', 800))
    enqueue(sayNpc('missao', 1400))
    enqueue(shotStep('02_suzu_missao'))
    enqueue(say('bye', 500))
    enqueue(say('/rank', 1000))
    enqueue(shotStep('03_rank_final'))
    enqueue(say('!conquistas', 1000))
    enqueue(shotStep('04_conquistas_final'))

    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      if p then log(string.format('stats finais: hp %d/%d chakra %d/%d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana())) end
      g_game.safeLogout()
      scheduleEvent(nextFn, 1500)
    end)

    scheduleEvent(runNext, 1500)
  end,
  onDeath = function() log('EVENTO onDeath -- autoReconnect deve reconectar em ~2s') end,
  onTextMessage = function(mode, text) log('msg(' .. tostring(mode) .. '): ' .. tostring(text)) end,
  onTalk = function(name, level, mode, text) log('talk: [' .. tostring(mode) .. '] ' .. tostring(name) .. ': ' .. tostring(text)) end,
  onLoginError = function(m) log('onLoginError ' .. tostring(m)) end,
  onConnectionError = function(m, c) log('onConnectionError ' .. tostring(m)) end,
})
scheduleEvent(function() shot('99_timeout'); log('TIMEOUT GERAL'); g_app.exit() end, 220000)
