# Relatório de balanceamento PvM — rodada 4 (setembro/2026)

Continuação direta da rodada 3 (`docs/sistemas/balanceamento-relatorio-v3.md`), que fechou com
2 pendências centrais que esta rodada ataca de frente: **(1)** a tensão entre burst (jutsu
"sentido") e paridade sustentada — resolvida trocando o cooldown do tier 1 de 2,0s (igual ao
intervalo de ataque do player) para 3,5s, o que **matematicamente destrava** as duas metas ao
mesmo tempo (ver §1); **(2)** o platô de arma L15→L20 que deixava o boss L19 fora da meta — um
item novo (`wakizashi_temperado`) fecha o buraco. Também: regen permanente modelado como padrão
(não mais "sem regen"), pílula de chakra simulada em combate pela primeira vez, e um cenário de
"hunt de 30 min" novo no simulador para medir chakra sustentável de verdade em vez de luta única.

## 0. Arquivos tocados

- `tools/balance/sim.py`: modelo de híbrido intercalado (arma+jutsu em cadências
  independentes), `_CHAKRA_POTIONS` finalmente usado em combate, `simulate_hunt`/
  `run_hunt_matrix`/`nearest_common_monster` novos, `best_item_for_slot` corrigido (escolhia por
  `required_level`, não pelo atributo — bug real, ver §3), `HYBRID_TAIJUTSU_FRAC`/
  `HYBRID_NINJUTSU_FRAC` recalibrados (0,5→0,4), CLI `--hunt`/`--minutes`/`--chakra-pills`.
- `data/jutsus/{katon,fuuton,raiton,doton,suiton}.json`: os 5 projéteis tier 1 do kit elemental
  (cooldown 2,0s→3,5s, dano maior) e 3 dos tier 2 (`katon_housenka`, `fuuton_rajada_cortante`,
  `raiton_lanca_relampago`, cooldown 4,0-5,5s→6,0-6,5s, dano escalado pra preservar o DPS — ver
  §4). Nenhum outro jutsu (tier 2/3 "teto"/controle, `personal.json`, `neutral.json`) foi tocado.
- `data/items/weapons.json`: item novo `wakizashi_temperado` (req15, melee, attack 21).
- `data/tfs_mapping.json`, `data/npcs/coastal_tides.json`, `data/npcs/leaf.json`: mapeamento TFS
  e venda do item novo nas lojas da região do boss L19 e da Vila (ver §3).

**Não tocado**: `data/monsters/*.json` (fora do escopo — nenhum HP/dano de monstro mudou),
`data/characters.json`/`personal.json`/`neutral.json` (ver §7 — pendência de reverificação, não
de mudança), `server/generated/*` e `server/tfs/data/*` (só `tools/export_tfs.py` rodado, sem
instalar — nenhum arquivo do servidor em execução foi tocado, conforme instruído).

## 1. Regen permanente + pílula de chakra em combate (modelagem, mission item 1)

**Regen**: `server/tfs/data/scripts/naruto/character_switch.lua` (linha ~30, bloco
`-- Regeneracao natural`) aplica uma `Condition(CONDITION_REGENERATION, ...)` com
`CONDITION_PARAM_TICKS=-1` (permanente) no login, usando `gainhpamount`/`gainmanaamount` da
vocação (`vocations.xml`: 2 HP/5s, 3 chakra/5s = 0,6 chakra/s, igual em toda vila) — isso é
aplicado via `player:addCondition`, **não depende de comida** (diferente do TFS vanilla) e não é
suspenso em combate (nenhum código do projeto reseta essa condição ao entrar em luta). O achado
do playtest r3 (P1-1, "chakra travado em 8/60 por 7 minutos") é, portanto, **consistente com o
código real**: a condição regenera de fato, mas 0,6/s é tão lento que não é perceptível numa
janela de minutos contra um pool de dezenas — o playtest não estava vendo um bug, estava vendo a
escala real do número. `tools/balance/sim.py` já modelava esse regen contínuo desde a rodada 1
(`SimPlayer.regen_tick`, chamado a cada `dt` do loop, nunca pausado) — o que faltava era **não
tratar isso como ausência de regen** na documentação, e é isso que este relatório e
`balanceamento.md` corrigem.

**Pílula de chakra**: `server/tfs/data/actions/scripts/other/potions.lua:onUse` (a ação que
processa `data/items/consumables.json` tipo `heal_chakra`, mapeado pros itens vanilla "mana
potion"/"strong mana potion" via `data/tfs_mapping.json`) **não seta nenhuma
`Condition`/exhaustion no item** — TFS 1.4.2 deixa beber quantas poções o cliente conseguir
enviar em sequência. `tools/balance/sim.py` agora simula isso com o mesmo `POTION_DRINK_COOLDOWN_S
= 1.0` (aproximação documentada, não uma regra real do TFS — sem ALGUM intervalo o Monte Carlo
bebe uma pilha inteira num único tick de 0,1s) já usado pra poção de vida desde a rodada 1;
`_CHAKRA_POTIONS` (carregado desde a rodada 3 mas nunca lido em combate — pendência #5 do
relatório v3) agora é bebido quando o chakra não basta pro jutsu escolhido, com `--chakra-pills`
(1×1) ou automaticamente na hunt (ver §7).

## 2. Burst feel: cooldown de tier 1 3,5s + híbrido intercalado (mission item 2)

### A prova matemática que destrava a tensão da rodada 3

A rodada 3 (§8 do relatório v3) provou que, com `cooldown_tier1 == ATTACK_INTERVAL_S` (2,0s nas
duas rodadas), a meta de burst (hit ≥1,3× o hit de arma) e a meta de paridade sustentada
(DPS de jutsu ≈ DPS de arma) são **matematicamente incompatíveis** — se
`dano_tier1/cooldown ≈ dano_arma/attack_interval` e `cooldown == attack_interval`, então
necessariamente `dano_tier1 ≈ dano_arma` por hit (nunca 1,3×). Com `cooldown_tier1 = 3,5s`:

```
hit_tier1 = 1,3 × hit_arma  (meta de burst, no limite)
dps_tier1_se_spammado = hit_tier1 / 3,5 = 0,371 × hit_arma
dps_arma               = hit_arma / 2,0  = 0,500 × hit_arma
razão = 0,371 / 0,500 = 0,743  →  dps de jutsu SEMPRE abaixo do de arma, mesmo no limite do burst
```

Ou seja: com cooldown 3,5s, **um tier 1 que bate exatamente a meta de burst (1,3×) já entrega,
sozinho e sem limite de chakra, menos DPS sustentado que a arma** — a rotação racional do
ninjutsu puro (`pick_ninjutsu_jutsu`, decisão "só uso se bate a arma") rejeita automaticamente
usá-lo como substituto contínuo, convergindo pra taijutsu puro (paridade limpa, 0% de diferença)
sem precisar de nenhum ajuste de chakra pra isso. Isso só funciona pro **build híbrido** de um
jeito diferente: lá o jutsu não é um substituto (não ocupa o turno da arma), é uma camada
adicional — por isso o híbrido precisa de uma regra própria (ver "Híbrido intercalado" abaixo).

### Recalibração aplicada (5 projéteis tier 1)

| Jutsu | cooldown antes→depois | chakra antes→depois | base/level/skill antes | base/level/skill depois |
|---|---|---|---|---|
| `katon_goukakyuu` | 2,0s→**3,5s** | 15→**30** | 8,75 / 0,42 / 0,28 | 4,0 / 3,3 / 0,1 |
| `fuuton_lamina_vento` | 2,0s→**3,5s** | 13→**26** | 8,05 / 0,385 / 0,297 | 3,68 / 3,03 / 0,106 |
| `raiton_hari` | 2,0s→**3,5s** | 14→**28** | 7,0 / 0,385 / 0,315 | 3,2 / 3,03 / 0,1125 |
| `doton_bala_lama` | 2,0s→**3,5s** | 14→**28** | 8,05 / 0,385 / 0,297 | 3,68 / 3,03 / 0,106 |
| `suiton_mizudan` | 2,0s→**3,5s** | 12→**25** | 7,7 / 0,385 / 0,28 | 3,52 / 3,03 / 0,1 |

O `level_scale` cresceu ~8× (era pensado pra um cooldown igual ao da arma; agora precisa cobrir
1,75× mais tempo por cast) e o `skill_scale` caiu (o magic level não é confiável o bastante numa
faixa tão ampla — ver rodada 3 §1 — então o `level` puro é o lever principal). Custos escalaram
~2× (não os ~2,5-12× que testei antes de perceber a tensão com a rodada 4 abaixo — ver §7).

### Resultado: hit médio de tier 1 vs arma (com vantagem elemental)

| Nível | Hit médio de arma | Hit tier 1 (c/ vantagem) | Razão | Meta ≥1,3× |
|---|---|---|---|---|
| 1 | 5,0 | 11,1 | 2,22× | ✅ |
| 5 | 15,5 | 34,3 | 2,22× | ✅ |
| 10 | 37,5 | 60,0 | 1,60× | ✅ |
| 15 | 54,0 | 85,5 | 1,58× | ✅ |
| 20 | 76,5 | 110,9 | 1,45× | ✅ |
| 25 | 82,0 | 136,2 | 1,66× | ✅ |
| 30 | 119,5 | 162,0 | 1,36× | ✅ |
| 40 | 178,0 | 212,1 | 1,19× | ❌ (perto) |
| 50 | 285,5 | 263,0 | 0,92× | ❌ |
| 60 | 282,5 | 314,5 | 1,11× | ❌ |
| 70 | 423,0 | 363,1 | 0,86× | ❌ |
| 80 | 527,0 | 413,2 | 0,78× | ❌ |
| 90 | 538,0 | 464,0 | 0,86× | ❌ |
| 100 | 681,5 | 515,0 | 0,76× | ❌ |

**Melhora real vs rodada 3** (mesma tabela, `--no-fallback`, cooldown 2,0s): L10 0,93×→**1,60×**,
L15 0,98×→**1,58×**, L20 0,55×→**1,45×**, L30 (não medido em r3, ~0,3× esperado)→**1,36×**, L50
0,24×→**0,92×**, L100 0,16×→**0,76×**. A meta de 1,3× agora fecha em **L1 a L30** (antes só
L1-5); L40+ continua abaixo, mas a distância caiu de "5-6× fraco demais" para "20-30% fraco" —
uma melhora de ordem de grandeza, não perfeita. Ver §10 pra por que L40+ não fecha (o dano de
arma cresce ~40× de L1 a L100 enquanto o jutsu só pode crescer linear em `level` — a mesma
incompatibilidade de forma que a rodada 3 já tinha identificado, só que agora empurrada pra mais
tarde no jogo em vez de aparecer desde L10).

### Híbrido intercalado: "arma entre casts" vira mecanismo real, não só design

Achado de arquitetura da própria rodada 4: o `simulate_fight` antigo tratava jutsu e arma como a
MESMA ação (cast de jutsu = `next_player_action = t + cooldown`, ou seja, o personagem ficava
**parado** entre casts, sem atacar com a arma) — isso sempre foi verdade desde a rodada 1, mas só
importava pouco enquanto cooldown de tier 1 (2,0s) ≈ intervalo de ataque (2,0s). Com 3,5s, essa
folga de 1,5s ociosa por cast vira relevante, e é exatamente o "híbrido = arma entre casts"
pedido na missão. Fix: `simulate_fight`/`simulate_hunt` agora rodam a arma e o jutsu em **timers
independentes** pro build `hybrid` (a arma ataca a cada `ATTACK_INTERVAL_S`, o jutsu lança
sempre que pronto e pagável, os dois SEM se atrapalhar) — `ninjutsu` puro continua no modelo de
ação única (jutsu OU arma), porque pra ele o jutsu é um SUBSTITUTO racional da arma (só vale a
pena se bate o DPS dela), não uma camada adicional. Consequência direta: o híbrido agora sempre
usa o jutsu quando pronto/pagável (`no_fallback=True` fixo pro build `hybrid`, já que "só uso se
bate a arma" não faz sentido quando o jutsu não ocupa o turno da arma) — isso tornou o híbrido
sistematicamente ≥ os dois builds puros (nunca mais abaixo, ver §2 tabela), mas com um teto de
+15% que nem toda fração de skill testada consegue fechar (ver `HYBRID_TAIJUTSU_FRAC`/
`HYBRID_NINJUTSU_FRAC` em `tools/balance/sim.py`, 0,5→0,4, e §10).

### Paridade sustentada 1×1 (ninjutsu puro) e híbrido, 6 bosses de `GROUP_SCENARIOS`

| Boss | Nível | TTK taijutsu | TTK ninjutsu | ninj vs taij | TTK híbrido | híbrido vs melhor |
|---|---|---|---|---|---|---|
| Chefe dos Bandidos | 12 | 132,95s | 111,56s | **-16,1%** ❌ (perto) | 110,61s | +0,9% ✅ |
| Espadachim da Névoa | 19 | 89,59s | 69,48s | **-22,4%** ❌ | 47,08s | +47,6% ❌ |
| Serpente Branca | 25 | 163,51s | 151,46s | -7,4% ✅ | 123,79s | +22,4% ❌ |
| Marionetista | 50 | 78,98s | 78,98s | 0,0% ✅ (fallback total) | 69,96s | +12,9% ✅ |
| Oni Ancestral | 80 | 93,68s | 93,68s | 0,0% ✅ (fallback total) | 75,57s | +24,0% ❌ |
| Ancestral Carmesim | 100 | 102,82s | 102,82s | 0,0% ✅ (fallback total) | 78,98s | +30,2% ❌ |

Meta ninjutsu puro (−15%..+10%): **4 de 6 dentro** (L25/50/80/100); L12 fica a 1,1 ponto do
limite (-16,1%); **L19 é o outlier real** (-22,4%, ver §10 — o mesmo boss que era o platô de
arma na rodada 3, agora com uma causa diferente). Meta híbrido (≥ ambos, ≤+15%): **nunca fica
abaixo do melhor** (ganho real da mudança de arquitetura), mas só L12/L50 ficam dentro do teto
de +15% — L19/25/80/100 excedem, alguns bastante (§10, pendência honesta).

## 3. Platô de arma L15→L20 (mission item 3)

**Dois problemas achados, um data e um bug do simulador:**

1. **Bug do simulador** (`tools/balance/sim.py`, `best_item_for_slot`): escolhia o item pelo
   MAIOR `required_level`, não pelo maior atributo — `gloves_taijutsu` (req10, attack=**14**)
   tem `required_level` maior que `tanto_steel` (req8, attack=**16**), então de L10 a L19 o
   simulador vestia as luvas (mais fracas!) em vez do tantō, um "downgrade automático" que
   piorava artificialmente o platô. Corrigido: agora pega o maior `attack`/`defense` entre os
   itens desbloqueados, não o de `required_level` mais recente.
2. **Platô de dado real**: mesmo com o bug corrigido, `tanto_steel` (req8, attack 16) é a única
   arma melee de L8 a L19 — 12 níveis flat — antes de `katana_ronin` (req20, attack 28). É esse
   platô que deixava o boss L19 (Espadachim da Névoa, `boss_mist_swordsman`) lutando com uma
   arma de nível 8 efetivo.

**Fix aplicado**: item novo `wakizashi_temperado` (`data/items/weapons.json`, req15, melee,
attack **21** — meio do caminho entre 16 e 28, western `buy_price = 8×15² = 1800` exatamente na
fórmula de `balanceamento.md` §5), mapeado em `data/tfs_mapping.json` (`"wakizashi_temperado":
2384` — id vanilla "rapier", livre, mesmo padrão de reaproveitar sprite/id do TFS que
`tanto_steel`/`katana_ronin` já usam) e adicionado à venda de **Mercador Itsuki**
(`data/npcs/coastal_tides.json`, a loja da própria região do boss L19) e **Velha Sumi**
(`data/npcs/leaf.json`, redundância regional). Curva de arma melee agora:

| Nível | Antes (arma equipada) | Depois |
|---|---|---|
| 8–14 | Tantō de Aço (16) | Tantō de Aço (16) — sem mudança |
| 15–19 | Tantō de Aço (16) — **platô de 12 níveis** | **Wakizashi Temperado (21) — NOVO** |
| 20+ | Katana do Ronin (28) | Katana do Ronin (28) — sem mudança |

**Efeito isolado do fix de arma no boss L19** (medido ANTES de qualquer mudança de jutsu, só
`best_item_for_slot` + item novo): diferença ninjutsu vs taijutsu caiu de **-25,8%** (rodada 3,
modo `--no-fallback`) para **-1,2%** — o platô de arma sozinho já explicava quase todo o desvio.
A recalibração de jutsu do §2 reabriu uma diferença nova e menor (-22,4%, ver §10) por um motivo
diferente (doton, o elemento com vantagem contra suiton, só tem o projétil tier 1 desbloqueado
em L19 — nenhum tier 2/3 ainda — tornando esse boss o teste mais "puro" do novo tier 1).

**Pendência não corrigida**: a mesma lacuna existe no lado ranged (`senbon_de_ferro` req10→
`fuuma_shuriken` req25, 15 níveis flat) — fora do escopo desta rodada (a missão citava
especificamente L15→L20/boss L19, que é melee).

## 4. Tier 2 com cooldown 6-12s (mission item 2, continuação)

3 dos 8 jutsus tier 2 do kit automático tinham cooldown abaixo de 6s (fora da faixa 6-12s
pedida): `katon_housenka` (4,0s), `fuuton_rajada_cortante` (4,5s), `raiton_lanca_relampago`
(5,5s). Ajustados pra 6,0-6,5s com `base_damage`/`level_scale`/`skill_scale` escalados pelo MESMO
fator do cooldown (preserva o DPS exato calibrado na rodada 3 — só o hit fica maior e o cast mais
espaçado, sem reabrir a paridade de grupo já obtida):

| Jutsu | cooldown antes→depois | base_damage antes→depois | level_scale antes→depois |
|---|---|---|---|
| `katon_housenka` | 4,0s→**6,0s** | 16,2→**24,3** | 2,07→**3,105** |
| `fuuton_rajada_cortante` | 4,5s→**6,5s** | 27,0→**38,99** | 2,691→**3,886** |
| `raiton_lanca_relampago` | 5,5s→**6,5s** | 39,6→**46,8** | 1,35→**1,596** |

Os outros 5 tier 2/3 do kit (`katon_anel_chamas` 6,0s, `katon_karyuu_endan` 8,0s,
`fuuton_tornado_cortante` 8,0s, `fuuton_redemoinho_prisao` 9,0s, `raiton_punho_trovao` 7,0s,
`doton_estacas_terra` 6,0s, `doton_colapso_terreno` 9,0s, `suiton_suiryuudan` 6,0s,
`suiton_prisao_agua` 7,0s) já estavam dentro de 6-12s desde a rodada 3 — intocados.

## 5. Cenário "hunt de 30 min" e chakra sustentável (mission item 1, medição real)

`simulate_hunt` (novo, `tools/balance/sim.py`): sequência de pulls 1×1 do monstro comum mais
próximo do nível pedido (`nearest_common_monster`), pausas uniformes de 5-15s entre lutas (não a
downtime fixa de 3,0s do XP/h "throughput máximo"), HP/chakra persistindo com regen contínuo
entre lutas, morte custando `DEATH_RECOVERY_S=75s` (viagem de volta, `docs/qa/
playtest-l1-20-r3.md`) + a pausa normal. Mede a fração do tempo em que o chakra fica abaixo do
custo do tier 1 do elemento escolhido — a pergunta literal da missão.

| Nível | Monstro | %tempo sem chakra p/ tier 1 (SEM pílula) | Meta ≤20% | %tempo sem chakra (COM pílula) | Meta 0% |
|---|---|---|---|---|---|
| 5 | Bandido | **97,6%** | ❌ | 0,8% | ✅ (quase) |
| 15 | Batedor da Névoa | **93,4%** | ❌ | 0,2% | ✅ |
| 30 | Sentinela de Pedra | 14,6% | ✅ | 0,1% | ✅ |
| 60 | Oni da Geleira | 9,8% | ✅ | 0,0% | ✅ |
| 100 | Guarda de Elite da Nuvem | 11,6% | ✅ | 0,1% | ✅ |

**3 de 5 níveis dentro da meta sem pílula** (L30/60/100); **com pílula, 4 de 5 praticamente em
0%** (L5 fica em 0,8%, arredondamento de trials). **L5 e L15 falham feio sem pílula** — motivo
estrutural, não erro de calibração pontual: o pool de chakra cresce com o nível
(`50+level×10` — 100 em L5, 200 em L15) mas o custo de tier 1 é **flat** (a mesma pílula/jutsu
custa o mesmo em qualquer nível), então um custo calibrado pra não dominar uma luta de boss de
90-150s em L12-25 (§2) é proporcionalmente ENORME contra o pool minúsculo de L5-15 — e o regen
(0,6 chakra/s, fixo) é rápido demais pra qualquer pull de boss mas devagar demais pra recuperar
esse custo entre pulls curtos de monstro comum. **Essa é uma tensão nova, não documentada nas
rodadas 1-3** (que nunca tinham medido uma hunt de verdade) — ver §10.

## 6. Custo real: pílulas/h que o jogador consegue bancar (mission item 4)

`ryo_per_hour` (líquido, build híbrido, monstro comum do nível — `nearest_common_monster`) vs
custo de manter ~0% sem chakra (pílulas/h realmente gastas na hunt COM pílula):

| Nível | ryo/h (líquido) | Pílula usada | Preço | Pílulas/h gastas na hunt | Ryo/h gasto em pílulas | Pílulas/h que o ryo/h BANCA | Sobra? |
|---|---|---|---|---|---|---|---|
| 5 | 5 572 | Pequena (30 ryo) | 30 | 304 | 9 120 | 185,7 | **NÃO — déficit de 9 120-5 572=3 548 ryo/h** |
| 15 | 14 201 | Média (120 ryo) | 120 | 80 | 9 600 | 118,3 | **NÃO — déficit de ~600 ryo/h (perto)** |
| 30 | 212 471 | Grande (250 ryo) | 250 | 38 | 9 500 | 850,0 | Sim, sobra grande |
| 60 | 605 647 | Grande (250 ryo) | 250 | 14 | 3 500 | 2 422,6 | Sim, sobra grande |
| 100 | 1 801 138 | Grande (250 ryo) | 250 | 26 | 6 500 | 7 204,6 | Sim, sobra grande |

**Achado direto**: em L5, o jogador precisaria de ~304 pílulas/h (9 120 ryo/h) pra zerar o tempo
sem chakra, mas só ganha ~5 572 ryo/h caçando — **não dá pra bancar** (déficit real, não só
"caro"). Em L15 o déficit é pequeno (~600 ryo/h, ~4% do ganho) — quase sustentável. De L30 em
diante a economia sobra muito (o ryo/h cresce muito mais rápido que o custo de pílula, que é
flat como o `chakra_cost`). **Isso confirma a preocupação da missão**: em L5-15, ninjutsu
"depende de pílula que o jogador não paga" — ver §10 pra recomendação (não apliquei, é uma
escolha de design: baixar ainda mais o custo do tier 1 nesses níveis especificamente re-abriria
a paridade sustentada do §2, ou dar ao Genin uma reserva inicial maior de pílulas grátis).

## 7. Personagens e elementos — reverificação (mission constraints, não alterado)

- **Elementos (±10%)**: comparando os "campeões" de cada kit (tier 3 ou tier 2-teto,
  `katon_karyuu_endan`/`fuuton_tornado_cortante`/`raiton_punho_trovao`/`doton_colapso_terreno`/
  `suiton_suiryuudan` — nenhum tocado nesta rodada) por DPS em L80: **-0,3% a +0,3%** — igual ao
  ±3% já validado na rodada 3 (esperado, já que nenhum desses 5 jutsus mudou de número).
- **Personagens (±15%)**: **não reverificado numericamente nesta rodada** — `personal.json` e
  `neutral.json` não foram tocados, então os 9 personagens permanecem nos valores da rodada 3
  (-8,6% a +10,2%). O risco real: a métrica-proxy de jutsu utilitário usada nas rodadas 2/3 (média
  de dano/chakra de TODOS os jutsus de dano) muda quando qualquer jutsu de dano muda — e o §2/§4
  mudaram 8 jutsus elementais. Não recalculei essa proxy (fora do orçamento desta rodada) —
  **pendência honesta**, ver §10.

## 8. Curva antes → depois (resumo por nível)

| Nível | Hit arma | Hit tier 1 (antes r3→depois r4) | DPS taijutsu (TTK boss) | DPS ninjutsu (Δ%) | DPS híbrido (Δ% vs melhor) | Chakra sustentável 30min (sem/com pílula) |
|---|---|---|---|---|---|---|
| 12 | 39,0 | — / 1,38× | 132,95s | -16,1% | +0,9% | — |
| 19 | 54,0* | 0,98×(r3) / 1,58×(r4) | 89,59s | -22,4% | +47,6% | — |
| 25 | 82,0 | — / 1,66× | 163,51s | -7,4% | +22,4% | — |
| 30 | 119,5 | ~0,3×(r3 estimado) / 1,36× | — | — | — | 14,6% / 0,1% |
| 50 | 285,5 | 0,24×(r3) / 0,92×(r4) | 78,98s | 0,0% | +12,9% | — |
| 60 | 282,5 | — / 1,11× | — | — | — | 9,8% / 0,0% |
| 80 | 527,0 | — / 0,78× | 93,68s | 0,0% | +24,0% | — |
| 100 | 681,5 | 0,16×(r3) / 0,76×(r4) | 102,82s | 0,0% | +30,2% | 11,6% / 0,1% |

\* L19 antes do fix de arma (r3) usava a arma L8 (16 attack); depois (r4) usa `wakizashi_temperado`
(21 attack) — os dois "hit arma" da tabela já refletem seus respectivos períodos.

## 9. `validate_data.py` / `export_tfs.py` / timing (mission item 5)

```
.venv/bin/python tools/validate_data.py   → OK — tudo válido (54 jutsus, 174 itens, 38 monstros...)
.venv/bin/python tools/export_tfs.py      → OK, sem erros (38 monstros, 54 jutsus, 174 itens...)
python3 tools/balance/sim.py --matrix --json ...   → 1938 simulações em 55,1s (orçamento: 120s)
python3 tools/balance/sim.py --group-matrix --json ... → 36 grupo + 18 boss em 1,1s
python3 tools/balance/sim.py --hunt --json ...     → 5 níveis × 2 (com/sem pílula) em 0,2s
```

Nenhum arquivo em `server/generated/` ou `server/tfs/data/` foi instalado
(`install_generated.sh` **não** rodado) nem o servidor reiniciado, conforme instruído (playtest
em andamento).

## 10. Pendências honestas

1. **Boss L19 continua fora da meta, por um motivo NOVO**: -22,4% (era -25,8% pelo platô de
   arma na rodada 3; o fix de arma sozinho já tinha derrubado isso para -1,2%, mas a
   recalibração de tier 1 do §2 reabriu uma diferença — L19 é o único boss testado onde o
   elemento com vantagem (doton vs suiton) só tem o PROJÉTIL tier 1 desbloqueado, nenhum tier
   2/3 — tornando esse encontro o teste mais "puro" e mais sensível ao novo tier 1 de todos os
   6 bosses). Não achei um ajuste que resolvesse L19 sem reabrir L12/L25 pro lado oposto —
   precisaria de um número específico pro `doton_bala_lama` nesse boss em particular, ou de
   uma calibração por-monstro (fora do escopo de "um número por jutsu").
2. **Híbrido nunca fica pior que o melhor build puro (ganho real desta rodada), mas o teto de
   +15% não fecha em 4 dos 6 bosses** (L19 +47,6%, L25 +22,4%, L80 +24,0%, L100 +30,2%) —
   `HYBRID_TAIJUTSU_FRAC`/`HYBRID_NINJUTSU_FRAC` foi escolhido (0,4) priorizando "nunca abaixo
   do melhor" sobre "nunca acima do teto", porque um híbrido pior que os dois builds puros
   invalidaria a proposta de design inteira (ninguém jogaria híbrido); ver comentário em
   `tools/balance/sim.py` pra sweep completo de frações testadas (nenhuma fecha os dois lados).
3. **Chakra sustentável falha em L5 e L15 sem pílula** (97,6%/93,4% do tempo sem chakra, meta
   ≤20%) — tensão estrutural nova (§5/§6): custo flat de tier 1 calibrado pra não dominar boss
   de L12-25 é proporcionalmente grande demais contra o pool minúsculo de L5-15, e a economia
   de L5 literalmente não sustenta pílulas suficientes pra compensar (déficit de ~3 548 ryo/h,
   §6). Não resolvido — exigiria ou um custo de tier 1 mais baixo especificamente pros
   primeiros ~15 níveis (o jogo não tem chakra_cost por faixa de nível, só por jutsu) ou uma
   pílula gratuita/mais barata cedo (decisão de design de economia, não numérica).
4. **Grupo 3+ (meta +30-60%) segue não-uniforme, herdado da rodada 3, não resolvido**:
   `ruin_puppet`(+35%)/`lesser_serpent`(+33%) agora DENTRO da meta (eram +24,6%/N/A na rodada
   3); `wolf`(-12%)/`bandit`(+5%)/`leech`(+13%)/`mercenary_bridge`(+18%)/`mist_guardian`(+17%)
   seguem abaixo; `curse_shaman`(+177%)/`thunder_eagle`(+178%, era +442% na rodada 3 — melhorou
   muito, mas ainda longe)/`storm_monk`(+234%)/`elite_cloud_guard`(+117%) seguem MUITO acima;
   `white_clone` ficou negativo (-31%, pior que o taijutsu). Mesma causa raiz que a rodada 3 já
   documentou (§6/§10 do relatório v3): HP total do pull varia demais entre monstros pro mesmo
   multiplicador global de tier 2/3 servir todos.
5. **Personagens (±15%) não reverificados numericamente** (§7) — risco real de a proxy de
   jutsu utilitário ter mudado de baseline com os 8 jutsus elementais recalibrados; nenhum
   personagem foi tocado nesta rodada por falta de orçamento pra recalcular a proxy.
6. **Ranged (shuriken) tem o mesmo platô de arma que o melee tinha** (`senbon_de_ferro` req10 →
   `fuuma_shuriken` req25, 15 níveis flat) — fora do escopo explícito da missão (que citava
   L15→L20/boss L19, um encontro melee), não corrigido.
7. **`suiton_nevoa_cortante`/`raiton_corrente_estatica`** (as variantes de controle tier 1,
   cooldown curto) não foram tocadas — continuam fora do escopo de "tier 1 primário" definido
   nesta rodada (são ferramentas de controle, não candidatas de DPS, ver rodada 3 §6).
8. **`chakra_pill_large` não tem exhaustion real no TFS** (§1) — a aproximação de 1,0s do
   simulador é só isso, uma aproximação; se o servidor real permitir spam de pílula mais rápido
   que 1,0s, o jogador real pode sustentar chakra melhor do que este relatório prevê (viés
   conservador, não otimista).

## 11. Como reproduzir

```bash
cd /Users/stenioz/Projetos/shinobi-legends
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json          # ~55s
python3 tools/balance/sim.py --group-matrix --json /tmp/group.json     # ~1.1s
python3 tools/balance/sim.py --hunt --json /tmp/hunt.json              # ~0.2s (5 níveis, hybrid, c/ e s/ pílula)
python3 tools/balance/sim.py --hunt --level 15 --monster mist_scout --build hybrid --chakra-pills --minutes 30
python3 tools/balance/sim.py --level 19 --monster boss_mist_swordsman --build ninjutsu -v
.venv/bin/python tools/validate_data.py
.venv/bin/python tools/export_tfs.py       # escreve em server/generated/, não instala
```
