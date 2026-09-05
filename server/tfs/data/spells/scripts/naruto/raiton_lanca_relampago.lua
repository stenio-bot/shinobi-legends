-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Raiton: Lança do Relâmpago: Um raio contínuo perfura em linha reta e atravessa vários inimigos.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_ENERGYDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_ENERGYHIT)
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
	local base = 39.6 + level * 1.35 + maglevel * 0.99
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 1500)
condition:setFormula(-0.9, 0, -0.9, 0)
combat:addCondition(condition)  -- paralyze, chance 0.35

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
