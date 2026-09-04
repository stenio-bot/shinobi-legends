-- Teste automatizado ponta a ponta. Copiado para client-otc/shinobirc.lua por tools/autotest_client.sh
-- (o OTClient executa /<compactName>rc.lua depois de carregar os módulos). Removido ao final.
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

local function nearestMonster()
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  local best, bestd = nil, 99
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() then
      local d = math.max(math.abs(c:getPosition().x - p:getPosition().x), math.abs(c:getPosition().y - p:getPosition().y))
      if d < bestd then best, bestd = c, d end
    end
  end
  return best
end

connect(g_game, {
  onGameStart = function()
    log('em jogo!')
    log(string.format('versao cliente %s protocolo %s envEffect=%s', tostring(g_game.getClientVersion()), tostring(g_game.getProtocolVersion()), tostring(g_game.getFeature(GameEnvironmentEffect))))
    local t = 2000
    local function at(ms, fn) scheduleEvent(fn, t + ms) end
    at(0, function() shot('autotest_01_spawn.png') end)
    -- sai da zona de proteção (comando GM: anda N tiles na direção atual)
    at(300, function() g_game.talk('/pos') end)
    at(400, function() g_game.talk('/sl') end)
    at(500, function() g_game.talk('/arena') end)
    at(1500, function() g_game.talk('/jutsus') end)
    at(2000, function() g_game.talk('/lvl 20') end)
    at(3500, function() g_game.talk('/m Lobo') end)
    at(4000, function() g_game.talk('/m Sapo Gigante') end)
    at(5500, function() shot('autotest_02_monstros.png') end)
    at(6000, function()
      local m = nearestMonster()
      if m then g_game.attack(m); log('alvo: ' .. m:getName()) else log('nenhum monstro perto') end
    end)
    at(6500, function() g_game.talk('katon goukakyuu') end)
    at(7300, function() shot('autotest_03_jutsu.png') end)
    at(8500, function() g_game.talk('kawarimi') end)
    at(9000, function() shot('autotest_04_kawarimi.png') end)
    at(10000, function()
      local p = g_game.getLocalPlayer()
      log(string.format('stats: hp %d/%d chakra %d/%d level %d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana(), p:getLevel()))
    end)
    at(11000, function() g_app.exit() end)
  end,
  onLoginError = function(msg) log('onLoginError ' .. tostring(msg)) end,
  onConnectionError = function(msg, code) log('onConnectionError ' .. tostring(msg) .. ' ' .. tostring(code)) end,
  onTextMessage = function(mode, text) log('msg: ' .. tostring(text)) end,
  onTalk = function(name, level, mode, text) log('talk: ' .. tostring(name) .. ': ' .. tostring(text)) end,
})
scheduleEvent(function() shot('autotest_timeout.png'); log('timeout'); g_app.exit() end, 40000)
