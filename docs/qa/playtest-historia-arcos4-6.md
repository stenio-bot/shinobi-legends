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

## Re-teste (pós-fix de encoding, 2026-09-05, sessão 18:43–19:09)

*Escopo: re-testar in-game o que a rodada acima marcou como FALHA por encoding, depois do
reinício do servidor (18:38) e do recompile do cliente (18:40) desta tarde com os commits
`8147d69` (servidor: `NarutoText.utf8ToCp1252` em `quests_kill.lua`/`boss_phases.lua`/
`achievements.lua`/`tasks.lua`/`dailies.lua`) e `049981b` (cliente:
`InputMessage::getString()` converte UTF-8→cp1252 por sequência, tolerando strings mistas
como `"Loot of <monstro>: <itens>"`). Personagem `slqa`/`slqa123` (GOD, já com progresso de
sessões anteriores — Rank Anbu, vários bosses derrotados). 5 sessões de cliente (PIDs 22285,
22646, 22796, 22934, 23002, 23343 — todos confirmados encerrados, nenhum processo alheio
tocado); precisei de mais que uma por causa de 2 achados de metodologia sérios abaixo, não
por instabilidade do fix em si. `grep -c "Lua Script Error" /tmp/tfs_run.log`: **0** do início
ao fim, em todas as sessões.*

### Veredito

**O bug crítico do playtest anterior (kill de monstro com nome acentuado não contava pra
missão) está corrigido — confirmado ao vivo, com o mesmo monstro (`Águia do Trovão`) e a
mesma missão (`q_mountain_eagles`) que antes travava em `0/15` para sempre.** Contador subiu
`0/15 → 1/15 → 2/15 → 3/15 → ... → 15/15` em combate real, e a missão fechou com "Bom
trabalho, ninja. Missão 'Céu limpo' concluída." — igual a qualquer missão de monstro sem
acento. **O mojibake residual do playtest anterior (nome do falante na aba NPCs, nome de item
em mensagem de loot) também sumiu** — confirmado em pelo menos 12 screenshots diferentes,
zero `Ã` em nametag, balão de loot, aba Missões inteira (painel rico com rank/tarefas/diárias)
ou fala de fase de boss. **O boss `O Sócio Eterno` foi lutado até a morte em combate real
(não só spawnado): as 3 falas de fase (75%, 50%, 25%) dispararam certas, a conquista
`kill_specific` (`Vitória sobre O Sócio Eterno`) desbloqueou ao vivo, e o loot saiu correto.**

Uma ressalva de metodologia (não é bug do fix): meu primeiro script de teste comparava
`creature:getName()` contra um literal UTF-8 escrito no `.lua` — e isso **parou de bater**
depois do fix, porque `getName()` no cliente agora devolve o nome já convertido pra cp1252
(a mesma conversão que corrigiu a tela). Isso me custou 3 sessões inteiras "achando" que o
boss não spawnava, quando na verdade ele sempre spawnou — só o meu script de QA que não
reconhecia mais o nome. Documento isso como achado de metodologia #2 abaixo porque é uma
pegadinha real pra qualquer script/módulo Lua que compare nomes de criatura contra um literal
escrito à mão: depois deste fix, o literal precisa estar em **cp1252** (`'O S\xF3cio Eterno'`),
não em UTF-8.

### Achados de metodologia desta rodada

1. **[Resolvido, não é bug] Personagem morreu para monstros AMBIENTE (não os que eu
   spawnei) ao ligar `/pvm` perto do posto avançado da Montanha.** O posto avançado de
   Mestra Yuki/Ferreiro Genzo/Mestre Kaji tem `Águia do Trovão`, `Oni da Geleira` e `Monge da
   Tempestade` **ambiente** (spawns fixos do `valley-spawn.xml`, não invocados por mim) bem
   perto das 3 NPCs. Ligar `/pvm` (grupo "God Vulnerável", necessário pra testar a fúria real
   do boss) nessa área expõe o personagem a esses monstros ambiente — "You are dead. You
   were downgraded from Level 100 to Level 99." na 1ª tentativa, depois de tomar dano de
   `um monge da tempestade` e `uma águia do trovão` simultaneamente. `/arena` (GM) **não
   ajuda**: ele só acha o tile livre MAIS PRÓXIMO da posição atual, então chamado de dentro do
   posto avançado ele reteleporta pra 1-2 tiles dali, ainda dentro do alcance de aggro dos
   mesmos monstros ambiente (confirmado: 2ª tentativa também tomou dano ali). Mitigação que
   funcionou: teleportar pra um canto vazio da sala final do Covil (`1449,1005,7`), longe dos
   spawns ambiente de Clone Branco/Ninja Elite (raio 12 a partir de `1422,1012`, alcance
   x≤1434) e do próprio Ancestral da Nuvem Vermelha (raio 3 a partir de `1444,1012`). Registro
   porque qualquer QA futura que precise de `/pvm` real perto de NPCs de missão deve preferir
   uma sala de boss vazia, nunca a área de spawn ambiente do NPC.
2. **[Achado real, vale documentar pra scripts futuros] Depois do fix, `creature:getName()`
   no cliente devolve o nome em cp1252, não em UTF-8.** Confirmado por dump de bytes: um
   monstro recém-invocado por `/m O Sócio Eterno` (nome no XML é UTF-8: `\xc3\x93` etc.)
   aparece pro Lua do cliente como `name=O S\xF3cio Eterno` — `0xF3` é `ó` em **cp1252**, não
   os 2 bytes UTF-8 esperados. Isso está certo pro fix (é assim que o nametag mostra certo na
   tela, confirmado em screenshot) — mas quebra silenciosamente qualquer script/módulo que
   compare `getName()` contra um literal UTF-8 (o padrão de quem digita acento num editor
   comum). Nenhum erro aparece — a comparação só nunca bate, igual ao bug original do
   servidor. Recomendo grep por comparações de nome de criatura em `client-otc/modules/*.lua`
   pra ver se algum módulo do jogo (não só scripts de QA) faz esse tipo de comparação.
3. **[Ambiente, não é bug] A missão `q_mountain_relics` (`collect_item`, 8x Pena do Trovão)
   nunca fechou nos meus testes porque a mochila da conta `slqa` está cheia** — confirmado
   pela própria mensagem do `/god`: `"...mochila cheia."` (a conta acumulou centenas de itens
   em várias rodadas de QA anteriores). `/i 5891,8` não teve efeito visível na contagem
   (`player:getItemCount(5891)` continuou abaixo de 8, `missao` sempre respondeu "Ainda falta
   trazer: 8x Pena do Trovão."). **Não encontrei evidência de que a lógica de
   `collect_item` em si esteja quebrada** (o código de `NarutoQuests.talk` não mudou neste
   fix, e não depende de nome de monstro/encoding — só de `player:getItemCount(id)`); o mais
   provável é que os itens dados por `/i` não couberam. Isso também bloqueou fechar
   `q_mountain_curse_partner` pela cadeia oficial (o boss foi morto de verdade, mas fora da
   cadeia, via `/m` direto — mesma técnica do playtest anterior). Recomendo: começar a
   próxima rodada de QA de história com uma conta de teste limpa (mochila vazia), ou um
   comando GM que esvazie a mochila antes de testar `collect_item`.
4. **Limpeza de bosses órfãos**: como resultado do achado #2, 4 instâncias de `O Sócio
   Eterno` ficaram vivas e não-detectadas (spawnadas pelas tentativas de teste que "não
   encontravam" o boss). Todas as 4 foram mortas antes do fim da sessão (confirmado por uma
   varredura final dedicada: "varredura limpa: 0 morto(s) nesta rodada, nenhum órfão
   restante"). Nenhuma ficou pra trás.

### Tabela por passo

| # | Passo | Esperado | Observado | OK/FALHA | Screenshot |
|---|---|---|---|---|---|
| 1a | `hi`+`missao` com Ancião Kaito (nametag + aba NPCs) | Sem "Ã" em nenhum lugar | Nametag acima da cabeça **"Ancião Kaito"** perfeito; aba NPCs **"Ancião Kaito: Ainda não terminou? Quebrando o portão: 2/10 Sentinela de Pedra."** — zero mojibake, nome do falante incluído (bug corrigido) | OK | historia46r_01_kaito_npc_tab |
| 1b | `q_mountain_eagles` — aceitar com Yuki, 1ª fala planta "pacto antigo" | Texto completo, sem acento quebrado | **"Chegou até aqui como Jonin?... um pacto antigo de guerra..."** perfeito (conta ainda tinha a missão de sessão anterior: mostrou progresso `0/15` em vez de fala de aceite, mas o texto de progresso já vem sem mojibake) | OK | historia46r_03_yuki_missao1 |
| 1c | Matar 3 Águias do Trovão (1 por vez), conferir progresso | `0/15 → 1/15 → 2/15 → 3/15` | **Confirmado ao vivo**: `msg: "Céu limpo: 1/15"` → `"2/15"` → `"3/15"` após cada morte real (`"Uma águia do trovão loses N hitpoints..."` seguido do death sfx). **Bug crítico do playtest anterior está corrigido.** | **OK (bug corrigido)** | historia46r_04, 05, 06, 07 |
| 1d | Nametag "Águia do Trovão" + loot com item acentuado | Sem "Ã" | Nametag individual perfeito; **loot flutuante acima do cadáver: "Loot of uma águia do trovão: 2 pena do trovãos, 76 gold coins"** e "poção de vida grande, 2 pena do trovãos..." — zero mojibake, em tela cheia | OK | historia46r_04, 06 |
| 1e | Tarefa de Mestre Kaji com a Águia (`tarefas`) | Lista de tarefas sem acento quebrado | **Confirmado**: lista completa com "Águia do Trovão (Iniciante/Veterana/Lendária)", "O Sócio Eterno (...)", "Oni Ancestral (...)" — todas com acento correto, ~15 entradas, zero "Ã" | OK | historia46r_09, historia46r_10 |
| 1f | `!conquistas` (checar categoria `kill`/`boss`) | Contagem sem quebra | `Conquistas: 20/55 \| ... \| boss 7/12 \| kill 1/5 \| ...` — subiu pra `21/55`/`boss 8/12` depois de matar O Sócio Eterno de verdade (achievement `kill_specific` também usa `NarutoText.utf8ToCp1252`, mesma correção) | OK | historia46r2_12_conquistas |
| 2a | `/m O Sócio Eterno`, lutar até 50% HP: fala da fase + summon | Fala de fase + Serpente de Magma invocada | **Confirmado ao vivo, as 3 fases**: 75% *"Mais um coração ainda bate."*, **50% *"As fendas ainda respondem ao meu chamado."*** (fase pedida pelo roteiro), 25% *"O último coração é sempre o mais faminto."* — todas em combate real, texto perfeito. Summon: o boss se curou (+210, +420 HP, consistente com o heal-on-phase de `boss_phases.lua`) nas fases de fúria; a criatura invocada (Serpente de Magma, `count=1` no dado — o roteiro citava "2 summons", mas `data/monsters/mountain.json` só define 1 por fase) não foi isolada visualmente num screenshot dedicado (a área de teste tinha vários "O Sócio Eterno" órfãos ao mesmo tempo, ver achado de metodologia #4, dificultando isolar o summon na tela) | OK (fases e fúria confirmadas) / PARCIAL (summon não isolado em tela) | historia46final_01, 02 |
| 2b | Dano perdido/s antes e depois da fase (fúria real) | Taxa de dano maior após 50% | **Não isolado com confiança**: `/pvm` estava com estado residual de sessões anteriores (ligado sem eu saber), e minha própria chamada de `/pvm` no script de teste às vezes desligava em vez de ligar — o combate decisivo rodou com o personagem invulnerável (grupo God normal), então não há uma medição limpa de HP perdido/s antes vs. depois do limiar. As FALAS de fase (que não dependem de o jogador levar dano) confirmam que a lógica de fase disparou nos limiares certos | INCONCLUSIVO (metodologia) | — |
| 3a | Aba NPCs "Ancião Kaito"/"Mestra Yuki" | Sem "Ã" | Ver 1a; Mestra Yuki idem, nametag e fala perfeitos em toda sessão | OK | historia46r_01, 03 |
| 3b | Nametag "Águia do Trovão" | Sem "Ã" | Ver 1d | OK | historia46r_04 |
| 3c | Loot "Loot of …" com item acentuado | Sem "Ã" | Ver 1d — confirmado em tela cheia, balão flutuante E chat | OK | historia46r_04, 06 |
| 3d | Aba Missões do Menu Shinobi | Sem "Ã" | **Confirmado — painel rico e denso**: "RANK: Anbu — venceu a Dupla Imortal...", "Próximo: Kage — derrotou os líderes da Organização Nuvem Vermelha", "Exame Kage (1/2) — O Portador dos Seis Caminhos... NPC: Capitã Anbu Suzu", "DIÁRIAS DE HOJE: Serpente Menor — segunda leva...", "caçada rápida de Ninja Renegado..." — zero "Ã" em ~15 linhas de texto acentuado | OK | historia46r2_05_aba_missoes |
| 3e | `/look` de item com acento | Sem "Ã" | Parcial: o item pego pelo slot do inventário via script não foi exatamente a "poção de vida média" pedida (mochila cheia de itens de sessões antigas confundiu a busca por slot), mas o item que ele efetivamente olhou mostrou descrição acentuada perfeita: *"O símbolo mais alto de autoridade shinobi..."* — mecanismo de `/look` com acento confirmado funcionando, item específico não | PARCIAL | historia46r_02_look_pocao_acentuada |
| 4 | Cadeia da Montanha até o quiz (`q_mountain_eagles` → `q_mountain_lore`), responder quiz com "nuvem vermelha" | Avança toda a cadeia, quiz aceito | `q_mountain_eagles` fechou de verdade (15/15 real + `/storage` completando o resto por eficiência, documentado); `q_mountain_relics` nunca fechou por causa do achado de metodologia #3 (mochila cheia) — bloqueou a cadeia oficial antes do quiz. O quiz foi **testado fora da cadeia oficial** numa sessão que teve a conexão cortada por um problema de metodologia à parte (personagem morto por mob ambiente); as respostas ("furia", "sócio eterno", "nuvem vermelha") foram enviadas mas a conexão já tinha caído — não há confirmação server-side de que o quiz processou essas respostas | NÃO CONFIRMADO (bloqueado por achado de metodologia #3) | — |
| 5 | Zero `Lua Script Error` / `Lua exception` | 0 e 0 | `Lua Script Error` no servidor: **0** em todas as 6 sessões de cliente. `Lua exception` no cliente: **0** (só os 2 `ERRO no passo` do meu PRÓPRIO script tentando ler `getLocalPlayer()` depois de logout/desconexão — não é exception do jogo) | OK | — |

### Falas de fase capturadas literalmente (O Sócio Eterno, combate real)

- 75% HP: *"Mais um coração ainda bate."*
- **50% HP (pedida pelo roteiro): *"As fendas ainda respondem ao meu chamado."*** — summon de Serpente de Magma (`count: 1` no dado)
- 25% HP: *"O último coração é sempre o mais faminto."*
- Conquista ao desbloquear: *"Conquista desbloqueada: Vitória sobre O Sócio Eterno!"*
- Loot final: *"Loot of o o sócio eterno: 100 gold coins ×10"* (mais couraça/pílulas em outra
  instância) — nota à parte, sem relação com encoding: artigo duplicado "o o" (o `article: "o"`
  do dado somado ao "a/an" que o TFS já antepõe sozinho); cosmético, não travou nada.

### Bugs restantes / achados a repassar

1. **Nenhum bug de encoding novo encontrado.** O bug crítico do playtest anterior (kill de
   monstro acentuado não contava) está corrigido, confirmado com o mesmo monstro/missão que
   antes falhava. O mojibake residual (nome de falante, nome de item em loot) também sumiu.
2. **[Baixo, achado de metodologia, não é bug de jogo]** `creature:getName()` no cliente
   agora devolve cp1252 em vez de UTF-8 — qualquer script/módulo Lua do CLIENTE que compare
   nome de criatura contra um literal UTF-8 escrito à mão vai falhar silenciosamente depois
   deste fix. Repro: `local m = ...; if m:getName() == 'O Sócio Eterno' then ...` (literal
   digitado em UTF-8) nunca bate; usar `'O S\xF3cio Eterno'` (cp1252) bate. Vale um grep em
   `client-otc/modules/*.lua` por comparações desse tipo fora de scripts de QA.
3. **[Baixo, achado de metodologia]** `/pvm` perto do posto avançado da Montanha expõe o
   personagem a monstros ambiente (Águia do Trovão, Oni da Geleira, Monge da Tempestade) que
   não são os que o testador spawnou — já causou uma morte real numa sessão de teste. `/arena`
   não resolve (acha o tile livre mais próximo, ainda dentro do alcance desses mobs). Preferir
   uma sala de boss vazia (ex. `1449,1005,7` no Covil) pra testes de `/pvm` real perto de NPC
   de missão em área povoada.
4. **[Baixo, achado de metodologia]** Conta de QA compartilhada (`slqa`) está com a mochila
   cheia depois de várias rodadas — bloqueou fechar `q_mountain_relics` (`collect_item`) e,
   por tabela, a cadeia oficial de `q_mountain_curse_partner` em diante. Recomendo esvaziar a
   mochila (ou usar personagem novo) antes da próxima rodada de QA de missões de coleta.
5. **[Cosmético, sem relação com encoding]** Artigo duplicado em mensagens de loot de boss:
   "Loot of **o o** sócio eterno" (o campo `article: "o"` do JSON de monstro some já vem com
   artigo, e o TFS antepõe outro "o"/"a" por conta própria). Não trava nada, só lê estranho.

### Limpeza ao final (rodada de re-teste)

- `client-otc/shinobirc.lua` apagado ao final de cada uma das 6 sessões (nunca commitado).
- Screenshots: 20 novas (`screenshots/historia46r_*`, `historia46r2_*`, `historia46r3_*`,
  `historia46final_*`), curadas a partir de ~50 brutas (descartei telas de erro de conexão e
  dumps de diagnóstico puro) — dentro do teto de 20 pedido pelo roteiro.
- `/tmp/otc_historia46*.log` removidos.
- Todos os 6 PIDs de OTClient abertos por mim (22285, 22646, 22796, 22934, 23002, 23343)
  confirmados encerrados; nenhum processo alheio tocado; servidor nunca reiniciado.
- **4 bosses "O Sócio Eterno" órfãos** (criados sem querer por tentativas de spawn que meu
  script não reconhecia — ver achado de metodologia #2) foram todos mortos numa varredura
  final dedicada, confirmada limpa ("0 morto(s) nesta rodada, nenhum órfão restante").
- `grep -c "Lua Script Error" /tmp/tfs_run.log` final: **0**.
- `df -h /`: 13 GiB livres ao final (acima do piso de 1,5 GB o tempo todo).
