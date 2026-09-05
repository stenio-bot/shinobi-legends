-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Rasteira de Vento Leve: Uma rasteira reforçada por uma leve corrente de vento, desequilibra o alvo.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_HOLYDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_HOLYAREA)
local area = {
	{1, 1, 1},
	{0, 1, 0},
	{0, 2, 0}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 12 + level * 0.7 + maglevel * 0.5
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 2000)
condition:setFormula(-0.3, 0, -0.3, 0)
combat:addCondition(condition)  -- slow, chance 0.4

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
