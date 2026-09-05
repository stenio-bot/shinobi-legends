-- Teste manual do modulo naruto_sounds (missao de audio, 2026-09-05).
-- Copiado para client-otc/shinobirc.lua por uma sessao de teste isolada (NAO pelo
-- tools/autotest_client.sh compartilhado - esse mata TODO OTClient.app com pkill -x,
-- o que mataria a sessao do usuario). Remova shinobirc.lua ao terminar.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'slqa'
local PASSWORD = os.getenv('SL_PASSWORD') or 'slqa123'
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('AUDIOTEST: ' .. m) end

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

connect(g_game, {
  onGameStart = function()
    log('em jogo!')
    log('naruto_sounds carregado: ' .. tostring(modules.naruto_sounds ~= nil))
    if modules.naruto_sounds then
      log('NarutoSfxCatalog entradas: ' .. tostring(modules.naruto_sounds and modules.naruto_sounds.NarutoSfxCatalog and table.size(modules.naruto_sounds.NarutoSfxCatalog) or 'nil'))
    end
    local t = 2000
    local function at(ms, fn) scheduleEvent(fn, t + ms) end

    -- IMPORTANTE: tools/install_generated.sh so escreve os arquivos em disco; o TFS
    -- 1.4.2 nao ve mudanca de script/lib sem um /reload explicito (achado real deste
    -- teste: sem isto, os casts de jutsu usavam o onCastSpell ANTIGO, sem
    -- NarutoJson.broadcastSfx, e nenhum som de jutsu tocava). /reload all recarrega
    -- spells (RELOAD_TYPE_SPELLS) e libs/data/lib (RELOAD_TYPE_GLOBAL via "all").
    at(0, function() g_game.talk('/reload all') end)
    at(1000, function() g_game.talk('/god') end)
    at(1400, function() g_game.talk('/full') end)
    at(1600, function() g_game.cancelAttack() end) -- limpa alvo de sessao de teste anterior
    at(1800, function() shot('som_01_login.png') end)

    -- (d) UI: abrir/fechar o Menu Shinobi (opcode 210, sfx_menu_open/close) + clique
    at(2200, function() modules.naruto_menu.show() end)
    at(2700, function() shot('som_02_menu_aberto.png') end)
    at(3000, function() modules.naruto_menu.hide() end)

    -- (a) jutsu: 3 elementos diferentes (sem precisar de alvo -> area/self), via
    -- opcode 210 "sfx" mandado pelo servidor no onCastSpell. 1800ms de folga apos
    -- cada /elemento para o servidor terminar NarutoCharacters.apply (forget+learn)
    -- antes do texto do cast chegar.
    at(3500, function() g_game.talk('/elemento katon') end)
    at(5300, function() g_game.talk('katon housenka') end)
    at(6000, function() shot('som_03_katon.png') end)

    at(6500, function() g_game.talk('/elemento raiton') end)
    at(8300, function() g_game.talk('raiton corrente estatica') end)
    at(9000, function() shot('som_04_raiton.png') end)

    at(9500, function() g_game.talk('/elemento doton') end)
    at(11300, function() g_game.talk('doton colapso terreno') end)
    at(12000, function() shot('som_05_doton.png') end)

    -- (b) level up (mensagem de sistema "You advanced from Level X to Level Y.")
    at(12500, function() g_game.talk('/lvl 25') end)
    at(13200, function() shot('som_06_levelup.png') end)

    -- (c) dano recebido / morte de monstro: invoca e ataca um Lobo
    at(13800, function() g_game.talk('/m Lobo') end)
    at(14500, function()
      local p = g_game.getLocalPlayer()
      local best, bestd = nil, 99
      for _, c in ipairs(g_map.getSpectators(p:getPosition(), false)) do
        if c:isMonster() then
          local d = math.max(math.abs(c:getPosition().x - p:getPosition().x), math.abs(c:getPosition().y - p:getPosition().y))
          if d < bestd then best, bestd = c, d end
        end
      end
      if best then
        g_game.attack(best)
        log('alvo: ' .. best:getName())
      else
        log('nenhum monstro perto para atacar')
      end
    end)
    at(17000, function() shot('som_07_combate.png') end)
    at(18500, function()
      g_game.cancelAttack()
      local p = g_game.getLocalPlayer()
      log(string.format('stats finais: hp %d/%d level %d', p:getHealth(), p:getMaxHealth(), p:getLevel()))
    end)
    at(19000, function() g_app.exit() end)
  end,
  onLoginError = function(msg) log('onLoginError ' .. tostring(msg)) end,
  onConnectionError = function(msg, code) log('onConnectionError ' .. tostring(msg) .. ' ' .. tostring(code)) end,
  onTextMessage = function(mode, text) log('msg[' .. tostring(mode) .. ']: ' .. tostring(text)) end,
})
scheduleEvent(function() shot('som_timeout.png'); log('timeout'); g_app.exit() end, 40000)
