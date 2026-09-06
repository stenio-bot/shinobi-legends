-- Re-teste dedicado do achado "boss (Espadachim da Nevoa) fica preso em 0% HP sem
-- morrer, continua atacando por >180s" (docs/qa/playtest-arco2-costa.md, secao
-- "Achado inesperado: o combate NAO terminou quando o boss chegou a 0% HP").
-- Objetivo: (a) confirmar/descartar duplo spawn (natural + /m sobrepostos) via
-- contagem explicita de criaturas "espadachim" antes/depois do /m; (b) se nao for
-- duplo spawn, medir se boss_phases.lua realmente trava a morte. Roda numa area
-- vazia (/arena), NUNCA na plataforma natural da Costa (evita o proprio spawn fixo
-- de spawns_lore.json). Copiado para shinobirc.lua por esta sessao, apagado ao final.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('boss_recheck_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('BRECK: ' .. tostring(m)) end

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
local function shotStep(name, delay) return function(nextFn) shot(name); scheduleEvent(nextFn, delay or 250) end end

local function playerStatus()
  local ok, p = pcall(g_game.getLocalPlayer)
  if not ok or not p then return 'sem player' end
  local okPos, pos = pcall(function() return p:getPosition() end)
  if not okPos or not pos then return string.format('HP %s/%s', tostring(p:getHealth()), tostring(p:getMaxHealth())) end
  return string.format('HP %d/%d (%.0f%%) pos %d,%d,%d', p:getHealth(), p:getMaxHealth(), p:getHealthPercent(), pos.x, pos.y, pos.z)
end

-- Lista TODAS as criaturas visiveis cujo nome contem `nameSubstr` (substring plana,
-- sem acento, case-insensitive -- c:getName() no cliente ja vem em cp1252/ASCII pro
-- que interessa aqui). Retorna lista de {creature, id, name, hpPct, pos}.
local function findAllByName(nameSubstr)
  local out = {}
  local p = g_game.getLocalPlayer()
  if not p then return out end
  local ok, specs = pcall(g_map.getSpectators, p:getPosition(), false)
  if not ok then return out end
  for _, c in ipairs(specs) do
    if c:isMonster() then
      local ok2, cname = pcall(function() return c:getName() end)
      if ok2 and cname and cname:lower():find(nameSubstr:lower(), 1, true) then
        local pos = c:getPosition()
        table.insert(out, {creature = c, id = c:getId(), name = cname, hpPct = c:getHealthPercent(), pos = pos})
      end
    end
  end
  return out
end

local function listVisibleMonsters(tag)
  return function(nextFn)
    local p = g_game.getLocalPlayer()
    local out = {}
    if p then
      local ok, specs = pcall(g_map.getSpectators, p:getPosition(), false)
      if ok then
        for _, c in ipairs(specs) do
          if c:isMonster() then
            local ok2, cname = pcall(function() return c:getName() end)
            table.insert(out, (ok2 and cname or '?') .. '#' .. tostring(c:getId()))
          end
        end
      end
    end
    log(tag .. ': criaturas visiveis (' .. #out .. '): ' .. table.concat(out, ', '))
    nextFn()
  end
end

local function checkDuplicates(tag, nameSubstr)
  return function(nextFn)
    local found = findAllByName(nameSubstr)
    log(tag .. ': ' .. #found .. ' criatura(s) casando "' .. nameSubstr .. '"')
    for i, f in ipairs(found) do
      log(tag .. ':   #' .. i .. ' id=' .. f.id .. ' nome="' .. f.name .. '" hp%=' .. tostring(f.hpPct) ..
        ' pos=' .. f.pos.x .. ',' .. f.pos.y .. ',' .. f.pos.z)
    end
    if #found >= 2 then
      log(tag .. ': *** DUPLICIDADE CONFIRMADA *** (' .. #found .. ' instancias simultaneas de "' .. nameSubstr .. '")')
    elseif #found == 1 then
      log(tag .. ': spawn unico confirmado')
    end
    nextFn()
  end
end

-- Luta ate a morte (creature some do mapa) ou timeout. Loga a cada ~5s: HP% do
-- boss travado por ID, HP do jogador, e se o Aprendiz Mascarado esta visivel.
-- Tambem tenta castar fuuton_lamina_vento a cada ~9s (cooldown da spell) alem do
-- auto-attack continuo.
local function fightBoss(tag, bossId, timeoutMs)
  return function(nextFn)
    local elapsed = 0
    local sinceCast = 99999
    local lastHpLogged = 101
    local stuckAtZeroSince = nil
    local function poll()
      local m = bossId and g_map.getCreatureById(bossId)
      local p = g_game.getLocalPlayer()
      if not p then log(tag .. ': jogador nil, abortando'); nextFn(); return end
      if not m then
        log(tag .. ': BOSS SUMIU DO MAPA em ~' .. elapsed .. 'ms (TTK) | ' .. playerStatus())
        shot(tag .. '_morto')
        nextFn(); return
      end
      g_game.attack(m)
      if sinceCast >= 9200 then
        local ok = pcall(g_game.talk, 'fuuton lamina vento')
        if ok then log(tag .. ': cast fuuton lamina vento') end
        sinceCast = 0
      end
      local hpPct = m:getHealthPercent()
      local aprendiz = findAllByName('aprendiz')
      if elapsed % 5000 < 900 then
        log(string.format('%s: t=%dms boss_hp%%=%s | %s | aprendiz_visivel=%s(%d)', tag, elapsed,
          tostring(hpPct), playerStatus(), (#aprendiz > 0) and 'SIM' or 'nao', #aprendiz))
      end
      if hpPct and hpPct ~= lastHpLogged then
        if (lastHpLogged > 60 and hpPct <= 60) or (lastHpLogged > 25 and hpPct <= 25) then
          shot(tag .. '_fase_hp' .. hpPct)
        end
        lastHpLogged = hpPct
      end
      if hpPct and hpPct <= 1 then
        stuckAtZeroSince = stuckAtZeroSince or elapsed
        if elapsed - stuckAtZeroSince >= 15000 and (elapsed - stuckAtZeroSince) % 15000 < 900 then
          log(tag .. ': ALERTA preso em hp%=' .. tostring(hpPct) .. ' ha ' .. (elapsed - stuckAtZeroSince) .. 'ms sem sumir do mapa')
        end
      else
        stuckAtZeroSince = nil
      end
      elapsed = elapsed + 700
      sinceCast = sinceCast + 700
      if elapsed >= (timeoutMs or 240000) then
        log(tag .. ': TIMEOUT em ' .. elapsed .. 'ms (hp%=' .. tostring(hpPct) .. ') | ' .. playerStatus())
        shot(tag .. '_timeout')
        nextFn(); return
      end
      scheduleEvent(poll, 700)
    end
    poll()
  end
end

connect(g_game, {
  onGameStart = function()
    log('em jogo | ' .. playerStatus())
    enqueue(say('/pvm', 700))
    enqueue(say('/lvl 19', 900))
    enqueue(say('/full', 500))
    enqueue(say('/elemento fuuton', 900))

    -- 1. area vazia + lista de criaturas ANTES de spawnar
    enqueue(say('/arena', 1200))
    enqueue(shotStep('00_arena'))
    enqueue(listVisibleMonsters('antes_do_m'))
    enqueue(checkDuplicates('antes_do_m', 'espadachim'))

    -- 2. spawn UNICO do boss
    enqueue(say('/m Espadachim da Névoa', 2000))
    enqueue(shotStep('01_boss_invocado'))
    enqueue(checkDuplicates('logo_apos_m', 'espadachim'))

    -- trava o alvo pelo ID do PRIMEIRO (e, no caso normal, unico) match
    enqueue(function(nextFn)
      local found = findAllByName('espadachim')
      if #found == 0 then
        log('ERRO CRITICO: nenhum espadachim encontrado apos /m -- abortando luta')
        nextFn(); return
      end
      BOSS_ID = found[1].id
      log('alvo travado: id=' .. BOSS_ID .. ' nome="' .. found[1].name .. '"')
      nextFn()
    end)

    -- 3. luta ate morrer ou 240s
    enqueue(function(nextFn) fightBoss('bossfight', BOSS_ID, 240000)(nextFn) end)

    -- 4. checagem pos-combate: duplicidade + criaturas remanescentes na area
    enqueue(checkDuplicates('pos_combate', 'espadachim'))
    enqueue(listVisibleMonsters('pos_combate'))
    enqueue(shotStep('02_pos_combate'))

    -- 5. teste de controle: monstro comum de fase (Chefe dos Bandidos) na mesma area,
    --    pra ver se o travamento em 0% e generico do sistema de fases ou especifico
    --    do Espadachim/duplo-spawn.
    enqueue(say('/full', 500))
    enqueue(say('/m Chefe dos Bandidos', 2000))
    enqueue(checkDuplicates('controle_bandidos', 'chefe dos bandidos'))
    enqueue(function(nextFn)
      local found = findAllByName('chefe dos bandidos')
      if #found == 0 then log('controle: Chefe dos Bandidos NAO encontrado, pulando'); nextFn(); return end
      CTRL_ID = found[1].id
      log('controle: alvo travado id=' .. CTRL_ID)
      nextFn()
    end)
    enqueue(function(nextFn) fightBoss('controle_bandidos', CTRL_ID, 90000)(nextFn) end)
    enqueue(shotStep('03_controle_pos'))

    enqueue(function(nextFn)
      log('stats finais: ' .. playerStatus())
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

scheduleEvent(function() shot('99_timeout_geral'); log('TIMEOUT GERAL'); g_app.exit() end, 9 * 60 * 1000)
