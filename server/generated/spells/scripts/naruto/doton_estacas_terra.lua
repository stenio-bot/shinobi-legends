-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Doton: Estacas de Terra: Estacas de pedra irrompem do chão em cruz, prendendo quem estiver em cima.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_EARTHDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_STONES)
local area = {
	{0, 0, 1, 0, 0},
	{0, 0, 1, 0, 0},
	{1, 1, 2, 1, 1},
	{0, 0, 1, 0, 0},
	{0, 0, 1, 0, 0}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 37.8 + level * 1.35 + maglevel * 0.9
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 2000)
condition:setFormula(-0.9, 0, -0.9, 0)
combat:addCondition(condition)  -- paralyze, chance 0.4

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
