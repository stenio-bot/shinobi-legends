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
a regra de bosses. `attack_multiplier` de 1.9 na fase 3 vale, na prática, ~+45% de velocidade
(ver a limitação do TFS em `monstros-e-pvm.md`).

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

**Economia de chakra (checada na rodada 3):** regen passivo é `gainmanaticks=5 gainmanaamount=3`
(0,6 chakra/s, igual em toda vila, **não escala com level** — `tools/export_tfs.py`) contra um
pool de `50+level*10`. Com os custos de tier 2/3 da rodada 3 (105–245, ver tabela de escala por
tier acima), a rotação de ninjutsu "seca" (chakra insuficiente pro jutsu que estava usando) bem
antes dos 30s em quase todo nível — L15 seca em 4s, L30 em 12s, L60 em 24s, L100 em 40s (jutsu
tier 1 "de sustento", mais barato, aguenta mais: 12–20s em L5–10). Isso é **intencional, não bug**:
é o mecanismo que faz o burst de tier 2/3 (calibrado pra bater o dano de arma num boss) não virar
DPS sustentado de graça — o resto da luta (que dura minutos contra um boss) é taijutsu. Regen
natural do zero ao cheio leva de 250s (L10) a 1750s (L100) — trickle entre lutas, não um lever de
combate. O lever de combate real são as **pílulas de chakra**: uma Pílula Grande (350 CK, req
L30) dá ~1,7 cast extra de tier 3 no meio de uma luta longa. `tools/balance/sim.py` ainda não
simula o jogador bebendo pílula de chakra em combate (só HP) — pendência documentada em
`balanceamento-relatorio-v3.md` §8.

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
> tier 2 `suiryuudan` recebeu compensação extra). Números **pós-rodada-3** abaixo.

Escala por tier (com `required_level` de referência e ninjutsu = magic level real, ver acima):

| Tier | base_damage | level_scale | skill_scale | chakra | cooldown |
|---|---|---|---|---|---|
| 1 projétil | 7–9 | 0,385–0,42 | 0,28–0,315 | 12–16 | 2,0 s (inalterado na rodada 3) |
| 1 área/self | 4,9–5,6 (área) / 0 (self) | 0,315 | 0,21–0,245 | 14–28 | 1,3–3,0 s (2 jutsus ganharam CD menor, ver §4 do relatório v3) |
| 2 "normal" (katon/doton/fuuton, tem tier 3 atrás) | 16–37,8 | 2,07–3,1 | 0,63–0,9 | 105–147 | 4,0–6,0 s |
| 2 "teto do elemento" (raiton/suiton, sem tier 3 no kit) | 39,6–71,8 | 1,35–7,05 | 0,5–0,72 | 140–158 | 5,5–6,0 s |
| 3 | 54–86 | 9,0–11,9 | 0,18–0,37 | 175–245 | 7,0–9,0 s |

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
inalterados desde a rodada 2 — ver nota acima da tabela de escala por tier)

`doton_bala_lama` fecha a categoria "projétil básico" que faltava no elemento (os outros 3
jutsus de doton já existiam: muralha de pedra self, estacas de terra área, colapso do terreno
área forte). `fuuton_tornado_cortante` e `fuuton_redemoinho_prisao` fecham "beam/linha forte"
e "utilitário/controle" que faltavam em fuuton (só existiam projétil e área).

> **Atualizado na rodada 2**: `base_damage`/`level_scale`/`skill_scale` de 11 desses jutsus
> mudaram pra equilibrar o "valor total dos 4 jutsus pessoais" entre os 9 personagens (meta
> ±15%, ver `balanceamento-relatorio-v2.md` §7 — a tabela abaixo mantém os valores originais de
> quando cada jutsu foi criado; `data/jutsus/personal.json` é sempre a fonte da verdade).

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
