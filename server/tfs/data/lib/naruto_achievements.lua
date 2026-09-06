-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/lib/naruto_achievements.lua e adicione dofile em data/lib/lib.lua.
-- Conquistas (data/achievements.json, docs/sistemas/progressao-servidor.md, se\xE7\xE3o
-- "Conquistas"). Cada conquista tem UM storage de "desbloqueada" (NarutoAchievements.
-- UNLOCK_BASE + \xEDndice); os \xFAnicos contadores NOVOS s\xE3o TOTAL_KILLS/TOTAL_TASKS/TOTAL_DAILIES
-- (nada preexistente contava "mortes/tarefas/di\xE1rias de qualquer tipo, somadas" antes desta
-- miss\xE3o \x97 os storages de tasks/dailies s\xE3o por-tarefa/por-slot, n\xE3o um total).
NarutoAchievements = {}
NarutoAchievements.UNLOCK_BASE = 64000
NarutoAchievements.TOTAL_KILLS = 65000
NarutoAchievements.TOTAL_TASKS = 65001
NarutoAchievements.TOTAL_DAILIES = 65002
NarutoAchievements.LAST_UNLOCKED = 65003
NarutoAchievements.EFFECT_ID = 222

NarutoAchievements.list = {
	{idx = 1, id = 'explore_floresta_da_vila', name = 'Pisou em Floresta da Vila', description = 'Visite Floresta da Vila pela primeira vez.', category = 'exploration', kind = 'visit_zone', target = 'floresta_da_vila', count = 0, title = 'Viajante de Floresta da Vila', ryo = 100, storage = 64001},
	{idx = 2, id = 'explore_costa_das_mares', name = 'Pisou em Costa das Mar\xE9s', description = 'Visite Costa das Mar\xE9s pela primeira vez.', category = 'exploration', kind = 'visit_zone', target = 'costa_das_mares', count = 0, title = 'Viajante de Costa das Mar\xE9s', ryo = 100, storage = 64002},
	{idx = 3, id = 'explore_floresta_da_morte', name = 'Pisou em Floresta da Morte', description = 'Visite Floresta da Morte pela primeira vez.', category = 'exploration', kind = 'visit_zone', target = 'floresta_da_morte', count = 0, title = 'Viajante de Floresta da Morte', ryo = 100, storage = 64003},
	{idx = 4, id = 'explore_ruinas_do_cla_marionetista', name = 'Pisou em Ru\xEDnas do Cl\xE3 Marionetista', description = 'Visite Ru\xEDnas do Cl\xE3 Marionetista pela primeira vez.', category = 'exploration', kind = 'visit_zone', target = 'ruinas_do_cla_marionetista', count = 0, title = 'Viajante de Ru\xEDnas do Cl\xE3 Marionetista', ryo = 100, storage = 64004},
	{idx = 5, id = 'explore_montanha_do_trovao', name = 'Pisou em Montanha do Trov\xE3o', description = 'Visite Montanha do Trov\xE3o pela primeira vez.', category = 'exploration', kind = 'visit_zone', target = 'montanha_do_trovao', count = 0, title = 'Viajante de Montanha do Trov\xE3o', ryo = 100, storage = 64005},
	{idx = 6, id = 'explore_covil_nuvem_vermelha', name = 'Pisou em Covil da Nuvem Vermelha', description = 'Visite Covil da Nuvem Vermelha pela primeira vez.', category = 'exploration', kind = 'visit_zone', target = 'covil_nuvem_vermelha', count = 0, title = 'Viajante de Covil da Nuvem Vermelha', ryo = 100, storage = 64006},
	{idx = 7, id = 'exam_chunin', name = 'Aprovado no Exame Chunin', description = 'Complete todas as etapas do Exame Chunin.', category = 'exam', kind = 'grants_rank', target = 'chunin', count = 0, title = 'Chunin', ryo = 500, storage = 64007},
	{idx = 8, id = 'exam_jonin', name = 'Aprovado no Exame Jonin', description = 'Complete todas as etapas do Exame Jonin.', category = 'exam', kind = 'grants_rank', target = 'jonin', count = 0, title = 'Jonin', ryo = 2000, storage = 64008},
	{idx = 9, id = 'exam_anbu', name = 'Aprovado no Exame Anbu', description = 'Complete todas as etapas do Exame Anbu.', category = 'exam', kind = 'grants_rank', target = 'anbu', count = 0, title = 'Anbu', ryo = 8000, storage = 64009},
	{idx = 10, id = 'exam_kage', name = 'Aprovado no Exame Kage', description = 'Complete todas as etapas do Exame Kage.', category = 'exam', kind = 'grants_rank', target = 'kage', count = 0, title = 'Kage', ryo = 30000, storage = 64010},
	{idx = 11, id = 'chain_floresta_da_vila', name = 'Hist\xF3ria de Floresta da Vila', description = 'Complete toda a cadeia de miss\xF5es de Floresta da Vila (NPC quest_giver_leaf).', category = 'quest', kind = 'quest_chain_complete', target = 'quest_giver_leaf', count = 0, title = 'Her\xF3i de Floresta da Vila', ryo = 1500, storage = 64011},
	{idx = 12, id = 'chain_costa_das_mares', name = 'Hist\xF3ria de Costa das Mar\xE9s', description = 'Complete toda a cadeia de miss\xF5es de Costa das Mar\xE9s (NPC quest_giver_coastal).', category = 'quest', kind = 'quest_chain_complete', target = 'quest_giver_coastal', count = 0, title = 'Her\xF3i de Costa das Mar\xE9s', ryo = 1500, storage = 64012},
	{idx = 13, id = 'chain_floresta_da_morte', name = 'Hist\xF3ria de Floresta da Morte', description = 'Complete toda a cadeia de miss\xF5es de Floresta da Morte (NPC quest_giver_swamp).', category = 'quest', kind = 'quest_chain_complete', target = 'quest_giver_swamp', count = 0, title = 'Her\xF3i de Floresta da Morte', ryo = 1500, storage = 64013},
	{idx = 14, id = 'chain_ruinas_do_cla_marionetista', name = 'Hist\xF3ria de Ru\xEDnas do Cl\xE3 Marionetista', description = 'Complete toda a cadeia de miss\xF5es de Ru\xEDnas do Cl\xE3 Marionetista (NPC quest_giver_ruins).', category = 'quest', kind = 'quest_chain_complete', target = 'quest_giver_ruins', count = 0, title = 'Her\xF3i de Ru\xEDnas do Cl\xE3 Marionetista', ryo = 1500, storage = 64014},
	{idx = 15, id = 'chain_montanha_do_trovao', name = 'Hist\xF3ria de Montanha do Trov\xE3o', description = 'Complete toda a cadeia de miss\xF5es de Montanha do Trov\xE3o (NPC quest_giver_mountain).', category = 'quest', kind = 'quest_chain_complete', target = 'quest_giver_mountain', count = 0, title = 'Her\xF3i de Montanha do Trov\xE3o', ryo = 1500, storage = 64015},
	{idx = 16, id = 'chain_covil_nuvem_vermelha', name = 'Hist\xF3ria de Covil da Nuvem Vermelha', description = 'Complete toda a cadeia de miss\xF5es de Covil da Nuvem Vermelha (NPC quest_giver_akatsuki_lair).', category = 'quest', kind = 'quest_chain_complete', target = 'quest_giver_akatsuki_lair', count = 0, title = 'Her\xF3i de Covil da Nuvem Vermelha', ryo = 1500, storage = 64016},
	{idx = 17, id = 'boss_boss_bandit_chief', name = 'Vit\xF3ria sobre Chefe dos Bandidos', description = 'Derrote Chefe dos Bandidos pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_bandit_chief', count = 1, title = 'Algoz de Chefe dos Bandidos', ryo = 200, storage = 64017, monsterName = 'Chefe dos Bandidos'},
	{idx = 18, id = 'boss_boss_mist_swordsman', name = 'Vit\xF3ria sobre Espadachim da N\xE9voa', description = 'Derrote Espadachim da N\xE9voa pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_mist_swordsman', count = 1, title = 'Algoz de Espadachim da N\xE9voa', ryo = 800, storage = 64018, monsterName = 'Espadachim da N\xE9voa'},
	{idx = 19, id = 'boss_boss_elder_toad', name = 'Vit\xF3ria sobre Sapo Anci\xE3o', description = 'Derrote Sapo Anci\xE3o pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_elder_toad', count = 1, title = 'Algoz de Sapo Anci\xE3o', ryo = 1200, storage = 64019, monsterName = 'Sapo Anci\xE3o'},
	{idx = 20, id = 'boss_boss_white_serpent', name = 'Vit\xF3ria sobre Serpente Branca', description = 'Derrote Serpente Branca pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_white_serpent', count = 1, title = 'Algoz de Serpente Branca', ryo = 1500, storage = 64020, monsterName = 'Serpente Branca'},
	{idx = 21, id = 'boss_elite_deserter', name = 'Vit\xF3ria sobre Desertor de Elite', description = 'Derrote Desertor de Elite pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'elite_deserter', count = 1, title = 'Algoz de Desertor de Elite', ryo = 2000, storage = 64021, monsterName = 'Desertor de Elite'},
	{idx = 22, id = 'boss_boss_puppeteer', name = 'Vit\xF3ria sobre Marionetista das Ru\xEDnas', description = 'Derrote Marionetista das Ru\xEDnas pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_puppeteer', count = 1, title = 'Algoz de Marionetista das Ru\xEDnas', ryo = 3000, storage = 64022, monsterName = 'Marionetista das Ru\xEDnas'},
	{idx = 23, id = 'boss_boss_curse_partner', name = 'Vit\xF3ria sobre O S\xF3cio Eterno', description = 'Derrote O S\xF3cio Eterno pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_curse_partner', count = 1, title = 'Algoz de O S\xF3cio Eterno', ryo = 6000, storage = 64023, monsterName = 'O S\xF3cio Eterno'},
	{idx = 24, id = 'boss_boss_ancestral_oni', name = 'Vit\xF3ria sobre Oni Ancestral', description = 'Derrote Oni Ancestral pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_ancestral_oni', count = 1, title = 'Algoz de Oni Ancestral', ryo = 12000, storage = 64024, monsterName = 'Oni Ancestral'},
	{idx = 25, id = 'boss_boss_illusive_eye', name = 'Vit\xF3ria sobre O Vigia Ilus\xF3rio', description = 'Derrote O Vigia Ilus\xF3rio pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_illusive_eye', count = 1, title = 'Algoz de O Vigia Ilus\xF3rio', ryo = 15000, storage = 64025, monsterName = 'O Vigia Ilus\xF3rio'},
	{idx = 26, id = 'boss_boss_masked_puppeteer', name = 'Vit\xF3ria sobre O Mascarado das Sombras', description = 'Derrote O Mascarado das Sombras pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_masked_puppeteer', count = 1, title = 'Algoz de O Mascarado das Sombras', ryo = 18000, storage = 64026, monsterName = 'O Mascarado das Sombras'},
	{idx = 27, id = 'boss_boss_rings_bearer', name = 'Vit\xF3ria sobre O Portador dos Seis Caminhos', description = 'Derrote O Portador dos Seis Caminhos pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_rings_bearer', count = 1, title = 'Algoz de O Portador dos Seis Caminhos', ryo = 22000, storage = 64027, monsterName = 'O Portador dos Seis Caminhos'},
	{idx = 28, id = 'boss_boss_crimson_ancestor', name = 'Vit\xF3ria sobre O Ancestral da Nuvem Vermelha', description = 'Derrote O Ancestral da Nuvem Vermelha pelo menos uma vez.', category = 'boss', kind = 'kill_specific', target = 'boss_crimson_ancestor', count = 1, title = 'Algoz de O Ancestral da Nuvem Vermelha', ryo = 40000, storage = 64028, monsterName = 'O Ancestral da Nuvem Vermelha'},
	{idx = 29, id = 'kills_total_100', name = '100 abates', description = 'Derrote 100 monstros no total, de qualquer tipo.', category = 'kill', kind = 'kill_count', target = 'any', count = 100, title = 'Ca\xE7ador (100)', ryo = 100, storage = 64029},
	{idx = 30, id = 'kills_total_500', name = '500 abates', description = 'Derrote 500 monstros no total, de qualquer tipo.', category = 'kill', kind = 'kill_count', target = 'any', count = 500, title = 'Ca\xE7ador (500)', ryo = 400, storage = 64030},
	{idx = 31, id = 'kills_total_1000', name = '1000 abates', description = 'Derrote 1000 monstros no total, de qualquer tipo.', category = 'kill', kind = 'kill_count', target = 'any', count = 1000, title = 'Ca\xE7ador (1000)', ryo = 900, storage = 64031},
	{idx = 32, id = 'kills_total_5000', name = '5000 abates', description = 'Derrote 5000 monstros no total, de qualquer tipo.', category = 'kill', kind = 'kill_count', target = 'any', count = 5000, title = 'Ca\xE7ador (5000)', ryo = 4000, storage = 64032},
	{idx = 33, id = 'kills_total_10000', name = '10000 abates', description = 'Derrote 10000 monstros no total, de qualquer tipo.', category = 'kill', kind = 'kill_count', target = 'any', count = 10000, title = 'Ca\xE7ador (10000)', ryo = 9000, storage = 64033},
	{idx = 34, id = 'level_25', name = 'N\xEDvel 25', description = 'Alcance o n\xEDvel 25.', category = 'level', kind = 'level_reached', target = '25', count = 25, title = 'N\xEDvel 25', ryo = 300, storage = 64034},
	{idx = 35, id = 'level_50', name = 'N\xEDvel 50', description = 'Alcance o n\xEDvel 50.', category = 'level', kind = 'level_reached', target = '50', count = 50, title = 'N\xEDvel 50', ryo = 1500, storage = 64035},
	{idx = 36, id = 'level_75', name = 'N\xEDvel 75', description = 'Alcance o n\xEDvel 75.', category = 'level', kind = 'level_reached', target = '75', count = 75, title = 'N\xEDvel 75', ryo = 6000, storage = 64036},
	{idx = 37, id = 'level_100', name = 'N\xEDvel 100', description = 'Alcance o n\xEDvel 100.', category = 'level', kind = 'level_reached', target = '100', count = 100, title = 'N\xEDvel 100', ryo = 25000, storage = 64037},
	{idx = 38, id = 'tasks_completed_10', name = '10 tarefas entregues', description = 'Entregue 10 tarefas no total (qualquer NPC \'tasks\').', category = 'task', kind = 'task_count', target = 'any', count = 10, title = 'Contratado (10)', ryo = 200, storage = 64038},
	{idx = 39, id = 'tasks_completed_50', name = '50 tarefas entregues', description = 'Entregue 50 tarefas no total (qualquer NPC \'tasks\').', category = 'task', kind = 'task_count', target = 'any', count = 50, title = 'Contratado (50)', ryo = 1000, storage = 64039},
	{idx = 40, id = 'tasks_completed_100', name = '100 tarefas entregues', description = 'Entregue 100 tarefas no total (qualquer NPC \'tasks\').', category = 'task', kind = 'task_count', target = 'any', count = 100, title = 'Contratado (100)', ryo = 2500, storage = 64040},
	{idx = 41, id = 'dailies_completed_7', name = '7 di\xE1rias completas', description = 'Complete 7 miss\xF5es di\xE1rias no total.', category = 'daily', kind = 'daily_streak', target = 'any', count = 7, title = 'Disciplinado (7)', ryo = 150, storage = 64041},
	{idx = 42, id = 'dailies_completed_30', name = '30 di\xE1rias completas', description = 'Complete 30 miss\xF5es di\xE1rias no total.', category = 'daily', kind = 'daily_streak', target = 'any', count = 30, title = 'Disciplinado (30)', ryo = 800, storage = 64042},
	{idx = 43, id = 'dailies_completed_100', name = '100 di\xE1rias completas', description = 'Complete 100 miss\xF5es di\xE1rias no total.', category = 'daily', kind = 'daily_streak', target = 'any', count = 100, title = 'Disciplinado (100)', ryo = 3000, storage = 64043},
	{idx = 44, id = 'gearset_l1', name = 'Conjunto completo: Kit de Genin', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 1 (Kit de Genin) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_1', count = 0, title = 'Kit de Genin', ryo = 20, storage = 64044, tier = 1},
	{idx = 45, id = 'gearset_l10', name = 'Conjunto completo: Traje do Batedor', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 10 (Traje do Batedor) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_10', count = 0, title = 'Traje do Batedor', ryo = 200, storage = 64045, tier = 10},
	{idx = 46, id = 'gearset_l20', name = 'Conjunto completo: Uniforme Chunin', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 20 (Uniforme Chunin) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_20', count = 0, title = 'Uniforme Chunin', ryo = 400, storage = 64046, tier = 20},
	{idx = 47, id = 'gearset_l30', name = 'Conjunto completo: Vestes do Cl\xE3 Marionetista', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 30 (Vestes do Cl\xE3 Marionetista) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_30', count = 0, title = 'Vestes do Cl\xE3 Marionetista', ryo = 600, storage = 64047, tier = 30},
	{idx = 48, id = 'gearset_l40', name = 'Conjunto completo: Traje do Rastreador Sombrio', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 40 (Traje do Rastreador Sombrio) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_40', count = 0, title = 'Traje do Rastreador Sombrio', ryo = 800, storage = 64048, tier = 40},
	{idx = 49, id = 'gearset_l50', name = 'Conjunto completo: Vestimenta de Jonin', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 50 (Vestimenta de Jonin) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_50', count = 0, title = 'Vestimenta de Jonin', ryo = 1000, storage = 64049, tier = 50},
	{idx = 50, id = 'gearset_l60', name = 'Conjunto completo: Armadura Stormcaller', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 60 (Armadura Stormcaller) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_60', count = 0, title = 'Armadura Stormcaller', ryo = 1200, storage = 64050, tier = 60},
	{idx = 51, id = 'gearset_l70', name = 'Conjunto completo: Armadura do Ca\xE7ador de Onis', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 70 (Armadura do Ca\xE7ador de Onis) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_70', count = 0, title = 'Armadura do Ca\xE7ador de Onis', ryo = 1400, storage = 64051, tier = 70},
	{idx = 52, id = 'gearset_l80', name = 'Conjunto completo: Manto Anbu Negro', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 80 (Manto Anbu Negro) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_80', count = 0, title = 'Manto Anbu Negro', ryo = 1600, storage = 64052, tier = 80},
	{idx = 53, id = 'gearset_l90', name = 'Conjunto completo: Vestes da Aurora Carmesim', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 90 (Vestes da Aurora Carmesim) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_90', count = 0, title = 'Vestes da Aurora Carmesim', ryo = 1800, storage = 64053, tier = 90},
	{idx = 54, id = 'gearset_l100', name = 'Conjunto completo: Vestes do Kage', description = 'Vista as 5 pe\xE7as de equipamento + arma do conjunto de n\xEDvel 100 (Vestes do Kage) ao mesmo tempo.', category = 'collection', kind = 'collect_set', target = 'tier_100', count = 0, title = 'Vestes do Kage', ryo = 2000, storage = 64054, tier = 100},
	{idx = 55, id = 'trophies_all', name = 'Ca\xE7ador Lend\xE1rio', description = 'Obtenha os 38 trof\xE9us de tarefa, um de cada monstro do jogo.', category = 'collection', kind = 'collect_item_count', target = 'trophy_*', count = 38, title = 'Ca\xE7ador Lend\xE1rio', ryo = 50000, storage = 64055, itemPrefix = 'trophy_'},
}
NarutoAchievements.byId = {}
NarutoAchievements.byKind = {}
for _, a in ipairs(NarutoAchievements.list) do
	NarutoAchievements.byId[a.id] = a
	NarutoAchievements.byKind[a.kind] = NarutoAchievements.byKind[a.kind] or {}
	table.insert(NarutoAchievements.byKind[a.kind], a)
end

NarutoAchievements.gearSets = {
	[1] = {head = {2480}, body = {2467}, legs = {2649}, feet = {2643}, accessory = {2126}, weapon = {2404, 7378}},
	[10] = {feet = {2195}, head = {7458}, legs = {9928}, weapon = {2399, 2172}, accessory = {2210}},
	[20] = {body = {2464}, head = {5917}, legs = {2648}, feet = {2642}, weapon = {2412}},
	[30] = {weapon = {2397, 2410}, head = {2457}, body = {2465}, legs = {2478}, feet = {2645}, accessory = {2131}},
	[40] = {head = {3967}, body = {8870}, legs = {15409}, feet = {11303}, weapon = {2402, 7366}, accessory = {2201}},
	[50] = {head = {2497}, body = {2476}, legs = {2647}, feet = {6132}, weapon = {2406, 3965}, accessory = {2166}},
	[60] = {weapon = {7367}, head = {2491}, body = {2492}, legs = {2477}, feet = {2646}, accessory = {2136}},
	[70] = {weapon = {2421, 7438}, head = {2496}, body = {2494}, legs = {7894}, feet = {7891}, accessory = {2161}},
	[80] = {head = {2490}, body = {2489}, legs = {11304}, feet = {11240}, weapon = {8849}, accessory = {2142}},
	[90] = {head = {2493}, body = {8868}, legs = {23539}, feet = {11118}, weapon = {8209, 8850}, accessory = {2204}},
	[100] = {head = {2498}, body = {2472}, legs = {10300}, feet = {11117}, weapon = {6528, 8851}, accessory = {2357}},
}
NarutoAchievements.SLOT_CONST = {head = CONST_SLOT_HEAD, body = CONST_SLOT_ARMOR, legs = CONST_SLOT_LEGS, feet = CONST_SLOT_FEET, accessory = CONST_SLOT_RING}

NarutoAchievements.itemPrefixIds = {
	['trophy_'] = {6435, 7394, 7395, 7396, 7397, 7398, 7399, 7401, 7936, 7964, 10130, 10131, 10132, 10142, 10455, 10529, 10542, 10543, 11161, 11315, 11336, 11338, 12635, 12650, 15415, 15416, 15417, 15418, 15419, 15420, 15619, 16004, 16005, 16006, 24757, 24758, 24759, 24760},
}

-- Zonas: aproxima\xE7\xE3o por ret\xE2ngulo de posi\xE7\xE3o (o TFS n\xE3o tem "zona" em runtime, s\xF3 os
-- ret\xE2ngulos que tools/map/build_valley.py (X0/Y0=1000/1000, DEATH_X0=1130) e
-- tools/map/build_regions.py (COAST_*/RUINS_*/MOUNT_*/LAIR_*) usaram para desenhar o mapa \x97
-- reaproveitados aqui verbatim). Boa o suficiente para "visitou pela 1a vez"; os 6 ret\xE2ngulos
-- n\xE3o se sobrep\xF5em.
NarutoAchievements.zoneBounds = {
	floresta_da_vila = {1000, 1000, 1129, 1119},
	floresta_da_morte = {1130, 1000, 1199, 1119},
	costa_das_mares = {1000, 1120, 1049, 1169},
	ruinas_do_cla_marionetista = {1200, 1000, 1249, 1049},
	montanha_do_trovao = {1200, 1060, 1249, 1109},
	covil_nuvem_vermelha = {1400, 1000, 1449, 1049},
}

-- Dentro da muralha da Vila da Folha (build_valley.py V_X0..V_Y1 = 1010,1030..1049,1069) NAO conta
-- como "pisou na Floresta da Vila" (playtest r4: a conquista destravava no login, na praca).
NarutoAchievements.zoneExclude = { {1010, 1030, 1049, 1069} }

function NarutoAchievements.zoneAt(pos)
	for _, e in ipairs(NarutoAchievements.zoneExclude) do
		if pos.x >= e[1] and pos.x <= e[3] and pos.y >= e[2] and pos.y <= e[4] then
			return nil
		end
	end
	for zone, b in pairs(NarutoAchievements.zoneBounds) do
		if pos.x >= b[1] and pos.x <= b[3] and pos.y >= b[2] and pos.y <= b[4] then
			return zone
		end
	end
	return nil
end

function NarutoAchievements.isUnlocked(player, a)
	return player:getStorageValue(a.storage) == 1
end

--- Concede a conquista `a`: marca o storage, manda mensagem de sistema + efeito visual + ryo.
--- Idempotente (retorna false sem fazer nada se j\xE1 estava desbloqueada).
function NarutoAchievements.grant(player, a)
	if NarutoAchievements.isUnlocked(player, a) then return false end
	player:setStorageValue(a.storage, 1)
	player:setStorageValue(NarutoAchievements.LAST_UNLOCKED, a.idx)
	player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Conquista desbloqueada: " .. a.name .. "!")
	player:getPosition():sendMagicEffect(NarutoAchievements.EFFECT_ID)
	if a.ryo and a.ryo > 0 and NarutoQuests then
		player:addItem(NarutoQuests.RYO_ID, a.ryo)
	end
	return true
end

--- true se o jogador tem TODOS os slots do tier vestidos ao mesmo tempo (arma aceita qualquer
--- id da lista \x97 ex. tier 1 aceita kunai OU shuriken de ferro).
function NarutoAchievements.hasGearSet(player, tier)
	local set = NarutoAchievements.gearSets[tier]
	if not set then return false end
	for slot, ids in pairs(set) do
		if slot == 'weapon' then
			local left = player:getSlotItem(CONST_SLOT_LEFT)
			local right = player:getSlotItem(CONST_SLOT_RIGHT)
			local leftId = left and left:getId() or 0
			local rightId = right and right:getId() or 0
			local ok = false
			for _, iid in ipairs(ids) do
				if leftId == iid or rightId == iid then ok = true end
			end
			if not ok then return false end
		else
			local slotConst = NarutoAchievements.SLOT_CONST[slot]
			local it = slotConst and player:getSlotItem(slotConst)
			local itemId = it and it:getId() or 0
			local ok = false
			for _, iid in ipairs(ids) do
				if itemId == iid then ok = true end
			end
			if not ok then return false end
		end
	end
	return true
end

function NarutoAchievements.prefixItemCount(player, prefix)
	local ids = NarutoAchievements.itemPrefixIds[prefix]
	if not ids then return 0 end
	local n = 0
	for _, iid in ipairs(ids) do
		if player:getItemCount(iid) > 0 then n = n + 1 end
	end
	return n
end

-- ------------------------------------------------------------------ hooks por tipo de evento
-- (chamados de dentro de scripts/naruto/achievements.lua e dos m\xF3dulos j\xE1 existentes \x97
-- naruto_ranks.lua/NarutoRanks.promote, naruto_quests.lua/completeQuest, e o "tasks"/deliverCallback
-- gerado por npc_files() \x97 NUNCA duplicando um contador que j\xE1 existe).

function NarutoAchievements.onKill(player, monsterName)
	local total = player:getStorageValue(NarutoAchievements.TOTAL_KILLS)
	if total < 0 then total = 0 end
	total = total + 1
	player:setStorageValue(NarutoAchievements.TOTAL_KILLS, total)
	for _, a in ipairs(NarutoAchievements.byKind['kill_count'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and total >= a.count then
			NarutoAchievements.grant(player, a)
		end
	end
	for _, a in ipairs(NarutoAchievements.byKind['kill_specific'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and a.monsterName == monsterName then
			NarutoAchievements.grant(player, a)
		end
	end
end

function NarutoAchievements.onTaskDelivered(player)
	local total = player:getStorageValue(NarutoAchievements.TOTAL_TASKS)
	if total < 0 then total = 0 end
	total = total + 1
	player:setStorageValue(NarutoAchievements.TOTAL_TASKS, total)
	for _, a in ipairs(NarutoAchievements.byKind['task_count'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and total >= a.count then
			NarutoAchievements.grant(player, a)
		end
	end
end

function NarutoAchievements.onDailyDelivered(player)
	local total = player:getStorageValue(NarutoAchievements.TOTAL_DAILIES)
	if total < 0 then total = 0 end
	total = total + 1
	player:setStorageValue(NarutoAchievements.TOTAL_DAILIES, total)
	for _, a in ipairs(NarutoAchievements.byKind['daily_streak'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and total >= a.count then
			NarutoAchievements.grant(player, a)
		end
	end
end

function NarutoAchievements.onRankPromoted(player, rankId)
	for _, a in ipairs(NarutoAchievements.byKind['grants_rank'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and a.target == rankId then
			NarutoAchievements.grant(player, a)
		end
	end
end

function NarutoAchievements.onQuestChainComplete(player, npcId)
	for _, a in ipairs(NarutoAchievements.byKind['quest_chain_complete'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and a.target == npcId then
			NarutoAchievements.grant(player, a)
		end
	end
end

function NarutoAchievements.onLevelReached(player, newLevel)
	for _, a in ipairs(NarutoAchievements.byKind['level_reached'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and newLevel >= a.count then
			NarutoAchievements.grant(player, a)
		end
	end
end

--- Checagens sem evento dedicado (posi\xE7\xE3o/equipamento/itens): chamada no login e por um
--- GlobalEvent peri\xF3dico (scripts/naruto/achievements.lua) \x97 o TFS 1.4.2 n\xE3o tem onEquip nem
--- "entrou na zona X" gen\xE9ricos sem editar item por item ou o mapa; poll \xE9 a solu\xE7\xE3o mais
--- simples que cobre os 55 sem tocar nesses dois (ver limita\xE7\xE3o no relat\xF3rio da miss\xE3o).
function NarutoAchievements.pollPlayer(player)
	local zone = NarutoAchievements.zoneAt(player:getPosition())
	if zone then
		for _, a in ipairs(NarutoAchievements.byKind['visit_zone'] or {}) do
			if not NarutoAchievements.isUnlocked(player, a) and a.target == zone then
				NarutoAchievements.grant(player, a)
			end
		end
	end
	for _, a in ipairs(NarutoAchievements.byKind['collect_set'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) and NarutoAchievements.hasGearSet(player, a.tier) then
			NarutoAchievements.grant(player, a)
		end
	end
	for _, a in ipairs(NarutoAchievements.byKind['collect_item_count'] or {}) do
		if not NarutoAchievements.isUnlocked(player, a) then
			local n = NarutoAchievements.prefixItemCount(player, a.itemPrefix)
			if n >= a.count then
				NarutoAchievements.grant(player, a)
			end
		end
	end
end

--- JSON para a aba Miss\xF5es (se\xE7\xE3o Conquistas, opcode 210 get_progress) \x97 ver
--- character_switch.lua/achievementsProgressJson. Cont\xE1veis ganham progress/count; as demais
--- (kill_specific/quest_chain_complete/grants_rank/visit_zone/collect_set) s\xF3 unlocked.
function NarutoAchievements.progressJson(player)
	local out = NarutoJson.array({})
	for _, a in ipairs(NarutoAchievements.list) do
		local entry = {
			id = a.id, name = a.name, description = a.description,
			category = a.category, title = a.title, unlocked = NarutoAchievements.isUnlocked(player, a),
		}
		if a.kind == 'kill_count' then
			entry.progress = math.min(math.max(player:getStorageValue(NarutoAchievements.TOTAL_KILLS), 0), a.count)
			entry.count = a.count
		elseif a.kind == 'task_count' then
			entry.progress = math.min(math.max(player:getStorageValue(NarutoAchievements.TOTAL_TASKS), 0), a.count)
			entry.count = a.count
		elseif a.kind == 'daily_streak' then
			entry.progress = math.min(math.max(player:getStorageValue(NarutoAchievements.TOTAL_DAILIES), 0), a.count)
			entry.count = a.count
		elseif a.kind == 'level_reached' then
			entry.progress = math.min(player:getLevel(), a.count)
			entry.count = a.count
		elseif a.kind == 'collect_item_count' then
			entry.progress = math.min(NarutoAchievements.prefixItemCount(player, a.itemPrefix), a.count)
			entry.count = a.count
		end
		out[#out + 1] = entry
	end
	return out
end
