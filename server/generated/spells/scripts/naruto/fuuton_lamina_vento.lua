-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Fuuton: Lâmina de Vento: Uma lâmina de ar comprimido cortando em linha reta até o alvo.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_HOLYDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 216)
combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, 64)

function onGetFormulaValues(player, level, maglevel)
	local base = 8.05 + level * 0.385 + maglevel * 0.297
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
