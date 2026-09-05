-- Teste visual do Terreno v3 + icones de jutsu. Copiado para client-otc/shinobirc.lua
-- por um comando ad-hoc (nao ha script dedicado; ver docs/sistemas/arte-e-sprites.md,
-- secao "Teste in-game (Terreno v3)"). Removido ao final.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'god'
local PASSWORD = os.getenv('SL_PASSWORD') or 'god'
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('AUTOTEST: ' .. m) end

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

local SPOTS = {
  { name = 'floresta',        x = 1060, y = 1080, z = 7 },
  { name = 'lago_ponte',      x = 1127, y = 1060, z = 7 },
  { name = 'praca',           x = 1029, y = 1044, z = 7 },
  { name = 'floresta_morte',  x = 1165, y = 1061, z = 7 },
}

connect(g_game, {
  onGameStart = function()
    log('em jogo!')
    local t = 1500
    local function at(ms, fn) scheduleEvent(fn, t + ms) end
    at(0, function() g_game.talk('/god') end)
    local step = 0
    for _, spot in ipairs(SPOTS) do
      local base = 800 + step * 2600
      at(base, function()
        g_game.talk(string.format('/tp %d,%d,%d', spot.x, spot.y, spot.z))
        log('tp -> ' .. spot.name)
      end)
      at(base + 900, function() shot('render_v3_' .. spot.name .. '.png') end)
      step = step + 1
    end
    local afterSpots = 800 + step * 2600
    at(afterSpots + 500, function()
      if modules.naruto_menu then
        modules.naruto_menu.show('Jutsus')
        log('menu Shinobi aberto na aba Jutsus')
      else
        log('modules.naruto_menu nao carregado!')
      end
    end)
    at(afterSpots + 1400, function() shot('render_v3_icons.png') end)
    at(afterSpots + 2200, function() g_app.exit() end)
  end,
  onLoginError = function(msg) log('onLoginError ' .. tostring(msg)) end,
  onConnectionError = function(msg, code) log('onConnectionError ' .. tostring(msg) .. ' ' .. tostring(code)) end,
  onTextMessage = function(mode, text) log('msg: ' .. tostring(text)) end,
})
scheduleEvent(function() shot('render_v3_timeout.png'); log('timeout'); g_app.exit() end, 40000)
