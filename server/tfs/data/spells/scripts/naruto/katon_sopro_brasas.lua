-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Katon: Sopro de Brasas: Um sopro curto de brasas que cobre os tiles imediatamente à frente.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_FIREDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 202)
local area = {
	{1, 1, 1},
	{0, 1, 0},
	{0, 2, 0}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 5.6 + level * 0.315 + maglevel * 0.21
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_FIRE)
condition:setParameter(CONDITION_PARAM_DELAYED, 1)
condition:addDamage(4, 1000, -3)
combat:addCondition(condition)  -- chance 0.35: TODO aplicar chance via callback

function onCastSpell(creature, variant)
	NarutoJson.broadcastSfx(creature:getPosition(), "sfx_fire_puff")
	return combat:execute(creature, variant)
end
