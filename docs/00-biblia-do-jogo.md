# A Bíblia de Shinobi Legends

*Documento mãe do jogo — mundo, história, progressão, sistemas e estado atual, tudo num só lugar.
Escrito para ser lido por qualquer pessoa do projeto: o dono, um artista, um dev novo, um jogador
beta. Cada seção cita o(s) arquivo(s) de onde os números e fatos vêm; onde a lore ainda era fina,
este documento escreve conteúdo novo — marcado **(novo)** — e o mesmo texto foi replicado em
`docs/lore/mundo.md` para não existirem duas versões da mesma lenda.*

*Última revisão: 2026-09-05 (sincronizada com balanceamento rodada 5, som procedural, conquistas e
playtests r3/r4). Fontes principais: `CLAUDE.md`, `README.md`, `docs/00-visao-geral.md`,
`docs/01-roadmap.md`, `docs/02-arquitetura.md`, `docs/03-decisoes-tecnicas.md`, `docs/04-setup-ot.md`,
`docs/lore/*.md`, `docs/sistemas/*.md`, `docs/qa/*.md`, `docs/backlog-sprites.md`,
`docs/backlog-audio.md`, e todo `data/*.json`.*

## Índice

1. [Visão](#1-visão)
2. [História do mundo](#2-história-do-mundo)
3. [O jogador](#3-o-jogador)
4. [Jornada do jogador](#4-jornada-do-jogador)
5. [Sistemas](#5-sistemas)
6. [Bestiário](#6-bestiário)
7. [Grimório de jutsus](#7-grimório-de-jutsus)
8. [Personagens e NPCs](#8-personagens-e-npcs)
9. [Direção de arte e som](#9-direção-de-arte-e-som)
10. [Tecnologia](#10-tecnologia)
11. [Estado atual e roadmap](#11-estado-atual-e-roadmap)
12. [Glossário](#12-glossário)
13. [Inconsistências encontradas](#13-inconsistências-encontradas)

---

## 1. Visão

*Fonte: `docs/00-visao-geral.md`, `CLAUDE.md`, `README.md`.*

**Shinobi Legends** é um MMORPG 2D top-down no estilo **Tibia clássico** — grid de 32px, sem
diagonal livre, sem física — ambientado num mundo shinobi original **inspirado** no universo
Naruto (nenhum nome, sprite ou termo registrado do anime aparece no jogo; ver ADR-002 na seção
9). O jogador cria um ninja, escolhe uma vila (que hoje funciona como vocação/cidade natal) e um
personagem com identidade própria, e evolui **caçando monstros**: cada caçada dá XP, sobe skills
por uso, dropa itens e ryo, e o jutsu certo na hora certa é o que faz a diferença entre uma matança
rápida e uma corrida até a poção de vida.

### Pilares de design
1. **Grind com propósito** — nenhuma caçada é vazia: XP, skill e chance de drop andam sempre
   juntos, e a curva de horas (seção 4) foi desenhada nível a nível, não por uma fórmula cega.
2. **Identidade de build** — vila (cidade/skill bônus) + personagem (4 jutsus pessoais fixos) +
   elemento (4 jutsus de kit, escolha livre) tornam cada ninja mecanicamente diferente sem exigir
   uma árvore de talentos.
3. **Jutsus são o show** — cada um dos 54 jutsus tem efeito visual próprio (seção 7); soltar o
   jutsu certo precisa ser o momento mais gostoso do combate, não um número saindo da tela.
4. **PvM primeiro** — o jogo inteiro (mapa, missões, tarefas, exames de rank) foi construído para
   jogador-vs-monstro. PvP, clãs e mercado entre jogadores estão no roadmap (Marco 5), não no MVP.

### Público e plataforma
O público-alvo é quem já jogou (ou queria ter jogado) **Narutibia/NTO Ultimate** e sente falta da
mistura "grind satisfatório de Open Tibia + fantasia ninja". É um jogo de **centenas de horas**:
a tabela da seção 4 mira ~1000 horas de conteúdo do nível 1 ao 100, concentradas de propósito nos
últimos 20 níveis (o "grind de nível alto" que define a experiência Tibia). Plataforma: cliente
**OTClient Redemption** (C++20, compila para macOS/Windows/Linux a partir do código-fonte; suporte
a Android/web existe no upstream mas não foi testado neste projeto) conversando com um servidor
**The Forgotten Server 1.4.2** — ou seja, multiplayer real desde o primeiro login, mesmo que hoje
só um jogador de cada vez tenha sido testado de verdade (seção 11).

### O que este jogo NÃO é
- **Não é** um jogo licenciado da franquia Naruto — é universo próprio, "inspirado em" (ADR-002).
- **Não é** PvP-first: não há guerra de clã, arena ranqueada nem mercado entre jogadores hoje.
- **Não é** uma MMO com loja/cash-shop: os módulos de loja, mercado, prey, wheel, forge e imbuing
  do OTClient/TFS foram todos desativados (seção 9 e `docs/04-setup-ot.md`).
- **Não é** turn-based nem tático: combate em tempo real, ataque automático no alvo + jutsus
  ativos via hotbar.
- **Não tem** (ainda) crafting complexo, casas compráveis, party ou clã — tudo isso é roadmap
  (Marco 5), não uma omissão silenciosa.

---

## 2. História do mundo

*Fontes: `docs/lore/mundo.md`, `docs/lore/pesquisa-naruto.md`, `docs/lore/progressao.md`. Os
trechos de cosmologia e da Grande Guerra abaixo são conteúdo novo desta missão — marcados
**(novo)** — e foram replicados em `docs/lore/mundo.md` (nova seção "0. As origens") para que
exista uma única versão do mito.*

### As origens **(novo)**

Antes das vilas, o mundo era só terra crua e mar sem nome — até que a primeira faísca de chakra
nasceu do encontro entre a vontade viva de um punhado de pessoas e a força bruta dos quatro
elementos primordiais: fogo, água, terra e vento. O raio veio depois, filho do choque entre os
quatro, e por isso ainda hoje é tratado como o elemento "mais jovem" nas lendas de fundação — a
única afinidade que nenhuma vila reivindica como a sua desde o princípio. Quem primeiro aprendeu a
dobrar essa força ao próprio corpo virou lenda antes de virar história: os "primeiros shinobi",
sem vila, sem bandana, sem rank, ensinando uns aos outros por pura necessidade de sobreviver a
bestas que hoje só existem enfraquecidas nos arredores de cada vila — os ancestrais dos lobos,
cobras e sapos que um Genin caça na primeira semana de jogo.

Vilas nasceram quando essas famílias de praticantes pararam de vagar e escolheram terra para
chamar de sua. A **Vila da Folha** se fixou onde a floresta era mais viva e o Katon mais fácil de
dominar. A **Vila da Névoa** cresceu onde a água nunca faltava, dona do Suiton. A **Vila da
Nuvem** se ergueu no alto, onde a tempestade quase nunca para, e reivindicou o Raiton como seu. A
**Vila da Areia**, na fronteira entre o deserto e a rocha, nunca escolheu um elemento só — dividiu-se
entre Fuuton (o corte do vento) e Doton (o peso da rocha), e por isso hoje é a única vila cuja
skill bônus é defensiva, não ofensiva (seção 3). Por gerações as quatro cresceram em paz relativa
— até a Grande Guerra.

### A Grande Guerra e o silêncio que está acabando **(novo)**

Ninguém vivo hoje viveu a Grande Guerra, mas todo mundo — cada Genin que entra na Academia —
carrega o que ela deixou. Foi nela que o sistema de ranks (Genin → Chunin → Jonin → Kage, com o
ANBU agindo como corpo de elite direto sob o Kage, fora da hierarquia numerada normal) deixou de
ser uma escala temporária de tempos de guerra e virou a estrutura permanente de qualquer vila em
paz: nenhuma vila desmobiliza um exército que pode precisar de novo. E foi nela, nas cinzas de
esquadrões inteiros dados como extintos ou que simplesmente desertaram, que um punhado de
sobreviventes — cada um carregando um poder que uma vila inteira temeu enfrentar uma segunda vez —
se organizou sob bandeira própria: nuvens vermelhas sobre capas pretas. Perderam a guerra, ou
pareceram perder; passaram uma geração inteira em silêncio, recrutando aos poucos os desertores
que toda vila grande acaba produzindo (bandidos de estrada, mercenários, ninjas renegados — o
"elenco genérico" que povoa as seis regiões do jogo).

É esse silêncio que está acabando agora — no exato momento em que o jogador nasce como Genin. A
**Organização Nuvem Vermelha** é a ameaça atual: não um exército às portas da vila, mas uma sombra
que já se infiltrou em quatro lugares diferentes do mapa antes mesmo de o jogador saber que ela
existe — o Chefe dos Bandidos na própria Floresta da Vila (sem saber, um eco pequeno demais do que
está por vir), o Espadachim da Névoa contratado por uma guilda rival na Costa das Marés, um gênio
desertor escondido nas Ruínas a caminho de recrutas maiores, e uma dupla amaldiçoada guardando a
Montanha do Trovão em nome do mesmo pacto antigo. O covil de verdade só aparece no fim: quatro
guardiões, cada um um espectro de um poder que uma vila enfrentou uma vez e nunca mais quis
enfrentar de novo.

### Os seis arcos, na ordem em que o jogador os vive

*(síntese literária de `docs/lore/mundo.md`, que continua sendo a fonte de detalhe — bestiário,
NPCs e coordenadas de mapa completos nas seções 6 e 8 deste documento.)*

**Floresta da Vila (Genin, nível 1–10).** A floresta que cerca a vila é o primeiro teste de
qualquer genin recém-formado: perto o bastante para uma equipe Jonin resgatar quem se meter em
apuros, perigosa o bastante para separar quem está pronto do resto do mundo. Lobos, cobras e uma
trilha comercial infestada de bandidos comuns dão o primeiro sabor de combate real — nada aqui é
obra de vilão lendário, só gente e bicho tentando sobreviver perto demais da vila. O Chefe dos
Bandidos, boss da região, não é ninja renomado nenhum: é só o bandido mais experiente da estrada,
armado e com squad — mas é o primeiro a cair para o jogador, e por isso importa.

**Costa das Marés (Genin, nível 12–19).** Inspirada no arco do País das Ondas: uma vila de
pescadores e a ponte que a liga ao continente vivem sob a sombra de uma guilda mercante rival, que
contratou um espadachim renegado para sabotar a obra. Ele não trabalha sozinho — um aprendiz
mascarado, ligado a ele por uma dívida mais funda que dinheiro, aparece sempre que o mestre está
perto de cair, e luta como se a própria vida dependesse disso, porque de fato depende. Antes da
ponte, mercenários de baixo escalão e batedores da névoa cobram o preço de sempre: gente comum do
lado errado da lei. Vencer o Espadachim (e por consequência o Aprendiz) é um dos dois requisitos
do Exame Jonin — mas só conta de verdade quando o jogador já é Chunin e volta aqui como prova.

**Floresta da Morte (Genin→Chunin, nível 10–25).** A mesma floresta abriga o campo de provas mais
temido da região: gente entra em duplas ou trios e só sai — supostamente — depois de provar que
sobrevive sem apoio da vila. Sanguessugas e sapos gigantes são só o alarme; ninjas renegados
fizeram da mata um esconderijo permanente; e no fundo, perto de um santuário abandonado, mora uma
criatura que já foi humana e decidiu que não precisa mais fingir — a Serpente Branca, o boss mais
"canônico" do jogo, um ninja renegado de pele pálida que abandona a forma humana quando encurralado.
É aqui, e só aqui, que roda o Exame Chunin inteiro: prova teórica com a Instrutora Ibuki, os dois
pergaminhos (Céu e Terra, guardados pelo Sapo Ancião e pela Serpente Branca) e o torneio contra três
rivais de vilas rivais.

**Ruínas do Clã Marionetista (Chunin, nível 25–50).** Um clã extinto que servia à Vila da Areia
dominava a arte de lutar através de bonecos de guerra. As ruínas do seu templo continuam de pé, os
bonecos ainda "vivos" pela última ordem que receberam, guardadas por sentinelas de pedra e por
espíritos que morreram defendendo o lugar e nunca aceitaram a derrota. Um xamã mantém os selos de
maldição ativos há gerações; e recentemente um gênio desertor, fugindo da própria vila atrás de
poder proibido, escolheu estas ruínas como esconderijo antes de seguir adiante — o mesmo enredo, em
miniatura, da perseguição que toda vila lança atrás dos seus próprios desertores de elite. O
Marionetista das Ruínas, boss principal, é o segundo requisito do Exame Jonin.

**Montanha do Trovão (Jonin, nível 50–80).** A trilha que sobe a montanha é onde jonins provam que
aguentam o próprio peso: águias territoriais, onis que descem do gelo, monges que treinam a vida
toda no penhasco e serpentes que vivem nas fendas de magma. No topo, dois seres amaldiçoados por
um pacto antigo dividem a montanha entre si — um não sabe morrer, o outro cobra um preço por cada
vida que consome — a mesma fantasia da dupla imortal que a Organização Nuvem Vermelha já lançou
contra vilas inteiras durante a Grande Guerra. Ninguém sabe se os dois nasceram assim ou se o
pacto os transformou; o que se sabe é que só caem juntos — matar um sem enfrentar o outro é perder
tempo, o sobrevivente simplesmente absorve a fúria do parceiro morto. Derrotar os dois é a metade
"de campo" do Exame Anbu.

**Covil da Organização Nuvem Vermelha (Anbu/Kage, nível 80–100).** No topo da cadeia de poder do
mundo shinobi está a organização que a Grande Guerra não conseguiu apagar: renegados de capa preta
e nuvens vermelhas, colecionando portadores de poder para um plano que nenhum Kage sozinho
consegue deter. Só quem prova ser Anbu recebe autorização para entrar. Quatro figuras guardam os
corredores, cada uma um espectro de um poder que a vila enfrentou uma vez e nunca mais quis
enfrentar de novo: o olho que prende quem olha demais, o mascarado que puxa os fios de todos os
outros eventos de longe, o portador de olhos em anel que multiplica a própria vontade em vários
corpos, e o ancestral que fundou a própria ideia da organização. Ninguém que entra aqui como
Chunin sai vivo — este é o teste final antes do posto de Kage. Derrotar os dois primeiros fecha o
Exame Anbu; derrotar os dois últimos fecha o Exame Kage e encerra a progressão de rank do jogo
hoje (o posto político de Kage de verdade fica para o pós-jogo, Marco 5).

### Ganchos de saída e a semente da Nuvem Vermelha, arco por arco **(novo, 2026-09-05)**

Resposta à auditoria narrativa (`docs/design/auditoria-historia.md`, achado central: a Nuvem
Vermelha "só aparecia como resposta de quiz na Montanha"): os 4 lotes de história do dia
(`1439749`, `6f0893f`, `006f3c3`, `0dc49a5`) plantam a organização e um gancho de saída (fala de
NPC que empurra o jogador pro próximo arco) em cada um dos 6 arcos, não só no fim:

1. **Floresta da Vila.** O Chefe dos Bandidos, a 50% HP, entrega a semente sem saber o que é:
   *"Essa 'nuvem vermelha' que anda nos vigiando não fui eu quem escolhi, moleque — fui só
   pago."* `done_text` de Capitã Rin (`q_bandit_chief`) já empurra pra Floresta da Morte e Costa.
2. **Costa das Marés.** O Espadachim da Névoa, a 60% HP, revela o Aprendiz Mascarado como algo
   mais que um subordinado: *"ele não luta por dinheiro, luta por mim."* Rastreador Goro e
   Instrutora Ibuki referenciam a mesma prova (matar o Sapo Ancião sozinho, "sem pergaminho em
   jogo, só glória") antes do Exame Chunin oficial cobrar a mesma coisa.
3. **Floresta da Morte.** A Serpente Branca carrega uma fala velada sobre o próprio passado;
   `done_text` da Instrutora Ibuki no fim do Exame Chunin aponta pra Costa (se ainda não visitada)
   e Ruínas.
4. **Ruínas do Clã Marionetista.** O Marionetista, a 15% HP (última fase, `attack_multiplier
   1.5`), revela a organização por nome: *"A Nuvem Vermelha prometeu poder a quem guardasse este
   templo até o fim — e é isso que vou fazer."* Gancho de saída aponta pra Montanha.
5. **Montanha do Trovão.** Mestra Yuki **ensina a resposta antes de perguntar**: o texto de oferta
   de `q_mountain_lore` já entrega a informação ("uma dupla que a Nuvem Vermelha já usou contra
   vilas inteiras, há uma geração, ainda na Grande Guerra") antes do `keyword_quiz` cobrar de
   volta — decisão de design pra não travar o jogador numa pergunta sem pista. O Sócio Eterno
   invoca Serpentes de Magma na fase intermediária (50% HP). Gancho de saída aponta pro Covil.
6. **Covil da Nuvem Vermelha.** Quiz de fechamento; o Portador dos Seis Caminhos invoca Caminhos
   Invocados, o Ancestral da Nuvem Vermelha invoca um Eco Carmesim e revela a Grande Guerra por
   nome na última fase: *"A Grande Guerra nunca terminou. Só mudou de nome."* Falas de
   encerramento e a promoção a Kage fecham a progressão de rank.

Validado in-game nos 2 playtests de história do dia (`docs/qa/playtest-historia-arcos1-3.md`,
`-arcos4-6.md`): todas as falas de fase e `done_text` acima foram vistas em tela, não só no dado.

### Mentores e figuras principais

Os poucos looktypes de personagem principal (900–926, ver seção 9) que aparecem fora dos 9
personagens jogáveis são reservados a **mentores** e aos **bosses de arco de verdade** — nunca a
um monstro comum. Mestre Hayato (mestre de pergaminhos da Vila da Folha), Capitã Rin (dá as
primeiras missões), Instrutora Ibuki (proctora do Exame Chunin) e Capitã Anbu Suzu (guia a prova
final no Covil) são as quatro presenças humanas que acompanham o jogador do início ao fim — ver
tabela completa na seção 8.

---

## 3. O jogador

*Fontes: `data/villages.json`, `data/characters.json`, `data/element_sets.json`, `data/skills.json`,
`data/ranks.json`, `data/progression.json`, `docs/sistemas/vilas-e-clas.md`,
`docs/sistemas/combate-e-jutsus.md`, `docs/lore/progressao.md`.*

### Vilas = vocações

A vila é escolhida na criação e define cidade inicial, NPCs, elemento "de referência" e uma skill
que sobe 20% mais rápido — mas **não filtra mais jutsu** (ver "4+4" abaixo).

| Vila | Elemento de referência | Skill bônus (+20%) | Jutsu inicial (herdado, cosmético) |
|---|---|---|---|
| Vila da Folha | Katon | Taijutsu | Katon: Grande Bola de Fogo |
| Vila da Névoa | Suiton | Ninjutsu | Suiton: Projétil de Água |
| Vila da Nuvem | Raiton | Shuriken | Raiton: Agulha de Raio |
| Vila da Areia | Fuuton/Doton | Defesa | Fuuton: Lâmina de Vento |

A Areia é a única vila com bônus defensivo em vez de ofensivo, e a única que cobre dois elementos
— no ciclo elemental (Katon > Fuuton > Raiton > Doton > Suiton > Katon), ela é forte contra Raiton
(via Fuuton) e contra Suiton (via Doton), a vila mecanicamente mais flexível.

### Personagens (9) e seus 4 jutsus pessoais

Ao entrar no jogo, o jogador escolhe um **personagem** (identidade fixa, looktype 900–909) e um
**elemento** (livre, não travado pela vila). Cada personagem tem exatamente 4 jutsus pessoais —
taijutsu, armas, selos, visão — que não mudam com o elemento escolhido:

| Personagem | Vila | Elemento padrão | Jutsus pessoais |
|---|---|---|---|
| Genin Laranja | Folha | Fuuton | Clone Sombrio, Kawarimi no Jutsu, Rasteira de Vento Leve, Vigor Teimoso |
| Genin Uchiha | Folha | Katon | Foco Ocular, Agulhas Incendiárias, Contra-Ataque Calculado, Kawarimi no Jutsu |
| Kunoichi Rosa | Folha | Suiton | Shousen: Palma Curativa, Punho Suave, Soco Monstruoso, Kawarimi no Jutsu |
| Herdeira Hyuga | Névoa | Suiton | Palma Gentil, Fuuin: Selo de Contenção, Visão de Alcance Total, Palma Dupla |
| Kunoichi das Armas | Névoa | Suiton | Agulhas Múltiplas, Lâmina de Chakra, Doku: Névoa Venenosa, Bunshin no Jutsu |
| Ninja Verde | Nuvem | Raiton | Punho Suave, Chute Giratório, Soco da Juventude, Chute Ascendente |
| Ninja Abelha | Nuvem | Raiton | Lâmina Relâmpago, Corte Duplo, Bainha Elétrica, Raio Selado |
| Sábio Loiro | Areia | Fuuton | Kawarimi no Jutsu, Kunai Marcada, Salto do Selo, Explosão do Selo |
| Sábio Cerimonial | Areia | Doton | Fuuin: Selo de Contenção, Barreira Protetora, Selo de Exorcismo, Círculo de Selos |

`kawarimi`, `punho_suave` e `fuuin_contencao` aparecem em até 2 personagens cada — movimentos
genéricos o bastante (substituição, golpe de chakra, selo de papel) para caber em identidades
diferentes sem quebrar a fantasia de nenhuma delas.

### 5 elementos e seus 4 jutsus (`data/element_sets.json`)

Cada elemento tem um kit fixo de 4 jutsus na mesma ordem estrutural — **projétil básico → área/cone
→ beam/linha forte → utilitário** — igual para qualquer personagem que o escolha:

| Elemento | Projétil básico | Área/cone (ou controle rápido) | Beam/linha forte | Utilitário |
|---|---|---|---|---|
| Katon (Fogo) | Grande Bola de Fogo | Flores de Fênix | Dragão de Fogo | Anel de Chamas |
| Suiton (Água) | Projétil de Água | Névoa Cortante | Dragão de Água | Prisão de Água |
| Raiton (Raio) | Agulha de Raio | Corrente Estática | Lança do Relâmpago | Punho do Trovão |
| Doton (Terra) | Bala de Lama | Estacas de Terra | Colapso do Terreno | Muralha de Pedra |
| Fuuton (Vento) | Lâmina de Vento | Rajada Cortante | Tornado Cortante | Redemoinho Prisão |

### O modelo 4+4 sem aprendizado

Decisão de design central do jogo (substitui "aprender jutsu por level/vila"): ao escolher
personagem + elemento, o jogador recebe **imediatamente os 8 jutsus, já no nível máximo** — sem
cooldown de aprendizado, sem pergaminho, sem grind de desbloqueio. A progressão deixa de ser
"aprender jutsu novo" e passa a ser **treino físico**: level e as 5 skills sobem a fórmula de dano
dos mesmos 8 jutsus, nunca desbloqueiam um jutsu adicional. Pergaminhos e drops raros continuam
existindo para os jutsus que ficaram **fora** do kit automático (ex.: `katon_sopro_brasas`,
`suiton_vortice_devorador`) — bônus opcional, não parte do combo principal. Troca de elemento está
fora do MVP (mesma regra de "troca de vila"); troca de personagem existe hoje como comando de GM
(`!personagem`).

### Ranks: Genin → Chunin → Jonin → Anbu → Kage

*Fonte: `data/ranks.json`, `docs/lore/progressao.md`.* O rank é uma camada narrativa e de exame
por cima do level — o level continua sendo a progressão numérica de sempre, o rank é o que exige
que o jogador **prove** competência, não só grinde até o número certo.

| Rank | Nível mínimo | Como se promove | Bônus de status | Áreas liberadas |
|---|---|---|---|---|
| Genin | 1 | rank inicial, sem exame | — | Floresta da Vila |
| Chunin | 20 | Exame Chunin: prova teórica (quiz por palavra-chave) → 2 pergaminhos (matar Sapo Ancião e Serpente Branca) → torneio (3 rivais em sequência) | +30 HP, +15 Chakra | Floresta da Morte, Costa das Marés, Ruínas do Clã |
| Jonin | 50 | Exame Jonin: vencer o Espadachim da Névoa (Costa) **e** o Marionetista das Ruínas — 2 quests independentes, sem ordem entre si | +80 HP, +40 Chakra, +5 defesa | Montanha do Trovão |
| Anbu | 80 | Exame Anbu: vencer a Dupla Imortal da Montanha (Sócio Eterno + Oni Ancestral) **e** os 2 primeiros guardiões do Covil (Vigia Ilusório + Mascarado das Sombras) | +150 HP, +70 Chakra, +10 defesa | Covil da Nuvem Vermelha |
| Kage | 100 | Exame Kage: vencer os 2 últimos guardiões do Covil (Portador dos Seis Caminhos + Ancestral da Nuvem Vermelha) | +300 HP, +70 Chakra, +20 defesa | — (fim da progressão de rank) |

O gate de rank existe fisicamente no mapa (actionids 45001–45005 em tiles de entrada de região,
ver seção 5) e é checado no servidor (`NarutoRanks.canEnter`) — um jogador sem o rank exigido é
barrado com mensagem e teleportado de volta, testado in-game (`docs/sistemas/mapas.md`, "Mapa v3").

### Skills (sobem com uso, não com pontos)

*Fonte: `data/skills.json`.* Cinco skills, todas começam em **10** e vão até **150**: Taijutsu
(dano físico melee), Shuriken (dano físico à distância), Ninjutsu (dano de jutsu), Genjutsu
(duração/chance de efeitos de status) e Defesa (reduz dano recebido). Cada acerto relevante dá 1
"tentativa"; pontos necessários para subir seguem `50 * 1.1^(skill - 10)` — a mesma curva usada
para calibrar o magic level real (ver "Balanceamento" na seção 5). A skill bônus da vila sobe 20%
mais rápido que as demais (`village_bonus_multiplier: 1.2`).

### Chakra

*Fonte: `data/progression.json`, atualizado na rodada 5 de balanceamento e reajustado de novo na
rodada 7 (`docs/sistemas/balanceamento-relatorio-v7.md`).* `Chakra máximo = 100 + level*10` (era
`50 + level*10` — o piso de chakra inicial do Genin subiu de 60 para 110 no primeiro login).
Regen passivo **escala com level** desde a rodada 5 (era fixo, 0,6 chakra/s em qualquer nível):
`3 + level÷4` a cada 2s — um Genin L1 recupera o pool inteiro parado em ~73s; um Kage L100,
em ~79s. Os 5 jutsus tier 1 elementais (o projétil básico de cada elemento) custam uma
**porcentagem do chakra máximo** — **12–14% desde a rodada 7** (era 2,5–3,0% nas rodadas 5/6):
o playtest r5 (`docs/qa/playtest-l1-20-r5.md`) mediu ao vivo que com 2,5–3,0% o chakra nunca saía
de 108-110/110 em 9 casts seguidos no L1 (a regen entre casts, com cooldown 9,0s, já era maior
que o próprio custo) — a rodada 7 escalou os 5 valores ~4,7× (proporção relativa entre elementos
preservada) pra fechar a meta de 6-8 casts por pool cheio (era 36-55) sem tocar cooldown/regen.
**Cooldown do tier 1 subiu de 9,0s para 27,0s na rodada 8** (o custo percentual em si não mudou,
continua 12-14% do pool, mantendo os 6-8 casts/pool do Genin L1): o modelo antigo do build
híbrido (`HYBRID_JUTSU_CADENCE_FRAC=0,22`, uma cadência artificialmente esticada só pro híbrido)
foi substituído por "castar o tier 1 sempre que o cooldown libera e tem chakra" — o jeito que um
jogador de verdade joga híbrido — e no cooldown real de 9,0s isso tornava o híbrido forte demais
contra boss (até -45% de TTK vs. o melhor build puro); o cooldown subiu pra 27,0s pra manter o
híbrido ≤+15% (ver `docs/sistemas/balanceamento-relatorio-v8.md` §2). **Achado importante, não
fechado**: mesmo com o modelo novo, a meta de 15-25% de tempo sem chakra numa hunt híbrida
continua em 0% em todos os níveis — o custo que criaria essa pressão de recurso (≈3-5× o atual)
quebraria a meta "Genin L1 6-8 casts/pool" (cai pra 1 cast/pool), um conflito estrutural entre as
duas metas, não uma questão de achar o número certo (relatório v8 §2). Pílulas de chakra
(pequena/média/grande, ver seção 5) continuam o lever real de combate para estender uma rotação
de jutsus tier 2/3 (custo fixo, inalterado) numa luta longa.

**Rodada 9 (mudança de FILOSOFIA, não só de número)**: o orquestrador **rejeitou** o cooldown de
27,0s ("um jutsu por meio minuto destrói a sensação de ninja") — voltou pra **9,0s**. E rejeitou
o próprio teto "híbrido ≤+15%" que motivou os 27,0s: no Tibia (e aqui) jogar com arma + magia
junto é o jogo normal, não uma exceção a conter. **O híbrido passa a ser o build de referência**
— monstros/XP/progressão calibrados pelo TTK híbrido; taijutsu/ninjutsu puros só precisam ser
**viáveis** (≥70% do DPS híbrido em todo nível 5-100, ≥60% nos 6 bosses de referência), não mais
"perto do híbrido". A meta de chakra sem pílula (10-35%, todo nível) continua sem fechar — ver
`docs/sistemas/balanceamento-relatorio-v9.md` §5.

---

## 4. Jornada do jogador

*Fonte: `docs/sistemas/progressao-jogador.md` (traduz `data/progression.json` e
`docs/sistemas/balanceamento-relatorio*.md` em guia prático). Curva Tibia-like de propósito: rápida
no início, cada vez mais lenta perto do fim — a maior parte das ~1000 horas totais fica concentrada
nos últimos 20 níveis, não distribuída igualmente pelos 100. As horas por bloco vêm de uma curva de
eficiência de caça que cai com o nível (mais HP de monstro, bosses de cooldown longo, exames que
exigem preparo) — o XP/h da tabela é resultado, não um valor arbitrado à parte.*

| Nível | Onde caçar | XP/h esperado | Horas do bloco | Horas acumuladas | Missões / tarefas | Equipamento a ter |
|---|---|---|---|---|---|---|
| 1–5 | Floresta da Vila: Lobo, Cervo (opcional) | ~536 | 2,8 h | 2,8 h | `q_wolves_1` · `q_forest_snakes` · `task_wolf_1` | Kit de genin: bandana, colete, calça, sandálias, kunai/shuriken de ferro, amuleto da Academia |
| 6–10 | Floresta da Vila: Bandido, Bandido Arqueiro | ~1290 | 3,1 h | 5,9 h | `q_bandits_1` · `q_bandit_archers` · `q_forest_supplies` · `task_bandit_1/2` | Tanto de aço (8), luvas de taijutsu (10) |
| 11–15 | Floresta da Morte: Sanguessuga, Sapo Gigante · Costa: Mercenário da Ponte | ~1757 | 3,7 h | 9,6 h | `q_leeches` · `q_coastal_mercenaries` · `q_coastal_supplies` · `task_leech_1` | Set do Batedor completo (capuz, calça, colete, botas, senbon, bracelete) |
| 16–20 | Costa: Batedor da Névoa, Guardião da Neblina · Floresta da Morte: Ninja Renegado, Serpente Menor | ~1837 | 4,9 h | 14,5 h | `q_coastal_scouts/guardians` · `q_lesser_serpents` · início do **Exame Chunin** | Preparar troca pro set Chunin; poções médias no cinto |
| 21–25 | Floresta da Morte: rivais do exame, Sapo Ancião, Serpente Branca | ~1716 | 6,7 h | 21,2 h | `q_forest_death_collect` · `q_elder_toad_hunt` · `q_rogues` · `q_white_serpent` · **fecha o Exame Chunin** | Set Chunin completo: colete, bandana, calça, sandália, katana Ronin, fuuma shuriken, anel de chakra |
| 26–30 | Ruínas: Marionete de Combate | ~1522 | 9,2 h | 30,4 h | `q_ruins_intro` · `q_ruins_puppets` · `task_ruin_puppet_1/2` | Set das Ruínas completo (máscara, robe, greaves, botas, kodachi/chain kunai, amuleto do selo) |
| 31–35 | Ruínas: Sentinela de Pedra | ~1320 | 12,5 h | 42,9 h | `q_ruins_sentinels` · `task_stone_sentinel_1` | Puppet Blade; anel da Vontade de Pedra |
| 36–40 | Ruínas: Guerreiro Espectral | ~1145 | 16,6 h | 59,5 h | `q_ruins_curse_lore` (quiz) · `task_spectral_warrior_1` | Começa a droppar o set "Rastreador Sombrio" (L40) |
| 41–45 | Ruínas: Xamã da Maldição | ~991 | 21,7 h | 81,2 h | `q_ruins_shamans` · `task_curse_shaman_1` | Set Rastreador Sombrio completo |
| 46–50 | Ruínas: Desertor de Elite, Marionetista das Ruínas — fecha metade do **Exame Jonin** | ~860 | 27,9 h | 109,1 h | `q_ruins_deserter` · `q_ruins_boss` · `task_elite_deserter_1` · `task_boss_puppeteer_1` | Set de Jonin (máscara Anbu, colete, calça, botas, tanto/senbon, bracelete) |
| 51–55 | Montanha: Águia do Trovão | ~755 | 35,1 h | 144,2 h | `q_mountain_eagles` · `q_mountain_relics` · `task_thunder_eagle_1` | Fechar set de Jonin; guardar ryo pro set stormcaller (L60) |
| 56–60 | Montanha: Oni da Geleira | ~667 | 43,5 h | 187,7 h | `q_mountain_oni` · `task_glacier_oni_1` | Set stormcaller completo |
| 61–65 | Montanha: Oni da Geleira (tarefa tier 2), rotação | ~593 | 53,1 h | 240,8 h | `task_glacier_oni_2` | Manter stormcaller; anel ancestral se já caiu |
| 66–70 | Montanha: Monge da Tempestade, O Sócio Eterno | ~530 | 64,1 h | 304,9 h | `q_mountain_serpents` (início) · `q_mountain_lore` (quiz) · `q_mountain_curse_partner` · `task_storm_monk_1` | Começa a droppar "Caçador de Onis" (L70); kanabo de oni |
| 71–75 | Montanha: Serpente de Magma | ~478 | 76,4 h | 381,3 h | `q_mountain_serpents` · `task_magma_serpent_1` | Set Caçador de Onis completo |
| 76–80 | Montanha: Oni Ancestral — fecha metade "de campo" do **Exame Anbu** | ~433 | 90,1 h | 471,4 h | `q_mountain_boss` · `task_boss_ancestral_oni_1` | Oni Fang Blade; começa a droppar "Anbu Negro" (L80) |
| 81–85 | Covil: Clone Branco, O Vigia Ilusório | ~394 | 105,4 h | 576,8 h | `q_lair_intro` · `q_lair_1_illusive_eye` | Set Anbu Negro completo |
| 86–90 | Covil: Ninja Elite da Aurora, O Mascarado das Sombras | ~360 | 122,1 h | 698,9 h | `q_lair_guards` · `q_lair_2_masked_puppeteer` | Começa a droppar "Aurora Carmesim" (L90) |
| 91–95 | Covil: O Portador dos Seis Caminhos | ~331 | 140,5 h | 839,4 h | `q_lair_3_rings_bearer` · `task_boss_rings_bearer_1` | Set Aurora Carmesim completo |
| 96–100 | Covil: O Ancestral da Nuvem Vermelha — fecha o **Exame Kage** | ~305 | 160,6 h | **1000,0 h** | `q_lair_4_crimson_ancestor` · `task_boss_crimson_ancestor_1/2/3` | Set do Kage (fim de progressão): chapéu, manto, calça, sandálias, lâmina/leque, anel do Kage |

### Leitura da curva

- **Blocos 1–4 (nível 1–20, ~14,5 h acumuladas):** XP/h **sobe** (536 → 1837) — o jogador ganha
  eficiência de combate (jutsus tier 1, primeiro equipamento) mais rápido do que o custo de XP por
  nível sobe. É a única parte do jogo em que XP/h cresce; funciona como rampa de aprendizado.
- **Blocos 5–10 (nível 21–50, +88 h no meio do jogo):** XP/h cai de forma constante (1716 → 860)
  conforme o HP de monstro cresce mais rápido que o dano do jogador recém-equipado.
- **Blocos 11–16 (nível 51–80, +327 h):** a Montanha do Trovão é a fase mais longa em horas
  absolutas — monstros tanque/ranged, bosses de cooldown longo (7200s) e o próprio requisito
  narrativo do Exame Anbu desaceleram XP/h de 755 para 433.
- **Blocos 17–20 (nível 81–100, +423 h — 42% do jogo inteiro nos últimos 20 níveis):** o Covil da
  Nuvem Vermelha é deliberadamente a parede final. Só 2 monstros comuns e 4 bosses de respawn
  10800s sustentam a região inteira — o análogo direto do "grind de nível 100+" de Tibia.

A fórmula de XP em si (`50*level² + 50*level`) **não foi alterada** para produzir essa curva — o
ajuste inteiro está nas horas-por-bloco esperadas (eficiência de caça), não no expoente da fórmula.

### Costa das Marés não exige mais Chunin (Lote M, `0dc49a5`)

A tabela acima já reflete a ordem pretendida da história (Costa jogável nos blocos 11–20, antes do
Exame Chunin fechar no bloco 21–25) — mas até o Lote M de hoje o gate físico da região (actionid)
exigia rank **Chunin**, um paradoxo que trancava a Costa atrás do próprio exame que ela deveria
preceder (achado #1 da auditoria narrativa). Corrigido em `build_regions.py::build_coastal_tides`:
o gate trocou de `"chunin"` (45002) para `"genin"` (45001, novo) — como todo jogador já nasce
Genin, o item físico continua na entrada (mesma posição, mesma placa reescrita como sugestão de
nível, não requisito) mas nunca mais barra ninguém. `data/ranks.json` ainda lista
`costa_das_mares` em `unlocks.areas` do rank Chunin — dado órfão que só afeta o comando de debug
`/sl canenter`, não o gate real (ver `docs/sistemas/mapas.md`, "A1").

---

## 5. Sistemas

*Fontes: `docs/sistemas/combate-e-jutsus.md`, `docs/sistemas/balanceamento.md`,
`docs/sistemas/balanceamento-relatorio-v3.md`, `docs/sistemas/monstros-e-pvm.md`,
`docs/sistemas/itens-e-equipamentos.md`, `docs/sistemas/economia.md`,
`docs/sistemas/progressao-servidor.md`, `docs/sistemas/mapas.md`,
`docs/sistemas/personagem-e-progressao.md`, `docs/sistemas/vilas-e-clas.md`.*

### Combate (fórmulas)

O fluxo de um ataque: o jogador seleciona alvo ou mira um jutsu → o sistema checa alcance, linha de
visão, cooldown e chakra → calcula e aplica o dano → dispara efeitos de status (queimadura,
lentidão, etc.). Em prosa, as fórmulas de referência do protótipo (ainda a base conceitual das
fórmulas reais do TFS) são:

- **Dano físico** = (ataque da arma + metade da skill relevante) × um fator aleatório entre 0,8 e
  1,0, menos metade da defesa do alvo. Crítico: 5% de chance, 1,5× dano.
- **Dano de jutsu** = (dano base do jutsu + level × escala de nível + skill de Ninjutsu × escala de
  skill) × multiplicador elemental × fator aleatório entre 0,9 e 1,1.
- **Defesa do alvo** = soma da defesa dos itens equipados + skill de Defesa × 0,3.
- Dano mínimo é sempre 1.

**Elementos** seguem um ciclo circular de vantagem: Katon > Fuuton > Raiton > Doton > Suiton >
Katon (vantagem ×1,5, desvantagem ×0,75, neutro ×1,0).

**HP e XP de monstro** seguem curvas próprias calibradas contra os monstros que já existiam:
`hp_base(L) = 20 * L * (1 + (L-20)/100)`, multiplicado por um fator de papel (normal 1,0 · tanque
1,4 · rápido 0,85–0,9 · ranged 0,75–0,8 · boss 7–8×). O XP usa um `ratio` que **cai** com o nível
(0,40–0,70 em L1–20 até 0,60 em L66–80, boss sempre 1,2) para manter o alvo de 4–7 kills por nível
mesmo com o HP crescendo mais rápido que a XP necessária.

**Balanceamento entre taijutsu (arma) e ninjutsu (jutsu)**, medido por simulação Monte Carlo
(`tools/balance/sim.py`) contra 6 bosses de referência (um por região): depois de cinco rodadas
de calibração, **os 6 de 6 bosses** ficam dentro da meta de paridade (-15%/+10%) entre um build
de arma pura e um de jutsu puro (rodada 5 fechou os 2 últimos que faltavam, L12/L19, trocando o
cooldown do tier 1 de 3,5s para 9,0s — ver `docs/sistemas/balanceamento-relatorio-v5.md` §2/§3).
O burst do tier 1 (hit ≥1,3× o hit médio de arma do mesmo nível) fecha em 94 dos 100 níveis
(L1-77, L83-99) — os 6-9 níveis restantes (L78-84, L100) ficam 9-11% abaixo do alvo por um
limite matemático real: o dano de arma cresce como um PRODUTO skill×attack (super-linear,
~136× de L1 a L100), o dano de jutsu só pode crescer como uma SOMA level+magic-level (linear +
côncavo) — nenhum coeficiente fecha as duas pontas do range ao mesmo tempo sem quebrar a
paridade de boss no meio (prova completa no relatório v5 §2). O build híbrido (arma+jutsu
juntos) fica dentro do teto de +15% sobre o melhor build puro nos **6 de 6** bosses de
referência — fechado na rodada 6 com um parâmetro de modelo artificial (o híbrido só "acertava
o timing" de castar numa fração das janelas livres, cadência esticada ~4,5×) que a rodada 8
substituiu pelo modelo real ("castar o tier 1 sempre que libera e tem chakra", cooldown sem
esticamento — ver `docs/sistemas/balanceamento-relatorio-v8.md` §2); manter o teto de +15% com
o novo modelo exigiu subir o cooldown do tier 1 de 9,0s para 27,0s (o custo percentual em si
ficou igual). **A rodada 9 rejeitou essa escolha**: o cooldown voltou a 9,0s e o teto de +15%
foi removido de vez — o híbrido é agora o build de REFERÊNCIA (calibra monstro/XP/progressão),
e os builds puros só precisam ficar ≥70% do DPS híbrido (todo nível 5-100) / ≥60% (nos 6
bosses). Achado real da rodada 9: **≥60% nos bosses fecha** (3 dos 6 bosses de referência
tiveram a armadura reduzida — a armadura mitiga só o dano de arma, não o de jutsu elemental,
então baixá-la ajuda desproporcionalmente quem depende só de arma); **≥70% nos níveis comuns
NÃO fecha em 64 de 96 níveis** (pior caso 46,3% em L16) — provado como tensão estrutural real
com o burst ≥1,3×, não falta de tuning (ver `docs/sistemas/balanceamento-relatorio-v9.md` §4.3).
Os 5 elementos ficam entre si dentro de **±0,3%** de dano em
L50–100 (números de dano dos jutsus "campeão" de cada elemento não mudaram na rodada 5) — bem
mais apertado que a meta de ±10% pedida. Uma tensão real e documentada permanece sem solução
fechada no cenário de GRUPO (3+ monstros): o mesmo número de dano que faz um jutsu tier 3
competir contra um boss de milhares de HP também consegue **apagar um pull inteiro de monstros
de HP baixo** num único cast — ver `docs/sistemas/balanceamento-relatorio-v3.md` §6/§10 e
`-v4.md` §10 para as opções de correção consideradas e por que nenhuma foi aplicada sem uma
decisão de design explícita (fora do escopo declarado da rodada 5, que focou em economia de
chakra e paridade 1×1). Nos pulls de 3 monstros medidos (`ruin_puppet` L27, `thunder_eagle`
L54), ninjutsu foi recolocado em +30-60% sobre taijutsu na rodada 8 ajustando os jutsus de
área/beam tier 2/3 (`katon_anel_chamas`, `fuuton_rajada_cortante`/`fuuton_tornado_cortante`),
não o tier 1 — ver relatório v8 §3. O pull de `wolf` (L2, n=3) fica bem fora dessa faixa
(nenhum jutsu de área existe ainda nesse nível — só o projétil tier 1), um limite estrutural
do início de jogo, não corrigido.

### Regeneração natural (HP e chakra)

*Fonte: `docs/04-setup-ot.md` ("Notas de QA"), `docs/sistemas/balanceamento-relatorio-v4.md` §1,
`-v5.md` §1, `docs/qa/playtest-l1-20-r3.md`.* No TFS 1.4.2 puro, HP/chakra só regeneram com comida.
Este jogo aplica no login (`character_switch.lua`, gerado) uma `Condition(CONDITION_REGENERATION)`
**permanente** (subId 9020, nunca expira, independe de comida) com valores por vocação — não é uma
condição temporária, e não é suspensa em combate por nenhum código do projeto. Desde a rodada 5 de
balanceamento os valores **escalam com o level do próprio jogador** e são recalculados/reaplicados
a cada level-up (`NarutoRegen.apply`, chamado no login e em `CreatureEvent NarutoRegenAdvance`,
mesmo padrão de `NarutoAchievementAdvance`): chakra `3 + level÷4` a cada 2s, HP `2 + level÷10` a
cada 5s (antes da rodada 5: fixo, 3 chakra/2 HP a cada 5s, igual em qualquer nível). Achado real de
playtest (rodada 3, `playtest-l1-20-r3.md`): mesmo com a condição regenerando corretamente, um spot
de caça muito populoso (ex. a Trilha dos Lobos antes da redução de densidade) pode manter o
jogador "em combate" por minutos seguidos, mascarando a percepção de regen — não é um bug de
chakra, é o efeito esperado de ficar perto de monstros o tempo todo.

### Jutsus: papéis

Cada elemento segue a mesma estrutura de 4 papéis (ver seção 3 e tabela completa na seção 7):

- **Burst à distância** (projétil básico, tier 1) — o pão-com-manteiga de qualquer build.
- **Área/controle** — cone ou cruz, geralmente carrega um efeito de status (lentidão, paralisia).
- **Burst forte em linha** (beam, tier 2/3) — o "carro-chefe" de dano do elemento em nível alto.
- **Utilidade** (defensivo, cura ou controle single-target) — o que sustenta uma luta longa.

### Monstros: comportamento e bosses

Quatro categorias de `behavior`: **agressivo** (persegue e ataca sozinho), **passivo** (só briga se
atacado — hoje só o Cervo), **covarde** (foge abaixo de 20% HP) e **à distância** (mantém alcance,
atira). Bosses têm `phases`: gatilhos por % de HP que disparam fala, invocação de reforços ou
transformação visual (`looktype`). O TFS 1.4.2 não deixa reescrever a lista de ataques/spells de um
monstro em runtime (lida uma única vez do XML no carregamento) — mas desde hoje (`87c19a1`) a
"fase de fúria" multiplica dano de **verdade**, não só cura+velocidade como antes: o
`attack_multiplier` de uma fase publica um estado (`NarutoBossPhases`) que o `CreatureEvent
onHealthChange` do **jogador** (não do monstro — é o jogador que recebe o evento quando o boss
acerta nele) lê para multiplicar `primaryDamage`/`secondaryDamage` de verdade antes do dano ser
aplicado (`NarutoBossFury`, `server/generated/scripts/naruto/boss_phases.lua`), cobrindo dano
melee e de spell do boss por igual. Summons invocados na fase não herdam o multiplicador — só o
boss original. Cura percentual e aumento de velocidade continuam valendo em cima disso (mais
golpes por minuto). Testado em 19 casos headless (`tools/tests/test_boss_fury_headless.lua`,
`tools/tests/run_boss_fury_tests.sh`). Exemplo completo: a **Serpente Branca** (L25, 4600 HP) tem
3 fases — forma humana (ataque com veneno), transformação em serpente 2×2 a 60% de vida (invoca 3
Cobras da Floresta) e fúria a 25% (`attack_multiplier 1,45`, recalibrado na rodada 8 — era 1,9
quando o multiplicador de dano ainda não tinha efeito real: dano real ×1,45 + cura pontual +4,5%
+ velocidade, invoca 2 Serpentes Menores). `tools/balance/sim.py` passou a modelar
`phases[].attack_multiplier`/`summons` (rodada 8: dano do boss ×mult a partir do `hp_percent` da
fase, summons como DPS extra simplificado — ver `docs/sistemas/balanceamento-relatorio-v8.md` §1)
e a recalibração confirmou os 12 bosses com fase de fúria dentro de 1,3×-1,8× de dano recebido/s
(fase final vs. fase 1) e `death_rate` 0% (taijutsu solo, com poções, no level-alvo) — só a
**Serpente Branca** precisou de ajuste (1,9→1,45, único fora da faixa).

### Itens, tiers, loot e economia

*Fonte: `docs/sistemas/itens-e-equipamentos.md`, `docs/sistemas/economia.md`.* 173 itens em
`data/items/*.json`: armas (melee/ranged), armaduras (head/body/legs/feet), acessórios, consumíveis,
pergaminhos (ensinam jutsus fora do kit automático), materiais e a moeda **ryo**. Cinco raridades
(comum/incomum/raro/épico/lendário). Mochila base de 20 slots + peso (`100 + level*5` de
capacidade). Cada set de armadura é dimensionado por faixa de nível (L1, 10, 20, 30... até 100),
acompanhando a jornada da seção 4. Economia: ryo cai de monstro (~N×3 em média) e é ganho vendendo
loot a NPC (que compra por ~40% do preço de venda); pergaminhos custam de ~500 (tier 1) a
20.000–45.000 (tier 3, variando por elemento/level).

### Missões (motor v2, `184de6f`)

*Fonte: `docs/sistemas/missoes.md`.* O motor de missões ganhou 4 tipos novos de
`objective.kind` (era 2: `kill`, `keyword_quiz`) sem mudar o comportamento das 45 missões já
escritas — todo campo novo é opcional com fallback pro texto/comportamento de sempre:
`collect_item` (com drops condicionais), `talk_to` universal, `reach` (posição no mapa, checada
por poll a cada 7s) e `kill` com `any_of`/`boss`. Além disso: pré-requisitos cruzados entre
missões (`requires.quests`) com `locked_text` dedicado, textos condicionados por placeholders
(`{player}`, `{count}`, `{needed}`), e recompensas novas (`storage`, `outfit`, `addon`, `title`)
além de xp/ryo/items — progresso aparece ao vivo na aba Missões do Menu Shinobi. 63 testes
headless em luajit com stub do TFS (`tools/tests/test_quests_headless.lua`,
`tools/tests/run_quests_tests.sh`). É a base técnica que os Lotes A/B/C/M usaram para plantar os
ganchos de saída e a Nuvem Vermelha em cada arco (seção 2).

### Tarefas, diárias e conquistas

*Fonte: `docs/sistemas/progressao-servidor.md`, `data/tasks.json`, `data/dailies.json`,
`data/achievements.json`.* **Tarefas** (`data/tasks.json`, 114 entradas — 3 tiers "Iniciante/
Veterana/Lendária" por monstro): repetíveis, com cooldown, dadas por um "Mestre de Tarefas" dedicado
por região; XP de recompensa é expresso como "kills equivalentes" escalados pelo level de quem
entrega (`NarutoRewards.scaledXp`), não um valor absoluto. **Diárias** (`data/dailies.json`, 60
entradas, faixas de 5 em 5 níveis): 3 sorteadas por dia por jogador, auto-aceitas, entregues de uma
vez pelo comando `!diaria`. **Conquistas** (`data/achievements.json`, 55 entradas, 9 categorias:
kill/boss/quest/exam/exploration/collection/task/daily/level) dão título e ryo — ex.: "Viajante de
Floresta da Vila" por só visitar a região pela primeira vez.

Todas as 55 conquistas têm lógica real no servidor desde `e02aa0b`, cobrindo os **10 tipos de
condição** do schema (`docs/sistemas/progressao-servidor.md` §9): `kill_count`/`kill_specific`
(hook direto no `CreatureEvent` de morte), `quest_chain_complete`/`grants_rank`/`level_reached`
(hook direto no evento correspondente — completar quest, promover rank, subir level),
`task_count`/`daily_streak` (hook direto na entrega de tarefa/diária), e três que **não têm evento
nativo no TFS** e por isso rodam por poll periódico (`GlobalEvent NarutoAchievementPoll`, 7s):
`visit_zone` (posição do jogador contra os mesmos retângulos de região usados na hora de construir
o mapa), `collect_set` (conjunto de equipamento vestido) e `collect_item_count` (troféus na
mochila) — latência de até 7s entre a condição ficar verdadeira e a mensagem aparecer, aceitável
para conquista (não é uma checagem de gameplay sensível a frame). Recompensa é só **ryo** (o schema
não tem campo de XP/item); ao desbloquear, o jogador recebe `"Conquista desbloqueada: <nome>!"`,
um efeito visual (`fx_seal_glow`) e o título da última conquista passa a aparecer numa 2ª linha no
`/look`. Comandos: `!conquistas` (resumo por categoria) e `/conquista [id]` (GM, força o
desbloqueio para teste).

### Som

*Fonte: `docs/sistemas/audio.md`, `docs/backlog-audio.md`.* 51 SFX procedurais (síntese
subtrativa/FM em `tools/audio/gen_sfx.py`, sem download de terceiros — ADR-002), cobrindo os 33
`sfx` referenciados em `data/jutsus/*.json` mais 17-18 sons de base (dano recebido, morte de
monstro, level up, item, moeda, UI, conquista). Tocado pelo módulo cliente `naruto_sounds` em 4
ganchos: **(a)** efeito de jutsu visto na tela — opcode estendido 210, ação `"sfx"`
(`NarutoJson.broadcastSfx`, chamado dentro de todo `onCastSpell` gerado); **(b)** level up e
conquista, via `onTextMessage`; **(c)** dano recebido e morte de monstro, via `connect(Creature/
LocalPlayer, {...})`; **(d)** UI (abrir/fechar o Menu Shinobi, clique de botão). Opção "Sons do
jogo" no menu de opções (padrão ligado, volume 100). **Música segue sem trilha própria** — a opção
de música existe no cliente mas fica desligada por padrão (nenhum arquivo além do tema genérico
herdado do OTClient); é o único item de arte/som ainda 100% pendente (ver seção 9).

### Encoding: cp1252 na tela, UTF-8 no protocolo

*Fonte: `docs/sistemas/cliente-ux.md` §5.* Achado do playtest de história dos arcos 4–6
(`docs/qa/playtest-historia-arcos4-6.md`): matar um monstro com nome acentuado (`Águia do
Trovão`, `Xamã da Maldição`, 3 bosses) não contava pra missão, porque o Lua gerado
(`tools/export_tfs.py`) passou a sair em **cp1252** (fim do mojibake nas falas, rodada anterior)
enquanto o nome do monstro chega em tempo real do protocolo em **UTF-8** — a comparação de string
nunca batia. Corrigido em duas camadas hoje: **(1)** `NarutoText.utf8ToCp1252`/`.cp1252ToUtf8`
(servidor, `naruto_json.lua`) normaliza qualquer nome vindo do jogo antes de comparar contra um
literal gerado, usado em missões/tarefas/diárias/conquistas/fases de boss (52 testes headless,
`test_encoding_headless.lua`); **(2)** `InputMessage::getString` (cliente, C++) converte toda
string do protocolo de UTF-8 para cp1252 **na entrada**, por sequência (`stdext::utf8_to_cp1252`,
tolera strings mistas como "Loot of …" onde nome de monstro e de item vêm em encodings
diferentes na mesma mensagem) — fim do mojibake em nomes de NPC, criatura e item na tela, não só
nas falas.

### NPCs e lojas

21 NPCs em `data/npcs/*.json`, um mercador + um dador de missões por região, mais os NPCs novos de
tarefa/exame (ver tabela completa na seção 8). Loja funciona por palavra-chave (`{trade}`, o padrão
do TFS): cada NPC vende uma lista fixa de itens e compra de volta só certos `types` (material/arma/
armadura), nunca itens raros — regra anti-inflação simples (mercado entre jogadores, com taxa,
segue no roadmap).

### Mapa: 6 regiões, gates de rank, coordenadas de entrada

*Fonte: `docs/sistemas/mapas.md`.* Um único OTBM (`server/generated/world/valley.otbm`, cabeçalho
2048×2048, conteúdo real no andar 7) hospeda as 6 regiões — 4 no mundo aberto original (x
1000–1199/y 1000–1119) e 2 construídas depois em `build_regions.py` (x≥1200 ou y≥1120):

| Região | Nível | Coordenadas (x, y, 7) | Gate de rank (actionid) |
|---|---|---|---|
| Floresta da Vila | 1–10 | zona 0,0,50,40 dentro do mundo aberto; templo em 1029,1042 | — (rank inicial) |
| Floresta da Morte | 10–25 | zona 50,0,46,40 | — (Exame Chunin roda dentro dela; gatear a entrada criaria paradoxo) |
| Costa das Marés | 12–19 | x 1000–1049, y 1120–1169 | Chunin (45002), em (1028–1030, 1120) |
| Ruínas do Clã Marionetista | 25–50 | x 1200–1249, y 1000–1049 | Chunin (45002), em (1200, 1020/1021) |
| Montanha do Trovão | 50–80 | x 1200–1249, y 1060–1109 | Jonin (45003), em (1224–1226, 1060) |
| Covil da Nuvem Vermelha | 80–100 | x 1400–1449, y 1000–1049 (masmorra isolada) | Anbu (45004), no portal gated no topo da Montanha (1225,1103) |

O gate é um `MoveEvent` genérico (`rank_gate.lua`) que lê o actionid do **tile** (não de um item) e
barra quem não tem o rank mínimo com mensagem + teleporte de volta — testado in-game com conta sem
rank (barrada) e conta GM (atravessa livre, por design).

### Kit inicial e onboarding

*Fonte: `docs/qa/playtest-l1-20-r2.md`, `-r3.md`, `-r4.md`.* O TFS vanilla entrega um kit próprio
no primeiro login via `creaturescripts/scripts/firstitems.lua` (jaqueta, taco, mochila) que
competia pelos mesmos slots do kit da vila gerado por `character_switch.lua` — achado de playtest
(rodada 2), corrigido neutralizando `firstitems.lua` para só entregar a mochila de couro, deixando
o kit da vila (bandana, colete de genin, calça ninja, sandálias, kunai/shuriken de ferro, amuleto
da Academia) ocupar os 6 slots reais. Confirmado com contas 100% novas via AAC nos 3 playtests
seguintes (r2/r3/r4): kit completo, HP/chakra no teto da vocação já no primeiro login.

### Morte e penalidades

*Fonte: `data/progression.json`, `docs/qa/playtest-l1-20-r3.md`.* Ao morrer: perde 10% da XP do
nível atual (nunca cai de nível) e dropa cada item não equipado da mochila com 30% de chance
independente — os itens ficam no próprio corpo por 60 segundos (estilo Tibia clássico), não somem.
Achado de playtest: morrer **não reposiciona o personagem em tempo real** — o cliente fica
~25-30s parado na tela de morte e cai por timeout de conexão; o jogador precisa logar de novo, e
ao reconectar aparece no templo com HP/chakra cheios e o mesmo inventário (a perda de XP/drop já
foi aplicada no instante da morte, antes da desconexão). Comportamento herdado do TFS clássico, não
um bug — mas vale como nota de UX honesta: um jogador que não souber disso pode achar que travou.

### Social (hoje: nada)

Não existe party, clã, chat de clã ou mercado entre jogadores no jogo hoje — tudo isso está
desenhado (clã a partir de level 30, custo em ryo, até 50 membros, XP bônus 5% em party do mesmo
clã) mas depende do Marco 4/5 do roadmap (seção 11). O jogo de hoje é **PvM solo**, ainda que
tecnicamente multiplayer (o servidor TFS aceita várias conexões desde o primeiro dia).

---

## 6. Bestiário

*Fonte: `data/monsters/*.json` (números), `docs/lore/mundo.md` (região/comportamento narrativo),
`docs/backlog-sprites.md` (status de sprite). 38 monstros no total — 6 regiões, cada uma com
monstros comuns + 1 ou mais bosses.*

| Nome | Região | Nível | HP | XP | Elemento | Comportamento | Loot notável | Sprite (status) |
|---|---|---|---|---|---|---|---|---|
| Lobo (`wolf`) | Floresta da Vila | 2 | 60 | 25 | none | agressivo | Pele de lobo, onigiri, amuleto da Academia | procedural (looktype 940, 4 direções reais) |
| Bandido (`bandit`) | Floresta da Vila | 5 | 120 | 60 | none | agressivo | Emblema de bandido, kunai de ferro, poção pequena | variante de paleta (looktype 956) |
| Cobra da Floresta (`forest_snake`) | Floresta da Vila | 4 | 70 | 45 | doton | covarde (foge) | Presa de cobra | procedural (looktype 943, compartilhado c/ máscara de cor) |
| Bandido Arqueiro (`bandit_archer`) | Floresta da Vila | 7 | 100 | 80 | none | à distância | Emblema de bandido, shuriken de ferro | variante de paleta (looktype 946) |
| Chefe dos Bandidos (`boss_bandit_chief`) | Floresta da Vila | 12 | 1500 | 1500 | katon | **BOSS** — agressivo | Katana Ronin, pergaminho de Shousen, luvas de taijutsu | variante de paleta (looktype 957, P1: falta pose de boss) |
| Cervo (`forest_deer`) | Floresta da Vila | 2 | 30 | 5 | none | passivo | Onigiri | procedural (looktype 941, 4 direções reais) |
| Sanguessuga Gigante (`leech`) | Floresta da Morte | 10 | 180 | 120 | suiton | agressivo | Glândula de sanguessuga, antídoto | procedural (looktype 945, 4 direções reais) |
| Sapo Gigante (`giant_toad`) | Floresta da Morte | 13 | 260 | 180 | suiton | agressivo | Pele de sapo, óleo de sapo, pílula de chakra média | procedural (looktype 944, 4 direções reais) |
| Ninja Renegado (`rogue_ninja`) | Floresta da Morte | 18 | 340 | 300 | none | à distância | Bandana de renegado, katana Ronin, set Chuunin | variante de paleta (looktype 950) |
| Serpente Menor (`lesser_serpent`) | Floresta da Morte | 18 | 340 | 260 | doton | agressivo | Presa de cobra, antídoto | procedural (looktype 943, compartilhado c/ máscara de cor) |
| Sapo Ancião (`boss_elder_toad`) | Floresta da Morte | 25 | 4000 | 5000 | suiton | **BOSS** — agressivo | Anel de chakra, fuuma shuriken, pergaminho Céu, Suiryuudan | importado lateral (looktype 60, 2×2, P1: falta pose de boss) |
| Serpente Branca (`boss_white_serpent`) | Floresta da Morte | 25 | 4600 | 5600 | doton | **BOSS** — agressivo | Presa da Serpente Branca (100%), pergaminho de Doku Kiri, pergaminho Terra | **MUGEN (looktype 916, Sasuke Rinnegan)** — uso intencional (boss de arco), mas viola ADR-002 |
| Rival do Exame — Pedra (`exam_rival_stone`) | Floresta da Morte | 20 | 420 | 260 | doton | agressivo | Poção pequena | importado lateral (looktype 128, P2) |
| Rival do Exame — Som (`exam_rival_sound`) | Floresta da Morte | 20 | 360 | 260 | raiton | à distância | Poção pequena | importado lateral (looktype 129, P2) |
| Rival do Exame — Névoa (`exam_rival_mist`) | Floresta da Morte | 20 | 380 | 260 | suiton | agressivo | Poção pequena | importado lateral (looktype 130, P2) |
| Mercenário da Ponte (`mercenary_bridge`) | Costa das Marés | 12 | 230 | 140 | none | agressivo | Emblema de bandido, poção pequena, bracelete do viajante | variante de paleta (looktype 947) |
| Batedor da Névoa (`mist_scout`) | Costa das Marés | 14 | 260 | 170 | suiton | à distância | Shuriken de ferro, senbon de ferro | variante de paleta (looktype 949) |
| Guardião da Neblina (`mist_guardian`) | Costa das Marés | 16 | 420 | 230 | suiton | agressivo | Poção pequena, capuz do batedor | variante de paleta (looktype 951) |
| Aprendiz Mascarado (`masked_apprentice`) | Costa das Marés | 17 | 650 | 380 | suiton | à distância | Máscara de aprendiz, calça do batedor | importado lateral (looktype 130, P0: falta pose própria) |
| Espadachim da Névoa (`boss_mist_swordsman`) | Costa das Marés | 19 | 1700 | 1700 | suiton | **BOSS** — agressivo | Presa do espadachim, katana Ronin, set Chuunin | importado lateral (looktype 132, P0) |
| Marionete de Combate (`ruin_puppet`) | Ruínas do Clã Marionetista | 27 | 580 | 490 | none | agressivo | Junta de marionete, poção média, chain kunai | variante de paleta (looktype 948, tom madeira) |
| Sentinela de Pedra (`stone_sentinel`) | Ruínas do Clã Marionetista | 32 | 1000 | 850 | doton | agressivo | Núcleo de granito, greaves/botas do Clã Ruínas | importado lateral (looktype 61 "stone_golem", P1) |
| Guerreiro Espectral (`spectral_warrior`) | Ruínas do Clã Marionetista | 38 | 900 | 720 | raiton | agressivo | Cinza espectral, máscara do Clã Ruínas, kodachi | variante de paleta (looktype 953) |
| Xamã da Maldição (`curse_shaman`) | Ruínas do Clã Marionetista | 44 | 870 | 700 | katon | à distância | Talismã amaldiçoado, amuleto do Clã, pergaminho de Estacas de Terra | importado lateral (looktype 138, P1) |
| Desertor de Elite (`elite_deserter`) | Ruínas do Clã Marionetista | 46 | 2600 | 2200 | katon | **BOSS** — agressivo | Selo do desertor, pergaminho de Karyuu Endan | **MUGEN (looktype 915, Sasuke Akatsuki)** — viola ADR-002 |
| Marionetista das Ruínas (`boss_puppeteer`) | Ruínas do Clã Marionetista | 50 | 9100 | 11000 | fuuton | **BOSS** — agressivo | Fios do Marionetista, Puppet Blade, robe do Clã, anel da Vontade de Pedra | importado lateral (looktype 131, idêntico ao Chefe dos Bandidos, P0) |
| Águia do Trovão (`thunder_eagle`) | Montanha do Trovão | 54 | 1160 | 810 | raiton | à distância | Pena do trovão, poção grande, botas stormcaller | procedural (looktype 942, sempre em voo) |
| Oni da Geleira (`glacier_oni`) | Montanha do Trovão | 60 | 2350 | 1650 | suiton | agressivo | Fragmento de gelo, chifre de oni, greaves stormcaller | variante de paleta (looktype 955) |
| Monge da Tempestade (`storm_monk`) | Montanha do Trovão | 68 | 1800 | 1080 | fuuton | agressivo | Pena do trovão, chifre de oni, elmo stormcaller, windblade shuriken | importado lateral (looktype 137, P1) |
| Serpente de Magma (`magma_serpent`) | Montanha do Trovão | 74 | 2280 | 1370 | katon | agressivo | Escama de magma, chifre de oni, Thunder Katana | procedural (looktype 943, compartilhado c/ máscara de cor) |
| O Sócio Eterno (`boss_curse_partner`) | Montanha do Trovão | 70 | 6200 | 7200 | doton | **BOSS** — agressivo | Coração amaldiçoado, pergaminho de Colapso do Terreno | variante de paleta (looktype 954, P1: faltam fases visuais) |
| Oni Ancestral (`boss_ancestral_oni`) | Montanha do Trovão | 80 | 20500 | 24600 | raiton | **BOSS** — agressivo | Oni Fang Blade, mail stormcaller, colar Storm Fang, anel ancestral | **MUGEN (looktype 913, Madara)** — viola ADR-002 |
| Clone Branco (`white_clone`) | Covil da Nuvem Vermelha | 82 | 2700 | 1900 | doton | agressivo | Emblema da Nuvem, set Anbu Negro | importado lateral (looktype 130, P1) |
| Ninja Elite da Aurora (`elite_cloud_guard`) | Covil da Nuvem Vermelha | 88 | 4100 | 2500 | raiton | agressivo | Emblema da Nuvem, poção grande, set Anbu Negro | importado lateral (looktype 129 cru, sem recolor, P1) |
| O Vigia Ilusório (`boss_illusive_eye`) | Covil da Nuvem Vermelha | 85 | 21000 | 25200 | katon | **BOSS** — agressivo | Fragmento de anel carmesim, poção grande, pílula de soldado, set Aurora Carmesim | **MUGEN (looktype 910, Itachi)** — viola ADR-002 |
| O Mascarado das Sombras (`boss_masked_puppeteer`) | Covil da Nuvem Vermelha | 90 | 23500 | 28200 | fuuton | **BOSS** — agressivo | Fragmento de anel carmesim, set Aurora Carmesim, katana | **MUGEN (looktype 912, Obito)** — viola ADR-002 |
| O Portador dos Seis Caminhos (`boss_rings_bearer`) | Covil da Nuvem Vermelha | 95 | 26000 | 31200 | doton | **BOSS** — agressivo | Fragmento de anel carmesim, shuriken Aurora Carmesim, chapéu do Kage | **MUGEN (looktype 911, Pain)** — viola ADR-002 |
| O Ancestral da Nuvem Vermelha (`boss_crimson_ancestor`) | Covil da Nuvem Vermelha | 100 | 29000 | 34800 | raiton | **BOSS** — agressivo | Fragmento de anel carmesim, set completo do Kage (lâmina, leque, anel) | **MUGEN (looktype 913, Madara, reaproveitado)** — viola ADR-002, prioridade máxima |

---

## 7. Grimório de jutsus

*Fonte: `data/jutsus/*.json` (54 jutsus: 5 Katon, 5 Suiton, 5 Raiton, 4 Doton, 4 Fuuton, 10
universais/genéricos, 21 pessoais exclusivos — `data/element_sets.json` decide os 4 "de kit" por
elemento, `data/characters.json` decide os 4 pessoais por personagem, ver seção 3). Tabelas
regeneradas diretamente de `data/jutsus/*.json` (campos `animation`/`sfx` na última coluna) —
custo dos 5 tier 1 atualizado na rodada 7 de balanceamento
(`docs/sistemas/balanceamento-relatorio-v7.md`): os 5 projéteis tier 1 do kit elemental (nível 1,
"burst à distância") custam uma **% do pool de chakra** (`chakra_cost_percent`/`manapercent`) em
vez de um número fixo — **12–14% desde a rodada 7** (era 2,5–3,0% nas rodadas 5/6, ~4,7× mais
caro, ver seção 3 "Chakra") — e o cooldown desses 5 subiu de 2,0s (rodada 3) → 3,5s (rodada 4) →
**9,0s** (rodada 5, valor atual, não tocado nas rodadas 6/7). O resto do jutsu (custo
fixo, cooldown) foi só reescalado pela mudança do pool de chakra (100+level×10, era
50+level×10), sem tocar em dano/papel. Som: cada jutsu já tinha um `sfx` no JSON antes desta
missão; agora o som toca de verdade em jogo (módulo `naruto_sounds`, ver seção 5 "Som").

### Katon (Fogo) (5)

| Nome | Tipo | Custo (chakra) | Cooldown | Nível req. | Papel | Efeito visual (som) |
|---|---|---|---|---|---|---|
| Katon: Grande Bola de Fogo | projectile | 14,0% do pool | 27,0s | 1 | burst à distância (projétil básico, kit) + queimadura | `fx_fireball` · som `sfx_fire_whoosh` |
| Katon: Sopro de Brasas | area | 26 | 3,0s | 6 | área (reserva, fora do kit) + queimadura | `fx_ember_cone` · som `sfx_fire_puff` |
| Katon: Flores de Fênix | area | 136 | 6,0s | 12 | área/cone (kit) + queimadura | `fx_fire_cone` · som `sfx_fire_burst` |
| Katon: Anel de Chamas | area | 176 | 6,0s | 20 | utilitário/área (kit) + queimadura | `fx_fire_ring` · som `sfx_fire_burst` |
| Katon: Dragão de Fogo | beam | 236 | 8,0s | 35 | burst forte em linha (kit) + queimadura | `fx_fire_dragon` · som `sfx_dragon_roar` |

### Suiton (Água) (5)

| Nome | Tipo | Custo (chakra) | Cooldown | Nível req. | Papel | Efeito visual (som) |
|---|---|---|---|---|---|---|
| Suiton: Projétil de Água | projectile | 12,0% do pool | 27,0s | 1 | burst à distância (projétil básico, kit) + lentidão | `fx_water_bullet` · som `sfx_splash` |
| Suiton: Névoa Cortante | area | 22 | 3,0s | 6 | controle de área rápido (kit) + lentidão | `fx_mist_cone` · som `sfx_mist` |
| Suiton: Prisão de Água | target | 45 | 7,0s | 22 | controle/utilitário (kit) + paralisia | `fx_water_prison` · som `sfx_bubble` |
| Suiton: Dragão de Água | beam | 184 | 6,0s | 25 | burst forte em linha (kit, teto do elemento) + lentidão | `fx_water_dragon` · som `sfx_wave` |
| Suiton: Vórtice Devorador | area | 79 | 9,0s | 45 | área (reserva, fora do kit) + lentidão | `fx_water_vortex` · som `sfx_wave` |

### Raiton (Raio) (5)

| Nome | Tipo | Custo (chakra) | Cooldown | Nível req. | Papel | Efeito visual (som) |
|---|---|---|---|---|---|---|
| Raiton: Agulha de Raio | projectile | 13,0% do pool | 27,0s | 1 | burst à distância (projétil básico, kit) + paralisia | `fx_lightning_needle` · som `sfx_zap` |
| Raiton: Corrente Estática | area | 20 | 3,0s | 6 | controle de área rápido (kit) + paralisia | `fx_static_cross` · som `sfx_zap` |
| Raiton: Lança do Relâmpago | beam | 170 | 6,5s | 18 | burst forte em linha (kit, teto do elemento) + paralisia | `fx_lightning_lance` · som `sfx_thunder` |
| Raiton: Armadura Elétrica | self | 42 | 16,0s | 24 | utilitário/buff (reserva, fora do kit) + cura contínua | `fx_lightning_armor` · som `sfx_zap_loop` |
| Raiton: Punho do Trovão | target | 200 | 7,0s | 30 | burst forte single-target (kit) + stun | `fx_thunder_fist` · som `sfx_thunder_hit` |

### Doton (Terra) (4)

| Nome | Tipo | Custo (chakra) | Cooldown | Nível req. | Papel | Efeito visual (som) |
|---|---|---|---|---|---|---|
| Doton: Bala de Lama | projectile | 13,0% do pool | 27,0s | 1 | burst à distância (projétil básico, kit) + lentidão | `fx_mud_bullet` · som `sfx_splat` |
| Doton: Muralha de Pedra | self | 39 | 14,0s | 8 | utilitário/defensivo (kit) + cura contínua | `fx_stone_shell` · som `sfx_rock_rumble` |
| Doton: Estacas de Terra | area | 166 | 6,0s | 22 | área/controle (kit) + paralisia | `fx_earth_spikes` · som `sfx_rock_crack` |
| Doton: Colapso do Terreno | area | 268 | 9,0s | 48 | área forte (kit) + stun | `fx_earth_collapse` · som `sfx_quake` |

### Fuuton (Vento) (4)

| Nome | Tipo | Custo (chakra) | Cooldown | Nível req. | Papel | Efeito visual (som) |
|---|---|---|---|---|---|---|
| Fuuton: Lâmina de Vento | projectile | 13,0% do pool | 27,0s | 1 | burst à distância (projétil básico, kit) | `fx_wind_blade` · som `sfx_wind_cut` |
| Fuuton: Rajada Cortante | area | 147 | 6,5s | 16 | área/cone (kit) + lentidão | `fx_wind_cone` · som `sfx_wind_burst` |
| Fuuton: Redemoinho Prisão | target | 45 | 9,0s | 23 | controle/utilitário (kit) + paralisia | `fx_wind_prison` · som `sfx_wind_trap` |
| Fuuton: Tornado Cortante | beam | 243 | 8,0s | 36 | burst forte em linha (kit) + lentidão | `fx_wind_tornado` · som `sfx_wind_roar` |

### Universais/genéricos (multi-personagem) (10)

| Nome | Tipo | Custo (chakra) | Cooldown | Nível req. | Papel | Efeito visual (som) |
|---|---|---|---|---|---|---|
| Agulhas Multiplas | projectile | 26 | 2,0s | 1 | burst à distância | `fx_needles` · som `sfx_metal_throw` |
| Punho Suave | target | 20 | 2,0s | 3 | single-target/controle + lentidão | `fx_taijutsu_hit` · som `sfx_punch` |
| Kawarimi no Jutsu | self | 30 | 12,0s | 5 | utilitário (substituição, universal) | `fx_log_poof` · som `sfx_poof` |
| Bunshin no Jutsu | self | 35 | 15,0s | 8 | utilitário (invocação de clone) | `fx_clone_poof` · som `sfx_poof` |
| Clone Sombrio | self | 47 | 20,0s | 10 | utilitário/buff | `fx_smoke_puff` · som `sfx_poof` |
| Shousen: Palma Curativa | self | 47 | 10,0s | 10 | cura + cura contínua | `fx_heal_glow` · som `sfx_heal` |
| Chute Giratorio | area | 28 | 4,0s | 14 | área/controle | `fx_taijutsu_spin` · som `sfx_whirl` |
| Lamina de Chakra | beam | 34 | 5,0s | 20 | burst forte em linha | `fx_chakra_blade` · som `sfx_slash` |
| Doku: Névoa Venenosa | area | 54 | 6,0s | 25 | área/veneno (dano ao longo do tempo) + veneno | `fx_poison_mist` · som `sfx_hiss` |
| Fuuin: Selo de Contenção | target | 50 | 12,0s | 40 | controle (selo) + paralisia | `fx_seal_paper` · som `sfx_seal` |

### Pessoais (exclusivos de 1 personagem) (21)

| Nome | Tipo | Custo (chakra) | Cooldown | Nível req. | Papel | Efeito visual (som) |
|---|---|---|---|---|---|---|
| Raio Selado | projectile | 28 | 2,0s | 1 | burst à distância | `fx_lightning_bolt` · som `sfx_zap` |
| Chute Ascendente | target | 27 | 2,5s | 2 | single-target/controle + lentidão | `fx_rising_kick` · som `sfx_kick` |
| Kunai Marcada | projectile | 23 | 2,0s | 3 | burst à distância | `fx_marked_kunai` · som `sfx_metal_throw` |
| Rasteira de Vento Leve | area | 22 | 3,0s | 4 | área/controle + lentidão | `fx_wind_sweep` · som `sfx_wind_cut` |
| Agulhas Incendiárias | projectile | 21 | 2,0s | 5 | burst à distância + queimadura | `fx_burning_needles` · som `sfx_metal_throw` |
| Palma Gentil | target | 24 | 2,0s | 5 | single-target/controle + lentidão | `fx_palm_strike` · som `sfx_punch` |
| Foco Ocular | self | 37 | 14,0s | 7 | utilitário/buff + cura contínua | `fx_eye_glow` · som `sfx_focus` |
| Vigor Teimoso | self | 41 | 18,0s | 9 | utilitário/buff + cura contínua | `fx_aura_orange` · som `sfx_shout` |
| Visão de Alcance Total | self | 30 | 16,0s | 9 | utilitário/buff + cura contínua | `fx_eye_veins` · som `sfx_focus` |
| Lâmina Relâmpago | target | 29 | 2,2s | 10 | single-target/controle + paralisia | `fx_sword_spark` · som `sfx_slash` |
| Salto do Selo | self | 36 | 10,0s | 12 | utilitário/buff | `fx_flash_teleport` · som `sfx_teleport` |
| Barreira Protetora | self | 48 | 18,0s | 14 | utilitário/buff + cura contínua | `fx_barrier_glow` · som `sfx_seal` |
| Contra-Ataque Calculado | target | 25 | 6,0s | 15 | single-target/controle + stun | `fx_counter_strike` · som `sfx_punch` |
| Soco Monstruoso | target | 30 | 4,0s | 16 | single-target/controle + stun | `fx_ground_crack` · som `sfx_heavy_punch` |
| Soco da Juventude | target | 32 | 4,5s | 18 | single-target/controle + stun | `fx_heavy_punch` · som `sfx_heavy_punch` |
| Selo de Exorcismo | target | 41 | 6,0s | 19 | single-target/controle + paralisia | `fx_seal_paper` · som `sfx_seal` |
| Corte Duplo | area | 38 | 4,5s | 20 | área/controle | `fx_double_slash` · som `sfx_slash` |
| Palma Dupla | area | 42 | 5,0s | 24 | área/controle + paralisia | `fx_double_palm` · som `sfx_double_hit` |
| Bainha Elétrica | self | 39 | 16,0s | 26 | utilitário/buff + cura contínua | `fx_lightning_armor` · som `sfx_zap_loop` |
| Círculo de Selos | area | 51 | 8,0s | 27 | área/controle + paralisia | `fx_seal_circle` · som `sfx_seal` |
| Explosão do Selo | area | 53 | 7,0s | 28 | área/controle + stun | `fx_seal_explosion` · som `sfx_explosion` |


---

## 8. Personagens e NPCs

*Fontes: `data/npcs/*.json` (identidade, loja, texto de missão), `docs/lore/mundo.md` (papel
narrativo), `docs/sistemas/mapas.md` "Mapa v3" (posições finais no `.otbm`), `docs/lore/progressao.md`
(exames).*

### Mentores e figuras de rank (looktypes de personagem principal — uso reservado)

| Nome no jogo | Papel | Onde fica | Fala-chave |
|---|---|---|---|
| Mestre Hayato | Mestre de pergaminhos, Vila da Folha (`scroll_master_leaf`) | Vila da Folha | Vende os pergaminhos de jutsu fora do kit automático (tier 1 a 3) |
| Capitã Rin | Dá as primeiras missões da vila (`quest_giver_leaf`) | Vila da Folha | *"Os lobos estão atacando viajantes. Mate 5."* |
| Instrutora Ibuki | Proctora do Exame Chunin (`exam_proctor_forest`) | Academia, Floresta da Vila (1018, 1048) | *"Antes de qualquer coisa, prove que prestou atenção no que a vila te ensinou..."* — as 5 perguntas do quiz cobrem chakra, elementos, mestre, ninjutsu e hokage |
| Capitã Anbu Suzu | Guia as 4 missões do Exame Anbu/Kage (`quest_giver_akatsuki_lair`) | Hall de entrada do Covil (1406, 1010) | *"Antes de encarar os quatro guardiões, prove que aguenta os clones brancos que patrulham os corredores. Mate 10."* |

### Mercadores e dadores de missão (uma dupla por região)

| NPC | Papel | Região | Posição (x, y, 7) |
|---|---|---|---|
| Ichiro, o Mercador | loja (kunai, colete, poções, mochila) | Floresta da Vila | 22, 18 (mapa lógico da vila) |
| Velha Sumi | loja | Floresta da Morte | — (mapa abstrato/Godot, não portado ao OTBM ainda) |
| Rastreador Goro | missões — *"Sanguessugas infestam a margem. Mate 8."* | Floresta da Morte | — |
| Mercador Itsuki | loja | Costa das Marés | 1026, 1145 |
| Ancião Tazu | missões — *"Mercenários contratados por uma guilda rival atacam quem trabalha na ponte. Afaste-os. Mate 8."* | Costa das Marés | 1032, 1145 |
| Tsubaki, a Escavadora | loja | Ruínas do Clã Marionetista | 1207, 1022 |
| Ancião Kaito | missões — *"Ancião Kaito quer entender como as marionetes ainda se movem. Traga 8 juntas de marionete."* Antes dos xamãs, também testa o que o jogador sabe da maldição do clã (quiz). | Ruínas do Clã Marionetista | 1205, 1022 |
| Ferreiro Genzo | loja | Montanha do Trovão | 1228, 1058 |
| Mestra Yuki | missões — *"As águias do trovão não deixam ninguém subir a trilha. Abata 15."* Antes do quiz do pacto antigo, já ensina a resposta: *"uma dupla que a Nuvem Vermelha já usou contra vilas inteiras, há uma geração, ainda na Grande Guerra."* | Montanha do Trovão | 1222, 1058 |
| Fornecedor Enji | loja | Covil da Nuvem Vermelha | 1406, 1012 |

### Mestres de Tarefas (um por região, sistema novo)

| NPC | Região | Posição (x, y, 7) |
|---|---|---|
| Mestre de Tarefas Jiro | Floresta da Vila (Portão Sul) | 1030, 1067 |
| Mestre de Tarefas Ren | Hub do Pântano (antes da Floresta da Morte) | 1137, 1057 |
| Mestre de Tarefas Umi | Costa das Marés | 1029, 1147 |
| Mestre de Tarefas Dokan | Ruínas do Clã Marionetista | 1202, 1020 |
| Mestre de Tarefas Kaji | Montanha do Trovão | 1228, 1062 |
| Mestre de Tarefas Kuro | Covil da Nuvem Vermelha | 1406, 1014 |
| Quadro de Missões (diárias) | Praça da Vila da Folha | 1035, 1040 |

### Bosses como personagens (motivação)

Detalhados na seção 2 (narrativa) e na seção 6 (números). Resumo de motivação por boss:

| Boss | Motivação |
|---|---|
| Chefe dos Bandidos | Sobreviver na estrada liderando a gangue mais experiente da Floresta da Vila — sem ligação alguma com a organização maior. |
| Espadachim da Névoa + Aprendiz Mascarado | Contratado por uma guilda rival para sabotar a ponte; o aprendiz luta por dívida de vida, não por dinheiro. |
| Serpente Branca | Ninja renegado que abandona a própria forma humana quando encurralado — o boss de arco mais "canônico" do jogo. |
| Sapo Ancião | Guardião independente do Pergaminho do Céu, boss secundário opcional da Floresta da Morte. |
| Desertor de Elite | Gênio que abandonou a própria vila atrás de poder proibido, a caminho de recrutar para a organização maior. |
| Marionetista das Ruínas | Última vontade do clã extinto, ainda "vivo" através dos bonecos que comanda. |
| O Sócio Eterno + Oni Ancestral | Dupla amaldiçoada por um pacto antigo — um não sabe morrer, o outro cobra um preço por cada vida; só caem juntos. |
| Os 4 guardiões do Covil | Cada um espectro de um poder que uma vila enfrentou uma vez e nunca mais quis enfrentar — o clímax de progressão do jogo. |

---

## 9. Direção de arte e som

*Fonte: `docs/sistemas/arte-e-sprites.md`, `docs/backlog-sprites.md`, `docs/03-decisoes-tecnicas.md`
(ADR-002).*

### Regra de ouro: "se não parece Tibia, não faz"

O jogo reproduz deliberadamente a estética "Open Tibia clássico": grid 32×32, chão na linha y=30,
alpha binário (sem transparência suave), sem UI moderna — só os estilos `.otui` existentes. Nenhuma
decisão de arte deve fugir dessa referência.

### Pipeline procedural

Como nenhum sprite da Tibia original ou de NTO pode ser redistribuído (ADR-002) e não há
ObjectBuilder funcional no Mac, o projeto tem seu **próprio compilador de assets**: `tools/spr/`.
`assets-src/sprites/` (PNGs + `manifest.json`/`tiles.json`) é a fonte da verdade; `build_assets.py`
gera `Tibia.spr`/`Tibia.dat` (cliente) e `items.otb`/`items_tiles_naruto.xml` (servidor) — nunca
editados à mão. Hoje cobrem: 23.626 things de item (estilo procedural, ícone próprio para os 78
itens do jogo), looktypes de criatura 1–897 com arte temática básica, 27 efeitos + 8 misseis
próprios para os 54 jutsus (`gen_effects.py`), tiles de cenário criados do zero (tatame, torii,
lanterna, cerca de bambu) e terreno com autoborder (grama↔água↔areia↔lama↔terra↔cobble).

### O que é placeholder

A maior parte da arte de criatura/NPC ainda é **placeholder**: sprites genéricos do Tibia vanilla
recoloridos (procedural) ou recortes de planilhas de terceiros (`assets-src/import/`, "importado
lateral"). Três camadas de cobertura hoje (`docs/sistemas/arte-e-sprites.md`, "Criaturas
procedurais"):
- **6 monstros com arte 100% procedural e 4 direções reais** (looktypes 940–945, `gen_animals.py`):
  Lobo, Cervo, Águia do Trovão (sempre em voo), Sanguessuga, Sapo Gigante, e as 3 serpentes
  (Cobra da Floresta/Serpente Menor/Serpente de Magma) compartilhando o looktype 943 com máscara
  de cor de verdade (`layers=2`).
- **12 monstros humanoides agora TAMBÉM com 4 direções reais e andar de verdade** (looktypes
  946–957, `humanoid_art.py` + `gen_humanoid_variants.py` v2, `2ac02b3`, 2026-09-05 2ª passada):
  Bandido, Bandido Arqueiro, Chefe dos Bandidos, Mercenário da Ponte, Batedor da Névoa, Ninja
  Renegado, Guardião da Neblina, Marionete de Combate, Marionetista das Ruínas, Guerreiro
  Espectral, O Sócio Eterno e Oni da Geleira. O boneco genérico é desenhado do zero por código
  (`humanoid_art.draw_body`, sem material importado) com 4 direções reais, 3 fases de andar e um
  adereço próprio por classe (`humanoid_art._gear`: arco+aljava no Bandido Arqueiro, manto longo
  no Chefe dos Bandidos etc.) — substitui a v1 (hue-shift do PNG importado, `layers=1`, pose
  única repetida nas 4 direções), que fica só como histórico em
  `docs/sistemas/arte-e-sprites.md`.
- **~14 monstros ainda no looktype importado cru**, sem cor nem direção próprias (ex.:
  `elite_cloud_guard`, os 3 `exam_rival_*`) — ver `docs/backlog-sprites.md`.

### ADR-002: material de terceiros só para teste privado, nunca versionado

**Achado real e sério, não hipotético:** `assets-src/sprites/mugen_looktypes.json` mapeia os
looktypes **900–926** para sprites extraídos de um jogo de luta MUGEN com personagens do anime
Naruto **de verdade** (pastas literalmente chamadas `Naruto/`, `Sasuke/Sasuke Rinnegan`, `Kakashi`,
`Itachi`, `Pain`, `Obito`, `Madara`...). Isso é **exatamente** o que a ADR-002 proíbe ("nada de
sprites copiados de NTO ou do anime") — e hoje esses looktypes estão em uso de produção em **13
lugares**: os 3 NPCs mentores, a Capitã Anbu Suzu, e 6 bosses de arco (Serpente Branca, Desertor de
Elite, e os 4 guardiões finais do Covil). O `docs/backlog-sprites.md` marca isso como **P0** — risco
legal real, acima até da prioridade dos monstros comuns — e recomenda encomendar arte própria para
substituir os 13 looktypes antes de qualquer lançamento público. A pasta `assets-src/import/mugen/`
em si já está fora do controle de versão (git), como a regra exige; o problema é que os looktypes
gerados a partir dela **já foram exportados para o jogo jogável**.

### Backlog de arte resumido

*Fonte: `docs/backlog-sprites.md`.* Total estimado para zerar o backlog inteiro: **~900 horas de
pixel artist** — 38 monstros (~340h), 21 NPCs (~135h), 9 personagens jogáveis (~126h), jutsus
(~87h, já quase todo resolvido via procedural), itens (~117h, destaque para os 44 quadros de
armadura com variação visual no boneco — hoje nenhum set "veste" diferente do outro), tiles das 2
regiões novas (~55h) e UI (~43h). Prioridade nº 1 recomendada: os 5 personagens jogáveis P0 + os 8
NPCs/bosses em looktype MUGEN (risco legal + maior visibilidade simultânea).

### Som: efeitos prontos, música pendente

*Fonte: `docs/sistemas/audio.md`, `docs/backlog-audio.md` — ver seção 5 ("Som") para o resumo
funcional.* 51 efeitos sonoros procedurais (síntese própria, `tools/audio/gen_sfx.py`, sem
material de terceiros — mesma regra da ADR-002) cobrindo jutsu, combate e UI, tocados de verdade
em jogo pelo módulo `naruto_sounds`. **Música segue 100% pendente**: nenhuma trilha própria existe,
a opção "Música" do cliente fica desligada por padrão, e gerar música proceduralmente (progressão
harmônica, não só um envelope de síntese) é reconhecidamente mais trabalhoso que os SFX curtos —
`tools/audio/gen_music.py` é a ferramenta candidata, ainda não escrita.

---

## 10. Tecnologia

*Fonte: `CLAUDE.md`, `docs/02-arquitetura.md`, `docs/03-decisoes-tecnicas.md` (ADR-005),
`docs/04-setup-ot.md`.*

### Stack em 1 página

```
[OTClient Redemption]  ──TCP 7171/7172──►  [TFS 1.4.2]  ──►  [MariaDB]
   client-otc/                                server/tfs/
```

- **Cliente:** OTClient Redemption (fork mehah/opentibiabr, C++20 + Lua/OTUI, MIT). Customização
  via módulos Lua próprios em `client-otc/modules/naruto_*`, sem tocar no C++.
- **Servidor:** The Forgotten Server 1.4.2, protocolo 10.98, scripting em Lua (revscriptsys para
  scripts novos, sistema clássico para `creaturescripts` legadas como `login.lua`).
- **Conteúdo:** `data/*.json` continua sendo a **fonte da verdade** — jutsus, itens, monstros,
  NPCs, ranks, tarefas, diárias, conquistas, curva de XP. `tools/export_tfs.py` gera tudo que o TFS
  precisa (`server/generated/`); nunca editar os XML/Lua gerados à mão.
- **Sprites:** `.spr`/`.dat` versão 1098, compilados por `tools/spr/build_assets.py` a partir de
  `assets-src/sprites/` (pipeline procedural próprio, seção 9).
- **Mapa:** um único OTBM (`tools/map/build_valley.py` + `build_regions.py`), editável no Remere's
  Map Editor, nunca escrito à mão.
- **`client-godot/`** é o protótipo antigo (Marcos 1–3, Godot 4/GDScript) — provou o loop de jogo e
  o balanceamento inicial antes do pivô (ADR-005), congelado como referência de regras, não recebe
  mais features.

### Como rodar

```bash
python3 tools/validate_data.py        # valida todo data/*.json contra os schemas
python3 tools/export_tfs.py            # gera server/generated/ a partir de data/
# compilar cliente e servidor: ver docs/04-setup-ot.md (CMake + vcpkg + Ninja, 30-60min na 1ª vez)
tools/play.sh                          # sobe servidor + AAC + abre o cliente
```

Contas de teste conhecidas: `god`/`god` (GM, grupo 6), `teste`/`teste` (jogador comum). Uma
segunda conta GM (`slqa`) foi criada durante QA e não removida — útil para testes paralelos sem
colidir com `god`.

### Ferramentas principais

- **Simulador de balanceamento** (`tools/balance/sim.py`) — Monte Carlo de TTK/DPS por
  nível×monstro×build, usado para calibrar todas as fórmulas da seção 5.
- **Pipeline de sprites** (`tools/spr/`) — compilador de assets próprio (seção 9).
- **Pipeline de mapa** (`tools/map/`) — leitor/gravador OTBM, gerador do mapa, auditoria de
  caminhabilidade (`walk_audit.py`), preview sem abrir o cliente (`render_preview.py`).
- **AAC** (`tools/aac/`) — site de registro de conta, porta 8080, sobe junto com `play.sh`.

### O que é gerado vs. fonte

Fonte (editar aqui): `data/*.json`, `docs/`, `assets-src/`, `client-otc/modules/naruto_*`,
`tools/*.py`. Gerado (nunca editar à mão, sempre regenerar): `server/generated/`,
`server/tfs/data/monster|spells|npc/naruto/*`, `client-otc/data/things/1098/*`,
`client-otc/modules/naruto_theme/jutsus_data.lua`, `server/generated/world/*.otbm`.

---

## 11. Estado atual e roadmap

*Fonte: `CLAUDE.md` ("Estado atual"), `docs/01-roadmap.md`, `docs/qa/*.md`.*

### O que está pronto (2026-09-05, tarde — HEAD `88ea822`)

O jogo roda ponta a ponta: OTClient compilado, TFS 1.4.2 com todo o conteúdo Naruto instalado,
mapa próprio `valley` com as 6 regiões fisicamente construídas, sprites placeholder/procedurais
próprios, ferramentas de GM (`/sl`). Números atuais: **173 itens, 54 jutsus, 38 monstros, 21 NPCs**,
sistemas de rank/exame/tarefas/diárias/**conquistas** (55, com lógica real, `e02aa0b`) rodando no
servidor, walk-cycle do outfit do jogador validado por filtro geométrico automático.

**Sessão da tarde de hoje (6 commits de conteúdo/design + 6 de engenharia)**:
- **Auditoria narrativa dos 6 arcos** (`5873bd3`) + **Lotes A/B/C/M** (`1439749`, `6f0893f`,
  `006f3c3`, `0dc49a5`): a Nuvem Vermelha e um gancho de saída plantados em cada um dos 6 arcos
  (seção 2), 4 NPCs novos posicionados no mapa (Kaito/Tsubaki/Yuki/Genzo, seção 8), gate da Costa
  das Marés corrigido de Chunin pra Genin (seção 4), spawns soltos do Aprendiz Mascarado/Serpente
  Menor/Cervo adicionados, `tools/map/validate_world.py` (validador cruzado missão↔spawn↔mapa)
  novo.
- **Motor de missões v2** (`184de6f`): 4 tipos de objetivo novos, pré-requisitos cruzados,
  recompensas storage/outfit/addon/title (seção 5, "Missões").
- **Humanoides procedurais v2** (`2ac02b3`): os 12 looktypes 946–957 ganharam 4 direções reais e
  andar de verdade, sem material importado (seção 9).
- **Balanceamento rodadas 6 e 7** (`5fe6056`, `87c19a1`): híbrido ≤+15% em 6/6 bosses (r6); tier 1
  reescalado pra 12–14% do pool (r7, seção 3 "Chakra"); **fúria de boss com dano real** via
  `onHealthChange` do jogador (seção 5, "Monstros: comportamento e bosses").
- **Encoding**: mojibake nas falas resolvido (`5fe6056`), regressão de kill-por-nome-acentuado
  encontrada e corrigida em servidor+cliente (`8147d69`, `049981b`, seção 5, "Encoding").
- **Fix do andar travando** (`bc20778`): bordas geradas sem `FLAG_ALWAYSONTOP` no `items.otb`
  causavam `stackpos` divergente cliente↔servidor.
- **2 playtests de história completos** (arcos 1–3 e 4–6, `docs/qa/playtest-historia-arcos1-3.md`,
  `-arcos4-6.md`) validaram in-game todas as falas/ganchos acima.

**Estado herdado (sessões anteriores)**: ninjutsu puro fecha 6 de 6 bosses de referência dentro da
meta de paridade desde a rodada 5 (`1a46739`); 51 SFX procedurais tocando em jogo (`ef195b4`) —
música segue pendente; 6 monstros com arte procedural e 4 direções reais desde `79881e0`. Locale
pt-BR cobre a UI, os nomes de sistema (Mana→Chakra) e a maior parte das mensagens de sistema do
TFS. Menu Shinobi (Ctrl+J) com abas Personagem/Elemento/Jutsus/Missões (com seção Conquistas)/
Comandos (GM) funcionando in-game, rank visível na janela de Atributos.

### Em andamento

**Balanceamento rodada 8** (concluída — ver `docs/sistemas/balanceamento-relatorio-v8.md`):
`tools/balance/sim.py` passou a modelar `phases[].attack_multiplier`/`summons` de boss (fúria
real); Serpente Branca recalibrada (1,9→1,45, único boss fora de 1,3×-1,8× de dano recebido/s);
`HYBRID_JUTSU_CADENCE_FRAC` substituído pelo modelo "castar o tier 1 sempre que libera e tem
chakra" (cooldown real, sem esticamento artificial) — exigiu subir o cooldown do tier 1 de 9,0s
para 27,0s pra manter o híbrido ≤+15% contra os 6 bosses de referência; a meta de 15-25% de
tempo sem chakra numa hunt híbrida NÃO fechou (0% em todos os níveis) — conflito estrutural com
a meta "Genin L1 6-8 casts por pool" (custo mais alto fecharia a scarcity mas quebraria os
casts/pool), documentado como pendência honesta. `katon_anel_chamas`/`fuuton_rajada_cortante`/
`fuuton_tornado_cortante` (área/beam tier 2/3) ajustados pra devolver ninjutsu a +30-60% sobre
taijutsu nos pulls de 3 monstros de Ruínas e Montanha (a rodada 7 tinha derrubado isso).
**Re-teste de história arcos 4–6** (pendente): o playtest de hoje rodou ANTES do fix de encoding
049981b/8147d69 estar completamente validado em combate longo — confirmar que kills com nome
acentuado contam de verdade pra missão/conquista numa sessão nova, do zero. Polimento de mapa
(bordas neve↔rocha, gelo↔rocha ainda retas em vários trechos); vista de costas do personagem
ainda sintetizada por código.

### Próximos passos (ordem de valor, conforme `01-roadmap.md`)

1. Balanceamento rodada 9 (sugestão): achar uma alavanca real pra 15-25% de tempo sem chakra em
   hunt híbrida sem violar "Genin L1 6-8 casts por pool" (pendência da rodada 8, ver
   `docs/sistemas/balanceamento-relatorio-v8.md` §2); revisitar o pull L2 (`wolf`, n=3) que ficou
   bem abaixo de -60% (sem jutsu de área disponível nesse nível).
2. Re-teste de história arcos 4–6 numa sessão nova, do zero, confirmando o fix de encoding em
   combate real sustentado (não só os primeiros minutos pós-restart).
3. Música ambiente (`tools/audio/gen_music.py`, ainda não escrita) — único item de som pendente.
4. Polimento de mapa v3 (bordas neve/gelo↔rocha, antecâmaras do Covil).
5. Vista de costas real para o personagem padrão (hoje sintetizada por código, não desenhada).
6. Templos/vilas 2–4 no mapa físico (hoje só a Vila da Folha existe fisicamente; Névoa/Nuvem/Areia
   só existem como vocação/dados, sem cidade própria no OTBM).
7. Substituir os 13 looktypes MUGEN (P0 de arte, seção 9) antes de qualquer lançamento público.
8. Party com XP compartilhada, clãs, PvP em arena (Marco 5 — pós-lançamento).

### Riscos e limitações honestas

- **Os looktypes 900–926 (personagens MUGEN) violam a ADR-002 na prática** — não é dívida técnica
  comum, é risco legal de takedown se o jogo for distribuído assim (seção 9).
- **Sprites de monstro/NPC são majoritariamente placeholder** — 18 monstros/humanoides já com
  direção/andar reais (6 animais + 12 humanoides v2, hoje), ~14 ainda sem cor nem direção
  (seção 9); "o jogo parece incompleto" continua o feedback mais provável de um jogador novo.
- **Vista de costas do personagem é sintetizada por código**, não desenhada — aproximação, não arte
  final.
- **Sem música** — os 51 efeitos sonoros de combate/UI existem e tocam; trilha ambiente por
  vila/bioma não existe (seção 9).
- **Fúria real de boss recalibrada na rodada 8** — `sim.py` agora modela `attack_multiplier`/
  summons; só a Serpente Branca precisou de ajuste (1,9→1,45). Ver
  `docs/sistemas/balanceamento-relatorio-v8.md` §1.
- **Chakra do tier 1 ainda não fecha a meta de tempo-sem-chakra em hunt híbrida** (0% medido
  contra meta 15-25%, mesmo depois de trocar o modelo de cadência na rodada 8) — conflito
  estrutural real com "Genin L1 6-8 casts por pool" (o custo que fecharia a scarcity quebra os
  casts/pool), não uma questão de calibração fina; ver relatório v8 §2.
- **Playtests de história (arcos 1-6) validaram narrativa e falas, não combate sustentado**: os
  dois playtests do dia confirmaram texto/fases em tela, mas não uma sessão longa pós-fix de
  encoding — ver "Em andamento".
- **Só a Vila da Folha existe fisicamente no mapa** — as outras 3 vilas são vocação/dados sem
  cidade própria construída no OTBM ainda.
- **Sem party, clã, mercado ou PvP** — social é 100% roadmap, não uma omissão silenciosa (Marco 5).

---

## 12. Glossário

*Fonte: `CLAUDE.md`, todos os documentos de sistema.*

| Termo | Significado |
|---|---|
| **Ryo** | Moeda do jogo (equivalente a "gold coin" da Tibia). |
| **Chakra** | Recurso gasto por jutsus (equivalente a "mana"). |
| **Jutsu** | Habilidade ativa (equivalente a "spell"). 54 no jogo, 8 por combinação personagem+elemento. |
| **Elemento** | Afinidade ofensiva: Katon (fogo), Suiton (água), Doton (terra), Fuuton (vento), Raiton (raio). Ciclo circular de vantagem/desvantagem. |
| **Vila** | Facção/vocação inicial do jogador (Folha, Névoa, Nuvem, Areia). Define cidade, NPCs e skill bônus — não mais o jutsu. |
| **Personagem** | Identidade jogável fixa (9 no jogo), dona de 4 jutsus pessoais que não mudam com o elemento. |
| **Skill** | Proficiência que sobe com uso: Taijutsu, Shuriken, Ninjutsu, Genjutsu, Defesa. |
| **Rank** | Genin → Chunin → Jonin → Anbu → Kage — camada narrativa/de exame sobre o level. |
| **Gate de rank** | Tile de entrada de região com actionid 45001–45005 que barra quem não tem o rank mínimo. |
| **Tier** | Nível de força de um jutsu/item dentro do seu grupo (1, 2 ou 3 para jutsu; L1/10/20.../100 para equipamento). |
| **Task Master (Mestre de Tarefas)** | NPC regional que dá tarefas repetíveis com cooldown, um por região. |
| **Diária** | Missão repetível sorteada por dia, 3 por jogador, auto-aceita. |
| **Kawarimi** | Jutsu universal de substituição (esquiva mágica), compartilhado por vários personagens. |
| **PvM** | Player vs. Monster — o pilar central do jogo (caça de monstros). |
| **Boss** | Monstro especial com `phases` (mudança de comportamento por % de HP), respawn de horas, loot exclusivo. |
| **OTBM** | Formato de mapa do Open Tibia, lido/gravado por `tools/map/otbm.py`, editável no Remere's Map Editor. |
| **ADR** | Architecture/Design Decision Record — formato de decisão documentada em `docs/03-decisoes-tecnicas.md`. |
| **`manapercent`** | Atributo do TFS que faz um jutsu custar uma % do chakra máximo em vez de um valor fixo (`chakra_cost_percent` no JSON) — usado nos 5 projéteis tier 1 elementais desde a rodada 5 de balanceamento. |
| **Regen por level** | Regeneração natural de HP/chakra escalando com o level do jogador (desde a rodada 5), reaplicada a cada level-up — ver seção 5, "Regeneração natural". |
| **Conquista** | Recompensa (título + ryo) por atingir uma condição fixa (`data/achievements.json`, 55 entradas, 10 tipos de condição) — ver seção 5. |

---

## 13. Inconsistências encontradas

*Lista curta para o dono do projeto corrigir — todo número deste documento veio de `data/`; onde
dois documentos discordavam, usei `data/` como fonte e anoto a divergência aqui.*

1. **`data/villages.json` tem campos órfãos do protótipo Godot.** `starting_jutsus` (um jutsu por
   vila) e `start_map`/`start_x`/`start_y` (mapas separados `leaf_village`/`mist_village`/
   `cloud_village`/`sand_village`) contradizem o modelo atual descrito em
   `docs/sistemas/combate-e-jutsus.md` ("vila não filtra mais jutsu", jutsu vem de Personagem +
   Elemento) e o mapa único `valley` do TFS (`docs/sistemas/mapas.md`). Ainda não editado (fora do
   escopo desta e da missão anterior) — sinalizo de novo para quem decidir se esses campos ainda
   são lidos por algum script legado ou podem ser removidos/atualizados.
2. **`docs/sistemas/personagem-e-progressao.md` é anterior ao pivô ADR-005.** Descreve save em
   `user://save_slot_N.json` (formato do protótipo Godot) — a persistência real hoje é MariaDB via
   TFS. Usei desse documento só as fórmulas de HP/Chakra (que batem exatamente com
   `data/progression.json`); o restante (seção "Save", menção a "vilas... definem jutsus
   iniciais") deveria ser marcado como histórico ou atualizado.
3. **`docs/sistemas/arte-e-sprites.md` tem duas seções que se contradizem sobre cobertura de
   criatura.** A tabela antiga "O que existe hoje (placeholder)" (perto do topo do arquivo) diz
   que looktypes de criatura "1..897 ganham arte temática" sem distinguir grau de cobertura; a
   seção nova "Criaturas procedurais" (final do arquivo) detalha que hoje **18** monstros (6
   animais + 12 humanoides desde a v2 de hoje, `2ac02b3`) têm 4 direções reais e andar de verdade
   — a tabela antiga nunca foi atualizada para refletir essa distinção, então lida isolada ela
   sugere uma cobertura mais uniforme do que existe de verdade. Esta bíblia usa a seção mais
   recente como fonte (seção 9).
4. **`docs/backlog-audio.md` pode estar desatualizado sobre `task_1e2c0ec0`.** O documento lista
   como pendente uma falha de login (`NarutoAchievements` nil, bloqueando toda conta) encontrada
   durante a sessão de áudio (`ef195b4`) e corrigida só em código, sem confirmação ao vivo na
   época. Os playtests seguintes (r3, r4 — ambos posteriores, e a rc de validação `c2d716f`)
   conseguiram logar múltiplas vezes sem esse erro reaparecer, sugerindo que já foi resolvido —
   mas nenhum documento fecha esse achado explicitamente nem confirma se `task_1e2c0ec0` foi
   encerrada. Não consegui confirmar 100% sem acesso ao rastreador de tasks; sinalizo para quem
   tiver esse acesso fechar ou reabrir.
5. **`data/ranks.json` ainda lista `costa_das_mares` em `unlocks.areas` do rank Chunin** (achado do
   Lote M, `docs/sistemas/mapas.md` "A1"), mesmo depois do gate físico ter sido corrigido pra
   Genin — dado órfão que só afeta o comando de debug de GM `/sl canenter <zona>`
   (`NarutoRanks.zoneMinIndex`), não o gate real (`rank_gate.lua` lê o actionid do tile, não essa
   tabela). Não corrigido hoje (edição de `data/ranks.json` fora do escopo do lote de mapa).
6. **(resolvido na rodada 8) O `attack_multiplier` de fase de boss foi recalibrado
   pós-fúria-real.** `tools/balance/sim.py` agora modela `phases[].attack_multiplier`/`summons`
   (antes ignorados); dos 12 bosses com fase de fúria, só a Serpente Branca (`data/monsters/
   swamp.json`) precisou de ajuste (1,9→1,45) pra ficar dentro de 1,3×-1,8× de dano recebido/s
   (fase final vs. fase 1) com `death_rate` 0% (taijutsu solo, com poções, no level-alvo). Ver
   `docs/sistemas/balanceamento-relatorio-v8.md` §1.

### O que ficou faltando (não coberto por esta bíblia)

- Falas-chave completas de NPCs de loja (não existe campo de diálogo/saudação em
  `data/npcs/*.json` além do texto de missão — a seção 8 usa o texto de missão disponível).
- Posições físicas no mapa de Velha Sumi e Rastreador Goro (Floresta da Morte) — únicos 2 NPCs
  restantes ainda só no mapa abstrato do protótipo Godot; os outros 4 (Tsubaki, Ancião Kaito,
  Ferreiro Genzo, Mestra Yuki) foram posicionados hoje no Lote M (seção 8).
- Dados de combate reais (XP/h medido, TTK, chakra até secar) numa sessão de história longa —
  os 2 playtests de história de hoje mediram narrativa/falas, não uma hunt sustentada
  pós-fix-de-encoding (seção 11).
