-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

-- Raiton: Corrente Est\xE1tica: A eletricidade salta em cruz pelo ch\xE3o a partir do conjurador, prendendo quem tocar.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_ENERGYDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 209)
local area = {
	{0, 0, 1, 0, 0},
	{0, 0, 1, 0, 0},
	{1, 1, 2, 1, 1},
	{0, 0, 1, 0, 0},
	{0, 0, 1, 0, 0}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 4.9 + level * 0.315 + maglevel * 0.245
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 2000)
condition:setFormula(-0.9, 0, -0.9, 0)
combat:addCondition(condition)  -- paralyze, chance 0.5

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_zap") end
	return combat:execute(creature, variant)
end
