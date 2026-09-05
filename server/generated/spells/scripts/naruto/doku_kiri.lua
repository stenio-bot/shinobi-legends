-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Doku: Névoa Venenosa: Exala uma névoa roxa ao redor do conjurador; quem respira sai envenenado.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_HITAREA)
local area = {
	{1, 1, 1, 1, 1},
	{1, 1, 1, 1, 1},
	{1, 1, 2, 1, 1},
	{1, 1, 1, 1, 1},
	{1, 1, 1, 1, 1}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 36 + level * 2.1 + maglevel * 1.25
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_POISON)
condition:setParameter(CONDITION_PARAM_DELAYED, 1)
condition:addDamage(10, 1000, -6)
combat:addCondition(condition)  -- chance 0.85: TODO aplicar chance via callback

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
