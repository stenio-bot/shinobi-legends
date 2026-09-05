-- Diagnostico cirurgico: por que "O Socio Eterno" nao foi encontrado por nome em 3
-- tentativas seguidas (rodadas 1-3), mesmo numa area isolada e limpa? Hipotese: o
-- monstro spawna server-side normalmente, mas o MATCH POR NOME no cliente (Lua deste
-- rc) falha por causa da MESMA conversao UTF-8->cp1252 da entrada (inputmessage.cpp)
-- -- se ela tambem re-codifica o campo de nome da criatura no pacote de "criatura
-- apareceu" (nao so texto de chat), entao c:getName() no cliente NUNCA mais bate
-- contra um literal UTF-8 escrito neste .lua. Este script nao filtra por nome: soma
-- TODAS as criaturas por perto (nome bruto + hex dos primeiros bytes) antes e depois
-- do /m, pra provar ou descartar a hipotese sem ambiguidade.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('historia46diag_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('DIAG: ' .. tostring(m)) end

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

local function hexName(s)
  if not s then return 'nil' end
  local out = {}
  for i = 1, #s do out[#out+1] = string.format('%02x', s:byte(i)) end
  return s .. ' [' .. table.concat(out, ' ') .. ']'
end

local function dumpCreatures(tag)
  local p = g_game.getLocalPlayer()
  if not p then log(tag .. ': sem player'); return end
  local list = g_map.getSpectators(p:getPosition(), false)
  log(tag .. ': ' .. #list .. ' criaturas por perto')
  for _, c in ipairs(list) do
    local ok, nm = pcall(function() return c:getName() end)
    log(tag .. ' -> isMonster=' .. tostring(c:isMonster()) .. ' name=' .. hexName(ok and nm or '<erro>'))
  end
end

connect(g_game, {
  onGameStart = function()
    log('em jogo')
    scheduleEvent(function() g_game.talk('/god') end, 1000)
    scheduleEvent(function() g_game.talk('/full') end, 1500)
    scheduleEvent(function() g_game.talk('/tp 1449,1005,7') end, 2200)
    scheduleEvent(function() dumpCreatures('ANTES') end, 3200)
    scheduleEvent(function() shot('01_antes') end, 3400)
    scheduleEvent(function() g_game.talk('/m O Sócio Eterno'); log('enviado: /m O Sócio Eterno') end, 4000)
    scheduleEvent(function() dumpCreatures('DEPOIS_1s') end, 5000)
    scheduleEvent(function() shot('02_depois_1s') end, 5200)
    scheduleEvent(function() dumpCreatures('DEPOIS_3s') end, 7000)
    scheduleEvent(function() shot('03_depois_3s') end, 7200)
    -- se algo apareceu, ataca (proximidade, sem filtrar por nome) pra confirmar que e o boss de verdade
    scheduleEvent(function()
      local p = g_game.getLocalPlayer()
      local best, bestd = nil, 99
      for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
        if c:isMonster() then
          local d = math.max(math.abs(c:getPosition().x - p:getPosition().x), math.abs(c:getPosition().y - p:getPosition().y))
          if d < bestd then best, bestd = c, d end
        end
      end
      if best then
        log('atacando criatura mais proxima (proximidade, sem filtro de nome)')
        g_game.attack(best)
      else
        log('NENHUMA criatura monstro encontrada por perto -- spawn realmente falhou')
      end
    end, 7500)
    scheduleEvent(function() dumpCreatures('COMBATE_3s') end, 10500)
    scheduleEvent(function() shot('04_combate') end, 10700)
    scheduleEvent(function()
      g_game.talk('/pvm') -- limpa qualquer residuo de estado vulneravel antes de sair
      g_game.safeLogout()
    end, 13000)
    scheduleEvent(function() g_app.exit() end, 15000)
  end,
  onTextMessage = function(mode, text) log('msg(' .. tostring(mode) .. '): ' .. tostring(text)) end,
  onTalk = function(name, level, mode, text) log('talk: [' .. tostring(mode) .. '] ' .. hexName(name) .. ': ' .. tostring(text)) end,
})
scheduleEvent(function() shot('99_timeout'); log('TIMEOUT'); g_app.exit() end, 60000)
