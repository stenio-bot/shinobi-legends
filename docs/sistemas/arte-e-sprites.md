# Sistema de arte e sprites

## Objetivo

O OTClient só desenha alguma coisa se existir um par `Tibia.spr` + `Tibia.dat`
da versão 10.98 em `client-otc/data/things/1098/`. Como **nenhum sprite da Tibia
ou de NTO pode ser usado** (ADR-002) e não há ObjectBuilder no Mac, o projeto tem
seu próprio compilador de assets: `tools/spr/`.

## Pipeline

```
data/tfs_mapping.json ─┐
server/tfs/data/items/items.otb ─┐
                                 ├─> tools/spr/gen_placeholders.py
tools/spr/art.py (desenho) ──────┘        │
                                          ▼
                          assets-src/sprites/**.png + manifest.json
                                          │
                                          ▼
                          tools/spr/build_assets.py
                                          │
                                          ▼
                client-otc/data/things/1098/Tibia.spr + Tibia.dat
                                          │
                                          ▼
                          tools/spr/dump_dat.py (validação)
```

- **Fonte da verdade da arte:** `assets-src/sprites/` (PNGs) + `manifest.json`.
- **Artefatos gerados:** `client-otc/data/things/1098/Tibia.spr` e `Tibia.dat`.
  Nunca edite à mão; regenere.
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
