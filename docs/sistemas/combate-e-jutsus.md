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
  "rank": { "id": "genin", "title": "Genin da vila", "index": 1 },  // ou null (NarutoRanks ausente)
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
| `{"type":"get_progress"}` | responde `progress` (ver abaixo) sem mudar nada |

Se a seleção for inválida (personagem de outra vila para um não-GM, id desconhecido) o
servidor manda um `sendCancelMessage` **e** o `state` atual — o cliente nunca fica sem estado.

**Servidor → cliente: `progress`** (ação `get_progress`, aba "Missões" do menu Shinobi —
`docs/sistemas/cliente-ux.md`). Ao contrário do `state`, o `progress` **não** é empurrado
sozinho pelo servidor: o cliente pede sob demanda (abrir a aba, botão "Atualizar", depois de
`!diaria entregar`), porque a lista de 45 missões de história deixaria o payload
desnecessariamente grande para mandar em todo login/troca de personagem.

```json
{
  "type": "progress",
  "rank": {
    "id": "genin", "title": "Genin da vila", "index": 1,
    "next": {                                   // null se já for Kage (rank máximo)
      "id": "chunin", "title": "Chunin — aprovado no Exame Chunin", "index": 2, "minLevel": 20,
      "requirements": [                         // 1 por quest do grupo (NarutoQuests.rankGroups)
        { "name": "Exame Chunin — Torneio (3/3)", "npc": "Instrutora Ibuki", "done": false }
      ]
    }
  },
  "tasks": [   // só as ACEITAS (progressStorage >= 0), igual ao !tarefas
    { "id": "task_wolf_1", "name": "...", "npc": "Mestre de Tarefas Jiro", "monster": "Lobo",
      "progress": 3, "count": 8, "ready": false, "cooldownRemainingMin": 0 }
  ],
  "dailies": [  // as 3 do dia (NarutoDailies), status: progress | ready | delivered
    { "slot": 1, "id": "daily_wolves", "name": "Diária: Alcateia", "monster": "Lobo",
      "progress": 6, "count": 6, "status": "ready" }
  ],
  "missions": [  // TODAS as 45 quests de história (NarutoQuests.list), status:
                 // available | in_progress | done
    { "id": "q_lair_intro", "name": "Clones não sangram, mas caem",
      "npc": "Capitã Anbu Suzu", "status": "available" }
  ]
}
```

Implementado em `NarutoCharacters.sendProgress` (mesmo arquivo gerado que `sendState`), com 4
funções auxiliares (`rankProgressJson`, `tasksProgressJson`, `dailiesProgressJson`,
`missionsProgressJson`) — cada uma faz `if not NarutoX then return {} end` antes de usar
`NarutoRanks`/`NarutoTasks`/`NarutoDailies`/`NarutoQuests`, então o `progress` nunca quebra se
uma dessas libs não estiver instalada (ex.: servidor sem `data/tasks.json`). `NarutoQuests`
ganhou um índice reverso `NarutoQuests.byStorage[storage] -> quest` (usado por
`rankProgressJson` para achar nome/NPC de cada requisito de rank) e cada quest/tarefa passou a
carregar `npcName` (nome de exibição do NPC, ex. "Instrutora Ibuki") além do `npc` (id interno,
ex. `exam_proctor_forest`) — os dois campos vêm de `tools/export_tfs.py`.

**`state.rank` e `NarutoRanks.promote`**: `NarutoCharacters.sendState` agora inclui um campo
`rank` (id/título/índice do rank atual, ou `null` se `NarutoRanks` não estiver carregado) — é
esse campo que o cliente mostra na janela de Atributos (`docs/sistemas/cliente-ux.md`).
`NarutoRanks.promote` (chamada por `grantQuestRankIfReady` ao concluir a quest final de um
exame, ou por `/rank <id>` de GM) agora termina chamando `NarutoCharacters.sendState(player)`
(guardado por `if NarutoCharacters and NarutoCharacters.sendState then`) — o rank na tela
atualiza na hora da promoção, sem precisar reabrir o menu nem relogar.

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

## Efeitos e misseis (`animation` -> catálogo, 2026-09-05)

Cobertura 1:1 dos 54 jutsus (`data/jutsus/*.json`, campo `animation`) para uma
chave de `assets-src/sprites/effects.json` (catálogo procedural, ver
`docs/sistemas/arte-e-sprites.md` § Efeitos). Regra: `type=projectile` usa o
alias como MISSILE em voo (`COMBAT_PARAM_DISTANCEEFFECT`) e o IMPACTO
(`COMBAT_PARAM_EFFECT`) cai no efeito padrão do elemento (ex. katon =
`fx_fire_burst`); os demais tipos (area/beam/target/self) usam o alias
diretamente como efeito. Implementado em `tools/export_tfs.py`
(`jutsu_effect_id`/`jutsu_missile_id`, carregam o catálogo uma vez no topo
do script). `kawarimi`/`bunshin`/`shousen` (e todo self-buff genérico) são
casos especiais no gerador (não passam por `Combat()`) e usam a mesma função
`jutsu_effect_id`, com `bunshin` propositalmente resolvendo para
`fx_shadow_clone` (223) em vez do `fx_smoke_poof` (221) do `kawarimi` — a
mesma string `CONST_ME_POFF` antes tornava os dois idênticos.

| Jutsu | Elemento | Tipo | `animation` | Efeito/missile usado |
|---|---|---|---|---|
| `doton_bala_lama` | doton | projectile | `fx_mud_bullet` | impacto **fx_mud_splash**(215) + missile **ms_mud_bullet**(63) |
| `doton_muralha_pedra` | doton | self | `fx_stone_shell` | efeito **fx_stone_shell**(214) |
| `doton_estacas_terra` | doton | area | `fx_earth_spikes` | efeito **fx_earth_spikes**(212) |
| `doton_colapso_terreno` | doton | area | `fx_earth_collapse` | efeito **fx_earth_collapse**(213) |
| `fuuton_lamina_vento` | fuuton | projectile | `fx_wind_blade` | impacto **fx_wind_slash**(216) + missile **ms_wind_blade**(64) |
| `fuuton_rajada_cortante` | fuuton | area | `fx_wind_cone` | efeito **fx_wind_slash**(216) |
| `fuuton_tornado_cortante` | fuuton | beam | `fx_wind_tornado` | efeito **fx_wind_tornado**(217) |
| `fuuton_redemoinho_prisao` | fuuton | target | `fx_wind_prison` | efeito **fx_wind_prison**(218) |
| `katon_goukakyuu` | katon | projectile | `fx_fireball` | impacto **fx_fire_burst**(200) + missile **ms_fireball**(60) |
| `katon_housenka` | katon | area | `fx_fire_cone` | efeito **fx_fire_cone**(202) |
| `katon_karyuu_endan` | katon | beam | `fx_fire_dragon` | efeito **fx_fire_dragon**(203) |
| `katon_sopro_brasas` | katon | area | `fx_ember_cone` | efeito **fx_fire_cone**(202) |
| `katon_anel_chamas` | katon | area | `fx_fire_ring` | efeito **fx_fire_ring**(201) |
| `kawarimi` | none | self | `fx_log_poof` | efeito **fx_smoke_poof**(221) |
| `bunshin` | none | self | `fx_clone_poof` | efeito **fx_shadow_clone**(223) |
| `shousen` | none | self | `fx_heal_glow` | efeito **fx_heal_green**(220) |
| `fuuin_contencao` | none | target | `fx_seal_paper` | efeito **fx_seal_glow**(222) |
| `doku_kiri` | none | area | `fx_poison_mist` | efeito **fx_poison_mist**(225) |
| `clone_sombrio` | none | self | `fx_smoke_puff` | efeito **fx_smoke_poof**(221) |
| `punho_suave` | none | target | `fx_taijutsu_hit` | efeito **fx_melee_hit**(224) |
| `chute_giratorio` | none | area | `fx_taijutsu_spin` | efeito **fx_melee_hit**(224) |
| `agulhas_multiplas` | none | projectile | `fx_needles` | impacto **fx_melee_hit**(224) + missile **ms_senbon**(67) |
| `lamina_chakra` | none | beam | `fx_chakra_blade` | efeito **fx_chakra_blade**(226) |
| `raio_selado` | raiton | projectile | `fx_lightning_bolt` | impacto **fx_lightning_strike**(208) + missile **ms_lightning_needle**(62) |
| `fuuton_rasteira_vento` | fuuton | area | `fx_wind_sweep` | efeito **fx_wind_slash**(216) |
| `vigor_teimoso` | none | self | `fx_aura_orange` | efeito **fx_chakra_focus**(219) |
| `foco_ocular` | none | self | `fx_eye_glow` | efeito **fx_chakra_focus**(219) |
| `agulhas_incendiarias` | katon | projectile | `fx_burning_needles` | impacto **fx_fire_burst**(200) + missile **ms_senbon**(67) |
| `contra_ataque_calculado` | none | target | `fx_counter_strike` | efeito **fx_melee_hit**(224) |
| `soco_monstruoso` | none | target | `fx_ground_crack` | efeito **fx_earth_collapse**(213) |
| `palma_gentil` | none | target | `fx_palm_strike` | efeito **fx_melee_hit**(224) |
| `visao_total` | none | self | `fx_eye_veins` | efeito **fx_chakra_focus**(219) |
| `palma_dupla` | none | area | `fx_double_palm` | efeito **fx_melee_hit**(224) |
| `soco_da_juventude` | none | target | `fx_heavy_punch` | efeito **fx_melee_hit**(224) |
| `chute_ascendente` | none | target | `fx_rising_kick` | efeito **fx_melee_hit**(224) |
| `lamina_relampago_pessoal` | raiton | target | `fx_sword_spark` | efeito **fx_lightning_strike**(208) |
| `corte_duplo` | none | area | `fx_double_slash` | efeito **fx_melee_hit**(224) |
| `bainha_eletrica` | raiton | self | `fx_lightning_armor` | efeito **fx_lightning_armor**(211) |
| `kunai_marcada` | none | projectile | `fx_marked_kunai` | impacto **fx_melee_hit**(224) + missile **ms_kunai**(65) |
| `salto_do_selo` | none | self | `fx_flash_teleport` | efeito **fx_smoke_poof**(221) |
| `explosao_do_selo` | none | area | `fx_seal_explosion` | efeito **fx_seal_glow**(222) |
| `barreira_protetora` | none | self | `fx_barrier_glow` | efeito **fx_chakra_focus**(219) |
| `selo_de_exorcismo` | none | target | `fx_seal_paper` | efeito **fx_seal_glow**(222) |
| `circulo_de_selos` | none | area | `fx_seal_circle` | efeito **fx_seal_glow**(222) |
| `raiton_hari` | raiton | projectile | `fx_lightning_needle` | impacto **fx_lightning_strike**(208) + missile **ms_lightning_needle**(62) |
| `raiton_punho_trovao` | raiton | target | `fx_thunder_fist` | efeito **fx_lightning_strike**(208) |
| `raiton_corrente_estatica` | raiton | area | `fx_static_cross` | efeito **fx_static_field**(209) |
| `raiton_lanca_relampago` | raiton | beam | `fx_lightning_lance` | efeito **fx_lightning_lance**(210) |
| `raiton_armadura_eletrica` | raiton | self | `fx_lightning_armor` | efeito **fx_lightning_armor**(211) |
| `suiton_mizudan` | suiton | projectile | `fx_water_bullet` | impacto **fx_water_splash**(204) + missile **ms_water_bullet**(61) |
| `suiton_suiryuudan` | suiton | beam | `fx_water_dragon` | efeito **fx_water_dragon**(205) |
| `suiton_nevoa_cortante` | suiton | area | `fx_mist_cone` | efeito **fx_water_mist**(206) |
| `suiton_prisao_agua` | suiton | target | `fx_water_prison` | efeito **fx_water_vortex**(207) |
| `suiton_vortice_devorador` | suiton | area | `fx_water_vortex` | efeito **fx_water_vortex**(207) |
### Validação in-game

`client-otc/tests/vfx_rc.lua` (copiado para `client-otc/shinobirc.lua` — arquivo
compartilhado, removido ao final, nunca comitado): login `slqa`, `/lvl 60` +
`/full`, troca de personagem/elemento via GM (`/personagem`, `/elemento`) e
`/m Bandido` + `g_game.attack` antes de cada jutsu que precisa de alvo,
3 screenshots a 150ms de intervalo por cast. Cobriu os 5 elementos (projétil +
a assinatura de área/beam mais forte), `kawarimi`, `bunshin`, `shousen`,
`lamina_chakra`, `doku_kiri` — 46 PNGs em `screenshots/vfx_*.png`. Resultado:
burst de fogo visível no impacto do Bandido, trilha do dragão de fogo/água em
vários tiles ao longo da linha, raio serrilhado amarelo bem legível na lança do
relâmpago, fumaça branca do kawarimi x fumaça ROXA distinta do bunshin, cura
verde pulsante, lâmina de chakra ciano brilhante, névoa de veneno cobrindo o chão
em área. Ver detalhe completo em `docs/sistemas/arte-e-sprites.md`.
