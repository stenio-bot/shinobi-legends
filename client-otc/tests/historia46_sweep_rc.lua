-- Varredura final: mata qualquer "O Socio Eterno" orfao que tenha sobrado no canto
-- da sala do Covil usado pros testes de boss (1449,1005,7) -- limpeza do ambiente
-- compartilhado, nao deixar bosses vivos e nao-atacados por ai. Fecha a missao
-- q_mountain_curse_partner (done_text) se ainda estiver pendente e confere !conquistas.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('historia46sweep_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('SWEEP: ' .. tostring(m)) end

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

local SOCIO_ETERNO_CP1252 = 'O S\xF3cio Eterno'
local function findSocioEterno()
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() and c:getName() == SOCIO_ETERNO_CP1252 then return c end
  end
  return nil
end

local killed = 0
local function killLoop()
  local target = findSocioEterno()
  if not target then
    log('varredura limpa: ' .. killed .. ' morto(s) nesta rodada, nenhum orfao restante')
    g_game.talk('/tp 1222,1058,7')
    scheduleEvent(function() g_game.talk('hi') end, 700)
    scheduleEvent(function() g_game.talkChannel(MessageModes.NpcTo, 0, 'missao') end, 1600)
    scheduleEvent(function() shot('01_missao_final') end, 2600)
    scheduleEvent(function() g_game.talk('bye') end, 3000)
    scheduleEvent(function() g_game.talk('!conquistas') end, 3500)
    scheduleEvent(function() shot('02_conquistas_final') end, 4500)
    scheduleEvent(function()
      local p = g_game.getLocalPlayer()
      if p then log('stats finais hp=' .. p:getHealth() .. '/' .. p:getMaxHealth()) end
      g_game.safeLogout()
    end, 5500)
    scheduleEvent(function() g_app.exit() end, 7500)
    return
  end
  local id = target:getId()
  local elapsed = 0
  local function poll()
    local m = g_map.getCreatureById(id)
    if not m then
      killed = killed + 1
      log('orfao ' .. killed .. ' morto')
      scheduleEvent(killLoop, 500)
      return
    end
    g_game.attack(m)
    elapsed = elapsed + 700
    if elapsed >= 45000 then log('TIMEOUT matando orfao (id ' .. id .. ')'); scheduleEvent(killLoop, 500); return end
    scheduleEvent(poll, 700)
  end
  poll()
end

connect(g_game, {
  onGameStart = function()
    log('em jogo')
    scheduleEvent(function() g_game.talk('/god') end, 900)
    scheduleEvent(function() g_game.talk('/full') end, 1400)
    scheduleEvent(function() g_game.talk('/tp 1449,1005,7') end, 2000)
    -- NAO mexe em /pvm aqui: a rodada anterior deixou desligado (God normal, seguro).
    -- Matar os orfaos nao depende de levar dano de volta.
    scheduleEvent(killLoop, 2800)
  end,
  onTextMessage = function(mode, text)
    log('msg(' .. tostring(mode) .. '): ' .. tostring(text))
  end,
  onTalk = function(name, level, mode, text) log('talk: [' .. tostring(mode) .. '] ' .. tostring(name) .. ': ' .. tostring(text)) end,
})
scheduleEvent(function() shot('99_timeout'); log('TIMEOUT GERAL'); g_app.exit() end, 180000)
