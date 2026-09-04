-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/scripts/naruto/village_outfit.lua (revscriptsys carrega sozinho).
-- Na 1ª vez que o jogador loga, aplica o outfit padrão da vila (vocação) e libera os
-- outfits escolhíveis daquela vila (NarutoVillages, definido em data/lib/naruto_villages.lua).
local STORAGE_VILLAGE_OUTFIT = 60000

local ev = CreatureEvent("NarutoVillageOutfit")
function ev.onLogin(player)
	if player:getStorageValue(STORAGE_VILLAGE_OUTFIT) < 1 then
		local village = NarutoVillages[player:getVocation():getId()]
		if village then
			player:setOutfit({lookType = village.default_outfit})
			for _, look in ipairs(village.outfits) do
				player:addOutfit(look)
			end
		end
		player:setStorageValue(STORAGE_VILLAGE_OUTFIT, 1)
	end
	return true
end
ev:register()
