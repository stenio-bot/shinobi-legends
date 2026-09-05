-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Suiton: Névoa Cortante: Gotículas afiadas suspensas no ar cortam quem estiver à frente.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_ICEDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_ICEATTACK)
local area = {
	{1, 1, 1},
	{0, 1, 0},
	{0, 2, 0}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 5.25 + level * 0.315 + maglevel * 0.227
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 3000)
condition:setFormula(-0.3, 0, -0.3, 0)
combat:addCondition(condition)  -- slow, chance 0.35

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
