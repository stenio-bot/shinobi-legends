-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/lib/naruto_quests.lua e adicione `dofile('data/lib/naruto_quests.lua')` em data/lib/lib.lua
-- Storage: -1/ausente = não iniciada, 0..count-1 = progresso (ou 0..quizMin-1 no quiz), count/quizMin = pronta,
-- 50500 = entregue (marcador). kind='kill' (padrão) conta mortes (scripts/naruto/quests_kill.lua);
-- kind='keyword_quiz' conta acertos da prova (ver npc/scripts/naruto/<npc>.lua, palavra-chave {prova}).
NarutoQuests = {}
NarutoQuests.RYO_ID = 2148
NarutoQuests.DONE = 50500
-- rank -> lista de storages das quests com grants_rank/grants_rank_progress daquele rank
-- (docs/lore/progressao.md). Promoção só acontece quando TODAS estiverem DONE — ver
-- NarutoRanks.checkProgress, chamado por NarutoQuests.talk ao concluir qualquer uma delas.
NarutoQuests.rankGroups = {
	['anbu'] = {50003, 50004, 50037, 50038},
	['kage'] = {50005, 50006},
	['jonin'] = {50012, 50045},
	['chunin'] = {50031},
}
NarutoQuests.list = {
	{id = 'q_lair_intro', npc = 'quest_giver_akatsuki_lair', name = 'Clones não sangram, mas caem', text = 'Antes de encarar os quatro guardiões, prove que aguenta os clones brancos que patrulham os corredores. Mate 10.', kind = 'kill', monster = 'Clone Branco', count = 10, storage = 50001, reward = {xp = 45000, ryo = 10000, items = {{id = 2490, count = 1}}}},
	{id = 'q_lair_guards', npc = 'quest_giver_akatsuki_lair', name = 'A guarda da Aurora', text = 'Os ninjas elite da Aurora não deixam ninguém passar sem lutar. Mate 8.', kind = 'kill', monster = 'Ninja Elite da Aurora', count = 8, storage = 50002, reward = {xp = 55000, ryo = 13000, items = {{id = 2489, count = 1}}}},
	{id = 'q_lair_1_illusive_eye', npc = 'quest_giver_akatsuki_lair', name = 'Exame Anbu (1/2) — O Vigia Ilusório', text = 'Ninguém que entra aqui como Chunin sai vivo. Prove que é Anbu: derrote O Vigia Ilusório.', kind = 'kill', monster = 'O Vigia Ilusório', count = 1, storage = 50003, reward = {xp = 60000, ryo = 15000, items = {{id = 7591, count = 1}}}, grantsRankProgress = 'anbu'},
	{id = 'q_lair_2_masked_puppeteer', npc = 'quest_giver_akatsuki_lair', name = 'Exame Anbu (2/2) — O Mascarado das Sombras', text = 'O segundo guardião puxa os fios de longe. Encontre-o e encerre isso.', kind = 'kill', monster = 'O Mascarado das Sombras', count = 1, storage = 50004, reward = {xp = 70000, ryo = 18000, items = {{id = 7591, count = 1}}}, grantsRank = 'anbu'},
	{id = 'q_lair_3_rings_bearer', npc = 'quest_giver_akatsuki_lair', name = 'Exame Kage (1/2) — O Portador dos Seis Caminhos', text = 'Só um Kage de verdade encara o próximo guardião e vive para contar. Derrote O Portador dos Seis Caminhos.', kind = 'kill', monster = 'O Portador dos Seis Caminhos', count = 1, storage = 50005, reward = {xp = 85000, ryo = 22000, items = {{id = 8472, count = 1}}}, grantsRankProgress = 'kage'},
	{id = 'q_lair_4_crimson_ancestor', npc = 'quest_giver_akatsuki_lair', name = 'Exame Kage (2/2) — O Ancestral da Nuvem Vermelha', text = 'O fundador da organização te espera no salão final. Vença, e a vila vai te chamar de Kage.', kind = 'kill', monster = 'O Ancestral da Nuvem Vermelha', count = 1, storage = 50006, reward = {xp = 120000, ryo = 40000, items = {{id = 6938, count = 1}}}, grantsRank = 'kage'},
	{id = 'q_coastal_mercenaries', npc = 'quest_giver_coastal', name = 'A ponte ameaçada', text = 'Mercenários contratados por uma guilda rival atacam quem trabalha na ponte. Afaste-os. Mate 8.', kind = 'kill', monster = 'Mercenário da Ponte', count = 8, storage = 50007, reward = {xp = 900, ryo = 250, items = {{id = 7618, count = 1}}}},
	{id = 'q_coastal_supplies', npc = 'quest_giver_coastal', name = 'Abastecendo os pescadores', text = 'A vila de pescadores está sem suprimentos com a ponte bloqueada. Entregue 5 poções de vida pequenas ao Ancião Tazu.', kind = 'collect_item', monster = '', count = 0, storage = 50008, reward = {xp = 700, ryo = 200, items = {{id = 2210, count = 1}}}, collectItems = {{id = 7618, count = 5, name = 'Poção de Vida Pequena'}}},
	{id = 'q_coastal_scouts', npc = 'quest_giver_coastal', name = 'Olhos na neblina', text = 'Batedores vigiam a estrada da costa. Mate 8.', kind = 'kill', monster = 'Batedor da Névoa', count = 8, storage = 50009, reward = {xp = 1300, ryo = 350, items = {{id = 7378, count = 1}}}},
	{id = 'q_coastal_guardians', npc = 'quest_giver_coastal', name = 'Quebrando a linha', text = 'Guardiões da neblina bloqueiam a entrada da vila. Derrube 8.', kind = 'kill', monster = 'Guardião da Neblina', count = 8, storage = 50010, reward = {xp = 1800, ryo = 500, items = {{id = 7588, count = 1}}}},
	{id = 'q_coastal_apprentice', npc = 'quest_giver_coastal', name = 'O aprendiz mascarado', text = 'Antes de chegar ao Espadachim, alguém precisa afastar o aprendiz que protege os flancos dele. Mate 6.', kind = 'kill', monster = 'Aprendiz Mascarado', count = 6, storage = 50011, reward = {xp = 3200, ryo = 900, items = {{id = 9928, count = 1}}}},
	{id = 'q_coastal_swordsman', npc = 'quest_giver_coastal', name = 'O Espadachim da Névoa', text = 'Um espadachim renegado e seu aprendiz mascarado vieram sabotar a ponte que salvaria esta vila. Derrote os dois.', kind = 'kill', monster = 'Espadachim da Névoa', count = 1, storage = 50012, reward = {xp = 12000, ryo = 4000, items = {{id = 2412, count = 1}}}, grantsRankProgress = 'jonin'},
	{id = 'q_wolves_1', npc = 'quest_giver_leaf', name = 'Lobos na trilha', text = 'Os lobos estão atacando viajantes. Mate 5.', kind = 'kill', monster = 'Lobo', count = 5, storage = 50013, reward = {xp = 120, ryo = 60, items = {{id = 7618, count = 1}}}},
	{id = 'q_forest_snakes', npc = 'quest_giver_leaf', name = 'Presas na relva', text = 'As cobras da floresta andam mordendo quem passa perto do riacho. Mate 8.', kind = 'kill', monster = 'Cobra da Floresta', count = 8, storage = 50014, reward = {xp = 260, ryo = 90, items = {{id = 2126, count = 1}}}},
	{id = 'q_bandits_1', npc = 'quest_giver_leaf', name = 'Limpando a estrada', text = 'Bandidos na estrada leste. Mate 10.', kind = 'kill', monster = 'Bandido', count = 10, storage = 50015, reward = {xp = 400, ryo = 200, items = {{id = 1949, count = 1}}}},
	{id = 'q_bandit_archers', npc = 'quest_giver_leaf', name = 'Flechas na copa das árvores', text = 'Bandidos arqueiros se escondem nas árvores para emboscar viajantes. Mate 8.', kind = 'kill', monster = 'Bandido Arqueiro', count = 8, storage = 50016, reward = {xp = 500, ryo = 220, items = {{id = 7378, count = 1}}}},
	{id = 'q_forest_supplies', npc = 'quest_giver_leaf', name = 'Abastecendo a vila', text = 'Antes de ir atrás do Chefe, a vila precisa de suprimentos: entregue 5 peles de lobo à Capitã Rin.', kind = 'collect_item', monster = '', count = 0, storage = 50017, reward = {xp = 350, ryo = 150, items = {{id = 7618, count = 1}}}, collectItems = {{id = 5897, count = 5, name = 'Pele de Lobo'}}},
	{id = 'q_bandit_chief', npc = 'quest_giver_leaf', name = 'O Chefe', text = 'Acabe com o Chefe dos Bandidos no sudeste da floresta.', kind = 'kill', monster = 'Chefe dos Bandidos', count = 1, storage = 50018, reward = {xp = 1500, ryo = 800, items = {{id = 1988, count = 1}}}},
	{id = 'q_leeches', npc = 'quest_giver_swamp', name = 'Sangue ruim', text = 'Sanguessugas infestam a margem. Mate 8.', kind = 'kill', monster = 'Sanguessuga Gigante', count = 8, storage = 50019, reward = {xp = 900, ryo = 300, items = {{id = 8473, count = 1}, {id = 8473, count = 1}}}},
	{id = 'q_lesser_serpents', npc = 'quest_giver_swamp', name = 'Ninhada de serpentes', text = 'Serpentes menores se multiplicaram perto do santuário abandonado. Mate 10.', kind = 'kill', monster = 'Serpente Menor', count = 10, storage = 50020, reward = {xp = 1400, ryo = 400, items = {{id = 5917, count = 1}}}},
	{id = 'q_forest_death_collect', npc = 'quest_giver_swamp', name = 'Peles curtidas', text = 'Rastreador Goro precisa de peles de sapo curtidas para reforçar equipamentos. Traga 6.', kind = 'collect_item', monster = '', count = 0, storage = 50021, reward = {xp = 1200, ryo = 350, items = {{id = 7589, count = 1}}}, collectItems = {{id = 5880, count = 6, name = 'Pele de Sapo'}}},
	{id = 'q_toads', npc = 'quest_giver_swamp', name = 'Coaxar da morte', text = 'Mate 10 sapos gigantes.', kind = 'kill', monster = 'Sapo Gigante', count = 10, storage = 50022, reward = {xp = 2000, ryo = 600, items = {{id = 2463, count = 1}}}},
	{id = 'q_elder_toad_hunt', npc = 'quest_giver_swamp', name = 'O sapo que não deveria existir', text = 'Antes do Exame, prove que sobrevive ao Sapo Ancião sozinho — sem pergaminho em jogo, só glória.', kind = 'kill', monster = 'Sapo Ancião', count = 1, storage = 50023, reward = {xp = 4000, ryo = 1500, items = {{id = 2642, count = 1}}}},
	{id = 'q_rogues', npc = 'quest_giver_swamp', name = 'Desertores', text = 'Traga a cabeça de 8 ninjas renegados.', kind = 'kill', monster = 'Ninja Renegado', count = 8, storage = 50024, reward = {xp = 3500, ryo = 1200, items = {{id = 1948, count = 1}}}},
	{id = 'q_white_serpent', npc = 'quest_giver_swamp', name = 'A Serpente Branca', text = 'Um renegado de pele pálida montou covil no fim da Floresta da Morte. Ele não é humano faz tempo. Mate a Serpente Branca.', kind = 'kill', monster = 'Serpente Branca', count = 1, storage = 50025, reward = {xp = 9000, ryo = 3500, items = {{id = 1956, count = 1}}}},
	{id = 'exam_chunin_1_teoria', npc = 'exam_proctor_forest', name = 'Exame Chunin — Prova Teórica', text = 'Antes de qualquer coisa, prove que prestou atenção no que a vila te ensinou. Responda o que eu perguntar e traga prova de que ainda sabe se virar sozinho na floresta.', kind = 'keyword_quiz', monster = '', count = 3, storage = 50026, reward = {xp = 500, ryo = 100, items = {}}, quiz = {{question = 'O que você gasta para lançar um jutsu?', keywords = {'chakra'}}, {question = 'Qual elemento é forte contra Doton?', keywords = {'fuuton', 'vento'}}, {question = 'Quem te ensinou seus primeiros jutsus?', keywords = {'sensei', 'mestre', 'hayato'}}, {question = 'Qual skill sobe quando você lança jutsu?', keywords = {'ninjutsu'}}, {question = 'Quem lidera a vila?', keywords = {'hokage'}}}, quizMin = 3},
	{id = 'exam_chunin_2a_pergaminho_ceu', npc = 'exam_proctor_forest', name = 'Exame Chunin — Pergaminho do Céu', text = 'Etapa 2: sobrevivência na Floresta da Morte. O Sapo Ancião guarda um Pergaminho do Céu. Traga-o.', kind = 'kill', monster = 'Sapo Ancião', count = 1, storage = 50027, reward = {xp = 0, ryo = 0, items = {{id = 6287, count = 1}}}},
	{id = 'exam_chunin_2b_pergaminho_terra', npc = 'exam_proctor_forest', name = 'Exame Chunin — Pergaminho da Terra', text = 'Agora o Pergaminho da Terra. A Serpente Branca guarda o dela no fim da floresta — só entre se estiver pronto.', kind = 'kill', monster = 'Serpente Branca', count = 1, storage = 50028, reward = {xp = 0, ryo = 0, items = {{id = 6288, count = 1}}}},
	{id = 'exam_chunin_3a_rival_pedra', npc = 'exam_proctor_forest', name = 'Exame Chunin — Torneio (1/3)', text = 'Etapa 3: o torneio. Seu primeiro oponente veio da Vila da Pedra.', kind = 'kill', monster = 'Rival do Exame — Pedra', count = 1, storage = 50029, reward = {xp = 300, ryo = 50, items = {}}},
	{id = 'exam_chunin_3b_rival_som', npc = 'exam_proctor_forest', name = 'Exame Chunin — Torneio (2/3)', text = 'Seu segundo oponente veio da Vila do Som.', kind = 'kill', monster = 'Rival do Exame — Som', count = 1, storage = 50030, reward = {xp = 300, ryo = 50, items = {}}},
	{id = 'exam_chunin_3c_rival_mist', npc = 'exam_proctor_forest', name = 'Exame Chunin — Torneio (3/3)', text = 'Seu último oponente veio da Vila da Névoa. Vença e você será Chunin.', kind = 'kill', monster = 'Rival do Exame — Névoa', count = 1, storage = 50031, reward = {xp = 5000, ryo = 2000, items = {{id = 2464, count = 1}}}, grantsRank = 'chunin'},
	{id = 'q_mountain_eagles', npc = 'quest_giver_mountain', name = 'Céu limpo', text = 'As águias do trovão não deixam ninguém subir a trilha. Abata 15.', kind = 'kill', monster = 'Águia do Trovão', count = 15, storage = 50032, reward = {xp = 20000, ryo = 6000, items = {{id = 7591, count = 1}}}},
	{id = 'q_mountain_relics', npc = 'quest_giver_mountain', name = 'Penas de valor', text = 'Mestra Yuki comercia penas de águia do trovão com ferreiros da vila. Traga 8.', kind = 'collect_item', monster = '', count = 0, storage = 50033, reward = {xp = 18000, ryo = 5000, items = {{id = 3965, count = 1}}}, collectItems = {{id = 5891, count = 8, name = 'Pena do Trovão'}}},
	{id = 'q_mountain_oni', npc = 'quest_giver_mountain', name = 'O que desce do gelo', text = 'Onis da geleira invadiram o acampamento. Mate 10.', kind = 'kill', monster = 'Oni da Geleira', count = 10, storage = 50034, reward = {xp = 32000, ryo = 10000, items = {{id = 2646, count = 1}}}},
	{id = 'q_mountain_serpents', npc = 'quest_giver_mountain', name = 'As fendas quentes', text = 'As serpentes de magma estão abrindo o pico por dentro. Mate 10.', kind = 'kill', monster = 'Serpente de Magma', count = 10, storage = 50035, reward = {xp = 48000, ryo = 16000, items = {{id = 6119, count = 1}}}},
	{id = 'q_mountain_lore', npc = 'quest_giver_mountain', name = 'O pacto que não morre', text = 'Mestra Yuki quer garantir que você entende o que vai enfrentar no topo da montanha antes de deixá-lo subir.', kind = 'keyword_quiz', monster = '', count = 2, storage = 50036, reward = {xp = 40000, ryo = 12000, items = {{id = 2161, count = 1}}}, quiz = {{question = 'O que acontece quando um dos dois seres do topo morre sozinho?', keywords = {'absorve', 'absorver', 'furia', 'fúria'}}, {question = 'Quem cobra um preço por cada vida que consome?', keywords = {'sócio eterno', 'socio eterno', 'boss_curse_partner'}}, {question = 'Quem lançou essa dupla imortal contra vilas inteiras na guerra?', keywords = {'nuvem vermelha', 'organizacao', 'organização'}}}, quizMin = 2},
	{id = 'q_mountain_curse_partner', npc = 'quest_giver_mountain', name = 'O Sócio Eterno', text = 'Uma dupla amaldiçoada divide esta montanha. A metade que ainda parece gente não sabe morrer — mas sabe sangrar. Enfrente O Sócio Eterno.', kind = 'kill', monster = 'O Sócio Eterno', count = 1, storage = 50037, reward = {xp = 65000, ryo = 22000, items = {{id = 5952, count = 1}}}, grantsRankProgress = 'anbu'},
	{id = 'q_mountain_boss', npc = 'quest_giver_mountain', name = 'A raiva antiga', text = 'Dentro do pico dorme o Oni Ancestral, a outra metade da dupla amaldiçoada. Ele não vai dormir para sempre.', kind = 'kill', monster = 'Oni Ancestral', count = 1, storage = 50038, reward = {xp = 90000, ryo = 30000, items = {{id = 2169, count = 1}}}, grantsRankProgress = 'anbu'},
	{id = 'q_ruins_intro', npc = 'quest_giver_ruins', name = 'Primeiras peças', text = 'Ancião Kaito quer entender como as marionetes ainda se movem. Traga 8 juntas de marionete.', kind = 'collect_item', monster = '', count = 0, storage = 50039, reward = {xp = 4500, ryo = 1000, items = {{id = 7588, count = 1}}}, collectItems = {{id = 5901, count = 8, name = 'Junta de Marionete'}}},
	{id = 'q_ruins_puppets', npc = 'quest_giver_ruins', name = 'Ordens antigas', text = 'As marionetes ainda patrulham o pátio. Destrua 12 delas.', kind = 'kill', monster = 'Marionete de Combate', count = 12, storage = 50040, reward = {xp = 6000, ryo = 1500, items = {{id = 7588, count = 1}}}},
	{id = 'q_ruins_sentinels', npc = 'quest_giver_ruins', name = 'Quebrando o portão', text = 'Sentinelas de pedra bloqueiam o portão interno. Derrube 10.', kind = 'kill', monster = 'Sentinela de Pedra', count = 10, storage = 50041, reward = {xp = 9000, ryo = 2400, items = {{id = 2645, count = 1}}}},
	{id = 'q_ruins_curse_lore', npc = 'quest_giver_ruins', name = 'Os selos que não se apagam', text = 'Antes de enfrentar os xamãs, Ancião Kaito testa o que você já sabe sobre a maldição do clã.', kind = 'keyword_quiz', monster = '', count = 2, storage = 50042, reward = {xp = 3000, ryo = 600, items = {{id = 2201, count = 1}}}, quiz = {{question = 'O que mantém os bonecos do clã \'vivos\' até hoje?', keywords = {'selo', 'selos', 'maldicao', 'maldição'}}, {question = 'Quem mantém os selos de maldição ativos há gerações?', keywords = {'xama', 'xamã', 'curse_shaman'}}, {question = 'Para onde o gênio desertor pretende fugir depois das Ruínas?', keywords = {'toca do som', 'som'}}}, quizMin = 2},
	{id = 'q_ruins_shamans', npc = 'quest_giver_ruins', name = 'Selos que não se apagam', text = 'Os xamãs mantêm a maldição viva. Silencie 8.', kind = 'kill', monster = 'Xamã da Maldição', count = 8, storage = 50043, reward = {xp = 14000, ryo = 4000, items = {{id = 2131, count = 1}}}},
	{id = 'q_ruins_deserter', npc = 'quest_giver_ruins', name = 'O gênio desertor', text = 'Um desertor de elite escondeu-se nas ruínas atrás de poder proibido, recrutando para a Toca do Som. Detenha-o antes que ele siga viagem.', kind = 'kill', monster = 'Desertor de Elite', count = 1, storage = 50044, reward = {xp = 22000, ryo = 8000, items = {{id = 2131, count = 1}}}},
	{id = 'q_ruins_boss', npc = 'quest_giver_ruins', name = 'Quem puxa os fios', text = 'No salão central alguém comanda tudo isso. Acabe com o Marionetista.', kind = 'kill', monster = 'Marionetista das Ruínas', count = 1, storage = 50045, reward = {xp = 30000, ryo = 12000, items = {{id = 2164, count = 1}}}, grantsRankProgress = 'jonin'},
}
NarutoQuests.byNpc = {}
for _, q in ipairs(NarutoQuests.list) do
	NarutoQuests.byNpc[q.npc] = NarutoQuests.byNpc[q.npc] or {}
	table.insert(NarutoQuests.byNpc[q.npc], q)
end

--- Checa progressão de rank (grants_rank/grants_rank_progress) depois de marcar uma quest
--- DONE. Retorna a mensagem extra de promoção, ou nil.
local function grantQuestRankIfReady(player, q)
	local rank = q.grantsRank or q.grantsRankProgress
	if not rank or not NarutoRanks then return nil end
	local group = NarutoQuests.rankGroups[rank]
	if not group then return nil end
	for _, storage in ipairs(group) do
		if player:getStorageValue(storage) ~= NarutoQuests.DONE then return nil end
	end
	if NarutoRanks.promote(player, rank) then
		return "Você agora é " .. NarutoRanks.byRank[rank].title .. "!"
	end
	return nil
end

--- Marca a quest DONE, aplica a recompensa e checa rank. Usada pelas 3 formas de conclusão
--- (kill, keyword_quiz, collect_item) para não duplicar a lógica de recompensa.
local function completeQuest(player, q)
	player:setStorageValue(q.storage, NarutoQuests.DONE)
	local xp = q.reward.xp
	if xp > 0 then player:addExperience(xp, true) end
	if q.reward.ryo > 0 then player:addItem(NarutoQuests.RYO_ID, q.reward.ryo) end
	for _, it in ipairs(q.reward.items) do player:addItem(it.id, it.count) end
	local msg = "Bom trabalho, ninja. Missão '" .. q.name .. "' concluída."
	local rankMsg = grantQuestRankIfReady(player, q)
	if rankMsg then msg = msg .. " " .. rankMsg end
	return msg
end

function NarutoQuests.talk(player, quests)
	for _, q in ipairs(quests) do
		local st = player:getStorageValue(q.storage)
		if st ~= NarutoQuests.DONE then
			if q.kind == 'keyword_quiz' then
				if st < 0 then
					player:setStorageValue(q.storage, 0)
					return q.text .. " (Missão aceita: " .. q.name .. "). Diga {prova} quando estiver pronto para responder.", false
				elseif st < q.count then
					return "Prova ainda não feita. Diga {prova} para começar: " .. q.name .. ".", false
				else
					return completeQuest(player, q), true
				end
			elseif q.kind == 'collect_item' then
				if st < 0 then
					player:setStorageValue(q.storage, 0)
					return q.text .. " (Missão aceita: " .. q.name .. ")", false
				end
				local missing = {}
				for _, it in ipairs(q.collectItems) do
					if player:getItemCount(it.id) < it.count then
						missing[#missing + 1] = it.count .. "x " .. it.name
					end
				end
				if #missing > 0 then
					return "Ainda falta trazer: " .. table.concat(missing, ", ") .. ".", false
				end
				for _, it in ipairs(q.collectItems) do player:removeItem(it.id, it.count) end
				return completeQuest(player, q), true
			elseif st >= q.count then
				return completeQuest(player, q), true
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
