-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Soco Monstruoso: Um soco de força monstruosa que racha o chão ao redor do impacto.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_HITAREA)

function onGetFormulaValues(player, level, maglevel)
	local base = 34 + level * 1.3 + maglevel * 1.0
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 1000)
condition:setFormula(-0.9, 0, -0.9, 0)
combat:addCondition(condition)  -- stun, chance 0.35

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
