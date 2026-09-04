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
