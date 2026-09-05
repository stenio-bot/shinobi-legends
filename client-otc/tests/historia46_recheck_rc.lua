-- RE-TESTE (2026-09-05, pos-fix cp1252 servidor+cliente) do que
-- docs/qa/playtest-historia-arcos4-6.md marcou como FALHA por encoding.
-- Copiado para client-otc/shinobirc.lua por uma sessao de teste e REMOVIDO ao final
-- (arquivo compartilhado -- nunca commitar). Uso:
--   cp client-otc/tests/historia46_recheck_rc.lua client-otc/shinobirc.lua
--   (rodar OTClient.app manualmente ou via script que so mate o PID que abriu)
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('historia46r_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('R46: ' .. tostring(m)) end

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

-- ===== sequenciador: fila de passos, cada um chama next() quando termina =====
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
local function shotStep(name, delay) return function(nextFn) shot(name); scheduleEvent(nextFn, delay or 200) end end
local function tp(x, y, z) return say('/tp ' .. x .. ',' .. y .. ',' .. z, 700) end

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

--- Spawna 1 monstro por vez (regra do achado #1 do playtest anterior: nunca lote),
--- ataca, e espera ele morrer (poll a cada 500ms, timeout 25s) antes de seguir.
local function spawnAndKill(monsterName, timeoutMs)
  return function(nextFn)
    g_game.talk('/m ' .. monsterName)
    log('spawn: ' .. monsterName)
    scheduleEvent(function()
      local elapsed = 0
      local function poll()
        local m = nearestMonster()
        if not m then
          log(monsterName .. ' morto/sumiu (elapsed ' .. elapsed .. 'ms)')
          nextFn()
          return
        end
        g_game.attack(m)
        elapsed = elapsed + 500
        if elapsed >= (timeoutMs or 25000) then
          log(monsterName .. ' TIMEOUT de combate')
          nextFn()
          return
        end
        scheduleEvent(poll, 500)
      end
      poll()
    end, 500)
  end
end

--- Acha o creature ESPECIFICO por nome (nao "o mais proximo qualquer") -- importante
--- pro boss porque a fase de 50% invoca uma Serpente de Magma perto, e "nearestMonster"
--- pegaria o summon em vez do boss.
local function findMonsterByName(name)
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() and c:getName() == name then return c end
  end
  return nil
end

--- Trava no creature id do boss (resolvido pelo nome logo apos o /m) e fica de olho nele
--- ate morrer OU cruzar um limiar de HP%, ignorando summons que aparecerem do lado.
--- Loga HP do boss e do jogador a cada tick (pra medir dano perdido/s antes/depois da fase).
local function fightBossUntil(tag, bossName, hpThresholdPct, timeoutMs)
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
        if not m then
          log(tag .. ': boss morto/sumiu (id ' .. tostring(bossId) .. ')')
          nextFn()
          return
        end
        g_game.attack(m)
        local hpPct = m:getHealthPercent()
        log(string.format('%s: boss hp%%=%s | player hp=%d/%d', tag, tostring(hpPct), p:getHealth(), p:getMaxHealth()))
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
    -- ==== setup: stats maximos, sem trocar personagem/elemento (nao mexer no save) ====
    enqueue(say('/god', 900))
    enqueue(say('/full', 500))
    enqueue(say('/pvm', 500)) -- liga PvM: monstros atacam de volta (precisa pra fase de furia real)

    -- ==== PASSO 3 (parcial): Ruinas -- nametag/NPC tab de Ancião Kaito ====
    enqueue(tp(1206, 1022, 7))
    enqueue(say('hi', 700))
    enqueue(sayNpc('missao', 900))
    enqueue(shotStep('01_kaito_npc_tab'))
    enqueue(say('bye', 400))

    -- ==== PASSO 3: /look de item acentuado (poção de vida média, id 7588) ====
    enqueue(say('/i 7588,1', 600))
    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      local found = nil
      if p and p.getInventoryItem then
        for slot = 1, 10 do
          local ok, it = pcall(function() return p:getInventoryItem(slot) end)
          if ok and it then found = it break end
        end
      end
      if found then
        g_game.look(found)
        log('/look disparado no item id ' .. tostring(found:getId()))
      else
        log('item da poção não encontrado no inventário pra /look')
      end
      scheduleEvent(nextFn, 800)
    end)
    enqueue(shotStep('02_look_pocao_acentuada'))

    -- ==== PASSO 1: Montanha -- Yuki, aceita q_mountain_eagles, planta pacto antigo ====
    enqueue(tp(1222, 1058, 7))
    enqueue(say('hi', 700))
    enqueue(sayNpc('missao', 900))
    enqueue(shotStep('03_yuki_missao1'))

    -- mata 3 Aguias do Trovao, 1 por vez, conferindo progresso 1/15 -> 3/15
    -- ('hi' antes de cada missao: perseguir o alvo (ranged, foge) pode tirar o jogador
    -- do raio de foco do NPC -- refoca sempre pra nao confundir "focus perdido" com bug)
    enqueue(spawnAndKill('Águia do Trovão', 20000))
    enqueue(shotStep('04_aguia_nametag_loot'))
    enqueue(say('hi', 600))
    enqueue(sayNpc('missao', 900))
    enqueue(shotStep('05_missao_1_15'))

    enqueue(spawnAndKill('Águia do Trovão', 20000))
    enqueue(say('hi', 600))
    enqueue(sayNpc('missao', 900))
    enqueue(shotStep('06_missao_2_15'))

    enqueue(spawnAndKill('Águia do Trovão', 20000))
    enqueue(say('hi', 600))
    enqueue(sayNpc('missao', 900))
    enqueue(shotStep('07_missao_3_15'))

    -- aba Missoes do menu Shinobi
    enqueue(function(nextFn)
      local ok = pcall(function() modules.naruto_menu.show() end)
      log('naruto_menu.show() -> ' .. tostring(ok))
      scheduleEvent(nextFn, 1200)
    end)
    enqueue(shotStep('08_aba_missoes'))
    enqueue(function(nextFn)
      pcall(function() modules.naruto_menu.hide() end)
      nextFn()
    end)

    -- ==== Mestre Kaji: tarefas (Aguia do Trovao) ====
    enqueue(tp(1228, 1062, 7))
    enqueue(say('hi', 700))
    enqueue(sayNpc('tarefas', 900))
    enqueue(shotStep('09_kaji_tarefas'))
    enqueue(say('bye', 400))

    -- ==== fast-track dos passos NAO relacionados a encoding (nomes sem acento ja
    -- provados OK no playtest anterior) para chegar no quiz sem gastar 30+ kills:
    -- confere 1 kill real de cada + storage pro resto. Documentado no relatorio. ====
    enqueue(tp(1222, 1058, 7))
    enqueue(say('hi', 700)) -- re-foca em Yuki (focus expira ao andar/idle)
    enqueue(say('/storage 50034 15', 600)) -- completa q_mountain_eagles (15/15 real+fast-track)
    enqueue(sayNpc('missao', 900)) -- fecha eagles
    enqueue(shotStep('10_missao_eagles_completa'))
    enqueue(sayNpc('missao', 900)) -- aceita relics
    enqueue(shotStep('11_missao_relics_aceita'))
    enqueue(say('/i 5891,8', 700)) -- 8x Pena do Trovão (thunder_feather, id 5891)
    enqueue(sayNpc('missao', 900)) -- fecha relics
    enqueue(sayNpc('missao', 900)) -- aceita oni
    enqueue(shotStep('12_missao_oni_aceita'))

    enqueue(spawnAndKill('Oni da Geleira', 20000)) -- sanity real kill (nome sem acento)
    enqueue(say('/storage 50036 10', 600))
    enqueue(say('hi', 600))
    enqueue(sayNpc('missao', 900)) -- fecha oni
    enqueue(sayNpc('missao', 900)) -- aceita serpents
    enqueue(shotStep('13_missao_serpents_aceita'))

    enqueue(spawnAndKill('Serpente de Magma', 20000)) -- sanity real kill (nome sem acento)
    enqueue(say('/storage 50037 10', 600))
    enqueue(say('hi', 600))
    enqueue(sayNpc('missao', 900)) -- fecha serpents
    enqueue(sayNpc('missao', 900)) -- aceita lore quiz
    enqueue(shotStep('14_missao_lore_aceita'))

    -- ==== PASSO 4: quiz q_mountain_lore -- responde com keywords certas ====
    enqueue(sayNpc('prova', 900))
    enqueue(shotStep('15_quiz_pergunta1'))
    enqueue(sayNpc('furia', 900)) -- Q1: "o que acontece quando um dos dois morre sozinho" -> furia/absorve
    enqueue(shotStep('16_quiz_pergunta2'))
    enqueue(sayNpc('sócio eterno', 900)) -- Q2: quem cobra preco -> Socio Eterno
    enqueue(shotStep('17_quiz_pergunta3'))
    enqueue(sayNpc('nuvem vermelha', 900)) -- Q3: quem lancou a dupla -> Nuvem Vermelha
    enqueue(shotStep('18_quiz_resultado'))
    enqueue(sayNpc('missao', 900)) -- aceita q_mountain_curse_partner
    enqueue(shotStep('19_missao_curse_partner_aceita'))
    enqueue(say('bye', 400))

    -- ==== PASSO 2: O Sócio Eterno -- fase e summon a 50% HP, fúria real (dano antes/depois) ====
    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      log('HP jogador ANTES do boss: ' .. p:getHealth() .. '/' .. p:getMaxHealth())
      nextFn()
    end)
    enqueue(say('/m O Sócio Eterno', 1200))
    enqueue(fightBossUntil('20_socio_eterno', 'O Sócio Eterno', 50, 60000))
    enqueue(shotStep('21_socio_eterno_pos_fase50'))
    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      log('HP jogador DEPOIS de cruzar 50% (fúria 1.3x deveria estar ativa): ' .. p:getHealth() .. '/' .. p:getMaxHealth())
      nextFn()
    end)
    -- continua a luta ate matar (pra testar done_text, contagem de missao e !conquistas)
    enqueue(fightBossUntil('22_socio_eterno_kill', 'O Sócio Eterno', 0, 60000))
    enqueue(shotStep('23_socio_eterno_morto'))
    enqueue(tp(1222, 1058, 7))
    enqueue(say('hi', 600))
    enqueue(sayNpc('missao', 900))
    enqueue(shotStep('24_missao_curse_partner_completa'))
    enqueue(say('!conquistas', 900))
    enqueue(shotStep('25_conquistas'))

    -- ==== estado final ====
    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      log(string.format('stats finais: hp %d/%d chakra %d/%d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana()))
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
scheduleEvent(function() shot('99_timeout'); log('TIMEOUT GERAL'); g_app.exit() end, 480000)
