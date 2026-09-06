-- Verificacao das trilhas iniciais (Portao Leste -> Bosque Norte; anel norte -> Trilha dos Lobos)
-- andando tile a tile com g_game.walk (autoWalk nao acha caminho fora do minimapa conhecido).
-- Copiado para client-otc/shinobirc.lua e removido ao final. Esperado: chegar exatamente aos alvos.
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('WALK: '..m) end
scheduleEvent(function() EnterGame.setDefaultServer('127.0.0.1',7171,1098); field('accountNameTextEdit'):setText('god'); field('accountPasswordTextEdit'):setText('god'); EnterGame.doLogin() end, 2500)
scheduleEvent(function() if not g_game.isOnline() then pcall(CharacterList.doLogin) end end, 7000)
connect(g_game,{ onGameStart=function()
  local t=2000; local function at(ms,fn) scheduleEvent(fn,t+ms) end
  local steps={}
  for i=1,3 do steps[#steps+1]=East end
  for i=1,30 do steps[#steps+1]=North end
  for i=1,5 do steps[#steps+1]=West end
  for i=1,13 do steps[#steps+1]=North end
  at(0, function() g_game.talk('/tp 1052,1055,7') end)
  for i,d in ipairs(steps) do at(1500+i*330, function() g_game.walk(d) end) end
  at(1500+(#steps+2)*330, function() local p=g_game.getLocalPlayer():getPosition(); log('END-BosqueNorte '..p.x..','..p.y..' (esperado 1050,1012)') end)
  local t2=1500+(#steps+6)*330
  at(t2, function() g_game.talk('/tp 1055,1025,7') end)
  local steps2={}
  for i=1,43 do steps2[#steps2+1]=West end
  for i=1,12 do steps2[#steps2+1]=North end
  for i,d in ipairs(steps2) do at(t2+1000+i*330, function() g_game.walk(d) end) end
  at(t2+1000+(#steps2+2)*330, function() local p=g_game.getLocalPlayer():getPosition(); log('END-TrilhaLobos '..p.x..','..p.y..' (esperado 1012,1013)') end)
  at(t2+1000+(#steps2+6)*330, function() g_game.safeLogout() end); at(t2+1000+(#steps2+12)*330, function() g_app.exit() end)
end })
scheduleEvent(function() log('timeout'); g_app.exit() end, 90000)
