-- Fecha o teste do boss O Socio Eterno (diagnostico anterior provou que o spawn
-- sempre funcionou -- o "nao encontrado" das rodadas 1-3 era um bug do MEU script de
-- teste: c:getName() no cliente agora devolve o nome ja em cp1252 (correto pra tela,
-- confirmado por screenshot), entao comparar contra um literal UTF-8 no .lua nunca
-- batia. Trava por ID logo apos escolher o alvo mais proximo (nunca por nome) --
-- assim nao troca de alvo pro summon de Serpente de Magma a 50%. Tambem mata os 3
-- bosses orfaos que ficaram vivos das tentativas anteriores (mesma area).
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('historia46final_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('FIN: ' .. tostring(m)) end

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

local queue = {}
local function enqueue(fn) table.insert(queue, fn) end
local function runNext()
  if #queue == 0 then log('SEQUENCIA COMPLETA'); scheduleEvent(function() g_app.exit() end, 3000); return end
  local fn = table.remove(queue, 1)
  local ok, err = pcall(fn, runNext)
  if not ok then log('ERRO no passo: ' .. tostring(err)); scheduleEvent(runNext, 300) end
end

local pvmOn = false -- sabemos que ficou "false" (desligado) no fim da rodada 3
local function say(msg, delay) return function(nextFn) g_game.talk(msg); log('talk: ' .. msg); scheduleEvent(nextFn, delay or 500) end end
local function sayNpc(msg, delay) return function(nextFn) g_game.talkChannel(MessageModes.NpcTo, 0, msg); log('npc: ' .. msg); scheduleEvent(nextFn, delay or 900) end end
local function shotStep(name, delay) return function(nextFn) shot(name); scheduleEvent(nextFn, delay or 200) end end
local function tp(x, y, z) return say('/tp ' .. x .. ',' .. y .. ',' .. z, 700) end
local function ensurePvm(wantOn)
  return function(nextFn)
    if pvmOn == wantOn then log('pvm ja ' .. (wantOn and 'ligado' or 'desligado')); nextFn(); return end
    g_game.talk('/pvm'); pvmOn = wantOn
    log('talk: /pvm -> agora ' .. (wantOn and 'ligado' or 'desligado'))
    scheduleEvent(nextFn, 600)
  end
end

-- Diagnostico anterior (historia46_boss_diag_rc.lua) provou por hexdump que
-- c:getName() no cliente pos-fix devolve o nome JA EM CP1252 (0xF3 pra 'o', nao mais
-- 0xC3 0xB3 UTF-8) -- mesma string que aparece certa na tela. Usa o literal exato em
-- cp1252 (nao UTF-8) pra filtrar so os bosses "O Socio Eterno" orfaos, ignorando "O
-- Ancestral Da Nuvem Vermelha" (boss fixo vizinho, nao mexer nele).
local SOCIO_ETERNO_CP1252 = 'O S\xF3cio Eterno'
local function nearestSocioEterno()
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  local best, bestd = nil, 99
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() and c:getName() == SOCIO_ETERNO_CP1252 then
      local d = math.max(math.abs(c:getPosition().x - p:getPosition().x), math.abs(c:getPosition().y - p:getPosition().y))
      if d < bestd then best, bestd = c, d end
    end
  end
  return best
end

--- Mata 1 "O Socio Eterno" (ou qualquer boss mais proximo): trava por ID assim que
--- escolhe o alvo, ignora summons que aparecerem (nunca troca de alvo), loga HP do
--- boss e do jogador a cada tick (fase/furia), screenshot ao cruzar o limiar de HP%.
local function killNearestBoss(tag, hpThresholdPct, timeoutMs)
  return function(nextFn)
    local target = nearestSocioEterno()
    if not target then log(tag .. ': nenhum O Socio Eterno por perto (ja matou todos?)'); nextFn(); return end
    local id = target:getId()
    log(tag .. ': alvo travado id=' .. tostring(id))
    local elapsed = 0
    local crossed = false
    local function poll()
      local m = g_map.getCreatureById(id)
      local p = g_game.getLocalPlayer()
      if not p then log(tag .. ': jogador nil'); nextFn(); return end
      if not m then log(tag .. ': alvo morto/sumiu'); nextFn(); return end
      g_game.attack(m)
      local hpPct = m:getHealthPercent()
      log(string.format('%s: alvo hp%%=%s | player hp=%d/%d (%.0f%%)', tag, tostring(hpPct), p:getHealth(), p:getMaxHealth(), p:getHealthPercent()))
      if not crossed and hpPct and hpPct <= hpThresholdPct then
        crossed = true
        shot(tag .. '_fase_cruzada')
        log(tag .. ': cruzou ' .. hpThresholdPct .. '%')
      end
      elapsed = elapsed + 700
      if elapsed >= (timeoutMs or 40000) then log(tag .. ': TIMEOUT hp%=' .. tostring(hpPct)); nextFn(); return end
      scheduleEvent(poll, 700)
    end
    poll()
  end
end

connect(g_game, {
  onGameStart = function()
    log('em jogo')
    enqueue(say('/god', 900))
    enqueue(say('/full', 500))
    enqueue(tp(1449, 1005, 7))
    enqueue(ensurePvm(true)) -- furia real: precisa levar dano de verdade
    enqueue(function(nextFn) local p = g_game.getLocalPlayer(); log('HP_ANTES=' .. p:getHealth() .. '/' .. p:getMaxHealth()); nextFn() end)

    -- mata o 1o boss orfao ate 50% (fase + summon), screenshot, continua ate matar
    enqueue(killNearestBoss('01_ate_fase50', 50, 60000))
    enqueue(shotStep('02_pos_fase50'))
    enqueue(function(nextFn) local p = g_game.getLocalPlayer(); log('HP_APOS_50pct=' .. p:getHealth() .. '/' .. p:getMaxHealth()); nextFn() end)
    enqueue(killNearestBoss('03_ate_morte', 0, 60000))
    enqueue(shotStep('04_boss1_morto'))

    -- limpa os outros 2 bosses orfaos (mata rapido, sem instrumentar fase de novo)
    enqueue(killNearestBoss('05_boss2', 0, 60000))
    enqueue(killNearestBoss('06_boss3', 0, 60000))
    enqueue(ensurePvm(false))

    -- fecha a missao (done_text) e confere !conquistas (kill_specific)
    enqueue(tp(1222, 1058, 7))
    enqueue(say('hi', 700))
    enqueue(sayNpc('missao', 900))
    enqueue(shotStep('07_missao_curse_partner_completa'))
    enqueue(say('bye', 400))
    enqueue(say('!conquistas', 900))
    enqueue(shotStep('08_conquistas'))

    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      if p then log('stats finais hp=' .. p:getHealth() .. '/' .. p:getMaxHealth()) end
      g_game.safeLogout()
      scheduleEvent(nextFn, 1500)
    end)
    scheduleEvent(runNext, 1500)
  end,
  onTextMessage = function(mode, text) log('msg(' .. tostring(mode) .. '): ' .. tostring(text)) end,
  onTalk = function(name, level, mode, text) log('talk: [' .. tostring(mode) .. '] ' .. tostring(name) .. ': ' .. tostring(text)) end,
  onLoginError = function(m) log('onLoginError ' .. tostring(m)) end,
  onConnectionError = function(m, c) log('onConnectionError ' .. tostring(m)) end,
})
scheduleEvent(function() shot('99_timeout'); log('TIMEOUT'); g_app.exit() end, 240000)
