-- Playtest ARCO 2 -- rodada 3, FOCO EXCLUSIVO no boss (Espadachim da Nevoa), depois que
-- as rodadas 1/2 nao conseguiram fechar essa etapa. Vai direto pra plataforma via /tp,
-- invoca o boss, luta ate matar (ou timeout), mede fases/TTK, depois tp pro Tazu pro
-- done_text. Copiado para shinobirc.lua por esta sessao, apagado ao final.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('arco2_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('ARCO2C: ' .. tostring(m)) end

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
local function tp(x, y, z) return say('/tp ' .. x .. ',' .. y .. ',' .. z, 900) end

local function playerStatus()
  local ok, p = pcall(g_game.getLocalPlayer)
  if not ok or not p then return 'sem player' end
  local okPos, pos = pcall(function() return p:getPosition() end)
  if not okPos or not pos then return string.format('HP %s/%s chakra %s/%s (sem pos)', tostring(p:getHealth()), tostring(p:getMaxHealth()), tostring(p:getMana()), tostring(p:getMaxMana())) end
  return string.format('HP %d/%d chakra %d/%d pos %d,%d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana(), pos.x, pos.y)
end

-- achado da rodada 3: getName() do creature (client) parece nao bater byte-a-byte com o
-- literal UTF-8 do script Lua para nomes acentuados ("Espadachim da Nevoa" nao achou o
-- boss mesmo com ele visivel na tela, nametag "Espadachim Da Nevoa"/"Da Nevoa" perto do
-- jogador) -- match por substring plana e sem acento em vez de igualdade exata.
local function findMonsterByName(nameSubstr)
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() then
      local ok, cname = pcall(function() return c:getName() end)
      if ok and cname and (cname:lower():find(nameSubstr:lower(), 1, true) or nameSubstr:lower():find(cname:lower(), 1, true)) then
        return c
      end
    end
  end
  return nil
end
local function anyBossLike()
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  local best, bestHp = nil, -1
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() then
      local ok, hp = pcall(function() return c:getHealth() end)
      if ok and hp and hp > bestHp then best, bestHp = c, hp end
    end
  end
  return best
end

local function fightBoss(tag, bossName, timeoutMs)
  return function(nextFn)
    scheduleEvent(function()
      local boss = findMonsterByName(bossName) or anyBossLike()
      local bossId = boss and boss:getId()
      if not boss then
        log(tag .. ': boss "' .. bossName .. '" NAO ENCONTRADO logo apos /m (nem por substring nem por maior HP nas redondezas)')
      else
        local ok, cname = pcall(function() return boss:getName() end)
        log(tag .. ': travado no creature id ' .. tostring(bossId) .. ' nome="' .. tostring(ok and cname or '?') .. '"')
      end
      local elapsed = 0
      local lastPhaseLogged = 101
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
        if hpPct and hpPct < lastPhaseLogged - 3 then
          lastPhaseLogged = hpPct
          log(string.format('%s: boss hp%%=%s | %s', tag, tostring(hpPct), playerStatus()))
          if hpPct <= 63 and hpPct > 55 then shot(tag .. '_fase60') end
          if hpPct <= 28 and hpPct > 20 then shot(tag .. '_fase25') end
        end
        elapsed = elapsed + 600
        if elapsed >= (timeoutMs or 180000) then log(tag .. ': TIMEOUT em ' .. elapsed .. 'ms (hp%=' .. tostring(hpPct) .. ') | ' .. playerStatus()); nextFn(); return end
        scheduleEvent(poll, 600)
      end
      poll()
    end, 700)
  end
end

connect(g_game, {
  onGameStart = function()
    log('em jogo | ' .. playerStatus())
    enqueue(say('/lvl 12', 900))
    enqueue(say('/full', 500))
    -- checa estado atual do grupo antes de mexer no pvm (rodada 2 deixou "God" invulneravel)
    enqueue(say('/pvm', 700)) -- liga vulneravel de novo

    enqueue(tp(1029, 1163, 7)) -- direto na plataforma do boss
    enqueue(shotStep('40_plataforma_antes_boss'))
    enqueue(say('/m Espadachim da Névoa', 1800))
    enqueue(shotStep('41_boss_invocado'))
    enqueue(fightBoss('bossfinal', 'Espadachim', 180000))

    enqueue(tp(1032, 1145, 7)) -- volta pro Ancião Tazu
    enqueue(say('hi', 900))
    enqueue(sayNpc('missao', 1200))
    enqueue(shotStep('42_tazu_pos_boss'))

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

scheduleEvent(function() shot('99_timeout_c'); log('TIMEOUT GERAL'); g_app.exit() end, 6 * 60 * 1000)
