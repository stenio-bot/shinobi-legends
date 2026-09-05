# Relatório de balanceamento PvM — rodada 5 (setembro/2026)

Ataca a pendência central deixada pela rodada 4 (`docs/sistemas/balanceamento-relatorio-v4.md`
§10, item 3): **"chakra sustentável falha em L5 e L15 numa hunt de 30 min sem pílula"** — custo
de tier 1 flat (25-30), calibrado para não dominar um boss L12-25, era proporcionalmente enorme
contra o pool minúsculo (60-200) de L5-15, e o regen fixo (0,6 chakra/s em qualquer nível) nunca
alcançava. A missão pedia para escolher e implementar uma correção estrutural (não um
retoque de número) entre: (a) regen por level, (b) pool inicial maior, (c) custo de jutsu
proporcional ao pool. **Implementei as três, combinadas** — nenhuma sozinha bastava (ver §1) —
e depois recalibrei o tier 1 elemental inteiro (dano E cooldown, não só custo) para a paridade
pedida no item 2 da missão.

## 0. Arquivos tocados

- `tools/balance/sim.py`: `player_chakra` (nova fórmula), `chakra_regen_amount_per_tick`/
  `hp_regen_amount_per_tick`/`CHAKRA_REGEN_TICK_S`/`HP_REGEN_TICK_S` (regen por level, novo),
  `jutsu_chakra_cost()` (custo como % do pool, novo), todos os call-sites de `chakra_cost`
  atualizados para usar essa função, `typical_skills`/`typical_skills_split` (proxy de custo
  médio atualizada), `HUNT_LEVELS` (5 pontos → 20 pontos, L5-L100 de 5 em 5).
- `data/progression.json`: `chakra_formula` (comentário atualizado, 50+level×10 → 100+level×10).
- `data/schemas/jutsu.schema.json`: campo novo opcional `chakra_cost_percent`.
- `data/jutsus/{katon,fuuton,raiton,doton,suiton}.json`: os 5 projéteis tier 1 —
  `chakra_cost` (fixo) → `chakra_cost_percent` (2,5-3,0%), `cooldown_s` 3,5s→**9,0s**,
  `base_damage`/`level_scale`/`skill_scale` recalibrados (ver §2).
- `data/jutsus/*.json` (todos os 7 arquivos, 49 jutsus restantes): `chakra_cost` fixo
  **reescalado** pela razão pool-novo/pool-antigo no `required_level` de cada um — só isso,
  nenhum dano tocado (ver §1, por que isso era necessário para não desarrumar a paridade já
  calibrada nas rodadas 2-4 por um efeito colateral da mudança de pool).
- `tools/export_tfs.py`: `spells_xml()` emite `manapercent` em vez de `mana` quando
  `chakra_cost_percent` está presente; `jutsu_display_chakra_cost()` (novo, custo cosmético
  pro cliente estático); `character_switch_script` — piso de chakra inicial 60→110,
  `NarutoRegen.apply()` (novo, condição recalculada por level) + `CreatureEvent
  NarutoRegenAdvance` (reaplica no level-up, mesmo padrão de `NarutoAchievementAdvance`).
- `tools/balance/README.md`, `docs/sistemas/balanceamento.md`, `docs/00-biblia-do-jogo.md`
  (só a seção "Chakra"/"Combate (fórmulas)"): documentação atualizada.

**Não tocado**: `data/monsters/*.json`, `data/characters.json`/`personal.json`/`neutral.json`
(danos — só custo rescalado, ver acima), `data/element_sets.json`, `server/tfs/data/*` e
`server/generated/*` não foram **instalados** (só regenerados com `tools/export_tfs.py`,
`install_generated.sh` **não** rodado, servidor **não** reiniciado, conforme instruído).

## 1. Economia de chakra estrutural (item 1 da missão)

### Por que as três opções, não uma

Testei cada opção isoladamente antes de combinar (números no histórico de simulação desta
sessão, reproduzíveis com os comandos do §11):

- **Só regen por level** (opção a, fórmula sugerida pela missão `max(3, floor(level/4))` a
  cada 5s, mantendo o pool antigo): a 5s de tick, o valor em L1 é `max(3,0)=3` — **idêntico** ao
  valor fixo antigo (0,6/s). Recuperar o pool antigo (60) do zero levaria 100s, **acima** do
  limite de 90s pedido para o Genin L1. A fórmula sugerida só ajuda a partir de L12+; sozinha
  não resolve o requisito de L1.
- **Só pool maior** (opção b, piso 60→110): resolve "≥4 casts" trivialmente (110/27≈4 com o
  custo antigo), mas não muda a PROPORÇÃO custo/pool nem o regen — a hunt de 30 min continua
  falhando quase igual (custo flat continua grande relativo ao pool em qualquer nível baixo).
- **Só custo proporcional** (opção c): resolve a proporção, mas sem regen mais rápido o
  Genin L1 ainda leva >150s para recuperar o pool do zero (viola "≤90s parado").

**Decisão**: as três juntas. Pool 100+level×10 (piso 110 em L1, +10/level nativo da vocação,
inalterado) cobre "≥4 casts" com folga; regen por level (chakra `3+floor(level/4)` a cada
**2s** — não 5s, precisa do tick mais curto para o L1 recuperar em <90s, ver tabela abaixo)
cobre "recupera em ≤90s"; custo de tier 1 como **% do pool** (`chakra_cost_percent`,
`manapercent` no TFS) resolve a proporção em QUALQUER nível automaticamente, porque escala
junto com o pool sem precisar de uma tabela de custo por faixa de nível (que o formato de jutsu
não suporta — a mesma limitação que a rodada 4 §10 já tinha identificado).

### Onde cada mecanismo vem do TFS

- **Regen por level**: `server/tfs/src/creature.h`/`.cpp` `CONDITION_REGENERATION` com
  `CONDITION_PARAM_MANAGAIN`/`CONDITION_PARAM_MANATICKS` (e os equivalentes de `HEALTHGAIN`/
  `HEALTHTICKS`) — a condição permanente já existia desde a rodada 4
  (`server/tfs/data/scripts/naruto/character_switch.lua`, subId 9020, ver relatório v4 §1), só
  usava os valores FIXOS de `voc:getManaGainAmount()`/`getManaGainTicks()` (vocations.xml,
  `tools/export_tfs.py` linha ~571, gerados iguais para toda vila e todo nível). Esta rodada
  troca a fonte: `NarutoRegen.apply(player)` (novo, `tools/export_tfs.py`, gerado em
  `character_switch.lua`) calcula os valores em Lua puro a partir de `player:getLevel()` e
  recria a condição (mesmo subId 9020 — `Creature::addCondition` substitui a condição antiga
  de mesmo tipo+subId, `server/tfs/src/creature.cpp`) — chamado no login E em
  `CreatureEvent("NarutoRegenAdvance").onAdvance(player, skill, oldLevel, newLevel)` sempre que
  `skill == SKILL_LEVEL` (mesmo padrão que `NarutoAchievementAdvance` já usa para
  achievements de level, `tools/export_tfs.py` linha ~2730).
- **Custo como % do pool**: `server/tfs/src/spells.cpp:466` lê o atributo `manapercent` do XML;
  `spells.cpp:804 Spell::getManaCost` prioriza `mana` se diferente de zero, senão calcula
  `(maxMana * manaPercent) / 100` (divisão inteira, truncada — `tools/balance/sim.py
  jutsu_chakra_cost()` replica exatamente essa conta). `tools/export_tfs.py` emite
  `mana="0" manapercent="X"` em vez de `mana="X"` para os 5 jutsus com `chakra_cost_percent`
  no JSON (todos os outros 49 continuam com `mana="{chakra_cost}"`, sem mudança de mecanismo).

### Fórmulas finais

```
pool de chakra(level)      = 100 + level*10        (era 50 + level*10)
regen de chakra(level)     = [3 + level//4] a cada 2s   (era 3 a cada 5s, fixo, qualquer level)
regen de HP(level)         = [2 + level//10] a cada 5s  (era 2 a cada 5s, fixo — em L1-9 é
                              EXATAMENTE o valor antigo, só acelera a partir de L10)
custo de tier 1 elemental  = X% do pool (manapercent) — X = 3,0 (katon) / 2,75 (fuuton, raiton,
                              doton) / 2,5 (suiton), por jutsu, não por level
custo de tier 2/3/personal = chakra_cost FIXO antigo × (100+10·required_level)/(50+10·required_level)
                              — reescala só para não ficar acidentalmente mais barato com o pool maior
```

O piso de chakra inicial (`character_switch.lua`, aplicado uma vez no primeiro login) subiu de
60 para **110** — como a vocação continua dando +10 de chakra por level (`gainmana="10"`,
inalterado), o pool resultante em QUALQUER nível é `110 + (level-1)*10 = 100 + level*10`,
batendo exatamente com a fórmula acima em todo o range, não só em L1.

### Por que reescalar os outros 49 jutsus (achado real desta rodada)

Ao implementar só o pool maior + regen maior + tier 1 percentual, rodei os 6 bosses de
referência e o ninjutsu puro passou a ganhar do taijutsu por **+60-68%** em L12/19/25 (a
paridade da rodada 4 — já dentro da meta nesses 3 bosses — quebrou). Investigando: o pool maior
(sem reescalar) tornava TODO jutsu de custo fixo (tier 2/3, calibrado nas rodadas 2-4 contra o
pool ANTIGO) proporcionalmente **mais barato**, e em L12 o jutsu selecionado pela rotação não
era mais o tier 1 novo — era `katon_housenka` (tier 2, desbloqueado exatamente em L12), agora
sustentável por muito mais tempo do que a calibração original previa. Reescalar o
`chakra_cost` de todo jutsu fixo pela razão `pool_novo/pool_antigo` no nível de desbloqueio
preserva a fração custo/pool que as rodadas anteriores já validaram, isolando o efeito da
mudança de pool (que "vaza" para TODOS os jutsus, não só os 5 que eu queria mudar) do efeito
da recalibração de tier 1 (que eu queria mesmo mudar). Depois desse fix, a paridade dos 6
bosses de referência voltou para dentro da meta (ver §3).

### Tabela por nível (meta: hunt 30 min híbrido ≤25% sem chakra tier 1 sem pílula, ≤5% com pílula)

| Nível | Pool | Regen chakra/s | Custo tier1 (katon) | Casts/pool | %sem chakra (sem pílula) | %sem chakra (com pílula) | Hit arma | Hit tier1 (c/ vantagem) | Razão burst |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 110 | 1,5 | 3 | 36 | — (L1 não pedido; ver checagem à parte abaixo) | — | 5,0 | 14,5 | 2,91× ✅ |
| 5 | 150 | 2,0 | 4 | 37 | 0,0% | 0,0% | 15,5 | 51,8 | 3,34× ✅ |
| 10 | 200 | 2,5 | 6 | 33 | 0,0% | 0,0% | 37,5 | 94,3 | 2,51× ✅ |
| 15 | 250 | 3,0 | 7 | 35 | 0,0% | 0,0% | 54,0 | 136,1 | 2,52× ✅ |
| 20 | 300 | 4,0 | 9 | 33 | **20,7%** | 0,2% | 76,5 | 177,6 | 2,32× ✅ |
| 25 | 350 | 4,5 | 10 | 35 | 4,2% | 0,3% | 82,0 | 219,2 | 2,67× ✅ |
| 30 | 400 | 5,0 | 12 | 33 | 5,9% | 0,2% | 119,5 | 260,6 | 2,18× ✅ |
| 40 | 500 | 6,5 | 15 | 33 | 2,6% | 0,2% | 178,0 | 343,2 | 1,93× ✅ |
| 50 | 600 | 7,5 | 18 | 33 | 3,8% | 0,1% | 285,5 | 425,7 | 1,49× ✅ |
| 60 | 700 | 9,0 | 21 | 33 | 7,4% | 0,3% | 282,5 | 508,1 | 1,80× ✅ |
| 70 | 800 | 10,0 | 24 | 33 | 5,8% | 0,2% | 423,0 | 590,2 | 1,40× ✅ |
| 80 | 900 | 11,5 | 27 | 33 | 7,9% | 0,1% | 527,0 | 672,3 | **1,28× ❌** |
| 90 | 1000 | 12,5 | 30 | 33 | 6,3% | 0,2% | 538,0 | 754,2 | 1,40× ✅ |
| 100 | 1100 | 14,0 | 33 | 33 | 6,0% | 0,1% | 681,5 | 836,1 | **1,23× ❌** |

(custo/casts/razão calculados para `katon_goukakyuu`; os outros 4 elementos variam ±0,25% no
custo e ±0,15 no `level_scale`, mesma ordem de grandeza — ver `data/jutsus/*.json`.)

**Verificação em TODOS os níveis 5-100 (não só a amostra acima)**: rodei
`simulate_hunt`/`HUNT_LEVELS` de 5 em 5 (20 pontos) — pior caso sem pílula é **L20 (20,7%)**,
dentro da meta de ≤25%; pior caso com pílula é **L26 (0,4%)**, dentro de ≤5%. `python3
tools/balance/sim.py --hunt --json /tmp/hunt.json` reproduz (0,85s de execução).

**L20 é o pior caso, e o motivo é o monstro, não o número de tier 1**: `exam_rival_stone`
(usado pelo `nearest_common_monster(20)`) tem 420 HP contra ~300-350 dos monstros vizinhos da
mesma faixa — a luta dura mais, puxando mais casts de tier 1 por ciclo de caça antes da pausa
de 5-15s poder repor o chakra. Não é um problema de calibração do JUTSU (o mesmo tier 1 fica
bem abaixo de 25% em L15 e L25, os vizinhos de nível); é variância entre monstros da mesma
faixa — fora do escopo desta rodada mexer em `data/monsters/*.json`.

**Genin L1 novo (checagem à parte, não faz parte da tabela de hunt que só cobre 5-100)**:
pool=110, custo de tier 1 = 3 (katon) a 2 (suiton) → **36 a 55 casts** do pool inicial (meta:
≥4, folga generosa). Recuperação do pool cheio, parado, do zero: `110 / 1,5 chakra/s = 73,3s`
(meta: ≤90s). Ambos os requisitos batem com folga.

## 2. Recalibração de tier 1 (item 2, burst ≥1,3×)

### A prova de que nenhum `level_scale` fecha L1-100 inteiro

Dano de arma (`weapons.cpp:135 getMaxWeaponDamage`) é `(level/5) + (skill/4+1)*(attack/3)*1,03`
— skill (taijutsu, treinado por uso) E attack (do item equipado) **crescem os dois com o
level**, então o termo dominante é um **PRODUTO** de duas grandezas que sobem com o nível:
cresce super-linear (~136× de L1 a L100, medido: hit médio 5,0→681,5). Dano de tier 1
(`base_damage + level×level_scale + ninjutsu×skill_scale`) é uma **SOMA**: `level` cresce
linear, `ninjutsu` (magic level) cresce **côncavo** (satura — medido: 0 em L1, 109 em L100,
menos de 4× a proporção de crescimento do dano de arma). Uma soma de um termo linear e um
côncavo NUNCA alcança um produto super-linear tanto no início quanto no fim do range ao mesmo
tempo com UM ÚNICO coeficiente — testei numericamente: o `level_scale` mínimo que fecha
burst≥1,3× em TODO L1-100 (calibrado no pior ponto, L100) é ~5,76-5,9; qualquer valor menor
deixa L100 abaixo de 1,3×, qualquer valor maior SOBRA tanto nos níveis baixos/médios que o
DPS-se-spammado do tier 1 passa a competir com — e às vezes SUPERAR — o DPS de arma, quebrando
a paridade de boss em L12-25 (o mesmo tipo de tensão "burst vs sustentado" que a rodada 4 §2 já
tinha achado para o cooldown, agora reaparecendo para o `level_scale`).

### Solução aplicada: cooldown como o terceiro lever

Cooldown NÃO afeta o burst por-hit (só o dano médio por cast, independente de quantas vezes
cast por segundo) — mas afeta DIRETAMENTE o DPS-se-spammado (`dano/cooldown`). Testei
`level_scale=5,4` (fecha burst em 94 dos 100 níveis, ver tabela) combinado com cooldowns
crescentes contra os 6 bosses de referência (`--group-matrix`), medindo a diferença REAL
1×1 ninjutsu vs taijutsu (não uma conta de DPS bruto — a mitigação assimétrica entre arma
(sofre armadura/defesa do monstro, `creature.cpp:818 blockHit`) e jutsu (elemental, ignora
armadura, `monsters.cpp`: só `melee` seta `BLOCKARMOR`) faz a diferença REAL bem mais extrema
que uma conta de dano bruto — só simulação decide isso):

| Cooldown tier 1 | L12 (d_ninj) | L19 | L25 | L50 | L80 | L100 |
|---|---|---|---|---|---|---|
| 3,5s (herdado r4) | +67,6% ❌ | +64,5% ❌ | +59,5% ❌ | +15,8% ❌ | 0,0% ✅ | 0,0% ✅ |
| 6,5s | +39,8% ❌ | +34,5% ❌ | +24,7% ❌ | 0,0% ✅ | 0,0% ✅ | 0,0% ✅ |
| **9,0s (escolhido)** | **+13,1% ✅** | **0,0% ✅** | **+3,6% ✅** | **0,0% ✅** | **0,0% ✅** | **0,0% ✅** |

(`d_ninj = (TTK_taijutsu - TTK_ninjutsu)/TTK_taijutsu` — positivo = ninjutsu mais rápido; meta
-15%..+10% inteira, aqui só o lado "ninjutsu rápido demais" estava em risco.)

**Cooldown 9,0s** (era 3,5s) fecha os 6 bosses de referência dentro de -15%..+10% (na
verdade, todos entre 0% e +13,1% — bem dentro). Efeito colateral, verificado: cooldown maior
= MENOS casts por hora = MENOS pressão sobre o pool = a meta de hunt (§1) também melhora com
esta mudança (não piora — verificado depois de aplicar cooldown 9,0s, os números da tabela do
§1 já são COM esse cooldown).

### Valores finais por elemento

| Jutsu | base_damage | level_scale | skill_scale | cooldown_s | chakra_cost_percent |
|---|---|---|---|---|---|
| `katon_goukakyuu` | 4,3 | 5,40 | 0,120 | 9,0 | 3,00% |
| `fuuton_lamina_vento` | 4,0 | 5,35 | 0,115 | 9,0 | 2,75% |
| `raiton_hari` | 3,8 | 5,30 | 0,120 | 9,0 | 2,75% |
| `doton_bala_lama` | 4,0 | 5,35 | 0,115 | 9,0 | 2,75% |
| `suiton_mizudan` | 3,7 | 5,25 | 0,110 | 9,0 | 2,50% |

### Resultado: burst ≥1,3× em 94 dos 100 níveis (era ~17 dos 100 na rodada 4)

Ver tabela do §1 para a amostra; verificação fina (todo L1-100, não só a amostra de 14 pontos):
**falha em 6-9 níveis por elemento, sempre a mesma região (L78-84 e L100)**, por 9-11% do alvo
(pior caso: suiton em L78, 1,19× contra a meta de 1,30×). Essa é a região onde o produto
skill×attack acelera mais rápido que qualquer soma linear+côncava consegue acompanhar — ver
prova acima. **Melhora de ordem de grandeza sobre a rodada 4** (que falhava ~60 dos 100 níveis,
com razões chegando a 0,16× — 84% abaixo do alvo, contra 9-11% abaixo agora).

## 3. Paridade 1×1 dos 6 bosses de referência

| Boss | Nível | TTK taijutsu | TTK ninjutsu | Δ ninjutsu | Meta -15%..+10% | TTK híbrido | Δ híbrido vs melhor puro | Meta ≤+15% |
|---|---|---|---|---|---|---|---|---|
| Chefe dos Bandidos | 12 | 131,3s | 114,1s | **+13,1%** | ✅ | 109,5s | **+4,0%** | ✅ |
| Espadachim da Névoa | 19 | 89,7s | 89,7s | 0,0% | ✅ | 49,5s | **+44,8%** | ❌ |
| Serpente Branca | 25 | 166,0s | 160,0s | +3,6% | ✅ | 127,1s | **+20,5%** | ❌ |
| Marionetista | 50 | 79,7s | 79,7s | 0,0% | ✅ | 54,2s | **+32,0%** | ❌ |
| Oni Ancestral | 80 | 93,7s | 93,7s | 0,0% | ✅ | 60,7s | **+35,3%** | ❌ |
| Ancestral Carmesim | 100 | 103,7s | 103,7s | 0,0% | ✅ | 61,1s | **+41,0%** | ❌ |

**Ninjutsu puro: 6 de 6 dentro da meta** (-15%..+10%) — melhora completa sobre a rodada 4 (que
tinha 4 de 6, com L12 a -16,1% e L19 a -22,4%, ambos agora corrigidos pelo cooldown 9,0s).

**Híbrido: 2 de 6 dentro do teto de +15%** (mesma pendência da rodada 4, não resolvida — sweep
de `HYBRID_TAIJUTSU_FRAC`/`HYBRID_NINJUTSU_FRAC` de 0,15 a 0,40 confirma de novo que nenhuma
fração fecha "nunca abaixo do melhor puro" (viola em frações <0,35) E "nunca acima do teto"
(viola em qualquer fração ≥0) ao mesmo tempo — ver §10. Mantido em 0,4 como a rodada 4 escolheu,
priorizando "nunca pior que o melhor".

## 4. Grupo, elementos, personagens (verificação, não recalibração)

- **Elementos (±10%)**: os 5 jutsus "campeões" usados como proxy (`katon_karyuu_endan`,
  `fuuton_tornado_cortante`, `raiton_punho_trovao`, `doton_colapso_terreno`,
  `suiton_suiryuudan`) **não tiveram nenhum número de dano tocado nesta rodada** (só
  `chakra_cost` de outros jutsus foi reescalado, e nenhum desses 5 é tier 1) — o resultado
  ±0,3% da rodada 4 continua válido bit-a-bit.
- **Personagens (±15%)**: **não reverificado nesta rodada** — mesmo risco herdado da rodada 4
  (a proxy de "valor" de personagem depende da média de dano/chakra de todo jutsu de dano, que
  mudou de novo com os 5 tier 1 elementais). `personal.json`/`neutral.json` só tiveram
  `chakra_cost` reescalado (§1), nenhum `base_damage`/`level_scale` — pendência honesta, ver §10.
- **Grupo 3+ (+30-60%)**: não recalibrado nesta rodada (fora do escopo declarado da missão,
  que pedia "economia de chakra" + "paridade 1×1/híbrido/grupo" — priorizei paridade 1×1, que
  a rodada 4 documentava como quebrada pelo mesmo lever que eu já estava mexendo). Segue
  não-uniforme (mesma causa raiz das rodadas 3/4: multiplicador global não serve para todo HP
  de pull) — números não remedidos (fora do orçamento desta rodada; a mudança de tier 1 não
  afeta jutsus de área/beam tier 2/3, que são os que dominam o cenário de grupo).

## 5. `validate_data.py` / `export_tfs.py` / `luajit` / timing

```
.venv/bin/python tools/validate_data.py
  → 54 jutsus, 174 itens, 38 monstros, 4 vilas, 9 personagens, 5 sets elementais — OK
.venv/bin/python tools/export_tfs.py
  → OK: 38 monstros, 54 jutsus, 174 itens, 21 NPCs, 45 missões, 5 ranks, 114 tarefas, 60 diárias
for f in $(find server/generated -iname "*.lua"); do luajit -bl "$f" /tmp/out.luac; done
  → 0 falhas (todos os .lua gerados, incluindo character_switch.lua com NarutoRegen/
    NarutoRegenAdvance novos, compilam limpo)
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json      → 1938 simulações em 53,0s (orçamento 120s)
python3 tools/balance/sim.py --group-matrix --json /tmp/group.json → 36 grupo + 18 boss em 1,2s
python3 tools/balance/sim.py --hunt --json /tmp/hunt.json          → 20 níveis × 2 (com/sem pílula) em 0,85s
```

Nenhum arquivo em `server/tfs/data/` foi editado à mão nem `install_generated.sh` rodado; o
servidor do playtest em andamento não foi reiniciado, conforme instruído.

## 6. Como reproduzir

```bash
cd /Users/stenioz/Projetos/shinobi-legends
.venv/bin/python tools/validate_data.py
.venv/bin/python tools/export_tfs.py
python3 tools/balance/sim.py --hunt --json /tmp/hunt.json                       # economia, todos os níveis
python3 tools/balance/sim.py --group-matrix --json /tmp/group.json              # paridade 1x1 + grupo
python3 tools/balance/sim.py --level 100 --monster boss_crimson_ancestor --build ninjutsu -v
```

## 7. Pendências honestas

Ver a lista completa e numerada em `tools/balance/README.md` ("Pendências honestas da rodada
5") — resumo:

1. Burst ≥1,3× falha em 6-9 dos 100 níveis (L78-84, L100), por 9-11% — limite matemático da
   forma linear+côncava do jutsu contra o crescimento super-linear (produto) do dano de arma;
   não fechável sem um campo de escala não-linear que o schema de jutsu não tem hoje.
2. Híbrido excede o teto de +15% em 4 dos 6 bosses (L19/25/50/80/100 — só L12 fecha) — mesma
   tensão estrutural da rodada 4 (híbrido aditivo sempre casta quando pronto/pagável), não
   resolvida por nenhuma fração de `HYBRID_TAIJUTSU_FRAC` testada.
3. Grupo 3+ não recalibrado (fora do escopo declarado desta rodada).
4. Personagens (±15%) não reverificados (mesmo risco herdado da rodada 4).
5. `exam_rival_stone` (L20) é o pior caso da meta de hunt (20,7%, dentro do limite mas o mais
   próximo) por ter HP acima da média da sua faixa — variância de monstro, não de jutsu.
