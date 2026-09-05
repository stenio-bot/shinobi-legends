# Playtest QA — nível 1 a 20, rodada 4 (2026-09-05)

Sessão de playtest de um jogador comum, conta `playtester4` (personagem **Playtester
Quatro**, Vila da Folha, criada pelo AAC — `POST /criar-conta` + `POST /criar-personagem`,
sem `god`/GM), no molde de `client-otc/tests/autotest_rc.lua`/`validate_v4_rc.lua` e da
metodologia validada pela rodada 3 (saltos curtos de `autoWalk`, tratamento de morte/relogin,
`g_game.safeLogout()`, script `client-otc/shinobirc.lua` temporário, nunca commitado).

## Resumo executivo

**Esta rodada foi interrompida por um evento de ambiente fora do meu controle, não por um
bug do jogo — e por isso a cobertura real é muito menor do que a pedida.** A conta e o
personagem foram criados com sucesso, o kit inicial chegou completo e o chakra nasceu em
60/60 (ambos confirmados ao vivo, ver abaixo), mas **por volta de 10:00, no meio da 6ª
tentativa de conectar o cliente, o processo `tfs` (que já estava no ar antes desta sessão
começar, PID 67566, de pé desde 09:41) foi encerrado de forma limpa por algo externo a esta
sessão** — o log do servidor mostra `Saving server... > Saved house items in: 0.001 s
Shutting down... done!` sem nenhum erro, sinal de crash ou mensagem de aviso antes disso, e
o timing bate exatamente com uma tentativa de login minha que falhou silenciosamente (nem
`onGameStart` nem `onLoginError` dispararam) — ou seja, o servidor caiu (ou foi derrubado por
alguém/algo) bem no instante em que eu tentava conectar, não por causa de nada que eu tenha
rodado. Disco (13 GB livres, bem acima do limiar de 1,5 GB) e MariaDB (`mysqld is alive`)
estavam saudáveis nesse momento — **não foi o mesmo problema da rodada 2** (ENOSPC).
Esperei ~10 minutos, monitorando `lsof -i :7171` a cada 15s, sem o processo voltar sozinho
(diferente do achado de `cliente-ux.md`, "o processo tfs reiniciou sozinho... PID mudou", em
que ele voltou por conta própria). Como a regra do ambiente é explícita — **nunca reinicie o
servidor** — e este não é um caso de "preciso reiniciar para pegar uma mudança", mas sim "o
servidor caiu por conta de terceiros", segui a regra à risca e não rodei `tools/run_server.sh`
nem qualquer variante. Isso encerrou a parte jogável desta sessão.

**O que consegui confirmar ao vivo antes da queda** (login funcionou 6 vezes seguidas nesta
janela, então os dados abaixo são reais, não hipotéticos): kit da vila com os mesmos 6 slots
da rodada 3 (bandana, mochila, colete de genin, kunai, calça, sandálias — ids 3374/2854/3361/
3292/3559/3552, slots direita/dedo/munição vazios), HP 150/150 e chakra 60/60 no primeiro
login, `!conquistas` respondendo `1/55` corretamente, e um **achado novo e concreto**: a
conquista de exploração "Pisou em Floresta da Vila" desbloqueia **no exato instante do login**,
antes de qualquer movimento — porque o retângulo usado para a zona "Floresta da Vila"
(`tools/export_tfs.py:2493`, `{1000, 1000, 1129, 1119}`) engloba a Vila da Folha inteira
(muralha em `1010-1049, 1030-1069`), então nascer no templo já conta como "estar na floresta".
Ver P1-3 abaixo.

**Confirmado por inspeção de arquivo (não foi possível confirmar ao vivo, mas os arquivos
gerados/instalados batem com o que a missão pediu para validar):**
- **Regen de HP/chakra**: `server/tfs/data/XML/vocations.xml`, vocação "Vila da Folha":
  `gainhpticks="5" gainhpamount="2" gainmanaticks="5" gainmanaamount="3"` — exatamente os
  "+2 HP/5s, +3 chakra/5s" que a missão descreveu como mudança desta rodada. **Não pude medir
  o comportamento em jogo** (precisa de combate ao vivo, que a queda do servidor impediu).
- **Densidade da Trilha dos Lobos**: `server/tfs/data/world/valley-spawn.xml` mostra os dois
  pontos de spawn (`1012,1012` e `1050,1010`, raio 4) agora com **2 Lobos cada** (era 3-4 na
  rodada 3) — o P2-2 da rodada 3 (a causa das duas mortes daquela sessão) parece endereçado
  no arquivo instalado. De novo, **não pude confirmar em combate real**.
- **Achievements/sprites/sons**: não verificados (precisam de jogo ao vivo).

**Cobertura real desta rodada: só o spawn (nível 1, XP 0).** Nenhum combate, nenhuma missão,
nenhuma tarefa, nenhuma diária, nenhuma compra no Ichiro, nenhum dado de XP/h ou chakra em
combate. A tabela de progressão e a lista de "o que faria desistir" abaixo são, portanto,
baseadas no que dá para inferir de arquivos estáticos e do histórico das rodadas 1-3, não em
medição nova — deixo isso marcado em cada seção.

## Cronologia do que rodei (para quem retomar)

1. `df -h /System/Volumes/Data` → 13 GB livres (bem acima do limiar). Servidor (`tfs`, pid
   67566) e AAC (`tools/aac.sh`) já estavam de pé antes de eu começar — não reiniciei nada.
2. Conta `playtester4` + personagem "Playtester Quatro" (Folha, `genin_laranja`) criados via
   AAC (`curl -X POST` para `/criar-conta` e `/criar-personagem`) — nasceu no templo
   (1029,1042,7), confirmado pela própria resposta do AAC.
3. 6 sessões curtas de `client-otc/shinobirc.lua` (cópia de scripts de teste próprios,
   variações incrementais enquanto eu ajustava a navegação — nunca commitado, apagado ao
   final de cada uma), todas via um runner próprio que **nunca usa `pkill -x OTClient`** —
   só mata o PID específico que ele mesmo abriu (diferente de `tools/autotest_client.sh`, que
   faz `pkill -x OTClient` incondicional no fim; não usei esse script por segurança, já que
   pode haver um OTClient do usuário aberto).
   - Sessão 1: login + `!conquistas` + abrir menu Shinobi → confirma HP 150/150, chakra
     60/60, level 1, e a conquista de exploração disparando cedo demais (ver P1-3).
   - Sessões 2-5: leitura dos 10 slots de inventário (kit confirmado) + depuração da
     navegação — descobri que `LocalPlayer:autoWalk` falha com `PathFindResultNoWay` (status
     4) contra a porta fechada do templo (item 1629/"door"), mesmo depois de eu mandar
     `g_game.use()` nela; só funcionou de verdade andando passo a passo
     (`g_game.walk(direction)`) na direção da porta, o que a abre automaticamente ao pisar
     nela — isto refina o aprendizado da rodada 3 ("abrir portas antes de cada trecho"): não
     basta abrir a porta com `use`, o *pathfinding* do cliente trata a tile da porta como
     bloqueada mesmo aberta até você andar por ela manualmente pelo menos uma vez.
   - Sessão 6: tentativa de viagem templo → Trilha dos Lobos em waypoints de ~10 tiles — o
     login falhou silenciosamente (sem `onGameStart` nem `onLoginError`) bem no momento em
     que o log do servidor mostra o boot de uma nova instância do `tfs` (arquivo
     `/tmp/tfs_run.log` criado às 10:00:00) seguido, minutos depois, de um `Shutting down...
     done!` limpo. Não fui eu que derrubei ou reiniciei o processo em nenhum momento.
4. Confirmei por `mysql -u tfs -ptfs forgottenserver` (leitura, sem alterar nada) que o
   personagem ficou salvo em `level=1, experience=0, health=150/150, mana=60/60,
   pos=(1029,1048,7)` — na praça, logo depois da porta do templo, pronto para a rodada 5
   continuar a viagem até a Trilha dos Lobos sem precisar refazer o kit/onboarding.
5. Limpei os 5 screenshots que gerei (`pt4_01..05`) de
   `~/Library/Application Support/shinobi/.shinobi/`, copiei para `screenshots/playtest4_*`
   reduzidos com `sips -Z 400` (~112-124 KB cada, total ~584 KB, bem abaixo do limite de 40
   arquivos), e apaguei `client-otc/shinobirc.lua` ao final de cada sub-sessão (confirmado
   que não sobrou nenhuma cópia).

## Achados por severidade

### P0 — bloqueia a progressão

Nenhum novo. Não cheguei a combate para reconfirmar os P0 das rodadas 1/2 (kit vazio, loja
quebrando), mas o kit chegou completo de novo nesta sessão (ver abaixo), então não há sinal
de regressão nisso.

### P1 — atrapalha bastante

**P1-3 (novo, confirmado ao vivo). A conquista de exploração "Pisou em Floresta da Vila"
desbloqueia no instante do login, antes de qualquer movimento do jogador.**

- **Repro**: criar personagem novo, logar. No log do cliente, a primeira mensagem depois de
  "em jogo" já é `Conquista desbloqueada: Pisou em Floresta da Vila!` — antes de qualquer
  `g_game.walk`/`autoWalk` ter rodado.
- **Causa raiz**: `tools/export_tfs.py:2493` (bloco `NarutoAchievements.zoneBounds`, também
  duplicado em `server/tfs/data/lib/naruto_achievements.lua:106`, ambos gerados a partir do
  mesmo dicionário Python) define `floresta_da_vila = {1000, 1000, 1129, 1119}` (retângulo
  x:1000-1129, y:1000-1119). A Vila da Folha (muralha em x:1010-1049, y:1030-1069, per
  `docs/sistemas/mapas.md`) está **inteiramente dentro** desse retângulo — não existe
  exclusão da própria vila. Um `GlobalEvent` periódico (`achievements.lua`, comentário "Sem
  onEquip/entrou na zona genérico no TFS 1.4.2") varre a posição de cada jogador contra esses
  6 retângulos e desbloqueia `visit_zone` na primeira vez que a posição cai dentro — como o
  templo (spawn, 1029,1042) já está dentro do retângulo "floresta", a conquista dispara sem o
  jogador nunca ter saído da vila.
- **Efeito**: baixo em termos de jogabilidade (é só uma conquista de exploração, dá 100 ryo),
  mas é um bug de primeira impressão ruim — a primeira conquista do jogo é "mentirosa"
  (recompensa por algo que ele não fez ainda) e provavelmente confunde quem for conferir a
  lista de conquistas logo cedo.
- **Por que não corrigi**: o retângulo mora em `tools/export_tfs.py` (o gerador em si, não um
  dos arquivos de dados autorizados desta missão — `data/npcs`, `tasks.json`, `dailies.json`,
  `items`, textos `naruto_*`). Ajustar o retângulo (ex.: recortar o excerto da muralha da
  vila, ou trocar por um polígono/lista de zonas menores) é uma mudança de lógica do
  exportador, fora do escopo autorizado desta rodada — mesma régua aplicada ao P1-1 da
  rodada 3. **Sugestão para quem tiver escopo**: subtrair o retângulo da Vila da Folha
  (x:1010-1049, y:1030-1069) do retângulo "floresta_da_vila", ou versionar os 6 retângulos
  como uma lista de sub-áreas em vez de 1 retângulo grande por região (os outros 5 têm o
  mesmo risco em tese, mas não os testei — Ruínas/Montanha/Covil não têm vila dentro do
  retângulo declarado, então o problema é específico da Vila da Folha por enquanto).

**P1-4 (herdado, não pôde ser reconfirmado). Chakra não regenera naturalmente perto de
spawns densos (P1-1 da rodada 3).** A missão descreveu uma mudança específica para esta
rodada (regen permanente configurada no login, `+2 HP/5s +3 chakra/5s` pela vocação) que eu
**confirmei existir no arquivo instalado** (`vocations.xml`, ver acima) mas **não pude testar
em jogo** — a queda do servidor aconteceu antes de eu chegar à Trilha dos Lobos. Fica como a
pendência nº 1 da rodada 5: repetir exatamente o teste da rodada 3 (chakra até secar, medir
a cada 10s parado e em combate) para confirmar se a condição permanente realmente resolveu o
achado antigo.

### P2 — polimento

**P2-5 (novo, achado de metodologia, não bug de jogo).** `LocalPlayer:autoWalk` retorna
`Otc.PathFindResultNoWay` (status 4) contra qualquer porta fechada, **mesmo depois de eu
mandar `g_game.use()` nela para abri-la** — o cache de pathfinding do cliente parece não
reconhecer a porta como andável até o jogador andar manualmente por cima dela pelo menos uma
vez (só então passa a rotear por ali normalmente). Isso é mais forte que o aprendizado da
rodada 3 ("abra a porta antes do trecho") — não basta abrir, é preciso um passo manual
(`g_game.walk(direção)`) através da tile da porta antes de voltar a usar `autoWalk`. Documento
aqui para o script de QA da rodada 5 economizar o tempo que gastei descobrindo isso ao vivo
(a porta do templo, item 1629/1630, alternando id ao usar — confirma que é uma porta de
verdade, não decoração).

**P2-6 (novo, operacional, baixo impacto).** O processo `OTClient` deu `Segmentation fault:
11` de forma consistente (nas 6 sessões desta rodada) **depois** de `g_app.exit()` já ter
sido chamado e o log já ter registrado tudo que o script pedia — ou seja, o crash acontece no
teardown/saída do processo, não durante o jogo. Não vi nenhum efeito colateral no servidor ou
no personagem por causa disso (o `has logged out.` aparece limpo no log do servidor mesmo
assim). Não investiguei a causa (fora do escopo de C++ do cliente autorizado nesta missão),
mas registro para quem for mexer no ciclo de vida do app (`client-otc/src/client/...` ou
`framework/application.cpp`).

**P2-7 (herdado, confirmado por inspeção). Densidade da Trilha dos Lobos parece corrigida
no arquivo instalado** (ver "Resumo executivo" acima) — reduzo a severidade do P2-2 da rodada
3 para "watch": o arquivo bate com o que a missão descreveu, mas só um combate real (rodada 5)
fecha esse achado de vez.

## Tabela por nível

| Nível | Tempo real gasto | Kills | Mortes | XP ganho | XP/h | Observação |
|---|---|---|---|---|---|---|
| 1 | ~20 min (majoritariamente debugando navegação/porta, não jogando) | 0 | 0 | 0 | N/D | Sessão interrompida pela queda do servidor antes de qualquer combate. Personagem ficou salvo em (1029,1048,7), na praça, logo após a porta do templo — pronto pra continuar a rota (Rua dos Mercadores → Portão Leste → ~44 tiles de mata → Trilha dos Lobos, mesma rota validada pela rodada 3) assim que o servidor voltar. |

Sem dados de nível 2 em diante. Nenhum combate foi alcançado.

## Tabela de chakra/regen

| Nível | Jutsu | Custo | Cooldown | Casts até secar | Chakra final | Regen medido |
|---|---|---|---|---|---|---|
| 1 | `fuuton lamina vento` | 13 | ~2s | **Não testado** | — | **Não testado** — servidor caiu antes do combate. Confirmado só por inspeção de arquivo: `vocations.xml` da Vila da Folha tem `gainhpticks=5 gainhpamount=2 gainmanaticks=5 gainmanaamount=3`, que bate com o "+2 HP/5s +3 chakra/5s" descrito na missão como a mudança desta rodada — mas isso é a *configuração*, não o *comportamento observado*. |

**Esta é a lacuna mais importante desta rodada**: a missão pediu explicitamente para medir
"chakra a cada 10s parado, casts até secar, tempo para voltar a 60" como prioridade nº 1, e
não deu pra fazer nenhuma dessas três medições. Prioridade máxima da rodada 5.

## Comparação com `progressao-jogador.md`

Não há dados novos de XP/h para comparar (nenhum combate). O que dá pra dizer com o que foi
confirmado nesta rodada:

- O kit e os stats iniciais (HP 150/150, chakra 60/60) batem com a coluna "Equipamento a ter"
  do bloco 1-5 (`bandana_leaf`, `vest_genin`, `pants_ninja`, `sandalias_ninja`, `kunai_iron`).
- A regra de regen (`+2 HP/5s +3 chakra/5s`) confirmada no arquivo instalado é exatamente o
  tipo de mudança que poderia colocar a rodada 3 de volta nos ~536 XP/h esperados pela tabela
  (o P1-1 da rodada 3 mostrava chakra **travado em 8/60 por ~7 minutos**, o que forçava o
  jogador a lutar só de soco depois do burst inicial de jutsu — regen ativo devolveria o
  jutsu como opção recorrente, não só de abertura). **Mas isso é uma inferência, não uma
  medição** — só a rodada 5, com combate de verdade, confirma se a mudança teve o efeito
  esperado.
- A redução da densidade da Trilha dos Lobos (2 Lobos por ponto em vez de 3-4) deveria, em
  teoria, eliminar o cenário de "pull total mata antes do primeiro kill" que produziu as duas
  mortes da rodada 3 — de novo, inferência a partir do arquivo, não confirmada em combate.

## O que faria um jogador desistir (honesto, baseado em 1-3 + o pouco desta rodada)

1. **Ainda não dá pra saber se o chakra trava de novo** (o motivo nº 1 de desistência
   apontado pela rodada 3) — essa é literalmente a pergunta que esta rodada deveria responder
   e não respondeu. Um jogador que sinta o chakra "morrer" depois do 6º-7º cast e não voltar
   por minutos vai voltar a socar sem parar, o que é chato mas não impede progressão (dano de
   soco funciona desde a rodada 3).
2. **Um jogador que crie conta e personagem pelo site (AAC) e depois o servidor caia no meio
   da primeira sessão dele, sem aviso, perderia a paciência.** Isso não é um bug do jogo em
   si (foi um evento de infraestrutura, fora do meu controle), mas é exatamente o tipo de
   experiência que um jogador real teria se isso acontecesse fora de um ambiente de teste —
   vale que quem administra o servidor tenha um plano de "auto-restart com log claro" para
   produção, mesmo que a regra de QA (não reiniciar) continue certa para sessões de teste.
3. **A porta do templo trava a navegação de scripts de QA** (P2-5) — não afeta jogador humano
   (que clica na porta normalmente e ela abre), mas é uma armadilha real para quem for
   automatizar o próximo playtest; documentado para não repetir o tempo perdido.
4. Pontos já conhecidos das rodadas 1-3 que continuam válidos até prova em contrário: a
   densidade de spawn da Trilha dos Lobos (agora parece corrigida, não confirmado em combate)
   e o comando `{tarefas}` que trava o chat do cliente (P1-2 da rodada 3, não testado de novo
   aqui, mesma pendência).

## O que foi corrigido nesta sessão

Nada. Não cheguei a nenhum combate/missão/tarefa/diária que gerasse um achado de texto/dado
corrigível dentro do escopo autorizado (`data/npcs`, `tasks.json`, `dailies.json`, `items`,
`naruto_*`) — só o achado da conquista de zona (P1-3), que mora em `tools/export_tfs.py`,
fora desse escopo. Rodei `.venv/bin/python tools/validate_data.py` mesmo assim, só para
conferir a saúde atual dos dados (sem editar nada): `OK — tudo válido`, 114 tarefas, 60
diárias, 55 conquistas — nenhuma regressão nos dados desde a rodada 3 (a checagem de nomes
duplicados "Tarefa: Tarefa:"/"Diária: Diária:" que a rodada 3 corrigiu continua limpa, 0
ocorrências em `tasks.json`/`dailies.json`).

## Metodologia e limitações

- **Script de automação**: 6 variações de `client-otc/shinobirc.lua` (nunca commitadas,
  apagadas ao final de cada sessão), rodadas por um runner próprio (não
  `tools/autotest_client.sh`) que mata **só o PID que ele mesmo abriu** — nunca `pkill -x
  OTClient` — para não arriscar matar um OTClient do usuário que estivesse aberto (não havia
  nenhum: confirmei com `pgrep -x OTClient` antes de começar).
- **Sem GM usado para jogar**: toda a sessão foi só com a conta `playtester4` (comum, sem
  `god`); não usei `slqa`/GM em nenhum momento (não cheguei nem a precisar de `/reload`, já
  que não corrigi nada no servidor).
- **`safeLogout()` não foi confirmado com sucesso desta vez**: nas tentativas dentro do
  templo, `g_game.safeLogout()` retornou "You can not logout here." (confirma que o interior
  do templo tem `no-logout`, como `docs/sistemas/mapas.md` já documentava) — eu ainda estava
  processando a saída pela porta quando o tempo/servidor acabou, então não cheguei a testar
  logout limpo fora da zona de proteção nesta rodada. O personagem ficou salvo via timeout de
  rede (documentado como comportamento esperado desde a rodada 3), não via logout limpo — sem
  efeito colateral visível (o personagem carregou de volta certinho na consulta ao banco).
- **Bloqueio de ambiente, não do jogo**: o evento central desta rodada (queda do processo
  `tfs`) não foi causado por nenhum comando meu — confirmei disco (13 GB livres) e MariaDB
  (`mysqld is alive`) saudáveis no momento da queda, e o log do servidor mostra um shutdown
  limpo (`Saving server... Shutting down... done!`), sem stack trace nem sinal de crash.
  Esperei ~10 minutos (checagem de `lsof -i :7171` a cada 15s) sem o processo voltar sozinho.
  Segui a regra do ambiente ("nunca reinicie o servidor") à risca e não tentei subir
  `tools/run_server.sh` nem nenhuma variante — o que significa que esta rodada termina aqui,
  sem chegar perto da cobertura L1-L10 pedida.
- **Conta `playtester4`**: criada nesta sessão via AAC, mantida no banco (não apagada) para
  a rodada 5 continuar — personagem "Playtester Quatro", nível 1, 0 XP, HP 150/150, chakra
  60/60, posição salva (1029,1048,7), já do lado de fora da porta do templo.

## Screenshots

Em `screenshots/`, prefixo `playtest4_`: `playtest4_01_spawn.png` (kit + stats confirmados no
templo), `playtest4_02_conquistas_antes.png` (resposta de `!conquistas`, 1/55, mostrando a
conquista de zona já desbloqueada), `playtest4_03_menu_personagem.png` (Menu Shinobi aberto),
`playtest4_04_inventario.png`, `playtest4_05_praca.png` (personagem já fora do templo, na
praça). 5 screenshots no total (limite era 40).

## Espaço em disco

| Momento | Livre em `/System/Volumes/Data` |
|---|---|
| Antes da sessão | 13-14 GB |
| Depois da sessão (após limpeza de screenshots e `shinobirc.lua`) | 13 GB |

Sem variação relevante — bem acima do limiar de 1,5 GB da regra de disco. A queda do
servidor nesta rodada **não foi causada por falta de espaço** (confirmado o valor no momento
exato da queda).

## Para o usuário / próxima rodada (r5), em ordem de impacto

1. **Confirmar que o servidor está de pé de novo antes de começar** (`lsof -i :7171` ou
   `ps aux | grep build/tfs`) — esta rodada não conseguiu medir nada de combate porque ele
   caiu no meio do caminho, por um motivo externo a esta sessão de QA.
2. **Repetir a medição de chakra/regen que era a prioridade nº 1 desta missão** e não foi
   feita: chakra a cada 10s parado, casts até secar, tempo de volta a 60, tanto parado quanto
   em combate sustentado perto da Trilha dos Lobos — a mudança de regen já está no arquivo
   instalado (`vocations.xml`), só falta confirmar o comportamento.
3. **Confirmar se a Trilha dos Lobos com 2 Lobos por spawn (em vez de 3-4) resolve as mortes
   da rodada 3** — arquivo já mostra a mudança instalada, falta um combate real.
4. Considerar corrigir o P1-3 (conquista de zona disparando no spawn) — fora do escopo desta
   missão (mora em `tools/export_tfs.py`), mas é uma correção pequena e de baixo risco para
   quem tiver permissão de mexer no exportador: subtrair o retângulo da Vila da Folha do
   retângulo "floresta_da_vila", ou usar uma lista de sub-retângulos por região.
5. Retomar exatamente de onde esta rodada parou: personagem "Playtester Quatro" já está na
   praça (1029,1048,7), só falta a rota Rua dos Mercadores → Portão Leste → mata → Trilha dos
   Lobos, já validada pela rodada 3 (~44 tiles em saltos curtos).
6. Ao escrever o próximo script de navegação, usar o achado do P2-5 (portas fechadas
   precisam de um passo manual através da tile, não só `g_game.use()`) para economizar o
   tempo que esta rodada gastou descobrindo isso.
