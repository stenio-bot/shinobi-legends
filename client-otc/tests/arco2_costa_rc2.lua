-- Playtest ARCO 2 -- Costa das Mares, RODADA 2 (correcao pos-achado P0 do portao sul).
-- A 1a rodada (arco2_costa_rc.lua) provou que andar reto ao sul a partir do Portao Sul
-- trava no torii (1029/1030,1069-1070) -- "Nao ha espaco suficiente" repetido, jogador
-- nunca sai da vila andando. Aqui: reconfirma o bloqueio com um teste dirigido (poucos
-- passos, screenshot antes/depois), depois usa /tp para seguir o resto da missao na
-- Costa de verdade (NPCs no alcance certo, loja, boss com /m, ambiente real).
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('arco2_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('ARCO2B: ' .. tostring(m)) end

scheduleEvent(function()
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT)
  field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin()
  log('doLogin ' .. ACCOUNT)
end, 2500)
scheduleEvent(function() if not g_game.isOnline() then pcall(CharacterList.doLogin) end end, 7000)

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
local function shotStep(name, delay) return function(nextFn) shot(name); scheduleEvent(nextFn, delay or 250) end end
local function tp(x, y, z) return say('/tp ' .. x .. ',' .. y .. ',' .. z, 800) end
local function wait(ms) return function(nextFn) scheduleEvent(nextFn, ms) end end

local function playerStatus()
  local ok, p = pcall(g_game.getLocalPlayer)
  if not ok or not p then return 'sem player' end
  local okPos, pos = pcall(function() return p:getPosition() end)
  if not okPos or not pos then return string.format('HP %s/%s chakra %s/%s (sem pos)', tostring(p:getHealth()), tostring(p:getMaxHealth()), tostring(p:getMana()), tostring(p:getMaxMana())) end
  return string.format('HP %d/%d chakra %d/%d pos %d,%d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana(), pos.x, pos.y)
end

local function walkSteps(dirs, stepMs)
  return function(nextFn)
    local i = 0
    local function step()
      i = i + 1
      if i > #dirs then log('walk fim: ' .. playerStatus()); nextFn(); return end
      g_game.walk(dirs[i])
      scheduleEvent(step, stepMs or 350)
    end
    step()
  end
end
local function repeated(dir, n) local t = {} for i = 1, n do t[#t + 1] = dir end return t end

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
local function findMonsterByName(name)
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() and c:getName() == name then return c end
  end
  return nil
end

local function spawnAndFight(tag, monsterName, timeoutMs)
  return function(nextFn)
    g_game.talk('/m ' .. monsterName)
    log(tag .. ': spawn ' .. monsterName .. ' | inicio ' .. playerStatus())
    scheduleEvent(function()
      local elapsed = 0
      local minHpPct = 100
      local p0 = g_game.getLocalPlayer()
      local maxHp = p0 and p0:getMaxHealth() or 1
      local function poll()
        local m = nearestMonster()
        local p = g_game.getLocalPlayer()
        if p then local pct = math.floor(100 * p:getHealth() / maxHp); if pct < minHpPct then minHpPct = pct end end
        if not m then
          log(tag .. ': morto/sumiu em ~' .. elapsed .. 'ms | fim ' .. playerStatus() .. ' | HP min%=' .. minHpPct)
          nextFn(); return
        end
        g_game.attack(m)
        elapsed = elapsed + 500
        if elapsed >= (timeoutMs or 30000) then log(tag .. ': TIMEOUT ' .. elapsed .. 'ms | ' .. playerStatus()); nextFn(); return end
        scheduleEvent(poll, 500)
      end
      poll()
    end, 500)
  end
end

local function fightBoss(tag, bossName, timeoutMs)
  return function(nextFn)
    scheduleEvent(function()
      local boss = findMonsterByName(bossName)
      local bossId = boss and boss:getId()
      if not boss then log(tag .. ': boss "' .. bossName .. '" NAO ENCONTRADO') end
      local elapsed = 0
      local lastPhaseLogged = 100
      local minHpPct = 100
      local p0 = g_game.getLocalPlayer()
      local maxHp = p0 and p0:getMaxHealth() or 1
      local function poll()
        local m = bossId and g_map.getCreatureById(bossId)
        local p = g_game.getLocalPlayer()
        if p then local pct = math.floor(100 * p:getHealth() / maxHp); if pct < minHpPct then minHpPct = pct end end
        if not m then
          log(tag .. ': BOSS MORTO em ~' .. elapsed .. 'ms (TTK) | ' .. playerStatus() .. ' | HP min%=' .. minHpPct)
          shot(tag .. '_vitoria'); nextFn(); return
        end
        g_game.attack(m)
        local hpPct = m:getHealthPercent()
        if hpPct and hpPct < lastPhaseLogged - 4 then
          lastPhaseLogged = hpPct
          log(string.format('%s: boss hp%%=%s | %s', tag, tostring(hpPct), playerStatus()))
          if hpPct <= 64 and hpPct > 55 then shot(tag .. '_fase60') end
          if hpPct <= 29 and hpPct > 20 then shot(tag .. '_fase25') end
        end
        elapsed = elapsed + 700
        if elapsed >= (timeoutMs or 200000) then log(tag .. ': TIMEOUT em ' .. elapsed .. 'ms (hp%=' .. tostring(hpPct) .. ') | ' .. playerStatus()); nextFn(); return end
        scheduleEvent(poll, 700)
      end
      poll()
    end, 600)
  end
end

connect(g_game, {
  onGameStart = function()
    log('em jogo | ' .. playerStatus())
    enqueue(say('/lvl 12', 900))
    enqueue(say('/full', 500))
    enqueue(say('/pvm', 700))

    -- ===== 1. RECONFIRMACAO DIRIGIDA do bloqueio do Portao Sul (achado P0 da rodada 1) =====
    enqueue(tp(1029, 1067, 7))
    enqueue(shotStep('20_gate_antes'))
    enqueue(walkSteps(repeated(South, 6), 400))
    enqueue(shotStep('21_gate_depois'))
    enqueue(function(nextFn) log('CONFIRMACAO GATE: ' .. playerStatus()); nextFn() end)

    -- ===== 2. Costa das Mares de verdade (via /tp, apos o bloqueio confirmado) =====
    enqueue(tp(1029, 1130, 7)) -- dentro do gate de rank, ainda na trilha
    enqueue(shotStep('22_trilha_pos_gate_rank'))
    enqueue(walkSteps(repeated(South, 6), 350)) -- ate a placa da vila de pescadores
    enqueue(shotStep('23_vila_pescadores_real'))
    enqueue(walkSteps(repeated(South, 9), 350)) -- ate a linha dos NPCs (1029,1145)
    enqueue(shotStep('24_praia_npcs_real'))

    enqueue(walkSteps(repeated(East, 3), 350)) -- Ancião Tazu em 1032,1145
    enqueue(say('hi', 900))
    enqueue(sayNpc('missao', 1200))
    enqueue(shotStep('25_tazu_missao1_real'))

    enqueue(spawnAndFight('merc1', 'Mercenário da Ponte', 25000))
    enqueue(say('hi', 700)) enqueue(sayNpc('missao', 1000))
    enqueue(spawnAndFight('merc2', 'Mercenário da Ponte', 25000))
    enqueue(say('hi', 700)) enqueue(sayNpc('missao', 1000))
    enqueue(shotStep('26_mercenarios_progresso_real'))
    enqueue(say('/storage 50100 8', 600))
    enqueue(say('hi', 700)) enqueue(sayNpc('missao', 1000)) -- fecha mercenarios (real, NPC no alcance)
    enqueue(shotStep('27_mercenarios_completo_real'))
    enqueue(sayNpc('missao', 1000)) -- aceita batedores
    enqueue(shotStep('28_batedores_aceito_real'))

    enqueue(spawnAndFight('scout1', 'Batedor da Névoa', 28000))
    enqueue(say('hi', 700)) enqueue(sayNpc('missao', 1000))
    enqueue(say('/storage 50101 8', 600))
    enqueue(say('hi', 700)) enqueue(sayNpc('missao', 1000)) -- fecha batedores
    enqueue(sayNpc('missao', 1000)) -- aceita guardioes
    enqueue(shotStep('29_guardioes_aceito_real'))

    enqueue(spawnAndFight('guard1', 'Guardião da Neblina', 30000))
    enqueue(say('hi', 700)) enqueue(sayNpc('missao', 1000))
    enqueue(say('/storage 50102 8', 600))
    enqueue(say('hi', 700)) enqueue(sayNpc('missao', 1000)) -- fecha guardioes
    enqueue(sayNpc('missao', 1000)) -- aceita aprendiz mascarado
    enqueue(shotStep('30_aprendiz_aceito_real'))

    enqueue(spawnAndFight('apprentice1', 'Aprendiz Mascarado', 40000))
    enqueue(say('hi', 700)) enqueue(sayNpc('missao', 1000))
    enqueue(say('/storage 50103 6', 600))
    enqueue(say('hi', 700)) enqueue(sayNpc('missao', 1000)) -- fecha aprendiz mascarado
    enqueue(sayNpc('missao', 1000)) -- aceita boss
    enqueue(shotStep('31_boss_aceito_real'))
    enqueue(say('bye', 400))

    -- ===== 3. Mercador Itsuki: loja de verdade (checar wakizashi_temperado) =====
    enqueue(walkSteps(repeated(West, 6), 350)) -- 1026,1145
    enqueue(say('hi', 900))
    enqueue(shotStep('32_loja_itsuki_hi_real'))
    enqueue(function(nextFn) local ok = pcall(function() g_game.talkChannel(MessageModes.NpcTo, 0, 'trade') end) log('itsuki trade -> ' .. tostring(ok)) scheduleEvent(nextFn, 1200) end)
    enqueue(shotStep('33_loja_itsuki_trade_real'))
    enqueue(say('bye', 400))

    -- ===== 4. cais + boss Espadachim da Nevoa (com /m, no local certo) =====
    enqueue(walkSteps(repeated(East, 6), 350)) -- volta pro eixo 1029,1145
    enqueue(walkSteps(repeated(South, 3), 350)) -- 1029,1148 entrada do cais
    enqueue(shotStep('34_cais_entrada_real'))
    enqueue(walkSteps(repeated(South, 15), 350)) -- ate a plataforma ~1029,1163
    enqueue(shotStep('35_ponte_plataforma_real'))

    enqueue(say('/m Espadachim da Névoa', 1500))
    enqueue(fightBoss('boss', 'Espadachim da Névoa', 200000))
    enqueue(say('hi', 900))
    enqueue(sayNpc('missao', 1200)) -- pode nao alcancar Tazu daqui (~18 tiles) -- ver achado
    enqueue(shotStep('36_pos_boss'))

    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      if p then log('stats finais: ' .. playerStatus()) end
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

scheduleEvent(function() shot('99_timeout_b'); log('TIMEOUT GERAL'); g_app.exit() end, 12 * 60 * 1000)
