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
