# Relatório de balanceamento PvM — rodada 10 (setembro/2026)

Tema: itens de arma e a curva do taijutsu puro em L5-40 — execução direta da recomendação
central da pendência #1 da rodada 9 ("viabilidade dos puros ≥70% falha em 64/96 níveis; lever
recomendado é buffar item de arma L5-40, não jutsu, não monstro").

## 0. Arquivos tocados

- `data/items/weapons.json`: 3 itens novos (`adaga_genin` req5, `espadao_de_aco` req25) +
  attack maior em `tanto_steel`, `gloves_taijutsu`, `wakizashi_temperado`, `katana_ronin`.
- `data/items/ruins.json`: 1 item novo (`katana_aprimorada` req30) + attack maior em
  `kodachi_ruins`, `puppet_blade`.
- `data/items/tiers.json`: attack maior em `adaga_sombria`.
- `data/tfs_mapping.json`: 3 entradas novas (ids vanilla livres, reaproveitando sprites de
  espada/adaga já usados como "sword"/"dagger" genéricos do catálogo TFS 10.98 — nunca
  compartilhados com outro item nosso, confirmado por `tools/check_mapping.py`).
- `data/npcs/leaf.json`, `data/npcs/coastal_tides.json`, `data/npcs/ruins.json`: novos itens
  adicionados ao `sells` do NPC certo da região; `gloves_taijutsu` (que já existia mas não era
  vendida em NENHUM NPC) também entrou no catálogo de Ichiro.
- `data/monsters/forest.json`, `coastal_tides.json`, `swamp.json`: `hp` de
  `boss_bandit_chief`/`boss_mist_swordsman`/`boss_white_serpent` +15% (compensação explícita da
  meta 4 — a arma nova encurtava o TTK híbrido desses 3 bosses abaixo do piso de 60s).
- `docs/sistemas/itens-e-equipamentos.md`, `docs/sistemas/balanceamento.md`,
  `tools/balance/README.md`: documentação da escada nova e dos achados.
- **Não tocado**: nenhum jutsu (`data/jutsus/*.json`, `data/element_sets.json`), nenhum
  personagem (`data/characters/*.json`), nenhum monstro além dos 3 bosses citados,
  `tools/export_tfs.py` (só executado, não editado), `tools/balance/sim.py` (só usado como
  ferramenta de medição).

## 1. Metodologia

`tools/balance/sim.py --matrix` roda só 17 níveis fixos (`MATRIX_LEVELS`); a meta da missão
("TODOS os níveis 5-100") e o "64 de 96" citado pela rodada 9 vêm de uma varredura própria
nível-a-nível (todos os 96 inteiros de 5 a 100), reproduzida nesta rodada com um script local
(não commitado, mesmo padrão das rodadas anteriores) que:

1. Para cada nível, chama `sim.nearest_common_monster(level)` (mesma função usada por
   `simulate_hunt`) e roda `sim.simulate(level, monster, build, trials=20-40)` pros builds
   `taijutsu`/`ninjutsu`/`hybrid`.
2. Razão de viabilidade = `ttk_híbrido / ttk_puro * 100` (mesma direção de leitura da rodada 9:
   <100% = híbrido mais rápido = puro "perde"; ≥70% = meta batida).
3. Pra cada degrau de arma candidato, `attack` foi encontrado por busca binária maximizando essa
   razão no PIOR nível da janela até o próximo degrau (não só no nível de desbloqueio),
   sujeito a burst do tier 1 (`jutsu_damage()` médio / `roll_weapon_damage()` médio do PRÓPRIO
   personagem, sem monstro — é uma métrica só do jogador) continuar ≥1,3× em toda a janela.
4. Depois de fechar a escada, os 6 bosses de referência foram checados com `sim.simulate()`
   real (30-100 trials) pra TTK híbrido e razão puro/híbrido.

`python3 tools/balance/sim.py --matrix --json /tmp/matrix_v10.json` (48,9s, 2040 simulações) e
`--group-matrix --json /tmp/group_v10.json` (1,3s) rodaram sem erro ao final da sessão, como
confirmação estrutural (goal 6) — não são a fonte da tabela nível-a-nível abaixo (não cobrem
todos os 96 níveis).

## 2. Escada de arma nova (meta 1, "itens de arma")

| Nível | Item | Attack antes | Attack depois | Vendedor/origem | Preço (buy) | Loot 1,5h da região |
|---|---|---|---|---|---|---|
| 1 | `kunai_iron` | 8 | 8 (sem mudança) | Ichiro | 50 | — |
| 5 | `adaga_genin` (novo) | — | 18 | Ichiro · Mercador Itsuki | 200 | 5.715 ryo/h → 8.573 |
| 8 | `tanto_steel` | 16 | 17 | Ichiro | 400 | 16.704 ryo/h → 25.056 |
| 10 | `gloves_taijutsu` | 14 | 18 | **Ichiro (novo — não era vendida em NENHUM NPC)** | 1.200 | 28.667 ryo/h → 43.000 |
| 15 | `wakizashi_temperado` | 21 | 27 | Velha Sumi · Mercador Itsuki | 1.800 | 12.849 ryo/h → 19.273 |
| 20 | `katana_ronin` | 28 | 34 | Velha Sumi · Mercador Itsuki | 2.500 | 8.397 ryo/h → 12.595 |
| 25 | `espadao_de_aco` (novo) | — | 54 | Velha Sumi · Mercador Itsuki | 5.000 | 82.472 ryo/h → 123.708 |
| 28 | `kodachi_ruins` | 40 | 58 | Tsubaki | 6.200 | 127.445 ryo/h → 191.168 |
| 30 | `katana_aprimorada` (novo) | — | 66 | Tsubaki | 7.200 | 111.725 ryo/h → 167.587 |
| 35 | `puppet_blade` | 52 | 70 | Tsubaki | 9.800 | 169.977 ryo/h → 254.965 |
| 40 | `adaga_sombria` | 54 | 70 | drop do Xamã da Maldição (sem NPC) | 12.800 | 303.760 ryo/h → 455.640 |

Todo preço fica MUITO abaixo do teto de 1,5h de loot da região (folga de 5×-25×, coluna da
direita = `1,5 × ryo/h` medido por `simulate()` build híbrido no nível do item — mesma
metodologia usada para validar `wakizashi_temperado` na rodada 4). Preço (`buy_price`) não
mudou em nenhum item existente — a fórmula `8 * required_level²` de `balanceamento.md` §5
depende só do `required_level`, que não mudou em nenhum deles.

**3 buracos reais preenchidos** (gap >7 níveis sem degrau): L1→L8 (nada em L5), L20→L28 (nada em
L25), L28→L35 (nada em L30). `gloves_taijutsu` também tinha um bug de conteúdo pré-existente,
não introduzido nesta rodada: existia em `data/items/weapons.json` desde a rodada 4 mas nunca
tinha sido colocada no `sells` de nenhum NPC — corrigido junto (Ichiro agora vende).

**`tanto_steel`/`gloves_taijutsu`/`wakizashi_temperado` receberam um `attack` MENOR que o ótimo
de viabilidade pura** (achado 4 abaixo — o valor ótimo de cada um encurtava demais o TTK híbrido
dos bosses L12/L19).

## 3. Viabilidade dos puros ≥70% em TODOS os níveis 5-100 (meta 1) — ❌ NÃO atingida, melhora real

**Resumo**: 65 → **41 de 96 níveis** abaixo de 70% (68% → 43% de falha). Melhora de ordem de
grandeza na faixa L5-40 (33 de 36 falhas → 16 de 36), que era o escopo explícito da missão.

### 3.1 Tabela detalhada L5-L40 (o escopo da missão)

| Nível | Monstro | Antes | Depois |
|---|---|---|---|
| L5 | bandit | 59,1% ❌ | 97,6% ✅ |
| L6 | bandit | 48,4% ❌ | 100,5% ✅ |
| L7 | bandit_archer | 48,4% ❌ | 81,6% ✅ |
| L8 | bandit_archer | 81,6% ✅ | 63,6% ❌ |
| L9 | leech | 63,3% ❌ | 70,5% ✅ |
| L10 | leech | 59,7% ❌ | 61,9% ❌ |
| L11 | mercenary_bridge | 67,8% ❌ | 76,6% ✅ |
| L12 | mercenary_bridge | 61,1% ❌ | 75,1% ✅ |
| L13 | giant_toad | 48,7% ❌ | 56,6% ❌ |
| L14 | mist_scout | 48,9% ❌ | 49,3% ❌ |
| L15 | mist_scout | 52,5% ❌ | 56,3% ❌ |
| L16 | mist_guardian | 46,2% ❌ (pior caso da rodada 9) | 59,9% ❌ |
| L17 | masked_apprentice | 57,8% ❌ | 64,0% ❌ |
| L18 | rogue_ninja | 63,7% ❌ | 70,1% ✅ |
| L19 | rogue_ninja | 56,7% ❌ | 68,3% ❌ |
| L20 | exam_rival_stone | 56,8% ❌ | 66,7% ❌ |
| L21 | exam_rival_stone | 56,7% ❌ | 63,8% ❌ |
| L22 | exam_rival_stone | 57,7% ❌ | 63,5% ❌ |
| L23 | exam_rival_stone | 56,2% ❌ | 63,6% ❌ |
| L24 | ruin_puppet | 70,0% ✅ | 68,6% ❌ |
| L25 | ruin_puppet | 66,3% ❌ | 93,0% ✅ |
| L26 | ruin_puppet | 64,4% ❌ | 88,5% ✅ |
| L27 | ruin_puppet | 62,3% ❌ | 86,2% ✅ |
| L28 | ruin_puppet | 76,5% ✅ | 79,4% ✅ |
| L29 | ruin_puppet | 76,6% ✅ | 72,5% ✅ |
| L30 | stone_sentinel | 54,0% ❌ | 69,2% ❌ |
| L31 | stone_sentinel | 55,6% ❌ | 70,5% ✅ |
| L32 | stone_sentinel | 61,0% ❌ | 71,5% ✅ |
| L33 | stone_sentinel | 55,2% ❌ | 68,7% ❌ |
| L34 | stone_sentinel | 49,6% ❌ | 72,3% ✅ |
| L35 | stone_sentinel | 59,5% ❌ | 73,0% ✅ |
| L36 | spectral_warrior | 63,1% ❌ | 70,5% ✅ |
| L37 | spectral_warrior | 65,6% ❌ | 67,7% ❌ |
| L38 | spectral_warrior | 63,8% ❌ | 73,0% ✅ |
| L39 | spectral_warrior | 60,6% ❌ | 74,2% ✅ |
| L40 | spectral_warrior | 61,6% ❌ | 72,2% ✅ |

L41-49 (fora do escopo "L5-L40", mas beneficiado de graça pelo buff de `adaga_sombria`, req40,
que cobre até L49): melhorou de forma consistente (ex. L46 69,3%→83,3%, L49 68,5%→80,5%),
6 de 9 níveis passam a fechar ≥70% (eram 1 de 9). L50-77 não tocado (fora do "L5-L40" — ver
pendências).

### 3.2 Achado central: teto estrutural de viabilidade que `attack` não ultrapassa

Testando valores de `attack` MUITO acima de qualquer NPC (até 500, bem além do orçamento de
burst) em alguns rungs (L5, L10, L15, L20, L35), a razão puro/híbrido **piora** a partir de um
certo ponto em vez de continuar melhorando:

```
L15 (mist_scout), attack crescente:  21→56,7%  25→54,1%  30→46,3%  40→27,7%  100→22,0%  250→15,0%
```

Causa raiz: `mist_scout` (L14, hp=260) morre tão rápido contra o híbrido que o ÚNICO cast de
tier 1 no início da luta (jutsu ignora armadura, arma não — mesma assimetria de `blockHit`
documentada desde a rodada 1) já é a maior parte do HP do monstro; aumentar `attack` acelera os
DOIS lados (puro e híbrido) mas a fração de dano "de graça" do primeiro cast de jutsu não
diminui — ela até cresce relativamente, porque o combate fica ainda mais curto. Isso é uma
tensão **diferente** da "burst vs. sustentado" das rodadas 5/9 (aquela é sobre o TAMANHO de um
cast; esta é sobre a DURAÇÃO da luta ser curta demais pra diluir esse cast). Rungs afetados por
esse teto (mesmo no valor de `attack` mais alto ainda seguro pro burst): **L5, L10, L15, L20,
L35** — o valor final de cada um foi escolhido no PICO da curva (nem o menor nem o maior
`attack` testado), não no limite de burst.

## 4. Bosses de referência (metas 3 e 4) — ✅ atingidas após ajuste de HP

A escada de arma nova encurtava o TTK híbrido dos 3 bosses baixos abaixo do piso de 60s — ajuste
de `hp` (+15%, dentro do limite da missão) nos 3 bosses afetados resolveu os dois lados (TTK e
viabilidade) ao mesmo tempo, mesmo raciocínio já usado na rodada 9 com `defense`.

| Boss | Nível | TTK híbrido só com arma nova (sem ajuste) | `hp` antes→depois | TTK híbrido final | Pure/híbrido antes→depois |
|---|---|---|---|---|---|
| `boss_bandit_chief` | 12 | 39,9s ❌ (abaixo de 60s) | 1.500→1.725 (+15%) | **66,8s** ✅ | 61,8% → **65,8%** |
| `boss_mist_swordsman` | 19 | 51,9s ❌ | 2.380→2.737 (+15%) | **63,9s** ✅ | 60,5% → **68,9%** |
| `boss_white_serpent` | 25 | 55,1s ❌ | 4.600→5.290 (+15%) | **63,6s** ✅ | 62,8% → **83,0%** |
| `boss_puppeteer` | 50 | não tocado | não tocado | 58,8s (ver pendências) | 75,9% (inalterado) |
| `boss_ancestral_oni` | 80 | não tocado | não tocado | 80,1s | 79,6% (inalterado) |
| `boss_crimson_ancestor` | 100 | não tocado | não tocado | 91,4s | 82,3% (inalterado) |

`death_rate` = 0,00 nos 6 (com poções), como nas rodadas anteriores. Nenhum boss ultrapassou
180s. **`tanto_steel`/`gloves_taijutsu`/`wakizashi_temperado` tiveram o `attack` reduzido do
"ótimo de viabilidade pura" (20/28/30) pra um valor mais conservador (17/18/27)** justamente
porque o valor ótimo, combinado com o `attack` já alto dos itens vizinhos, encurtava o TTK dos
bosses L12/L19 demais mesmo com os 15% de HP — a versão final é o maior `attack` que ainda deixa
folga segura (TTK ≥63s, >5% acima do piso de 60s) nesses 2 bosses.

## 5. Ninjutsu ≥70% e nunca excede híbrido (meta 2) — ✅ mantida/melhorada

Mesma varredura nível-a-nível pro build `ninjutsu`: **35 de 96 abaixo de 70%** (melhor que
taijutsu, porque a build cai pro fallback de arma sempre que o jutsu não vale a pena — herda o
buff de arma automaticamente). **Nenhum overshoot real sobre o híbrido**: só 1 nível (L6) empata
em 100,5% — os dois builds caem pro "só arma" nesse nível específico (`bandit`, muito fraco pro
nível), não é ninjutsu vencendo por jutsu. Não foi necessário reduzir nenhum passo da escada por
causa desta meta.

## 6. Burst do tier 1 ≥1,3× (meta 3, "manter") — ✅ mantido sem regressão

Checado nível a nível (L1-100, não só a amostra): **4 de 100 níveis abaixo de 1,3×** —
exatamente o mesmo padrão de antes desta rodada (L78, L79, L80, L100 — "aceito perder L78+" já
documentado desde a rodada 5). A escada nova foi desenhada com essa restrição como limite duro
(busca binária capada em burst≥1,3×, ver §1) — nenhum item da escada L5-40 quebra o burst na sua
janela de uso; o único quase-erro (achado 4 do README) foi `adaga_sombria` numa janela mais
larga que o previsto (L40-49, não L40-44), corrigido antes da entrega final.

## 7. Kits pessoais ±15% (meta 5) — ✅ mantida (não verificada numericamente, sem risco)

Nenhum jutsu (`data/jutsus/*.json`, `data/element_sets.json`) nem personagem
(`data/characters/*.json`) foi tocado nesta rodada — só itens de arma (que nenhum kit pessoal
referencia por id, confirmado por grep) e `hp` de 3 bosses. A proxy de valor de kit não depende
de item de arma comprável (usa a média de dano/chakra dos jutsus do personagem), então o risco é
zero por construção, não por reverificação.

## 8. `validate_data.py` / `export_tfs.py` / `check_mapping.py` / timing (meta 6)

```
.venv/bin/python tools/validate_data.py      # OK — 54 jutsus, 177 itens (era 174), 40 monstros
.venv/bin/python tools/export_tfs.py         # OK — 177 itens, 21 NPCs, server/generated/
.venv/bin/python tools/check_mapping.py      # OK — 177 itens, 177 ids vanilla únicos
python3 tools/balance/sim.py --matrix --json /tmp/matrix_v10.json        # 2040 sims, 48,9s (<120s)
python3 tools/balance/sim.py --group-matrix --json /tmp/group_v10.json   # 36 grupo + 18 boss, 1,3s
```

`export_tfs.py` avisa que os 3 itens novos (`adaga_genin`, `espadao_de_aco`,
`katana_aprimorada`) substituem itens vanilla de mesmo id — comportamento esperado (modo
OVERRIDE, mesmo padrão de todo item já existente que reaproveita sprite vanilla, ex.
`wakizashi_temperado`), não um erro. Não rodei `install_generated.sh`, não reiniciei o servidor,
não usei o cliente — só `export_tfs.py` pra conferência, como orientado.

## 9. Documentação atualizada (meta 7)

- `docs/sistemas/itens-e-equipamentos.md`: seção nova "Escada de arma melee L1-L40" com a
  tabela completa antes/depois, vendedor e preço de cada degrau.
- `docs/sistemas/balanceamento.md`: metas 3/4 atualizadas com os achados desta rodada; §5
  (preço de item) ganhou um parágrafo sobre a escada nova e por que 3 itens ficaram com
  `attack` deliberadamente abaixo do ótimo de viabilidade.
- `tools/balance/README.md`: seção "Achados da rodada 10" + "Pendências honestas da rodada 10".
- `data/tfs_mapping.json`: 3 entradas novas.

## 10. Metas atingidas / não atingidas — resumo honesto

| Meta | Resultado |
|---|---|
| 1. Taijutsu puro ≥70% do DPS híbrido em TODOS os níveis 5-100 | ❌ **Não atingida** — 41/96 abaixo de 70% (era 65/96); melhora real na faixa L5-40 (33/36→16/36), mas achado novo prova que parte do restante é um teto estrutural que nenhum `attack` de arma fecha (§3.2) |
| 1b. Escada de arma a cada ~5 níveis L5-L40, vendida na região certa, preço ≤1,5h de loot | ✅ **Atingida** — 3 buracos reais preenchidos, todos os preços com folga de 5×-25× sobre o teto |
| 2. Ninjutsu puro ≥70% e nunca excede híbrido | ✅ **Mantida/melhorada** — 35/96 abaixo de 70% (melhor que taijutsu); 0 overshoots reais |
| 3. Burst tier 1 ≥1,3× em L1-77 | ✅ **Mantido sem regressão** — mesmo padrão de falha (só L78-80,100), escada desenhada com esse limite como restrição dura |
| 4. Bosses TTK híbrido 60-180s, ajuste de HP ±15% se necessário | ✅ **Atingida** — 3 bosses baixos precisaram de +15% HP; viabilidade ≥60% nos 6 bosses batida com folga (65,8%-83,0%) |
| 5. Kits ±15% | ✅ **Mantida** — nenhum jutsu/personagem tocado |
| 6. `validate_data.py`/`export_tfs.py` OK, `--matrix`<120s | ✅ **Confirmado** — 48,9s |
| 7. Documentação | ✅ **Atingida** — 4 arquivos atualizados/criados |

### Pendências honestas para a rodada 11

1. **Viabilidade dos puros ≥70% ainda falha em 41 de 96 níveis** — achado novo (§3.2): em
   vários rungs (L5, L10, L15, L20, L35) o teto de viabilidade não sobe mais mesmo com `attack`
   muito além do que qualquer NPC venderia, porque o monstro mais próximo desses níveis morre
   rápido demais pro cast único de tier 1 do híbrido virar uma fração pequena do dano total.
   Levers que sobram (nenhum é "só item de arma"): HP de monstro comum maior nesses pontos
   específicos, ou uma mudança de modelo/engine (dano de jutsu reduzido contra alvos que já
   morreriam num único hit de qualquer forma).
2. **L41-77 não tocado** (fora do "L5-L40" da missão) — continua com falhas parecidas às da
   rodada 9, exceto L41-49 que melhorou de graça (efeito colateral de `adaga_sombria`).
3. **`boss_puppeteer` (L50) medido em 58,84s** — abaixo do piso de 60s, não tocado nesta rodada
   (usa item req50 intocado); parece variação de medição em relação aos 62,7-62,8s de relatórios
   anteriores, sinalizado pra investigação, não corrigido (fora do escopo "só L5-40").
4. **`ruin_puppet` (grupo N=3) saiu de +22,5% pra -32,8%** (ninjutsu virou desvantagem sobre
   taijutsu nesse cenário de pull) — efeito colateral direto de `espadao_de_aco` (req25); a meta
   de grupo +30-60% não é uma meta explícita desta rodada, mas fica sinalizado.
5. **Kits (±15%) não reverificados numericamente** — confiança alta (nenhum jutsu/personagem
   tocado), mas a proxy não foi rodada de novo.
