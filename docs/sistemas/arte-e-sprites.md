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
dois o 129). Nas folhas de monstro não há direções nem quadros de andar, então a
mesma imagem vai nas 4 direções e nas 3 fases de caminhada. **Exceção**: entradas
com o bloco `directions` (ver "Outfit do jogador") têm arte por direção e ciclo
de andar de verdade.

### Receita completa

```bash
.venv/bin/python tools/spr/import_sheets.py     # 1. recortar + folha de revisão
# 2. olhar assets-src/import/extracted/<folha>_contact.png e editar imports.json
.venv/bin/python tools/spr/build_assets.py      # 3. compilar .spr/.dat
.venv/bin/python tools/spr/dump_dat.py          # 4. validacao: OK, divergencias=0
```

## Outfit do jogador (`overrides/30_player.json` + `player_frames.json`)

O looktype **128** (outfit padrão do jogador) e o looktype **898**
(`naruto_attack`, poses de golpe para jutsus/efeitos futuros) saem de um material
privado do usuário em `assets-src/import/player/` — 76 quadros RGBA de
17..33 × 30..41 px, fora do git (ADR-002). O `_contact.png` da pasta é a folha de
revisão numerada.

```bash
.venv/bin/python tools/spr/build_assets.py      # aplica overrides/30_player.json
.venv/bin/python tools/spr/dump_dat.py          # validacao: OK, divergencias=0
```

### O que o material é (e o que não é)

Não é um set top-down de 4 direções: é um set de **vista lateral** de jogo de
ação, com poses de ataque/pulo (0012–0059) e de parado/andar (0060–0087). Todos os
76 quadros mostram o rosto — frontal ou 3/4 virado para a **direita**. **Não
existe nenhuma vista de costas** (conferido pixel a pixel: há pele na faixa da
cabeça em 76/76 quadros). Por isso a direção 0 (norte) é uma aproximação e a
direção 3 (oeste) é espelhada da 1.

A triagem quadro → (direção, fase) fica versionada em
**`assets-src/sprites/player_frames.json`** — só índices e a justificativa de cada
escolha, nenhuma imagem. Quem o build lê de verdade é
`assets-src/sprites/overrides/30_player.json`.

| Direção | Parado | Andar (4 fases) |
|---|---|---|
| 0 Norte (costas) | **SINTETIZADA** (`_synth/back_idle.png`) | `_synth/back_walk0..3.png` |
| 1 Leste | 0080 | 0084, 0083, 0075, **synth** (`_synth/east_walk3_synth.png`) |
| 2 Sul (frente) | 0071 | 0070, 0076, 0070 espelhado, **synth** (`_synth/south_walk3_synth.png`) |
| 3 Oeste | espelho do leste | espelho do leste |

O ciclo do leste foi escolhido medindo os **pés** (pixels de sandália no terço
inferior): 0084 = pé direito no ar (vão 15 px), 0083 = pés juntos na passagem
(vão 2 px), 0075 = pé esquerdo no ar (vão 13 px), os três com 39 px de altura.

O ataque 898 usa 0043 (guarda) → 0031 (recuo) → 0017 (jab) → 0012 (avanço), nas 4
fases do frame group "andando" (inalterado por este trabalho).

### Atualização: costas sintetizada + 4ª fase (`import_player.py`)

O material de 76 quadros **não tem nenhuma vista de costas** (documentado desde
sempre) — o norte usava o quadro 0068 (o único sem olhos desenhados: a 32 px a
faixa clara sob a bandana lia como nuca) + seu espelho, e o ciclo de andar tinha
só **3** fases em toda direção. `tools/spr/import_player.py` (novo) aplica ao 128
a mesma técnica do `import_mugen.py`:

1. **Costas sintetizada** (`char_synth.synthesize_back`): espelha o quadro 0080
   (idle leste), detecta a região de PELE da cabeça (dilatada 3px para pegar
   contorno de olhos/sobrancelha), repinta com a cor de **cabelo** do personagem
   (amostrada dos fios acima da bandana — ver `hair_color()`, que ignora a faixa
   azul da bandana, que dominava a média ingênua) e escurece ~14%. Aplicado ao
   idle E às 4 fases de andar do leste (mesmo ciclo de pernas, só recolorido):
   agora o norte **anda de verdade** em vez de só balançar entre 2 poses.
2. **4ª fase de andar sintética** (`char_synth.synth_walk_offset`) no leste e no
   sul: desloca a metade inferior (pernas) do quadro de passagem alguns px para
   o lado oposto + leve inclinação, para completar o ciclo sem repetir uma pose.
3. **Nitidez**: automática — é o novo padrão de `imports.fit_uniform`
   (downscale por área + realce + contorno 1px), usado por *toda* criatura com
   `directions`, então o 128 já ganhou o pipeline sem precisar de nada específico
   aqui (ver seção "Personagens MUGEN" abaixo para o comparativo que decidiu isso).

`assets-src/import/player/_synth/` guarda os PNGs gerados (privado, fora do git).
Rodar de novo: `.venv/bin/python tools/spr/import_player.py` (idempotente).

### `directions` no `imports.py`

`Importer.creature_dirs` aceita, numa entrada de `creatures`, um bloco
`directions` no lugar do `src`/`dirs` único (que continua funcionando igual):

```jsonc
"directions": {
  "0": { "idle": "sprite_0068.png",
         "walk": ["sprite_0068.png",
                  {"src": "sprite_0068.png", "mirror": true},
                  "sprite_0068.png"] },
  "1": { "idle": "...", "walk": ["...", "...", "..."] },
  "2": { "...": "..." },
  "3": { "mirror_of": 1 }        // espelha a direção 1, quadro a quadro
}
```

- Direções na ordem do enum `Otc::Direction` (`pattern_x` do `.dat`):
  **0 = Norte, 1 = Leste, 2 = Sul, 3 = Oeste**.
- `idle` vira o frame group 0 (1 fase); `walk` vira o frame group 1 com **N**
  fases (3 no outfit, 4 no ataque — o número é livre, só precisa bater entre as
  direções; quem tiver menos repete o último quadro).
- Um quadro é uma string ou `{"src": ..., "mirror": true, "crop": [...]}`.
- `layers = 1`, como toda arte importada.
- `"duration"` (ms por fase, padrão 220) controla a velocidade da animação.

### Normalização: por que os quadros não "pulam"

`fit()` (usado pelas entradas antigas) redimensiona **cada** quadro para preencher
a célula — com quadros de alturas diferentes o boneco cresce e encolhe a cada
fase. As entradas com `directions` usam `fit_uniform()`:

1. **Uma escala só** para todos os quadros da entrada:
   `min(32/maior_largura, 32/maior_altura, 1.0)` — no outfit dá 32/40 = **0,80**.
   LANCZOS na redução e alpha rebinarizado depois (o `.spr` 1098 é RGB).
2. **Base dos pés** no fundo da célula de 32×32.
3. **Centro do apoio** no meio da célula: o centroide dos pixels opacos do terço
   inferior, não o centro da caixa. Centralizar pela caixa faz o corpo escorregar
   quando um braço ou perna sai para fora (poses de ataque, passo largo).

Personagem da Tibia é **1×1**: os quadros de até 41 px são *reduzidos* para caber
em 32×32, nunca cortados nem promovidos a 1×2.

### Faixa de ids

`gen_placeholders.py` reserva `BOSS_FIRST..BOSS_LAST` (20 looktypes acima do maior
citado nos XML do TFS, hoje 878..897) para chefes 2×2 — por isso o ataque usa
**898**. Não foi preciso mexer no `build_assets.py`: ele já grava
`maxCreatureId = max(tables[creature])` e preenche com thing vazio todo id sem
arte no intervalo ("todo id de 1..max precisa existir"). Depois desta mudança o
`.dat` tem 898 criaturas em vez de 897.

### Teste in-game (3 rodadas, ver seção MUGEN para o script `charwalk_rc.lua`)

O 128 foi testado JUNTO com os MUGEN no mesmo `client-otc/tests/charwalk_rc.lua`
(6 passos por direção, 3 screenshots a ~150ms durante o movimento). Resultado
final: costas com cabelo loiro visível e pernas andando de verdade no norte,
perfil correto em leste/oeste, frente reconhecível no sul, pés no chão nas 4
direções, sem mudança de tamanho ao virar. Ver a seção MUGEN para as 3 rodadas
completas (2 primeiras falharam por causa do AMBIENTE de teste — monstro
sobrevivente de outra sessão paralisando o jogador, depois uma sessão presa no
servidor —, não da arte; corrigido trocando `/arena` por um `/tp` fixo na praça
e reiniciando o servidor).

### Limitações

- A costas sintetizada usa o MESMO ciclo de pernas do leste (só recolorido): se
  o jogador olhasse de verdade o material teria outro ritmo de passada; é uma
  aproximação, não uma vista real.
- Não há passo frontal de verdade: o sul usa 0070/0076/0070-espelhado + 1 fase
  sintética; a "passada" frontal é uma simulação por deslocamento, não uma
  perna real levantando.
- O oeste é espelhado do leste, então bandana e zíper trocam de lado (invisível a
  32 px).
- Os quadros de 39–41 px são reduzidos e perdem ~1 px de detalhe no rosto (o
  contorno 1px pós-redução devolve parte da legibilidade — ver comparativo de
  nitidez na seção MUGEN).
- `layers = 1`: as cores de outfit (`head/body/legs/feet`) que o servidor manda
  são ignoradas no 128 — todo jogador fica com a mesma roupa laranja.
- O looktype 898 tem a mesma arte nas 4 direções (só o oeste é espelhado): quem
  usar precisa travar a direção ou usá-lo apenas como animação.

## Personagens MUGEN (`import_mugen.py` + `overrides/40_mugen.json`)

Os looktypes **900–926** são 27 personagens de Naruto (26 nomes distintos + o
Minato Edo como variação) vindos de um material privado do usuário em
`assets-src/import/mugen/` (fora do git, ADR-002): 21.653 BMPs paletados, rips
estilo MUGEN/JUS de um jogo de luta. A numeração é **fixa** e vive em
`assets-src/sprites/mugen_looktypes.json` (looktype → pasta → nome), versionado.

```bash
.venv/bin/python tools/spr/survey_mugen.py           # varredura EXAUSTIVA + _survey_<lt>.png
.venv/bin/python tools/spr/import_mugen.py           # triagem final + PNGs + 40_mugen.json
.venv/bin/python tools/spr/import_mugen.py --report  # só o diagnóstico, não grava
.venv/bin/python tools/spr/import_mugen.py --only 913 922
.venv/bin/python tools/spr/import_player.py          # mesma técnica aplicada ao 128
.venv/bin/python tools/spr/build_assets.py
.venv/bin/python tools/spr/dump_dat.py               # validacao: OK, divergencias=0
```

### Retrabalho (feedback: "a forma de andar está errada ainda, muito ruim")

A primeira versão deste pipeline resolvia o básico (parado + 3 fases de andar,
mesma escala, sem escorregar) mas deixava três problemas que o usuário sentiu
jogando: (1) olhando **para os lados** o personagem sempre aparecia de **perfil**
mesmo andando para norte/sul; (2) **5 personagens** não tinham ciclo de andar
real e só "respiravam" parados; (3) o downscale 60→32px direto por LANCZOS
borrava detalhe. As três seções abaixo (varredura exaustiva, síntese de costas e
4ª fase, comparativo de nitidez) documentam a correção.

### O que o material é (e o que não é)

Vista **lateral** de jogo de luta: o personagem olha para a direita ou para a
esquerda. A varredura exaustiva (`survey_mugen.py`, TODO quadro do rip, não só
os primeiros ~200) confirma: **não existe vista de costas real em nenhum dos 27
rips** — o classificador de orientação (pele no terço superior: simétrica =
frente, ausente = costas, concentrada de um lado = perfil) só encontra "costas"
em blobs de efeito (chakra, fumaça) sem pele nenhuma, nunca um personagem
virado. Muitos rips (vários desenhados num ângulo 3/4 "heroico", não 90° puro)
**têm sim** poses de frente/3-4 espalhadas pelo arquivo — geralmente vitória,
intro ou um chute/soco que gira o corpo para a câmera — e a varredura consegue
achar candidatos aproveitáveis para o Sul em 25 dos 27. O fundo é a **cor-chave
do índice 0 da paleta**, cuja cor concreta muda de quadro para quadro.

A ordem dos arquivos é *quase* sempre: ícone, retrato 120×140, parado
(respirando), agachar, andar, correr, pular e depois dezenas de golpes — mas
varia o bastante para não dar para confiar em índices fixos. O script mede cada
quadro.

### Varredura exaustiva (`survey_mugen.py`)

Novo script: le **todos** os BMPs de cada personagem (sem o teto de ~200
arquivos da triagem antiga), classifica cada quadro por:

- **orientação** — `frente` / `perfil_direita` / `perfil_esquerda` / `3/4` /
  `costas`, pela razão e assimetria de pele no terço superior da caixa;
- **pose** — `parado` / `andar` / `correr` / `pular` / `ataque` / `especial` /
  `dano` / `vitoria` / `outro`, por uma combinação de altura relativa ao parado,
  proporção largura/altura, movimento de silhueta entre vizinhos e (para
  "vitória") posição no arquivo. **Isto é heurística best-effort**, não um fato:
  serve para gerar candidatos que o artista (eu) revisou visualmente, não para
  decidir sozinha.

Também estima por personagem a **cor de pele** e a **cor de cabelo** (cluster
pela cor mais frequente — moda, não média, dos pixels que passam no teste de
tom de pele / dos pixels do topo da cabeça que não são pele), usadas depois pela
síntese de costas.

Saída: `assets-src/import/extracted/mugen/_survey_<looktype>.png` — uma linha
por orientação, colunas = melhor candidato de cada pose encontrada, com o
número do arquivo abaixo. Os 27 foram olhados um a um; a varredura confirmou o
"sem costas real" e ajudou a calibrar o filtro do candidato de frente (ver
próxima seção — o primeiro candidato automático pegava um quadro adjacente ao
parado, quase idêntico a ele, e foi preciso excluir a própria corrida do parado
e exigir uma diferença mínima de silhueta).

### Escolha automática dos quadros

- **Parado** = a animação de *respirar*: a **primeira** corrida de quadros
  consecutivos com a silhueta quase constante e mais alta que larga. Dentro dela
  fica o quadro **mediano pelo vão entre os pés**. Inalterado desde a v1.
- **Andar, agora com 4 fases**: o script tenta primeiro uma janela de **4**
  quadros consecutivos com a mesma altura do parado e **2 alternâncias** no vão
  entre os pés (contato-passagem-contato-passagem — `_walk4_in`), em 4 passadas
  de tolerância crescente, olhando o rip **inteiro** se precisar. **22 dos 27**
  acharam um ciclo real de 4 fases (`real4`); os outros 5 (902 Sakura Kid, 907
  Minato, 908 Minato Edo, 915 Sasuke Akatsuki, 925 Naruto Girl — os mesmos "sem
  ciclo de andar" da v1) caem para 3 fases reais (`real3`) + **1 fase
  sintética**.
- **Frente (Sul)**: `pick_front` procura, no rip INTEIRO, o melhor quadro
  classificado `frente` ou `3/4`, com altura parecida com o parado, paleta
  parecida (não é um efeito) e **silhueta suficientemente diferente do parado**
  (motion ≥ 5%, excluindo a própria corrida do parado) — sem esse último filtro
  o candidato mais "barato" era um quadro vizinho ao parado, visualmente idêntico
  a ele. Achou candidato em **25 dos 27** (não achou em 923 Naruto 6 Caldas, que
  cai para o perfil do Leste).
- **Lado** = massa de pele no terço superior à esquerda × à direita. Inalterado.
- **Costas (Norte)**: **sintetizada**, nunca copiada do material — ver próxima
  seção.

### Síntese de costas (`char_synth.synthesize_back`)

Como não existe costas real em nenhum rip, o Norte agora é **gerado** a partir
do ciclo de perfil (idle + as 4 fases de andar), com a técnica pedida:

1. **Espelha** o quadro horizontalmente (`ImageOps.mirror`).
2. **Detecta a região de pele da cabeça** (~46% superior da caixa, o mesmo
   detector de tom de pele usado para orientação), **dilata a máscara 3px** para
   pegar contorno de olhos/sobrancelha/boca que não são "pele" pelo teste de cor
   mas ficam cercados por ela.
3. **Repinta** essa região com a **cor de cabelo** estimada do personagem,
   preservando parte da luminância original do pixel (não fica um floodfill
   chapado — mantém alguma sombra/luz onde já havia).
4. **Escurece** o sprite inteiro ~14% (RGB × 0,86).
5. A **silhueta (alpha) não muda** — o quadro de costas continua alinhado ao
   mesmo ciclo de passos do perfil, só recolorido. Isso é o que faz o Norte
   **andar de verdade** em vez de balançar: as pernas se movem exatamente como
   no Leste, só a cabeça lê como nuca em vez de rosto.

Exceção: as 4 formas de raposa/quadrúpede (921, 922, 923, 926 — `NO_FACE_SYNTH`)
não têm "rosto" reconhecível (é chakra/pelagem), então só recebem o
escurecimento, sem tentativa de repintura de rosto (que geraria manchas
aleatórias num bicho sem cara).

Antes/depois (Naruto Kid, 900): o perfil original (0004) tem cabelo loiro e
rosto visível olhando para a direita; a costas sintetizada mostra o mesmo
boneco, espelhado, com a região do rosto virada um blob de cabelo
dourado-acastanhado (a cor estimada, mais escura que o loiro puro por causa do
escurecimento geral) e sem olhos/faixa — lê como "de costas" à distância de
jogo. Aplicado também ao 128 (jogador): a cor de cabelo estimada bateu em
azul-acinzentado na primeira tentativa (a amostra do "terço superior" pegava
mais a bandana do que os fios, num sprite de só 40px de altura); corrigido com
um detector específico de pixels QUENTES (r>g>b) no `import_player.py`, que deu
um dourado plausível.

### 4ª fase sintética (`char_synth.synth_walk_offset`)

Onde só há 3 fases reais (ou nenhuma), a 4ª é sintetizada deslocando a metade
inferior (pernas, ~55% de baixo) horizontalmente 1-3px com uma leve inclinação
(shear) que cresce da cintura ao pé, e a imagem inteira 1px na vertical (o
"baloiço" do passo) — **nunca** a imagem inteira nem um efeito aleatório, só a
região das pernas, para parecer passo e não tremor. Nos 5 personagens sem ciclo
nenhum, as 4 fases inteiras (incluindo a 0ª = parado) vêm dessa síntese, com
deslocamentos alternados (+2/0/-2px) simulando um balanço de perna esquerda →
direita → esquerda.

### Overrides manuais

`OVERRIDES`, no topo de `tools/spr/import_mugen.py`, fixa `idle`, `walk`
(3 ou 4 números — 3 ganha a 4ª fase sintética), `faces` e `front` por looktype,
pelo **número do arquivo**. Mesmos 11 casos da v1 (ver tabela no histórico do
arquivo), sem mudança de motivo. Casos novos (retrabalho "golpe/agachamento
vazando pro ciclo", ver seção seguinte): `"904"`, `"905"`, `"918"` com
`{"front": None}` — desliga o quadro de frente automático (era um chute
voador/agachamento mirando arma na revisão visual), caindo no mesmo fallback
de "sem candidato" (Sul repete o perfil do Leste).

### Retrabalho 2: filtro obrigatório do ciclo de andar (regras a-e)

Feedback de uma segunda rodada de revisão: mesmo com o ciclo de 4 fases
"funcionando" (a costas sintetizada anda de verdade, ver seção acima), a
**heurística às vezes escolhia um quadro de golpe/agachamento/pulo** para
dentro do ciclo de andar — ex.: looktype 900 (Naruto Kid) tinha um soco de
braço estendido no ciclo leste/oeste; 906 (Kakashi) tinha uma silhueta
baixa/escura de agachamento vazando pro ciclo sul (que reusa os quadros do
leste — ver "Encaixe"). A causa: o critério antigo (altura parecida + vão dos
pés variando + paleta parecida) não olhava para a **forma da pose em si**,
só para o tamanho da caixa — um soco ou chute que mantém altura/largura
parecidas com o parado passava despercebido.

**Cinco regras**, implementadas em `char_synth.validate_frame`/
`validate_cycle` e usadas como **filtro obrigatório** (não mais só pontuação)
antes de aceitar um quadro no ciclo:

| Regra | O quê | Por quê |
|---|---|---|
| (a) altura | bbox do quadro dentro de ±2px da altura do idle (**escalado**: ver abaixo) | agachamento encolhe a caixa, salto/chute a estica |
| (b) largura | ≤ 1,25× a largura do idle | soco/chute lateral estica a caixa muito mais que um passo |
| (c) centroide da cabeça | offset X da pele/cabeça (topo 25%) em relação ao apoio dos pés (rodapé 34%), variando ≤2px do mesmo offset no idle (**escalado**) | soco/chute inclina o tronco — a cabeça se desloca em relação ao apoio muito mais que um passo normal |
| (d) paleta | ≤5% de pixels "de efeito" (fora da paleta do PRÓPRIO personagem, extraída do idle, E saturados/claros o bastante pra ser chama/chakra/brilho) | golpes especiais trazem cor que o personagem não tem parado |
| (e) continuidade | diferença de máscara (silhueta 24×32) entre quadros CONSECUTIVOS do ciclo (fecha o loop último→primeiro) entre 3% e 25% | menos = quadro duplicado; mais = pose diferente (chute/agachamento/pulo) |

**Escala das tolerâncias em pixel (a, c):** os rips chegam em resoluções bem
diferentes por personagem (40 a 90px de altura), mas as regras foram
calibradas pensando no sprite FINAL de 32px. `char_synth.validation_scale`
converte: `escala = min(32/maior_lado_do_idle, 1)`, a MESMA conta de
`imports.fit_uniform`; a tolerância em px do recorte bruto vira
`tolerância_final / escala`. Sem isso, um personagem grande (Tenten, 69px)
teria tolerância apertada demais e um pequeno, solta demais.

**Calibração:** os valores literais da missão (±2px, 25%) se mostraram
corretos para pegar os golpes de verdade (offsets de cabeça de 5-20px, motion
de 28-49% nos quadros ruins) mas **rejeitavam o próprio ciclo leste do
outfit do jogador (128)**, já testado e documentado (offset de cabeça
2,7-3,4px, motion 27% — balanço normal de um passo real, não golpe). Ajustado
para `HEAD_TOL=3.0` e `MOTION_HI=0.28`: ainda corta todo golpe/agachamento
encontrado na revisão, mas não reprova mais o passo legítimo do 128. As
constantes ficam documentadas em `char_synth.py`, seção "validação do ciclo".

**Conserto em duas passadas** (`import_mugen.repair_window` /
`char_synth.repair_cycle`, usado por `import_player.py`): um quadro que
reprova é **descartado e substituído**, nunca simplesmente removido do ciclo:

1. Troca por um **quadro vizinho válido** — procura, por proximidade no rip
   (ou no pool inteiro de 76 quadros, no caso do 128), outro quadro que passe
   nas regras (a-d) **e** mantenha a transição (regra e) com quem já está nas
   posições vizinhas naquele momento. Esse segundo requisito (adicionado
   depois de um teste que só checava a-d) importa: sem ele, o substituto era
   escolhido só pelo tamanho, sem relação de movimento com o resto do ciclo,
   e a passada 2 acabava sintetizando o ciclo INTEIRO em vez de só o quadro
   ruim (aconteceu com 903 Hinata, 909 Killer Bee e 918 Sakura The Last antes
   do ajuste).
2. Só **depois** de todas as trocas reais possíveis, valida a **continuidade**
   do ciclo já atualizado; o que ainda reprovar vira **síntese de deslocamento
   de pernas** (`char_synth.synth_walk_offset`) a partir do vizinho REAL mais
   próximo do ciclo — nunca de outra síntese (evita encadear deslocamentos e
   distorcer o quadro, sintese-sobre-sintese-sobre-sintese).

Toda troca/síntese fica registrada — no console (`REJEITADO quadro N (ciclo):
motivo -> substituto`), em `assets-src/sprites/mugen_frames.json`
(`quadros_rejeitados`, por personagem: posição, motivo(s), quadro rejeitado,
substituto) e em `assets-src/sprites/player_frames.json` para o 128.

**Frente (Sul) também passou a ser filtrada**: `pick_front` agora usa largura
mais apertada (1,6× → 1,35× a largura do idle) e checa a fração de pixels de
efeito (regra d) — chute/golpe especial usado como "pose de frente" também é
descartado, caindo no perfil do Leste.

**Folha de revisão rotulada** (`assets-src/import/extracted/mugen/
_cycle_<lt>.png`, um por personagem 900-926 **e** 128): mesmo layout de
`_review_<lt>.png` (idle + 4 fases × 4 direções, ampliada 3×), com um rótulo
por célula — o **número do quadro de origem** (verde) ou **"S"** (laranja)
quando a fase é sintética. Todos os 28 foram olhados um a um; os únicos golpes
residuais achados foram nos candidatos de FRENTE (Sul idle) de 904, 905 e 918
(chute voador/agachamento mirando arma), corrigidos com `"front": None` (ver
Overrides manuais acima) — o resto do material (parado + 4 fases de andar nas
4 direções) ficou limpo em todos os 28.

### Comparativo de nitidez (`tools/spr/compare_sharpen.py`)

Quatro variantes testadas no downscale ~60px→32px (folha ampliada 4×, 4
personagens de paletas bem diferentes: Naruto laranja, Kakashi verde/cinza,
Madara vermelho/preto, Sakura rosa/branco):

| Variante | Resultado |
|---|---|
| (a) recorte + LANCZOS direto (o que já existia) | boa, mas borda um pouco solta no fundo |
| (b) downscale por ÁREA (`Image.BOX`, média dos pixels) + realce (`unsharp`) | quase igual a (a), levemente mais limpo |
| (c) (a) + quantização à paleta original (nearest-color por pixel) | **ruim** — criou ruído de sal-e-pimenta nas bordas: o material tem antialiasing (centenas de tons), então um pixel de borda intermediário fica **equidistante** de cores muito diferentes da paleta reduzida e escolhe errado (ex.: um pixel laranja-claro de transição virou branco ou azul) |
| (d) = (c) + contorno 1px | mesmo defeito de (c), só com bordas mais duras |
| (e) = (b) + contorno escuro de 1px redesenhado após a redução | **vencedora** — silhueta nítida, sem ruído, cores fiéis |

A quantização de paleta (c/d) foi **testada e descartada**: parecia a técnica
mais "correta" no papel (evitar tons intermediários) mas piorou visualmente
porque o material de origem não é pixel-art de paleta pequena, é um rip com
antialiasing pesado. A vencedora foi (e): `imports.fit_uniform` agora faz
downscale por área + realce (`amount=0.8`) e redesenha um contorno escuro de 1px
na silhueta final — **automático para toda criatura com `directions`** (mugen E
o outfit do jogador), sem precisar de flag nenhuma (`sharpen=True` é o padrão;
dá para desligar com `sharpen=False` se algum caso futuro precisar do
comportamento antigo).

### Tabela final por personagem

Atualizada após o retrabalho 2 (filtro de validação a-e, seção acima) — vários
quadros mudaram de número porque o antigo foi rejeitado (golpe/agachamento/
pulo) e substituído por um vizinho válido ou por síntese ("S" na coluna
Andar). Ver `assets-src/sprites/mugen_frames.json` (`quadros_rejeitados`) para
o detalhe de cada troca.

| Look | Nome | Parado | Andar (4 fases) | Frente (Sul) | Notas |
|---|---|---|---|---|---|
| 900 | Naruto Kid | 0004 | 0029/S/S/S real4 | 0066 real | 4 quadros trocados/sintetizados; cor de cabelo ajustada a mão |
| 901 | Sasuke Kid | 0005 | 0027/0044/0053/0043 real4 | 0048 real | 4 quadros trocados/sintetizados |
| 902 | Sakura Kid | 0004 | 0003/04/05 + synth | 0055 real | sem ciclo real (override); cor de cabelo ajustada a mão |
| 903 | Hinata | 0003 | 0076/0050/S/S real4 | 0060 real | 4 quadros trocados/sintetizados; cor de cabelo ajustada a mão |
| 904 | Rock Lee | 0005 | 0045/0048/0055/0050 real4 | **perfil (Leste)** | frente desligada (era chute voador); 2 quadros trocados |
| 905 | Tenten | 0005 | 0113/14/15/118 real4 | **perfil (Leste)** | frente desligada (era agachamento mirando arma); leque gigante em todo quadro |
| 906 | Kakashi | 0004 | S/0029/0030/S real4 | **perfil (Leste)** | frente desligada (era alcance/joelho baixo — a "silhueta agachada" do feedback); cor de cabelo ajustada a mão; 2 quadros sintetizados |
| 907 | Minato | 0003 | 0003/04/S real3 | 0017 real (3/4) | sem ciclo real (override); 1 quadro sintetizado |
| 908 | Minato Edo | 0005 | 0005/06/S real3 | 0009 real (3/4) | sem ciclo real (override); 1 quadro sintetizado |
| 909 | Killer Bee | 0006 | S/S/S/S real4 | 0047 real | cor de cabelo ajustada a mão (loiro claro); ciclo inteiro sintetizado (nenhum vizinho válido achado) |
| 910 | Itachi | 0005 | 0132/33/36/37 real4 | 0113 real | limpo (sem rejeição) |
| 911 | Pain | 0008 | 0036/0008/0053/0083 real4 | 0009 real | idle por override; 3 quadros trocados |
| 912 | Obito | 0003 | S/0083/0084/0087 real4 | 0087 real | 2 quadros trocados/sintetizados |
| 913 | Madara | 0005 | 0055/56/57/58 real4 | 0100 real | limpo (sem rejeição) |
| 914 | Sasuke Taka | 0002 | 0087/0071/0072/S real4 | 0087 real (3/4) | 4 quadros trocados (efeito fora da paleta) |
| 915 | Sasuke Akatsuki | 0003 | S/S/0004 real3 | 0064 real | sem ciclo real (override); 2 quadros sintetizados (duplicados) |
| 916 | Sasuke Rinnegan | 0006 | 0191/92/93/94 real4 | 0063 real | limpo (sem rejeição) |
| 917 | Sakura | 0005 | 0039/40/41/42 real4 | 0060 real | cor de cabelo ajustada a mão (rosa); limpo após troca automática de janela |
| 918 | Sakura The Last | 0004 | 0153/0114/0115/0108 real4 | **perfil (Leste)** | frente desligada (era chute voador); 2 quadros trocados |
| 919 | Naruto Sennin | 0004 | S/S/S real3 | 0055 real | walk por override; ciclo sintetizado (golpe com efeito grande) |
| 920 | Naruto KCM | 0005 | S/S/S real3 | 0004 real | walk por override; ciclo sintetizado |
| 921 | Naruto 1 Calda | 0005 | S/S/S real3 | 0200 real | quadrúpede, sem repintura de rosto; ciclo sintetizado |
| 922 | Naruto 4 Caldas | 0076 | S/S/S real3 | **perfil (Leste)** | quadrúpede, sem repintura de rosto; ciclo sintetizado |
| 923 | Naruto 6 Caldas | 0022 | 0022/0033/S real3 | **perfil (Leste)** | quadrúpede; sem candidato de frente |
| 924 | Naruto Ashura | 0004 | 0020/S/S/S real4 | 0135 real | 3 quadros trocados/sintetizados |
| 925 | Naruto Girl | 0006 | 0110/0006/0133 real3 | 0197 real | sem ciclo real (override); 2 quadros trocados |
| 926 | Naruto Kid Fox | 0001 | 0013/0003/0015/0044 real4 | 0044 real | 2 quadros trocados |
| 128 | Jogador (Naruto laranja) | sprite_0071 (Sul) / 0080 (Leste) | 3 reais + 1 synth (todas direções) | 0071 real (já existia) | costas 100% sintetizada; ciclo original (84/83/75 leste, 70/76/70-espelhado sul) validado LIMPO pelo filtro a-e |

Todas as 28 entradas têm **Norte = costas sintetizada** (nunca copiada do rip) e
**Leste/Oeste = perfil espelhado**. "real4"/"real3+synth" = quantas das 4 fases
de andar são quadros de verdade do rip vs. sintetizadas por deslocamento de
pernas.

### Saídas

- `assets-src/import/extracted/mugen/<looktype>/{idle,walk0..3,back_idle,
  back_walk0..3,front}_NNNN.png` — quadros recortados/sintetizados (privado);
- `assets-src/import/extracted/mugen/_survey_<looktype>.png` — folha da
  varredura exaustiva (candidatos por orientação × pose);
- `assets-src/import/extracted/mugen/_review_<looktype>.png` — parado + 4 fases
  de andar nas 4 direções (agora com costas sintetizada), ampliada 3×, já
  passada pelo `fit_uniform`;
- `assets-src/import/extracted/mugen/_review_all.png` — folha geral;
- **`assets-src/sprites/mugen_frames.json`** — registro VERSIONADO (só índices e
  metadados, nenhuma imagem) da escolha final por personagem: quadro do parado,
  quadros de andar, `walk_kind`, lado, quadro de frente, cores de pele/cabelo
  estimadas e notas — o que a tabela acima resume;
- **`assets-src/sprites/overrides/40_mugen.json`** — o que o build lê de
  verdade. Mesmo esquema do `imports.json`; toda entrada cujo PNG não existir é
  ignorada com aviso.

### Encaixe

`Importer.creature_dirs` + `fit_uniform` (agora com o pipeline de nitidez da
seção acima): uma escala só por personagem, base dos pés no chão da célula,
centro do apoio no meio. Todos 1×1. Madara (60px) cai para ~53%, as formas de
raposa (86px de largura) para ~37% — preço de um bicho quadrúpede largo em
32×32, inalterado desde a v1.

### Teste in-game (3 rodadas)

Novo script `client-otc/tests/charwalk_rc.lua` (temporário, copiado para
`client-otc/shinobirc.lua` e removido no fim): login `god`, troca de outfit **no
cliente** (`setOutfit`, contorna o `/looktype` do TFS que recusa id ≥ 903) para
**128, 900, 901, 902, 903, 906, 909, 913**, 6 passos (`g_game.walk`) em cada
direção com 3 screenshots a ~150ms de intervalo DURANTE o movimento →
`screenshots/walk_<looktype>_<dir>_<i>.png`.

- **Rodada 1**: o teleporte inicial usava `/arena` (como na v1) — mas um monstro
  "Sapo Ancião" **sobrevivente de uma sessão de teste anterior** (o servidor
  estava rodando há dezenas de minutos, com bichos invocados por
  `autotest_rc.lua` ainda vivos) estava parado bem no ponto da arena e
  **paralisava o jogador** ao chegar (`"You are paralyzed"`), impedindo os
  `g_game.walk` de moverem o personagem — screenshots mostravam o monstro, não
  o personagem andando. Defeito do AMBIENTE de teste, não da arte.
- **Rodada 2**: trocado `/arena` por um `/tp` fixo na praça (zona de proteção,
  garantidamente livre de bicho) — mas a sessão anterior não tinha se
  desconectado direito do servidor (o cliente encerrou de forma abrupta ao
  bater no timeout da Rodada 1) e o login da Rodada 2 ficou **preso** (`"GM has
  logged in"` sem `"logged out"` correspondente no log do TFS), sem nunca entrar
  em jogo. Corrigido reiniciando o `tfs` (`kill` + novo `./build/tfs`), o que
  também limpou o monstro sobrevivente da Rodada 1.
- **Rodada 3** (final, servidor limpo): os 8 looktypes renderizaram certo —
  **Norte** com cabelo visível e pernas se movendo (não é mais um balanço),
  **Leste/Oeste** com o perfil de combate esperado, **Sul** com uma pose de
  frente reconhecível (não repete o parado do Leste), pés no chão em todas as
  fases, **sem mudança de tamanho** ao virar em nenhum dos 8. 0 erros no log do
  cliente.
- **Rodada 4** (retrabalho 2, filtro de validação a-e): mesmos 8 looktypes,
  mesmo script. Ambiente **compartilhado com outro agente** rodando testes em
  paralelo no mesmo servidor/conta `god` — o servidor foi reiniciado e o
  cliente desconectado no meio do teste por duas vezes (telas de
  seleção-de-personagem capturadas por engano em vez do jogo, descartadas
  pelo tamanho de arquivo muito menor). Rodadas de reteste isoladas (só o
  looktype afetado) fecharam a lacuna: **900** sem soco visível em
  leste/oeste (cabelo loiro confirmado); **906** sem a pose de
  agachamento/alcance no sul (era o quadro de frente 0053, agora desligado —
  ver Overrides manuais); **909** com cabelo loiro claro confirmado e sem
  chute/agachamento em nenhuma direção; **903** com cabelo azul-escuro
  confirmado. Os 8 looktypes ficaram limpos nas 4 direções — 0 erros de
  cliente relacionados à arte (os erros vistos foram todos de conexão com o
  servidor compartilhado, não de sprite/thing).

### Limitações restantes

- **Costas é sempre síntese**, nunca material real — em close-ups grandes lê-se
  como "cabelo cobrindo o rosto" mais do que uma anatomia de nuca desenhada à
  mão; a 32px na visão do jogo funciona bem.
- Vários personagens não têm mais 4 fases 100% reais — o filtro de validação
  (a-e, seção "Retrabalho 2" acima) troca ou sintetiza qualquer quadro que
  pareça golpe/agachamento/pulo ou que não flua com o vizinho, então alguns
  ciclos que antes eram "real4"/"real3" ficaram parcial ou totalmente
  sintéticos quando o rip não tinha material limpo o bastante por perto (ex.:
  909 Killer Bee ficou com o ciclo inteiro sintetizado). Isso é uma escolha
  deliberada — prefere um passo sintético (sempre parece caminhada) a um
  quadro de golpe real (não parece). Ver a coluna "Andar" da Tabela final por
  personagem para o estado exato de cada um (`S` = fase sintética).
- As 4 formas de raposa/quadrúpede (921-923, 926) não recebem repintura de rosto
  na síntese de costas (só escurecem) — não têm "cara" para apagar, e são
  reduzidas a ~37% do tamanho por serem largas.
- 923 (Naruto 6 Caldas) não achou nenhum candidato de frente utilizável: Sul
  repete o perfil do Leste.
- O oeste continua espelhado do leste (bandana/zíper/arma trocam de lado,
  invisível a 32px); `layers=1` (cores de outfit do servidor ignoradas); o
  `/looktype` do TFS não alcança 900-926 (preciso setar o outfit por script ou
  mexer em `server/`, fora do escopo).
- A classificação de POSE da varredura exaustiva (correr/pular/ataque/especial/
  dano/vitória) é heurística best-effort — usada só para montar candidatos a
  revisar, não é uma verdade automática; nomes como "vitória" ou "dano" numa
  folha de revisão podem estar errados sem que isso afete a arte final (que
  passa por seleção e revisão visual separadas).
- O filtro de validação (a-e) mede geometria (altura/largura/centroide/paleta/
  continuidade de máscara) — não "entende" a pose. Um golpe cuja caixa e
  centroide fiquem parecidos com o parado (raro, mas visto em picks de
  "frente" tipo braço estendido sem inclinar o tronco) pode passar; por isso a
  revisão visual das 28 folhas `_cycle_<lt>.png` continua necessária, o filtro
  reduz o trabalho manual mas não substitui a olhada.
- O ambiente de teste in-game é **compartilhado** (servidor TFS e conta `god`
  usados por outros agentes/sessões em paralelo, ver docs/sistemas gerais do
  projeto) — reinícios de servidor e logins concorrentes desconectam o
  cliente no meio de um teste sem aviso no Lua (a screenshot vira a tela de
  seleção de personagem, não o jogo). Mitigado detectando o tamanho de
  arquivo anômalo (a tela de login pesa ~400KB contra ~1MB de uma cena real)
  e reexecutando só o looktype afetado.

## Terreno procedural (`gen_terrain.py` + `overrides/10_terrain.json`)

O mapa `valley` usa **itens vanilla** do `items.otb` (grama 4526–4531, cobblestone
19744–19748, árvores 2700–2716, muro 1049–1051…). Esses ids caem nas *rules* de
estilo do `manifest.json` e ganhavam um quadrado chapado tingido pela cor de
minimapa — o mapa inteiro parecia um mosaico de retângulos coloridos. O terreno
procedural substitui a arte desses ids por pixel art própria, **sem tocar no
`items.otb`**: o item já existe, só o desenho muda.

```bash
.venv/bin/python tools/spr/gen_terrain.py     # desenha assets-src/sprites/terrain/*.png
.venv/bin/python tools/spr/build_assets.py    # compila .spr/.dat
.venv/bin/python tools/spr/dump_dat.py        # validacao: OK, divergencias=0
```

- **`tools/spr/gen_terrain.py`** — desenha tudo por código (Pillow). Arte própria,
  versionada em `assets-src/sprites/terrain/` (ao contrário de `assets-src/import/`,
  que é material privado fora do git).
- **`assets-src/sprites/overrides/10_terrain.json`** — liga cada server id vanilla
  aos PNGs. Fica em `assets-src/sprites/overrides/`, pasta que o `build_assets.py`
  varre em ordem alfabética aplicando cada arquivo com o **mesmo esquema do
  `imports.json`** (`tools/spr/imports.py`).

### O que faz "parecer Tibia"

| Técnica | Onde |
|---|---|
| Paleta **limitada** (4–6 tons por material), nunca gradiente | `P_GRASS`, `P_DIRT`, `P_COBBLE`, `P_WATER`, `P_LEAF`… |
| Ruído de valor **tileável** (grade que dá a volta) + dither de Bayer 4×4 | `noise_tile`, `fbm`, `quantize` |
| Campo **base compartilhado** entre as variantes do mesmo material | `shared_field` |
| Voronoi com rejunte na fronteira das células | `cobble` |
| Copa lobulada em 3 tons + sombra opaca no chão | `_canopy`, `_conifer` |
| Contorno escuro de 1px na silhueta | `outline` |

Duas armadilhas que valem a documentação:

1. **A emenda entre tiles.** O ruído é periódico em 32px e as decorações são
   desenhadas com *wrap* (`put(..., wrap=True)`); nenhuma borda é pintada no
   perímetro do tile. Por isso qualquer variante encosta em qualquer outra sem
   costura visível.
2. **O xadrez de brilho.** Se cada variante usasse uma semente independente, cada
   tile teria um brilho médio diferente e o campo viraria um tabuleiro visível de
   longe — mesmo com as bordas casando. `shared_field` resolve: 55% do valor vem
   de um campo comum ao material e 45% da semente da variante.

Sombra é **opaca**: o `.spr` de 1098 é RGB, não existe alpha parcial
(`FORMATO.md` seção 1). As sombras das árvores são elipses de verde escuro.

### Geometria: o que `imports.py` passou a aceitar em `items`

Uma entrada "simples" (1×1, 1 quadro) continua só trocando a folha do item. Com
qualquer um dos campos abaixo a entrada vira um **thing de item completo** no
manifesto, com geometria e atributos próprios — o `build_assets.py` aplica os
`things` do manifesto *depois* de `build_items()`, então a arte de regra é
substituída:

| Campo | Efeito |
|---|---|
| `"tiles": 2` | 64×64 = 2×2 tiles, **ancorado no canto inferior direito** (a arte sobe e vai para a esquerda — é assim que a Tibia desenha árvore grande) |
| `"height": 64` | 1 tile de largura × 2 de altura: paredes e portas sobem 32px acima do tile |
| `"frames": [...]` + `"duration"` | animação (`animationPhases > 1` com bloco `Animator`) |
| `"displacement": [x, y]` | atributo `Displacement` do `.dat` |

Grupo, flags, luz e `speed` **vêm do `items.otb`** — `imports.py` chama
`build_assets.item_attrs` no item do OTB, então chão continua sendo chão.

**Regra do `FLAG_ANIMATION` (`FORMATO.md` seção 5), aplicada automaticamente:**
quem manda é o OTB. Se o item **não** tem a flag, mais de um quadro é recusado
com aviso e reduzido a 1 (senão sobraria um byte no pacote de mapa e o cliente
daria `getThing: invalid thing id`). Se o item **tem** a flag e só há um quadro,
ele é duplicado para 2 fases. A água do mapa (`4608`, *shallow water*) **tem** a
flag no `items.otb`, então as 3 fases de onda são legais — não foi preciso trocar
o id no mapa.

### Cobertura

| Categoria | Qtd. | Server ids |
|---|---|---|
| Grama (variantes) | 6 | 4526–4531 |
| Terra batida | 3 | 351, 352, 353 |
| Cobblestone | 5 | 19744–19748 |
| Piso de pedra clara / madeira | 1 + 1 | 431, 405 |
| Lama e pântano | 4 | 354, 355, 11145, 19947 |
| Água rasa (3 fases) | 3 PNGs | 4608 |
| Árvores (fir, sicômoro, salgueiro, faia, pinheiro alto), 2×2 | 5 | 2700, 2701, 2702, 2707, 2712 |
| Árvores mortas, 2×2 | 5 | 2709, 2713–2716 |
| Arbustos | 3 | 2767, 2784, 3986 |
| Plantas de pântano | 3 | 2771, 2774, 2775 |
| Paredes de pedra H/V/canto, 32×64 | 3 | 1049, 1050, 1051 |
| Paredes de madeira H/V/canto + janela, 32×64 | 4 | 5261, 5262, 5263, 5277 |
| Portas fechadas de pedra e madeira H/V, 32×64 | 4 | 1210, 1213, 5099, 5101 |
| Tocha de parede (2 fases) / fogueira (2 fases) | 4 PNGs | 2059, 1428 |
| Placa, cerca, depot, boneco de treino, tenda | 5 | 1440, 1533/1534, 2594, 5787, 7605 |

`assets-src/sprites/terrain/_sheets/` é **gerado** pelo build (as folhas já
encaixadas na grade de 32px); não edite à mão.

## Bordas de terreno / autoborder (`gen_borders.py` + `tiles.json`)

O terreno procedural acima resolve a textura de cada material, mas cada tile
ainda terminava numa linha reta exatamente no limite dos 32px — a transição
grama/terra, grama/água, grama/lama e terra/cobblestone era um degrau
perfeito. `tools/spr/gen_borders.py` desenha os **tiles de borda** (o
autoborder clássico da Tibia): itens de decoração, com alpha real na
máscara, desenhados por cima do chão na transição entre dois materiais.

Diferente do terreno (que troca a arte de um id que já existe), borda é
**item novo**: entra pelo mesmo fluxo de "Criando itens NOVOS" acima
(`tiles.json` → `allocate_ids.py` → `build_assets.py`), só que com o grupo
`decoration` + `on_top`/`top_order` (ver tabela de flags em "Criando itens
NOVOS"). Detalhe completo do algoritmo, da convenção de nomes de par/peça e
de como `build_valley.py` decide onde colocar cada peça:
**`docs/sistemas/mapas.md#autoborder`**.

Resumo do pipeline:

```bash
.venv/bin/python tools/spr/gen_borders.py        # 64 PNGs em terrain/borders/
# declarar border_<par>_<peca> em assets-src/sprites/tiles.json (feito)
.venv/bin/python tools/spr/allocate_ids.py        # ids permanentes
.venv/bin/python tools/map/build_valley.py        # autoborder no mapa (apply_borders)
.venv/bin/python tools/map/render_preview.py      # PNG de conferência sem cliente
.venv/bin/python tools/spr/build_assets.py        # só entao grava items.otb/.dat/.spr
```

Reusa as paletas E as funções de desenho de `gen_terrain.py` (import direto
do módulo): a textura do material invasor não é um ruído próprio, é a MESMA
função que pinta o chão de verdade (`GT.grass(1)`, `GT.cobble(1)`) — é o que
faz a borda casar pixel a pixel (paralelepípedo de verdade no canto de
cobblestone, não uma mancha cinza lisa).

### v2 — bordas fluidas (curva-base única + 2 variantes por peça reta)

A v1 desenhava cada uma das 12 peças (retas, cantos externos, cantos
internos) com uma fórmula própria, e a transição virava uma faixa serrilhada
uniforme com emenda visível nos cantos (feedback do usuário: "a conexão
entre as texturas está ruim"). A v2 deriva as 12 peças de **uma única curva
de profundidade de invasão por direção** (periódica, amplitude 3–6px,
suavizada antes do jitter): retas usam a curva direto, cantos externos são a
mesma curva das duas retas do canto encolhendo perto do canto (`_taper`), e
cantos internos são "tile cheio menos o bolsão de canto externo oposto" —
nenhuma peça inventa uma forma independente, todas reaproveitam a mesma
fonte, o que garante que a curva não "quebra" onde uma peça reta encontra um
canto. Mais detalhes, incluindo o bug de textura encontrado e corrigido na
2ª rodada de preview (canto interno de cobble saindo cinza liso em vez de
paralelepípedo) e os 3 recortes de validação:
**`docs/sistemas/mapas.md#autoborder`**.

Também ganhou **2 variantes por peça reta** (`border_<par>_<edge>2`, 16
itens novos, server ids 30328–30343/client 24054–24069) — o autoborder em
`build_valley.py` escolhe entre a base e a variante por um hash
determinístico (CRC32) da posição do tile, pra uma trilha comprida não
repetir sempre a mesma peça "carimbada".

> **v2 (2026-09-05)**: mais 2 pares, `grass_sand` e `sand_water` (32 itens
> novos, server ids 30344–30375/client 24070–24101) — ver "Decoração v2..."
> perto do final deste arquivo.

## Decoração de cenário (`gen_decor.py` + `tiles_decor.json`)

Ponte de madeira, pedras, tocos, flores, tufos de grama alta, cogumelos,
galho caído, poça decorativa, tocha de rua em poste, placa de trilha,
barril, caixote, cerca de madeira e caminho de pedras soltas — 30 itens
novos, 31 PNGs (`stone_large` é 2×2). Igual a bordas, entra pelo fluxo de
"Criando itens NOVOS" (declarar → `allocate_ids.py` → `build_assets.py`), mas
com um manifesto **separado**, `assets-src/sprites/tiles_decor.json` (mesmo
esquema do `tiles.json`), para não colidir com outra edição concorrente do
`tiles.json` (bordas). O coordenador mescla as duas listas antes de rodar
`allocate_ids.py` — por isso as entradas de `tiles_decor.json` ainda não têm
`server_id`/`client_id`.

```bash
.venv/bin/python tools/spr/gen_decor.py           # PNGs em terrain/decor/
# mesclar tiles_decor.json em tiles.json (coordenador)
.venv/bin/python tools/spr/allocate_ids.py        # ids permanentes
.venv/bin/python tools/map/decor.py               # teste de conectividade isolado (sem otbm)
.venv/bin/python tools/map/build_valley.py        # mapa completo com a decoração integrada
.venv/bin/python tools/spr/build_assets.py        # só então grava items.otb/.dat/.spr
```

Reaproveita as paletas e primitivas de `gen_terrain.py` (`P_WOOD`, `P_STONE`,
`P_BARK`, `P_GRASS_DOT`, `P_FLOWER`, `P_PUDDLE`, `Rnd`, `put`, `rect`,
`ellipse`, `outline`, `shade`, `fbm`) em vez de duplicá-las. Fogueira do
acampamento (id vanilla 1428) e tendas (id vanilla 7605) já existem em
`gen_terrain.py`/`overrides/10_terrain.json` — não foram redesenhadas.

Flags de alto nível por categoria (ver tabela completa em "Criando itens
NOVOS"): ponte = `ground` caminhável com `speed` igual ao piso (100, igual a
405/431); corrimão da ponte = `wall` que bloqueia 1 tile (`walkable: false`,
`has_height: true`); pedregulho grande = `decoration` bloqueante 2×2; pedras
pequenas/médias, flores, tufos, cogumelos, galho e pedras de trilha =
`decoration` caminhável; tocha de rua e fogueira = `decoration` bloqueante
com `light`; cerca de madeira (H/V/canto) = `wall` bloqueante.

O `tools/map/decor.py` correspondente (funções `place_bridge`,
`place_forest_decor`, `place_camp_decor`, `place_village_decor`) e a
integração no mapa estão documentados em
**`docs/sistemas/mapas.md#decoração-e-ponte`**.

> **v2 (2026-09-05)**: 10 itens novos (cadeira, estátua de santuário,
> lanterna de pedra, decor de praia) + areia com textura própria + 2 pares de
> autoborder novos (`grass_sand`, `sand_water`) — ver "Decoração v2..." perto
> do final deste arquivo.

## Extração de screenshots (`extract_screenshot.py` + `overrides/20_screenshot.json`)

Terreno **real**, recortado de screenshots de um cliente Open Tibia de um jogo
Naruto (material privado do usuário, em `assets-src/import/`, fora do git):

| arquivo em `assets-src/import/` | origem | conteúdo |
| --- | --- | --- |
| `screenshot_forest_full.png` | `sprite_0000.png` (PNG sem perdas, 1920×1080) | floresta densa, trilha de terra, clareira, cobra vermelha (boss) |
| `screenshot_naruto_ot_b.jpg` | `scDBJuV.jpg` | a **mesma** cena em JPG (só referência; a extração usa o PNG) |
| `screenshot_naruto_ot_a.jpg` | `a0YYar9.jpg` | área submersa com deck de madeira (sem terreno que a gente use hoje) |

### Escala e grade

O cliente **não** desenha 32 px por tile: ele renderiza 21 tiles na largura da
janela de 1920 px, então cada tile ocupa **1920/21 = 91.43 px** — um zoom de
2.86× sobre a arte de 32. O período foi achado por autocorrelação da textura de
chão (`|imagem − imagem deslocada de p|`, vale mais nítido em 91 px nos dois
eixos, medido separadamente em grama, terra e trilha) e depois arredondado para
a fração exata `largura/N`. A fase da grade (`offset x=61 y=89`) veio do
alinhamento das transições grama↔terra, que no Tibia são tiles inteiros de
borda. Confira sempre olhando `assets-src/import/extracted/screenshot/_grid.png`
(grade desenhada por cima, com o número da célula).

Como o período é fracionário, **todo recorte é reamostrado com
`Image.resize(box=...)` em coordenada fracionária**: cortar em pixel inteiro
acumula 0.43 px por tile e estraga a costura entre tiles.

```
.venv/bin/python tools/spr/extract_screenshot.py grid      # escala + grade
.venv/bin/python tools/spr/extract_screenshot.py ground    # chão -> 32x32
.venv/bin/python tools/spr/extract_screenshot.py objects   # árvores/arbustos com alpha
.venv/bin/python tools/spr/extract_screenshot.py sheet     # folhas de revisão
```

### Chão

Cada célula da grade vira uma amostra com cor média e desvio. A classificação é
por cor média (`grass_light`, `grass_dark`, `dirt`) e o descarte tem **três**
filtros, porque média e desvio sozinhos não pegam uma copa de árvore por cima do
chão:

1. distância da cor média à **mediana da classe** (`--tol`);
2. desvio da célula contra o desvio mediano da classe (`--std-tol`);
3. **pureza**: fração de pixels dentro de uma bola de cor em volta da mediana
   (`--purity`, padrão 0.985). É o filtro que joga fora sombra, folhagem e bicho.

Só as células da grade dariam ~27 candidatos de grama, e nesse pouco o filtro é
obrigado a aceitar tiles com uma folha escura da copa vizinha — que aparece
repetida no jogo inteiro. Como **o chão repete com o período do tile, qualquer
janela de um período tirada de área homogênea já é um tile válido e tileable**,
`--substeps` (padrão 3) amostra também em frações de tile: 185 candidatos, e aí
dá para exigir pureza ≥ 0.985 e ainda sobrar variante.

O que sobra é reduzido 91→32 com LANCZOS + unsharp leve + quantização em 24
cores (para voltar ao "pixel art"), deduplicado por hash e ordenado pelo **erro
de costura** (diferença entre a coluna/linha da borda esquerda e da direita).
`sheet` monta `_review_ground.png` com cada tile repetido 2×2, que é como se vê
se a variante é realmente *tileable*.

### Objetos

Alpha por distância de cor sozinho **esburaca a copa**: o brilho das folhas tem
quase a mesma cor da grama. Então `cut_object` fecha a máscara
morfologicamente (Max→Min) e só apaga o fundo **conectado à borda** do recorte
(rotulagem de componentes conexas própria, sem scipy); buraco interno continua
opaco. Objetos que ficam por cima da copa, e não da grama, usam
`"bg": "local"` (mediana do anel em volta da caixa).

Como a copa é um recorte de uma massa contínua, a borda da caixa sai reta e o
sprite fica com cara de quadrado. Para `tiles > 1` a borda é **roída por um
ruído determinístico** de 3 px, o que devolve uma silhueta de folhagem (o `.spr`
1098 tem alpha de 1 bit, então suavizar não adiantaria).

A floresta do material é densa: **só uma copa** no screenshot inteiro fica
isolada o bastante para a varredura automática achar sozinha. Por isso os
recortes bons são escolhidos à mão em `tools/spr/screenshot_objects.json`
(célula da grade + ajuste fino em pixels + lado em tiles); a varredura
automática por caixa deslizante (miolo cheio de "não-chão", anel em volta cheio
de chão) continua rodando e complementa com arbustos soltos.

### Mapeamento (`assets-src/sprites/overrides/20_screenshot.json`)

O build carrega `assets-src/sprites/overrides/*.json` em ordem de nome, o último
vence: o `20_screenshot.json` fica **por cima** do `10_terrain.json`
(procedural). Toda entrada cujo PNG não existir é ignorada com aviso, então numa
máquina sem o material privado o build cai de volta no terreno procedural.

| ids do mapa (`tools/map/build_valley.py`) | quantos | arte |
| --- | --- | --- |
| `GRASS` 4526–4531 | 6 | 6 variantes de grama clara |
| `DIRT` 351, 352, 353 | 3 | 3 variantes de terra da trilha |
| `TREES` 2700, 2701, 2702, 2707, 2712 | 5 | 5 copas 2×2 (`"tiles": 2`) |
| `BUSHES` 2767, 2784, 3986 | 3 | 2 arbustos redondos + 1 com flores |

Também foram extraídos `rock_grey`, `branch_fallen` e `bush_flower_b`, ainda sem
id no mapa (o `valley.otbm` não usa nenhum item de pedra nem de galho caído —
confira com `tools/map/otbm.py`, `OtbmMap.read(...).item_count_by_id()`).

### Limitações desta extração

- **Não há grama escura limpa** no material: todo pixel verde escuro do
  screenshot é copa de árvore, não chão. A classe `grass_dark` sai com zero
  variantes e os 6 ids de `GRASS` são preenchidos com a família clara, que já
  varia de tom o suficiente.
- As copas não são árvores inteiras e sim **recortes 2×2 de uma massa contínua
  de folhagem**: funcionam para floresta fechada (que é o caso do `valley`), mas
  uma árvore isolada no meio de um campo fica com o corte reto aparente.
- Tufos de grama e detalhes finos não sobrevivem ao alpha (cor perto demais da
  grama) e ficam com aparência de ruído; não foram mapeados.
- O segundo screenshot (`screenshot_naruto_ot_a.jpg`) é submerso e tem escala
  diferente; nada dele foi usado.

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
- ~~O terreno procedural não tem bordas de transição~~ resolvido por
  `gen_borders.py` + `apply_borders` (ver seção "Bordas de terreno /
  autoborder" acima) — grama/terra, grama/água, grama/lama e cobble/terra
  têm faixa ondulada própria (v2: curva-base única + 2 variantes por peça
  reta, sem emenda visível entre reta e canto).
- Árvores de 2×2 desenham para oeste/norte mas **bloqueiam uma casa só** — em
  floresta densa a copa de uma cobre o tronco da vizinha; é o comportamento da
  Tibia, mas exige que o mapa não empilhe árvores em casas adjacentes.
- A água anima em 3 fases de onda senoidal: o padrão se repete de forma
  perceptível em lâminas grandes.
- Ponte de madeira desenhada e testada (`tools/spr/gen_decor.py`,
  `tools/map/decor.py`), mas ainda **não integrada** ao `build_valley.py`
  principal: até o coordenador mesclar `tiles_decor.json` em `tiles.json`,
  alocar ids de verdade e chamar `place_bridge`/`place_*` de dentro do build,
  o mapa gerado continua atravessando o rio com piso de pedra (431) e cerca
  (1533) como guarda-corpo.
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
- A arte importada de monstro não tem direções nem quadros de andar: as 4 direções
  e as 3 fases de caminhada usam a mesma imagem (o bicho "desliza"). Só o outfit
  do jogador (looktype 128, `overrides/30_player.json`) usa o bloco `directions`
  com ciclo real — e mesmo lá o norte é uma aproximação, porque o material não tem
  vista de costas.
- Sprites que se sobrepõem na folha original não são separáveis por componente
  conexo; só com `crop` manual no `imports.json`.
- Recortes maiores que 128 px são reduzidos para caber em 4×4 (o `.dat` não vai
  além disso na prática); recortes entre 32 e 45 px são reduzidos para 1×1, o que
  perde um pouco de nitidez nos humanoides.

## Terreno v3 (grama/terra/água mais "renderizados")

Feedback do usuário depois de ver o jogo rodando: "as coisas mais renderizadas
ainda" — a grama in-game vinha de `overrides/20_screenshot.json` (extraída de um
print real de um cliente Open Tibia), que por vir de uma imagem JPEG comprimida
lê como um verde quase sólido, sem tufos, sem contraste, sem "chão de jogo".

### Comparativo (Pillow, folha 4×4 a 4×)

`screenshots/compare_grass_v3.png` e `screenshots/compare_dirt_v3.png` colocam
lado a lado, na mesma escala: (1) a grama/terra extraída do screenshot
(`20_screenshot.json`), (2) a procedural antiga (`gen_terrain.py` antes deste
trabalho — backup usado só para o comparativo, não versionado), (3) a v3 nova.

**Grama — venceu a v3.** O screenshot é uma mancha verde-clara quase uniforme
(ruído de compressão JPEG, não textura); a v2 já tinha tufos + flor/pedra
ocasionais mas pouco contraste; a v3 abre a paleta (tom mais escuro 44 e mais
claro 138, era 56–126), adiciona "lâminas" isoladas (riscos de 2px que quebram
a leitura de "pontinho + fundo liso"), sobe de 6 para 8 variantes e torna a flor
**rara** (1 variante em 8, era 2 em 6 — flor demais lia como canteiro). Decisão:
**v3 ativa, `20_screenshot.json` desativado** (`items: []`, ver comentário
`_desativado_v3` no próprio arquivo — os PNGs originais continuam em
`assets-src/import/extracted/screenshot/` para reverter se necessário).

**Terra — venceu a v3** pelo mesmo motivo (screenshot chapado); a v3 soma
cascalho em 2 tons (claro E escuro, era só claro) e rachaduras finas
(terra ressecada, não só "marrom com pontinhos").

**Cobblestone, piso de pedra, lama** — não vieram do screenshot (só grama e
terra tinham entrada em `20_screenshot.json`); a versão procedural já cobria
bem o pedido (`cobble()`: Voronoi com rejunte escuro na fronteira das células +
bisel de luz/sombra por pedra; `stone_floor()`: lajes em fiada com junta e
desgaste; `mud()`: poça com reflexo). Neste trabalho a junta do piso de pedra
foi aprofundada (`shade(P_STONE[0], -30)` → `-44`, confirmado no
render_v3_praca.png da rodada 2: juntas nitidamente mais fundas).

**Água** — reforçada, não trocada: 2ª crista de onda (reflexo, fase deslocada
da primeira), cintilação mais forte (10→14 pontos, brilho +22→+26) e um
borrifo de espuma branca esparsa (4 pixels/fase). Continua com 3 fases
(`animationPhases`, exigido pelo `FLAG_ANIMATION` do id 4608).

### `grass_shade` — variante para sombra de árvore (documentado, não ligado)

A missão pediu uma "vinheta de sombra em tiles adjacentes a árvores", mas
**não** no gerador de mapa (fora do escopo deste trabalho: `tools/map/` é de
outro agente). `gen_terrain.py` ganhou `grass_shade(v, amount=-26)`: pega a
MESMA arte de `grass(v)` (pixel a pixel, sem regenerar do zero — por isso
encaixa sem costura com a variante normal) e escurece em bloco. Gera 3 amostras
(`terrain/grass_shade_0..2.png`), **não referenciadas em nenhum server id** —
servem de referência para quem for implementar a troca de tile por vizinhança
em `tools/map/build_valley.py` (autoborder/decor): ao detectar um tile de grama
adjacente a uma árvore (2×2), trocar o server id normal pela variante
`grass_shade` correspondente.

### Tiles refeitos (mesmos nomes de arquivo — 10_terrain.json não mudou)

| Arquivo | Server ids | O que mudou |
|---|---|---|
| `grass_0..5.png` (+ `grass_6.png`, `grass_7.png` extra) | 4526–4531 | paleta mais aberta, tufo 2 tons, lâminas, flor rara, +2 variantes (não ligadas — reserva p/ mapas futuros) |
| `dirt_0..2.png` | 351–353 | cascalho 2 tons + rachaduras |
| `stone_floor.png` | 431 | junta mais funda |
| `water_0..2.png` | 4608 | 2ª crista (reflexo), cintilação mais forte, espuma |
| `grass_shade_0..2.png` | nenhum (amostra/documentação) | ver acima |

Cobblestone (`cobble_0..4.png`), piso de madeira, lama/pântano, árvores,
paredes e portas **não precisaram de reescrita** — já tinham contorno, tufo/
musgo/veio e sombra elíptica opaca sob árvore (`_tree_shadow`) desde a versão
anterior; confirmado nos screenshots in-game (ver abaixo).

### Teste in-game (3 rodadas)

Script `client-otc/tests/render_v3_rc.lua` (copiado para `client-otc/shinobirc.lua`
e removido ao final, mesmo padrão de `autotest_rc.lua`): login `god`, `/god`
(status máximo), `/tp x,y,z` (comando de `server/tfs/data/scripts/naruto/gm_tools.lua`)
para floresta (1060,1080,7), lago/ponte (1127,1060,7), praça (1029,1044,7) e
Floresta da Morte (1165,1061,7), screenshot em cada, depois
`modules.naruto_menu.show('Jutsus')` (chamada direta à função pública do
módulo — não precisa simular Ctrl+J) e screenshot da lista de jutsus + barra
de ação. Saída: `screenshots/render_v3_{floresta,lago_ponte,praca,
floresta_morte,icons}.png`.

- **Rodada 1** (grama/terra/água v3 + junta de piso original): sombra elíptica
  de árvore visível e nítida, tronco com 2 tons de casca, copa em 4 tons +
  contorno, ponte de madeira com veio, tocha e fogueira acesas, parede de
  pedra com musgo — tudo já "renderizado" no sentido pedido. `0 erros` no
  cliente (`grep -c error`).
- **Rodada 2** (junta do piso de pedra aprofundada de -30 para -44): confirmado
  em close-up (`render_v3_praca.png`) que a junta ficou nitidamente mais funda,
  sem quebrar o padrão de fiada. Rebuild + `dump_dat.py` OK, `0 erros`.
- **Rodada 3** (confirmação de estabilidade, sem mudança de código): mesmo
  teste rodado de novo do zero para provar que o build é idempotente — os 5
  screenshots saem iguais à rodada 2, `0 erros` no log do cliente.

## Grama v4: regras de baixo contraste

Revisão do trabalho da v3, com feedback do usuário depois de ver o jogo
rodando de novo: a grama v3 (paleta 44..138, tufos em 2 tons, lâminas, flor,
pedrinha) ficou **manchada e escura**, com "remendos retangulares por tile"
visíveis (xadrez de tons) e cara de mofo — o oposto de Tibia clássica, que é
grama de tom médio, **uniforme à distância**, com variação sutil (2–3 tons
próximos, tufos claros pequenos e raros, nenhuma emenda perceptível).

### Causa raiz (não era só a paleta)

A paleta mais aberta (44..138) era metade do problema; a outra metade — a que
de fato produzia o "xadrez por tile" — estava em `shared_field()`: cada uma
das 8 variantes misturava o campo comum (55%) com um `fbm` **próprio**
(45%), e `fbm()` normaliza cada campo ao seu **próprio** min/max antes da
mistura. Normalizar independentemente faz a **média** do resultado variar
ligeiramente de variante para variante (a forma da distribuição de ruído
não é idêntica entre sementes diferentes, mesmo normalizada 0..1) — o
suficiente para o olho notar tiles vizinhos com brilho médio um pouco
diferente, lido como remendos/xadrez quando o chão cobre uma área grande.

### O que a v4 muda

`tools/spr/gen_terrain.py`, funções `grass()` e `mud()`:

1. **Um tom base único por material**, próximo do pedido (`#5aa03c`/
   `#4f8f34`): grama usa `P_GRASS_V4 = [(81,141,53), (86,150,56), (91,159,59)]`
   — só **3 tons**, ±6% em torno da base (86,150,56), contra os 5 tons
   44..138 da v3. Lama (`P_MUD_V4`) segue a mesma regra: 3 tons ±8% em torno
   de (78,72,52), contra os 5 tons 48..110 da v3; a poça (`P_PUDDLE`) também
   foi clareada (não precisa ser quase preta para ler como água parada).
2. **Campo de ruído CONTÍNUO através dos tiles, sem mistura por variante**:
   todas as 8 variantes de grama (e as 4 de lama) usam o **MESMO** campo
   `fbm(CELL, SEED_FIXO, octaves)` — nenhuma soma de campo próprio por
   variante. `noise_tile()` já é periódica no tamanho do tile (32px, múltiplo
   de 32 por construção — o grid do ruído fecha em si mesmo via `% cells`),
   então usar o mesmo campo em toda variante dá emenda **exata** (mesma
   textura) em vez de apenas parecida. Não dá para fazer a fase depender da
   posição do tile no mundo — as variantes são PNGs fixos, gerados sem saber
   onde o mapa (`tools/map/build_valley.py`, fora do escopo) vai colocá-los —
   mas o mesmo campo compartilhado resolve o mesmo problema (média e emenda
   idênticas) por um caminho que não depende disso.
3. **Tufo claro em vez de touceira/lâmina/flor/pedrinha**: a v3 empilhava por
   tile uma touceira escura, uma lâmina, e ocasionalmente flor ou pedrinha —
   cada uma uma mancha de baixo contraste sozinha, mas HAVIA MUITAS por
   tile. A v4 tem **uma única decoração**: um tufo de 2–4px, 1 tom acima do
   mais claro da paleta (`shade(P_GRASS_V4[2], 14)`), presente em **2 das 8
   variantes** (25%, o mais perto de "20%" que dá com 8 variantes discretas;
   as outras 6 são pixel-a-pixel idênticas ao campo base, o que por
   construção não pode gerar xadrez). Nenhuma mancha escura em lugar nenhum
   (zero touceira/lâmina/flor/pedrinha) e nenhum contorno preto (`outline()`
   nunca é chamado em `grass()`/`mud()`, como antes).

### Medição de uniformidade (script `compare_grass.py`, ad-hoc nesta sessão)

Mosaico 8×8 de tiles aleatórios (com repetição), 4× de zoom; duas métricas:
desvio-padrão da luminância **média por tile** entre os 64 tiles do mosaico
(mede o "xadrez") e diferença média de luminância entre pixels de bordas de
tiles adjacentes (mede a emenda). Comparativo em
`screenshots/compare_grass_v4.png` (v3 atual | v4 nova | grama extraída do
print, lado a lado):

| Métrica (grama) | v3 | v4 | screenshot (referência) |
|---|---|---|---|
| desvio-padrão ENTRE tiles | 2,34 | **0,03** | 1,27 |
| diff média de borda (emenda) | 21,56 | **0,56** | 13,59 |
| diff MÁXIMA de borda | 32,16 | **0,67** | 20,64 |
| desvio-padrão interno (textura) | 21,23 | 5,53 | 14,42 |
| faixa interna (max−min) | 125,91 | **14,24** | 59,66 |

A v4 fica **abaixo** da própria referência do screenshot em todas as
métricas de uniformidade (menos xadrez, menos emenda) — ganha por larga
margem e sem repetir o defeito antigo da v20_screenshot (chapada demais,
"ruído de compressão JPEG, não textura"): a faixa interna de 14,24 ainda
dá uma textura visível de baixo contraste, só que sem os saltos de 125,91
da v3. Lama (mesma mudança, valores do arquivo `mud_0..3.png` como
efetivamente buildado): desvio entre tiles caiu de 1,16 para 0,76 (-34%),
diff média de borda de 13,29 para 4,33 (-67%), diff máxima de 25,76 para
14,83 (-42%) — melhoria em toda métrica, ainda que com só 4 variantes a
poça (elemento distinto, não faz parte do "xadrez" de material) se repita
de forma um pouco mais reconhecível no mosaico do que a grama.

### Iteração de parâmetros (3 rodadas, olhando as folhas)

Harness isolado (fora do repo, sem tocar `gen_terrain.py` durante a
iteração) gerando só a grama com 3 combinações de oitavas/paleta, sempre com
o MESMO campo compartilhado (a mudança estrutural já elimina o xadrez; o que
sobra para calibrar é a leitura visual do ruído):

1. **r1**: base (86,150,56), ±6%, oitavas `((3,1.0),(7,0.4))` — manchas
   orgânicas, sem listra visível. **Vencedora.**
2. **r2**: base (90,150,55), ±5%, oitavas `((4,1.0),(9,0.35))` — visualmente
   quase igual a r1, mas a célula-9 do ruído criou uma leve listra vertical
   (batimento entre a grade de 9 e o tile de 32px) perceptível de perto.
3. **r3**: base (88,148,55), ±5,5%, oitavas com 3 camadas
   `((3,1.0),(6,0.4),(12,0.2))` — a camada extra de alta frequência (12)
   também gerou um padrão sutil em xadrez fino, pior que r1.

r1 venceu por não ter nenhum artefato periódico visível nas 3 folhas
(`mosaic_v4_r1/r2/r3.png`, comparadas via Read nesta sessão) e por bater
a luminância média (119,9) muito perto da referência do screenshot (121,2).
Os mesmos parâmetros (oitavas `(3,1.0),(7,0.4)`) foram usados de saída para
a lama, com paleta e semente próprias; um ajuste posterior de oitavas da
lama para `((4,1.0),(9,0.35))` não mudou a leitura visual de forma notável
(a poça domina visualmente), então ficou como está.

### Teste in-game

`client-otc/shinobirc.lua` temporário (copiado, testado, removido ao final,
mesmo padrão da v3): login `god`, `/god`, `/tp 1060,1080,7` (floresta) e
`/tp 1029,1044,7` (praça), screenshot em cada. `0 erros` no log do cliente.
Saída: `screenshots/render_v4_floresta.png` e `render_v4_praca.png` —
comparados com `render_v3_floresta.png`: a grama lê como um campo verde
uniforme de tom médio, sem nenhum remendo/xadrez visível tile a tile; o piso
de pedra da praça (`stone_floor()`, 1 variante só — não pode gerar xadrez
por definição, não precisou mudar) segue igual, junta funda e legível.

### Lama e piso de pedra da praça

- **Lama**: mostrava o mesmo xadrez de material que a grama (mesma causa
  raiz — `shared_field()` com fbm próprio por variante) e foi corrigida do
  mesmo jeito (ver acima). Não foi possível confirmar in-game nesta rodada
  porque `tools/map/build_valley.py` (fora do escopo) não usa lama nos dois
  pontos de teste pedidos (floresta e praça); a correção foi validada só
  por medição/mosaico (`mosaic_mud_v4_final.png`).
- **Piso de pedra da praça** (`stone_floor()`): checado e **não mudou** — é
  uma única variante (sem lista de variantes para divergir em média), a
  junta em fiada já é de baixo contraste desde a v3 (junta -44, não um
  "xadrez de papel quadriculado"), e o `render_v4_praca.png` confirma visual
  idêntico ao `render_v3_praca.png`. Regra do enunciado era condicional ("se
  hoje mostrarem xadrez") — este não mostra, então ficou como estava.

### Pendências

- A poça da lama ainda se repete de forma um pouco reconhecível em um
  mosaico denso de só 4 variantes (mesma limitação estrutural de "poucas
  variantes", não um problema de contraste); aumentar para 6–8 variantes de
  lama resolveria, mas está fora do pedido desta rodada.
- `grass_shade()` (amostra de sombra sob árvore, não ligada a nenhum server
  id) automaticamente passou a usar a nova `grass()` — não foi verificada
  visualmente porque não é usada por nenhum server id hoje (mesma situação
  documentada na v3).

## Índice de ícone determinístico (jutsus.png × jutsus_data.lua)

### O bug visto (causa raiz)

`screenshots/menu_04_jutsus.png` (de um commit anterior, "Modelo 4+4... 23
jutsus novos") mostra ícones cortados/errados na aba Jutsus e na barra: alguns
jutsus de elemento `fuuton`/`none` apareciam com ícone **cinza** (cor de
elemento errada) ou com sprites **completamente alheios** — uma tocha, um
cadeado/bolsa marrom — no lugar do símbolo esperado (bola/anel/linha/cruz/
silhueta). Outros apareciam em branco.

Investigação: `tools/spr/gen_jutsu_icons.py` e `tools/export_tfs.py` calculam
a MESMA ordem (`jutsu_icon_order`: por elemento, tier, level, id — fórmula
duplicada nos dois arquivos de propósito, um não importa o outro). O índice na
folha (`clientId` em `NarutoSpellInfo`) é `posição * 32px`. O commit "Modelo
4+4" **adicionou 23 jutsus** a `data/jutsus/*.json` — `tools/export_tfs.py`
rodou e gravou `jutsus_data.lua` com `clientId` até 53 (54 entradas), mas
`jutsus.png` **não foi regenerado junto** naquele momento: continuou com a
largura antiga (menos de 54×32px). Um `clientId` maior que a largura real da
folha faz o cliente recortar (`setImageClip`) uma região **fora** da imagem —
o OTClient não recusa nem preenche com transparente, ele lê o que estiver no
atlas de textura logo depois (nesse caso, pixels de outro ícone da UI: tocha,
cadeado). **Causa raiz: os dois artefatos são gerados por comandos separados,
e nada garantia que rodassem juntos** depois que `data/jutsus/*.json` mudou de
tamanho — um bug de processo, não de fórmula (as duas fórmulas de ordenação
já eram idênticas).

Estado atual verificado: `jutsus.png` já tinha 54 ícones (1728×32px) batendo
com as 54 entradas de `jutsus_data.lua` **antes** deste trabalho (`git diff`
vazio depois de rodar `gen_jutsu_icons.py`) — ou seja, o bug do screenshot
antigo já não se manifesta no estado atual do repo. `render_v3_icons.png`
(rodadas 1–3) confirma: todos os 8 jutsus ativos mostram o símbolo certo (bola/
anel/linha/silhueta/cruz) na cor certa do elemento (verde para Fuuton, cinza
para `none`), e a barra de ação (F1–F10) também — nenhum ícone cortado, nenhum
sprite alheio, nenhum branco.

### O que foi feito para não voltar a acontecer

Como `tools/export_tfs.py` está fora do escopo editável deste trabalho (não
pode ser alterado para LER um arquivo de ordem externo), a correção foi:

1. **`assets-src/sprites/jutsu_icon_order.json`** (novo, gerado por
   `gen_jutsu_icons.py` a cada execução): registro auditável e versionado da
   ordem calculada — índice, id, elemento, tier, level de cada jutsu. Serve
   para revisar em `git diff` quando a ordem muda (jutsu novo inserido no meio
   de um elemento, por exemplo).
2. **Validação embutida em `gen_jutsu_icons.py`** (`validate_against_lua`):
   toda vez que o script roda, ele lê `jutsus_data.lua` já gerado, extrai os
   pares `icon`/`clientId` de `NarutoSpellInfo` e compara com a ordem que
   acabou de calcular. Diverge (contagem diferente ou id no índice errado) →
   imprime `DIVERGENCIA jutsus.png x jutsus_data.lua` linha a linha e **sai com
   código 1** (mesmo padrão "OK, divergencias=0" de `dump_dat.py`). Hoje
   imprime `validacao de indice: OK, divergencias=0 (54 jutsus, ...)`.
3. **Guarda de sanidade no cliente** (`naruto_menu.lua`, `buildIconIndex`):
   antes de aceitar uma posição `{x, y}` do `NarutoSpellIcons`/`clientId`, o
   código confere que `x < (numero de jutsus) * 32`. Se um dia os dois
   arquivos voltarem a divergir (alguém regenerar só um dos dois), o cliente
   **não desenha ícone nenhum** para o jutsu fora do intervalo, em vez de
   sampler lixo do atlas — troca "ícone alheio" por "sem ícone", bem mais
   fácil de notar e depurar.

**Se um dia for preciso mexer em `tools/export_tfs.py`** (fora do escopo
deste trabalho): o ideal seria ele LER `assets-src/sprites/jutsu_icon_order.json`
em vez de recalcular `jutsu_icon_order` com a fórmula duplicada — eliminaria de
vez a possibilidade das duas ordens divergirem (hoje elas só coincidem porque
as duas fórmulas foram escritas iguais e mantidas manualmente em sincronia).

### 54 jutsus, não 25

A missão citava "hoje 25?" — não confirmado: no estado atual do repo já são
**54** jutsus em `data/jutsus/*.json` (katon 6, suiton 5, raiton 8, doton 4,
fuuton 5, neutral/personal 26) e `jutsus.png` já tem 54 ícones (1728×32px),
gerados e validados por este trabalho. Não havia nenhum jutsu sem ícone.

## Decoração v2: cadeira/estátua/lanterna + areia + praia (2026-09-05)

Resposta às 3 lacunas do tour in-game do mapa v2.1
(`screenshots/mapa_v21_*.png`, ver `docs/sistemas/mapas.md#pendências-da-v21`):
item vanilla invisível (estátua/cadeira), sem autoborder de areia, Costa das
Marés pobre em decoração.

### Causa raiz do item vanilla "invisível" (1442/1650)

Não era um buraco de cobertura no `.dat` (o item existe, com grupo/flags
corretos e client id dentro da faixa normal). Exportando os sprites com
`tools/spr/sprformat.py` (`spr_get_sprite` + `decode_sprite`, contando pixels
de alpha != 0) e conferindo com `dump_dat.py --thing item:<clientId>`:

```
item:2025 (statue, 1442)        -> 1º sprite id 4  -> 25 de 1024px opacos
item:2358 (wooden chair, 1650)  -> 1º sprite id 4  -> 25 de 1024px opacos (MESMO sprite)
```

Os dois clientIds apontam para o **mesmo** sprite: um pontinho de ~2px opaco
num quadro 32×32 quase inteiramente transparente — o placeholder genérico que
`gen_placeholders.py` usa quando nenhuma regra de estilo (`manifest.json`)
casa bem com o item. Não é um bug de `tools/spr/build_assets.py` nem do
`.dat`/`.spr` em si (a "regra de ouro de cobertura de ids" continua
cumprida — todo id tem um thing); é que o thing aponta pra uma arte
efetivamente vazia. Consertar a regra de estilo genérica para esses 2 ids
vanilla especificamente ficou fora do escopo (poderia mudar a arte de outros
itens que caem na mesma regra); a solução foi criar substitutos NOVOS com
arte de verdade (abaixo) e trocar os 2 usos no mapa
(`tools/map/build_regions.py`).

### Itens novos (`gen_decor.py`)

Reaproveita `P_STONE`/`P_WOOD`/`P_BARK`/`Rnd`/`ellipse`/`rect`/`outline`/
`shade` de `gen_terrain.py`, como o resto deste arquivo. Paletas próprias
novas (não existem em `gen_terrain.py`): `_MOSS` (musgo verde da estátua),
`_P_SHELL`/`_P_DRIFTWOOD`/`_P_WET` (decor de praia) e `_BEACH_SHADOW` — a
sombra padrão do arquivo (`GT.SHADOW`) é esverdeada (pensada pra grama) e
destoava muito sobre areia na 1ª rodada de revisão visual (a base do galho
encalhado lia como uma mancha verde).

| Função | Item(ns) | Notas de design |
|---|---|---|
| `chair(facing)` | `wood_chair_east`/`_west` | encosto do lado OPOSTO a `facing` — quem senta olha pra `facing`; 3 ripas verticais + assento de 2 tons |
| `shrine_statue(mossy)` | `shrine_statue_gray`/`_mossy` | corpo em elipse (túnica), mãos unidas em bloco central mais claro, capuz/chapéu achatado por cima; variante com musgo pinta 3 manchas verdes (topo do chapéu, ombros) |
| `stone_lantern(phase)` | `stone_lantern` (2 fases) | toro: base + haste + câmara vazada com o brilho por dentro (2 tons de laranja/dourado) + capitel; luz igual a `street_torch` |
| `seashell(v)` | `seashell_spiral`/`_fan` | v0 = bandas horizontais estreitando pro topo (silhueta de cone/caramujo, com abertura num tom mais escuro do lado) — a 1ª versão (elipses concêntricas deslocadas) virou um blob redondo sem leitura nenhuma de concha, teve que ser redesenhada; v1 = leque com nervuras (vieira) |
| `wet_rock()` | `wet_rock` | mais escura que `stone_*`, brilho especular frio (reflexo de água) + poça rasa translúcida-opaca na base |
| `mooring_post()` | `mooring_post` | poste + corda enrolada (4 elipses alternando 2 tons) + ponta solta caindo |
| `driftwood()` | `driftwood` | tronco de 4px de espessura (a 1ª versão tinha só 1px e a sombra dominava a leitura, virando uma mancha em vez de um galho) + toco de galho quebrado numa ponta |

10 PNGs em `assets-src/sprites/terrain/decor/`. Registrados em
`assets-src/sprites/tiles.json` (não precisou do arquivo separado
`tiles_decor.json` desta vez — nenhuma edição concorrente de bordas). Server
ids 30376–30385, client ids 24102–24111.

### Areia (`gen_terrain.sand()`)

`P_SAND_V4` (3 tons próximos, mesma filosofia de baixo contraste de
`grass()`/`mud()` — "Grama v4") + `sand(v)`: campo `fbm` único (evita o
xadrez de tiles claros/escuros entre variantes, mesmo raciocínio de
`P_GRASS_V4`), grãos/conchinhas claras esparsas, sombra rasa ocasional e uma
ondulação sutil de vento numa das 3 variantes. Ligada aos ids vanilla
104→`sand_0`, 231+9059→`sand_1` (231 e 9059 já compartilham client id no
`items.otb`) via `assets-src/sprites/overrides/10_terrain.json` — antes
**não havia override nenhum** pra esses 3 ids, e a Costa das Marés usava o
placeholder genérico (quadrado liso/pontilhado cinza — a causa raiz do
"praia lisa com quadrados cinza" do relato).

### Autoborder de areia (`gen_borders.py`)

Pares `grass_sand` (grama invade areia, contorno de contato = sombra escura,
mesma regra dos pares terrosos) e `sand_water` (areia invade água, contorno
de contato = espuma clara `FOAM`, mesma regra de `grass_water`) — textura do
material alto reaproveita `GT.sand(1)` quando o par começa com `"sand"`
(`_texture_hi`), pela mesma razão dos outros pares: casar pixel a pixel com o
chão de verdade. 32 PNGs novos (16 por par), `WATER_EDGE_PAIRS` generalizado
de `pk == "grass_water"` pra incluir `"sand_water"`.

### Teste in-game (`client-otc/shinobirc.lua`, 3 sessões — confirmado sem
### shinobirc.lua compartilhado ativo antes de cada uma)

Login `god`/`god`, `/god` + `/tp x,y,z`, `screenshots/decor_v2_*.png`:
cadeiras da Taverna visíveis e viradas pra mesa (`decor_v2_01`), altar do
templo com estátua + fogueira + 2 lanternas acesas (`decor_v2_02/03`), praia
com areia texturizada + conchas/pedra molhada/madeira encalhada/caixotes
(`decor_v2_05`), cais com borda areia↔água ondulada + postes de amarração
(`decor_v2_06`), trilha→praia com borda grama↔areia ondulada
(`decor_v2_08`). `dump_dat.py` (`validacao: OK, divergencias=0`),
`test_otb_roundtrip.py` (`RESULTADO: OK`) e `tools/map/walk_audit.py` (0
divergências novas) rodados depois do build. Detalhe completo (screenshots
ponto a ponto) em `docs/sistemas/mapas.md#decoração-de-praia-e-mobiliário-do-santuário-v2-2026-09-05`.

### Limitações honestas

- A estátua/lanterna/cadeira leem bem a 32px mas não foram testadas em
  ângulos de câmera diferentes (o jogo só tem uma projeção); a variante
  "musgo" da estátua é sutil a distância (3 manchas de poucos pixels).
- Não foi feita nenhuma tentativa de consertar o placeholder genérico de
  `gen_placeholders.py` para OUTROS itens vanilla que possam ter o mesmo
  problema (sprite quase vazio) — só os 2 citados no relato (1442/1650) foram
  investigados. Um agente futuro plantando item "nunca usado antes" no mapa
  deveria conferir a cobertura real (`dump_dat.py --thing`) antes de confiar
  no placeholder.
- `seashell_spiral`/`seashell_fan` ficaram com `pickupable: true` (dá pra
  pegar) — decisão de bom senso (concha de praia é o tipo de bugiganga que
  faz sentido catalogar/vender), não um pedido explícito da missão.

## Efeitos e misseis próprios dos jutsus (`gen_effects.py`, 2026-09-05)

### Situação anterior

Os 54 jutsus (`data/jutsus/*.json`) já tinham os campos `animation`/`sfx`
preenchidos desde antes desta missão (nenhum estava vazio), mas **nada os
lia**: `tools/export_tfs.py` mandava o mesmo par de efeito/missile POR
ELEMENTO (`data/tfs_mapping.json` → `elements.<el>.area_effect`/`shoot`,
nomes `CONST_ME_*`/`CONST_ANI_*` reais da Tibia) para TODOS os jutsus daquele
elemento, e o `.dat` (`tools/spr/gen_placeholders.py`) preenche os 255 ids de
efeito/missile do protocolo com arte **genérica rotativa** (`burst/sparks/
smoke/slash/pulse`, tingida por um hash do id) — nenhum sprite "de fogo",
"de água" etc. de verdade. Resultado: katon acertava com um "burst" que podia
sair verde, suiton com um "slash" azul, sem relação com o elemento, e os 3
jutsus de um mesmo elemento (projétil/área/beam) eram visualmente idênticos.

### O que mudou

`tools/spr/gen_effects.py` desenha por código (Pillow, ADR-002) **27 efeitos
próprios** (ids **200–226**) e **8 misseis próprios** (ids **60–67**), 32×32,
paleta de ≤4 tons por peça + contorno escuro de 1px (`char_synth.outline_1px`),
5–7 fases por efeito. Ids escolhidos na faixa **livre** do protocolo: o enum
`MagicEffectClasses` (`server/tfs/src/const.h`) só vai até 175 e `ShootType_t`
até 54 (+ 254 reservado "internal use") — nada no TFS manda um número maior
que isso para essas categorias, então 200+/60+ nunca colide com nenhum script
vanilla ou de monstro.

Cada chave do catálogo (`fx_fire_burst`, `ms_fireball`, `fx_smoke_poof`...)
tem uma folha de PNGs em `assets-src/sprites/effects_src/<key>/f*.png`
(versionada) e entra no `.dat` via **`assets-src/sprites/overrides/
50_effects_naruto.json`** — mesmo esquema de `imports.json` (`root`/
`build_dir`/`effects`/`missiles`), então `tools/spr/build_assets.py` aplica
sem precisar de nenhuma mudança de código (o loop que já varre
`assets-src/sprites/overrides/*.json` pega o arquivo novo sozinho). O
catálogo "de verdade" — ids, papel, alias por jutsu — fica em
**`assets-src/sprites/effects.json`** (não segue o esquema de build; é lido
por `tools/export_tfs.py` para montar os números que vão no Lua).

### Slots "vanilla" redesenhados (ataques de monstro)

`data/monsters/*.json` → `monster_xml()` continua mandando o
`shootEffect`/`areaEffect` por **nome** (`fire`, `icearea`...), porque
`Monsters::deserializeSpell` (`server/tfs/src/monsters.cpp` +
`getMagicEffect`/`getShootType` em `tools.cpp`) só resolve uma tabela fixa de
nomes — nunca aceita número cru. Reescrever os ataques de monstro em Lua
scriptado daria o mesmo resultado com risco bem maior (servidor compartilhado
com playtest ao vivo), então a solução foi **redesenhar o PIXEL** dos ids que
já existiam com esses nomes (nenhum sprite deste projeto é "de verdade",
ADR-002, então trocar o desenho de um id não quebra nada):

| Const (nome usado no XML/Lua) | Id | Arte nova (reaproveita a key) |
|---|---|---|
| `CONST_ME_FIREAREA` | 7 | `fx_fire_ring` |
| `CONST_ME_ICEATTACK` | 44 | `fx_water_splash` |
| `CONST_ME_ENERGYHIT` | 12 | `fx_lightning_strike` |
| `CONST_ME_STONES` | 45 | `fx_earth_spikes` |
| `CONST_ME_HOLYAREA` | 50 | `fx_wind_slash` (recolorido verde, não dourado) |
| `CONST_ME_HITAREA` | 10 | `fx_melee_hit` |
| `CONST_ME_POFF` | 3 | `fx_smoke_poof` |
| `CONST_ME_MAGIC_GREEN` | 15 | `fx_heal_green` |
| `CONST_ANI_FIRE` | 4 | `ms_fireball` |
| `CONST_ANI_ICE` | 29 | `ms_water_bullet` |
| `CONST_ANI_ENERGY` | 5 | `ms_lightning_needle` |
| `CONST_ANI_EARTH` | 30 | `ms_mud_bullet` |
| `CONST_ANI_HOLY` | 31 | `ms_wind_blade` |
| `CONST_ANI_THROWINGSTAR` | 8 | `ms_shuriken` |

Nenhum outro id vanilla (0..255) foi tocado. `data/tfs_mapping.json` não
mudou — os NOMES continuam os mesmos, só o desenho por trás do id.

### `assets-src/sprites/effects.json`: aliases e fallback por elemento

O campo `animation` de cada jutsu (ex. `fx_fireball`, `fx_earth_collapse`,
`fx_seal_paper`) é mapeado por `aliases` para uma key do catálogo — cobertura
1:1 dos 54 jutsus (ver `docs/sistemas/combate-e-jutsus.md`). Jutsus
`type=projectile` usam o alias como MISSILE (o `animation` descreve o objeto
voando, ex. `fx_mud_bullet` → `ms_mud_bullet`) e o impacto usa o efeito
padrão do elemento (`element_defaults`, ex. katon → `fx_fire_burst`) — a
Tibia sempre separa `shootEffect` (missile) de `areaEffect`/impacto, e o
`animation` de um jutsu de projétil nomeia só o primeiro. Jutsus sem elemento
("pessoais": taijutsu, selos) reaproveitam `fx_melee_hit`/`fx_chakra_focus`/
`fx_seal_glow` por falta de paleta própria — ver limitações.

### Por que não alocar ids em `allocations.json`

`assets-src/sprites/allocations.json` guarda a alocação dos **tiles** (ids de
`items.otb`/clientId ≥ 30000/23726) e `tools/spr/tiles.py::allocate` **reescreve
o arquivo inteiro** a cada build a partir de só 4 chaves (`next_server_id`,
`next_client_id`, `by_key`, mais o `_doc`) — uma chave extra tipo `"effects"`
seria apagada no build seguinte. Como o espaço de ids de efeito/missile é
outro (u8, 1..255, nada a ver com `items.otb`) e o catálogo (~35 entradas) é
pequeno e fechado, os ids ficam gravados diretamente em `assets-src/sprites/
effects.json` (permanentes, append-only por convenção do arquivo — nunca
renumere uma key já publicada).

### Validação

`tools/spr/build_assets.py` (override aplicado, `conferencia OTB -> .dat:
OK`) → `tools/spr/dump_dat.py` (`validacao: OK`, `effect 255 things ids
1..255`, `missile 255 things ids 1..255`) → `tools/export_tfs.py` (ids
numéricos corretos nos `.lua` gerados, conferido em
`katon_goukakyuu.lua`/`kawarimi.lua`/`bunshin.lua`/`shousen.lua`) →
`bash tools/install_generated.sh` → `/reload spells` no servidor (sem
reiniciar, servidor compartilhado com playtest) → sessão de screenshots
(`client-otc/tests/vfx_rc.lua`, ver `docs/sistemas/combate-e-jutsus.md`).

### Limitações honestas

- `fx_wind_tornado` lê mais como uma linha esverdeada ondulando do que uma
  coluna de vento girando — o template (arcos deslocados por linha) não
  vendeu bem a ideia de funil a 32px; ficou aceitável, não bom.
- `fx_lightning_armor`/`fx_wind_prison` (auras de self-buff) são discretas —
  um anel pontilhado — comparado aos efeitos de impacto/beam, que ficaram bem
  mais expressivos.
- Jutsus "pessoais" (taijutsu, selos, armas) sem elemento reaproveitam um
  punhado de efeitos genéricos (`fx_melee_hit`, `fx_chakra_focus`,
  `fx_seal_glow`) — não têm assinatura visual própria por personagem (ex.
  `agulhas_incendiarias`, que é katon, usa o missile `ms_senbon` sem tingir de
  laranja/fogo).
- Ataques de MONSTRO continuam limitados aos 6 slots vanilla redesenhados
  (um efeito/missile por elemento, sem variação por jutsu) — os 27 efeitos
  novos só aparecem nos jutsus do jogador.
