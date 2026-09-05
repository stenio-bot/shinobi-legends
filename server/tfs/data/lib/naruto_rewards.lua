-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/lib/naruto_rewards.lua e adicione dofile em data/lib/lib.lua.
-- XP escalada por level (docs/sistemas/progressao-servidor.md; docs/sistemas/balanceamento.md:
-- 'XP p/ subir de level = 100*L + 100', ~5,5 kills por level em média no conteúdo já existente).
--
-- Usada por TAREFAS (data/tasks.json) e DIÁRIAS (data/dailies.json): seu 'reward.xp' é um
-- número de KILLS EQUIVALENTES (tipicamente 5-8), não XP absoluto, convertido aqui para o
-- level ATUAL de quem entrega — a entrega vale sempre ~o mesmo tanto de kills, não um valor
-- fixo que fica trivial (jogador alto level) ou impossível (jogador baixo level) com o tempo.
-- Missões de história (data/npcs/*.json) continuam com reward.xp absoluto e hand-tuned
-- (docs/sistemas/balanceamento.md) e NÃO passam por esta função — decisão documentada em
-- docs/sistemas/progressao-servidor.md para não destuning números de quest já balanceados.
NarutoRewards = {}
NarutoRewards.XP_PER_KILL_DIVISOR = 5.5  -- kills médios por level, ver balanceamento.md

function NarutoRewards.xpToNextLevel(level)
	return 100 * level + 100
end

function NarutoRewards.scaledXp(player, killsEquivalent)
	local level = math.max(1, player:getLevel())
	local xpPerKill = NarutoRewards.xpToNextLevel(level) / NarutoRewards.XP_PER_KILL_DIVISOR
	return math.floor(xpPerKill * (killsEquivalent or 0))
end
