-- ---------------------------------------------------------------------------
-- Menu Shinobi (modules/naruto_menu)
--
-- Janela unica com abas: Personagem, Elemento, Jutsus e Comandos (so GM).
-- Toda a informacao vem do SERVIDOR pelo opcode estendido 210 (buffer JSON):
--
--   servidor -> cliente
--     { "type":"state", "first_time":bool, "is_gm":bool,
--       "character":"id|null", "element":"id|null", "level":N,
--       "village":"leaf|mist|cloud|sand",
--       "characters":[ {id,name,description,looktype,village,default_element,
--                       jutsus:[{id,name,words,element,type,chakra,cooldown_s}]} ],
--       "elements":[ {id,name,jutsus:[...]} ],
--       "active_jutsus":[ ...8 jutsus... ] }
--
--   cliente -> servidor
--     { "type":"select", "character":"id|null", "element":"id|null" }
--     { "type":"get_state" }
--
-- Enquanto o servidor nao mandar nada, a janela abre vazia com o aviso
-- "Aguardando servidor" e nenhum erro vai para o log.
--
-- Abrir: botao "Shinobi" no game_mainpanel, atalho Ctrl+J (Keybind) e
-- automaticamente quando chega um state com first_time = true (aba Personagem).
--
-- ATENCAO DE ENCODING: arquivo ASCII puro. As fontes do OTClient sao bitmaps
-- indexados por byte, entao acentos vao como escapes \xNN em cp1252 (mesma
-- regra de naruto_theme.lua). Nao troque por acentos literais.
-- ---------------------------------------------------------------------------

menuController = Controller:new()

local OPCODE = 210

-- paleta (copia de data/styles/50-ninja.otui; ver naruto_menu.otui)
local COLOR_GREY = '#c0c8d4'
local COLOR_GREEN = '#56a860'
local COLOR_GOLD = '#e0c070'

-- elementos: ordem, rotulo pt-BR e cor do botao. A lista de verdade (com os
-- jutsus) vem do servidor; isto e so nome/cor de exibicao.
local ELEMENTS = {
    { id = 'katon',  label = 'Fogo',    color = '#ff6a3d' },
    { id = 'suiton', label = '\xC1gua', color = '#6ec8ff' },
    { id = 'raiton', label = 'Raio',    color = '#e0c070' },
    { id = 'doton',  label = 'Terra',   color = '#a97448' },
    { id = 'fuuton', label = 'Vento',   color = '#56a860' },
}
local ELEMENT_BY_ID = {}
for _, e in ipairs(ELEMENTS) do
    ELEMENT_BY_ID[e.id] = e
end

local VILLAGES = {
    leaf = 'Vila da Folha',
    mist = 'Vila da N\xE9voa',
    cloud = 'Vila da Nuvem',
    sand = 'Vila da Areia',
}

local WAITING = 'Aguardando servidor...'

-- widgets
local menuWindow = nil
local menuButton = nil
local tabBar = nil
local charTab, elemTab, jutsuTab, missionsTab, cmdTab = nil, nil, nil, nil, nil
local charTabButton, elemTabButton, jutsuTabButton, missionsTabButton, cmdTabButton = nil, nil, nil, nil, nil
local elementButtons = {}

-- estado
local lastState = nil
local lastProgress = nil -- ultimo `progress` recebido (aba Missoes)
local pendingElement = nil -- elemento marcado na aba (ainda nao enviado)

-- noclip (GM)
local noclipEnabled = false
local noclipLastStep = 0
local NOCLIP_STEP_COOLDOWN = 300 -- ms: no maximo 1 tentativa de /tp por passo

local function log(msg)
    g_logger.info('naruto_menu: ' .. msg)
end

local function setStatus(text)
    if menuWindow then
        menuWindow.statusLabel:setText(text)
    end
end

-- ---------------------------------------------------------------------------
-- icones de jutsu: reaproveita a folha data/images/game/spells/jutsus.png.
-- jutsus_data.lua (sandbox de naruto_theme) tem NarutoSpellIcons indexado por
-- NOME e NarutoSpellInfo indexado por nome com .icon = id do jutsu (snake_case,
-- o mesmo id que o servidor manda) e .clientId = indice na folha. Aqui viramos
-- isso em id -> {x, y}. Se o id nao bater, a linha aparece sem icone (sem erro).
-- ---------------------------------------------------------------------------
local iconById = nil

local function buildIconIndex()
    if iconById then
        return iconById
    end
    iconById = {}
    local theme = modules.naruto_theme
    local icons = theme and theme.NarutoSpellIcons
    local info = (theme and theme.NarutoSpellInfo) or (SpellInfo and SpellInfo['Shinobi'])
    if not info then
        return iconById
    end
    -- guarda de sanidade contra o bug historico de icone cortado/errado: a folha
    -- jutsus.png tem exatamente #info * 32px de largura QUANDO gen_jutsu_icons.py
    -- e export_tfs.py rodam sobre o mesmo data/jutsus/*.json (tools/spr/gen_jutsu_icons.py
    -- valida isso no build; ver docs/sistemas/arte-e-sprites.md, secao "Indice de icone
    -- deterministico"). Se um dos dois ficar desatualizado (regenerado sem o outro), um
    -- x fora do intervalo amostraria pixels de outra imagem no atlas do cliente (o
    -- defeito visto em screenshots/menu_04_jutsus.png: icone de tocha/cadeado no lugar
    -- de jutsu). Em vez de mostrar lixo, cai para "sem icone".
    local maxIndex = 0
    for _ in pairs(info) do
        maxIndex = maxIndex + 1
    end
    for name, spell in pairs(info) do
        local id = spell.icon
        if id then
            local pos = icons and icons[name]
            if pos and pos.x >= 0 and pos.x < maxIndex * 32 then
                iconById[id] = { x = pos.x, y = pos.y }
            elseif spell.clientId and spell.clientId >= 0 and spell.clientId < maxIndex then
                iconById[id] = { x = spell.clientId * 32, y = 0 }
            end
        end
    end
    return iconById
end

-- ---------------------------------------------------------------------------
-- encoding: o servidor manda JSON em UTF-8, mas as fontes do OTClient sao
-- bitmaps indexados por BYTE (ttfloader.cpp gera glifos 32..255 e
-- bitmapfont.cpp indexa com static_cast<uint8_t>). Texto UTF-8 acentuado sai
-- como mojibake ("advers\xC3\xA1rio" vira "adversArio"). Entao convertemos tudo
-- que chega do servidor de UTF-8 para cp1252 - a mesma codificacao que
-- naruto_theme.lua/jutsus_data.lua usam nos escapes \xNN.
-- ---------------------------------------------------------------------------
local CP1252_EXTRA = {
    [0x20AC] = 0x80, [0x201A] = 0x82, [0x0192] = 0x83, [0x201E] = 0x84,
    [0x2026] = 0x85, [0x2020] = 0x86, [0x2021] = 0x87, [0x02C6] = 0x88,
    [0x2030] = 0x89, [0x0160] = 0x8A, [0x2039] = 0x8B, [0x0152] = 0x8C,
    [0x017D] = 0x8E, [0x2018] = 0x91, [0x2019] = 0x92, [0x201C] = 0x93,
    [0x201D] = 0x94, [0x2022] = 0x95, [0x2013] = 0x96, [0x2014] = 0x97,
    [0x02DC] = 0x98, [0x2122] = 0x99, [0x0161] = 0x9A, [0x203A] = 0x9B,
    [0x0153] = 0x9C, [0x017E] = 0x9E, [0x0178] = 0x9F,
}

-- Byte de continuacao UTF-8 valido (0x80-0xBF)? Sem essa checagem, um 'a' cp1252 (0xE3)
-- seguido de 'o' era lido como sequencia de 3 bytes e string.char explodia (2026-09-05:
-- o servidor passou a mandar as strings ja em cp1252, ver tools/export_tfs.py _lua_cp1252).
local function isCont(s, k)
    local c = s:byte(k)
    return c ~= nil and c >= 0x80 and c <= 0xBF
end

local function utf8ToCp1252(str)
    if not str:find('[\128-\255]') then
        return str -- ASCII puro: nada a fazer (o caso do 'words' dos jutsus)
    end
    local out, i, n = {}, 1, #str
    while i <= n do
        local b = str:byte(i)
        local cp, len
        if b < 0x80 then
            cp, len = b, 1
        elseif b >= 0xC2 and b <= 0xDF and isCont(str, i + 1) then
            cp, len = (b - 0xC0) * 64 + (str:byte(i + 1) - 0x80), 2
        elseif b >= 0xE0 and b <= 0xEF and isCont(str, i + 1) and isCont(str, i + 2) then
            cp = (b - 0xE0) * 4096 + (str:byte(i + 1) - 0x80) * 64 + (str:byte(i + 2) - 0x80)
            len = 3
        else
            cp, len = b, 1 -- byte solto: passa direto (ja pode ser cp1252)
        end
        if cp <= 0xFF then
            table.insert(out, string.char(cp))
        elseif CP1252_EXTRA[cp] then
            table.insert(out, string.char(CP1252_EXTRA[cp]))
        else
            table.insert(out, '?')
        end
        i = i + len
    end
    return table.concat(out)
end

--- Converte recursivamente todas as strings de uma tabela decodificada.
local function decodeStrings(value)
    if type(value) == 'string' then
        return utf8ToCp1252(value)
    end
    if type(value) ~= 'table' then
        return value
    end
    local out = {}
    for k, v in pairs(value) do
        out[k] = decodeStrings(v)
    end
    return out
end

-- ---------------------------------------------------------------------------
-- protocolo
-- ---------------------------------------------------------------------------
local function send(tbl)
    if not g_game.isOnline() then
        return false
    end
    local ok, buffer = pcall(json.encode, tbl)
    if not ok then
        g_logger.error('naruto_menu: json.encode falhou: ' .. tostring(buffer))
        return false
    end
    menuController:sendExtendedOpcode(OPCODE, buffer)
    return true
end

function requestState()
    return send({ type = 'get_state' })
end

function sendSelect(characterId, elementId)
    return send({ type = 'select', character = characterId, element = elementId })
end

--- Pede o `progress` (aba Missoes): rank/proximo rank, tarefas ativas, diarias
--- do dia e missoes de historia. Ver server/generated/scripts/naruto/
--- character_switch.lua, NarutoCharacters.sendProgress.
function requestProgress()
    return send({ type = 'get_progress' })
end

-- ---------------------------------------------------------------------------
-- linhas de jutsu (abas Elemento e Jutsus)
-- ---------------------------------------------------------------------------
local function addJutsuRow(parent, jutsu)
    local row = g_ui.createWidget('ShinobiJutsuRow', parent)

    local pos = buildIconIndex()[jutsu.id or '']
    if pos then
        row.icon:setImageClip(string.format('%d %d 32 32', pos.x, pos.y))
    else
        row.icon:setVisible(false)
    end

    row.nameLabel:setText(jutsu.name or jutsu.id or '?')

    local parts = {}
    if jutsu.words then
        table.insert(parts, 'Selos: ' .. jutsu.words)
    end
    if jutsu.chakra then
        table.insert(parts, 'Chakra: ' .. tostring(jutsu.chakra))
    end
    if jutsu.cooldown_s then
        table.insert(parts, 'Recarga: ' .. tostring(jutsu.cooldown_s) .. 's')
    end
    if jutsu.element and ELEMENT_BY_ID[jutsu.element] then
        table.insert(parts, ELEMENT_BY_ID[jutsu.element].label)
    elseif jutsu.type then
        table.insert(parts, tostring(jutsu.type))
    end
    row.infoLabel:setText(table.concat(parts, '   '))

    if jutsu.words then
        row.useButton:setText('Usar')
        row.useButton.onClick = function()
            g_game.talk(jutsu.words)
            setStatus('Selos ditos: ' .. jutsu.words)
        end
    else
        row.useButton:setVisible(false)
    end
    return row
end

local function emptyList(list, text)
    local lbl = g_ui.createWidget('ShinobiHint', list)
    lbl:setHeight(20)
    lbl:setText(text or WAITING)
    lbl:setColor(COLOR_GREY)
end

-- ---------------------------------------------------------------------------
-- aba Personagem
-- ---------------------------------------------------------------------------
local function buildCharacterTab()
    local list = charTab.list
    list:destroyChildren()
    local state = lastState
    if not state or not state.characters or #state.characters == 0 then
        emptyList(list)
        return
    end
    for _, char in ipairs(state.characters) do
        local box = g_ui.createWidget('ShinobiCharacterBox', list)
        box.preview:setOutfit({
            type = char.looktype or 0,
            auxType = 0,
            -- looktypes 900-909 sao layers=2 (mascara de cor, tools/spr/gen_players.py) —
            -- as cores default vem do servidor (data/tfs_mapping.json.characters.*), nao
            -- mais fixas em 0/0/0/0.
            head = char.head or 0, body = char.body or 0, legs = char.legs or 0, feet = char.feet or 0,
            addons = 0, mount = 0,
        })
        box.preview:setCreatureSize(64)
        box.preview:setCenter(true)
        local creature = box.preview:getCreature()
        if creature then
            creature:setDirection(2) -- South: de frente para o jogador
        end

        local title = char.name or char.id or '?'
        if char.village and VILLAGES[char.village] then
            title = title .. '  -  ' .. VILLAGES[char.village]
        end
        box.nameLabel:setText(title)

        local desc = char.description or ''
        if char.default_element and ELEMENT_BY_ID[char.default_element] then
            desc = desc .. (desc ~= '' and '\n' or '') ..
                'Elemento padr\xE3o: ' .. ELEMENT_BY_ID[char.default_element].label
        end
        if char.jutsus then
            desc = desc .. (desc ~= '' and '\n' or '') .. #char.jutsus .. ' jutsus'
        end
        box.descLabel:setText(desc)

        if state.character ~= nil and state.character == char.id then
            box.markLabel:setText('ATUAL')
            box:setBorderColor(COLOR_GREEN)
            box.chooseButton:setText('Atual')
            box.chooseButton:setEnabled(false)
        else
            box.markLabel:setText('')
            box.chooseButton:setText('Escolher')
            box.chooseButton.onClick = function()
                sendSelect(char.id, nil)
                setStatus('Enviado: personagem "' .. (char.name or char.id) .. '".')
            end
        end
    end
end

-- ---------------------------------------------------------------------------
-- aba Elemento
-- ---------------------------------------------------------------------------
local function selectElement(elementId)
    pendingElement = elementId
    for id, btn in pairs(elementButtons) do
        btn:setChecked(id == elementId)
    end

    local list = elemTab.list
    list:destroyChildren()

    local data = nil
    if lastState and lastState.elements then
        for _, e in ipairs(lastState.elements) do
            if e.id == elementId then
                data = e
                break
            end
        end
    end
    local meta = ELEMENT_BY_ID[elementId]
    elemTab.elementTitle:setText((data and data.name) or (meta and meta.label) or tostring(elementId))
    if meta then
        elemTab.elementTitle:setColor(meta.color)
    end

    if not data or not data.jutsus or #data.jutsus == 0 then
        emptyList(list)
    else
        for _, jutsu in ipairs(data.jutsus) do
            addJutsuRow(list, jutsu)
        end
    end

    local current = lastState and lastState.element
    local isCurrent = elementId ~= nil and elementId == current
    elemTab.chooseElementButton:setEnabled(not isCurrent)
    elemTab.chooseElementButton:setText(isCurrent and 'Atual' or 'Escolher')
end

local function buildElementTab()
    local current = lastState and lastState.element
    for _, e in ipairs(ELEMENTS) do
        local btn = elementButtons[e.id]
        btn:setText(e.label .. (e.id == current and '\n(atual)' or ''))
    end
    selectElement(pendingElement or current or ELEMENTS[1].id)
end

-- ---------------------------------------------------------------------------
-- aba Jutsus
-- ---------------------------------------------------------------------------
local function fillActionBar()
    local state = lastState
    if not state or not state.active_jutsus then
        return
    end
    local words = {}
    for _, jutsu in ipairs(state.active_jutsus) do
        if jutsu.words then
            table.insert(words, jutsu.words)
        end
    end
    local theme = modules.naruto_theme
    if not theme or not theme.fillActionBarWithWords then
        setStatus('naruto_theme n\xE3o carregou: n\xE3o d\xE1 para preencher a barra.')
        return
    end
    local ok, res = pcall(theme.fillActionBarWithWords, words, 'shinobi_menu')
    if ok and res then
        setStatus('Barra de a\xE7\xE3o preenchida com ' .. #words .. ' jutsus (F1..F' .. #words .. ').')
    else
        setStatus('N\xE3o foi poss\xEDvel preencher a barra de a\xE7\xE3o.')
        if not ok then
            g_logger.error('naruto_menu: fillActionBarWithWords: ' .. tostring(res))
        end
    end
end

local function buildJutsusTab()
    local list = jutsuTab.list
    list:destroyChildren()
    local active = lastState and lastState.active_jutsus
    if not active or #active == 0 then
        emptyList(list)
        jutsuTab.fillBarButton:setEnabled(false)
        return
    end
    for _, jutsu in ipairs(active) do
        addJutsuRow(list, jutsu)
    end
    jutsuTab.fillBarButton:setEnabled(true)
end

-- ---------------------------------------------------------------------------
-- aba Missoes: rank + proximo rank, tarefas ativas, diarias do dia e missoes
-- de historia (naruto_menu.otui: ShinobiSectionHeader/ShinobiInfoRow). Tudo
-- vem do `progress` (opcode 210, ver requestProgress/onProgress).
-- ---------------------------------------------------------------------------
local function addSectionHeader(parent, text)
    local lbl = g_ui.createWidget('ShinobiSectionHeader', parent)
    lbl:setText(text)
    return lbl
end

--- opts: title, sub, status, statusColor, actionText, onAction.
local function addInfoRow(parent, opts)
    local row = g_ui.createWidget('ShinobiInfoRow', parent)
    row.titleLabel:setText(opts.title or '?')
    row.subLabel:setText(opts.sub or '')
    if opts.status then
        row.statusLabel:setText(opts.status)
        row.statusLabel:setColor(opts.statusColor or COLOR_GREY)
    end
    if opts.actionText then
        row.actionButton:setVisible(true)
        row.actionButton:setText(opts.actionText)
        row.actionButton.onClick = opts.onAction
    end
    return row
end

--- Rotulo/cor comuns aos 3 vocabularios de status que o servidor manda:
--- missoes (available/in_progress/done), tarefas (usa progress/ready direto)
--- e diarias (progress/ready/delivered).
local function progressStatusLabel(status)
    if status == 'done' or status == 'delivered' then
        return 'Conclu\xEDda', COLOR_GREEN
    elseif status == 'ready' then
        return 'PRONTA', COLOR_GOLD
    elseif status == 'in_progress' or status == 'progress' then
        return 'Em andamento', COLOR_GOLD
    end
    return 'Dispon\xEDvel', COLOR_GREY -- 'available'
end

-- ---------------------------------------------------------------------------
-- secao Conquistas (dentro da aba Missoes): X/55 no total + por categoria, lista
-- completa com desbloqueadas destacadas e progresso x/y nas contaveis. Vem do
-- mesmo `progress` (campo novo `achievements`, ver NarutoAchievements.progressJson
-- no servidor). Ordem = data/achievements.json (ja agrupado por categoria).
-- ---------------------------------------------------------------------------
local ACH_CATEGORY_LABEL = {
    exploration = 'Explora\xE7\xE3o', exam = 'Exame', quest = 'Cadeias de Hist\xF3ria',
    boss = 'Chefes', kill = 'Abates', level = 'N\xEDvel', task = 'Tarefas',
    daily = 'Di\xE1rias', collection = 'Cole\xE7\xE3o',
}

local function buildAchievementsSection(list, p)
    local achievements = p.achievements or {}
    local unlockedCount = 0
    for _, a in ipairs(achievements) do
        if a.unlocked then unlockedCount = unlockedCount + 1 end
    end
    addSectionHeader(list, 'CONQUISTAS (' .. unlockedCount .. '/' .. #achievements .. ')')
    if #achievements == 0 then
        emptyList(list, 'Sistema de conquistas indispon\xEDvel no servidor.')
        return
    end
    local lastCategory = nil
    for _, a in ipairs(achievements) do
        if a.category ~= lastCategory then
            lastCategory = a.category
            local catUnlocked, catTotal = 0, 0
            for _, b in ipairs(achievements) do
                if b.category == a.category then
                    catTotal = catTotal + 1
                    if b.unlocked then catUnlocked = catUnlocked + 1 end
                end
            end
            addInfoRow(list, {
                title = ACH_CATEGORY_LABEL[a.category] or a.category,
                sub = '',
                status = catUnlocked .. '/' .. catTotal,
                statusColor = (catUnlocked >= catTotal) and COLOR_GREEN or COLOR_GREY,
            })
        end
        local status, color
        if a.unlocked then
            status, color = 'Desbloqueada', COLOR_GREEN
        elseif a.progress ~= nil and a.count ~= nil then
            status, color = a.progress .. '/' .. a.count, COLOR_GOLD
        else
            status, color = 'Bloqueada', COLOR_GREY
        end
        addInfoRow(list, {
            title = a.name or a.id or '?',
            sub = a.description or '',
            status = status, statusColor = color,
        })
    end
end

local function buildMissionsTab()
    local list = missionsTab.list
    list:destroyChildren()
    local p = lastProgress
    if not p then
        emptyList(list, 'Aguardando servidor... (feche e abra esta aba de novo se demorar)')
        return
    end

    addSectionHeader(list, 'RANK')
    local rank = p.rank
    if not rank then
        emptyList(list, 'Sistema de rank indispon\xEDvel no servidor.')
    else
        addInfoRow(list, { title = rank.title or rank.id or '?', sub = 'Seu rank atual.' })
        local nxt = rank.next
        if not nxt then
            addInfoRow(list, { title = 'Rank m\xE1ximo alcan\xE7ado', sub = 'Voc\xEA chegou a Kage.' })
        else
            local reqs = nxt.requirements or {}
            local doneCount = 0
            for _, r in ipairs(reqs) do
                if r.done then
                    doneCount = doneCount + 1
                end
            end
            addInfoRow(list, {
                title = 'Pr\xF3ximo: ' .. (nxt.title or nxt.id or '?'),
                sub = 'N\xEDvel m\xEDnimo ' .. tostring(nxt.minLevel or '?') .. '.',
                status = doneCount .. '/' .. #reqs,
                statusColor = (doneCount >= #reqs and #reqs > 0) and COLOR_GREEN or COLOR_GOLD,
            })
            for _, r in ipairs(reqs) do
                local status, color = r.done and 'Conclu\xEDda' or 'Pendente', r.done and COLOR_GREEN or COLOR_GREY
                addInfoRow(list, {
                    title = r.name or '?',
                    sub = 'NPC: ' .. (r.npc or '?'),
                    status = status, statusColor = color,
                })
            end
        end
    end

    addSectionHeader(list, 'TAREFAS ATIVAS')
    local tasks = p.tasks or {}
    if #tasks == 0 then
        emptyList(list, 'Nenhuma tarefa aceita. Fale com um Mestre de Tarefas da regi\xE3o e diga {tarefa}.')
    else
        for _, t in ipairs(tasks) do
            local status, color
            if t.ready then
                status, color = 'PRONTA', COLOR_GOLD
            elseif (t.cooldownRemainingMin or 0) > 0 then
                status, color = t.cooldownRemainingMin .. ' min', COLOR_GREY
            else
                status, color = (t.progress or 0) .. '/' .. (t.count or 0), COLOR_GREY
            end
            addInfoRow(list, {
                title = t.name or '?',
                sub = (t.monster or '?') .. ' - entregar com ' .. (t.npc or '?'),
                status = status, statusColor = color,
            })
        end
    end

    addSectionHeader(list, 'DI\xC1RIAS DE HOJE')
    local dailies = p.dailies or {}
    if #dailies == 0 then
        emptyList(list, 'Nenhuma di\xE1ria dispon\xEDvel para o seu level hoje.')
    else
        for _, d in ipairs(dailies) do
            local status, color = progressStatusLabel(d.status)
            local row = addInfoRow(list, {
                title = d.name or '?',
                sub = (d.monster or '') .. ': ' .. (d.progress or 0) .. '/' .. (d.count or 0),
                status = status, statusColor = color,
            })
            if d.status == 'ready' then
                row.actionButton:setVisible(true)
                row.actionButton:setText('Entregar')
                row.actionButton.onClick = function()
                    g_game.talk('!diaria entregar')
                    setStatus('Comando enviado: !diaria entregar')
                    scheduleEvent(requestProgress, 500)
                end
            end
        end
    end

    addSectionHeader(list, 'MISS\xD5ES')
    local missions = p.missions or {}
    if #missions == 0 then
        emptyList(list, 'Nenhuma miss\xE3o cadastrada no servidor.')
    else
        for _, m in ipairs(missions) do
            local status, color = progressStatusLabel(m.status)
            addInfoRow(list, {
                title = m.name or '?',
                sub = 'NPC: ' .. (m.npc or '?'),
                status = status, statusColor = color,
            })
        end
    end

    buildAchievementsSection(list, p)
end

-- ---------------------------------------------------------------------------
-- aba Comandos (so GM)
-- ---------------------------------------------------------------------------
local function talk(command)
    if not g_game.isOnline() then
        return
    end
    g_game.talk(command)
    setStatus('Comando enviado: ' .. command)
end

-- ---------------------------------------------------------------------------
-- noclip (GM): atravessar paredes e arvores
--
-- COMO FUNCIONA (o truque):
--  * O TFS nao tem "noclip". O que existe e o /tp x,y,z de
--    server/tfs/data/scripts/naruto/gm_tools.lua, que so responde para GOD.
--  * Entao, quando um passo do jogador local e recusado, o cliente calcula o
--    tile de destino (posicao do jogador + direcao do passo) e manda
--    g_game.talk('/tp x,y,z') para la. O servidor teleporta 1 tile e o efeito
--    e o de ter atravessado o obstaculo.
--  * Sao DOIS gatilhos, porque um so nao cobre tudo:
--      1. LocalPlayer.onCancelWalk - src/client/localplayer.cpp faz
--         callLuaField("onCancelWalk", direction) dentro de cancelWalk().
--         Dispara quando o SERVIDOR recusa o passo (0xB5 GameServerCancelWalk):
--         PZ, criatura no caminho, "you are exhausted" etc.
--      2. Gatilho de "passo barrado pelo proprio cliente": com a feature
--         GameAllowPreWalk ligada (game_features/features.lua faz isso sempre),
--         o game_walk/walk.lua testa `toTile:isWalkable()` e da `return false`
--         ANTES de mandar qualquer coisa para o servidor. Nesse caso o cancel
--         walk nunca acontece - e esse e exatamente o caso de arvore/parede.
--         Por isso o modulo tambem escuta as teclas de andar (corelib/
--         keyboard.lua aceita varios callbacks por combo, entao isso convive
--         com o game_walk) e, se o tile de destino existe mas nao e andavel,
--         faz o /tp.
--  * Limites: 1 tentativa por passo (NOCLIP_STEP_COOLDOWN) e so para tiles que
--    existem em g_map.getTile - nao teleporta para fora do mapa carregado.
-- ---------------------------------------------------------------------------
local MOVE_KEYS = {
    { 'Up', North }, { 'Right', East }, { 'Down', South }, { 'Left', West },
    { 'Numpad8', North }, { 'Numpad9', NorthEast }, { 'Numpad6', East },
    { 'Numpad3', SouthEast }, { 'Numpad2', South }, { 'Numpad1', SouthWest },
    { 'Numpad4', West }, { 'Numpad7', NorthWest },
}

local function isGm()
    return lastState ~= nil and lastState.is_gm == true
end

--- Tenta atravessar 1 tile na direcao dada. Devolve true se mandou o /tp.
local function noclipStep(dir)
    if not noclipEnabled or not isGm() or not g_game.isOnline() then
        return false
    end
    local player = g_game.getLocalPlayer()
    if not player or player:isDead() then
        return false
    end
    if type(dir) ~= 'number' or dir < 0 or dir > 7 then
        dir = player:getDirection()
    end
    if type(dir) ~= 'number' then
        return false
    end
    local now = g_clock.millis()
    if now - noclipLastStep < NOCLIP_STEP_COOLDOWN then
        return false
    end
    local dest = Position.translatedToDirection(player:getPosition(), dir)
    if not dest or not g_map.getTile(dest) then
        return false
    end
    noclipLastStep = now
    g_game.talk(string.format('/tp %d,%d,%d', dest.x, dest.y, dest.z))
    return true
end

--- Gatilho 1: o servidor cancelou o passo.
local function onCancelWalk(player, direction)
    noclipStep(direction)
end

--- Gatilho 2: o proprio cliente barrou o passo (tile nao andavel).
--- Publico porque e exatamente o que as teclas de andar chamam - o rc de teste
--- (client-otc/shinobirc.lua) usa a mesma porta de entrada.
function noclipMoveAttempt(dir)
    if not noclipEnabled or not isGm() then
        return
    end
    if g_keyboard.getModifiers() ~= KeyboardNoModifier then
        return -- Ctrl+seta = virar, nao andar
    end
    local player = g_game.getLocalPlayer()
    if not player then
        return
    end
    local dest = Position.translatedToDirection(player:getPosition(), dir)
    local tile = dest and g_map.getTile(dest)
    if not tile or tile:isWalkable() then
        return -- passo normal: deixa o game_walk trabalhar
    end
    noclipStep(dir)
end

function setNoclip(enabled)
    noclipEnabled = enabled and true or false
    if cmdTab then
        cmdTab.noclipBox:setChecked(noclipEnabled)
    end
    setStatus(noclipEnabled and
        'Noclip ligado: andar contra um obst\xE1culo teleporta 1 tile.' or
        'Noclip desligado.')
    log('noclip = ' .. tostring(noclipEnabled))
end

function isNoclipEnabled()
    return noclipEnabled
end

-- ---------------------------------------------------------------------------
-- traducao das mensagens de sistema (barra de chat) - naruto_theme/naruto_chat.lua
--
-- Por que isto mora AQUI (no controller de prioridade 1100) e nao dentro do
-- proprio naruto_theme (prioridade 600): a lista de callbacks por "message
-- mode" (modules/gamelib/textmessages.lua, registerMessageMode/
-- messageModeCallbacks) so existe depois que game_textmessage.init() roda, e
-- game_textmessage e carregado pelo load-later de game_interface - que, pela
-- ordem de autoload de init.lua (ver docs/referencias/otclient-modulos.md),
-- só terminou de carregar quando os modulos de prioridade 1000-9999
-- (client_mods, onde entra o naruto_menu) comecam. Em naruto_theme (600) o
-- game_textmessage as vezes ainda nem existe.
--
-- COMO: desregistra o callback original (modules.game_textmessage.
-- displayMessage, acessivel de fora porque module.cpp poe cada modulo
-- sandboxed em package.loaded[nome] = modules.<nome>) de todo "message mode"
-- e registra um wrapper que traduz o texto (naruto_theme.translateMessage)
-- antes de chamar o original - o resto do pipeline (console, texto flutuante,
-- cor por tipo de item no loot etc.) continua igual, so o texto muda.
local chatHooked = false
local function hookChatTranslation()
    if chatHooked then
        return
    end
    local tm = modules.game_textmessage
    local theme = modules.naruto_theme
    if not tm or not tm.displayMessage or not tm.MessageTypes or not theme or not theme.translateMessage then
        return
    end
    local original = tm.displayMessage
    local function translated(mode, text)
        local ok, out = pcall(theme.translateMessage, text)
        return original(mode, (ok and out) or text)
    end
    local count = 0
    for mode in pairs(tm.MessageTypes) do
        unregisterMessageMode(mode, original)
        registerMessageMode(mode, translated)
        count = count + 1
    end
    chatHooked = true
    log('tradutor de mensagens de sistema instalado (' .. count .. ' modos).')
end

-- ---------------------------------------------------------------------------
-- montagem das abas
-- ---------------------------------------------------------------------------
local function createCommandsTab()
    cmdTab = g_ui.createWidget('ShinobiCommandsTab')
    cmdTab:setId('shinobiCommandsTab')
    cmdTab.hint:setText('Comandos de GM (talkactions de ' ..
        'server/tfs/data/scripts/naruto/gm_tools.lua). Esta aba s\xF3 aparece para conta GOD.')
    cmdTab.btnGod.onClick = function()
        if modules.naruto_sounds then
            modules.naruto_sounds.playClick()
        end
        talk('/god')
    end
    cmdTab.btnFull.onClick = function() talk('/full') end
    cmdTab.btnArena.onClick = function() talk('/arena') end
    cmdTab.btnPvm.onClick = function() talk('/pvm') end
    cmdTab.btnLvl50.onClick = function() talk('/lvl 50') end
    cmdTab.btnLvl100.onClick = function() talk('/lvl 100') end
    cmdTab.btnSummon:setText('/m (invocar)')
    cmdTab.btnSummon.onClick = function()
        local name = cmdTab.monsterEdit:getText():trim()
        if name ~= '' then
            talk('/m ' .. name)
        end
    end
    cmdTab.btnTp.onClick = function()
        local pos = cmdTab.posEdit:getText():trim()
        if pos ~= '' then
            talk('/tp ' .. pos)
        end
    end
    cmdTab.noclipBox:setText('Atravessar tudo (noclip)')
    cmdTab.noclipBox:setChecked(noclipEnabled)
    cmdTab.noclipBox.onCheckChange = function(widget, checked)
        if checked ~= noclipEnabled then
            setNoclip(checked)
        end
    end
    cmdTab.noclipHint:setText('Com o noclip ligado, andar contra uma parede ou \xE1rvore manda um ' ..
        '/tp para o tile de destino: 1 tentativa por passo e s\xF3 para tiles que existem no mapa. ' ..
        'Serve para o mapa inteiro ficar "desbloqueado" na sua vers\xE3o de GM.')
    return cmdTab
end

local function createTabs()
    tabBar = menuWindow.menuTabBar
    tabBar:setContentWidget(menuWindow.menuContent)

    charTab = g_ui.createWidget('ShinobiCharacterTab')
    charTab:setId('shinobiCharacterTab')
    -- o Panel que recebe as linhas fica DENTRO da ScrollablePanel (ver otui);
    -- so filhos diretos viram campo Lua do pai (UIWidget::setId), entao
    -- guardamos o atalho aqui.
    charTab.list = charTab.listArea.list
    charTabButton = tabBar:addTab('Personagem', charTab)

    elemTab = g_ui.createWidget('ShinobiElementTab')
    elemTab:setId('shinobiElementTab')
    elemTab.list = elemTab.listArea.list
    for _, e in ipairs(ELEMENTS) do
        local btn = g_ui.createWidget('ShinobiElementButton', elemTab.elementRow)
        btn:setId('element_' .. e.id)
        btn:setText(e.label)
        btn:setImageColor(e.color)
        btn.onClick = function()
            selectElement(e.id)
        end
        elementButtons[e.id] = btn
    end
    elemTab.chooseElementButton:setText('Escolher')
    elemTab.chooseElementButton.onClick = function()
        if pendingElement then
            local meta = ELEMENT_BY_ID[pendingElement]
            sendSelect(nil, pendingElement)
            setStatus('Enviado: elemento "' .. (meta and meta.label or pendingElement) .. '".')
        end
    end
    elemTabButton = tabBar:addTab('Elemento', elemTab)

    jutsuTab = g_ui.createWidget('ShinobiJutsusTab')
    jutsuTab:setId('shinobiJutsusTab')
    jutsuTab.list = jutsuTab.listArea.list
    jutsuTab.hint:setText('Seus 8 jutsus ativos. "Usar" fala os selos; ' ..
        '"Preencher barra" joga todos na barra de a\xE7\xE3o (F1..F8).')
    jutsuTab.fillBarButton:setText('Preencher barra')
    jutsuTab.fillBarButton.onClick = fillActionBar
    jutsuTabButton = tabBar:addTab('Jutsus', jutsuTab)

    missionsTab = g_ui.createWidget('ShinobiMissionsTab')
    missionsTab:setId('shinobiMissionsTab')
    missionsTab.list = missionsTab.listArea.list
    missionsTab.hint:setText('Rank, tarefas ativas, di\xE1rias de hoje, miss\xF5es de hist\xF3ria e conquistas.')
    missionsTab.refreshButton:setText('Atualizar')
    missionsTab.refreshButton.onClick = requestProgress
    missionsTabButton = tabBar:addTab('Miss\xF5es', missionsTab)

    -- pede o progress na hora de abrir a aba (o `progress` nao chega sozinho
    -- do servidor como o `state`; so sob pedido, para nao gastar banda a toa).
    local previousOnTabChange = tabBar.onTabChange
    tabBar.onTabChange = function(bar, tab)
        if previousOnTabChange then
            previousOnTabChange(bar, tab)
        end
        if tab == missionsTabButton then
            requestProgress()
        end
    end
end

-- ---------------------------------------------------------------------------
-- rank na janela de Atributos (Ctrl+S / botao "Skills"): uma linha discreta
-- "Rank: <titulo>" logo apos "Level", no mesmo estilo (SkillButton) das
-- outras linhas. NAO editamos game_skills/skills.otui: criamos o widget em
-- runtime e o inserimos na mesma lista (MiniWindowContents usa
-- layout: verticalBox, entao mover com moveChildToIndex reflui o layout
-- sozinho - ver docs/sistemas/cliente-ux.md).
-- ---------------------------------------------------------------------------
local rankRow = nil

local function updateRankDisplay()
    local rank = lastState and lastState.rank
    local skills = modules.game_skills
    local win = skills and skills.skillsWindow
    if not win then
        return -- game_skills nao carregou (nao deveria acontecer, mas nao trava por isso)
    end
    if not rankRow or rankRow:isDestroyed() then
        local levelRow = win:recursiveGetChildById('level')
        if not levelRow then
            return
        end
        local parent = levelRow:getParent()
        local idx = parent:getChildIndex(levelRow)
        rankRow = g_ui.createWidget('SkillButton', parent)
        rankRow:setId('shinobiRankRow')
        rankRow:setHeight(15)
        rankRow:setFocusable(false)
        local nameLbl = g_ui.createWidget('SkillNameLabel', rankRow)
        nameLbl:setText('Rank')
        g_ui.createWidget('SkillValueLabel', rankRow) -- id: value (ver skills.otui)
        parent:moveChildToIndex(rankRow, idx + 1)
    end
    if not rank then
        rankRow:setVisible(false)
        return
    end
    rankRow:setVisible(true)
    rankRow.value:setText(rank.title or rank.id or '?')
end

-- ---------------------------------------------------------------------------
-- state
-- ---------------------------------------------------------------------------
local function refreshAll()
    updateRankDisplay()
    if not menuWindow then
        return
    end
    buildCharacterTab()
    buildElementTab()
    buildJutsusTab()
    buildMissionsTab()

    -- a aba Comandos so existe para GM
    if isGm() and not cmdTabButton then
        cmdTabButton = tabBar:addTab('Comandos', createCommandsTab())
    elseif not isGm() and cmdTabButton then
        noclipEnabled = false
        tabBar:removeTab(cmdTabButton) -- destroi o tabPanel junto
        cmdTabButton = nil
        cmdTab = nil
    end

    local state = lastState
    if not state then
        setStatus(WAITING)
        return
    end
    local bits = {}
    if state.character then
        table.insert(bits, 'Personagem: ' .. tostring(state.character))
    end
    if state.element then
        local meta = ELEMENT_BY_ID[state.element]
        table.insert(bits, 'Elemento: ' .. (meta and meta.label or tostring(state.element)))
    end
    if state.level then
        table.insert(bits, 'Level ' .. tostring(state.level))
    end
    if state.village and VILLAGES[state.village] then
        table.insert(bits, VILLAGES[state.village])
    end
    if state.is_gm then
        table.insert(bits, 'GM')
    end
    setStatus(#bits > 0 and table.concat(bits, '   |   ') or 'Sem dados do servidor.')
end

--- Trata um state ja decodificado. Publico de proposito: enquanto o servidor
--- nao mandar o opcode 210 da para testar a UI injetando um state falso pelo rc
--- (client-otc/shinobirc.lua):
---   modules.naruto_menu.onState(json.decode(meuJson))
function onState(data)
    if type(data) ~= 'table' or data.type ~= 'state' then
        return false
    end
    lastState = decodeStrings(data)
    pendingElement = nil
    refreshAll()
    log(string.format('state recebido: %d personagens, %d elementos, %d jutsus ativos, gm=%s, first_time=%s',
        data.characters and #data.characters or 0,
        data.elements and #data.elements or 0,
        data.active_jutsus and #data.active_jutsus or 0,
        tostring(data.is_gm), tostring(data.first_time)))
    if data.first_time == true then
        show('Personagem')
    end
    return true
end

--- Trata um `progress` ja decodificado (aba Missoes). Publico pelo mesmo
--- motivo de onState: da pra testar via
---   modules.naruto_menu.onProgress(json.decode(meuJson))
function onProgress(data)
    if type(data) ~= 'table' or data.type ~= 'progress' then
        return false
    end
    lastProgress = decodeStrings(data)
    if missionsTab then
        buildMissionsTab()
    end
    log(string.format('progress recebido: rank=%s, %d tarefas, %d diarias, %d missoes',
        tostring(data.rank and data.rank.id), data.tasks and #data.tasks or 0,
        data.dailies and #data.dailies or 0, data.missions and #data.missions or 0))
    return true
end

-- data.type == 'sfx' e' despachado por modules/naruto_sounds (opcode 210 ja e'
-- registrado aqui - so pode haver 1 registerExtendedOpcode por codigo, ver
-- gamelib/protocolgame.lua - entao naruto_sounds nao registra de novo, so
-- expoe NarutoSounds.onOpcodeSfx para quem já escuta o opcode chamar).
local function onSfx(data)
    if type(data) ~= 'table' or data.type ~= 'sfx' then
        return false
    end
    if modules.naruto_sounds and modules.naruto_sounds.onOpcodeSfx then
        return modules.naruto_sounds.onOpcodeSfx(data)
    end
    return true -- reconhecido mesmo sem o modulo de audio carregado
end

local function onExtendedOpcode(protocol, code, buffer)
    local ok, data = pcall(json.decode, buffer)
    if not ok then
        g_logger.error('naruto_menu: JSON invalido no opcode ' .. OPCODE .. ': ' .. tostring(data))
        return
    end
    if onState(data) or onProgress(data) or onSfx(data) then
        return
    end
    log('mensagem ignorada (type = ' ..
        tostring(type(data) == 'table' and data.type or '?') .. ')')
end

-- ---------------------------------------------------------------------------
-- janela
-- ---------------------------------------------------------------------------
function show(tabName)
    if not menuWindow then
        return
    end
    if modules.naruto_sounds then
        modules.naruto_sounds.play('sfx_menu_open')
    end
    menuWindow:show()
    menuWindow:raise()
    menuWindow:focus()
    if tabName then
        local tab = tabBar:getTab(tabName)
        if tab then
            tabBar:selectTab(tab)
        end
    end
    if lastState == nil then
        requestState()
    end
end

function hide()
    if menuWindow then
        if modules.naruto_sounds then
            modules.naruto_sounds.play('sfx_menu_close')
        end
        menuWindow:hide()
    end
end

function toggle()
    if menuWindow and menuWindow:isVisible() then
        hide()
    else
        show()
    end
end

function isVisible()
    return menuWindow ~= nil and menuWindow:isVisible()
end

function getState()
    return lastState
end

-- ---------------------------------------------------------------------------
-- ciclo de vida
-- ---------------------------------------------------------------------------
function menuController:onInit()
    menuWindow = g_ui.displayUI('naruto_menu')
    menuWindow:setText('Shinobi')
    menuWindow:hide()
    menuWindow.closeButton:setText('Fechar')
    menuWindow.closeButton.onClick = hide

    createTabs()
    setStatus(WAITING)

    self:registerExtendedOpcode(OPCODE, onExtendedOpcode)

    Keybind.new('Windows', 'Show/hide Shinobi menu', 'Ctrl+J', '')
    Keybind.bind('Windows', 'Show/hide Shinobi menu', { { type = KEY_DOWN, callback = toggle } })

    if modules.game_mainpanel and modules.game_mainpanel.addToggleButton then
        menuButton = modules.game_mainpanel.addToggleButton('shinobiMenu',
            tr('Shinobi') .. ' (Ctrl+J)', '/images/game/shinobi_menu', toggle, true, 1)
    end

    -- noclip, gatilho 2 (ver o bloco de comentario do noclip acima)
    for _, entry in ipairs(MOVE_KEYS) do
        local dir = entry[2]
        local fn = function()
            noclipMoveAttempt(dir)
        end
        self:bindKeyDown(entry[1], fn)
        self:bindKeyPress(entry[1], fn)
    end

    hookChatTranslation()
end

function menuController:onGameStart()
    lastState = nil
    lastProgress = nil
    pendingElement = nil
    noclipEnabled = false
    refreshAll()
    -- noclip, gatilho 1
    self:registerEvents(LocalPlayer, { onCancelWalk = onCancelWalk })
    -- o servidor manda o state sozinho ~1s depois do login; se nada chegar
    -- (opcode ainda nao implementado), pedimos uma vez.
    self:scheduleEvent(function()
        if lastState == nil then
            requestState()
        end
    end, 2500, 'naruto_menu_get_state')
end

function menuController:onGameEnd()
    noclipEnabled = false
    lastState = nil
    lastProgress = nil
    hide()
end

function menuController:onTerminate()
    Keybind.delete('Windows', 'Show/hide Shinobi menu')
    if menuButton then
        menuButton:destroy()
        menuButton = nil
    end
    if menuWindow then
        menuWindow:destroy()
        menuWindow = nil
    end
    tabBar = nil
    charTab, elemTab, jutsuTab, missionsTab, cmdTab = nil, nil, nil, nil, nil
    charTabButton, elemTabButton, jutsuTabButton, missionsTabButton, cmdTabButton = nil, nil, nil, nil, nil
    elementButtons = {}
    lastState = nil
    lastProgress = nil
    -- rankRow foi anexado na janela de Skills (modules.game_skills), fora da
    -- arvore do menuWindow - destruir explicitamente, senao um reload do
    -- modulo (reloadable: true) criaria uma segunda linha "Rank" duplicada.
    if rankRow and not rankRow:isDestroyed() then
        rankRow:destroy()
    end
    rankRow = nil
end
