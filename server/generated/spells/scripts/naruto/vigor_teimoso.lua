-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

-- Vigor Teimoso: Determina\xE7\xE3o teimosa que acelera a recupera\xE7\xE3o do pr\xF3prio corpo em combate.
local condition = Condition(CONDITION_REGENERATION)
condition:setParameter(CONDITION_PARAM_SUBID, 1)
condition:setParameter(CONDITION_PARAM_TICKS, 6000)
condition:setParameter(CONDITION_PARAM_HEALTHGAIN, 7)
condition:setParameter(CONDITION_PARAM_HEALTHTICKS, 1000)

function onCastSpell(creature, variant)
	creature:addCondition(condition)
	local pos = creature:getPosition()
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(pos, "sfx_shout") end
	pos:sendMagicEffect(219)
	return true
end
