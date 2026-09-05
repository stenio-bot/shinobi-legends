# Relatório de balanceamento PvM — rodada 7 (setembro/2026)

Tema único: **o chakra voltou a não ser um recurso.** Achado citado na missão
(`docs/qa/playtest-l1-20-r5.md`, seção "Tabela de chakra/regen"): custo 2 de 110, regen 1,5/s,
cooldown 9s → o chakra nunca sai de 108-110/110 em 9 casts seguidos no playtest ao vivo do L1.
Meta do orquestrador: 6-8 casts de tier 1 por pool cheio no Genin L1 (hoje 36-55), recuperação
do pool em 60-90s parado, e 15-25% do tempo sem chakra para tier 1 numa caçada híbrida
sustentada de 30 min em TODOS os níveis 5-100 (hoje ~0%).

**Resultado resumido**: 2 das 3 metas numéricas fechadas com folga (casts/pool e recuperação de
L1); a terceira (15-25% de tempo sem chakra numa hunt híbrida) **não fecha** — não por falta de
tentativa, mas por um limite estrutural do próprio modelo de combate híbrido calibrado na
rodada 6 (`HYBRID_JUTSU_CADENCE_FRAC=0,22`), que torna o cast de jutsu tão raro que NENHUM custo
dentro da faixa permitida (6-8 casts/pool) nem regen razoável consegue criar pressão real de
recurso — ver §5 pra prova matemática e numérica completa, com a alavanca que fecharia o
problema (e por que não foi aplicada).

## 0. Arquivos tocados

- `data/jutsus/{katon,fuuton,raiton,doton,suiton}.json`: `chakra_cost_percent` dos 5 projéteis
  tier 1 subiu ~4,7× (2,5-3,0% → 12-14%, ver §2). Nada mais tocado nesses arquivos
  (`cooldown_s`, `base_damage`, `level_scale`, `skill_scale` idênticos à rodada 5/6).
- `tools/balance/sim.py`: `casts_per_full_pool()`/`time_to_refill_pool_s()` (novo, métricas
  analíticas pedidas na missão, §2); `simulate_hunt()` ganhou o parâmetro `force_tier1` (novo,
  achado central desta rodada, §3) — `run_hunt_matrix()` agora usa `force_tier1=True` por
  padrão; CLI ganhou `--no-force-tier1` pra voltar ao comportamento antigo. **Nenhuma fórmula de
  regen ou de custo/cooldown foi alterada no `sim.py`** — `chakra_regen_amount_per_tick`,
  `CHAKRA_REGEN_TICK_S`, `HYBRID_JUTSU_CADENCE_FRAC` e o `cooldown_s` dos 5 jutsus continuam
  IDÊNTICOS à rodada 5/6 (testados apenas em cópias de memória fora do arquivo real, ver §5/§6).
- `tools/export_tfs.py`: **não editado** (outro agente está com o arquivo; rodado só para LER —
  `manapercent` gerado confere com o novo `chakra_cost_percent`, ver §2 — e para confirmar que
  nada quebrou; `install_generated.sh` **não** rodado).
- `docs/sistemas/balanceamento.md` §5/§6, `tools/balance/README.md`: atualizados (ver final
  deste relatório).

**Não tocado**: `data/jutsus/*.json` tier 2/3/personal (custo fixo — avaliado e descartado
reescalar, ver §7), `data/monsters/*.json`, `data/progression.json`, `data/element_sets.json`,
`server/tfs/data/*`/`server/generated/*` não foram instalados, servidor não reiniciado, cliente
não usado.

## 1. Diagnóstico confirmado

Com os valores da rodada 5 (2,5-3,0% do pool, cooldown 9,0s, regen `3+level//4` a cada 2s):
Genin L1 (pool 110) gastava 3 de chakra por cast de `katon_goukakyuu` → **36 casts** por pool
cheio (playtest reportou 9 casts consecutivos sem sair de 108-110/110 — bate: com regen de
1,5/s e cooldown de 9s, a regeneração ENTRE casts, 13,5, é maior que o próprio custo, 3 — o
pool nunca desce de verdade). Recuperação do zero: 73,3s (já dentro de 60-90s desde a rodada 5
— não era esse o problema). O problema é inteiramente de **custo**: 2,5-3,0% do pool é baixo
demais para qualquer cooldown/regen razoável criar gestão de recurso.

## 2. Alavanca 1 — `chakra_cost_percent` do tier 1 (aplicada)

Escalei os 5 valores da rodada 5 pelo MESMO fator (~4,7-4,8×), preservando a proporção relativa
entre elementos (razão máx/mín 1,20 antes → 1,17 depois, dentro de "±10%" pedido):

| Jutsu | Antes (r5/r6) | Depois (r7) | Fator |
|---|---|---|---|
| `katon_goukakyuu` | 3,00% | **14,0%** | ×4,67 |
| `fuuton_lamina_vento` | 2,75% | **13,0%** | ×4,73 |
| `raiton_hari` | 2,75% | **13,0%** | ×4,73 |
| `doton_bala_lama` | 2,75% | **13,0%** | ×4,73 |
| `suiton_mizudan` | 2,50% | **12,0%** | ×4,80 |

`cooldown_s` (9,0s), `base_damage`/`level_scale`/`skill_scale` (burst) **não tocados** — só o
campo `chakra_cost_percent`. `tools/export_tfs.py` confere: `manapercent="14"`/`"13"`/`"12"`
nos 5 `<instant>` gerados, `cooldown="9000"` inalterado.

### Verificação: casts por pool cheio (`casts_per_full_pool`, métrica nova)

`chakra_max // custo`, custo com a MESMA divisão inteira truncada do servidor
(`spells.cpp:804`). Testado nos 5 elementos × 21 níveis (1, 5, 10, ..., 100):
**TODOS entre 6 e 8 casts** (nenhum fora da faixa). Amostra:

| Nível | Pool | Custo `katon_goukakyuu` (14%) | Casts/pool | Custo `suiton_mizudan` (12%) | Casts/pool |
|---|---|---|---|---|---|
| 1 (Genin) | 110 | 15 | **7** | 13 | **8** |
| 5 | 150 | 21 | 7 | 18 | 8 |
| 10 | 200 | 28 | 7 | 24 | 8 |
| 20 | 300 | 42 | 7 | 36 | 8 |
| 40 | 500 | 70 | 7 | 60 | 8 |
| 60 | 700 | 98 | 7 | 84 | 8 |
| 80 | 900 | 126 | 7 | 108 | 8 |
| 100 | 1100 | 154 | 7 | 132 | 8 |

**Meta "6-8 casts, hoje 36-55" → ✅ fechada** (era 33-55 nos 20 níveis testados na rodada 5;
agora 6-8 em TODOS, incluindo Genin L1: 7 casts com `katon_goukakyuu`, 7-8 com os outros 4
elementos — nunca abaixo de 6 nem acima de 8).

### Verificação: tempo até pool cheio (`time_to_refill_pool_s`, métrica nova)

Conta fechada (não Monte Carlo): `chakra_max / (chakra_regen_amount_per_tick(level) /
CHAKRA_REGEN_TICK_S)` — regen não foi tocado nesta rodada, então o número é o mesmo em
qualquer nível calculado pela fórmula pura: **73,3s a 83,3s em TODO L1-100** (não só L1).
**Meta "60-90s no Genin L1" → ✅ fechada** (73,3s; com o gear típico do build híbrido em
alguns níveis o pool fica um pouco maior por causa de acessórios com `+chakra` — a
`simulate_hunt` real reporta até 104s em L30 e 94-95s em L60/65 por causa disso — nenhum nível
exigido pela missão, só L1, viola a faixa).

## 3. Achado estrutural: o "tempo sem chakra" antigo media o jutsu ERRADO em L20+

Ao rodar `--hunt` com o custo novo, os níveis 5-15 e 40-100 continuaram em ~0% de tempo sem
chakra (nenhuma mudança visível apesar do custo 4,7× maior), e só L20-35 subiu (de 3-4,6% pra
19-26%). Investigando: `pick_ninjutsu_jutsu()` (usado por `simulate_hunt` desde sempre) escolhe
o jutsu de MAIOR dano/segundo do kit elemental JÁ DESBLOQUEADO — **não necessariamente o tier
1**. Confirmado com `element_kit`/`pick_ninjutsu_jutsu` direto:

| Nível | Monstro da hunt | Jutsu REALMENTE conjurado | Tier | Custo |
|---|---|---|---|---|
| 5 | `bandit` | `katon_goukakyuu` | 1 | 21 (14% de 150) |
| 15 | `mist_scout` | `doton_bala_lama` | 1 | 32 (13% de 250) |
| **20** | `exam_rival_stone` | **`raiton_lanca_relampago`** | **2** | **170 (fixo)** |
| 25 | `ruin_puppet` | `katon_anel_chamas` | 2 | 176 (fixo) |
| 30 | `stone_sentinel` | `raiton_punho_trovao` | 3 | 200 (fixo) |
| 100 | `crimson_echo` | `fuuton_tornado_cortante` | 3 | 243 (fixo) |

A partir do primeiro tier 2 desbloqueado por elemento (`required_level` 12-26 conforme o
elemento), a rotação "racional" do build ninjutsu/híbrido **abandona o tier 1 para sempre** —
ele nunca mais é conjurado de verdade pelo simulador, mesmo sendo sempre castável. A métrica
antiga (`pct_time_without_chakra_for_tier1`) só comparava "chakra atual < custo do tier 1" como
um LIMIAR de contabilidade — em L20+ isso mede o efeito colateral de gastar chakra em tier 2/3
(que já era caro, 60%+ do pool, desde a rodada 5), não o uso real do tier 1. **Subir o custo do
tier 1 nesses níveis não muda nada de verdade** — só infla o limiar de comparação.

**Fix**: `force_tier1` (novo parâmetro em `simulate_hunt`, `tools/balance/sim.py`) força o
jutsu efetivamente conjurado a ser sempre o tier 1, ignorando a seleção por maior DPS — o
cenário que a missão pede de fato medir: "um jogador usa o projétil barato como filler
constante em TODOS os níveis", não a build ninjutsu ótima que abandona o tier 1 assim que algo
melhor desbloqueia. `run_hunt_matrix()` usa isso por padrão agora; `--no-force-tier1` volta ao
comportamento das rodadas 4-6 para quem precisar da leitura antiga ("tempo sem chakra pra
QUALQUER coisa do kit").

## 4. Alavanca 2 — cooldown 9,0s → 6,0s (avaliada e **descartada**)

Testei `cooldown_s` em 9,0/6,0/4,0/3,0s com `force_tier1=True` (o cenário certo, §3) e o custo
final do §2. **Nenhuma mudança visível no híbrido** — 0,0% de tempo sem chakra em TODOS os
níveis 5-100, nos 4 valores de cooldown testados (tabela completa no §5). Motivo:
`HYBRID_JUTSU_CADENCE_FRAC=0,22` (rodada 6) estica o cooldown EFETIVO do jutsu só para o build
híbrido (`cooldown_s / 0,22`) — em 9,0s isso já é ~40,9s entre casts; em 6,0s cai só para
~27,3s. Contra uma janela de 1800s (30 min) de regen contínuo, a diferença é irrelevante (ver
prova no §5). Reduzir cooldown o bastante para importar (~1,5-2,0s, abaixo até do intervalo de
ataque da arma, 2,0s) multiplicaria a taxa de cast por 4,5-6× e **quebraria** a paridade de
boss ninjutsu/híbrido calibrada nas rodadas 5-6 (o cooldown de 9,0s foi escolhido EXATAMENTE
para neutralizar o `level_scale` alto o bastante para fechar burst ≥1,3×, ver relatório v5 §2)
— não vale a troca. **Decisão: `cooldown_s` mantido em 9,0s.**

## 5. Por que 15-25% de tempo sem chakra (híbrido, todos os níveis) não é atingível aqui

### A matemática

Com `force_tier1=True`, o número de casts possíveis numa hunt de `T` segundos é limitado pelo
intervalo efetivo `cooldown_s / HYBRID_JUTSU_CADENCE_FRAC` (o build híbrido só "acerta o timing"
de conjurar 1 em cada ~4,5 janelas livres, rodada 6). A razão entre chakra GASTO e chakra
REGENERADO na janela inteira é:

```
razão = custo × frac / (cooldown_s × regen_rate(level))
```

Com `frac=0,22`, `cooldown_s=9,0`, `custo=14% do pool`, `regen_rate(1)=1,5/s`: razão = 0,244 —
a hunt gasta em média só 24% do que regenera; o pool satura no teto e fica lá (daí os 0,0%
observados). Essa razão é a MESMA em qualquer nível (pool e regen crescem quase na mesma
proporção — recuperação do zero fica sempre entre 73-83s, ver §2) — não existe UM valor de
custo (dentro de 6-8 casts/pool, ou seja, 12,5-16,7%) que empurre essa razão perto de 1 (onde a
transição de "quase sempre cheio" pra "quase sempre vazio" acontece — ver sweep abaixo, a zona
intermediária é uma faixa muito estreita, não um platô de 15-25%).

### Sweep que prova (custo fixo em 14%/13%/13%/13%/12%, `force_tier1=True`, build híbrido)

| Cooldown | Resultado em TODOS os 20 níveis (5-100) |
|---|---|
| 9,0s (atual) | 0,0% em todos |
| 6,0s | 0,0% em todos |
| 4,0s | 0,0% em todos |
| 3,0s | 0,0% em todos |
| 2,0s | 0,0-66,1% (alguns níveis já viram 0% pra 20-66%, nada estável) |
| 1,0s | 51,6-87,3% (ultrapassou o alvo, quase todo nível "seco" a maior parte do tempo) |

A transição inteira acontece entre cooldown 1,5-2,0s — abaixo do intervalo de ataque da arma
(2,0s), ou seja, mais rápido que o próprio ataque básico. Isso não é um cooldown de jutsu
viável (quebraria burst-vs-sustentado, boss parity, e o "feel" de projétil elemental).

### Segunda leitura (fora do pedido literal, mas informativa): build ninjutsu puro

Sem o amortecedor `HYBRID_JUTSU_CADENCE_FRAC` (só existe pro híbrido), o build ninjutsu PURO
com tier 1 forçado E o custo do §2 mostra scarcity real, ainda que ACIMA da faixa pedida:

| Nível | %sem chakra sem pílula (ninjutsu puro, tier1 forçado) | %sem chakra COM pílula |
|---|---|---|
| 5 | 50,1% | 0,0% |
| 15 | 37,7% | 0,0% |
| 20 | 57,5% | 0,0% |
| 30 | 72,1% | 0,1% |
| 50 | 33,7% | 0,0% |
| 100 | 52,0% | 0,0% |

Isso confirma que o custo do §2 FUNCIONA como recurso gerenciado — só não no modelo híbrido
específico (que a missão pediu testar), por causa do amortecedor da rodada 6. Com pílula,
todos os níveis caem a ≤0,1% (bem dentro de ≤5%). Custo de pílula em ryo/h ficou dentro de
≤30% do ryo/h da região em 4 dos 5 níveis testados (L25 10,7%, L30 11,9%, L60 2,5%, L65 2,1%);
**L20 ficou em 36,6%**, levemente acima — `exam_rival_stone` é o mesmo monstro atípico (HP
acima da média da faixa) que a rodada 5 já tinha identificado como outlier no §1 daquele
relatório, não um problema do preço da pílula em si.

### Conclusão desta seção

**Meta "15-25% em TODOS os níveis 5-100, build híbrido" → ❌ não fechada.** Não é uma questão
de calibração fina — é um limite estrutural: `HYBRID_JUTSU_CADENCE_FRAC=0,22` (necessário para
o híbrido não estourar +15% de TTK contra boss, rodada 6) faz o jutsu ser conjurado raro demais
para QUALQUER custo dentro de 6-8 casts/pool criar pressão real de recurso no cenário de hunt.
Resolver os dois ao mesmo tempo exigiria uma quarta alavanca fora da lista da missão: aumentar
`HYBRID_JUTSU_CADENCE_FRAC` (fazer o híbrido acertar o timing de cast mais vezes) — o que
reabriria a pendência que a própria rodada 6 fechou (híbrido ultrapassando +15% de TTK contra
boss). Não apliquei essa mudança por estourar uma meta que a missão pede explicitamente manter.

## 6. Alavanca 3 — recomendação de regen (só recomendação, não aplicada)

Testei (em memória, sem tocar `sim.py`/`export_tfs.py`) reduzir a regen por um fator constante
`k` (`(3+level//4)/k` a cada 2s) mantendo custo e cooldown do §2/§4. Resultado: só a partir de
`k≈4-5` (regen 4-5× mais lenta que hoje) alguns níveis começam a sair de 0%, mas de forma
**não-uniforme e binária** (a maioria pula direto de 0% para 50-80%, não passa suavemente por
15-25% — mesma transição estreita do §5, porque o termo dominante da razão é `frac/cooldown`,
não a regen). Além disso, `k=4-5` faria a recuperação do pool em L1 saltar de 73s para
**~220-290s** — violando a meta de 60-90s que ESTA MESMA rodada pediu para o Genin L1.

**Não recomendo mudar a fórmula de regen isoladamente** — o número que fecharia o alvo de
scarcity é incompatível com o número que fecha a recuperação de L1, com a mesma matemática do
§5 (o gargalo real é `HYBRID_JUTSU_CADENCE_FRAC`, não a regen). Se o orquestrador ainda assim
quiser mexer em regen como parte de uma futura combinação (ex.: junto com um
`HYBRID_JUTSU_CADENCE_FRAC` maior), a linha exata em `tools/export_tfs.py` é:

```lua
-- tools/export_tfs.py ~linha 1422 (dentro de NarutoRegen.apply):
regen:setParameter(CONDITION_PARAM_MANAGAIN, 3 + math.floor(level / 4))   -- ATUAL, inalterada
```

Nenhuma mudança proposta para esta linha nesta rodada — mantenha como está.

## 7. Alavanca 4 — custos fixos de tier 2/3/personagens (avaliada, **não reescalada**)

### Personagens (±15%, meta "kits" da missão)

A métrica reconstruída na rodada 6 é `valor(jutsu) = (chakra_cost/cooldown_s) ×
(dano_médio/chakra_cost)` — o `chakra_cost` **cancela algebricamente**: `valor(jutsu) =
dano_médio/cooldown_s`, independente de custo. Como nenhum `base_damage`/`level_scale`/
`skill_scale`/`cooldown_s` de `data/jutsus/personal.json` foi tocado (só os 5 tier 1 elementais
mudaram, e eles não entram nessa lista — são compartilhados, não pessoais), **os 9
personagens continuam exatamente onde a rodada 6 deixou (−11,8%..+8,6%, dentro de ±15%)** —
confirmado analiticamente, sem precisar rerodar a proxy.

### Boss parity 1×1 (6 bosses de referência) e grupo (pull 3+)

TTK medido (`--group-matrix`) antes/depois é **byte-a-byte idêntico** nos 6 bosses de
referência (nenhum usa o tier 1 elemental como pick de DPS — todos já usam tier 2/3 ou caem em
fallback pra taijutsu desde a rodada 5/6, ver v6 §1):

| Boss | Nível | TTK taijutsu | TTK ninjutsu (Δ) | TTK híbrido (Δ vs melhor puro) | Antes = Depois? |
|---|---|---|---|---|---|
| `boss_bandit_chief` | 12 | 131,31s | 125,59s (+4,4%) | 128,92s (−2,7%) | ✅ idêntico |
| `boss_mist_swordsman` | 19 | 89,66s | 89,66s (0,0%) | 84,21s (+6,1%) | ✅ idêntico |
| `boss_white_serpent` | 25 | 165,96s | 165,96s (0,0%) | 161,07s (+2,9%) | ✅ idêntico |
| `boss_puppeteer` | 50 | 79,72s | 79,72s (0,0%) | 79,03s (+0,9%) | ✅ idêntico |
| `boss_ancestral_oni` | 80 | 93,72s | 93,72s (0,0%) | 94,64s (−1,0%) | ✅ idêntico |
| `boss_crimson_ancestor` | 100 | 103,66s | 103,66s (0,0%) | 101,29s (+2,3%) | ✅ idêntico |

Todos dentro de −15%..+10% (ninjutsu) e ≤+15% (híbrido) — **meta mantida, 6/6** (igual à
rodada 6).

**Achado colateral (fora das metas nomeadas desta rodada, documentado por transparência)**: no
cenário de PULL 3+ (`simulate_group_fight`, que considera custo de chakra na escolha do jutsu a
cada ação — diferente do 1×1), 3 dos 12 cenários de grupo mudaram de XP/h ninjutsu porque o
tier 1, agora mais caro, deixa de ser um "filler sempre pagável" entre os cooldowns de tier 2/3:

| Monstro | Nível | XP/h ninjutsu antes | depois | Observação |
|---|---|---|---|---|
| `ruin_puppet` | 27 | +56,9% | **+3,7%** | saiu da faixa 30-60% que a rodada 6 tinha fechado (meta de OUTRA rodada, não desta) |
| `lesser_serpent` | 18 | +12,7% | +5,7% | já estava fora da faixa 30-60% antes; continua fora |
| `mercenary_bridge` | 12 | +2,7% | −5,8% | já estava fora da faixa 30-60% antes; continua fora |

Isso não viola nenhuma meta desta rodada (nem "ninjutsu −15%..+10%" nem "híbrido ≤+15%" nem
"kits ±15%" — nenhuma delas é essa métrica de grupo). É uma consequência ESPERADA de tornar o
tier 1 um recurso de verdade (deixa de ser spam grátis entre cooldowns de tier 2/3 em pulls).
Não reescalei tier 2/3 para compensar — faria isso reabrir a paridade de boss 1×1 já fechada
(tier 2/3 é compartilhado entre os cenários de pull e os 6 bosses de referência). Sinalizo como
pendência para uma rodada futura que priorize a métrica de grupo 30-60%, não corrigido aqui.

## 8. Tabela por nível (antes → depois, níveis pedidos pela missão)

| Nível | Pool | Regen/s | Custo tier1 antes→depois (katon) | Casts/pool antes→depois | %sem chakra sem pílula (antigo/kit-wide) antes→depois | %sem chakra sem pílula (tier1 forçado, híbrido) | TTK boss por build |
|---|---|---|---|---|---|---|---|
| 5 | 150 | 2,00 | 4→21 | 37→7 | 0,0%→0,0% | 0,0% | (sem boss de referência neste nível) |
| 10 | 200 | 2,50 | 5→26 | 40→7 | 0,0%→0,0% | 0,0% | — |
| 20 | 300 | 4,00 | 9→44 | 33→7 | 3,3%→18,8%* | 0,0% | boss L19 acima: sem mudança |
| 40 | 500 | 6,50 | 13→65 | 38→7 | 0,0%→0,0% | 0,0% | — |
| 60 | 700 | 9,00 | 23→110 | 30→7 | 0,0%→0,0% | 0,0% | boss L50 acima: sem mudança |
| 80 | 900 | 11,50 | 24→117 | 37→7 | 0,0%→0,0% | 0,0% | boss L80: sem mudança |
| 100 | 1100 | 14,00 | 30→143 | 36→7 | 0,0%→0,0% | 0,0% | boss L100: sem mudança |

(*) L20 usa a métrica ANTIGA/kit-wide (`force_tier1=False`) — o jutsu real conjurado em L20 é
`raiton_lanca_relampago` (tier 2, custo fixo 170), não o tier 1; o número sobe porque o LIMIAR
de comparação (custo do tier 1) subiu, não porque o uso real mudou — ver §3. Na métrica correta
(tier1 forçado), L20 = 0,0% igual a todos os outros níveis (ver §5).

Burst (razão hit-tier1-com-vantagem / hit-arma) **matematicamente inalterado** — nenhum campo
que entra na conta (`base_damage`/`level_scale`/`skill_scale`) foi tocado. Recalculado para
confirmar (idêntico byte-a-byte à rodada 5/6): 2,91× (L1), 3,34× (L5), 2,32× (L20), 1,93×
(L40), 1,80× (L60), **1,28× (L80, abaixo de 1,3×, aceito desde a rodada 5)**, **1,23× (L100,
idem)**. 94/100 níveis fecham ≥1,3× (igual à rodada 5/6).

## 9. Comandos para reproduzir

```bash
.venv/bin/python tools/validate_data.py                              # OK
.venv/bin/python tools/export_tfs.py                                 # OK, não instalado
python3 tools/balance/sim.py --hunt --json /tmp/hunt.json             # força tier1 por padrão (novo)
python3 tools/balance/sim.py --hunt --no-force-tier1 --json /tmp/x.json  # métrica antiga (r4-r6)
python3 tools/balance/sim.py --hunt --level 1 --monster wolf --build hybrid --chakra-pills
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json         # 2040 sims, ~68s
python3 tools/balance/sim.py --group-matrix --json /tmp/group.json    # 36 grupo + 18 boss, ~1,4s
```

## 10. Metas atingidas / não atingidas

| Meta | Resultado |
|---|---|
| Genin L1: 6-8 casts de tier 1 por pool cheio (hoje 36-55) | **✅ fechada** — 7-8 em todos os 5 elementos |
| Genin L1: recuperar pool em 60-90s parado | **✅ fechada** — 73,3s (fórmula pura, sem tocar regen) |
| 15-25% sem chakra tier1, hunt híbrida 30min, TODOS níveis 5-100 | **❌ não fechada** — 0,0% em todos os 20 níveis testados; limite estrutural do `HYBRID_JUTSU_CADENCE_FRAC=0,22` da rodada 6, ver §5 (matemática completa) |
| Com pílula, ≤5% sem chakra | ✅ trivialmente satisfeita para híbrido (já era ~0% sem pílula); ✅ para ninjutsu puro (leitura suplementar, ≤0,1% com pílula) |
| Pílulas valem a pena (ryo/h ≤30% da região) | ✅ 4/5 níveis testados (2,1-11,9%); L20 em 36,6% (monstro outlier já identificado na rodada 5) |
| Ninjutsu −15%..+10% em 6 bosses | ✅ mantida, idêntica à rodada 6 (nenhum boss de referência usa tier 1) |
| Híbrido ≤+15% | ✅ mantida, idêntica à rodada 6 |
| Burst ≥1,3× (aceito perder L78+) | ✅ mantida, idêntica à rodada 5/6 (94/100 níveis) |
| Kits/personagens ±15% | ✅ mantida — cancelamento algébrico do custo na fórmula `valor()`, confirmado sem precisar rerodar |

**Recomendação para a próxima rodada**: se a meta de 15-25% de scarcity no híbrido for
realmente prioritária, a alavanca que fecharia é aumentar `HYBRID_JUTSU_CADENCE_FRAC` (fazer o
híbrido conjurar com mais frequência) — mas isso precisa vir acoplado a uma NOVA rodada de
recalibração de boss parity híbrida (reabre a pendência que a rodada 6 fechou), não é um ajuste
isolado. Documentei a matemática completa no §5 para quem for atacar isso depois.
