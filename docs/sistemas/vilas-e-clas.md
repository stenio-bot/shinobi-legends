# Sistema: Vilas e Clãs

## Vilas (escolha na criação — nomes provisórios, ver ADR-002)
| Vila | Elemento principal | Skill bônus (+20% ganho) | Jutsu inicial |
|---|---|---|---|
| Vila da Folha | Katon | Taijutsu | Katon: Bola de Fogo |
| Vila da Névoa | Suiton | Ninjutsu | Suiton: Projétil de Água |
| Vila da Nuvem | Raiton | Shuriken | Raiton: Agulha de Raio |
| Vila da Areia | Fuuton / Doton | Defesa | Fuuton: Lâmina de Vento |

Cada vila tem: cidade inicial, NPCs próprios, 1 área de caça 1–10 próxima, jutsus exclusivos (campo `villages` no jutsu).

## Mudança de vila
Não permitida no MVP. Futuro: quest cara que reseta jutsus exclusivos.

## Visual (outfits) por vila
Os personagens importados usam looktypes **fixos 900–926** (tabela em
`assets-src/sprites/mugen_looktypes.json`, gerada por outro agente). Nomes de personagens do
anime NÃO aparecem no jogo (ADR-002): os looktypes são só o visual; NPCs/monstros usam nomes
próprios, e os outfits jogáveis são nomeados como trajes genéricos (ex.: "Traje Genin Laranja"),
nunca com o nome do personagem original.

`data/tfs_mapping.json` (`villages.<id>.outfits`/`default_outfit`) decide quais looktypes cada
vila oferece na criação de personagem. `tools/export_tfs.py` gera:
- `server/generated/XML/outfits.xml` — as entradas `<outfit>` (type 0 e 1) com nome de traje.
- `server/generated/lib/naruto_villages.lua` — `NarutoVillages[vocation_id] = {name, default_outfit, outfits}`.
- `server/generated/scripts/naruto/village_outfit.lua` — revscript `onLogin` que, na primeira
  vez (storage 60000), aplica o outfit padrão da vila e libera (`addOutfit`) os demais outfits
  daquela vila para o jogador escolher depois.

| Vila | Outfits escolhíveis (looktype) | Outfit padrão |
|---|---|---|
| Folha | 900 (Traje Genin Laranja), 901 (Traje Genin Azul), 902 (Traje Genin Rosa) | 900 |
| Névoa | 903 (Traje Kunoichi Branco), 905 (Traje Marrom de Viajante) | 903 |
| Nuvem | 909 (Traje Listrado da Nuvem), 904 (Traje Verde de Treino) | 909 |
| Areia | 907 (Traje Amarelo do Sábio), 908 (Traje Branco Cerimonial) | 907 |

## Modos (transformações)
Looktypes **919–926** são reservados para **transformações do jogador** (não são inimigos, não
são escolhíveis na criação de personagem). Ideia de uso futuro: um jutsu tier 3 de "modo"
(equivalente a Sábio/Bijuu no anime, mas com nome próprio no jogo) que troca o outfit do
jogador temporariamente por um desses looktypes enquanto o efeito estiver ativo, revertendo ao
outfit normal quando expirar ou o jogador for nocauteado. Mecanicamente seria parecido com a
transformação dos bosses (`phases[].looktype` em `boss_phases.lua`), só que disparado por um
jutsu do próprio jogador em vez de uma fase de vida — **ainda não implementado**.

| Looktype | Sprite de origem (mugen_looktypes.json) |
|---|---|
| 919 | Naruto Sennin |
| 920 | Naruto KCM |
| 921 | Naruto 1 Calda |
| 922 | Naruto 4 Caldas |
| 923 | Naruto 6 Caldas |
| 924 | Naruto Ashura |
| 925 | Naruto Girl |
| 926 | Naruto Kid Fox |

## Clãs (Marco 4, multiplayer)
- Criados por jogador level 30+, custo em ryo.
- Até 50 membros, cargos (líder, oficial, membro).
- Chat de clã, XP bônus 5% em party do mesmo clã.
- Guerras de clã (Marco 5).

## Vila da Areia (id `sand`)
Implementada em `data/villages.json` (vocation 4 / town 4 no `tfs_mapping.json`).

- **Elementos:** Fuuton (ofensivo, alcance e corte) e Doton (controle e defesa).
- **Skill favorita (+20% de ganho):** Defesa. É a única vila cujo bônus não é ofensivo —
  a fantasia é o ninja que aguenta o hit e devolve com Doton.
- **Jutsu inicial:** `fuuton_lamina_vento` (projétil, tier 1, level 1).
- **Jutsus próprios (2 Fuuton + 3 Doton, tiers 1/1/2/2/3):**

| Jutsu | Elemento | Tier | Level | Forma |
|---|---|---|---|---|
| Fuuton: Lâmina de Vento | fuuton | 1 | 1 | projectile |
| Doton: Muralha de Pedra | doton | 1 | 8 | self (casca de rocha, regen 6/s por 6s) |
| Fuuton: Rajada Cortante | fuuton | 2 | 16 | area `cone_3` (slow) |
| Doton: Estacas de Terra | doton | 2 | 22 | area `cross_r2` (paralyze) |
| Doton: Colapso do Terreno | doton | 3 | 48 | area `circle_r2` (stun) |

No ciclo elemental (`katon > fuuton > raiton > doton > suiton > katon`) a Areia cobre dois
elos opostos: Fuuton bate forte em Raiton e Doton bate forte em Suiton — é a vila mais
flexível contra as áreas existentes, e a mais fraca contra Katon.

## Jutsus por vila (estado atual)
Cada vila tem **5 jutsus próprios** nos tiers 1, 1, 2, 2, 3, mais os neutros
(`kawarimi`, `bunshin`, `shousen`, `fuuin_contencao`, `doku_kiri`), disponíveis para todas.

| Vila | Tier 1 | Tier 1 | Tier 2 | Tier 2 | Tier 3 |
|---|---|---|---|---|---|
| Folha | Grande Bola de Fogo | Sopro de Brasas | Flores de Fênix | Anel de Chamas | Dragão de Fogo |
| Névoa | Projétil de Água | Névoa Cortante | Dragão de Água | Prisão de Água | Vórtice Devorador |
| Nuvem | Agulha de Raio | Corrente Estática | Lança do Relâmpago | Armadura Elétrica | Punho do Trovão |
| Areia | Lâmina de Vento | Muralha de Pedra | Rajada Cortante | Estacas de Terra | Colapso do Terreno |

> Nota de PI (ADR-002): nenhum jutsu usa nome registrado do anime. O antigo
> `raiton_chidori` / "Mil Pássaros" foi renomeado para `raiton_punho_trovao` /
> "Raiton: Punho do Trovão" e passou a ser exclusivo da Nuvem; o pergaminho virou
> `scroll_raiton_punho_trovao`.
