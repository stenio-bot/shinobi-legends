-- Auditoria DINÂMICA de caminhabilidade. Copiado para client-otc/shinobirc.lua
-- por tools/map/run_walk_audit.sh (removido ao final). Loga em
-- screenshots/walk_audit.txt via prints capturados pelo runner (grep AUTOWALK).
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'teste'
local PASSWORD = os.getenv('SL_PASSWORD') or 'teste'
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('AUTOWALK: ' .. m) end

scheduleEvent(function()
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT)
  field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin()
  log('doLogin enviado (' .. ACCOUNT .. ')')
end, 2500)
scheduleEvent(function()
  if not g_game.isOnline() then
    local ok, err = pcall(CharacterList.doLogin)
    log('CharacterList.doLogin -> ' .. tostring(ok) .. ' ' .. tostring(err))
  end
end, 7000)

-- rota do templo ate a torre da Floresta da Morte, em SALTOS CURTOS (<=6 tiles,
-- dentro do raio de visao do cliente — autoWalk pra um alvo fora da tela
-- sempre falha com NoWay mesmo sem bug nenhum de mapa, entao a auditoria
-- precisa avançar em saltos pequenos, como um jogador clicando na tela)
local ROUTE = {
  {1029, 1046, 7, 'porta do templo'},
  {1029, 1050, 7, 'praca'},
  {1029, 1056, 7, 'rua (cruzamento leste-oeste)'},
  {1029, 1062, 7, 'rua sul'},
  {1029, 1069, 7, 'portao sul'},
  {1029, 1075, 7, 'trilha (fora do portao)'},
  {1029, 1080, 7, 'trilha'},
  {1024, 1080, 7, 'clareira oeste'},
  {1029, 1080, 7, 'trilha (volta)'},
  {1035, 1080, 7, 'trilha leste'},
  {1042, 1080, 7, 'trilha leste 2'},
  {1050, 1080, 7, 'clareira leste'},
  {1058, 1084, 7, 'mata a sudeste'},
  {1066, 1088, 7, 'mata a sudeste 2'},
  {1074, 1092, 7, 'mata a sudeste 3'},
  {1082, 1096, 7, 'mata a sudeste 4'},
  {1090, 1097, 7, 'aproximacao acampamento'},
  {1096, 1096, 7, 'borda acampamento'},
  {1100, 1090, 7, 'acampamento'},
  {1105, 1082, 7, 'saida acampamento'},
  {1110, 1075, 7, 'floresta central'},
  {1116, 1068, 7, 'floresta central 2'},
  {1121, 1063, 7, 'aproximacao do rio'},
  {1124, 1060, 7, 'cabeceira da ponte'},
  {1127, 1060, 7, 'ponte'},
  {1131, 1060, 7, 'saida da ponte'},
  {1135, 1058, 7, 'hub pantano'},
  {1141, 1058, 7, 'pantano leste'},
  {1147, 1059, 7, 'pantano leste 2'},
  {1153, 1060, 7, 'aproximacao da torre'},
  {1159, 1060, 7, 'porta da torre (fora)'},
  {1163, 1060, 7, 'torre floresta da morte'},
}

local function posEq(a, b)
  return a.x == b.x and a.y == b.y and a.z == b.z
end

local function dumpTileItems(x, y, z)
  local tile = g_map.getTile({x = x, y = y, z = z})
  if not tile then return 'sem tile' end
  local items = tile:getItems()
  local ids = {}
  for _, it in ipairs(items or {}) do
    table.insert(ids, tostring(it:getId()))
  end
  return '[' .. table.concat(ids, ',') .. ']'
end

-- client ids das portas de pedra/madeira usadas nas fachadas (ver
-- build_valley.DOOR_IDS; aqui em client id, pois Item:getId() no OTClient
-- devolve o client id, nao o server id)
local DOOR_CLIENT_IDS = {[1629] = true, [1632] = true, [5098] = true, [5100] = true, [2178] = true}

local function tryOpenDoorsNear(x, y, z, radius)
  local opened = 0
  for dx = -radius, radius do
    for dy = -radius, radius do
      local p = {x = x + dx, y = y + dy, z = z}
      local tile = g_map.getTile(p)
      if tile then
        for _, it in ipairs(tile:getItems()) do
          if DOOR_CLIENT_IDS[it:getId()] then
            log(string.format('abrindo porta client_id=%d em (%d,%d,%d)', it:getId(), p.x, p.y, p.z))
            g_game.use(it)
            opened = opened + 1
          end
        end
      end
    end
  end
  return opened
end

local stuckCount = 0
local stepIdx = 0

local function tryStep()
  stepIdx = stepIdx + 1
  local wp = ROUTE[stepIdx]
  if not wp then
    log(string.format('ROTA COMPLETA travas=%d', stuckCount))
    shot('walkaudit_04_fim.png')
    scheduleEvent(function() g_app.exit() end, 500)
    return
  end
  local target = {x = wp[1], y = wp[2], z = wp[3]}
  local label = wp[4]
  local player = g_game.getLocalPlayer()
  local startPos = player:getPosition()
  log(string.format('INDO para %s (%d,%d,%d) partindo de (%d,%d,%d)',
      label, target.x, target.y, target.z, startPos.x, startPos.y, startPos.z))
  local ttile = g_map.getTile(target)
  if ttile then
    log(string.format('  alvo tile walkable=%s items=%s',
        tostring(ttile:isWalkable()), dumpTileItems(target.x, target.y, target.z)))
  else
    log('  alvo tile DESCONHECIDO pelo cliente')
  end
  -- abre portas fechadas no caminho (o teste simula um jogador, que precisa
  -- usar a porta antes de atravessar; nao e travamento de mapa)
  local doorsOpened = tryOpenDoorsNear(startPos.x, startPos.y, startPos.z, 5)
  doorsOpened = doorsOpened + tryOpenDoorsNear(target.x, target.y, target.z, 2)

  -- espera ate 9s pra chegar; verifica progresso a cada 1.5s
  local checks = 0
  local lastPos = startPos
  local function poll()
    checks = checks + 1
    local p = g_game.getLocalPlayer():getPosition()
    if posEq(p, target) then
      log(string.format('CHEGOU em %s (%d,%d,%d)', label, p.x, p.y, p.z))
      scheduleEvent(tryStep, 400)
      return
    end
    if checks >= 4 then
      -- nao chegou: travou. distingue "nao andou nada" (bloqueio real) de
      -- "andou mas nao terminou" (so lento/rota longa)
      if posEq(p, lastPos) and not posEq(p, startPos) then
        stuckCount = stuckCount + 1
        log(string.format(
            'TRAVA(parou no meio) alvo=%s pos_atual=(%d,%d,%d) itens_pos_atual=%s',
            label, p.x, p.y, p.z, dumpTileItems(p.x, p.y, p.z)))
        if stuckCount <= 3 then shot(string.format('walkaudit_trava_%d.png', stuckCount)) end
      elseif posEq(p, startPos) then
        stuckCount = stuckCount + 1
        log(string.format(
            'TRAVA(nao saiu do lugar) alvo=%s pos=(%d,%d,%d) itens=%s',
            label, p.x, p.y, p.z, dumpTileItems(p.x, p.y, p.z)))
        if stuckCount <= 3 then shot(string.format('walkaudit_trava_%d.png', stuckCount)) end
      else
        log(string.format('SEGUE (nao chegou ainda) alvo=%s pos=(%d,%d,%d)', label, p.x, p.y, p.z))
      end
      scheduleEvent(tryStep, 400)
      return
    end
    lastPos = p
    scheduleEvent(poll, 1500)
  end
  -- espera a porta (se houver) processar antes do autoWalk
  scheduleEvent(function()
    local ok = player:autoWalk(target)
    log('autoWalk retornou ' .. tostring(ok) .. ' (portas abertas: ' .. doorsOpened .. ')')
    scheduleEvent(poll, 1500)
  end, doorsOpened > 0 and 700 or 50)
end

local PathFindResultNames = {
  [0] = 'Ok', [1] = 'SamePosition', [2] = 'Impossible', [3] = 'TooFar', [4] = 'NoWay',
}

connect(g_game, {
  onGameStart = function()
    log('em jogo!')
    local player = g_game.getLocalPlayer()
    connect(player, {
      onPositionChange = function(creature, newPos, oldPos)
        if newPos and oldPos then
          log(string.format('POSCHANGE de (%d,%d,%d) para (%d,%d,%d)',
              oldPos.x, oldPos.y, oldPos.z, newPos.x, newPos.y, newPos.z))
        elseif newPos then
          log(string.format('POSCHANGE (spawn) para (%d,%d,%d)', newPos.x, newPos.y, newPos.z))
        end
      end,
      onAutoWalkFail = function(creature, status)
        local p = creature and creature:getPosition()
        log(string.format('AUTOWALKFAIL status=%s(%s) pos=%s',
            PathFindResultNames[status] or '?', tostring(status),
            p and string.format('(%d,%d,%d)', p.x, p.y, p.z) or '?'))
      end,
    })
    -- diagnostico direto de tiles de saida do templo (porta sul em 1029,1046)
    for dy = 0, 8 do
      local p = {x = 1029, y = 1042 + dy, z = 7}
      local tile = g_map.getTile(p)
      if tile then
        log(string.format('TILE (%d,%d,%d) walkable=%s items=%s',
            p.x, p.y, p.z, tostring(tile:isWalkable()), dumpTileItems(p.x, p.y, p.z)))
      else
        log(string.format('TILE (%d,%d,%d) NAO CONHECIDO PELO CLIENTE (nil)', p.x, p.y, p.z))
      end
    end
    shot('walkaudit_01_spawn.png')
    scheduleEvent(function()
      local p0 = g_game.getLocalPlayer():getPosition()
      log(string.format('teste de passo manual: g_game.walk(South) de (%d,%d,%d)', p0.x, p0.y, p0.z))
      g_game.walk(South)
      scheduleEvent(function()
        local p1 = g_game.getLocalPlayer():getPosition()
        log(string.format('apos passo manual: (%d,%d,%d) moveu=%s', p1.x, p1.y, p1.z,
            tostring(p1.x ~= p0.x or p1.y ~= p0.y)))
        scheduleEvent(tryStep, 500)
      end, 2000)
    end, 800)
  end,
  onLoginError = function(msg) log('onLoginError ' .. tostring(msg)) end,
  onConnectionError = function(msg, code) log('onConnectionError ' .. tostring(msg) .. ' ' .. tostring(code)) end,
})
scheduleEvent(function() shot('walkaudit_timeout.png'); log('TIMEOUT GLOBAL'); g_app.exit() end, 300000)
