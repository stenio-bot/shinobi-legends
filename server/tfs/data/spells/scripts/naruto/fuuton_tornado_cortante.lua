-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

-- Fuuton: Tornado Cortante: Uma coluna de vento afiado que avan\xE7a em linha reta, despeda\xE7ando tudo no caminho.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_HOLYDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 217)
local area = {
	{1},
	{1},
	{1},
	{1},
	{1},
	{1},
	{2}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 21.06 + level * 4.212 + maglevel * 0.03367
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 4000)
condition:setFormula(-0.4, 0, -0.4, 0)
combat:addCondition(condition)  -- slow, chance 0.6

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_wind_roar") end
	return combat:execute(creature, variant)
end
