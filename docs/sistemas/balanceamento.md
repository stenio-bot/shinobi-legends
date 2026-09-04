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
Escala por tier (com `required_level` de referência e ninjutsu ≈ level+10):

| Tier | base_damage | level_scale | skill_scale | chakra | cooldown |
|---|---|---|---|---|---|
| 1 projétil | 20–25 | 1.1 | 0.8–0.9 | 12–16 | 1,5–2,0 s |
| 1 área/self | 14–18 | 0.9 | 0.6–0.7 | 16–28 | 2,5–3,0 s |
| 2 | 30–44 | 1.3–1.5 | 0.9–1.1 | 34–42 | 4,5–6,0 s |
| 3 | 70–90 | 2.0–2.2 | 1.2–1.3 | 60–72 | 7,0–9,0 s |

Regras que mantêm o tier 3 sendo o "show" sem virar obrigatório:
- **dano por chakra** cai de tier 1 (~1,7 dano/chakra) para tier 3 (~1,2), mas o
  **dano por cooldown** sobe — tier 3 é burst, tier 1 é sustentado.
- Formas de área custam ~30% mais chakra que um projétil de dano equivalente.
- Jutsus `self` não causam dano; o custo compra sobrevivência (`heal_over_time`).
- Multiplicador elemental (×1.5 / ×0.75) é aplicado **depois**, então uma vantagem
  elemental vale mais que subir um tier — isso é intencional e é o que faz o jogador
  trocar de jutsu por área em vez de spammar o mais caro.

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
