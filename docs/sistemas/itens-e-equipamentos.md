# Sistema: Itens e Equipamentos

## Slots de equipamento
`head`, `body`, `legs`, `feet`, `weapon`, `offhand`, `accessory1`, `accessory2`, `back` (mochila).

## Tipos de item (`type`)
| Tipo | Exemplos | Campos extras |
|---|---|---|
| `weapon` | kunai, katana, luvas | `attack`, `weapon_class` (melee/ranged), `skill` |
| `armor` | colete, bandana, sandálias | `defense`, `slot` |
| `accessory` | anel, colar, faixa | `bonuses` |
| `consumable` | poção de chakra, onigiri | `effect`, `stack_max` |
| `scroll` | pergaminho de jutsu | `teaches_jutsu` |
| `material` | pele de lobo, minério | crafting futuro |
| `currency` | ryo | — |

## Raridade (cor no inventário)
`common` (branco) · `uncommon` (verde) · `rare` (azul) · `epic` (roxo) · `legendary` (laranja)

## Bônus possíveis (`bonuses`)
`hp`, `chakra`, `speed`, `attack`, `defense`, `crit_chance`, `regen_hp`, `regen_chakra`,
`skill_taijutsu`, `skill_ninjutsu`, `skill_shuriken`, `skill_genjutsu`, `skill_defense`,
`element_damage_<elemento>`, `element_resist_<elemento>`.

## Requisitos
`required_level`, `required_village` (opcional), `required_skill` (`{skill, value}`).

## Inventário
- Mochila base: 20 slots. Mochilas maiores como item `back`.
- Peso: cada item tem `weight`; capacidade = `100 + level*5 + bônus`. Acima disso: não anda.
- Stack até `stack_max` (padrão 1 para equipamentos, 100 para consumíveis/materiais).

## Economia (resumo, ver economia.md)
Moeda: **ryo**. Itens têm `buy_price` (NPC vende) e `sell_price` (NPC compra, ~40% do buy).

## Escada de arma melee L1-L40 (rodada 10 de balanceamento)

Degraus a cada ~5 níveis, calibrados com `tools/balance/sim.py` para que taijutsu puro chegue
o mais perto possível de 70% do DPS híbrido nos níveis 5-40 sem quebrar o burst do jutsu tier 1
(`≥1,3× o hit de arma`, ver `balanceamento.md` §6) nem encurtar demais o TTK dos bosses de
referência L12/L19/L25 (meta 60-180s). Ver `docs/sistemas/balanceamento-relatorio-v10.md` para
o processo completo e os números antes/depois.

| Nível | Item | Attack | Vendedor | Preço (buy/sell) |
|---|---|---|---|---|
| 1 | `kunai_iron` | 8 | Ichiro (Folha) | 50 / 20 |
| 5 | `adaga_genin` (novo) | 18 | Ichiro (Folha) · Mercador Itsuki (Costa) | 200 / 80 |
| 8 | `tanto_steel` | 17 (era 16) | Ichiro (Folha) | 400 / 160 |
| 10 | `gloves_taijutsu` | 18 (era 14) | Ichiro (Folha) — **novo**: antes existia no catálogo mas não era vendida em nenhum NPC | 1.200 / 480 |
| 15 | `wakizashi_temperado` | 27 (era 21) | Velha Sumi (Floresta) · Mercador Itsuki (Costa) | 1.800 / 720 |
| 20 | `katana_ronin` | 34 (era 28) | Velha Sumi (Floresta) · Mercador Itsuki (Costa) | 2.500 / 1.000 |
| 25 | `espadao_de_aco` (novo) | 54 | Velha Sumi (Floresta) · Mercador Itsuki (Costa) | 5.000 / 2.000 |
| 28 | `kodachi_ruins` | 58 (era 40) | Tsubaki (Ruínas) | 6.200 / 2.480 |
| 30 | `katana_aprimorada` (novo) | 66 | Tsubaki (Ruínas) | 7.200 / 2.880 |
| 35 | `puppet_blade` | 70 (era 52) | Tsubaki (Ruínas) | 9.800 / 3.920 |
| 40 | `adaga_sombria` | 70 (era 54) | (drop do Xamã da Maldição, sem NPC — ver `progressao-jogador.md`) | 12.800 / 5.120 |

Preço segue a fórmula de `balanceamento.md` §5 (`8 * required_level²`), sem alteração — só o
`attack` mudou nos itens já existentes. Custo pago em bem menos de 1,5h de loot da região no
level do item em todos os degraus (ver relatório v10 §2, folga de 5x-25x). `tanto_steel`,
`gloves_taijutsu` e `wakizashi_temperado` receberam um attack MENOR do que o simulador indicava
como ótimo pra viabilidade pura, de propósito — um valor maior encurtava demais o TTK híbrido
dos bosses L12 (Chefe dos Bandidos) e L19 (Espadachim da Névoa), violando a meta de 60-180s;
ver relatório v10 §4 para os números da troca.

## Mapeamento para o TFS (ids vanilla)
Todo item de `data/items/*.json` precisa de uma entrada em `data/tfs_mapping.json` (seção
`items`: nosso id → id vanilla do Tibia 10.98, do mesmo tipo/slot — arma→arma, armadura
corporal→body, capacete→head, pernas→legs, botas→feet, anel/colar→acessório,
material→material/troféu). O `tools/export_tfs.py` usa esse id como placeholder e emite o
item em `server/generated/items/items_naruto.xml` com **nosso** nome/atributos, sobrescrevendo
o item vanilla original (`server/tfs/data/items/items.xml`); troque o id quando houver sprite
próprio (ObjectBuilder) e regenere. `tools/check_mapping.py` falha (exit 1) se algum item ficar
sem entrada no mapping ou se dois itens nossos reaproveitarem o mesmo id vanilla — rode-o junto
com `tools/validate_data.py` sempre que adicionar itens novos.
