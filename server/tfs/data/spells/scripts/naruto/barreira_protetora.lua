-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Barreira Protetora: Uma barreira de chakra selado que absorve parte do dano recebido.
local condition = Condition(CONDITION_REGENERATION)
condition:setParameter(CONDITION_PARAM_SUBID, 1)
condition:setParameter(CONDITION_PARAM_TICKS, 8000)
condition:setParameter(CONDITION_PARAM_HEALTHGAIN, 9)
condition:setParameter(CONDITION_PARAM_HEALTHTICKS, 1000)

function onCastSpell(creature, variant)
	creature:addCondition(condition)
	creature:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
	return true
end
