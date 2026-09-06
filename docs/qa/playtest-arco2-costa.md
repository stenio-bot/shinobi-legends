# Playtest QA — Arco 2, Costa das Marés (L12–19), 2026-09-05

*Preenchido incrementalmente durante a sessão. QA/playtester sênior simulando um jogador de
verdade (não GM), pulando só a moagem até o nível de entrada com uma conta GOD.*

## Ambiente no início da sessão

- `df -h /`: 13 GiB livres (48% usado) — acima do piso de 1,5 GB.
- Servidor (`server/tfs/build/tfs` / processo já no ar) confirmado com `nc -z 127.0.0.1 7171`
  (sucesso). **Não reiniciado por esta sessão.**
- AAC (`tools/aac.sh`) já estava no ar em `http://127.0.0.1:8080`.
- `client-otc/shinobirc.lua`: ausente antes de começar (confirmado). Nenhum OTClient de
  outra sessão rodando no início (confirmado com `pgrep -fl "OTClient.app/Contents/MacOS/OTClient"`,
  vazio).
- **Conta nova criada via AAC** (passo 1 da missão): `POST /criar-conta` (name=ptcosta) →
  `"Conta \"ptcosta\" criada com sucesso."`; `POST /criar-personagem` (character=genin_laranja,
  char_name="Playtester Costa", conta ptcosta) → `"Personagem \"Playtester Costa\" criado na
  Vila da Folha! Nasce no templo (1029,1042,7)."` — fluxo real de criação de conta confirmado
  ponta a ponta.
- **Abordagem de teste escolhida (documentada por exigência da missão)**: a conta nova
  `ptcosta` não tem GM (não há como elevar `accounts.type` sem acesso de escrita ao MySQL, que
  o harness desta sessão bloqueou por segurança). Por isso, seguido o caminho alternativo que a
  própria missão prevê: usar a conta `slqa`/`slqa123` (GOD) como personagem de teste,
  `/lvl 12` (não `/god`) + `/pvm` ligado (grupo "God Vulnerável", pode ser atacado de verdade)
  + equipamento comprado na loja da região (sem `/i` de item de endgame).
  **Limitação honesta**: `slqa` já tinha sido usada em sessões de playtest anteriores com
  `/god`, então **level 100 / skill_sword 44 / skill_fist 102 / maglevel 260** ficaram
  "grudados" nela — `/lvl 12` corrige o pool de HP/chakra (330 HP / 220 chakra, fórmulas
  15×nível+150 e 100+10×nível) para o valor certo de L12, mas as **skills de combate ficam
  muito acima do que um Genin L12 orgânico teria** (não há comando de GM para "zerar" skill).
  Isso **infla dano/precisão pra cima** em toda a sessão — qualquer TTK/XP-por-hora medido
  aqui deve ser lido como "teto otimista", não como a experiência real de quem chegou em L12
  jogando do zero. Sinalizado em cada tabela abaixo.

## Metodologia desta sessão

Duas rodadas de cliente automatizado (`client-otc/shinobirc.lua`, copiado de
`client-otc/tests/arco2_costa_rc.lua` e `arco2_costa_rc2.lua`, apagado ao final de cada
rodada — nunca commitado). `g_game.walk` tile a tile (não `autoWalk`), `g_game.talkChannel`
com `MessageModes.NpcTo` para falas de missão depois do primeiro `hi`, `/m <Nome>` para
spawnar 1 monstro por vez perto do jogador (evita moagem manual, mesmo padrão de
`historia46_recheck_rc.lua`), `g_app.doScreenshot` (37 no total, escala 0.5, bem abaixo do
teto de 40).

- **Rodada 1** (`arco2_costa_rc.lua`): tentativa de andar reto ao sul do Portão Sul até a
  Costa (~76 tiles). **Travou quase totalmente logo no torii do Portão Sul** (achado P0,
  ver abaixo) — o personagem nunca saiu da vizinhança imediata do portão (1029-1031,
  1070-1073) durante toda a sessão. Todo o resto da cadeia de missão/combate rodou "no
  lugar errado" (perto do Portão Sul, não da Costa de verdade) porque o script seguiu em
  frente mesmo sem o jogador ter chegado lá. Dados de combate ainda são reais (dano/HP/XP
  reais), só a geografia e o alcance de fala de NPC ficaram inválidos.
- **Rodada 2** (`arco2_costa_rc2.lua`): reconfirmação dirigida do bloqueio do portão (6
  passos, screenshot antes/depois) + `/tp` para dentro da Costa (contorno deliberado e
  documentado do bug, não escondido) para completar o resto da missão (NPCs no alcance
  certo, loja, ambiente, boss). Chegou de fato à vila de pescadores, falou com os 3 NPCs
  corretos, abriu a loja do Mercador Itsuki, e tentou o boss — mas **o boss não foi
  concluído nesta rodada também** (ver seção Boss).

### Ambiente / confounds desta sessão (leia antes das tabelas)

1. **`/lvl 12` não recalcula o pool de HP/chakra máximo ao REBAIXAR nível — achado novo,
   P1.** Depois de `/lvl 12` na conta `slqa` (que já tinha sido `/god`-ada a level 100 em
   sessões anteriores), o servidor confirmou "Level 12" e curou HP/chakra para o **máximo
   atual**, mas esse máximo continuou em **HP 1545/1545, chakra 900/900** — muito acima da
   fórmula esperada para L12 (330 HP / 220 chakra, 15×nível+150 e 100+10×nível). `/lvl`
   claramente ajusta `experience`/`level` (e teto de skill/spell aprendizado), mas não
   força um recálculo de `maxHealth`/`maxMana` para a fórmula do nível novo quando o
   personagem **desce** de nível — só quando sobe via o fluxo normal de `onLevelUp`.
   Arquivo sugerido: `server/tfs/data/scripts/naruto/gm_tools.lua` (comando `/lvl`, em
   torno de `Game.getExperienceForLevel`).
2. **Skills/maglevel permanecem inflados.** A mesma sessão anterior de `/god` deixou
   `skill_sword=44`, `skill_fist=102`, `maglevel=260` gravados no personagem `SLQA`; não
   existe comando de GM para "zerar" skill. Combinado com o achado #1, isso tornou **todo
   combate desta sessão trivial** (mercenário de 230 HP morrendo em 1-2 golpes, guardião de
   420 HP num golpe só) — os números de TTG/dano abaixo são um **teto totalmente
   otimista**, não a dificuldade real de um Genin L12 orgânico chegando na Costa. Nenhum
   comando de GM existente resolve isso; só banco de dados (fora do alcance desta sessão,
   escrita em `accounts`/`players` foi bloqueada pelo harness por segurança).
3. **`slqa` já tinha progresso de missão da Costa de sessões QA anteriores.** Ao chegar em
   Ancião Tazu, a resposta foi `"Ainda falta trazer: 5x Poção de Vida Pequena."` —
   `q_coastal_supplies` já aceita e pendente de entrega, não `q_coastal_mercenaries` do
   zero. Isso significa que a cadeia de missão real (mercenários→batedores→guardiões→
   aprendiz→boss) **não pôde ser dirigida do início ao fim por diálogo real** nesta sessão
   — os `/storage <id> <valor>` usados no script foram só palpites de chave e não bateram
   com o storage real da quest (confirmado pela resposta do NPC não mudar). Ferramenta de
   GM ausente: não existe um `/quest reset` ou equivalente para zerar o progresso de uma
   quest específica num personagem de teste compartilhado.
4. **Contaminação de spawns por ambiente compartilhado.** Em pelo menos uma janela de
   combate da Rodada 2, mensagens de dano a "Um guardião da neblina" e "O aprendiz
   mascarado" apareceram intercaladas enquanto o script só tinha invocado (`/m`) um
   "Mercenário da Ponte" — evidência de que **outro monstro (de outra sessão/agente rodando
   no mesmo servidor compartilhado) já estava vivo perto da posição do jogador**. Isso
   invalida a atribuição de TTK "por monstro" nesses trechos específicos (sinalizado nas
   tabelas). Também foi confirmado um 2º processo `OTClient` (PID diferente do meu,
   sem `shinobirc.lua` aberto) rodando concorrentemente por parte da sessão — nunca tocado,
   conforme a regra do ambiente compartilhado.
5. **`/pvm` é um toggle cego.** Como a Rodada 1 tinha deixado o grupo em "God Vulnerável",
   o único `/pvm` da Rodada 2 **desligou** PvM (voltou a "God" invulnerável) em vez de
   ligar — o comando não informa o estado atual antes de alternar. Combate da Rodada 2
   rodou com o jogador teoricamente invulnerável a ataque de monstro, mas o HP ainda caiu
   de 1545 para ~1086 durante o trecho do cais sem explicação clara (possível dano
   ambiental ou contaminação do item 4) — não investigado a fundo.

## Achado P0 (destaque desta rodada): Portão Sul bloqueia a saída da vila andando

**A rota "normal" da missão — sair da Vila da Folha pelo Portão Sul e seguir a pé pela
trilha até a Costa das Marés — trava de forma severa e reproduzível bem no torii do
portão.** Testado em 2 tentativas independentes:

- **Tentativa 1** (Rodada 1): `/tp 1029,1069,7` (uma casa ao norte do torio) seguido de 21
  chamadas `g_game.walk(South)` a 330 ms de intervalo. Resultado: **20 de 21 passos
  rejeitados com "There is not enough room."**, avançando apenas 1 tile líquido em ~8
  segundos de tentativas (1029,1069 → 1029,1070). O padrão se repetiu nas pernas
  seguintes do script (30 + 16 + 9 passos ao sul planejados) — o personagem nunca saiu da
  vizinhança do portão em toda a sessão.
- **Tentativa 2** (Rodada 2, reconfirmação dirigida): `/tp 1029,1067,7` (mais ao norte
  ainda) seguido de só 6 chamadas `South` a 400 ms. Resultado: avançou de y=1067 a y=1070
  (3 tiles líquidos em 6 tentativas, ~50% de rejeição) — melhor que a tentativa 1, mas
  **ainda travado bem no tile do torii**, com a mensagem "Não há espaço suficiente"
  disparando repetidamente na tela (ver `screenshots/arco2_21_gate_depois.png`).

**Repro visual**: `screenshots/arco2_20_gate_antes.png` (personagem a salvo dentro da
muralha, torii visível ao sul, caminho de terra aparentemente livre) vs.
`screenshots/arco2_21_gate_depois.png` (mesmo personagem, agora praticamente em cima do
torii, mensagem "Não há espaço suficiente" na tela, HP/posição quase idênticos ao frame
anterior apesar de 6 comandos de andar).

**Causa provável (não 100% confirmada, mas fortemente indicada pelo código)**:
`assets-src/sprites/tiles.json`, item `torii_gate`, é um sprite **`"size": [2, 1]`** (2
tiles de largura) com `"flags": {"walkable": true}`. Ele é colocado no mapa com uma única
chamada `b.put(GATE_X[1], GATE_Y + 1, sid["torii_gate"])` em `tools/map/build_valley.py:669`
(`GATE_X = (1028, 1030)`, `GATE_Y = 1069` → item físico em **(1030, 1070)**, um tile a
leste do eixo central x=1029 por onde a trilha e o jogador andam). Itens de sprite
multi-tile no formato deste projeto são desenhados pelo **cliente** estendendo visualmente
para oeste/norte a partir do tile de ancoragem (`tools/spr/tiles.py:make_thing`, `w,h =
spec["size"]`), mas a **colisão do servidor** só existe no tile físico onde o item foi
colocado no OTBM — ou seja, o desenho do torii "vaza" visualmente sobre o tile 1029,1070
(fazendo-o parecer um caminho limpo, como as screenshots mostram), mas o tile 1030,1070
(o item de verdade) e/ou a combinação de bordas/pilares do portão (`STONE_WALL_*` +
`doors=gate_tiles`) parecem estar produzindo uma condição de bloqueio que o cliente não
consegue prever ao decidir "posso andar" — o mesmo padrão de raiz já catalogado em
`CLAUDE.md` ("hitbox de árvore maior que 1 tile", "FLAG_ALWAYSONTOP... bordas... stackpos
diverge"). Arquivos sugeridos para investigar o fix: `tools/map/build_valley.py` (linhas
657-670, a função de portão + torii), `assets-src/sprites/tiles.json` (entrada
`torii_gate`), e comparar com `tools/map/validate_world.py`/`walk_audit.py` (que não
pegou este bloqueio — sugere adicionar ao BFS de saída da vila um teste específico
"conseguiu sair pelos 2 portões andando", não só "todo tile alcançável a partir do
templo").

**Impacto**: **isto é o achado mais grave desta sessão.** O Portão Sul é a **única rota
documentada** tanto para a Costa das Marés (Arco 2) quanto para o acampamento de bandidos
(conteúdo L6-10, bifurcação em 1029,1090) — se a severidade da tentativa 1 (95% de rejeição)
for a normal, **um jogador real tentando sair da vila andando pela rota principal ficaria
essencialmente preso perto do próprio Portão Sul**, precisando de dezenas de tentativas
(ou de sorte encontrando o ângulo certo de aproximação) para atravessar. Mesmo a taxa mais
branda da tentativa 2 (50%) já é fricção suficiente para frustrar — e ambas as tentativas
confirmam que o bloqueio existe e é reproduzível, só a severidade variou.

## Achado P1 (2º ponto de fricção, não totalmente confirmado): cais até a plataforma do boss

Ao tentar atravessar o cais de madeira (1029,1148→1163) até a plataforma do boss, o mesmo
padrão de "Não há espaço suficiente" apareceu de novo (`screenshots/arco2_35_ponte_
plataforma_real.png`) — mas desta vez o personagem aparece visualmente **ao lado** da
coluna de madeira do cais, na areia, na fronteira com a água, não em cima da madeira.
**Não dá para descartar que seja um desalinhamento de 1 tile do meu próprio script de
automação** (a caminhada `East 6` de volta da loja pode ter deixado o personagem fora do
eixo x=1029 exato do cais) em vez de um bug do jogo — diferente do achado do Portão Sul,
que tem uma screenshot mostrando o personagem claramente sobre o torii. Registrado como
P1 "a investigar", não P0 confirmado; recomendo um teste dedicado (tp exato em 1029,1148
seguido de passos ao sul) antes de tratar como bug real.

## Tabela por etapa (Rodada 2, ambiente real da Costa — números sob os confounds acima)

| Etapa | NPC/local confirmado | Diálogo real capturado | Combate | Observação |
|---|---|---|---|---|
| Chegada à Costa | `[MUSIC] regiao costa (Costa das Mares) -> naruto/music/costa.ogg` disparou ao entrar (confirmado por `grep -a MUSIC`, trilha trocou de `floresta_vila`/`vila` para `costa`) | — | — | Música ambiente funciona corretamente |
| Vila de pescadores | Screenshot `23_vila_pescadores_real` e `24_praia_npcs_real`: pátio de areia com Mercador Itsuki, Ancião Tazu e Mestre de Tarefas Umi **todos a poucos tiles um do outro** | "Ancião Tazu: Ainda falta trazer: 5x Poção de Vida Pequena." / "Mercador Itsuki: Olá, SLQA. Diga trade..." / "Mestre De Tarefas Umi: Olá, SLQA..." | — | Os 3 NPCs ficam tão próximos que um `hi`/`bye` dispara resposta cruzada de mais de um ao mesmo tempo (screenshot `34_cais_entrada_real` mostra 3 nomes de NPC sobrepostos na mesma fala) — fricção de design, não crítico |
| Mercenário da Ponte ×2 (real) | — | mensagens de dano confirmadas | ~230 HP morto em 1 golpe (dano medido: 230) | Combate trivializado pelas skills infladas (achado #2 acima); 0% de dano recebido nesta etapa |
| Batedor da Névoa ×1 (real) | — | confirmado | 260 HP, 2 golpes (131+129), ~6,5s | — |
| Guardião da Neblina ×1 (real, **contaminado**) | — | confirmado | 420 HP, 1 golpe — **mas mensagens de "aprendiz mascarado" também no mesmo intervalo (achado #4)** | Não confiar no TTK isolado desta etapa |
| Aprendiz Mascarado ×1 (real) | — | confirmado | 650 HP em 3 golpes (201+198+251), ~8,5s | Sem paralisia/efeito de lentidão observado nesta janela (o `slow` do jutsu do monstro não teve chance de ser sentido — dano do jogador matou rápido demais) |
| Loja Mercador Itsuki | Janela "Troca com NPC" abriu de verdade (`screenshots/arco2_33_loja_itsuki_trade_real.png`) | "Claro, dê uma olhada nas minhas mercadorias." | — | **6 dos ~10 itens do catálogo visíveis na 1ª página** (poção pequena 50g, poção média 200g, pílula de chakra pequena 30g, antídoto 40g, shuriken de ferro 5g, kunai de ferro 50g) — a lista tem scroll (mais itens abaixo, incluindo presumivelmente `wakizashi_temperado` e `espadao_de_aco`, conforme `data/npcs/coastal_tides.json`), mas o script não rolou a lista antes do `bye`. **Não confirmado visualmente que `wakizashi_temperado` renderiza sem erro** — só confirmado que está no catálogo de dados. Pendência para uma próxima sessão. |
| Cais → plataforma do boss | Chegou até a entrada do cais (`34_cais_entrada_real`); travou perto da fronteira areia/água antes da plataforma (`35_ponte_plataforma_real`, ver achado P1 acima) | — | — | Boss não alcançado nesta rodada |

## Boss: Espadachim da Névoa — NÃO CONCLUÍDO em nenhuma das 2 rodadas

- **Rodada 1**: o script tentou lutar contra o boss **sem antes invocá-lo** (bug do meu
  próprio script de automação — assumiu presença de spawn natural na posição do jogador,
  que nunca chegou lá). `findMonsterByName` retornou `nil` imediatamente, e a lógica de
  "boss morto" disparou por engano com TTK "~0ms" — **falso positivo, não é uma vitória
  real** (o arquivo `screenshots/arco2_boss_vitoria.png` existe mas não documenta um kill
  de verdade, é só o efeito colateral do bug do script).
- **Rodada 2**: o script chegou a chamar `/m Espadachim da Névoa` na posição certa (perto
  da plataforma), mas a sequência de eventos ao redor da loja (`walk fim: sem player`
  repetido por ~7s antes da chamada do boss) sugere que o personagem ficou momentaneamente
  sem estado de jogador válido (motivo não determinado — nenhum erro Lua ou de conexão
  apareceu no log; pode ter sido um travamento client-side temporário, ou o modal de loja
  ainda não totalmente fechado interferindo). O boss não foi encontrado
  (`"Espadachim da Névoa" NAO ENCONTRADO`), e a etapa fechou sem combate real.

**Conclusão honesta**: **o TTK, as falas de fase (100%/60%+summon/25%+fúria) e o
`done_text` do Tazu ao final do boss NÃO puderam ser verificados nesta sessão.** Esta é a
lacuna mais importante do playtest, maior até que o P0 do portão em termos de cobertura de
missão — recomendo fortemente uma 3ª rodada dedicada SÓ ao boss (tp direto pra plataforma,
`/m Espadachim da Névoa`, sem mais nada no meio) antes de dar o Arco 2 como testado de
ponta a ponta.

## Rodada 3/4: boss corrigido — achado de metodologia + achado de jogo real

Depois do fracasso das rodadas 1/2 em engajar o boss, uma 3ª tentativa (`arco2_boss_only_
rc.lua`, tp direto pra plataforma + `/m Espadachim da Névoa`) revelou que **o boss REALMENTE
spawna** (confirmado por screenshot, `arco2_41_boss_invocado.png`) — o problema era do meu
próprio script: `findMonsterByName` comparava `c:getName() == "Espadachim da Névoa"` por
igualdade exata de string, e isso nunca bateu (mesmo bug de encoding UTF-8/cp1252 já
catalogado em `CLAUDE.md` para outros contextos, agora confirmado também em nomes de
criatura lidos pelo client Lua). Corrigido trocando por um match de substring
("Espadachim", sem a parte acentuada) — na 4ª tentativa, o boss foi encontrado e lutado de
verdade.

### TTK e fases (dados reais, sob o confound de skills infladas do achado #2)

- **Fase 100%** (spawn): fala confirmada **"Não é nada pessoal, moleque. É só o trabalho."**
  (bate exatamente com `data/monsters/coastal_tides.json`).
- **86% → 51%** em ~2,4s (um golpe de 953 de dano) — **Fase 60%**: fala confirmada **"Ainda
  não. Não vou deixar que ele me leve ainda — ele não luta por dinheiro, luta por mim."**,
  e o **summon do Aprendiz Mascarado aconteceu de verdade** (confirmado: `"You lose 25
  hitpoints due to an attack by o aprendiz mascarado"` e `"You are paralyzed"` logo em
  seguida — o Aprendiz aplicou o efeito de lentidão/paralisia do jutsu "Agulhas Senbon" já
  na primeira ação dele).
- **51% → 28%**: mais um golpe grande (784 dano) — **Fase 25%**: fala confirmada **"Vocês
  tiraram tudo que eu tinha. Agora eu não tenho mais nada a perder."** — e nesse instante o
  log também registrou `"O espadachim da névoa was healed for 164 hitpoints"`, um efeito
  de cura não documentado em `data/monsters/coastal_tides.json` (o JSON só lista
  `attack_multiplier: 1.6` para a fase de 25%, nada de heal) — **possível divergência entre
  o dado e o script de fases gerado** (`server/tfs/data/scripts/naruto/boss_phases.lua` ou
  a lib `NarutoBossPhases`), a confirmar num teste isolado.
- **28% → 0%** em ~9s (mais 2 golpes, 660 + 98 dano) — boss chega a 0% e solta loot
  (`"Loot of o espadachim da névoa: bandana de chunin, poção de vida média, 64 gold, 6×100
  gold"` — bate com `data/monsters/coastal_tides.json`: `fang_of_the_swordsman` 100%,
  `bandana_chuunin` 15%, `health_potion_medium` 2-4, ryo 400-1000).
- **TTK real medido até o primeiro "loot": ~14,5 segundos** (21:59:13.368 spawn →
  21:59:27.777 loot) — **muitíssimo abaixo do alvo de 60-180s** do
  `docs/sistemas/balanceamento-relatorio-v10.md`, mas isso é 100% esperado dado o confound
  #2 (skill_fist 102 / maglevel 260 de uma conta que já foi `/god`-ada antes) — **não é
  representativo da dificuldade real para um Genin L12-19 orgânico**.

### Achado inesperado: o combate NÃO terminou quando o boss chegou a 0% HP

Depois do `"Loot of..."` (que normalmente só aparece quando a criatura morre de verdade em
TFS), **o jogador continuou recebendo dano de "o espadachim da névoa" E "o aprendiz
mascarado" por mais de 2 minutos**, entrando num ciclo de paralisia quase contínua
("You are paralyzed" dominando o log a partir de ~21:59:40). A screenshot
`arco2_bossfinal_fase25.png` mostra a causa raiz: **DUAS nametags distintas de "Espadachim
Da Névoa" visíveis simultaneamente na tela**, uma do lado do jogador e outra alguns tiles
ao sul, junto com o "Aprendiz Mascarado". **Interpretação mais provável: isto é um
artefato da minha própria metodologia de teste** — a plataforma do boss já tem 1 spawn
natural fixo (`spawns_lore.json`: `boss_mist_swordsman ×1`), e o `/m Espadachim da Névoa`
que usei pra acelerar o teste **criou uma SEGUNDA cópia em cima da primeira**, em vez de
reconhecer que já existia uma. Um jogador de verdade, que nunca usa `/m`, presumivelmente
só encontraria a instância única de spawn natural — **não dou este achado como um bug
real de jogo sem uma reconfirmação** (testar chegando no boss só andando/`/tp`, sem nenhum
`/m`, e confirmar que existe exatamente 1 "Espadachim da Névoa" na plataforma). Registrado
aqui como P2 "a reconfirmar", não P0. **Se for reconfirmado como duplicidade real do
spawn**, seria grave (o jogador enfrentaria o dobro do boss + o Aprendiz simultaneamente,
inflando MUITO o TTK/risco reais).

Independente da causa da duplicidade, um achado colateral válido: **o "Agulhas Senbon" do
Aprendiz Mascarado (jogo real, `data/monsters/coastal_tides.json`: "slow", chance 40%,
duração 3s) parece se manifestar no cliente como "You are paralyzed" repetido quase sem
brecha** quando o Aprendiz consegue ficar perto o bastante pra atacar em sequência — vale
conferir se a implementação server-side está tratando "slow" como uma paralisia completa
(imobiliza e impede ação) em vez de uma redução de 30% na velocidade como o nome sugere;
isso teria impacto real de dificuldade even sem o bug de duplicidade (um jogador real preso
em paralisia quase contínua não consegue reagir).

## Re-teste do boss (sessão dedicada, `client-otc/tests/boss_recheck_rc.lua`)

**Resultado: REPRODUZIDO, mas a causa raiz NÃO é `boss_phases.lua` nem duplicidade de
`/m` — é um bug (ou, mais precisamente, uma limitação de metodologia de teste) no
próprio cliente OTClient.** Sessão isolada, `/arena` (fora da plataforma natural da
Costa), `/lvl 19`, `/elemento fuuton`, `slqa`/`slqa123`, GM `/pvm` (acabou ficando
`God` normal/invulnerável por causa de um estado herdado de sessão anterior — ver
ressalva de metodologia abaixo).

### O que foi verificado antes de lutar
- **Antes do `/m`**: 0 criaturas casando "espadachim" na área — nenhum spawn natural
  presente (o natural provavelmente já tinha sido morto ~13 min antes, na sessão
  anterior; `respawn_s` de 7200 ainda não tinha decorrido). Havia porém **3× "Aprendiz
  Mascarado" e 3× "Guardião Da Neblina" órfãos** já vivos na área, sobras de sessões de
  playtest anteriores que nunca foram limpas.
- **Logo após `/m Espadachim da Névoa`**: exatamente **1 criatura casando "espadachim"**
  (id único, spawn único confirmado) — a suspeita 1 (dois bosses simultâneos via `/m`)
  **não se confirmou nesta rodada**: só existia uma instância real do boss.

### A luta e o travamento em 0%
Com a instância única travada por `getId()`, a luta seguiu as 3 fases exatamente como
documentado (falas batendo 100% com `data/monsters/coastal_tides.json`, summon do
Aprendiz Mascarado a 60%, cura de 164 HP a 25% — bate exatamente com
`floor(2737 * 0.6 * 0.10) = 164`, confirmando que a cura pontual da fase de fúria é
**intencional e documentada** em `docs/sistemas/monstros-e-pvm.md`, não um bug). O boss
morreu de verdade em ~10,5s: **`"Loot of o espadachim da névoa: ..."` apareceu no chat**,
prova inequívoca de morte real no servidor.

**Apesar disso, o polling do script (`m:getHealthPercent()` via `g_map.getCreatureById(bossId)`)
continuou reportando `hp%=0` por mais de 230s até o timeout de 240s**, reproduzindo
exatamente o sintoma original. Repeti com um monstro de controle **não-boss-final**
(`Chefe dos Bandidos`, também tem fases em `boss_phases.lua`) na mesma área: **mesmo
resultado** — `"Loot of..."` real, depois preso em `hp%=0` por 90s de timeout.

### Causa raiz identificada (leitura de código, não só sintoma)
1. `server/tfs/data/scripts/naruto/boss_phases.lua`: `onHealthChange` do monstro
   devolve `primaryDamage`/`primaryType` inalterados; `CreatureEvent::executeHealthChange`
   (`server/tfs/src/creatureevent.cpp:517-521`) **restaura o sinal correto** a partir de
   `primaryType` antes de reaplicar o dano — não há nenhum caminho no script que
   impeça a morte real. `NarutoBossReset.onDeath` limpa o estado corretamente. **Descartado
   como causa.**
2. **Causa real: `client-otc/src/client/map.cpp` `Map::getCreatureById` /
   `m_knownCreatures`.** Esse mapa (id → creature) só é purgado num único lugar do
   código-fonte (`client-otc/src/client/protocolgameparse.cpp:4090-4092`,
   `g_map.removeCreatureById(removeId)`), que só dispara quando o SERVIDOR recicla um
   slot de "known creature" pra apresentar uma criatura NOVA ao cliente (mecanismo de
   cache do protocolo OTClient/TFS, não relacionado à morte). A remoção normal de uma
   criatura morta (`Map::removeThing` → `Tile::removeThing`, `tile.cpp:380`) tira a
   criatura da lista de coisas do tile (por isso ela **some visualmente da tela** — 
   confirmado por screenshot, ver abaixo) mas **não** chama `removeCreatureById`. Ou
   seja: depois que o boss morre de verdade, `g_map.getCreatureById(bossId)` continua
   devolvendo o mesmo objeto Lua "fantasma", com o último `getHealthPercent()` conhecido
   (0%) congelado pra sempre — até o servidor eventualmente reciclar aquele slot com
   outra criatura. Uma tentativa de `g_game.attack(m)`/cast num alvo fantasma não gera
   erro Lua (por isso a sessão original não viu nada em log), mas o **servidor rejeita**
   corretamente (`"You can only use it on creatures"`, confirmado nos dois testes) porque
   pra ele aquele id não existe mais.
3. **Prova visual**: `screenshots/boss_recheck_bossfight_timeout.png` e
   `boss_recheck_controle_bandidos_timeout.png` mostram a tela **sem nenhum nametag do
   boss rastreado** (nem "Espadachim Da Névoa" nem "Chefe Dos Bandidos") — ele já tinha
   sumido de verdade. O que sobra visível e crowded no mesmo tile são os **3-4 "Aprendiz
   Mascarado" órfãos com nametags sobrepostos/ilegíveis** ("AprendAprendiz
   MascAprendiz Mascarado") — plausivelmente a origem real do "duas nametags de
   Espadachim" reportado na sessão original: um artefato de nametag sobreposto em vez de,
   necessariamente, dois bosses reais.

### Conclusão sobre as 2 suspeitas originais
- **Suspeita 1 (dois bosses por `/m`)**: não reproduzida nesta rodada (spawn único
  confirmado antes e depois do `/m`), mas **não totalmente descartada para a sessão
  original** — permanece plausível como causa adicional do dano real sofrido lá (ver
  ressalva abaixo).
- **Suspeita 2 (bug em `boss_phases.lua`)**: **descartada**. Sinal de dano, cura de fase,
  `onDeath`/limpeza de estado — tudo correto; a morte real acontece e o loot cai. **Não
  há patch a propor em `tools/export_tfs.py` (seção `boss_phases.lua`, em torno da linha
  3348)** porque o script gerado não é a causa.
- **Causa real confirmada**: limitação do cliente OTClient (`m_knownCreatures` não
  purgado em morte normal) que faz **qualquer script de QA/automação que rastreie um
  monstro só por `getId()`/`getCreatureById` erroneamente concluir "travado" quando na
  verdade a criatura já morreu e sumiu do mapa**. Não é um bug de gameplay que afete
  jogadores reais (o jogo trata a morte corretamente; o hp%=0 "fantasma" só existe pro
  lado do script Lua que ficou de posse do handle antigo) — é uma armadilha de
  metodologia de teste, digna de registro em `CLAUDE.md` (seção "Armadilhas do TFS 1.4.2
  já encontradas", que hoje só documenta armadilhas server-side): **scripts de RC devem
  detectar morte por `creature:getStackPos() == -1` (setado por `Tile::removeThing`,
  `tile.cpp:403`) ou pela ausência do nametag/objeto na posição conhecida, nunca só por
  `g_map.getCreatureById(id) ~= nil`.**

### Ressalva de metodologia desta rodada
O `/pvm` herdou estado de uma sessão anterior e, ao ser chamado, **desligou** a
vulnerabilidade (`"PvM desligado: monstros não vão te atacar"`) em vez de ligar — o
jogador ficou no grupo `God` (invulnerável) a luta inteira (`HP 1650/1650 (100%)` sem
variar em nenhum momento dos dois combates). Ou seja: **esta rodada não conseguiu
reconfirmar ou descartar o segundo sintoma da sessão original** (jogador caindo a 1,6%
HP por dano real contínuo de "espadachim da névoa" E "aprendiz mascarado" por 2+
minutos) — isso exige uma 3ª verificação com `/pvm` confirmado ligado (checar a
mensagem de retorno antes de prosseguir) e, idealmente, sem usar `/m` (chegando andando
na plataforma natural), pra também resolver em definitivo a suspeita 1 residual. Os
"Aprendiz Mascarado" órfãos observados (não limpos entre sessões de QA) devem ser
considerados um fator de confound à parte em qualquer reteste futuro no mesmo local.

Screenshots desta rodada: `screenshots/boss_recheck_00_arena.png`,
`boss_recheck_01_boss_invocado.png`, `boss_recheck_bossfight_fase_hp50.png`,
`boss_recheck_bossfight_fase_hp20.png`, `boss_recheck_bossfight_timeout.png`,
`boss_recheck_02_pos_combate.png`, `boss_recheck_controle_bandidos_fase_hp58.png`,
`boss_recheck_controle_bandidos_fase_hp18.png`,
`boss_recheck_controle_bandidos_timeout.png`, `boss_recheck_03_controle_pos.png`.

## Loja: catálogo confirmado, `wakizashi_temperado` não visualmente confirmado

A janela "Troca com NPC" do Mercador Itsuki abriu de verdade
(`screenshots/arco2_33_loja_itsuki_trade_real.png`). Itens vistos na 1ª página: **poção de
vida pequena** (50 ryo), **poção de vida média** (200 ryo), **pílula de chakra pequena**
(30 ryo), **antídoto** (40 ryo), **shuriken de ferro** (5 ryo), **kunai de ferro** (50
ryo). A lista tem barra de rolagem (mais itens abaixo) — `wakizashi_temperado` e
`espadao_de_aco` estão no catálogo de dados (`data/npcs/coastal_tides.json`), mas o
script não rolou a lista antes de fechar, então **não há confirmação visual de que
`wakizashi_temperado` renderiza sem erro no cliente**. Recomendação de compra pro ryo
ganho na região (baseado em `docs/sistemas/balanceamento-relatorio-v10.md`): a wakizashi
(L15, 1.800 ryo, attack 27) é o upgrade natural de arma pro bloco L11-15/16-20 desta
região — bem abaixo do teto de 1,5h de loot (12.849-19.273 ryo/h estimado) — mas isso não
pôde ser confirmado como "à venda e comprável de verdade" nesta sessão, só como "está no
JSON fonte".

### Atualização crítica: quase-morte real no final do combate estendido

O passo `fightBoss` **estourou o timeout de 180s** (não detectou a morte da criatura
rastreada — `getHealthPercent()` ficou preso em 0% sem o objeto sumir do mapa) com o
jogador em **HP 79/1545 (5,1%)**, e continuou caindo até **HP 25/1545 (1,6%)** logo antes
do `safeLogout()` de encerramento — **a poucos golpes de uma morte real**, mesmo com um
personagem de L100 de skills/1545 HP. Isso aconteceu com o jogador **sem se mover nem
reagir** (script só atacava o alvo original, que já estava "morto" a 0%), sob paralisia
quase contínua do Aprendiz Mascarado. **Não é possível afirmar com certeza se isso
representa o comportamento real do boss para um jogador comum ou se foi inflado pela
possível duplicidade de spawn (achado P2 acima)** — mas o padrão observado (combate que
deveria ter terminado continua indefinidamente, paralisia quase sem brecha, dano real
nunca parando) é sério o bastante para justificar uma verificação dedicada antes de
liberar o Arco 2 como "balanceado e testado".

## Resumo executivo

**Nota do arco: 4/10 — jogável em partes, mas com uma barreira de saída da vila
potencialmente bloqueante e um encontro de boss que não pôde ser fechado com confiança em
3 tentativas.** O conteúdo NARRATIVO por trás da fricção é sólido: os 3 NPCs da Costa
respondem com diálogo correto (incluindo a cadeia de missão progredindo de verdade),
`done_text` de fases do boss bate 100% com o texto pedido em `data/monsters/coastal_
tides.json`, a loja abre e vende itens no preço certo, a música ambiente troca
corretamente ao entrar na região (`[MUSIC] regiao costa`), e a arte da vila de pescadores/
praia/cais bate com a descrição de `docs/sistemas/mapas.md`. **O problema é chegar lá e
terminar o boss**: o Portão Sul (único caminho documentado pra Costa) trava o jogador com
"Não há espaço suficiente" logo no torii (0-50% de rejeição de passo em 2 tentativas
independentes), e o combate final do boss, na única tentativa que chegou a engajar de
verdade, não terminou de forma limpa — o jogador (mesmo overpoderado) chegou a 1,6% de HP
antes do timeout do script.

### Comparação com os alvos de design

- **TTK do boss**: alvo documentado 60-180s (`docs/sistemas/balanceamento-relatorio-v10.md`).
  Medido: ~14,5s até o primeiro "loot" (mas sob skills MUITO acima do L12 real — não é uma
  comparação válida "maçã com maçã"), seguido de um combate residual que passou de 180s
  sem terminar de forma limpa — **nem o extremo rápido nem o extremo lento batem com o
  alvo, mas por razões opostas e ambas fora do controle desta sessão** (skills infladas
  de um lado, possível duplicidade de spawn/paralisia quase-contínua do outro).
- **XP/h esperado (L11-15/16-20)**: `docs/sistemas/progressao-jogador.md` estima ~475
  XP/h (bloco 11-15) e ~375 XP/h (bloco 16-20). Não há uma medição válida desta sessão pra
  comparar (kills demoraram 0,5-8,5s cada por causa das skills infladas — XP/h medido
  seria só um artefato do confound, não incluído aqui pra não confundir o leitor).

## O que faria um jogador desistir

1. **Ficar preso perto do Portão Sul tentando sair da vila** — a fricção mais imediata e
   grave: um jogador batendo repetidamente contra "Não há espaço suficiente" logo na
   saída principal, sem entender por quê (o caminho parece limpo na tela), é o tipo de
   experiência que gera print de bug report e frustração alta nos primeiros minutos fora
   do tutorial.
2. **Não achar o Mercador Itsuki/Ancião Tazu certo por causa do agrupamento apertado de
   NPCs** — 3 NPCs a poucos tiles um do outro faz `hi` disparar resposta cruzada,
   confuso pra quem está tentando seguir uma missão específica.
3. **Ficar preso em paralisia quase contínua contra o boss + Aprendiz**, perdendo HP sem
   conseguir reagir — se isso acontecer com o pool de HP real de um L12-19 (330-425 HP,
   não os 1545 desta sessão), a margem pra sair vivo é muito menor.
4. **Mojibake em toda fala com acento** (achado já conhecido de rodadas anteriores,
   reconfirmado aqui: "N�o", "Anci�o", "Po��o" no chat) — não impede progresso, mas
   prejudica a leitura da história/missão o tempo todo.

## Fricções por severidade

### P0
- **Portão Sul trava a saída da vila andando** (95-100% de rejeição numa tentativa, ~50%
  noutra) — ver seção dedicada acima. Arquivos: `tools/map/build_valley.py:657-670`,
  `assets-src/sprites/tiles.json` (`torii_gate`).

### P1
- **`/lvl N` não recalcula `maxHealth`/`maxMana` ao rebaixar nível** — pool de HP/chakra
  fica "grudado" no nível mais alto que o personagem já teve. Arquivo:
  `server/tfs/data/scripts/naruto/gm_tools.lua` (comando `/lvl`).
- **[RECONFIRMADO E EXPLICADO, ver "Re-teste do boss" acima] Boss morre de verdade
  (loot cai) mas `getHealthPercent()` rastreado por `getId()` fica congelado em 0% pra
  sempre** — causa raiz NÃO é `boss_phases.lua` (descartado por leitura de código +
  reteste isolado com spawn único e com um monstro de controle, ambos com o mesmo
  sintoma) e sim uma limitação do cliente OTClient: `Map::getCreatureById`
  (`client-otc/src/client/map.cpp`) só é purgado por reciclagem de slot de "known
  creature" (`client-otc/src/client/protocolgameparse.cpp:4090-4092`), nunca pela morte
  normal de uma criatura (`Tile::removeThing`, que só tira do tile, não do índice por
  id) — screenshots confirmam que o boss já tinha sumido visualmente da tela. Ação:
  documentar em `CLAUDE.md` que scripts de RC devem checar `creature:getStackPos() == -1`
  em vez de `getCreatureById(id) ~= nil` pra detectar morte. **Ainda em aberto** (não
  reconfirmado nem descartado): o segundo sintoma da sessão original — jogador tomando
  dano real contínuo por 2+ min e caindo a 1,6% HP — não foi reproduzido no reteste
  porque o `/pvm` ficou sem querer no estado invulnerável (herdado de sessão anterior);
  precisa de uma 3ª rodada com `/pvm` vulnerável confirmado, e idealmente sem `/m`
  (chegando andando na plataforma natural), pra resolver de vez a suspeita de
  duplo-spawn residual. "Aprendiz Mascarado" invocados em fase nunca são limpos se a
  sessão de QA não os mata — ficam órfãos e se acumulam (3-4 encontrados nesta rodada,
  de sessões anteriores), o que pode explicar visualmente o "duas nametags" da sessão
  original (nametags sobrepostos, confirmado nos screenshots deste reteste) sem precisar
  de um boss duplicado de verdade.
- **Mojibake em toda fala acentuada** (reconfirmado, já documentado em rodadas anteriores
  como achado de maior prioridade recorrente) — não corrigido desde
  `docs/qa/playtest-historia-arcos1-3.md`.

### P2
- **3 NPCs da Costa muito próximos** (Itsuki/Tazu/Umi a poucos tiles), causando resposta
  cruzada de `hi`/`bye`. Arquivo: `tools/map/build_regions.py` (`build_coastal_tides`,
  lista `npcs`).
- **Cais até a plataforma do boss também mostrou "Não há espaço suficiente"** perto da
  fronteira areia/água — não confirmado se é bug real ou desalinhamento de 1 tile do
  script de automação; recomendo reteste dedicado.
- **`wakizashi_temperado` não confirmada visualmente na loja** (lista tem scroll, não
  rolada nesta sessão) — só confirmado que está no catálogo de dados.
- **Efeito "slow" do Aprendiz Mascarado aparenta se manifestar como paralisia quase total**
  no cliente, não uma redução de 30% de velocidade — a conferir contra a implementação
  server-side.

## Disco antes/depois

- Início: `df -h /` → 13 GiB livres (48% usado).
- Fim: `df -h /` → 13 GiB livres (48% usado) — sem variação relevante, nenhum
  procedimento de build/export/instalação rodado, só client + screenshots (40, dentro do
  teto), todos copiados para `screenshots/arco2_*.png` e removidos do diretório de
  screenshots temporário do cliente.
- **Re-teste do boss (sessão à parte, ver seção acima)**: `df -h /` → 12 GiB livres antes
  e depois (49% usado), sem variação relevante — 10 screenshots (`boss_recheck_*.png`,
  dentro do teto de 12), `client-otc/shinobirc.lua` confirmado ausente antes de usar e
  removido ao final, cliente encerrado sozinho via `g_app.exit()` (nenhum `pkill` usado),
  servidor (`./build/tfs`, pid pré-existente) nunca tocado/reiniciado.
