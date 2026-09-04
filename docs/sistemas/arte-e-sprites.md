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

| Direção | Parado | Andar (contato, passagem, contato oposto) |
|---|---|---|
| 0 Norte (costas) | 0068 | 0068, 0068 espelhado, 0068 |
| 1 Leste | 0080 | 0084, 0083, 0075 |
| 2 Sul (frente) | 0071 | 0070, 0076, 0070 espelhado |
| 3 Oeste | espelho do leste | espelho do leste |

O ciclo do leste foi escolhido medindo os **pés** (pixels de sandália no terço
inferior): 0084 = pé direito no ar (vão 15 px), 0083 = pés juntos na passagem
(vão 2 px), 0075 = pé esquerdo no ar (vão 13 px), os três com 39 px de altura.
0068 é o único quadro **alto** em que os olhos não foram desenhados: a 32 px a
faixa clara sob a bandana lê como a nuca, e por ser alto virar de sul para norte
não encolhe o boneco.

O ataque 898 usa 0043 (guarda) → 0031 (recuo) → 0017 (jab) → 0012 (avanço), nas 4
fases do frame group "andando".

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

### Teste in-game (2 rodadas)

Cópia temporária de `client-otc/tests/autotest_rc.lua` em
`client-otc/shinobirc.lua`: login `god`, `/arena` (sai da protection zone),
`/looktype 128`, `g_game.walk` 6× em cada direção e `g_app.doScreenshot` a cada
130 ms durante o movimento. Resultado em `screenshots/player_*.png`.

- **Rodada 1** pegou um defeito: a fase de passagem do norte era o quadro 0074
  (cabeça baixa, mas com rosto desenhado) e **piscava um rosto de frente** a cada
  volta do ciclo. Trocada pelo espelho do 0068.
- **Rodada 2** (final): as 4 direções corretas, pés no chão em todas as fases,
  sem mudança de tamanho ao virar, leste e oeste espelhados, ciclo do leste com
  as 3 poses visivelmente distintas.

### Limitações

- Não há vista de costas: o norte é 0068 + espelho, então o ciclo tem só **2
  poses distintas** e lê como um balanço, não como uma passada.
- Não há passo frontal: o sul usa 0070 e o seu espelho para simular a alternância.
- O oeste é espelhado do leste, então bandana e zíper trocam de lado (invisível a
  32 px).
- Os quadros de 39–41 px são reduzidos a 80% e perdem ~1 px de detalhe no rosto.
- `layers = 1`: as cores de outfit (`head/body/legs/feet`) que o servidor manda
  são ignoradas no 128 — todo jogador fica com a mesma roupa laranja.
- O looktype 898 tem a mesma arte nas 4 direções (só o oeste é espelhado): quem
  usar precisa travar a direção ou usá-lo apenas como animação.

## Personagens MUGEN (`import_mugen.py` + `overrides/40_mugen.json`)

Os looktypes **900–926** são 26 personagens de Naruto vindos de um material
privado do usuário em `assets-src/import/mugen/` (fora do git, ADR-002): 21.653
BMPs paletados, rips estilo MUGEN/JUS de um jogo de luta. A numeração é **fixa** e
vive em `assets-src/sprites/mugen_looktypes.json` (looktype → pasta → nome), que é
versionado e serve tanto para a arte quanto para o uso no jogo.

```bash
.venv/bin/python tools/spr/import_mugen.py           # triagem + PNGs + 40_mugen.json
.venv/bin/python tools/spr/import_mugen.py --report  # só o diagnóstico, não grava
.venv/bin/python tools/spr/import_mugen.py --only 913 922
.venv/bin/python tools/spr/build_assets.py
.venv/bin/python tools/spr/dump_dat.py               # validacao: OK, divergencias=0
```

### O que o material é (e o que não é)

Vista **lateral** de jogo de luta: o personagem olha para a direita ou para a
esquerda. **Não existe vista de frente nem de costas** em nenhum dos 26 rips
(conferido com um detector de pele na faixa da cabeça — ver `pick_back`, hoje só
acessível por override manual). O fundo é a **cor-chave do índice 0 da paleta**,
cuja cor concreta muda de quadro para quadro (verde escuro, verde neon…).

A ordem dos arquivos é *quase* sempre: ícone, retrato 120×140, parado
(respirando), agachar, andar, correr, pular e depois dezenas de golpes — mas
varia o bastante para não dar para confiar em índices fixos. O script mede cada
quadro.

### Conversão e peneiras

1. **BMP → RGBA** com chave dupla: índice 0 da paleta **e** a cor exata do pixel
   (0,0). Alguns rips remapeiam a paleta; o canto superior esquerdo é sempre fundo.
2. **Tamanho**: acima de 96 px de lado é tela/efeito (320×240, 632×480…); abaixo
   de 12×20 é faísca, poeira ou ícone.
3. **Densidade da caixa**: abaixo de 10% é fumaça espalhada, acima de 75% é uma
   bola/pedra sólida (vários rips começam com dezenas dessas).
4. **Altura típica**: a moda das alturas do rip é a altura do personagem — ele
   aparece em centenas de quadros, cada efeito em poucos. Serve de **piso** para
   a busca da pose parada.

### Escolha automática dos quadros

- **Parado** = a animação de *respirar*: a **primeira** corrida de quadros
  consecutivos com a silhueta quase constante (altura e largura variando ≤ 4 px)
  e mais alta que larga (`w ≤ 0,90 h`). Dentro dela fica o quadro **mediano pelo
  vão entre os pés**. Também testei "a corrida mais longa" e "a mais estreita":
  as duas erram mais (a mais longa pega o ciclo de andar do Kakashi, a mais
  estreita pega uma pose inclinada do Naruto Kid).
- **Andar** = 3 quadros **consecutivos** com a mesma altura do parado, com o
  **vão entre os pés oscilando** (contato → passagem → contato oposto, o mesmo
  critério do `30_player.json`), silhueta realmente mudando entre as fases
  (diferença de máscara ≥ 3%), paleta parecida com a do parado (cosseno ≥ 0,80,
  o que derruba espadas de chakra e mantos de raposa) e contagem de pixels a até
  ±45% da do parado. Três passadas, da mais exigente para a mais tolerante:
  primeiros 45 quadros com ±3 px de altura, depois ±6 px, depois até o quadro 120.
- **Lado** = massa de pixels de **pele no terço superior** à esquerda × à direita
  da caixa. Leste = olhando para a direita; se o rip olha para a esquerda, todos
  os quadros entram espelhados e o oeste desespelha.
- **Norte/Sul**: não existem no material. As três direções N/L/S usam o mesmo
  perfil e o oeste é `mirror_of: 1`.

### Overrides manuais

`OVERRIDES`, no topo de `tools/spr/import_mugen.py`, permite fixar `idle`,
`walk`, `faces` e `back` por looktype, pelo **número do arquivo** (`_NNNN`), não
pelo índice na lista filtrada. **11 dos 26** precisaram:

| Motivo | Looktypes |
|---|---|
| O rip **não tem** ciclo de andar (só parado, agachar, pular e golpes) — uso as fases do respirar como andar | 902 Sakura Kid, 907 Minato, 908 Minato Edo, 915 Sasuke Akatsuki, 925 Naruto Girl |
| A heurística elegeu um golpe com efeito grande como "andar" | 919 Naruto Sennin, 920 Naruto KCM |
| Forma de raposa: o rip começa com dezenas de efeitos e o bicho é quadrúpede | 921 1 Calda, 922 4 Caldas, 923 6 Caldas, 926 Kid Fox (só o lado) |
| A primeira corrida de silhueta constante era um "apontar o braço" em loop | 911 Pain |

### Saídas

- `assets-src/import/extracted/mugen/<looktype>/{idle,walk0,walk1,walk2}_NNNN.png`
  — os quadros recortados (privado);
- `assets-src/import/extracted/mugen/_review_<looktype>.png` — folha de revisão
  por personagem: parado + 3 fases nas 4 direções, ampliada 3×, já passada pelo
  `fit_uniform` (é o que o build vai gravar);
- `assets-src/import/extracted/mugen/_review_all.png` — folha geral, uma linha
  por personagem;
- **`assets-src/sprites/overrides/40_mugen.json`** — o único versionado. Mesmo
  esquema do `imports.json`/`30_player.json`; `root` aponta para o material bruto
  e os `src` começam com `../extracted/` porque os recortes ficam fora dele. Toda
  entrada cujo PNG não existir é ignorada com aviso: numa máquina sem o material
  o build cai no placeholder.

### Encaixe

`Importer.creature_dirs` + `fit_uniform`: **uma escala só por personagem**
(`min(32/maior_largura, 32/maior_altura, 1)`), base dos pés no chão da célula e
centro do apoio (centroide do terço inferior) no meio. Todos são **1×1**, como o
outfit do jogador — nada vira 1×2. Madara (60 px) cai para ~53%, as formas de
raposa (86 px de largura) para ~37% e ficam pequenas na célula: é o preço de um
bicho quadrúpede e largo em 32×32.

### Teste in-game (2 rodadas)

Cópia temporária de `client-otc/tests/mugen_rc.lua` em `client-otc/shinobirc.lua`
(removida no fim): login `god`, `/arena`, e para 900, 901, 906, 911, 913 e 922
troca de outfit + `g_game.walk` nas 4 direções com 2 screenshots por direção →
`screenshots/mugen_<looktype>_*.png`. **0 erros no cliente.**

- **Rodada 1** achou dois defeitos do *teste* (não da arte): o `/looktype` do TFS
  recusa id ≥ 903 (`server/tfs/data/talkactions/scripts/looktype.lua`, fora do
  escopo deste trabalho), então o rc passou a trocar o outfit **no cliente**
  (`localPlayer:setOutfit`) — quem desenha e anima a criatura é ele, é o
  suficiente para conferir a arte; e 3 `zoomIn` cortavam o boneco na captura.
- **Rodada 2** (final): os 6 renderizam certo, pés no chão, sem mudar de tamanho
  ao virar, as 3 fases de andar visivelmente diferentes e o oeste espelhado.

### Limitações

- **Não há norte nem sul**: as três direções mostram o mesmo perfil. Andando para
  cima ou para baixo o personagem continua de lado. É a mesma limitação do
  `30_player.json`, só que aqui vale para os **quatro** lados menos o oeste.
- O oeste é espelhado do leste: bandana, zíper e arma trocam de lado (invisível a
  32 px).
- `layers = 1`: as cores de outfit (`head/body/legs/feet`) do servidor são
  ignoradas — cada looktype tem uma roupa fixa.
- 5 personagens não têm ciclo de andar no material e apenas *balançam* ao andar.
- As formas de raposa (921–923, 926) são quadrúpedes largos: reduzidos a ~37% da
  altura original, leem como um vulto vermelho a 32 px.
- Tenten (905) carrega um leque gigante em **todos** os quadros do rip; ele ocupa
  metade da célula e não há como separá-lo.
- O `/looktype` do TFS não alcança 900–926: para usar in-game é preciso mexer em
  `server/` (fora do escopo) ou setar o outfit por script.

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
.venv/bin/python tools/spr/gen_borders.py        # 48 PNGs em terrain/borders/
# declarar border_<par>_<peca> em assets-src/sprites/tiles.json (feito)
.venv/bin/python tools/spr/allocate_ids.py        # ids permanentes
.venv/bin/python tools/map/build_valley.py        # autoborder no mapa (apply_borders)
.venv/bin/python tools/map/render_preview.py      # PNG de conferência sem cliente
.venv/bin/python tools/spr/build_assets.py        # só entao grava items.otb/.dat/.spr
```

Reusa as paletas de `gen_terrain.py` (import direto do módulo, sem duplicar
`P_GRASS`/`P_DIRT`/`P_WATER`/`P_MUD`/`P_COBBLE`) para a borda casar
exatamente com o chão que ela cobre.

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
- O terreno procedural não tem **bordas de transição** (grama→terra, terra→água):
  cada material termina no limite do tile. Falta um conjunto de itens de borda no
  mapa (`GROUND_BORDER`) para o encontro ficar suave.
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
