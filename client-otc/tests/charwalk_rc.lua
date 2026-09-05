-- TEMPORARIO: teste in-game do ciclo de andar (costas/perfil/frente) dos
-- personagens MUGEN + outfit do jogador. Copiado para client-otc/shinobirc.lua
-- e REMOVIDO no fim do teste (ver missao "melhorar forma de andar").
--
-- Para cada looktype da lista: troca o outfit NO CLIENTE (setOutfit; o
-- /looktype do TFS recusa id >= 903 — quem desenha/anima e o cliente, e o
-- suficiente pra conferir a arte), anda 6 passos em cada uma das 4 direcoes e
-- tira 3 screenshots por direcao a ~150ms de intervalo DURANTE o movimento ->
-- screenshots/walk_<looktype>_<dir>_<i>.png (dir = n/l/s/o).
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'god'
local PASSWORD = os.getenv('SL_PASSWORD') or 'god'
local LOOKS = {128, 900, 901, 902, 903, 906, 909, 913}
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('CHARWALK: ' .. tostring(m)) end

scheduleEvent(function()
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT)
  field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin()
  log('doLogin ' .. ACCOUNT)
end, 2500)
scheduleEvent(function()
  if not g_game.isOnline() then pcall(CharacterList.doLogin) end
end, 7000)

connect(g_game, {
  onGameStart = function()
    log('em jogo')
    local t = 2500
    local function at(ms, fn) scheduleEvent(fn, t + ms) end
    -- praca do templo (zona de protecao, sem monstros) em vez de /arena: um
    -- "Sapo Ancião" sobrevivente de rodadas anteriores de autotest_rc.lua
    -- ficou parado na arena e PARALISAVA o jogador ao teleportar (1a rodada
    -- deste teste flagrou isso — corrigido usando um lugar garantidamente
    -- livre de bicho em vez de reusar /arena).
    at(0, function() g_game.talk('/tp 1029,1050,7') end)
    at(600, function()
      local mp = modules.game_interface.getMapPanel()
      pcall(function() mp:zoomIn() end)
    end)
    local STEP = 500
    local DIRS = {{North, 'n'}, {East, 'l'}, {South, 's'}, {West, 'o'}}
    local ms = 1400
    for _, lt in ipairs(LOOKS) do
      local L = lt
      at(ms, function()
        local pl = g_game.getLocalPlayer()
        local o = pl:getOutfit(); o.type = L; o.addons = 0; pl:setOutfit(o)
        log('looktype ' .. L .. ' -> ' .. tostring(pl:getOutfit().type))
      end)
      ms = ms + 500
      at(ms, function() g_app.doScreenshot(string.format('walk_%d_parado.png', L)) end)
      ms = ms + 300
      for _, d in ipairs(DIRS) do
        local dir, tag = d[1], d[2]
        local base = ms
        for step = 0, 5 do
          at(base + step * STEP, function() g_game.walk(dir) end)
        end
        at(base + 150, function() g_app.doScreenshot(string.format('walk_%d_%s_1.png', L, tag)) end)
        at(base + 300, function() g_app.doScreenshot(string.format('walk_%d_%s_2.png', L, tag)) end)
        at(base + 450, function() g_app.doScreenshot(string.format('walk_%d_%s_3.png', L, tag)) end)
        ms = ms + 6 * STEP + 200
      end
      ms = ms + 300
    end
    at(ms + 500, function() log('fim'); g_app.exit() end)
  end,
  onLoginError = function(m) log('onLoginError ' .. tostring(m)) end,
  onConnectionError = function(m, c) log('onConnectionError ' .. tostring(m)) end,
})
scheduleEvent(function() log('timeout'); g_app.exit() end, 220000)
