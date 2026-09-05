-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Vigor Teimoso: Determinação teimosa que acelera a recuperação do próprio corpo em combate.
local condition = Condition(CONDITION_REGENERATION)
condition:setParameter(CONDITION_PARAM_SUBID, 1)
condition:setParameter(CONDITION_PARAM_TICKS, 6000)
condition:setParameter(CONDITION_PARAM_HEALTHGAIN, 7)
condition:setParameter(CONDITION_PARAM_HEALTHTICKS, 1000)

function onCastSpell(creature, variant)
	creature:addCondition(condition)
	creature:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
	return true
end
