-- Validacao visual dos efeitos/misseis novos (tools/spr/gen_effects.py).
-- Copiado para client-otc/shinobirc.lua por uma sessao de teste e removido ao
-- final (arquivo shinobirc.lua e compartilhado -- nunca commitar).
-- Uso: cp client-otc/tests/vfx_rc.lua client-otc/shinobirc.lua && rode o OTClient.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('VFX: ' .. m) end

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

connect(g_game, {
  onGameStart = function()
    log('em jogo!')
    local t = 2000
    -- `at` monta o cronograma em ORDEM, no momento em que o script carrega (nao
    -- em runtime) -- nunca chame `at` de dentro de uma funcao ja agendada, so
    -- durante a montagem linear abaixo. Dentro de callbacks agendados use
    -- scheduleEvent(fn, ms) direto (relativo ao instante em que o callback roda).
    local function at(dt, fn) t = t + dt; scheduleEvent(fn, t) end
    local function shotSeq(prefix, n)
      for i = 1, n do at(150, function() shot(string.format('%s_%d.png', prefix, i)) end) end
    end
    local function retargetAt(dt)
      at(dt, function()
        g_game.talk('/m Bandido')
        scheduleEvent(function()
          local m = nearestMonster()
          if m then g_game.attack(m); log('alvo: ' .. m:getName()) else log('sem monstro') end
        end, 300)
      end)
    end

    at(0, function() g_game.talk('/arena') end)
    at(300, function() g_game.talk('/lvl 60') end)
    at(300, function() g_game.talk('/full') end)
    at(300, function() shot('vfx_00_spawn.png') end)

    -- kunoichi_rosa: kawarimi (fumaca) + shousen (cura) -- ambos self, sem alvo
    at(400, function() g_game.talk('/personagem kunoichi_rosa') end)
    at(300, function() g_game.talk('/jutsus') end)
    at(500, function() g_game.talk('kawarimi') end)
    shotSeq('vfx_kawarimi', 3)
    at(600, function() g_game.talk('shousen') end)
    shotSeq('vfx_heal', 3)

    -- kunoichi_armas: bunshin (clone, distinto do poof) + lamina_chakra (beam) + doku_kiri (veneno)
    at(700, function() g_game.talk('/personagem kunoichi_armas') end)
    at(300, function() g_game.talk('/jutsus') end)
    at(500, function() g_game.talk('bunshin') end)
    shotSeq('vfx_bunshin', 3)
    retargetAt(700)
    at(300, function() g_game.talk('lamina chakra') end)
    shotSeq('vfx_chakrablade', 3)
    at(700, function() g_game.talk('doku kiri') end)
    shotSeq('vfx_poison', 3)

    -- 5 elementos: projetil (precisa de alvo) + "assinatura" (area/beam mais forte)
    local ELEMENTS = {
      {id = 'katon', proj = 'katon goukakyuu', sig = 'katon karyuu endan', signame = 'dragon'},
      {id = 'suiton', proj = 'suiton mizudan', sig = 'suiton suiryuudan', signame = 'dragon'},
      {id = 'raiton', proj = 'raiton hari', sig = 'raiton lanca relampago', signame = 'lance'},
      {id = 'doton', proj = 'doton bala lama', sig = 'doton colapso terreno', signame = 'collapse'},
      {id = 'fuuton', proj = 'fuuton lamina vento', sig = 'fuuton tornado cortante', signame = 'tornado'},
    }
    for _, el in ipairs(ELEMENTS) do
      at(700, function() g_game.talk('/elemento ' .. el.id) end)
      at(300, function() g_game.talk('/jutsus') end)
      retargetAt(300)
      at(700, function() g_game.talk(el.proj) end)
      shotSeq('vfx_' .. el.id .. '_projectile', 3)
      at(700, function() g_game.talk(el.sig) end)
      shotSeq('vfx_' .. el.id .. '_' .. el.signame, 3)
    end

    at(1000, function()
      local p = g_game.getLocalPlayer()
      log(string.format('fim: hp %d/%d chakra %d/%d level %d', p:getHealth(), p:getMaxHealth(), p:getMana(), p:getMaxMana(), p:getLevel()))
    end)
    at(500, function() g_app.exit() end)
  end,
  onLoginError = function(msg) log('onLoginError ' .. tostring(msg)) end,
  onConnectionError = function(msg, code) log('onConnectionError ' .. tostring(msg) .. ' ' .. tostring(code)) end,
  onTextMessage = function(mode, text) log('msg: ' .. tostring(text)) end,
})
scheduleEvent(function() shot('vfx_timeout.png'); log('timeout'); g_app.exit() end, 120000)
