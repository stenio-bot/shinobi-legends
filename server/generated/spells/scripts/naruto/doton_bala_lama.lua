-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Doton: Bala de Lama: Uma bala de lama endurecida disparada em alta velocidade.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_EARTHDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 215)
combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, 63)

function onGetFormulaValues(player, level, maglevel)
	local base = 8.05 + level * 0.385 + maglevel * 0.297
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 3000)
condition:setFormula(-0.25, 0, -0.25, 0)
combat:addCondition(condition)  -- slow, chance 0.3

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
