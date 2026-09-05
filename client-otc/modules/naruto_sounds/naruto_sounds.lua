-- ---------------------------------------------------------------------------
-- Sons do jogo (modules/naruto_sounds)
--
-- Toca os SFX procedurais de tools/audio/gen_sfx.py (client-otc/data/sounds/naruto/*.ogg,
-- catalogados em sfx_catalog.lua, gerado a partir de assets-src/audio/sfx_catalog.json).
-- Ver docs/sistemas/audio.md para a lista completa e os ganchos usados.
--
-- Ganchos (na falta de um callback client-side para "efeito magico visto na tela" -
-- o Redemption nao tem onMagicEffect/onMissile em Lua, so parseMagicEffect no C++, que
-- nao chama nenhum callLuaField - ver client-otc/src/client/protocolgameparse.cpp):
--
--   (a) jutsu/efeito: OPCODE ESTENDIDO 210, acao "sfx" mandada pelo servidor no
--       onCastSpell de cada jutsu (tools/export_tfs.py, NarutoJson.broadcastSfx) para
--       o conjurador + criaturas/jogadores proximos. O opcode 210 ja e de
--       modules/naruto_menu (so pode haver 1 registerExtendedOpcode por codigo -
--       gamelib/protocolgame.lua da erro "Opcode is already taken." no 2o registro),
--       entao NAO registramos de novo aqui: naruto_menu.onExtendedOpcode despacha
--       para NarutoSounds.onOpcodeSfx quando data.type == 'sfx' (ver o fim deste
--       arquivo e o trecho equivalente em naruto_menu.lua).
--   (b) onTextMessage (modules/gamelib/textmessages.lua, registerMessageMode): nivel
--       (regex igual ao de naruto_chat.lua em cima do texto EM INGLES que vem do
--       core do TFS, MessageModes.Game) e conquista (best-effort - o projeto ainda
--       nao tem sistema de conquistas ligado ao chat, ver docs/sistemas/audio.md).
--   (c) connect(Creature, {onHealthPercentChange=..., onDeath=...}) para dano
--       recebido/morte de criatura - mesmo padrao de modules/game_battle/battle.lua
--       (connect na CLASSE Creature inteira, nao por instancia).
--   (d) UI: abrir/fechar o Menu Shinobi chama NarutoSounds.play via 2 linhas
--       adicionadas em naruto_menu.lua (show()/hide()); clique generico exposto
--       como NarutoSounds.playClick() (usado pelo botao GOD do menu, prova de UI).
--
-- Volume: le g_settings 'enableGameSound'/'gameSoundVolume' (client_options,
-- styles/sound/audio.otui) a cada tocada - g_sounds.play() nao usa SoundChannel
-- (isso e so para streaming/musica), entao o volume tem que ser aplicado no gain
-- passado para play().
--
-- ATENCAO DE ENCODING: arquivo ASCII puro (mesma regra de naruto_theme.lua).
-- ---------------------------------------------------------------------------

NarutoSounds = {}

-- true: loga "[SFX] tocando <nome>" a cada chamada (pedido da missao de audio,
-- para provar por log que g_sounds.play foi chamado com o arquivo certo).
NarutoSounds.debug = true

local function log(msg)
    if NarutoSounds.debug then
        g_logger.info('[SFX] ' .. msg)
    end
end

-- ---------------------------------------------------------------------------
-- reproducao
-- ---------------------------------------------------------------------------
local function effectiveGain(catalogGain)
    local enabled = true
    local vol = 100
    if g_settings then
        enabled = g_settings.getBoolean('enableGameSound', true)
        vol = g_settings.getNumber('gameSoundVolume', 100)
    end
    if not enabled then
        return 0
    end
    return (catalogGain or 0.85) * (vol / 100)
end

--- Toca um SFX pelo id do catalogo (ex.: 'sfx_fire_whoosh'). Sem-op silencioso se o
--- id nao existir no catalogo (loga um aviso) ou se audio/volume estiver zerado.
function NarutoSounds.play(id)
    if not id then
        return nil
    end
    local entry = NarutoSfxCatalog and NarutoSfxCatalog[id]
    if not entry then
        log('id desconhecido no catalogo: ' .. tostring(id))
        return nil
    end
    if not g_sounds then
        return nil -- build sem audio (raro; nao trava o jogo)
    end

    local file = entry.file
    if entry.variations and #entry.variations > 0 then
        file = entry.variations[math.random(#entry.variations)]
    end

    local gain = effectiveGain(entry.gain)
    if gain <= 0 then
        log('tocando ' .. id .. ' -> ' .. tostring(file) .. ' (audio desligado, gain=0)')
        return nil
    end

    -- BARRA INICIAL OBRIGATORIA: ResourceManager::resolvePath (src/framework/core/
    -- resourcemanager.cpp) resolve um caminho RELATIVO contra o diretorio do MODULO
    -- que esta chamando (g_lua.getCurrentSourcePath(), ex. "naruto_sounds"), nao
    -- contra a raiz de dados - por isso o padrao do proprio client.lua guarda seu som
    -- em modules/client/sounds/startup.ogg e usa 'sounds/startup' (relativo). Como os
    -- nossos .ogg vivem em client-otc/data/sounds/naruto/ (data/ e' montado na raiz
    -- "/" por g_resources.addSearchPath em init.lua), precisamos de um caminho
    -- ABSOLUTO ('/sounds/...') para nao virar '/naruto_sounds/sounds/...' e falhar
    -- com "unable to open file" (bug real encontrado e corrigido durante o teste
    -- manual - ver docs/sistemas/audio.md).
    local source = g_sounds.play('/sounds/' .. file, 0, gain, 1)
    if not source then
        -- g_sounds.play() devolve nil sem log nenhum do lado C++ quando o audio do
        -- ENGINE inteiro esta desligado (SoundManager::m_audioEnabled, opcao "Enable
        -- audio" do client_options - g_sounds.isAudioEnabled() reflete isso). Nesse
        -- caso NAO e' erro nosso: so avisa em log info, sem [error], para nao mascarar
        -- uma falha real de carregamento (arquivo ausente/corrompido) atras de um
        -- "audio geral desligado".
        if g_sounds.isAudioEnabled and not g_sounds.isAudioEnabled() then
            log('tocando ' .. id .. ' -> ' .. tostring(file) ..
                ' (SEM SOM: "Enable audio" esta desligado nas opcoes do cliente)')
        else
            g_logger.error('[SFX] falha ao iniciar ' .. id .. ' (' .. tostring(file) .. ')')
        end
    else
        log('tocando ' .. id .. ' -> ' .. tostring(file) .. ' (gain=' .. string.format('%.2f', gain) .. ')')
    end
    return source
end

-- clique generico de UI (botoes do Menu Shinobi etc.)
function NarutoSounds.playClick()
    NarutoSounds.play('sfx_click')
end

-- ---------------------------------------------------------------------------
-- (a) opcode 210, acao "sfx" - despachado por naruto_menu.onExtendedOpcode.
-- data = { type='sfx', id='sfx_fire_whoosh', ... }
-- ---------------------------------------------------------------------------
function NarutoSounds.onOpcodeSfx(data)
    if type(data) ~= 'table' or data.type ~= 'sfx' or not data.id then
        return false
    end
    NarutoSounds.play(data.id)
    return true
end

-- ---------------------------------------------------------------------------
-- (b) onTextMessage: nivel e conquista
-- ---------------------------------------------------------------------------
-- mesma regex de naruto_theme/naruto_chat.lua (texto EM INGLES do core do TFS -
-- nao reescrevemos server/tfs/src, so casamos o padrao).
local LEVEL_UP_PATTERN = '^You advanced from Level %d+ to Level %d+%.$'
local ACHIEVEMENT_PATTERNS = {
    '^Achievement unlocked: .+$',
    '^Conquista desbloqueada.*$', -- caso algum dia o servidor mande em pt-BR
}

local function onGameMessage(mode, text)
    if text:match(LEVEL_UP_PATTERN) then
        NarutoSounds.play('sfx_level_up')
        return
    end
    for _, pat in ipairs(ACHIEVEMENT_PATTERNS) do
        if text:match(pat) then
            NarutoSounds.play('sfx_achievement')
            return
        end
    end
end

local function onDamageReceivedMessage(mode, text)
    -- MessageModes.DamageReceived cobre "You lose X hitpoints..." e afins; nao
    -- precisamos parsear o numero, so confirmar que o jogador tomou dano.
    NarutoSounds.play('sfx_damage_taken')
end

-- ---------------------------------------------------------------------------
-- (c) Creature (classe inteira, igual game_battle/battle.lua): dano recebido
-- pelo LocalPlayer (via onHealthChange, mais confiavel que parsear texto) e
-- morte de criatura (onDeath, so para monstros - jogador tem seu proprio som
-- em modules/game_playerdeath).
-- ---------------------------------------------------------------------------
local lastLocalHealth = nil

local function onLocalHealthChange(localPlayer, health, maxHealth, oldHealth, oldMaxHealth)
    if lastLocalHealth ~= nil and health < lastLocalHealth then
        NarutoSounds.play('sfx_damage_taken')
    end
    lastLocalHealth = health
end

local function onCreatureDeath(creature)
    if not creature then
        return
    end
    if creature:isLocalPlayer() then
        return -- morte do proprio jogador: som proprio (nao criado nesta missao)
    end
    if creature:isMonster() then
        NarutoSounds.play('sfx_monster_death')
    end
end

-- ---------------------------------------------------------------------------
-- ciclo de vida
-- ---------------------------------------------------------------------------
local eventsConnected = false
local messageModesConnected = false

local function connectEvents()
    if eventsConnected then
        return
    end
    connect(LocalPlayer, { onHealthChange = onLocalHealthChange })
    connect(Creature, { onDeath = onCreatureDeath })
    eventsConnected = true
end

local function disconnectEvents()
    if not eventsConnected then
        return
    end
    disconnect(LocalPlayer, { onHealthChange = onLocalHealthChange })
    disconnect(Creature, { onDeath = onCreatureDeath })
    eventsConnected = false
end

-- registerMessageMode so funciona depois que game_textmessage.init() rodou
-- (mesma restricao documentada em naruto_menu.lua/hookChatTranslation) -
-- tentamos no init() e nos game events, o que vier primeiro.
local function connectMessageModes()
    if messageModesConnected then
        return true
    end
    if not modules.game_textmessage then
        return false
    end
    registerMessageMode(MessageModes.Game, onGameMessage)
    registerMessageMode(MessageModes.DamageReceived, onDamageReceivedMessage)
    messageModesConnected = true
    g_logger.info('naruto_sounds: message modes conectados (nivel, dano recebido).')
    return true
end

function init()
    connect(g_game, {
        onGameStart = connectEvents,
        onGameEnd = disconnectEvents,
    })
    if g_game.isOnline() then
        connectEvents()
    end
    if not connectMessageModes() then
        -- naruto_menu (prioridade 1100) carrega logo antes de naruto_sounds
        -- (1150), mas game_textmessage pode ainda nao ter rodado onInit();
        -- tenta de novo apos o load-later terminar.
        scheduleEvent(connectMessageModes, 500)
    end
    g_logger.info('naruto_sounds: modulo iniciado (' ..
        (NarutoSfxCatalog and table.size(NarutoSfxCatalog) or 0) .. ' sfx no catalogo).')
end

function terminate()
    disconnect(g_game, {
        onGameStart = connectEvents,
        onGameEnd = disconnectEvents,
    })
    disconnectEvents()
    if messageModesConnected then
        unregisterMessageMode(MessageModes.Game, onGameMessage)
        unregisterMessageMode(MessageModes.DamageReceived, onDamageReceivedMessage)
        messageModesConnected = false
    end
end

-- ---------------------------------------------------------------------------
-- API publica do modulo. Modulos sandboxed expoem seus GLOBAIS como campos de
-- `modules.<nome>` (module.cpp poe package.loaded[nome] = ambiente do modulo) -
-- entao um global `NarutoSounds` (tabela) aparece como `modules.naruto_sounds.
-- NarutoSounds`, NAO como `modules.naruto_sounds.play` direto. Os aliases
-- abaixo (globais de 1o nivel) sao o que naruto_menu.lua e outros modulos
-- devem chamar: modules.naruto_sounds.play(id), .playClick(), .onOpcodeSfx(data).
-- ---------------------------------------------------------------------------
play = NarutoSounds.play
playClick = NarutoSounds.playClick
onOpcodeSfx = NarutoSounds.onOpcodeSfx
