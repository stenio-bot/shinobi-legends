-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Coloque em data/scripts/naruto/boss_phases.lua
local PHASES = {
	['Chefe dos Bandidos'] = {
		{hp = 50, mult = 1.0, message = 'Venham, seus inúteis!', summons = {{name = 'Bandido', count = 3}}},
		{hp = 20, mult = 1.5, message = 'Não vou cair para um genin!', summons = {}},
	},
	['Oni Ancestral'] = {
		{hp = 70, mult = 1.0, message = 'O céu é meu. Desçam com ele.', summons = {{name = 'Águia do Trovão', count = 3}}},
		{hp = 40, mult = 1.0, message = 'Meus irmãos ainda respiram sob o gelo!', summons = {{name = 'Oni da Geleira', count = 2}}},
		{hp = 15, mult = 1.7, message = 'Que a montanha caia junto comigo!', summons = {{name = 'Monge da Tempestade', count = 2}}},
	},
	['Marionetista das Ruínas'] = {
		{hp = 70, mult = 1.0, message = 'Vocês vieram brincar com meus bonecos?', summons = {{name = 'Marionete de Combate', count = 2}}},
		{hp = 40, mult = 1.0, message = 'A sentinela acorda. Corram.', summons = {{name = 'Sentinela de Pedra', count = 1}, {name = 'Marionete de Combate', count = 2}}},
		{hp = 15, mult = 1.5, message = 'Então eu mesmo corto os fios!', summons = {}},
	},
	['Sapo Ancião'] = {
		{hp = 60, mult = 1.0, message = 'Meus filhos, devorem o intruso!', summons = {{name = 'Sapo Gigante', count = 2}}},
		{hp = 30, mult = 1.6, message = 'O pântano inteiro se levanta contra você!', summons = {{name = 'Sanguessuga Gigante', count = 3}}},
	},
}

local fired = {}  -- monsterId -> índice da última fase disparada
local ev = CreatureEvent("NarutoBossPhases")
function ev.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)
	local list = PHASES[creature:getName()]
	if not list then return primaryDamage, primaryType, secondaryDamage, secondaryType end
	local id = creature:getId()
	local pct = (creature:getHealth() - primaryDamage) * 100 / creature:getMaxHealth()
	local idx = fired[id] or 0
	while idx < #list and pct <= list[idx + 1].hp do
		idx = idx + 1
		local ph = list[idx]
		if ph.message ~= '' then creature:say(ph.message, TALKTYPE_MONSTER_YELL) end
		for _, s in ipairs(ph.summons) do
			for _ = 1, s.count do
				local pos = creature:getPosition()
				pos.x = pos.x + math.random(-2, 2); pos.y = pos.y + math.random(-2, 2)
				local mon = Game.createMonster(s.name, pos, false, true)
				if mon and attacker then mon:setTarget(attacker) end
			end
		end
		if ph.mult > 1.0 then
			-- TFS não permite mudar o dano do monstro em runtime; aproximação: cura + registra para uso futuro
			NarutoBossMult = NarutoBossMult or {}
			NarutoBossMult[id] = ph.mult
			creature:getPosition():sendMagicEffect(CONST_ME_MAGIC_RED)
		end
	end
	fired[id] = idx
	return primaryDamage, primaryType, secondaryDamage, secondaryType
end
ev:register()

local reset = CreatureEvent("NarutoBossReset")
function reset.onDeath(creature) fired[creature:getId()] = nil return true end
reset:register()

