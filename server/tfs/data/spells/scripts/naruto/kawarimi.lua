-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Kawarimi no Jutsu: Substituição: fica invulnerável por 1s e teleporta 2 tiles para trás.
function onCastSpell(creature, variant)
	local pos = creature:getPosition()
	local dir = creature:getDirection()
	local back = Position(pos)
	for _ = 1, 2 do
		back:getNextPosition(dir == DIRECTION_NORTH and DIRECTION_SOUTH or dir == DIRECTION_SOUTH and DIRECTION_NORTH or dir == DIRECTION_EAST and DIRECTION_WEST or DIRECTION_EAST)
	end
	local tile = Tile(back)
	if tile and tile:isWalkable() and not tile:hasFlag(TILESTATE_BLOCKSOLID) then
		pos:sendMagicEffect(CONST_ME_POFF)
		creature:teleportTo(back)
		back:sendMagicEffect(CONST_ME_POFF)
		local cond = Condition(CONDITION_INVISIBLE)
		cond:setParameter(CONDITION_PARAM_TICKS, 1000)
		creature:addCondition(cond)
		return true
	end
	creature:sendCancelMessage("Não há espaço para a substituição.")
	pos:sendMagicEffect(CONST_ME_POFF)
	return false
end
