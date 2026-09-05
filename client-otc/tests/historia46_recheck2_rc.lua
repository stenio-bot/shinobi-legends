-- Continuacao do re-teste historia46 (1a rodada morreu pra um Monge da Tempestade
-- ambiente perto do posto avancado da Montanha ao ligar /pvm, e a conexao caiu logo
-- depois -- boss e quiz nunca foram de fato testados no servidor). Fecha a cadeia
-- ate o quiz (idempotente: reforca storages ja batidos, sem risco) e testa O Socio
-- Eterno isolado via /arena (longe dos monstros ambiente que mataram o GM antes).
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('historia46r2_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('R46B: ' .. tostring(m)) end

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

local function say(msg, delay) return function(nextFn) g_game.talk(msg); log('talk: ' .. msg); scheduleEvent(nextFn, delay or 500) end end
local function sayNpc(msg, delay) return function(nextFn) g_game.talkChannel(MessageModes.NpcTo, 0, msg); log('npc: ' .. msg); scheduleEvent(nextFn, delay or 900) end end
local function shotStep(name, delay) return function(nextFn) shot(name); scheduleEvent(nextFn, delay or 200) end end
local function tp(x, y, z) return say('/tp ' .. x .. ',' .. y .. ',' .. z, 700) end
local function hp(tag) return function(nextFn) local p = g_game.getLocalPlayer(); if p then log(tag .. ' hp=' .. p:getHealth() .. '/' .. p:getMaxHealth()) end; nextFn() end end

local function findMonsterByName(name)
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() and c:getName() == name then return c end
  end
  return nil
end

local function fightBossUntil(tag, bossName, hpThresholdPct, timeoutMs, healGuard)
  return function(nextFn)
    scheduleEvent(function()
      local boss = findMonsterByName(bossName)
      local bossId = boss and boss:getId()
      if not boss then log(tag .. ': boss "' .. bossName .. '" nao encontrado no spawn') end
      local elapsed = 0
      local crossed = false
      local function poll()
        local m = bossId and g_map.getCreatureById(bossId)
        local p = g_game.getLocalPlayer()
        if not p then log(tag .. ': jogador nil (desconectado?)'); nextFn(); return end
        if not m then
          log(tag .. ': boss morto/sumiu (id ' .. tostring(bossId) .. ')')
          nextFn()
          return
        end
        g_game.attack(m)
        -- guarda de seguranca: nunca deixa o GM morrer de verdade pro boss (nao e o que
        -- estamos testando aqui -- so a fala/summon/furia da fase)
        if healGuard and p:getHealthPercent() < 25 then
          g_game.talk('/full')
          log(tag .. ': /full de seguranca (hp baixo)')
        end
        local hpPct = m:getHealthPercent()
        log(string.format('%s: boss hp%%=%s | player hp=%d/%d (%.0f%%)', tag, tostring(hpPct), p:getHealth(), p:getMaxHealth(), p:getHealthPercent()))
        if not crossed and hpPct and hpPct <= hpThresholdPct then
          crossed = true
          shot(tag .. '_fase_cruzada')
          log(tag .. ': cruzou ' .. hpThresholdPct .. '% -- capturando fala/summons')
        end
        elapsed = elapsed + 700
        if elapsed >= (timeoutMs or 40000) then
          log(tag .. ': TIMEOUT (parou em hp%=' .. tostring(hpPct) .. ')')
          nextFn()
          return
        end
        scheduleEvent(poll, 700)
      end
      poll()
    end, 600)
  end
end

connect(g_game, {
  onGameStart = function()
    log('em jogo')
    enqueue(say('/god', 900))
    enqueue(say('/full', 500))
    -- NAO liga /pvm ainda -- so na arena isolada, na hora do boss.

    -- ==== fecha a cadeia ate o quiz (idempotente -- reforca o que ja foi feito) ====
    enqueue(tp(1222, 1058, 7))
    enqueue(say('hi', 700))
    enqueue(say('/storage 50034 15', 500))
    enqueue(sayNpc('missao', 900)) -- fecha eagles (no-op se ja fechada)
    enqueue(sayNpc('missao', 900)) -- aceita/segue relics
    enqueue(say('/i 5891,8', 700))
    enqueue(say('hi', 600))
    enqueue(sayNpc('missao', 900)) -- fecha relics
    enqueue(sayNpc('missao', 900)) -- aceita oni
    enqueue(say('/storage 50036 10', 500))
    enqueue(say('hi', 600))
    enqueue(sayNpc('missao', 900)) -- fecha oni
    enqueue(sayNpc('missao', 900)) -- aceita serpents
    enqueue(say('/storage 50037 10', 500))
    enqueue(say('hi', 600))
    enqueue(sayNpc('missao', 900)) -- fecha serpents
    enqueue(sayNpc('missao', 900)) -- aceita lore quiz
    enqueue(shotStep('01_cadeia_ate_quiz'))

    -- ==== quiz q_mountain_lore ====
    enqueue(sayNpc('prova', 900))
    enqueue(shotStep('02_quiz_pergunta1'))
    enqueue(sayNpc('furia', 900))
    enqueue(sayNpc('sócio eterno', 900))
    enqueue(sayNpc('nuvem vermelha', 900))
    enqueue(shotStep('03_quiz_resultado'))
    enqueue(sayNpc('missao', 900)) -- aceita curse_partner
    enqueue(shotStep('04_missao_curse_partner_aceita'))
    enqueue(say('bye', 400))

    -- ==== aba Missoes: naruto_menu.show(tabName) seleciona a aba direto (tabBar:getTab),
    -- evita ficar na aba padrao "Personagem" (erro da rodada 1). O nome da aba foi
    -- registrado como 'Miss\xF5es' (cp1252) em naruto_menu.lua -- mesma string aqui. ====
    enqueue(function(nextFn)
      local ok, err = pcall(function() modules.naruto_menu.show('Miss\xF5es') end)
      log('naruto_menu.show("Missões") -> ' .. tostring(ok) .. ' ' .. tostring(err))
      scheduleEvent(nextFn, 1200)
    end)
    enqueue(shotStep('05_aba_missoes'))
    enqueue(function(nextFn) pcall(function() modules.naruto_menu.hide() end); nextFn() end)

    -- ==== boss O Sócio Eterno, ISOLADO via /arena (longe do Monge da Tempestade
    -- ambiente que matou o GM na rodada 1) ====
    enqueue(say('/arena', 1000))
    enqueue(shotStep('06_arena'))
    enqueue(hp('ANTES_boss'))
    enqueue(say('/pvm', 500)) -- liga PvM SO agora, isolado
    enqueue(say('/m O Sócio Eterno', 1200))
    enqueue(fightBossUntil('07_socio_eterno_fase50', 'O Sócio Eterno', 50, 60000, true))
    enqueue(shotStep('08_socio_eterno_pos_fase50'))
    enqueue(hp('APOS_cruzar_50pct'))
    enqueue(fightBossUntil('09_socio_eterno_kill', 'O Sócio Eterno', 0, 60000, true))
    enqueue(shotStep('10_socio_eterno_morto'))
    enqueue(say('/pvm', 500)) -- desliga PvM de novo (seguranca pro resto da sessao)

    enqueue(tp(1222, 1058, 7))
    enqueue(say('hi', 600))
    enqueue(sayNpc('missao', 900)) -- fecha curse_partner (done_text)
    enqueue(shotStep('11_missao_curse_partner_completa'))
    enqueue(say('bye', 400))
    enqueue(say('!conquistas', 900))
    enqueue(shotStep('12_conquistas'))

    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      if p then log(string.format('stats finais: hp %d/%d chakra %d/%d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana())) end
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
scheduleEvent(function() shot('99_timeout'); log('TIMEOUT GERAL'); g_app.exit() end, 300000)
