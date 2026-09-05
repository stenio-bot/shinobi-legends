-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Visão de Alcance Total: Visão que enxerga os pontos vitais de chakra do inimigo, refinando cada golpe seguinte.
local condition = Condition(CONDITION_REGENERATION)
condition:setParameter(CONDITION_PARAM_SUBID, 1)
condition:setParameter(CONDITION_PARAM_TICKS, 5000)
condition:setParameter(CONDITION_PARAM_HEALTHGAIN, 5)
condition:setParameter(CONDITION_PARAM_HEALTHTICKS, 1000)

function onCastSpell(creature, variant)
	creature:addCondition(condition)
	local pos = creature:getPosition()
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(pos, "sfx_focus") end
	pos:sendMagicEffect(219)
	return true
end
