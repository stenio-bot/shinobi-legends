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

## Formas de aprender jutsu
- Automático ao atingir level (jutsus básicos da vila).
- Comprar pergaminho de NPC (custo em ryo).
- Drop raro de boss (jutsus lendários).
