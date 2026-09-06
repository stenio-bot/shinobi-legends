-- Rodada 2: mesma missao (Lobo 940 / Cervo 941), agora tentando capturar
-- FRENTE e PERFIL de verdade (rodada 1 só pegou costas — lobos/cervo
-- ficaram parados de costas p/ o jogador o tempo todo). Ataca o alvo (o
-- lobo e agressivo, o cervo so briga se atacado) e da tempo (1.8s) pro
-- servidor processar o contra-ataque, que faz o bicho VIRAR pro jogador.
-- Copiado para client-otc/shinobirc.lua e removido ao final.
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('ANIMAISV2B: ' .. m) end

scheduleEvent(function()
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText('slqa')
  field('accountPasswordTextEdit'):setText('slqa123')
  EnterGame.doLogin()
  log('doLogin enviado (slqa)')
end, 2500)
scheduleEvent(function()
  if not g_game.isOnline() then
    local ok, err = pcall(CharacterList.doLogin)
    log('CharacterList.doLogin -> ' .. tostring(ok) .. ' ' .. tostring(err))
  end
end, 7000)

local function nearestMonster(nameFilter)
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  local best, bestd = nil, 99
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() and (not nameFilter or c:getName() == nameFilter) then
      local d = math.max(math.abs(c:getPosition().x - p:getPosition().x), math.abs(c:getPosition().y - p:getPosition().y))
      if d < bestd then best, bestd = c, d end
    end
  end
  return best
end

connect(g_game, {
  onGameStart = function()
    log('em jogo!')
    local t = 2000
    local function at(ms, fn) scheduleEvent(fn, t + ms) end

    at(0, function() g_game.talk('/tp 1050,1012,7') end)
    at(1000, function()
      local m = nearestMonster('Lobo')
      if m then g_game.attack(m); log('lobo atacado, dist inicial') else log('lobo nao encontrado') end
    end)
    at(2800, function() shot('animais_v2_01_lobo_frente.png') end)  -- deve virar p/ o jogador (contra-ataque)
    at(3200, function() g_game.cancelAttackAndFollow() end)
    at(3600, function() g_game.walk(East) end)
    at(4200, function() g_game.walk(East) end)
    at(4800, function()
      local m = nearestMonster('Lobo')
      if m then g_game.attack(m); log('lobo atacado, 2o angulo') else log('lobo nao encontrado (2)') end
    end)
    at(6600, function() shot('animais_v2_02_lobo_perfil.png') end)
    at(7000, function() g_game.cancelAttackAndFollow() end)

    at(7500, function() g_game.talk('/m Cervo') end)
    at(8100, function() shot('animais_v2_03_cervo_costas.png') end)
    at(8600, function()
      local m = nearestMonster('Cervo')
      if m then g_game.attack(m); log('cervo atacado') else log('cervo nao encontrado') end
    end)
    at(10400, function() shot('animais_v2_04_cervo_frente.png') end)
    at(10800, function() g_game.cancelAttackAndFollow() end)
    at(11200, function() g_game.walk(South) end)
    at(11800, function() g_game.walk(West) end)
    at(12400, function()
      local m = nearestMonster('Cervo')
      if m then g_game.attack(m); log('cervo atacado (2o angulo)') end
    end)
    at(14200, function() shot('animais_v2_05_cervo_perfil.png') end)
    at(14600, function() g_game.cancelAttackAndFollow() end)

    at(15200, function() g_game.talk('/pos') end)
    at(15700, function() g_game.safeLogout() end)
    at(16700, function() g_app.exit() end)
  end,
  onLoginError = function(msg) log('onLoginError ' .. tostring(msg)) end,
  onConnectionError = function(msg, code) log('onConnectionError ' .. tostring(msg) .. ' ' .. tostring(code)) end,
  onTextMessage = function(mode, text) log('msg: ' .. tostring(text)) end,
})

scheduleEvent(function() log('timeout'); g_app.exit() end, 40000)
