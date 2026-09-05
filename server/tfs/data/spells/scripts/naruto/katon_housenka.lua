-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Katon: Flores de Fênix: Vários projéteis de fogo em cone à frente.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_FIREDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 202)
local area = {
	{1, 1, 1, 1, 1},
	{0, 1, 1, 1, 0},
	{0, 0, 1, 0, 0},
	{0, 0, 2, 0, 0}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 16.2 + level * 2.07 + maglevel * 0.63
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_FIRE)
condition:setParameter(CONDITION_PARAM_DELAYED, 1)
condition:addDamage(5, 1000, -4)
combat:addCondition(condition)  -- chance 0.5: TODO aplicar chance via callback

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_fire_burst") end
	return combat:execute(creature, variant)
end
