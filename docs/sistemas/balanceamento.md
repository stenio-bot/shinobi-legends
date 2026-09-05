# Sistema: Balanceamento numérico

Este documento é a **lógica por trás dos números** em `data/`. Toda vez que alguém
perguntar "por que esse monstro tem 900 de HP?", a resposta está aqui. Valores marcados
`[PLACEHOLDER]` ainda não passaram por playtest.

## Referências fixas (de `progression.json` e `personagem-e-progressao.md`)

```
HP do player      = 100 + level*15
Chakra do player  = 50 + level*10
XP total          = 50*level^2 + 50*level   →  XP para subir de L para L+1 = 100*L + 100
```

## Metas de balanceamento (rodada 9 — reescrita completa)

**Mudança de filosofia (decisão do orquestrador, pós-rodada 8):** o cooldown do tier 1
elemental voltou de 27,0s para **9,0s** ("um jutsu por meio minuto destrói a sensação de
ninja") e o teto "híbrido ≤+15% sobre o melhor build puro", que guiou as rodadas 4-8, foi
**removido** — não existe mais nenhum teto artificial sobre o híbrido neste jogo. No Tibia (e
aqui) jogar com arma + magia junto é o jogo normal, não uma exceção a conter.

**O build híbrido (arma + jutsus, castando o tier 1 sempre que o cooldown de 9s libera e há
chakra) é o build de referência.** Monstros, XP/h e a tabela de progressão são calibrados pelo
TTK/XP-por-hora híbrido — não mais por um "jogador médio" abstrato nem por um teto sobre o
híbrido. Os builds puros (só taijutsu, só ninjutsu) só precisam ser **viáveis**, não iguais:

1. **TTK/XP-por-hora do híbrido** é a métrica central de calibração de monstro/level/região —
   ver `tools/balance/sim.py --matrix`/`--hunt` (build `hybrid`).
2. **Curva de progressão**: XP/h por bloco e horas acumuladas até L100 devem bater com
   `docs/sistemas/progressao-jogador.md` (±20%) usando o híbrido como referência. **Achado da
   rodada 9**: a métrica "kills por level" (abaixo) já bate; o XP/h ABSOLUTO do simulador mede
   "eficiência de caça pura" e é estruturalmente maior (15×-4000×, cresce com o nível) que o
   XP/h "misto" do doc (que embute viagem/missão/espera de boss) — não é fechável só com
   `data/monsters` sem quebrar kills-por-level; ver `balanceamento-relatorio-v9.md` §2 pro
   detalhe e a recomendação (um parâmetro de "overhead de sessão real" no simulador).
3. **Bosses**: TTK híbrido no level-alvo entre **60s e 180s**, `death_rate` ≤10% com poções
   (fúria de fase real considerada, rodada 8). 6 bosses de referência: `boss_bandit_chief`(12),
   `boss_mist_swordsman`(19), `boss_white_serpent`(25), `boss_puppeteer`(50),
   `boss_ancestral_oni`(80), `boss_crimson_ancestor`(100).
4. **Builds puros viáveis**: taijutsu puro e ninjutsu puro ≥70% do DPS híbrido em todo nível
   5-100, e ≥60% nos 6 bosses de referência. Ninjutsu puro nunca deve exceder o híbrido (se
   acontecer, o lever é o custo/dano fixo dos jutsus tier 2/3, não o tier 1). **Achado da
   rodada 9**: ≥60% nos bosses fecha; ≥70% nos níveis comuns 5-100 **não fecha em 64 de 96
   níveis** (pior caso 46,3%) — tensão estrutural real com o burst do item 6 abaixo (mitigação
   de armadura reduz o dano de arma mas não o de jutsu elemental; qualquer nerf de tier 1 forte
   o bastante pra fechar 70% no pior caso quebra burst em dezenas de níveis extras abaixo de
   L78). Ver `balanceamento-relatorio-v9.md` §4.3 pra prova e recomendação (buffar item de arma
   L5-40, não jutsu).
5. **Chakra**: com regen `2+floor(level/4)` a cada 2s, numa hunt híbrida de 30 min: % do tempo
   sem chakra pro tier 1 entre 10-35% (sem pílula) e ≤5% (com pílula); Genin L1 6-8 casts por
   pool cheio. **Achado da rodada 9**: casts/pool e a meta com pílula fecham; sem pílula o
   resultado oscila 0%-81% dependendo do monstro mais próximo do nível (não é função suave do
   nível nem da regen) — testada varredura de regen 0,3×-4,0×, melhor achado é 1,15× (3 de 20
   pontos na faixa, contra 1 de 20 hoje); causa raiz é variância de HP entre monstros da mesma
   faixa, não a fórmula de regen. Ver `balanceamento-relatorio-v9.md` §5.
6. **Manter**: burst do tier 1 ≥1,3× o hit de arma (aceito perder L78+); kits pessoais (9
   personagens) dentro de ±15% de valor entre si; grupo de 3+ com ninjutsu +30-60% sobre
   taijutsu onde há jutsu de área desbloqueado.
7. `tools/validate_data.py` e `tools/export_tfs.py` passam sem erro; `--matrix` roda em
   menos de 120s; `--json` de `--matrix`/`--group-matrix`/`--hunt` sempre válido.

## 1. HP de monstro

```
hp_base(L) = 20 * L * (1 + (L-20)/100)        # linear até L20, levemente super-linear depois
hp = hp_base(L) * papel
papel:  normal 1.0 · tanque 1.4 · rápido 0.85–0.9 · ranged 0.75–0.8 · boss 7–8×
```

A fórmula foi **ajustada aos monstros que já existiam** (lobo L2=60, sanguessuga L10=180,
sapo L13=260, renegado L18=340 → todos ≈ 20×level). O termo `(1+(L-20)/100)` existe para
que o tempo de matar não caia conforme o dano do player cresce mais rápido que `20*L`.

| Level | hp_base | normal | tanque | ranged | boss |
|---|---|---|---|---|---|
| 27 | 578 | 580 | 810 | 460 | — |
| 32 | 717 | 720 | **1000** | 570 | — |
| 38 | 897 | **900** | 1260 | 720 | — |
| 44 | 1091 | 1090 | 1530 | **870** | — |
| 50 | 1300 | 1300 | 1820 | 1040 | **9100** (7×) |
| 54 | 1447 | 1450 | 2030 | **1160** | — |
| 60 | 1680 | 1680 | **2350** | 1340 | — |
| 68 | 2013 | 2010 | 2820 | **1800** (rápido 0.9) | — |
| 74 | 2279 | **2280** | 3190 | 1820 | — |
| 80 | 2560 | 2560 | 3580 | 2050 | **20500** (8×) |

Em negrito: o valor efetivamente usado em `data/monsters/`.

## 2. XP de monstro

```
xp = hp * ratio(L)
ratio: L1–20 ≈ 0.40–0.70 (conteúdo antigo) · L25–35 0.85 · L36–50 0.80 · L51–65 0.70 · L66–80 0.60
boss: ratio 1.2
```

O ratio **cai** com o level de propósito: o HP cresce mais rápido que a XP necessária por
level, então manter ratio constante faria a curva desabar. O alvo é **4–7 kills por level**
com monstro do mesmo level, que é exatamente o ritmo do conteúdo já existente
(bandido L5 = 10 kills, renegado L18 = 6,3 kills).

| Monstro | L | HP | ratio | XP | XP p/ subir | kills/level |
|---|---|---|---|---|---|---|
| Marionete de Combate | 27 | 580 | 0.85 | 490 | 2 800 | 5,7 |
| Sentinela de Pedra | 32 | 1000 | 0.85 | 850 | 3 300 | 3,9 |
| Guerreiro Espectral | 38 | 900 | 0.80 | 720 | 3 900 | 5,4 |
| Xamã da Maldição | 44 | 870 | 0.80 | 700 | 4 500 | 6,4 |
| **Marionetista** (boss) | 50 | 9 100 | 1.20 | 11 000 | 5 100 | 0,46 |
| Águia do Trovão | 54 | 1 160 | 0.70 | 810 | 5 500 | 6,8 |
| Oni da Geleira | 60 | 2 350 | 0.70 | 1 650 | 6 100 | 3,7 |
| Monge da Tempestade | 68 | 1 800 | 0.60 | 1 080 | 6 900 | 6,4 |
| Serpente de Magma | 74 | 2 280 | 0.60 | 1 370 | 7 500 | 5,5 |
| **Oni Ancestral** (boss) | 80 | 20 500 | 1.20 | 24 600 | 8 100 | 0,33 |

### Floresta da Morte (área 10–25, revisada com a Serpente Branca)

| Monstro | L | HP | ratio | XP | XP p/ subir | kills/level |
|---|---|---|---|---|---|---|
| Serpente Menor | 18 | 340 | 0.76 | 260 | 1 900 | 7,3 |
| **Serpente Branca** (boss) | 25 | 4 600 | 1.22 | 5 600 | 2 600 | 0,46 |
| Sapo Ancião (boss secundário) | 25 | 4 000 | 1.25 | 5 000 | 2 600 | 0,52 |

A Serpente Branca é o boss **final** da faixa: 4 600 HP = 7× o `hp_base(25)` de 525 arredondado
para cima (o Sapo Ancião fica em 4 000 e vira boss opcional). Dano: 40–62 no golpe primário
(HP do player em L25 = 475 → 8–13%), névoa em área e cuspe ácido a ~90% do primário, como manda
a regra de bosses. `attack_multiplier` na fase 3 é **1,45** (recalibrado na rodada 8, era 1,9 —
ver `docs/sistemas/balanceamento-relatorio-v8.md` §1): desde o commit `87c19a1` ele multiplica o
dano de verdade (`NarutoBossFury`), não só velocidade/cura — `tools/balance/sim.py` modela isso
desde a rodada 8 (`apply_boss_phase_tick`), confirmando dano recebido/s na fase final em ~1,45×
o da fase 1 (dentro da meta 1,3×-1,8×).

> **"Broken" definido antes do playtest:** se um spot der menos de 3 ou mais de 12 kills
> por level, o `ratio` da faixa está errado. O lever é `ratio`, nunca o HP.

## 3. Dano de monstro

```
damage_min = 0.08 * hp_player(L)      # 8% do HP de um player do mesmo level
damage_max = 0.12 * hp_player(L)      # 12%  → ~9 hits para matar sem cura nem defesa
bosses: 8–13% no golpe primário; secundários (área/projétil) a ~90% do primário
attack  ≈ damage_max * 0.75
defense ≈ 0.7 * L   (tanque ×1.5 · ranged ×0.6)
```

| Level | HP player | dano por hit | usado em |
|---|---|---|---|
| 27 | 505 | 40–61 | Marionete |
| 32 | 580 | 46–70 | Sentinela |
| 38 | 670 | 54–80 | Espectral |
| 44 | 760 | 61–91 | Xamã |
| 50 | 850 | 68–110 | Marionetista |
| 54 | 910 | 73–109 | Águia |
| 60 | 1 000 | 80–120 | Oni da Geleira |
| 68 | 1 120 | 90–134 | Monge |
| 74 | 1 210 | 97–145 | Serpente |
| 80 | 1 300 | 104–170 | Oni Ancestral |

Cooldowns: tanque 2,4–2,6 s · normal 2,0–2,2 s · rápido 1,6–1,8 s · ranged 2,2–2,4 s.
Ataques de área têm cooldown 5–10 s e dano ~90% do golpe primário — a área é o que obriga
o player a se mover, não o que mata.

## 4. Ryo

```
ryo_min = 2.5 * L      ryo_max = 5 * L        # média ≈ 3.75*L, coerente com "N*3" de economia.md
boss:  ryo_min = 60 * L    ryo_max = 120 * L
```

## 5. Preço de item

```
buy_price(arma principal / peça de corpo) ≈ 8 * required_level^2
sell_price = 40% do buy_price   (regra anti-inflação de economia.md)
peça de cabeça ≈ 0.40 · pernas ≈ 0.60 · pés ≈ 0.30 do preço do corpo
acessório ≈ 0.85 do preço do corpo
```

Isso reproduz as âncoras de `economia.md`: L20 → ~3.200 (faixa 1.000–5.000);
L50 → ~20.000 (faixa "20.000+"); L60 → ~28.800; L70 → ~39.200.

| Faixa | Arma melee | Ranged | Cabeça | Corpo | Pernas | Pés | Acessório |
|---|---|---|---|---|---|---|---|
| Ruínas (req 28–35) | 6 200 / 9 800 | 7 200 | 2 900 | 7 200 | 4 300 | 2 200 | 6 000 / 6 500 |
| Montanha (req 55–70) | 24 200 / 39 200 | 28 800 | 11 500 | 28 800 | 17 300 | 8 600 | 24 000 / 27 000 |

**Defesa de armadura:** `corpo ≈ 0.55*L · pernas ≈ 0.35*L · cabeça ≈ 0.25*L · pés ≈ 0.20*L`.
**Ataque de arma:** `≈ 1.35 * required_level` (kodachi L28 = 40; katana do trovão L55 = 74;
kanabō L70 = 96; lâmina lendária do boss L78 = 112, ~15% acima da curva por ser drop de boss).

**Platô L8→L20 corrigido na rodada 4**: a arma melee ficava travada em `Tantō de Aço` (req8,
attack 16) por 12 níveis inteiros até `Katana do Ronin` (req20, attack 28) — o boss L19
(Espadachim da Névoa) lutava com uma arma efetivamente 11 níveis atrasada. Item novo
`wakizashi_temperado` (req15, attack 21, `buy_price = 8×15² = 1800` exatamente na fórmula acima)
preenche o meio do caminho, vendido no Mercador Itsuki (Costa das Marés, a região do próprio
boss L19) e na Velha Sumi. Um bug do simulador de balanceamento (`best_item_for_slot` escolhia
o item pelo maior `required_level`, não pelo maior `attack` — fazia `gloves_taijutsu`, req10 mas
attack **14**, "substituir" o Tantō de attack 16 de L10 a L19) também foi corrigido — ver
relatório v4 §3.

**Pergaminhos** (âncora de `economia.md`: t1 500 · t2 5.000 · t3 50.000):
tier 1 = 500 · tier 2 = 5.000–9.000 · tier 3 = 20.000–45.000.

**Consumíveis:** cura por ryo cai conforme o tier sobe, para o consumível grande ser
conveniência e não eficiência.

| Consumível | Efeito | Preço | HP por ryo |
|---|---|---|---|
| Poção de Vida Pequena | 100 HP | 50 | 2,00 |
| Poção de Vida Média | 300 HP | 200 | 1,50 |
| Poção de Vida Grande | 700 HP | 800 | 0,88 |
| Pílula de Chakra Pequena | 60 CK | 30 | 2,00 |
| Pílula de Chakra Grande | 350 CK | 250 | 1,40 |
| Pílula do Soldado | 500 HP + 500 CK | 900 | 1,11 (contando os dois) |

**Regen de chakra ESCALA COM LEVEL desde a rodada 5** (era permanente mas fixo desde a rodada 4):
`character_switch.lua` (`server/tfs/data/scripts/naruto/`) aplica no login E a cada level-up
(`CreatureEvent NarutoRegenAdvance`, novo) uma `Condition(CONDITION_REGENERATION, ...)` com
`CONDITION_PARAM_TICKS=-1` (permanente) recalculada em Lua puro a partir de `player:getLevel()`
— chakra `2+floor(level/6)` a cada **2s** (era 3 a cada 5s fixo, 0,6/s em qualquer nível), HP
`2+floor(level/10)` a cada 5s (em L1-9 é idêntico ao valor antigo, só acelera depois). Pool de
chakra também subiu: `100+level*10` (era `50+level*10`) — piso de chakra inicial em
`character_switch.lua` 60→110. Ver `balanceamento-relatorio-v5.md` §1 pro raciocínio completo
(por que as 3 mudanças da missão — regen por level, pool maior, custo proporcional — foram
implementadas JUNTAS, nenhuma sozinha resolvia a hunt de 30 min).

**Custo de tier 1 como % do pool desde a rodada 5** (`chakra_cost_percent`, `manapercent` no TFS
— `server/tfs/src/spells.cpp:466`/`804`, `mana` tem prioridade se != 0, senão
`(maxMana*manaPercent)/100`): os 5 projéteis tier 1 elementais custam 2,5-3,0% do pool ATUAL do
jogador, não mais um número fixo — resolve estruturalmente o problema da rodada 4 (custo fixo
calibrado pra boss L12-25 era proporcionalmente enorme contra o pool de L5-15) porque o custo
escala automaticamente com o pool em QUALQUER nível. Os outros 49 jutsus (tier 2/3/personal,
custo fixo) tiveram o `chakra_cost` reescalado pela razão pool-novo/pool-antigo no nível de
desbloqueio de cada um — só para preservar a fração custo/pool que as rodadas 2-4 já validaram
(o pool maior, sozinho, teria tornado esses 49 jutsus proporcionalmente mais baratos por
acidente, reabrindo a paridade já calibrada por um efeito colateral não relacionado à mudança).

**Economia de chakra (rodada 3, tier 2/3, ainda válida):** com os custos de tier 2/3 (agora
reescalados pela razão de pool, ver acima — a PROPORÇÃO custo/pool é a mesma da rodada 3), a
rotação de ninjutsu "seca" bem antes dos 30s em quase todo nível. Isso é **intencional, não
bug**: é o mecanismo que faz o burst de tier 2/3 (calibrado pra bater o dano de arma num boss)
não virar DPS sustentado de graça — o resto da luta (que dura minutos contra um boss) é taijutsu.

**Tier 1 (rodada 5)**: cooldown subiu de 3,5s pra **9,0s** e `level_scale` quase dobrou (~3,0 →
~5,3-5,4) — a combinação que fecha burst ≥1,3× em 94 dos 100 níveis (era só L1-30 na rodada 4)
SEM reabrir a paridade de boss (cooldown maior neutraliza o DPS-se-spammado do `level_scale`
maior — ver `balanceamento-relatorio-v5.md` §2 pra prova). Medido numa **hunt de 30 min**
(`tools/balance/sim.py --hunt`), o pior caso agora é **20,7% em L20** (era 97,6%/93,4% em
L5/L15 na rodada 4) — dentro da meta de ≤25% em TODOS os níveis 5-100 testados (de 5 em 5).
Ver relatório v5 §1 — pendência restante: um único nível (L20) fica perto do limite por causa
de um monstro específico com HP acima da média da faixa, não do número do jutsu.

**Pílulas de chakra são simuladas em combate desde a rodada 4** (`_CHAKRA_POTIONS`,
`tools/balance/sim.py --chakra-pills`/`--hunt`): bebidas quando o chakra não basta pro jutsu
escolhido, mesma aproximação de cooldown de 1,0s da poção de vida (o TFS real, `server/tfs/data/
actions/scripts/other/potions.lua:onUse`, **não seta exhaustion nenhuma** pro item). Com pílula,
o tempo sem chakra pro tier 1 cai pra ≤0,4% em todos os níveis 5-100 testados (rodada 5) — bem
dentro da meta de ≤5%; o déficit de "não dá pra bancar pílulas suficiente" que a rodada 4 achou
em L5 deixou de existir (o tier 1 agora raramente precisa de pílula pra começo de conversa).

> **Atualizado na rodada 7** (`docs/sistemas/balanceamento-relatorio-v7.md`): o número "20,7%
> em L20" acima (rodada 5) media o cenário ERRADO a partir de L20 — `pick_ninjutsu_jutsu()`
> abandona o tier 1 assim que o primeiro tier 2 do elemento desbloqueia (L12-26 conforme o
> elemento) e nunca mais volta a conjurá-lo; o número media só o efeito colateral de gastar
> chakra em tier 2/3 (fixo, ~60%+ do pool desde a rodada 5), não uso real do tier 1. Achado
> real desta rodada, confirmado com playtest ao vivo (`docs/qa/playtest-l1-20-r5.md`): o custo
> real do tier 1 (2,5-3,0% do pool) era baixo demais para QUALQUER cooldown/regen razoável
> criar gestão de recurso — 9 casts seguidos sem sair de 108-110/110 no L1. FIX: `chakra_cost_
> percent` subiu ~4,7× (2,5-3,0% → 12-14%, `data/jutsus/{katon,fuuton,raiton,doton,suiton}.json`
> — `cooldown_s`/dano intocados) e `tools/balance/sim.py` ganhou `force_tier1` (novo parâmetro
> de `simulate_hunt`, agora o padrão de `--hunt`) para medir o tier 1 de verdade em todo nível,
> não o que a rotação "racional" escolhe. Resultado: **6-8 casts por pool cheio em TODO nível
> 1-100 e nos 5 elementos** (era 33-55) e recuperação do zero em 73,3-83,3s em qualquer nível
> (era igual — regen não foi tocado). A meta de "15-25% de tempo sem chakra numa hunt híbrida
> sustentada" **não fechou** — achado estrutural: `HYBRID_JUTSU_CADENCE_FRAC=0,22` (rodada 6)
> torna o cast de jutsu tão raro no build híbrido que nenhum custo dentro de 6-8 casts/pool cria
> pressão real (a razão gasto/regen numa hunt de 30 min fica em ~0,24, bem abaixo do ponto de
> transição ≈1 — ver relatório v7 §5 pra prova completa e pro sweep de cooldown/regen que
> descarta as outras duas alavancas dentro dos limites seguros). Sem build híbrido, o mesmo
> custo aplicado a ninjutsu puro (sem o amortecedor) já cria scarcity real (33-72% sem pílula,
> ≤0,1% com pílula) — confirma que o custo em si funciona; o gargalo é só o modelo híbrido.

> **Atualizado na rodada 8** (`docs/sistemas/balanceamento-relatorio-v8.md` §2):
> `HYBRID_JUTSU_CADENCE_FRAC` foi **removida** — o híbrido agora sempre conjura o tier 1 no
> cooldown REAL (sem esticamento artificial), o modelo "castar sempre que libera e tem chakra"
> medido no playtest da rodada 5. No cooldown original (9,0s) isso deixava o híbrido forte
> demais contra boss (até -44% de TTK vs. melhor puro) — o cooldown dos 5 tier 1 subiu para
> **27,0s** (custo do pool inalterado) pra manter o teto de +15%. A meta de 15-25% de tempo sem
> chakra em hunt híbrida **continua não fechando** (0% em todos os níveis) — agora por um motivo
> diferente: "Genin L1 6-8 casts/pool" e essa faixa de scarcity são matematicamente
> incompatíveis sob o custo percentual fixo do pool (o custo que fecharia a scarcity, ×4-6,
> quebra os casts/pool). Priorizado manter "6-8 casts/pool" (item da lista "Manter" da missão) e
> o teto de boss (meta com lever nomeado) sobre a faixa de scarcity.

**Material exclusivo de boss:** `sell_price ≈ 3 × (4.5 * L)` — a Presa da Serpente Branca (L25)
vale 340, contra ~112 de um material comum da mesma faixa. Cai 100% (1–2), então é a renda
garantida da luta; o resto do loot é chance.

**Materiais de drop:** `sell_price ≈ 4.5 * L do monstro que dropa` (120–220 nas Ruínas,
280–420 na Montanha). Com ~45% de chance por kill, o material é ~40% da renda de um spot;
o ryo direto é os outros 60%.

## 6. Jutsus

```
dano_medio(jutsu) ≈ base_damage + level*level_scale + ninjutsu*skill_scale
```

> **Atualizado na rodada 3 de balanceamento** (`docs/sistemas/balanceamento-relatorio-v3.md`):
> a rodada 2 tinha alcançado paridade 1×1 em bosses L12–25, mas o próprio relatório admitia que
> "de L50 em diante o build ninjutsu empata só porque degenera em taijutsu puro" — o magic level
> (= skill "ninjutsu") ficava preso por `manamultiplier=1.3` (`vocation.cpp:149 getReqMana`,
> `tools/export_tfs.py`), crescendo quase reto (~16 no L15 a ~34 no L100) enquanto o dano de
> arma cresce ~40× no mesmo intervalo. FIX: **`manamultiplier=1.1`** (igual às outras skills,
> `data/skills.json`) faz o magic level crescer de ~23 (L5) a ~83 (L100) — mesma ordem de
> grandeza do taijutsu (skill ~40→~101) — e o `level_scale`/`skill_scale` de todo jutsu tier 2/3
> foi recalibrado em cima dessa mudança (o "jutsu de Kage" agora escala de verdade com o nível:
> `level_scale` de tier 3 subiu 5–7,5× sobre o valor pós-rodada-2). O `chakra_cost` de tier 2/3
> também subiu (~2,4–3,5×) para que o burst continue pago por um recurso finito, não de graça —
> ver relatório v3 §2–3 pro raciocínio completo (por que baixar só o `manamultiplier` sem
> recalibrar as escalas OU sem subir o chakra teria quebrado o 1×1 pra outro lado). `raiton`
> ganhou um tier 3 de verdade no kit (`raiton_punho_trovao` trocou de lugar com
> `raiton_armadura_eletrica` em `data/element_sets.json`) — sem isso, o elemento não tinha como
> acompanhar katon/doton/fuuton em L50+ (só `suiton` continua sem tier 3 no kit, por design; seu
> tier 2 `suiryuudan` recebeu compensação extra).

> **Atualizado na rodada 4** (`docs/sistemas/balanceamento-relatorio-v4.md`): o tier 1 (o
> projétil básico de cada elemento, escolhido pela rotação 1×1 desde a rodada 1) tinha
> cooldown IGUAL ao intervalo de ataque do player (2,0s) — a rodada 3 provou matematicamente que
> isso torna "burst sentido" (hit ≥1,3× o hit de arma) e "paridade sustentada" incompatíveis
> (se os cooldowns são iguais, `dano_tier1 ≈ dano_arma` por hit, nunca 1,3×). FIX: **cooldown
> 2,0s→3,5s** nos 5 projéteis tier 1 (`katon_goukakyuu`, `fuuton_lamina_vento`, `raiton_hari`,
> `doton_bala_lama`, `suiton_mizudan`) — com cooldown maior que o da arma, os dois lados da
> tensão se destravam ao mesmo tempo (ver relatório v4 §2 pra prova). `base_damage`/`level_scale`
> subiram bem mais que `skill_scale` (o magic level não é confiável o bastante numa faixa tão
> ampla — nível puro é o lever principal) e `chakra_cost` subiu ~2× (25-30, contra 12-15 antes)
> — não mais que isso, porque um custo maior (testado até 12× nesta rodada) quebra a
> sustentabilidade de uma **hunt de 30 min** em L5-15 (ver acima) sem resolver totalmente a
> paridade sustentada em boss (a causa raiz virou outra: L19 é o único boss testado onde o
> elemento com vantagem só tem o tier 1 desbloqueado — ver relatório v4 §10). 3 dos 8 tier 2 do
> kit automático (`katon_housenka`, `fuuton_rajada_cortante`, `raiton_lanca_relampago`) tinham
> cooldown abaixo de 6s — subidos pra 6,0-6,5s com dano escalado pelo MESMO fator (preserva o
> DPS já calibrado na rodada 3, só o hit fica maior e o cast mais espaçado). O **híbrido** ganhou
> um modelo novo: arma e jutsu em cadências independentes (arma ataca no intervalo normal, jutsu
> lança por cima sempre que pronto/pagável — "arma entre casts" de verdade, não só design) —
> isso tornou o híbrido sistematicamente ≥ os builds puros (nunca mais atrás), ao custo de
> exceder o teto de +15% em vários bosses (pendência, ver relatório v4 §10).

> **Atualizado na rodada 5** (`docs/sistemas/balanceamento-relatorio-v5.md`): tier 1 recalibrado
> de novo nas 3 dimensões (custo, dano, cooldown), desta vez motivado pela ECONOMIA de chakra
> (item 1 da missão), não só pela paridade. Custo virou **`chakra_cost_percent`** (2,5-3,0% do
> pool, `manapercent` no TFS) em vez de `chakra_cost` fixo — resolve a hunt de 30 min (pior caso
> caiu de 97,6% pra 20,7% de tempo sem chakra, ver `balanceamento.md` §5.1 acima). Cooldown
> **3,5s→9,0s** e `level_scale` quase dobrou (~3,0→~5,3-5,4) — a combinação que fecha burst
> ≥1,3× em 94 dos 100 níveis (era só L1-30) sem reabrir a paridade de boss (cooldown maior
> neutraliza o DPS-se-spammado do `level_scale` maior — prova em relatório v5 §2). Os 6 bosses
> de referência (ninjutsu puro) ficaram TODOS dentro de -15%..+10% (era 4 de 6). Os outros 49
> jutsus (tier 2/3/personal) só tiveram `chakra_cost` reescalado pela razão de pool — nenhum
> dano tocado, preservando a calibração das rodadas 2-4.

> **Atualizado na rodada 6** (`docs/sistemas/balanceamento-relatorio-v6.md`): o híbrido excedia
> o teto de +15% em 4 dos 6 bosses de referência — causa raiz NOVA identificada: 2 jutsus tier 1
> de área (`raiton_corrente_estatica`/`suiton_nevoa_cortante`, cooldown 1,3s/1,6s, pensados como
> controle desde a rodada 3) tinham `dano/cooldown` alto o bastante pra virar picks de DPS
> não-intencionais — cooldown subiu pra **3,0s** (igual ao irmão `katon_sopro_brasas`). Isso só
> resolveu parte; o resto exigiu um parâmetro de MODELO novo, não um número de jutsu:
> `HYBRID_JUTSU_CADENCE_FRAC=0,22` (`tools/balance/sim.py`) estica o cooldown EFETIVO do jutsu
> só pro build híbrido (arma continua na cadência cheia) — modela que um jogador que divide
> atenção entre arma e jutsu não aproveita TODA janela de cast livre entre golpes (cabem 4-5
> golpes de arma no cooldown de 9,0s do tier 1; o híbrido só "acerta o timing" de ~1 em 4-5). O
> ninjutsu PURO não é afetado (já paga o custo de rotação certo). Resultado: 6 de 6 bosses de
> referência dentro do teto (era 2 de 6), burst matematicamente inalterado (não depende de
> cooldown). Verificado também: `groupcooldown` (`spells.cpp:429/583`, `CONDITION_
> SPELLGROUPCOOLDOWN`) NÃO bloqueia o ataque básico de arma — só outro jutsu do mesmo grupo —
> `CONDITION_EXHAUST_WEAPON`/`_COMBAT` estão "unused" nesta build do TFS 1.4.2; não é o lever do
> híbrido, subido de 1000ms→2000ms só como piso de segurança (inerte pro kit atual).

> **Atualizado na rodada 7** (`docs/sistemas/balanceamento-relatorio-v7.md`): tema único "o
> chakra voltou a não ser um recurso" — playtest ao vivo (`docs/qa/playtest-l1-20-r5.md`)
> confirmou que com 2,5-3,0% do pool (rodada 5), 9 casts seguidos de tier 1 no L1 não tiravam o
> chakra de 108-110/110. FIX: `chakra_cost_percent` dos 5 projéteis tier 1 subiu ~4,7× (2,5-3,0%
> → **12-14%**), preservando a proporção relativa entre elementos — `cooldown_s`/`base_damage`/
> `level_scale`/`skill_scale` (burst) **intocados**. Resultado: **6-8 casts por pool cheio em
> TODO nível 1-100** (era 33-55) e recuperação do pool do zero em 73,3-83,3s (era igual — regen
> não mudou). `tools/balance/sim.py` ganhou duas métricas analíticas novas
> (`casts_per_full_pool`/`time_to_refill_pool_s`) e um achado de modelo: `pick_ninjutsu_jutsu()`
> abandona o tier 1 assim que o primeiro tier 2 do elemento desbloqueia (L12-26), então a
> métrica antiga de "tempo sem chakra" media o custo de tier 2/3 em L20+, não o tier 1 — novo
> parâmetro `force_tier1` (default de `--hunt` agora) conjura sempre o tier 1 pra medir o
> cenário certo. Avaliado e **descartado**: `cooldown_s` 9,0s→6,0s não muda nada no build
> híbrido (o amortecedor `HYBRID_JUTSU_CADENCE_FRAC=0,22` da rodada 6 domina a conta — só
> cooldowns abaixo de 2,0s, inviáveis, criariam pressão real, e quebrariam a paridade de boss).
> A meta de "15-25% de tempo sem chakra numa hunt híbrida sustentada, todo nível 5-100" **não
> fechou** por esse mesmo motivo estrutural (build ninjutsu puro, sem o amortecedor, já mostra
> 33-72% — confirma que o custo funciona; só o modelo híbrido neutraliza). Boss parity (6/6),
> burst (94/100) e personagens (9/9 dentro de ±15%, cancelamento algébrico do custo na fórmula
> `valor()`) confirmados **inalterados**.

> **Atualizado na rodada 8** (`docs/sistemas/balanceamento-relatorio-v8.md` §2-3):
> `HYBRID_JUTSU_CADENCE_FRAC` **removida** — o híbrido agora conjura o tier 1 sempre que
> pronto/pagável, no cooldown REAL (sem esticamento). Isso obrigou subir o `cooldown_s` do tier 1
> de **9,0s para 27,0s** (custo do pool inalterado) pra manter o teto de +15% — testado e
> descartado usar o custo (precisaria de ×4-6, quebrando "Genin L1 6-8 casts/pool"). A meta de
> scarcity em hunt híbrida (15-25%) continua em 0% — conflito estrutural com "6-8 casts/pool",
> não uma questão de achar o custo certo. Grupo 3+: `katon_anel_chamas` (dano ×1,2) e
> `fuuton_rajada_cortante`/`fuuton_tornado_cortante` (dano ×0,65 cada) recolocaram `ruin_puppet`/
> `thunder_eagle` em +30-60% sobre taijutsu (a rodada 7 tinha derrubado `ruin_puppet` a +3,7% como
> efeito colateral do custo de tier 1 — ver §3 do relatório).

Escala por tier (com `required_level` de referência e ninjutsu = magic level real, ver acima):

| Tier | base_damage | level_scale | skill_scale | chakra | cooldown |
|---|---|---|---|---|---|
| 1 projétil (pós-rodada-9) | 3,7–4,3 | 5,25–5,40 | 0,110–0,120 | **12-14% do pool** (inalterado desde a rodada 7; era 2,5-3,0% na r5, 25-30 fixo antes) | **9,0 s** (subiu pra 27,0s na rodada 8 pra manter o antigo teto de híbrido ≤+15%; o orquestrador REJEITOU esse cooldown pós-rodada-8 — "um jutsu por meio minuto destrói a sensação de ninja" — e voltou a 9,0s; não existe mais teto de híbrido, ver `balanceamento-relatorio-v9.md`) |
| 1 área/self | 4,9–5,6 (área) / 0 (self) | 0,315 | 0,21–0,245 | 14–28 | 1,3–3,0 s (2 jutsus tier 1 de área — `raiton_corrente_estatica`/`suiton_nevoa_cortante` — subiram de 1,3-1,6s pra **3,0s** na rodada 6, ver acima) |
| 2 "normal" (katon/doton/fuuton, tem tier 3 atrás) | 24,3–43,2 (`katon_anel_chamas` subiu de 36,0 pra **43,2** na rodada 8, ver `balanceamento-relatorio-v8.md` §3) / 16–37,8 (os demais) | 1,596–3,886 | 0,585–1,17 / 0,63–0,9 | 105–147 | **6,0–6,5 s** (3 subiram de 4,0-5,5s na r4) |
| 2 "teto do elemento" (raiton/suiton, sem tier 3 no kit) | 39,6–71,8 | 1,35–7,05 | 0,5–0,72 | 140–158 | 5,5–6,0 s |
| 3 | 54–86 | 9,0–11,9 | 0,18–0,37 | 175–400 | 7,0–9,0 s |

> **Rodada 9**: `raiton_punho_trovao` (chakra 200→**320**) e `doton_colapso_terreno` (chakra
> 268→**400**, `level_scale`×0,9, `base_damage`×0,9) recalibrados — com o cooldown do tier 1 de
> volta a 9,0s (não mais 27,0s), o híbrido virou a referência e passou a ser possível medir
> "ninjutsu puro excede o híbrido" de verdade pela primeira vez: esses 2 jutsus tier 3, ao
> desbloquear (L30/L48), permitiam a ninjutsu puro um único cast que já superava metade do HP do
> monstro comum mais próximo daquele nível — mais rápido que o híbrido inteiro (proibido pela
> meta 4). Custo sozinho resolveu `raiton_punho_trovao` (o segundo cast fica inacessível);
> `doton_colapso_terreno` precisou também de corte de dano (um único cast já era grande demais
> pro custo isolar). Ver `balanceamento-relatorio-v9.md` §4.2.

Regras que mantêm o tier 3 sendo o "show" sem virar obrigatório:
- **dano por chakra** cai de tier 1 pra tier 3, mas o **dano por cooldown** sobe — tier 3 é
  burst, tier 1 é sustentado. Na rodada 3 essa diferença ficou bem mais extrema (chakra de tier
  3 sobe pra ~245 contra pool de 50+level×10 — um Kage L100 tem 1050 de chakra e dá ~5 casts de
  tier 3 antes de secar, ~40s de burst puro numa luta que dura 100s+; o resto é taijutsu).
- Formas de área custam ~30% mais chakra que um projétil de dano equivalente.
- Jutsus `self` não causam dano; o custo compra sobrevivência (`heal_over_time`).
- Multiplicador elemental (×1.5 / ×0.75) é aplicado **depois**, então uma vantagem
  elemental vale mais que subir um tier — isso é intencional e é o que faz o jogador
  trocar de jutsu por área em vez de spammar o mais caro.
- Em grupo (pull de N monstros), a rotação escolhe o jutsu de maior `(dano×hits)/cooldown` —
  é aí que tier 2/3 (área/beam) compensam o dano/cooldown menor que tier 1: cada hit extra
  (até `min(N, area_capacity(shape))` alvos) multiplica o valor do cast inteiro. Na rodada 3
  isso ficou forte demais em alguns pulls pequenos com HP baixo (ver relatório v3 §6/§10 —
  o mesmo número calibrado pro 1×1 de boss vira "apaga o grupo inteiro num cast só" quando o
  grupo tem pouco HP total).

### Jutsus novos criados (Personagem + Elemento: 4 + 4)

Fechando os `element_sets.json` (doton tinha só 3 jutsus, fuuton só 2) e as 36 vagas de
`personal_jutsus` (9 personagens × 4), com a curva de tier acima.

**Elementais (`data/jutsus/doton.json`, `data/jutsus/fuuton.json`):**

| id | Tier | Tipo | chakra | cooldown_s | base_damage | level_scale | skill_scale | Efeito |
|---|---|---|---|---|---|---|---|---|
| `doton_bala_lama` | 1 | projectile | 14 | 2,0 | 8,05 | 0,385 | 0,297 | slow 30% / 3s |
| `fuuton_tornado_cortante` | 3 | beam (line_6) | 217 | 8,0 | 54,0 | 10,8 | 0,086 | slow 60% / 4s |
| `fuuton_redemoinho_prisao` | 2 | target (controle) | 38 | 9,0 | 18,0 | 0,72 | 0,9 | paralyze 75% / 3s |

(valores pós-rodada-3 pro `fuuton_tornado_cortante` — era o jutsu tier 3 "nunca escolhido" da
rodada 2; agora é o pick real de fuuton em bosses L54-100, ver relatório v3 §4. Os outros dois,
inalterados desde a rodada 2 — ver nota acima da tabela de escala por tier. **`doton_bala_lama`
foi recalibrado na rodada 5, com o custo reajustado de novo na rodada 7 e o cooldown na rodada
8** junto com os outros 4 projéteis tier 1 elementais — valores atuais
`chakra_cost_percent=13,0%`/`cooldown_s=27,0`/`base_damage=4,0`/`level_scale=5,35`/
`skill_scale=0,115`, ver tabela de escala por tier acima e `data/jutsus/doton.json`; a linha
acima fica como registro histórico de quando o jutsu foi criado, não como valor atual.)

`doton_bala_lama` fecha a categoria "projétil básico" que faltava no elemento (os outros 3
jutsus de doton já existiam: muralha de pedra self, estacas de terra área, colapso do terreno
área forte). `fuuton_tornado_cortante` e `fuuton_redemoinho_prisao` fecham "beam/linha forte"
e "utilitário/controle" que faltavam em fuuton (só existiam projétil e área).

> **Atualizado na rodada 2**: `base_damage`/`level_scale`/`skill_scale` de 11 desses jutsus
> mudaram pra equilibrar o "valor total dos 4 jutsus pessoais" entre os 9 personagens (meta
> ±15%, ver `balanceamento-relatorio-v2.md` §7 — a tabela abaixo mantém os valores originais de
> quando cada jutsu foi criado; `data/jutsus/personal.json` é sempre a fonte da verdade).

> **Reverificado na rodada 6** (`balanceamento-relatorio-v6.md` §3): o script de proxy original
> (`analyze_v2.py`) não sobreviveu entre sessões — a métrica foi reconstruída a partir da
> descrição dos relatórios anteriores. Achado real (não introduzido nesta rodada):
> `sabio_cerimonial` estava a **+88,4%** da média — `selo_de_exorcismo`/`circulo_de_selos`
> (dano ~396/~429 em L19/L27) chegavam a quase 3× o dano de qualquer jutsu elemental do mesmo
> nível pós-rodada-5. Nerf ×0,4 nesses dois; isso deslocou `herdeira_hyuga` pra fora por cima
> (a média cai quando o maior outlier é corrigido), corrigido com nerf ×0,7 em
> `palma_gentil`/`palma_dupla` (não-compartilhados dela). Os 9 personagens ficaram entre
> −11,8% e +8,6% da média.

**Pessoais (`data/jutsus/personal.json`, 20 jutsus — 16 restantes das 36 vagas reusam jutsus
já existentes, ver `docs/sistemas/vilas-e-clas.md`):**

| id | Tier | Tipo | chakra | cooldown_s | base_damage | Efeito |
|---|---|---|---|---|---|---|
| `fuuton_rasteira_vento` | 1 | area (cone_2) | 14 | 3.0 | 55,7 (pós-r3) | slow 40% / 2s |
| `vigor_teimoso` | 1 | self | 30 | 18.0 | 0 | heal_over_time 7/s por 6s |
| `foco_ocular` | 1 | self | 26 | 14.0 | 0 | heal_over_time 5/s por 5s |
| `agulhas_incendiarias` | 1 | projectile | 14 | 2.0 | 19 | burn 30% / 4s |
| `contra_ataque_calculado` | 2 | target | 20 | 6.0 | 28 | stun 30% / 1s |
| `soco_monstruoso` | 2 | target | 24 | 4.0 | 34 | stun 35% / 1s |
| `palma_gentil` | 1 | target | 16 | 2.0 | 22 | slow 30% / 3s |
| `visao_total` | 1 | self | 22 | 16.0 | 0 | heal_over_time 5/s por 5s |
| `palma_dupla` | 2 | area (cone_2) | 36 | 5.0 | 38 | paralyze 40% / 1.5s |
| `soco_da_juventude` | 2 | target | 26 | 4.5 | 36 | stun 30% / 1s |
| `chute_ascendente` | 1 | target | 16 | 2.5 | 20 | slow 30% / 2s |
| `lamina_relampago_pessoal` | 1 | target | 22 | 2.2 | 26 | paralyze 20% / 1s |
| `corte_duplo` | 2 | area (cone_2) | 32 | 4.5 | 32 | — |
| `bainha_eletrica` | 2 | self | 34 | 16.0 | 0 | heal_over_time 9/s por 8s |
| `kunai_marcada` | 1 | projectile | 14 | 1.8 | 18 | — (marca alvo p/ `salto_do_selo`) |
| `salto_do_selo` | 1 | self | 28 | 10.0 | 0 | teleporte até a marca |
| `explosao_do_selo` | 2 | area (circle_r1) | 46 | 7.0 | 48 | stun 40% / 1s |
| `barreira_protetora` | 2 | self | 38 | 18.0 | 0 | heal_over_time 9/s por 8s |
| `selo_de_exorcismo` | 2 | target | 34 | 6.0 | 109,2 (pós-r3) | paralyze 40% / 2s |
| `circulo_de_selos` | 2 | area (circle_r2) | 44 | 8.0 | 94,6 (pós-r3) | paralyze 50% / 2.5s |

Todos seguem a regra da seção acima: `self`/utilitário sem dano compra sobrevivência
(`heal_over_time`) ou controle (`paralyze`/`stun`/`slow`), nunca os dois ao mesmo tempo; tier 2
custa ~2× o chakra do tier 1 pelo dobro (ou mais) de `base_damage`. `fuuton_rasteira_vento`/
`selo_de_exorcismo`/`circulo_de_selos` tiveram `base_damage`/`level_scale` reajustados na rodada
3 (ver relatório v3 §7) porque o `manamultiplier` menor mudou o "preço" implícito de jutsus
utilitários usados como proxy de valor — não porque o design do personagem mudou.

## 7. Distribuição elemental por área

Toda área tem pelo menos 3 elementos diferentes para que o ciclo elemental importe e
nenhuma vila limpe uma zona inteira com vantagem:

| Área | Elementos presentes | Vila mais favorecida | Vila mais punida |
|---|---|---|---|
| Floresta | none, doton, katon (boss) | Nuvem (raiton > doton) | — |
| Floresta da Morte | suiton, none, doton | Folha (katon vs suiton é desvantagem) | Nuvem |
| Ruínas do Clã | none, doton, raiton, katon, fuuton (boss) | Nuvem e Areia | Folha |
| Montanha do Trovão | raiton, suiton, fuuton, katon | Areia e Névoa | Nuvem |

## 8. Premissas a validar no playtest

1. `[PLACEHOLDER]` 4–7 kills por level é o ritmo alvo. Se a sessão média for de 20 min,
   isso dá ~2–3 levels por sessão em L27 e ~1 level em L74 — confirmar se a queda é sentida
   como progressão ou como parede.
2. `[PLACEHOLDER]` Dano de 8–12% do HP assume que o player tem defesa de equipamento da
   faixa. Sem set completo, o mesmo monstro bate ~18% — checar se isso é uma barreira justa
   de gear ou uma frustração.
3. `[PLACEHOLDER]` Bosses a 7–8× o HP normal com dano só ~10% acima duram ~4 min de luta.
   Se durar mais que 6 min sem mudar nada, é HP demais, não dano de menos.
4. `[PLACEHOLDER]` A economia foi modelada só pelas fontes de PvM. Missões sequenciais
   somam ~24.000 ryo nas Ruínas e ~62.000 na Montanha — o suficiente para ~1 peça de set
   por área, que é o alvo. Recompensa de missão não deve pagar o set inteiro.


> **Rodada 9 (2026-09-05)**: regeneração de chakra passou de `3+floor(level/4)` para `2+floor(level/4)` a cada 2 s (1,0/s no L1, 3,5/s no L20) para o chakra voltar a ser recurso; cooldown do tier 1 fica em 9 s (não mais 27s — decisão do orquestrador no fim de `balanceamento-relatorio-v8.md`). O teto "híbrido ≤+15%" foi removido de vez — ver a nova seção "Metas de balanceamento (rodada 9)" no topo deste documento e `balanceamento-relatorio-v9.md` pro detalhe completo: bosses (`boss_bandit_chief`/`boss_mist_swordsman`/`boss_white_serpent`) tiveram `defense` reduzida (12→6/15→8/18→9) e `boss_mist_swordsman` teve `hp` +40% (1700→2380) pra fechar TTK híbrido 60-180s e viabilidade de puro ≥60% ao mesmo tempo; `raiton_punho_trovao`/`doton_colapso_terreno` (tier 3) recalibrados pra ninjutsu puro nunca exceder o híbrido.
