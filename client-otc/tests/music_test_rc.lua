-- Teste manual do modulo naruto_music (missao de musica ambiente, 2026-09-05).
-- Copiado para client-otc/shinobirc.lua por uma sessao de teste isolada (NAO usa
-- tools/autotest_client.sh - esse mata TODO OTClient.app com pkill -x, o que mataria
-- sessoes de outros agentes). Remova shinobirc.lua ao terminar.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('MUSICTEST: ' .. m) end

scheduleEvent(function()
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT)
  field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin()
  log('doLogin enviado (' .. ACCOUNT .. ')')
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
    log('naruto_music carregado: ' .. tostring(modules.naruto_sounds and NarutoMusic ~= nil))
    log('enableMusicSound=' .. tostring(g_settings.getBoolean('enableMusicSound', true)) ..
        ' musicSoundVolume=' .. tostring(g_settings.getNumber('musicSoundVolume', 100)))

    local t = 1500
    local function at(ms, fn) scheduleEvent(fn, t + ms) end

    at(0, function() g_game.talk('/god') end)
    at(400, function() g_game.talk('/full') end)
    at(800, function() g_game.cancelAttack() end)
    at(1200, function()
      local p = g_game.getLocalPlayer()
      log('posicao inicial: ' .. p:getPosition().x .. ',' .. p:getPosition().y .. ',' .. p:getPosition().z)
    end)

    -- primeira regiao (spawn = vila da folha) ja deve ter tocado pelo poll imediato
    -- do naruto_music.startPolling(); da 3s de folga (poll a cada 2s) antes do shot.
    at(3000, function() shot('music_01_vila.png') end)

    at(3400, function() g_game.talk('/tp 1150,1050,7') end)  -- Floresta da Morte
    at(6200, function() shot('music_02_floresta_morte.png') end)

    at(6600, function() g_game.talk('/tp 1020,1140,7') end)  -- Costa das Mares
    at(9400, function() end)

    at(9800, function() g_game.talk('/tp 1220,1020,7') end)  -- Ruinas
    at(12600, function() shot('music_03_ruinas.png') end)

    at(13000, function() g_game.talk('/tp 1220,1080,7') end) -- Montanha do Trovao
    at(15800, function() end)

    at(16200, function() g_game.talk('/tp 1015,1010,7') end) -- Floresta da Vila
    at(19000, function() end)

    at(19400, function() g_game.talk('/tp 1420,1020,7') end) -- Covil da Nuvem Vermelha
    at(22200, function() shot('music_04_covil.png') end)

    at(22600, function() g_game.talk('/tp 1030,1050,7') end) -- volta pra Vila
    at(25400, function()
      shot('music_05_volta_vila.png')
      log('teste de regioes concluido')
    end)

    at(26000, function()
      local p = g_game.getLocalPlayer()
      log(string.format('stats finais: hp %d/%d level %d', p:getHealth(), p:getMaxHealth(), p:getLevel()))
      g_game.safeLogout()
    end)
    at(28000, function() g_app.exit() end)
  end,
  onLoginError = function(msg) log('onLoginError ' .. tostring(msg)) end,
  onConnectionError = function(msg, code) log('onConnectionError ' .. tostring(msg) .. ' ' .. tostring(code)) end,
  onTextMessage = function(mode, text) log('msg[' .. tostring(mode) .. ']: ' .. tostring(text)) end,
})
scheduleEvent(function() shot('music_timeout.png'); log('timeout'); g_app.exit() end, 45000)
