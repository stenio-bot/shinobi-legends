-- Retry rapido do teste de gate (a Serpente Branca no Ninho, perto da
-- Floresta da Morte, agride a distancia e a 1a tentativa morreu antes de
-- pisar no tile do gate). Personagem reposicionado 1 tile a oeste do gate
-- (1199,1020) via SQL; aqui so' 1 passo pra leste + screenshot imediato.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'teste'
local PASSWORD = os.getenv('SL_PASSWORD') or 'teste'
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('GATEV3B: ' .. m) end

scheduleEvent(function()
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT)
  field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin()
  log('doLogin enviado (' .. ACCOUNT .. ')')
end, 1500)
scheduleEvent(function()
  if not g_game.isOnline() then
    local ok, err = pcall(CharacterList.doLogin)
    log('CharacterList.doLogin -> ' .. tostring(ok) .. ' ' .. tostring(err))
  end
end, 4500)

connect(g_game, {
  onGameStart = function()
    log('em jogo!')
    scheduleEvent(function()
      local pos = g_game.getLocalPlayer():getPosition()
      log('posicao antes: ' .. pos.x .. ',' .. pos.y .. ',' .. pos.z)
      shot('mapa_v3_20b_gate_teste_antes.png')
      g_game.walk(East)
    end, 300)
    scheduleEvent(function()
      local pos = g_game.getLocalPlayer():getPosition()
      log('posicao depois: ' .. pos.x .. ',' .. pos.y .. ',' .. pos.z)
      shot('mapa_v3_21b_gate_teste_depois.png')
    end, 900)
    scheduleEvent(function() log('RETRY COMPLETO') end, 1400)
  end
})

connect(g_game, {
  onTextMessage = function(mode, text)
    log('MSG(' .. tostring(mode) .. '): ' .. tostring(text))
  end
})
