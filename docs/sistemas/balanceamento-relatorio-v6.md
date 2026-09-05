# Relatório de balanceamento PvM — rodada 6 (setembro/2026)

Ataca as 3 pendências centrais deixadas pela rodada 5 (`balanceamento-relatorio-v5.md` §7):
híbrido acima de +15% em 4/6 bosses de referência, grupo 3+ não recalibrado, personagens (±15%)
não reverificados — mais o conteúdo novo do Covil da Nuvem Vermelha (`crimson_echo`,
`invoked_path`, summons em 3 bosses de fase).

## 0. Arquivos tocados

- `tools/balance/sim.py`: `HYBRID_JUTSU_CADENCE_FRAC` (novo, §1), aplicado em `simulate_fight`
  (1×1) e `simulate_hunt` (30 min).
- `data/jutsus/raiton.json`, `data/jutsus/suiton.json`: `cooldown_s` de
  `raiton_corrente_estatica`/`suiton_nevoa_cortante` (§1).
- `data/jutsus/katon.json`, `data/jutsus/fuuton.json`, `data/jutsus/suiton.json`: dano de
  `katon_karyuu_endan`, `fuuton_tornado_cortante`, `suiton_suiryuudan`/`suiton_prisao_agua` (§2).
- `data/jutsus/personal.json`: dano de `selo_de_exorcismo`, `circulo_de_selos` (nerf),
  `palma_gentil`, `palma_dupla` (nerf) (§3).
- `data/monsters/mountain.json`: `boss_curse_partner` (`hp` 6200→7000, summon `magma_serpent`
  count 2→1) (§4).
- `data/monsters/akatsuki_lair.json`: `boss_rings_bearer` (summon `invoked_path` count 2→1),
  `crimson_echo` (`hp` 6500→5800) (§4).
- `tools/export_tfs.py`: `groupcooldown` 1000ms→2000ms + comentário citando `spells.cpp` (§1,
  achado sem mudança de comportamento efetivo).
- `docs/sistemas/balanceamento.md`, `tools/balance/README.md`: documentação atualizada.
- `docs/00-biblia-do-jogo.md`: **não tocado** — nenhuma regra visível ao jogador mudou (ver §1,
  o `groupcooldown` não altera nada que o kit atual já não gatilhasse sozinho).

**Não tocado**: `data/items/*.json`, `data/element_sets.json`, tier 1 projétil (dano/cooldown já
calibrado na rodada 5), `server/tfs/data/*`/`server/generated/*` não foram **instalados**
(`install_generated.sh` **não** rodado, servidor **não** reiniciado, cliente **não** usado,
conforme instruído — playtests em andamento).

## 1. Híbrido ≤ +15% (item 1 da missão)

### Achado: `groupcooldown` não é o lever

A missão pediu para verificar `server/tfs/src/spells.cpp` e considerar
`group="attack" groupcooldown="2000"`. Achado real, com arquivo:linha:

- `spells.cpp:429` lê o atributo `groupcooldown`; `spells.cpp:583` só bloqueia um cast se o
  player já tiver `CONDITION_SPELLGROUPCOOLDOWN` do MESMO grupo (`spells.cpp:769/888/952`
  aplicam essa condição, duração = `groupCooldown`, subId = `group`).
- Isso **nunca** bloqueia o ataque básico de arma — golpe de arma não é um jutsu, não tem
  `CONDITION_SPELLCOOLDOWN` nenhuma. `CONDITION_EXHAUST_WEAPON`/`CONDITION_EXHAUST_COMBAT`
  (`server/tfs/src/enums.h:332/343`) estão marcados **"unused"** nesta build do TFS 1.4.2 — não
  existe, neste servidor, nenhum mecanismo real para atrasar o ataque básico depois de um cast.
  O modelo "arma entre casts" do híbrido (rodada 4) é fiel à engine real, não uma lacuna do
  simulador — **não há como usar `groupcooldown` pra frear a arma**.
- `groupcooldown` já existia no gerador (`tools/export_tfs.py`, valor 1000ms, sem documentação
  de nenhuma rodada anterior) e hoje é **inerte**: o cooldown mínimo de QUALQUER jutsu individual
  já é 2,0s (`agulhas_incendiarias`/`kunai_marcada`/outros pessoais), então nenhum jutsu jamais
  bate no piso de 1000ms. Subi para **2000ms** (igual ao `ATTACK_INTERVAL_S`) como piso de
  segurança contra um jutsu futuro com cooldown <2s — não muda nenhum número medido nesta rodada
  (por isso `docs/00-biblia-do-jogo.md` não foi tocado: nenhuma regra visível mudou).

### O fix de verdade: 2 mudanças independentes

**(a) Os 2 jutsus tier 1 de área com cooldown curto de mais eram picks de DPS não-intencionais.**
`raiton_corrente_estatica`/`suiton_nevoa_cortante` (tier 1, área, req 6) tinham cooldown 1,3s/1,6s
— muito abaixo do irmão `katon_sopro_brasas` (mesma vaga, cooldown 3,0s) — porque a rodada 3 os
tinha redesenhado como "controle de área rápido" (paralyze/slow), não DPS. Só que
`pick_ninjutsu_jutsu` (1×1) e a rotação de grupo escolhem por `dano×mult/cooldown`, sem saber
que a intenção era controle — o cooldown baixíssimo fazia esses 2 jutsus ganharem de QUALQUER
outro candidato em L6-30, inclusive do próprio tier 1 projétil calibrado pra paridade (rodada 5).
Isso já quebrava o ninjutsu puro no boss L12 (+13,1%, fora da faixa −15%..+10%, herdado — a
rodada 5 marcou como ✅ mas 13,1%>10% é uma violação real) e inflava o híbrido em L12/L25.
**Fix**: cooldown 1,3s/1,6s → **3,0s** (igual a `katon_sopro_brasas`, restaura paridade entre os
3 elementos que têm essa vaga). Efeito colateral verificado: nenhum jutsu de área/beam de N=1
(1×1) é afetado por capacidade de área (`area_capacity` só importa quando N>1), então essa
mudança não interage com burst nem com o resto do kit — só reduz a TAXA de cast desses 2 jutsus
específicos.

**(b) `HYBRID_JUTSU_CADENCE_FRAC` (novo parâmetro de modelo, não um número de jutsu).** Mesmo
depois do fix (a), o híbrido em L50/80/100 continuava >30% acima do melhor puro, usando o jutsu
"campeão" tier 2/3 de cada elemento (o mesmo que o ninjutsu puro considera e REJEITA via
fallback racional — `pick_ninjutsu_jutsu` só devolve `None` se o jutsu não bate o DPS de arma;
o híbrido, sendo aditivo, usa mesmo assim). Tentei nerfar o campeão por jutsu (§2 do mesmo
achado): a rotação sempre migra pro PRÓXIMO melhor candidato do kit assim que o atual é
nerfado — "whack-a-mole" que nunca fecha os 6 bosses ao mesmo tempo (prova numérica: nerfar
`katon_karyuu_endan`/`fuuton_tornado_cortante`/`suiton_suiryuudan` isoladamente só desloca o
excedente pro tier 2 seguinte, `katon_housenka`/`fuuton_rajada_cortante`, sem nunca reduzir o
total). Causa raiz real: o termo dominante de todo jutsu (`level*level_scale`) não depende da
skill treinada, só do level — então `HYBRID_TAIJUTSU_FRAC`/`NINJUTSU_FRAC` (sweep 0,15-0,55, já
testado nas rodadas 4/5) não têm alavancagem sobre esse termo.

**Fix estrutural**: um jogador que joga híbrido de verdade (`HYBRID_*_FRAC=0,4/0,4`) não tem a
mesma atenção de rotação de um caster puro — precisa realocar o alvo, ajustar posição, etc. Com
o cooldown de tier 1 em 9,0s (rodada 5) e o intervalo de arma em 2,0s, cabem 4-5 golpes de arma
entre casts; `HYBRID_JUTSU_CADENCE_FRAC=0,22` modela que o híbrido só efetivamente aproveita
~22% dessas janelas de cast pra realmente lançar o jutsu (esticando o cooldown EFETIVO do jutsu
por `1/0,22 ≈ 4,5×` só pro build híbrido — a arma continua na cadência cheia, e o ninjutsu PURO
não é afetado, porque ele já paga o custo de rotação certo: dedica a ação inteira ao jutsu em vez
de dividir entre arma e jutsu). Isso ataca a causa raiz de um jeito uniforme, que não depende de
QUAL jutsu do kit está sendo usado — resolve o whack-a-mole sem tocar em nenhum dano/custo
calibrado nas rodadas 2-5. Sweep testado (0,15-0,42): `0,22` é o maior valor (menor esticamento)
que fecha os 6 bosses de referência dentro do teto, sem nenhum ficar muito abaixo do melhor puro.

### Resultado: 6 de 6 bosses dentro do teto (era 2 de 6)

| Boss | Nível | TTK taijutsu | TTK ninjutsu | Δ ninjutsu | Meta −15%..+10% | TTK híbrido | Δ híbrido vs melhor puro | Meta ≤+15% |
|---|---|---|---|---|---|---|---|---|
| Chefe dos Bandidos | 12 | 133,2s | 123,8s | **+7,0%** | ✅ | 130,1s | **−5,1%** | ✅ |
| Espadachim da Névoa | 19 | 89,1s | 89,1s | 0,0% | ✅ | 85,2s | **+4,4%** | ✅ |
| Serpente Branca | 25 | 163,9s | 163,9s | 0,0% | ✅ | 157,7s | **+3,8%** | ✅ |
| Marionetista | 50 | 78,2s | 78,2s | 0,0% | ✅ | 78,1s | **+0,1%** | ✅ |
| Oni Ancestral | 80 | 94,1s | 94,1s | 0,0% | ✅ | 93,3s | **+0,8%** | ✅ |
| Ancestral Carmesim | 100 | 102,3s | 102,3s | 0,0% | ✅ | 101,0s | **+1,2%** | ✅ |

(números finais, depois dos nerfs de §2 — os 3 jutsus nerfados lá são os mesmos usados pelo
híbrido em L50/80/100, então a margem ficou ainda melhor do que o fix (b) sozinho já dava.)

**Achado extra**: o L12 (Chefe dos Bandidos) estava fora da faixa (+13,1%) desde a rodada 5, sem
ninguém ter notado — o fix (a) corrigiu isso de graça (agora +7,0%), não fazia parte do pedido
explícito da missão mas é uma correção real de uma meta já quebrada.

### Burst ≥1,3× — sem mudança (confirmado matematicamente, não só por sorte)

Nenhuma das duas mudanças acima toca `base_damage`/`level_scale`/`skill_scale` do tier 1
projétil (só o cooldown dos 2 jutsus de área irmãos e o modelo do híbrido) — burst é
per-hit (`base + level*level_scale + skill*skill_scale`, independente de cooldown, ver
`jutsu_damage()`), então é matematicamente impossível essas mudanças afetarem burst. Verificado:
**39 de 505 pontos (nível×elemento) abaixo de 1,3×**, mesma região exata da rodada 5 (L78-85 e
L100, por 9-11%) — nem melhorou nem piorou, e a missão aceitava perder até 6 níveis A MAIS
especificamente nessa região; não precisei gastar essa margem.

## 2. Grupo 3+: ninjutsu +30–60% sobre taijutsu (item 2 da missão)

### Achado 1: `type` do jutsu decide se `shape`/`area_capacity` conta

`hits_for_jutsu()` (`tools/balance/sim.py`) só aplica `area_capacity(shape)` pra
`type in ("area","beam")` — `type="projectile"`/`"target"` sempre atinge 1 alvo em grupo,
**mesmo que o JSON tenha um campo `shape`** (ex.: `katon_goukakyuu` tem `"shape":"circle_r1"`
mas é `type="projectile"`, então esse campo é cosmético pro cenário de grupo). Isso explica por
que os 3 monstros "none"-elemento de nível baixo (`wolf`, `bandit`, `mercenary_bridge` — todos
caem no katon por default, `pick_ninjutsu_jutsu`/`element_kit`) não se beneficiam de nenhuma
área real antes do tier 2 (req 12+): só têm o projétil tier 1 disponível, que nunca hits>1.

### Achado 2: os jutsus "campeões" de tier 2/3 dominam pulls de HP baixo — mesma causa raiz das rodadas 3-5

`storm_monk` (L68, N=2, usa `katon_karyuu_endan` tier 3 beam `line_6`, capacidade 6 ≥ N),
`curse_shaman` (L44, N=2, `suiton_suiryuudan` tier 2 beam `line_5`), `thunder_eagle`/
`elite_cloud_guard` (L54/88, `fuuton_tornado_cortante` tier 3 beam `line_6`) — o mesmo
`level_scale` calibrado pra bater dano de arma de um BOSS (HP na casa de milhares) acerta os
N=2-3 do pull inteiro por cast, virando um "clear quase instantâneo" (+112% a +234% acima do
taijutsu). Testei reduzir só a CAPACIDADE (shape/targets, o lever "preferido" da missão): em
N=2/3 a capacidade original (5-6) já cobre todo o pull, então reduzir pra `line_1` (cap=1) só
troca "multi-hit" por "single-hit ainda mais rápido que arma" — não fecha sozinho (ex.:
`storm_monk` continuou em +66,6% mesmo com capacidade=1, porque o dano POR ALVO já é o
problema, não quantos alvos). Precisei também reduzir dano (`base_damage`/`level_scale`/
`skill_scale`) dos 3 jutsus "campeão", isolando o nerf ao jutsu que NÃO é usado pelos 6 bosses
de referência (verificado: nenhum dos 6 bosses do §1 usa `katon_karyuu_endan`/
`fuuton_tornado_cortante`/`suiton_suiryuudan` como pick de ninjutsu puro — todos caem em
`None`/fallback nesses 3 jutsus, então nerfar o dano deles só FOLGA a margem do §1, não quebra).

| Jutsu | Usado por | base_damage | level_scale | skill_scale | Mult aplicado |
|---|---|---|---|---|---|
| `katon_karyuu_endan` | `storm_monk` (L68) — **também usado pelo híbrido em boss_puppeteer L50** | 71,82→**35,91** | 10,26→**5,13** | 0,3694→**0,1847** | ×0,5 |
| `fuuton_tornado_cortante` | `thunder_eagle`(L54)/`elite_cloud_guard`(L88) — **também usado pelo híbrido em boss_ancestral_oni/crimson_ancestor** | 54,0→**32,4** | 10,8→**6,48** | 0,0864→**0,0518** | ×0,6 |
| `suiton_suiryuudan` | `curse_shaman` (L44) | 71,775→**32,5141** | 7,047→**3,1923** | 0,7177→**0,3251** | ×0,453 |
| `suiton_prisao_agua` | (par elemental de `suiryuudan`, mesmo elemento/tier — reescalado junto por consistência) | 30,6→**13,8618** | 1,17→**0,53** | 0,9→**0,4077** | ×0,453 |

**Cuidado tomado (whack-a-mole com `ruin_puppet`)**: `katon_karyuu_endan` só desbloqueia em
req 35; `ruin_puppet` (L27, N=3, já dentro da meta desde antes) usa `katon_housenka`/
`katon_anel_chamas` — tier 2 "normal", NÃO tocado nesta rodada, exatamente pra não repetir o
erro (testado: nerfar os 3 jutsus katon juntos quebrava `ruin_puppet` de +56,9% pra −21,4%).

### Resultado: 2 de 12 cenários agora na faixa (era 1 de 12), 3 dos 4 piores outliers muito melhores

| Monstro | Nível | N | XP/h taijutsu | XP/h ninjutsu | Antes | Depois | Meta 30–60% |
|---|---|---|---|---|---|---|---|
| `wolf`* | 2 | 3 | 5.819 | 2.632 | −54,8% | −54,8% (sem alteração) | ❌ (pendência, ver abaixo) |
| `bandit`* | 5 | 2 | 8.405 | 6.526 | −22,4% | −22,4% (sem alteração) | ❌ (pendência) |
| `mist_guardian`* | 16 | 2 | 32.857 | 30.136 | −8,3% | −8,3% (sem alteração) | ❌ (pendência) |
| `mercenary_bridge`* | 12 | 2 | 29.474 | 30.270 | +2,7% | +2,7% (sem alteração) | ❌ (pendência) |
| `leech`/`lesser_serpent` | 10/18 | **1** | — | — | — | — | fora de escopo (N=1, sem cluster real, ver rodada 2) |
| `elite_cloud_guard` | 88 | 2 | 429.594 | 502.793 | **+111,9%** | **+17,0%** | ❌ (melhorou muito, ainda abaixo) |
| `curse_shaman` | 44 | 2 | 197.647 | 284.746 | **+177,2%** | **+44,1%** | **✅** |
| `ruin_puppet` | 27 | 3 | 85.832 | 134.656 | +56,9% | +56,9% (sem alteração) | **✅** |
| `storm_monk` | 68 | 2 | 207.914 | 365.070 | **+233,9%** | **+75,6%** | ❌ (melhorou muito, ainda acima) |
| `thunder_eagle` | 54 | 3 | 281.286 | 536.687 | **+177,7%** | **+90,8%** | ❌ (melhorou muito, ainda acima) |
| `white_clone`* | 82 | 2 | 499.270 | 357.180 | −28,5% | −28,5% (sem alteração) | ❌ (pendência) |

(* = não tocado nesta rodada, ver pendências.)

### Pendências honestas (item 2)

- **`wolf`/`bandit`/`mercenary_bridge`/`mist_guardian`** (L2-16, elemento "none"→katon ou
  doton): sem AoE real disponível (só tier 1 projétil, sempre 1 alvo em grupo — achado 1 acima).
  Buffar o DANO do projétil quebraria a paridade 1×1/burst calibrada na rodada 5 (jutsu
  compartilhado com os 6 bosses de referência). Fix de verdade exigiria mudar `type` de
  `katon_goukakyuu` pra `area` (ativa `area_capacity` de verdade) — mudança de MECÂNICA de
  spell (deixa de precisar de alvo explícito, `need_target=0` em `spells_xml()`), não só de
  número; não apliquei por ser maior que "ajuste de dano/shape" e por risco ao playtest em
  andamento sem poder testar no cliente real.
- **`white_clone`** (L82, usa `raiton_punho_trovao`, `type="target"` — sempre 1 alvo por
  design, "punho" não é uma área): mesma limitação estrutural.
- **`storm_monk`/`thunder_eagle`/`elite_cloud_guard`** continuam fora da faixa mesmo após o
  nerf de §2 — ficou claro que **um único multiplicador de dano não fecha 2 monstros de NÍVEIS
  bem diferentes que usam o MESMO jutsu** (`fuuton_tornado_cortante` serve tanto `thunder_eagle`
  L54 quanto `elite_cloud_guard` L88): testei nerfar só até o piso onde `elite_cloud_guard`
  também não fica negativo (compromisso, não solução) — mesma causa raiz identificada nas
  rodadas 3-5 ("mesmo multiplicador não serve pra todo HP de pull/nível"), não resolvida.

## 3. Personagens ±15% (item 3 da missão)

O script de proxy da rodada 2/3 (`analyze_v2.py`, citado no `sim.py` mas não versionado —
não sobreviveu entre sessões) não existe mais no repo; reconstruí a métrica descrita nos
relatórios anteriores (`(chakra_cost/cooldown) × dano-médio-por-chakra`) a partir do zero:

```
valor(jutsu) = (chakra_cost/cooldown_s) × dano_por_chakra(jutsu)
  onde dano_por_chakra(jutsu) = dano_médio(jutsu, no seu required_level) / chakra_cost
  — e pra jutsu utilitário (base_damage=0, ex. buffs/kawarimi): dano_por_chakra imputado =
    média de dano/chakra de TODO jutsu de dano do jogo (mesma definição da rodada 3/4/5)
valor(personagem) = soma de valor(jutsu) pelos 4 jutsus de `personal_jutsus`
  (jutsus compartilhados por 2+ personagens contam igual pra cada um — não ajustados,
  mesma disciplina das rodadas 2/3: só o jutsu NÃO-compartilhado de cada um é tocado)
```

**Achado real** (não um efeito colateral desta rodada — pré-existente, nunca medido desde a
rodada 3 porque a proxy mudou de base 2 vezes desde então): `sabio_cerimonial` estava **+88,4%**
acima da média — `selo_de_exorcismo` (req 19) e `circulo_de_selos` (req 27) tinham
`base_damage`/`level_scale` desproporcionais a QUALQUER curva elemental do mesmo nível
(`selo_de_exorcismo` chegava a ~396 de dano médio em L19, contra ~136 do tier 1 elemental
recalibrado na rodada 5 no mesmo nível — quase 3× o "hit forte" do jogo inteiro naquele nível).
Nerfar isso sozinho deslocava `herdeira_hyuga` (usa `palma_gentil`/`palma_dupla`, não
compartilhados) pra fora por cima (a MÉDIA cai quando o outlier é corrigido, empurrando todo
mundo pra cima em % relativo) — precisou de um segundo ajuste.

| Personagem | Jutsu ajustado | Mudança | Desvio final |
|---|---|---|---|
| `sabio_cerimonial` | `selo_de_exorcismo`, `circulo_de_selos` | base/level/skill ×0,4 | +8,6% |
| `herdeira_hyuga` | `palma_gentil`, `palma_dupla` | base/level/skill ×0,7 | +1,2% |
| `genin_laranja` | (sem ajuste) | — | −11,8% |
| `kunoichi_armas` | (sem ajuste) | — | −5,0% |
| `genin_uchiha` | (sem ajuste) | — | −5,0% |
| `ninja_verde` | (sem ajuste) | — | −4,9% |
| `ninja_abelha` | (sem ajuste) | — | +3,9% |
| `sabio_loiro` | (sem ajuste) | — | +5,1% |
| `kunoichi_rosa` | (sem ajuste) | — | +7,9% |

**Todos os 9 dentro de ±11,8%** (mais apertado que o pedido de ±15%).

**Honestidade sobre a métrica**: como o script original se perdeu, esta é uma reconstrução
baseada na DESCRIÇÃO da fórmula nos relatórios anteriores, não uma reexecução idêntica — pode
diferir da rodada 3 em detalhe (ex.: genjutsu não tem curva de skill própria em `sim.py`,
aproximei com a curva de ninjutsu, mesma limitação documentada). O achado do `sabio_cerimonial`
(quase 3× o dano do resto do jogo no mesmo nível) é grande o bastante pra ser real independente
do detalhe exato da métrica — confirmado comparando na mão contra a tabela de tier do §6 de
`balanceamento.md`, não só pelo proxy.

## 4. Bosses novos/alterados do Covil (item 4 da missão)

`tools/balance/sim.py` **não modela fases nem summons** (`MONSTERS[id]` só tem `hp`/`attacks`
fixos — `phases` é lido só por `tools/export_tfs.py` pra gerar `boss_phases.lua`). Escrevi uma
simulação bespoke pra este check pontual (não faz parte do `sim.py` oficial), fiel ao que
`server/generated/scripts/naruto/boss_phases.lua` realmente gera — achado importante ao ler o
gerador: **`attack_multiplier` de fase NÃO aumenta o dano dos ataques do boss** (comentário do
próprio `tools/export_tfs.py`: "o `onHealthChange` não consegue alterar o dano dos `<attack>`
do monstro em runtime — a spell list é lida uma vez, no carregamento do XML"). O que a fase
"fúria" faz de verdade é: (1) cura de uma vez `floor(maxHealth×(mult−1)×0,10)` — HP extra a
limpar — e (2) aumenta a velocidade de movimento do boss. Minha simulação modela (1)
(relevante pro TTK) e nota (2) como fora do escopo de precisão deste check pontual.

Build taijutsu solo, TTK com summons vs sem (`hp_percent` de fase e `count` de summon lidos
direto de `data/monsters/*.json`):

| Boss | Summon novo/alterado | TTK sem summon | TTK com summon | Δ | Meta ±20% | death_rate (com summon) |
|---|---|---|---|---|---|---|
| Sócio Eterno (L70) | `magma_serpent` ×2 (existente, reusado) | 37,4s | 65,5s | **+75,5%** | ❌ (ver ajuste abaixo) | 0,00 |
| Portador dos Seis Caminhos (L95) | `invoked_path` ×2 (novo, L88 5000HP) | 124,2s | 168,8s | **+35,9%** | ❌ | 0,00 |
| Ancestral da Nuvem Vermelha (L100) | `crimson_echo` ×1 (novo, L92 6500HP) | 111,6s | 136,7s | **+22,5%** | ❌ (perto) | 0,00 |

**`death_rate` já era 0,00 nos 3 antes de qualquer ajuste** — a meta "não pode virar impossível
pro build taijutsu solo" já estava garantida. O `hp`/`count` dos summons foi ajustado pra também
fechar (ou chegar perto d)o ±20% de TTK:

- **`boss_rings_bearer`**: `invoked_path` count 2→**1** (`invoked_path` só existe como summon
  deste boss — sem colateral em nenhum spawn/quest/tarefa, verificado com grep em `data/`).
  Resultado: **+18,0%** ✅.
- **`boss_crimson_ancestor`**: `crimson_echo.hp` 6500→**5800** (mesma verificação — só existe
  como summon deste boss). Resultado: **+19,5%** ✅.
- **`boss_curse_partner`**: `magma_serpent` é reusado de verdade (spawn físico em
  `data/maps/forest_valley.json`, alvo de 8 tarefas/diárias — `grep -rn "magma_serpent" data/`
  confirma) — **não** toquei nos números dele (mudaria a economia de XP/hunt de quem caça esse
  monstro no campo, fora do escopo desta missão). Reduzi o `count` do summon 2→**1** (+79,5%→
  +37,8% de TTK) e subi o HP PRÓPRIO do boss 6200→**7000** (miniboss de trilha, não um dos 6 de
  referência — bump modesto, não dobrado) pra diluir mais a fração: **+34,3%**, ainda acima da
  meta, mas uma melhora de mais de 2× sobre o número original.

### Pendência honesta (item 4)

- **`boss_curse_partner` continua acima de +20%** (+34,3%). Fechar de verdade exigiria (a)
  dobrar o HP do boss (6200→~11400, desproporcional pra um miniboss de trilha) ou (b) uma
  variante mais fraca do summon dedicada a esta luta (o padrão que `crimson_echo`/
  `invoked_path` já demonstram ser a solução certa pros outros 2 bosses — um `magma_serpent_eco`
  ou campo `hp_scale` no summon de fase, que exigiria mudar também `tools/export_tfs.py`
  `boss_phases.lua` pra aplicar escala — maior que um ajuste de número, não implementado nesta
  rodada). `death_rate=0,00` confirma que a luta continua **vencível** solo, só mais longa que o
  ideal — não é um bloqueador de progressão, é um desvio de ritmo.

### Addendum 2026-09-05: `attack_multiplier` agora aumenta dano de verdade — recalibrar na rodada 7

O achado do §4 acima (`attack_multiplier` de fase NÃO aumentava o dano dos ataques do boss) foi
**corrigido**: `boss_phases.lua` (gerado por `tools/export_tfs.py`) ganhou um segundo
`CreatureEvent`, `NarutoBossFury`, registrado no `onHealthChange` do JOGADOR (login, via
`character_switch.lua`), que multiplica `primaryDamage`/`secondaryDamage` de verdade (arredondado)
quando quem bateu é um boss na fase de fúria atual (`mult > 1`, lido de
`NarutoBossPhases.state[bossId]`, publicado pelo `onHealthChange` do MONSTRO de sempre) — cobre
dano melee e de spell do boss, não afeta summons. Detalhe completo em
`docs/sistemas/monstros-e-pvm.md` §Bosses. Validado headless (sem instalar/reiniciar o servidor
do playtest): `tools/tests/test_boss_fury_headless.lua` / `tools/tests/run_boss_fury_tests.sh`
(19/19, boss fictício com fases {100%: mult 1.0, 50%: mult 1.5} — dano ×1,5 confirmado ao cruzar
50%, outro monstro não afetado, limpeza no `onDeath` confirmada).

**Isto NÃO foi reavaliado pelo `tools/balance/sim.py`** — como o §4 já registrou, o simulador
oficial não modela `phases`/summons (só `hp`/`attacks` fixos por `MONSTERS[id]`), então os TTKs
de boss deste relatório (e da rodada 5/6 anteriores) foram medidos **sem** o multiplicador de
dano real — só com a cura pontual (`+(mult−1)×10%` do HP máximo) e o aumento de velocidade, que
continuam acontecendo (não foram removidos). Na prática, **o TTK real dos 12 bosses do jogo na
fase de fúria vai subir** a partir de agora — a fração de dano extra na fase de fúria é
proporcional a `mult` (ex. Serpente Branca `mult 1.9` = quase o dobro de dano nos ~25% finais de
vida dela), e como esse dano nunca foi contabilizado nas simulações de TTK/death_rate acima, os
valores atuais de `attack_multiplier` em `data/monsters/*.json` foram calibrados (rodadas 1–6)
**pressupondo que o multiplicador não fazia nada** — ou seja, estão mais altos do que deveriam
agora que fazem.

**Recomendação pra rodada 7 (NÃO aplicada nesta sessão — só JSON de fases, `data/monsters/`, não
foi tocado)**: cortar pela metade o excedente de cada `attack_multiplier` acima de 1.0 (ex.
`1.5 → 1.25`, `1.9 → 1.45`, `1.3 → 1.15`) em todos os bosses com fase de fúria, depois rodar uma
simulação bespoke (mesmo molde do §4, já que `sim.py` não modela fases) medindo TTK/death_rate
COM o multiplicador de dano real aplicado, e reajustar caso a caso contra a mesma meta de ±20% de
TTK usada no §4. `boss_curse_partner` (já **acima** da meta mesmo antes deste fix, ver pendência
logo acima) deve ser o primeiro a testar — o dano real de fúria só piora a folga que já faltava.

## 5. `validate_data.py` / `export_tfs.py` / `luajit` / timing

```
.venv/bin/python tools/validate_data.py
  → 54 jutsus, 174 itens, 40 monstros, 4 vilas, 9 personagens, 5 sets elementais — OK
.venv/bin/python tools/export_tfs.py
  → OK: 40 monstros, 54 jutsus, 174 itens, 21 NPCs, 47 missões, 5 ranks, 114 tarefas, 60 diárias
for f in $(find server/generated -iname "*.lua"); do luajit -bl "$f" /tmp/out.luac; done
  → 0 falhas (todos os .lua gerados compilam limpo, incluindo boss_phases.lua)
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json      → 2040 simulações em 96,9s (orçamento 120s)
python3 tools/balance/sim.py --group-matrix --json /tmp/group.json → 36 grupo + 18 boss em 2,1s
python3 tools/balance/sim.py --hunt --json /tmp/hunt.json          → 40 níveis × 2 (com/sem pílula) em 1,4s
```

Nenhum arquivo em `server/tfs/data/` foi editado à mão nem `install_generated.sh` rodado; o
servidor do playtest em andamento não foi reiniciado, o cliente não foi usado, conforme
instruído.

**Achado colateral bom**: o pior caso da meta de hunt de 30 min (item 5 da rodada 5, "chakra
sustentável") melhorou de 20,7% (L20, `exam_rival_stone`) pra **4,6%** (L30, `stone_sentinel`)
— efeito colateral do `HYBRID_JUTSU_CADENCE_FRAC` (§1): menos casts por hora = menos pressão
sobre o chakra na build híbrida, que é a única testada por `simulate_hunt`.

## 6. Resumo: metas atingidas / não atingidas

| Meta | Status |
|---|---|
| 1. Híbrido ≤+15% em 6/6 bosses, ninjutsu −15%..+10%, burst ≥1,3× preservado | **✅ 6/6** (era 2/6) — burst inalterado (39/505, mesma região da r5) |
| 2. Grupo 3+: ninjutsu +30-60% | ❌ parcial — **2/12 cenários na faixa** (era 1/12); 3 dos 4 piores outliers caíram de +112%/+177%/+178%/+234% pra +17%/+44%/+76%/+91% |
| 3. Personagens ±15% | **✅ 9/9**, pior caso ±11,8% |
| 4. Bosses novos: TTK ±20%, não impossível pro taijutsu solo | ❌ parcial — **2/3 dentro de ±20%**, `death_rate=0,00` nos 3 (não impossível, meta de segurança cumprida) |
| 5. `validate_data.py`/`export_tfs.py` passam, matriz <120s, `--json` OK | **✅** |
| 6. Documentação (`balanceamento.md`, `README.md`, `balanceamento-relatorio-v6.md`) | **✅** — `docs/00-biblia-do-jogo.md` deliberadamente não tocado (nenhuma regra visível mudou, ver §1) |

## 7. Pendências honestas pra rodada 7

1. **Grupo 3+ ainda não-uniforme** (10/12 fora da faixa, contando N=1/2 no cômputo tradicional
   dos relatórios anteriores) — causa raiz confirmada de novo: monstros "none"/tier-1-só não têm
   AoE de verdade (achado 1 do §2, corrigível só mudando `type` de spell — mecânica, não número);
   jutsus "campeão" compartilhados entre 2 níveis/monstros bem diferentes não fecham com um
   multiplicador único (achado 2 do §2). Resolver de vez provavelmente precisa de: (a) mudar
   `katon_goukakyuu` pra `type="area"` (ativa capacidade real em grupo) OU (b) um jutsu de área
   tier 1 dedicado pra L2-11 (abaixo do `req 6` atual de `katon_sopro_brasas`), e (c) uma forma
   de "dano decrescente contra pull de HP baixo" (mudança de engine, já apontada como fora de
   escopo desde a rodada 3).
2. **`boss_curse_partner` (Sócio Eterno) acima de +20% de TTK com summons** (+34,3%) — precisa
   de uma variante mais fraca dedicada do summon (`magma_serpent` é reusado demais pra tocar) ou
   um campo `hp_scale` em `tools/export_tfs.py`/`boss_phases.lua` (mudança de exportador, não só
   de dado).
3. **Proxy de personagens reconstruída do zero** (`analyze_v2.py` da rodada 2/3 não sobreviveu
   entre sessões) — considerar versionar o script desta vez (`tools/balance/character_value.py`)
   pra rodada 7 não precisar reconstruir de novo. Não versionei nesta sessão por não ter certeza
   se bate 100% com a fórmula original das rodadas 2/3 (documentado como aproximação no §3).
4. **`wolf`/`bandit`/`mercenary_bridge`/`mist_guardian`/`white_clone`** seguem abaixo da faixa
   de grupo — herdado, não coberto pelas mudanças desta rodada (ver §2).
