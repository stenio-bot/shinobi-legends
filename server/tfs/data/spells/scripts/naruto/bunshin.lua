-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

-- Bunshin no Jutsu: Cria 2 clones que distraem monstros por 6s.
-- TODO: criar monstro 'Clone' (c\xF3pia do outfit do jogador, 1 HP, some em 6s) e usar creature:addSummon.
function onCastSpell(creature, variant)
	local pos = creature:getPosition()
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(pos, "sfx_poof") end
	pos:sendMagicEffect(223)
	for _, spec in ipairs(Game.getSpectators(pos, false, false, 8, 8, 8, 8)) do
		if spec:isMonster() and spec:getTarget() == creature then
			spec:setTarget(nil)  -- distrai por um instante; o monstro reavalia alvo depois
		end
	end
	return true
end
