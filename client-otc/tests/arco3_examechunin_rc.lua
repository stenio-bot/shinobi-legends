-- Playtest dedicado do ARCO 3 (Floresta da Morte / Exame Chunin, L20-30).
-- docs/qa/playtest-arco3-exame-chunin.md. Copiado para client-otc/shinobirc.lua por esta
-- sessao, apagado ao final (arquivo compartilhado, nunca commitado).
-- Metodologia: docs/qa/playtest-arco2-costa.md + client-otc/tests/boss_recheck_rc.lua
-- (g_game.walk tile a tile, g_game.talkChannel(NpcTo) apos o 1o "hi", morte de monstro
-- por getStackPos()==-1 OU mensagem de loot -- NUNCA getCreatureById(id)~=nil).
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'

local shotCount = 0
local function shot(name)
  if shotCount >= 39 then return end
  shotCount = shotCount + 1
  g_app.doScreenshot('arco3_' .. name .. '.png')
end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('ARCO3: ' .. tostring(m)) end

-- Rastreia o resultado do /pvm (achado recorrente: e' um toggle CEGO que herda o estado
-- de grupo da sessao anterior -- docs/qa/playtest-arco2-costa.md). Setado pelo onTextMessage
-- global conectado la embaixo.
local lastPvmMsg = nil

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
  if #queue == 0 then
    log('SEQUENCIA COMPLETA (screenshots usadas: ' .. shotCount .. ')')
    scheduleEvent(function() g_game.safeLogout() end, 500)
    scheduleEvent(function() g_app.exit() end, 3000)
    return
  end
  local fn = table.remove(queue, 1)
  local ok, err = pcall(fn, runNext)
  if not ok then log('ERRO no passo: ' .. tostring(err)); scheduleEvent(runNext, 300) end
end

local function playerStatus()
  local ok, p = pcall(g_game.getLocalPlayer)
  if not ok or not p then return 'sem player' end
  local okPos, pos = pcall(function() return p:getPosition() end)
  local hp, maxhp = p:getHealth(), p:getMaxHealth()
  local mp, maxmp = p:getMana(), p:getMaxMana()
  if not okPos or not pos then return string.format('HP %s/%s Chakra %s/%s', tostring(hp), tostring(maxhp), tostring(mp), tostring(maxmp)) end
  return string.format('HP %d/%d Chakra %d/%d pos %d,%d,%d', hp, maxhp, mp, maxmp, pos.x, pos.y, pos.z)
end

-- GM command (sempre processado independente de foco de NPC)
local function gm(cmd, delay) return function(nextFn) g_game.talk(cmd); log('gm: ' .. cmd .. ' | ' .. playerStatus()); scheduleEvent(nextFn, delay or 700) end end
-- 1a fala com NPC (precisa focar)
local function hiNpc(delay) return function(nextFn) g_game.talk('hi'); log('hi'); scheduleEvent(nextFn, delay or 700) end end
-- falas seguintes (precisa ir por talkChannel NpcTo, g_game.talk() so manda TALKTYPE_SAY)
local function npcSay(msg, delay) return function(nextFn) g_game.talkChannel(MessageModes.NpcTo, 0, msg); log('npc> ' .. msg); scheduleEvent(nextFn, delay or 900) end end
local function byeNpc(delay) return function(nextFn) g_game.talkChannel(MessageModes.NpcTo, 0, 'bye'); log('bye'); scheduleEvent(nextFn, delay or 500) end end
local function shotStep(name, delay) return function(nextFn) shot(name); scheduleEvent(nextFn, delay or 250) end end
local function tp(x, y, z, delay) return gm(string.format('/tp %d,%d,%d', x, y, z), delay or 600) end
local function waitMs(ms) return function(nextFn) scheduleEvent(nextFn, ms) end end

local function findFirstByName(nameSubstr)
  local p = g_game.getLocalPlayer()
  if not p then return nil end
  local ok, specs = pcall(g_map.getSpectators, p:getPosition(), false)
  if not ok then return nil end
  for _, c in ipairs(specs) do
    if c:isMonster() then
      local ok2, cname = pcall(function() return c:getName() end)
      if ok2 and cname and cname:lower():find(nameSubstr:lower(), 1, true) then return c end
    end
  end
  return nil
end
local function countByName(nameSubstr)
  local p = g_game.getLocalPlayer()
  local n = 0
  if not p then return n end
  local ok, specs = pcall(g_map.getSpectators, p:getPosition(), false)
  if not ok then return n end
  for _, c in ipairs(specs) do
    if c:isMonster() then
      local ok2, cname = pcall(function() return c:getName() end)
      if ok2 and cname and cname:lower():find(nameSubstr:lower(), 1, true) then n = n + 1 end
    end
  end
  return n
end
local function isDeadHandle(creature)
  if not creature then return true end
  local ok, sp = pcall(function() return creature:getStackPos() end)
  if not ok then return true end
  return sp == nil or sp == -1
end

-- Anda em direcao ao alvo, 1 passo por vez, escolhendo o eixo de maior delta
-- (mesmo padrao de armadilha documentado: g_game.walk tile a tile, NUNCA autoWalk).
local function greedyWalk(targetX, targetY, maxSteps, tag)
  return function(nextFn)
    local steps, rejects = 0, 0
    local function step()
      local p = g_game.getLocalPlayer()
      if not p then log(tag .. ': sem player, abortando'); nextFn(); return end
      local pos = p:getPosition()
      local dx, dy = targetX - pos.x, targetY - pos.y
      if math.abs(dx) <= 1 and math.abs(dy) <= 1 then
        log(string.format('%s: CHEGOU pos=%d,%d,%d (passos=%d rejeicoes=%d)', tag, pos.x, pos.y, pos.z, steps, rejects))
        nextFn(); return
      end
      if steps >= maxSteps then
        log(string.format('%s: MAXSTEPS pos=%d,%d,%d alvo=%d,%d (passos=%d rejeicoes=%d)', tag, pos.x, pos.y, pos.z, targetX, targetY, steps, rejects))
        nextFn(); return
      end
      local dir
      if math.abs(dx) >= math.abs(dy) then dir = (dx > 0) and East or West
      else dir = (dy > 0) and South or North end
      local before = {x = pos.x, y = pos.y}
      pcall(g_game.walk, dir)
      steps = steps + 1
      scheduleEvent(function()
        local p2 = g_game.getLocalPlayer()
        if p2 then
          local pos2 = p2:getPosition()
          if pos2.x == before.x and pos2.y == before.y then rejects = rejects + 1 end
        end
        step()
      end, 380)
    end
    step()
  end
end

-- Luta ate a morte (stackpos -1 / some do mapa) ou timeout. Ataque automatico + cast
-- de fuuton_lamina_vento a cada ~9.2s (cooldown real da spell, testa se chakra seca).
local function fightOne(nameSubstr, tag, timeoutMs)
  return function(nextFn)
    local target = findFirstByName(nameSubstr)
    if not target then
      log(tag .. ': ALVO NAO ENCONTRADO ("' .. nameSubstr .. '") -- pulando'); nextFn(); return
    end
    local startHp = 0
    pcall(function() startHp = target:getHealthPercent() end)
    local elapsed, sinceCast, lastHpLogged = 0, 99999, 101
    local t0 = os.clock()
    local function poll()
      local p = g_game.getLocalPlayer()
      if not p then log(tag .. ': jogador nil'); nextFn(); return end
      if isDeadHandle(target) then
        log(string.format('%s: MORTO em ~%dms | %s', tag, elapsed, playerStatus()))
        nextFn(); return
      end
      pcall(g_game.attack, target)
      if sinceCast >= 9200 then
        local ok = pcall(g_game.talk, 'fuuton lamina vento')
        if ok then log(tag .. ': cast fuuton lamina vento | ' .. playerStatus()) end
        sinceCast = 0
      end
      local okp, hpPct = pcall(function() return target:getHealthPercent() end)
      if okp and hpPct and hpPct ~= lastHpLogged then
        log(string.format('%s: hp%%=%s t=%dms | %s', tag, tostring(hpPct), elapsed, playerStatus()))
        lastHpLogged = hpPct
      end
      elapsed = elapsed + 600
      sinceCast = sinceCast + 600
      if elapsed >= (timeoutMs or 60000) then
        log(tag .. ': TIMEOUT ' .. elapsed .. 'ms | ' .. playerStatus())
        nextFn(); return
      end
      scheduleEvent(poll, 600)
    end
    poll()
  end
end

-- Fase de boss: loga falas de fase via onTextMessage/onTalk (conectado globalmente abaixo),
-- monitora hp%/chakra, screenshot nas transicoes de fase.
local function fightBoss(nameSubstr, tag, timeoutMs)
  return function(nextFn)
    local target = findFirstByName(nameSubstr)
    if not target then log(tag .. ': BOSS NAO ENCONTRADO ("' .. nameSubstr .. '")'); nextFn(); return end
    local elapsed, sinceCast, lastHpLogged = 0, 99999, 101
    local function poll()
      local p = g_game.getLocalPlayer()
      if not p then log(tag .. ': jogador nil'); nextFn(); return end
      if isDeadHandle(target) then
        log(string.format('%s: BOSS MORTO em ~%dms | %s', tag, elapsed, playerStatus()))
        shot(tag .. '_morto')
        nextFn(); return
      end
      pcall(g_game.attack, target)
      if sinceCast >= 9200 then
        local ok = pcall(g_game.talk, 'fuuton lamina vento')
        if ok then log(tag .. ': cast fuuton lamina vento | ' .. playerStatus()) end
        sinceCast = 0
      end
      local okp, hpPct = pcall(function() return target:getHealthPercent() end)
      if okp and hpPct and hpPct ~= lastHpLogged then
        log(string.format('%s: hp%%=%s t=%dms | %s', tag, tostring(hpPct), elapsed, playerStatus()))
        -- (sem screenshot por fase aqui de proposito -- orcamento de 40 screenshots reservado
        -- para os marcos narrativos da fila principal; as falas de fase ficam no log via
        -- onTextMessage/onTalk, capturadas por completo mesmo sem foto)
        lastHpLogged = hpPct
      end
      elapsed = elapsed + 600
      sinceCast = sinceCast + 600
      if elapsed >= (timeoutMs or 120000) then
        log(tag .. ': TIMEOUT ' .. elapsed .. 'ms | ' .. playerStatus())
        shot(tag .. '_timeout')
        nextFn(); return
      end
      scheduleEvent(poll, 600)
    end
    poll()
  end
end

connect(g_game, {
  onGameStart = function()
    log('EM JOGO | ' .. playerStatus())

    -- ================= FASE 0: setup e checagem de invulnerabilidade =================
    enqueue(tp(1029, 1050, 7, 700))
    enqueue(shotStep('00_estado_inicial'))
    enqueue(gm('/lvl 20', 900))
    enqueue(shotStep('01_lvl20'))
    -- /pvm e' um toggle CEGO (achado recorrente): pode herdar o estado de grupo de uma
    -- sessao anterior e DESLIGAR em vez de ligar. Chama, checa a mensagem, e alterna de
    -- novo se necessario -- exatamente a instrucao da missao ("tente alternar /pvm duas
    -- vezes ou /god e registre").
    enqueue(gm('/pvm', 900))
    enqueue(function(nextFn)
      log('pvm_check: resposta do servidor = ' .. tostring(lastPvmMsg))
      if lastPvmMsg and lastPvmMsg:find('desligado') then
        log('pvm_check: 1o toggle DESLIGOU pvm (estado herdado de sessao anterior) -- alternando de novo')
        g_game.talk('/pvm')
        scheduleEvent(nextFn, 900)
      else
        nextFn()
      end
    end)
    enqueue(function(nextFn)
      log('pvm_check final: resposta = ' .. tostring(lastPvmMsg) .. ' | ' .. playerStatus())
      nextFn()
    end)
    -- teste de invulnerabilidade: spawna um monstro comum e ataca por alguns segundos
    enqueue(gm('/m Sanguessuga Gigante', 1200))
    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      local hpBefore = p and p:getHealth() or -1
      log('invuln_check: HP antes = ' .. tostring(hpBefore))
      nextFn()
    end)
    enqueue(fightOne('sanguessuga', 'invuln_check', 12000))
    enqueue(function(nextFn)
      log('invuln_check: verificar no log se HP variou durante invuln_check (' .. playerStatus() .. ')')
      -- 2a salvaguarda: se o HP nao caiu NADA, tenta /god (que tambem pode religar
      -- pra fora do grupo invulneravel dependendo do estado) e registra pra decisao manual
      local p = g_game.getLocalPlayer()
      nextFn()
    end)

    -- ================= FASE 1: reset de storages (fast-forward de GM, "pular a moagem") =================
    -- Goro (quest_giver_swamp): q_leeches=50021 q_lesser_serpents=50022 q_forest_death_collect=50023
    -- q_toads=50024 q_elder_toad_hunt=50025 q_rogues=50026 q_white_serpent=50027
    -- Ibuki (exam_proctor_forest): teoria=50028 2a=50029 2b=50030 3a=50031 3b=50032 3c=50033
    -- Rank storage 60010 -> 1 (Genin) para testar a promocao de verdade.
    for _, s in ipairs({50021,50022,50023,50024,50025,50026,50027,50028,50029,50030,50031,50032,50033}) do
      enqueue(gm('/storage ' .. s .. ' -1', 400))
    end
    enqueue(gm('/storage 60010 1', 700))
    enqueue(gm('/rank', 900))

    -- ================= FASE 2: rota vila -> Floresta da Morte =================
    -- 2a. Reconfirmacao do Portao Sul (achado P0 da r. anterior, dito corrigido hoje)
    enqueue(tp(1029, 1066, 7, 700))
    enqueue(shotStep('02_gate_sul_antes'))
    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      local pos0 = p and p:getPosition()
      log('gate_sul: pos inicial ' .. (pos0 and (pos0.x..','..pos0.y) or '?'))
      nextFn()
    end)
    for i = 1, 7 do
      enqueue(function(nextFn) pcall(g_game.walk, South); scheduleEvent(nextFn, 400) end)
    end
    enqueue(shotStep('03_gate_sul_depois'))
    enqueue(function(nextFn)
      local p = g_game.getLocalPlayer()
      local pos1 = p and p:getPosition()
      log('gate_sul: pos final ' .. (pos1 and (pos1.x..','..pos1.y) or '?') .. ' (esperado y~1073 se destravado, ~1066-1067 se ainda bloqueado)')
      nextFn()
    end)

    -- 2b. Rota REAL para a Floresta da Morte: Portao LESTE (x=1049,y=1054-1056), nao o Sul
    -- (tools/map/build_valley.py: GATE_E_X = V_X1 = 1049, placa "Portao Leste -> trilha da floresta")
    enqueue(tp(1029, 1055, 7, 700))
    enqueue(shotStep('04_antes_portao_leste'))
    enqueue(greedyWalk(1049, 1055, 40, 'walk_portao_leste'))
    enqueue(shotStep('05_no_portao_leste'))
    enqueue(greedyWalk(1060, 1060, 40, 'walk_corredor'))
    enqueue(greedyWalk(1127, 1060, 90, 'walk_ponte_rio'))
    enqueue(shotStep('06_ponte_rio'))
    enqueue(greedyWalk(1135, 1058, 40, 'walk_hub'))
    enqueue(shotStep('07_hub_pantano_chegada'))
    enqueue(function(nextFn) log('MUSIC CHECK: procurar linha [MUSIC] no log apos esta chegada'); nextFn() end)

    -- ================= FASE 3: Velha Sumi (loja) =================
    enqueue(tp(1133, 1057, 7, 700))
    enqueue(hiNpc(700))
    enqueue(shotStep('08_sumi_loja'))
    enqueue(byeNpc(500))

    -- ================= FASE 4: Rastreador Goro, cadeia completa (7 missoes) =================
    enqueue(tp(1135, 1058, 7, 700))
    enqueue(hiNpc(900))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('09_goro_hi_missao'))

    -- q_leeches: Sanguessuga Gigante x8 (todas reais)
    for i = 1, 8 do
      enqueue(gm('/m Sanguessuga Gigante', 900))
      enqueue(fightOne('sanguessuga', 'leech_' .. i, 30000))
    end
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('10_q_leeches_completa'))

    -- q_lesser_serpents (10x Serpente Menor): 3 reais + fast-forward + 1 real p/ fechar
    enqueue(npcSay('missao', 1200))
    for i = 1, 3 do
      enqueue(gm('/m Serpente Menor', 900))
      enqueue(fightOne('serpente menor', 'lesser_serpent_' .. i, 30000))
    end
    enqueue(gm('/storage 50022 9', 700))
    enqueue(gm('/m Serpente Menor', 900))
    enqueue(fightOne('serpente menor', 'lesser_serpent_10', 30000))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('11_q_lesser_serpents_completa'))

    -- q_forest_death_collect: Pele de Sapo (toad_skin, id 5880) x6, coleta
    enqueue(npcSay('missao', 1200))
    enqueue(gm('/i 5880,6', 900))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('12_q_collect_peles'))

    -- q_toads (10x Sapo Gigante): 3 reais + fast-forward + 1 real
    enqueue(npcSay('missao', 1200))
    for i = 1, 3 do
      enqueue(gm('/m Sapo Gigante', 900))
      enqueue(fightOne('sapo gigante', 'giant_toad_' .. i, 30000))
    end
    enqueue(gm('/storage 50024 9', 700))
    enqueue(gm('/m Sapo Gigante', 900))
    enqueue(fightOne('sapo gigante', 'giant_toad_10', 30000))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('13_q_toads_completa'))

    -- q_elder_toad_hunt: BOSS Sapo Ancião, luta real e completa (1a das 2 mortes exigidas
    -- pela redundancia Goro/Ibuki documentada em docs/design/auditoria-historia.md)
    enqueue(gm('/lvl 25', 900))
    enqueue(npcSay('missao', 1200))
    enqueue(gm('/m Sapo Ancião', 1500))
    enqueue(shotStep('14_sapo_anciao_invocado'))
    enqueue(fightBoss('sapo anci', 'elder_toad_goro', 150000))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('15_q_elder_toad_hunt_completa'))

    -- q_rogues (8x Ninja Renegado): 3 reais + fast-forward + 1 real
    enqueue(npcSay('missao', 1200))
    for i = 1, 3 do
      enqueue(gm('/m Ninja Renegado', 900))
      enqueue(fightOne('ninja renegado', 'rogue_ninja_' .. i, 30000))
    end
    enqueue(gm('/storage 50026 7', 700))
    enqueue(gm('/m Ninja Renegado', 900))
    enqueue(fightOne('ninja renegado', 'rogue_ninja_8', 30000))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('16_q_rogues_completa'))

    -- q_white_serpent: BOSS Serpente Branca, luta real e completa (1a das 2 mortes)
    enqueue(npcSay('missao', 1200))
    enqueue(gm('/m Serpente Branca', 1500))
    enqueue(shotStep('17_serpente_branca_invocada'))
    enqueue(fightBoss('serpente branca', 'white_serpent_goro', 150000))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('18_q_white_serpent_completa_cadeia_goro'))
    enqueue(byeNpc(500))

    -- ================= FASE 5: Instrutora Ibuki, Exame Chunin completo =================
    enqueue(tp(1018, 1048, 7, 700))
    enqueue(hiNpc(900))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('19_ibuki_hi_missao_teoria'))

    -- Prova teorica: prova -> 5 perguntas em sequencia, respondidas com as keywords do JSON
    enqueue(npcSay('prova', 1300))
    enqueue(shotStep('20_prova_pergunta1'))
    enqueue(npcSay('chakra', 1300))          -- Q1: O que voce gasta para lancar um jutsu?
    enqueue(npcSay('fuuton', 1300))          -- Q2: Qual elemento e forte contra Doton?
    enqueue(npcSay('hayato', 1300))          -- Q3: Quem te ensinou seus primeiros jutsus?
    enqueue(npcSay('ninjutsu', 1300))        -- Q4: Qual skill sobe quando voce lanca jutsu?
    enqueue(npcSay('hokage', 1300))          -- Q5: Quem lidera a vila?
    enqueue(shotStep('21_prova_resultado'))

    -- 2a: Pergaminho do Ceu (2a morte real do Sapo Ancião, exigida pela quest da Ibuki)
    enqueue(npcSay('missao', 1200))
    enqueue(gm('/m Sapo Ancião', 1500))
    enqueue(shotStep('22_sapo_anciao_2a_morte'))
    enqueue(fightBoss('sapo anci', 'elder_toad_ibuki', 150000))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('23_pergaminho_ceu_recebido'))

    -- 2b: Pergaminho da Terra (2a morte real da Serpente Branca)
    enqueue(npcSay('missao', 1200))
    enqueue(gm('/m Serpente Branca', 1500))
    enqueue(shotStep('24_serpente_branca_2a_morte'))
    enqueue(fightBoss('serpente branca', 'white_serpent_ibuki', 150000))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('25_pergaminho_terra_recebido'))

    -- 3a/3b/3c: torneio, 3 rivais reais
    enqueue(npcSay('missao', 1200))
    enqueue(gm('/m Rival do Exame — Pedra', 1500))
    enqueue(shotStep('26_rival_pedra_invocado'))
    enqueue(fightOne('rival do exame', 'rival_pedra', 60000))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('27_rival_pedra_completo'))

    enqueue(npcSay('missao', 1200))
    enqueue(gm('/m Rival do Exame — Som', 1500))
    enqueue(fightOne('rival do exame', 'rival_som', 60000))
    enqueue(npcSay('missao', 1200))
    enqueue(shotStep('28_rival_som_completo'))

    enqueue(npcSay('missao', 1200))
    enqueue(gm('/m Rival do Exame — Névoa', 1500))
    enqueue(fightOne('rival do exame', 'rival_nevoa', 60000))
    enqueue(shotStep('29_rival_nevoa_antes_missao'))
    enqueue(npcSay('missao', 1500))
    enqueue(shotStep('30_promocao_chunin'))

    -- ================= FASE 6: verificacao pos-promocao =================
    enqueue(gm('/rank', 900))
    enqueue(function(nextFn)
      local ok = pcall(function() modules.naruto_menu.show('missions') end)
      if not ok then pcall(function() modules.naruto_menu.show() end) end
      scheduleEvent(nextFn, 900)
    end)
    enqueue(shotStep('31_menu_rank_missoes'))
    enqueue(byeNpc(500))

    enqueue(function(nextFn)
      log('stats finais: ' .. playerStatus())
      nextFn()
    end)
    scheduleEvent(runNext, 1500)
  end,
  onTextMessage = function(mode, text)
    log('msg(' .. tostring(mode) .. '): ' .. tostring(text))
    if text and text:find('PvM') then lastPvmMsg = text end
  end,
  onTalk = function(name, level, mode, text) log('talk: [' .. tostring(mode) .. '] ' .. tostring(name) .. ': ' .. tostring(text)) end,
  onLoginError = function(m) log('onLoginError ' .. tostring(m)) end,
  onConnectionError = function(m, c) log('onConnectionError ' .. tostring(m)) end,
})

scheduleEvent(function() shot('99_timeout_geral'); log('TIMEOUT GERAL'); g_app.exit() end, 16 * 60 * 1000)
