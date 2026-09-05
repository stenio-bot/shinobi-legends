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
