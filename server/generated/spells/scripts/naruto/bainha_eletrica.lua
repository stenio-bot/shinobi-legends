-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Bainha Elétrica: A lâmina vibra com eletricidade, formando uma bainha que acelera a recuperação do usuário.
local condition = Condition(CONDITION_REGENERATION)
condition:setParameter(CONDITION_PARAM_SUBID, 1)
condition:setParameter(CONDITION_PARAM_TICKS, 8000)
condition:setParameter(CONDITION_PARAM_HEALTHGAIN, 9)
condition:setParameter(CONDITION_PARAM_HEALTHTICKS, 1000)

function onCastSpell(creature, variant)
	creature:addCondition(condition)
	local pos = creature:getPosition()
	NarutoJson.broadcastSfx(pos, "sfx_zap_loop")
	pos:sendMagicEffect(211)
	return true
end
