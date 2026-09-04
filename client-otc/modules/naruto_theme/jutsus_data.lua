-- GERADO por tools/export_tfs.py a partir de data/jutsus/*.json. NAO EDITE A MAO.
-- Regenerar: python3 tools/export_tfs.py (e .venv/bin/python tools/spr/gen_jutsu_icons.py
-- para a folha client-otc/data/images/game/spells/jutsus.png, que precisa da MESMA ordem).
--
-- ENCODING: arquivo ASCII puro. As fontes do OTClient sao bitmaps indexados por byte,
-- entao acentos vao como escapes \xNN em cp1252 (mesma regra de naruto_theme.lua).

-- Ajustes da folha de icones (mesmo formato de SpelllistSettings em gamelib/spells.lua).
NarutoSpelllistProfile = 'Shinobi'
NarutoSpelllistSettings = {
    iconFile = '/images/game/spells/jutsus',
    iconsForGameCooldown = '/images/game/spells/jutsus',
    iconSize = { width = 32, height = 32 },
    iconSizeCooldown = { width = 32, height = 32 },
    spellListWidth = 210,
    spellWindowWidth = 550,
}

-- [nome do jutsu] = posicao na folha jutsus.png; x = indice * 32, y = 0.
NarutoSpellIcons = {
    ['Katon: Grande Bola de Fogo'] = { x = 0, y = 0, index = 0 },
    ['Katon: Sopro de Brasas'] = { x = 32, y = 0, index = 1 },
    ['Katon: Flores de F\xEAnix'] = { x = 64, y = 0, index = 2 },
    ['Katon: Anel de Chamas'] = { x = 96, y = 0, index = 3 },
    ['Katon: Drag\xE3o de Fogo'] = { x = 128, y = 0, index = 4 },
    ['Suiton: Proj\xE9til de \xC1gua'] = { x = 160, y = 0, index = 5 },
    ['Suiton: N\xE9voa Cortante'] = { x = 192, y = 0, index = 6 },
    ['Suiton: Pris\xE3o de \xC1gua'] = { x = 224, y = 0, index = 7 },
    ['Suiton: Drag\xE3o de \xC1gua'] = { x = 256, y = 0, index = 8 },
    ['Suiton: V\xF3rtice Devorador'] = { x = 288, y = 0, index = 9 },
    ['Raiton: Agulha de Raio'] = { x = 320, y = 0, index = 10 },
    ['Raiton: Corrente Est\xE1tica'] = { x = 352, y = 0, index = 11 },
    ['Raiton: Lan\xE7a do Rel\xE2mpago'] = { x = 384, y = 0, index = 12 },
    ['Raiton: Armadura El\xE9trica'] = { x = 416, y = 0, index = 13 },
    ['Raiton: Punho do Trov\xE3o'] = { x = 448, y = 0, index = 14 },
    ['Doton: Muralha de Pedra'] = { x = 480, y = 0, index = 15 },
    ['Doton: Estacas de Terra'] = { x = 512, y = 0, index = 16 },
    ['Doton: Colapso do Terreno'] = { x = 544, y = 0, index = 17 },
    ['Fuuton: L\xE2mina de Vento'] = { x = 576, y = 0, index = 18 },
    ['Fuuton: Rajada Cortante'] = { x = 608, y = 0, index = 19 },
    ['Kawarimi no Jutsu'] = { x = 640, y = 0, index = 20 },
    ['Bunshin no Jutsu'] = { x = 672, y = 0, index = 21 },
    ['Shousen: Palma Curativa'] = { x = 704, y = 0, index = 22 },
    ['Doku: N\xE9voa Venenosa'] = { x = 736, y = 0, index = 23 },
    ['Fuuin: Selo de Conten\xE7\xE3o'] = { x = 768, y = 0, index = 24 },
}

-- Mesmo formato de SpellInfo['Default']. 'words' sao os selos (= words do spells.xml).
NarutoSpellInfo = {
    ['Katon: Grande Bola de Fogo'] = { id = 900, name = 'Katon: Grande Bola de Fogo', words = 'katon goukakyuu', type = 'Instant', level = 1, mana = 15, soul = 0, maglevel = 0, icon = 'katon_goukakyuu', clientId = 0, group = { [1] = 1000 }, needTarget = true, parameter = false, range = 5, exhaustion = 2000, premium = false, vocations = { 4, 8 }, special = false, source = 0, description = 'Dispara uma bola de fogo que explode no impacto.' },
    ['Katon: Sopro de Brasas'] = { id = 901, name = 'Katon: Sopro de Brasas', words = 'katon sopro brasas', type = 'Instant', level = 6, mana = 18, soul = 0, maglevel = 0, icon = 'katon_sopro_brasas', clientId = 1, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 2, exhaustion = 3000, premium = false, vocations = { 4, 8 }, special = false, source = 0, description = 'Um sopro curto de brasas que cobre os tiles imediatamente \xE0 frente.' },
    ['Katon: Flores de F\xEAnix'] = { id = 902, name = 'Katon: Flores de F\xEAnix', words = 'katon housenka', type = 'Instant', level = 12, mana = 30, soul = 0, maglevel = 0, icon = 'katon_housenka', clientId = 2, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 3, exhaustion = 4000, premium = false, vocations = { 4, 8 }, special = false, source = 0, description = 'V\xE1rios proj\xE9teis de fogo em cone \xE0 frente.' },
    ['Katon: Anel de Chamas'] = { id = 903, name = 'Katon: Anel de Chamas', words = 'katon anel chamas', type = 'Instant', level = 20, mana = 42, soul = 0, maglevel = 0, icon = 'katon_anel_chamas', clientId = 3, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 1, exhaustion = 6000, premium = false, vocations = { 4, 8 }, special = false, source = 0, description = 'Um anel de fogo explode ao redor do conjurador, queimando tudo em volta.' },
    ['Katon: Drag\xE3o de Fogo'] = { id = 904, name = 'Katon: Drag\xE3o de Fogo', words = 'katon karyuu endan', type = 'Instant', level = 35, mana = 60, soul = 0, maglevel = 0, icon = 'katon_karyuu_endan', clientId = 4, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 6, exhaustion = 8000, premium = false, vocations = { 4, 8 }, special = false, source = 0, description = 'Um drag\xE3o de chamas em linha reta, atravessa inimigos.' },
    ['Suiton: Proj\xE9til de \xC1gua'] = { id = 905, name = 'Suiton: Proj\xE9til de \xC1gua', words = 'suiton mizudan', type = 'Instant', level = 1, mana = 12, soul = 0, maglevel = 0, icon = 'suiton_mizudan', clientId = 5, group = { [1] = 1000 }, needTarget = true, parameter = false, range = 6, exhaustion = 1800, premium = false, vocations = { 3, 7 }, special = false, source = 0, description = 'Bala de \xE1gua comprimida.' },
    ['Suiton: N\xE9voa Cortante'] = { id = 906, name = 'Suiton: N\xE9voa Cortante', words = 'suiton nevoa cortante', type = 'Instant', level = 6, mana = 17, soul = 0, maglevel = 0, icon = 'suiton_nevoa_cortante', clientId = 6, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 2, exhaustion = 3000, premium = false, vocations = { 3, 7 }, special = false, source = 0, description = 'Got\xEDculas afiadas suspensas no ar cortam quem estiver \xE0 frente.' },
    ['Suiton: Pris\xE3o de \xC1gua'] = { id = 907, name = 'Suiton: Pris\xE3o de \xC1gua', words = 'suiton prisao agua', type = 'Instant', level = 22, mana = 38, soul = 0, maglevel = 0, icon = 'suiton_prisao_agua', clientId = 7, group = { [1] = 1000 }, needTarget = true, parameter = false, range = 3, exhaustion = 7000, premium = false, vocations = { 3, 7 }, special = false, source = 0, description = 'Uma esfera de \xE1gua prende o alvo no lugar e o sufoca lentamente.' },
    ['Suiton: Drag\xE3o de \xC1gua'] = { id = 908, name = 'Suiton: Drag\xE3o de \xC1gua', words = 'suiton suiryuudan', type = 'Instant', level = 25, mana = 45, soul = 0, maglevel = 0, icon = 'suiton_suiryuudan', clientId = 8, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 5, exhaustion = 6000, premium = false, vocations = { 3, 7 }, special = false, source = 0, description = 'Onda em linha que empurra e desacelera.' },
    ['Suiton: V\xF3rtice Devorador'] = { id = 909, name = 'Suiton: V\xF3rtice Devorador', words = 'suiton vortice devorador', type = 'Instant', level = 45, mana = 72, soul = 0, maglevel = 0, icon = 'suiton_vortice_devorador', clientId = 9, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 5, exhaustion = 9000, premium = false, vocations = { 3, 7 }, special = false, source = 0, description = 'Um redemoinho colossal engole a \xE1rea e arrasta tudo para o centro.' },
    ['Raiton: Agulha de Raio'] = { id = 910, name = 'Raiton: Agulha de Raio', words = 'raiton hari', type = 'Instant', level = 1, mana = 14, soul = 0, maglevel = 0, icon = 'raiton_hari', clientId = 10, group = { [1] = 1000 }, needTarget = true, parameter = false, range = 7, exhaustion = 1500, premium = false, vocations = { 1, 5 }, special = false, source = 0, description = 'Agulha el\xE9trica r\xE1pida, pode paralisar.' },
    ['Raiton: Corrente Est\xE1tica'] = { id = 911, name = 'Raiton: Corrente Est\xE1tica', words = 'raiton corrente estatica', type = 'Instant', level = 6, mana = 16, soul = 0, maglevel = 0, icon = 'raiton_corrente_estatica', clientId = 11, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 1, exhaustion = 2500, premium = false, vocations = { 1, 5 }, special = false, source = 0, description = 'A eletricidade salta em cruz pelo ch\xE3o a partir do conjurador.' },
    ['Raiton: Lan\xE7a do Rel\xE2mpago'] = { id = 912, name = 'Raiton: Lan\xE7a do Rel\xE2mpago', words = 'raiton lanca relampago', type = 'Instant', level = 18, mana = 40, soul = 0, maglevel = 0, icon = 'raiton_lanca_relampago', clientId = 12, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 5, exhaustion = 5500, premium = false, vocations = { 1, 5 }, special = false, source = 0, description = 'Um raio cont\xEDnuo perfura em linha reta e atravessa v\xE1rios inimigos.' },
    ['Raiton: Armadura El\xE9trica'] = { id = 913, name = 'Raiton: Armadura El\xE9trica', words = 'raiton armadura eletrica', type = 'Instant', level = 24, mana = 36, soul = 0, maglevel = 0, icon = 'raiton_armadura_eletrica', clientId = 13, group = { [2] = 1000 }, needTarget = false, parameter = false, range = 1, exhaustion = 16000, premium = false, vocations = { 1, 5 }, special = false, source = 0, description = 'Uma casca de eletricidade cobre o corpo, acelerando a recupera\xE7\xE3o enquanto dura.' },
    ['Raiton: Punho do Trov\xE3o'] = { id = 914, name = 'Raiton: Punho do Trov\xE3o', words = 'raiton punho trovao', type = 'Instant', level = 30, mana = 50, soul = 0, maglevel = 0, icon = 'raiton_punho_trovao', clientId = 14, group = { [1] = 1000 }, needTarget = true, parameter = false, range = 1, exhaustion = 7000, premium = false, vocations = { 1, 5 }, special = false, source = 0, description = 'Concentra o raio na palma da m\xE3o e desfere um golpe devastador no alvo adjacente.' },
    ['Doton: Muralha de Pedra'] = { id = 915, name = 'Doton: Muralha de Pedra', words = 'doton muralha pedra', type = 'Instant', level = 8, mana = 28, soul = 0, maglevel = 0, icon = 'doton_muralha_pedra', clientId = 15, group = { [2] = 1000 }, needTarget = false, parameter = false, range = 1, exhaustion = 14000, premium = false, vocations = { 2, 6 }, special = false, source = 0, description = 'Ergue uma casca de rocha ao redor do corpo, endurecendo a pele por alguns segundos.' },
    ['Doton: Estacas de Terra'] = { id = 916, name = 'Doton: Estacas de Terra', words = 'doton estacas terra', type = 'Instant', level = 22, mana = 40, soul = 0, maglevel = 0, icon = 'doton_estacas_terra', clientId = 16, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 4, exhaustion = 6000, premium = false, vocations = { 2, 6 }, special = false, source = 0, description = 'Estacas de pedra irrompem do ch\xE3o em cruz, prendendo quem estiver em cima.' },
    ['Doton: Colapso do Terreno'] = { id = 917, name = 'Doton: Colapso do Terreno', words = 'doton colapso terreno', type = 'Instant', level = 48, mana = 70, soul = 0, maglevel = 0, icon = 'doton_colapso_terreno', clientId = 17, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 5, exhaustion = 9000, premium = false, vocations = { 2, 6 }, special = false, source = 0, description = 'O solo afunda num raio amplo e esmaga tudo que est\xE1 dentro da cratera.' },
    ['Fuuton: L\xE2mina de Vento'] = { id = 918, name = 'Fuuton: L\xE2mina de Vento', words = 'fuuton lamina vento', type = 'Instant', level = 1, mana = 13, soul = 0, maglevel = 0, icon = 'fuuton_lamina_vento', clientId = 18, group = { [1] = 1000 }, needTarget = true, parameter = false, range = 6, exhaustion = 1700, premium = false, vocations = { 2, 6 }, special = false, source = 0, description = 'Uma l\xE2mina de ar comprimido cortando em linha reta at\xE9 o alvo.' },
    ['Fuuton: Rajada Cortante'] = { id = 919, name = 'Fuuton: Rajada Cortante', words = 'fuuton rajada cortante', type = 'Instant', level = 16, mana = 34, soul = 0, maglevel = 0, icon = 'fuuton_rajada_cortante', clientId = 19, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 3, exhaustion = 4500, premium = false, vocations = { 2, 6 }, special = false, source = 0, description = 'Uma rajada em leque que retalha tudo \xE0 frente e desequilibra os atingidos.' },
    ['Kawarimi no Jutsu'] = { id = 920, name = 'Kawarimi no Jutsu', words = 'kawarimi', type = 'Instant', level = 5, mana = 20, soul = 0, maglevel = 0, icon = 'kawarimi', clientId = 20, group = { [2] = 1000 }, needTarget = false, parameter = false, range = 1, exhaustion = 12000, premium = false, vocations = { 1, 2, 3, 4, 5, 6, 7, 8 }, special = false, source = 0, description = 'Substitui\xE7\xE3o: fica invulner\xE1vel por 1s e teleporta 2 tiles para tr\xE1s.' },
    ['Bunshin no Jutsu'] = { id = 921, name = 'Bunshin no Jutsu', words = 'bunshin', type = 'Instant', level = 8, mana = 25, soul = 0, maglevel = 0, icon = 'bunshin', clientId = 21, group = { [2] = 1000 }, needTarget = false, parameter = false, range = 1, exhaustion = 15000, premium = false, vocations = { 1, 2, 3, 4, 5, 6, 7, 8 }, special = false, source = 0, description = 'Cria 2 clones que distraem monstros por 6s.' },
    ['Shousen: Palma Curativa'] = { id = 922, name = 'Shousen: Palma Curativa', words = 'shousen', type = 'Instant', level = 10, mana = 35, soul = 0, maglevel = 0, icon = 'shousen', clientId = 22, group = { [2] = 1000 }, needTarget = false, parameter = false, range = 1, exhaustion = 10000, premium = false, vocations = { 1, 2, 3, 4, 5, 6, 7, 8 }, special = false, source = 0, description = 'Cura o pr\xF3prio HP ao longo de 5s.' },
    ['Doku: N\xE9voa Venenosa'] = { id = 923, name = 'Doku: N\xE9voa Venenosa', words = 'doku kiri', type = 'Instant', level = 25, mana = 46, soul = 0, maglevel = 0, icon = 'doku_kiri', clientId = 23, group = { [1] = 1000 }, needTarget = false, parameter = false, range = 2, exhaustion = 6000, premium = false, vocations = { 1, 2, 3, 4, 5, 6, 7, 8 }, special = false, source = 0, description = 'Exala uma n\xE9voa roxa ao redor do conjurador; quem respira sai envenenado.' },
    ['Fuuin: Selo de Conten\xE7\xE3o'] = { id = 924, name = 'Fuuin: Selo de Conten\xE7\xE3o', words = 'fuuin contencao', type = 'Instant', level = 40, mana = 45, soul = 0, maglevel = 0, icon = 'fuuin_contencao', clientId = 24, group = { [1] = 1000 }, needTarget = true, parameter = false, range = 4, exhaustion = 12000, premium = false, vocations = { 1, 2, 3, 4, 5, 6, 7, 8 }, special = false, source = 0, description = 'Selo de papel que trava os m\xFAsculos do alvo por alguns segundos.' },
}

-- Vilas por vocation_id (o que player:getVocation() devolve). setName e o nome do
-- conjunto de hotkeys do game_actionbar: ASCII puro, porque vira chave no JSON.
NarutoVillages = {
    [1] = { id = 'leaf', name = 'Vila da Folha', setName = 'Vila da Folha', element = 'katon' },
    [2] = { id = 'mist', name = 'Vila da N\xE9voa', setName = 'Vila da Nevoa', element = 'suiton' },
    [3] = { id = 'cloud', name = 'Vila da Nuvem', setName = 'Vila da Nuvem', element = 'raiton' },
    [4] = { id = 'sand', name = 'Vila da Areia', setName = 'Vila da Areia', element = 'fuuton' },
}

-- Ordem sugerida da barra de acao: por level exigido, depois nome.
NarutoJutsuOrder = {
    'Fuuton: L\xE2mina de Vento',
    'Katon: Grande Bola de Fogo',
    'Raiton: Agulha de Raio',
    'Suiton: Proj\xE9til de \xC1gua',
    'Kawarimi no Jutsu',
    'Katon: Sopro de Brasas',
    'Raiton: Corrente Est\xE1tica',
    'Suiton: N\xE9voa Cortante',
    'Bunshin no Jutsu',
    'Doton: Muralha de Pedra',
    'Shousen: Palma Curativa',
    'Katon: Flores de F\xEAnix',
    'Fuuton: Rajada Cortante',
    'Raiton: Lan\xE7a do Rel\xE2mpago',
    'Katon: Anel de Chamas',
    'Doton: Estacas de Terra',
    'Suiton: Pris\xE3o de \xC1gua',
    'Raiton: Armadura El\xE9trica',
    'Doku: N\xE9voa Venenosa',
    'Suiton: Drag\xE3o de \xC1gua',
    'Raiton: Punho do Trov\xE3o',
    'Katon: Drag\xE3o de Fogo',
    'Fuuin: Selo de Conten\xE7\xE3o',
    'Suiton: V\xF3rtice Devorador',
    'Doton: Colapso do Terreno',
}
