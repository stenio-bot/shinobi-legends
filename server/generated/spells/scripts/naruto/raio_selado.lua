-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Raio Selado: Um raio fino disparado com precisao cirurgica.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_ENERGYDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 208)
combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, 62)

function onGetFormulaValues(player, level, maglevel)
	local base = 17.3 + level * 0.864 + maglevel * 0.628
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_zap") end
	return combat:execute(creature, variant)
end
