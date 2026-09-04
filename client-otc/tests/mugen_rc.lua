-- TEMPORARIO: teste in-game dos outfits MUGEN (looktypes 900..926).
-- Copiado para client-otc/shinobirc.lua e REMOVIDO no fim do teste.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'god'
local PASSWORD = os.getenv('SL_PASSWORD') or 'god'
local LOOKS = {900, 901, 906, 911, 913, 922}
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('MUGEN: ' .. tostring(m)) end

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
    at(0, function() g_game.talk('/arena') end)
    at(600, function()
      local mp = modules.game_interface.getMapPanel()
      pcall(function() mp:zoomIn() end)
    end)
    local ms = 1400
    local DIRS = {{North, 'n'}, {East, 'l'}, {South, 's'}, {West, 'o'}}
    for _, lt in ipairs(LOOKS) do
      local L = lt
      at(ms, function()
        -- o /looktype do TFS recusa id >= 903 (talkactions/scripts/looktype.lua,
        -- que nao faz parte deste trabalho). Para CONFERIR A ARTE basta trocar o
        -- outfit no cliente: quem desenha e anima a criatura e ele.
        local pl = g_game.getLocalPlayer()
        local o = pl:getOutfit(); o.type = L; o.addons = 0; pl:setOutfit(o)
        log('looktype ' .. L .. ' -> ' .. tostring(pl:getOutfit().type))
      end)
      ms = ms + 700
      at(ms, function() g_app.doScreenshot(string.format('mugen_%d_parado.png', L)) end)
      ms = ms + 300
      for _, d in ipairs(DIRS) do
        local dir, tag = d[1], d[2]
        at(ms, function() g_game.walk(dir) end)
        at(ms + 110, function()
          g_app.doScreenshot(string.format('mugen_%d_%s1.png', L, tag))
        end)
        at(ms + 260, function()
          g_app.doScreenshot(string.format('mugen_%d_%s2.png', L, tag))
        end)
        ms = ms + 700
      end
    end
    at(ms + 800, function() log('fim'); g_app.exit() end)
  end,
  onLoginError = function(m) log('onLoginError ' .. tostring(m)) end,
  onConnectionError = function(m, c) log('onConnectionError ' .. tostring(m)) end,
})
scheduleEvent(function() log('timeout'); g_app.exit() end, 90000)
