-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Katon: Grande Bola de Fogo: Dispara uma bola de fogo que explode no impacto.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_FIREDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 200)
combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, 60)

function onGetFormulaValues(player, level, maglevel)
	local base = 8.75 + level * 0.42 + maglevel * 0.28
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_FIRE)
condition:setParameter(CONDITION_PARAM_DELAYED, 1)
condition:addDamage(4, 1000, -3)
combat:addCondition(condition)  -- chance 0.3: TODO aplicar chance via callback

function onCastSpell(creature, variant)
	NarutoJson.broadcastSfx(creature:getPosition(), "sfx_fire_whoosh")
	return combat:execute(creature, variant)
end
