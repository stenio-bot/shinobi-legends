-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Lâmina Relâmpago: Um corte de lâmina eletrificada, rápido o bastante para atordoar.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_ENERGYDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_ENERGYHIT)

function onGetFormulaValues(player, level, maglevel)
	local base = 20.4 + level * 0.864 + maglevel * 0.707
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 1000)
condition:setFormula(-0.9, 0, -0.9, 0)
combat:addCondition(condition)  -- paralyze, chance 0.2

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
