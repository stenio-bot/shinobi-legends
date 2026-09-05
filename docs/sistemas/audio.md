# Sistema: Áudio

## Formato suportado pelo cliente (descoberto no C++)

`client-otc/src/framework/sound/soundfile.cpp` (`SoundFile::loadSoundFile`) só reconhece um
formato: lê os 4 primeiros bytes do arquivo e, se forem `OggS` (magic do container Ogg), monta
um `OggSoundFile` (`oggsoundfile.cpp`, decodifica via `libvorbisfile`/`ov_open_callbacks`);
qualquer outro magic lança `Exception("unknown sound file format")`. **Não há suporte a WAV,
MP3 ou qualquer outro formato** — só **Ogg Vorbis** (não Opus: o decoder é `libvorbisfile`, que
não lê Opus-em-Ogg). Mono ou estéreo, 8 ou 16 bits (`SoundFile::getSampleFormat`).

`SoundManager::play()`/`preload()` resolvem o nome do arquivo com `g_resources.guessFilePath`
(`+".ogg"` se não tiver extensão) e `resolvePath`. **Armadilha real, encontrada testando**:
`ResourceManager::resolvePath` (`src/framework/core/resourcemanager.cpp`) resolve um caminho
que **não** começa com `/` contra o diretório do **módulo Lua que está chamando**
(`g_lua.getCurrentSourcePath()`), não contra a raiz de dados — por isso o próprio
`modules/client/client.lua` guarda seu som em `modules/client/sounds/startup.ogg` e usa o
caminho relativo `'sounds/startup'`. Como os SFX do projeto moram em
`client-otc/data/sounds/naruto/` (that's fora de qualquer módulo — `data/` é montada na raiz
`/` por `g_resources.addSearchPath` em `init.lua`), `modules/naruto_sounds` precisa chamar
`g_sounds.play('/sounds/naruto/<arquivo>.ogg', ...)` com **barra inicial** (caminho absoluto);
sem ela o resolvedor produzia `/naruto_sounds/sounds/naruto/<arquivo>.ogg` e falhava com
`unable to open file ...: not found` (log real do primeiro teste, corrigido em
`naruto_sounds.lua`).

`g_sounds.play(filename, fadetime=0, gain=0, pitch=0)` cria um `SoundSource` avulso — **não**
usa `SoundChannel` (canais só servem para streaming/enqueue, ex. música). Por isso o volume de
"Sons do jogo" é aplicado manualmente no `gain` passado a cada chamada (não existe um
"canal de efeitos" para abaixar de uma vez).

## Encoder usado (sem downloads, sem `ffmpeg`/`sox`)

A máquina não tem `ffmpeg` nem `sox` instalados. Em vez de `brew install`, instalei o pacote
Python **`soundfile`** na `.venv` (`'.venv/bin/pip install soundfile'` — puxa `cffi`/`pycparser`
como dependência, ~1 MB) porque o wheel do PyPI para macOS já embute o **libsndfile**
compilado com suporte a Ogg Vorbis (`sf.available_subtypes('OGG')` lista `VORBIS`/`OPUS`).
`tools/audio/gen_sfx.py` sintetiza cada som como array numpy, escreve um WAV de staging
(`wave` da stdlib, apagado ao final) e converte para `.ogg` com
`soundfile.write(path, data, rate, format='OGG', subtype='VORBIS')`. Nenhum material de
terceiros foi baixado (ADR-002) — todo o áudio é gerado por síntese subtrativa/FM simples em
`tools/audio/gen_sfx.py`.

## Geração procedural — `tools/audio/gen_sfx.py`

```
.venv/bin/python tools/audio/gen_sfx.py            # regenera tudo
.venv/bin/python tools/audio/gen_sfx.py --keep-wav  # mantém os WAV de staging (debug)
```

- 22.050 Hz, mono, 16 bits antes de converter para Ogg Vorbis; duração 0,05–1,2 s.
- Blocos de síntese reaproveitáveis: `_sine`/`_sine_sweep` (tom/glissando), `_noise` (ruído
  branco com seed determinístico), `_one_pole_lowpass`/`_highpass`/`_bandpass` (filtros de 1
  polo, baratos), `_envelope` (ADSR simplificado), `_chord` (sequência de notas curtas — usado
  em level up, moeda, conquista, cura).
- Cada som tem sua própria função/seed (fogo = whoosh + burst, água = splash + jorro, raio =
  crack + zumbido/loop, terra = impacto grave + pedras, vento = corte + rajada, kawarimi =
  poof, invocação = sopro grave, etc.) — ver `build_catalog()` no script para a lista completa.
- Normalização: pico em **-6 dBFS** (`_peak_normalize`, alvo linear ≈0,50) sem clipping (`int16`
  sempre dentro de [-32768, 32767]).
- Saída:
  - `client-otc/data/sounds/naruto/*.ogg` — **versionável** (síntese própria, sem IP de
    terceiros). 51 arquivos, ~380 KB no total (05/09/2026).
  - `assets-src/audio/sfx_catalog.json` — fonte da verdade: `{sounds: {id: {file|variations,
    gain, channel}}}`.
  - `client-otc/modules/naruto_sounds/sfx_catalog.lua` — espelho Lua do mesmo catálogo
    (`NarutoSfxCatalog`), gerado junto, para o módulo cliente não precisar de um parser JSON
    em tempo de jogo.

### Catálogo (50 entradas — 33 jutsus + 17 base; `sfx_taijutsu_hit` conta como 1 com 2 variações)

**Referenciados por `data/jutsus/*.json` (campo `sfx`)**: `sfx_bubble`, `sfx_double_hit`,
`sfx_dragon_roar`, `sfx_explosion`, `sfx_fire_burst`, `sfx_fire_puff`, `sfx_fire_whoosh`,
`sfx_focus`, `sfx_heal`, `sfx_heavy_punch`, `sfx_hiss`, `sfx_kick`, `sfx_metal_throw`,
`sfx_mist`, `sfx_poof`, `sfx_punch`, `sfx_quake`, `sfx_rock_crack`, `sfx_rock_rumble`,
`sfx_seal`, `sfx_shout`, `sfx_slash`, `sfx_splash`, `sfx_splat`, `sfx_teleport`,
`sfx_thunder`, `sfx_thunder_hit`, `sfx_wave`, `sfx_whirl`, `sfx_wind_burst`, `sfx_wind_cut`,
`sfx_wind_roar`, `sfx_wind_trap`, `sfx_zap`, `sfx_zap_loop`.

**Conjunto base do jogo**: `sfx_taijutsu_hit` (2 variações), `sfx_critical_hit`,
`sfx_damage_taken`, `sfx_monster_death`, `sfx_level_up` (3 notas, estilo Tibia),
`sfx_item_pickup`, `sfx_item_drop`, `sfx_coin`, `sfx_door`, `sfx_menu_open`, `sfx_menu_close`,
`sfx_click`, `sfx_achievement`, `sfx_chakra_empty` (buzzer de "erro"), `sfx_summon`. Cura reusa
`sfx_heal` (já no conjunto de jutsus).

## Módulo cliente — `client-otc/modules/naruto_sounds/`

Autoload (`.otmod`, `autoload-priority: 1150`, depois de `naruto_menu` — precisa dele já
carregado para o dispatch do opcode 210 e o hook de show/hide). Ver o cabeçalho de
`naruto_sounds.lua` para a lista completa; resumo dos 4 ganchos usados e por quê:

### (a) Efeito de jutsu visto na tela → opcode 210, ação `"sfx"`

**Investigação primeiro.** O Redemption **não tem** um callback Lua para "efeito
mágico/míssil apareceu no mapa" — `ProtocolGame::parseMagicEffect`/`parseAddMissile`
(`src/client/protocolgameparse.cpp`) e `Creature::onDeath`/etc. são os únicos pontos que
chamam `callLuaField`, e nenhum deles cobre `MagicEffect`/`Missile` (`grep -rn
"onMagicEffect\|onMissile" src/` não bate nada). `Effect`/`Missile` são `@bindclass` (dá para
inspecionar um que já existe), mas não há evento "um efeito foi adicionado".

**Decisão**: opcode estendido 210 (o mesmo já usado por `state`/`progress` do Menu Shinobi),
ação nova `"sfx"`. `tools/export_tfs.py` gera, dentro de **todo** `onCastSpell` (jutsus de
combate e os 3 `self` especiais — kawarimi, bunshin, buff/cura), a chamada:

```lua
if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(pos_ou_creature:getPosition(), "sfx_id") end
```

`NarutoJson.broadcastSfx(pos, sfxId, radius=7)` (nova função em `data/lib/naruto_json.lua`,
gerada dentro de `NARUTO_JSON_LUA` em `tools/export_tfs.py`) varre `Game.getSpectators(pos,
false, false, radius, radius, radius, radius)` e chama `NarutoJson.sendExtended(spec, 210,
'{"type":"sfx","id":"..."}')` para cada **jogador** espectador (conjurador incluído, já que ele
é seu próprio spectator) — é assim que "criaturas próximas" também ouvem.

No cliente, o opcode 210 **já é dono de `modules/naruto_menu`** (`ProtocolGame.
registerExtendedOpcode` só aceita 1 callback por código — 2ª chamada dá `error("Opcode is
already taken.")`, `gamelib/protocolgame.lua`). Em vez de brigar pelo opcode,
`naruto_menu.lua`'s `onExtendedOpcode` ganhou um 3º ramo `onSfx(data)` (ao lado de
`onState`/`onProgress`) que, quando `data.type == 'sfx'`, chama
`modules.naruto_sounds.onOpcodeSfx(data)` se o módulo existir.

**Por que `if NarutoJson.broadcastSfx then`**: achado real ao testar (ver seção "Limitações").

### (b) `onTextMessage` — nível e conquista

`registerMessageMode(MessageModes.Game, ...)` casa `'^You advanced from Level %d+ to Level
%d+%.$'` (mesmo texto cru em inglês que `naruto_theme/naruto_chat.lua` traduz para pt-BR — os
dois só **leem** o mesmo `onTextMessage`, não competem: `registerMessageMode` guarda uma
**lista** de callbacks por modo, não substitui) → `sfx_level_up`. Conquista é *best-effort*:
casa `'^Achievement unlocked: .+$'`/`'^Conquista desbloqueada.*$'`, mas **o projeto ainda não
tem um sistema de conquistas** que gere essa frase (ver Limitações) — o gancho existe e está
pronto, só não dispara hoje.

Dano recebido **não** usa `onTextMessage` (`MessageModes.DamageReceived` fica registrado só
como reforço) — o gancho principal é (c) abaixo, mais confiável que casar texto.

### (c) `connect(Creature, {...})` — dano recebido e morte de monstro

Mesmo padrão de `modules/game_battle/battle.lua`: conecta na **classe** `Creature` inteira (não
por instância), então cobre qualquer criatura que aparecer depois:

```lua
connect(LocalPlayer, { onHealthChange = onLocalHealthChange })  -- health caiu → sfx_damage_taken
connect(Creature, { onDeath = onCreatureDeath })                -- isMonster() e não isLocalPlayer() → sfx_monster_death
```

### (d) UI — abrir/fechar o Menu Shinobi, clique

`naruto_menu.lua`'s `show()`/`hide()` ganharam 2 linhas cada (`modules.naruto_sounds.play('sfx_
menu_open'|'sfx_menu_close')`, guardadas por `if modules.naruto_sounds then`). O botão `/god`
da aba Comandos toca `sfx_click` antes do `talk('/god')`, como prova de "clique em botão".

### Opção "Sons do jogo" (volume)

`client_options/data_options.lua` ganhou `enableGameSound` (padrão **ligado**) e
`gameSoundVolume` (padrão 100), com checkbox+slider em `styles/sound/audio.otui` (mesmo
padrão visual do bloco de música existente). Como `g_sounds.play()` não usa `SoundChannel`,
`NarutoSounds.play()` lê `g_settings.getBoolean('enableGameSound')`/`getNumber(
'gameSoundVolume')` a cada chamada e multiplica no `gain`. **Música (`enableMusicSound`) virou
padrão desligado** (o projeto ainda não tem trilha própria — só os SFX desta missão).

## Como adicionar um som novo

1. `tools/audio/gen_sfx.py`: escreva uma função de síntese (ou reuse uma existente) e registre
   em `build_catalog()` com `reg("sfx_novo_id", lambda: minha_func(...), gain=0.85)`.
2. Rode `.venv/bin/python tools/audio/gen_sfx.py` — gera o `.ogg`, atualiza
   `assets-src/audio/sfx_catalog.json` e `client-otc/modules/naruto_sounds/sfx_catalog.lua`.
3. Para tocar num evento novo do cliente: `modules.naruto_sounds.play('sfx_novo_id')` (ou, de
   dentro do próprio módulo, `NarutoSounds.play(...)`).
4. Para tocar num jutsu novo: só preencha o campo `sfx` em `data/jutsus/<elemento>.json` com um
   id do catálogo — `tools/export_tfs.py` já embute a chamada de `broadcastSfx` automaticamente
   em todo `onCastSpell` gerado.

## Prova por log (sem áudio real — máquina de dev/CI)

`NarutoSounds.play()` sempre loga (`NarutoSounds.debug = true`, flag no topo do módulo):

```
[SFX] tocando sfx_level_up -> naruto/sfx_level_up.ogg (gain=0.95)
[SFX] tocando sfx_menu_open -> naruto/sfx_menu_open.ogg (gain=0.70)
[SFX] tocando sfx_menu_close -> naruto/sfx_menu_close.ogg (gain=0.70)
[SFX] tocando sfx_monster_death -> naruto/sfx_monster_death.ogg (gain=0.85)
[SFX] tocando sfx_damage_taken -> naruto/sfx_damage_taken.ogg (gain=0.85)
```
(log real, `client-otc` rodando com `SL_ACCOUNT=slqa`, 05/09/2026 09:22 — nenhuma linha de
`[error]` no mesmo teste: nem `Failed to load sound source`, nem `unable to open file`, nem
`Lua exception`.) Confirma que `g_sounds.play()` foi chamado com o arquivo/gain certos e sem
erro de carregamento, para os 4 ganchos que não dependem do opcode 210 de jutsu (level up,
UI, morte de monstro, dano recebido).

## Limitações honestas

- **Cast de jutsu → som ainda não comprovado ponta a ponta no servidor ao vivo.**
  `NarutoJson.broadcastSfx` é uma função **nova** em `data/lib/naruto_json.lua`. TFS 1.4.2 só
  carrega `data/lib/*.lua` (via `dofile` em `data/lib/lib.lua`) **no boot** — nenhum `/reload`
  (conferido em `server/tfs/src/game.cpp Game::reload`: `RELOAD_TYPE_SPELLS`/`_SCRIPTS`/`_ALL`
  recarregam spells/revscripts, nunca `data/lib/`) recarrega libs. O servidor compartilhado
  já estava rodando antes desta função existir, então `/reload spells` (ou `all`) recarrega o
  **script** do jutsu (que passa a *chamar* `broadcastSfx`) mas não o `NarutoJson` **em
  memória** (que ainda não *tem* `broadcastSfx`). Provei isso ao vivo: o log do servidor
  (`Lua Script Error: [Spell Interface] .../katon_housenka.lua:27: attempt to call field
  'broadcastSfx' (a nil value)`) mostra exatamente a linha gerada sendo alcançada — a
  integração está certa, só falta o próximo restart do servidor para o `NarutoJson` em memória
  ganhar a função. Depois disso adicionei uma blindagem (`if NarutoJson.broadcastSfx then ...
  end`, a mesma técnica usada em todo o resto do código para libs opcionais) para o cast nunca
  mais falhar por causa disso — só toca o som quando a função existir.
- **Achado colateral, fora do escopo de áudio, mas registrado**: durante o mesmo teste, o
  servidor compartilhado começou a recusar **todo** login (qualquer conta) com
  `attempt to index global 'NarutoAchievements' (a nil value)` dentro do `onLogin` de
  `scripts/naruto/achievements.lua` — o mesmo tipo de problema (uma lib nova,
  `data/lib/naruto_achievements.lua`, que só carrega no boot, enquanto o *script* que a chama
  já foi recarregado por um `/reload`). Apliquei a mesma blindagem defensiva nesse arquivo
  (guardas `if not NarutoAchievements then ... end`, gerados por `tools/export_tfs.py`) e
  gerei/instalei o arquivo corrigido, mas **não consegui aplicá-lo ao vivo** (precisa de
  `/reload scripts`, que precisa de um login funcionando — nenhum login funciona agora). Task
  separada aberta para isso (`task_1e2c0ec0`); não mexi em mais nada do sistema de conquistas.
- **Sem prova auditiva real.** Esta é uma máquina de dev/CI; não há como "ouvir". A prova é por
  log (`g_sounds.play` chamado com arquivo/gain corretos, sem erro de carregamento) e pela
  reabertura de todos os 51 `.ogg` com a biblioteca `soundfile` (mesma família libvorbis do
  decoder do cliente, não literalmente o mesmo binding) confirmando mono/22050 Hz/`OggS` válido
  e pico ≤ 0 dBFS em todos.
- **`ffprobe` não estava disponível** (sem `ffmpeg` na máquina) — a validação de reabertura
  usou `soundfile` (Python) em vez disso.
- **0 screenshots deste ciclo de teste.** Os `som_*.png` do primeiro teste bem-sucedido foram
  apagados pela limpeza automática (`rm som_*.png`) antes da próxima tentativa, e o achado do
  `NarutoAchievements` (acima) passou a bloquear **todo** login logo depois — sem login não dá
  para tirar screenshot de menu/combate. A cobertura funcional ficou só nos logs (citados
  acima e no relatório final da missão).
- **Conquista, moeda, item pegar/solar**: os ganchos existem e os sons foram gerados, mas
  nenhum sistema do jogo hoje dispara "conquista desbloqueada" (não existe ainda) nem chama
  `NarutoSounds.play('sfx_coin'|'sfx_item_pickup'|'sfx_item_drop'|'sfx_door')` em nenhum evento
  real (não há um hook de "pegou item"/"abriu porta" no OTClient sem tocar em `game_*`; ver
  `docs/backlog-audio.md`).
