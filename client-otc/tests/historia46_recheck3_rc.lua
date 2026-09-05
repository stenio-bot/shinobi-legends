-- 3a tentativa, so pro boss O Socio Eterno (as 2 rodadas anteriores nao conseguiram:
-- rodada 1 morreu pra mobs ambiente da Montanha ao ligar /pvm perto do posto avancado
-- de Yuki; rodada 2 usou /arena, que so acha o tile livre MAIS PROXIMO da posicao
-- atual -- ainda dentro do alcance dos mesmos mobs ambiente -- e o /m falhou "nao
-- encontrado", provavel not-enough-room). Desta vez usa um canto vazio da sala final
-- do Covil (1436-1449,1000-1024, ja usada com sucesso no playtest anterior pros 4
-- bosses de la), longe dos spawns ambiente de Clone Branco/Ninja Elite (raio 12 a
-- partir de 1422,1012, alcance maximo x=1434) e do proprio Ancestral da Nuvem
-- Vermelha (raio 3 a partir de 1444,1012) -- 1449,1005,7 fica fora dos dois.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('historia46r3_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('R46C: ' .. tostring(m)) end

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

local pvmOn = nil -- rastreado via mensagens do servidor (nao assume estado)
local function say(msg, delay) return function(nextFn) g_game.talk(msg); log('talk: ' .. msg); scheduleEvent(nextFn, delay or 500) end end
local function sayNpc(msg, delay) return function(nextFn) g_game.talkChannel(MessageModes.NpcTo, 0, msg); log('npc: ' .. msg); scheduleEvent(nextFn, delay or 900) end end
local function shotStep(name, delay) return function(nextFn) shot(name); scheduleEvent(nextFn, delay or 200) end end
local function tp(x, y, z) return say('/tp ' .. x .. ',' .. y .. ',' .. z, 700) end
local function hp(tag) return function(nextFn) local p = g_game.getLocalPlayer(); if p then log(tag .. ' hp=' .. p:getHealth() .. '/' .. p:getMaxHealth()) end; nextFn() end end

--- Garante PvM no estado desejado (true=ligado) checando o flag rastreado por
--- onTextMessage; so chama /pvm se precisar mudar (idempotente, nao fica alternando).
local function ensurePvm(wantOn)
  return function(nextFn)
    if pvmOn == wantOn then log('pvm ja esta ' .. (wantOn and 'ligado' or 'desligado')); nextFn(); return end
    g_game.talk('/pvm')
    log('talk: /pvm (querendo ' .. (wantOn and 'ligado' or 'desligado') .. ')')
    scheduleEvent(nextFn, 600)
  end
end

local function findMonsterByName(name)
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() and c:getName() == name then return c end
  end
  return nil
end

--- Tenta /m ate achar o monstro (retry ate 3x, 1.5s entre tentativas -- cobre spawn
--- falhando por not-enough-room transitorio).
local function spawnRetry(name, tries)
  return function(nextFn)
    local attempt = 0
    local function tryOnce()
      attempt = attempt + 1
      g_game.talk('/m ' .. name)
      log('spawn tentativa ' .. attempt .. ': ' .. name)
      scheduleEvent(function()
        local m = findMonsterByName(name)
        if m then log(name .. ' encontrado apos tentativa ' .. attempt); nextFn(); return end
        if attempt >= (tries or 3) then log(name .. ' NAO SPAWNOU apos ' .. attempt .. ' tentativas'); nextFn(); return end
        scheduleEvent(tryOnce, 1500)
      end, 1200)
    end
    tryOnce()
  end
end

local function fightBossUntil(tag, bossName, hpThresholdPct, timeoutMs)
  return function(nextFn)
    local boss = findMonsterByName(bossName)
    local bossId = boss and boss:getId()
    if not boss then log(tag .. ': boss "' .. bossName .. '" nao presente -- pulando fase'); nextFn(); return end
    local elapsed = 0
    local crossed = false
    local function poll()
      local m = bossId and g_map.getCreatureById(bossId)
      local p = g_game.getLocalPlayer()
      if not p then log(tag .. ': jogador nil (desconectado?)'); nextFn(); return end
      if not m then log(tag .. ': boss morto/sumiu'); nextFn(); return end
      g_game.attack(m)
      if p:getHealthPercent() < 20 then g_game.talk('/full'); log(tag .. ': /full de seguranca') end
      local hpPct = m:getHealthPercent()
      log(string.format('%s: boss hp%%=%s | player hp=%d/%d (%.0f%%)', tag, tostring(hpPct), p:getHealth(), p:getMaxHealth(), p:getHealthPercent()))
      if not crossed and hpPct and hpPct <= hpThresholdPct then
        crossed = true
        shot(tag .. '_fase_cruzada')
        log(tag .. ': cruzou ' .. hpThresholdPct .. '%')
      end
      elapsed = elapsed + 700
      if elapsed >= (timeoutMs or 45000) then log(tag .. ': TIMEOUT hp%=' .. tostring(hpPct)); nextFn(); return end
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
    enqueue(tp(1449, 1005, 7)) -- canto vazio da sala final do Covil (ver comentario no topo)
    enqueue(shotStep('00_local_isolado'))
    enqueue(ensurePvm(true))
    enqueue(hp('ANTES_boss'))
    enqueue(spawnRetry('O Sócio Eterno', 3))
    enqueue(fightBossUntil('01_socio_eterno_fase50', 'O Sócio Eterno', 50, 60000))
    enqueue(shotStep('02_socio_eterno_pos_fase50'))
    enqueue(hp('APOS_cruzar_50pct'))
    enqueue(fightBossUntil('03_socio_eterno_kill', 'O Sócio Eterno', 0, 60000))
    enqueue(shotStep('04_socio_eterno_morto'))
    enqueue(ensurePvm(false))

    enqueue(tp(1222, 1058, 7))
    enqueue(say('hi', 700))
    enqueue(sayNpc('missao', 900)) -- fecha q_mountain_curse_partner (done_text)
    enqueue(shotStep('05_missao_curse_partner_completa'))
    enqueue(say('bye', 400))
    enqueue(say('!conquistas', 900))
    enqueue(shotStep('06_conquistas'))

    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      if p then log(string.format('stats finais: hp %d/%d chakra %d/%d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana())) end
      g_game.safeLogout()
      scheduleEvent(nextFn, 1500)
    end)

    scheduleEvent(runNext, 1500)
  end,
  onTextMessage = function(mode, text)
    log('msg(' .. tostring(mode) .. '): ' .. tostring(text))
    if type(text) == 'string' then
      if text:find('PvM ligado') then pvmOn = true end
      if text:find('PvM desligado') then pvmOn = false end
    end
  end,
  onTalk = function(name, level, mode, text) log('talk: [' .. tostring(mode) .. '] ' .. tostring(name) .. ': ' .. tostring(text)) end,
  onLoginError = function(m) log('onLoginError ' .. tostring(m)) end,
  onConnectionError = function(m, c) log('onConnectionError ' .. tostring(m)) end,
})
scheduleEvent(function() shot('99_timeout'); log('TIMEOUT GERAL'); g_app.exit() end, 240000)
