# Sistema: Combate e Jutsus

## Fluxo de um ataque
1. Jogador seleciona alvo (clique) ou usa jutsu em direção/área.
2. Sistema verifica: alcance, linha de visão, cooldown, chakra.
3. Calcula dano → aplica → dispara eventos (`damage_dealt`, `entity_died`).
4. Efeitos (queimadura, lentidão) entram na lista de status do alvo.

## Fórmulas (todas em `damage_calc.gd`, sem estado)
```
dano_fisico  = (ataque_arma + skill_relevante * 0.5) * rand(0.8, 1.0) - defesa_alvo * 0.5
dano_jutsu   = (jutsu.base_damage + level * jutsu.level_scale + ninjutsu * jutsu.skill_scale)
               * multiplicador_elemental * rand(0.9, 1.1)
defesa_alvo  = soma(defesa dos itens) + skill_defesa * 0.3
crítico      = 5% base, dano * 1.5
```
Dano mínimo sempre 1.

## Elementos e afinidade
```
Katon (fogo)  > Fuuton (vento) > Raiton (raio) > Doton (terra) > Suiton (água) > Katon
```
Vantagem: ×1.5. Desvantagem: ×0.75. Neutro: ×1.0. Monstros têm `element` (ou `none`).

## Anatomia de um jutsu (`data/schemas/jutsu.schema.json`)
| Campo | Descrição |
|---|---|
| `id`, `name`, `description` | identidade |
| `element` | katon, suiton, doton, fuuton, raiton, none |
| `type` | `projectile`, `area`, `self`, `target`, `beam` |
| `shape` | para área: `circle_r1`, `cross_r2`, `line_5`, `cone_3`... |
| `range` | tiles |
| `chakra_cost`, `cooldown_s` | recurso e tempo |
| `base_damage`, `level_scale`, `skill_scale` | fórmula |
| `required_level`, `required_skill` | pré-requisito |
| `villages` | quem pode aprender (`[]` = todas) |
| `effects` | lista de status: `{type, chance, duration_s, value}` |
| `animation`, `sfx` | assets |

## Status (efeitos)
| Tipo | Efeito |
|---|---|
| `burn` | dano por segundo |
| `slow` | reduz velocidade |
| `stun` | não age por X s |
| `poison` | dano por segundo, stackável |
| `paralyze` | não move (pode usar jutsu) |
| `heal_over_time` | cura por segundo |

## Hotbar
No OTClient a hotbar é o módulo `game_actionbar` (barra inferior 1, teclas F1–F12). Os jutsus
chegam nela por `client-otc/modules/naruto_theme/naruto_jutsus.lua`:

- **Onde vivem os dados.** O cliente só conhece as spells da Tibia
  (`modules/gamelib/spells.lua`: `SpellInfo['Default']` + `SpelllistSettings['Default']`).
  `tools/export_tfs.py` gera `client-otc/modules/naruto_theme/jutsus_data.lua` (cabeçalho
  `GERADO`) com um **segundo perfil**, `'Shinobi'`, no mesmo formato — `name`, `words` (os selos,
  iguais aos do `spells_naruto.xml`), `level`, `mana`, `exhaustion` (cooldown em ms),
  `group = {[1|2] = 1000}`, `vocations`, `description`, `clientId` (índice do ícone). O
  `naruto_theme` só acrescenta as chaves `SpellInfo['Shinobi']` / `SpelllistSettings['Shinobi']`;
  nenhum módulo original é sobrescrito.
- **Ícones.** `.venv/bin/python tools/spr/gen_jutsu_icons.py` desenha (Pillow, arte própria)
  `client-otc/data/images/game/spells/jutsus.png`: tira horizontal de 25 ícones 32×32, cor por
  elemento e símbolo por tipo (projétil/alvo = bola, área = anel, beam = linha, self = silhueta,
  cura = cruz; pontinhos no canto = tier). A **ordem da tira** (elemento → tier → level → id) é a
  mesma de `jutsu_icon_order` nos dois scripts — mexeu em um, regenere o outro.
- **Vocação = vila.** `player:getVocation()` devolve o `clientid` da vocação
  (`data/tfs_mapping.json` → `villages.*.vocation_id`). O OTClient traduz isso para as vocações
  da Tibia (`VocationsClient` → `VocationsServer`, `logics/const.lua translateVocation`), então
  cada jutsu é exportado com `vocations = {base, base+4}`: Folha `{4,8}`, Névoa `{3,7}`,
  Nuvem `{1,5}`, Areia `{2,6}`; jutsus neutros levam as oito.
- **Preenchimento automático.** Em `onGameStart` (+1,5 s, para o level/vocação já terem chegado)
  o módulo cria/seleciona um conjunto de hotkeys por vila (`Vila da Folha`, `Vila da Nevoa`…) e,
  **se a barra inferior 1 desse conjunto estiver vazia**, grava nos slots 1..12 os jutsus que o
  personagem pode usar (vocação + level), ordenados por level, via
  `ApiJson.createOrUpdateText(1, i, words, true)` — o mesmo formato `chatText`/`sendAutomatically`
  que a UI grava quando você arrasta uma spell para o slot — e liga F1..F12 com
  `ApiJson.updateActionBarHotkey`. Depois `ApiJson.saveData()` + `selectHotkeySet` para redesenhar.
  Slots já preenchidos pelo jogador nunca são sobrescritos.
- **Lista de Jutsus** (Alt+L): `naruto_jutsus` chama `setSpelllistProfile('Shinobi')`, então a
  janela lista os 25 jutsus com ícone e o filtro de "Vila" já vem marcado na vila do personagem.

## Personagem + Elemento: 4 + 4

**Decisão de design (substitui "aprender jutsu por level/vila" como fluxo principal):** ao
entrar no jogo o jogador escolhe um **PERSONAGEM** (`data/characters.json`, looktype 900–909)
e um **ELEMENTO** (katon, suiton, doton, fuuton ou raiton). Ele recebe imediatamente, já no
nível máximo (sem cooldown de aprendizado, sem pergaminho), **8 jutsus**:

- **4 jutsus PESSOAIS** (`personal_jutsus` do personagem) — a identidade dele: taijutsu,
  armas, selos, visão etc. Não são elementais (o `element` do jutsu pode ser `none` ou um
  elemento "de sabor", mas nunca é um dos 4 jutsus de um `element_sets.json`).
- **4 jutsus do ELEMENTO** (`data/element_sets.json`, schema
  `data/schemas/element_set.schema.json`) — o mesmo kit para qualquer personagem/vila que
  escolha aquele elemento. Ordem fixa de uso: **1 projétil básico → 1 área/cone → 1 beam/linha
  forte → 1 utilitário (defensivo ou de controle)**.

Vilas continuam existindo como vocação/town (cidade inicial, NPCs, skill bônus), mas **não
filtram mais jutsu**: todo jutsu em `data/jutsus/*.json` tem `villages: []`. A progressão do
jogador deixa de ser "aprender jutsu" e passa a ser treino físico — level e skills (Taijutsu,
Ninjutsu, Genjutsu, Defesa, Shuriken) sobem a fórmula de dano dos mesmos 8 jutsus, não
desbloqueiam jutsus novos. Troca de elemento: fora do MVP inicial (mesma regra de "mudança de
vila" — ver `docs/sistemas/vilas-e-clas.md`); troca de personagem continua existindo como
mecânica de GM/talkaction (`!personagem`), e troca junto o elemento para o `default_element`
do personagem escolhido, a menos que o jogador reescolha.

### Elementos e seus 4 jutsus (`data/element_sets.json`)

| Elemento | Projétil básico | Área/cone | Beam/linha forte | Utilitário (defensivo/controle) |
|---|---|---|---|---|
| Katon (Fogo) | Grande Bola de Fogo | Flores de Fênix | Dragão de Fogo | Anel de Chamas |
| Suiton (Água) | Projétil de Água | Névoa Cortante | Dragão de Água | Prisão de Água |
| Raiton (Raio) | Agulha de Raio | Corrente Estática | Lança do Relâmpago | Armadura Elétrica |
| Doton (Terra) | Bala de Lama *(novo)* | Estacas de Terra | Colapso do Terreno | Muralha de Pedra |
| Fuuton (Vento) | Lâmina de Vento | Rajada Cortante | Tornado Cortante *(novo)* | Redemoinho Prisão *(novo)* |

Doton tinha só 3 jutsus (faltava projétil) e Fuuton só 2 (faltava beam e utilitário/controle):
os 3 jutsus marcados "novo" foram criados em `data/jutsus/doton.json` e `data/jutsus/fuuton.json`
seguindo a mesma curva de `docs/sistemas/balanceamento.md` (tier 1 para o projétil, tier
2/3 para o resto). Katon, Suiton e Raiton já tinham jutsu de sobra nas quatro categorias — os
jutsus elementais que não entraram no set (`katon_sopro_brasas`, `suiton_vortice_devorador`,
`raiton_punho_trovao`...) continuam válidos em `data/jutsus/*.json`, só ficam de fora do kit
automático (candidatos a loot/pergaminho de bônus no futuro).

### Personagens e seus 4 jutsus pessoais (`data/characters.json`)
Ver a tabela completa em `docs/sistemas/vilas-e-clas.md` → "Personagens e jutsus". Resumo:
cada personagem tem `personal_jutsus` (exatamente 4, ids de `data/jutsus/*.json`, `villages:
[]`), mais `description` (1 frase de identidade) e `default_element` (sugestão inicial). Os
jutsus pessoais que faltavam foram criados em `data/jutsus/personal.json`; o restante reutiliza
jutsus já existentes (`clone_sombrio`, `punho_suave`, `chute_giratorio`, `agulhas_multiplas`,
`lamina_chakra`, `raio_selado`, `kawarimi`, `bunshin`, `shousen`, `fuuin_contencao`,
`doku_kiri`) — alguns compartilhados entre 2 personagens (ex.: `kawarimi`), nunca mais que
isso.

### Protocolo opcode 210 (servidor ↔ cliente)

A escolha de personagem/elemento acontece no **menu Shinobi do cliente**, que fala com o
servidor pelo **opcode estendido 210** (`CREATURE_EVENT_EXTENDED_OPCODE` do TFS; o buffer é
uma string **JSON**). Servidor: `server/generated/scripts/naruto/character_switch.lua`
(gerado por `tools/export_tfs.py`) + `server/generated/lib/naruto_json.lua` (JSON puro em Lua
— o TFS 1.4.2 não traz nenhuma biblioteca JSON).

**Servidor → cliente: `state`.** Enviado ~1 s depois do login (`addEvent` de 1000 ms, tempo de
o cliente carregar os módulos) e depois de qualquer mudança (`select`, `!personagem`,
`!elemento`, `/personagem`, `/elemento`, `/jutsus`).

```json
{
  "type": "state",
  "first_time": false,          // true no 1º login (storage 60000 ainda vazio)
  "is_gm": false,               // conta GOD: vê os personagens de TODAS as vilas
  "character": "genin_uchiha",  // ou null
  "element": "suiton",          // ou null
  "level": 8,
  "village": "leaf",            // leaf | mist | cloud | sand
  "characters": [               // só os da vila do jogador (GM: todos os 9)
    {
      "id": "genin_laranja",
      "name": "Genin Laranja",
      "description": "Um genin barulhento e teimoso que nunca desiste de um combate.",
      "looktype": 900,
      "village": "leaf",
      "default_element": "fuuton",
      "jutsus": [ { "id": "clone_sombrio", "name": "Clone Sombrio",
                    "words": "clone sombrio", "element": "none",
                    "type": "self", "chakra": 35, "cooldown_s": 20 } ]
    }
  ],
  "elements": [ { "id": "katon", "name": "Fogo", "jutsus": [ /* mesmo formato, 4 itens */ ] } ],
  "active_jutsus": [ /* os 8 atuais: 4 pessoais, depois 4 elementais */ ]
}
```

**Cliente → servidor** (mesmo opcode 210):

| Buffer | Efeito |
|---|---|
| `{"type":"select","character":"genin_uchiha","element":"katon"}` | valida, aplica e responde `state`. Qualquer um dos dois campos pode vir `null`/ausente = **manter** o atual |
| `{"type":"get_state"}` | responde `state` sem mudar nada |

Se a seleção for inválida (personagem de outra vila para um não-GM, id desconhecido) o
servidor manda um `sendCancelMessage` **e** o `state` atual — o cliente nunca fica sem estado.

**O que `NarutoCharacters.apply(player, characterId, elementId, opts)` faz**, na ordem:
libera os trajes da vila no 1º login → `player:addOutfit(look)` do personagem → `forgetSpell`
de **todos** os jutsus pessoais e elementais (`NarutoCharacters.allJutsuNames`, menos os
universais como `kawarimi`) → `learnSpell` dos 4 + 4 → `setOutfit` → storages → `sendState`.
Todos os jutsus saem do gerador com `needlearn="1"` e **sem filtro de vocação** no
`spells.xml`: quem controla o acesso é o par learn/forget, não a vila.

| Storage | Conteúdo |
|---|---|
| `60000` | `1` depois da primeira aplicação (usado para `first_time` e para liberar os trajes) |
| `60001` | `looktype` do personagem atual |
| `60002` | índice do elemento em `NarutoElements.list` (ordem katon, suiton, raiton, doton, fuuton) |

> **Armadilha (custou um bug real): `NetworkMessage::addString` do TFS 1.4.2 descarta em
> silêncio qualquer string com mais de 8192 bytes** (`server/tfs/src/networkmessage.cpp`).
> `Player.sendExtendedOpcode` (`data/lib/core/player.lua`) usa `addString`, então o `state` de
> um **GM** (~11 KB, porque lista os 9 personagens) chegava ao cliente como um `0x32` sem
> corpo e o OTClient logava `ProtocolGame parse message exception ... InputMessage eof
> reached`. O `state` de um jogador normal (~6 KB) passava — o bug só aparecia na conta `god`.
> Solução em `naruto_json.lua`: `NarutoJson.sendExtended(player, opcode, str)` usa
> `sendExtendedOpcode` até 8192 bytes e, acima disso, monta o pacote na mão
> (`addByte(0x32)`, `addByte(opcode)`, `addU16(#str)`, um `addByte` por caractere), que só
> esbarra em `MAX_BODY_LENGTH` = 24576.

## Formas de aprender jutsu (fluxo legado, mantido para pergaminhos/drops futuros)
- Automático ao atingir level (jutsus básicos da vila) — **substituído** pelo fluxo
  Personagem + Elemento acima para os 8 jutsus principais.
- Comprar pergaminho de NPC (custo em ryo) — continua válido para jutsus elementais fora do
  set (ex.: `katon_sopro_brasas`) e jutsus lendários.
- Drop raro de boss (jutsus lendários).

## Jutsus por PERSONAGEM + ELEMENTO (servidor TFS)
No servidor (ver `docs/sistemas/vilas-e-clas.md` → "Personagens e jutsus"), o jogador escolhe
um PERSONAGEM (`data/characters.json`, outfit 900–909) e um ELEMENTO
(`data/element_sets.json`), com um kit fixo de **4 pessoais + 4 elementais = 8 jutsus** (a
VILA/vocação deixou de decidir isso). Isso é aplicado via `spells.xml`: todo jutsu tem `needlearn="1"`
(exceto `kawarimi`, universal) e o servidor só sabe quais jutsus o jogador conhece através de
`player:learnSpell`/`forgetSpell` — chamados por `NarutoCharacters.apply` (`server/generated/
scripts/naruto/character_switch.lua`) sempre que o personagem troca (`!personagem <nome>` para
jogadores, `/personagem <id|nome>` para GM). Tentar usar um jutsu que não está no kit do
personagem atual é recusado pelo servidor com "You must learn this spell first.", mesmo que o
jogador conheça as palavras do jutsu de um personagem anterior.

No cliente, `client-otc/modules/naruto_theme/naruto_jutsus.lua` reage à troca de personagem
(evento `onOutfitChange` do `LocalPlayer`) preenchendo a barra de ação (slot 1) com os jutsus
do personagem atual (`NarutoCharacterJutsus[looktype]`, gerado em `jutsus_data.lua`). A janela
"Lista de Jutsus" continua filtrando por vila (vocação), não por personagem.
