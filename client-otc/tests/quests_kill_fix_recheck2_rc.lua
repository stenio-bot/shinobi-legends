-- Re-verificação ao vivo do fix de encoding (NarutoText.utf8ToCp1252 em onKill,
-- server/generated/scripts/naruto/quests_kill.lua) para os 3 monstros/bosses do
-- Achado de jogo #2 (docs/qa/playtest-historia-arcos4-6.md) que a rodada de re-teste
-- anterior (commit bf36f7f) NÃO chegou a confirmar ao vivo: só Águia do Trovão
-- (q_mountain_eagles) e O Sócio Eterno (q_mountain_curse_partner) foram testados
-- naquela rodada. Faltam: Xamã da Maldição (q_ruins_shamans, storage 50045, count
-- 8), Marionetista das Ruínas (q_ruins_boss, storage 50047, count 1, concede
-- Jonin) e O Vigia Ilusório (q_lair_1_illusive_eye, storage 50003, count 1,
-- concede Anbu).
--
-- Método: `/storage <id> 0` zera cada quest pro estado "aceita, progresso 0" sem
-- precisar repetir a cadeia de pré-requisitos (mesma técnica documentada no
-- playtest anterior, "storage completando o resto por eficiência") -- isola
-- exatamente o trecho sob teste (onKill/NarutoQuests.talk), que é o único afetado
-- pelo bug de encoding. `/storage <id>` (sem valor) LÊ o valor atual e devolve por
-- chat -- é a prova numérica de que o contador avança a cada kill.
--
-- Cantos de spawn seguros (longe de mobs ambiente, evita "not enough room"):
--  - Câmara do Xamã (Ruínas, tools/map/build_regions.py build_ruins): sala
--    1234,1004-1245,1014, spawn ambiente do Xamã em ~(1239,1009); canto
--    (1244,1013,7) fica a 5+ tiles de distância.
--  - Salão do Marionetista (Ruínas): sala 1236,1015-1248,1035, boss ambiente em
--    (1242,1025); canto (1246,1032,7) fica a 4+/7+ tiles de distância.
--  - Sala final do Covil (1436,1000-1449,1024): canto (1449,1005,7), já usado com
--    sucesso no playtest anterior pros 4 bosses de lá (fora do alcance dos mobs
--    de corredor x<=1434 e do Ancestral da Nuvem Vermelha, raio 3 de 1444,1012).
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot('qkfix2_' .. name .. '.png') end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('QKFIX2: ' .. tostring(m)) end

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
local function readStorage(id, delay) return say('/storage ' .. id, delay or 900) end
local function setStorage(id, value, delay) return say('/storage ' .. id .. ' ' .. value, delay or 700) end

local function findMonsterByName(name)
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
    if c:isMonster() and c:getName() == name then return c end
  end
  return nil
end

--- Tenta /m até achar o monstro (retry até 4x, 1.5s entre tentativas -- cobre
--- spawn falhando por not-enough-room transitório).
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
        if attempt >= (tries or 4) then log(name .. ' NAO SPAWNOU apos ' .. attempt .. ' tentativas'); nextFn(); return end
        scheduleEvent(tryOnce, 1500)
      end, 1200)
    end
    tryOnce()
  end
end

--- Mata o monstro mais próximo com esse nome (trava por ID assim que ataca,
--- não troca de alvo). tag identifica a linha de log; timeoutMs default 20s
--- (monstros comuns, não bosses).
local function killNearest(tag, name, timeoutMs)
  return function(nextFn)
    local target = findMonsterByName(name)
    if not target then log(tag .. ': "' .. name .. '" nao encontrado -- pulando'); nextFn(); return end
    local id = target:getId()
    log(tag .. ': alvo travado id=' .. tostring(id))
    local elapsed = 0
    local function poll()
      local m = g_map.getCreatureById(id)
      local p = g_game.getLocalPlayer()
      if not p then log(tag .. ': jogador nil'); nextFn(); return end
      if not m then log(tag .. ': alvo morto/sumiu'); scheduleEvent(nextFn, 600); return end
      g_game.attack(m)
      if p:getHealthPercent() < 20 then g_game.talk('/full') end
      elapsed = elapsed + 500
      if elapsed >= (timeoutMs or 20000) then log(tag .. ': TIMEOUT'); nextFn(); return end
      scheduleEvent(poll, 500)
    end
    poll()
  end
end

--- Spawna + mata 1 unidade e lê o storage logo depois -- 1 "ciclo" completo,
--- reusado N vezes pro Xamã (8x) e 1x pros 2 bosses únicos.
local function killOneAndCheck(tag, monsterName, storageId, spawnTries)
  return function(nextFn)
    local steps = {
      spawnRetry(monsterName, spawnTries or 4),
      killNearest(tag, monsterName, 20000),
      readStorage(storageId, 900),
    }
    local i = 0
    local function step()
      i = i + 1
      if i > #steps then nextFn(); return end
      steps[i](step)
    end
    step()
  end
end

connect(g_game, {
  onGameStart = function()
    log('em jogo')
    enqueue(say('/god', 900))
    enqueue(say('/full', 500))

    -- reset limpo das 3 quests pro estado "aceita, progresso 0" (bypassa a
    -- cadeia de pre-requisitos -- so' o onKill/talk esta sob teste aqui)
    enqueue(setStorage(50045, 0)) -- q_ruins_shamans (Xama da Maldicao x8)
    enqueue(setStorage(50047, 0)) -- q_ruins_boss (Marionetista das Ruinas x1, concede Jonin)
    enqueue(setStorage(50003, 0)) -- q_lair_1_illusive_eye (O Vigia Ilusorio x1, concede Anbu)
    enqueue(shotStep('00_storages_zeradas'))

    -- ===== Xama da Maldicao x8 (q_ruins_shamans, storage 50045) =====
    enqueue(tp(1244, 1013, 7))
    enqueue(shotStep('01_camara_xama'))
    for i = 1, 8 do
      enqueue(killOneAndCheck('xama_' .. i, 'Xamã da Maldição', 50045, 4))
    end
    enqueue(shotStep('02_xama_8x_feito'))

    -- ===== Marionetista das Ruinas x1 (q_ruins_boss, storage 50047) =====
    enqueue(tp(1246, 1032, 7))
    enqueue(shotStep('03_salao_marionetista'))
    enqueue(killOneAndCheck('puppeteer', 'Marionetista das Ruínas', 50047, 4))
    enqueue(shotStep('04_puppeteer_morto'))

    -- fecha as 2 quests das Ruinas com o Anciao Kaito (2 chamadas de 'missao'
    -- -- Achado #3 do playtest: so' 1 transicao por chamada)
    enqueue(tp(1206, 1023, 7))
    enqueue(say('hi', 700))
    enqueue(sayNpc('missao', 1200))
    enqueue(shotStep('05_kaito_missao_1'))
    enqueue(sayNpc('missao', 1200))
    enqueue(shotStep('06_kaito_missao_2'))
    enqueue(say('bye', 400))
    enqueue(say('/rank', 900))
    enqueue(shotStep('07_rank_apos_ruinas'))

    -- ===== O Vigia Ilusorio x1 (q_lair_1_illusive_eye, storage 50003) =====
    enqueue(tp(1449, 1005, 7))
    enqueue(shotStep('08_covil_canto_seguro'))
    enqueue(killOneAndCheck('illusive_eye', 'O Vigia Ilusório', 50003, 4))
    enqueue(shotStep('09_illusive_eye_morto'))

    -- fecha a quest do Covil com a Capita Anbu Suzu
    enqueue(tp(1407, 1010, 7))
    enqueue(say('hi', 700))
    enqueue(sayNpc('missao', 1200))
    enqueue(shotStep('10_suzu_missao'))
    enqueue(say('bye', 400))
    enqueue(say('/rank', 900))
    enqueue(shotStep('11_rank_apos_covil'))

    enqueue(say('!conquistas', 900))
    enqueue(shotStep('12_conquistas_final'))

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
scheduleEvent(function() shot('99_timeout'); log('TIMEOUT GERAL'); g_app.exit() end, 280000)
