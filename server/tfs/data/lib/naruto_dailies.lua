-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/lib/naruto_dailies.lua e adicione dofile em data/lib/lib.lua.
-- Missões diárias (data/dailies.json, docs/sistemas/progressao-servidor.md): a cada dia, 3
-- entradas são sorteadas do pool cuja faixa [levelMin,levelMax] contém o level do jogador (na
-- hora do sorteio). Simplificação vs. o pedido original: as 3 diárias do dia já ficam
-- AUTO-ACEITAS (contam kills desde o sorteio, sem passo extra de 'aceitar por número') —
-- '!diaria' mostra e '!diaria entregar' entrega; ver pendências no relatório da missão.
-- SLOT_PROGRESS: -1 sem entrada nesse slot hoje, 0..count-1 em andamento, count = pronta,
-- count+1 = já entregue hoje.
NarutoDailies = {}
NarutoDailies.DAY = 60020
NarutoDailies.SLOT_POOL = {60021, 60022, 60023}
NarutoDailies.SLOT_PROGRESS = {60024, 60025, 60026}
NarutoDailies.pool = {
	{id = 'daily_kill_wolf_001', name = 'Diária: Lobo (1-5)', text = 'Reduza a população de Lobo por perto — mate 12.', monster = 'Lobo', count = 12, levelMin = 1, levelMax = 5, reward = {xp = 6.0, ryo = 21, items = {}}},
	{id = 'daily_kill_forest_deer_001b', name = 'Diária: Cervo — segunda leva (1-5)', text = 'Mais uma leva: 12 de Cervo na mesma região.', monster = 'Cervo', count = 12, levelMin = 1, levelMax = 5, reward = {xp = 5.4, ryo = 8, items = {}}},
	{id = 'daily_hunt_wolf_001c', name = 'Diária: caçada rápida de Lobo (1-5)', text = 'Uma leva mais curta e mais bem paga: 8 de Lobo, entregue direto no quadro.', monster = 'Lobo', count = 8, levelMin = 1, levelMax = 5, reward = {xp = 5.6, ryo = 22, items = {{id = 7618, count = 1}}}},
	{id = 'daily_kill_bandit_archer_006', name = 'Diária: Bandido Arqueiro (6-10)', text = 'Reduza a população de Bandido Arqueiro por perto — mate 12.', monster = 'Bandido Arqueiro', count = 12, levelMin = 6, levelMax = 10, reward = {xp = 6.0, ryo = 84, items = {}}},
	{id = 'daily_kill_leech_006b', name = 'Diária: Sanguessuga Gigante — segunda leva (6-10)', text = 'Mais uma leva: 12 de Sanguessuga Gigante na mesma região.', monster = 'Sanguessuga Gigante', count = 12, levelMin = 6, levelMax = 10, reward = {xp = 5.4, ryo = 106, items = {}}},
	{id = 'daily_hunt_bandit_archer_006c', name = 'Diária: caçada rápida de Bandido Arqueiro (6-10)', text = 'Uma leva mais curta e mais bem paga: 8 de Bandido Arqueiro, entregue direto no quadro.', monster = 'Bandido Arqueiro', count = 8, levelMin = 6, levelMax = 10, reward = {xp = 5.6, ryo = 88, items = {{id = 7618, count = 1}}}},
	{id = 'daily_kill_giant_toad_011', name = 'Diária: Sapo Gigante (11-15)', text = 'Reduza a população de Sapo Gigante por perto — mate 12.', monster = 'Sapo Gigante', count = 12, levelMin = 11, levelMax = 15, reward = {xp = 6.0, ryo = 178, items = {}}},
	{id = 'daily_kill_mercenary_bridge_011b', name = 'Diária: Mercenário da Ponte — segunda leva (11-15)', text = 'Mais uma leva: 12 de Mercenário da Ponte na mesma região.', monster = 'Mercenário da Ponte', count = 12, levelMin = 11, levelMax = 15, reward = {xp = 5.4, ryo = 63, items = {}}},
	{id = 'daily_hunt_giant_toad_011c', name = 'Diária: caçada rápida de Sapo Gigante (11-15)', text = 'Uma leva mais curta e mais bem paga: 8 de Sapo Gigante, entregue direto no quadro.', monster = 'Sapo Gigante', count = 8, levelMin = 11, levelMax = 15, reward = {xp = 5.6, ryo = 187, items = {{id = 7618, count = 1}}}},
	{id = 'daily_kill_rogue_ninja_016', name = 'Diária: Ninja Renegado (16-20)', text = 'Reduza a população de Ninja Renegado por perto — mate 12.', monster = 'Ninja Renegado', count = 12, levelMin = 16, levelMax = 20, reward = {xp = 6.0, ryo = 294, items = {}}},
	{id = 'daily_kill_lesser_serpent_016b', name = 'Diária: Serpente Menor — segunda leva (16-20)', text = 'Mais uma leva: 12 de Serpente Menor na mesma região.', monster = 'Serpente Menor', count = 12, levelMin = 16, levelMax = 20, reward = {xp = 5.4, ryo = 259, items = {}}},
	{id = 'daily_hunt_rogue_ninja_016c', name = 'Diária: caçada rápida de Ninja Renegado (16-20)', text = 'Uma leva mais curta e mais bem paga: 8 de Ninja Renegado, entregue direto no quadro.', monster = 'Ninja Renegado', count = 8, levelMin = 16, levelMax = 20, reward = {xp = 5.6, ryo = 308, items = {{id = 7588, count = 1}}}},
	{id = 'daily_kill_ruin_puppet_021', name = 'Diária: Marionete de Combate (21-25)', text = 'Reduza a população de Marionete de Combate por perto — mate 8.', monster = 'Marionete de Combate', count = 8, levelMin = 21, levelMax = 25, reward = {xp = 4.0, ryo = 284, items = {}}},
	{id = 'daily_kill_rogue_ninja_021b', name = 'Diária: Ninja Renegado — segunda leva (21-25)', text = 'Mais uma leva: 8 de Ninja Renegado na mesma região.', monster = 'Ninja Renegado', count = 8, levelMin = 21, levelMax = 25, reward = {xp = 3.6, ryo = 179, items = {}}},
	{id = 'daily_hunt_ruin_puppet_021c', name = 'Diária: caçada rápida de Marionete de Combate (21-25)', text = 'Uma leva mais curta e mais bem paga: 4 de Marionete de Combate, entregue direto no quadro.', monster = 'Marionete de Combate', count = 4, levelMin = 21, levelMax = 25, reward = {xp = 2.8, ryo = 223, items = {{id = 7588, count = 1}}}},
	{id = 'daily_kill_ruin_puppet_026', name = 'Diária: Marionete de Combate (26-30)', text = 'Reduza a população de Marionete de Combate por perto — mate 8.', monster = 'Marionete de Combate', count = 8, levelMin = 26, levelMax = 30, reward = {xp = 4.0, ryo = 284, items = {}}},
	{id = 'daily_kill_stone_sentinel_026b', name = 'Diária: Sentinela de Pedra — segunda leva (26-30)', text = 'Mais uma leva: 8 de Sentinela de Pedra na mesma região.', monster = 'Sentinela de Pedra', count = 8, levelMin = 26, levelMax = 30, reward = {xp = 3.6, ryo = 307, items = {}}},
	{id = 'daily_hunt_ruin_puppet_026c', name = 'Diária: caçada rápida de Marionete de Combate (26-30)', text = 'Uma leva mais curta e mais bem paga: 4 de Marionete de Combate, entregue direto no quadro.', monster = 'Marionete de Combate', count = 4, levelMin = 26, levelMax = 30, reward = {xp = 2.8, ryo = 223, items = {{id = 7588, count = 1}}}},
	{id = 'daily_kill_stone_sentinel_031', name = 'Diária: Sentinela de Pedra (31-35)', text = 'Reduza a população de Sentinela de Pedra por perto — mate 8.', monster = 'Sentinela de Pedra', count = 8, levelMin = 31, levelMax = 35, reward = {xp = 4.0, ryo = 336, items = {}}},
	{id = 'daily_kill_spectral_warrior_031b', name = 'Diária: Guerreiro Espectral — segunda leva (31-35)', text = 'Mais uma leva: 8 de Guerreiro Espectral na mesma região.', monster = 'Guerreiro Espectral', count = 8, levelMin = 31, levelMax = 35, reward = {xp = 3.6, ryo = 365, items = {}}},
	{id = 'daily_hunt_stone_sentinel_031c', name = 'Diária: caçada rápida de Sentinela de Pedra (31-35)', text = 'Uma leva mais curta e mais bem paga: 4 de Sentinela de Pedra, entregue direto no quadro.', monster = 'Sentinela de Pedra', count = 4, levelMin = 31, levelMax = 35, reward = {xp = 2.8, ryo = 264, items = {{id = 7589, count = 1}}}},
	{id = 'daily_kill_spectral_warrior_036', name = 'Diária: Guerreiro Espectral (36-40)', text = 'Reduza a população de Guerreiro Espectral por perto — mate 8.', monster = 'Guerreiro Espectral', count = 8, levelMin = 36, levelMax = 40, reward = {xp = 4.0, ryo = 399, items = {}}},
	{id = 'daily_kill_stone_sentinel_036b', name = 'Diária: Sentinela de Pedra — segunda leva (36-40)', text = 'Mais uma leva: 8 de Sentinela de Pedra na mesma região.', monster = 'Sentinela de Pedra', count = 8, levelMin = 36, levelMax = 40, reward = {xp = 3.6, ryo = 307, items = {}}},
	{id = 'daily_hunt_spectral_warrior_036c', name = 'Diária: caçada rápida de Guerreiro Espectral (36-40)', text = 'Uma leva mais curta e mais bem paga: 4 de Guerreiro Espectral, entregue direto no quadro.', monster = 'Guerreiro Espectral', count = 4, levelMin = 36, levelMax = 40, reward = {xp = 2.8, ryo = 314, items = {{id = 7589, count = 1}}}},
	{id = 'daily_kill_curse_shaman_041', name = 'Diária: Xamã da Maldição (41-45)', text = 'Reduza a população de Xamã da Maldição por perto — mate 8.', monster = 'Xamã da Maldição', count = 8, levelMin = 41, levelMax = 45, reward = {xp = 4.0, ryo = 462, items = {}}},
	{id = 'daily_kill_spectral_warrior_041b', name = 'Diária: Guerreiro Espectral — segunda leva (41-45)', text = 'Mais uma leva: 8 de Guerreiro Espectral na mesma região.', monster = 'Guerreiro Espectral', count = 8, levelMin = 41, levelMax = 45, reward = {xp = 3.6, ryo = 365, items = {}}},
	{id = 'daily_hunt_curse_shaman_041c', name = 'Diária: caçada rápida de Xamã da Maldição (41-45)', text = 'Uma leva mais curta e mais bem paga: 4 de Xamã da Maldição, entregue direto no quadro.', monster = 'Xamã da Maldição', count = 4, levelMin = 41, levelMax = 45, reward = {xp = 2.8, ryo = 363, items = {{id = 7589, count = 1}}}},
	{id = 'daily_kill_curse_shaman_046', name = 'Diária: Xamã da Maldição (46-50)', text = 'Reduza a população de Xamã da Maldição por perto — mate 8.', monster = 'Xamã da Maldição', count = 8, levelMin = 46, levelMax = 50, reward = {xp = 4.0, ryo = 462, items = {}}},
	{id = 'daily_kill_thunder_eagle_046b', name = 'Diária: Águia do Trovão — segunda leva (46-50)', text = 'Mais uma leva: 8 de Águia do Trovão na mesma região.', monster = 'Águia do Trovão', count = 8, levelMin = 46, levelMax = 50, reward = {xp = 3.6, ryo = 518, items = {}}},
	{id = 'daily_hunt_curse_shaman_046c', name = 'Diária: caçada rápida de Xamã da Maldição (46-50)', text = 'Uma leva mais curta e mais bem paga: 4 de Xamã da Maldição, entregue direto no quadro.', monster = 'Xamã da Maldição', count = 4, levelMin = 46, levelMax = 50, reward = {xp = 2.8, ryo = 363, items = {{id = 7589, count = 1}}}},
	{id = 'daily_kill_thunder_eagle_051', name = 'Diária: Águia do Trovão (51-55)', text = 'Reduza a população de Águia do Trovão por perto — mate 5.', monster = 'Águia do Trovão', count = 5, levelMin = 51, levelMax = 55, reward = {xp = 2.5, ryo = 354, items = {}}},
	{id = 'daily_kill_glacier_oni_051b', name = 'Diária: Oni da Geleira — segunda leva (51-55)', text = 'Mais uma leva: 5 de Oni da Geleira na mesma região.', monster = 'Oni da Geleira', count = 5, levelMin = 51, levelMax = 55, reward = {xp = 2.2, ryo = 360, items = {}}},
	{id = 'daily_hunt_thunder_eagle_051c', name = 'Diária: caçada rápida de Águia do Trovão (51-55)', text = 'Uma leva mais curta e mais bem paga: 3 de Águia do Trovão, entregue direto no quadro.', monster = 'Águia do Trovão', count = 3, levelMin = 51, levelMax = 55, reward = {xp = 2.1, ryo = 334, items = {{id = 7589, count = 1}}}},
	{id = 'daily_kill_glacier_oni_056', name = 'Diária: Oni da Geleira (56-60)', text = 'Reduza a população de Oni da Geleira por perto — mate 5.', monster = 'Oni da Geleira', count = 5, levelMin = 56, levelMax = 60, reward = {xp = 2.5, ryo = 394, items = {}}},
	{id = 'daily_kill_thunder_eagle_056b', name = 'Diária: Águia do Trovão — segunda leva (56-60)', text = 'Mais uma leva: 5 de Águia do Trovão na mesma região.', monster = 'Águia do Trovão', count = 5, levelMin = 56, levelMax = 60, reward = {xp = 2.2, ryo = 324, items = {}}},
	{id = 'daily_hunt_glacier_oni_056c', name = 'Diária: caçada rápida de Oni da Geleira (56-60)', text = 'Uma leva mais curta e mais bem paga: 3 de Oni da Geleira, entregue direto no quadro.', monster = 'Oni da Geleira', count = 3, levelMin = 56, levelMax = 60, reward = {xp = 2.1, ryo = 371, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_glacier_oni_061', name = 'Diária: Oni da Geleira (61-65)', text = 'Reduza a população de Oni da Geleira por perto — mate 5.', monster = 'Oni da Geleira', count = 5, levelMin = 61, levelMax = 65, reward = {xp = 2.5, ryo = 394, items = {}}},
	{id = 'daily_kill_storm_monk_061b', name = 'Diária: Monge da Tempestade — segunda leva (61-65)', text = 'Mais uma leva: 5 de Monge da Tempestade na mesma região.', monster = 'Monge da Tempestade', count = 5, levelMin = 61, levelMax = 65, reward = {xp = 2.2, ryo = 408, items = {}}},
	{id = 'daily_hunt_glacier_oni_061c', name = 'Diária: caçada rápida de Oni da Geleira (61-65)', text = 'Uma leva mais curta e mais bem paga: 3 de Oni da Geleira, entregue direto no quadro.', monster = 'Oni da Geleira', count = 3, levelMin = 61, levelMax = 65, reward = {xp = 2.1, ryo = 371, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_storm_monk_066', name = 'Diária: Monge da Tempestade (66-70)', text = 'Reduza a população de Monge da Tempestade por perto — mate 5.', monster = 'Monge da Tempestade', count = 5, levelMin = 66, levelMax = 70, reward = {xp = 2.5, ryo = 446, items = {}}},
	{id = 'daily_kill_magma_serpent_066b', name = 'Diária: Serpente de Magma — segunda leva (66-70)', text = 'Mais uma leva: 5 de Serpente de Magma na mesma região.', monster = 'Serpente de Magma', count = 5, levelMin = 66, levelMax = 70, reward = {xp = 2.2, ryo = 444, items = {}}},
	{id = 'daily_hunt_storm_monk_066c', name = 'Diária: caçada rápida de Monge da Tempestade (66-70)', text = 'Uma leva mais curta e mais bem paga: 3 de Monge da Tempestade, entregue direto no quadro.', monster = 'Monge da Tempestade', count = 3, levelMin = 66, levelMax = 70, reward = {xp = 2.1, ryo = 421, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_magma_serpent_071', name = 'Diária: Serpente de Magma (71-75)', text = 'Reduza a população de Serpente de Magma por perto — mate 5.', monster = 'Serpente de Magma', count = 5, levelMin = 71, levelMax = 75, reward = {xp = 2.5, ryo = 486, items = {}}},
	{id = 'daily_kill_storm_monk_071b', name = 'Diária: Monge da Tempestade — segunda leva (71-75)', text = 'Mais uma leva: 5 de Monge da Tempestade na mesma região.', monster = 'Monge da Tempestade', count = 5, levelMin = 71, levelMax = 75, reward = {xp = 2.2, ryo = 408, items = {}}},
	{id = 'daily_hunt_magma_serpent_071c', name = 'Diária: caçada rápida de Serpente de Magma (71-75)', text = 'Uma leva mais curta e mais bem paga: 3 de Serpente de Magma, entregue direto no quadro.', monster = 'Serpente de Magma', count = 3, levelMin = 71, levelMax = 75, reward = {xp = 2.1, ryo = 458, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_magma_serpent_076', name = 'Diária: Serpente de Magma (76-80)', text = 'Reduza a população de Serpente de Magma por perto — mate 5.', monster = 'Serpente de Magma', count = 5, levelMin = 76, levelMax = 80, reward = {xp = 2.5, ryo = 486, items = {}}},
	{id = 'daily_kill_white_clone_076b', name = 'Diária: Clone Branco — segunda leva (76-80)', text = 'Mais uma leva: 5 de Clone Branco na mesma região.', monster = 'Clone Branco', count = 5, levelMin = 76, levelMax = 80, reward = {xp = 2.2, ryo = 432, items = {}}},
	{id = 'daily_hunt_magma_serpent_076c', name = 'Diária: caçada rápida de Serpente de Magma (76-80)', text = 'Uma leva mais curta e mais bem paga: 3 de Serpente de Magma, entregue direto no quadro.', monster = 'Serpente de Magma', count = 3, levelMin = 76, levelMax = 80, reward = {xp = 2.1, ryo = 458, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_white_clone_081', name = 'Diária: Clone Branco (81-85)', text = 'Reduza a população de Clone Branco por perto — mate 5.', monster = 'Clone Branco', count = 5, levelMin = 81, levelMax = 85, reward = {xp = 2.5, ryo = 472, items = {}}},
	{id = 'daily_kill_elite_cloud_guard_081b', name = 'Diária: Ninja Elite da Aurora — segunda leva (81-85)', text = 'Mais uma leva: 5 de Ninja Elite da Aurora na mesma região.', monster = 'Ninja Elite da Aurora', count = 5, levelMin = 81, levelMax = 85, reward = {xp = 2.2, ryo = 528, items = {}}},
	{id = 'daily_hunt_white_clone_081c', name = 'Diária: caçada rápida de Clone Branco (81-85)', text = 'Uma leva mais curta e mais bem paga: 3 de Clone Branco, entregue direto no quadro.', monster = 'Clone Branco', count = 3, levelMin = 81, levelMax = 85, reward = {xp = 2.1, ryo = 446, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_elite_cloud_guard_086', name = 'Diária: Ninja Elite da Aurora (86-90)', text = 'Reduza a população de Ninja Elite da Aurora por perto — mate 5.', monster = 'Ninja Elite da Aurora', count = 5, levelMin = 86, levelMax = 90, reward = {xp = 2.5, ryo = 578, items = {}}},
	{id = 'daily_kill_white_clone_086b', name = 'Diária: Clone Branco — segunda leva (86-90)', text = 'Mais uma leva: 5 de Clone Branco na mesma região.', monster = 'Clone Branco', count = 5, levelMin = 86, levelMax = 90, reward = {xp = 2.2, ryo = 432, items = {}}},
	{id = 'daily_hunt_elite_cloud_guard_086c', name = 'Diária: caçada rápida de Ninja Elite da Aurora (86-90)', text = 'Uma leva mais curta e mais bem paga: 3 de Ninja Elite da Aurora, entregue direto no quadro.', monster = 'Ninja Elite da Aurora', count = 3, levelMin = 86, levelMax = 90, reward = {xp = 2.1, ryo = 544, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_elite_cloud_guard_091', name = 'Diária: Ninja Elite da Aurora (91-95)', text = 'Reduza a população de Ninja Elite da Aurora por perto — mate 5.', monster = 'Ninja Elite da Aurora', count = 5, levelMin = 91, levelMax = 95, reward = {xp = 2.5, ryo = 578, items = {}}},
	{id = 'daily_kill_white_clone_091b', name = 'Diária: Clone Branco — segunda leva (91-95)', text = 'Mais uma leva: 5 de Clone Branco na mesma região.', monster = 'Clone Branco', count = 5, levelMin = 91, levelMax = 95, reward = {xp = 2.2, ryo = 432, items = {}}},
	{id = 'daily_hunt_elite_cloud_guard_091c', name = 'Diária: caçada rápida de Ninja Elite da Aurora (91-95)', text = 'Uma leva mais curta e mais bem paga: 3 de Ninja Elite da Aurora, entregue direto no quadro.', monster = 'Ninja Elite da Aurora', count = 3, levelMin = 91, levelMax = 95, reward = {xp = 2.1, ryo = 544, items = {{id = 7591, count = 1}}}},
	{id = 'daily_kill_elite_cloud_guard_096', name = 'Diária: Ninja Elite da Aurora (96-100)', text = 'Reduza a população de Ninja Elite da Aurora por perto — mate 5.', monster = 'Ninja Elite da Aurora', count = 5, levelMin = 96, levelMax = 100, reward = {xp = 2.5, ryo = 578, items = {}}},
	{id = 'daily_kill_white_clone_096b', name = 'Diária: Clone Branco — segunda leva (96-100)', text = 'Mais uma leva: 5 de Clone Branco na mesma região.', monster = 'Clone Branco', count = 5, levelMin = 96, levelMax = 100, reward = {xp = 2.2, ryo = 432, items = {}}},
	{id = 'daily_hunt_elite_cloud_guard_096c', name = 'Diária: caçada rápida de Ninja Elite da Aurora (96-100)', text = 'Uma leva mais curta e mais bem paga: 3 de Ninja Elite da Aurora, entregue direto no quadro.', monster = 'Ninja Elite da Aurora', count = 3, levelMin = 96, levelMax = 100, reward = {xp = 2.1, ryo = 544, items = {{id = 7591, count = 1}}}},
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

--- Sorteia as 3 diárias do dia se ainda não sorteou hoje para este jogador (chamado no login,
--- em !diaria e em qualquer kill, então nunca precisa ser chamado manualmente por fora).
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
				player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Diária " .. entry.name .. ": " .. (prog + 1) .. "/" .. entry.count)
			end
		end
	end
end

--- Entrega TODAS as diárias do dia que já estão prontas. Retorna (algumaEntregue, xpTotal, ryoTotal).
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
			end
		end
	end
	return any, totalXp, totalRyo
end
