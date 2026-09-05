-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/scripts/naruto/achievements.lua (revscriptsys carrega sozinho).
local killEvent = CreatureEvent("NarutoAchievementKill")
function killEvent.onKill(player, target)
	if not target:isMonster() then return true end
	NarutoAchievements.onKill(player, target:getName())
	return true
end
killEvent:register()

local advanceEvent = CreatureEvent("NarutoAchievementAdvance")
function advanceEvent.onAdvance(player, skill, oldLevel, newLevel)
	if skill == SKILL_LEVEL then
		NarutoAchievements.onLevelReached(player, newLevel)
	end
	return true
end
advanceEvent:register()

local login = CreatureEvent("NarutoAchievementLogin")
function login.onLogin(player)
	player:registerEvent("NarutoAchievementKill")
	player:registerEvent("NarutoAchievementAdvance")
	NarutoAchievements.pollPlayer(player)
	return true
end
login:register()

-- Sem onEquip/"entrou na zona" genérico no TFS 1.4.2: um GlobalEvent periódico cobre visit_zone
-- e collect_set para todos os jogadores online (NarutoAchievements.pollPlayer). 7s é baixo o
-- bastante pra não demorar perceptivelmente depois de vestir o conjunto/entrar numa zona nova,
-- e alto o bastante pra não pesar com a contagem de jogadores esperada do projeto.
local poll = GlobalEvent("NarutoAchievementPoll")
function poll.onThink(interval, lastExecution)
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
