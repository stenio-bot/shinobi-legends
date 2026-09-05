-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/scripts/naruto/rank_gate.lua (revscriptsys carrega sozinho).
-- Gate de área por rank (docs/lore/progressao.md): tiles com actionid 45001..45005 (= rank
-- mínimo 1 Genin..5 Kage) barram quem não tem o rank. O agente de mapa aplica o actionid certo
-- nos teleportes/portas de cada zona nova; sem isso o tile funciona normalmente (fallback: no-op).
local gate = MoveEvent()
gate:type("stepin")

function gate.onStepIn(player, item, position, fromPosition)
	local need = item:getActionId() - 45000
	if need < 1 or need > 5 then return true end
	if not NarutoRanks or NarutoRanks.get(player).index >= need then return true end
	local reqRank = NarutoRanks.byIndex[need]
	player:sendCancelMessage("Você precisa ser " .. (reqRank and reqRank.title or "de rank superior") .. " para entrar aqui.")
	player:teleportTo(fromPosition, true)
	fromPosition:sendMagicEffect(CONST_ME_POFF)
	return true
end

gate:aid(45001, 45002, 45003, 45004, 45005)
gate:register()
