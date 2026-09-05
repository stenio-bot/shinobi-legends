-- ---------------------------------------------------------------------------
-- Musica ambiente por regiao (modules/naruto_sounds/naruto_music.lua)
--
-- 7 faixas em loop (tools/audio/gen_music.py, sintese procedural - ADR-002), uma por
-- regiao/bioma. A cada ~2s le a posicao do jogador local e resolve a regiao pelos
-- retangulos de music_catalog.lua (gerado a partir de assets-src/audio/music_catalog.json,
-- ver docs/sistemas/mapas.md para as coordenadas). So troca de faixa quando a regiao
-- muda, com crossfade via SoundChannel de musica (fadetime 2.5s).
--
-- Mecanismo de loop: SoundChannel nao expoe um "loop" nativo pro Lua (SoundSource nao e
-- @bindclass - so SoundChannel e' - ver client-otc/src/framework/sound/soundsource.h vs
-- soundchannel.h), mas SoundChannel:enqueue(file) reenfileira sozinho a MESMA entrada
-- toda vez que ela termina (SoundChannel::update() faz pop_front + push_back antes de
-- tocar de novo) - com 1 faixa so na fila isso já É o loop; o wav em si foi gerado com
-- crossfade de amostra (fim funde com o comeco, sy.crossfade_loop_stereo) para nao ter
-- clique na costura. Trocar de regiao = stop(fadetime) [limpa a fila] + enqueue(nova
-- faixa, fadetime) - mesmo padrao que modules/client/client.lua usa pra musica de menu.
--
-- Respeita enableMusicSound/musicSoundVolume (client_options/data_options.lua): a
-- musica so preenche a fila quando o canal esta habilitado; SoundChannel:setEnabled()
-- (chamado pela action da opcao) para/retoma sozinho - nao precisamos checar aqui, so
-- logar quando pulamos por causa disso.
--
-- ATENCAO DE ENCODING: arquivo ASCII puro (mesma regra de naruto_sounds.lua).
-- ---------------------------------------------------------------------------

NarutoMusic = {}
NarutoMusic.debug = true
NarutoMusic.pollIntervalMs = 2000
NarutoMusic.fadeTimeS = 2.5

local currentRegion = nil
local pollEvent = nil

local function log(msg)
    if NarutoMusic.debug then
        g_logger.info('[MUSIC] ' .. msg)
    end
end

-- ---------------------------------------------------------------------------
-- resolucao de regiao pelos retangulos do catalogo (mais especifico primeiro -
-- 'vila' fica DENTRO do retangulo de 'floresta_vila', por isso a ordem importa;
-- resolve_order ja vem assim de tools/audio/gen_music.py)
-- ---------------------------------------------------------------------------
local function insideRect(pos, rect)
    return pos.x >= rect.x1 and pos.x <= rect.x2 and pos.y >= rect.y1 and pos.y <= rect.y2
end

function NarutoMusic.resolveRegion(pos)
    if not (NarutoMusicCatalog and NarutoMusicCatalog.tracks) then
        return nil
    end
    for _, regionId in ipairs(NarutoMusicCatalog.resolve_order or {}) do
        local track = NarutoMusicCatalog.tracks[regionId]
        if track and insideRect(pos, track.region) then
            return regionId
        end
    end
    return nil
end

-- ---------------------------------------------------------------------------
-- troca de faixa com crossfade
-- ---------------------------------------------------------------------------
local function musicChannel()
    if not g_sounds then
        return nil
    end
    return g_sounds.getChannel(SoundChannels.Music)
end

function NarutoMusic.switchTo(regionId)
    local channel = musicChannel()
    if not channel then
        return
    end
    local track = NarutoMusicCatalog and NarutoMusicCatalog.tracks[regionId]
    if not track then
        log('regiao desconhecida no catalogo: ' .. tostring(regionId))
        return
    end

    currentRegion = regionId
    channel:stop(NarutoMusic.fadeTimeS)
    channel:enqueue('/sounds/' .. track.file, NarutoMusic.fadeTimeS, track.gain, 1)

    local enabled = true
    if g_settings then
        enabled = g_settings.getBoolean('enableMusicSound', true)
    end
    if enabled then
        log('regiao ' .. regionId .. ' (' .. tostring(track.title) .. ') -> ' .. track.file)
    else
        log('regiao ' .. regionId .. ' -> ' .. track.file .. ' (SEM SOM: musica desligada nas opcoes)')
    end
end

-- ---------------------------------------------------------------------------
-- polling da posicao (a cada ~2s, so quando em jogo)
-- ---------------------------------------------------------------------------
local function pollRegion()
    if not g_game.isOnline() then
        return
    end
    local player = g_game.getLocalPlayer()
    if not player then
        return
    end
    local pos = player:getPosition()
    if not pos then
        return
    end
    local regionId = NarutoMusic.resolveRegion(pos)
    if regionId and regionId ~= currentRegion then
        NarutoMusic.switchTo(regionId)
    end
end

local function startPolling()
    if pollEvent then
        return
    end
    currentRegion = nil
    pollRegion() -- primeira checagem imediata, nao espera 2s
    pollEvent = cycleEvent(pollRegion, NarutoMusic.pollIntervalMs)
end

local function stopPolling()
    if pollEvent then
        pollEvent:cancel()
        pollEvent = nil
    end
    currentRegion = nil
    local channel = musicChannel()
    if channel then
        channel:stop(NarutoMusic.fadeTimeS)
    end
end

-- ---------------------------------------------------------------------------
-- ciclo de vida
-- ---------------------------------------------------------------------------
function NarutoMusic.init()
    connect(g_game, {
        onGameStart = startPolling,
        onGameEnd = stopPolling,
    })
    if g_game.isOnline() then
        startPolling()
    end
    g_logger.info('naruto_music: modulo iniciado (' ..
        (NarutoMusicCatalog and table.size(NarutoMusicCatalog.tracks or {}) or 0) .. ' regioes no catalogo).')
end

function NarutoMusic.terminate()
    disconnect(g_game, {
        onGameStart = startPolling,
        onGameEnd = stopPolling,
    })
    stopPolling()
end
