-- Playtest ARCO 2 -- Costa das Mares (L12-19). QA/playtester senior, 2026-09-05.
-- Conta slqa/slqa123 (GOD) usada como personagem de teste, conforme a missao:
-- /lvl 12 (nao /god -- nao maximiza skills), /pvm ligado (vulneravel a monstro real),
-- equipamento comprado na loja da regiao (nao /i de item de endgame).
-- CAVEAT documentado no relatorio: esta conta ja tinha level 100 / skills altas de
-- sessoes anteriores de playtest (nao ha como "zerar" skill via comando de GM) --
-- /lvl 12 corrige o pool de HP/chakra pro nivel certo, mas skill_sword/skill_fist/
-- maglevel ficam ACIMA do que um Genin L12 organico teria. Ver relatorio.
-- Copiado para client-otc/shinobirc.lua por esta sessao e REMOVIDO ao final.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('arco2_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('ARCO2: ' .. tostring(m)) end

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

-- ===== sequenciador =====
local queue = {}
local function enqueue(fn) table.insert(queue, fn) end
local function runNext()
  if #queue == 0 then log('SEQUENCIA COMPLETA'); scheduleEvent(function() g_app.exit() end, 3000); return end
  local fn = table.remove(queue, 1)
  local ok, err = pcall(fn, runNext)
  if not ok then log('ERRO no passo: ' .. tostring(err)); scheduleEvent(runNext, 300) end
end

local function wait(ms) return function(nextFn) scheduleEvent(nextFn, ms) end end
local function say(msg, delay) return function(nextFn) g_game.talk(msg); log('talk: ' .. msg); scheduleEvent(nextFn, delay or 500) end end
local function sayNpc(msg, delay) return function(nextFn) g_game.talkChannel(MessageModes.NpcTo, 0, msg); log('npc: ' .. msg); scheduleEvent(nextFn, delay or 700) end end
local function shotStep(name, delay) return function(nextFn) shot(name); scheduleEvent(nextFn, delay or 250) end end
local function tp(x, y, z) return say('/tp ' .. x .. ',' .. y .. ',' .. z, 800) end

local function playerStatus()
  local ok, p = pcall(g_game.getLocalPlayer)
  if not ok or not p then return 'sem player' end
  local okPos, pos = pcall(function() return p:getPosition() end)
  if not okPos or not pos then return string.format('HP %s/%s chakra %s/%s (sem pos)', tostring(p:getHealth()), tostring(p:getMaxHealth()), tostring(p:getMana()), tostring(p:getMaxMana())) end
  return string.format('HP %d/%d chakra %d/%d pos %d,%d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana(), pos.x, pos.y)
end

--- Anda N tiles numa direcao, um passo real por vez (g_game.walk -- autoWalk nao
--- acha caminho fora do minimapa conhecido, metodologia obrigatoria da missao).
local function walkSteps(dirs, stepMs)
  return function(nextFn)
    local i = 0
    local function step()
      i = i + 1
      if i > #dirs then log('walk fim: ' .. playerStatus()); nextFn(); return end
      g_game.walk(dirs[i])
      scheduleEvent(step, stepMs or 330)
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

--- Spawna 1 monstro por vez perto do jogador (so para nao perder tempo achando o
--- mob no mapa -- o combate em si e' real: dano real, HP/chakra reais, morte real
--- possivel com /pvm ligado). Mede tempo real (elapsed) e HP/chakra minimo do jogador.
local function spawnAndFight(tag, monsterName, timeoutMs)
  return function(nextFn)
    local startTick = os.clock and os.clock() or 0
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
        if p then
          local pct = math.floor(100 * p:getHealth() / maxHp)
          if pct < minHpPct then minHpPct = pct end
        end
        if not m then
          log(tag .. ': morto/sumiu em ~' .. elapsed .. 'ms | fim ' .. playerStatus() .. ' | HP min%=' .. minHpPct)
          nextFn()
          return
        end
        g_game.attack(m)
        elapsed = elapsed + 500
        if elapsed >= (timeoutMs or 30000) then
          log(tag .. ': TIMEOUT ' .. elapsed .. 'ms | ' .. playerStatus())
          nextFn()
          return
        end
        scheduleEvent(poll, 500)
      end
      poll()
    end, 500)
  end
end

--- Luta contra o boss com nome travado (ignora summons), loga fases e HP/chakra
--- do jogador a cada tick, ate morrer ou timeout.
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
        if p then
          local pct = math.floor(100 * p:getHealth() / maxHp)
          if pct < minHpPct then minHpPct = pct end
        end
        if not m then
          log(tag .. ': BOSS MORTO em ~' .. elapsed .. 'ms (TTK) | ' .. playerStatus() .. ' | HP min%=' .. minHpPct)
          shot(tag .. '_vitoria')
          nextFn()
          return
        end
        g_game.attack(m)
        local hpPct = m:getHealthPercent()
        if hpPct and hpPct < lastPhaseLogged - 5 then
          lastPhaseLogged = hpPct
          log(string.format('%s: boss hp%%=%s | %s', tag, tostring(hpPct), playerStatus()))
          if hpPct <= 62 and hpPct > 55 then shot(tag .. '_fase60') end
          if hpPct <= 27 and hpPct > 20 then shot(tag .. '_fase25') end
        end
        elapsed = elapsed + 700
        if elapsed >= (timeoutMs or 200000) then
          log(tag .. ': TIMEOUT em ' .. elapsed .. 'ms (hp%=' .. tostring(hpPct) .. ') | ' .. playerStatus())
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
    log('em jogo | ' .. playerStatus())
    enqueue(say('/lvl 12', 900))
    enqueue(say('/full', 500))
    enqueue(say('/pvm', 700))
    enqueue(function(nextFn) log('setup feito: ' .. playerStatus()); nextFn() end)

    -- ===== 1. chegada ao Portao Sul e caminhada real ate a Costa =====
    enqueue(tp(1029, 1069, 7))
    enqueue(shotStep('01_portao_sul'))
    enqueue(walkSteps(repeated(South, 21))) -- ate a bifurcacao (1029,1090)
    enqueue(shotStep('02_bifurcacao_trilha'))
    enqueue(walkSteps(repeated(South, 30))) -- ate o gate de rank (~1029,1120)
    enqueue(shotStep('03_gate_costa'))
    enqueue(walkSteps(repeated(South, 16))) -- ate a placa da vila de pescadores (~1029,1136)
    enqueue(shotStep('04_vila_pescadores'))
    enqueue(walkSteps(repeated(South, 9))) -- ate a linha dos NPCs (~1029,1145)
    enqueue(shotStep('05_praia_npcs'))

    -- ===== 2. Ancião Tazu: cadeia de missoes =====
    enqueue(walkSteps(repeated(East, 3))) -- 1032,1145
    enqueue(say('hi', 800))
    enqueue(sayNpc('missao', 1000))
    enqueue(shotStep('06_tazu_missao1'))

    enqueue(spawnAndFight('merc1', 'Mercenário da Ponte', 25000))
    enqueue(say('hi', 600)) enqueue(sayNpc('missao', 900))
    enqueue(spawnAndFight('merc2', 'Mercenário da Ponte', 25000))
    enqueue(say('hi', 600)) enqueue(sayNpc('missao', 900))
    enqueue(spawnAndFight('merc3', 'Mercenário da Ponte', 25000))
    enqueue(shotStep('07_mercenarios_progresso'))
    -- fast-track dos 5 restantes (mesmo mob, mesmo padrao ja confirmado 3x reais)
    enqueue(say('/storage 50100 8', 600))
    enqueue(say('hi', 600)) enqueue(sayNpc('missao', 900)) -- fecha mercenarios
    enqueue(shotStep('08_mercenarios_completo'))
    enqueue(sayNpc('missao', 900)) -- aceita batedores
    enqueue(shotStep('09_batedores_aceito'))

    enqueue(spawnAndFight('scout1', 'Batedor da Névoa', 28000))
    enqueue(say('hi', 600)) enqueue(sayNpc('missao', 900))
    enqueue(spawnAndFight('scout2', 'Batedor da Névoa', 28000))
    enqueue(shotStep('10_batedores_progresso'))
    enqueue(say('/storage 50101 8', 600))
    enqueue(say('hi', 600)) enqueue(sayNpc('missao', 900)) -- fecha batedores
    enqueue(sayNpc('missao', 900)) -- aceita guardioes
    enqueue(shotStep('11_guardioes_aceito'))

    enqueue(spawnAndFight('guard1', 'Guardião da Neblina', 30000))
    enqueue(say('hi', 600)) enqueue(sayNpc('missao', 900))
    enqueue(spawnAndFight('guard2', 'Guardião da Neblina', 30000))
    enqueue(shotStep('12_guardioes_progresso'))
    enqueue(say('/storage 50102 8', 600))
    enqueue(say('hi', 600)) enqueue(sayNpc('missao', 900)) -- fecha guardioes
    enqueue(sayNpc('missao', 900)) -- aceita aprendiz mascarado
    enqueue(shotStep('13_aprendiz_aceito'))

    enqueue(spawnAndFight('apprentice1', 'Aprendiz Mascarado', 40000))
    enqueue(say('hi', 600)) enqueue(sayNpc('missao', 900))
    enqueue(spawnAndFight('apprentice2', 'Aprendiz Mascarado', 40000))
    enqueue(shotStep('14_aprendiz_progresso'))
    enqueue(say('/storage 50103 6', 600))
    enqueue(say('hi', 600)) enqueue(sayNpc('missao', 900)) -- fecha aprendiz mascarado
    enqueue(sayNpc('missao', 900)) -- aceita boss
    enqueue(shotStep('15_boss_aceito'))

    -- ===== 3. loja do Mercador Itsuki =====
    enqueue(walkSteps(repeated(West, 6))) -- 1026,1145
    enqueue(say('hi', 800))
    enqueue(function(nextFn) local ok = pcall(function() g_game.talkChannel(MessageModes.NpcTo, 0, 'trade') end) log('itsuki trade -> ' .. tostring(ok)) scheduleEvent(nextFn, 1200) end)
    enqueue(shotStep('16_loja_itsuki'))
    enqueue(say('bye', 400))

    -- ===== 4. cais + boss Espadachim da Nevoa =====
    enqueue(walkSteps(repeated(East, 3))) -- volta pro eixo 1029
    enqueue(walkSteps(repeated(South, 3))) -- 1029,1148 entrada do cais
    enqueue(shotStep('17_cais_entrada'))
    enqueue(walkSteps(repeated(South, 15))) -- ate a plataforma do boss ~1029,1163
    enqueue(shotStep('18_ponte_plataforma'))

    enqueue(fightBoss('boss', 'Espadachim da Névoa', 200000))
    enqueue(say('hi', 700))
    enqueue(sayNpc('missao', 1200))
    enqueue(shotStep('19_tazu_done_text'))

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

scheduleEvent(function() shot('99_timeout'); log('TIMEOUT GERAL DA SESSAO'); g_app.exit() end, 18 * 60 * 1000)
