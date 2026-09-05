# Estrutura do jogo — Narutibia PvM (Shinobi Legends)

Índice organizado de toda a documentação do projeto. Cada seção segue a ordem em que alguém novo
deveria ler: primeiro o que o jogo é, depois como o jogador o vive, depois como cada sistema
funciona, depois o que foi testado e o que falta.

## 1. O jogo
- [Bíblia do jogo](00-biblia-do-jogo.md) — documento mãe: visão, história, jogador, jornada L1–100, sistemas, bestiário, grimório, NPCs, arte, tecnologia, estado, glossário
- [Visão geral (GDD resumido)](00-visao-geral.md)
- [Roadmap](01-roadmap.md) — o que está feito (com commit), em andamento e próximo

## 2. História e mundo
- [Bíblia do mundo](lore/mundo.md) — cosmologia, Grande Guerra, as 4 vilas, os 6 arcos, bosses
- [Progressão de rank](lore/progressao.md) — Genin → Chunin → Jonin → Anbu → Kage
- [Pesquisa: estrutura narrativa do Naruto](lore/pesquisa-naruto.md)
- [Auditoria da história do jogador](design/auditoria-historia.md) — nota por arco, lacunas, plano em lotes

## 3. O jogador e a progressão
- [Tabela de progressão L1–100](sistemas/progressao-jogador.md)
- [Progressão de servidor](sistemas/progressao-servidor.md) — rank, quiz, tarefas, diárias, conquistas, storages
- [Vilas e clãs](sistemas/vilas-e-clas.md)
- [Personagem e progressão](sistemas/personagem-e-progressao.md)

## 4. Sistemas de jogo
- [Combate e jutsus](sistemas/combate-e-jutsus.md)
- [Missões](sistemas/missoes.md) — formato JSON, tipos (kill, coleta, falar, chegar, quiz), pré-requisitos
- [Monstros e PvM](sistemas/monstros-e-pvm.md) — regiões, bosses, fases
- [Itens e equipamentos](sistemas/itens-e-equipamentos.md)
- [Economia](sistemas/economia.md)
- [Mapas](sistemas/mapas.md) — as 6 regiões, coordenadas, gates, ferramentas
- [Cliente / UX](sistemas/cliente-ux.md) — Menu Shinobi, opcode 210, chat
- [Áudio](sistemas/audio.md) — 51 efeitos procedurais

## 5. Balanceamento
- [Sistema de balanceamento](sistemas/balanceamento.md) — metas e simulador
- Relatórios por rodada: [r1](sistemas/balanceamento-relatorio.md) · [r2](sistemas/balanceamento-relatorio-v2.md) · [r3](sistemas/balanceamento-relatorio-v3.md) · [r4](sistemas/balanceamento-relatorio-v4.md) · [r5](sistemas/balanceamento-relatorio-v5.md) · [r6](sistemas/balanceamento-relatorio-v6.md)

## 6. Arte
- [Arte e sprites](sistemas/arte-e-sprites.md) — pipeline procedural, criaturas, efeitos, regras Tibia
- [Backlog de sprites](backlog-sprites.md)
- [Backlog de áudio](backlog-audio.md)

## 7. Qualidade (playtests)
- [Playtest L1–20 r1](qa/playtest-l1-20.md) · [r2](qa/playtest-l1-20-r2.md) · [r3](qa/playtest-l1-20-r3.md) · [r4](qa/playtest-l1-20-r4.md) · [r5](qa/playtest-l1-20-r5.md)
- [Playtest de história, arcos 1–3](qa/playtest-historia-arcos1-3.md)

## 8. Tecnologia
- [Arquitetura](02-arquitetura.md)
- [Decisões técnicas (ADRs)](03-decisoes-tecnicas.md)
- [Setup do ambiente Open Tibia](04-setup-ot.md)
- [Guia de contexto do projeto (CLAUDE.md)](../CLAUDE.md)
- Referências: [Narutibia/NTO](referencias/nto-narutibia.md) · [OTClient arquitetura](referencias/otclient-arquitetura.md) · [OTClient módulos](referencias/otclient-modulos.md)
