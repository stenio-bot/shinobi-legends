-- Verificacao in-game do redesenho de Lobo (940) e Cervo (941) N/S (missao:
-- poses de frente/costas pareciam boneco bipede cor de pele). Copiado para
-- client-otc/shinobirc.lua e removido ao final (nunca comitado).
-- Login slqa/slqa123 (conta GM ja existente) -> /tp 1050,1012,7 (Bosque
-- Norte, lobos reais patrulhando) -> screenshots -> /m Cervo (cervo de
-- teste, so briga se atacado) -> ataca + circula pra forcar a virar em
-- direcoes diferentes -> screenshots -> logout seguro.
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('ANIMAISV2: ' .. m) end

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
    at(600, function() log('pos apos tp: ' .. tostring(g_game.getLocalPlayer():getPosition())) end)
    at(1200, function() shot('animais_v2_01_lobos_selvagens.png') end)
    at(3200, function() shot('animais_v2_02_lobos_selvagens_b.png') end)

    -- cervo de teste: sempre no MESMO looktype/direcao inicial, controlamos
    -- a direcao ATACANDO de posicoes diferentes (o monstro vira pro alvo).
    at(4000, function() g_game.talk('/m Cervo') end)
    at(4600, function() shot('animais_v2_03_cervo_spawn.png') end)
    at(5200, function()
      local m = nearestMonster('Cervo')
      if m then g_game.attack(m); log('ataque 1 (cervo deve virar p/ o jogador)') else log('cervo nao encontrado') end
    end)
    at(5900, function() shot('animais_v2_04_cervo_direcao1.png') end)
    at(6300, function() g_game.walk(East) end)
    at(6900, function() g_game.walk(North) end)
    at(7500, function()
      local m = nearestMonster('Cervo')
      if m then g_game.attack(m); log('ataque 2 (novo angulo)') end
    end)
    at(8200, function() shot('animais_v2_05_cervo_direcao2.png') end)
    at(8600, function() g_game.walk(West) end)
    at(9200, function() g_game.walk(West) end)
    at(9800, function()
      local m = nearestMonster('Cervo')
      if m then g_game.attack(m); log('ataque 3 (novo angulo)') end
    end)
    at(10500, function() shot('animais_v2_06_cervo_direcao3.png') end)

    at(11500, function() g_game.talk('/pos') end)
    at(12000, function() g_game.safeLogout() end)
    at(13000, function() g_app.exit() end)
  end,
  onLoginError = function(msg) log('onLoginError ' .. tostring(msg)) end,
  onConnectionError = function(msg, code) log('onConnectionError ' .. tostring(msg) .. ' ' .. tostring(code)) end,
  onTextMessage = function(mode, text) log('msg: ' .. tostring(text)) end,
})

scheduleEvent(function() log('timeout'); g_app.exit() end, 45000)
