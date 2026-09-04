-- Jutsus no cliente: registra o perfil de spelllist 'Shinobi' e monta a barra de acao padrao.
--
-- O OTClient so conhece as spells da Tibia (modules/gamelib/spells.lua): SpellInfo['Default']
-- + SpelllistSettings['Default']. Aqui adicionamos um SEGUNDO perfil, 'Shinobi', com os 25
-- jutsus gerados em jutsus_data.lua (tools/export_tfs.py) e a folha de icones
-- data/images/game/spells/jutsus.png (tools/spr/gen_jutsu_icons.py). Nada dos modulos
-- originais e sobrescrito: a tabela global so ganha uma chave nova.
--
-- Em onGameStart:
--   1. registra o perfil e manda o game_spelllist trocar para ele (janela "Lista de Jutsus");
--   2. garante um conjunto de hotkeys do game_actionbar por vila ("Vila da Folha", ...);
--   3. se a barra inferior 1 desse conjunto ainda estiver vazia, preenche os slots 1..N com
--      os jutsus que o personagem pode usar (vocacao + level), ordenados por level, como
--      acoes de chatText/sendAutomatically -- exatamente o que a UI grava quando voce arrasta
--      uma spell para um slot (ver ApiJson.createOrUpdateText / ActionButtonLogic).
--
-- ATENCAO DE ENCODING: ASCII puro (ver cabecalho de naruto_theme.lua).

local PROFILE = 'Shinobi'
local BOTTOM_BAR = 1 -- barra de acao inferior 1 (ids 1-3 = inferior, 4-6 = esquerda, 7-9 = direita)
local MAX_SLOTS = 12 -- F1..F12
local SETUP_DELAY = 1500 -- ms apos onGameStart: da tempo do servidor mandar level/vocacao

-- player:getVocation() devolve o clientid da vocacao (data/tfs_mapping.json -> vocation_id).
-- O game_actionbar (logics/const.lua translateVocation) e o game_spelllist mapeiam
-- VocationsClient (Knight=1, Paladin=2, Sorcerer=3, Druid=4, Monk=5) para VocationsServer
-- (base e base+4). tools/export_tfs.py grava as duas ids em cada jutsu; a tabela abaixo
-- precisa ser a mesma (CLIENT_VOC_TO_TIBIA_BASE la).
local VOC_CLIENT_TO_TIBIA_BASE = { [1] = 4, [2] = 3, [3] = 1, [4] = 2, [5] = 9 }

local registered = false

local function log(msg)
    g_logger.info('naruto_jutsus: ' .. msg)
end

--- Adiciona o perfil 'Shinobi' as tabelas globais do gamelib.
function registerJutsus()
    if registered then
        return true
    end
    if not NarutoSpellInfo or not NarutoSpelllistSettings then
        g_logger.error('naruto_jutsus: jutsus_data.lua nao carregou (rode tools/export_tfs.py)')
        return false
    end
    -- indexacao de tabela global: nao redefine SpellInfo/SpelllistSettings, so acrescenta.
    SpelllistSettings[PROFILE] = NarutoSpelllistSettings
    SpellInfo[PROFILE] = NarutoSpellInfo
    registered = true
    local n = 0
    for _ in pairs(NarutoSpellInfo) do
        n = n + 1
    end
    log(n .. ' jutsus registrados no perfil ' .. PROFILE)
    return true
end

--- Troca a janela "Lista de Jutsus" para o perfil dos jutsus.
local function applySpelllistProfile()
    local m = modules.game_spelllist
    if not m or not m.setSpelllistProfile then
        return
    end
    if m.getSpelllistProfile and m.getSpelllistProfile() == PROFILE then
        return
    end
    local ok, err = pcall(m.setSpelllistProfile, PROFILE)
    if not ok then
        g_logger.error('naruto_jutsus: setSpelllistProfile falhou: ' .. tostring(err))
    end
end

--- Jutsus que o personagem pode usar agora (vocacao da vila + level), do menor level ao maior.
function getUsableJutsus(player)
    local voc = player:getVocation()
    local base = VOC_CLIENT_TO_TIBIA_BASE[voc] or voc
    local out = {}
    for _, spell in pairs(NarutoSpellInfo or {}) do
        local vocOk = table.contains(spell.vocations, base) or table.contains(spell.vocations, base + 4)
        if vocOk and spell.level <= player:getLevel() then
            table.insert(out, spell)
        end
    end
    table.sort(out, function(a, b)
        if a.level ~= b.level then
            return a.level < b.level
        end
        return a.name < b.name
    end)
    return out
end

--- Nome do conjunto de hotkeys da vila do personagem (ASCII: vira chave em clientoptions.json).
local function hotkeySetName(player)
    local v = NarutoVillages and NarutoVillages[player:getVocation()]
    return v and v.setName or 'Shinobi'
end

--- Preenche a barra inferior 1 com os jutsus padrao, se ela ainda estiver vazia.
function setupDefaultActionBar()
    local ab = modules.game_actionbar
    if not ab or not ab.ApiJson or not ab.selectHotkeySet then
        return false
    end
    local player = g_game.getLocalPlayer()
    if not player then
        return false
    end
    local api = ab.ApiJson
    local setName = hotkeySetName(player)

    -- conjunto proprio por vila: os conjuntos que vem do cipsoft-default-options-minimal.json
    -- (Druid/Knight/...) ja trazem slots com itens/spells da Tibia.
    if ab.createHotkeySet then
        ab.createHotkeySet(setName) -- devolve false se ja existir; tudo bem
    end
    ab.selectHotkeySet(setName)

    for i = 1, MAX_SLOTS do
        if api.getMapping(BOTTOM_BAR, i) then
            log('conjunto "' .. setName .. '" ja tem slots na barra ' .. BOTTOM_BAR .. '; nada a fazer')
            return false
        end
    end

    local jutsus = getUsableJutsus(player)
    if #jutsus == 0 then
        log('nenhum jutsu disponivel para vocacao ' .. player:getVocation() .. ' level ' .. player:getLevel())
        return false
    end

    local names = {}
    for i, spell in ipairs(jutsus) do
        if i > MAX_SLOTS then
            break
        end
        -- mesmo formato que a UI grava ao arrastar uma spell para o slot
        api.createOrUpdateText(BOTTOM_BAR, i, spell.words, true)
        if api.updateActionBarHotkey then
            api.updateActionBarHotkey('TriggerActionButton_' .. BOTTOM_BAR .. '.' .. i, 'F' .. i)
        end
        table.insert(names, spell.name)
    end
    api.saveData()
    ab.selectHotkeySet(setName) -- recria os botoes da barra a partir do JSON
    log('barra ' .. BOTTOM_BAR .. ' do conjunto "' .. setName .. '" preenchida com ' .. #names ..
            ' jutsus: ' .. table.concat(names, ', '))
    return true
end

local function onGameStart()
    if not registerJutsus() then
        return
    end
    scheduleEvent(function()
        if not g_game.isOnline() then
            return
        end
        applySpelllistProfile()
        local ok, err = pcall(setupDefaultActionBar)
        if not ok then
            g_logger.error('naruto_jutsus: setupDefaultActionBar falhou: ' .. tostring(err))
        end
    end, SETUP_DELAY)
end

function initJutsus()
    registerJutsus()
    connect(g_game, { onGameStart = onGameStart })
    if g_game.isOnline() then
        onGameStart()
    end
end

function terminateJutsus()
    disconnect(g_game, { onGameStart = onGameStart })
end
