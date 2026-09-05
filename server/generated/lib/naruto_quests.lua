-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/lib/naruto_quests.lua e adicione `dofile('data/lib/naruto_quests.lua')` em data/lib/lib.lua
-- Storage: -1/ausente = não iniciada, 0..count-1 = progresso, count = pronta, 50500 = entregue (marcador)
NarutoQuests = {}
NarutoQuests.RYO_ID = 2148
NarutoQuests.DONE = 50500
NarutoQuests.list = {
	{id = 'q_lair_1_illusive_eye', npc = 'quest_giver_akatsuki_lair', name = 'Exame Anbu (1/2) — O Vigia Ilusório', text = 'Ninguém que entra aqui como Chunin sai vivo. Prove que é Anbu: derrote O Vigia Ilusório.', monster = 'O Vigia Ilusório', count = 1, storage = 50001, reward = {xp = 60000, ryo = 15000, items = {{id = 7591, count = 1}}}},
	{id = 'q_lair_2_masked_puppeteer', npc = 'quest_giver_akatsuki_lair', name = 'Exame Anbu (2/2) — O Mascarado das Sombras', text = 'O segundo guardião puxa os fios de longe. Encontre-o e encerre isso.', monster = 'O Mascarado das Sombras', count = 1, storage = 50002, reward = {xp = 70000, ryo = 18000, items = {{id = 7591, count = 1}}}},
	{id = 'q_lair_3_rings_bearer', npc = 'quest_giver_akatsuki_lair', name = 'Exame Kage (1/2) — O Portador dos Seis Caminhos', text = 'Só um Kage de verdade encara o próximo guardião e vive para contar. Derrote O Portador dos Seis Caminhos.', monster = 'O Portador dos Seis Caminhos', count = 1, storage = 50003, reward = {xp = 85000, ryo = 22000, items = {{id = 8472, count = 1}}}},
	{id = 'q_lair_4_crimson_ancestor', npc = 'quest_giver_akatsuki_lair', name = 'Exame Kage (2/2) — O Ancestral da Nuvem Vermelha', text = 'O fundador da organização te espera no salão final. Vença, e a vila vai te chamar de Kage.', monster = 'O Ancestral da Nuvem Vermelha', count = 1, storage = 50004, reward = {xp = 120000, ryo = 40000, items = {{id = 6938, count = 1}}}},
	{id = 'q_coastal_mercenaries', npc = 'quest_giver_coastal', name = 'A ponte ameaçada', text = 'Mercenários contratados por uma guilda rival atacam quem trabalha na ponte. Afaste-os. Mate 8.', monster = 'Mercenário da Ponte', count = 8, storage = 50005, reward = {xp = 900, ryo = 250, items = {{id = 7618, count = 1}}}},
	{id = 'q_coastal_scouts', npc = 'quest_giver_coastal', name = 'Olhos na neblina', text = 'Batedores vigiam a estrada da costa. Mate 8.', monster = 'Batedor da Névoa', count = 8, storage = 50006, reward = {xp = 1300, ryo = 350, items = {{id = 7378, count = 1}}}},
	{id = 'q_coastal_guardians', npc = 'quest_giver_coastal', name = 'Quebrando a linha', text = 'Guardiões da neblina bloqueiam a entrada da vila. Derrube 8.', monster = 'Guardião da Neblina', count = 8, storage = 50007, reward = {xp = 1800, ryo = 500, items = {{id = 7588, count = 1}}}},
	{id = 'q_coastal_swordsman', npc = 'quest_giver_coastal', name = 'O Espadachim da Névoa', text = 'Um espadachim renegado e seu aprendiz mascarado vieram sabotar a ponte que salvaria esta vila. Derrote os dois.', monster = 'Espadachim da Névoa', count = 1, storage = 50008, reward = {xp = 12000, ryo = 4000, items = {{id = 2412, count = 1}}}},
	{id = 'q_wolves_1', npc = 'quest_giver_leaf', name = 'Lobos na trilha', text = 'Os lobos estão atacando viajantes. Mate 5.', monster = 'Lobo', count = 5, storage = 50009, reward = {xp = 120, ryo = 60, items = {{id = 7618, count = 1}}}},
	{id = 'q_bandits_1', npc = 'quest_giver_leaf', name = 'Limpando a estrada', text = 'Bandidos na estrada leste. Mate 10.', monster = 'Bandido', count = 10, storage = 50010, reward = {xp = 400, ryo = 200, items = {{id = 1949, count = 1}}}},
	{id = 'q_bandit_chief', npc = 'quest_giver_leaf', name = 'O Chefe', text = 'Acabe com o Chefe dos Bandidos no sudeste da floresta.', monster = 'Chefe dos Bandidos', count = 1, storage = 50011, reward = {xp = 1500, ryo = 800, items = {{id = 1988, count = 1}}}},
	{id = 'q_leeches', npc = 'quest_giver_swamp', name = 'Sangue ruim', text = 'Sanguessugas infestam a margem. Mate 8.', monster = 'Sanguessuga Gigante', count = 8, storage = 50012, reward = {xp = 900, ryo = 300, items = {{id = 8473, count = 1}, {id = 8473, count = 1}}}},
	{id = 'q_toads', npc = 'quest_giver_swamp', name = 'Coaxar da morte', text = 'Mate 10 sapos gigantes.', monster = 'Sapo Gigante', count = 10, storage = 50013, reward = {xp = 2000, ryo = 600, items = {{id = 2463, count = 1}}}},
	{id = 'q_rogues', npc = 'quest_giver_swamp', name = 'Desertores', text = 'Traga a cabeça de 8 ninjas renegados.', monster = 'Ninja Renegado', count = 8, storage = 50014, reward = {xp = 3500, ryo = 1200, items = {{id = 1948, count = 1}}}},
	{id = 'q_white_serpent', npc = 'quest_giver_swamp', name = 'A Serpente Branca', text = 'Um renegado de pele pálida montou covil no fim da Floresta da Morte. Ele não é humano faz tempo. Mate a Serpente Branca.', monster = 'Serpente Branca', count = 1, storage = 50015, reward = {xp = 9000, ryo = 3500, items = {{id = 1956, count = 1}}}},
	{id = 'exam_chunin_1_teoria', npc = 'exam_proctor_forest', name = 'Exame Chunin — Prova Teórica', text = 'Antes de qualquer coisa, prove que prestou atenção no que a vila te ensinou. Responda o que eu perguntar e traga prova de que ainda sabe se virar sozinho na floresta.', monster = 'Cobra da Floresta', count = 1, storage = 50016, reward = {xp = 500, ryo = 100, items = {}}},
	{id = 'exam_chunin_2a_pergaminho_ceu', npc = 'exam_proctor_forest', name = 'Exame Chunin — Pergaminho do Céu', text = 'Etapa 2: sobrevivência na Floresta da Morte. O Sapo Ancião guarda um Pergaminho do Céu. Traga-o.', monster = 'Sapo Ancião', count = 1, storage = 50017, reward = {xp = 0, ryo = 0, items = {{id = 6287, count = 1}}}},
	{id = 'exam_chunin_2b_pergaminho_terra', npc = 'exam_proctor_forest', name = 'Exame Chunin — Pergaminho da Terra', text = 'Agora o Pergaminho da Terra. A Serpente Branca guarda o dela no fim da floresta — só entre se estiver pronto.', monster = 'Serpente Branca', count = 1, storage = 50018, reward = {xp = 0, ryo = 0, items = {{id = 6288, count = 1}}}},
	{id = 'exam_chunin_3a_rival_pedra', npc = 'exam_proctor_forest', name = 'Exame Chunin — Torneio (1/3)', text = 'Etapa 3: o torneio. Seu primeiro oponente veio da Vila da Pedra.', monster = 'Rival do Exame — Pedra', count = 1, storage = 50019, reward = {xp = 300, ryo = 50, items = {}}},
	{id = 'exam_chunin_3b_rival_som', npc = 'exam_proctor_forest', name = 'Exame Chunin — Torneio (2/3)', text = 'Seu segundo oponente veio da Vila do Som.', monster = 'Rival do Exame — Som', count = 1, storage = 50020, reward = {xp = 300, ryo = 50, items = {}}},
	{id = 'exam_chunin_3c_rival_mist', npc = 'exam_proctor_forest', name = 'Exame Chunin — Torneio (3/3)', text = 'Seu último oponente veio da Vila da Névoa. Vença e você será Chunin.', monster = 'Rival do Exame — Névoa', count = 1, storage = 50021, reward = {xp = 5000, ryo = 2000, items = {{id = 2464, count = 1}}}},
	{id = 'q_mountain_eagles', npc = 'quest_giver_mountain', name = 'Céu limpo', text = 'As águias do trovão não deixam ninguém subir a trilha. Abata 15.', monster = 'Águia do Trovão', count = 15, storage = 50022, reward = {xp = 20000, ryo = 6000, items = {{id = 7591, count = 1}}}},
	{id = 'q_mountain_oni', npc = 'quest_giver_mountain', name = 'O que desce do gelo', text = 'Onis da geleira invadiram o acampamento. Mate 10.', monster = 'Oni da Geleira', count = 10, storage = 50023, reward = {xp = 32000, ryo = 10000, items = {{id = 2646, count = 1}}}},
	{id = 'q_mountain_serpents', npc = 'quest_giver_mountain', name = 'As fendas quentes', text = 'As serpentes de magma estão abrindo o pico por dentro. Mate 10.', monster = 'Serpente de Magma', count = 10, storage = 50024, reward = {xp = 48000, ryo = 16000, items = {{id = 6119, count = 1}}}},
	{id = 'q_mountain_curse_partner', npc = 'quest_giver_mountain', name = 'O Sócio Eterno', text = 'Uma dupla amaldiçoada divide esta montanha. A metade que ainda parece gente não sabe morrer — mas sabe sangrar. Enfrente O Sócio Eterno.', monster = 'O Sócio Eterno', count = 1, storage = 50025, reward = {xp = 65000, ryo = 22000, items = {{id = 5952, count = 1}}}},
	{id = 'q_mountain_boss', npc = 'quest_giver_mountain', name = 'A raiva antiga', text = 'Dentro do pico dorme o Oni Ancestral, a outra metade da dupla amaldiçoada. Ele não vai dormir para sempre.', monster = 'Oni Ancestral', count = 1, storage = 50026, reward = {xp = 90000, ryo = 30000, items = {{id = 2169, count = 1}}}},
	{id = 'q_ruins_puppets', npc = 'quest_giver_ruins', name = 'Ordens antigas', text = 'As marionetes ainda patrulham o pátio. Destrua 12 delas.', monster = 'Marionete de Combate', count = 12, storage = 50027, reward = {xp = 6000, ryo = 1500, items = {{id = 7588, count = 1}}}},
	{id = 'q_ruins_sentinels', npc = 'quest_giver_ruins', name = 'Quebrando o portão', text = 'Sentinelas de pedra bloqueiam o portão interno. Derrube 10.', monster = 'Sentinela de Pedra', count = 10, storage = 50028, reward = {xp = 9000, ryo = 2400, items = {{id = 2645, count = 1}}}},
	{id = 'q_ruins_shamans', npc = 'quest_giver_ruins', name = 'Selos que não se apagam', text = 'Os xamãs mantêm a maldição viva. Silencie 8.', monster = 'Xamã da Maldição', count = 8, storage = 50029, reward = {xp = 14000, ryo = 4000, items = {{id = 2131, count = 1}}}},
	{id = 'q_ruins_deserter', npc = 'quest_giver_ruins', name = 'O gênio desertor', text = 'Um desertor de elite escondeu-se nas ruínas atrás de poder proibido, recrutando para a Toca do Som. Detenha-o antes que ele siga viagem.', monster = 'Desertor de Elite', count = 1, storage = 50030, reward = {xp = 22000, ryo = 8000, items = {{id = 2131, count = 1}}}},
	{id = 'q_ruins_boss', npc = 'quest_giver_ruins', name = 'Quem puxa os fios', text = 'No salão central alguém comanda tudo isso. Acabe com o Marionetista.', monster = 'Marionetista das Ruínas', count = 1, storage = 50031, reward = {xp = 30000, ryo = 12000, items = {{id = 2164, count = 1}}}},
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
