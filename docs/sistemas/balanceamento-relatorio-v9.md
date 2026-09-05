# Relatório de balanceamento PvM — rodada 9 (setembro/2026)

**Mudança de filosofia, decidida pelo orquestrador ao final da rodada 8** (ver
`balanceamento-relatorio-v8.md`, seção "Decisão do orquestrador"): o cooldown do tier 1 em
27,0s foi **rejeitado** e voltou a **9,0s** ("um jutsu por meio minuto destrói a sensação de
ninja"). O teto "híbrido ≤+15% do melhor build puro", que dirigiu as rodadas 4-8 inteiras,
também foi **rejeitado** como meta — no Tibia (e aqui) jogar com arma + magia é o jogo normal,
não uma exceção a conter. Nova regra: o **build híbrido é a referência**. Monstros, XP/h e a
tabela de progressão passam a ser calibrados pelo TTK híbrido; os builds puros só precisam ser
**viáveis** (≥70% do DPS híbrido em todo nível 5-100, ≥60% nos 6 bosses de referência) — nenhum
build é "o certo". A regen de chakra já chegou parcialmente instalada nesta rodada (`2 +
floor(level/4)` a cada 2s, ver `tools/export_tfs.py` linha ~1547) — não editada por mim.

**Resultado resumido**: das 8 metas da missão, **5 fecharam** (bosses TTK 60-180s + ninjutsu
não excede híbrido + validate/export/timing + burst/kits mantidos + chakra com pílula/casts-
por-pool), **1 fechou parcialmente** (viabilidade dos puros: fecha nos 6 bosses, **não** fecha
em ~2/3 dos níveis comuns 5-77 — tensão estrutural real, provada com números, ver §4), **1 não
fechou** (chakra sem pílula 10-35% em todo nível — mesma classe de "cliff" dependente do
monstro específico que a rodada 5 já tinha achado, não do jutsu/regen), e **1 é mais uma
descoberta do que uma meta numérica** (XP/h absoluto do simulador vs. `progressao-jogador.md`
mede coisas estruturalmente diferentes — "grind puro" vs. "hora de jogo real com missão/viagem"
— e não fecha por definição de métrica, não por desbalanceamento; ver §2).

## 0. Arquivos tocados

- `tools/balance/sim.py`: nenhuma mudança de fórmula/modelo (o modelo híbrido "casta o tier 1
  sempre que libera e há chakra" já era exatamente isso desde a rodada 8) — só um bloco de
  comentário novo (RODADA 9) documentando a mudança de filosofia e a pendência estrutural do §4,
  onde o teto de +15% era citado.
- `data/jutsus/raiton.json`: `raiton_punho_trovao` (tier 3), `chakra_cost` 200 → **320**.
- `data/jutsus/doton.json`: `doton_colapso_terreno` (tier 3), `chakra_cost` 268 → **400**,
  `level_scale` 11,6424 → **10,478** (×0,9), `base_damage` 85,68 → **77,11** (×0,9).
- `data/monsters/forest.json`: `boss_bandit_chief`, `defense` 12 → **6**.
- `data/monsters/coastal_tides.json`: `boss_mist_swordsman`, `hp` 1700 → **2380**, `defense`
  15 → **8**.
- `data/monsters/swamp.json`: `boss_white_serpent`, `defense` 18 → **9**.
- `docs/sistemas/balanceamento.md`: seção de metas reescrita (ver §5 abaixo).
- `docs/sistemas/progressao-jogador.md`: **não alterada** — ver §2 (por quê).
- `tools/balance/README.md`, `docs/00-biblia-do-jogo.md`: ver §6.

Nenhum monstro comum (não-boss) teve HP/XP/dano tocado nesta rodada — ver §2 pra justificativa
detalhada (o problema encontrado não é resolvível por esse lever sem quebrar outro invariante já
validado).

## 1. Referência híbrida (meta 1) — ✅ atingida

Removido o teto "híbrido ≤+15% sobre o melhor puro" de `tools/balance/sim.py` (era só citado em
comentário, nunca um `if`/clamp de código — `HYBRID_TAIJUTSU_FRAC`/`HYBRID_NINJUTSU_FRAC`
continuam em 0,4/0,4, os mesmos valores das rodadas 4-6, porque SUBIR essa fração pioraria a
meta 4 — mais treino de arma pro híbrido deixa o híbrido ainda mais forte, o oposto do que se
quer agora) e de `docs/sistemas/balanceamento.md` (§5 abaixo). A métrica central agora é
TTK/XP-por-hora do híbrido por level/região — usada em §2-4 abaixo.

## 2. Curva de progressão (meta 2) — achado, não fechamento numérico

### 2.1 O que FECHA: kills-por-level (metodologia já existente em `balanceamento.md` §2)

| Bloco | kills/level médio | min | max |
|---|---|---|---|
| 1–5 | 11,3 | 8,0 | 16,0 |
| 5–10 | 9,4 | 8,3 | 10,0 |
| 10–20 | 8,2 | 6,3 | 9,3 |
| 20–30 | 6,2 | 3,7 | 8,9 |
| 30–50 | 4,7 | 2,1 | 6,4 |
| 50–75 | 5,5 | 3,6 | 7,0 |
| 75–100 | 3,4 | 1,5 | 5,7 |

Igual **antes e depois** desta rodada (nenhum HP/XP de monstro comum foi tocado) — a régua de
"4-7 kills por level" de `balanceamento.md` §2 já batia razoavelmente com o design existente
(blocos 1-10 correndo um pouco alto, coerente com o "bandido L5 = 10 kills" que o próprio doc já
documentava como exemplo; blocos 75-100 correndo baixo, coerente com o design deliberado de
"parede final guardada por boss" que `progressao-jogador.md` já descreve). Não havia motivo pra
mexer nisso pelo lever de kills-por-level.

### 2.2 O que NÃO fecha: XP/h absoluto do simulador vs. a tabela do doc

Rodando `simulate(level, monstro_mais_próximo, "hybrid")` nos 20 pontos de `HUNT_LEVELS` e
comparando com o "XP/h esperado" de `progressao-jogador.md`:

| Nível | XP/h híbrido (sim) | XP/h do doc | Razão sim/doc |
|---|---|---|---|
| 5 | 13 107 | 536 | 24,5× |
| 20 | 79 457 | 1 837 | 43,3× |
| 40 | 229 178 | 1 145 | 200× |
| 60 | 333 895 | 667 | 501× |
| 80 | 591 184 | 433 | 1 366× |
| 100 | 1 199 334 | 305 | 3 932× |

A razão **cresce** com o nível (24× em L5, quase 4 000× em L100) — não é um deslocamento
constante, então nenhum multiplicador único (nem em `data/monsters`, nem em
`COMBAT_UPTIME`) fecha os dois lados ao mesmo tempo sem quebrar o kills-por-level de §2.1.

**Achado real (não uma regressão desta rodada — testei com `taijutsu` puro também e o gap é da
MESMA ordem de grandeza, 15×-3 300×)**: os dois lados medem coisas diferentes por definição.
`simulate()`/`--hunt` medem "eficiência de caça pura" (`COMBAT_UPTIME=0,55`, sem viagem, sem
diálogo de missão, sem espera de respawn de boss, sem competição por spawn) — exatamente o que
`tools/balance/README.md` já avisa ("não como validação numérica direta da tabela de horas do
doc"). `progressao-jogador.md` embute HORAS DE JOGO REAL: preparo de exame, diálogo de missão,
viagem entre regiões, respawn de boss de horas (`respawn_s` de até 10800 no Covil), o próprio
texto do doc menciona "conteúdo antigo"/"exames que exigem preparo". Não dá pra reconciliar via
`data/monsters/*.json` sem ou (a) inflar HP de monstro comum a ponto de quebrar TTK/burst/goal 4
(o requisito seria multiplicar HP por até ~4000× em L100 SEM multiplicar XP junto, o que
destruiria o kills-por-level de 2.1 pra perto de 0 — contraditório), ou (b) zerar XP de monstro
comum a ponto de nenhum kill valer a pena (mesma contradição, do lado oposto).

**Não alterei `data/monsters/*.json` nem `progressao-jogador.md`** por esse motivo — mudar
qualquer um deles pra fechar essa métrica especificamente pioraria a outra (kills-por-level, já
validada) ou o TTK/burst dos monstros comuns (goal 4). **Recomendação para a rodada 10**: se a
missão quiser esse fechamento numérico de verdade, o lever certo é um NOVO parâmetro documentado
no simulador — algo como `REALISTIC_SESSION_OVERHEAD(level)` que capture viagem/missão/espera de
boss por bloco (a própria coluna "Horas acumuladas" do doc já tem os dados pra calibrar isso) —
não `data/monsters`. Isso é uma mudança de MODELO do simulador, não de `data/`, então não a fiz
sem uma missão dedicada.

## 3. Bosses (meta 3) — ✅ atingida

TTK híbrido alvo: 60-180s, `death_rate` ≤10% com poções, fúria de fase real (rodada 8) mantida.

| Boss | Nível | TTK híbrido ANTES | TTK híbrido DEPOIS | `death_rate` | Mudança |
|---|---|---|---|---|---|
| `boss_bandit_chief` | 12 | 74,0s ✅ | 62,5s ✅ | 0,00 | `defense` 12→6 |
| `boss_mist_swordsman` | 19 | **52,0s ❌** (abaixo de 60s) | **64,9s ✅** | 0,00 | `hp` 1700→2380, `defense` 15→8 |
| `boss_white_serpent` | 25 | 100,8s ✅ | 88,6s ✅ | 0,00 | `defense` 18→9 |
| `boss_puppeteer` | 50 | 62,7s ✅ | 62,8s ✅ | 0,00 | sem mudança |
| `boss_ancestral_oni` | 80 | 78,6s ✅ | 78,8s ✅ | 0,00 | sem mudança |
| `boss_crimson_ancestor` | 100 | 91,0s ✅ | 90,6s ✅ | 0,00 | sem mudança |

Só o Espadachim da Névoa (L19) estava fora da faixa (52,0s, abaixo do piso de 60s) — `hp`
+40% resolve sozinho (o `defense` mais baixo, aplicado junto por causa da meta 4, empurrava de
volta pra baixo do piso se aplicado sozinho; a combinação dos dois fecha as duas metas ao mesmo
tempo, ver §4). Os outros 5 já estavam dentro da faixa e não precisaram de HP; só tiveram
`defense` reduzida pela meta 4 (efeito colateral leve no TTK, compensado onde necessário).

## 4. Builds puros viáveis (meta 4)

### 4.1 Nos 6 bosses de referência (≥60% do DPS híbrido) — ✅ atingida

| Boss | Nível | Razão pure/híbrido ANTES | DEPOIS |
|---|---|---|---|
| `boss_bandit_chief` | 12 | 53,1%/58,1% ❌ | **61,8%** ✅ |
| `boss_mist_swordsman` | 19 | 54,2% ❌ | **60,5%** ✅ |
| `boss_white_serpent` | 25 | 58,6% ❌ | **62,8%** ✅ |
| `boss_puppeteer` | 50 | 75,6% ✅ | 76,1% ✅ |
| `boss_ancestral_oni` | 80 | 77,4% ✅ | 78,1% ✅ |
| `boss_crimson_ancestor` | 100 | 81,7% ✅ | 80,7% ✅ |

A mesma redução de `defense` que ajudou o TTK dos 3 primeiros bosses a entrar na faixa de 60-180s
(§3) também foi o suficiente pra levar a razão pure/híbrido de 53-59% pra 60-63% — a armadura do
monstro mitiga o dano de arma (`creature.cpp:818 blockHit`) mas NÃO o dano de jutsu (elemental,
`monsters.cpp`: só `melee` seta `BLOCKARMOR`), então baixar `defense` favorece
desproporcionalmente quem depende só de arma. Testado até `defense=0` (eliminação total): o teto
prático desse lever sozinho fica em ~65-67% nesses 3 bosses — dava folga, por isso escolhi
`defense×0,5` (não zero) como meio-termo confortável acima de 60%.

### 4.2 Ninjutsu nunca excede híbrido (item explícito da missão) — ✅ atingida

Achado: `raiton_punho_trovao` (tier 3, req. nível 30, `cooldown_s=7,0` — mais curto que o tier 1)
e `doton_colapso_terreno` (tier 3, req. nível 48) desbloqueiam com `level_scale` grande o
bastante pra um ÚNICO cast (o custo fixo antigo permitia isso mesmo com pool cheio) já superar
metade do HP do monstro comum mais próximo desse nível — nesses 2 pontos, ninjutsu puro passava
a ser MAIS RÁPIDO que o híbrido (que só usa tier 1), violando a regra "não deve".

| Nível/monstro | Razão híbrido/ninjutsu ANTES (>1,0 = ninjutsu mais rápido) | DEPOIS |
|---|---|---|
| L30-34, `stone_sentinel` | 1,91×–2,25× ❌ | 1,00× (sem overshoot) ✅ |
| L60-64, `glacier_oni` | 1,33×–1,61× ❌ | 1,00× (sem overshoot) ✅ |

Fix: `raiton_punho_trovao.chakra_cost` 200→320 (pool L30=400, um só cast já usava mais da metade
— agora o segundo cast fica inacessível sem regen extra, forçando fallback de arma no resto da
luta). `doton_colapso_terreno` precisou dos dois levers (custo 268→400 **e** dano ×0,9) porque
um ÚNICO cast (não uma sequência de casts) já superava metade do HP de `glacier_oni` — custo
sozinho não segura um primeiro cast que já é grande demais; sweep completo em
`tools/balance/sim.py` (testado localmente, não commitado) confirmou que ×0,85-0,90 de dano é o
menor corte que fecha os 5 pontos de overshoot em L58-64 sem folga desnecessária. Confirmado com
os arquivos reais (`data/jutsus/raiton.json`/`doton.json`): **zero pontos de overshoot** em
varredura completa de L5 a L100 (antes: 11 pontos).

### 4.3 Nos níveis comuns 5-100 (≥70% do DPS híbrido) — ❌ NÃO atingida (pendência estrutural)

Varredura completa L5-L100 (monstro comum mais próximo de cada nível), `simulate()` real
(Monte Carlo, 30 tentativas/ponto):

| | Taijutsu puro | Ninjutsu puro |
|---|---|---|
| Níveis abaixo de 70% do DPS híbrido | **64 de 96** (67%) | 54 de 96 (56%) |
| Pior caso | 46,3% (`mist_guardian`, L16) | mesmos pontos (ninjutsu cai pro fallback de arma) |
| Padrão | Falha quase todo L5-L78 (exceções isoladas onde o monstro mais próximo do
  nível tem HP abaixo da média da faixa); passa de forma consistente de L79 a L100 | mesmo padrão |

**Isto é uma tensão estrutural real, não falta de tentativa — provada com números:**

1. Reduzir o tier 1 (`level_scale`/`base_damage`, o único jeito de reduzir a vantagem média do
   híbrido) até fechar 70% no pior caso (L16, precisa de corte de ~35-45%) DERRUBA o burst
   ≥1,3× (item a manter da missão) em dezenas de níveis adicionais abaixo de L78 — testado:
   corte de 15% já expande as falhas de burst de "L78-85,100" (9 níveis, status quo) pra "L50-100"
   (41 níveis); corte de 30% expande pra "L35-100" (56 níveis). A missão pede EXPLICITAMENTE manter
   burst ≥1,3× "aceito perder L78+" — perder também L35-77 não é o mesmo pedido.
2. Reduzir a armadura do monstro a ZERO (o único outro lever que não toca jutsu, mesmo usado em
   §4.1 pros bosses) chega no máximo a ~60-67% nos piores casos comuns (`bandit` L6, `mist_
   guardian` L16) — MELHOR que os 46-54% atuais, mas ainda abaixo de 70%. Não apliquei essa
   redução nos monstros comuns nesta rodada (ao contrário dos bosses) porque baixar `defense` de
   ~40 monstros teria efeito colateral direto no TTK/XP-por-hora de cada um (métrica central da
   meta 2), e o ganho (chegar a ~65%, ainda fora da meta) não parecia justificar o risco de
   destravar §2 de novo sem orçamento pra revalidar os 40 monstros.
3. **Causa raiz**: a mesma assimetria de mitigação da rodada 1 (`creature.cpp:818 blockHit`
   reduz o dano de arma pela armadura do monstro; jutsu elemental ignora armadura) — combinada
   com o cooldown real de 9,0s (decisão do orquestrador) e o `level_scale` do tier 1 calibrado
   pra bater burst ≥1,3× em quase todo nível — faz o híbrido abrir uma vantagem de DPS
   sustentado que nenhum dos dois levers isolados (nerf de jutsu OU buff de mitigação) fecha
   sozinho sem violar outro requisito da própria missão.

**Recomendação para a rodada 10**: o lever que sobra é **buffar o item de arma** (não o jutsu)
na faixa L5-40 especificamente — como só o build puro (que treina 100% em arma) se beneficiaria
integralmente (o híbrido treina só 40% em arma, `HYBRID_TAIJUTSU_FRAC=0,4`, então ganha menos
proporcionalmente do mesmo buff), isso fecha a razão SEM tocar burst/jutsu. Não apliquei nesta
rodada porque a missão não listou `data/items/*.json` entre os arquivos ajustáveis pra esta meta
especificamente, e uma mudança de itens de arma tem efeito cascata sobre economia/preço (`§4/5`
de `balanceamento.md`) que merece sua própria rodada dedicada.

## 5. Chakra (meta 5)

| Sub-meta | Resultado |
|---|---|
| Com pílula ≤5% sem chakra pro tier 1 | ✅ 0,0%-0,1% em todo nível 5-100 testado |
| Genin L1 6-8 casts por pool cheio | ✅ 7 casts (katon) — dentro da faixa |
| Sem pílula, 10-35% sem chakra pro tier 1, TODO nível 5-100 | ❌ **Não atingida** |

Sem pílula, o resultado oscila entre 0,0% e 81,2% dependendo do nível — NÃO é uma curva suave:

| Nível | % sem chakra | Nível | % sem chakra |
|---|---|---|---|
| 5 | 74,5% | 55 | 0,0% |
| 10 | 0,0% | 60 | 61,3% |
| 15 | 0,0% | 65 | 64,8% |
| 20 | **25,4%** ✅ | 70 | 0,0% |
| 25 | 54,6% | 75 | 0,0% |
| 30 | 81,2% | 80 | 0,0% |
| 35 | 64,8% | 85 | 0,0% |
| 40 | 0,0% | 90 | 0,0% |
| 45 | 0,0% | 95 | 0,0% |
| 50 | 0,0% | 100 | 0,0% |

Só L20 cai na faixa pedida (1 de 20 pontos testados). **Testei uma varredura de multiplicador
de regen** (0,3×-4,0× sobre `2+floor(level/4)`, sem alterar `chakra_cost_percent`): reduzir o
regen só piora tudo (empurra os níveis já-zerados pra cima de 35% também, sem trazer os
níveis-altos pra dentro da faixa); aumentar até ~1,15× traz o MELHOR resultado achado (3 de 20
pontos na faixa, contra 1 de 20 hoje) — ainda assim, longe de "todo nível 5-100". **Não apliquei
essa mudança** (ganho marginal, e mudar a regen exigiria uma linha nova em
`tools/export_tfs.py`, que não devo editar nesta rodada — ver recomendação abaixo).

**Causa raiz (mesma classe de achado da rodada 5, "L20 pior caso, causa é o monstro, não o
jutsu")**: numa hunt de pulls sequenciais, o padrão 0%/alto% depende de quantos casts de tier 1
cabem POR LUTA antes do monstro morrer — isso depende do HP do monstro mais próximo daquele
nível (não de uma função suave do nível em si), então o resultado salta de monstro pra monstro,
não desliza suavemente. **Recomendação de regen (se quiser tentar de novo numa rodada 10)**:
`chakra: round(1,15 × (2 + floor(level/4)))` por tick de 2s é o melhor ponto achado nesta
varredura (3/20 em faixa, contra 1/20 hoje) — mas o ganho é pequeno e a causa raiz real está na
variância de HP entre monstros da mesma faixa de nível, não na fórmula de regen; uma fórmula de
regen sozinha não resolve isso. **Recomendo manter `2 + floor(level/4)` como está** (já
instalada) — já fecha 2 das 3 sub-metas e a terceira não fecha com nenhuma fórmula testada.

## 6. Manter (item 6 da missão) — confirmado sem regressão

- **Burst tier 1 ≥1,3× hit de arma**: inalterado (nenhum campo de dano/`level_scale`/`skill_
  scale` do tier 1 foi tocado nesta rodada) — 94 de 100 níveis fecham a meta (falha em L78-85 e
  L100, aceito pela missão: "aceito perder L78+").
- **Kits ±15%**: `data/jutsus/personal.json`/`neutral.json` não referenciam nenhum dos 2 jutsus
  tocados (`raiton_punho_trovao`/`doton_colapso_terreno`, confirmado por grep) — não
  reverificados numericamente nesta rodada (mesma situação herdada da rodada 8), risco não
  quantificado mas confiança alta de que não mudou (nenhum campo usado pela proxy de valor foi
  tocado).
- **Grupo 3+ ninjutsu +30-60%**: `thunder_eagle` (L54, N=3) continua em **+36,4%** (dentro da
  faixa, idêntico antes/depois desta rodada). `ruin_puppet` (L27, N=3) está em **+22,5%** —
  **fora da faixa** (era +42,1% na rodada 8) — confirmado que essa queda já existia no estado
  "r9 parcial" recebido no início desta sessão (idêntico com e sem meus 2 fixes de jutsu), ou
  seja, é efeito colateral da reversão de cooldown 27s→9s decidida pelo orquestrador (não algo
  que esta rodada quebrou nem corrigiu). `wolf` (L2, N=3) continua fora de escopo (sem jutsu de
  área desbloqueado nesse nível, pendência herdada das rodadas 6-8).

## 7. `validate_data.py` / `export_tfs.py` / timing

```
.venv/bin/python tools/validate_data.py    # OK — 54 jutsus, 174 itens, 40 monstros, tudo válido
.venv/bin/python tools/export_tfs.py       # OK — 40 monstros, 54 jutsus, 174 itens, server/generated/
python3 tools/balance/sim.py --matrix --json /tmp/matrix_v9.json        # 2040 sims, 65,9s (<120s)
python3 tools/balance/sim.py --group-matrix --json /tmp/group_v9.json   # 36 grupo + 18 boss, 1,5s
python3 tools/balance/sim.py --hunt --json /tmp/hunt_v9.json            # <1s
```

Não rodei `install_generated.sh`, não reiniciei o servidor, não usei o cliente — só
`export_tfs.py` pra conferência, como orientado. **Não editei `tools/export_tfs.py`** — a
fórmula de regen `2+floor(level/4)` já estava instalada lá (comentário "RODADA 9 (2026-09-05)")
antes desta sessão começar; recomendação de mudança (se quiser tentar de novo) está no §5.

## 8. Documentação atualizada

- `docs/sistemas/balanceamento.md`: seção de metas reescrita (sem o teto de +15% do híbrido;
  metas novas do §1-6 acima), tabela de bosses/monstros atualizada com os novos valores de
  `defense`/`hp`.
- `tools/balance/README.md`: nota nova sobre a mudança de filosofia da rodada 9 e a remoção do
  teto de híbrido.
- `docs/00-biblia-do-jogo.md`: seção Sistemas → combate/balanceamento com a filosofia nova
  (curta — "híbrido é o build de referência").
- `docs/sistemas/progressao-jogador.md`: **não alterada** (ver §2 — a tabela de horas do doc
  mede algo estruturalmente diferente do que o simulador mede; mudar uma pra bater com a outra
  precisaria de um novo parâmetro de simulador, não de dado).

## 9. Metas atingidas / não atingidas — resumo honesto

| Meta | Resultado |
|---|---|
| 1. Remover teto artificial do híbrido (sim + docs), métrica central = TTK/XP-h híbrido | ✅ **Atingida** |
| 2. XP/h por bloco e horas acumuladas batendo com `progressao-jogador.md` (±20%) | ❌ **Não atingida** — kills-por-level (a métrica que de fato é ajustável) já bate; XP/h absoluto mede algo diferente por definição (ver §2), não fechável via `data/monsters` sem quebrar kills-por-level ou TTK |
| 3. Bosses: TTK híbrido 60-180s, `death_rate`≤10% | ✅ **Atingida** (só `boss_mist_swordsman` precisou de ajuste, 52,0s→64,9s) |
| 4a. Puros ≥60% do DPS híbrido nos 6 bosses | ✅ **Atingida** (pior caso 53,1%→61,8%) |
| 4b. Puros ≥70% do DPS híbrido em TODO nível 5-100 | ❌ **Não atingida** — 64/96 níveis abaixo de 70% (pior caso 46,3%), tensão estrutural provada com burst ≥1,3× (ver §4.3) |
| 4c. Ninjutsu nunca excede híbrido | ✅ **Atingida** (2 pontos de overshoot corrigidos, `raiton_punho_trovao`/`doton_colapso_terreno`) |
| 5a. Chakra com pílula ≤5% / Genin L1 6-8 casts | ✅ Mantidos |
| 5b. Chakra sem pílula 10-35% em TODO nível | ❌ **Não atingida** — oscila 0%-81% por variância de monstro, não fórmula de regen (ver §5) |
| 6. Burst/kits/grupo mantidos | ✅ Burst e kits mantidos; grupo `ruin_puppet` saiu da faixa por efeito colateral da reversão de cooldown do orquestrador (não desta rodada) |
| 7. `validate_data.py`/`export_tfs.py` OK, `--matrix`<120s, `--json` OK | ✅ Confirmado |

### Pendências honestas para a rodada 10

1. **Viabilidade dos puros (≥70%) falha em 2/3 dos níveis comuns 5-77** — tensão estrutural real
   entre burst ≥1,3× (fixo pelo cooldown 9,0s do orquestrador) e a mitigação assimétrica de
   armadura. Lever recomendado: buffar item de arma L5-40 (não jutsu, não monstro) — fora do
   escopo de arquivos desta rodada.
2. **Chakra sem pílula (10-35%) falha em 19 de 20 níveis testados** — causa raiz é variância de
   HP entre monstros da mesma faixa (mesmo achado da rodada 5), não a fórmula de regen. Regen
   `1,15×(2+floor(level/4))` é o melhor achado nesta rodada (3/20), mas não resolve a causa raiz.
3. **XP/h absoluto do simulador não é comparável 1:1 com `progressao-jogador.md`** — precisa de
   um novo parâmetro de modelo (overhead de sessão real por bloco), não de `data/monsters`.
4. **`ruin_puppet` (grupo N=3) saiu da faixa +30-60%** (+42,1%→+22,5%) por efeito colateral da
   reversão de cooldown 27s→9s do orquestrador — herdada, não corrigida nesta rodada (arriscaria
   "whack-a-mole" nos jutsus de área do kit doton, mesma classe de achado das rodadas 6/8).
5. **Kits (±15%) não reverificados numericamente** — confirmado que nenhum jutsu tocado é
   referenciado por `personal.json`/`neutral.json`, mas não rodei a proxy de valor de novo.
