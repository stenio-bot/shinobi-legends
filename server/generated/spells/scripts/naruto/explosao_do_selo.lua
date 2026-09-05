-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Explosão do Selo: Detona o selo de uma kunai marcada à distância, sem precisar estar perto.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_HITAREA)
local area = {
	{1, 1, 1},
	{1, 2, 1},
	{1, 1, 1}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 48 + level * 1.6 + maglevel * 1.1
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 1000)
condition:setFormula(-0.9, 0, -0.9, 0)
combat:addCondition(condition)  -- stun, chance 0.4

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
