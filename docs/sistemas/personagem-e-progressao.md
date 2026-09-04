# Sistema: Personagem e Progressão

## Atributos base
| Atributo | Descrição | Fórmula base |
|---|---|---|
| HP | Vida | `100 + level*15 + vitalidade*5` |
| Chakra | Recurso de jutsus | `50 + level*10 + espirito*5` |
| Velocidade | tiles/s | `4 + bônus de itens` |
| Regen HP | por 5s | `2 + level*0.2` (dobra comendo) |
| Regen Chakra | por 5s | `3 + level*0.3` |

## Level e XP
- Level máximo inicial: 100 (expandir depois).
- XP necessária por level em `data/progression.json` (curva quadrática suave:
  `50 * level^2 + 50 * level`).
- XP de monstro = `xp_base` do monstro, sem penalidade de level (evita "cair de level").
- Ao morrer: perde 10% da XP do level atual (nunca cai de level), dropa itens
  não-equipados com 30% de chance cada (regra estilo Tibia, ajustável).

## Skills (sobem com uso, não com pontos)
| Skill | Sobe quando | Efeito |
|---|---|---|
| Taijutsu | Acerta ataque corpo a corpo | + dano físico melee |
| Shuriken | Acerta ataque à distância | + dano físico ranged |
| Ninjutsu | Usa jutsu elemental | + dano de jutsu |
| Genjutsu | Usa jutsu de controle | + duração/chance de efeitos |
| Defesa | Bloqueia/recebe hit com escudo/armadura | reduz dano recebido |

- Skill começa em 10, máximo 150.
- Cada acerto dá 1 ponto de "tentativa". Pontos para subir = `50 * 1.1^(skill-10)`.
- Skill de vila favorita sobe 20% mais rápido (ver `vilas-e-clas.md`).

## Vilas (escolha na criação)
Definem jutsus iniciais e bônus de skill. Ver `vilas-e-clas.md`.

## Ranks (título, cosmético + desbloqueios)
Genin (1) → Chuunin (20) → Jounin (50) → Anbu (80) → Kage (100).
Cada rank desbloqueia um tier de jutsus e uma área.

## Save (fase 1)
`user://save_slot_N.json` com: atributos, level, xp, skills, inventário,
equipamento, jutsus aprendidos, posição, vila, flags de missão.
