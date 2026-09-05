-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/lib/naruto_dailies.lua e adicione dofile em data/lib/lib.lua.
-- Miss\xF5es di\xE1rias (data/dailies.json, docs/sistemas/progressao-servidor.md): a cada dia, 3
-- entradas s\xE3o sorteadas do pool cuja faixa [levelMin,levelMax] cont\xE9m o level do jogador (na
-- hora do sorteio). Simplifica\xE7\xE3o vs. o pedido original: as 3 di\xE1rias do dia j\xE1 ficam
-- AUTO-ACEITAS (contam kills desde o sorteio, sem passo extra de 'aceitar por n\xFAmero') \x97
-- '!diaria' mostra e '!diaria entregar' entrega; ver pend\xEAncias no relat\xF3rio da miss\xE3o.
-- SLOT_PROGRESS: -1 sem entrada nesse slot hoje, 0..count-1 em andamento, count = pronta,
-- count+1 = j\xE1 entregue hoje.
NarutoDailies = {}
NarutoDailies.DAY = 60020
NarutoDailies.SLOT_POOL = {60021, 60022, 60023}
NarutoDailies.SLOT_PROGRESS = {60024, 60025, 60026}
NarutoDailies.pool = {
	{id = 'daily_kill_wolf_001', name = 'Lobo (1-5)', text = 'Reduza a popula\xE7\xE3o de Lobo por perto \x97 mate 12.', monster = 'Lobo', count = 12, levelMin = 1, levelMax = 5, reward = {xp = 6.0, ryo = 21, items = {}}},
	{id = 'daily_kill_forest_deer_001b', name = 'Cervo \x97 segunda leva (1-5)', text = 'Mais uma leva: 12 de Cervo na mesma regi\xE3o.', monster = 'Cervo', count = 12, levelMin = 1, levelMax = 5, reward = {xp = 5.4, ryo = 8, items = {}}},
	{id = 'daily_hunt_wolf_001c', name = 'ca\xE7ada r\xE1pida de Lobo (1-5)', text = 'Uma leva mais curta e mais bem paga: 8 de Lobo, entregue direto no quadro.', monster = 'Lobo', count = 8, levelMin = 1, levelMax = 5, reward = {xp = 5.6, ryo = 22, items = {{id = 7618, count = 1}}}},
	{id = 'daily_kill_bandit_archer_006', name = 'Bandido Arqueiro (6-10)', text = 'Reduza a popula\xE7\xE3o de Bandido Arqueiro por perto \x97 mate 12.', monster = 'Bandido Arqueiro', count = 12, levelMin = 6, levelMax = 10, reward = {xp = 6.0, ryo = 84, items = {}}},
	{id = 'daily_kill_leech_006b', name = 'Sanguessuga Gigante \x97 segunda leva (6-10)', text = 'Mais uma leva: 12 de Sanguessuga Gigante na mesma regi\xE3o.', monster = 'Sanguessuga Gigante', count = 12, levelMin = 6, levelMax = 10, reward = {xp = 5.4, ryo = 106, items = {}}},
	{id = 'daily_hunt_bandit_archer_006c', name = 'ca\xE7ada r\xE1pida de Bandido Arqueiro (6-10)', text = 'Uma leva mais curta e mais bem paga: 8 de Bandido Arqueiro, entregue direto no quadro.', monster = 'Bandido Arqueiro', count = 8, levelMin = 6, levelMax = 10, reward = {xp = 5.6, ryo = 88, items = {{id = 7618, count = 1}}}},
	{id = 'daily_kill_giant_toad_011', name = 'Sapo Gigante (11-15)', text = 'Reduza a popula\xE7\xE3o de Sapo Gigante por perto \x97 mate 12.', monster = 'Sapo Gigante', count = 12, levelMin = 11, levelMax = 15, reward = {xp = 6.0, ryo = 178, items = {}}},
	{id = 'daily_kill_mercenary_bridge_011b', name = 'Mercen\xE1rio da Ponte \x97 segunda leva (11-15)', text = 'Mais uma leva: 12 de Mercen\xE1rio da Ponte na mesma regi\xE3o.', monster = 'Mercen\xE1rio da Ponte', count = 12, levelMin = 11, levelMax = 15, reward = {xp = 5.4, ryo = 63, items = {}}},
	{id = 'daily_hunt_giant_toad_011c', name = 'ca\xE7ada r\xE1pida de Sapo Gigante (11-15)', text = 'Uma leva mais curta e mais bem paga: 8 de Sapo Gigante, entregue direto no quadro.', monster = 'Sapo Gigante', count = 8, levelMin = 11, levelMax = 15, reward = {xp = 5.6, ryo = 187, items = {{id = 7618, count = 1}}}},
	{id = 'daily_kill_rogue_ninja_016', name = 'Ninja Renegado (16-20)', text = 'Reduza a popula\xE7\xE3o de Ninja Renegado por perto \x97 mate 12.', monster = 'Ninja Renegado', count = 12, levelMin = 16, levelMax = 20, reward = {xp = 6.0, ryo = 294, items = {}}},
	{id = 'daily_kill_lesser_serpent_016b', name = 'Serpente Menor \x97 segunda leva (16-20)', text = 'Mais uma leva: 12 de Serpente Menor na mesma regi\xE3o.', monster = 'Serpente Menor', count = 12, levelMin = 16, levelMax = 20, reward = {xp = 5.4, ryo = 259, items = {}}},
	{id = 'daily_hunt_rogue_ninja_016c', name = 'ca\xE7ada r\xE1pida de Ninja Renegado (16-20)', text = 'Uma leva mais curta e mais bem paga: 8 de Ninja Renegado, entregue direto no quadro.', monster = 'Ninja Renegado', count = 8, levelMin = 16, levelMax = 20, reward = {xp = 5.6, ryo = 308, items = {{id = 7588, count = 1}}}},
	{id = 'daily_kill_ruin_puppet_021', name = 'Marionete de Combate (21-25)', text = 'Reduza a popula\xE7\xE3o de Marionete de Combate por perto \x97 mate 8.', monster = 'Marionete de Combate', count = 8, levelMin = 21, levelMax = 25, reward = {xp = 4.0, ryo = 284, items = {}}},
	{id = 'daily_kill_rogue_ninja_021b', name = 'Ninja Renegado \x97 segunda leva (21-25)', text = 'Mais uma leva: 8 de Ninja Renegado na mesma regi\xE3o.', monster = 'Ninja Renegado', count = 8, levelMin = 21, levelMax = 25, reward = {xp = 3.6, ryo = 179, items = {}}},
	{id = 'daily_hunt_ruin_puppet_021c', name = 'ca\xE7ada r\xE1pida de Marionete de Combate (21-25)', text = 'Uma leva mais curta e mais bem paga: 4 de Marionete de Combate, entregue direto no quadro.', monster = 'Marionete de Combate', count = 4, levelMin = 21, levelMax = 25, reward = {xp = 2.8, ryo = 223, items = {{id = 7588, count = 1}}}},
	{id = 'daily_kill_ruin_puppet_026', name = 'Marionete de Combate (26-30)', text = 'Reduza a popula\xE7\xE3o de Marionete de Combate por perto \x97 mate 8.', monster = 'Marionete de Combate', count = 8, levelMin = 26, levelMax = 30, reward = {xp = 4.0, ryo = 284, items = {}}},
	{id = 'daily_kill_stone_sentinel_026b', name = 'Sentinela de Pedra \x97 segunda leva (26-30)', text = 'Mais uma leva: 8 de Sentinela de Pedra na mesma regi\xE3o.', monster = 'Sentinela de Pedra', count = 8, levelMin = 26, levelMax = 30, reward = {xp = 3.6, ryo = 307, items = {}}},
	{id = 'daily_hunt_ruin_puppet_026c', name = 'ca\xE7ada r\xE1pida de Marionete de Combate (26-30)', text = 'Uma leva mais curta e mais bem paga: 4 de Marionete de Combate, entregue direto no quadro.', monster = 'Marionete de Combate', count = 4, levelMin = 26, levelMax = 30, reward = {xp = 2.8, ryo = 223, items = {{id = 7588, count = 1}}}},
	{id = 'daily_kill_stone_sentinel_031', name = 'Sentinela de Pedra (31-35)', text = 'Reduza a popula\xE7\xE3o de Sentinela de Pedra por perto \x97 mate 8.', monster = 'Sentinela de Pedra', count = 8, levelMin = 31, levelMax = 35, reward = {xp = 4.0, ryo = 336, items = {}}},
	{id = 'daily_kill_spectral_warrior_031b', name = 'Guerreiro Espectral \x97 segunda leva (31-35)', text = 'Mais uma leva: 8 de Guerreiro Espectral na mesma regi\xE3o.', monster = 'Guerreiro Espectral', count = 8, levelMin = 31, levelMax = 35, reward = {xp = 3.6, ryo = 365, items = {}}},
	{id = 'daily_hunt_stone_sentinel_031c', name = 'ca\xE7ada r\xE1pida de Sentinela de Pedra (31-35)', text = 'Uma leva mais curta e mais bem paga: 4 de Sentinela de Pedra, entregue direto no quadro.', monster = 'Sentinela de Pedra', count = 4, levelMin = 31, levelMax = 35, reward = {xp = 2.8, ryo = 264, items = {{id = 7589, count = 1}}}},
	{id = 'daily_kill_spectral_warrior_036', name = 'Guerreiro Espectral (36-40)', text = 'Reduza a popula\xE7\xE3o de Guerreiro Espectral por perto \x97 mate 8.', monster = 'Guerreiro Espectral', count = 8, levelMin = 36, levelMax = 40, reward = {xp = 4.0, ryo = 399, items = {}}},
	{id = 'daily_kill_stone_sentinel_036b', name = 'Sentinela de Pedra \x97 segunda leva (36-40)', text = 'Mais uma leva: 8 de Sentinela de Pedra na mesma regi\xE3o.', monster = 'Sentinela de Pedra', count = 8, levelMin = 36, levelMax = 40, reward = {xp = 3.6, ryo = 307, items = {}}},
	{id = 'daily_hunt_spectral_warrior_036c', name = 'ca\xE7ada r\xE1pida de Guerreiro Espectral (36-40)', text = 'Uma leva mais curta e mais bem paga: 4 de Guerreiro Espectral, entregue direto no quadro.', monster = 'Guerreiro Espectral', count = 4, levelMin = 36, levelMax = 40, reward = {xp = 2.8, ryo = 314, items = {{id = 7589, count = 1}}}},
	{id = 'daily_kill_curse_shaman_041', name = 'Xam\xE3 da Maldi\xE7\xE3o (41-45)', text = 'Reduza a popula\xE7\xE3o de Xam\xE3 da Maldi\xE7\xE3o por perto \x97 mate 8.', monster = 'Xam\xE3 da Maldi\xE7\xE3o', count = 8, levelMin = 41, levelMax = 45, reward = {xp = 4.0, ryo = 462, items = {}}},
	{id = 'daily_kill_spectral_warrior_041b', name = 'Guerreiro Espectral \x97 segunda leva (41-45)', text = 'Mais uma leva: 8 de Guerreiro Espectral na mesma regi\xE3o.', monster = 'Guerreiro Espectral', count = 8, levelMin = 41, levelMax = 45, reward = {xp = 3.6, ryo = 365, items = {}}},
	{id = 'daily_hunt_curse_shaman_041c', name = 'ca\xE7ada r\xE1pida de Xam\xE3 da Maldi\xE7\xE3o (41-45)', text = 'Uma leva mais curta e mais bem paga: 4 de Xam\xE3 da Maldi\xE7\xE3o, entregue direto no quadro.', monster = 'Xam\xE3 da Maldi\xE7\xE3o', count = 4, levelMin = 41, levelMax = 45, reward = {xp = 2.8, ryo = 363, items = {{id = 7589, count = 1}}}},
	{id = 'daily_kill_curse_shaman_046', name = 'Xam\xE3 da Maldi\xE7\xE3o (46-50)', text = 'Reduza a popula\xE7\xE3o de Xam\xE3 da Maldi\xE7\xE3o por perto \x97 mate 8.', monster = 'Xam\xE3 da Maldi\xE7\xE3o', count = 8, levelMin = 46, levelMax = 50, reward = {xp = 4.0, ryo = 462, items = {}}},
	{id = 'daily_kill_thunder_eagle_046b', name = '\xC1guia do Trov\xE3o \x97 segunda leva (46-50)', text = 'Mais uma leva: 8 de \xC1guia do Trov\xE3o na mesma regi\xE3o.', monster = '\xC1guia do Trov\xE3o', count = 8, levelMin = 46, levelMax = 50, reward = {xp = 3.6, ryo = 518, items = {}}},
	{id = 'daily_hunt_curse_shaman_046c', name = 'ca\xE7ada r\xE1pida de Xam\xE3 da Maldi\xE7\xE3o (46-50)', text = 'Uma leva mais curta e mais bem paga: 4 de Xam\xE3 da Maldi\xE7\xE3o, entregue direto no quadro.', monster = 'Xam\xE3 da Maldi\xE7\xE3o', count = 4, levelMin = 46, levelMax = 50, reward = {xp = 2.8, ryo = 363, items = {{id = 7589, count = 1}}}},
	{id = 'daily_kill_thunder_eagle_051', name = '\xC1guia do Trov\xE3o (51-55)', text = 'Reduza a popula\xE7\xE3o de \xC1guia do Trov\xE3o por perto \x97 mate 5.', monster = '\xC1guia do Trov\xE3o', count = 5, levelMin = 51, levelMax = 55, reward = {xp = 2.5, ryo = 354, items = {}}},
	{id = 'daily_kill_glacier_oni_051b', name = 'Oni da Geleira \x97 segunda leva (51-55)', text = 'Mais uma leva: 5 de Oni da Geleira na mesma regi\xE3o.', monster = 'Oni da Geleira', count = 5, levelMin = 51, levelMax = 55, reward = {xp = 2.2, ryo = 360, items = {}}},
	{id = 'daily_hunt_thunder_eagle_051c', name = 'ca\xE7ada r\xE1pida de \xC1guia do Trov\xE3o (51-55)', text = 'Uma leva mais curta e mais bem paga: 3 de \xC1guia do Trov\xE3o, entregue direto no quadro.', monster = '\xC1guia do Trov\xE3o', count = 3, levelMin = 51, levelMax = 55, reward = {xp = 2.1, ryo = 334, items = {{id = 7589, count = 1}}}},
	{id = 'daily_kill_glacier_oni_056', name = 'Oni da Geleira (56-60)', text = 'Reduza a popula\xE7\xE3o de Oni da Geleira por perto \x97 mate 5.', monster = 'Oni da Geleira', count = 5, levelMin = 56, levelMax = 60, reward = {xp = 2.5, ryo = 394, items = {}}},
	{id = 'daily_kill_thunder_eagle_056b', name = '\xC1guia do Trov\xE3o \x97 segunda leva (56-60)', text = 'Mais uma leva: 5 de \xC1guia do Trov\xE3o na mesma regi\xE3o.', monster = '\xC1guia do Trov\xE3o', count = 5, levelMin = 56, levelMax = 60, reward = {xp = 2.2, ryo = 324, items = {}}},
	{id = 'daily_hunt_glacier_oni_056c', name = 'ca\xE7ada r\xE1pida de Oni da Geleira (56-60)', text = 'Uma leva mais curta e mais bem paga: 3 de Oni da Geleira, entregue direto no quadro.', monster = 'Oni da Geleira', count = 3, levelMin = 56, levelMax = 60, reward = {xp = 2.1, ryo = 371, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_glacier_oni_061', name = 'Oni da Geleira (61-65)', text = 'Reduza a popula\xE7\xE3o de Oni da Geleira por perto \x97 mate 5.', monster = 'Oni da Geleira', count = 5, levelMin = 61, levelMax = 65, reward = {xp = 2.5, ryo = 394, items = {}}},
	{id = 'daily_kill_storm_monk_061b', name = 'Monge da Tempestade \x97 segunda leva (61-65)', text = 'Mais uma leva: 5 de Monge da Tempestade na mesma regi\xE3o.', monster = 'Monge da Tempestade', count = 5, levelMin = 61, levelMax = 65, reward = {xp = 2.2, ryo = 408, items = {}}},
	{id = 'daily_hunt_glacier_oni_061c', name = 'ca\xE7ada r\xE1pida de Oni da Geleira (61-65)', text = 'Uma leva mais curta e mais bem paga: 3 de Oni da Geleira, entregue direto no quadro.', monster = 'Oni da Geleira', count = 3, levelMin = 61, levelMax = 65, reward = {xp = 2.1, ryo = 371, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_storm_monk_066', name = 'Monge da Tempestade (66-70)', text = 'Reduza a popula\xE7\xE3o de Monge da Tempestade por perto \x97 mate 5.', monster = 'Monge da Tempestade', count = 5, levelMin = 66, levelMax = 70, reward = {xp = 2.5, ryo = 446, items = {}}},
	{id = 'daily_kill_magma_serpent_066b', name = 'Serpente de Magma \x97 segunda leva (66-70)', text = 'Mais uma leva: 5 de Serpente de Magma na mesma regi\xE3o.', monster = 'Serpente de Magma', count = 5, levelMin = 66, levelMax = 70, reward = {xp = 2.2, ryo = 444, items = {}}},
	{id = 'daily_hunt_storm_monk_066c', name = 'ca\xE7ada r\xE1pida de Monge da Tempestade (66-70)', text = 'Uma leva mais curta e mais bem paga: 3 de Monge da Tempestade, entregue direto no quadro.', monster = 'Monge da Tempestade', count = 3, levelMin = 66, levelMax = 70, reward = {xp = 2.1, ryo = 421, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_magma_serpent_071', name = 'Serpente de Magma (71-75)', text = 'Reduza a popula\xE7\xE3o de Serpente de Magma por perto \x97 mate 5.', monster = 'Serpente de Magma', count = 5, levelMin = 71, levelMax = 75, reward = {xp = 2.5, ryo = 486, items = {}}},
	{id = 'daily_kill_storm_monk_071b', name = 'Monge da Tempestade \x97 segunda leva (71-75)', text = 'Mais uma leva: 5 de Monge da Tempestade na mesma regi\xE3o.', monster = 'Monge da Tempestade', count = 5, levelMin = 71, levelMax = 75, reward = {xp = 2.2, ryo = 408, items = {}}},
	{id = 'daily_hunt_magma_serpent_071c', name = 'ca\xE7ada r\xE1pida de Serpente de Magma (71-75)', text = 'Uma leva mais curta e mais bem paga: 3 de Serpente de Magma, entregue direto no quadro.', monster = 'Serpente de Magma', count = 3, levelMin = 71, levelMax = 75, reward = {xp = 2.1, ryo = 458, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_magma_serpent_076', name = 'Serpente de Magma (76-80)', text = 'Reduza a popula\xE7\xE3o de Serpente de Magma por perto \x97 mate 5.', monster = 'Serpente de Magma', count = 5, levelMin = 76, levelMax = 80, reward = {xp = 2.5, ryo = 486, items = {}}},
	{id = 'daily_kill_white_clone_076b', name = 'Clone Branco \x97 segunda leva (76-80)', text = 'Mais uma leva: 5 de Clone Branco na mesma regi\xE3o.', monster = 'Clone Branco', count = 5, levelMin = 76, levelMax = 80, reward = {xp = 2.2, ryo = 432, items = {}}},
	{id = 'daily_hunt_magma_serpent_076c', name = 'ca\xE7ada r\xE1pida de Serpente de Magma (76-80)', text = 'Uma leva mais curta e mais bem paga: 3 de Serpente de Magma, entregue direto no quadro.', monster = 'Serpente de Magma', count = 3, levelMin = 76, levelMax = 80, reward = {xp = 2.1, ryo = 458, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_white_clone_081', name = 'Clone Branco (81-85)', text = 'Reduza a popula\xE7\xE3o de Clone Branco por perto \x97 mate 5.', monster = 'Clone Branco', count = 5, levelMin = 81, levelMax = 85, reward = {xp = 2.5, ryo = 472, items = {}}},
	{id = 'daily_kill_elite_cloud_guard_081b', name = 'Ninja Elite da Aurora \x97 segunda leva (81-85)', text = 'Mais uma leva: 5 de Ninja Elite da Aurora na mesma regi\xE3o.', monster = 'Ninja Elite da Aurora', count = 5, levelMin = 81, levelMax = 85, reward = {xp = 2.2, ryo = 528, items = {}}},
	{id = 'daily_hunt_white_clone_081c', name = 'ca\xE7ada r\xE1pida de Clone Branco (81-85)', text = 'Uma leva mais curta e mais bem paga: 3 de Clone Branco, entregue direto no quadro.', monster = 'Clone Branco', count = 3, levelMin = 81, levelMax = 85, reward = {xp = 2.1, ryo = 446, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_elite_cloud_guard_086', name = 'Ninja Elite da Aurora (86-90)', text = 'Reduza a popula\xE7\xE3o de Ninja Elite da Aurora por perto \x97 mate 5.', monster = 'Ninja Elite da Aurora', count = 5, levelMin = 86, levelMax = 90, reward = {xp = 2.5, ryo = 578, items = {}}},
	{id = 'daily_kill_white_clone_086b', name = 'Clone Branco \x97 segunda leva (86-90)', text = 'Mais uma leva: 5 de Clone Branco na mesma regi\xE3o.', monster = 'Clone Branco', count = 5, levelMin = 86, levelMax = 90, reward = {xp = 2.2, ryo = 432, items = {}}},
	{id = 'daily_hunt_elite_cloud_guard_086c', name = 'ca\xE7ada r\xE1pida de Ninja Elite da Aurora (86-90)', text = 'Uma leva mais curta e mais bem paga: 3 de Ninja Elite da Aurora, entregue direto no quadro.', monster = 'Ninja Elite da Aurora', count = 3, levelMin = 86, levelMax = 90, reward = {xp = 2.1, ryo = 544, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_elite_cloud_guard_091', name = 'Ninja Elite da Aurora (91-95)', text = 'Reduza a popula\xE7\xE3o de Ninja Elite da Aurora por perto \x97 mate 5.', monster = 'Ninja Elite da Aurora', count = 5, levelMin = 91, levelMax = 95, reward = {xp = 2.5, ryo = 578, items = {}}},
	{id = 'daily_kill_white_clone_091b', name = 'Clone Branco \x97 segunda leva (91-95)', text = 'Mais uma leva: 5 de Clone Branco na mesma regi\xE3o.', monster = 'Clone Branco', count = 5, levelMin = 91, levelMax = 95, reward = {xp = 2.2, ryo = 432, items = {}}},
	{id = 'daily_hunt_elite_cloud_guard_091c', name = 'ca\xE7ada r\xE1pida de Ninja Elite da Aurora (91-95)', text = 'Uma leva mais curta e mais bem paga: 3 de Ninja Elite da Aurora, entregue direto no quadro.', monster = 'Ninja Elite da Aurora', count = 3, levelMin = 91, levelMax = 95, reward = {xp = 2.1, ryo = 544, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_elite_cloud_guard_096', name = 'Ninja Elite da Aurora (96-100)', text = 'Reduza a popula\xE7\xE3o de Ninja Elite da Aurora por perto \x97 mate 5.', monster = 'Ninja Elite da Aurora', count = 5, levelMin = 96, levelMax = 100, reward = {xp = 2.5, ryo = 578, items = {}}},
	{id = 'daily_kill_white_clone_096b', name = 'Clone Branco \x97 segunda leva (96-100)', text = 'Mais uma leva: 5 de Clone Branco na mesma regi\xE3o.', monster = 'Clone Branco', count = 5, levelMin = 96, levelMax = 100, reward = {xp = 2.2, ryo = 432, items = {}}},
	{id = 'daily_hunt_elite_cloud_guard_096c', name = 'ca\xE7ada r\xE1pida de Ninja Elite da Aurora (96-100)', text = 'Uma leva mais curta e mais bem paga: 3 de Ninja Elite da Aurora, entregue direto no quadro.', monster = 'Ninja Elite da Aurora', count = 3, levelMin = 96, levelMax = 100, reward = {xp = 2.1, ryo = 544, items = {{id = 7591, count = 1}}}},
}

local function today()
	local t = os.date('*t')
	return t.year * 400 + t.yday
end

local function bracketPool(level)
	local out = {}
	for i, d in ipairs(NarutoDailies.pool) do
		if level >= d.levelMin and level <= d.levelMax then out[#out + 1] = i end
	end
	return out
end

--- Sorteia as 3 di\xE1rias do dia se ainda n\xE3o sorteou hoje para este jogador (chamado no login,
--- em !diaria e em qualquer kill, ent\xE3o nunca precisa ser chamado manualmente por fora).
function NarutoDailies.rollIfNeeded(player)
	if player:getStorageValue(NarutoDailies.DAY) == today() then return end
	local pool = bracketPool(player:getLevel())
	for i = #pool, 2, -1 do
		local j = math.random(i)
		pool[i], pool[j] = pool[j], pool[i]
	end
	for slot = 1, 3 do
		local idx = pool[slot] or -1
		player:setStorageValue(NarutoDailies.SLOT_POOL[slot], idx)
		player:setStorageValue(NarutoDailies.SLOT_PROGRESS[slot], idx > 0 and 0 or -1)
	end
	player:setStorageValue(NarutoDailies.DAY, today())
end

function NarutoDailies.slotEntry(player, slot)
	local idx = player:getStorageValue(NarutoDailies.SLOT_POOL[slot])
	if not idx or idx < 1 then return nil end
	return NarutoDailies.pool[idx]
end

function NarutoDailies.slotProgress(player, slot)
	return player:getStorageValue(NarutoDailies.SLOT_PROGRESS[slot])
end

function NarutoDailies.onKill(player, monsterName)
	NarutoDailies.rollIfNeeded(player)
	for slot = 1, 3 do
		local entry = NarutoDailies.slotEntry(player, slot)
		if entry and entry.monster == monsterName then
			local prog = NarutoDailies.slotProgress(player, slot)
			if prog >= 0 and prog < entry.count then
				player:setStorageValue(NarutoDailies.SLOT_PROGRESS[slot], prog + 1)
				player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Di\xE1ria " .. entry.name .. ": " .. (prog + 1) .. "/" .. entry.count)
			end
		end
	end
end

--- Entrega TODAS as di\xE1rias do dia que j\xE1 est\xE3o prontas. Retorna (algumaEntregue, xpTotal, ryoTotal).
function NarutoDailies.deliver(player)
	NarutoDailies.rollIfNeeded(player)
	local totalXp, totalRyo, any = 0, 0, false
	for slot = 1, 3 do
		local entry = NarutoDailies.slotEntry(player, slot)
		if entry then
			local prog = NarutoDailies.slotProgress(player, slot)
			if prog == entry.count then
				any = true
				local xp = NarutoRewards.scaledXp(player, entry.reward.xp)
				player:addExperience(xp, true)
				totalXp = totalXp + xp
				if entry.reward.ryo > 0 then player:addItem(NarutoQuests.RYO_ID, entry.reward.ryo) end
				totalRyo = totalRyo + entry.reward.ryo
				for _, it in ipairs(entry.reward.items) do player:addItem(it.id, it.count) end
				player:setStorageValue(NarutoDailies.SLOT_PROGRESS[slot], entry.count + 1)
				if NarutoAchievements then NarutoAchievements.onDailyDelivered(player) end
			end
		end
	end
	return any, totalXp, totalRyo
end
