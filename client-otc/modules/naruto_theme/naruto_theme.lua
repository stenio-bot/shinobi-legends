-- Tema Shinobi Legends.
-- Sobrescreve traducoes (o cliente passa todo texto por tr()), assim renomeamos conceitos
-- de Tibia para Naruto sem editar os modulos game_* originais.
-- Mapeamento em docs/03-decisoes-tecnicas.md (ADR-005).
--
-- ATENCAO DE ENCODING: este arquivo e ASCII puro de proposito.
-- As fontes do OTClient sao bitmaps indexados por BYTE: ttfloader.cpp so gera glifos
-- de 32 a 255 e bitmapfont.cpp indexa com static_cast<uint8_t>(text[i]). Um acento em
-- UTF-8 ocupa 2 bytes e sai como mojibake na tela; o cliente precisa de cp1252.
-- Para ter as duas coisas, os acentos ficam como escapes \xNN (LuaJIT resolve para o
-- byte cp1252 em tempo de carga) e o arquivo em si continua ASCII/UTF-8 valido, entao
-- as ferramentas Python do projeto conseguem le-lo. Nao troque os \xNN por acentos
-- literais nem salve o arquivo em UTF-8 com acentos.

-- idiomas nos quais os termos sao instalados
local LOCALES = { 'en', 'pt', 'pt_br' }

-- idioma padrao do projeto
local DEFAULT_LOCALE = 'pt_br'

local TERMS = {
    -- recursos
    ['Mana'] = 'Chakra',
    ['Mana:'] = 'Chakra:',
    ['Health'] = 'Vida',
    ['Soul'] = 'Vontade',
    ['Capacity'] = 'Capacidade',
    ['Experience'] = 'Experi\xEAncia',
    ['Speed'] = 'Velocidade',
    ['Stamina'] = 'Stamina',
    -- skills (ordem de skills.otui)
    ['Magic Level'] = 'Ninjutsu',
    ['Fist Fighting'] = 'Corpo a Corpo',
    ['Club Fighting'] = 'Genjutsu',
    ['Sword Fighting'] = 'Taijutsu',
    ['Axe Fighting'] = 'Bukijutsu',
    ['Distance Fighting'] = 'Shuriken',
    ['Shielding'] = 'Defesa',
    ['Fishing'] = 'Pesca',
    ['Critical Hit Chance'] = 'Chance de Cr\xEDtico',
    ['Critical Hit Damage'] = 'Dano de Cr\xEDtico',
    ['Life Leech Chance'] = 'Chance de Roubo de Vida',
    ['Life Leech Amount'] = 'Roubo de Vida',
    ['Mana Leech Chance'] = 'Chance de Roubo de Chakra',
    ['Mana Leech Amount'] = 'Roubo de Chakra',
    ['Mana Leech'] = 'Roubo de Chakra',
    ['Manadrain'] = 'Dreno de Chakra',
    -- jutsus
    ['Spell List'] = 'Lista de Jutsus',
    ['Spells'] = 'Jutsus',
    ['Spell'] = 'Jutsu',
    ['Vocation'] = 'Vila',
    ['Vocation:'] = 'Vila:',
    ['Premium'] = 'Premium',
    ['Words'] = 'Selos',
    ['Words:'] = 'Selos:',
    -- interface
    ['Enter Game'] = 'Entrar no Jogo',
    ['Journey Onwards'] = 'Entrar no Jogo',
    ['Email:'] = 'Conta:',
    ['Acc Name:'] = 'Conta:',
    ['Remember Email:'] = 'Lembrar conta:',
    ['Remember password:'] = 'Lembrar senha:',
    ['Skills'] = 'Atributos',
    ['Show health'] = 'Mostrar vida e chakra',
    ['Battle'] = 'Combate',
    ['Quest Log'] = 'Miss\xF5es',
    ['Inventory'] = 'Equipamento',
    ['Minimap'] = 'Mapa',
    ['VIP List'] = 'Amigos',
    ['Options'] = 'Op\xE7\xF5es',
    ['Logout'] = 'Sair',
    ['Exit'] = 'Fechar',
    ['Account name'] = 'Conta',
    ['Password'] = 'Senha',
    ['Password:'] = 'Senha:',
    ['Remember password'] = 'Lembrar senha',
    ['Character List'] = 'Personagens',
    -- keybinds: presets renomeados para as vilas (ver corelib/keybind.lua)
    ['Preset'] = 'Vila',
    ['Presets'] = 'Vilas',
}

local function apply()
    if not modules.client_locales or not modules.client_locales.installLocale then
        return
    end
    -- instala nos idiomas suportados: quem jogar em ingles tambem ve "Chakra"
    for _, name in ipairs(LOCALES) do
        modules.client_locales.installLocale({ name = name, translation = TERMS })
    end
    -- idioma padrao do projeto
    if modules.client_locales.setLocale then
        if pcall(modules.client_locales.setLocale, DEFAULT_LOCALE) then
            -- ja escolhemos o idioma: nao mostrar a janela de selecao de locale
            if modules.client_locales.createWindow then
                pcall(disconnect, g_app, { onRun = modules.client_locales.createWindow })
                pcall(disconnect, g_app, { onUpdateFinished = modules.client_locales.createWindow })
            end
        end
    end
end

function init()
    apply()
    g_logger.info('naruto_theme: termos aplicados (Mana->Chakra, skills, jutsus); locale = ' ..
        DEFAULT_LOCALE)
end

function terminate()
end
