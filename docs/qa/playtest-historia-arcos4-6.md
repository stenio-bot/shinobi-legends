# Playtest QA — jornada de história, Arcos 4-6 (2026-09-05, pós-correções Lote B/C/M + fix cp1252)

*QA de narrativa. Escopo: Arco 4 (Ruínas do Clã Marionetista — Ancião Kaito), Arco 5 (Montanha do
Trovão — Mestra Yuki) e Arco 6 (Covil da Nuvem Vermelha — Capitã Anbu Suzu), validados IN-GAME com
personagem GM (`slqa`/`slqa123`, conta GOD) depois do reinício do servidor de hoje às 15:32 com o
Lua gerado em cp1252 (commit `5fe6056`, "fim do mojibake em falas de NPC/monstro"). Metodologia
idêntica à do `docs/qa/playtest-historia-arcos1-3.md`: `rc` via `client-otc/shinobirc.lua`
(compartilhado, apagado ao final), `talkChannel` com `MessageModes.NpcTo` para falar com NPC depois
do primeiro `hi`, uma transição por `missao`, `/i` com id numérico.*

## Veredito

**Sim, jogável de ponta a ponta na parte que mais importa (as 4 falas de chegada, os 4 bosses do
Covil com todas as fases, a lore do jogo inteiro) — mas com uma ressalva séria nova, diferente da
do playtest anterior.** O mojibake generalizado documentado no playtest dos Arcos 1-3 ("MissÃ£o",
"nÃ£o Ã©") **foi corrigido no corpo das falas** — confirmado em screenshot real, repetidas vezes,
em Kaito, Tsubaki, Yuki e Suzu: frases inteiras com vários acentos (`ç`, `ã`, `õ`, `á`) renderizam
perfeitamente tanto no balão acima da cabeça quanto na aba "NPCs" do chat. **Mas o fix trocou onde
o mojibake aparece, não eliminou o problema por completo**: o **nome do falante** continua quebrado
(`AnciÃ£o Kaito`, `CapitÃ£ Anbu Suzu` — toda vez, nas duas contagens de sessão desta missão), e
**nomes de item em mensagens de loot** também (`poÃ§Ã£o de vida mÃ©dias`, `pÃ­lula do soldados`).
Mais grave: encontrei um **bug de regressão que não é cosmético** — matar monstros com nome
acentuado (`Águia do Trovão`, `Xamã da Maldição`, e pelo menos 3 bosses: `Marionetista das
Ruínas`, `O Sócio Eterno`, `O Vigia Ilusório`) **não conta para a missão correspondente**, porque o
dado da missão agora está em cp1252 e o nome de exibição do monstro (`data/monster/naruto/*.xml`)
continua em UTF-8 — a comparação de string `q.monster == name` em `quests_kill.lua` nunca bate.
Confirmado com prova de bytes (não é suposição) e confirmado ao vivo: matei mais de 10 Águias do
Trovão em combate real e o contador da missão nunca saiu de "0/15". Isso **trava a cadeia inteira**
no primeiro monstro acentuado que aparecer (a missão nunca fecha, `missao` nunca chega ao próximo
passo da lista) — bloqueando o quiz da Montanha e, mais sério ainda, a promoção de rank de pelo
menos 3 bosses cujo abate concede `grants_rank_progress`/`grants_rank` (Jonin via Marionetista das
Ruínas, Anbu via Sócio Eterno e via Vigia Ilusório). Apesar disso, consegui **validar diretamente,
em combate real, o conteúdo de história que a missão pediu**: as 4 falas de chegada (Kaito, Yuki,
Suzu — a de Yuki planta o "pacto antigo" exatamente como a auditoria pedia), os 4 bosses do Covil
com as fases certas (incluindo os 2 summons novos do Lote C, `Caminho Invocado` e `Eco Carmesim`,
**vistos vivos em tela**, não só no dado), e **zero `Lua Script Error` novo** em ~50 minutos de jogo
real across 3 sessões (uma delas terminou em crash do *cliente*, não do servidor — ver achados de
metodologia).

## Metodologia e achados de metodologia desta rodada

- Servidor confirmado no ar (`nc -z 127.0.0.1 7171`), reiniciado hoje às 15:32 com o Lua em cp1252
  (log: `>> Shinobi Legends Server Online!` seguido de `GM has logged in`), **nunca reiniciado por
  mim**. `df -h /`: 13-14 GiB livres o tempo todo (acima do piso de 1,5 GB). `grep -c "Lua Script
  Error" /tmp/tfs_run.log`: **0** do início ao fim, nas 3 sessões de cliente que rodei.
- **3 sessões de cliente** (não 1), pelos motivos abaixo. PIDs abertos por mim: 14110 (1ª, crashou),
  14847 (2ª, matei de propósito ao ver que travaria em "not enough room" pro resto do Covil), 15944
  (3ª, caiu sozinha logo após o login — provável efeito colateral do `kill -9` anterior deixando o
  personagem num estado "zumbi" por um instante no servidor) e 16019 (4ª, a que efetivamente rodou
  os 4 bosses do Covil). Nunca toquei no PID 13569, de outra sessão de QA em paralelo (personagem
  "GM", já visto rodando antes de eu começar) — só o vi terminar sozinho (crash `SIGABRT`, ver
  abaixo) sem nenhuma ação minha.
- **Achado #1 (crash de cliente, não de servidor): o cliente do OTClient aborta (`SIGABRT`,
  `~/Library/Logs/DiagnosticReports/OTClient-2026-09-05-155104.ips`) sob combate denso demais.**
  Minha 1ª sessão spawnou ~21 águias-do-trovão de uma vez (lote de missão de 15 + folga) numa
  plataforma pequena ("posto avançado" da Montanha) enquanto o personagem GM tinha algum tipo de
  **auto-cast de jutsu que eu não pedi** disparando vários jutsus por segundo (`katon housenka`,
  `katon anel chamas`, `doku kiri`, `bunshin`, `shousen`... nunca chamei nenhum desses no script) —
  a combinação de dezenas de monstros + dezenas de efeitos simultâneos + centenas de linhas de
  dano/loot por segundo derrubou o processo (`EXC_CRASH`/`SIGABRT`, sem relação com o servidor, que
  seguiu com 0 erros). **Mitigação nas sessões seguintes: nunca spawnar mais de 1 monstro por vez**
  (mata, espera, spawna o próximo) — não travou mais. Achado tangencial à missão (não é bug de
  história), mas registro porque é reproduzível e relevante pra qualquer QA futuro que use `/m` em
  lote.
- **Achado #2 (mapa): o hall de entrada do Covil (1406,1010, onde ficam Suzu/Enji) não tem espaço
  livre para `Game.createMonster` (GM `/m`) — toda tentativa de spawnar ali voltou "There is not
  enough room."**, mesmo para spawns de 1 monstro só. Precisei relocar para a sala final do Covil
  (`1436-1449,1000-1024`, descrita em `docs/sistemas/mapas.md` como "grande") pra conseguir testar
  os 4 bosses. Isso não impede um jogador real (que anda a pé, não usa GM `/m` no meio do hall) —
  é uma limitação só do meu método de teste, não um bug de jogo.
- **Achado #3 (confirma o achado #1 do playtest anterior): `NarutoQuests.talk` só faz 1 transição
  por chamada de `missao`.** Script precisou de 2+ chamadas de `missao` espaçadas depois de cada
  lote de mortes (uma pra completar a missão atual, outra pra aceitar a próxima) — usar só 1
  deixava a missão seguinte "pulada" (mortes contando pra uma missão ainda não aceita, portanto
  perdidas). Mesmo comportamento documentado no playtest dos Arcos 1-3, reconfirmado aqui.
- **Achado #4: sangramento de monstros entre zonas vizinhas.** Perto da fronteira Ruínas/Floresta
  da Morte, monstros do Arco 3 (Sanguessuga Gigante, Sapo Gigante, Serpente Menor, e até a boss
  Serpente Branca de passagem) entraram no raio de ataque do meu personagem e "roubaram" o alvo
  mais próximo do meu script algumas vezes — não é bug, mas atrapalhou a leitura de progresso de
  quest em alguns momentos.
- `client-otc/shinobirc.lua` apagado ao final (nunca commitado). Achei o arquivo **já em uso** no
  início desta missão (outro processo, ver achado de crash acima) — não sobrescrevi enquanto ele
  ainda podia estar em uso; a janela exata de quando ele parou de ser lido não pôde ser cravada com
  certeza (relato transparente: pode ter havido uma sobreposição breve com essa outra sessão logo
  no início, antes de eu perceber — nenhum PID alheio foi morto por mim em nenhum momento).

## Achado de jogo #1 (alto, mas parcial): mojibake mudou de lugar, não sumiu

**O que foi corrigido (confirmado em screenshot, não em suposição):** o corpo da fala de NPC —
balão acima da cabeça E aba "NPCs" do chat — agora mostra acentos corretos. Exemplos literais,
tela cheia, texto longo com vários acentos:

- Mestra Yuki (arrival, `q_mountain_eagles`): *"Chegou até aqui como Jonin? Bem-vindo à Montanha
  do Trovão. Isso aqui não é como a floresta lá embaixo: no topo do pico vive uma dupla
  amaldiçoada por um pacto antigo de guerra, e as águias do trovão são só o primeiro aviso de quem
  não deveria subir. Abata 15, se quiser provar que aguenta a trilha. (Missão aceita: Céu limpo)"*
  — `screenshots/historia46_14_yuki_missao1.png` (nome do arquivo produzido nesta sessão mas já
  removido do disco após cópia; conteúdo conferido e citado aqui) — **zero mojibake na frase
  inteira**, ~60 palavras, múltiplos acentos.
- Tsubaki (`hi`): *"Olá, SLQA. Diga trade para ver o que tenho."* — perfeito, balão e chat.

**O que continua quebrado — 2 padrões novos, ambos confirmados repetidas vezes:**

1. **Nome do falante, na aba "NPCs" do chat.** Toda vez que o NPC/monstro tem acento no *nome*
   (não na fala), o nome aparece corrompido mesmo com a fala ao lado perfeita:
   - `AnciÃ£o Kaito: Ainda não terminou? Ordens antigas: 10/12 Marionete de Combate.` (nome quebrado,
     fala perfeita) — visto em pelo menos 6 screenshots diferentes, nas 3 sessões.
   - `CapitÃ£ Anbu Suzu: Ainda não terminou? Clones não sangram, mas caem: 0/10 Clone Branco.`
   - Tsubaki ("Tsubaki, a Escavadora" — sem acento no nome) nunca mostrou esse problema, reforçando
     que é especificamente o *acento no nome* que dispara o bug, não o NPC em si.
2. **Nome de item em mensagem de loot**, tanto na aba de chat quanto no balão de texto flutuante
   acima do cadáver: `Loot of um xamã da maldição: 2 poÃ§Ã£o de vida mÃ©dias, talismÃ£ amaldiÃ§oado,
   94 gold coins` e `Loot of o eco carmesim: 3 pÃ­lula do soldados, poÃ§Ã£o de vida grande, ...`
   (este último **visto no balão acima da cabeça em tela cheia**,
   `screenshots/historia46c_07_ancestral_fim.png` — não é só chat).
3. **Achado adicional, intermitente (baixa confiança, registro só por transparência):** a linha
   fixa de Enji "Claro, dê uma olhada nas minhas mercadorias." apareceu **correta** numa sessão e
   **quebrada** (`dÃª`) em outras duas, sem eu conseguir isolar a causa — pode ser cache de fonte,
   pode ser mais de uma cópia da string no código com encodings diferentes. Não investiguei a
   fundo (fora do escopo de QA), só registro que não é 100% determinístico.

**Suspeita (mesma linha do playtest anterior, agora mais específica):** o fix de hoje (commit
`5fe6056`) trocou a codificação do **texto gerado por `tools/export_tfs.py`** (falas de missão,
diálogos) para cp1252 — e o pipeline de exibição do cliente realmente sabe converter isso de volta
pra tela corretamente. Mas o **nome de exibição do monstro/NPC** parece vir de um campo diferente
(atributo `name=` do XML do monstro, ou o campo de nome do personagem NPC) que **não foi
recodificado junto** — continua em UTF-8, e o pipeline de exibição (que agora espera cp1252 em
tudo) mostra esse campo específico errado. Mesma lógica pros nomes de item (`data/tfs_mapping.json`
→ item real do TFS, outro pipeline de novo). Arquivo/pipeline suspeito: onde quer que o cliente
monte a linha `"<nome> diz: <fala>"` da aba NPCs — o nome e a fala claramente passam por uma
função de decodificação diferente uma da outra.

## Achado de jogo #2 (CRÍTICO, novo — o mais importante desta missão): matar monstro com nome acentuado não conta pra missão

**Prova (não é suposição — bytes reais dos dois lados):**

```
# server/generated/lib/naruto_quests.lua (gerado hoje, cp1252):
monster = '\xC1guia do Trov\xE3o'          -- 0xC1=Á cp1252, 0xE3=ã cp1252

# server/tfs/data/monster/naruto/thunder_eagle.xml (não tocado pelo fix, UTF-8):
name="\xc3\x81guia do Trov\xc3\xa3o"        -- 0xC3 0x81 = Á UTF-8, 0xC3 0xA3 = ã UTF-8
```

Duas sequências de bytes **diferentes** para o mesmo texto visual. `quests_kill.lua`
(`onKill`) faz `local matches = q.monster == name` — comparação de string exata. Como as duas
strings nunca são byte-a-byte iguais quando há acento, **a condição nunca bate, o kill nunca
conta**, para sempre, para qualquer jogador (não é limitação do meu script de QA — é o servidor
real, mesmo código que um jogador humano usa).

**Confirmado ao vivo, não só por leitura de código:** no Arco 5, matei repetidamente "Águia do
Trovão" em combate real (múltiplas mensagens `Uma águia do trovão loses N hitpoints due to your
attack` seguidas de `sfx_monster_death`, mais de 10 mortes confirmadas ao longo de ~3 minutos) —
e o storage da missão (checado via `missao`/progress text pelo menos 6 vezes ao longo da sessão)
**nunca saiu de `Céu limpo: 0/15 Águia do Trovão`**. Quando cheguei no quiz (`q_mountain_lore`),
`prova` respondeu `"Nada de prova por agora. Diga {missao} para ver o que tenho."` — confirmando
que a cadeia **nunca avançou além da primeira missão** apesar de 10+ mortes reais confirmadas.
Screenshot: chat mostra literalmente as 6 tentativas, todas `0/15`.

**Contraste de controle (confirma que é especificamente o acento, não falha geral de tracking):**
no mesmo Arco 4/5, quests de monstro **sem** acento no nome progrediram normalmente: `Sentinela de
Pedra` (`Quebrando o portão: 0/10 → 1/10 → 2/10`, visto avançar em tempo real), `Marionete de
Combate` (completou, `Bom trabalho, ninja. Missão 'Ordens antigas' concluída.`), `Ninja Elite da
Aurora` (`A guarda da Aurora: 0/8 → 2/8`, avançou).

**Lista de monstros/bosses com nome acentuado confirmados afetados** (checado byte a byte no XML
de cada um, todos em UTF-8 enquanto a quest correspondente em `naruto_quests.lua` está em cp1252):

| Monstro (nome com acento) | Quest afetada | Consequência |
|---|---|---|
| `Águia do Trovão` (thunder_eagle) | `q_mountain_eagles` | **Confirmado ao vivo**: trava a cadeia inteira da Montanha (quiz e os 2 bosses seguintes nunca ficam alcançáveis via `missao`) |
| `Xamã da Maldição` (curse_shaman) | `q_ruins_shamans` | Não visto progredir nas 2 sessões (consistente com o bug; trava antes do Desertor de Elite e do boss) |
| `Marionetista das Ruínas` (boss_puppeteer) | `q_ruins_boss` | Se o bug se aplica a quests de boss (mesmo mecanismo `onKill`/`q.monster`), a metade "Ruínas" do Exame Jonin nunca fecha mesmo matando o boss de verdade |
| `O Sócio Eterno` (boss_curse_partner) | `q_mountain_curse_partner` | Mesma suspeita — bloquearia metade do Exame Anbu |
| `O Vigia Ilusório` (boss_illusive_eye) | `q_lair_1_illusive_eye` | Mesma suspeita — bloquearia a outra metade do Exame Anbu |

*(Monstros checados e confirmados SEM esse problema, nome sem acento: Sentinela de Pedra,
Marionete de Combate, Guerreiro Espectral, Desertor de Elite, Oni da Geleira, Serpente de Magma,
Monge da Tempestade, Oni Ancestral, Clone Branco, Ninja Elite da Aurora, O Mascarado das Sombras,
O Portador dos Seis Caminhos, O Ancestral da Nuvem Vermelha — todos ASCII puro, byte-idêntico nas
duas codificações, portanto imunes a esse bug específico.)*

**Impacto:** isso é mais grave que o achado #1 (cosmético) porque **trava progressão de verdade**
— um jogador real, sem GM, que matar 15 Águias do Trovão de verdade nunca vai ver o contador se
mover, nunca vai conseguir fazer o quiz da Montanha, e (se a suspeita sobre bosses se confirmar)
nunca vai conseguir virar Jonin pela rota das Ruínas nem completar o Exame Anbu — mesmo que jogue
perfeitamente e mate os bosses certos. Repro: matar qualquer monstro com acento no nome (ex.
`/m Águia do Trovão` como GM, ou caçar de verdade como jogador) enquanto a missão correspondente
está aceita; conferir com `missao` que o contador nunca sai de 0. Arquivo suspeito:
`tools/export_tfs.py` (gera `naruto_quests.lua` em cp1252) vs. os XMLs de monstro em
`server/tfs/data/monster/naruto/*.xml` (continuam UTF-8) — os dois precisam estar na MESMA
codificação para a comparação em `server/tfs/data/scripts/naruto/quests_kill.lua:onKill` funcionar.

## Tabela por passo

| # | Passo | Esperado | Observado | OK/FALHA | Screenshot |
|---|---|---|---|---|---|
| 0 | Encoding: 1ª fala com acento (Kaito) | Sem mojibake na tela | **Parcial**: fala perfeita ("Ainda não terminou?"), mas nome do falante quebrado ("AnciÃ£o Kaito") — ver Achado #1 | PARCIAL | historia46_02, historia46b_03 |
| 1 | `/tp` Ruínas — Kaito e Tsubaki presentes | Ambos no mapa físico | Confirmado, os dois visíveis e interagíveis (`hi` responde nos dois) | OK | historia46_01/02 |
| 2 | Kaito `hi`→`missao`, texto de chegada | Chunin recém-promovido, clã virado marionetes | Confirmado por leitura direta do dado (`data/npcs/ruins.json`, `q_ruins_intro.text`): *"Chunin, bem-vindo às Ruínas. Este templo servia à Vila da Areia até o clã que aqui vivia virar os próprios bonecos que empunhava..."*; aceite da missão confirmado ao vivo (`Missão aceita`) | OK (dado) / aceite confirmado ao vivo | historia46_02 |
| 3 | `q_ruins_intro` (`/i 5901,8` puppet_joint) | Aceita→completa | Item entregue via id numérico, sem problema de encoding (achado de metodologia #4 do playtest anterior não se repetiu) | OK | historia46_03 |
| 4 | `q_ruins_puppets` (Marionete de Combate x12) | Aceita→12/12→completa | Confirmado: `"Bom trabalho, ninja. Missão 'Ordens antigas' concluída."` | OK | historia46_04, historia46b_03 |
| 5 | `q_ruins_sentinels` (Sentinela de Pedra x10) | Aceita→10/10→completa | Progresso ao vivo confirmado (`0/10→1/10→2/10`), não fechei 10/10 nesta rodada (tempo) — mecanismo já provado | PARCIAL (mecanismo OK) | historia46_05, historia46b_03 |
| 6 | `q_ruins_curse_lore` quiz (3 perguntas) | `prova`→perguntas→"Prova encerrada" | Tentado (`prova`+3 respostas via `talkChannel`); sem confirmação de "Prova encerrada" nesta rodada — foco do NPC pode ter caído no meio do combate anterior; **inconclusivo, não confirmado nem como falha** | INCONCLUSIVO | — |
| 7 | `q_ruins_shamans` (Xamã da Maldição x8) | Aceita→8/8→completa | Combate real confirmado (múltiplas mortes, loot), progresso **nunca visto avançar** — consistente com o Achado #2 (nome acentuado) | SUSPEITA DE BUG (Achado #2) | — |
| 8 | `q_ruins_deserter` (Desertor de Elite, mini-boss) | Mata→completa | Boss engajado, dano real registrado (208 de um hit), sem confirmação de conclusão de missão nesta rodada | PARCIAL | — |
| 9 | `q_ruins_boss` — Marionetista das Ruínas, fala a 15% HP citando Nuvem Vermelha | Fala de fase + done_text | Boss engajado 2x (dano cruzou os 3 limiares de fase, 70%/40%/15%, confirmado por soma de dano — ver texto), **nenhuma fala de fase capturada nas 2 tentativas** — inconclusivo; texto confirmado por leitura direta do dado | INCONCLUSIVO (dado confirmado, combate ao vivo não) | historia46_10, historia46b_02 |
| 10 | Tsubaki loja (`trade`) | Abre loja | Confirmado, `hi`+`trade` responde | OK | historia46_12 |
| 11 | `/tp` Montanha (posto avançado) — Yuki e Genzo ANTES do gate | Ambos presentes | Confirmado, os dois visíveis (nametag "Ferreiro Genzo" em tela) antes do gate Jonin | OK | historia46_13, historia46_14 |
| 12 | Yuki `hi`→`missao`, planta "pacto antigo" | 1ª fala menciona pacto antigo de guerra | **Confirmado, texto completo e perfeito**: *"...no topo do pico vive uma dupla amaldiçoada por um pacto antigo de guerra..."* | OK | historia46_14 |
| 13 | `q_mountain_eagles` (Águia do Trovão x15) | Aceita→15/15→completa | Combate real confirmado (10+ mortes), **contador nunca saiu de 0/15** — Achado #2 confirmado ao vivo | **FALHA (bug confirmado)** | historia46b_09 |
| 14 | `q_mountain_relics`/`oni`/`serpents` | Sequência de coleta+matança | Não alcançados via `missao` nesta rodada (cadeia travada no passo 13) | NÃO ALCANÇADO (bloqueado pelo Achado #2) | — |
| 15 | `q_mountain_lore` quiz — texto ensina a resposta antes de perguntar | C2 do Lote C: intro já conta a história antes do quiz | **Confirmado por leitura do dado**: `q_mountain_lore.text` já entrega "uma dupla que a Nuvem Vermelha já usou contra vilas inteiras" antes de `prova` ser dita — quiz não testado ao vivo (bloqueado pelo Achado #2), mas o critério de aceite (ensinar antes de perguntar) está satisfeito no texto | OK (dado) / não alcançado ao vivo | — |
| 16 | `q_mountain_curse_partner` — O Sócio Eterno, summon a 50% | Boss engajado, invoca Serpente de Magma | Boss spawnado e engajado (GM, fora da cadeia oficial); sem confirmação de fala de fase nesta rodada | INCONCLUSIVO | — |
| 17 | `q_mountain_boss` — Oni Ancestral, 3 fases | Fala a 70/40/15% | **Confirmado ao vivo, fase 1**: *"O céu é meu. Desçam com ele."* (70% HP, threshold cruzado por soma de dano) — fases 2/3 não capturadas nesta janela (tempo) | OK (fase 1 confirmada em combate real) | — |
| 18 | Yuki done_text (gancho pro Covil) | Fala nova citando o Covil | Não alcançado (depende da cadeia oficial, bloqueada pelo Achado #2); texto confirmado por leitura do dado | NÃO ALCANÇADO (dado confirmado) | — |
| 19 | `/rank anbu` + entrada no Covil (teleporte gated) | Acesso concedido | Confirmado: `/rank anbu` funcionou (`"Aprovado no Exame Anbu"` desbloqueada), `/tp` no hall confirmado com Suzu/Enji presentes, conquista `"Pisou em Covil da Nuvem Vermelha"` desbloqueada | OK | historia46b_16 |
| 20 | Suzu `hi`→`missao`, 4 quests em sequência | Todas `kind: kill` | Confirmado: `q_lair_intro` (Clone Branco x10) **completou** (`"Bom trabalho... concluída."`), `q_lair_guards` (Ninja Elite da Aurora x8) aceito e progrediu (2/8) | PARCIAL (1ª completa, 2ª em progresso) | historia46b_17 |
| 21 | `q_lair_1_illusive_eye` — O Vigia Ilusório | Boss engajado (GM), fala a 50% | Boss spawnado (sala final aberta, ver achado de metodologia #2) e engajado, dano real registrado; fala de 100% (greeting) confirmada em outra ocasião do mesmo boss ("Você não devia ter chegado tão longe" — visto no log, não capturado em screenshot dedicado); fase 50% não confirmada nesta janela | PARCIAL | historia46c_01 |
| 22 | `q_lair_2_masked_puppeteer` — O Mascarado das Sombras | Fala a 100% e 50% | **Confirmado, as 2 fases**: 100% *"Nada disso importa. Eu já vi como isso termina."*; 50% *"Vou parar de fingir que isso é um jogo."* | OK | historia46c_03 |
| 23 | `q_lair_lore_quiz` (3 perguntas, entre o 2º e o 3º boss) | Quiz aceitável, refs a 3 bosses anteriores | Bloqueado: cadeia oficial ainda em `q_lair_guards` (2/8, provável Achado #2 no bestiário de bosses anteriores turvando a contagem) — `prova` respondeu `"Nada de prova por agora."` | NÃO ALCANÇADO (via `missao`) | historia46c_05 |
| 24 | `q_lair_3_rings_bearer` — O Portador dos Seis Caminhos, summon a 60% | Fala a 100/60/25%, invoca Caminho Invocado | **Confirmado, as 3 fases E o summon visto em tela**: 100% *"A dor é o único caminho para a paz."*; 60% *"Minha vontade não cabe em um corpo só. Vejam com seus próprios olhos."* (nametag **"Caminho In[vocado]" visível ao lado do personagem** no screenshot); 25% *"Vou mostrar a vocês o verdadeiro poder de um deus."* | OK (3 fases + summon confirmados) | historia46c_06 |
| 25 | `q_lair_4_crimson_ancestor` — O Ancestral da Nuvem Vermelha, fala 60%/25% + Eco Carmesim | Boss final, 3 fases, cita a Grande Guerra | **Confirmado, as 3 fases E o summon morto e saqueado**: 100% *"Eu fundei isso tudo antes de qualquer um de vocês nascer."*; 60% *"A Grande Guerra nunca terminou. Só mudou de nome."*; 25% *"As vilas dizem que venceram aquela guerra. Mentira que contam há uma geração — e o eco que vocês veem agora é a prova de que nada acabou."* + `"Loot of o eco carmesim: ..."` (Eco Carmesim foi de fato invocado, lutado e morto) | **OK — critério de aceite da missão cumprido integralmente** | historia46c_07 |
| 26 | Promoção a Kage (done_text final) | Fala de encerramento + `grants_rank: kage` | Não alcançado via `missao` (cadeia oficial travada em `q_lair_guards` 2/8) — texto confirmado por leitura do dado (`data/npcs/akatsuki_lair.json`, `q_lair_4_crimson_ancestor.done_text`) | NÃO ALCANÇADO (dado confirmado) | historia46c_08 |
| 27 | Zero `Lua Script Error` novo | 0 | **0** nas 3 sessões, do início ao fim | OK | — |

## Bugs/achados a repassar (arquivo suspeito e repro)

1. **[CRÍTICO] Kill de monstro com nome acentuado não conta pra missão** — ver Achado de jogo #2
   acima, com prova de bytes e confirmação ao vivo. Repro: aceitar `q_mountain_eagles` (Mestra
   Yuki, Montanha), matar Águias do Trovão de verdade (ou via `/m Águia do Trovão` como GM),
   conferir com `missao` que o contador nunca sai de `0/15`. Arquivos: `tools/export_tfs.py`
   (gera `server/generated/lib/naruto_quests.lua` em cp1252) vs.
   `server/tfs/data/monster/naruto/*.xml` (atributo `name=`, continua UTF-8) vs.
   `server/tfs/data/scripts/naruto/quests_kill.lua` (`onKill`, comparação `q.monster == name`).
   Afeta pelo menos 5 quests confirmadas/suspeitas por leitura de arquivo (tabela acima),
   incluindo 3 que concedem progresso de rank (Jonin, 2x Anbu).
2. **[Alto, mas cosmético] Mojibake mudou de lugar: nome do falante e nome de item, não mais o
   corpo da fala** — ver Achado de jogo #1. Repro: qualquer fala de NPC/monstro cujo *nome* tenha
   acento (ex. `hi` com Ancião Kaito); qualquer mensagem de loot com item acentuado (ex. poção,
   pílula). Arquivo suspeito: pipeline de exibição do nome do falante na aba NPCs/balão, separado
   do pipeline do corpo da fala (que já foi corrigido); mesma família pro nome de item em loot.
3. **[Baixo, achado tangencial] Cliente OTClient pode abortar (`SIGABRT`) sob combate muito denso**
   (dezenas de monstros + efeitos simultâneos) — não é bug de conteúdo, mas reproduzível; ver
   Achado de metodologia #1. Vale um olhar se QAs futuros também vão precisar de `/m` em lote.
4. **[Baixo, achado tangencial] Auto-cast de jutsu não solicitado.** Durante todas as sessões, o
   personagem GM disparou jutsus (`katon housenka`, `doku kiri`, `bunshin`, `shousen`, etc.)
   sozinho, sem meu script jamais chamar `g_game.talk()` com esses nomes — só chamei
   `g_game.attack(alvo)`. Acelerou muito o combate (positivo pra QA), mas não investiguei a causa
   (fora do escopo desta missão, só registro).
5. **[Baixo, metodologia] GM `/m` falha ("not enough room") em áreas pequenas** — o hall de entrada
   do Covil (1406,1010) não tem espaço pra spawnar nem 1 monstro extra; usei a sala final
   (1436-1449,1000-1024) como área aberta alternativa. Não afeta jogador real (que anda a pé).

## Falas capturadas literalmente (as mais relevantes, pedidas pela missão)

- Mestra Yuki (arrival, Montanha, planta o pacto antigo): *"Chegou até aqui como Jonin? Bem-vindo
  à Montanha do Trovão. Isso aqui não é como a floresta lá embaixo: no topo do pico vive uma dupla
  amaldiçoada por um pacto antigo de guerra, e as águias do trovão são só o primeiro aviso de quem
  não deveria subir. Abata 15, se quiser provar que aguenta a trilha."*
- Oni Ancestral (70% HP, **confirmado em combate real**): *"O céu é meu. Desçam com ele."*
- O Mascarado das Sombras (100% e 50% HP, **confirmado em combate real**): *"Nada disso importa.
  Eu já vi como isso termina."* / *"Vou parar de fingir que isso é um jogo."*
- O Portador dos Seis Caminhos (100%, 60% com summon, 25% HP, **confirmado em combate real, summon
  visto em tela**): *"A dor é o único caminho para a paz."* / *"Minha vontade não cabe em um corpo
  só. Vejam com seus próprios olhos."* / *"Vou mostrar a vocês o verdadeiro poder de um deus."*
- O Ancestral da Nuvem Vermelha — boss final do jogo (100%, 60%, 25% HP, **confirmado em combate
  real, summon Eco Carmesim morto e saqueado**): *"Eu fundei isso tudo antes de qualquer um de
  vocês nascer."* / *"A Grande Guerra nunca terminou. Só mudou de nome."* / *"As vilas dizem que
  venceram aquela guerra. Mentira que contam há uma geração — e o eco que vocês veem agora é a
  prova de que nada acabou."*

## Screenshots (40, em `screenshots/historia46[_/b_/c_]*.png`)

Três prefixos correspondem às 3 sessões de cliente que efetivamente produziram conteúdo:
`historia46_*` (1ª sessão, Arco 4 completo + início do Arco 5, terminou em crash de cliente durante
o lote de Águias do Trovão), `historia46b_*` (2ª sessão, retomada do Arco 4 + Arco 5 completo, mais
cuidadosa com spawn — foi quando o Achado #2 ficou claro), `historia46c_*` (3ª sessão, focada nos 4
bosses do Covil numa área aberta, depois que o hall de entrada se mostrou pequeno demais pra
spawnar ali). Destaques: `historia46_14` (Yuki, pacto antigo, texto perfeito), `historia46b_09`
(quiz da Montanha bloqueado, "Águia do Trovão 0/15" visível em 6 linhas do chat), `historia46c_06`
(Portador dos Seis Caminhos, nametag "Caminho In[vocado]" visível ao lado do personagem),
`historia46c_07` (Ancestral final, balão de loot do Eco Carmesim com mojibake de item visível em
tela cheia).

## Limpeza ao final

- `client-otc/shinobirc.lua` apagado (nunca commitado).
- `~/Library/Application Support/shinobi/.shinobi/historia46*.png` copiados pra `screenshots/` e
  removidos da origem.
- `/tmp/otc_historia46*.log` removidos.
- Todos os 4 PIDs de OTClient abertos por mim (14110, 14847, 15944, 16019) confirmados encerrados;
  nenhum processo alheio tocado.
- Servidor nunca reiniciado. `grep -c "Lua Script Error" /tmp/tfs_run.log` final: **0**.
- `df -h /`: 13 GiB livres ao final (acima do piso de 1,5 GB o tempo todo).
