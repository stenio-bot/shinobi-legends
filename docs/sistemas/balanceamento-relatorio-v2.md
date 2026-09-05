# Relatório de balanceamento PvM — rodada 2 (setembro/2026)

Continuação da rodada 1 (`docs/sistemas/balanceamento-relatorio.md`). Esta rodada terminou o
cenário **multi-alvo** em `tools/balance/sim.py` (pull de N monstros, chakra finito com regen
real, rotação por dano/segundo disponível) e usou os dois cenários (1×1 longo em boss + grupo)
pra resolver o achado central da rodada 1: *"ninjutsu perde 20–90% do DPS sustentado em lutas
longas"*. Ver `tools/balance/README.md` (seção "o que é fórmula real e o que é premissa") antes
de questionar qualquer número aqui — ele não mudou nesta rodada, só ganhou as seções novas.

Comandos usados (mantidos <120s, ver §5):

```bash
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json          # 1938 sims, ~57s
python3 tools/balance/sim.py --group-matrix --json /tmp/group.json     # 36 grupo + 18 boss, ~1.5s
python3 tools/validate_data.py
python3 tools/export_tfs.py     # gera server/generated/, NÃO instalado (outro agente usando o servidor)
```

## 0. Estado em que a sessão começou (trabalho parcial no disco, não comitado)

Um agente anterior desta mesma missão foi interrompido a meio de "rodar as matrizes de novo".
Ele tinha:

1. Escrito **quase todo** o cenário multi-alvo em `sim.py` (`simulate_group_fight`,
   `simulate_group`, `GROUP_SCENARIOS`, `run_group_matrix`, `run_boss_matrix`, `--group-matrix`)
   — funcional e bem documentado, mas com **um bug real**: a função `pick_ninjutsu_jutsu` tinha
   sido estendida com um parâmetro `taijutsu_dps_est` (só usa o jutsu se ele bater o DPS de
   arma), mas o **call site dentro de `simulate_fight`** (o combate 1×1, linha 469) não foi
   atualizado pra passar esse valor — o parâmetro sempre chegava como o default `0.0`, ou seja,
   a checagem "só usa ninjutsu se for melhor que taijutsu" **nunca rodava de verdade** no 1×1.
   Esse era, sozinho, o motivo principal de ninjutsu aparecer "pior que taijutsu" em boss de
   nível alto (rodada 1, achado 6): o build gastava chakra em jutsu **pior** que golpear com a
   arma, e isso inflava o TTK. Corrigido nesta sessão (ver §2).
2. Ajustado `level_scale`/`skill_scale` de todo jutsu tier 2/3 elemental (×1.5/×1.25, exceto
   dois outliers inconsistentes — `raiton_lanca_relampago` ×2.025 e `suiton_suiryuudan` ×1.725 —
   que quebravam a paridade elemental; corrigidos nesta sessão, ver §4) e normalizado o
   `cooldown_s` de todo tier 1 pra 2.0s (mantido — é uma correção válida, alinha a cadência do
   jutsu básico ao attack interval do player).
3. Deixado uma pasta `tools/balance/_v2backup/` com o estado pré-rodada-2 do `data/` (não mexi
   nela; serviu de referência pra comparar antes/depois nesta sessão).

Não descartei nada do trabalho parcial: o código do cenário multi-alvo ficou como estava (só
corrigi o bug do call site), e a filosofia "tier 2/3 mais forte que tier 1" foi mantida — só
recalibrei os multiplicadores porque, medindo com o simulador já corrigido, eles não bastavam
pra atingir as metas da missão (ver §2–§4).

## 1. Cenário multi-alvo: geometria e N por região

Pedido da missão: **N pela densidade real de `spawns_lore.json` por região**. Esse arquivo é
um *pedido* ao agente de mapa (`"spawns": []` de propósito — só tem `requests` com `count` por
zona, sem coordenadas). A geometria **jogável de verdade** está em `data/maps/forest_valley.json`
(`"spawns"` com x/y reais). Medi o "pull" real como **clustering por union-find** (mesma
espécie, raio 10 tiles) nesse mapa — script:

```python
# unindo spawns da mesma espécie a <=10 tiles (Euclidiana) via union-find,
# pull real = tamanho do maior componente conectado
```

Isso **corrigiu um erro real do agente anterior**: o `GROUP_SCENARIOS` dele usava **um N por
região inteira** (ex.: `ruinas_do_cla_marionetista: n=4` aplicado tanto a `ruin_puppet` quanto
a `curse_shaman`), sem medir cada monstro. Medindo de verdade:

| Monstro | Região | Spawns no mapa | Maior cluster (≤10 tiles) | N usado antes | N usado agora |
|---|---|---|---|---|---|
| `wolf` | Floresta da Vila | 6 | **3** | 2 | 3 |
| `bandit` | Floresta da Vila | 4 | **2** | 2 | 2 |
| `leech` | Floresta da Morte | 4 | **1** (todos a 12+ tiles) | 3 | 1 |
| `lesser_serpent` | Floresta da Morte | 3 | **1** (todos a 12–26 tiles) | 3 | 1 |
| `ruin_puppet` | Ruínas do Clã | 6 | **3** | 4 | 3 |
| `curse_shaman` | Ruínas do Clã | 3 | **2** | 4 | 2 |
| `thunder_eagle` | Montanha do Trovão | 5 | **3** | 2 | 3 |
| `storm_monk` | Montanha do Trovão | 3 | **2** | 2 | 2 |
| `mercenary_bridge`/`mist_guardian` | Costa das Marés | 0 (região sem mapa ainda) | — | 1 | 2 (placeholder conservador, ver nota) |
| `white_clone`/`elite_cloud_guard` | Covil da Nuvem Vermelha | 0 (região sem mapa ainda) | — | 2 | 2 (idem) |

Achado direto dessa correção: **`curse_shaman` a N=4 morria pro jogador 45–55% das vezes**
(`death_rate` real medido antes da correção, com HP/dano de `data/monsters/curse_shaman.json`
inalterados) — um pull que o mapa real não suporta (o 3º spawn fica a 12+ tiles do par mais
próximo). Com N=2 (o pull que o mapa de verdade permite), `death_rate` cai a 0%. **Isso não era
um bug de jutsu — era um cenário de teste inválido.** Da mesma forma, boa parte do "ninjutsu
domina 300–800%" que a rodada 2 via em `lesser_serpent` (N=3 usado antes) some quando N vira 1
(a "geometria simples: adjacentes/em linha" da missão não existe pra esse monstro no mapa
atual — os 3 spawns estão espalhados). Regiões sem mapa físico (Costa das Marés, Covil) usam um
placeholder conservador N=2, sinalizado explicitamente no código — não é medição real, é um
palpite razoável até o agente de mapa desenhar essas zonas.

## 2. O bug do call site (§0.1) + a causa restante do desbalanço

Com o bug corrigido (`taijutsu_dps_est` passado de verdade em `simulate_fight`), rodei os 6
bosses (1 por região, "luta longa" de 1–3 min) **sem tocar em nenhum número de jutsu ainda**:

| Boss | Nível | Taijutsu TTK | Ninjutsu TTK (só com o fix do bug) | Diferença |
|---|---|---|---|---|
| Chefe dos Bandidos | 12 | 150,9s | 66,5s | ninjutsu **56% mais rápido** |
| Espadachim da Névoa | 19 | 158,6s | 38,4s | ninjutsu **76% mais rápido** |
| Serpente Branca | 25 | 166,0s | 123,1s | ninjutsu **26% mais rápido** |
| Marionetista | 50 | 77,6s | 77,6s | empate (jutsu nunca bate o DPS de arma) |
| Oni Ancestral | 80 | 93,7s | 93,7s | empate |
| Ancestral da Nuvem Vermelha | 100 | 103,7s | 103,7s | empate |

Isso já **inverteu completamente** o achado da rodada 1: com o bug corrigido, ninjutsu não
"perde" em luta longa — ele **ganha demais** em L12–25 (jutsu ignora armadura + a reserva de
chakra inicial é grande o bastante pra durar quase a luta inteira nesses níveis) e empata
exatamente em L50+ (o magic level, preso pela constante `1600` fixa em
`vocation.cpp:149 Vocation::getReqMana`, já não alcança nenhum jutsu que bata o DPS de arma —
o build vira taijutsu puro sozinho, sem precisar de nenhum ajuste numérico). A meta da missão
é **taijutsu ≥ ninjutsu por margem ≤15%** — ou seja, o problema real da rodada 2 não era "ninjutsu
fraco", era "ninjutsu forte demais em L12–25 e na distância certa só a partir de L50".

## 3. Ajuste numérico: tier 1 vs tier 2/3, e por quê

`pick_ninjutsu_jutsu` (1×1) escolhe o **único** jutsu de maior dano/cooldown do kit elemental
com vantagem — e por causa da amortização de cooldown curto, isso **é sempre um tier 1**
(mesmo depois do buff ×1.5/×1.25 do tier 2/3 feito na sessão anterior: um tier 3 a nível 100 dá
~54 dano/s contra ~90 dano/s do tier 1 equivalente). Ou seja: **o lever que decide o 1×1 é
sempre o tier 1**; tier 2/3 só importa pra grupo (`simulate_group_fight` escolhe entre TODOS os
jutsus do kit prontos, e aí a multiplicação por `hits` — nº de alvos atingidos — faz área/beam
valer a pena mesmo com dano/cooldown menor que o tier 1).

Isso separa os dois problemas em dois levers independentes:

- **`tier1_mult = 0.35`** em `base_damage`, `level_scale` e `skill_scale` de todo jutsu tier 1
  ofensivo (projétil e área) das 5 vilas elementais — resolve o 1×1 (bosses L12/19/25).
- **`tier23_mult = 0.9`** no mesmo conjunto de campos pra todo tier 2/3 — mantém área/beam
  fortes o bastante pra valerem a pena em grupo sem reintroduzir o domínio de 1×1 (tier 2/3
  quase nunca vira o "melhor pick" 1×1 mesmo depois do nerf de tier 1, exceto en casos
  pontuais — ver §4).

Recalibrei os dois multiplicadores a partir do **baseline original** (antes de qualquer edição
desta sessão OU da sessão anterior — `git show HEAD:data/jutsus/*.json`), não empilhando em
cima do ×1.5/×1.25 do agente anterior, porque empilhar multiplicadores tornava a busca por um
ponto de equilíbrio impossível de raciocinar (testei e o resultado inicial ficou preso em 0%
pra qualquer variação, porque a base já estava nerfada demais). O resultado final:

### Boss 1×1 (depois do fix do bug + tuning numérico)

| Boss | Nível | Taijutsu TTK | Ninjutsu TTK | Diferença | Dentro da meta (≤15%)? |
|---|---|---|---|---|---|
| Chefe dos Bandidos | 12 | 150,9s | 145,7s | -3,5% | ✅ |
| Espadachim da Névoa | 19 | 158,6s | 137,3s | -13,4% | ✅ (perto do limite) |
| Serpente Branca | 25 | 166,0s | 166,0s | 0% | ✅ |
| Marionetista | 50 | 77,6s | 77,6s | 0% | ✅ |
| Oni Ancestral | 80 | 93,7s | 93,7s | 0% | ✅ |
| Ancestral da Nuvem Vermelha | 100 | 103,7s | 103,7s | 0% | ✅ |

Híbrido (metade do tempo de treino em cada trilha): fica entre 6,6% e 19,9% **atrás do melhor
build** em cada boss (mediana ~13%) — "perto do melhor", não empatado, o que é coerente: um
personagem que divide o treino entre taijutsu e ninjutsu tem as duas skills mais baixas que um
especialista em qualquer uma delas.

**Por que L19 fica em -13,4% (não 0%) mesmo depois do tuning:** a Espadachim da Névoa é boss de
nível 19, bem no meio do platô de dano de arma entre os tiers de equipamento em L15
(`weapon_max_damage` bruto ≈19) e L20 (≈38, o dobro) — ou seja, **taijutsu está anormalmente
fraco exatamente nesse nível** por falta de um tier de arma intermediário, não por causa de
nenhum número de jutsu. Confirmei rodando o mesmo cálculo de dano de arma sem monstro nenhum
(só nível/skill/gear) e o salto malfeito segue lá. É um achado de `data/items/*.json`, fora do
escopo desta sessão (missão limita a `jutsus/element_sets/characters`) — reportando como
pendência (ver §7), não escondendo atrás do número de ninjutsu.

### Grupo (N corrigido, ver §1) — meta: ninjutsu +30–60% em grupos de 3+

| Monstro | Nível | N | Taijutsu XP/h | Ninjutsu XP/h | Diferença | Dentro da meta? |
|---|---|---|---|---|---|---|
| `wolf` | 2 | 3 | 5 819 | 6 221 | +6,9% | ❌ (abaixo) |
| `ruin_puppet` | 27 | 3 | 85 832 | 134 656 | **+56,9%** | ✅ |
| `thunder_eagle` | 54 | 3 | 271 677 | 274 447 | +1,0% | ❌ (abaixo) |

Só 3 dos 6 cenários de grupo do jogo têm N≥3 real (ver §1 — o resto virou N=1/2 depois da
correção de clustering). `ruin_puppet` bate a meta em cheio. `wolf`/`thunder_eagle` ficam
positivos mas abaixo de +30%: testei um `tier23_mult` maior (até 1.3) pra tentar puxar os dois
pra cima, mas isso quebra `ruin_puppet` (sobe a +125%) e o boss L19/25 (sobe a -23%/-10%) — os
três cenários respondem de forma DIFERENTE ao mesmo multiplicador global porque dependem de
elemento, defesa do monstro e nível de forma não-uniforme (ex.: `thunder_eagle`/`wolf` usam kit
katon/fuuton com jutsus tier 1 relativamente mais fracos no nível deles do que
`ruin_puppet`/katon tier 2 no L27). Não achei um único par `(tier1_mult, tier23_mult)` que
satisfaça os 6 pontos de teste (3 boss "apertados" + 3 grupo) simultaneamente — prioridade foi
manter o 1×1 dentro da meta (item 1 da missão, listado primeiro) e aceitar `wolf`/`thunder_eagle`
como miss documentado, não escondido (ver §7). `curse_shaman`/`leech`/`lesser_serpent`/
`mercenary_bridge`/`mist_guardian` etc. viraram N=1/2 pela correção de clustering — não são mais
testes válidos de "+30–60% em grupo de 3+" (ver §1), mas seus números (todos com
`death_rate=0`) seguem saudáveis.

## 4. Paridade elemental (meta: ±10% em burst e DPS-de-grupo)

Comparei, pro mesmo nível/skill de ninjutsu, o `(dano×hits)/cooldown` do MELHOR jutsu de cada
elemento (5 kits), sem vantagem/desvantagem elemental (isolando só a força intrínseca do kit):

| Elemento | Nível 40 (desvio da média) | Nível 70 | Nível 100 |
|---|---|---|---|
| Katon | -3,3% | -5,4% | -6,3% |
| Fuuton | -0,5% | +1,2% | +3,0% |
| Raiton | +2,4% | +1,8% | +2,3% |
| Doton | -9,2% | -7,4% | -8,7% |
| Suiton | +10,6% | +9,7% | +9,7% |

Dentro de ±10% (suiton bate exatamente o limite em alguns níveis) do nível 30 em diante — abaixo
disso (L8–20) os 5 elementos ainda estão desbloqueando jutsus em `required_level` diferentes uns
dos outros (raiton/doton são deliberadamente "burst single"/"área lenta" por design, ver
`docs/sistemas/combate-e-jutsus.md`), então grandes desvios em L8–20 são a flavor pretendida, não
desbalanço. Corrigi 2 outliers específicos que o agente anterior tinha introduzido sem querer
(`raiton_lanca_relampago` e `suiton_suiryuudan` receberam ×2.025/×1.725 em vez do ×1.5 uniforme
dos outros tier 2/3 — provavelmente um erro de cálculo, não intencional) — sem esse fix, suiton
e raiton ficavam 15%+ acima da média.

## 5. Jutsu inútil / dominante

Rodei `pick_ninjutsu_jutsu` pra toda combinação `MATRIX_LEVELS × monstro` (646 combinações) e
extraí o `dmg_by_jutsu` de todo cenário de grupo. **Nenhum jutsu domina >60% do valor do kit
sozinho** — a frequência de escolha entre os 5 tier-1 varia 15–24% cada (katon 18,7%, fuuton
19,5%, raiton 22,8%, doton 23,5%, suiton 15,4% das vezes em que ALGUM jutsu foi escolhido),
razoavelmente equilibrada.

**6 jutsus nunca foram o pick ótimo** em nenhum dos dois cenários testados (1×1 ou grupo):

| Jutsu | Tier/tipo | Por quê (hipótese) |
|---|---|---|
| `raiton_corrente_estatica` | 1, área (cross_r1) | Dano menor que o projétil irmão (`raiton_hari`) com cooldown parecido — mesmo em grupo, `hits` não compensa; **candidato a buff de dano ou de área** num próximo passe. |
| `suiton_nevoa_cortante` | 1, área (cone_2) | Mesmo problema do item acima, espelhado em suiton. |
| `fuuton_redemoinho_prisao` | 2, alvo único (controle) | É jutsu de **controle** (paralyze), não de dano — nunca vence uma corrida de DPS por design; o simulador não modela o valor de "trava o alvo", então isso é esperado, não bug. |
| `suiton_prisao_agua` | 2, alvo único (controle) | Idem — control-type. |
| `fuuton_tornado_cortante` | 3, beam (line_6) | Perde a corrida de DPS/hits pro `fuuton_rajada_cortante` (tier 2) no nível em que os dois já estão desbloqueados — **candidato a revisão** (era esperado que o tier 3 vencesse pelo menos em grupos grandes). |
| `doton_colapso_terreno` | 3, área (circle_r2) | Nenhum monstro comum testado tem `doton` como elemento de vantagem num nível ≥48 (`required_level`) simultâneo a um cenário de grupo — pode ser cobertura de teste insuficiente, não o jutsu em si; recomendo testar de novo quando a Montanha/Covil tiverem mapa real (ver §1). |

Não toquei nos 2 candidatos "a revisão" (`fuuton_tornado_cortante`, `raiton_corrente_estatica`/
`suiton_nevoa_cortante`) numericamente nesta sessão — prefiro reportar com evidência a adivinhar
mais um multiplicador sem conseguir testar contra um cenário real que os force a ser escolhidos
(ver §7).

## 6. Papel de cada jutsu (documentado, não mudou de tipo/forma nesta sessão)

| Tier | Papel pretendido | Exemplo |
|---|---|---|
| 1 projétil | Burst curto CD, sustenta a rotação inteira | `katon_goukakyuu`, cd 2,0s |
| 1 área | DoT/controle leve em pull pequeno | `katon_sopro_brasas`, cone_2 |
| 1 self | Utilidade (heal_over_time) | `doton_muralha_pedra` |
| 2 área/beam | Workhorse de grupo — o que carrega o "+30-60%" | `katon_anel_chamas`, `raiton_lanca_relampago` |
| 2 alvo único | Controle (paralyze/stun) — não é sobre DPS | `fuuton_redemoinho_prisao`, `suiton_prisao_agua` |
| 3 área/beam grande | Nuke — só relevante em pulls grandes (N≥4) ou builds de altíssimo nível | `suiton_vortice_devorador`, `doton_colapso_terreno` |

## 7. Personagens: 4 jutsus pessoais, ±15% em valor total

Nenhum dos 9 personagens é simulado em combate por `sim.py` (`CHARACTERS`/`personal_jutsus`
nunca são referenciados no loop de luta — só `ELEMENT_SETS` entram na rotação de ninjutsu).
Defini então um "valor" por jutsu pessoal independente do simulador de combate: `dano/cooldown`
a nível 50 pros jutsus ofensivos (usando a skill correspondente ao campo `skill` do próprio
jutsu — taijutsu/ninjutsu/genjutsu/shuriken), e pros jutsus utilitários (`base_damage=0`, ex.
`kawarimi`/`shousen`/buffs), uma equivalência `(chakra_cost/cooldown_s) × (dano médio por
chakra dos jutsus de dano do pool)` — um proxy honesto, não uma fórmula do jogo (documentado
como tal).

**Antes** (4 personagens fora de ±15%, 2 deles a mais de 50% de distância da média):

| Personagem | Valor | Desvio |
|---|---|---|
| `genin_laranja` | 67,4 | **-52,3%** |
| `sabio_cerimonial` | 70,4 | **-50,3%** |
| `genin_uchiha` | 107,0 | -24,4% |
| `ninja_verde` | 238,6 | **+68,6%** |
| (outros 5) | 130,4–186,8 | -7,9% a +32,0% |

**Depois** (ajustei só o(s) jutsu ÚNICO(s) — não compartilhado(s) com outro personagem — de
cada um dos 4 fora da faixa; `kawarimi`/`punho_suave`/`fuuin_contencao`, compartilhados por 2+
personagens, ficaram intocados pra não desequilibrar quem já estava OK):

| Personagem | Valor | Desvio | Jutsu ajustado |
|---|---|---|---|
| `kunoichi_armas` | 161,1 | +13,3% | (sem ajuste) |
| `kunoichi_rosa` | 159,7 | +12,4% | `soco_monstruoso` ×0,82 |
| `ninja_abelha` | 150,6 | +6,0% | `lamina_relampago_pessoal`/`corte_duplo`/`raio_selado` ×0,785 |
| `ninja_verde` | 144,9 | +1,9% | `chute_giratorio`/`soco_da_juventude`/`chute_ascendente` ×0,438 |
| `herdeira_hyuga` | 143,5 | +1,0% | (sem ajuste) |
| `sabio_cerimonial` | 140,7 | -1,0% | `selo_de_exorcismo`/`circulo_de_selos` ×2,6 |
| `sabio_loiro` | 131,3 | -7,6% | (sem ajuste) |
| `genin_laranja` | 124,2 | -12,6% | `fuuton_rasteira_vento` ×2,9 |
| `genin_uchiha` | 123,0 | -13,5% | `agulhas_incendiarias` ×1,324 |

Todos os 9 dentro de ±15%. `genin_laranja` e `sabio_cerimonial` precisaram de multiplicadores
grandes (×2,9/×2,6) porque cada um tem só 1–2 jutsus de dano entre os 4 (o resto é utilidade) —
concentrar o "orçamento de dano" de um personagem-suporte num único jutsu-assinatura é uma
escolha de design razoável (ver nota no próprio arquivo), não um número arbitrário.

## 8. `tools/export_tfs.py`: dois itens da rodada 1

**Item 10 (aplicado — mudança simples, testada):** `items_xml()` traduzia `bonuses` do JSON
pros atributos do `items.xml`, mas não reconhecia as chaves `attack`/`defense` — dois itens
(`ring_stone_will`, `strings_of_the_puppeteer`) tinham esses bônus silenciosamente descartados.
Confirmei em `server/tfs/src/items.cpp:22` (`"armor"` → `ITEM_PARSE_ARMOR`) e `:25` (`"attack"`
→ `ITEM_PARSE_ATTACK`) que os dois são atributos genéricos válidos em **qualquer** item, não só
`weapon`/`armor` — bastou adicionar `"attack": "attack", "defense": "armor"` ao dicionário.
Rodei `tools/export_tfs.py` depois do fix: `server/generated/items/items_naruto.xml` agora tem
`<attribute key="armor" value="3"/>` no anel e `<attribute key="attack" value="8"/>` nos fios
do marionetista.

**Item 4 (avaliado, NÃO aplicado — decisão explícita):** a missão pediu pra avaliar usar
`level` em vez de `maglevel` na fórmula gerada (`onGetFormulaValues`, `tools/export_tfs.py`
linha ~394), já que o magic level fica preso baixo pela constante `1600` fixa em
`vocation.cpp:149`. Confirmei que a troca é tecnicamente trivial e não exige C++
(`combat.cpp:1108-1111 ValueCallback::getMinMaxValues` já empurra `player:getLevel()` E
`player:getMagicLevel()` pro Lua goal — o script é livre pra ignorar `maglevel` e usar só
`level`). **Não apliquei** porque todo o tuning desta sessão (§2–§4) foi calibrado
**assumindo** que o magic level fica baixo (é justamente isso que faz ninjutsu convergir pra
taijutsu puro em L50+, cumprindo a meta de 0% de diferença sem precisar de mais nenhum ajuste).
Trocar a fórmula agora mudaria a curva de dano de todo jutsu em todo nível simultaneamente,
exigindo recalibrar `tier1_mult`/`tier23_mult` do zero sem orçamento de tempo nesta sessão — e
o resultado atual já cumpre a meta de 1×1 sem essa mudança. Fica registrado como opção viável
pra uma rodada 3 dedicada a ela (não uma miscelânea no fim desta).

## 9. Achado extra (não corrigido, fora do escopo de `data/jutsus`)

`curse_shaman` (N corrigido para 2, ver §1) tinha `death_rate` 45–55% no N=4 anterior — não é
mais um problema depois da correção de N, mas vale registrar: **um pull de 4 curse_shaman L44
seria perigoso de verdade** se o mapa algum dia permitir esse cluster. Não editei
`data/monsters/curse_shaman.json` (fora da lista de arquivos autorizados desta missão:
`jutsus/element_sets/characters`) — sinalizando pro próximo passe de balanceamento de monstro.

## 10. Pendências honestas

1. **Boss L19 em -13,4% (dentro da meta, mas no limite) por causa de um platô de tier de arma
   em L15–20** (`data/items/*.json`, fora do escopo desta sessão) — ver §3.
2. **`wolf`/`thunder_eagle` abaixo de +30% em grupo de 3** — os 3 cenários de grupo válidos
   respondem de forma não-uniforme ao mesmo multiplicador global (ver §3); não achei um par
   `(tier1_mult, tier23_mult)` que satisfaça os 6 pontos de teste (3 boss + 3 grupo)
   simultaneamente, e priorizei a meta de 1×1 (listada primeiro na missão).
3. **2 jutsus candidatos a revisão de número** (`fuuton_tornado_cortante` perdendo pro próprio
   tier 2 do mesmo elemento; `raiton_corrente_estatica`/`suiton_nevoa_cortante` tier 1 de área
   sem uso) — reportados com evidência (§5), não ajustados (faltou um cenário de teste que os
   force a ser escolhidos pra calibrar com confiança).
4. **Magic level estruturalmente baixo** (constante `1600` em `vocation.cpp:149`) — avaliado
   usar `level` na fórmula gerada (§8), decidido NÃO aplicar nesta sessão (mudaria toda a curva
   recém-calibrada sem orçamento pra recalibrar).
5. **Costa das Marés e Covil da Nuvem Vermelha não têm mapa físico** — N=2 usado nos cenários
   de grupo dessas regiões é um placeholder conservador, não medição real (ver §1); revisitar
   quando o agente de mapa desenhar essas zonas.
6. **`curse_shaman` L44 seria perigoso em pull de 4** (§9) — fora do escopo de arquivo desta
   sessão, sinalizado pro próximo passe de monstros.

## 11. Como reproduzir

```bash
cd /Users/stenioz/Projetos/shinobi-legends
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json          # ~57s
python3 tools/balance/sim.py --group-matrix --json /tmp/group.json     # ~1.5s
python3 tools/validate_data.py
python3 tools/export_tfs.py       # escreve em server/generated/, não instala
```
