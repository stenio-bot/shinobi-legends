# Sistema: Mapas (OTBM)

O mapa jogável do Shinobi Legends é um **OTBM** carregado pelo TFS 1.4.2 e editável no
**Remere's Map Editor**. Ele NÃO é gerado por `tools/export_tfs.py`: existe um pipeline
próprio em `tools/map/`, porque geometria de mapa não cabe em `data/*.json`.

| Arquivo | Papel |
|---|---|
| `tools/map/otbm.py` | leitor/gravador de OTBM (nós OTB, tiles, itens, towns, waypoints, house tiles) |
| `tools/map/items_otb.py` | leitor mínimo do `items.otb` (valida ids, grupo `ground`, flag de bloqueio) |
| `tools/map/spawn_xml.py` | gravador de `<mapa>-spawn.xml` e de `<mapa>-house.xml` vazio |
| `tools/map/build_valley.py` | gerador do mapa "Vale da Folha" |
| `server/generated/world/valley.otbm` | mapa gerado (não editar à mão) |
| `server/generated/world/valley-spawn.xml` | spawns de monstros e NPCs |
| `server/generated/world/valley-house.xml` | vazio e válido (o mapa não tem casas compráveis) |

## Formato OTBM (resumo)

```
"OTBM" ou \0\0\0\0            identificador (4 bytes)
0xFE <tipo> <props> [filhos] 0xFF     nó; 0xFD escapa 0xFD/0xFE/0xFF dentro de <props>

ROOT (tipo 0)        props: version(u32) width(u16) height(u16) major(u32) minor(u32)
  OTBM_MAP_DATA      props: DESCRIPTION / EXT_SPAWN_FILE / EXT_HOUSE_FILE
    OTBM_TILE_AREA   props: x(u16) y(u16) z(u8)  — blocos de 256x256 por andar
      OTBM_TILE      props: dx(u8) dy(u8) [ATTR_TILE_FLAGS] [ATTR_ITEM = chão]
      OTBM_HOUSETILE props: dx dy houseid(u32) …
        OTBM_ITEM    props: id(u16) + atributos (COUNT, ACTION_ID, UNIQUE_ID, TEXT,
                            TELE_DEST, DEPOT_ID, HOUSEDOORID, CHARGES, …)
    OTBM_TOWNS -> OTBM_TOWN        id(u32) nome(str) x(u16) y(u16) z(u8)
    OTBM_WAYPOINTS -> OTBM_WAYPOINT nome(str) x y z
```

Referência no código do servidor: `server/tfs/src/iomap.cpp`, `iomap.h` e `fileloader.cpp`.

`otbm.py` guarda os atributos de item como bytes crus na ordem original, então a
leitura + reescrita de um mapa é **fiel** (mesmo número de tiles, itens, flags,
house tiles, towns e waypoints).

## Layout do Vale da Folha

Cabeçalho 2048x2048 (OTBM v2, items 3.57). Conteúdo jogável no **andar 7**, em
duas faixas: o mundo aberto **x 1000–1199, y 1000–1119** (200x120 = 24.000
tiles) e um apêndice isolado (interiores de loja + Arena do Exame Chunin) em
**x 1298–1332, y 998–1036**, ligado ao mundo aberto só por teleporte.

> O cabeçalho declara 2048x2048 e não 1024x1024 porque o conteúdo vai até
> x=1329: o TFS ignora `width`/`height`, mas o Remere's usa esses valores para
> delimitar o canvas e recortaria tudo acima de 1023.

### Mapa v2 (2026-09-04) — por que mudou

Feedback do usuário sobre a v1: "o mapa está todo desengonçado; não sei o que é
estrada, o que é lugar, loja; precisa de lógica". A v1 tinha as 3 lojas
espalhadas em 3 pontos diferentes da vila (2 delas nem na mesma rua), sem
interior (NPC parado na rua, na frente de uma fachada que só bloqueia), sem
placas explicando o que é cada coisa, e só 1 portão. A v2 resolve isso:

- **Um único portão principal** (sul, com torii vermelho) leva à avenida
  N-S, que atravessa a praça e termina na Torre do Hokage — exatamente o eixo
  "portão → praça → prédio principal" de uma cidade Tibia clássica.
- **Um segundo portão** (leste) abre direto na **Rua dos Mercadores**, que
  agora tem as 3 lojas **lado a lado, na mesma rua**, cada uma com uma placa.
- **Lojas têm INTERIOR de verdade**: a fachada (bloqueia tudo, só a porta é
  passável) ganhou uma sala separada em outro trecho do mapa (x 1300+, ver
  "Interiores"), com o NPC atrás de um balcão, ligada por **teleporte na
  própria célula da porta** — visualmente o jogador "entra pela porta".
- **Sinalização**: placa de madeira (item 1440) em toda rua, portão, loja,
  bairro e bifurcação de trilha — "Rua dos Mercadores", "Portão Leste →
  trilha da floresta", "-> Trilha dos Lobos", etc.
- **Muralha com 2 portões nomeados**, academia cercada de bambu, Floresta da
  Morte cercada (bambu alto, 1 portão na ponte) e uma **Arena do Exame
  Chunin** nova (30x20, arquibancada de bancos, teleporte de entrada na
  Academia).

Como não existe NPC "Guarda da Folha" em `data/npcs/` (regra da missão: só
usar se já existisse), os portões são sinalizados por placa + tochas, sem
guarda.

### Planta lógica da vila (declarativo, ver `tools/map/build_valley.py`)

O gerador foi refeito em **funções por bairro**, cada uma cuidando de um
pedaço (chamadas em sequência de dentro de `build()`): muralha+portões, ruas+
praça+templo, torre do Hokage, bairro residencial, Rua dos Mercadores
(fachadas), bloco cívico (taverna/prisão), Academia+cerca, decoração, muro da
Floresta da Morte, placas de trilha, interiores das lojas, Arena. A planta
abaixo é o "mapa lógico" em texto (cada célula ≈ 1 tile, y 1030→1069 de cima
pra baixo, x 1010→1049 da esquerda pra direita); os detalhes finos (porta
exata, decoração) ficam nas funções, não neste desenho:

```
legenda: # muralha   G portão   R rua (cobble)   P praça (pedra)
         T templo    H torre Hokage   S loja (fachada+porta)
         D casa (residencial)   A academia (cercada de bambu)
         V depósito   K taverna/prisão   . terra batida

##################G(leste)#######
#  D          H(torre)      D    #
#  D        ###########     S,S,S# <- Rua dos Mercadores (loja, loja, loja)
#            #P  T  P#      ,,,, #    (R = rua leste-oeste, y1054-1056)
#  A(cerca)  #P     P#       .   #
#  A         ###door##       .   #
#  A          ..R..           .  #
#..........R.R.R.R.R..............#  <- Rua dos Mercadores continua
#            R                    #
#  K    D    K,K   D              #
#  (prisão)  (taverna)             #
##########G(sul, torii)############
```

### Pontos de referência

| Lugar | Coordenadas (x, y, 7) |
|---|---|
| **Templo / posição da town 1 "Vila da Folha"** | **1029, 1042** |
| Prédio do templo (paredes de pedra) | 1025,1038 – 1033,1046, porta em 1029,1046 |
| Praça central (chão de pedra, zona de proteção) | 1022,1036 – 1036,1052 |
| Fonte da praça / bancos | 1029,1049 / 1027,1050·1031,1050·1029,1048 |
| Muralha da vila | 1010,1030 – 1049,1069 |
| **Portão Sul** (principal, torii vermelho) | 1028–1030, 1069 |
| **Portão Leste** (Rua dos Mercadores) | 1049, 1054–1056 |
| Avenida norte-sul (cobblestone) | x 1028–1030 |
| **Rua dos Mercadores** (leste-oeste, cobblestone) | y 1054–1056 |
| Torre do Hokage (prédio importado) | 1027,1031 – 1031,1036, porta em 1029,1036 |
| Bairro residencial (norte + sul) | y 1031–1036 (`big_house`, `house_green`) e y 1060–1063 (`blue_house` x2) |
| Loja do Ichiro, o Mercador (`newbie_shop`) | fachada 1037,1050–1040,1053, porta/teleporte em 1038,1053 |
| Loja do Mestre Hayato (`ramen_shop`) | fachada 1042,1049–1045,1053, porta/teleporte em 1044,1053 |
| Loja da Capitã Rin (`blue_shop`) | fachada 1046,1050–1048,1053, porta/teleporte em 1047,1053 |
| Prisão | 1013,1060 – 1016,1063, porta em 1014,1063 |
| Taverna | 1032,1059 – 1036,1063, porta em 1034,1063 |
| Academia Ninja / campo de treino (cercada de bambu, 6 dummies) | 1013,1046 – 1020,1052, entrada sul em 1016-1017,1053 |
| Teleporte Academia → Arena | 1020,1049 → 1314,1033 |
| Depósito (depot chest) | 1024, 1051 |
| Rio (norte-sul, intransponível) | x 1125–1129 |
| **Ponte de madeira** (com corrimão) | x 1124–1130, y 1058–1061 |
| **Muro da Floresta da Morte** (cerca de bambu, 1 portão) | perímetro x1130/x1199,y1000/y1119; portão y1057–1062 |
| Hub de NPCs do pântano | 1131,1055 – 1139,1064 |
| Velha Sumi / Rastreador Goro | 1133,1057 / 1135,1058 |
| **Torre de pedra** (interior 3x3) | 1163,1058 – 1167,1062, porta em 1163,1060 |
| Boss Sapo Ancião (dentro da torre) | 1165, 1060 |
| **Acampamento dos bandidos** | centro 1100, 1100 (raio 7) |
| Boss Chefe dos Bandidos | 1100, 1100 |
| **Interior — Ichiro** | 1300,1000 – 1306,1005 |
| **Interior — Hayato** | 1310,1000 – 1317,1005 |
| **Interior — Rin** | 1320,1000 – 1325,1005 |
| **Arena do Exame Chunin** (30x20) | 1300,1015 – 1329,1034, centro 1314,1024 |
| Instrutora Ibuki (proctora do exame, Academia) | 1018,1048 |
| Rivais do Exame (Pedra/Som/Névoa, 2 cada, na Arena) | em torno de 1314,1024 |

Waypoints gravados no OTBM: `Templo`, `Praca`, `Portao Sul`, `Portao Leste`,
`Rua dos Mercadores`, `Academia`, `Ponte`, `Torre`, `Acampamento`,
`Hub Pantano`, `Arena Chunin`, `Muro Floresta da Morte`.

### Lojas: NPC + interior

| Loja | NPC | Fachada (rua) | Interior | Teleporte |
|---|---|---|---|---|
| Loja de Armas (`newbie_shop`) | Ichiro, o Mercador | 1037-1040,1050-1053 | 1300-1306,1000-1005 | entrada empilhada na porta (1038,1053); saída no pad dentro da sala → 1038,1054 (rua) |
| Loja de Pergaminhos (`ramen_shop`) | Mestre Hayato | 1042-1045,1049-1053 | 1310-1317,1000-1005 | entrada em 1044,1053; saída → 1044,1054 |
| Quartel/Missões (`blue_shop`) | Capitã Rin | 1046-1048,1050-1053 | 1320-1325,1000-1005 | entrada em 1047,1053; saída → 1047,1054 |

Cada interior: chão de tatame (`tatami_floor`), paredes de madeira
(`wood_wall_h/v`), balcão (item 1617, bloqueia) com o NPC atrás, 2 baús
(1740), 2 lanternas de papel (`paper_lantern`) e uma placa "Saída - <NPC>"
perto do pad de retorno. **Taverna e Prisão continuam só fachada** (sem
interior) porque não existe NPC de taverneiro/carcereiro em `data/npcs/` — se
um for criado depois, o mesmo padrão de `build_shop_interior` serve.

### Arena do Exame Chunin

30x20 tiles, piso de pedra (`STONE_FLOOR`), muralha de pedra com um anel de
bancos (`BENCH`, item 1662) encostado por dentro simulando arquibancada,
2 tochas perto da entrada e uma placa central. Teleporte de entrada na
Academia (pad em 1020,1049 → pousa em 1314,1033, sem item na célula de
pouso); o pad de retorno fica um tile ao norte do pouso (1314,1032) e devolve
pra Academia num tile livre (1019,1049) — nunca no MESMO tile do pad de ida,
senão os dois teleportes formam um loop infinito. Populada com os 6 "Rivais
do Exame" (`data/maps/spawns_lore.json`) e sinalizada como zona nova em
`data/maps/forest_valley.json`. Deixada documentada aqui para o agente de
lore usar depois (ex.: cutscene do torneio, diálogo da Instrutora Ibuki).

### Prédios importados

As casas e lojas de **parede de madeira vanilla** (`b.building(...)`, ids 5261–5277)
foram substituídas por prédios recortados de `assets-src/import/village_buildings.png`
(material de referência privado, no `.gitignore`). O recorte é
`tools/spr/slice_buildings.py`; os templates ficam em
**`assets-src/sprites/buildings.json`** e cada célula 32x32 é um **item novo**
(`bld_*` em `assets-src/sprites/tiles.json`, server ids **30008–30249**).

**São fachadas** — em Tibia tudo do prédio bloqueia; só a célula de porta é
caminhável (`group: "door"`, `walkable: true`). Desde a v2 do mapa, as 3
fachadas de loja (Ichiro/Hayato/Rin) **ganharam interior de verdade**: a
célula da porta recebe um item de teleporte (`TELEPORT_ITEM = 1387`, empilhado
por cima do item de porta, sem apagar o desenho) que leva a uma sala separada
em `tools/map/build_shop_interior()` (x 1300+, ver seção "Lojas: NPC +
interior" acima). Taverna e Prisão continuam só fachada (sem NPC próprio em
`data/npcs/`, então sem interior).

`tools/map/build_valley.py` estampa com:

```python
stamp_building(b, tpls, sid, "tavern", 1032, 1063, ground=DIRT)
```

O ponto `(x, y)` é o **canto inferior esquerdo**: a célula `(col, row)` da matriz do
template cai em `(x + col, y - (altura - 1 - row))`. A função limpa os itens do
retângulo inteiro, troca o chão se `ground` for dado, empilha os itens e devolve a
posição absoluta da porta.

| Template | Tamanho (col x lin) | Onde | Porta |
|---|---|---|---|
| `tower` (Torre do Hokage) | 5x6 | 1027,1036 — ao norte da praça | 1029,1036 |
| `big_house` | 5x6 | 1013,1036 | 1014,1036 |
| `house_green` | 4x4 | 1040,1036 | 1041,1036 |
| `newbie_shop` (Ichiro) | 4x4 | 1037,1053 — Rua dos Mercadores | 1038,1053 |
| `ramen_shop` (Hayato) | 4x5 | 1042,1053 — Rua dos Mercadores | 1044,1053 |
| `blue_shop` (Rin) | 3x4 | 1046,1053 — Rua dos Mercadores | 1047,1053 |
| `prison` | 4x4 | 1013,1063 | 1014,1063 |
| `blue_house` | 3x4 | 1021,1063 e 1041,1063 | col 1 da base |
| `tavern` | 5x5 | 1032,1063 | 1034,1063 |
| `roof_orange` | 3x4 | 1037,1063 (galpão) | — |
| `tree` / `bushes` / `big_bush` / `grass_patch` | 1–3 tiles | praça, academia, fora do portão | — |
| `green_gate_a/b/c`, `gate_east` | muros verdes | fora do portão sul | — |
| `shop_east` | 3x3 | 1132,1062 (hub do pântano) | — |

> `lamp_post` saiu da lista: as 2 estampas antigas (1021,1053 e 1037,1053) caíam
> em cima da cerca de bambu nova da Academia e da fachada nova do Ichiro. As
> ruas continuam iluminadas por tochas de parede (`TORCH`) e pela lanterna de
> papel (`paper_lantern`) dentro dos interiores.

O **templo continua sendo a PZ** e a posição da town — a torre foi colocada ao lado
(ao norte da praça), sem tocar no templo nem no `flag_rect` de proteção.

Ordem obrigatória ao mexer nesses prédios:

```bash
.venv/bin/python tools/spr/slice_buildings.py   # fatia a folha, escreve tiles.json/buildings.json
.venv/bin/python tools/spr/allocate_ids.py      # aloca server/client ids (NÃO toca no OTB)
.venv/bin/python tools/map/build_valley.py      # gera o mapa com esses ids
.venv/bin/python tools/spr/build_assets.py      # grava items.otb + Tibia.dat/.spr + items.xml
tools/install_generated.sh                      # instala no servidor
```

> **Aviso do gerador.** Enquanto os ids novos não estiverem no `items.otb`, o
> `build_valley.py` imprime `AVISO: N server ids de tiles novos ainda NAO existem no
> items.otb` e valida esses ids (>= 30000, presentes em `allocations.json`) usando as
> flags declaradas em `tiles.json`. Isso é deliberado, para o mapa poder ser gerado
> antes do build de assets. **Instalar o mapa sem rodar `build_assets.py` faz o TFS
> recusar os itens.**

### Zonas

- **Vila da Folha** — muralha de pedra com **2 portões nomeados** (Sul,
  principal, com torii; Leste, saída da Rua dos Mercadores), ruas de
  cobblestone com tochas, praça com fonte+bancos e templo em **zona de
  proteção** (o interior do templo também tem `no-logout`). Bairros
  separados: residencial (norte junto à Torre do Hokage + sul), Rua dos
  Mercadores (as 3 lojas, cada uma com interior), Academia Ninja (cercada de
  bambu), bloco cívico (taverna+prisão).
- **Floresta** (level 1–10) — grama com manchas densas de árvores, trilhas de terra e um
  anel de trilha em volta da vila (y 1025 / y 1075, x 1005 / x 1055), com placa em cada
  bifurcação. Clareiras com Lobo, Bandido, Cobra da Floresta e Bandido Arqueiro. A
  sudeste, o acampamento dos bandidos com tendas, fogueira e cerca, guardado por
  bandidos.
- **Floresta da Morte** (level 10–25) — a leste do rio, agora **cercada por um muro
  alto de bambu com 1 portão** alinhado à ponte (área do Exame Chunin). Chão de
  lama/pântano, árvores mortas, juncos e poças d'água. Sanguessuga Gigante, Sapo
  Gigante e Ninja Renegado, mais a **Serpente Branca** numa clareira isolada
  ("Ninho da Serpente", 1190,1015).
- **Interiores da Vila** e **Arena do Exame Chunin** — apêndice isolado (x 1300+),
  só acessível por teleporte; ver seções acima. Registrado como zona nova em
  `data/maps/forest_valley.json`.

### Spawns

30 grupos, 64 monstros, 6 NPCs. Raio 2–4, `spawntime` 60–120 s para monstros comuns
(120 s pros Rivais do Exame) e 3600 s para bosses.

| Monstro | Qtd |
|---|---|
| Lobo | 12 |
| Bandido | 10 |
| Cobra da Floresta | 7 |
| Bandido Arqueiro | 7 |
| Sanguessuga Gigante | 7 |
| Sapo Gigante | 7 |
| Ninja Renegado | 5 |
| Rival do Exame — Pedra/Som/Névoa (Arena) | 2+2+2 = 6 |
| Serpente Branca (boss) | 1 |
| Chefe dos Bandidos (boss) | 1 |
| Sapo Ancião (boss) | 1 |

Os 6 "Rivais do Exame" e a NPC Instrutora Ibuki vieram de um pedido de
`data/maps/spawns_lore.json` (agente de lore) que se encaixou diretamente na
Arena nova. Os outros 4 pedidos desse arquivo (Costa das Marés, Ruínas do
Clã, Montanha do Trovão, Covil da Nuvem Vermelha) ganharam mapa físico na
missão **v2.1** — ver seção abaixo.

## Vila da Folha v2.1 (2026-09-04) — resposta às ressalvas do orquestrador

A revisão do orquestrador aprovou a v2 com 5 ressalvas: (1) grandes áreas de
terra batida vazia dentro da muralha; (2) prédios sem rua até a porta; (3)
taverna e prisão sem interior; (4) templo sem nada dentro; (5) placas sem
texto. `tools/map/build_regions.py` (novo módulo, mesmo estilo de `decor.py`:
só importa `build_valley`, nunca o edita — chamado do `main()` via
`build_regions.build_all(b, sid, tpls)`, depois de `decor.py` e antes de
`apply_borders`) resolve as 5:

1. **Quintais e becos** (`upgrade_village`): 4 casas novas nos maiores vazios
   dentro da muralha (`house_green` em 1021,1036 e `blue_house` em 1045,1036
   ao norte; `blue_house` em 1017,1063 e `house_green` em 1045,1063 ao sul —
   os anchors batem com o mesmo padrão de porta-na-linha-de-baixo dos
   prédios existentes). O resto do vazio vira **quintal** (grama + canteiro
   de flor/touceira/arbusto/cerca/barril — pool de `assets-src/sprites/
   tiles_decor.json`, mesma técnica de `decor.place_forest_decor`) perto de
   qualquer parede, ou **beco de terra estreito** (quase vazio, só ~8% de
   chance de um barril/caixote) longe delas — 172 tiles de quintal + 25
   itens de beco na 1ª geração.
2. **Rua até a porta**: 2 ruas de fundo novas, cobblestone, uma linha ao sul
   de cada fileira de portas (`NORTH_LANE_Y = 1037`, `SOUTH_LANE_Y = 1064`,
   61 tiles) — toda casa/taverna/prisão nova E antiga passou a ter a porta
   colada numa rua (as lojas já tinham, desde a v2; a torre e o templo abrem
   direto na praça). A rua norte respeita a praça (não repinta x 1022–1036,
   já é piso de pedra) e encosta nela pelos dois lados.
3. **Interior da Taverna e da Prisão**: mesmo padrão de teleporte-na-porta
   dos shops (`build_shop_interior`), em salas novas no apêndice de
   interiores (x 1300+): Taverna em **1300,1008–1306,1013** (mesas + cadeiras
   + balcão + barris + lanternas), Prisão em **1310,1008–1315,1013** (2
   celas separadas por grade de madeira — item vanilla 3798 "wooden bars" —
   cada uma com cama vanilla 1754). Sem NPC (taverneiro/carcereiro não
   existem em `data/npcs/`), só mobília.
4. **Templo com conteúdo**: um ponto de "chama eterna" (ver nota abaixo) +
   2 tochas em 1029,1041 (um tile ao norte da posição da town/spawn de
   personagem novo, pra não bloquear ninguém nascendo ali) + placa "Templo"
   colada na porta (1029,1047).
5. **Placas com texto**: placa individual em cada uma das 3 lojas (além da
   placa geral da rua) e a placa nova do templo — todas com `text=` (item
   1440, o mesmo de sempre).

> **Achado do tour in-game (2026-09-04).** A 1ª versão do altar usava
> `STATUE` (item vanilla 1442) — o build/validate/BFS passaram limpo e o
> preview Python mostrou o círculo placeholder "S" certinho, mas o tour com
> o cliente real (`screenshots/mapa_v21_03_templo_altar.png`, zoom em
> `/tmp/zoom_statue3.png`) revelou que o item **não aparece** na tela: o
> OTBM tem o item 1442 na célula certa (conferido lendo o `.otbm` instalado
> byte a byte), mas o sprite não é desenhado — client id 2025, na mesma
> faixa de outros itens vanilla que renderizam bem (fonte 1922, balcão
> 2317, baú 2472), então não é um id fora do range. Provável lacuna no
> `Tibia.dat`/`.spr` próprio do projeto (`tools/spr/`, fora do escopo desta
> missão) para um item que nunca tinha sido colocado no mapa antes. Trocado
> por `CAMPFIRE` (1428, "campfire") — já confirmado renderizando de verdade
> no acampamento dos bandidos — e reconferido lendo o `.otbm` reinstalado
> (item 1428 na célula 1029,1041,7); combina melhor com o nome "Templo da
> Chama" de quebra. A cadeira de madeira (item vanilla 1650) na Taverna tem
> o mesmo sintoma (aparece como um losango cinza genérico em vez de uma
> cadeira) — mantida mesmo assim porque é só decoração (não bloqueia BFS
> nem gameplay); registrado como pendência no fim deste documento.

## Regiões novas (v2.1) — Costa das Marés, Ruínas, Montanha, Covil

Os 4 pedidos de `data/maps/spawns_lore.json` sem mapa físico ganharam
região de verdade, todas em `tools/map/build_regions.py`, todas em x≥1200
ou y≥1120 (fora do retângulo do mundo aberto atual, 1000–1199/1000–1119) —
o cabeçalho do OTBM continua 2048×2048, folga de sobra. Nomes de monstro e
NPC usados nos spawns são os campos `"name"` de `data/monsters/*.json` /
`data/npc/<Nome>.xml` (já exportados por outro agente antes desta missão —
conferido em `server/tfs/data/monster/naruto/` e `server/tfs/data/npc/`),
não os ids `snake_case`.

### Costa das Marés (nível 12–19)

`build_coastal_tides`, x **1000–1049**, y **1120–1169**. Vila de pescadores
pequena (4 cabanas `blue_house`, cada uma com um barril/caixote de
equipamento de pesca ao lado — não existe item vanilla "rede de pesca"
catalogado) em volta de um patio de areia; praia (chão vanilla `sand`, ids
104/231/9059 — ground, não bloqueia) com fronteira reta pra grama (**sem
borda dedicada**: o par grama↔areia não existe em
`assets-src/sprites/tiles.json`, só grama↔terra/água/lama e cobble↔terra —
documentado aqui em vez de forçar uma borda errada); 2 barcos pequenos
(item vanilla 3587 "small boat", não bloqueia) encalhados na areia perto da
água. Liga à Vale da Folha por um ramal da trilha sul: a mesma trilha que
hoje vira pra leste rumo ao acampamento dos bandidos (1029,1090) continua
reto pro sul até 1029,1142, com uma placa de bifurcação em 1025,1091 ("<-
Vila da Folha \| Costa das Mares ->", pedido item 3 da missão).

Cais de madeira (`bridge_wood_center`, reaproveitando os mesmos tiles da
ponte do rio) saindo da praia (1029,1148) até uma **plataforma de pedra
sobre a água** (1025,1163–1033,1168, com 2 tochas + placa) onde fica o boss.
Um SEGUNDO trecho de cais, mais curto (1008,1148–1008,1157), termina no
meio da água sem nada do outro lado — a **ponte inacabada** pedida na
missão, com placa "Obra da ponte - sabotada pelos mercenários da guilda
rival".

Spawns: Mercenário da Ponte ×6, Batedor da Névoa ×4, Guardião da Neblina
×3, Espadachim da Névoa (boss) ×1 na plataforma — o Aprendiz Mascarado é
invocado em combate (fase 2 do boss), não tem spawn próprio, conforme
`data/maps/spawns_lore.json`. NPCs: Mercador Itsuki (1026,1145) e Ancião
Tazu (1032,1145) — `data/npcs/coastal_tides.json` atualizado (só x/y/map);
Mestre de Tarefas Umi ganhou x/y (1029,1147) mas **não tem spawn no mapa**
porque não existe `data/npc/Mestre de Tarefas Umi.xml` ainda (nenhum
"Mestre de Tarefas" do jogo tem — gap pré-existente do exportador, não
desta missão).

### Ruínas do Clã Marionetista compacta (nível 25–50)

`build_ruins`, x **1200–1249**, y **1000–1049**. A zona "Ruínas do Clã" que
já existia em `data/maps/forest_valley.json` é a versão **abstrata** usada
pelo protótipo Godot (não evolui mais); esta é a primeira versão **física**
no OTBM de verdade. Portão novo no muro leste da Floresta da Morte
(1199,1020–1021, tochas + placa de bifurcação "<- Floresta da Morte \|
Ruínas do Clã Marionetista ->"), pátio de terra com **5 grupos de paredes
de pedra quebradas** (só 2 lados fecham, norte com um trecho reaberto no
meio — "a parede caiu" — e oeste) + 2 trechos de parede solta + entulho
(pedras/tocos/galhos, mesmo pool de `decor.place_forest_decor`) encostado
nas quinas. Salão do Marionetista **intacto** no fundo leste
(1236,1015–1248,1035), com porta, 2 tochas e o boss no centro.

Spawns: Marionete de Combate ×6, Sentinela de Pedra ×4, Guerreiro Espectral
×3, Xamã da Maldição ×3 (roster geral de `data/monsters/ruins.json`,
espalhados no pátio, longe das paredes pra não cair em cima de um canto),
Desertor de Elite (mini-boss, **NOVO** pedido de `spawns_lore.json`) ×1 perto
da porta do salão, Marionetista das Ruínas (boss) ×1 no centro do salão.
Sem NPC (Tsubaki/Kaito já têm posição própria no mapa abstrato do Godot,
`data/npcs/ruins.json`, fora do escopo de edição desta missão).

### Montanha do Trovão compacta (nível 50–80)

`build_mountain`, x **1200–1249**, y **1060–1109**. Mesma ressalva da
Ruínas (a zona homônima em `forest_valley.json` é a versão abstrata; esta é
a física). Corredor novo (1225,1049–1225,1060) liga o fim das Ruínas a
esta zona pelo vão y 1050–1059 (nenhuma das duas usava essa faixa). Chão de
pedra (`STONE_FLOOR`) numa trilha sinuosa (largura 16, curva por
`(y%14)`) flanqueada por **água = abismo** (pedido da missão: "penhascos
usando... água como abismo") dos dois lados — intransponível, bloqueia
igual a qualquer água do jogo. Planalto no topo (1215,1099–1235,1109),
achatado, com sinalização e o portal para o Covil.

**Portal gated**: teleporte em **1225,1103** com `action_id=45004` (o
"actionid = rank mínimo Anbu" pedido na missão — a checagem de rank em si é
de outro agente, que deve ler esse actionid antes de deixar o teleporte
agir; aqui só o item e o destino foram criados) para o Covil da Nuvem
Vermelha, com placa ao lado explicando o requisito. Retorno: um pad
separado em 1225,1102 (nunca a mesma célula do portal — regra anti-loop de
sempre) volta pro topo da montanha.

Spawns: Águia do Trovão ×5, Oni da Geleira ×4, Monge da Tempestade ×3,
Serpente de Magma ×3 (ao longo da trilha), O Sócio Eterno (boss, **NOVO**
pedido de `spawns_lore.json`) ×1 e Oni Ancestral (boss final) ×1 no
planalto. Sem NPC (Genzo/Yuki já têm posição própria no mapa abstrato,
`data/npcs/mountain.json`, fora do escopo de edição desta missão).

### Covil da Nuvem Vermelha (nível 80–100)

`build_akatsuki_lair`, x **1400–1449**, y **1000–1049**. **Masmorra
isolada de propósito** — nenhuma trilha a pé liga a ela; o único acesso é o
teleporte gated no topo da Montanha (acima). Hall de entrada
(1400,1005–1409,1019, com o pad de chegada, o pad de retorno e as 2 NPCs)
→ corredor de pedra (y 1011–1013) → 3 salas de boss alternando norte/sul
(cada uma com porta própria abrindo pro corredor) → sala final grande
(1436,1000–1449,1024, no extremo leste).

| Sala | Boss | Nível |
|---|---|---|
| 1 (norte) | O Vigia Ilusório | 85 |
| 2 (sul) | O Mascarado das Sombras | 90 |
| 3 (norte) | O Portador dos Seis Caminhos | 95 |
| Final (leste, grande) | O Ancestral da Nuvem Vermelha | 100 |

Corredor patrulhado por Clone Branco ×10 e Ninja Elite da Aurora ×6 (offsets
sempre com `dy` em {-1,0,1} — as 3 linhas do corredor nunca cruzam a parede
de nenhuma sala, então qualquer `dx` dentro do corredor é seguro; foi
exatamente o bug encontrado e corrigido na 1ª rodada de build, ver
histórico do commit). NPCs: Capitã Anbu Suzu (1406,1010) e Fornecedor Enji
(1406,1012) no hall — `data/npcs/akatsuki_lair.json` atualizado (só
x/y/map); Mestre de Tarefas Kuro ganhou x/y (1406,1014) mas sem spawn, mesmo
motivo do Mestre de Tarefas Umi acima.

**Confirmado no tour in-game** (`screenshots/mapa_v21_10_covil_sala_final.png`):
personagem tomou dano de "O Ancestral da Nuvem Vermelha" parado na sala
final, boss vivo e atacando de verdade.

## Como regenerar

```bash
.venv/bin/python tools/map/build_valley.py
```

O build **falha** (exit 1, nada é gravado) se:

- algum id usado não existir no `items.otb` **nem** em `allocations.json` com id
  >= 30000 (esse é o relaxamento descrito em "Prédios importados");
- algum chão não for do grupo `ground`;
- o templo, algum centro de spawn, alguma criatura ou algum NPC não for alcançável a
  pé a partir do templo (BFS de 4 vizinhos sobre tiles caminháveis — portas contam
  como passáveis; água, paredes, árvores e arbustos bloqueiam).

Para inspecionar um OTBM qualquer:

```bash
.venv/bin/python tools/map/otbm.py server/generated/world/valley.otbm
```

## Autoborder

Sem isso, grama, terra, lama e água terminavam em uma linha reta exatamente no
limite do tile — o "efeito xadrez" que denuncia mapa gerado por código. A
Tibia resolve isso com **tiles de borda** (autoborder): um item de
DECORAÇÃO, desenhado por cima do chão, com uma faixa irregular do material
"de cima" invadindo o tile do material "de baixo". `tools/map/build_valley.py`
tem um passe final, `apply_borders(b, sid)`, chamado depois de
`carve_clearings`/`connect_clearings` e antes de `build_spawns`/`validate`.

### Arte (`tools/spr/gen_borders.py`) — v2, "fluida"

A v1 desenhava cada uma das 12 peças com uma fórmula própria (reta = uma
onda; canto externo/interno = uma elipse radial independente). O resultado
tinha o material certo mas a "caligrafia" da curva mudava de uma peça pra
outra — na trilha isso lia como uma faixa serrilhada uniforme, com emenda
visível bem onde uma peça reta encontrava um canto. A v2 resolve isso na
raiz: **uma única curva-base por direção** (`_depth_profile`, periódica,
amplitude 3–6px, suavizada por média móvel antes de receber o jitter — sem
isso o "ruído independente por pixel" da v1 é o que lia como serrilhado) e
as 12 peças são **derivadas** dela, nunca reinventadas:

- retas (`n/s/e/w`): a curva direto, `y < profundidade(x)` (e rotações).
- cantos EXTERNOS (`cnw/cne/csw/cse`): união de 2 "línguas curtas" — a MESMA
  curva das duas retas que formam o canto, encolhenda por `_taper` (uma
  smoothstep) conforme se afasta do canto (alcance `REACH = 12px`, por isso
  a língua não vira uma reta disfarçada). Como reusam literalmente
  `profile["n"]`/`profile["w"]` etc., a amplitude e o "sotaque" da onda no
  canto são garantidos iguais aos da peça reta correspondente — é a
  continuidade C0 pedida na missão, por construção, não por coincidência.
- cantos INTERNOS (`icnw/icne/icsw/icse`) = tile cheio **menos** o bolsão no
  canto OPOSTO, e esse bolsão é literalmente a máscara de canto externo
  oposto (`icnw` = NOT `cse`-shape usando as curvas sul/leste) — de novo,
  nenhuma fórmula nova, só reaproveitar.

Cima disso: **dithering leve** na linha de contato (`_dither_edge`, troca
alguns pixels da beira seguindo a matriz de Bayer — o mesmo dither ordenado
do `gen_terrain`, não ruído aleatório puro), **brilho de 1px do lado do
invasor** (anel interno) e **contorno de 1px do lado do material invadido**:
sombra escura de contato para os pares terrosos, e uma linha fina de
**espuma/areia clara** (`FOAM`) para `grass_water` — margem de rio, não uma
sombra. A textura do material invasor não é mais um ruído genérico
(`shared_field` + paleta, v1) e sim a **função de verdade** do chão
(`GT.grass(1)`/`GT.cobble(1)`) — sem isso o canto interno de cobblestone
lia como uma mancha cinza lisa em vez de paralelepípedo de verdade (bug visto
e corrigido na 2ª rodada de preview, ver "Como validar" abaixo).

Gera 4 pares × 16 peças (12 base + 4 variantes `n2/s2/e2/w2`, ver abaixo) =
**64 PNGs** 32×32 RGBA (alpha binário, igual ao resto do projeto) em
`assets-src/sprites/terrain/borders/`.

Convenção de nome do par: **`<alto>_<baixo>`** — o material ALTO manda a
faixa ondulada por cima do tile do material BAIXO, seguindo a hierarquia
`água < lama < terra < grama < cobble`. Pares gerados: `grass_dirt`,
`grass_water`, `grass_mud`, `cobble_dirt`. (A missão original pedia o par
"terra→cobblestone"; como a hierarquia diz que cobble é o material mais
alto de todos, o par foi implementado como `cobble_dirt` — cobblestone
invadindo terra —, e não o contrário, para não contradizer a própria
hierarquia que define o algoritmo.)

> **v2 (2026-09-05)**: mais 2 pares (`grass_sand`, `sand_water`) e a
> hierarquia ganhou `areia` entre água e lama — ver "Decoração de praia e
> mobiliário do santuário (v2)" no final deste arquivo.

As 12 peças base por par: `n, s, e, w` (bordas retas), `cnw, cne, csw, cse`
(cantos EXTERNOS: o alto só toca a diagonal, uma língua curta) e `icnw,
icne, icsw, icse` (cantos INTERNOS: o alto cerca as duas laterais que formam
aquele canto, sobra só um bolsão do baixo na diagonal oposta) — mais **2
variantes por peça reta** (`n2, s2, e2, w2`, semente irmã da mesma família
de curva): o autoborder escolhe entre a base e a variante por um hash
determinístico da posição (`_border_variant` em `build_valley.py`, CRC32 —
não o `hash()` embutido do Python, que é salgado por processo e daria uma
escolha diferente a cada execução), pra uma trilha comprida não repetir
sempre a mesma peça "carimbada".

```bash
.venv/bin/python tools/spr/gen_borders.py          # PNGs + folha de revisão
.venv/bin/python tools/spr/gen_borders.py --sheet  # só a folha, mais rápido
```

A folha de revisão fica em `assets-src/sprites/terrain/borders/_sheet.png`
(uma linha por par, uma coluna por peça — 16 colunas agora —, fundo =
material baixo).

### Declaração de item (`assets-src/sprites/tiles.json`)

As 64 peças viram itens novos `border_<par>_<peça>` (chaves permanentes,
grupo `decoration`, `walkable: true`, `blocks_pathfind: false`, sem
`blocks_projectile`). Como toda borda, usam `on_top: true` + `top_order: 1`
— no `.dat`/OTB isso é a flag `FLAG_ALWAYSONTOP` com `topOrder=1`, que na
Tibia é exatamente a categoria "ground border": desenha por cima do chão e
por baixo de criaturas, itens soltos e efeitos (ver `tools/spr/tiles.py`,
`FLAG_ALIAS["on_top"] = "alwaysOnTop"` e `otb.new_item(..., top_order=...)`).
IDs alocados com `.venv/bin/python tools/spr/allocate_ids.py`: as 48 peças
base ficaram em server ids 30250–30297 (primeira geração); as 16 variantes
`n2/s2/e2/w2` novas entraram DEPOIS, append-only, em **30328–30343** (client
ids 24054–24069) — não reaproveitam nem renumeram nada já alocado.

### Algoritmo (`apply_borders` em `build_valley.py`)

Autoborder clássico por bitmask de 8 vizinhos (estilo Remere's Map Editor),
rodando **depois** que todo o chão final já foi pintado (florestas, trilhas,
vila, clareiras, ponte, pântano):

1. Cada tile de chão é classificado (`classify_ground`) em um dos 5
   materiais conhecidos (`grass`, `dirt`, `cobble`, `mud`, `water`) a partir
   dos ids vanilla usados em `GRASS`/`DIRT`/`COBBLE`/`MUD`/`WATER`; chão de
   pedra/madeira (praça, templo, interiores) não entra no autoborder — fica
   `None` e é ignorado.
2. Só materiais que aparecem como "baixo" em algum par têm vizinhos
   testados: `dirt` (pode ser invadido por `grass` OU `cobble`), `water` e
   `mud` (só por `grass`) — tabela `BORDER_INVADERS`, agora percorrida em
   ORDEM DE HIERARQUIA (`_MATERIAL_RANK`) pra garantir que, quando os dois
   invasores se aplicam ao mesmo tile de `dirt`, o `cobble` (mais alto) fique
   empilhado por cima do `grass` — antes disso já saía assim por acaso
   (ordem do dict/tupla), agora é explícito e não depende de detalhe de
   implementação do Python.
3. Para cada tile-baixo e cada material-alto candidato, olha os 8 vizinhos
   (N, S, L, O, e as 4 diagonais) e decide as peças:
   - vizinho ortogonal (N/S/L/O) é o material alto → peça reta
     correspondente (com a variante escolhida por `_border_variant`);
   - vizinho diagonal é o material alto **e nenhum** dos dois ortogonais
     adjacentes é → canto EXTERNO (contato isolado pela diagonal);
   - os dois ortogonais adjacentes a uma diagonal são o material alto **e**
     a diagonal também → canto INTERNO (o baixo só sobra num bolsão).
4. As peças viram itens (`b.put(x, y, sid[...])`) empilhados por cima do
   chão da célula — não substituem nada, e por isso o BFS de conectividade
   (`walkable_map`) continua enxergando o tile como caminhável: os itens de
   borda são `walkable`/não bloqueiam.

Nota sobre os "casos faltando" que a missão original apontou (diagonal
isolada, dois cantos internos opostos, tile com 3 lados): como os passos 3–4
avaliam os 4 lados e as 4 diagonais **independentemente** e empilham quantas
peças forem necessárias no mesmo tile (uma peça reta por lado + até 4 peças
de canto, todas no mesmo `b.put` em sequência), esses casos já eram cobertos
por composição — uma diagonal isolada vira só a peça de canto externo
correspondente; dois cantos internos opostos (ex.: N+O+NO hi e S+L+SE hi ao
mesmo tempo) empilham `n+s+e+w+icnw+icse` no mesmo tile; um tile com 3 lados
hi empilha as 3 peças retas mais os cantos internos onde a diagonal também
bate. Não foi preciso montar a tabela de 47 combinações fixas do blob
tileset clássico porque aquela tabela existe pra evitar montar arte NOVA
para cada combinação (arte pintada à mão não compõe); aqui a arte É
procedural e compõe naturalmente. O que estava realmente quebrado era a
CONTINUIDADE VISUAL entre peças (resolvido na v2 do `gen_borders.py`
acima), não a cobertura de casos.

Na primeira geração do Vale da Folha isso colocou **1779 peças de borda** no
mapa inteiro (ver a linha `bordas (autoborder) N pecas` na saída de
`build_valley.py`) — principalmente grama/terra nas trilhas da floresta,
grama/lama na fronteira com a Floresta da Morte e cobblestone/terra nas ruas
e no portão da Vila da Folha. A v2 do algoritmo não muda ONDE as peças vão
(mesma lógica de bitmask), só qual arte é usada — o total continua 1779.

### Visualizar sem o cliente (`tools/map/render_preview.py`)

```bash
.venv/bin/python tools/map/render_preview.py
# presets prontos (v2): full = mundo aberto inteiro (1000,1000-1199,1119);
# interiors = lojas+arena (1298,998-1332,1036); vila_zoom = só a vila;
# default = vila+floresta (área antiga)
# presets novos (v2.1): vila_v21 = vila apos o infill; costa = Costa das
# Mares (1000,1085-1049,1169); ruinas (1195,998-1249,1049); montanha
# (1200,1058-1249,1109); covil (1398,998-1449,1036)
.venv/bin/python tools/map/render_preview.py --preset full --labels --zoom 1 \
    --out screenshots/preview_v2_anotado.png
# ou uma área especifica (--preset é ignorado se --area for passado):
.venv/bin/python tools/map/render_preview.py --area 1000 1020 1120 1080 \
    --out screenshots/preview_borders.png
```

`--labels` desenha o nome de cada zona/loja/portão em cima do render (usa a
lista `LABELS`/`INTERIOR_LABELS`/`REGION_LABELS` do próprio
`render_preview.py`, derivada das constantes de `build_valley.py`/
`build_regions.py` — atualiza sozinha se as coordenadas mudarem). `--zoom N`
redimensiona o PNG final por N (nearest-neighbor, mantém os pixels
nítidos) — útil para `vila_zoom --zoom 3`.

> **v2.1**: `render_preview.py` agora roda o pipeline COMPLETO (`build` →
> `carve_clearings` → `connect_clearings` → `decor.place_*` →
> `build_regions.build_all` → `apply_borders`), igual ao `build_valley.py`
> real — antes pulava `decor`/`build_regions`, então o preview mostrava a
> vila v2 "crua", sem o infill nem as regiões novas. `SpriteBook` ganhou
> placeholders extras (areia, cadeira, cama, grade de cela, barril/caixote
> vanilla, barco pequeno) só pro preview Python ficar legível — o cliente
> real usa o sprite de verdade (ou não, ver "Pendências da v2.1" sobre 1442
> e 1650).

Roda `build_valley` como biblioteca (mesma sequência exata do build real:
`build` → `carve_clearings` → `connect_clearings` → `apply_borders`) e
desenha 32px por tile usando os PNGs de `assets-src/sprites/terrain/`
(chão/objetos vanilla, via `assets-src/sprites/overrides/10_terrain.json`) e
de `tiles.json` (bordas, prédios importados, mobiliário). Servidor id sem PNG
conhecido no override E sem entrada em `SpriteBook._EXTRA_PLACEHOLDERS`
(fonte, teleporte, balcão, banco, baú, estátua — mobiliário vanilla usado só
a partir da v2) é desenhado em magenta — sinal de que falta mapear alguma
peça; os ids em `_EXTRA_PLACEHOLDERS` viram um círculo colorido com uma letra
(F=fonte, T=teleporte, C=balcão, B=banco, X=baú, S=estátua), só para o
preview ficar legível — o cliente real usa o sprite vanilla de verdade. É
assim que a arte das bordas foi ajustada e conferida (`Read` no PNG gerado)
sem precisar compilar assets nem abrir o OTClient.

#### Como a v2 foi validada (3 rodadas de preview)

`screenshots/preview_borders_v2.png` (mesma área do `preview_borders.png`
antigo, 1000,1020–1120,1080) e `screenshots/preview_borders_v2_zoom.png` (dois
recortes 4×, lado a lado: vila+trilha em 1024,1058–1057,1078, e
rio+ponte+hub do pântano em 1118,1050–1145,1070) documentam o resultado
final. O processo até chegar lá:

1. **1ª rodada** — reescrita completa do `gen_borders.py` com curva-base
   única + derivação das 12 peças (ver acima). Olhando a folha de revisão
   (`_sheet.png`), as retas já saíam onduladas e suaves em vez de
   serrilhadas, e os cantos mostravam a língua/bolsão coerente com a peça
   reta vizinha.
2. **2ª rodada** — build + preview do mapa inteiro revelou um bug que a
   folha de revisão sozinha não mostrava: o canto interno de `cobble_dirt`
   (`icnw`/`icne`/...) aparecia no jogo como uma **mancha cinza lisa**, sem
   nenhuma textura de paralelepípedo — porque `_texture_hi` usava um ruído
   genérico (`shared_field` + paleta) em vez da função de verdade do chão.
   Corrigido trocando para `GT.cobble(1)`/`GT.grass(1)` (a MESMA função que
   desenha o chão normal), o que também deixou a textura da invasão idêntica
   pixel a pixel ao material que ela devia imitar.
3. **3ª rodada** — novo build + preview (main + zoom) depois da correção:
   cantos internos de cobblestone agora mostram pedras de verdade, o rio
   mostra a linha de espuma clara contínua, e as trilhas da floresta ficaram
   com uma faixa larga e suave, sem quinas duras nem emenda visível entre
   peça reta e canto. Comparado ao `preview_borders.png` da v1 (faixa
   serrilhada uniforme, cantos com corte reto), a diferença é imediatamente
   visível lado a lado.

## Decoração e ponte

Itens NOVOS de cenário — ponte de madeira, pedras, tocos, flores, tufos de
grama, cogumelos, galho caído, poça decorativa, tocha de rua em poste, placa
de trilha, barril, caixote, cerca de madeira e caminho de pedras soltas —
ficam em `assets-src/sprites/tiles_decor.json` (mesmo esquema do
`tiles.json`, arquivo **separado** de propósito: outro agente edita
`tiles.json` ao mesmo tempo para as bordas). O coordenador mescla as duas
listas antes de rodar `tools/spr/allocate_ids.py` (que só lê `tiles.json`) —
por isso as entradas de `tiles_decor.json` **não têm `server_id`/`client_id`**
ainda.

> **v2 (2026-09-05)**: cadeira, estátua de santuário, lanterna de pedra e
> decor de praia (concha, pedra molhada, poste de amarração, madeira
> encalhada) entraram direto em `tiles.json` (sem o arquivo separado — não
> havia edição concorrente de bordas desta vez). Ver "Decoração de praia e
> mobiliário do santuário (v2)" no final deste arquivo.

### Arte (`tools/spr/gen_decor.py`)

```bash
.venv/bin/python tools/spr/gen_decor.py
```

Desenha 31 PNGs 32×32 (`stone_large` é 64×64, 2×2) em
`assets-src/sprites/terrain/decor/`, reaproveitando as paletas e primitivas
de `tools/spr/gen_terrain.py` (`P_WOOD`, `P_STONE`, `P_BARK`, `P_GRASS_DOT`,
`P_FLOWER`, `P_PUDDLE`, `Rnd`, `put`, `rect`, `ellipse`, `outline`, `shade`,
`fbm`) em vez de duplicá-las. Fogueira do acampamento (id vanilla 1428) e
tendas (id vanilla 7605) **já existem** em `gen_terrain.py`/
`overrides/10_terrain.json` — não foram redesenhadas de novo.

### Ponte de madeira

Substitui o piso de pedra (431) + cerca (1533) usados hoje pela travessia do
rio (`build_valley.RIVER_X0/X1`, `BRIDGE_Y0/Y1`) por 5 tiles novos:

| Tile | Grupo | Flags |
|---|---|---|
| `bridge_wood_center` | `ground`, `speed: 100` | `walkable: true` |
| `bridge_wood_head_west` / `_east` | `ground`, `speed: 100` | `walkable: true` (cabeceiras, viga de ancoragem visual) |
| `bridge_wood_rail_north` / `_south` | `wall` | `walkable: false`, `has_height: true` (corrimão — item, não chão; bloqueia 1 tile) |

O chão cobre a mesma faixa que o piso de pedra ocupa hoje (`RIVER_X0-1` até
`RIVER_X1+1`, `BRIDGE_Y0` até `BRIDGE_Y1`); os corrimões ficam nas linhas
`BRIDGE_Y0-1` e `BRIDGE_Y1+1`, onde hoje está a cerca vanilla. `speed: 100`
casa com o piso de pedra/madeira vanilla (405/431), então atravessar a ponte
não muda a velocidade do personagem.

### Placement (`tools/map/decor.py`)

Funções **puras** — recebem o `Builder` já construído por
`build_valley.build(...)` e um dict `key -> server_id` — chamadas pelo
coordenador de dentro de `build_valley.py` (este módulo só **importa**
`build_valley`, nunca o edita):

| Função | O que coloca | Onde |
|---|---|---|
| `place_bridge(b, ids)` | ponte de madeira (chão + corrimão) | trecho do rio já usado pela ponte |
| `place_forest_decor(b, ids, rng)` | pedras/tocos/flores/tufos/cogumelos/galho/poça, densidade baixa (1.2%); pedras soltas (6%) sobre as trilhas de terra | floresta a oeste do rio, só em tiles de grama/terra sem item, fora da vila, fora das áreas protegidas (`b.is_protected`) e fora de um raio de segurança em torno de cada clareira de spawn (`CLEARINGS`) |
| `place_camp_decor(b, ids)` | barril/caixote junto a cada tenda + caixote perto da fogueira + trecho de cerca de madeira nova completando a paliçada ao sul | acampamento dos bandidos (`CAMP_CENTER`); fogueira/tendas vanilla **reaproveitadas**, não duplicadas |
| `place_village_decor(b, ids)` | tochas de rua (poste) nas 4 quinas da praça + placa de trilha perto do portão sul; tochas + placa extras no hub do pântano | vila da Folha (`PLAZA`) e hub de NPCs (`HUB`) |

`tools/map/decor.py` roda sozinho (`.venv/bin/python tools/map/decor.py`):
monta ids **fictícios** (30900+, só para o teste — nada é gravado em
`allocations.json`), roda `build_valley.build()` +
`carve_clearings`/`connect_clearings`, aplica as 4 funções acima e valida a
conectividade com o **mesmo BFS** de `build_valley.validate` — sem gravar
nenhum `.otbm`. Na primeira rodada: ponte com 42 tiles, ~72 itens de floresta
+ 78 pedras de trilha, 9 itens novos no acampamento, 8 tochas/placas novas em
vila+hub, sem regressão de conectividade (95.5% alcançável do templo, contra
95.6% do mapa sem esta decoração).

## Como abrir no Remere's Map Editor

1. O RME precisa achar o mesmo `items.otb`/`items.xml` do servidor
   (`server/tfs/data/items/`) e os sprites 10.98 (`.spr`/`.dat`).
2. `File > Open` em `server/generated/world/valley.otbm`. Os arquivos
   `valley-spawn.xml` e `valley-house.xml` precisam estar **na mesma pasta** — os nomes
   vêm gravados no cabeçalho do OTBM (`OTBM_ATTR_EXT_SPAWN_FILE` / `EXT_HOUSE_FILE`).
3. Vá até o templo com `Search > Go to Position` → `1029, 1042, 7`.
4. Editar à mão é possível, mas o próximo `build_valley.py` sobrescreve tudo: mudanças
   permanentes devem ir para o gerador.

## Como instalar no servidor

```bash
cp server/generated/world/valley.otbm       server/tfs/data/world/
cp server/generated/world/valley-spawn.xml  server/tfs/data/world/
cp server/generated/world/valley-house.xml  server/tfs/data/world/
```

E em `server/tfs/config.lua`:

```lua
mapName = "valley"      -- sem o .otbm
```

O TFS resolve `valley-spawn.xml` e `valley-house.xml` pelo cabeçalho do OTBM
(caminhos relativos à pasta do mapa).

### Pré-requisito: NPCs

O TFS instancia NPC por nome: `<npc name="Ichiro, o Mercador"/>` no spawn procura
`data/npc/Ichiro, o Mercador.xml`. Hoje `tools/export_tfs.py` grava os NPCs em
`data/npc/naruto/<id>.xml` e aponta `script="naruto/<id>.lua"`, mas o TFS procura
scripts em `data/npc/scripts/`. Enquanto isso não for corrigido no exportador, os
NPCs não aparecem (o TFS os descarta em silêncio). Duas coisas precisam existir:

- `data/npc/<Nome do NPC>.xml` (pode ser cópia ou symlink do arquivo em `naruto/`);
- `data/npc/scripts/naruto/<id>.lua` (ou o `script=` apontando para o lugar certo).

## Testar sem mexer no servidor principal

`build_valley.py` não instala nada. Para validar o mapa isoladamente, crie uma pasta
com symlinks para `data/` e `build/`, um `config.lua` próprio com `mapName = "valley"`
e portas diferentes (7271/7272), e rode `./build/tfs` de dentro dela — o TFS lê o
`config.lua` do diretório atual.

## Auditoria de caminhabilidade

Feedback recorrente de usuário: "tem vários lugares do mapa que eu vou caminhando e
ele trava". `tools/map/walk_audit.py` audita isso de forma ESTÁTICA e
`client-otc/tests/walk_audit_rc.lua` de forma DINÂMICA (cliente real).

### Auditoria estática (`tools/map/walk_audit.py`)

```bash
.venv/bin/python tools/map/walk_audit.py [valley.otbm] [items.otb]
```

Para cada um dos 24.000 tiles do mapa, reproduz a regra REAL do TFS
(`Tile::queryAdd` em `server/tfs/src/tile.cpp`) usando as flags REAIS lidas do
`items.otb` — não as declaradas em `tiles.json` — e compara com a intenção
visual (chão comum + só decoração "walkable"/porta por cima). Diverge =
travamento fantasma (ou passagem indevida). Também compara, para cada id
novo (>= 30000), as flags reais do OTB com as declaradas em
`tiles.json`/`tiles_decor.json` — divergência aqui é bug de conversão em
`tools/spr/tiles.py`.

Regra confirmada lendo `Tile::queryAdd`: o que bloqueia o PASSO MANUAL de um
jogador é só `TILESTATE_BLOCKSOLID` (ativado se QUALQUER item da pilha —
chão ou empilhado — tiver a flag `blockSolid`, `item.cpp: hasProperty`).
`hasHeight`/elevação **não bloqueia o passo** — só entra em jogo em
`queryAdd` do ramo "empilhar item em cima de outro item", pra decidir se dá
pra empilhar mais um item ali (mito comum de dev OT). Já `blockPathfind` não
bloqueia passo nenhum: só faz o **autoWalk/clique-para-andar** do OTClient
recusar a rota (`game.cpp:750`, `TILESTATE_BLOCKPATH`, usado pelo A* do
servidor e pelo `Map::findPath` do próprio cliente) — por isso um item com
`blocks_pathfind` sem `blockSolid` faz o jogador "clicar e não acontecer
nada" sem nunca travar o passo manual (WASD).

Rodagem em 2026-09-04 (após regenerar items.otb/valley.otbm com as bordas
mais novas): **0 bugs de flag reais** — as únicas 2 "divergências" batidas
pelo script são as portas de pedra fechadas do templo (1029,1046,7) e da
torre da Floresta da Morte (1163,1060,7), que bloqueiam até serem abertas —
comportamento correto do Tibia, não travamento. Nenhum id >= 30000 diverge
entre `tiles.json`/`tiles_decor.json` e o OTB real (344 ids conferidos).

### Auditoria dinâmica (`client-otc/tests/walk_audit_rc.lua`)

Cliente OTClient real, logado como a conta `teste`/`teste` (personagem
Naruto, jogador comum — **não** o GM, que atravessa tudo). Percorre a rota
templo → praça → portão sul → trilha → clareiras → mata → acampamento →
ponte → hub do pântano → torre, em saltos curtos (autoWalk só encontra rota
dentro do que o cliente já "viu" — mandar autoWalk direto pra um alvo fora
da tela SEMPRE falha com `NoWay`, mesmo sem bug nenhum de mapa; por isso o
script avança aos poucos, como um jogador clicando na tela). Portas
fechadas no caminho são abertas com `g_game.use()` antes de cada trecho, e
cada travada registra a posição e os ids dos itens do tile (`Tile:getItems()`
— **atenção: retorna client id, não server id**; o script já faz a
conversão nos logs). Copie o `.lua` para `client-otc/shinobirc.lua`,suba o
cliente (`./OTClient.app/Contents/MacOS/OTClient`), e remova o arquivo ao
final — nunca fica commitado.

Resultado em 2026-09-04: nenhuma trava real encontrada. Toda ocorrência de
"TRAVA" nos logs caiu em uma de três categorias, nenhuma bug de mapa: (a)
porta fechada (mecânica normal, resolvida abrindo); (b) o script desistiu
de um salto por timeout (6s) enquanto o personagem ainda estava andando
normalmente em segundo plano — impaciência do script de teste, não do jogo;
(c) o próprio waypoint do script caiu em cima de uma árvore/moita de
propósito bloqueante. Detalhe completo em `screenshots/walk_audit.txt`.

**Achado do processo (não do mapa):** a primeira rodada reportou 100% de
travamento porque o **servidor local estava rodando com um `valley.otbm`/
`items.otb` desatualizados** (outro processo tinha acabado de editar
`tiles.json`/bordas sem reinstalar e reiniciar). Sempre que for investigar
travamento "no jogo", confirme que o servidor rodando é o build MAIS
recente: `.venv/bin/python tools/spr/build_assets.py &&
.venv/bin/python tools/map/build_valley.py && tools/install_generated.sh
&& cp server/generated/world/valley* server/tfs/data/world/ && pkill -x tfs`
(subir de novo em seguida).

### BFS por teleporte (mapa v2)

Os interiores das lojas e a Arena só são alcançáveis por teleporte, não a pé
(ficam num apêndice do mapa, x 1300+). `build_valley.validate()` ganhou
`teleport_edges(b)` — varre todo item com `tele_dest` setado (todo item
`TELEPORT_ITEM`/1387 colocado por `build_shop_interiors`/`build_arena`) e
devolve `{(x,y): (tx,ty)}` — e `bfs()` agora aceita esse dict e, ao visitar
uma célula, também enfileira o destino do teleporte de lá (se existir), além
dos 4 vizinhos. **Regra anti-loop**: a célula de POUSO de um teleporte nunca
pode ter, ela mesma, outro item de teleporte em cima — senão o pouso
reativaria o teleporte de volta e os dois lados formariam um ciclo infinito
(o BFS trataria como "alcançável" mas o servidor real travaria o jogador indo
e voltando). Todo par entrada/saída deste mapa respeita isso (pouso limpo,
pad de saída um tile ao lado — ver `build_shop_interior`/`build_arena`).

NPCs atrás de balcão também precisaram de uma regra própria: `validate()`
antes exigia a célula EXATA do NPC caminhável, mas um balcão (item 1617)
bloqueia de propósito a fileira toda atrás dele (como no Tibia de verdade).
A partir da v2, só NPCs (nunca monstros) são validados por **proximidade**
(`NPC_TALK_RADIUS = 3`, Chebyshev) em vez de célula exata — precisa haver
ALGUMA célula caminhável a até 3 tiles do NPC, não que o NPC em si seja
pisável.

### Tour in-game do mapa v2 (validação real, 2026-09-04)

Depois do build + `walk_audit` limpos, o mapa foi instalado de verdade
(`tools/install_generated.sh` + cópia pra `server/tfs/data/world/` +
`pkill -x tfs` + subir de novo) e visitado com o cliente real — cópia
temporária de `client-otc/tests/autotest_rc.lua` (removida ao final) logando
como GM (`/god`) e usando `/tp x,y,z` (talkaction de `gm_tools.lua`) por 9
pontos, 1 screenshot em cada (`screenshots/mapa_v2_*.png`): praça (fonte +
bancos), Rua dos Mercadores (as 3 fachadas lado a lado com o pad de
teleporte roxo em cada porta), **dentro da loja do Ichiro** (NPC atrás do
balcão, baús, lanternas), Torre do Hokage, Portão Sul (torii vermelho
visível), uma clareira com 2 Lobos vivos, a ponte de madeira + Hub do
Pântano (Velha Sumi e Rastreador Goro visíveis), o portão/cerca da Floresta
da Morte, e a Arena do Exame Chunin — com os 6 "Rivais do Exame" vivos e
atacando o personagem. Log do servidor sem erros/avisos durante toda a
sessão. Essa é a confirmação "de verdade" (não só render Python) de que
teleportes, fachadas, cerca e sinalização funcionam no jogo real.

### Tour in-game da v2.1 (validação real, 2026-09-04/05)

Mesmo processo (build + `walk_audit` limpos, `tools/install_generated.sh` +
cópia + `pkill -x tfs` + subir de novo), agora por **10 pontos** cobrindo a
vila v2.1 e as 4 regiões novas — `/god` + `/tp x,y,z` por ponto, 1
screenshot cada (`screenshots/mapa_v21_*.png`):

| # | Ponto | Confirmado no screenshot |
|---|---|---|
| 01 | Quarteirão novo (bairro N) | casa `house_green` nova + rua de fundo + quintal (grama/cerca/canteiro) |
| 02 | Ruas de fundo (bloco S) | casas novas + cobblestone colado nas portas |
| 03 | Altar do templo | (achado o bug do item 1442 — ver "Pendências da v2.1"; corrigido pra `CAMPFIRE`, reconferido só via leitura do `.otbm`, não por um 2º tour — ver nota abaixo) |
| 04 | Interior da Taverna | chão de tatame, mesas+cadeiras+balcão+lanternas visíveis |
| 05 | Interior da Prisão | celas + grade + camas |
| 06 | Praia / vila de pescadores | areia, cabanas, caminho de terra até a vila |
| 07 | Cais / arena do boss | plataforma de pedra sobre a água, **Espadachim da Névoa vivo** |
| 08 | Salão do Marionetista | sala intacta no fundo das Ruínas |
| 09 | Topo da Montanha | planalto + placa + **O Sócio Eterno e Oni Ancestral vivos** lado a lado |
| 10 | Sala final do Covil | **O Ancestral da Nuvem Vermelha vivo**, atacou o personagem (dano registrado no log) |

Log do servidor sem erros/avisos. **Concorrência entre agentes**: o rc
temporário (`client-otc/shinobirc.lua`) é compartilhado — outro agente
estava rodando seu próprio teste (tag de log `SLPROVA`) no mesmo arquivo
durante esta missão. O tour desta missão (tag `TOURV21`) capturou as 10
screenshots antes de o arquivo ser sobrescrito pelo do outro agente; a
troca do item do altar (1442→1428, ver "Vila da Folha v2.1" acima) foi
verificada só por leitura direta do `.otbm` instalado (item 1428 na célula
1029,1041,7), sem um 2º tour ao vivo, pra não competir de novo pelo mesmo
arquivo compartilhado enquanto a outra sessão ainda estava ativa.

### Pendências

- 406 bolsões pequenos de tiles caminháveis (789 tiles, 4,5% do total
  caminhável) ficam fora do alcance por BFS a partir do templo — reentrâncias
  dentro de aglomerados de árvores/água, sem spawn nem NPC. Comportamento
  esperado numa mata densa "de verdade"; não é tratado como bug.
- Árvores/decoração 2x2: o sprite ocupa 2x2 tiles na tela, mas a colisão real
  do TFS é sempre POR TILE (cada tile bloqueia só se o item que ocupa
  aquele tile específico tiver `blockSolid`); não há bloqueio "fantasma"
  além do tile em si nesta base de itens.
- O `OTClient.app` encerrou sozinho (stack trace de rede/asio) perto do fim
  de uma rodada de teste dinâmico longa (~2 min), antes de alcançar a
  ponte/hub/torre — não há indício de que seja causado pelo mapa (o
  personagem estava andando normalmente no momento do crash); parece
  instabilidade do cliente em sessões automatizadas longas, fora do escopo
  desta auditoria.
- **Portão Leste e entrada da Academia "somem" no preview Python** (não no
  jogo real): `stone_wall_v`/`bamboo_fence` têm `height` maior que 32px no
  override de renderização — o sprite do tile ABAIXO da abertura invade
  visualmente 1 linha da própria abertura no PNG gerado por
  `render_preview.py` (é assim que o Tibia sempre desenha parede alta; a
  colisão real continua por-tile, confirmada pelo `walk_audit` e pelo tour
  in-game — screenshot `mapa_v2_02_rua_comercial.png` mostra o portão leste
  de verdade, sem essa confusão). Só um artefato de leitura da screenshot
  "vista de cima" nesta ferramenta de preview, não um bug de mapa.
- ~~Taverna e Prisão continuam sem interior~~ **Resolvido na v2.1** — ver
  "Vila da Folha v2.1" acima (`build_tavern_interior`/`build_prison_interior`
  em `tools/map/build_regions.py`).
- ~~Os pedidos de `data/maps/spawns_lore.json` para Costa das Marés e Covil
  Nuvem Vermelha continuam pendentes~~ **Resolvido na v2.1** — ver "Regiões
  novas (v2.1)" acima.

### Pendências da v2.1 (2026-09-04/05)

- ~~Item vanilla 1442 ("statue") e 1650 ("wooden chair") não renderizam no
  cliente real~~ **Resolvido (missão "decor v2", 2026-09-05)** — causa raiz
  encontrada (não era só suspeita): os dois clientIds apontavam para o
  **mesmo** sprite quase vazio no `Tibia.spr` do projeto (25 de 1024px
  opacos, um pontinho de ~2px — visto exportando com `sprformat.py`/
  `dump_dat.py --thing`), não um buraco de cobertura. Os dois foram
  substituídos por itens NOVOS com arte de verdade: `shrine_statue_gray` no
  altar do templo e `wood_chair_east`/`wood_chair_west` na Taverna. Ver
  "Decoração de praia e mobiliário do santuário (v2)" abaixo.
- ~~Fronteira grama↔areia da Costa das Marés é um corte reto~~ **Resolvido
  (missão "decor v2", 2026-09-05)** — pares `grass_sand`/`sand_water` novos
  em `tools/spr/gen_borders.py`, mesma receita (curva-base + derivação das 12
  peças) dos 4 pares existentes; a areia também ganhou textura própria
  (`gen_terrain.sand()`) no lugar do quadrado cinza genérico. Ver seção
  "Autoborder" (hierarquia atualizada) e "Decoração de praia..." abaixo.
- **Mestre de Tarefas Umi/Kuro (Costa das Marés / Covil) não aparecem no
  jogo**, mesmo com x/y atualizados em `data/npcs/*.json`: nenhum "Mestre de
  Tarefas" do jogo tem NPC XML exportado ainda (`server/tfs/data/npc/` não
  tem nenhum arquivo "Mestre de Tarefas *"), nem os das regiões antigas
  (Vila da Folha, Ruínas, Montanha) — gap pré-existente do exportador/pipeline
  de NPCs, não introduzido nem resolvido por esta missão.
- **`client-otc/shinobirc.lua` é um recurso compartilhado entre agentes
  concorrentes.** Durante a validação desta missão outro agente (testes de
  outro sistema, tag de log `SLPROVA`) estava usando o mesmo arquivo ao
  mesmo tempo — o rc desta missão (`TOURV21`) rodou e capturou as 10
  screenshots antes de ser sobrescrito pelo do outro agente. Por isso o
  arquivo foi deixado como estava (conteúdo do outro agente) ao final desta
  missão, em vez de apagado — apagar no meio do uso de outra sessão
  quebraria o teste dela. Nenhuma versão deste arquivo deve ser commitada,
  não importa de qual agente seja o conteúdo no momento.
- A Arena do boss da Costa das Marés e o Covil da Nuvem Vermelha não têm
  waypoint OTBM próprio ainda (só as zonas antigas do Vale da Folha têm,
  ver "Waypoints gravados" acima) — cosmético, não afeta jogabilidade.

## Decoração de praia e mobiliário do santuário (v2, 2026-09-05)

Resposta ao tour in-game do mapa v2.1 (3 lacunas: cadeira/estátua vanilla
invisíveis, sem borda de areia, Costa das Marés pobre em decoração — ver
"Pendências da v2.1" acima, agora marcadas resolvidas).

### Itens novos (`tools/spr/gen_decor.py` + `assets-src/sprites/tiles.json`)

| Chave | O quê | Grupo/flags |
|---|---|---|
| `wood_chair_east` / `wood_chair_west` | cadeira de madeira, 2 orientações (encosto do lado oposto a quem senta) | `furniture`, `walkable: false` |
| `shrine_statue_gray` / `shrine_statue_mossy` | estátua de guardião de santuário (jizo), pedra crua / com musgo | `decoration`, `walkable: false`, `has_height: true` |
| `stone_lantern` | lanterna de pedra (toro) acesa, 2 fases de chama | `decoration`, `walkable: false`, `has_height: true`, `light` (igual a `street_torch`) |
| `seashell_spiral` / `seashell_fan` | conchas (cone/caramujo e leque/vieira) | `decoration`, `walkable: true`, `pickupable: true` |
| `wet_rock` | pedra escura molhada pela maré, com poça rasa | `decoration`, `walkable: true` |
| `mooring_post` | poste de amarração do cais, com corda enrolada | `decoration`, `walkable: false`, `has_height: true` |
| `driftwood` | galho de madeira encalhado, esbranquiçado pelo sal | `decoration`, `walkable: true` |

10 itens novos, server ids 30376–30385 (client ids 24102–24111,
`assets-src/sprites/allocations.json`). Substituem o uso dos ids VANILLA
1442 ("statue") e 1650 ("wooden chair") em `tools/map/build_regions.py`
(`build_tavern_interior`, `upgrade_village`).

**Causa raiz do bug antigo** (não só suspeita, confirmada): exportando os
sprites de clientId 2025 (1442) e 2358 (1650) com
`tools/spr/sprformat.py`/`dump_dat.py --thing`, os dois apontam para o
**mesmo** sprite — um pontinho de ~2px opaco num quadro 32×32 quase
inteiramente transparente (25 de 1024px). Não é um buraco de cobertura no
`.dat` (o thing existe, tem grupo/flags corretos): é o placeholder genérico
de `gen_placeholders.py` para itens sem regra de estilo compatível. Ficou
fora do escopo desta missão consertar o placeholder genérico desses 2 ids
vanilla especificamente (poderia afetar outros itens que usam o mesmo
sprite); a solução adotada foi dar aos dois um substituto NOVO com arte de
verdade.

### Areia com textura própria (`gen_terrain.sand()` + `overrides/10_terrain.json`)

A areia da Costa das Marés (ids vanilla 104/231/9059) não tinha NENHUM
override em `overrides/10_terrain.json` — caía na regra de estilo genérica
do `gen_placeholders.py` e virava um quadrado liso/pontilhado cinza (o "praia
lisa com quadrados cinza" do relato). `gen_terrain.py` ganhou `P_SAND_V4` +
`sand(v)` (mesma família de baixo contraste de `grass()`/`mud()`: campo fbm
único, 3 tons próximos, decoração esparsa de grãos/sombra rasa) — 3 PNGs
(`sand_0/1/2`), 2 usados via override (104→sand_0, 231+9059→sand_1, que já
compartilham client id no OTB).

### Autoborder: grama↔areia e areia↔água

`tools/spr/gen_borders.py` ganhou os pares `grass_sand` e `sand_water` (16
peças cada — 12 base + 4 variantes retas — mesma receita de curva-base única
do v2, reusando `GT.sand(1)` como textura do material alto em `sand_water`).
32 itens novos `border_grass_sand_*`/`border_sand_water_*` em
`assets-src/sprites/tiles.json`, server ids 30344–30375 (client ids
24070–24101). A hierarquia de materiais (ver "Autoborder" acima) passou de
`água < lama < terra < grama < cobble` para **`água < areia < lama < terra <
grama < cobble`**: `tools/map/build_valley.py` ganhou `SAND`/`_SAND_SET`,
`classify_ground` reconhece areia, `BORDER_INVADERS["water"]` agora inclui
`sand` (além de `grass`) e `BORDER_INVADERS["sand"] = ("grass",)`,
`_MATERIAL_RANK` foi renumerado para caber `sand` entre `water` e `mud`.

### `tools/map/build_regions.py`

- `upgrade_village`: cadeiras da Taverna (2 mesas × 2 cadeiras) agora usam
  `wood_chair_east`/`wood_chair_west` viradas para a mesa, no lugar do 1650.
- Altar do templo: `shrine_statue_gray` atrás da `CAMPFIRE` (mantida — já
  confirmada renderizando e "chama eterna diante do guardião" combina com o
  nome do templo) + 2 `stone_lantern` flanqueando (no lugar das 2 tochas de
  parede antigas), no lugar do 1442.
- `build_coastal_tides`: decor de praia espalhado com densidade esparsa
  (`rng.random() < 0.05` por tile de areia elegível, mesmo padrão de
  `tools/map/decor.py.place_forest_decor`) — conchas/pedra molhada/madeira
  encalhada — + 4 postes de amarração fixos junto ao cais (deslocados 2 tiles
  da faixa central por onde se anda, não bloqueiam o caminho). 36 itens no
  total nesta rodada de build.

### Validação in-game (`client-otc/shinobirc.lua` temporário, 3 sessões)

Login `god`/`god`, `/god` + `/tp x,y,z`, screenshots `screenshots/decor_v2_*.png`:

| # | Ponto | Confirmado no screenshot |
|---|---|---|
| 01 | Taverna (interior) | 2 mesas + 4 cadeiras novas visíveis, orientadas para a mesa |
| 02/03 | Templo (altar) | estátua cinza + fogueira acesa + 2 lanternas de pedra com brilho, todos visíveis |
| 05 | Costa das Marés (praia) | areia com textura (não mais quadrados cinza) + conchas/pedra molhada/madeira encalhada/caixotes |
| 06 | Costa das Marés (cais) | borda areia↔água ondulada (sem corte reto) + 2 postes de amarração |
| 08 | Costa das Marés (trilha→praia) | borda grama↔areia ondulada, sem corte reto |

Log do servidor sem novos `[Warning - Items::…]`. `tools/spr/dump_dat.py`
(`validacao: OK, divergencias=0`), `tools/spr/test_otb_roundtrip.py`
(`RESULTADO: OK`) e `tools/map/walk_audit.py` (0 divergências novas —
as 2 únicas divergências reportadas são portas fechadas pré-existentes,
não relacionadas a esta missão) rodados após o build.

## Mapa v3 (2026-09-05) — NPCs sem posição, gates de rank, identidade visual das 3 regiões

Continuação de uma missão interrompida (limite de API do agente anterior).
O agente anterior já tinha deixado prontos (achado ao ler o diff não
commitado, validado nesta missão): as texturas de piso por região
(`tools/spr/gen_terrain.py` — `crackstone_*` Ruínas, `rock_*`/`snow_*`/`ice`
Montanha, `basalt_*`/`basalt_wall_*` Covil, `stone_wall_broken`), o decor
temático (`tools/spr/gen_decor.py` — marionete quebrada, pilares, bandeiras
de oração, tochas vermelhas, poças de sangue/lava fria, `gate_marker`), o
par de borda `snow_rock`, o redesign físico das Ruínas (corredor + 3 salas +
pátio central + salão do boss com 2 pilares) e da Montanha (2 patamares,
lago gelado, santuário separado da arena), os 6 gates de rank (Chunin na
Costa/Ruínas, Jonin na Montanha, Anbu já existia no portal do Covil) e 7 dos
8 NPCs pedidos (só faltava Mestre de Tarefas Kuro no Covil). **Não redescartei
nada disso** — só consertei o que faltava rodar/validar:

1. **Bug de build (`tools/spr/tiles.json`)**: `ruin_wall_broken`,
   `basalt_wall_h/v/c` e `pillar_standing` tinham `"height": 64` (campo não
   consumido por `tools/spr/tiles.py` — só `flags.has_height` conta pro OTB)
   mas PNG 32×64 sem `"size": [1, 2]` declarado; `build_assets.py` falhava
   com `ValueError` no primeiro desses itens. Corrigido: os 5 ganharam
   `"size": [1, 2]` (largura 1 tile, altura 2 tiles = 64px, a sprite "alta de
   1 tile só" do Tibia) no lugar do `"height"` morto.
2. **Bug de conectividade na Montanha (`tools/map/build_regions.py`,
   `build_mountain`)**: a trilha "balança" de largura (`wobble`, período 14
   linhas) e o 1º patamar (`y0+14`) caía EXATAMENTE numa transição de
   período — o gap da parede, calculado só a partir da própria linha, ficava
   fora da faixa caminhável da linha vizinha (norte OU sul), virando um
   "beco sem saída": a passagem "única" na prática NUNCA conectava os dois
   lados, isolando todo o planalto (santuário + arena + portal do Covil) do
   resto do mapa. Corrigido: o gap agora usa a INTERSECÇÃO das faixas de
   `y-1`/`y`/`y+1` (`_band_at`), garantindo que a passagem sempre atravessa
   de verdade. O lago gelado tinha o mesmo risco (calculava a coluna uma vez
   só, com `cx` fixo) — trocado por cálculo por linha, sempre deixando o
   lado OESTE livre. Os centros de spawn de monstro (Águia/Oni/Monge/
   Serpente) também caíam eventualmente em cima do muro novo ou do gelo
   (`blockSolid`/não-caminhável) — a lista de offsets perdeu o `dy=±2` e o
   posicionamento agora pula linhas de perigo (patamar OU lago ±1).
   `python tools/map/build_valley.py` foi de "BUILD FALHOU (48 problemas)"
   para 0 problemas depois dessas duas correções.
3. **Covil da Nuvem Vermelha redesenhado** (`build_akatsuki_lair`, era só
   `STONE_FLOOR`/`STONE_WALL_*`/tocha branca genérica, sem identidade — o
   único item da missão original ainda não tocado pelo agente anterior):
   piso e paredes de basalto (`lair_basalt_0/1`, `basalt_wall_h/v/c`),
   tochas vermelhas (`red_torch`, luz avermelhada) no lugar da tocha branca,
   poças de sangue/lava fria (`blood_pool`/`lava_pool_cold`) como decor NÃO
   caminhável em cantos vazios do hall/salas/corredor (nunca em cima de
   NPC/porta/pad/centro de spawn), e uma **antecâmara de 1 tile** (parede +
   porta própria, separada da câmara do boss) antes de CADA uma das 4 salas
   de boss (3 salas menores + a sala final grande) — pedido explícito da
   missão que ainda não existia. Gate de rank do Covil continua o mesmo
   (actionid 45004, no portal da Montanha — a masmorra em si não tem outra
   entrada, então não precisa de gate próprio).
4. **NPC que faltava**: Mestre de Tarefas Kuro (`task_master_lair`,
   `data/npcs/akatsuki_lair.json`) posicionado no hall do Covil, em
   **(1406, 1014)** — mesmo x/y que já estava documentado no JSON (só
   faltava o spawn físico no mapa).
5. **Par de autoborder `dirt_sand`** (pedido da missão: "estrada de terra
   termina em corte reto na areia"): na hierarquia `água < areia < lama <
   terra < grama < cobble`, terra (`dirt`) é mais ALTA que areia (`sand`),
   então o par é `dirt_sand` (terra invade areia), convenção `<alto>_<baixo>`
   de sempre. 16 peças novas em `tools/spr/gen_borders.py` (textura do
   material alto = `GT.dirt(1)`, mesma receita dos outros pares) + entradas
   em `tiles.json` + `BORDER_INVADERS["sand"] = ("grass", "dirt")` /
   `BORDER_PAIR_KEY[("dirt","sand")] = "dirt_sand"` em `build_valley.py`.
   **Não precisou de código específico de região** — `apply_borders()` já
   varre o mapa inteiro por adjacência de material, então a borda nova
   apareceu sozinha nos 11 tiles onde a trilha de terra da Costa das Marés
   encosta no pátio de areia da vila de pescadores (em torno de
   `(1027-1031, 1140-1143)`), confirmado lendo o `.otbm` gerado.

### NPCs (Missão A.1) — posições finais

| NPC | Tipo | Região | Posição (x, y, 7) |
|---|---|---|---|
| Mestre de Tarefas Jiro | `task_master_leaf` | Vila da Folha (Portão Sul) | 1030, 1067 |
| Mestre de Tarefas Ren | `task_master_swamp` | Hub do Pântano (antes da Floresta da Morte) | 1137, 1057 |
| Quadro de Missões | `dailies_board_leaf` | Praça da vila, canto nordeste do templo | 1035, 1040 |
| Instrutora Ibuki | `exam_proctor_forest` | Academia (já existia antes desta missão) | 1018, 1048 |
| Mestre de Tarefas Dokan | `task_master_ruins` | Ruínas, logo após o gate de rank | 1202, 1020 |
| Mestre de Tarefas Kaji | `task_master_mountain` | Montanha, pé da trilha após o gate | 1228, 1062 |
| Mestre de Tarefas Umi | `task_master_coastal` | Costa das Marés, vila de pescadores | 1029, 1147 |
| Mestre de Tarefas Kuro | `task_master_lair` | Covil, hall de entrada | 1406, 1014 |

Todos os 17 NPCs (os 8 acima + os 9 pré-existentes) confirmados no
`valley-spawn.xml` gerado e no tour in-game (ver "Validação in-game v3"
abaixo). **Atualização (Lote M, ver seção no fim do arquivo): mais 4 NPCs
posicionados** (Ancião Kaito/Tsubaki nas Ruínas, Mestra Yuki/Ferreiro Genzo
na Montanha) — total agora 21.

### Gates de rank (Missão A.2) — cobertura final

| Região | Rank mínimo | actionid | Onde (largura cobre toda a entrada) |
|---|---|---|---|
| Floresta da Morte | — (Genin, de propósito) | — | Sem gate físico: o Exame Chunin roda DENTRO dela (Instrutora Ibuki manda matar Sapo Ancião/Serpente Branca lá dentro) — gatear a entrada por Chunin criaria paradoxo (precisa entrar pra virar Chunin, só Chunin entra). Decisão do agente anterior, mantida por ser exatamente a exceção que a missão previu ("se o lore não disser: Floresta da Morte = Genin com quest"). |
| Costa das Marés | **Genin** (era Chunin — corrigido no Lote M, ver seção no fim do arquivo) | **45001** | (1028-1030, 1120) — 3 marcadores `gate_marker`, largura da trilha. Todo jogador já nasce Genin, então o gate nunca barra ninguém (paridade visual com as outras regiões, sem bloquear a região de nível 12-19). |
| Ruínas do Clã Marionetista | Chunin | 45002 | (1200, 1020) e (1200, 1021) — 2 marcadores, largura do corredor de entrada |
| Montanha do Trovão | Jonin | 45003 | (1224-1226, 1060) — 3 marcadores, largura do corredor vindo das Ruínas |
| Covil da Nuvem Vermelha | Anbu | 45004 | Teleporte gated em (1225, 1103), no topo da Montanha — única entrada da masmorra, já existia antes desta missão |
| (Kage, 45005) | Kage | 45005 | Não usado: `data/ranks.json` não lista nenhuma área nova pro Kage (fim da progressão) |

> **Nota (Lote M)**: `data/ranks.json` (`unlocks.areas` do rank `chunin`)
> ainda lista `costa_das_mares` — usado só por `NarutoRanks.zoneMinIndex`/
> `canEnter()`, que por sua vez só é lido pelo comando de debug de GM
> `/sl canenter <zona>` (`server/tfs/data/scripts/naruto/gm_tools.lua`).
> Nenhum gate de jogo consulta essa tabela — `rank_gate.lua` olha só o
> `actionid` do item no tile (ver abaixo) — então a inconsistência de dado
> não afeta o jogo real, só o output desse comando de debug. Não corrigida
> aqui (fora do escopo de mapa desta missão; edição de `data/ranks.json` é
> de outro agente/lote).

`server/generated/scripts/naruto/rank_gate.lua` (MoveEvent `stepin`) lê o
actionid do TILE (não de item empilhado) — confirmado lendo o gerador:
`gate:aid(45001..45005)`, sem `itemid`. Testado com as duas contas: `god`/
`god` atravessa sem checagem (é GM); `teste`/`teste` (personagem Naruto,
level 7, rank Genin) foi barrado tentando entrar nas Ruínas, com a mensagem
de cancelamento e teleporte de volta — ver "Validação in-game v3" abaixo.

> **Bug encontrado e corrigido (`tools/export_tfs.py`, gerador de
> `rank_gate.lua`)**: como nenhuma missão anterior tinha colocado um
> actionid 45001-45005 num tile de verdade (o script existia mas nunca
> rodava — "fallback: no-op"), ninguém tinha notado que `gate.onStepIn`
> não checava se quem pisou é um jogador. Um monstro perseguindo o
> personagem (a Serpente Branca, na fronteira Floresta da Morte/Ruínas)
> pisou no tile do gate e `NarutoRanks.get(monstro)` explodiu com
> `attempt to call method 'getStorageValue' (a nil value)` (Creature/Monster
> não tem esse método, só Player) — 6 erros no log do servidor durante o
> 1º teste. Corrigido com `if not player:isPlayer() then return true end`
> no início de `onStepIn`; reinstalado (`export_tfs.py` → `install_generated.sh`
> → `pkill -x tfs` + subir de novo) e reconfirmado com um 2º teste de gate:
> mesma mensagem de bloqueio, **0 erros no log**.

### Validação in-game v3 (`client-otc/tests/mapa_v3_tour_rc.lua` e `mapa_v3_gate_rc.lua`)

Servidor reiniciado com o mapa/assets novos (`build_assets.py` →
`build_valley.py` → `install_generated.sh` + cópia manual de
`valley.otbm`/`valley-spawn.xml`/`valley-house.xml` pra
`server/tfs/data/world/` + `pkill -x tfs` + subir de novo), confirmado
`nc -z 127.0.0.1 7171` antes do tour. 21 screenshots `screenshots/mapa_v3_*.png`:

| # | Ponto | Confirmado no screenshot |
|---|---|---|
| 01-03 | Ruínas (pátio central, salão do boss, câmara norte) | piso rachado `crackstone`, paredes quebradas com musgo, pilares caídos/de pé, marionete quebrada |
| 04-06 | Montanha (patamar+lago, santuário, arena+portal) | muro de rocha com vão único, lago gelado (gelo azul-claro), estátua+lanternas do santuário, monstros vivos e alcançáveis (Águia/Oni/Monge/Serpente) |
| 07-09 | Covil (hall, antecâmara+sala 1, sala final) | basalto escuro, tochas vermelhas, poças de sangue, **O Vigia Ilusório vivo** no fim da antecâmara, monstros de corredor (Clone Branco/Ninja Elite da Aurora) patrulhando |
| 10-17 | Os 8 NPCs (Quadro de Missões, Jiro, Ibuki, Ren, Umi, Dokan, Kaji, **Kuro**) | todos visíveis e nomeados na tela, no ponto exato da tabela acima — `mapa_v3_17_npc_kuro.png` confirma Kuro ao lado de Suzu/Enji no hall do Covil |
| 18 | Borda `dirt_sand` (Costa das Marés) | transição terra→areia ondulada, sem corte reto |
| 19-21 | Gate de rank, 1ª tentativa (conta `teste`) | posição inicial perto do gate das Ruínas — a Serpente Branca (boss da clareira vizinha) matou o personagem antes de ele pisar no tile do gate; inconclusivo por si só, mas confirmou o rank "Genin da vila" no painel de atributos |
| 20b-21b | Gate de rank, 2ª tentativa (conta `teste`, reposicionado 1 tile a oeste do gate via SQL pra reduzir exposição ao boss) | personagem NÃO atravessa (posição antes/depois idêntica, 1199,1020), mensagem "Você precisa ser Chunin — aprovado no Exame Chunin para entrar aqui." (log `GATEV3B` em `/tmp/otc_gatev3c.log`) — screenshot mostra o personagem, a Serpente Branca e o **Mestre de Tarefas Dokan** visível do outro lado do gate |

Log do servidor sem erros/avisos novos durante as duas sessões (só os 3
avisos pré-existentes de `areaEffect: energyhit`, não relacionados a esta
missão). Pipeline completo rodado limpo antes do tour: `build_assets.py`
(sem processo concorrente), `dump_dat.py` (`validacao: OK, divergencias=0`),
`test_otb_roundtrip.py` (`RESULTADO: OK`), `build_valley.py` (0 problemas),
`walk_audit.py` (2 divergências, ambas as portas fechadas já conhecidas —
nenhuma nova).

### Limitações honestas

- A conta `teste` teve a posição salva (`posx`/`posy`/`posz` na tabela
  `players`) ajustada manualmente via SQL pra ficar perto do gate das
  Ruínas antes do teste — sem isso o personagem (level 7, nunca esteve
  perto de x=1200) levaria muitos saltos de `autoWalk` em área não vista
  pra chegar lá (ver nota de `walk_audit.py` sobre autoWalk não alcançar
  alvos fora da tela). É uma mudança de dado de teste (conta de QA, não de
  usuário real), não do mapa.
- A antecâmara do Covil ficou com só 1 tile de profundidade (não 2), porque
  as salas de boss originais já eram rasas (~5-7 tiles) e uma antecâmara
  maior deixaria pouco espaço pro raio de spawn do boss; o raio de spawn
  dos 3 bosses menores foi reduzido de 2 para 1 tile por isso.
- Não recontei manualmente os 406 bolsões pequenos inalcançáveis
  pré-existentes (mencionados na seção "Pendências" acima) nem investiguei
  se as mudanças desta missão criaram bolsões NOVOS do mesmo tipo — só
  validei que o `%` de alcançável do templo continua alto (89.9%) e que
  `validate()` não reporta nenhum centro de spawn/NPC/criatura inalcançável.

## Lote M (2026-09-05) — bugs de mapa que bloqueavam a história

Missão de mapa do plano `docs/design/auditoria-historia.md`, itens **A1, A2,
B1, B2, C1** (os 5 "críticos" que bloqueavam progressão jogável) + um
validador cruzado novo. Único arquivo tocado: `tools/map/build_regions.py` e
`tools/map/build_valley.py` (+ `tools/map/validate_world.py`, novo).

### A1 — gate da Costa das Marés (Chunin → Genin)

A Costa (nível 12-19) tinha o MESMO gate de rank Chunin das Ruínas — um
Genin recém-saído da Floresta da Vila (que ainda não fez o Exame Chunin, só
disponível DEPOIS na Floresta da Morte) era barrado na entrada e nunca
conseguia caçar lá (Achado #1 da auditoria). Corrigido em
`tools/map/build_regions.py::build_coastal_tides`: o gate trocou de
`"chunin"` (actionid 45002) pra `"genin"` (actionid 45001, novo na tabela
`RANK_GATE_ACTIONID`) — todo jogador já nasce rank Genin
(`NarutoRanks.get()` retorna índice 1 por padrão), então o item físico
continua no tile (mesma posição/largura) mas NUNCA barra ninguém. Placa
trocada de "Além daqui: nível Chunin ou superior." pra "Costa das Marés -
nível recomendado 12+." (não é mais um requisito, é uma sugestão). Ruínas
(Chunin) e Montanha (Jonin) continuam com seus gates originais, coerentes
com a tabela acima.

`data/ranks.json` ainda lista `costa_das_mares` em `unlocks.areas` do rank
Chunin — inconsistência de DADO que não afeta o jogo real (ver nota na
tabela de gates acima), fora do escopo desta missão de mapa (não editei
`data/ranks.json`).

### A2 — spawn solto do Aprendiz Mascarado

`masked_apprentice` só existia como reforço invocado na fase 60% HP do
Espadachim da Névoa — sem spawn próprio, `q_coastal_apprentice` (matar 6)
era praticamente impossível. Adicionado grupo de 3 unidades (respawn 90s)
em `build_coastal_tides`, centro `(1029, 1153)` raio 5, posições exatas
`(1025,1152)`, `(1032,1153)`, `(1030,1154)` — praia aberta entre o grupo do
Guardião da Neblina (`(1029, 1139)`) e a arena do boss (`boss_pos`,
`(1029, 1166)`), longe das 4 cabanas de pescadores e dos postes de
amarração.

### B1 — Ancião Kaito e Tsubaki (Ruínas)

Nunca tinham sido posicionados (só existiam em `data/npcs/ruins.json`, sem
spawn). Adicionados em `build_ruins`, mesmo padrão do Mestre de Tarefas
Dokan (perto do gate/entrada): **Ancião Kaito** (`quest_giver_ruins`) em
`(1205, 1022)`, **Tsubaki, a Escavadora** (`merchant_ruins`) em
`(1207, 1022)` — chão aberto do pátio, 2 tiles a leste/sul do corredor
estreito de entrada (que continua livre, sem bloqueio de passagem).

### B2 — spawn solto da Serpente Menor

`lesser_serpent` só existia em `data/maps/forest_valley.json` (protótipo
Godot abstrato, mapa 200×40) — sem spawn no OTBM real, `q_lesser_serpents`
ficava praticamente impossível. Os 3 pontos originais (zona "Floresta da
Morte" desse JSON, rect local `[50,0,46,40]`: `(74,18)`, `(82,8)`, `(86,34)`)
foram convertidos pra globais por escala proporcional dentro do retângulo
real da zona (`DEATH_WALL = (1130,1000,1199,1119)`, fórmula `real = origem +
fração_local × tamanho_real`), depois deslocados alguns tiles pra não
empilhar em cima da Torre (rect protegido) nem das outras clareiras.
Adicionados a `DEATH_CLEARINGS`/`DEATH_SETS` em `tools/map/build_valley.py`
(mesma lista/mecanismo das clareiras existentes — carve automático +
conexão à trilha principal + spawn):

| Clareira nova | Centro (x, y) | Raio | Serpente Menor |
|---|---|---|---|
| Charco das Serpentes Menores | 1158, 1048 | 4 | 3 unidades, respawn 90s |
| Poça Turva | 1178, 1030 | 4 | 2 unidades, respawn 90s |
| Juncal do Sul | 1188, 1105 | 4 | 3 unidades, respawn 90s |

### C1 — Mestra Yuki e Ferreiro Genzo (Montanha)

Nunca tinham sido posicionados — bloqueava as 7 missões da Montanha e as 2
metades do Exame Anbu. **Diferente** do Mestre de Tarefas Kaji (posicionado
DEPOIS do gate, já dentro da zona Jonin — ok pra um quadro de tarefas
repetíveis), o dador de missão/mercador precisa ficar acessível a quem AINDA
NÃO é Jonin: é a missão de Yuki que guia o jogador até o Exame Anbu, então
ela não pode depender do próprio gate que a missão dela ajuda a superar
(mesmo paradoxo que a Floresta da Morte evita com o Chunin). Aberto um
pequeno "posto avançado" (`build_mountain`, patamar 7 tiles de largura, 3
tiles ANTES do gate, no lado Ruínas): **Mestra Yuki** (`quest_giver_mountain`)
em `(1222, 1058)`, **Ferreiro Genzo** (`merchant_mountain`) em
`(1228, 1058)` — o corredor central (largura 1) fica livre entre os dois,
sem bloquear a passagem até o gate/Kaji.

### Validador cruzado — `tools/map/validate_world.py`

Script novo, roda DEPOIS de `tools/map/build_valley.py` (que gera o
`.otbm`/`-spawn.xml` em `server/generated/world/`). Lê `data/npcs/*.json`,
`data/tasks.json`, `data/dailies.json`, `data/monsters/*.json` e
`server/generated/world/valley-spawn.xml`/`valley.otbm`; falha (exit 1) se:

(a) algum `monster_id` exigido por `objective.kill` de missão/tarefa/diária
não tem spawn no XML — exceto `invoked_path`/`crimson_echo` (reforços de
fase do boss final do Covil, nunca spawn solto, listados em
`SUMMON_ONLY_MONSTERS` no topo do script); (b) algum NPC com `quests` ou
`type=="shop"` não está no XML (por nome exato); (c) algum NPC/monstro do
XML está numa posição não caminhável (mesma regra real do TFS que
`tools/map/walk_audit.py` usa — chão/item `blockSolid`; NPC aceita raio 3,
monstro exige célula exata).

Rodado após o Lote M: confirma os 5 itens acima (21 NPCs, todos os nomes de
Kaito/Tsubaki/Yuki/Genzo/Aprendiz Mascarado/Serpente Menor presentes e
caminháveis) e revela **1 problema pré-existente fora do escopo desta
missão**: `forest_deer` ("Cervo") é exigido por 4 tarefas
(`data/tasks.json`) mas não tem nenhum spawn no mapa — mesma classe de bug
do B2, mas não estava na lista de itens deste Lote; ver `data/maps/
forest_valley.json` (2 pontos já desenhados, zona "Floresta da Vila", nunca
portados). Não corrigido aqui (fora de escopo); marcado como tarefa de
acompanhamento.

### Rebuild e instalação

`.venv/bin/python tools/map/build_valley.py` (0 problemas) →
`tools/map/walk_audit.py` (2 divergências, ambas pré-existentes — portas
fechadas da Arena/Vila, nada novo) → `tools/map/validate_world.py` (1 falha,
`forest_deer`, fora de escopo — ver acima) → copiado `valley.otbm`/
`valley-spawn.xml`/`valley-house.xml` pra `server/tfs/data/world/`.
Servidor **não** foi reiniciado (sessão de jogo em andamento).
