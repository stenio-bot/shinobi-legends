# Playtest QA — Arco 3, Floresta da Morte / Exame Chunin (L20–30), 2026-09-06

*Preenchido incrementalmente durante a sessão. QA/playtester sênior simulando um jogador de
verdade (não GM), pulando só a moagem até o nível de entrada com uma conta GOD. Metodologia:
`docs/qa/playtest-arco2-costa.md` (g_game.walk tile a tile, talkChannel NpcTo após o 1º "hi",
morte de monstro por `getStackPos()==-1`/mensagem de loot, nunca `getCreatureById(id)~=nil`).*

## Ambiente no início da sessão

- `df -h /`: 13 GiB livres (48% usado). Servidor confirmado no ar (`nc -z 127.0.0.1 7171`,
  sucesso). **Não reiniciado por esta sessão** (mas ver achado abaixo: reiniciou sozinho por
  causa externa durante a sessão).
- `client-otc/shinobirc.lua` encontrado em uso por outra sessão no início (arquivo de re-teste
  de encoding do Arco 4-6, sem processo `OTClient` ativo no momento da checagem) — aguardados
  os 2 minutos da regra do `CLAUDE.md`, reconfirmada ausência de processo antes de sobrescrever.
- **Achado de ambiente (não é bug de jogo, mas afetou esta sessão de ponta a ponta): o ambiente
  compartilhado tinha, durante toda esta missão, PELO MENOS 2 outras sessões de agente rodando
  ciclos de teste/QA concorrentes na mesma máquina** (nomes de log vistos: `otc_qkfix3.log`,
  `otc_qkfix4.log`, e uma sessão que escreveu por cima deste mesmo arquivo `.md` entre uma
  checagem e outra, relatando um PID diferente — 40588 — bloqueado no mesmo `shinobirc.lua`).
  Isso teve 2 efeitos concretos nesta sessão:
  1. **O servidor TFS foi reiniciado por uma dessas sessões externas no meio do meu 1º teste**
     (confirmado: `/tmp/tfs_run.log` virou um boot novo, com só "Shinobi Legends Server Online!"
     seguido de poucos login/logout, no meio da minha sequência) — meu personagem (`SLQA`)
     caiu (`g_game.getLocalPlayer()` passou a `nil`) segundos depois de um `/tp`, e o resto da
     1ª rodada rodou "no vazio" (todo comando subsequente logou `sem player`, nenhum dano real
     foi trocado). Não fui eu quem reiniciou o servidor (nunca chamei restart/reload/install) —
     exatamente o cenário que o `CLAUDE.md` avisa ("o servidor às vezes cai ou reinicia sozinho
     por causa externa, não assuma que foi você").
  2. **Pelo menos uma dessas sessões usa o padrão `pkill -x OTClient` como faxina "por via das
     dúvidas" ao final do próprio loop de espera** (visto ao vivo via `ps aux`, um `for i in
     1..230; sleep 1; pgrep -x OTClient || break; done; pkill -x OTClient`) — esse padrão é
     exatamente o que o `CLAUDE.md` desta missão PROÍBE explicitamente para esta sessão
     ("nunca rode pkill -x OTClient, mata sessões de outros agentes"), mas outra sessão o usou
     mesmo assim, criando risco real de encerrar o MEU processo por nome (não por PID) a
     qualquer momento. Não retaliei nem usei o mesmo padrão — meus clientes foram sempre
     encerrados por `g_app.exit()` de dentro do próprio script Lua, nunca por `pkill`/`kill -9`
     de fora.
  3. **Este próprio arquivo (`docs/qa/playtest-arco3-exame-chunin.md`) foi sobrescrito por uma
     dessas sessões concorrentes entre uma escrita minha e a seguinte** (o conteúdo encontrado
     descrevia um PID/timeline diferentes dos meus, e afirmava "nenhuma ação in-game" quando
     esta sessão já tinha, de fato, rodado um cliente e coletado dados reais) — ou seja, **mais
     de um agente foi despachado para a mesma missão de playtest do Arco 3, ao mesmo tempo, sem
     coordenação de posse de arquivo entre eles.** Reescrito para refletir a sequência real
     desta sessão; nenhum dado do outro relatório foi preservado por não bater com eventos
     verificáveis nos logs desta sessão.
  - **Recomendação**: se o padrão de "vários agentes fazendo o mesmo QA ao mesmo tempo" persistir,
    vale um lock/arquivo de "sessão em andamento" mais explícito que `shinobirc.lua` sozinho
    (que só sinaliza posse do CLIENTE, não do relatório `.md` final).
- Conta: `slqa`/`slqa123` (GOD). Estado herdado de muitas sessões anteriores (Arcos 1-6):
  nível 98 antes do 1º `/lvl 20` desta sessão (confirmado por mensagem do servidor: "You were
  downgraded from Level 98 to Level 20") — skills de combate não têm comando de reset; qualquer
  TTK medido aqui deve ser lido como "teto otimista", igual às sessões anteriores.
- Script desta sessão: `client-otc/tests/arco3_examechunin_rc.lua` (mantido versionado; cópia
  temporária em `client-otc/shinobirc.lua`, apagada ao final de cada rodada).

## Metodologia desta sessão

Script único (`arco3_examechunin_rc.lua`) cobrindo: checagem de invulnerabilidade, reset de
storages via GM (`/storage <id> -1`) para simular Goro+Ibuki "do zero" na conta compartilhada,
reconfirmação do Portão Sul, rota real até a Floresta da Morte pelo Portão Leste (Hub do
Pântano), cadeia completa de 7 missões do Rastreador Goro, Exame Chunin completo (prova teórica
com as 5 perguntas reais, os 2 pergaminhos, torneio com os 3 rivais, promoção), e checagem
pós-promoção (`/rank`, menu). Contagem de monstros mistura kills 100% reais (leeches, toads,
rogue ninjas, serpentes) com fast-forward de GM (`/storage`) para o meio de lotes de 8-10,
sempre fechando com pelo menos 1 kill real antes de completar — "pular a moagem", não pular a
mecânica. `g_app.doScreenshot`, teto de 39 (abaixo do limite de 40 da missão).

## Resumo executivo

*(preencher ao final, depois de uma rodada completa)*

## Rodada 1 (interrompida por reinício externo do servidor, ~00:22:36–00:24:22)

Login, `/tp` para a vila, `/lvl 20`, `/pvm`, reset de storages (50021-50033, 60010) e a
reconfirmação do Portão Sul rodaram **de verdade e com dados válidos**. A partir do 2º `/tp`
(rumo ao Portão Leste), o servidor reiniciou por causa externa (ver "Ambiente" acima) e o
resto da rodada (toda a cadeia de Goro/Ibuki) rodou sem jogador válido — **descartado, não
usado no resto deste relatório**. Achados válidos desta janela:

- **`/lvl 20` a partir de L98: HP/chakra recalculados para um valor MUITO acima da fórmula
  esperada.** Mensagem do servidor: `"You were downgraded from Level 98 to Level 20."` /
  `"Level 20."`. HP/chakra resultantes: **1665/1665 HP, 980/980 chakra** — a fórmula documentada
  (`docs/sistemas/progressao-jogador.md`/`balanceamento`) prevê **15×20+150 = 450 HP** e
  **100+10×20 = 300 chakra** para L20. 1665/980 não bate nem com a fórmula de L20 nem
  parece ser simplesmente "o valor antigo preservado" (o valor em L98, visto momentos antes,
  era 2685/2835 HP e 1690/1760 chakra — diferente de 1665/980, então HOUVE recálculo, só que
  para uma fórmula/bônus que não é a nominal de L20 puro). Hipótese mais provável: o bônus de
  rank (`NarutoRanks.applyBonus`, condição permanente subId 9010) e/ou skills infladas de
  sessões `/god` anteriores continuam contribuindo pro pool máximo mesmo depois do `/lvl`
  rebaixar o nível base — **reconfirma, com números novos, o mesmo padrão já registrado como
  P1 em `docs/qa/playtest-arco2-costa.md`** ("`/lvl N` não recalcula corretamente ao rebaixar
  nível"), agora também claramente não-trivial mesmo quando HÁ recálculo. Arquivo suspeito:
  `server/tfs/data/scripts/naruto/gm_tools.lua` (`/lvl`) + `server/generated/lib/naruto_ranks.lua`
  (`applyBonus`).
- **`/pvm` reconfirma o achado "toggle cego" já documentado.** Resposta do servidor ao 1º
  `/pvm` desta sessão: `"PvM desligado: monstros não vão te atacar (grupo God normal)."` — ou
  seja, a conta já estava no grupo vulnerável (herdado de sessão anterior) e o 1º toggle
  desligou. **A missão previu exatamente esse cenário** ("tente alternar /pvm duas vezes"); a
  versão corrigida do script (usada nas rodadas seguintes) checa a mensagem e alterna de novo
  automaticamente quando detecta "desligado".
- **Portão Sul: TESTE POSITIVO — parece corrigido de verdade.** `/tp 1029,1066,7` (3 tiles ao
  norte do torii) seguido de **7 chamadas `g_game.walk(South)`** a 400ms: **7 de 7 passos
  aceitos**, posição final exata `1029,1073` (esperado: y sobe de 1066 para 1073 se destravado)
  — **0% de rejeição**, contra 95-100%/50% nas 2 tentativas de `playtest-arco2-costa.md`. Uma
  única amostra (a rodada foi interrompida antes de uma 2ª confirmação independente), mas é um
  resultado limpo e sem ambiguidade — ver seção própria abaixo.
- `[MUSIC] regiao floresta_vila` confirmado tocando nesse trecho (esperado, personagem ainda
  não tinha saído da vila).

## Portão Sul — reconfirmação do fix

**Corrigido, com uma ressalva de cobertura.** `docs/qa/playtest-arco2-costa.md` documentou o
Portão Sul travando 95-100% dos passos (tentativa 1) e ~50% (tentativa 2) com "Não há espaço
suficiente" bem no tile do torii. Nesta sessão, a mesma manobra (`/tp` a 3 tiles do portão +
caminhada `South` tile a tile) teve **100% de sucesso, 0 rejeições em 7 tentativas**,
atravessando exatamente a faixa do torii (`GATE_X=(1028,1030)`, `GATE_Y=1069`) sem nenhuma
mensagem de bloqueio. **Ressalva**: só 1 tentativa nesta sessão (a 2ª rodada não repetiu o
teste, focada no resto da missão); o padrão histórico (2 tentativas independentes na sessão do
Arco 2) sugere repetir pelo menos mais uma vez antes de fechar como 100% resolvido — mas o
resultado já é qualitativamente muito diferente do achado P0 original.

## Tabela por etapa

*(preencher com a rodada válida — ver abaixo)*

| Etapa | NPC/local | Diálogo capturado | Combate | Tempo real | Observação |
|---|---|---|---|---|---|
| | | | | | |

## Bosses

*(preencher: Sapo Ancião, Serpente Branca — fases, falas, TTK, mortes, chakra)*

## Exame Chunin — prova teórica

As 5 perguntas reais são lidas direto de `data/npcs/leaf.json`/`server/generated/lib/
naruto_quests.lua` (`exam_chunin_1_teoria`, `quizMin=3`, keyword match por substring,
case-insensitive, sem exigir acento) — a tabela abaixo já registra o texto exato e a
dedutibilidade a partir do que o próprio jogo ensina (kit inicial, HUD de chakra, o próprio
menu Shinobi). Resultado ao vivo (5/5 respondidas): *(preencher)*.

| # | Pergunta | Palavra-chave aceita | Dedutível de quê? |
|---|---|---|---|
| 1 | "O que você gasta para lançar um jutsu?" | `chakra` | Sim — o HUD mostra "Chakra" no lugar de mana (locale `pt.lua`) e todo tutorial/quest cita chakra |
| 2 | "Qual elemento é forte contra Doton?" | `fuuton`/`vento` | Parcial — exige saber a tabela de vantagem elemental (Fuuton > Doton), que não é ensinada explicitamente em nenhum diálogo visto até aqui nos Arcos 1-3; provavelmente exige conhecimento externo (lore de Naruto) ou tentativa e erro |
| 3 | "Quem te ensinou seus primeiros jutsus?" | `sensei`/`mestre`/`hayato` | Sim — Mestre Hayato é o NPC da loja de pergaminhos (`scroll_master_leaf`) que ensina/vende jutsus tier 2+ |
| 4 | "Qual skill sobe quando você lança jutsu?" | `ninjutsu` | Sim — a janela de skills (Alt+S) mostra a skill "Ninjutsu" subindo a cada cast, visível durante qualquer caçada |
| 5 | "Quem lidera a vila?" | `hokage` | Sim — glossário do `CLAUDE.md`/lore, "Hokage" aparece nos textos de vila desde o tutorial |

**Avaliação preliminar (a confirmar com a resposta ao vivo)**: 4 das 5 perguntas são
dedutíveis só de jogar (chakra, mestre, ninjutsu, hokage); a pergunta #2 (vantagem elemental
Fuuton>Doton) é a única que parece exigir conhecimento externo — nenhum diálogo/tutorial visto
nos Arcos 1-3 ensina a tabela de fraquezas elementais explicitamente.

## Torneio / promoção

*(preencher: TTK dos 3 rivais, mensagem de promoção, `/rank`, done_text da Ibuki)*

## Ambiente

*(preencher: música da Floresta da Morte, nomes acentuados, mojibake)*

## Comparação com os alvos de design

*(preencher: docs/sistemas/progressao-jogador.md bloco L20-30, TTK de boss 60-180s)*

## O que faria um jogador desistir

*(preencher)*

## Fricções por severidade

### P0

### P1

### P2

## Disco antes/depois

- Início: `df -h /` → 13 GiB livres (48% usado).
- Fim: *(preencher)*
