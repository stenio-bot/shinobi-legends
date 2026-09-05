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
```

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
`HYBRID_TAIJUTSU_FRAC`/`HYBRID_NINJUTSU_FRAC` = 0.5/0.5) — não é a média dos dois builds
"pura-raça", é um personagem que de fato joga assim: as duas skills ficam mais baixas que um
especialista em qualquer uma das trilhas, mas com acesso pleno a ambas. Meta da missão: "híbrido
perto do melhor" — ver relatório v2 §3 pros números reais (fica 6,6%–19,9% atrás do melhor build
em cada boss, mediana ~13%).

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
