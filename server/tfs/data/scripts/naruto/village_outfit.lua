-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/scripts/naruto/village_outfit.lua (revscriptsys carrega sozinho).
-- Na 1ª vez que o jogador loga: libera os outfits escolhíveis da vila (NarutoVillages) e
-- aplica o PERSONAGEM padrão da vila (o primeiro de data/characters.json daquela vila),
-- via NarutoCharacters.apply (definida em scripts/naruto/character_switch.lua), que também
-- aprende os jutsus daquele personagem.
local STORAGE_VILLAGE_OUTFIT = 60000

local ev = CreatureEvent("NarutoVillageOutfit")
function ev.onLogin(player)
	if player:getStorageValue(STORAGE_VILLAGE_OUTFIT) < 1 then
		local village = NarutoVillages[player:getVocation():getId()]
		if village then
			for _, look in ipairs(village.outfits) do
				player:addOutfit(look)
			end
			local defaultChar = NarutoCharacters.byVillage[player:getVocation():getId()]
			defaultChar = defaultChar and defaultChar[1]
			if defaultChar and NarutoCharacters.apply then
				NarutoCharacters.apply(player, defaultChar.looktype, {silent = true, force = true})
			else
				player:setOutfit({lookType = village.default_outfit})
			end
		end
		player:setStorageValue(STORAGE_VILLAGE_OUTFIT, 1)
	end
	return true
end
ev:register()
