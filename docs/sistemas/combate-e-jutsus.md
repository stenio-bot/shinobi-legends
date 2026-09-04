# Sistema: Combate e Jutsus

## Fluxo de um ataque
1. Jogador seleciona alvo (clique) ou usa jutsu em direção/área.
2. Sistema verifica: alcance, linha de visão, cooldown, chakra.
3. Calcula dano → aplica → dispara eventos (`damage_dealt`, `entity_died`).
4. Efeitos (queimadura, lentidão) entram na lista de status do alvo.

## Fórmulas (todas em `damage_calc.gd`, sem estado)
```
dano_fisico  = (ataque_arma + skill_relevante * 0.5) * rand(0.8, 1.0) - defesa_alvo * 0.5
dano_jutsu   = (jutsu.base_damage + level * jutsu.level_scale + ninjutsu * jutsu.skill_scale)
               * multiplicador_elemental * rand(0.9, 1.1)
defesa_alvo  = soma(defesa dos itens) + skill_defesa * 0.3
crítico      = 5% base, dano * 1.5
```
Dano mínimo sempre 1.

## Elementos e afinidade
```
Katon (fogo)  > Fuuton (vento) > Raiton (raio) > Doton (terra) > Suiton (água) > Katon
```
Vantagem: ×1.5. Desvantagem: ×0.75. Neutro: ×1.0. Monstros têm `element` (ou `none`).

## Anatomia de um jutsu (`data/schemas/jutsu.schema.json`)
| Campo | Descrição |
|---|---|
| `id`, `name`, `description` | identidade |
| `element` | katon, suiton, doton, fuuton, raiton, none |
| `type` | `projectile`, `area`, `self`, `target`, `beam` |
| `shape` | para área: `circle_r1`, `cross_r2`, `line_5`, `cone_3`... |
| `range` | tiles |
| `chakra_cost`, `cooldown_s` | recurso e tempo |
| `base_damage`, `level_scale`, `skill_scale` | fórmula |
| `required_level`, `required_skill` | pré-requisito |
| `villages` | quem pode aprender (`[]` = todas) |
| `effects` | lista de status: `{type, chance, duration_s, value}` |
| `animation`, `sfx` | assets |

## Status (efeitos)
| Tipo | Efeito |
|---|---|
| `burn` | dano por segundo |
| `slow` | reduz velocidade |
| `stun` | não age por X s |
| `poison` | dano por segundo, stackável |
| `paralyze` | não move (pode usar jutsu) |
| `heal_over_time` | cura por segundo |

## Hotbar
10 slots (teclas 1–0 ou F1–F10). Jutsus e consumíveis. Cooldown visual.

## Formas de aprender jutsu
- Automático ao atingir level (jutsus básicos da vila).
- Comprar pergaminho de NPC (custo em ryo).
- Drop raro de boss (jutsus lendários).
