-- Rodada 3: o Lobo (agressivo) e o Cervo (passivo) morrem num unico golpe da
-- conta GM (60/30 hp, dano do personagem GM e maior que isso) -- nao da pra
-- ver o contra-ataque virando de frente sem matar o bicho antes. Aqui NAO
-- ataca: so entra no raio de agro (5) do Lobo e deixa ele perseguir/morder o
-- jogador sozinho (comportamento "aggressive" do data/monsters/forest.json),
-- girando pra frente/perfil sem morrer. Copiado para shinobirc.lua e
-- removido ao final.
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('ANIMAISV2C: ' .. m) end

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

connect(g_game, {
  onGameStart = function()
    log('em jogo!')
    local t = 2000
    local function at(ms, fn) scheduleEvent(fn, t + ms) end

    -- 1050,1012: ponto ja confirmado com 2 lobos reais por perto (rodada 1).
    at(0, function() g_game.talk('/tp 1050,1012,7') end)
    at(800, function() shot('animais_v2_01_lobo_aproximando.png') end)
    at(4000, function() shot('animais_v2_02_lobo_frente.png') end)  -- da tempo de agro (raio 5) perseguir sem atacar
    at(5000, function() g_game.walk(East) end)
    at(5600, function() g_game.walk(East) end)
    at(8600, function() shot('animais_v2_03_lobo_perfil.png') end)  -- lobo reorienta pro novo lado, se estiver perseguindo

    at(8000, function() g_game.talk('/m Cervo') end)
    at(8600, function() shot('animais_v2_04_cervo_costas.png') end)  -- parado, sem ser atacado (nao morre)

    at(9500, function() g_game.talk('/pos') end)
    at(10000, function() g_game.safeLogout() end)
    at(11000, function() g_app.exit() end)
  end,
  onLoginError = function(msg) log('onLoginError ' .. tostring(msg)) end,
  onConnectionError = function(msg, code) log('onConnectionError ' .. tostring(msg) .. ' ' .. tostring(code)) end,
  onTextMessage = function(mode, text) log('msg: ' .. tostring(text)) end,
})

scheduleEvent(function() log('timeout'); g_app.exit() end, 30000)
