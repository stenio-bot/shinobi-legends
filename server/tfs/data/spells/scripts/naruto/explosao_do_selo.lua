-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

-- Explos\xE3o do Selo: Detona o selo de uma kunai marcada \xE0 dist\xE2ncia, sem precisar estar perto.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 222)
local area = {
	{1, 1, 1},
	{1, 2, 1},
	{1, 1, 1}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 48 + level * 2.4 + maglevel * 1.375
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 1000)
condition:setFormula(-0.9, 0, -0.9, 0)
combat:addCondition(condition)  -- stun, chance 0.4

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_explosion") end
	return combat:execute(creature, variant)
end
