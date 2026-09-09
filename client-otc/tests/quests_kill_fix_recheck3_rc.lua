-- 3a rodada: só os 2 alvos que a rodada 2 (quests_kill_fix_recheck2_rc.lua) NÃO
-- confirmou -- Marionetista das Ruínas (q_ruins_boss, storage 50047) e O Vigia
-- Ilusório (q_lair_1_illusive_eye, storage 50003). Xamã da Maldição (q_ruins_shamans,
-- storage 50045) já foi confirmado na rodada 2: progresso real 1/8 -> 8/8 em 8 kills
-- reais, storage final = 8 -- não precisa repetir.
--
-- 2 bugs da rodada 2 corrigidos aqui (ambos no MEU script de teste, não no jogo):
--  1. findMonsterByName comparava c:getName() contra um literal UTF-8 -- depois do
--     fix de encoding, getName() no cliente devolve cp1252 (mesma pegadinha
--     documentada em docs/qa/playtest-historia-arcos4-6.md, "achado de metodologia
--     #2"), então a detecção de spawn/alvo NUNCA batia e o retry ficava chamando /m
--     sem parar. Corrigido: detecta o alvo por DIFF DE ID (creature novo na lista de
--     spectators antes/depois do /m), sem nunca comparar nome -- funciona não importa
--     o encoding.
--  2. `/god` (talkaction deste servidor) só ajusta stats/skills, NÃO impede dano de
--     verdade (diferente do grupo "God" da conta) -- o personagem morreu de verdade
--     na rodada 2 (swarm de Xamãs + bug #1 gerando retries em excesso) e a janela de
--     morte do cliente (client-otc/modules/game_playerdeath) ficou esperando um OK
--     que o script nunca clicou, travando toda a sequência depois disso (nenhuma
--     resposta de /storage, NPC ou /rank chegou depois da morte). Corrigido:
--     autoReconnect ligado (a janela de morte reloga sozinha em ~2s) + /full a cada
--     tick de combate quando HP < 50%.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('qkfix3_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('QKFIX3: ' .. tostring(m)) end

scheduleEvent(function()
  g_settings.set('autoReconnect', true)
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT)
  field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin()
  log('doLogin ' .. ACCOUNT .. ' (autoReconnect=true)')
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
local function sayNpc(msg, delay) return function(nextFn) g_game.talkChannel(MessageModes.NpcTo, 0, msg); log('npc: ' .. msg); scheduleEvent(nextFn, delay or 1000) end end
local function shotStep(name, delay) return function(nextFn) shot(name); scheduleEvent(nextFn, delay or 200) end end
local function tp(x, y, z) return say('/tp ' .. x .. ',' .. y .. ',' .. z, 900) end
local function readStorage(id, delay) return say('/storage ' .. id, delay or 1000) end
local function setStorage(id, value, delay) return say('/storage ' .. id .. ' ' .. value, delay or 700) end
local function wait(ms) return function(nextFn) scheduleEvent(nextFn, ms) end end

local function currentMonsterIds()
  local ids = {}
  local p = g_game.getLocalPlayer()
  if not p then return ids end
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() then ids[c:getId()] = true end
  end
  return ids
end

--- Spawna 1 unidade de `name`, identifica o alvo por DIFF DE ID (nunca por nome --
--- ver comentário do topo), ataca até morrer/sumir ou timeout, chamando /full
--- sempre que o HP do jogador cair abaixo de 50%. tries = tentativas de /m antes
--- de desistir; timeoutMs = tempo máximo de combate.
local function spawnLockKill(tag, name, tries, timeoutMs)
  return function(nextFn)
    local before = currentMonsterIds()
    local attempt = 0
    local function fight(lockedId)
      local elapsed = 0
      local lastLog = 0
      local function poll()
        local m = g_map.getCreatureById(lockedId)
        local p = g_game.getLocalPlayer()
        if not p then log(tag .. ': jogador nil (desconectado?)'); nextFn(); return end
        if p:getHealthPercent() < 50 then g_game.talk('/full') end
        if not m then log(tag .. ': alvo morto/sumiu apos ' .. elapsed .. 'ms'); scheduleEvent(nextFn, 800); return end
        g_game.attack(m)
        elapsed = elapsed + 500
        if elapsed - lastLog >= 5000 then
          lastLog = elapsed
          log(string.format('%s: alvo hp%%=%s | player hp=%d/%d', tag, tostring(m:getHealthPercent()), p:getHealth(), p:getMaxHealth()))
        end
        if elapsed >= (timeoutMs or 45000) then log(tag .. ': TIMEOUT (alvo ainda vivo)'); nextFn(); return end
        scheduleEvent(poll, 500)
      end
      poll()
    end
    local function tryOnce()
      attempt = attempt + 1
      g_game.talk('/m ' .. name)
      log(tag .. ': spawn tentativa ' .. attempt .. ': ' .. name)
      scheduleEvent(function()
        local after = currentMonsterIds()
        local newId = nil
        for id in pairs(after) do
          if not before[id] then newId = id; break end
        end
        if newId then
          log(tag .. ': ' .. name .. ' spawnou id=' .. newId)
          fight(newId)
          return
        end
        if attempt >= (tries or 3) then
          log(tag .. ': ' .. name .. ' NAO SPAWNOU apos ' .. attempt .. ' tentativas (id-diff)')
          nextFn()
          return
        end
        scheduleEvent(tryOnce, 1500)
      end, 1300)
    end
    tryOnce()
  end
end

connect(g_game, {
  onGameStart = function()
    log('em jogo')
    enqueue(say('/god', 900))
    enqueue(say('/full', 600))

    -- ===== Marionetista das Ruinas x1 (q_ruins_boss, storage 50047) =====
    enqueue(tp(1246, 1032, 7))
    enqueue(shotStep('01_salao_marionetista'))
    enqueue(readStorage(50047)) -- baseline (deve ser 0, ja zerado na rodada 2)
    enqueue(spawnLockKill('puppeteer', 'Marionetista das Ruínas', 3, 45000))
    enqueue(wait(1200))
    enqueue(readStorage(50047)) -- deve virar 1
    enqueue(shotStep('02_puppeteer_pos_kill'))

    -- fecha q_ruins_shamans (ja em 8/8 desde a rodada 2) + q_ruins_boss com o
    -- Anciao Kaito -- 2 chamadas de 'missao' (Achado #3 do playtest: so' 1
    -- transicao por chamada)
    enqueue(tp(1206, 1023, 7))
    enqueue(shotStep('03_perto_kaito'))
    enqueue(say('hi', 800))
    enqueue(sayNpc('missao', 1400))
    enqueue(shotStep('04_kaito_missao_1'))
    enqueue(sayNpc('missao', 1400))
    enqueue(shotStep('05_kaito_missao_2'))
    enqueue(say('bye', 500))
    enqueue(say('/rank', 1000))
    enqueue(shotStep('06_rank_apos_ruinas'))

    -- ===== O Vigia Ilusorio x1 (q_lair_1_illusive_eye, storage 50003) =====
    enqueue(tp(1449, 1005, 7))
    enqueue(shotStep('07_covil_canto_seguro'))
    enqueue(readStorage(50003)) -- baseline (deve ser 0)
    enqueue(spawnLockKill('illusive_eye', 'O Vigia Ilusório', 3, 45000))
    enqueue(wait(1200))
    enqueue(readStorage(50003)) -- deve virar 1
    enqueue(shotStep('08_illusive_eye_pos_kill'))

    -- fecha a quest do Covil com a Capita Anbu Suzu
    enqueue(tp(1407, 1010, 7))
    enqueue(shotStep('09_perto_suzu'))
    enqueue(say('hi', 800))
    enqueue(sayNpc('missao', 1400))
    enqueue(shotStep('10_suzu_missao'))
    enqueue(say('bye', 500))
    enqueue(say('/rank', 1000))
    enqueue(shotStep('11_rank_apos_covil'))

    enqueue(say('!conquistas', 1000))
    enqueue(shotStep('12_conquistas_final'))

    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      if p then log(string.format('stats finais: hp %d/%d chakra %d/%d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana())) end
      g_game.safeLogout()
      scheduleEvent(nextFn, 1500)
    end)

    scheduleEvent(runNext, 1500)
  end,
  onDeath = function() log('EVENTO onDeath -- autoReconnect deve reconectar em ~2s') end,
  onTextMessage = function(mode, text) log('msg(' .. tostring(mode) .. '): ' .. tostring(text)) end,
  onTalk = function(name, level, mode, text) log('talk: [' .. tostring(mode) .. '] ' .. tostring(name) .. ': ' .. tostring(text)) end,
  onLoginError = function(m) log('onLoginError ' .. tostring(m)) end,
  onConnectionError = function(m, c) log('onConnectionError ' .. tostring(m)) end,
})
scheduleEvent(function() shot('99_timeout'); log('TIMEOUT GERAL'); g_app.exit() end, 240000)
