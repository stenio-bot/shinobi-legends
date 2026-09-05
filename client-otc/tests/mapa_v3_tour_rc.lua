-- Tour de validação in-game da Missão "level design + terreno" (mapa v3).
-- Copiado para client-otc/shinobirc.lua por um script temporário, removido ao final.
-- Login god/god, /god (noclip+invulnerável), /tp x,y,z por ponto, 1 screenshot cada.
local ACCOUNT = os.getenv('SL_ACCOUNT') or 'god'
local PASSWORD = os.getenv('SL_PASSWORD') or 'god'
local function shot(name) g_app.doScreenshot(name) end
local function field(id) return g_ui.getRootWidget():recursiveGetChildById(id) end
local function log(m) g_logger.info('MAPAV3: ' .. m) end

scheduleEvent(function()
  EnterGame.setDefaultServer('127.0.0.1', 7171, 1098)
  field('accountNameTextEdit'):setText(ACCOUNT)
  field('accountPasswordTextEdit'):setText(PASSWORD)
  EnterGame.doLogin()
  log('doLogin enviado (' .. ACCOUNT .. ')')
end, 2000)
scheduleEvent(function()
  if not g_game.isOnline() then
    local ok, err = pcall(CharacterList.doLogin)
    log('CharacterList.doLogin -> ' .. tostring(ok) .. ' ' .. tostring(err))
  end
end, 6000)

local POINTS = {
  {1222, 1024, 7, 'mapa_v3_01_ruinas_patio.png'},
  {1242, 1025, 7, 'mapa_v3_02_ruinas_salao_boss.png'},
  {1204, 1005, 7, 'mapa_v3_03_ruinas_camara_norte.png'},
  {1225, 1074, 7, 'mapa_v3_04_montanha_patamar_lago.png'},
  {1225, 1088, 7, 'mapa_v3_05_montanha_santuario.png'},
  {1225, 1103, 7, 'mapa_v3_06_montanha_arena_portal.png'},
  {1404, 1010, 7, 'mapa_v3_07_covil_hall.png'},
  {1414, 1009, 7, 'mapa_v3_08_covil_antecamara_sala1.png'},
  {1444, 1012, 7, 'mapa_v3_09_covil_sala_final.png'},
  {1035, 1040, 7, 'mapa_v3_10_npc_quadro_missoes.png'},
  {1030, 1067, 7, 'mapa_v3_11_npc_jiro.png'},
  {1018, 1048, 7, 'mapa_v3_12_npc_ibuki.png'},
  {1137, 1057, 7, 'mapa_v3_13_npc_ren.png'},
  {1029, 1147, 7, 'mapa_v3_14_npc_umi.png'},
  {1202, 1020, 7, 'mapa_v3_15_npc_dokan.png'},
  {1228, 1062, 7, 'mapa_v3_16_npc_kaji.png'},
  {1406, 1014, 7, 'mapa_v3_17_npc_kuro.png'},
  {1029, 1141, 7, 'mapa_v3_18_borda_dirt_sand.png'},
}

connect(g_game, {
  onGameStart = function()
    log('em jogo!')
    local t = 1500
    local function at(ms, fn) scheduleEvent(fn, t + ms) end
    at(0, function() g_game.talk('/god') end)
    local step = 700
    for i, p in ipairs(POINTS) do
      local delay = step * i
      at(delay, function()
        g_game.talk(string.format('/tp %d,%d,%d', p[1], p[2], p[3]))
        log(string.format('tp -> %d,%d,%d (%s)', p[1], p[2], p[3], p[4]))
      end)
      at(delay + 450, function()
        shot(p[4])
        log('shot ' .. p[4])
      end)
    end
    at(step * (#POINTS + 1) + 500, function()
      log('TOUR COMPLETO')
    end)
  end
})
