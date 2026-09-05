-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Suiton: Dragão de Água: Onda em linha que empurra e desacelera.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_ICEDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_ICEATTACK)
local area = {
	{1},
	{1},
	{1},
	{1},
	{1},
	{2}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 49.5 + level * 1.62 + maglevel * 0.99
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 4000)
condition:setFormula(-0.5, 0, -0.5, 0)
combat:addCondition(condition)  -- slow, chance 0.7

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
