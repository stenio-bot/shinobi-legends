-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/lib/naruto_quests.lua e adicione `dofile('data/lib/naruto_quests.lua')` em data/lib/lib.lua
-- Storage: -1/ausente = n\xE3o iniciada, 0..count-1 = progresso (ou 0..quizMin-1 no quiz), count/quizMin = pronta,
-- 50500 = entregue (marcador). kind='kill' (padr\xE3o) conta mortes (scripts/naruto/quests_kill.lua);
-- kind='keyword_quiz' conta acertos da prova (ver npc/scripts/naruto/<npc>.lua, palavra-chave {prova}).
NarutoQuests = {}
NarutoQuests.RYO_ID = 2148
NarutoQuests.DONE = 50500
-- rank -> lista de storages das quests com grants_rank/grants_rank_progress daquele rank
-- (docs/lore/progressao.md). Promo\xE7\xE3o s\xF3 acontece quando TODAS estiverem DONE \x97 ver
-- NarutoRanks.checkProgress, chamado por NarutoQuests.talk ao concluir qualquer uma delas.
NarutoQuests.rankGroups = {
	['anbu'] = {50003, 50004, 50039, 50040},
	['kage'] = {50006, 50007},
	['jonin'] = {50013, 50047},
	['chunin'] = {50033},
}
NarutoQuests.list = {
	{id = 'q_lair_intro', npc = 'quest_giver_akatsuki_lair', npcName = 'Capit\xE3 Anbu Suzu', name = 'Clones n\xE3o sangram, mas caem', text = 'Antes de encarar os quatro guardi\xF5es, prove que aguenta os clones brancos que patrulham os corredores. Mate 10.', kind = 'kill', monster = 'Clone Branco', count = 10, storage = 50001, reward = {xp = 45000, ryo = 10000, items = {{id = 2490, count = 1}}}},
	{id = 'q_lair_guards', npc = 'quest_giver_akatsuki_lair', npcName = 'Capit\xE3 Anbu Suzu', name = 'A guarda da Aurora', text = 'Os ninjas elite da Aurora n\xE3o deixam ningu\xE9m passar sem lutar. Mate 8.', kind = 'kill', monster = 'Ninja Elite da Aurora', count = 8, storage = 50002, reward = {xp = 55000, ryo = 13000, items = {{id = 2489, count = 1}}}},
	{id = 'q_lair_1_illusive_eye', npc = 'quest_giver_akatsuki_lair', npcName = 'Capit\xE3 Anbu Suzu', name = 'Exame Anbu (1/2) \x97 O Vigia Ilus\xF3rio', text = 'Ningu\xE9m que entra aqui como Chunin sai vivo. Prove que \xE9 Anbu: derrote O Vigia Ilus\xF3rio.', kind = 'kill', monster = 'O Vigia Ilus\xF3rio', count = 1, storage = 50003, reward = {xp = 60000, ryo = 15000, items = {{id = 7591, count = 1}}}, grantsRankProgress = 'anbu', doneText = 'Um olho fechado. Falta o segundo guardi\xE3o \x97 e ele j\xE1 sabe que voc\xEAs est\xE3o vindo.'},
	{id = 'q_lair_2_masked_puppeteer', npc = 'quest_giver_akatsuki_lair', npcName = 'Capit\xE3 Anbu Suzu', name = 'Exame Anbu (2/2) \x97 O Mascarado das Sombras', text = 'O segundo guardi\xE3o puxa os fios de longe. Encontre-o e encerre isso.', kind = 'kill', monster = 'O Mascarado das Sombras', count = 1, storage = 50004, reward = {xp = 70000, ryo = 18000, items = {{id = 7591, count = 1}}}, grantsRank = 'anbu', doneText = 'Anbu de verdade, enfim. Mas os dois que faltam s\xE3o os que fundaram tudo isso \x97 n\xE3o relaxem agora.'},
	{id = 'q_lair_lore_quiz', npc = 'quest_giver_akatsuki_lair', npcName = 'Capit\xE3 Anbu Suzu', name = 'O que ainda ecoa', text = 'Serpente Branca, Marionetista das Ru\xEDnas, S\xF3cio Eterno e Oni Ancestral j\xE1 ca\xEDram para voc\xEAs. Antes de abrir o corredor do Portador dos Seis Caminhos, provem que prestaram aten\xE7\xE3o em quem enfrentaram at\xE9 aqui.', kind = 'keyword_quiz', monster = '', count = 2, storage = 50005, reward = {xp = 78000, ryo = 20000, items = {{id = 7591, count = 1}}}, quiz = {{question = 'A Serpente Branca de verdade nunca foi s\xF3 uma cobra. O que ela era antes de abandonar a forma humana?', keywords = {'ninja', 'humano', 'renegado'}}, {question = 'O Marionetista das Ru\xEDnas quase n\xE3o lutava com o pr\xF3prio corpo. O que ele usava para lutar em seu lugar?', keywords = {'marionetes', 'marionete', 'bonecos', 'fios'}}, {question = 'Da dupla amaldi\xE7oada da Montanha do Trov\xE3o, o que acontece quando um dos dois morre sozinho?', keywords = {'absorve', 'absorver', 'furia', 'f\xFAria'}}}, quizMin = 2},
	{id = 'q_lair_3_rings_bearer', npc = 'quest_giver_akatsuki_lair', npcName = 'Capit\xE3 Anbu Suzu', name = 'Exame Kage (1/2) \x97 O Portador dos Seis Caminhos', text = 'S\xF3 um Kage de verdade encara o pr\xF3ximo guardi\xE3o e vive para contar. Derrote O Portador dos Seis Caminhos.', kind = 'kill', monster = 'O Portador dos Seis Caminhos', count = 1, storage = 50006, reward = {xp = 85000, ryo = 22000, items = {{id = 8472, count = 1}}}, grantsRankProgress = 'kage', doneText = 'Ele multiplicava a pr\xF3pria vontade em v\xE1rios corpos e ainda assim caiu para um s\xF3. Falta o fundador de tudo isso.'},
	{id = 'q_lair_4_crimson_ancestor', npc = 'quest_giver_akatsuki_lair', npcName = 'Capit\xE3 Anbu Suzu', name = 'Exame Kage (2/2) \x97 O Ancestral da Nuvem Vermelha', text = 'O fundador da organiza\xE7\xE3o te espera no sal\xE3o final. Ven\xE7a, e a vila vai te chamar de Kage.', kind = 'kill', monster = 'O Ancestral da Nuvem Vermelha', count = 1, storage = 50007, reward = {xp = 120000, ryo = 40000, items = {{id = 6938, count = 1}}}, grantsRank = 'kage', doneText = 'Voc\xEA fez o que nenhum Kage sozinho tinha conseguido: derrubou os l\xEDderes da Nuvem Vermelha. A vila vai te chamar de Kage a partir de hoje \x97 e vai ser verdade.'},
	{id = 'q_coastal_mercenaries', npc = 'quest_giver_coastal', npcName = 'Anci\xE3o Tazu', name = 'A ponte amea\xE7ada', text = 'Mercen\xE1rios contratados por uma guilda rival atacam quem trabalha na ponte. Afaste-os. Mate 8.', kind = 'kill', monster = 'Mercen\xE1rio da Ponte', count = 8, storage = 50008, reward = {xp = 900, ryo = 250, items = {{id = 7618, count = 1}}}},
	{id = 'q_coastal_supplies', npc = 'quest_giver_coastal', npcName = 'Anci\xE3o Tazu', name = 'Abastecendo os pescadores', text = 'A vila de pescadores est\xE1 sem suprimentos com a ponte bloqueada. Entregue 5 po\xE7\xF5es de vida pequenas ao Anci\xE3o Tazu.', kind = 'collect_item', monster = '', count = 0, storage = 50009, reward = {xp = 700, ryo = 200, items = {{id = 2210, count = 1}}}, collectItems = {{id = 7618, count = 5, name = 'Po\xE7\xE3o de Vida Pequena', itemKey = 'health_potion_small'}}},
	{id = 'q_coastal_scouts', npc = 'quest_giver_coastal', npcName = 'Anci\xE3o Tazu', name = 'Olhos na neblina', text = 'Batedores vigiam a estrada da costa \x97 dizem que servem a um espadachim renegado escondido al\xE9m da ponte. Afaste-os. Mate 8.', kind = 'kill', monster = 'Batedor da N\xE9voa', count = 8, storage = 50010, reward = {xp = 1300, ryo = 350, items = {{id = 7378, count = 1}}}},
	{id = 'q_coastal_guardians', npc = 'quest_giver_coastal', npcName = 'Anci\xE3o Tazu', name = 'Quebrando a linha', text = 'Guardi\xF5es da neblina bloqueiam a entrada da vila. Derrube 8.', kind = 'kill', monster = 'Guardi\xE3o da Neblina', count = 8, storage = 50011, reward = {xp = 1800, ryo = 500, items = {{id = 7588, count = 1}}}},
	{id = 'q_coastal_apprentice', npc = 'quest_giver_coastal', npcName = 'Anci\xE3o Tazu', name = 'O aprendiz mascarado', text = 'Antes de chegar ao Espadachim, algu\xE9m precisa afastar o aprendiz que protege os flancos dele. Mate 6.', kind = 'kill', monster = 'Aprendiz Mascarado', count = 6, storage = 50012, reward = {xp = 3200, ryo = 900, items = {{id = 9928, count = 1}}}},
	{id = 'q_coastal_swordsman', npc = 'quest_giver_coastal', npcName = 'Anci\xE3o Tazu', name = 'O Espadachim da N\xE9voa', text = 'Um espadachim renegado e seu aprendiz mascarado vieram sabotar a ponte que salvaria esta vila. Derrote os dois.', kind = 'kill', monster = 'Espadachim da N\xE9voa', count = 1, storage = 50013, reward = {xp = 12000, ryo = 4000, items = {{id = 2412, count = 1}}}, grantsRankProgress = 'jonin', doneText = 'Voc\xEAs salvaram esta ponte. Mas ouvi um batedor comentar, antes de cair, sobre uma floresta que mata os fracos rio acima \x97 cuidado. Antes de ir, d\xEA mais uma ronda: quero ter certeza que nenhum mercen\xE1rio ficou pra tr\xE1s.'},
	{id = 'q_wolves_1', npc = 'quest_giver_leaf', npcName = 'Capit\xE3 Rin', name = 'Lobos na trilha', text = 'Bem-vinda \xE0 Floresta da Vila, Genin. A Academia te ensinou o b\xE1sico \x97 hora de provar em campo. Os lobos andam atacando viajantes na trilha: mate 5.', kind = 'kill', monster = 'Lobo', count = 5, storage = 50014, reward = {xp = 120, ryo = 60, items = {{id = 7618, count = 1}}}},
	{id = 'q_forest_deer_1', npc = 'quest_giver_leaf', npcName = 'Capit\xE3 Rin', name = 'Um agrado para o posto avan\xE7ado', text = 'Os cervos da floresta n\xE3o fazem mal a ningu\xE9m, mas a carne deles rende um bom onigiri. Traga 3 para o posto avan\xE7ado \x97 n\xE3o precisa ca\xE7ar, eles nem revidam.', kind = 'collect_item', monster = '', count = 0, storage = 50015, reward = {xp = 150, ryo = 70, items = {{id = 7618, count = 1}}}, collectItems = {{id = 2666, count = 3, name = 'Onigiri', itemKey = 'onigiri'}}},
	{id = 'q_forest_snakes', npc = 'quest_giver_leaf', npcName = 'Capit\xE3 Rin', name = 'Presas na relva', text = 'As cobras da floresta andam mordendo quem passa perto do riacho. Mate 8.', kind = 'kill', monster = 'Cobra da Floresta', count = 8, storage = 50016, reward = {xp = 260, ryo = 90, items = {{id = 2126, count = 1}}}},
	{id = 'q_bandits_1', npc = 'quest_giver_leaf', npcName = 'Capit\xE3 Rin', name = 'Limpando a estrada', text = 'Bandidos na estrada leste. Mate 10.', kind = 'kill', monster = 'Bandido', count = 10, storage = 50017, reward = {xp = 400, ryo = 200, items = {{id = 1949, count = 1}}}},
	{id = 'q_bandit_archers', npc = 'quest_giver_leaf', npcName = 'Capit\xE3 Rin', name = 'Flechas na copa das \xE1rvores', text = 'Bandidos arqueiros se escondem nas \xE1rvores para emboscar viajantes. Mate 8.', kind = 'kill', monster = 'Bandido Arqueiro', count = 8, storage = 50018, reward = {xp = 500, ryo = 220, items = {{id = 7378, count = 1}}}},
	{id = 'q_forest_supplies', npc = 'quest_giver_leaf', npcName = 'Capit\xE3 Rin', name = 'Abastecendo a vila', text = 'Antes de ir atr\xE1s do Chefe, a vila precisa de suprimentos: entregue 5 peles de lobo \xE0 Capit\xE3 Rin.', kind = 'collect_item', monster = '', count = 0, storage = 50019, reward = {xp = 350, ryo = 150, items = {{id = 7618, count = 1}}}, collectItems = {{id = 5897, count = 5, name = 'Pele de Lobo', itemKey = 'wolf_pelt'}}},
	{id = 'q_bandit_chief', npc = 'quest_giver_leaf', npcName = 'Capit\xE3 Rin', name = 'O Chefe', text = 'Acabe com o Chefe dos Bandidos no sudeste da floresta.', kind = 'kill', monster = 'Chefe dos Bandidos', count = 1, storage = 50020, reward = {xp = 1500, ryo = 800, items = {{id = 1988, count = 1}}}, doneText = 'Bom trabalho, Genin. Mas isso foi s\xF3 a estrada perto de casa \x97 a Floresta da Morte separa quem est\xE1 pronto do resto do mundo, e ouvi dizer que mercadores da Costa das Mar\xE9s est\xE3o contratando gente como voc\xEA. S\xF3 uma \xFAltima coisa: garanta que n\xE3o sobrou nenhum bandido rondando a trilha.'},
	{id = 'q_leeches', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'Sangue ruim', text = 'Sanguessugas infestam a margem. Mate 8.', kind = 'kill', monster = 'Sanguessuga Gigante', count = 8, storage = 50021, reward = {xp = 900, ryo = 300, items = {{id = 8473, count = 1}, {id = 8473, count = 1}}}},
	{id = 'q_lesser_serpents', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'Ninhada de serpentes', text = 'Serpentes menores se multiplicaram perto do santu\xE1rio abandonado. Mate 10.', kind = 'kill', monster = 'Serpente Menor', count = 10, storage = 50022, reward = {xp = 1400, ryo = 400, items = {{id = 5917, count = 1}}}},
	{id = 'q_forest_death_collect', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'Peles curtidas', text = 'Rastreador Goro precisa de peles de sapo curtidas para refor\xE7ar equipamentos. Traga 6.', kind = 'collect_item', monster = '', count = 0, storage = 50023, reward = {xp = 1200, ryo = 350, items = {{id = 7589, count = 1}}}, collectItems = {{id = 5880, count = 6, name = 'Pele de Sapo', itemKey = 'toad_skin'}}},
	{id = 'q_toads', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'Coaxar da morte', text = 'Mate 10 sapos gigantes.', kind = 'kill', monster = 'Sapo Gigante', count = 10, storage = 50024, reward = {xp = 2000, ryo = 600, items = {{id = 2463, count = 1}}}},
	{id = 'q_elder_toad_hunt', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'O sapo que n\xE3o deveria existir', text = 'Antes do Exame, prove que sobrevive ao Sapo Anci\xE3o sozinho \x97 sem pergaminho em jogo, s\xF3 gl\xF3ria. Guarde essa vit\xF3ria na mem\xF3ria: a Instrutora Ibuki vai cobrar a mesma prova, oficialmente, quando voc\xEA for atr\xE1s do Pergaminho do C\xE9u.', kind = 'kill', monster = 'Sapo Anci\xE3o', count = 1, storage = 50025, reward = {xp = 4000, ryo = 1500, items = {{id = 2642, count = 1}}}},
	{id = 'q_rogues', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'Desertores', text = 'Traga a cabe\xE7a de 8 ninjas renegados.', kind = 'kill', monster = 'Ninja Renegado', count = 8, storage = 50026, reward = {xp = 3500, ryo = 1200, items = {{id = 1948, count = 1}}}},
	{id = 'q_white_serpent', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'A Serpente Branca', text = 'Um renegado de pele p\xE1lida montou covil no fim da Floresta da Morte. Ele n\xE3o \xE9 humano faz tempo. Mate a Serpente Branca \x97 e n\xE3o estranhe se a Instrutora Ibuki pedir o mesmo depois, para valer, na hora do Pergaminho da Terra.', kind = 'kill', monster = 'Serpente Branca', count = 1, storage = 50027, reward = {xp = 9000, ryo = 3500, items = {{id = 1956, count = 1}}}},
	{id = 'exam_chunin_1_teoria', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin \x97 Prova Te\xF3rica', text = 'Antes de qualquer coisa, prove que prestou aten\xE7\xE3o no que a vila te ensinou. Responda o que eu perguntar e traga prova de que ainda sabe se virar sozinho na floresta.', kind = 'keyword_quiz', monster = '', count = 3, storage = 50028, reward = {xp = 500, ryo = 100, items = {}}, quiz = {{question = 'O que voc\xEA gasta para lan\xE7ar um jutsu?', keywords = {'chakra'}}, {question = 'Qual elemento \xE9 forte contra Doton?', keywords = {'fuuton', 'vento'}}, {question = 'Quem te ensinou seus primeiros jutsus?', keywords = {'sensei', 'mestre', 'hayato'}}, {question = 'Qual skill sobe quando voc\xEA lan\xE7a jutsu?', keywords = {'ninjutsu'}}, {question = 'Quem lidera a vila?', keywords = {'hokage'}}}, quizMin = 3},
	{id = 'exam_chunin_2a_pergaminho_ceu', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin \x97 Pergaminho do C\xE9u', text = 'Etapa 2: sobreviv\xEAncia na Floresta da Morte. O Sapo Anci\xE3o guarda um Pergaminho do C\xE9u. Traga-o. Se j\xE1 provou pro Rastreador Goro que aguenta essa luta sozinho, j\xE1 sabe o que esperar \x97 dessa vez tem pergaminho de verdade em jogo.', kind = 'kill', monster = 'Sapo Anci\xE3o', count = 1, storage = 50029, reward = {xp = 0, ryo = 0, items = {{id = 6287, count = 1}}}},
	{id = 'exam_chunin_2b_pergaminho_terra', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin \x97 Pergaminho da Terra', text = 'Agora o Pergaminho da Terra. A Serpente Branca guarda o dela no fim da floresta \x97 s\xF3 entre se estiver pronto. Quem j\xE1 enfrentou essa serpente a pedido do Goro sabe bem o que vem a seguir.', kind = 'kill', monster = 'Serpente Branca', count = 1, storage = 50030, reward = {xp = 0, ryo = 0, items = {{id = 6288, count = 1}}}},
	{id = 'exam_chunin_3a_rival_pedra', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin \x97 Torneio (1/3)', text = 'Etapa 3: o torneio. Seu primeiro oponente veio da Vila da Pedra.', kind = 'kill', monster = 'Rival do Exame \x97 Pedra', count = 1, storage = 50031, reward = {xp = 300, ryo = 50, items = {}}},
	{id = 'exam_chunin_3b_rival_som', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin \x97 Torneio (2/3)', text = 'Seu segundo oponente veio da Vila do Som.', kind = 'kill', monster = 'Rival do Exame \x97 Som', count = 1, storage = 50032, reward = {xp = 300, ryo = 50, items = {}}},
	{id = 'exam_chunin_3c_rival_mist', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin \x97 Torneio (3/3)', text = 'Seu \xFAltimo oponente veio da Vila da N\xE9voa. Ven\xE7a e voc\xEA ser\xE1 Chunin.', kind = 'kill', monster = 'Rival do Exame \x97 N\xE9voa', count = 1, storage = 50033, reward = {xp = 5000, ryo = 2000, items = {{id = 2464, count = 1}}}, grantsRank = 'chunin', doneText = 'Chunin. Agora sim pode seguir \x97 a Costa das Mar\xE9s precisa de gente como voc\xEA, se ainda n\xE3o foi at\xE9 l\xE1, e as Ru\xEDnas do Cl\xE3 Marionetista n\xE3o v\xE3o esperar. S\xF3 quero ver com meus pr\xF3prios olhos que voc\xEA ainda aguenta a Floresta da Morte sem escolta: mate mais 1 ninja renegado antes de ir.'},
	{id = 'q_mountain_eagles', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'C\xE9u limpo', text = 'Chegou at\xE9 aqui como Jonin? Bem-vindo \xE0 Montanha do Trov\xE3o. Isso aqui n\xE3o \xE9 como a floresta l\xE1 embaixo: no topo do pico vive uma dupla amaldi\xE7oada por um pacto antigo de guerra, e as \xE1guias do trov\xE3o s\xE3o s\xF3 o primeiro aviso de quem n\xE3o deveria subir. Abata 15, se quiser provar que aguenta a trilha.', kind = 'kill', monster = '\xC1guia do Trov\xE3o', count = 15, storage = 50034, reward = {xp = 20000, ryo = 6000, items = {{id = 7591, count = 1}}}},
	{id = 'q_mountain_relics', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'Penas de valor', text = 'Mestra Yuki comercia penas de \xE1guia do trov\xE3o com ferreiros da vila. Traga 8.', kind = 'collect_item', monster = '', count = 0, storage = 50035, reward = {xp = 18000, ryo = 5000, items = {{id = 3965, count = 1}}}, collectItems = {{id = 5891, count = 8, name = 'Pena do Trov\xE3o', itemKey = 'thunder_feather'}}},
	{id = 'q_mountain_oni', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'O que desce do gelo', text = 'Onis da geleira invadiram o acampamento. Mate 10.', kind = 'kill', monster = 'Oni da Geleira', count = 10, storage = 50036, reward = {xp = 32000, ryo = 10000, items = {{id = 2646, count = 1}}}},
	{id = 'q_mountain_serpents', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'As fendas quentes', text = 'As serpentes de magma est\xE3o abrindo o pico por dentro. Mate 10.', kind = 'kill', monster = 'Serpente de Magma', count = 10, storage = 50037, reward = {xp = 48000, ryo = 16000, items = {{id = 6119, count = 1}}}},
	{id = 'q_mountain_lore', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'O pacto que n\xE3o morre', text = 'Mestra Yuki quer garantir que voc\xEA entende o que vai enfrentar no topo da montanha antes de deix\xE1-lo subir. Voc\xEAs v\xE3o enfrentar uma dupla que a Nuvem Vermelha j\xE1 usou contra vilas inteiras, h\xE1 uma gera\xE7\xE3o, ainda na Grande Guerra. Prove que prestou aten\xE7\xE3o.', kind = 'keyword_quiz', monster = '', count = 2, storage = 50038, reward = {xp = 40000, ryo = 12000, items = {{id = 2161, count = 1}}}, quiz = {{question = 'O que acontece quando um dos dois seres do topo morre sozinho?', keywords = {'absorve', 'absorver', 'furia', 'f\xFAria'}}, {question = 'Quem cobra um pre\xE7o por cada vida que consome?', keywords = {'s\xF3cio eterno', 'socio eterno', 'boss_curse_partner'}}, {question = 'Quem lan\xE7ou essa dupla imortal contra vilas inteiras na guerra?', keywords = {'nuvem vermelha', 'organizacao', 'organiza\xE7\xE3o'}}}, quizMin = 2},
	{id = 'q_mountain_curse_partner', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'O S\xF3cio Eterno', text = 'Uma dupla amaldi\xE7oada divide esta montanha. A metade que ainda parece gente n\xE3o sabe morrer \x97 mas sabe sangrar. Enfrente O S\xF3cio Eterno.', kind = 'kill', monster = 'O S\xF3cio Eterno', count = 1, storage = 50039, reward = {xp = 65000, ryo = 22000, items = {{id = 5952, count = 1}}}, grantsRankProgress = 'anbu', doneText = 'Um cora\xE7\xE3o j\xE1 parou. O outro vai acordar mais furioso do que nunca \x97 n\xE3o v\xE1 sozinho contra o Oni Ancestral.'},
	{id = 'q_mountain_boss', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'A raiva antiga', text = 'Dentro do pico dorme o Oni Ancestral, a outra metade da dupla amaldi\xE7oada. Ele n\xE3o vai dormir para sempre.', kind = 'kill', monster = 'Oni Ancestral', count = 1, storage = 50040, reward = {xp = 90000, ryo = 30000, items = {{id = 2169, count = 1}}}, grantsRankProgress = 'anbu', doneText = 'Isso \xE9 s\xF3 metade do que te espera no Covil da Nuvem Vermelha \x97 e agora voc\xEAs j\xE1 sabem o nome de quem enfrentam.'},
	{id = 'q_ruins_intro', npc = 'quest_giver_ruins', npcName = 'Anci\xE3o Kaito', name = 'Primeiras pe\xE7as', text = 'Chunin, bem-vindo \xE0s Ru\xEDnas. Este templo servia \xE0 Vila da Areia at\xE9 o cl\xE3 que aqui vivia virar os pr\xF3prios bonecos que empunhava \x97 e ningu\xE9m sabe dizer se a alma deles ainda comanda a madeira ou se \xE9 o contr\xE1rio. Comece trazendo 8 juntas de marionete: preciso entender como ainda se movem.', kind = 'collect_item', monster = '', count = 0, storage = 50041, reward = {xp = 4500, ryo = 1000, items = {{id = 7588, count = 1}}}, collectItems = {{id = 5901, count = 8, name = 'Junta de Marionete', itemKey = 'puppet_joint'}}},
	{id = 'q_ruins_puppets', npc = 'quest_giver_ruins', npcName = 'Anci\xE3o Kaito', name = 'Ordens antigas', text = 'As marionetes ainda seguem ordens de algu\xE9m \x97 patrulham o p\xE1tio como se o dono nunca tivesse morrido. Destrua 12 e ajude a descobrir quem ainda puxa os fios.', kind = 'kill', monster = 'Marionete de Combate', count = 12, storage = 50042, reward = {xp = 6000, ryo = 1500, items = {{id = 7588, count = 1}}}},
	{id = 'q_ruins_sentinels', npc = 'quest_giver_ruins', npcName = 'Anci\xE3o Kaito', name = 'Quebrando o port\xE3o', text = 'As sentinelas de pedra guardam o port\xE3o interno h\xE1 gera\xE7\xF5es, fi\xE9is a uma ordem que ningu\xE9m mais lembra quem deu. Derrube 10 e sigamos os rastros de quem ainda as comanda.', kind = 'kill', monster = 'Sentinela de Pedra', count = 10, storage = 50043, reward = {xp = 9000, ryo = 2400, items = {{id = 2645, count = 1}}}},
	{id = 'q_ruins_curse_lore', npc = 'quest_giver_ruins', npcName = 'Anci\xE3o Kaito', name = 'Os selos que n\xE3o se apagam', text = 'Antes de enfrentar os xam\xE3s, Anci\xE3o Kaito testa o que voc\xEA j\xE1 sabe sobre a maldi\xE7\xE3o do cl\xE3.', kind = 'keyword_quiz', monster = '', count = 2, storage = 50044, reward = {xp = 3000, ryo = 600, items = {{id = 2201, count = 1}}}, quiz = {{question = 'O que mant\xE9m os bonecos do cl\xE3 \'vivos\' at\xE9 hoje?', keywords = {'selo', 'selos', 'maldicao', 'maldi\xE7\xE3o'}}, {question = 'Quem mant\xE9m os selos de maldi\xE7\xE3o ativos h\xE1 gera\xE7\xF5es?', keywords = {'xama', 'xam\xE3', 'curse_shaman'}}, {question = 'Para onde o g\xEAnio desertor pretende fugir depois das Ru\xEDnas?', keywords = {'toca do som', 'som'}}}, quizMin = 2},
	{id = 'q_ruins_shamans', npc = 'quest_giver_ruins', npcName = 'Anci\xE3o Kaito', name = 'Selos que n\xE3o se apagam', text = 'Os xam\xE3s mant\xEAm os selos de maldi\xE7\xE3o ativos h\xE1 gera\xE7\xF5es \x97 silenci\xE1-los \xE9 o \xFAltimo passo antes de chegar ao g\xEAnio desertor. Silencie 8.', kind = 'kill', monster = 'Xam\xE3 da Maldi\xE7\xE3o', count = 8, storage = 50045, reward = {xp = 14000, ryo = 4000, items = {{id = 2131, count = 1}}}},
	{id = 'q_ruins_deserter', npc = 'quest_giver_ruins', npcName = 'Anci\xE3o Kaito', name = 'O g\xEAnio desertor', text = 'Um desertor de elite escondeu-se nas ru\xEDnas atr\xE1s de poder proibido, recrutando para a Toca do Som. Detenha-o antes que ele siga viagem.', kind = 'kill', monster = 'Desertor de Elite', count = 1, storage = 50046, reward = {xp = 22000, ryo = 8000, items = {{id = 2131, count = 1}}}},
	{id = 'q_ruins_boss', npc = 'quest_giver_ruins', npcName = 'Anci\xE3o Kaito', name = 'Quem puxa os fios', text = 'No sal\xE3o central, o Marionetista das Ru\xEDnas ainda d\xE1 as \xFAltimas ordens do cl\xE3 extinto \x97 e as marionetes obedecem como se ele nunca tivesse morrido. Acabe com ele antes que mais algu\xE9m desapare\xE7a sob a poeira deste templo.', kind = 'kill', monster = 'Marionetista das Ru\xEDnas', count = 1, storage = 50047, reward = {xp = 30000, ryo = 12000, items = {{id = 2164, count = 1}}}, grantsRankProgress = 'jonin', doneText = 'Metade do caminho. Se o Espadachim da N\xE9voa tamb\xE9m caiu, a Montanha do Trov\xE3o est\xE1 esperando por voc\xEA.'},
}
NarutoQuests.byNpc = {}
-- storage -> quest (\xEDndice reverso usado pela aba Miss\xF5es do menu Shinobi, opcode 210
-- get_progress, para listar os requisitos pendentes do pr\xF3ximo rank por nome/NPC).
NarutoQuests.byStorage = {}
-- NOVO (docs/sistemas/missoes.md): \xEDndice por id da quest \x97 usado por requires.quests (pr\xE9-
-- requisito cruzando NPCs) e por NarutoQuests.completeTalkTo (achar a quest pelo storage j\xE1
-- basta l\xE1, mas byId fica dispon\xEDvel pra qualquer outro script que precise).
NarutoQuests.byId = {}
for _, q in ipairs(NarutoQuests.list) do
	NarutoQuests.byNpc[q.npc] = NarutoQuests.byNpc[q.npc] or {}
	table.insert(NarutoQuests.byNpc[q.npc], q)
	NarutoQuests.byStorage[q.storage] = q
	NarutoQuests.byId[q.id] = q
end

--- NOVO (docs/sistemas/missoes.md): placeholders {count}/{needed}/{player} em text/
--- progress_text/done_text/locked_text. tpl nil (campo n\xE3o usado na quest) retorna nil \x97 quem
--- chama decide o texto padr\xE3o (fallback). Sem nenhum placeholder no texto, gsub n\xE3o altera nada
--- (no-op seguro para todo texto de quest j\xE1 existente, que nunca usa essas chaves).
local function renderTemplate(tpl, player, q, count)
	if not tpl then return nil end
	local out = tpl:gsub('{count}', tostring(count or 0)):gsub('{needed}', tostring(q.count or 0))
	if player then out = out:gsub('{player}', player:getName()) end
	return out
end

--- NOVO: requires.level/rank/quests (docs/sistemas/missoes.md). Sem 'requires' (todas as quests
--- de hoje), retorna sempre true \x97 zero mudan\xE7a de comportamento pras quests existentes.
local function requirementsMet(player, q)
	local req = q.requires
	if not req then return true end
	if req.level and player:getLevel() < req.level then return false end
	if req.rank and NarutoRanks then
		local cur = NarutoRanks.get(player)
		local needed = NarutoRanks.byRank[req.rank]
		if needed and cur.index < needed.index then return false end
	end
	if req.quests then
		for _, qid in ipairs(req.quests) do
			local rq = NarutoQuests.byId[qid]
			if rq and player:getStorageValue(rq.storage) ~= NarutoQuests.DONE then return false end
		end
	end
	return true
end

--- NOVO: fala padr\xE3o pt-BR quando 'requires' n\xE3o foi satisfeito e a quest n\xE3o definiu
--- locked_text \x97 lista o que falta (n\xEDvel/rank/miss\xF5es anteriores) de forma gen\xE9rica.
local function defaultLockedText(q)
	local req = q.requires or {}
	local parts = {}
	if req.level then parts[#parts + 1] = "level " .. req.level end
	if req.rank and NarutoRanks and NarutoRanks.byRank[req.rank] then
		parts[#parts + 1] = "rank " .. NarutoRanks.byRank[req.rank].title
	end
	if req.quests and #req.quests > 0 then
		parts[#parts + 1] = #req.quests .. " miss\xE3o(\xF5es) anterior(es)"
	end
	local falta = #parts > 0 and table.concat(parts, ", ") or "cumprir os requisitos"
	return "Volte quando estiver pronto: falta " .. falta .. "."
end

--- Checa progress\xE3o de rank (grants_rank/grants_rank_progress) depois de marcar uma quest
--- DONE. Retorna a mensagem extra de promo\xE7\xE3o, ou nil.
local function grantQuestRankIfReady(player, q)
	local rank = q.grantsRank or q.grantsRankProgress
	if not rank or not NarutoRanks then return nil end
	local group = NarutoQuests.rankGroups[rank]
	if not group then return nil end
	for _, storage in ipairs(group) do
		if player:getStorageValue(storage) ~= NarutoQuests.DONE then return nil end
	end
	if NarutoRanks.promote(player, rank) then
		return "Voc\xEA agora \xE9 " .. NarutoRanks.byRank[rank].title .. "!"
	end
	return nil
end

--- Marca a quest DONE, aplica a recompensa (xp/ryo/items + NOVO storage/outfit/addon, ver
--- reward.storage/outfit/addon do schema) e checa rank. Usada por TODAS as formas de conclus\xE3o
--- (kill, keyword_quiz, collect_item, reach, talk_to) para n\xE3o duplicar a l\xF3gica de recompensa.
local function completeQuest(player, q)
	player:setStorageValue(q.storage, NarutoQuests.DONE)
	local xp = q.reward.xp
	if xp > 0 then player:addExperience(xp, true) end
	if q.reward.ryo > 0 then player:addItem(NarutoQuests.RYO_ID, q.reward.ryo) end
	for _, it in ipairs(q.reward.items) do player:addItem(it.id, it.count) end
	-- NOVO: reward.storage (destrava di\xE1logo/gate) e reward.outfit/addon.
	if q.reward.storageKey then player:setStorageValue(q.reward.storageKey, q.reward.storageValue) end
	if q.reward.outfit then
		player:addOutfit(q.reward.outfit)
		if q.reward.addon and q.reward.addon > 0 then player:addOutfitAddon(q.reward.outfit, q.reward.addon) end
	end
	-- NOVO: done_text (fallback = mensagem padr\xE3o de sempre).
	local msg = renderTemplate(q.doneText, player, q) or ("Bom trabalho, ninja. Miss\xE3o '" .. q.name .. "' conclu\xEDda.")
	local rankMsg = grantQuestRankIfReady(player, q)
	if rankMsg then msg = msg .. " " .. rankMsg end
	-- conquista quest_chain_complete (docs/sistemas/progressao-servidor.md): s\xF3 quando TODAS as
	-- quests desse NPC (a cadeia inteira da regi\xE3o) j\xE1 estiverem DONE, n\xE3o s\xF3 esta.
	if NarutoAchievements then
		local allDone = true
		for _, qq in ipairs(NarutoQuests.byNpc[q.npc] or {}) do
			if player:getStorageValue(qq.storage) ~= NarutoQuests.DONE then allDone = false end
		end
		if allDone then NarutoAchievements.onQuestChainComplete(player, q.npc) end
	end
	return msg
end

--- NOVO: usada pelo NPC ALVO de objective.kind='talk_to' (bloco TALK_TO_QUESTS injetado em TODO
--- npc gerado, ver npc_files() em tools/export_tfs.py). Retorna a mensagem de conclus\xE3o, ou nil
--- se n\xE3o h\xE1 nada a fazer aqui (deixa a keyword cair pro pr\xF3ximo handler desse NPC \x97 ex.: o
--- 'missao' normal, se o NPC alvo tamb\xE9m for um NPC de quests).
function NarutoQuests.completeTalkTo(player, q)
	local st = player:getStorageValue(q.storage)
	if st == NarutoQuests.DONE or st < 0 then return nil end
	return completeQuest(player, q)
end

function NarutoQuests.talk(player, quests)
	for _, q in ipairs(quests) do
		local st = player:getStorageValue(q.storage)
		if st ~= NarutoQuests.DONE then
			-- NOVO: requires s\xF3 \xE9 checado ao ACEITAR (st < 0) \x97 sem 'requires' (compat: nenhuma
			-- quest de hoje usa o campo), requirementsMet sempre retorna true e este bloco nunca
			-- dispara.
			if st < 0 and not requirementsMet(player, q) then
				return renderTemplate(q.lockedText, player, q) or defaultLockedText(q), false
			end
			if q.kind == 'keyword_quiz' then
				if st < 0 then
					player:setStorageValue(q.storage, 0)
					return (renderTemplate(q.text, player, q) or q.text) .. " (Miss\xE3o aceita: " .. q.name .. "). Diga {prova} quando estiver pronto para responder.", false
				elseif st < q.count then
					return renderTemplate(q.progressText, player, q, st) or ("Prova ainda n\xE3o feita. Diga {prova} para come\xE7ar: " .. q.name .. "."), false
				else
					return completeQuest(player, q), true
				end
			elseif q.kind == 'collect_item' then
				if st < 0 then
					player:setStorageValue(q.storage, 0)
					return (renderTemplate(q.text, player, q) or q.text) .. " (Miss\xE3o aceita: " .. q.name .. ")", false
				end
				local missing = {}
				for _, it in ipairs(q.collectItems) do
					if player:getItemCount(it.id) < it.count then
						missing[#missing + 1] = it.count .. "x " .. it.name
					end
				end
				if #missing > 0 then
					return renderTemplate(q.progressText, player, q, #missing) or ("Ainda falta trazer: " .. table.concat(missing, ", ") .. "."), false
				end
				for _, it in ipairs(q.collectItems) do player:removeItem(it.id, it.count) end
				return completeQuest(player, q), true
			elseif st >= q.count then
				return completeQuest(player, q), true
			elseif st >= 0 then
				-- NOVO: progress_text (fallback por kind) \x97 reach/talk_to nunca tinham mensagem
				-- pr\xF3pria antes (n\xE3o existiam), kill/any_of mant\xE9m a mensagem padr\xE3o de sempre.
				if q.progressText then
					return renderTemplate(q.progressText, player, q, st), false
				elseif q.kind == 'reach' then
					return "Ainda n\xE3o chegou l\xE1. V\xE1 at\xE9 o local indicado.", false
				elseif q.kind == 'talk_to' then
					return "V\xE1 falar com " .. (q.targetNpcName or "a pessoa certa") .. ".", false
				else
					return "Ainda n\xE3o terminou? " .. q.name .. ": " .. st .. "/" .. q.count .. " " .. q.monster .. ".", false
				end
			else
				player:setStorageValue(q.storage, 0)
				return (renderTemplate(q.text, player, q) or q.text) .. " (Miss\xE3o aceita: " .. q.name .. ")", false
			end
		end
	end
	return "N\xE3o tenho mais nada para voc\xEA por enquanto.", false
end

--- NOVO (docs/sistemas/missoes.md, requisito 8): texto curto de progresso pro cliente (aba
--- Miss\xF5es, opcode 210 get_progress \x97 ver missionsProgressJson em scripts/naruto/
--- character_switch.lua) \x97 "3/5 itens", "Chegou!", etc. N\xE3o usado pelo di\xE1logo do NPC (que usa
--- NarutoQuests.talk/progress_text acima); \xE9 s\xF3 para a UI mostrar progresso sem precisar falar
--- com o NPC.
function NarutoQuests.progressText(player, q)
	local st = player:getStorageValue(q.storage)
	if st == NarutoQuests.DONE then return "Conclu\xEDda" end
	if st < 0 then return "Dispon\xEDvel" end
	if q.kind == 'collect_item' then
		-- soma por UNIDADE (n\xE3o por tipo de item) \x97 "3/5 itens" quando falta trazer 2 de 5
		-- unidades de um \xFAnico item, igual ao exemplo do requisito 8 da extens\xE3o de miss\xF5es.
		local have, needed = 0, 0
		for _, it in ipairs(q.collectItems) do
			needed = needed + it.count
			have = have + math.min(player:getItemCount(it.id), it.count)
		end
		return have .. "/" .. needed .. " itens"
	elseif q.kind == 'keyword_quiz' then
		return st .. "/" .. q.count .. " acertos"
	elseif q.kind == 'reach' then
		return (st >= q.count) and "Chegou! Fale com o NPC" or "A caminho"
	elseif q.kind == 'talk_to' then
		return "Fale com " .. (q.targetNpcName or "?")
	else
		return st .. "/" .. q.count .. (q.boss and " (chefe)" or "")
	end
end
