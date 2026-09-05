# Backlog — Áudio

Ver `docs/sistemas/audio.md` para o que já existe (catálogo, síntese, ganchos).

## Pendente — confirmar em produção
- **Verificar `NarutoJson.broadcastSfx` após o próximo restart do servidor compartilhado.**
  A função é nova em `data/lib/naruto_json.lua`; libs só carregam no boot (nenhum `/reload` os
  recarrega). Já testei a integração até onde deu (o cast alcança a linha gerada;
  `attempt to call field 'broadcastSfx' (a nil value)` no log confirma), só falta o restart
  para ela existir em memória. Depois de reiniciar: castar 1 jutsu de cada elemento e conferir
  `[SFX] tocando sfx_...` no log do cliente.
- **`task_1e2c0ec0`** (já aberta): `NarutoAchievements` nil derrubando todo login
  (`scripts/naruto/achievements.lua:onLogin`) — mesma classe de problema (lib nova sem
  restart). Bloqueava os testes de áudio no fim desta sessão; corrigido com blindagem
  defensiva, mas não aplicado ao vivo (precisa login funcionando pra rodar `/reload`).

## Música ambiente por região — FEITO (2026-09-05)
7 faixas em loop (60–85 s, OGG Vorbis, -12 dBFS) geradas por `tools/audio/gen_music.py`
em cima de um motor reutilizável (`tools/audio/synth.py`), uma por região, catalogadas em
`assets-src/audio/music_catalog.json` + espelho Lua. `client-otc/modules/naruto_sounds/
naruto_music.lua` faz poll da posição a cada 2 s e troca de faixa com crossfade
(`SoundChannel` de música). `enableMusicSound` virou **ligado por padrão**, com
`musicSoundVolume` moderado (35). Testado ao vivo (7 trocas de região logadas, zero erro
de carregamento) e validado por análise espectral (FFT/RMS/clipping) + 7 PNGs de
forma de onda/espectrograma. Ver `docs/sistemas/audio.md` § Música ambiente por região
para detalhes, paleta de cada faixa e limitações honestas (reverb é sintética, não IR
real; `musicSoundVolume` já persistido a 100 no perfil de dev compartilhado — o novo
default de 35 só pega num perfil novo).

Ideias para uma próxima rodada (não feitas aqui):
- Variar a faixa por hora do dia (dia/noite) dentro da mesma região.
- Um "sting" musical curto (2–4 notas) ao entrar num boss (Marionetista, Espadachim,
  Sócio Eterno etc.) antes de voltar pra faixa ambiente da região.
- Testar a resolução de região com movimento a pé (não só `/tp`) para confirmar que o
  poll de 2s não perde uma transição rápida perto de fronteira entre regiões.

## Sons de monstro
`data/monsters/*.json` não tem campo de som hoje (só `data/jutsus/*.json` tem `sfx`). Para
adicionar:
- Schema: `data/schemas/monster.schema.json` ganharia `sfx_attack`/`sfx_death`/`sfx_idle`
  (opcionais).
- Gancho client: o mesmo `connect(Creature, {onDeath=...})` de `naruto_sounds.lua` já dispara
  `sfx_monster_death` genérico para QUALQUER monstro — falta diferenciar por monstro (id/nome)
  se quiser sons específicos (lobo ≠ dragão). Precisaria de um mapa `monsterName -> sfxId` no
  cliente (gerado por `tools/export_tfs.py` a partir do novo campo do JSON, mesmo padrão do
  catálogo de efeitos) ou o servidor mandar o id certo via opcode 210 (mesmo mecanismo de
  `broadcastSfx`, chamado de um `onDeath`/`onSpawn` de creature script em vez de `onCastSpell`).
- "Ataque"/"idle" de monstro não tem gancho client hoje (nem `onAttack` nem grito periódico) —
  precisaria de um GlobalEvent servidor (como `NarutoAchievementPoll`) ou um creaturescript de
  `think` por monstro, o que custa performance com muitos monstros online; avaliar antes de
  implementar.

## Outras lacunas conhecidas (ver docs/sistemas/audio.md § Limitações)
- **Conquista**: gancho client pronto (`onTextMessage` casando `Achievement unlocked: ...`),
  mas não existe sistema de conquistas ligado ao chat ainda (há um `NarutoAchievements` em
  desenvolvimento em paralelo — task_1e2c0ec0 — mas ele não manda mensagem de chat, só
  storage). Quando o sistema de conquistas mandar uma mensagem/opcode de desbloqueio, plugar
  em `NarutoSounds.play('sfx_achievement')` ali.
- **Moeda / item pegar-soltar / porta**: sons gerados (`sfx_coin`, `sfx_item_pickup`,
  `sfx_item_drop`, `sfx_door`), mas nenhum evento do cliente dispara eles ainda. O Redemption
  não expõe um callback genérico de "item entrou/saiu do inventário" nem "porta abriu" sem
  tocar em `game_containers`/`game_interface` (`onAddThing` do tile ou container seria o
  candidato, mas não é um evento por-thing, é por-tile/lista inteira — precisa de mais
  investigação de qual sinal disparar sem sobrecarregar). Ficou de fora desta missão por
  tempo; ver `client-otc/modules/game_containers/` na próxima tentativa.
- **`ffprobe`**: não instalado nesta máquina (sem `ffmpeg`). A validação de reabertura dos
  `.ogg` usou a biblioteca Python `soundfile` como substituto honesto (mesma família de
  decoder libvorbis, não literalmente o binding do cliente). Se `ffmpeg`/`ffprobe` for
  instalado no futuro (`brew install ffmpeg`, fora do escopo desta sessão), revalidar com ele
  é mais fiel ao pipeline real do jogo.
