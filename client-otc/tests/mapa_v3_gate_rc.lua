-- Teste do gate de rank (Missão A.2): conta teste/teste (Genin comum,
-- personagem Naruto) tenta entrar na Ruinas do Cla Marionetista (gate
-- actionid 45002, exige Chunin) e deve ser barrado com mensagem + teleport
-- de volta. Copiado para client-otc/shinobirc.lua, removido ao final.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'teste'
local PASSWORD = os.getenv('SL_PASSWORD') or 'teste'
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('GATEV3: ' .. m) end

scheduleEvent(function()
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT)
  field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin()
  log('doLogin enviado (' .. ACCOUNT .. ')')
end, 2000)
scheduleEvent(function()
  if not g_game.isOnline() then
    local ok, err = pcall(CharacterList.doLogin)
    log('CharacterList.doLogin -> ' .. tostring(ok) .. ' ' .. tostring(err))
  end
end, 6000)

connect(g_game, {
  onGameStart = function()
    log('em jogo! rank do personagem ainda deve ser Genin (conta comum)')
    local t = 1500
    local function at(ms, fn) scheduleEvent(fn, t + ms) end
    -- anda ate perto da entrada das Ruinas (gate em x=1200, y=1020/1021) por
    -- fora do noclip (conta comum, sem /god) — usa autoWalk em saltos curtos
    -- (ver docs/sistemas/mapas.md#auditoria-dinamica) partindo de dentro da
    -- Floresta da Morte, ja perto do portao leste.
    at(0, function() g_game.talk('/pos') end)
    at(500, function()
      local pos = g_game.getLocalPlayer():getPosition()
      log('posicao inicial: ' .. pos.x .. ',' .. pos.y .. ',' .. pos.z)
      shot('mapa_v3_19_gate_teste_pos_inicial.png')
    end)
    at(1200, function()
      -- autoWalk ate o marcador de gate (1201,1020) — 1 tile antes da linha do gate,
      -- depois mais um passo manual pro leste pra pisar de fato no actionid.
      local ok = g_game.autoWalk({x = 1201, y = 1020, z = 7})
      log('autoWalk -> ' .. tostring(ok))
    end)
    at(9000, function()
      local pos = g_game.getLocalPlayer():getPosition()
      log('posicao apos autoWalk: ' .. pos.x .. ',' .. pos.y .. ',' .. pos.z)
      shot('mapa_v3_20_gate_teste_antes.png')
    end)
    at(9500, function() g_game.walk(East) end)
    at(10500, function() g_game.walk(East) end)
    at(11500, function()
      local pos = g_game.getLocalPlayer():getPosition()
      log('posicao apos tentar atravessar: ' .. pos.x .. ',' .. pos.y .. ',' .. pos.z)
      shot('mapa_v3_21_gate_teste_depois.png')
    end)
    at(12500, function() log('TESTE DE GATE COMPLETO') end)
  end
})

connect(g_game, {
  onTextMessage = function(mode, text)
    log('MSG(' .. tostring(mode) .. '): ' .. tostring(text))
  end
})
