-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/lib/naruto_quests.lua e adicione `dofile('data/lib/naruto_quests.lua')` em data/lib/lib.lua
-- Storage: -1/ausente = não iniciada, 0..count-1 = progresso, count = pronta, 50500 = entregue (marcador)
NarutoQuests = {}
NarutoQuests.RYO_ID = 2148
NarutoQuests.DONE = 50500
NarutoQuests.list = {
	{id = 'q_wolves_1', npc = 'quest_giver_leaf', name = 'Lobos na trilha', text = 'Os lobos estão atacando viajantes. Mate 5.', monster = 'Lobo', count = 5, storage = 50001, reward = {xp = 120, ryo = 60, items = {{id = 7618, count = 1}}}},
	{id = 'q_bandits_1', npc = 'quest_giver_leaf', name = 'Limpando a estrada', text = 'Bandidos na estrada leste. Mate 10.', monster = 'Bandido', count = 10, storage = 50002, reward = {xp = 400, ryo = 200, items = {{id = 1949, count = 1}}}},
	{id = 'q_bandit_chief', npc = 'quest_giver_leaf', name = 'O Chefe', text = 'Acabe com o Chefe dos Bandidos no sudeste da floresta.', monster = 'Chefe dos Bandidos', count = 1, storage = 50003, reward = {xp = 1500, ryo = 800, items = {{id = 1988, count = 1}}}},
	{id = 'q_leeches', npc = 'quest_giver_swamp', name = 'Sangue ruim', text = 'Sanguessugas infestam a margem. Mate 8.', monster = 'Sanguessuga Gigante', count = 8, storage = 50004, reward = {xp = 900, ryo = 300, items = {{id = 8473, count = 1}, {id = 8473, count = 1}}}},
	{id = 'q_toads', npc = 'quest_giver_swamp', name = 'Coaxar da morte', text = 'Mate 10 sapos gigantes.', monster = 'Sapo Gigante', count = 10, storage = 50005, reward = {xp = 2000, ryo = 600, items = {{id = 2463, count = 1}}}},
	{id = 'q_rogues', npc = 'quest_giver_swamp', name = 'Desertores', text = 'Traga a cabeça de 8 ninjas renegados.', monster = 'Ninja Renegado', count = 8, storage = 50006, reward = {xp = 3500, ryo = 1200, items = {{id = 1948, count = 1}}}},
	{id = 'q_white_serpent', npc = 'quest_giver_swamp', name = 'A Serpente Branca', text = 'Um renegado de pele pálida montou covil no fim da Floresta da Morte. Ele não é humano faz tempo. Mate a Serpente Branca.', monster = 'Serpente Branca', count = 1, storage = 50007, reward = {xp = 9000, ryo = 3500, items = {{id = 1956, count = 1}}}},
	{id = 'q_mountain_eagles', npc = 'quest_giver_mountain', name = 'Céu limpo', text = 'As águias do trovão não deixam ninguém subir a trilha. Abata 15.', monster = 'Águia do Trovão', count = 15, storage = 50008, reward = {xp = 20000, ryo = 6000, items = {{id = 7591, count = 1}}}},
	{id = 'q_mountain_oni', npc = 'quest_giver_mountain', name = 'O que desce do gelo', text = 'Onis da geleira invadiram o acampamento. Mate 10.', monster = 'Oni da Geleira', count = 10, storage = 50009, reward = {xp = 32000, ryo = 10000, items = {{id = 2646, count = 1}}}},
	{id = 'q_mountain_serpents', npc = 'quest_giver_mountain', name = 'As fendas quentes', text = 'As serpentes de magma estão abrindo o pico por dentro. Mate 10.', monster = 'Serpente de Magma', count = 10, storage = 50010, reward = {xp = 48000, ryo = 16000, items = {{id = 6119, count = 1}}}},
	{id = 'q_mountain_boss', npc = 'quest_giver_mountain', name = 'A raiva antiga', text = 'Dentro do pico dorme o Oni Ancestral. Ele não vai dormir para sempre.', monster = 'Oni Ancestral', count = 1, storage = 50011, reward = {xp = 90000, ryo = 30000, items = {{id = 2169, count = 1}}}},
	{id = 'q_ruins_puppets', npc = 'quest_giver_ruins', name = 'Ordens antigas', text = 'As marionetes ainda patrulham o pátio. Destrua 12 delas.', monster = 'Marionete de Combate', count = 12, storage = 50012, reward = {xp = 6000, ryo = 1500, items = {{id = 7588, count = 1}}}},
	{id = 'q_ruins_sentinels', npc = 'quest_giver_ruins', name = 'Quebrando o portão', text = 'Sentinelas de pedra bloqueiam o portão interno. Derrube 10.', monster = 'Sentinela de Pedra', count = 10, storage = 50013, reward = {xp = 9000, ryo = 2400, items = {{id = 2645, count = 1}}}},
	{id = 'q_ruins_shamans', npc = 'quest_giver_ruins', name = 'Selos que não se apagam', text = 'Os xamãs mantêm a maldição viva. Silencie 8.', monster = 'Xamã da Maldição', count = 8, storage = 50014, reward = {xp = 14000, ryo = 4000, items = {{id = 2131, count = 1}}}},
	{id = 'q_ruins_boss', npc = 'quest_giver_ruins', name = 'Quem puxa os fios', text = 'No salão central alguém comanda tudo isso. Acabe com o Marionetista.', monster = 'Marionetista das Ruínas', count = 1, storage = 50015, reward = {xp = 30000, ryo = 12000, items = {{id = 2164, count = 1}}}},
}
NarutoQuests.byNpc = {}
for _, q in ipairs(NarutoQuests.list) do
	NarutoQuests.byNpc[q.npc] = NarutoQuests.byNpc[q.npc] or {}
	table.insert(NarutoQuests.byNpc[q.npc], q)
end

function NarutoQuests.talk(player, quests)
	for _, q in ipairs(quests) do
		local st = player:getStorageValue(q.storage)
		if st ~= NarutoQuests.DONE then
			if st >= q.count then
				player:setStorageValue(q.storage, NarutoQuests.DONE)
				player:addExperience(q.reward.xp, true)
				if q.reward.ryo > 0 then player:addItem(NarutoQuests.RYO_ID, q.reward.ryo) end
				for _, it in ipairs(q.reward.items) do player:addItem(it.id, it.count) end
				return "Bom trabalho, ninja. Missão '" .. q.name .. "' concluída.", true
			elseif st >= 0 then
				return "Ainda não terminou? " .. q.name .. ": " .. st .. "/" .. q.count .. " " .. q.monster .. ".", false
			else
				player:setStorageValue(q.storage, 0)
				return q.text .. " (Missão aceita: " .. q.name .. ")", false
			end
		end
	end
	return "Não tenho mais nada para você por enquanto.", false
end
