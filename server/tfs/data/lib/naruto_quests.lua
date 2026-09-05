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
	['anbu'] = {50003, 50004, 50039, 50040},
	['kage'] = {50006, 50007},
	['jonin'] = {50013, 50047},
	['chunin'] = {50033},
}
NarutoQuests.list = {
	{id = 'q_lair_intro', npc = 'quest_giver_akatsuki_lair', npcName = 'Capitã Anbu Suzu', name = 'Clones não sangram, mas caem', text = 'Antes de encarar os quatro guardiões, prove que aguenta os clones brancos que patrulham os corredores. Mate 10.', kind = 'kill', monster = 'Clone Branco', count = 10, storage = 50001, reward = {xp = 45000, ryo = 10000, items = {{id = 2490, count = 1}}}},
	{id = 'q_lair_guards', npc = 'quest_giver_akatsuki_lair', npcName = 'Capitã Anbu Suzu', name = 'A guarda da Aurora', text = 'Os ninjas elite da Aurora não deixam ninguém passar sem lutar. Mate 8.', kind = 'kill', monster = 'Ninja Elite da Aurora', count = 8, storage = 50002, reward = {xp = 55000, ryo = 13000, items = {{id = 2489, count = 1}}}},
	{id = 'q_lair_1_illusive_eye', npc = 'quest_giver_akatsuki_lair', npcName = 'Capitã Anbu Suzu', name = 'Exame Anbu (1/2) — O Vigia Ilusório', text = 'Ninguém que entra aqui como Chunin sai vivo. Prove que é Anbu: derrote O Vigia Ilusório.', kind = 'kill', monster = 'O Vigia Ilusório', count = 1, storage = 50003, reward = {xp = 60000, ryo = 15000, items = {{id = 7591, count = 1}}}, grantsRankProgress = 'anbu', doneText = 'Um olho fechado. Falta o segundo guardião — e ele já sabe que vocês estão vindo.'},
	{id = 'q_lair_2_masked_puppeteer', npc = 'quest_giver_akatsuki_lair', npcName = 'Capitã Anbu Suzu', name = 'Exame Anbu (2/2) — O Mascarado das Sombras', text = 'O segundo guardião puxa os fios de longe. Encontre-o e encerre isso.', kind = 'kill', monster = 'O Mascarado das Sombras', count = 1, storage = 50004, reward = {xp = 70000, ryo = 18000, items = {{id = 7591, count = 1}}}, grantsRank = 'anbu', doneText = 'Anbu de verdade, enfim. Mas os dois que faltam são os que fundaram tudo isso — não relaxem agora.'},
	{id = 'q_lair_lore_quiz', npc = 'quest_giver_akatsuki_lair', npcName = 'Capitã Anbu Suzu', name = 'O que ainda ecoa', text = 'Serpente Branca, Marionetista das Ruínas, Sócio Eterno e Oni Ancestral já caíram para vocês. Antes de abrir o corredor do Portador dos Seis Caminhos, provem que prestaram atenção em quem enfrentaram até aqui.', kind = 'keyword_quiz', monster = '', count = 2, storage = 50005, reward = {xp = 78000, ryo = 20000, items = {{id = 7591, count = 1}}}, quiz = {{question = 'A Serpente Branca de verdade nunca foi só uma cobra. O que ela era antes de abandonar a forma humana?', keywords = {'ninja', 'humano', 'renegado'}}, {question = 'O Marionetista das Ruínas quase não lutava com o próprio corpo. O que ele usava para lutar em seu lugar?', keywords = {'marionetes', 'marionete', 'bonecos', 'fios'}}, {question = 'Da dupla amaldiçoada da Montanha do Trovão, o que acontece quando um dos dois morre sozinho?', keywords = {'absorve', 'absorver', 'furia', 'fúria'}}}, quizMin = 2},
	{id = 'q_lair_3_rings_bearer', npc = 'quest_giver_akatsuki_lair', npcName = 'Capitã Anbu Suzu', name = 'Exame Kage (1/2) — O Portador dos Seis Caminhos', text = 'Só um Kage de verdade encara o próximo guardião e vive para contar. Derrote O Portador dos Seis Caminhos.', kind = 'kill', monster = 'O Portador dos Seis Caminhos', count = 1, storage = 50006, reward = {xp = 85000, ryo = 22000, items = {{id = 8472, count = 1}}}, grantsRankProgress = 'kage', doneText = 'Ele multiplicava a própria vontade em vários corpos e ainda assim caiu para um só. Falta o fundador de tudo isso.'},
	{id = 'q_lair_4_crimson_ancestor', npc = 'quest_giver_akatsuki_lair', npcName = 'Capitã Anbu Suzu', name = 'Exame Kage (2/2) — O Ancestral da Nuvem Vermelha', text = 'O fundador da organização te espera no salão final. Vença, e a vila vai te chamar de Kage.', kind = 'kill', monster = 'O Ancestral da Nuvem Vermelha', count = 1, storage = 50007, reward = {xp = 120000, ryo = 40000, items = {{id = 6938, count = 1}}}, grantsRank = 'kage', doneText = 'Você fez o que nenhum Kage sozinho tinha conseguido: derrubou os líderes da Nuvem Vermelha. A vila vai te chamar de Kage a partir de hoje — e vai ser verdade.'},
	{id = 'q_coastal_mercenaries', npc = 'quest_giver_coastal', npcName = 'Ancião Tazu', name = 'A ponte ameaçada', text = 'Mercenários contratados por uma guilda rival atacam quem trabalha na ponte. Afaste-os. Mate 8.', kind = 'kill', monster = 'Mercenário da Ponte', count = 8, storage = 50008, reward = {xp = 900, ryo = 250, items = {{id = 7618, count = 1}}}},
	{id = 'q_coastal_supplies', npc = 'quest_giver_coastal', npcName = 'Ancião Tazu', name = 'Abastecendo os pescadores', text = 'A vila de pescadores está sem suprimentos com a ponte bloqueada. Entregue 5 poções de vida pequenas ao Ancião Tazu.', kind = 'collect_item', monster = '', count = 0, storage = 50009, reward = {xp = 700, ryo = 200, items = {{id = 2210, count = 1}}}, collectItems = {{id = 7618, count = 5, name = 'Poção de Vida Pequena', itemKey = 'health_potion_small'}}},
	{id = 'q_coastal_scouts', npc = 'quest_giver_coastal', npcName = 'Ancião Tazu', name = 'Olhos na neblina', text = 'Batedores vigiam a estrada da costa — dizem que servem a um espadachim renegado escondido além da ponte. Afaste-os. Mate 8.', kind = 'kill', monster = 'Batedor da Névoa', count = 8, storage = 50010, reward = {xp = 1300, ryo = 350, items = {{id = 7378, count = 1}}}},
	{id = 'q_coastal_guardians', npc = 'quest_giver_coastal', npcName = 'Ancião Tazu', name = 'Quebrando a linha', text = 'Guardiões da neblina bloqueiam a entrada da vila. Derrube 8.', kind = 'kill', monster = 'Guardião da Neblina', count = 8, storage = 50011, reward = {xp = 1800, ryo = 500, items = {{id = 7588, count = 1}}}},
	{id = 'q_coastal_apprentice', npc = 'quest_giver_coastal', npcName = 'Ancião Tazu', name = 'O aprendiz mascarado', text = 'Antes de chegar ao Espadachim, alguém precisa afastar o aprendiz que protege os flancos dele. Mate 6.', kind = 'kill', monster = 'Aprendiz Mascarado', count = 6, storage = 50012, reward = {xp = 3200, ryo = 900, items = {{id = 9928, count = 1}}}},
	{id = 'q_coastal_swordsman', npc = 'quest_giver_coastal', npcName = 'Ancião Tazu', name = 'O Espadachim da Névoa', text = 'Um espadachim renegado e seu aprendiz mascarado vieram sabotar a ponte que salvaria esta vila. Derrote os dois.', kind = 'kill', monster = 'Espadachim da Névoa', count = 1, storage = 50013, reward = {xp = 12000, ryo = 4000, items = {{id = 2412, count = 1}}}, grantsRankProgress = 'jonin', doneText = 'Vocês salvaram esta ponte. Mas ouvi um batedor comentar, antes de cair, sobre uma floresta que mata os fracos rio acima — cuidado. Antes de ir, dê mais uma ronda: quero ter certeza que nenhum mercenário ficou pra trás.'},
	{id = 'q_wolves_1', npc = 'quest_giver_leaf', npcName = 'Capitã Rin', name = 'Lobos na trilha', text = 'Bem-vinda à Floresta da Vila, Genin. A Academia te ensinou o básico — hora de provar em campo. Os lobos andam atacando viajantes na trilha: mate 5.', kind = 'kill', monster = 'Lobo', count = 5, storage = 50014, reward = {xp = 120, ryo = 60, items = {{id = 7618, count = 1}}}},
	{id = 'q_forest_deer_1', npc = 'quest_giver_leaf', npcName = 'Capitã Rin', name = 'Um agrado para o posto avançado', text = 'Os cervos da floresta não fazem mal a ninguém, mas a carne deles rende um bom onigiri. Traga 3 para o posto avançado — não precisa caçar, eles nem revidam.', kind = 'collect_item', monster = '', count = 0, storage = 50015, reward = {xp = 150, ryo = 70, items = {{id = 7618, count = 1}}}, collectItems = {{id = 2666, count = 3, name = 'Onigiri', itemKey = 'onigiri'}}},
	{id = 'q_forest_snakes', npc = 'quest_giver_leaf', npcName = 'Capitã Rin', name = 'Presas na relva', text = 'As cobras da floresta andam mordendo quem passa perto do riacho. Mate 8.', kind = 'kill', monster = 'Cobra da Floresta', count = 8, storage = 50016, reward = {xp = 260, ryo = 90, items = {{id = 2126, count = 1}}}},
	{id = 'q_bandits_1', npc = 'quest_giver_leaf', npcName = 'Capitã Rin', name = 'Limpando a estrada', text = 'Bandidos na estrada leste. Mate 10.', kind = 'kill', monster = 'Bandido', count = 10, storage = 50017, reward = {xp = 400, ryo = 200, items = {{id = 1949, count = 1}}}},
	{id = 'q_bandit_archers', npc = 'quest_giver_leaf', npcName = 'Capitã Rin', name = 'Flechas na copa das árvores', text = 'Bandidos arqueiros se escondem nas árvores para emboscar viajantes. Mate 8.', kind = 'kill', monster = 'Bandido Arqueiro', count = 8, storage = 50018, reward = {xp = 500, ryo = 220, items = {{id = 7378, count = 1}}}},
	{id = 'q_forest_supplies', npc = 'quest_giver_leaf', npcName = 'Capitã Rin', name = 'Abastecendo a vila', text = 'Antes de ir atrás do Chefe, a vila precisa de suprimentos: entregue 5 peles de lobo à Capitã Rin.', kind = 'collect_item', monster = '', count = 0, storage = 50019, reward = {xp = 350, ryo = 150, items = {{id = 7618, count = 1}}}, collectItems = {{id = 5897, count = 5, name = 'Pele de Lobo', itemKey = 'wolf_pelt'}}},
	{id = 'q_bandit_chief', npc = 'quest_giver_leaf', npcName = 'Capitã Rin', name = 'O Chefe', text = 'Acabe com o Chefe dos Bandidos no sudeste da floresta.', kind = 'kill', monster = 'Chefe dos Bandidos', count = 1, storage = 50020, reward = {xp = 1500, ryo = 800, items = {{id = 1988, count = 1}}}, doneText = 'Bom trabalho, Genin. Mas isso foi só a estrada perto de casa — a Floresta da Morte separa quem está pronto do resto do mundo, e ouvi dizer que mercadores da Costa das Marés estão contratando gente como você. Só uma última coisa: garanta que não sobrou nenhum bandido rondando a trilha.'},
	{id = 'q_leeches', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'Sangue ruim', text = 'Sanguessugas infestam a margem. Mate 8.', kind = 'kill', monster = 'Sanguessuga Gigante', count = 8, storage = 50021, reward = {xp = 900, ryo = 300, items = {{id = 8473, count = 1}, {id = 8473, count = 1}}}},
	{id = 'q_lesser_serpents', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'Ninhada de serpentes', text = 'Serpentes menores se multiplicaram perto do santuário abandonado. Mate 10.', kind = 'kill', monster = 'Serpente Menor', count = 10, storage = 50022, reward = {xp = 1400, ryo = 400, items = {{id = 5917, count = 1}}}},
	{id = 'q_forest_death_collect', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'Peles curtidas', text = 'Rastreador Goro precisa de peles de sapo curtidas para reforçar equipamentos. Traga 6.', kind = 'collect_item', monster = '', count = 0, storage = 50023, reward = {xp = 1200, ryo = 350, items = {{id = 7589, count = 1}}}, collectItems = {{id = 5880, count = 6, name = 'Pele de Sapo', itemKey = 'toad_skin'}}},
	{id = 'q_toads', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'Coaxar da morte', text = 'Mate 10 sapos gigantes.', kind = 'kill', monster = 'Sapo Gigante', count = 10, storage = 50024, reward = {xp = 2000, ryo = 600, items = {{id = 2463, count = 1}}}},
	{id = 'q_elder_toad_hunt', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'O sapo que não deveria existir', text = 'Antes do Exame, prove que sobrevive ao Sapo Ancião sozinho — sem pergaminho em jogo, só glória. Guarde essa vitória na memória: a Instrutora Ibuki vai cobrar a mesma prova, oficialmente, quando você for atrás do Pergaminho do Céu.', kind = 'kill', monster = 'Sapo Ancião', count = 1, storage = 50025, reward = {xp = 4000, ryo = 1500, items = {{id = 2642, count = 1}}}},
	{id = 'q_rogues', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'Desertores', text = 'Traga a cabeça de 8 ninjas renegados.', kind = 'kill', monster = 'Ninja Renegado', count = 8, storage = 50026, reward = {xp = 3500, ryo = 1200, items = {{id = 1948, count = 1}}}},
	{id = 'q_white_serpent', npc = 'quest_giver_swamp', npcName = 'Rastreador Goro', name = 'A Serpente Branca', text = 'Um renegado de pele pálida montou covil no fim da Floresta da Morte. Ele não é humano faz tempo. Mate a Serpente Branca — e não estranhe se a Instrutora Ibuki pedir o mesmo depois, para valer, na hora do Pergaminho da Terra.', kind = 'kill', monster = 'Serpente Branca', count = 1, storage = 50027, reward = {xp = 9000, ryo = 3500, items = {{id = 1956, count = 1}}}},
	{id = 'exam_chunin_1_teoria', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin — Prova Teórica', text = 'Antes de qualquer coisa, prove que prestou atenção no que a vila te ensinou. Responda o que eu perguntar e traga prova de que ainda sabe se virar sozinho na floresta.', kind = 'keyword_quiz', monster = '', count = 3, storage = 50028, reward = {xp = 500, ryo = 100, items = {}}, quiz = {{question = 'O que você gasta para lançar um jutsu?', keywords = {'chakra'}}, {question = 'Qual elemento é forte contra Doton?', keywords = {'fuuton', 'vento'}}, {question = 'Quem te ensinou seus primeiros jutsus?', keywords = {'sensei', 'mestre', 'hayato'}}, {question = 'Qual skill sobe quando você lança jutsu?', keywords = {'ninjutsu'}}, {question = 'Quem lidera a vila?', keywords = {'hokage'}}}, quizMin = 3},
	{id = 'exam_chunin_2a_pergaminho_ceu', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin — Pergaminho do Céu', text = 'Etapa 2: sobrevivência na Floresta da Morte. O Sapo Ancião guarda um Pergaminho do Céu. Traga-o. Se já provou pro Rastreador Goro que aguenta essa luta sozinho, já sabe o que esperar — dessa vez tem pergaminho de verdade em jogo.', kind = 'kill', monster = 'Sapo Ancião', count = 1, storage = 50029, reward = {xp = 0, ryo = 0, items = {{id = 6287, count = 1}}}},
	{id = 'exam_chunin_2b_pergaminho_terra', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin — Pergaminho da Terra', text = 'Agora o Pergaminho da Terra. A Serpente Branca guarda o dela no fim da floresta — só entre se estiver pronto. Quem já enfrentou essa serpente a pedido do Goro sabe bem o que vem a seguir.', kind = 'kill', monster = 'Serpente Branca', count = 1, storage = 50030, reward = {xp = 0, ryo = 0, items = {{id = 6288, count = 1}}}},
	{id = 'exam_chunin_3a_rival_pedra', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin — Torneio (1/3)', text = 'Etapa 3: o torneio. Seu primeiro oponente veio da Vila da Pedra.', kind = 'kill', monster = 'Rival do Exame — Pedra', count = 1, storage = 50031, reward = {xp = 300, ryo = 50, items = {}}},
	{id = 'exam_chunin_3b_rival_som', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin — Torneio (2/3)', text = 'Seu segundo oponente veio da Vila do Som.', kind = 'kill', monster = 'Rival do Exame — Som', count = 1, storage = 50032, reward = {xp = 300, ryo = 50, items = {}}},
	{id = 'exam_chunin_3c_rival_mist', npc = 'exam_proctor_forest', npcName = 'Instrutora Ibuki', name = 'Exame Chunin — Torneio (3/3)', text = 'Seu último oponente veio da Vila da Névoa. Vença e você será Chunin.', kind = 'kill', monster = 'Rival do Exame — Névoa', count = 1, storage = 50033, reward = {xp = 5000, ryo = 2000, items = {{id = 2464, count = 1}}}, grantsRank = 'chunin', doneText = 'Chunin. Agora sim pode seguir — a Costa das Marés precisa de gente como você, se ainda não foi até lá, e as Ruínas do Clã Marionetista não vão esperar. Só quero ver com meus próprios olhos que você ainda aguenta a Floresta da Morte sem escolta: mate mais 1 ninja renegado antes de ir.'},
	{id = 'q_mountain_eagles', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'Céu limpo', text = 'Chegou até aqui como Jonin? Bem-vindo à Montanha do Trovão. Isso aqui não é como a floresta lá embaixo: no topo do pico vive uma dupla amaldiçoada por um pacto antigo de guerra, e as águias do trovão são só o primeiro aviso de quem não deveria subir. Abata 15, se quiser provar que aguenta a trilha.', kind = 'kill', monster = 'Águia do Trovão', count = 15, storage = 50034, reward = {xp = 20000, ryo = 6000, items = {{id = 7591, count = 1}}}},
	{id = 'q_mountain_relics', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'Penas de valor', text = 'Mestra Yuki comercia penas de águia do trovão com ferreiros da vila. Traga 8.', kind = 'collect_item', monster = '', count = 0, storage = 50035, reward = {xp = 18000, ryo = 5000, items = {{id = 3965, count = 1}}}, collectItems = {{id = 5891, count = 8, name = 'Pena do Trovão', itemKey = 'thunder_feather'}}},
	{id = 'q_mountain_oni', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'O que desce do gelo', text = 'Onis da geleira invadiram o acampamento. Mate 10.', kind = 'kill', monster = 'Oni da Geleira', count = 10, storage = 50036, reward = {xp = 32000, ryo = 10000, items = {{id = 2646, count = 1}}}},
	{id = 'q_mountain_serpents', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'As fendas quentes', text = 'As serpentes de magma estão abrindo o pico por dentro. Mate 10.', kind = 'kill', monster = 'Serpente de Magma', count = 10, storage = 50037, reward = {xp = 48000, ryo = 16000, items = {{id = 6119, count = 1}}}},
	{id = 'q_mountain_lore', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'O pacto que não morre', text = 'Mestra Yuki quer garantir que você entende o que vai enfrentar no topo da montanha antes de deixá-lo subir. Vocês vão enfrentar uma dupla que a Nuvem Vermelha já usou contra vilas inteiras, há uma geração, ainda na Grande Guerra. Prove que prestou atenção.', kind = 'keyword_quiz', monster = '', count = 2, storage = 50038, reward = {xp = 40000, ryo = 12000, items = {{id = 2161, count = 1}}}, quiz = {{question = 'O que acontece quando um dos dois seres do topo morre sozinho?', keywords = {'absorve', 'absorver', 'furia', 'fúria'}}, {question = 'Quem cobra um preço por cada vida que consome?', keywords = {'sócio eterno', 'socio eterno', 'boss_curse_partner'}}, {question = 'Quem lançou essa dupla imortal contra vilas inteiras na guerra?', keywords = {'nuvem vermelha', 'organizacao', 'organização'}}}, quizMin = 2},
	{id = 'q_mountain_curse_partner', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'O Sócio Eterno', text = 'Uma dupla amaldiçoada divide esta montanha. A metade que ainda parece gente não sabe morrer — mas sabe sangrar. Enfrente O Sócio Eterno.', kind = 'kill', monster = 'O Sócio Eterno', count = 1, storage = 50039, reward = {xp = 65000, ryo = 22000, items = {{id = 5952, count = 1}}}, grantsRankProgress = 'anbu', doneText = 'Um coração já parou. O outro vai acordar mais furioso do que nunca — não vá sozinho contra o Oni Ancestral.'},
	{id = 'q_mountain_boss', npc = 'quest_giver_mountain', npcName = 'Mestra Yuki', name = 'A raiva antiga', text = 'Dentro do pico dorme o Oni Ancestral, a outra metade da dupla amaldiçoada. Ele não vai dormir para sempre.', kind = 'kill', monster = 'Oni Ancestral', count = 1, storage = 50040, reward = {xp = 90000, ryo = 30000, items = {{id = 2169, count = 1}}}, grantsRankProgress = 'anbu', doneText = 'Isso é só metade do que te espera no Covil da Nuvem Vermelha — e agora vocês já sabem o nome de quem enfrentam.'},
	{id = 'q_ruins_intro', npc = 'quest_giver_ruins', npcName = 'Ancião Kaito', name = 'Primeiras peças', text = 'Chunin, bem-vindo às Ruínas. Este templo servia à Vila da Areia até o clã que aqui vivia virar os próprios bonecos que empunhava — e ninguém sabe dizer se a alma deles ainda comanda a madeira ou se é o contrário. Comece trazendo 8 juntas de marionete: preciso entender como ainda se movem.', kind = 'collect_item', monster = '', count = 0, storage = 50041, reward = {xp = 4500, ryo = 1000, items = {{id = 7588, count = 1}}}, collectItems = {{id = 5901, count = 8, name = 'Junta de Marionete', itemKey = 'puppet_joint'}}},
	{id = 'q_ruins_puppets', npc = 'quest_giver_ruins', npcName = 'Ancião Kaito', name = 'Ordens antigas', text = 'As marionetes ainda seguem ordens de alguém — patrulham o pátio como se o dono nunca tivesse morrido. Destrua 12 e ajude a descobrir quem ainda puxa os fios.', kind = 'kill', monster = 'Marionete de Combate', count = 12, storage = 50042, reward = {xp = 6000, ryo = 1500, items = {{id = 7588, count = 1}}}},
	{id = 'q_ruins_sentinels', npc = 'quest_giver_ruins', npcName = 'Ancião Kaito', name = 'Quebrando o portão', text = 'As sentinelas de pedra guardam o portão interno há gerações, fiéis a uma ordem que ninguém mais lembra quem deu. Derrube 10 e sigamos os rastros de quem ainda as comanda.', kind = 'kill', monster = 'Sentinela de Pedra', count = 10, storage = 50043, reward = {xp = 9000, ryo = 2400, items = {{id = 2645, count = 1}}}},
	{id = 'q_ruins_curse_lore', npc = 'quest_giver_ruins', npcName = 'Ancião Kaito', name = 'Os selos que não se apagam', text = 'Antes de enfrentar os xamãs, Ancião Kaito testa o que você já sabe sobre a maldição do clã.', kind = 'keyword_quiz', monster = '', count = 2, storage = 50044, reward = {xp = 3000, ryo = 600, items = {{id = 2201, count = 1}}}, quiz = {{question = 'O que mantém os bonecos do clã \'vivos\' até hoje?', keywords = {'selo', 'selos', 'maldicao', 'maldição'}}, {question = 'Quem mantém os selos de maldição ativos há gerações?', keywords = {'xama', 'xamã', 'curse_shaman'}}, {question = 'Para onde o gênio desertor pretende fugir depois das Ruínas?', keywords = {'toca do som', 'som'}}}, quizMin = 2},
	{id = 'q_ruins_shamans', npc = 'quest_giver_ruins', npcName = 'Ancião Kaito', name = 'Selos que não se apagam', text = 'Os xamãs mantêm os selos de maldição ativos há gerações — silenciá-los é o último passo antes de chegar ao gênio desertor. Silencie 8.', kind = 'kill', monster = 'Xamã da Maldição', count = 8, storage = 50045, reward = {xp = 14000, ryo = 4000, items = {{id = 2131, count = 1}}}},
	{id = 'q_ruins_deserter', npc = 'quest_giver_ruins', npcName = 'Ancião Kaito', name = 'O gênio desertor', text = 'Um desertor de elite escondeu-se nas ruínas atrás de poder proibido, recrutando para a Toca do Som. Detenha-o antes que ele siga viagem.', kind = 'kill', monster = 'Desertor de Elite', count = 1, storage = 50046, reward = {xp = 22000, ryo = 8000, items = {{id = 2131, count = 1}}}},
	{id = 'q_ruins_boss', npc = 'quest_giver_ruins', npcName = 'Ancião Kaito', name = 'Quem puxa os fios', text = 'No salão central, o Marionetista das Ruínas ainda dá as últimas ordens do clã extinto — e as marionetes obedecem como se ele nunca tivesse morrido. Acabe com ele antes que mais alguém desapareça sob a poeira deste templo.', kind = 'kill', monster = 'Marionetista das Ruínas', count = 1, storage = 50047, reward = {xp = 30000, ryo = 12000, items = {{id = 2164, count = 1}}}, grantsRankProgress = 'jonin', doneText = 'Metade do caminho. Se o Espadachim da Névoa também caiu, a Montanha do Trovão está esperando por você.'},
}
NarutoQuests.byNpc = {}
-- storage -> quest (índice reverso usado pela aba Missões do menu Shinobi, opcode 210
-- get_progress, para listar os requisitos pendentes do próximo rank por nome/NPC).
NarutoQuests.byStorage = {}
-- NOVO (docs/sistemas/missoes.md): índice por id da quest — usado por requires.quests (pré-
-- requisito cruzando NPCs) e por NarutoQuests.completeTalkTo (achar a quest pelo storage já
-- basta lá, mas byId fica disponível pra qualquer outro script que precise).
NarutoQuests.byId = {}
for _, q in ipairs(NarutoQuests.list) do
	NarutoQuests.byNpc[q.npc] = NarutoQuests.byNpc[q.npc] or {}
	table.insert(NarutoQuests.byNpc[q.npc], q)
	NarutoQuests.byStorage[q.storage] = q
	NarutoQuests.byId[q.id] = q
end

--- NOVO (docs/sistemas/missoes.md): placeholders {count}/{needed}/{player} em text/
--- progress_text/done_text/locked_text. tpl nil (campo não usado na quest) retorna nil — quem
--- chama decide o texto padrão (fallback). Sem nenhum placeholder no texto, gsub não altera nada
--- (no-op seguro para todo texto de quest já existente, que nunca usa essas chaves).
local function renderTemplate(tpl, player, q, count)
	if not tpl then return nil end
	local out = tpl:gsub('{count}', tostring(count or 0)):gsub('{needed}', tostring(q.count or 0))
	if player then out = out:gsub('{player}', player:getName()) end
	return out
end

--- NOVO: requires.level/rank/quests (docs/sistemas/missoes.md). Sem 'requires' (todas as quests
--- de hoje), retorna sempre true — zero mudança de comportamento pras quests existentes.
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

--- NOVO: fala padrão pt-BR quando 'requires' não foi satisfeito e a quest não definiu
--- locked_text — lista o que falta (nível/rank/missões anteriores) de forma genérica.
local function defaultLockedText(q)
	local req = q.requires or {}
	local parts = {}
	if req.level then parts[#parts + 1] = "level " .. req.level end
	if req.rank and NarutoRanks and NarutoRanks.byRank[req.rank] then
		parts[#parts + 1] = "rank " .. NarutoRanks.byRank[req.rank].title
	end
	if req.quests and #req.quests > 0 then
		parts[#parts + 1] = #req.quests .. " missão(ões) anterior(es)"
	end
	local falta = #parts > 0 and table.concat(parts, ", ") or "cumprir os requisitos"
	return "Volte quando estiver pronto: falta " .. falta .. "."
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

--- Marca a quest DONE, aplica a recompensa (xp/ryo/items + NOVO storage/outfit/addon, ver
--- reward.storage/outfit/addon do schema) e checa rank. Usada por TODAS as formas de conclusão
--- (kill, keyword_quiz, collect_item, reach, talk_to) para não duplicar a lógica de recompensa.
local function completeQuest(player, q)
	player:setStorageValue(q.storage, NarutoQuests.DONE)
	local xp = q.reward.xp
	if xp > 0 then player:addExperience(xp, true) end
	if q.reward.ryo > 0 then player:addItem(NarutoQuests.RYO_ID, q.reward.ryo) end
	for _, it in ipairs(q.reward.items) do player:addItem(it.id, it.count) end
	-- NOVO: reward.storage (destrava diálogo/gate) e reward.outfit/addon.
	if q.reward.storageKey then player:setStorageValue(q.reward.storageKey, q.reward.storageValue) end
	if q.reward.outfit then
		player:addOutfit(q.reward.outfit)
		if q.reward.addon and q.reward.addon > 0 then player:addOutfitAddon(q.reward.outfit, q.reward.addon) end
	end
	-- NOVO: done_text (fallback = mensagem padrão de sempre).
	local msg = renderTemplate(q.doneText, player, q) or ("Bom trabalho, ninja. Missão '" .. q.name .. "' concluída.")
	local rankMsg = grantQuestRankIfReady(player, q)
	if rankMsg then msg = msg .. " " .. rankMsg end
	-- conquista quest_chain_complete (docs/sistemas/progressao-servidor.md): só quando TODAS as
	-- quests desse NPC (a cadeia inteira da região) já estiverem DONE, não só esta.
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
--- npc gerado, ver npc_files() em tools/export_tfs.py). Retorna a mensagem de conclusão, ou nil
--- se não há nada a fazer aqui (deixa a keyword cair pro próximo handler desse NPC — ex.: o
--- 'missao' normal, se o NPC alvo também for um NPC de quests).
function NarutoQuests.completeTalkTo(player, q)
	local st = player:getStorageValue(q.storage)
	if st == NarutoQuests.DONE or st < 0 then return nil end
	return completeQuest(player, q)
end

function NarutoQuests.talk(player, quests)
	for _, q in ipairs(quests) do
		local st = player:getStorageValue(q.storage)
		if st ~= NarutoQuests.DONE then
			-- NOVO: requires só é checado ao ACEITAR (st < 0) — sem 'requires' (compat: nenhuma
			-- quest de hoje usa o campo), requirementsMet sempre retorna true e este bloco nunca
			-- dispara.
			if st < 0 and not requirementsMet(player, q) then
				return renderTemplate(q.lockedText, player, q) or defaultLockedText(q), false
			end
			if q.kind == 'keyword_quiz' then
				if st < 0 then
					player:setStorageValue(q.storage, 0)
					return (renderTemplate(q.text, player, q) or q.text) .. " (Missão aceita: " .. q.name .. "). Diga {prova} quando estiver pronto para responder.", false
				elseif st < q.count then
					return renderTemplate(q.progressText, player, q, st) or ("Prova ainda não feita. Diga {prova} para começar: " .. q.name .. "."), false
				else
					return completeQuest(player, q), true
				end
			elseif q.kind == 'collect_item' then
				if st < 0 then
					player:setStorageValue(q.storage, 0)
					return (renderTemplate(q.text, player, q) or q.text) .. " (Missão aceita: " .. q.name .. ")", false
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
				-- NOVO: progress_text (fallback por kind) — reach/talk_to nunca tinham mensagem
				-- própria antes (não existiam), kill/any_of mantém a mensagem padrão de sempre.
				if q.progressText then
					return renderTemplate(q.progressText, player, q, st), false
				elseif q.kind == 'reach' then
					return "Ainda não chegou lá. Vá até o local indicado.", false
				elseif q.kind == 'talk_to' then
					return "Vá falar com " .. (q.targetNpcName or "a pessoa certa") .. ".", false
				else
					return "Ainda não terminou? " .. q.name .. ": " .. st .. "/" .. q.count .. " " .. q.monster .. ".", false
				end
			else
				player:setStorageValue(q.storage, 0)
				return (renderTemplate(q.text, player, q) or q.text) .. " (Missão aceita: " .. q.name .. ")", false
			end
		end
	end
	return "Não tenho mais nada para você por enquanto.", false
end

--- NOVO (docs/sistemas/missoes.md, requisito 8): texto curto de progresso pro cliente (aba
--- Missões, opcode 210 get_progress — ver missionsProgressJson em scripts/naruto/
--- character_switch.lua) — "3/5 itens", "Chegou!", etc. Não usado pelo diálogo do NPC (que usa
--- NarutoQuests.talk/progress_text acima); é só para a UI mostrar progresso sem precisar falar
--- com o NPC.
function NarutoQuests.progressText(player, q)
	local st = player:getStorageValue(q.storage)
	if st == NarutoQuests.DONE then return "Concluída" end
	if st < 0 then return "Disponível" end
	if q.kind == 'collect_item' then
		-- soma por UNIDADE (não por tipo de item) — "3/5 itens" quando falta trazer 2 de 5
		-- unidades de um único item, igual ao exemplo do requisito 8 da extensão de missões.
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
