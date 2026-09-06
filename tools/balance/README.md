# tools/balance/sim.py — simulador de balanceamento PvM

Python puro, sem depender do servidor TFS rodando. Reproduz as fórmulas REAIS do
The Forgotten Server 1.4.2 (citadas com arquivo:linha de `server/tfs/src/` nos comentários
do próprio `sim.py`) para dano de arma, dano de jutsu, mitigação por armadura/defesa, regen
de HP/chakra, e as taxas de `server/tfs/config.lua` (rateExp, rateSkill, rateMagic, rateLoot).

## Uso

```bash
# uma simulação (Monte Carlo) de um nível x monstro x build (builds: taijutsu/ninjutsu/hybrid/shuriken)
python3 tools/balance/sim.py --level 25 --monster boss_white_serpent --build ninjutsu -v

# multi-alvo: mesmo nível x monstro, N cópias do monstro (pull)
python3 tools/balance/sim.py --level 44 --monster curse_shaman --n-monsters 2 --build ninjutsu

# diagnóstico (rodada 3): força a build ninjutsu a NUNCA desistir do jutsu (mesmo quando ele
# faz menos dano/s que a arma) — mede a curva PURA de jutsu, não a decisão racional de fallback.
# Só vale pra --level/--monster (1x1); --matrix/--group-matrix continuam com fallback racional.
python3 tools/balance/sim.py --level 60 --monster boss_ancestral_oni --build ninjutsu --no-fallback

# matriz completa 1x1 (todos os MATRIX_LEVELS x todos os monstros x 3 builds), ~60s
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json

# matriz multi-alvo: pull por região (GROUP_SCENARIOS) + boss 1x1 lado a lado, ~1.5s
python3 tools/balance/sim.py --group-matrix --json /tmp/group.json

# mais trials por ponto (mais lento, menos ruído)
python3 tools/balance/sim.py --matrix --trials 100 --json /tmp/matrix.json

# rodada 4: cenário de "hunt de 30 min" (sequência de pulls do monstro comum mais próximo do
# nível, pausas de 5-15s entre lutas) — mede chakra sustentável de verdade, não numa luta só.
# Sozinho roda HUNT_LEVELS (rodada 5: de 5 em 5, L5-L100, 20 pontos) x build hybrid, com e sem
# pílula de chakra. RODADA 7: por padrão conjura sempre o tier 1 (force_tier1=True, ver seção
# "Achados da rodada 7" — sem isso, o jutsu real conjurado vira tier 2/3 a partir de L12-26 e a
# métrica de chakra do tier 1 passa a medir o custo de um jutsu que não é mais usado).
python3 tools/balance/sim.py --hunt --json /tmp/hunt.json

# rodada 7: --no-force-tier1 volta ao comportamento das rodadas 4-6 (mede "tempo sem chakra pra
# QUALQUER coisa do kit elemental", não especificamente o tier 1). RODADA 8: --no-force-tier1 só
# tem efeito sobre o build ninjutsu puro — o build hybrid (padrão de `--hunt`) SEMPRE conjura o
# tier 1 agora (ver "Build hybrid" acima), então --hunt e --hunt --no-force-tier1 dão o MESMO
# resultado pra hybrid; a flag só muda a leitura do ninjutsu puro (diagnóstico da rodada 7 §5).
python3 tools/balance/sim.py --hunt --no-force-tier1 --json /tmp/hunt_kitwide.json

# hunt pontual (nível/monstro/build escolhidos), com pílula de chakra ligada
python3 tools/balance/sim.py --hunt --level 15 --monster mist_scout --build hybrid --chakra-pills --minutes 30

# --chakra-pills também funciona em --level/--monster sem --hunt (luta única)
python3 tools/balance/sim.py --level 60 --monster boss_ancestral_oni --build hybrid --chakra-pills
```

`simulate_hunt()`/o resultado de `--hunt` também trazem duas métricas ANALÍTICAS novas da
rodada 7 (não precisam do Monte Carlo, são conta fechada a partir do nível/jutsu):
`casts_per_full_pool` (quantos casts seguidos o pool CHEIO aguenta, sem regen — pior caso) e
`time_to_full_pool_s` (segundos parado, sem gastar, até o pool voltar a encher do zero).

Saída de cada simulação (`simulate()`): `ttk_s_mean`/`ttk_s_p10` (tempo até matar, só contando
tentativas que terminam em morte do monstro), `dmg_taken_mean`, `death_rate`, `chakra_spent_mean`,
`chakra_efficiency` (dano de jutsu / chakra gasto), `jutsu_dps_pure_mean` (rodada 3: dano feito
só via jutsu / duração da luta, por tentativa vitoriosa — a métrica "DPS só de jutsus" pedida na
missão da rodada 3; combine com `--no-fallback` pra medir a curva pura sem a build desistir do
jutsu no meio da conta), `potions_per_kill`, `xp_per_hour`,
`ryo_per_hour` (líquido, já descontando poções compradas), `ryo_per_hour_gross`,
`loot_value_per_kill`. `simulate_group()` (usado por `--group-matrix` e por `--n-monsters`>1)
troca `ttk_s_mean` por `clear_s_mean` (tempo até zerar TODOS os N monstros), acrescenta
`oom_s_mean` (instante em que o chakra deixou de bastar pra qualquer jutsu do kit, `None` se
nunca faltou) e `dmg_by_jutsu` (dano total por jutsu — usado pra achar jutsu inútil/dominante,
ver relatório v2 §5).

`--matrix` roda os níveis `[1,3,5,8,10,12,15,20,25,30,40,50,60,70,80,90,100]` x todos os
monstros de `data/monsters/*.json` x builds `taijutsu`/`ninjutsu`/`hybrid` (30 trials cada por
padrão, ajustável com `--trials`) — **~57s no total** (3 builds desde a rodada 2, antes eram 2
e ~30s), dentro do orçamento de 120s pedido. `--group-matrix` roda `GROUP_SCENARIOS` (pull por
região, N por monstro — ver relatório v2 §1) + os mesmos 6 bosses em 1x1 lado a lado, **~1.5s**.

### Build "hybrid" (rodada 2)

Metade do tempo de treino de combate em taijutsu, metade em ninjutsu (`typical_skills_split`,
`HYBRID_TAIJUTSU_FRAC`/`HYBRID_NINJUTSU_FRAC` — **0.4/0.4 desde a rodada 4**, ver nota abaixo,
não mais o 0.5/0.5 original) — não é a média dos dois builds
"pura-raça", é um personagem que de fato joga assim: as duas skills ficam mais baixas que um
especialista em qualquer uma das trilhas, mas com acesso pleno a ambas. Meta da missão: "híbrido
perto do melhor" — ver relatório v2 §3 pros números reais (fica 6,6%–19,9% atrás do melhor build
em cada boss, mediana ~13%).

**Atualizado na rodada 4**: arma e jutsu passaram a rodar em cadências independentes (`interleave`
em `simulate_fight`/`simulate_hunt`) — o híbrido ataca com a arma no intervalo normal E lança o
jutsu por cima sempre que pronto/pagável, virando sistematicamente ≥ os builds puros.

**Atualizado na rodada 6**: isso passou a exceder o teto de +15% em 4-5 dos 6 bosses de
referência (nenhuma jutsu por jutsu fechava — a rotação sempre migra pro próximo candidato do
kit assim que o atual é nerfado). Fix: `HYBRID_JUTSU_CADENCE_FRAC=0,22` (novo) estica o
cooldown EFETIVO do jutsu só pro build híbrido (`cooldown_s / HYBRID_JUTSU_CADENCE_FRAC`, ~4,5×
mais devagar) — modela que um jogador dividindo atenção entre arma e jutsu não aproveita toda
janela de cast livre entre golpes (cabem 4-5 golpes de arma no cooldown de 9,0s do tier 1). O
ninjutsu PURO não usa esse parâmetro (não é `interleave`). Ver relatório v6 §1.

**Substituído na rodada 8**: `HYBRID_JUTSU_CADENCE_FRAC` foi REMOVIDA — a rodada 7 mediu que ela
deixava o cast de jutsu tão raro que nenhum custo criava scarcity real numa hunt de 30 min (ver
achado abaixo). Modelo novo: o híbrido não passa mais por `pick_ninjutsu_jutsu`; sempre conjura o
**tier 1** do elemento com vantagem (`advantage_element()`), no cooldown **real** (sem
esticamento). Isso deixou o híbrido forte demais contra boss no cooldown original de 9,0s
(até -44% de TTK vs. melhor puro) — o cooldown dos 5 tier 1 subiu para **27,0s** (custo
percentual do pool inalterado, pra não quebrar "Genin L1 6-8 casts/pool") pra fechar o teto de
+15% de novo. Ver relatório v8 §2.

**Revertido na rodada 9 (decisão do orquestrador, mudança de FILOSOFIA)**: o cooldown de 27,0s
foi rejeitado ("um jutsu por meio minuto destrói a sensação de ninja") e voltou a **9,0s** — e
o teto "híbrido ≤+15%" que motivou tanto `HYBRID_JUTSU_CADENCE_FRAC` (rodada 6) quanto o
cooldown de 27,0s (rodada 8) foi **removido de vez**. O híbrido passa a ser o build de
**referência** do jogo (não mais algo a conter); a única meta sobre os builds puros agora é
viabilidade (≥70% do DPS híbrido em todo nível 5-100, ≥60% nos 6 bosses) — ver "Achados da
rodada 9" abaixo pro que isso abriu (ninjutsu excedendo o híbrido em 2 pontos, corrigido) e pro
que ainda não fecha (viabilidade dos puros abaixo de L78, tensão estrutural real com o burst).

### Cenário multi-alvo (rodada 2)

`simulate_group_fight`/`simulate_group` simulam um pull de N cópias do mesmo monstro comum:
geometria simplificada (alvos "adjacentes/em linha" — área/beam sempre atinge
`min(N, area_capacity(shape))`, onde `area_capacity` espelha exatamente
`tools/export_tfs.py:183 area_matrix()`), chakra finito com regen real, rotação que escolhe a
cada ação o jutsu PRONTO (cooldown) E PAGÁVEL (chakra) do kit elemental com maior
`(dano×hits)/cooldown`, e taijutsu como filler sem custo de chakra quando nenhum jutsu do kit
está disponível. `GROUP_SCENARIOS` define, por região, os monstros comuns + boss e o **N por
monstro** (não por região — ver relatório v2 §1, isso mudou numa correção da própria rodada 2)
medido por clustering real (união de spawns da mesma espécie a ≤10 tiles em
`data/maps/forest_valley.json`, via union-find) nas 4 regiões que já têm mapa jogável; as 2
regiões sem mapa físico ainda (`costa_das_mares`, `covil_da_nuvem_vermelha`) usam um placeholder
conservador N=2, sinalizado no próprio código como não-medido.

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
- Regen de HP/chakra: `player.cpp:4602 updateRegeneration`. Até a rodada 4, valores fixos de
  `vocations.xml` (2 HP/5s, 3 chakra/5s, iguais em todas as vilas). **Rodada 5**: a condição
  aplicada no login/level-up (`server/tfs/data/scripts/naruto/character_switch.lua`,
  `NarutoRegen.apply`, subId 9020) não vem mais da vocação — é recalculada em Lua por level:
  chakra `3 + floor(level/4)` a cada 2s, HP `2 + floor(level/10)` a cada 5s (replicado em
  `chakra_regen_amount_per_tick`/`hp_regen_amount_per_tick` deste arquivo). Ver relatório v5 §1.
- Custo de jutsu como % do chakra máximo (`manapercent`): `spells.cpp:466` (lê o atributo),
  `spells.cpp:804 Spell::getManaCost` (`mana` tem prioridade se != 0, senão
  `(maxMana*manaPercent)/100`, divisão inteira). **Novo na rodada 5** — só os 5 projéteis tier 1
  elementais usam isso (`chakra_cost_percent` no JSON); replicado em `jutsu_chakra_cost()`.
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
- Rotação de ninjutsu 1x1 (`simulate_fight`/`pick_ninjutsu_jutsu`): escolhe o elemento com
  vantagem sobre o monstro (se houver) e, dentro dos jutsus daquele set já desbloqueados, o de
  maior dano-por-segundo — **mas só usa esse jutsu se ele bater o DPS de arma estimado
  (`estimate_weapon_dps`, mitigação incluída)**; senão o build luta 100% taijutsu (FIX rodada 2
  — ver "Achados rodada 2" abaixo). Isso quase sempre escolhe o projétil tier 1 quando algum
  jutsu vale a pena (cooldown curto amortiza melhor que área/beam num único alvo). Rotação de
  grupo (`simulate_group_fight`/`simulate_group`, desde a rodada 2): escolhe a cada ação, entre
  TODOS os jutsus do kit prontos e pagáveis, o de maior `(dano×hits)/cooldown` — é aí que
  jutsus de área/beam (tier 2/3) valem a pena mesmo com dano/cooldown menor que o tier 1, porque
  atingem `min(N, area_capacity(shape))` alvos simultaneamente.

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

## Achados da rodada 2 (setembro de 2026) — ver `docs/sistemas/balanceamento-relatorio-v2.md`

1. **Bug de call site**: `pick_ninjutsu_jutsu` ganhou um parâmetro `taijutsu_dps_est` (só usa o
   jutsu se bater o DPS de arma) numa sessão anterior, mas o call site em `simulate_fight` não
   foi atualizado pra passá-lo — a checagem nunca rodava de verdade no 1×1, e isso sozinho
   explicava boa parte do "ninjutsu perde em luta longa" da rodada 1. Corrigido.
2. **Tuning de tier 1 vs tier 2/3**: `tier1_mult=0.35` (todo tier 1 ofensivo) e
   `tier23_mult=0.9` (todo tier 2/3) em `base_damage`/`level_scale`/`skill_scale`, calibrados a
   partir do baseline original (`git show HEAD:data/jutsus/*.json`, não empilhado em cima de
   edições anteriores) — porque `pick_ninjutsu_jutsu` (1×1) sempre escolhe tier 1 (cooldown
   curto amortiza melhor), então esse é o lever que decide o 1×1; tier 2/3 só importa pra
   grupo (multiplicado por `hits`). Ver relatório v2 §2–§3 pros números completos.
3. **N de `GROUP_SCENARIOS` corrigido por monstro** (clustering real medido em
   `forest_valley.json`, não mais um N por região inteira) — revelou que `curse_shaman` a N=4
   tinha `death_rate` 45-55% (pull que o mapa real não suporta) e que boa parte do "ninjutsu
   domina 300-800%" em `lesser_serpent` vinha de um N=3 sem cluster real (spawns a 12+ tiles um
   do outro). Ver relatório v2 §1.
4. **2 outliers de tuning da sessão anterior corrigidos**: `raiton_lanca_relampago` e
   `suiton_suiryuudan` tinham `level_scale` ×2.025/×1.725 em vez do ×1.5 uniforme dos outros
   tier 2/3 (provável erro de cálculo, não intencional) — quebrava a paridade elemental
   (±10% pedido pela missão). Ver relatório v2 §4.
5. **Item 10 da rodada 1 (`attack`/`defense` de acessório) corrigido** — `items.cpp:22`/`:25`
   confirmam que são atributos genéricos válidos em qualquer item; bastou adicionar as duas
   chaves ao dicionário de `items_xml()`.

## Pendências (não corrigidas nesta sessão, ver relatório v2 §10)

- Boss L19 (Espadachim da Névoa) fica em -13,4% de diferença 1×1 (dentro da meta de ≤15%, mas
  no limite) por causa de um platô de tier de arma entre L15 e L20 em `data/items/*.json` —
  fora do escopo desta sessão (`jutsus/element_sets/characters` só).
- `wolf`/`thunder_eagle` (grupo de 3) ficam abaixo da meta de +30-60%; os 3 cenários de grupo
  válidos (`wolf`, `ruin_puppet`, `thunder_eagle`) respondem de forma não-uniforme ao mesmo
  `tier23_mult` global — não achei um par de multiplicadores que satisfaça 1×1 E grupo
  simultaneamente, e priorizei a meta de 1×1 (item 1 da missão).
- 2 jutsus candidatos a revisão de número (`fuuton_tornado_cortante` perdendo pro próprio tier 2
  do mesmo elemento; `raiton_corrente_estatica`/`suiton_nevoa_cortante` tier 1 de área sem uso
  em nenhum cenário testado) — reportados com evidência, não ajustados.
- O magic level real segue preso a um teto baixo por causa do `1600` fixo em
  `vocation.cpp:149 Vocation::getReqMana`. Avaliei trocar a fórmula gerada
  (`onGetFormulaValues`) pra usar `level` em vez de `maglevel` (tecnicamente trivial, ver
  relatório v2 §8) e decidi **não aplicar** nesta sessão — todo o tuning de tier 1/2/3 foi
  calibrado assumindo o magic level baixo (é o que faz ninjutsu convergir suavemente pra
  taijutsu puro em L50+); trocar a fórmula exigiria recalibrar tudo de novo sem orçamento.
- Costa das Marés e Covil da Nuvem Vermelha não têm mapa físico ainda — N=2 usado no cenário de
  grupo dessas regiões é um placeholder conservador, não medição real.

## Achados da rodada 3 (setembro de 2026) — ver `docs/sistemas/balanceamento-relatorio-v3.md`

Continuação direta da pendência #4 da rodada 2 ("magic level estruturalmente baixo"). A missão
pediu pra diagnosticar com `--no-fallback` (adicionado nesta sessão, ver acima) a curva PURA de
ninjutsu 1×1 de L5 a L100, sem deixar a build desistir do jutsu — e ela realmente degenera:
com o `manamultiplier=1.3` da rodada 1/2, um boss L100 mostrava ninjutsu ~117% MAIS LENTO que
taijutsu no modo puro (contra ~0% no modo com fallback racional, que simplesmente para de usar
jutsu). "Empatar desistindo do jutsu" não é o mesmo que "empatar competindo".

1. **`manamultiplier`: 1.3 → 1.1** (`tools/export_tfs.py`, `tools/balance/sim.py` `MANA_MULT`)
   — igual às outras skills (`data/skills.json`). `getReqMana(ML)=1600*mult^(ML-1)`
   (`vocation.cpp:149`, base 1600 fixo no C++) faz o magic level crescer de ~16 (L15) a ~34
   (L100) com mult=1.3 — quase reto, contra um dano de arma que cresce ~40× no mesmo intervalo
   (`weapons.cpp:135`, depende de skill/4+1 × attack da arma de tier, que sobe em degraus
   grandes a cada tier de `data/items/*.json`). Com mult=1.1, magic level vai de ~23 (L5) a ~83
   (L100) — mesma ordem de grandeza do taijutsu (skill ~40→~101, mesmo mult=1.1 desde a rodada
   1). Essa é a correção estrutural (a) pedida na missão.
2. **Bug encontrado durante a validação**: `_maglevel_from_mana` (linha ~176) tinha um teto de
   iteração `ml > 60` que nunca bindava com o `manamultiplier=1.3` das rodadas 1/2 (magic level
   real ficava em ~34), mas passou a truncar SILENCIOSAMENTE o magic level assim que o
   `manamultiplier` caiu pra 1.1 nesta sessão (o valor real quer chegar a ~83 no L100). Corrigido
   pra `ml > 300` (mesmo espírito do `skill > 200` de `_skill_from_tries`, uma trava de segurança
   que nunca deve bindar de verdade) — sem esse fix, a calibração de tier 2/3 desta sessão teria
   sido feita contra um magic level artificialmente baixo em L60+.
3. **`level_scale`/`skill_scale` de todo jutsu tier 2/3 elemental recalibrado** (correção (b) da
   missão, "aumentar level_scale dos tiers 2/3") em cima do `manamultiplier` novo — tier 2 dos
   elementos que TÊM tier 3 no kit (katon/doton/fuuton) só precisou de um ajuste moderado
   (`level_scale` ×2,07–3,1); os tier 3 (`katon_karyuu_endan`, `doton_colapso_terreno`,
   `fuuton_tornado_cortante`) e o novo tier 3 de raiton (`raiton_punho_trovao`, ver item 4)
   subiram bem mais (`level_scale` ×9,0–11,9) porque são o único lever pra acompanhar o dano de
   arma em L50-100; `suiton_suiryuudan` (tier 2 SEM tier 3 atrás, ver item 4) recebeu uma
   compensação própria maior (`level_scale` ×7,0) pra cobrir sozinho o papel de "teto do
   elemento" que os outros dividem entre tier 2 e tier 3. `chakra_cost` de todos esses jutsus
   subiu ~2,4–3,5× junto — sem isso, o mesmo `level_scale` maior deixava o burst "de graça"
   (dano/chakra alto demais), quebrando a paridade de grupo pra qualquer pull com HP total baixo
   (ver §10). Números completos e o processo de calibração (por que um multiplicador uniforme
   por tier não fecha sozinho — a resposta de cada monstro/elemento à mesma mudança não é
   uniforme) estão no relatório v3 §2-3.
4. **`raiton` ganhou um tier 3 de verdade no kit**: `data/element_sets.json` tinha
   `raiton_armadura_eletrica` (self, `base_damage=0`, nunca é candidato de dano) na 4ª vaga em
   vez de `raiton_punho_trovao` (tier 3, req 30) — um jutsu que já existia em `data/jutsus/
   raiton.json` e já tinha pergaminho mapeado (`scroll_raiton_punho_trovao` em
   `data/tfs_mapping.json`), só nunca tinha sido colocado no kit "livre" do elemento (a
   documentação de `combate-e-jutsus.md` já explicava isso como decisão deliberada — "candidato
   a loot/pergaminho de bônus no futuro" — mas isso deixava raiton SEM NENHUM tier 3 no kit,
   capado no tier 2 igual suiton, sem compensação). Troquei `raiton_armadura_eletrica` por
   `raiton_punho_trovao` no set — `armadura_eletrica` continua um jutsu válido (só fora do kit
   automático agora, igual os outros "sobressalentes" documentados). Isso sozinho consertou boa
   parte da degeneração em bosses de elemento doton (ex.: L82 foi de -35% pra +3% de diferença
   1×1 nos testes intermediários desta sessão — ver relatório v3 §2).
5. **Paridade elemental recalibrada** (meta ±10%): depois do item 3, os 5 elementos ficaram
   entre -30% e +30% de desvio entre si (raiton/fuuton ficaram fortes demais, suiton fraco
   demais) porque cada tier 3/tier 2 "teto" foi calibrado contra um boss DIFERENTE (elemento
   diferente por boss). Um segundo passe de correção por elemento (multiplicador só no jutsu
   "campeão" de cada kit: `katon_karyuu_endan` ×1,14, `fuuton_tornado_cortante` ×0,80,
   `raiton_punho_trovao` ×0,77, `doton_colapso_terreno` ×1,12, `suiton_suiryuudan` ×1,45) trouxe
   os 5 pra dentro de ±3% entre L50 e L100 — bem mais apertado que a meta de ±10%.
6. **2 dos 3 jutsus "nunca escolhidos" da rodada 2 resolvidos**: `fuuton_tornado_cortante`
   (tier 3) virou o pick de verdade em bosses/monstros L54-100 de elemento raiton via número
   (item 3). `raiton_corrente_estatica` e `suiton_nevoa_cortante` (tier 1 de área) mudaram de
   FORMA em vez de número: cooldown cortado quase pela metade (2,5s→1,3s / 3,0s→1,6s, contra
   2,0s do projétil irmão), shape mais largo (`cross_r1`→`cross_r2`, `cone_2`→`cone_3`) e efeito
   de controle bem mais forte (paralyze 20%/1s→50%/2s; slow 35%/3s→60%/5s) — viram a opção de
   controle de área rápida do kit tier 1, não competem em DPS puro por design (mesmo raciocínio
   que a rodada 2 já aplicava a `fuuton_redemoinho_prisao`/`suiton_prisao_agua`).
   `raiton_corrente_estatica` já aparece escolhido em pelo menos 1 cenário de `--group-matrix`
   depois da mudança; `suiton_nevoa_cortante` não tem nenhum monstro de elemento katon no nível
   6-24 nos `GROUP_SCENARIOS` atuais pra exercitar (lacuna de cobertura de cenário, não do
   jutsu — ver relatório v3 §4/§10).
7. **9 personagens recalibrados de novo** (meta ±15%, mesma métrica-proxy da rodada 2): o
   `manamultiplier` mais baixo deixou `doku_kiri` (jutsu neutro usado só por `kunoichi_armas`,
   `skill=ninjutsu`) puxar seu valor pra +22,5% (magic level maior = mais dano de graça sem
   nenhum número seu ter mudado) — nerf de `base_damage`/`level_scale` ×0,55 e `skill_scale`
   ×0,2. O deslocamento também empurrou `sabio_cerimonial` e `genin_laranja` pra fora por baixo
   (a métrica de jutsu utilitário usa a média de dano/chakra de TODOS os jutsus de dano como
   proxy — e essa média subiu com o rebalanceamento de tier 2/3) — buff em `selo_de_exorcismo`/
   `circulo_de_selos` (×1,4) e `fuuton_rasteira_vento` (×1,6), os únicos jutsus não-compartilhados
   desses 2 personagens. Os 9 ficaram entre -8,6% e +10,2% (relatório v3 §7).

## Achados da rodada 4 (setembro de 2026) — ver `docs/sistemas/balanceamento-relatorio-v4.md`

1. **Tensão burst-vs-sustentado da rodada 3 (§8) resolvida via cooldown maior, não mais número
   maior**: com `cooldown_tier1 == ATTACK_INTERVAL_S` (2,0s = 2,0s), burst (≥1,3× o hit de arma)
   e paridade sustentada são matematicamente incompatíveis (relatório v3 provou isso). Com
   `cooldown_tier1 = 3,5s`, os dois lados destravam ao mesmo tempo (relatório v4 §2 tem a
   prova). Os 5 projéteis tier 1 (`katon_goukakyuu`/`fuuton_lamina_vento`/`raiton_hari`/
   `doton_bala_lama`/`suiton_mizudan`) foram recalibrados: cooldown 2,0s→3,5s, `chakra_cost`
   ~2× (12-16→25-30), `base_damage`/`level_scale` bem maiores (`skill_scale` só um pouco — o
   magic level não é confiável o bastante numa faixa tão ampla, nível puro é o lever principal).
   Resultado: burst ≥1,3× fecha de L1 a L30 (era só L1-5); L40+ continua abaixo, mas a distância
   caiu de "5-6× fraco" pra "20-30% fraco" — melhora de ordem de grandeza, não perfeita.
2. **Modelo de híbrido reescrito**: arma e jutsu agora correm em cadências INDEPENDENTES pro
   build `hybrid` (a arma ataca sozinha no intervalo normal, o jutsu lança por cima sempre que
   pronto/pagável) — antes, cast de jutsu bloqueava a arma pelo cooldown INTEIRO (bug real desde
   a rodada 1, só passou a importar quando o cooldown de tier 1 ficou maior que o intervalo de
   ataque). Isso é literalmente o "arma entre casts" pedido na missão. Consequência: o híbrido
   agora usa o jutsu com `no_fallback=True` fixo (é aditivo, não substituto — "só uso se bate a
   arma" não faz sentido quando o jutsu não ocupa o turno da arma), tornando-o sistematicamente
   ≥ os builds puros (nunca mais atrás) — `HYBRID_TAIJUTSU_FRAC`/`HYBRID_NINJUTSU_FRAC` caiu de
   0,5/0,5 pra 0,4/0,4 pra conter o quanto ele passa do melhor build puro (ainda excede o teto de
   +15% em 4 dos 6 bosses testados — pendência, ver abaixo).
3. **Bug do simulador corrigido**: `best_item_for_slot` escolhia o item de MAIOR
   `required_level`, não o de maior `attack`/`defense` — fazia `gloves_taijutsu` (req10, attack
   **14**) "substituir" `tanto_steel` (req8, attack **16**) de L10 a L19, um downgrade
   automático que piorava o platô de arma que deixava o boss L19 fora da meta desde a rodada 2.
4. **Platô de arma L8→L20 corrigido**: item novo `wakizashi_temperado` (req15, attack 21) entre
   `tanto_steel` (req8, 16) e `katana_ronin` (req20, 28) — vendido na região do próprio boss L19
   (Mercador Itsuki, Costa das Marés). O fix de arma sozinho (bug do item 3 + item novo) derrubou
   o desvio do boss L19 de -25,8% (rodada 3) pra -1,2% — quase toda a diferença já era o platô.
5. **`_CHAKRA_POTIONS` finalmente usado em combate** (pendência #5 da rodada 3): `--chakra-pills`
   (1×1) e a nova `simulate_hunt`/`--hunt` (sequência de pulls de 30 min com pausas de 5-15s,
   chakra persistindo com regen contínuo entre lutas) simulam o jogador bebendo a melhor pílula
   desbloqueada quando não consegue pagar o jutsu escolhido.
6. **3 tier 2 do kit automático ganharam cooldown 6-12s** (`katon_housenka` 4,0s→6,0s,
   `fuuton_rajada_cortante` 4,5s→6,5s, `raiton_lanca_relampago` 5,5s→6,5s), dano escalado pelo
   MESMO fator do cooldown (preserva o DPS já calibrado na rodada 3).

## Pendências honestas da rodada 4 (ver relatório v4 §10 pros números)

- **Boss L19 continua fora da meta, por um motivo NOVO** (-22,4%, não mais o platô de arma —
  esse boss é o único teste onde o elemento com vantagem só tem o tier 1 desbloqueado, tornando-o
  o mais sensível de todos aos novos números de tier 1).
- **Híbrido nunca fica abaixo do melhor build puro (ganho real), mas excede o teto de +15% em 4
  dos 6 bosses** (chega a +47,6% em L19) — nenhuma fração de skill testada (0,15-0,55) fecha os
  dois lados ao mesmo tempo; `HYBRID_TAIJUTSU_FRAC=0,4` prioriza "nunca abaixo do melhor".
- **Chakra sustentável falha em L5/L15 numa hunt de 30 min sem pílula** (97,6%/93,4% do tempo
  sem chakra pro tier 1, meta ≤20%) — tensão nova: custo flat calibrado pra boss L12-25 é
  proporcionalmente enorme contra o pool minúsculo de L5-15. Em L5 a economia nem sustenta
  pílulas suficientes pra compensar (déficit de ~3.548 ryo/h).
- **Grupo 3+ segue não-uniforme** — `ruin_puppet`/`lesser_serpent` entraram na meta (+35%/+33%),
  `thunder_eagle` melhorou muito (+442%→+178%) mas continua acima; `wolf`/`bandit`/`leech` seguem
  abaixo; `curse_shaman`/`storm_monk`/`elite_cloud_guard` seguem muito acima; `white_clone` virou
  negativo. Mesma causa raiz da rodada 3 (HP total do pull varia demais pro mesmo multiplicador).
- **Personagens (±15%) não reverificados** — `personal.json`/`neutral.json` não foram tocados,
  mas a proxy de valor usada nas rodadas 2/3 depende da média de dano/chakra de todo jutsu de
  dano, que mudou com os 8 jutsus elementais recalibrados. Risco não quantificado nesta rodada.
- **Ranged tem o mesmo platô de arma que o melee tinha** (`senbon_de_ferro` req10→`fuuma_shuriken`
  req25) — fora do escopo desta rodada (a missão citava L15-20/boss L19, um encontro melee).

## Pendências honestas da rodada 3 (ver relatório v3 §10 pros números)

- **Boss L19 continua fora da meta** (-25,8% no modo `--no-fallback`, o mesmo platô de tier de
  arma em L15-20 já documentado na rodada 2 — `data/items/*.json`, fora do escopo desta sessão).
- **Tensão real entre paridade 1×1 de boss e paridade de grupo pra pulls de HP baixo**: o mesmo
  `level_scale` de tier 2/3 calibrado pra bater o dano de arma de um BOSS (HP na casa de
  milhares) vira um "apaga o grupo inteiro num cast só" contra um pull de monstros comuns com
  HP total baixo (`thunder_eagle` L54 N=3: +442% de XP/h ninjutsu vs taijutsu, bem acima da meta
  de +30-60%) — nem reduzir cooldown, nem subir `chakra_cost` resolve, porque a luta acaba rápido
  demais pro chakra chegar a faltar. `wolf` (N=3, tier 1 só) continua abaixo da meta (+11,5%),
  igual a rodada 2 já reportava. `ruin_puppet` (N=3) ficou perto (+24,6%, meta é +30 a +60%).
  Não achei uma forma de resolver isso só com os arquivos `jutsus/element_sets/characters`
  (precisaria ou de HP de monstro maior nesses pulls especificamente — `data/monsters`, fora do
  escopo — ou de uma regra de dano decrescente contra alvos de HP baixo, que exigiria mudança de
  engine/C++, não só dado).
- **`suiton_nevoa_cortante`** mudou de forma (item 6) mas não tem nenhum cenário nos
  `GROUP_SCENARIOS` atuais que o exercite (nenhum monstro comum de elemento katon no nível 6-24)
  — mudança de forma bem fundamentada, mas não confirmada pelo simulador nesta sessão.
- **`tools/balance/sim.py` não simula o jogador bebendo pílula de chakra em combate** (só poção
  de HP, ver `_HP_POTIONS`/`use_potions`) — a checagem de "a rotação seca em <30s" (missão item
  4) foi feita analiticamente (ver `docs/sistemas/balanceamento.md`, seção de consumíveis), não
  pelo Monte Carlo. Adicionar isso é natural pra uma rodada 4 (mesmo padrão de `_HP_POTIONS`).
- **Regen de chakra não escala com level** (`gainmanaticks`/`gainmanaamount` fixos em toda vila,
  `tools/export_tfs.py`) — vira irrelevante em nível alto (0,6 chakra/s contra um pool de 1050 no
  L100: 1750s pra regenerar do zero). Não mexi nisso nesta sessão porque toda a calibração de
  chakra_cost (item 3) assumiu esse regen como está; subir o regen sem recalibrar de novo
  desfaria a paridade 1×1 recém-alcançada.

**Resolvido na rodada 4**: os dois itens acima ("não simula pílula em combate" e "regen fixo")
foram endereçados — pílula de chakra agora é simulada (`_CHAKRA_POTIONS`, `--chakra-pills`/
`--hunt`) e o regen fixo foi RE-CONFIRMADO como intencional/permanente (não mais documentado como
"ausência de regen" — ver `character_switch.lua`), mas continua não escalando com level, e essa
mesma característica (regen fixo + custo flat de tier 1) é a causa da nova pendência "chakra
sustentável falha em L5/L15" acima — não foi "resolvido" no sentido de deixar de ser um problema,
só de deixar de ser uma lacuna de MODELAGEM do simulador.

## Achados da rodada 5 (setembro de 2026) — ver `docs/sistemas/balanceamento-relatorio-v5.md`

Ataca de frente a pendência "chakra sustentável falha em L5/L15" da rodada 4, com as 3 mudanças
estruturais que ela já apontava como possíveis (regen por level, pool maior, custo proporcional
ao pool) — as três foram implementadas, não só uma.

1. **Pool de chakra**: `chakra_formula` 50+level×10 → **100+level×10** (piso de chakra inicial
   em `character_switch.lua` subiu de 60 para 110; a vocação continua dando +10/level).
2. **Regen por level**: condição reaplicada a cada level-up (`NarutoRegenAdvance`, novo
   `CreatureEvent onAdvance`, mesmo padrão de `NarutoAchievementAdvance`) — ver acima.
3. **Custo de tier 1 como % do pool** (`manapercent`, não mais `chakra_cost` fixo): 2,5-3,0%
   conforme o elemento. Substitui os antigos 16-20 fixos. Os demais jutsus (tier 2/3/personal,
   custo fixo) tiveram o `chakra_cost` **reescalado pela razão pool novo/pool antigo no
   `required_level` de cada um** — sem isso, o pool maior tornaria TODO jutsu proporcionalmente
   mais barato sem querer, reabrindo a paridade 1×1 já calibrada nas rodadas 2-4 por um motivo
   não relacionado à mudança desta rodada.
4. **Tier 1 recalibrado nas 3 dimensões pedidas pela missão** (não só custo): `cooldown_s`
   3,5s→**9,0s**, `level_scale` ~3,0→**5,25-5,40** (a única forma de fechar burst ≥1,3× em
   quase todo L1-100 com uma fórmula LINEAR em level — dano de arma cresce ~136× de L1 a L100
   por ser um PRODUTO skill×attack, não uma soma; ver relatório v5 §2 pra prova de que nenhum
   `level_scale` fecha os 3 últimos níveis (78-84, 100) sem violar a paridade em bosses baixos).
   O cooldown maior (era o lever "livre" que a rodada 4 já tinha usado, agora empurrado mais)
   é o que permite este `level_scale` maior sem que o DPS SUSTENTADO (se o jutsu fosse
   spammado) ultrapasse o de arma nos bosses baixos — resolvido empiricamente via
   `--group-matrix`/`simulate()`, não por fórmula fechada (a mitigação assimétrica —
   jutsu ignora armadura do monstro, arma não — faz a razão DPS real bem mais extrema que a
   razão de dano BRUTO, então só simulação real decide isso, não conta de cabeça).

## Pendências honestas da rodada 5 (ver relatório v5 §10 pros números)

- **Burst ≥1,3× falha em ~6-9 dos 100 níveis** (L78-84 e L100, faltando 9-11% do alvo) — prova
  matemática: dano de arma cresce como produto skill(L)×attack(L) (~quadrático), dano de tier 1
  só pode crescer como soma level×level_scale + maglevel×skill_scale (linear + côncavo); nenhum
  `level_scale`/`skill_scale` fecha TODO L1-100 sem estourar a paridade de boss em L12-25 (ver
  relatório v5 §2). Melhora real sobre a rodada 4 (que falhava ~60 dos 100 níveis, alguns por
  >80%) — agora só a região L78-100, por <11%.
- **Híbrido excede o teto de +15% em 5 dos 6 bosses de referência** (mesma pendência da rodada
  4, magnitude parecida ou um pouco pior em alguns — `HYBRID_TAIJUTSU_FRAC` sweep 0,15-0,4
  confirma de novo que nenhuma fração fecha "nunca abaixo do melhor" E "nunca acima do teto" ao
  mesmo tempo). Não é uma regressão desta rodada — é a mesma tensão estrutural do modelo de
  híbrido intercalado (arma+jutsu aditivos) introduzido na rodada 4, não resolvida.
- **Grupo 3+ segue não-uniforme** (mesma causa raiz das rodadas 3/4, não tocada nesta rodada —
  fora do escopo declarado de "economia de chakra + paridade 1×1").
- **Personagens (±15%) não reverificados nesta rodada** — mesmo risco que a rodada 4 já
  carregava (a proxy depende da média de dano/chakra de todo jutsu de dano, e os 5 tier 1
  elementais mudaram de novo); `personal.json`/`neutral.json` só tiveram `chakra_cost`
  reescalado (item 3 acima), nunca `base_damage`/`level_scale`.
- **Um monstro específico (`exam_rival_stone`, L20) é o pior caso da meta de hunt** (20,7% sem
  pílula, dentro do limite de 25% mas o mais próximo dele) — HP acima da média da sua faixa
  (420 contra ~300-350 de monstros vizinhos) alonga a luta o bastante pra puxar mais casts de
  tier 1 por ciclo de caça; não é um problema do NÚMERO de tier 1, é a variância entre monstros
  da mesma faixa de nível (ver relatório v5 §1).

## Achados da rodada 6 (setembro de 2026) — ver `docs/sistemas/balanceamento-relatorio-v6.md`

Ataca as 3 pendências centrais da rodada 5 (híbrido, grupo 3+, personagens) + o conteúdo novo
do Covil da Nuvem Vermelha.

1. **Híbrido: 6 de 6 bosses de referência fechados** (era 2 de 6). Duas causas raiz, não uma:
   (a) 2 jutsus tier 1 de área (`raiton_corrente_estatica`/`suiton_nevoa_cortante`, cooldown
   1,3-1,6s, redesenhados como controle na rodada 3) eram picks de DPS não-intencionais por
   causa do cooldown curto — subidos pra 3,0s (igual ao irmão `katon_sopro_brasas`); (b) novo
   parâmetro de modelo `HYBRID_JUTSU_CADENCE_FRAC=0,22` esticando o cooldown EFETIVO do jutsu só
   pro build híbrido (arma continua na cadência cheia) — modela que um jogador dividindo atenção
   entre arma e jutsu não aproveita toda janela de cast livre. Nerfar jutsu por jutsu sozinho
   NÃO fecha (a rotação sempre migra pro próximo melhor candidato do kit — "whack-a-mole",
   testado e documentado no relatório v6 §1). Burst matematicamente inalterado (não depende de
   cooldown, ver `jutsu_damage()`). **Verificado e descartado**: `groupcooldown` (o "cast delay"
   sugerido pela missão) não bloqueia ataque básico de arma neste TFS (`CONDITION_
   SPELLGROUPCOOLDOWN` só afeta OUTRO jutsu do mesmo grupo; `CONDITION_EXHAUST_WEAPON`/`_COMBAT`
   estão "unused" em `server/tfs/src/enums.h`) — subido de 1000ms pra 2000ms como piso de
   segurança, sem efeito mensurável no kit atual.
2. **Grupo 3+: 2 de 12 cenários na faixa +30-60%** (era 1 de 12) — `curse_shaman` fechado
   (+177%→+44%), `storm_monk`/`thunder_eagle`/`elite_cloud_guard` muito melhores mas ainda
   fora (+234%/+178%/+112% → +76%/+91%/+17%). Achado novo: `hits_for_jutsu()` só aplica
   `area_capacity(shape)` pra `type in ("area","beam")` — `type="projectile"` (todo tier 1,
   mesmo com campo `shape` no JSON) sempre atinge 1 alvo em grupo, então monstros "none"-
   elemento de nível baixo (`wolf`/`bandit`/`mercenary_bridge`) nunca se beneficiam de AoE antes
   do tier 2. Fix de verdade exigiria mudar `type` (mecânica de spell, não número) — não aplicado
   por risco ao playtest em andamento.
3. **Personagens: 9 de 9 dentro de ±15%** (não reverificados desde a rodada 3/4) — proxy
   reconstruída do zero (`analyze_v2.py` da rodada 2/3 não sobreviveu entre sessões). Achado
   real (não desta rodada): `sabio_cerimonial` estava a +88,4% da média —
   `selo_de_exorcismo`/`circulo_de_selos` chegavam a ~3× o dano de qualquer jutsu elemental do
   mesmo nível pós-rodada-5. Nerfado ×0,4; isso deslocou `herdeira_hyuga` pra fora por cima
   (a média cai quando o outlier é corrigido) — corrigido com nerf ×0,7 em
   `palma_gentil`/`palma_dupla`. Todos os 9 entre −11,8% e +8,6%.
4. **Bosses novos do Covil (2/3 dentro de ±20% de TTK com summons)**: `tools/balance/sim.py`
   não modela fases/summons — simulação bespoke escrita só pra este check (não parte do
   `sim.py` oficial). Achado ao ler `boss_phases.lua` gerado: fase de "fúria"
   (`attack_multiplier`) NÃO aumenta o dano dos ataques do boss (comentário do próprio
   `tools/export_tfs.py`: `onHealthChange` não altera `<attack>` do XML em runtime) — o efeito
   real é cura de uma vez (`maxHealth×(mult-1)×0,10`) + velocidade de movimento maior.
   `boss_rings_bearer`/`boss_crimson_ancestor` fechados reduzindo `count`/`hp` do summon
   (verificado sem colateral: `invoked_path`/`crimson_echo` só existem como summon, sem spawn
   físico nem quest); `boss_curse_partner` (`magma_serpent`, reusado em spawns/tarefas de
   verdade — não tocado) ficou em +34,3% (era +79,5%), `death_rate=0,00` nos 3 (não impossível
   pro taijutsu solo, meta de segurança cumprida).

## Pendências honestas da rodada 6 (ver relatório v6 §7 pros números)

- **Grupo 3+ continua não-uniforme** (10/12 fora da faixa) — 2 causas raiz distintas e
  não resolvidas: (a) monstros sem AoE de verdade disponível no seu nível (mudança de `type` de
  spell, maior que ajuste de número); (b) jutsus "campeão" compartilhados entre 2 níveis/
  monstros bem diferentes não fecham com um multiplicador de dano único (mesma causa raiz das
  rodadas 3-5, "um multiplicador não serve pra todo HP de pull").
- **`boss_curse_partner` (Sócio Eterno) acima de +20% de TTK com summons** (+34,3%) — precisaria
  de uma variante mais fraca dedicada do summon (`magma_serpent` reusado demais pra tocar
  globalmente) ou um campo `hp_scale` no summon de fase (mudança de `tools/export_tfs.py`, não
  só de dado).
- **Proxy de personagens reconstruída sem o script original** — considerar versionar
  `tools/balance/character_value.py` (ou equivalente) na rodada 7 pra não perder de novo.
- **`wolf`/`bandit`/`mercenary_bridge`/`mist_guardian`/`white_clone`** seguem abaixo da faixa
  de grupo, herdado, não coberto pelas mudanças desta rodada.

## Achados da rodada 7 (setembro de 2026) — ver `docs/sistemas/balanceamento-relatorio-v7.md`

Tema único: "o chakra voltou a não ser um recurso" — playtest ao vivo confirmou 9 casts
seguidos de tier 1 no L1 sem sair de 108-110/110 de chakra (`docs/qa/playtest-l1-20-r5.md`).

1. **`chakra_cost_percent` dos 5 projéteis tier 1 subiu ~4,7×** (2,5-3,0% → 12-14%,
   `data/jutsus/{katon,fuuton,raiton,doton,suiton}.json`) — `cooldown_s`/dano intocados.
   Fecha **6-8 casts por pool cheio em TODO nível 1-100 e nos 5 elementos** (era 33-55) e
   recuperação do pool do zero em 73,3-83,3s em qualquer nível (regen não mudou, já fechava a
   meta de 60-90s no L1 desde a rodada 5).
2. **Métricas analíticas novas**: `casts_per_full_pool(jutsu, chakra_max)` e
   `time_to_refill_pool_s(level, chakra_max)` — não rodam Monte Carlo, respondem direto as duas
   perguntas de design da missão; incluídas no resultado de `simulate_hunt`/`--hunt`.
3. **Achado de modelo (o mais importante desta rodada)**: `pick_ninjutsu_jutsu()` escolhe o
   jutsu de maior dano/segundo do kit JÁ DESBLOQUEADO, não necessariamente o tier 1 — a partir
   do primeiro tier 2 do elemento (`required_level` 12-26 conforme o elemento), o tier 1 nunca
   mais é conjurado de verdade pela build ninjutsu/híbrida "racional". Isso significa que a
   métrica de "tempo sem chakra pro tier 1" das rodadas 4-6, em L20+, media o efeito colateral
   de gastar chakra em tier 2/3 (fixo, caro desde a rodada 5) — não o custo do tier 1, que é do
   que a missão desta rodada realmente precisava. **Fix**: `force_tier1` (novo parâmetro de
   `simulate_hunt`, default de `--hunt` agora — `--no-force-tier1` volta ao comportamento
   antigo) força o jutsu conjurado a ser sempre o tier 1, medindo o cenário certo em qualquer
   nível.
4. **Avaliado e descartado**: `cooldown_s` 9,0s→6,0s (e testado até 1,0s) no build híbrido —
   `HYBRID_JUTSU_CADENCE_FRAC=0,22` (rodada 6) estica o cooldown efetivo o bastante para que a
   diferença seja irrelevante numa hunt de 30 min; só cooldowns abaixo de ~2,0s (menor que o
   intervalo de ataque da arma) mostram alguma diferença — e essa faixa quebraria a paridade de
   boss ninjutsu/híbrida calibrada nas rodadas 5-6. `cooldown_s` mantido em 9,0s.
5. **Meta "15-25% de tempo sem chakra numa hunt híbrida sustentada, todo nível 5-100" NÃO
   fechou** — achado estrutural, não falta de tentativa: com `force_tier1=True` e o custo do
   item 1, a razão gasto/regen numa hunt de 30 min fica em ~0,24 em QUALQUER nível (pool e
   regen crescem na mesma proporção), bem abaixo do ponto de transição ≈1 onde a scarcity deixa
   de ser ~0% e passa a ser ~50-80% (a faixa intermediária pedida, 15-25%, é uma zona muito
   estreita, não um platô — testado com sweep de cooldown 1,0-9,0s e regen 1-10× mais lenta, ver
   relatório v7 §5/§6). Sem o amortecedor híbrido, ninjutsu puro com tier 1 forçado JÁ mostra
   33-72% de scarcity sem pílula e ≤0,1% com pílula — confirma que o custo funciona; o gargalo é
   só o modelo híbrido especificamente (calibrado do jeito que está para não estourar boss
   parity, ver achado 4 da rodada 6). Recomendação para destravar isso: aumentar
   `HYBRID_JUTSU_CADENCE_FRAC`, mas só como parte de uma rodada nova que também re-calibre boss
   parity híbrida (reabriria a pendência que a rodada 6 fechou) — não é um número isolado.
6. **Regen (só recomendação, não aplicada)**: slowdown de regen testado em memória (fator
   1-10× mais lento) tem o mesmo problema do item 5 (a razão é dominada por
   `frac/cooldown`, não pela regen) — e o fator que criaria alguma scarcity (4-5×) faria a
   recuperação do pool em L1 saltar de 73s pra 220-290s, violando a própria meta de 60-90s
   desta rodada. `chakra_regen_amount_per_tick` (`3+level//4` a cada 2s) **não mudou** em
   `tools/balance/sim.py` nem foi recomendado mudar em `tools/export_tfs.py`.
7. **Tier 2/3/personagens: avaliado, não reescalado**. A fórmula de "valor de personagem"
   (`(chakra_cost/cooldown)×dano_por_chakra`) CANCELA o `chakra_cost` algebricamente
   (`valor=dano_médio/cooldown_s`) — os 9 personagens continuam exatamente onde a rodada 6
   deixou, confirmado sem precisar rerodar a proxy. **Achado colateral fora do escopo desta
   rodada**: no cenário de pull 3+ (`simulate_group_fight`, que considera custo na escolha do
   jutsu), 3 dos 12 cenários mudaram de XP/h ninjutsu (`ruin_puppet` +56,9%→+3,7%, saiu da
   faixa 30-60% que a rodada 6 tinha fechado) porque o tier 1 deixa de ser filler grátis entre
   cooldowns de tier 2/3 — consequência esperada de tornar o tier 1 um recurso de verdade, não
   corrigido (reescalar tier 2/3 reabriria a paridade de boss 1×1, compartilhada com os
   cenários de grupo).
8. **Boss parity (6/6), burst (94/100) e personagens (9/9 dentro de ±15%) confirmados
   inalterados** (byte-a-byte idênticos à rodada 6) — nenhum dos 6 bosses de referência usa o
   tier 1 elemental como pick de DPS, e nenhum campo de dano/cooldown foi tocado.

## Pendências honestas da rodada 7 (ver relatório v7 §5-7 pros números)

- **Scarcity de tier 1 no build híbrido continua ~0% em toda hunt de 30 min** — a meta de
  15-25% não fechou por limite estrutural do `HYBRID_JUTSU_CADENCE_FRAC` da rodada 6 (ver
  achado 5 acima). Não é uma pendência de calibração fina; precisa de uma decisão de design
  (relaxar qual das duas metas — scarcity híbrida ou boss parity híbrida) antes de mexer de
  novo nisso.
- **Grupo 3+ piorou em 1 dos 2 cenários que a rodada 6 tinha fechado** (`ruin_puppet`,
  +56,9%→+3,7%, saiu da faixa 30-60%) — efeito colateral do item 1, não corrigido (ver achado 7
  acima). Continua não-uniforme (10-11/12 fora da faixa), mesma causa raiz da rodada 6 (não
  resolvida antes desta).
- **Pendências herdadas da rodada 6 sem mudança**: `boss_curse_partner` acima de +20% de TTK
  com summons; proxy de personagens ainda não versionada como script próprio;
  `wolf`/`bandit`/`mercenary_bridge`/`mist_guardian`/`white_clone` seguem abaixo da faixa de
  grupo.

## Achados da rodada 8 (setembro de 2026) — ver `docs/sistemas/balanceamento-relatorio-v8.md`

1. **`sim.py` passou a modelar `phases[].attack_multiplier`/`summons` de boss** (antes ignorados
   por completo — o simulador só lia `hp`/`attacks` fixos). `boss_phase_state_init()`/
   `apply_boss_phase_tick()` replicam `server/generated/scripts/naruto/boss_phases.lua`: ao
   cruzar o `hp_percent` de uma fase (checado por golpe individual, não por tick), o multiplicador
   passa a valer sobre TODO ataque do boss dali em diante (nunca some), com a mesma cura pontual
   `+max_hp×(mult-1)×0,10`. `summons` viram uma trickle de dano de fundo (`average_monster_dps_
   vs_player`, sem RNG) — aproximação deliberada, não simula os summons um a um.
2. **Só a Serpente Branca precisou de recalibração de `attack_multiplier`** (1,9→1,45) — os
   outros 11 bosses com fase de fúria já caíam dentro de 1,3×-1,8× de dano recebido/s (fase final
   vs. fase 1) mesmo sem tocar o valor. `death_rate`≤10% (com poções) já era 0% em todos, com e
   sem a fúria real — a folga de poção sempre cobriu isso.
3. **`HYBRID_JUTSU_CADENCE_FRAC` foi REMOVIDA** — modelo novo: híbrido sempre conjura tier 1
   (`advantage_element()`), cooldown real. Isso exigiu subir o cooldown do tier 1 (9,0s→27,0s,
   custo do pool inalterado) pra manter o teto de boss ≤+15% — testado e descartado usar o
   custo como lever (precisaria de ×4-6 pra tamponar o boss, o que quebra "Genin L1 6-8
   casts/pool").
4. **15-25% de tempo sem chakra em hunt híbrida CONTINUA não fechando (0% em todos os níveis)** —
   agora por um motivo diferente da rodada 7: "Genin L1 6-8 casts/pool" e essa faixa de scarcity
   são matematicamente incompatíveis sob o modelo de custo percentual fixo (o custo que fecha a
   scarcity quebra os casts/pool). Ver relatório v8 §2 pra prova numérica completa.
5. **Grupo 3+: `ruin_puppet` e `thunder_eagle` recolocados em +30-60%** ajustando os jutsus de
   área/beam tier 2/3 do rotação (`katon_anel_chamas` ×1,2; `fuuton_rajada_cortante` e
   `fuuton_tornado_cortante` ×0,65 cada — precisou nerfar os DOIS porque a rotação migra pro
   outro assim que um é nerfado sozinho, mesma classe de achado "whack-a-mole" da rodada 6).
   `wolf` L2 N=3 continua bem fora da faixa (-84,6%) — nenhum jutsu de área existe nesse nível,
   fora do escopo da alavanca pedida.

## Pendências honestas da rodada 8 (ver relatório v8 §7 pros números)

- **Scarcity híbrida (15-25% sem chakra) continua em 0%** — conflito estrutural real com "Genin
  L1 6-8 casts/pool" (não uma questão de achar o número certo). Resolver exigiria uma alavanca
  fora da lista desta rodada (ex. custo crescente por cast dentro de uma janela, não um
  percentual fixo do pool).
- **`wolf` L2 N=3 fica em -84,6%** (fora de +30-60%) — sem jutsu de área desbloqueado nesse
  nível; fora do escopo da alavanca "tier 2/3" pedida.
- **Híbrido fora dos 6 bosses de referência tem variância bem maior que antes** (ex.
  `stone_sentinel` +201,9%, `glacier_oni` +102,0%, em pares nível≈nível-do-monstro da matriz
  completa) — o modelo antigo ficava sempre perto de zero por castar tão raro; fora do escopo
  numérico desta rodada (só pede os 6 bosses de referência).
- **Margem do teto de boss não é folgada** (pior caso -13,4% de -15%, ~1,6pp de sobra) — revisitar
  se algum conteúdo futuro aumentar `level_scale` do tier 1 ou reduzir o cooldown de novo.

## Achados da rodada 9 (setembro de 2026) — ver `docs/sistemas/balanceamento-relatorio-v9.md`

**Mudança de filosofia, não só de número.** O orquestrador rejeitou o cooldown de 27,0s da
rodada 8 pós-fato ("um jutsu por meio minuto destrói a sensação de ninja") e voltou pra 9,0s —
e junto rejeitou o próprio teto "híbrido ≤+15% sobre o melhor puro" que guiou as rodadas 4-8: no
Tibia (e aqui) jogar com arma + magia é o jogo normal, não uma exceção a conter. **O híbrido
passa a ser o build de referência**; monstros/XP/progressão são calibrados pelo TTK/XP-h
híbrido; os builds puros só precisam ser viáveis (≥70% do DPS híbrido em todo nível 5-100,
≥60% nos 6 bosses de referência) — nenhum é "o certo".

1. **Nenhuma mudança de fórmula/modelo em `sim.py`** — o híbrido já castava "sempre que libera
   e há chakra" desde a rodada 8; só um comentário novo documentando a filosofia e a pendência
   estrutural do item 3 abaixo, onde o teto de +15% era citado.
2. **3 bosses recalibrados pra fechar TTK 60-180s + viabilidade ≥60% ao mesmo tempo**:
   `boss_bandit_chief` `defense` 12→6; `boss_mist_swordsman` `hp` 1700→2380 + `defense` 15→8
   (TTK híbrido 52,0s→64,9s, estava abaixo do piso de 60s); `boss_white_serpent` `defense`
   18→9. A armadura mitiga só o dano de arma (não o de jutsu), então baixá-la favorece
   desproporcionalmente quem depende só de arma — mesmo lever fecha os dois lados (TTK E
   viabilidade) nesses 3 bosses. Testado até `defense=0`: teto prático desse lever sozinho é
   ~65-67% nesses bosses — `×0,5` (não zero) foi escolhido como meio-termo com folga.
3. **Achado central (pendência, não resolvida)**: viabilidade dos puros ≥70% **falha em 64 de
   96 níveis comuns (5-100)**, pior caso 46,3% (`mist_guardian` L16) — provado que é tensão
   estrutural, não falta de tuning: qualquer nerf de tier 1 forte o bastante pra fechar 70% no
   pior caso expande a falha de burst ≥1,3× de "L78-85,100" (status quo, 9 níveis) pra "L35-100"
   ou pior (testado); zerar armadura do monstro comum (o único outro lever) chega no máximo a
   ~60-67%, ainda abaixo de 70%. Causa raiz: mitigação assimétrica (armadura reduz arma, não
   jutsu) + cooldown real de 9,0s (fixo pelo orquestrador) + `level_scale` do tier 1 calibrado
   pra burst em quase todo nível. Recomendação: buffar item de arma L5-40 (não jutsu, não
   monstro) — fora do escopo de arquivos desta rodada.
4. **Ninjutsu excedendo o híbrido, corrigido**: `raiton_punho_trovao` (tier 3, req 30,
   `cooldown_s=7,0` — mais curto que o tier 1) e `doton_colapso_terreno` (tier 3, req 48)
   permitiam a ninjutsu puro um único cast que já superava metade do HP do monstro comum mais
   próximo — mais rápido que o híbrido inteiro em 11 pontos de L30-35/L60-64. Fix:
   `raiton_punho_trovao.chakra_cost` 200→320 (custo sozinho resolve, pool não permite 2º cast);
   `doton_colapso_terreno.chakra_cost` 268→400 + `level_scale`/`base_damage`×0,9 (custo sozinho
   não bastava — um ÚNICO cast já era grande demais). Zero overshoot confirmado em L5-100.
5. **XP/h absoluto do simulador não bate com `progressao-jogador.md` — achado de métrica, não
   de calibração**: a razão sim/doc CRESCE com o nível (24× em L5, quase 4000× em L100) e o
   mesmo gap (mesma ordem de grandeza) já existe pro build `taijutsu` puro, ou seja, não é algo
   introduzido pelo híbrido desta rodada. `simulate()`/`--hunt` medem "eficiência de caça pura"
   (sem viagem/missão/espera de boss); o doc mede horas de jogo REAL (inclui isso tudo). A
   métrica "kills por level" (que É ajustável por `data/monsters`) já bate com o design
   existente — não mexi em HP/XP de monstro comum nenhum. Recomendação pra rodada 10: um
   parâmetro novo de simulador (overhead de sessão real por bloco), não `data/monsters`.
6. **Chakra sem pílula (10-35%, todo nível) continua não fechando** — oscila 0%-81,2%
   dependendo do monstro mais próximo de cada nível (só L20 cai na faixa, 1 de 20 pontos).
   Varredura de multiplicador de regen (0,3×-4,0× sobre `2+floor(level/4)`): reduzir regen só
   piora; aumentar até ~1,15× é o melhor achado (3 de 20 na faixa) — não aplicado (ganho
   marginal, mudar a regen precisaria de uma linha nova em `tools/export_tfs.py`, fora do
   escopo desta sessão). Causa raiz é variância de HP entre monstros da mesma faixa (mesmo
   achado da rodada 5 pro L20), não a fórmula de regen — recomendo manter `2+floor(level/4)`.
7. **Grupo `ruin_puppet` (N=3) saiu da faixa +30-60%** (+42,1%→+22,5%) — confirmado que já
   estava assim no estado "r9 parcial" recebido no início da sessão (idêntico antes/depois dos
   2 fixes de tier 2/3 desta rodada) — efeito colateral herdado da reversão de cooldown 27s→9s
   do orquestrador, não desta rodada. `thunder_eagle` (N=3) continua em +36,4%, dentro da faixa.

## Pendências honestas da rodada 9 (ver relatório v9 §9 pros números)

- **Viabilidade dos puros ≥70% falha em 2/3 dos níveis comuns 5-77** — tensão estrutural real
  com burst ≥1,3× (fixo pelo cooldown do orquestrador); lever recomendado é buffar arma L5-40.
- **Chakra sem pílula (10-35%) falha em 19 de 20 níveis testados** — causa raiz é variância de
  HP entre monstros, não fórmula de regen; `1,15×(2+floor(level/4))` é o melhor achado (3/20).
- **XP/h absoluto do simulador não é comparável 1:1 com `progressao-jogador.md`** — gap
  estrutural de métrica (grind puro vs. jogo real), precisa de um parâmetro novo de simulador.
- **`ruin_puppet` (grupo N=3) fora da faixa +30-60%** — herdado da reversão de cooldown do
  orquestrador, não corrigido nesta rodada (risco de whack-a-mole nos jutsus de área doton).
- **Kits (±15%) não reverificados numericamente** — confirmado que nenhum jutsu tocado é
  referenciado por `personal.json`/`neutral.json`, mas a proxy não foi rodada de novo.

## Achados da rodada 10 (setembro de 2026) — ver `docs/sistemas/balanceamento-relatorio-v10.md`

Tema: itens de arma e a curva do taijutsu puro em L5-40, executando a recomendação central da
pendência #1 da rodada 9 ("buffar item de arma L5-40, não jutsu, não monstro").

1. **Escada de arma melee L1-40 recalibrada**: 3 itens novos (`adaga_genin` req5,
   `espadao_de_aco` req25, `katana_aprimorada` req30 — preenchem os 3 buracos reais da escada,
   >7 níveis sem degrau) e `attack` maior em 6 itens já existentes (`tanto_steel`,
   `gloves_taijutsu`, `wakizashi_temperado`, `katana_ronin`, `kodachi_ruins`, `puppet_blade`,
   `adaga_sombria`) — ver a tabela completa com preço/vendedor em
   `docs/sistemas/itens-e-equipamentos.md`. `gloves_taijutsu` também passou a ser vendida por
   Ichiro — existia no catálogo desde sempre mas não estava em NENHUM NPC (gap real,
   provavelmente não intencional, que a deixava sempre dominada pelo Tantō mesmo no seu próprio
   nível de desbloqueio).
2. **Metodologia**: pra cada degrau, `attack` foi buscado por busca binária maximizando a razão
   TTK_híbrido/TTK_puro no PIOR nível dentro da janela de 5 níveis até o próximo degrau (não só
   no nível de desbloqueio do item), sujeito a "burst do tier 1 continua ≥1,3× em toda a
   janela" (checado via `weapon_max_damage()`/`jutsu_damage()` isolados, sem monstro — o burst é
   uma métrica só do personagem) — mesma lógica de `estimate_weapon_dps`, só que sem Monte
   Carlo pro burst (é conta fechada, não estocástica o bastante pra precisar).
3. **Achado central (o mais importante desta rodada, não esperado)**: MESMO maximizando
   `attack` até o limite seguro de burst, vários rungs (L5, L10, L15, L20, L35) têm um **teto de
   viabilidade abaixo de 70% que nenhum `attack` maior ultrapassa** — testado com valores de
   attack MUITO acima do que qualquer NPC venderia (até 500), a razão pura/híbrido PIORA (não
   melhora) a partir de um certo ponto. Causa raiz: o monstro comum mais próximo de alguns
   níveis (`mist_scout` L14-15, por HP baixo relativo ao level) morre tão rápido contra o
   híbrido que o ÚNICO cast de tier 1 no início da luta (jutsu ignora armadura, arma não) já é a
   maior parte do HP do monstro — nenhum `attack` de arma acelera o que já é quase instantâneo
   pro lado do jutsu. Isso é uma tensão DIFERENTE da "burst vs. sustentado" já documentada nas
   rodadas 5/9 (aquela é sobre o valor DE UM cast; esta é sobre a DURAÇÃO da luta ser curta
   demais pra diluir esse cast) — refina a recomendação da rodada 9: buffar arma L5-40 ajuda,
   mas não fecha 70% em TODO nível sozinho, mesmo dentro do orçamento de burst.
4. **Achado colateral (bug introduzido e corrigido na própria sessão)**: o primeiro rascunho da
   escada maximizava `attack` olhando só a janela de 5 níveis de CADA item isoladamente — mas
   `adaga_sombria` (req40) na prática cobre 10 níveis (L40-49, não há degrau em L45; fora do
   "L5-L40" da missão) até `tanto_jonin` (req50). `attack=78` (o valor "ótimo" pra L40-44) já
   quebrava burst em L45-48 quando testado no range completo — corrigido pra `attack=70`
   (worst-case burst 1,37× em L40-49, com folga). Acompanha um achado de MESMA classe nos 3
   bosses de referência baixos: `attack` maximizado por janela empurrava o TTK híbrido de
   `boss_bandit_chief`(L12)/`boss_mist_swordsman`(L19) pra 39,9s/51,9s (abaixo do piso de 60s) —
   `tanto_steel`/`gloves_taijutsu`/`wakizashi_temperado` tiveram o `attack` reduzido do "ótimo de
   viabilidade" pra um valor mais conservador (17/18/27, não 20/28/30) e os 3 bosses baixos
   (`boss_bandit_chief`, `boss_mist_swordsman`, `boss_white_serpent`) receberam +15% de `hp`
   (dentro do limite da missão) — ver relatório v10 §4 pros números completos da troca.
5. **Resultado líquido (varredura própria, 1 nível de cada vez, não só `MATRIX_LEVELS`)**:
   taijutsu puro abaixo de 70% caiu de **65 para 41 dos 96 níveis** (68%→43% de falha) — melhora
   real, mas a meta "TODOS os níveis" não fecha (achado 3 acima prova que não fecharia com
   NENHUM valor de `attack`, dentro do orçamento de burst). Os 6 bosses de referência: os 3
   baixos (12/19/25) subiram de 61,8%/60,5%/62,8% pra 65,8%/68,9%/83,0% do DPS híbrido — bem
   dentro da meta de ≥60%; os 3 altos (50/80/100), não tocados, continuam 75,9%/79,6%/82,3%
   (inalterados). Burst e kits confirmados sem regressão (burst continua 96/100, o mesmo padrão
   "aceito perder L78-80,100" de antes; nenhum jutsu/personagem tocado).
6. **Ninjutsu puro (mesma varredura)**: 35 de 96 abaixo de 70% (melhor que taijutsu, já que cai
   pro fallback de arma quando o jutsu não vale a pena) e **nenhum ponto de overshoot real sobre
   o híbrido** (1 nível, L6, empata em 100,5% — ruído de Monte Carlo, ambos os builds caem pro
   mesmo "só arma" nesse nível específico, não uma vitória de ninjutsu).

## Pendências honestas da rodada 10 (ver relatório v10 §9 pros números)

- **Viabilidade dos puros ≥70% ainda falha em 41 de 96 níveis** (era 65) — achado novo (item 3
  acima) prova que boa parte disso é um teto estrutural que NENHUM valor de `attack` de arma
  fecha (monstro morre rápido demais pro cast único de tier 1 do híbrido virar uma fração
  pequena do dano total). Os rungs mais afetados por esse teto: L5, L10, L15, L20, L35
  (`bandit_archer`/`leech`/`mist_scout`/`mist_guardian`/`exam_rival_stone`/`spectral_warrior`).
  Recomendação pra rodada 11: só fecha com HP de monstro comum maior nesses pontos específicos
  (fora do escopo "só itens" desta rodada) ou uma mudança de modelo (jutsu com dano reduzido
  contra alvos que morreriam num único hit de qualquer forma — mudança de engine/simulador, não
  de dado).
- **L41-77 não tocado** (fora do "L5-L40" da missão) — continua com falhas parecidas às da
  rodada 9 (`thunder_eagle`/`glacier_oni`/`storm_monk`/`magma_serpent`, L50-77), exceto L41-49
  que melhorou como efeito colateral do buff em `adaga_sombria` (req40, cobre até L49).
- **`boss_puppeteer` (L50) medido em 58,84s de TTK híbrido** (abaixo do piso de 60s) nesta
  sessão — não é um item tocado nesta rodada (usa `tanto_jonin`, req50, intocado); parece uma
  variação de medição (trials/seed) em relação aos 62,7-62,8s dos relatórios anteriores, não uma
  regressão desta rodada. Sinalizado, não corrigido (fora do escopo declarado "só L5-40").
- **`ruin_puppet` (grupo N=3) mudou de +22,5% pra -32,8%** (ninjutsu passou de vantagem pra
  desvantagem sobre taijutsu) — efeito colateral direto de `espadao_de_aco` (req25, usado por
  esse cenário L27) ter dado um salto grande de `attack` só pro lado taijutsu/híbrido; a meta de
  grupo (+30-60%) não é uma meta explícita desta rodada, mas fica sinalizado pra quem for tocar
  jutsu de área doton depois.
- **Kits (±15%) não reverificados numericamente** — nenhum jutsu/personagem foi tocado nesta
  rodada (só itens de arma + HP de 3 bosses), risco não quantificado mas confiança alta.
