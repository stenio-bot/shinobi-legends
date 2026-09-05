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

## Personagens e jutsus

A VILA continua sendo a vocação/facção (Folha, Névoa, Nuvem, Areia): decide town, elemento
principal, skill bônus e quais outfits (looktype 900–909) o jogador pode escolher. Dentro da
vila, cada OUTFIT agora é um **PERSONAGEM** com seu próprio conjunto fixo de jutsus (estilo
NTO Ultimate, onde a vocação = o personagem escolhido) — trocar de personagem troca a barra de
jutsus junto, sem mudar de vila.

Fonte de verdade: `data/characters.json` (schema em `data/schemas/character.schema.json`).
Cada entrada tem `id`, `name` (nome próprio, nunca do anime — ADR-002), `looktype` (900–909),
`village` e uma lista ORDENADA de 5–8 `jutsus` (ids de `data/jutsus/*.json`, que precisam
pertencer à `village` do personagem ou ser universais — `villages: []`).

| id | Nome | Vila | Looktype | Jutsus |
|---|---|---|---|---|
| `genin_laranja` | Genin Laranja | Folha | 900 | Fuuton: Lâmina de Vento, Kawarimi no Jutsu, Bunshin no Jutsu, Clone Sombrio, Fuuton: Rajada Cortante |
| `genin_uchiha` | Genin Uchiha | Folha | 901 | Katon: Grande Bola de Fogo, Raiton: Agulha de Raio, Katon: Sopro de Brasas, Raiton: Corrente Estática, Katon: Flores de Fênix, Katon: Dragão de Fogo |
| `kunoichi_rosa` | Kunoichi Rosa | Folha | 902 | Punho Suave, Kawarimi no Jutsu, Bunshin no Jutsu, Shousen: Palma Curativa, Chute Giratório |
| `herdeira_hyuga` | Herdeira Hyuga | Névoa | 903 | Suiton: Projétil de Água, Suiton: Névoa Cortante, Suiton: Prisão de Água, Suiton: Dragão de Água, Suiton: Vórtice Devorador, Fuuin: Selo de Contenção |
| `kunoichi_armas` | Kunoichi das Armas | Névoa | 905 | Agulhas Múltiplas, Kawarimi no Jutsu, Suiton: Névoa Cortante, Lâmina de Chakra, Doku: Névoa Venenosa |
| `ninja_verde` | Ninja Verde | Nuvem | 904 | Punho Suave, Kawarimi no Jutsu, Bunshin no Jutsu, Doton: Muralha de Pedra, Chute Giratório |
| `ninja_abelha` | Ninja Abelha | Nuvem | 909 | Raiton: Agulha de Raio, Raiton: Corrente Estática, Raiton: Lança do Relâmpago, Raiton: Armadura Elétrica, Raiton: Punho do Trovão |
| `sabio_loiro` | Sábio Loiro | Areia | 907 | Fuuton: Lâmina de Vento, Raio Selado, Kawarimi no Jutsu, Fuuton: Rajada Cortante, Doton: Estacas de Terra |
| `sabio_cerimonial` | Sábio Cerimonial | Areia | 908 | Fuuton: Lâmina de Vento, Doton: Muralha de Pedra, Fuuton: Rajada Cortante, Doton: Estacas de Terra, Doton: Colapso do Terreno |

Jutsus novos criados para fechar identidades sem elemento suficiente (nomes próprios,
`data/jutsus/neutral.json` e `raiton.json`):

| id | Nome | Tipo | Skill | Vilas |
|---|---|---|---|---|
| `clone_sombrio` | Clone Sombrio | self | genjutsu | universal |
| `punho_suave` | Punho Suave | target | taijutsu | Folha, Nuvem |
| `chute_giratorio` | Chute Giratório | area | taijutsu | Folha, Nuvem |
| `agulhas_multiplas` | Agulhas Múltiplas | projectile | shuriken | Névoa |
| `lamina_chakra` | Lâmina de Chakra | beam | shuriken | Névoa |
| `raio_selado` | Raio Selado | projectile (raiton) | ninjutsu | Areia |

Também foram ampliados os `villages` de alguns jutsus tier 1 já existentes para dar acesso
elemental a personagens "hibridos" (ex.: `raiton_hari`/`raiton_corrente_estatica` ganharam
Folha para o Genin Uchiha; `fuuton_lamina_vento`/`fuuton_rajada_cortante` ganharam Folha para
o Genin Laranja; `doton_muralha_pedra` ganhou Nuvem para o Ninja Verde). Isso só amplia QUEM
PODE aprender o jutsu (a checagem em `data/villages.json`/GM); quem efetivamente o conhece em
cada momento é sempre o personagem ativo.

### Servidor
- Todo jutsu passa a ter `needlearn="1"` no `spells.xml`, **exceto `kawarimi`** (universal,
  toda vila conhece — é a "esquiva básica"). Sem aprender, o servidor recusa o cast com
  "You must learn this spell first.".
- `server/generated/lib/naruto_characters.lua` (`NarutoCharacters`): tabela `list`/`byLook`/
  `byId`/`byVillage`/`allJutsuNames`, gerada de `data/characters.json`.
- `server/generated/scripts/naruto/character_switch.lua`: define `NarutoCharacters.apply(player,
  looktype, opts)` — valida vila (a menos que `opts.force` ou o jogador seja GM), esquece os
  jutsus de TODOS os personagens (exceto universais) e aprende só os do personagem escolhido,
  troca o `lookType` do outfit, salva `storage 60001` e avisa "Personagem: X. Jutsus: ...".
  Um `CreatureEvent onLogin` reaplica pelo storage a cada login. Talkaction `!personagem
  [nome|id]` para jogadores (lista/troca só dentro da própria vila).
- `village_outfit.lua` agora aplica, no primeiro login, o PRIMEIRO personagem de
  `characters.json` daquela vila (via `NarutoCharacters.apply`) em vez de só `setOutfit`.
- `/personagem <id|nome>` no `gm_tools.lua` troca para qualquer personagem (ignora vila);
  `/jutsus` e `/god` passam a aprender só os jutsus do personagem atual (não todos).

### Cliente
- `tools/export_tfs.py` gera `NarutoCharacterJutsus[looktype] = {id, name, village, words}` em
  `client-otc/modules/naruto_theme/jutsus_data.lua`.
- `naruto_jutsus.lua`: `fillActionBarForCharacter(looktype)` preenche a barra inferior 1 com os
  jutsus daquele personagem (um conjunto de hotkeys por `id` do personagem, nome ASCII),
  chamada em `onGameStart` e em `onOutfitChange` do `LocalPlayer` (via `connect(Creature,
  {onOutfitChange = ...})`, filtrando pelo jogador local). A Lista de Jutsus (spelllist)
  continua filtrando por vila/vocação, sem mudanças.

### Achado colateral
Nenhum jutsu tinha `spellid` explícito no `spells.xml` — o TFS 1.4.2 usa `0` como padrão para
TODOS (`spells.h: uint8_t spellId = 0`), então o cooldown de QUALQUER jutsu bloqueava todos os
outros (grupo diferente ou não) por engano. `tools/export_tfs.py` agora emite `spellid`
sequencial único por jutsu — corrigido junto com esta feature, pois mascarava os testes.
