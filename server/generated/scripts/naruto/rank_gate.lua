-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/scripts/naruto/rank_gate.lua (revscriptsys carrega sozinho).
-- Gate de \xE1rea por rank (docs/lore/progressao.md): tiles com actionid 45001..45005 (= rank
-- m\xEDnimo 1 Genin..5 Kage) barram quem n\xE3o tem o rank. O agente de mapa aplica o actionid certo
-- nos teleportes/portas de cada zona nova; sem isso o tile funciona normalmente (fallback: no-op).
local gate = MoveEvent()
gate:type("stepin")

function gate.onStepIn(player, item, position, fromPosition)
	-- ACHADO (miss\xE3o de mapa v3, 1a vez que um actionid de gate foi colocado
	-- num tile de verdade): monstros perseguindo o jogador podem pisar no
	-- mesmo tile do gate (ele \xE9 walkable, s\xF3 o jogador \xE9 barrado) \x97 sem essa
	-- checagem, `player:getStorageValue` explode com "attempt to call method
	-- 'getStorageValue' (a nil value)" porque Creature/Monster n\xE3o tem esse
	-- m\xE9todo (s\xF3 Player tem). Gate nunca deve barrar monstro.
	if not player:isPlayer() then return true end
	local need = item:getActionId() - 45000
	if need < 1 or need > 5 then return true end
	if not NarutoRanks or NarutoRanks.get(player).index >= need then return true end
	local reqRank = NarutoRanks.byIndex[need]
	player:sendCancelMessage("Voc\xEA precisa ser " .. (reqRank and reqRank.title or "de rank superior") .. " para entrar aqui.")
	player:teleportTo(fromPosition, true)
	fromPosition:sendMagicEffect(CONST_ME_POFF)
	return true
end

gate:aid(45001, 45002, 45003, 45004, 45005)
gate:register()
