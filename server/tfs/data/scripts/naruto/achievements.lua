-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/scripts/naruto/achievements.lua (revscriptsys carrega sozinho).
-- `if not NarutoAchievements then return true end` em TODO gancho (achado real ao testar
-- audio, docs/sistemas/audio.md): data/lib/naruto_achievements.lua so entra em memoria com
-- REINICIO do servidor (dofile em data/lib/lib.lua, so roda no boot - nenhum /reload toca
-- libs); esta script (revscriptsys) j\xE1 recarrega com /reload scripts|all. Sem a blindagem,
-- um servidor que j\xE1 tinha os HOOKS mas ainda nao tinha a LIB (ex.: logo apos um /reload sem
-- reiniciar) derrubava o onLogin de todo mundo com "attempt to index global
-- 'NarutoAchievements' (a nil value)".
local killEvent = CreatureEvent("NarutoAchievementKill")
function killEvent.onKill(player, target)
	if not NarutoAchievements then return true end
	if not target:isMonster() then return true end
	-- a.monsterName (naruto_achievements.lua, kill_specific) e' cp1252 gerado; getName() do TFS
	-- e' UTF-8 -- converte antes (mesma regra de quests_kill.lua/tasks.lua/dailies.lua).
	NarutoAchievements.onKill(player, NarutoText.utf8ToCp1252(target:getName()))
	return true
end
killEvent:register()

local advanceEvent = CreatureEvent("NarutoAchievementAdvance")
function advanceEvent.onAdvance(player, skill, oldLevel, newLevel)
	if NarutoAchievements and skill == SKILL_LEVEL then
		NarutoAchievements.onLevelReached(player, newLevel)
	end
	return true
end
advanceEvent:register()

local login = CreatureEvent("NarutoAchievementLogin")
function login.onLogin(player)
	player:registerEvent("NarutoAchievementKill")
	player:registerEvent("NarutoAchievementAdvance")
	if NarutoAchievements then NarutoAchievements.pollPlayer(player) end
	return true
end
login:register()

-- Sem onEquip/"entrou na zona" gen\xE9rico no TFS 1.4.2: um GlobalEvent peri\xF3dico cobre visit_zone
-- e collect_set para todos os jogadores online (NarutoAchievements.pollPlayer). 7s \xE9 baixo o
-- bastante pra n\xE3o demorar perceptivelmente depois de vestir o conjunto/entrar numa zona nova,
-- e alto o bastante pra n\xE3o pesar com a contagem de jogadores esperada do projeto.
local poll = GlobalEvent("NarutoAchievementPoll")
function poll.onThink(interval, lastExecution)
	if not NarutoAchievements then return true end
	for _, player in ipairs(Game.getPlayers()) do
		NarutoAchievements.pollPlayer(player)
	end
	return true
end
poll:interval(7000)
poll:register()

--- !conquistas: resumo (desbloqueadas/total) por categoria no chat.
local talk = TalkAction("!conquistas")
function talk.onSay(player, words, param)
	if not NarutoAchievements then
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Conquistas ainda n\xE3o carregadas neste servidor (precisa reiniciar).")
		return false
	end
	local total, unlocked = #NarutoAchievements.list, 0
	local byCat, catOrder = {}, {}
	for _, a in ipairs(NarutoAchievements.list) do
		local done = NarutoAchievements.isUnlocked(player, a)
		if done then unlocked = unlocked + 1 end
		if not byCat[a.category] then
			byCat[a.category] = {0, 0}
			catOrder[#catOrder + 1] = a.category
		end
		byCat[a.category][2] = byCat[a.category][2] + 1
		if done then byCat[a.category][1] = byCat[a.category][1] + 1 end
	end
	local parts = {"Conquistas: " .. unlocked .. "/" .. total}
	for _, cat in ipairs(catOrder) do
		parts[#parts + 1] = cat .. " " .. byCat[cat][1] .. "/" .. byCat[cat][2]
	end
	player:sendTextMessage(MESSAGE_INFO_DESCR, table.concat(parts, " | "))
	return false
end
talk:separator(" ")
talk:register()
