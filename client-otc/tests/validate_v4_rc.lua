-- Validacao pos-integracao (criaturas 940+, conquistas, sfx). Copiado para shinobirc.lua e removido.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'god'
local PASSWORD = os.getenv('SL_PASSWORD') or 'god'
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('VALID4: ' .. m) end
scheduleEvent(function()
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT); field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin(); log('doLogin')
end, 2500)
scheduleEvent(function() if not g_game.isOnline() then pcall(CharacterList.doLogin) end end, 7000)
connect(g_game, {
  onGameStart = function()
    log('em jogo')
    local t = 2000
    local function at(ms, fn) scheduleEvent(fn, t + ms) end
    at(0, function() g_game.talk('/sl') end)
    at(400, function() g_game.talk('/arena') end)
    at(1500, function() g_game.talk('/pvm') end)
    at(2200, function() g_game.talk('/m Lobo') end)
    at(2600, function() g_game.talk('/m Cervo') end)
    at(3000, function() g_game.talk('/m Águia do Trovão') end)
    at(3400, function() g_game.talk('/m Bandido') end)
    at(3800, function() g_game.talk('/m Bandido Arqueiro') end)
    at(4200, function() g_game.talk('/m Mercenário da Ponte') end)
    at(4600, function() g_game.talk('/m Cobra da Floresta') end)
    at(5000, function() g_game.talk('/m Sapo Gigante') end)
    at(6500, function() shot('valid4_01_criaturas.png') end)
    at(7000, function() g_game.talk('/conquista 1') end)
    at(8200, function() shot('valid4_02_conquista.png') end)
    at(8600, function() g_game.talk('!conquistas') end)
    at(9500, function() g_game.talk('katon goukakyuu') end)
    at(10300, function() shot('valid4_03_jutsu.png') end)
    at(11000, function() modules.naruto_menu.show(); end)
    at(12500, function() shot('valid4_04_menu.png') end)
    at(13500, function()
      local p = g_game.getLocalPlayer()
      log(string.format('stats: hp %d/%d chakra %d/%d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana()))
      g_game.safeLogout()
    end)
    at(15500, function() g_app.exit() end)
  end,
  onTextMessage = function(mode, text) log('msg: ' .. tostring(text)) end,
  onTalk = function(name, level, mode, text) log('talk: ' .. tostring(name) .. ': ' .. tostring(text)) end,
})
scheduleEvent(function() shot('valid4_timeout.png'); log('timeout'); g_app.exit() end, 45000)
