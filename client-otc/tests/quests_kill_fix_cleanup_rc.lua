-- Varredura final: mata qualquer monstro orfao deixado pelos testes de encoding
-- (rodadas recheck2/3/4) nos 3 cantos usados -- Camara do Xama (1244,1013,7),
-- Salao do Marionetista (1246,1032,7) e canto do Covil (1449,1005,7). Não
-- depende de nome (mesma licao das rodadas anteriores: getName() pos-fix vem em
-- cp1252) -- so' ataca qualquer isMonster() visivel em cada canto ate a area
-- ficar vazia.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function log(m) g_logger.info('QKCLEAN: ' .. tostring(m)) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end

scheduleEvent(function()
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT)
  field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin()
end, 2500)
scheduleEvent(function()
  if not g_game.isOnline() then pcall(CharacterList.doLogin) end
end, 7000)

local queue = {}
local function enqueue(fn) table.insert(queue, fn) end
local function runNext()
  if #queue == 0 then log('SEQUENCIA COMPLETA'); scheduleEvent(function() g_app.exit() end, 2000); return end
  local fn = table.remove(queue, 1)
  local ok, err = pcall(fn, runNext)
  if not ok then log('ERRO: ' .. tostring(err)); scheduleEvent(runNext, 300) end
end
local function say(msg, delay) return function(nextFn) g_game.talk(msg); scheduleEvent(nextFn, delay or 500) end end
local function tp(x, y, z) return say('/tp ' .. x .. ',' .. y .. ',' .. z, 900) end

local function nearbyMonsters()
  local list = {}
  local p = g_game.getLocalPlayer()
  if not p then return list end
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() then table.insert(list, c) end
  end
  return list
end

--- Mata tudo que estiver isMonster() por perto, em serie, ate a area ficar
--- vazia (ou timeout). tag so' pra log.
local function clearArea(tag, timeoutMs)
  return function(nextFn)
    local mons = nearbyMonsters()
    log(tag .. ': ' .. #mons .. ' monstro(s) visivel(is)')
    if #mons == 0 then nextFn(); return end
    local elapsed = 0
    local function poll()
      local mons2 = nearbyMonsters()
      if #mons2 == 0 then log(tag .. ': area limpa'); nextFn(); return end
      for _, m in ipairs(mons2) do g_game.attack(m) end
      elapsed = elapsed + 600
      if elapsed >= (timeoutMs or 60000) then
        log(tag .. ': TIMEOUT, ainda restam ' .. #mons2 .. ' monstro(s)')
        nextFn()
        return
      end
      scheduleEvent(poll, 600)
    end
    poll()
  end
end

connect(g_game, {
  onGameStart = function()
    log('em jogo')
    enqueue(say('/god', 900))
    enqueue(say('/full', 600))
    enqueue(tp(1244, 1013, 7))
    enqueue(clearArea('camara_xama', 40000))
    enqueue(tp(1246, 1032, 7))
    enqueue(clearArea('salao_marionetista', 40000))
    enqueue(tp(1449, 1005, 7))
    enqueue(clearArea('covil_canto', 40000))
    enqueue(function(nextFn) g_game.safeLogout(); scheduleEvent(nextFn, 1500) end)
    scheduleEvent(runNext, 1500)
  end,
  onTextMessage = function(mode, text) log('msg(' .. tostring(mode) .. '): ' .. tostring(text)) end,
  onLoginError = function(m) log('onLoginError ' .. tostring(m)) end,
  onConnectionError = function(m, c) log('onConnectionError ' .. tostring(m)) end,
})
scheduleEvent(function() log('TIMEOUT GERAL'); g_app.exit() end, 150000)
