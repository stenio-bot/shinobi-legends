-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/lib/naruto_rewards.lua e adicione dofile em data/lib/lib.lua.
-- XP escalada por level (docs/sistemas/progressao-servidor.md; docs/sistemas/balanceamento.md:
-- 'XP p/ subir de level = 100*L + 100', ~5,5 kills por level em m\xE9dia no conte\xFAdo j\xE1 existente).
--
-- Usada por TAREFAS (data/tasks.json) e DI\xC1RIAS (data/dailies.json): seu 'reward.xp' \xE9 um
-- n\xFAmero de KILLS EQUIVALENTES (tipicamente 5-8), n\xE3o XP absoluto, convertido aqui para o
-- level ATUAL de quem entrega \x97 a entrega vale sempre ~o mesmo tanto de kills, n\xE3o um valor
-- fixo que fica trivial (jogador alto level) ou imposs\xEDvel (jogador baixo level) com o tempo.
-- Miss\xF5es de hist\xF3ria (data/npcs/*.json) continuam com reward.xp absoluto e hand-tuned
-- (docs/sistemas/balanceamento.md) e N\xC3O passam por esta fun\xE7\xE3o \x97 decis\xE3o documentada em
-- docs/sistemas/progressao-servidor.md para n\xE3o destuning n\xFAmeros de quest j\xE1 balanceados.
NarutoRewards = {}
NarutoRewards.XP_PER_KILL_DIVISOR = 5.5  -- kills m\xE9dios por level, ver balanceamento.md

function NarutoRewards.xpToNextLevel(level)
	return 100 * level + 100
end

function NarutoRewards.scaledXp(player, killsEquivalent)
	local level = math.max(1, player:getLevel())
	local xpPerKill = NarutoRewards.xpToNextLevel(level) / NarutoRewards.XP_PER_KILL_DIVISOR
	return math.floor(xpPerKill * (killsEquivalent or 0))
end
