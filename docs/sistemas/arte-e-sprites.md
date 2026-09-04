# Sistema de arte e sprites

## Objetivo

O OTClient só desenha alguma coisa se existir um par `Tibia.spr` + `Tibia.dat`
da versão 10.98 em `client-otc/data/things/1098/`. Como **nenhum sprite da Tibia
ou de NTO pode ser usado** (ADR-002) e não há ObjectBuilder no Mac, o projeto tem
seu próprio compilador de assets: `tools/spr/`.

## Pipeline

```
data/tfs_mapping.json ─┐
items.otb.vanilla ─────┤
                       ├─> tools/spr/gen_placeholders.py   (itens que JÁ existem)
tools/spr/art.py ──────┘        │
                                ▼
                assets-src/sprites/**.png + manifest.json ──┐
                                                            │
tools/spr/gen_tiles.py ─> assets-src/sprites/tiles/*.png    │
                          + tiles.json (à mão)         ─────┤ (itens NOVOS)
                          + allocations.json (ids)          │
                                                            ▼
                                            tools/spr/build_assets.py
                                                            │
                    ┌───────────────────────┬───────────────┴──────────────┐
                    ▼                       ▼                              ▼
   client-otc/data/things/1098/   server/tfs/data/items/     server/generated/items/
     Tibia.spr + Tibia.dat            items.otb              items_tiles_naruto.xml
                    │                       │
                    ▼                       ▼
       tools/spr/dump_dat.py      tools/spr/test_otb_roundtrip.py
```

- **Fonte da verdade da arte:** `assets-src/sprites/` (PNGs) + `manifest.json`
  (itens que já existem no OTB) + `tiles.json` (itens **novos** de cenário).
- **Artefatos gerados:** `client-otc/data/things/1098/Tibia.spr` e `Tibia.dat`,
  `server/tfs/data/items/items.otb` e
  `server/generated/items/items_tiles_naruto.xml`. Nunca edite à mão; regenere.
- **Especificação do formato binário:** `tools/spr/FORMATO.md` (derivada do código
  do próprio cliente, não de documentação de terceiros).
- **Como usar:** `tools/spr/README.md`.

## Regra de ouro: cobertura de ids

O `.dat` é lido **sequencialmente**. O cabeçalho declara o maior id de cada
categoria e o cliente lê um registro para cada id do intervalo. Portanto:

- Itens: precisa existir um thing para **todo clientId referenciado pelo
  `items.otb`** do TFS (hoje 100..23725). Um id faltando desalinha o arquivo e o
  cliente falha com `corrupt data` ou desenha lixo.
- Criaturas: precisa cobrir **todo looktype citado nos XML de monstro e NPC do
  TFS** (`server/tfs/data/monster/**/*.xml`, `server/tfs/data/npc/*.xml`), sem
  buracos, até o maior deles. O mapa padrão traz centenas de monstros vanilla;
  faltando um looktype o cliente registra
  `ProtocolGame::getThing: invalid thing id`.
- Efeitos e missiles: o protocolo 10.98 manda esses ids em **U8**, então o
  intervalo obrigatório é **1..255** — o servidor pode mandar qualquer um deles.

Por isso o build lê o `items.otb` e cria um placeholder genérico para cada id,
o gerador varre os XML do servidor atrás de `look type="..."`, e os ids do
`data/tfs_mapping.json` são sobrescritos com arte específica. Assim o mapa
padrão do TFS (`forgotten.otbm`) renderiza inteiro.

## Segunda regra: o `.dat` precisa bater com o protocolo

Carregar sem erro não basta. O TFS decide quantos bytes extras manda por item
lendo o `items.otb`; o cliente decide quantos ler lendo o `.dat`. Divergir
desalinha o pacote de mapa inteiro (`getThing: invalid thing id`). O que precisa
casar 1:1 (detalhes em `tools/spr/FORMATO.md`, seção 5):

| `items.otb` | `.dat` |
|---|---|
| `FLAG_STACKABLE` | atributo `Stackable` |
| grupo `fluid` | atributo `FluidContainer` |
| grupo `splash` | atributo `Splash` |
| `FLAG_ANIMATION` | **`animationPhases >= 2`** — não é atributo, é geometria |

O caso do `FLAG_ANIMATION` já custou um bug: água, tochas e fogo do mapa padrão
fazem o servidor mandar um byte `0xFE` que o cliente só consome se o thing tiver
mais de uma fase. O build gera 2 fases (mesmo sprite nas duas) para os 2.083
clientIds animados, e `dump_dat.py` confere os quatro flags item a item.

## Criando itens NOVOS (cenário próprio)

Até aqui o pipeline só sabia **dar arte** a itens que já existiam no `items.otb`
do TFS. Para casa de vila ninja, portão torii, placa, móvel, chão de tatame etc.
é preciso **criar** o item, e isso são três arquivos ao mesmo tempo:

| Onde | O quê |
|---|---|
| `server/tfs/data/items/items.otb` | serverId novo → clientId novo, grupo (`itemgroup_t`) e flags (`itemflags_t`) |
| `client-otc/data/things/1098/Tibia.dat` + `.spr` | o *thing* daquele clientId: geometria, fases, atributos de render |
| `server/tfs/data/items/items.xml` | nome, descrição e atributos de gameplay do serverId |

O `tools/spr/build_assets.py` faz os três a partir de
**`assets-src/sprites/tiles.json`** (manifesto mantido à mão) — o passo a passo
está em `tools/spr/README.md`, seção "Itens NOVOS de cenário".

### Regras de id

- **Server id a partir de 30000** (o `items.otb` vanilla vai até 26381).
- **Client id a partir de 23726**, sequencial e **contíguo** com o vanilla
  (que vai até 23725). Um buraco desalinha o `.dat` inteiro.
- A alocação fica em **`assets-src/sprites/allocations.json`**, indexada pela
  `key` do tile, e é **append-only**: um id já alocado nunca é renumerado nem
  reaproveitado — mapas e saves já gravados apontariam para outro item. Apagar um
  tile do `tiles.json` só aposenta o id.

### Fatiando uma folha de prédios (`slice_buildings.py`)

Arte externa (RPG Maker etc.) chega como uma folha grande em
`assets-src/import/` — pasta de **uso privado, no `.gitignore`**, nada de lá é
versionado. `tools/spr/slice_buildings.py` transforma a folha em itens:

```bash
.venv/bin/python tools/spr/slice_buildings.py --align       # só o relatório de grade
.venv/bin/python tools/spr/slice_buildings.py --components  # só o teste de componentes
.venv/bin/python tools/spr/slice_buildings.py               # fatia e escreve tudo
```

1. **Alinhamento.** Testa os 32 deslocamentos possíveis em x e em y e escolhe o que
   minimiza a soma de pixels opacos **em cima das linhas de grade** — a grade certa é
   a que corta menos desenho. Para `village_buildings.png` (256x1024) o resultado é
   offset `(0, 0)`, grade **8 colunas x 32 linhas**. A folha `_grid.png` mostra a
   grade sobreposta para conferência visual.
2. **Células.** Recorta 32x32 e descarta as células com menos de 8 pixels opacos.
3. **Prédios.** O método natural — componentes conexos na grade — **não funciona nesta
   folha**: os prédios se encostam e as 243 células não-vazias formam **um único**
   componente. Por isso a segmentação é a tabela `SEGMENTS` do script, feita à mão em
   cima da folha de revisão. `--components` continua disponível para conferir isso em
   folhas futuras (se der um componente por prédio, dá para automatizar).
4. **Dedup.** Células com os mesmos pixels (SHA1 do RGBA) viram **um item só**; a
   primeira ocorrência define a `key` e as repetições apontam para ela. Nesta folha o
   ganho foi pequeno (243 células → 242 tiles): o telhado laranja repete a forma mas
   varia o sombreado pixel a pixel.
5. **Porta.** Heurística: na **linha de baixo** do prédio, a célula mais central com
   maior fração de pixels escuros (a abertura). A tabela `SEGMENTS` pode fixar a porta
   à mão em coordenadas locais.

Saídas:

| Caminho | O quê | Versionado? |
|---|---|---|
| `assets-src/import/extracted/buildings/<predio>/<col>_<row>.png` | células para revisão | não |
| `assets-src/import/extracted/buildings/_review.png` | folha numerada, caixa e porta por prédio | não |
| `assets-src/sprites/tiles/buildings/<key>.png` | a arte de fato | **sim** |
| `assets-src/sprites/tiles.json` | um item por célula única (`bld_*`) | **sim** |
| `assets-src/sprites/buildings.json` | matriz de chaves + porta, por prédio | **sim** |

Grupos escolhidos: corpo do prédio → `wall` (bloqueia, `blocks_projectile`); célula de
porta → `door` + `walkable: true`; postes, árvores e arbustos → `decoration` bloqueante
1x1; muros/painéis verdes → `wall`. **Em Tibia tudo do prédio bloqueia menos a porta** —
não existe "telhado por cima", então nada vira `on_top`. Como não há interior, o NPC de
uma loja fica na rua, à frente da porta (ver `docs/sistemas/mapas.md`).

### Alocar ids sem construir (`allocate_ids.py`)

`build_assets.py` aloca os ids como efeito colateral de reescrever `items.otb`,
`Tibia.dat` e `Tibia.spr`. Quando só os **ids** são necessários — por exemplo para
gerar o mapa antes do build de assets, ou enquanto outra pessoa está rodando
`build_assets.py` — use:

```bash
.venv/bin/python tools/spr/allocate_ids.py            # grava allocations.json
.venv/bin/python tools/spr/allocate_ids.py --dry-run  # só mostra o que faria
```

Mesma regra sequencial de `tools/spr/tiles.py::allocate` (append-only, 30000/23726).
Diferença deliberada: **não lê o `items.otb`** — ele pode estar sendo reescrito neste
instante. Não há risco de colisão porque o OTB vanilla para no server id 26381 e no
client id 23725.

### Backup do `items.otb`

A primeira gravação copia o OTB original para
**`server/tfs/data/items/items.otb.vanilla`** (uma única vez). A partir daí o
`.vanilla` é sempre a **base** do build: os 26.282 itens de fábrica são
reescritos byte a byte a partir dele e os tiles próprios são anexados no fim.
O build é idempotente — rodar duas vezes dá o mesmo arquivo, sem duplicar nada.

`tools/spr/test_otb_roundtrip.py` prova essa propriedade: lê um `items.otb`,
reescreve e compara (1) byte a byte, (2) campo a campo os dois parses e
(3) a serialização "do zero" (o caminho dos itens novos, que não têm bytes
originais para preservar).

Para voltar ao OTB de fábrica: `cp items.otb.vanilla items.otb` e rode o build
com `--no-otb`.

## Importar folhas de sprites (`import_sheets.py` + `imports.json`)

Arte de verdade chega como **folhas soltas**: um PNG com dezenas de sprites
espalhados sobre uma cor de fundo chapada, sem grade. O material fica em
`assets-src/import/`, que está no **`.gitignore`** (ADR-002: nada de terceiros é
versionado). O pipeline tem duas metades:

### 1. Extrair (`tools/spr/import_sheets.py`)

```bash
.venv/bin/python tools/spr/import_sheets.py                 # as folhas padrão
.venv/bin/python tools/spr/import_sheets.py folha.png --dilate 2 --tol 12
```

O que faz, em ordem:

1. **Detecta o fundo** = cor RGB mais comum da imagem. O verde `34,177,76`
   (retângulo de "chroma key" que algumas folhas trazem) é sempre tratado como
   fundo também, então os sprites de dentro dele saem recortados junto.
2. Monta a **máscara**: pixel opaco cuja cor esteja a mais de `--tol` por canal do
   fundo. O `.spr` 1098 é RGB, então o alpha vira binário mesmo.
3. **Dilata** a máscara (`--dilate`, raio em px) só para calcular a conectividade:
   junta partes soltas do mesmo sprite (cauda, chama, ponta de arma) sem colar
   sprites vizinhos. O raio certo é por folha — está em `DEFAULT_SHEETS`:
   `monsters_sheet` = 1, `npcs_sheet` = 0 (os sprites quase se encostam).
4. Rotula os **componentes conexos** (8-vizinhos) e descarta o que for menor que
   `--min-area` / `--min-side` (respingos e os rótulos numéricos da folha).
5. Grava `assets-src/import/extracted/<folha>/<idx>.png` (só os pixels daquele
   componente, fundo transparente), um `<folha>.json` com bbox/tamanho de cada um,
   e a **folha de revisão** `<folha>_contact.png` — cada recorte numerado com o
   tamanho. **Sempre olhe o contact sheet** antes de mapear: é ele que mostra se
   um sprite ficou partido (aumente `--dilate`) ou colado no vizinho (diminua).

Limite conhecido: quando dois sprites se **sobrepõem de fato** na folha original
(dois aldeões encostados, um ninja cuspindo a bola de fogo), nenhum valor de
`--dilate` separa. Nesses casos use o campo `crop` do `imports.json` para pegar só
o pedaço que interessa.

### 2. Mapear (`assets-src/sprites/imports.json`)

Arquivo **versionado** (só referencia caminhos dentro de `extracted/`, que podem
não existir em outra máquina). `tools/spr/imports.py` o aplica **por cima** do
`manifest.json` durante o `build_assets.py`, com prioridade
**import > override de placeholder > regra de estilo**. Toda entrada cujo PNG de
origem não exista é **ignorada com aviso** — em outra máquina o build roda igual e
cai no placeholder.

```jsonc
{
  "root": "assets-src/import/extracted",
  "build_dir": "assets-src/import/extracted/_sheets",   // folhas montadas
  "creatures": [
    {"id": 61, "name": "stone_golem", "src": "monsters_sheet/21.png", "tiles": 4}
  ],
  "effects": [
    {"id": 7, "name": "firearea", "src": "monsters_sheet/35.png",
     "crop": [0, 46, 60, 60], "grow": [0.45, 0.75, 1.0, 0.9], "duration": 90},
    {"id": 3, "name": "poff", "frames": ["…/82.png", "…/83.png", "…/84.png"]}
  ],
  "missiles": [ {"id": 9, "name": "kunai", "src": "…/46.png", "rotate": -90} ],
  "items":    [ {"name": "scroll", "src": "…/10.png", "server_ids": [1948, 1949]} ]
}
```

| campo | vale para | o que faz |
|---|---|---|
| `id` | creature/effect/missile | looktype, `CONST_ME_*` ou `CONST_ANI_*` (`server/tfs/src/const.h`) |
| `src` / `frames` | todos | recorte(s) em `extracted/`; `frames` viram fases de animação |
| `crop` | todos | `[x, y, w, h]` dentro do recorte (para separar sprites colados) |
| `tiles` | creature/effect | lado da caixa em tiles de 32 px (1..4); sem ele, automático |
| `grow` | effect | gera as fases escalando um único recorte (explosão crescendo) |
| `duration` | effect | ms por fase |
| `rotate` | missile | ângulo (graus, 0 = direita) para onde a arte aponta; as 9 direções são geradas girando |
| `server_ids` | item | ids do TFS (`data/tfs_mapping.json`); o build traduz para clientId pelo `items.otb` |

### Encaixe na grade da Tibia

Cada recorte vira um thing de **1×1 (32 px), 2×2 (64), 3×3 (96) ou 4×4 (128)**.
O `.dat` guarda `width`/`height` em U8 e o `exactSize` só existe quando algum dos
dois passa de 1 — `sprformat.py` já fazia isso genericamente, então 3×3 e 4×4
saíram de graça (o golem de pedra é 4×4 e a raposa 3×3, ambos testados no cliente).

- `auto_tiles`: cabe no tile de baixo enquanto o lado maior for ≤ `tiles*32*1.45`;
  acima disso sobe um tamanho. O recorte é reduzido com LANCZOS e o alpha volta a
  ser binário (`>= 128`).
- **Criaturas**: ancoradas embaixo e centralizadas na horizontal — é assim que o
  Tibia desenha (o tile do bicho é o canto inferior direito da caixa).
- **Efeitos/missiles/ícones**: centralizados nos dois eixos. Ícone de item menor
  que metade do tile é ampliado 2× com NEAREST.

### Criaturas importadas usam `layers = 1`

O placeholder tem 2 camadas (base + template de cores de outfit). A arte
importada já vem colorida, então vai com **`layers = 1`**: o cliente só aplica
`head/body/legs/feet` quando `layers == 2`, logo os valores do `tfs_mapping.json`
passam a ser ignorados nesses looktypes. Consequência direta: **monstros que
compartilham looktype ficam idênticos** (ex.: `bandit` e `bandit_archer` são os
dois o 129). Como não há direções nem quadros de andar no material, a mesma
imagem vai nas 4 direções e nas 3 fases de caminhada.

### Receita completa

```bash
.venv/bin/python tools/spr/import_sheets.py     # 1. recortar + folha de revisão
# 2. olhar assets-src/import/extracted/<folha>_contact.png e editar imports.json
.venv/bin/python tools/spr/build_assets.py      # 3. compilar .spr/.dat
.venv/bin/python tools/spr/dump_dat.py          # 4. validacao: OK, divergencias=0
```

## Convenções de arte

- Célula de 32×32, "chão" na linha y=30, fundo transparente.
- Alpha é binário (o formato 10.98 é RGB): `alpha < 128` = transparente.
- Criaturas usam **2 camadas**: base clara + template de máscara com
  vermelho=body, verde=legs, azul=feet, amarelo=head. As cores vêm do servidor
  (`data/tfs_mapping.json`, campos `head`/`body`/`legs`/`feet`).
- Criaturas têm 4 direções (Norte, Leste, Sul, Oeste) e 2 frame groups:
  parado (1 fase) + andando (3 fases).
- Chefes ocupam 2×2 tiles (64×64). Os **20 looktypes acima do maior usado pelo
  servidor** (hoje **878–897**) ficam reservados para chefes 2×2; para usar,
  aponte o `looktype` do monstro em `data/tfs_mapping.json` para um deles.
  A faixa é recalculada a cada `gen_placeholders.py`, então confira a saída do
  script antes de fixar um id.

## O que existe hoje (placeholder)

| Categoria | Cobertura |
|---|---|
| Itens | 23.626 things (clientId 100..23725 — cobertura total do `items.otb`), por estilo: chão tingido pela cor de minimapa, parede, contêiner, pilha, item de mochila, decoração, poça, fluido |
| Itens próprios | um ícone desenhado por item de `data/tfs_mapping.json` (kunai, shuriken, colete, pergaminho, poção, pelagem, ryo...) — 78 clientIds |
| Criaturas | looktypes 1..897 — os do `tfs_mapping.json` ganham arte temática (lobo/fera, cobra, sapo, sanguessuga, ninja, bandido); os looktypes vanilla do mapa do TFS viram fera genérica cinza (6 variantes); 878..897 são chefes 2×2 |
| Efeitos | ids 1..255 — 1..70 com arte própria (explosão, faíscas, fumaça, corte, pulso, 4–7 fases), 71..255 placeholder simples de 3 fases |
| Missiles | ids 1..255 — 1..50 com arte própria (shuriken, raio, orbe), 51..255 placeholder simples, todos em grade 3×3 de direções |
| Cenário próprio | 8 itens **criados do zero** (serverId 30000–30007, clientId 23726–23733): chão de tatame, terra batida de vila, parede de madeira (vertical e horizontal), portão torii 2×1, placa de madeira, lanterna de papel com luz (2 fases) e cerca de bambu — ver `assets-src/sprites/tiles.json` |

## Quando trocar por arte definitiva

1. Desenhe o PNG no layout de folha descrito em `tools/spr/README.md`.
2. Aponte a entrada correspondente no `manifest.json`.
3. Rode `build_assets.py` e depois `dump_dat.py`; a saída precisa terminar em
   `validacao: OK`.
4. Se o `manifest.json` for regenerado por `gen_placeholders.py`, as edições
   manuais se perdem — a intenção é que, com o tempo, o manifesto passe a ser
   mantido à mão e o gerador de placeholders seja aposentado.

## Limitações conhecidas

- Sem addons de outfit (`pattern_y = 1`) e sem montarias (`pattern_z = 1`):
  o `addons: 3` do `rogue_ninja` simplesmente não aparece.
- Itens não têm variação de padrão: chão não tem as 4×4 variações da Tibia e
  pilhas não mudam de sprite conforme a quantidade.
- Itens animados têm as 2 fases exigidas pelo protocolo, mas as duas apontam para
  o mesmo sprite — então nada se mexe de fato. Para animar de verdade, basta dar
  sprites diferentes às duas fases.
- Frente e costas de algumas feras são quase iguais (mudam só os olhos).
- A maioria dos looktypes (os vanilla do mapa do TFS) é a mesma fera cinza em 6
  variantes de tom: serve para o cliente não errar, não para reconhecer o monstro.
- Todos os humanoides compartilham a mesma base; a diferença entre monstros e NPCs
  vem inteiramente das cores de outfit do `tfs_mapping.json`.
- Um tile de `size: [2,1]` desenha 2 casas de largura mas **ocupa uma só casa** no
  servidor (o desenho se estende para oeste/norte, como na Tibia). Cenário que
  precise bloquear várias casas tem que ser montado com vários itens.
- Os tiles novos não têm variação de borda automática: não existe autoborder nem
  as 4×4 variações de chão que o RME espera. Cada variação é um item à parte.
- `tiles.json` não gera `items.otbm`/`materials.xml` para o editor de mapas: por
  ora os itens novos são colocados por script/GM (`/i <serverId>`), não pelo RME.
- Sprite importado que compartilha looktype com outro monstro/NPC fica idêntico a
  ele: com `layers = 1` as cores de outfit do `tfs_mapping.json` não se aplicam.
- A arte importada não tem direções nem quadros de andar: as 4 direções e as 3
  fases de caminhada usam a mesma imagem (o bicho "desliza").
- Sprites que se sobrepõem na folha original não são separáveis por componente
  conexo; só com `crop` manual no `imports.json`.
- Recortes maiores que 128 px são reduzidos para caber em 4×4 (o `.dat` não vai
  além disso na prática); recortes entre 32 e 45 px são reduzidos para 1×1, o que
  perde um pouco de nitidez nos humanoides.
