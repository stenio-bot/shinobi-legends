# tools/balance/sim.py — simulador de balanceamento PvM

Python puro, sem depender do servidor TFS rodando. Reproduz as fórmulas REAIS do
The Forgotten Server 1.4.2 (citadas com arquivo:linha de `server/tfs/src/` nos comentários
do próprio `sim.py`) para dano de arma, dano de jutsu, mitigação por armadura/defesa, regen
de HP/chakra, e as taxas de `server/tfs/config.lua` (rateExp, rateSkill, rateMagic, rateLoot).

## Uso

```bash
# uma simulação (Monte Carlo) de um nível x monstro x build
python3 tools/balance/sim.py --level 25 --monster boss_white_serpent --build ninjutsu -v

# matriz completa (todos os MATRIX_LEVELS x todos os monstros x 2 builds), ~30s
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json

# mais trials por ponto (mais lento, menos ruído)
python3 tools/balance/sim.py --matrix --trials 100 --json /tmp/matrix.json
```

Saída de cada simulação (`simulate()`): `ttk_s_mean`/`ttk_s_p10` (tempo até matar, só contando
tentativas que terminam em morte do monstro), `dmg_taken_mean`, `death_rate`, `chakra_spent_mean`,
`potions_per_kill`, `xp_per_hour`, `ryo_per_hour` (líquido, já descontando poções compradas),
`ryo_per_hour_gross`, `loot_value_per_kill`.

`--matrix` roda os níveis `[1,3,5,8,10,12,15,20,25,30,40,50,60,70,80,90,100]` x todos os
monstros de `data/monsters/*.json` x builds `taijutsu`/`ninjutsu` (30 trials cada por padrão,
ajustável com `--trials`) — **~30s no total**, dentro do orçamento de 60s pedido.

## O que é fórmula real do TFS (com fonte) e o que é premissa do simulador

**Fórmulas reais (não inventadas — cada uma tem a linha do `server/tfs/src/*.cpp` citada no
código):**
- Dano de arma do player: `weapons.cpp:135 Weapons::getMaxWeaponDamage` +
  `normal_random(min,max)` (`tools.cpp:299`, `Normal(0.5,0.25)` clipada).
- Dano de jutsu: `onGetFormulaValues(player, level, maglevel)` gerado por
  `tools/export_tfs.py`, mesma distribuição `normal_random`.
- Mitigação (armadura/"defesa" do alvo): `creature.cpp:818 Creature::blockHit` — reduz por
  `uniform(D/2, D)` (defesa/shield) e depois por `uniform(A/2, A-(A%2+1))` (armadura). Ataques
  `melee` do monstro e do player são físicos e sofrem os dois; ataques elementais (`projectile`/
  `area` do monstro, todo jutsu) **ignoram armadura** (`monsters.cpp`: só o tipo `melee` seta
  `COMBAT_PARAM_BLOCKARMOR`).
- Multiplicador elemental: `tools/export_tfs.py element_percents()` — o elemento anterior no
  ciclo (`data/elements.json`: katon→fuuton→raiton→doton→suiton→katon) causa 150%, o seguinte
  causa 75%.
- Regen de HP/chakra: `player.cpp:4602 updateRegeneration`, valores de `vocations.xml` gerado
  (2 HP/5s, 3 chakra/5s, iguais em todas as vilas).
- Progressão de skill/magic level: `vocation.cpp:141 getReqSkillTries` /
  `vocation.cpp:149 getReqMana`, com `rateSkill`/`rateMagic` de `config.lua` aplicados em
  `data/events/scripts/player.lua:onGainSkillTries`.
- XP por kill: `monster.xp * rateExp` (ou o multiplicador do stage ativo — ver "Achado" abaixo).

**Premissas do simulador (documentadas, NÃO vêm de nenhum arquivo do jogo — são o "jogador
médio" pedido na missão de balanceamento):**
- `COMBAT_UPTIME = 0.55`: fração do tempo jogado realmente trocando golpes (resto é andar,
  lootar, etc.).
- `DOWNTIME_BETWEEN_KILLS_S = 3.0`: tempo entre uma morte e o próximo ataque.
- `SKILL_POINT_MELEE`/`SKILL_POINT_RANGED`: pontos de skill por acerto (`weapons.cpp:548`/`856`).
- Skill "típico" no nível L: tries acumuladas = horas jogadas até esse nível (interpolado da
  tabela de `docs/sistemas/progressao-jogador.md`) x cadência de ataque x pontos/ataque x
  `rateSkill`/`rateMagic`, invertido pela fórmula real de `getReqSkillTries`/`getReqMana`.
- O simulador assume que o jogador **usa poção de vida** (a melhor disponível pro nível) quando
  a vida cai abaixo de 35% — sem isso, TODO boss aparece como "mata o jogador 100% das vezes",
  o que é um falso positivo: bosses deste jogo são encontros de poucas horas de respawn,
  pensados para gastar poção, não para serem vencidos "a seco".
- `ryo/h` líquido desconta o preço das poções realmente bebidas na simulação.
- Rotação de ninjutsu: escolhe o elemento com vantagem sobre o monstro (se houver) e, dentro
  dos 4 jutsus daquele set, o de maior dano-por-segundo já desbloqueado no nível atual — **em
  combate 1x1 isso quase sempre escolhe o projétil tier 1** (cooldown curto amortiza melhor
  que jutsus de área/beam num único alvo); a simulação portanto **não mede o valor de jutsus
  de área contra múltiplos alvos**, só single-target.

Essas premissas foram calibradas checando a ORDEM DE GRANDEZA do XP/h contra
`docs/sistemas/progressao-jogador.md`, não um valor exato — o simulador mede eficiência de
caça "pura" (sem viagem, sem concorrência por spawn, sem missão), que é estruturalmente MAIOR
que o XP/h "misto" documentado (que inclui viagem/missão/mortes/bosses de cooldown longo
amortizados). Use os números do simulador para comparação RELATIVA (monstro A vs B no mesmo
nível, build A vs B no mesmo monstro, "esse TTK é razoável?", "esse death_rate é seguro?"),
não como validação numérica direta da tabela de horas do doc.

## Achados desta sessão de balanceamento (setembro de 2026) que motivaram os 3 fixes abaixo

1. **`server/tfs/config.lua`**: `experienceStages` estava definido com multiplicadores
   7x/6x/5x/4x/3x por faixa de nível — e embora `data/XML/stages.xml` tenha
   `<config enabled="0"/>` (parecendo "desligado"), `ConfigManager::loadXMLStages()`
   (`configmanager.cpp:107-121`) devolve `{}` quando vê esse `enabled="0"`, e o código então
   CAI para `loadLuaStages()` (`configmanager.cpp:278-283`), que lê exatamente essa tabela do
   `config.lua` — ou seja, as stages **sempre estiveram ativas de verdade**. Isso multiplicava
   a XP recebida por 5-7x em relação ao que `docs/sistemas/balanceamento.md` (seção 2, tabela
   "kills por level") e `docs/sistemas/progressao-jogador.md` documentam — ambos foram
   calibrados usando XP CRUA do monstro, sem NENHUM multiplicador (confirmado batendo várias
   linhas da tabela: bandido L5 → 600 XP para subir / 60 XP do bandido = 10 kills, exatamente
   o "bandido L5 = 10 kills" do doc). Fix: `experienceStages = nil` (a forma documentada no
   próprio arquivo de desligar stages) + `rateExp = 1`.
2. **`tools/export_tfs.py`, gerador de `vocations.xml`**: o multiplicador de skill de
   taijutsu/shuriken/genjutsu/defesa era 1.5-2.0 (um template genérico de vocação de TFS,
   nunca calibrado pra este jogo), contradizendo `data/skills.json`
   (`"tries_formula": "50 * 1.1^(skill - 10)"`). Com mult=2.0 a skill taijutsu ficava travada
   em ~17-25 do nível 5 ao 100 inteiro — o simulador mostrou que isso deixava um personagem de
   taijutsu puro (sem jutsu) com **~100% de taxa de morte contra monstros do próprio nível a
   partir do nível 5**, porque `weapons.cpp:135` depende de `skill/4+1`, que ficava baixo
   demais. Fix: multiplicador uniforme 1.1 (bate com `data/skills.json`).
3. **`tools/export_tfs.py`, mesma seção**: `manamultiplier` (magic level = skill "ninjutsu")
   era 4.0 (padrão de vocação de mago do Tibia clássico). Combinado com a fórmula real
   `getReqMana(ML) = 1600*mult^(ML-1)` (`vocation.cpp:149`, a constante 1600 é fixa no C++,
   não editável via XML), isso deixava o magic level em single-digit o jogo inteiro,
   contribuindo para jutsus tier 2/3 perderem em DPS sustentado para taijutsu já por volta do
   nível 15-20. Fix: `manamultiplier = 1.3` (ainda propositalmente alto — dado o limite do
   1600 fixo, não dá pra igualar de vez a curva de taijutsu sem editar o C++; ver pendências).

Os 3 fixes viram tanto **config.lua** (roda o servidor, não é gerado nem `server/tfs/data/`)
quanto **tools/export_tfs.py** (o script gerador, não o XML gerado) — nenhum arquivo dentro de
`server/generated/` ou `server/tfs/data/` foi editado à mão, como manda `CLAUDE.md`. Rode
`tools/export_tfs.py` de novo para os fixes 2 e 3 chegarem no `server/generated/XML/vocations.xml`
(já feito nesta sessão; a instalação em `server/tfs/data/` fica pra quem administra o servidor
em execução, por instrução explícita desta sessão).

## Pendências (não corrigidas nesta sessão, ver relatório)

- `tools/export_tfs.py`, função `items_xml()`: o dicionário que traduz `bonuses` do JSON para
  atributos do `items.xml` não reconhece as chaves `attack` nem `defense` — dois itens
  (`ring_stone_will`, `strings_of_the_puppeteer`) têm bônus dessas chaves que são silenciosamente
  descartados na exportação (o item não erra, só não dá o bônus prometido no jogo real).
- O magic level real fica preso a um teto baixo por causa do `1600` fixo em
  `vocation.cpp:149 Vocation::getReqMana` — só dá pra destravar de verdade editando o C++
  (fora do escopo desta sessão de dados/config).
- A rotação ótima de ninjutsu 1x1 sempre prefere o jutsu de cooldown mais curto (tier 1); o
  valor de jutsus de área/beam contra grupos não é medido por este simulador.
