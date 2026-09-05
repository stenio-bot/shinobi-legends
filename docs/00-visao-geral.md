# 00 — Visão geral (GDD resumido)

> **Documento mãe:** para a visão completa do jogo — mundo, história, progressão, sistemas,
> bestiário, grimório de jutsus e estado atual — ver [`docs/00-biblia-do-jogo.md`](00-biblia-do-jogo.md).

## Pitch
Um MMORPG 2D onde você cria um ninja, escolhe uma vila, e evolui caçando monstros,
aprendendo jutsus, subindo skills e equipando itens. A sensação alvo é a do
**Narutibia / NTO**: grind satisfatório, jutsus com visual marcante, drop raro
que vale a pena, e progressão que dura meses.

## Pilares de design
1. **Grind com propósito** — cada caçada dá XP, skill e chance de drop. Nada é "vazio".
2. **Identidade de build** — vila + elemento + skills tornam cada ninja diferente.
3. **Jutsus são o show** — a hora de soltar o jutsu tem que ser o momento mais gostoso.
4. **PvM primeiro** — PvP e guerras de clã vêm depois e são opcionais.

## Loop principal
```
Escolher caça → Ir até o spot → Matar monstros (usar jutsus, gerenciar HP/Chakra)
   ↑                                              ↓
Comprar/craftar itens ← Voltar à vila ← Coletar drop / subir level e skills
```

## Fantasia do jogador
"Comecei como genin fraco com uma kunai e hoje sou um jounin com Rasengan
caçando bosses com meu clã."

## Escopo do MVP (Marco 1–2)
- 1 vila, 1 mapa de caça com 3 tipos de monstro, 1 boss.
- Personagem com HP, Chakra, Level, 5 skills.
- 6 jutsus (2 por elemento inicial: Katon, Suiton, Raiton).
- 15 itens (armas, armaduras, consumíveis).
- Save local. Sem multiplayer.

## Fora do escopo (por enquanto)
Multiplayer, PvP, clãs, mercado entre jogadores, quests com diálogo ramificado,
crafting complexo. Tudo isso está no roadmap, mas depois do MVP jogável.
