-- ---------------------------------------------------------------------------
-- Traducao de mensagens de sistema (modules/naruto_theme/naruto_chat.lua)
--
-- Duas coisas diferentes, ambas resolvidas aqui:
--
-- 1) MOJIBAKE de acento: o servidor manda TODO texto em UTF-8 (NPCs, quests,
--    tarefas, diarias, /look...), mas as fontes do OTClient sao bitmaps
--    indexados por BYTE (ver o comentario de encoding em naruto_theme.lua). Um
--    acento en UTF-8 (2 bytes) vira dois glifos errados na tela (ex.: "regiao"
--    com til vira "regi\xC3\xA3o" -> "regiÃ£o"). Isso afeta QUALQUER mensagem
--    do servidor com acento, nao so as 3 citadas na missao - confirmado em
--    screenshots/ux_chat_01_accents.png ("regiÃ£o" no lugar de "regi\xE3o").
--    Corrigido re-convertendo para cp1252 (mesma funcao de naruto_menu.lua).
--
-- 2) Textos gerados pelo NUCLEO do TFS (server/tfs/src/*.cpp, nao gerados por
--    tools/export_tfs.py) continuam em ingles porque vem hardcoded do C++
--    (ex.: "You advanced to X level Y.", "There is not enough room.", "Z loses
--    N hitpoints due to your attack."). NAO reescrevemos o core do TFS para
--    isso (regra de ouro da missao) - em vez disso, casamos por padrao/regex
--    aqui e trocamos pela frase em pt-BR no estilo do projeto ("Voce avancou
--    em Taijutsu nivel X"). Ver docs/sistemas/cliente-ux.md para a lista
--    completa e onde cada frase foi encontrada em tfs/src.
--
-- Instalado como hook em modules/naruto_menu/naruto_menu.lua (precisa rodar
-- DEPOIS que game_textmessage carregou; naruto_theme sozinho carrega cedo
-- demais - ver o comentario "hookChatTranslation" la).
--
-- ATENCAO DE ENCODING: arquivo ASCII puro, acentos em escapes \xNN cp1252
-- (mesma regra de naruto_theme.lua/naruto_menu.lua). Nao troque por acentos
-- literais.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- 1) UTF-8 -> cp1252 (copia da funcao de naruto_menu.lua; ver o comentario de
-- encoding la para o porque). Duplicada de proposito: dois modulos pequenos e
-- independentes valem mais que uma dependencia cruzada so por isto.
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

local function utf8ToCp1252(str)
    if not str:find('[\128-\255]') then
        return str -- ASCII puro: nada a fazer (a maioria das frases em ingles)
    end
    local out, i, n = {}, 1, #str
    while i <= n do
        local b = str:byte(i)
        local cp, len
        if b < 0x80 then
            cp, len = b, 1
        elseif b >= 0xC2 and b <= 0xDF and i + 1 <= n then
            cp, len = (b - 0xC0) * 64 + (str:byte(i + 1) - 0x80), 2
        elseif b >= 0xE0 and b <= 0xEF and i + 2 <= n then
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

--- Corrige mojibake de um NOME (jogador/monstro) capturado de um padrao em
--- ingles antes de embuti-lo numa frase ja em cp1252 - nunca rode
--- utf8ToCp1252 na frase FINAL inteira quando ela ja tem escapes \xNN
--- literais, ou os bytes cp1252 "soltos" (ex.: \xE9) podem ser lidos de novo
--- como inicio de sequencia UTF-8 e virar lixo.
local function fixName(s)
    return utf8ToCp1252(s)
end

-- ---------------------------------------------------------------------------
-- 2) dicionario exato: mensagens de cancelamento do TFS (tools.cpp,
-- getReturnMessage) - string fixa, sem parametro.
-- ---------------------------------------------------------------------------
local EXACT = {
    ["Destination is out of range."] = "O destino est\xE1 fora de alcance.",
    ["You cannot move this object."] = "Voc\xEA n\xE3o pode mover este objeto.",
    ["Drop the double-handed object first."] = "Solte primeiro o objeto de duas m\xE3os.",
    ["Both hands need to be free."] = "As duas m\xE3os precisam estar livres.",
    ["You cannot dress this object there."] = "Voc\xEA n\xE3o pode vestir este objeto a\xED.",
    ["Put this object in your hand."] = "Coloque este objeto na sua m\xE3o.",
    ["Put this object in both hands."] = "Coloque este objeto nas duas m\xE3os.",
    ["You may only use one weapon."] = "Voc\xEA s\xF3 pode usar uma arma.",
    ["You are too far away."] = "Voc\xEA est\xE1 muito longe.",
    ["First go downstairs."] = "Primeiro desça as escadas.",
    ["First go upstairs."] = "Primeiro suba as escadas.",
    ["This object is too heavy for you to carry."] = "Este objeto \xE9 pesado demais para voc\xEA carregar.",
    ["You cannot put more objects in this container."] = "Voc\xEA n\xE3o pode colocar mais objetos neste cont\xEAiner.",
    ["There is not enough room."] = "N\xE3o h\xE1 espa\xE7o suficiente.",
    ["You cannot take this object."] = "Voc\xEA n\xE3o pode pegar este objeto.",
    ["You cannot throw there."] = "Voc\xEA n\xE3o pode jogar para l\xE1.",
    ["There is no way."] = "N\xE3o h\xE1 caminho.",
    ["This is impossible."] = "Isso \xE9 imposs\xEDvel.",
    ["You can not enter a protection zone after attacking another player."] =
        "Voc\xEA n\xE3o pode entrar numa zona de prote\xE7\xE3o depois de atacar outro jogador.",
    ["You are not invited."] = "Voc\xEA n\xE3o foi convidado.",
    ["Creature does not exist."] = "A criatura n\xE3o existe.",
    ["You cannot put more items in this depot."] = "Voc\xEA n\xE3o pode colocar mais itens neste dep\xF3sito.",
    ["You cannot use this object."] = "Voc\xEA n\xE3o pode usar este objeto.",
    ["A player with this name is not online."] = "Nenhum jogador com este nome est\xE1 online.",
    ["You do not have the required magic level to use this rune."] =
        "Voc\xEA n\xE3o tem o n\xEDvel de ninjutsu necess\xE1rio para usar esta runa.",
    ["You are already trading. Finish this trade first."] = "Voc\xEA j\xE1 est\xE1 negociando. Termine essa troca primeiro.",
    ["This player is already trading."] = "Este jogador j\xE1 est\xE1 negociando.",
    ["You may not logout during or immediately after a fight!"] =
        "Voc\xEA n\xE3o pode sair do jogo durante ou logo ap\xF3s uma luta!",
    ["You are not allowed to shoot directly on players."] = "Voc\xEA n\xE3o pode atirar diretamente em jogadores.",
    ["Your level is too low."] = "Seu n\xEDvel \xE9 muito baixo.",
    ["You do not have enough magic level."] = "Voc\xEA n\xE3o tem ninjutsu suficiente.",
    ["You do not have enough mana."] = "Voc\xEA n\xE3o tem chakra suficiente.",
    ["You do not have enough soul."] = "Voc\xEA n\xE3o tem vontade suficiente.",
    ["You are exhausted."] = "Voc\xEA est\xE1 exausto.",
    ["You cannot use objects that fast."] = "Voc\xEA n\xE3o pode usar objetos t\xE3o r\xE1pido.",
    ["You can only use it on creatures."] = "Voc\xEA s\xF3 pode usar isso em criaturas.",
    ["Player is not reachable."] = "O jogador n\xE3o pode ser alcan\xE7ado.",
    ["Creature is not reachable."] = "A criatura n\xE3o pode ser alcan\xE7ada.",
    ["This action is not permitted in a protection zone."] = "Esta a\xE7\xE3o n\xE3o \xE9 permitida numa zona de prote\xE7\xE3o.",
    ["You may not attack this person."] = "Voc\xEA n\xE3o pode atacar esta pessoa.",
    ["You may not attack this creature."] = "Voc\xEA n\xE3o pode atacar esta criatura.",
    ["You may not attack a person in a protection zone."] = "Voc\xEA n\xE3o pode atacar algu\xE9m numa zona de prote\xE7\xE3o.",
    ["You may not attack a person while you are in a protection zone."] =
        "Voc\xEA n\xE3o pode atacar algu\xE9m enquanto estiver numa zona de prote\xE7\xE3o.",
    ["Turn secure mode off if you really want to attack unmarked players."] =
        "Desative o modo seguro se realmente quiser atacar jogadores n\xE3o marcados.",
    ["You need a premium account."] = "Voc\xEA precisa de uma conta premium.",
    ["You must learn this spell first."] = "Voc\xEA precisa aprender este jutsu primeiro.",
    ["You have the wrong vocation to cast this spell."] = "Sua vila n\xE3o pode usar este jutsu.",
    ["You need to equip a weapon to use this spell."] = "Voc\xEA precisa equipar uma arma para usar este jutsu.",
    ["You can not leave a pvp zone after attacking another player."] =
        "Voc\xEA n\xE3o pode sair de uma zona PvP depois de atacar outro jogador.",
    ["You can not enter a pvp zone after attacking another player."] =
        "Voc\xEA n\xE3o pode entrar numa zona PvP depois de atacar outro jogador.",
    ["This action is not permitted in a non pvp zone."] = "Esta a\xE7\xE3o n\xE3o \xE9 permitida numa zona sem PvP.",
    ["You can not logout here."] = "Voc\xEA n\xE3o pode sair do jogo aqui.",
    ["You need a magic item to cast this spell."] = "Voc\xEA precisa de um item m\xE1gico para usar este jutsu.",
    ["You cannot conjure items here."] = "Voc\xEA n\xE3o pode conjurar itens aqui.",
    ["You need to split your spears first."] = "Voc\xEA precisa separar suas lan\xE7as primeiro.",
    ["Player name is ambiguous."] = "O nome do jogador \xE9 amb\xEDguo.",
    ["You may use only one shield."] = "Voc\xEA s\xF3 pode usar um escudo.",
    ["No party members in range."] = "Nenhum membro do grupo por perto.",
    ["You are not the owner."] = "Voc\xEA n\xE3o \xE9 o dono.",
    ["No such raid exists."] = "Este evento n\xE3o existe.",
    ["Another raid is already executing."] = "Outro evento j\xE1 est\xE1 em andamento.",
    ["Trade player is too far away."] = "O jogador da troca est\xE1 muito longe.",
    ["You don't own this house."] = "Voc\xEA n\xE3o \xE9 dono desta casa.",
    ["Trade player already owns a house."] = "O jogador da troca j\xE1 tem uma casa.",
    ["You can not trade this house."] = "Voc\xEA n\xE3o pode negociar esta casa.",
    ["You don't have the required profession."] = "Voc\xEA n\xE3o tem a profiss\xE3o necess\xE1ria.",
    ["This item cannot be moved there."] = "Este item n\xE3o pode ser movido para l\xE1.",
    ["Sorry, not possible."] = "Desculpe, n\xE3o \xE9 poss\xEDvel.",
    ["There is no way."] = "N\xE3o h\xE1 caminho.",
    -- login (data/creaturescripts/scripts/login.lua ja foi ajustado no
    -- servidor - troca trivial - mas fica aqui tambem como rede de seguranca
    -- caso alguem reverta so o lado do servidor).
}

-- ---------------------------------------------------------------------------
-- 3) padroes com parametro (nivel, dano, cura, experiencia). Ordem importa:
-- os mais especificos (ex.: "to level N", sem nome de skill) vem antes dos
-- genericos correspondentes.
-- ---------------------------------------------------------------------------
local SKILL_NAMES = {
    ['fist fighting'] = 'Corpo a Corpo',
    ['club fighting'] = 'Genjutsu',
    ['sword fighting'] = 'Taijutsu',
    ['axe fighting'] = 'Bukijutsu',
    ['distance fighting'] = 'Shuriken',
    ['shielding'] = 'Defesa',
    ['fishing'] = 'Pesca',
    ['magic level'] = 'Ninjutsu',
}

local function skillName(s)
    return SKILL_NAMES[s] or s
end

-- {padrao Lua, function(capturas...) -> string pt-BR (ja em cp1252)}
local PATTERNS = {
    -- nivel de personagem (server/tfs/src/player.cpp: Player::addExperience/removeExperience;
    -- NAO existe "You advanced to level N." no TFS - o nivel de personagem sempre vem como
    -- "You advanced/were downgraded FROM Level X TO Level Y.", confirmado lendo tfs/src/player.cpp).
    { '^You advanced from Level (%d+) to Level (%d+)%.$', function(_from, to)
        return 'Voc\xEA avan\xE7ou para o n\xEDvel ' .. to .. '.'
    end },
    { '^You were downgraded from Level (%d+) to Level (%d+)%.$', function(_from, to)
        return 'Voc\xEA foi rebaixado para o n\xEDvel ' .. to .. '.'
    end },
    -- ninjutsu (magic level): tfs/src/player.cpp hardcoda "magic level" direto no formato (nao
    -- passa por getSkillName), entao precisa de um padrao proprio ANTES do generico de skills
    -- abaixo (senao "magic" vira "skill" e perde a palavra "level" que faz parte da frase).
    { '^You advanced to magic level (%d+)%.$', function(lvl)
        return 'Voc\xEA avan\xE7ou em Ninjutsu n\xEDvel ' .. lvl .. '.'
    end },
    { '^You were downgraded to magic level (%d+)%.$', function(lvl)
        return 'Voc\xEA foi rebaixado em Ninjutsu para o n\xEDvel ' .. lvl .. '.'
    end },
    -- skills (ex.: "You advanced to fishing level 5." -> "Voce avancou em Pesca nivel 5.")
    { '^You advanced to (.-) level (%d+)%.$', function(skill, lvl)
        return 'Voc\xEA avan\xE7ou em ' .. skillName(skill) .. ' n\xEDvel ' .. lvl .. '.'
    end },
    { '^You were downgraded to (.-) level (%d+)%.$', function(skill, lvl)
        return 'Voc\xEA foi rebaixado em ' .. skillName(skill) .. ' para o n\xEDvel ' .. lvl .. '.'
    end },
    -- chakra (mana): server/tfs/src/game.cpp
    { '^You lose (%d+) mana due to your own attack%.$', function(n)
        return 'Voc\xEA perde ' .. n .. ' de chakra devido ao pr\xF3prio ataque.'
    end },
    { '^You lose (%d+) mana due to an attack by (.+)%.$', function(n, who)
        return 'Voc\xEA perde ' .. n .. ' de chakra por um ataque de ' .. fixName(who) .. '.'
    end },
    { '^You lose (%d+) mana%.$', function(n)
        return 'Voc\xEA perde ' .. n .. ' de chakra.'
    end },
    { '^You gained (%d+) mana%.$', function(n)
        return 'Voc\xEA ganhou ' .. n .. ' de chakra.'
    end },
    { '^(.+) loses (%d+) mana due to your attack%.$', function(who, n)
        return fixName(who) .. ' perde ' .. n .. ' de chakra por causa do seu ataque.'
    end },
    { '^(.+) loses (%d+) mana due to %a+ own attack%.$', function(who, n)
        return fixName(who) .. ' perde ' .. n .. ' de chakra por causa do pr\xF3prio ataque.'
    end },
    { '^(.+) loses (%d+) mana due to an attack by (.+)%.$', function(who, n, attacker)
        return fixName(who) .. ' perde ' .. n .. ' de chakra por um ataque de ' .. fixName(attacker) .. '.'
    end },
    { '^(.+) loses (%d+) mana%.$', function(who, n)
        return fixName(who) .. ' perde ' .. n .. ' de chakra.'
    end },
    -- vida (hitpoints): server/tfs/src/game.cpp
    { '^You lose (%d+) hitpoints? due to your own attack%.$', function(n)
        return 'Voc\xEA perde ' .. n .. ' de vida devido ao pr\xF3prio ataque.'
    end },
    { '^You lose (%d+) hitpoints? due to an attack by (.+)%.$', function(n, who)
        return 'Voc\xEA perde ' .. n .. ' de vida por um ataque de ' .. fixName(who) .. '.'
    end },
    { '^You lose (%d+) hitpoints?%.$', function(n)
        return 'Voc\xEA perde ' .. n .. ' de vida.'
    end },
    { '^(.+) loses (%d+) hitpoints? due to your attack%.$', function(who, n)
        return fixName(who) .. ' perde ' .. n .. ' de vida por causa do seu ataque.'
    end },
    { '^(.+) loses (%d+) hitpoints? due to %a+ own attack%.$', function(who, n)
        return fixName(who) .. ' perde ' .. n .. ' de vida por causa do pr\xF3prio ataque.'
    end },
    { '^(.+) loses (%d+) hitpoints? due to an attack by (.+)%.$', function(who, n, attacker)
        return fixName(who) .. ' perde ' .. n .. ' de vida por um ataque de ' .. fixName(attacker) .. '.'
    end },
    { '^(.+) loses (%d+) hitpoints?%.$', function(who, n)
        return fixName(who) .. ' perde ' .. n .. ' de vida.'
    end },
    -- cura: server/tfs/src/game.cpp
    { '^You heal (.+) for (%d+) hitpoints?%.$', function(who, n)
        return 'Voc\xEA cura ' .. fixName(who) .. ' em ' .. n .. ' de vida.'
    end },
    { '^You were healed by (.+) for (%d+) hitpoints?%.$', function(who, n)
        return 'Voc\xEA foi curado por ' .. fixName(who) .. ' em ' .. n .. ' de vida.'
    end },
    { '^You were healed for (%d+) hitpoints?%.$', function(n)
        return 'Voc\xEA foi curado em ' .. n .. ' de vida.'
    end },
    { '^You healed yourself for (%d+) hitpoints?%.$', function(n)
        return 'Voc\xEA se curou em ' .. n .. ' de vida.'
    end },
    -- experiencia: server/tfs/src/player.cpp
    { '^You gained (%d+) experience points?%.$', function(n)
        return 'Voc\xEA ganhou ' .. n .. ' de experi\xEAncia.'
    end },
    { '^You lost (%d+) experience points?%.$', function(n)
        return 'Voc\xEA perdeu ' .. n .. ' de experi\xEAncia.'
    end },
    { '^(.+) gained (%d+) experience points?%.$', function(who, n)
        return fixName(who) .. ' ganhou ' .. n .. ' de experi\xEAncia.'
    end },
}

-- ---------------------------------------------------------------------------
-- API publica: modules.naruto_theme.translateMessage(text)
-- ---------------------------------------------------------------------------

--- Traduz uma mensagem de sistema em ingles (nucleo do TFS) para pt-BR quando
--- reconhece o padrao; senao so conserta o mojibake de acento UTF-8 (texto ja
--- em portugues vindo de naruto_quests/naruto_tasks/naruto_dailies/NPCs).
--- Nunca lanca erro (uso direto num hook de exibicao de mensagem).
function translateMessage(text)
    if type(text) ~= 'string' or text == '' then
        return text
    end
    local exact = EXACT[text]
    if exact then
        return exact
    end
    for _, entry in ipairs(PATTERNS) do
        local caps = { text:match(entry[1]) }
        if caps[1] ~= nil then
            local ok, out = pcall(entry[2], unpack(caps))
            if ok and out then
                return out
            end
        end
    end
    return utf8ToCp1252(text)
end
