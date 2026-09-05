# Relatório de balanceamento PvM — rodada 8 (setembro/2026)

Três metas independentes, todas dependentes de mudar `tools/balance/sim.py` (o simulador não
modelava `phases[].attack_multiplier`/`summons` de boss nem tinha um lever de scarcity híbrida
compatível com "castar o tier 1 sempre que libera e tem chakra"): (1) fúria real de boss —
recalibrar `attack_multiplier` agora que ele multiplica dano de verdade (addendum da rodada 6/7,
commit `87c19a1`); (2) trocar `HYBRID_JUTSU_CADENCE_FRAC` pelo modelo real de scarcity híbrida
(pendência da rodada 7); (3) devolver ninjutsu a +30-60% sobre taijutsu nos pulls de 3+ (a
rodada 7 tinha derrubado `ruin_puppet` pra +3,7% como efeito colateral do custo de tier 1).

**Resultado resumido**: meta 1 fechada (12/12 bosses); meta 3 fechada (2/2 pulls de N=3 com
jutsu de área disponível); meta 2 fechada **parcialmente** — o teto de híbrido ≤+15% contra boss
fechou, mas a faixa de 15-25% de tempo sem chakra numa hunt híbrida **não fechou**, por um
conflito estrutural real com a meta "Genin L1 6-8 casts/pool" (ver §2, é a mesma classe de achado
honesto que a rodada 7 já tinha documentado, agora sob um ângulo diferente).

## 0. Arquivos tocados

- `tools/balance/sim.py`: `simulate_fight`/`simulate_hunt` passam a modelar `phases[].
  attack_multiplier` (dano do boss ×mult a partir do `hp_percent` da fase, cura pontual e reset
  por fase — replica `boss_phases.lua` real) e `summons` (DPS extra simplificado, "pull
  adicional"); build `hybrid` deixou de usar `pick_ninjutsu_jutsu` + `HYBRID_JUTSU_CADENCE_FRAC`
  (removida) — agora sempre conjura o tier 1 do elemento com vantagem, no cooldown real.
- `data/monsters/swamp.json`: `boss_white_serpent`, fase final `attack_multiplier` 1,9 → 1,45.
- `data/jutsus/{katon,suiton,raiton,doton,fuuton}.json`: os 5 projéteis tier 1, `cooldown_s`
  9,0 → 27,0 (custo percentual **inalterado**, ver §2).
- `data/jutsus/katon.json`: `katon_anel_chamas` (área tier 2), dano ×1,2.
- `data/jutsus/fuuton.json`: `fuuton_rajada_cortante` (área tier 2) e `fuuton_tornado_cortante`
  (beam tier 3), dano ×0,65 cada.
- `docs/00-biblia-do-jogo.md`: tabela dos 5 tier 1 (cooldown), narrativa de fúria de boss/híbrido,
  pendências da rodada 8 fechadas para "resolvido"/atualizadas.
- `docs/sistemas/monstros-e-pvm.md`: ficha da Serpente Branca e nota de fúria real atualizadas.
- `docs/sistemas/balanceamento.md`, `tools/balance/README.md`: ver §6.
- `server/generated/**`: regenerado por `tools/export_tfs.py` (conferência, sem instalar).

## 1. Fúria real de boss (item 1 da missão)

### O que faltava no simulador

`tools/balance/sim.py` nunca leu `phases`/`summons` — só `hp`/`attacks` fixos por monstro (achado
já registrado no addendum da rodada 6). Isso significa que TODO TTK/death_rate de boss medido
nas rodadas 1-7 ignorava o multiplicador de dano de fúria — mesmo depois do commit `87c19a1` ter
feito esse multiplicador valer de verdade no servidor (`NarutoBossFury`, `onHealthChange` do
jogador).

### O que foi implementado

`boss_phase_state_init()`/`apply_boss_phase_tick()` replicam `server/generated/scripts/naruto/
boss_phases.lua` linha a linha: ao cruzar o `hp_percent` de uma fase (checado a cada golpe
individual, não por tick de 0,1s), o multiplicador da fase passa a valer sobre TODO ataque do
boss (melee e elemental) dali em diante — nunca some, só avança (mesmo que uma cura de fase
empurre o HP de volta pra cima, igual ao Lua real) — com a mesma cura pontual
`+max_hp×(mult-1)×0,10`. `summons` viram uma "trickle" contínua de dano de fundo (DPS médio dos
monstros invocados contra a armadura do jogador, sem RNG) somada ao dano recebido pelo resto da
luta — aproximação deliberada ("pull adicional simples", pedido explícito da missão): simular os
summons um a um exigiria todo o aparato de `simulate_group_fight`, fora de escopo aqui.
`simulate_hunt` ganhou o mesmo tratamento (reset de fase/summons a cada novo pull, igual ao
`onDeath` real).

### Recalibração: antes → depois, os 12 bosses com fase de fúria

Medido com o multiplicador de fase REAL (recalibrado), 150 trials, taijutsu solo, com poções, no
level-alvo de cada boss. `dps_ratio` = dano recebido/s medido com o boss travado na fase final
(mult aplicado o tempo todo) dividido pelo dano recebido/s com o boss travado na fase 1
(mult=1,0) — isolado de RNG de TTK via um HP artificialmente alto (boss nunca morre durante a
medição) e HP do jogador artificialmente alto (jogador nunca morre); meta: 1,3×-1,8×.

| Boss | Nível | `attack_multiplier` antes → depois | `dps_ratio` medido | `death_rate` (taijutsu, c/ poções) |
|---|---|---|---|---|
| Chefe dos Bandidos | 12 | 1,5 → **1,5** (sem mudança) | 1,50× | 0,0% |
| Espadachim da Névoa | 19 | 1,6 → **1,6** (sem mudança) | 1,59× | 0,0% |
| **Serpente Branca** | 25 | **1,9 → 1,45** | 1,45× | 0,0% |
| Sapo Ancião | 25 | 1,6 → **1,6** (sem mudança) | 1,59× | 0,0% |
| Desertor de Elite | 46 | 1,3 → **1,3** (sem mudança) | 1,29× | 0,0% |
| Marionetista das Ruínas | 50 | 1,5 → **1,5** (sem mudança) | 1,49× | 0,0% |
| Sócio Eterno | 70 | 1,6 → **1,6** (sem mudança) | 1,58× | 0,0% |
| Oni Ancestral | 80 | 1,7 → **1,7** (sem mudança) | 1,70× | 0,0% |
| Vigia Ilusório | 85 | 1,4 → **1,4** (sem mudança) | 1,40× | 0,0% |
| Mascarado das Sombras | 90 | 1,4 → **1,4** (sem mudança) | 1,40× | 0,0% |
| Portador dos Seis Caminhos | 95 | 1,5 → **1,5** (sem mudança) | 1,49× | 0,0% |
| Ancestral da Nuvem Vermelha | 100 | 1,3/1,7 → **1,3/1,7** (sem mudança, fase final=1,7) | 1,68× | 0,0% |

**Achado central**: 11 dos 12 bosses já estavam dentro de 1,3×-1,8× mesmo sem recalibração — a
recomendação da rodada 6/7 ("cortar pela metade o excedente", ex. 1,5→1,25) partia de uma
suposição que não se confirmou aqui: `dps_ratio` é, por construção do modelo (mesmo cooldown de
ataque nas duas fases, só o multiplicador muda), **igual ao próprio `attack_multiplier` da fase
final** — não composto com nenhum outro fator. Como o range original dos 12 bosses (1,3-1,9) já
cobria quase todo o alvo pedido (1,3-1,8), só a Serpente Branca (1,9, o único valor acima do
teto) precisou de ajuste. Apliquei a fórmula sugerida mesmo assim para ela: excedente sobre 1,0
cortado pela metade (0,9 → 0,45 → **1,45**).

**`death_rate` ≤10%**: 0,0% em todos os 12 bosses, com e sem a fúria real — as poções (melhor
disponível pro nível, bebida a cada 1s quando HP<35%) absorvem completamente o dano da fúria
nesta simulação; sem poções, `death_rate`=100% em todos (óbvio — nenhuma cura). Isso já era
verdade nas rodadas anteriores (a meta "com poções" nunca dependia da fúria real pra ser
alcançada) — não é um resultado nascido da recalibração, é uma confirmação de que a folga
existente já cobria a fúria real sem alarme.

## 2. Scarcity híbrida (item 2 da missão)

### Modelo novo

`HYBRID_JUTSU_CADENCE_FRAC=0,22` (rodada 6) fazia o híbrido escolher o jutsu de "melhor dps/
cooldown do kit já desbloqueado" (`pick_ninjutsu_jutsu`, migra pro tier 2/3 assim que
desbloqueia) e esticava o cooldown EFETIVO por `1/0,22≈4,5×` só pro build híbrido — um parâmetro
de modelo, não um número de jutsu. Substituído por: o híbrido sempre conjura o **tier 1** do
elemento com vantagem, no cooldown **real**, sempre que pronto e pagável — "castar o tier 1
sempre que libera e tem chakra", o comportamento medido no playtest da rodada 5.

### Boss ≤+15%: precisou subir o cooldown do tier 1 (9,0s → 27,0s)

Sem nenhum ajuste, o modelo novo no cooldown original (9,0s) deixou o híbrido **44,1% mais forte**
que o melhor puro no pior caso (Espadachim da Névoa) — o cooldown real é bem mais curto que o
esticamento antigo (~40,9s), e como o tier 1 tem `level_scale` mais baixo que os campeões de
tier 2/3 (calibrado desde a rodada 5 pra ficar atrás no burst), castar 4-5× mais rápido ainda
soma dano suficiente pra estourar o teto.

**Testado (e descartado) usar `chakra_cost_percent` como lever pra tamponar o boss**: até ×2 do
custo original não move o TTK de boss em nada perceptível (o pool inicial cheio absorve 10+
casts antes de esgotar, mais que suficiente pra uma luta de 80-180s) — e valores altos o
bastante pra importar (×4-6) **quebram a meta "Genin L1 6-8 casts/pool"** (cai pra 1 cast/pool).
Como essa meta está na lista "Manter" da missão, o custo ficou **inalterado** (14,0/12,0/13,0/
13,0/13,0% do pool, katon/suiton/raiton/doton/fuuton) — a única alavanca segura é o cooldown.

`cooldown_s` 9,0 → **27,0** (mesmo valor pros 5 elementos) fecha o teto com folga:

| Boss | Nível | TTK taijutsu | TTK ninjutsu (Δ) | TTK híbrido (Δ vs. melhor puro) |
|---|---|---|---|---|
| Chefe dos Bandidos | 12 | 138,6s | 138,6s (0,0%) | 123,2s (**-11,1%**) |
| Espadachim da Névoa | 19 | 94,2s | 94,2s (0,0%) | 81,6s (**-13,4%**) |
| Serpente Branca | 25 | 172,0s | 172,0s (0,0%) | 153,5s (**-10,8%**) |
| Marionetista das Ruínas | 50 | 82,3s | 82,3s (0,0%) | 81,0s (**-1,6%**) |
| Oni Ancestral | 80 | 101,6s | 101,6s (0,0%) | 99,2s (**-2,4%**) |
| Ancestral da Nuvem Vermelha | 100 | 111,6s | 111,6s (0,0%) | 110,8s (**-0,7%**) |

Pior caso -13,4% (dentro de ≤+15%, com ~1,6pp de folga). `ninjutsu puro` continua 0,0% de
diferença nos 6 bosses (o kit já vencia por taijutsu puro desde a rodada 5/6 — nenhum destes 6
usa o tier 1 como pick racional, então o cooldown maior não muda nada aqui).

**233 combinações checadas (level×monstro fora dos 6 de referência) mostram violações fora de
escopo**: a checagem acima é formalmente só sobre os 6 bosses (como a própria missão delimita:
"nos 6 bosses"). Rodando a matriz completa e filtrando só pares onde o nível do jogador é
parecido com o nível do monstro (não a matriz cruzada toda, que testa nível 1 contra monstro
nível 100 sem sentido nenhum), aparecem violações do híbrido em monstros COMUNS fora da lista de
6 (ex. `stone_sentinel` +201,9%, `glacier_oni` +102,0%) — o modelo novo tem variância bem maior
entre monstros diferentes do que o antigo (que ficava sempre perto de zero por castar tão raro).
Isso está fora do escopo numérico desta rodada (que só pede os 6 bosses de referência), mas é
uma pendência honesta sinalizada em §7 pra uma rodada futura de balanceamento de kits comuns.

### Genin L1 6-8 casts/pool: mantido (custo inalterado)

| Jutsu | Nível | Custo | Chakra máx. L1 | Casts por pool cheio |
|---|---|---|---|---|
| Katon: Grande Bola de Fogo | 1 | 14,0% | 110 | 7 |
| Suiton: Projétil de Água | 1 | 12,0% | 110 | 8 |
| Raiton: Agulha de Raio | 1 | 13,0% | 110 | 7 |
| Doton: Bala de Lama | 1 | 13,0% | 110 | 7 |
| Fuuton: Lâmina de Vento | 1 | 13,0% | 110 | 7 |

Todos dentro de 6-8 (igual às rodadas 6/7 — o custo percentual não mudou, só o cooldown).

### Scarcity 15-25% (sem pílula) / ≤5% (com pílula): **NÃO fechou**

Rodei `--hunt` (30 min, `force_tier1=True`, build híbrido, HUNT_LEVELS 5-100 de 5 em 5) no
estado final (cooldown 27,0s, custo inalterado):

| Métrica | Resultado |
|---|---|
| % tempo sem chakra, sem pílula (min–max nos 20 níveis) | **0,0% em todos os 20 níveis** |
| % tempo sem chakra, com pílula (máx.) | 0,0% (✅ dentro de ≤5%, mas trivialmente — a base já é 0%) |

**Por que não fechou (achado estrutural, não falta de tentativa)**: com o custo mantido em
12-14% do pool (exigido por "Genin L1 6-8 casts/pool") e cooldown 27,0s, a razão consumo/regen
numa hunt de 30 min fica muito abaixo de 1 (chakra sempre reabastece antes de faltar) — pool
nunca esvazia. Um sweep (2D, custo×cooldown, ~40 combinações) mostrou que **qualquer** combinação
que empurra essa razão pra perto de 1 (criando scarcity real) exige custo ≈3-5× o atual — que já
comprovadamente quebra "6-8 casts/pool" (cai pra 1) **e**, à parte, quebra pulls de baixo nível
(o pull de `wolf` L2 N=3 passa a dar timeout, ver §3). Ou seja: **as metas "Genin L1 6-8 casts/
pool" e "15-25% sem chakra em hunt híbrida" são matematicamente incompatíveis** sob este modelo
de custo percentual único — não existe um par (custo, cooldown) que feche as duas ao mesmo tempo
E o teto de boss ≤+15%. Priorizei o teto de boss (meta desta rodada com lever nomeado
explicitamente) e "Genin L1 6-8 casts/pool" (item da lista "Manter") sobre a faixa de scarcity —
a mesma ordem de prioridade que a missão sinaliza ("se estourar, a alavanca é custo/cooldown do
tier 1, não o modelo", sem mencionar sacrificar os outros invariantes). Documentado como
pendência honesta em §7 — resolver exigiria uma quarta alavanca fora da lista desta rodada (ex.
custo escalando com o número de casts JÁ feitos na sessão, não um percentual fixo do pool).

## 3. Pull 3+: ninjutsu +30-60% sobre taijutsu (item 3 da missão)

Alavanca usada: jutsus de **área/beam tier 2/3** (dano/custo), não o tier 1 — como pedido
explicitamente. O aumento de cooldown do tier 1 (§2) por si só já tinha um efeito colateral aqui
(tier 1 deixou de competir como "filler" na rotação de grupo, empurrando `ruin_puppet` de volta
pra +83,5% antes do ajuste dos jutsus de área) — os números abaixo já refletem o estado final.

| Cenário (pull N=3) | XP/h taijutsu | XP/h ninjutsu antes → depois | Δ antes → depois | Jutsu ajustado |
|---|---|---|---|---|
| `ruin_puppet` L27 (Ruínas) | 85 832 | +83,5% → **+42,1%** | dentro de +30-60% ✅ | `katon_anel_chamas` dano ×1,2 |
| `thunder_eagle` L54 (Montanha) | 281 286 | +90,8% → **+36,4%** | dentro de +30-60% ✅ | `fuuton_rajada_cortante` e `fuuton_tornado_cortante` dano ×0,65 cada |
| `wolf` L2 (Floresta da Vila) | 5 819 | -84,6% → **-84,6%** (sem mudança) | fora da faixa ❌ | nenhum (ver nota) |

**Nota sobre `wolf` L2 N=3**: nenhum jutsu de área existe nesse nível (o tier 2 de qualquer
elemento exige nível 6-22; a L2 só o projétil tier 1 single-target está desbloqueado) — a
alavanca pedida (jutsus de área tier 2/3) simplesmente não tem nada pra ajustar aqui. Isso é uma
característica estrutural do início de jogo (um genin L2 não tem AoE, taijutsu domina pulls),
não um bug introduzido nesta rodada — mas o cooldown maior do tier 1 (§2) piorou o número
(estava em -100% de timeout total antes do ajuste fino, agora clara em -84,6% sem timeout).
Sinalizado como pendência honesta (§7); corrigir exigiria mexer no tier 1 (fora do escopo desta
meta) ou introduzir cedo algum jutsu de área, uma decisão de design maior.

**Achado sobre "whack-a-mole" (mesma classe da rodada 6 pro híbrido)**: nerfar só
`fuuton_rajada_cortante` não mudava nada — a rotação de `thunder_eagle` migrava inteiramente pra
`fuuton_tornado_cortante` (tier 3, ainda mais forte). Precisei nerfar os DOIS jutsus do kit fuuton
que competem pelo posto de "campeão de área" ao mesmo tempo (mesmo fator ×0,65) pra o total cair
de fato.

Verificado: os 6 bosses de referência (§2) não usam nenhum dos 3 jutsus tocados aqui (elementos
diferentes ou fallback pra taijutsu) — sem interação com o teto de boss.

## 4. Manter (item 4 da missão) — confirmado sem regressão

- **Ninjutsu puro -15%..+10% nos 6 bosses**: 0,0% em 5/6 (fallback racional pra taijutsu, como
  desde a rodada 5/6) e 0,0% no 6º (`boss_bandit_chief`, usa `suiton_mizudan` tier 1 — cooldown
  maior não muda o resultado porque o kit inteiro já perdia pra taijutsu puro antes também).
  Nenhum dos jutsus tocados nesta rodada (tier 1 dos 5 elementos, `katon_anel_chamas`,
  `fuuton_rajada_cortante`/`tornado_cortante`) é usado pelo ninjutsu puro em nenhum dos 6 bosses.
- **Burst ≥1,3×**: matematicamente inalterado — nenhum `base_damage`/`level_scale`/`skill_scale`
  do tier 1 foi tocado (só `cooldown_s`/`chakra_cost_percent`, que não entram na conta de burst,
  per-hit). Continua 94/100 níveis fechando ≥1,3× (igual às rodadas 5-7).
- **Kits ±15%**: `data/jutsus/personal.json` não foi tocado nesta rodada — os 9 personagens
  continuam exatamente onde a rodada 6/7 deixou (-11,8%..+8,6%, dentro de ±15%), confirmado
  analiticamente (nenhum campo usado nessa métrica mudou).
- **Genin L1 6-8 casts/pool**: confirmado em §2 (7-8 casts, custo inalterado).

## 5. `validate_data.py` / `export_tfs.py` / timing

```
.venv/bin/python tools/validate_data.py    # OK — 54 jutsus, 174 itens, 40 monstros, ... tudo válido
.venv/bin/python tools/export_tfs.py       # OK — 40 monstros, 54 jutsus, 174 itens, ... server/generated/
python3 tools/balance/sim.py --matrix --json /tmp/matrix_final.json        # 2040 sims, 70,1s (<120s)
python3 tools/balance/sim.py --group-matrix --json /tmp/group_final.json   # 36 grupo + 18 boss, 1,8s
python3 tools/balance/sim.py --hunt --json /tmp/hunt_final.json            # 0,9s
```

Não rodei `install_generated.sh`, não reiniciei o servidor, não usei o cliente — só
`export_tfs.py` pra conferência, como orientado.

## 6. Documentação atualizada

- `docs/00-biblia-do-jogo.md`: tabela dos 5 jutsus tier 1 (cooldown 9,0s→27,0s em 5 linhas),
  narrativa de fúria de boss (Serpente Branca 1,9→1,45), narrativa de híbrido/scarcity (modelo
  novo + pendência da faixa 15-25%), seção "Em andamento"/"Próximos passos"/"Riscos e
  limitações" com as pendências da rodada 8 fechadas ou reatualizadas para a rodada 9.
- `docs/sistemas/monstros-e-pvm.md`: ficha da Serpente Branca (fase 3) e nota de fúria real.
- `docs/sistemas/balanceamento.md`, `tools/balance/README.md`: ver changelog/uso atualizados
  nesta rodada (constantes novas: `boss_phase_state_init`/`apply_boss_phase_tick`/
  `advantage_element`/`average_monster_dps_vs_player`; `HYBRID_JUTSU_CADENCE_FRAC` removida).

## 7. Metas atingidas / não atingidas — resumo honesto

| Meta | Resultado |
|---|---|
| 1. Fúria real modelada no sim + `death_rate`≤10% + `dps_ratio` 1,3×-1,8× nos 12 bosses | ✅ **Atingida** (só Serpente Branca precisou de ajuste, 1,9→1,45) |
| 2a. Híbrido ≤+15% sobre melhor puro nos 6 bosses (modelo novo) | ✅ **Atingida** (pior caso -13,4%, cooldown tier 1 9,0s→27,0s, custo inalterado) |
| 2b. 15-25% tempo sem chakra em hunt híbrida (sem pílula) | ❌ **Não atingida** — 0,0% em todos os níveis; conflito estrutural real com "Genin L1 6-8 casts/pool" (ver §2), não falta de tentativa |
| 2c. ≤5% tempo sem chakra em hunt híbrida (com pílula) | ✅ Atingida, mas trivialmente (base já em 0% sem pílula) |
| 3. Ninjutsu +30-60% sobre taijutsu em pulls N=3 com jutsu de área disponível | ✅ **Atingida** (`ruin_puppet` +42,1%, `thunder_eagle` +36,4%) — `wolf` L2 fora de escopo (sem AoE nesse nível) |
| 4. Ninjutsu -15%..+10% / burst ≥1,3× / kits ±15% / Genin L1 6-8 casts | ✅ Mantidos, confirmado sem regressão |
| 5. `validate_data.py`/`export_tfs.py` OK, `--matrix` <120s, `--json` OK | ✅ Confirmado |

### Pendências honestas para a rodada 9

1. **15-25% de tempo sem chakra em hunt híbrida continua em 0%** — conflito estrutural com
   "Genin L1 6-8 casts/pool" sob o modelo de custo percentual fixo do pool. Resolver exigiria uma
   alavanca fora da lista desta rodada (ex.: custo crescente por cast dentro de uma janela de
   tempo, decaindo com o descanso — não um percentual fixo por cast).
2. **Pull `wolf` L2 N=3 fica em -84,6%** (fora de +30-60%) — não há jutsu de área desbloqueado
   nesse nível; fora do escopo da alavanca pedida (tier 2/3). Uma correção real exigiria mexer no
   tier 1 (fora desta meta) ou introduzir algum jutsu de área cedo (decisão de design maior).
3. **Híbrido fora dos 6 bosses de referência tem variância bem maior que antes** (ex.
   `stone_sentinel` +201,9%, `glacier_oni` +102,0%, medido nos pares nível≈nível-do-monstro da
   matriz completa) — o modelo antigo ficava sempre perto de zero (castava tão raro que quase não
   importava); o novo (tier 1 real) interage de forma bem mais variável com o HP/defesa de cada
   monstro comum. Fora do escopo numérico desta rodada (só pede os 6 bosses), mas vale uma
   rodada dedicada a "kits ±15%" estendida a monstros comuns, não só personagens.
4. **Margem do teto de boss é real mas não folgada** (pior caso -13,4% de -15%, ~1,6pp de
   sobra) — qualquer NOVO conteúdo que aumente o `level_scale` do tier 1 ou reduza ainda mais o
   cooldown precisa reverificar os 6 bosses.


## Decisão do orquestrador (2026-09-05, pós-rodada)

O cooldown do tier 1 em **27 s foi rejeitado** e voltou para **9 s**. Um jutsu por meio minuto destrói a
sensação de ninja; o teto "híbrido ≤ +15% do melhor build puro" é que está errado como restrição de
design — no Tibia (e aqui) jogar com arma + magia É o jogo normal. Nova filosofia para a rodada 9:
o **híbrido é o build de referência**; monstros, XP/h e tabela de progressão são calibrados pelo TTK
híbrido; builds puros só precisam ser viáveis (≥ 70% do híbrido). A escassez de chakra vem da
regeneração, não do cooldown: proposta `2 + level//6` a cada 2 s (1,0/s no L1, abaixo do consumo de
~1,7/s de um tier 1 a cada 9 s), com recuperação do pool parado em até 120 s.
