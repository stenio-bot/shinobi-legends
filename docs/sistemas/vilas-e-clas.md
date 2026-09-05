# Sistema: Vilas e Clãs

## Vilas (escolha na criação — nomes provisórios, ver ADR-002)
| Vila | Elemento principal | Skill bônus (+20% ganho) | Jutsu inicial |
|---|---|---|---|
| Vila da Folha | Katon | Taijutsu | Katon: Bola de Fogo |
| Vila da Névoa | Suiton | Ninjutsu | Suiton: Projétil de Água |
| Vila da Nuvem | Raiton | Shuriken | Raiton: Agulha de Raio |
| Vila da Areia | Fuuton / Doton | Defesa | Fuuton: Lâmina de Vento |

Cada vila tem: cidade inicial, NPCs próprios, 1 área de caça 1–10 próxima. **Vila não filtra
mais jutsu** (ver "Personagem + Elemento: 4 + 4" em `docs/sistemas/combate-e-jutsus.md`): o
campo `villages` de todo jutsu em `data/jutsus/*.json` está vazio (`[]`), e o kit de combate do
jogador vem só do PERSONAGEM (identidade) + ELEMENTO (escolha livre), não da vila.

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

## Jutsus por elemento (histórico → ver "sets" atuais)
As tabelas abaixo mostram os jutsus que cada elemento acumulou ao longo do desenvolvimento.
No modelo atual (Personagem + Elemento), o que o jogador realmente recebe ao escolher um
elemento são só os **4 jutsus do set** em `data/element_sets.json` — ver a tabela em
"Personagens e jutsus" abaixo e a seção "Personagem + Elemento: 4 + 4" de
`docs/sistemas/combate-e-jutsus.md`. Os jutsus elementais que ficaram de fora do set (ex.:
`katon_sopro_brasas`, `suiton_vortice_devorador`, `raiton_punho_trovao`) continuam válidos em
`data/jutsus/*.json` (podem virar loot/pergaminho de bônus no futuro), só não fazem parte do
kit automático.

| Elemento | Jutsus existentes (tiers) |
|---|---|
| Katon | Grande Bola de Fogo (1), Sopro de Brasas (1), Flores de Fênix (2), Anel de Chamas (2), Dragão de Fogo (3) |
| Suiton | Projétil de Água (1), Névoa Cortante (1), Dragão de Água (2), Prisão de Água (2), Vórtice Devorador (3) |
| Raiton | Agulha de Raio (1), Corrente Estática (1), Lança do Relâmpago (2), Armadura Elétrica (2), Punho do Trovão (3) |
| Doton | Bala de Lama (1), Muralha de Pedra (1), Estacas de Terra (2), Colapso do Terreno (3) |
| Fuuton | Lâmina de Vento (1), Rajada Cortante (2), Redemoinho Prisão (2), Tornado Cortante (3) |

> Nota de PI (ADR-002): nenhum jutsu usa nome registrado do anime. O antigo
> `raiton_chidori` / "Mil Pássaros" foi renomeado para `raiton_punho_trovao` /
> "Raiton: Punho do Trovão"; o pergaminho virou `scroll_raiton_punho_trovao`.

## Personagens e jutsus (Personagem + Elemento)

A VILA agora é só vocação/town: decide cidade inicial, NPCs, elemento "de referência" e a
skill bônus — **não filtra mais jutsu**. Dentro da vila, cada OUTFIT (looktype 900–909) é um
**PERSONAGEM** com identidade fixa de 4 jutsus **pessoais** (`personal_jutsus`, não
elementais). Ao entrar no jogo o jogador escolhe PERSONAGEM + ELEMENTO e recebe, no nível
máximo, os 4 pessoais + os 4 do elemento (`data/element_sets.json`) — 8 jutsus, prontos, sem
precisar caçar level nem aprender nada depois. A progressão vira treino físico (level, skills),
não aprendizado de jutsu.

Fonte de verdade: `data/characters.json` (schema em `data/schemas/character.schema.json`).
Cada entrada tem `id`, `name` (nome próprio, nunca do anime — ADR-002), `description` (1 frase
de identidade), `looktype` (900–909), `village`, `default_element` (sugestão inicial, o
jogador pode trocar) e `personal_jutsus`: lista ORDENADA de **exatamente 4** ids de
`data/jutsus/*.json`, todos com `villages: []`.

| id | Nome | Descrição | Vila | Elemento padrão | Jutsus pessoais |
|---|---|---|---|---|---|
| `genin_laranja` | Genin Laranja | Genin barulhento e teimoso que nunca desiste de um combate | Folha | Fuuton | Clone Sombrio, Kawarimi no Jutsu, Rasteira de Vento Leve, Vigor Teimoso |
| `genin_uchiha` | Genin Uchiha | Genin frio e calculista, treinado para prever cada golpe do adversário | Folha | Katon | Foco Ocular, Agulhas Incendiárias, Contra-Ataque Calculado, Kawarimi no Jutsu |
| `kunoichi_rosa` | Kunoichi Rosa | Médica-ninja de força descomunal e socos que racham o chão | Folha | Suiton | Shousen: Palma Curativa, Punho Suave, Soco Monstruoso, Kawarimi no Jutsu |
| `herdeira_hyuga` | Herdeira Hyuga | Herdeira de um clã ocular, ataca pontos vitais de chakra com precisão cirúrgica | Névoa | Suiton | Palma Gentil, Fuuin: Selo de Contenção, Visão de Alcance Total, Palma Dupla |
| `kunoichi_armas` | Kunoichi das Armas | Especialista em armas arremessadas, cobre o campo com lâminas e veneno | Névoa | Suiton | Agulhas Múltiplas, Lâmina de Chakra, Doku: Névoa Venenosa, Bunshin no Jutsu |
| `ninja_verde` | Ninja Verde | Taijutsuísta puro que compensa a falta de chakra com força bruta e disciplina | Nuvem | Raiton | Punho Suave, Chute Giratório, Soco da Juventude, Chute Ascendente |
| `ninja_abelha` | Ninja Abelha | Espadachim elétrico, rápido e obcecado por evoluir a cada combate | Nuvem | Raiton | Lâmina Relâmpago, Corte Duplo, Bainha Elétrica, Raio Selado |
| `sabio_loiro` | Sábio Loiro | Sábio errante que domina selos de teleporte e ataques cirúrgicos à distância | Areia | Fuuton | Kawarimi no Jutsu, Kunai Marcada, Salto do Selo, Explosão do Selo |
| `sabio_cerimonial` | Sábio Cerimonial | Sábio cerimonial que protege aliados com barreiras e selos sagrados | Areia | Doton | Fuuin: Selo de Contenção, Barreira Protetora, Selo de Exorcismo, Círculo de Selos |

`kawarimi`, `punho_suave` e `fuuin_contencao` aparecem em mais de um personagem (no máximo 2
cada) — são movimentos genéricos o bastante (substituição, golpe de chakra, selo de papel)
para caber em identidades diferentes sem quebrar a fantasia de nenhuma delas.

Jutsus pessoais novos criados para fechar as identidades (`data/jutsus/personal.json`, todos
`villages: []`, `element` = `none` ou o elemento de sabor do personagem — não fazem parte de
nenhum `element_sets.json`):

| id | Nome | Elemento | Tipo | Personagem |
|---|---|---|---|---|
| `fuuton_rasteira_vento` | Rasteira de Vento Leve | fuuton | area | Genin Laranja |
| `vigor_teimoso` | Vigor Teimoso | none | self | Genin Laranja |
| `foco_ocular` | Foco Ocular | none | self | Genin Uchiha |
| `agulhas_incendiarias` | Agulhas Incendiárias | katon | projectile | Genin Uchiha |
| `contra_ataque_calculado` | Contra-Ataque Calculado | none | target | Genin Uchiha |
| `soco_monstruoso` | Soco Monstruoso | none | target | Kunoichi Rosa |
| `palma_gentil` | Palma Gentil | none | target | Herdeira Hyuga |
| `visao_total` | Visão de Alcance Total | none | self | Herdeira Hyuga |
| `palma_dupla` | Palma Dupla | none | area | Herdeira Hyuga |
| `soco_da_juventude` | Soco da Juventude | none | target | Ninja Verde |
| `chute_ascendente` | Chute Ascendente | none | target | Ninja Verde |
| `lamina_relampago_pessoal` | Lâmina Relâmpago | raiton | target | Ninja Abelha |
| `corte_duplo` | Corte Duplo | none | area | Ninja Abelha |
| `bainha_eletrica` | Bainha Elétrica | raiton | self | Ninja Abelha |
| `kunai_marcada` | Kunai Marcada | none | projectile | Sábio Loiro |
| `salto_do_selo` | Salto do Selo | none | self | Sábio Loiro |
| `explosao_do_selo` | Explosão do Selo | none | area | Sábio Loiro |
| `barreira_protetora` | Barreira Protetora | none | self | Sábio Cerimonial |
| `selo_de_exorcismo` | Selo de Exorcismo | none | target | Sábio Cerimonial |
| `circulo_de_selos` | Círculo de Selos | none | area | Sábio Cerimonial |

`raio_selado` (projétil de precisão, antes em `data/jutsus/raiton.json` com `villages:
["sand"]`) virou pessoal do Ninja Abelha e mudou de arquivo para `data/jutsus/personal.json`
(mesmo id, mesmos números, `villages: []`).

### Compatibilidade com o exportador
`tools/export_tfs.py` já lê `personal_jutsus` (com fallback para o campo legado `jutsus`) e
`data/element_sets.json`; por segurança, `characters.json` também grava um campo `jutsus` com
o MESMO conteúdo de `personal_jutsus` em cada personagem (não editar um sem o outro —
`tools/validate_data.py` acusa erro se divergirem).

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
