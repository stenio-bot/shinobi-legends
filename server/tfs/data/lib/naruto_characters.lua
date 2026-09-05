-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Personagens jogaveis: cada looktype tem seu proprio conjunto de jutsus.
-- Gerado a partir de data/characters.json. Ver server/generated/scripts/naruto/character_switch.lua
-- para a logica de troca (NarutoCharacters.apply), definida ali por cima desta tabela.
NarutoCharacters = { list = {}, byLook = {}, byId = {}, byVillage = {}, allJutsuNames = {} }
table.insert(NarutoCharacters.list, {id = 'genin_laranja', name = 'Genin Laranja', looktype = 900, village_vocation = 1, jutsus = {'Fuuton: Lâmina de Vento', 'Kawarimi no Jutsu', 'Bunshin no Jutsu', 'Clone Sombrio', 'Fuuton: Rajada Cortante'}})
table.insert(NarutoCharacters.list, {id = 'genin_uchiha', name = 'Genin Uchiha', looktype = 901, village_vocation = 1, jutsus = {'Katon: Grande Bola de Fogo', 'Raiton: Agulha de Raio', 'Katon: Sopro de Brasas', 'Raiton: Corrente Estática', 'Katon: Flores de Fênix', 'Katon: Dragão de Fogo'}})
table.insert(NarutoCharacters.list, {id = 'kunoichi_rosa', name = 'Kunoichi Rosa', looktype = 902, village_vocation = 1, jutsus = {'Punho Suave', 'Kawarimi no Jutsu', 'Bunshin no Jutsu', 'Shousen: Palma Curativa', 'Chute Giratorio'}})
table.insert(NarutoCharacters.list, {id = 'herdeira_hyuga', name = 'Herdeira Hyuga', looktype = 903, village_vocation = 2, jutsus = {'Suiton: Projétil de Água', 'Suiton: Névoa Cortante', 'Suiton: Prisão de Água', 'Suiton: Dragão de Água', 'Suiton: Vórtice Devorador', 'Fuuin: Selo de Contenção'}})
table.insert(NarutoCharacters.list, {id = 'kunoichi_armas', name = 'Kunoichi das Armas', looktype = 905, village_vocation = 2, jutsus = {'Agulhas Multiplas', 'Kawarimi no Jutsu', 'Suiton: Névoa Cortante', 'Lamina de Chakra', 'Doku: Névoa Venenosa'}})
table.insert(NarutoCharacters.list, {id = 'ninja_verde', name = 'Ninja Verde', looktype = 904, village_vocation = 3, jutsus = {'Punho Suave', 'Kawarimi no Jutsu', 'Bunshin no Jutsu', 'Doton: Muralha de Pedra', 'Chute Giratorio'}})
table.insert(NarutoCharacters.list, {id = 'ninja_abelha', name = 'Ninja Abelha', looktype = 909, village_vocation = 3, jutsus = {'Raiton: Agulha de Raio', 'Raiton: Corrente Estática', 'Raiton: Lança do Relâmpago', 'Raiton: Armadura Elétrica', 'Raiton: Punho do Trovão'}})
table.insert(NarutoCharacters.list, {id = 'sabio_loiro', name = 'Sabio Loiro', looktype = 907, village_vocation = 4, jutsus = {'Fuuton: Lâmina de Vento', 'Raio Selado', 'Kawarimi no Jutsu', 'Fuuton: Rajada Cortante', 'Doton: Estacas de Terra'}})
table.insert(NarutoCharacters.list, {id = 'sabio_cerimonial', name = 'Sabio Cerimonial', looktype = 908, village_vocation = 4, jutsus = {'Fuuton: Lâmina de Vento', 'Doton: Muralha de Pedra', 'Fuuton: Rajada Cortante', 'Doton: Estacas de Terra', 'Doton: Colapso do Terreno'}})

for _, c in ipairs(NarutoCharacters.list) do
	NarutoCharacters.byLook[c.looktype] = c
	NarutoCharacters.byId[c.id] = c
	NarutoCharacters.byVillage[c.village_vocation] = NarutoCharacters.byVillage[c.village_vocation] or {}
	table.insert(NarutoCharacters.byVillage[c.village_vocation], c)
	for _, jname in ipairs(c.jutsus) do
		NarutoCharacters.allJutsuNames[jname] = true
	end
end
NarutoCharacters.allJutsuNames['Kawarimi no Jutsu'] = nil  -- universal, nunca esquecido
