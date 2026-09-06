# AAC do Shinobi Legends (`tools/aac/`)

Site local, minimo, para criar conta e personagem sem escrever SQL na mao
(estilo os "AAC" clássicos de servidor de Tibia). Serve em `http://127.0.0.1:8080/`
por padrão.

## Rodar

```bash
tools/aac.sh            # sobe em background (porta 8080)
tools/aac.sh status     # mostra se esta no ar
tools/aac.sh stop       # derruba
```

Ou em primeiro plano (Ctrl+C para parar), útil para ver os logs na hora:

```bash
.venv/bin/python3 tools/aac/aac.py
```

Precisa de:
- **MariaDB no ar** com o schema do TFS (`server/tfs/schema.sql`) já aplicado.
- **`pymysql`** no `.venv` do projeto: `.venv/bin/pip install pymysql` (já feito
  neste checkout; se o `.venv` for recriado, rode de novo).
- As credenciais do banco são lidas de `server/tfs/config.lua` (nunca hardcoded
  e nunca editado por este script) — se você mudar usuário/senha/porta do
  MySQL lá, o AAC acompanha sozinho.

Porta alternativa: `AAC_PORT=8090 tools/aac.sh`.

## Páginas

| Rota | Método | O que faz |
|---|---|---|
| `/` | GET | Home: nome do jogo, uma frase da bíblia, dados de conexão (IP/porta/protocolo, lidos de `config.lua`) e links. |
| `/criar-conta` | GET/POST | Cria conta: nome (3-32 letras/números/`_`), senha (4-64), confirmação, e-mail opcional. |
| `/criar-personagem` | GET/POST | Escolhe vila (Folha/Névoa/Nuvem/Areia, com elemento e bônus de skill) → personagem inicial daquela vila (9 cards: preview do outfit, elemento padrão, os 4 jutsus pessoais) → nome do personagem (3-20 letras/espaços) + sexo + login/senha da conta dona do personagem. |
| `/conta` | GET/POST | Login (conta + senha) → lista os personagens dessa conta (nome, level, vila, personagem, último login) + formulário de troca de senha. |
| `/trocar-senha` | POST | Só usado pelo formulário de `/conta`: troca a senha da conta (confere a senha atual antes). |
| `/sprite/<looktype>.png` | GET | Retrato PNG (frame parado, olhando pro sul, 4x) de um looktype de personagem inicial, servido de `tools/aac/portraits/<looktype>.png` (arquivo versionado, obra nossa). Só serve os looktypes que aparecem em `data/characters.json` (whitelist) — não é um servidor de arquivos genérico. |

## De onde vêm os dados

Lido só para leitura, nunca escrito por este script:
- `data/villages.json` — nomes de exibição, elemento e skill-bônus de cada vila.
- `data/tfs_mapping.json` (`villages`) — `vocation_id`/`town_id`/outfits de cada vila.
- `data/characters.json` — personagens iniciais por vila (id, nome, descrição, `looktype`,
  elemento padrão, ids dos 4 jutsus pessoais).
- `data/element_sets.json` — nome em português de cada elemento (Katon → Fogo etc.).
- `data/jutsus/personal.json` e `data/jutsus/neutral.json` — nome de exibição de cada
  jutsu pessoal (alguns, como `kawarimi`/`punho_suave`/`fuuin_contencao`, são "universais"
  e moram em `neutral.json`, não em `personal.json`, apesar de aparecerem em `characters.json`).
- `tools/aac/portraits/<looktype>.png` — retrato do outfit na tela de criação de
  personagem. **Versionado** (obra nossa, ADR-002): renderizado por
  `tools/spr/render_outfit.py` direto de `client-otc/data/things/1098/Tibia.spr`/
  `Tibia.dat` (o par que o próprio cliente carrega), nunca de
  `assets-src/import/` (material de terceiros, gitignored). Regerar depois de
  qualquer `tools/spr/build_assets.py` que mude os looktypes 900–909:
  ```bash
  .venv/bin/python tools/spr/render_outfit.py \
      --looktype 900 901 902 903 904 905 907 908 909 \
      --outdir tools/aac/portraits --scale 4
  ```
  O AAC só expõe os looktypes que já aparecem em `characters.json` e cujo PNG
  exista nessa pasta (404 caso contrário — não é um servidor de arquivos
  genérico). Pendência de **arte**, não do AAC: os 9 looktypes ainda são
  `layers=1` importado do MUGEN por dentro do `.dat` (ver
  `docs/sistemas/arte-e-sprites.md` e a linha "Substituir os 13 looktypes
  MUGEN" em `docs/01-roadmap.md`) — o retrato deixa de ler PNG bruto de
  terceiros, mas o desenho em si ainda não é arte 100% própria.
- `server/tfs/config.lua` — host/porta/usuário/senha/banco do MySQL, e também
  `ip`/`loginProtocolPort` (dados de conexão mostrados na home).

## Regras aplicadas na criação de personagem

- **Senha em SHA1**: TFS 1.4.2 não tem `passwordType` configurável — o código
  (`server/tfs/src/iologindata.cpp`) sempre compara com `transformToSHA1(password)`.
  Este AAC grava e confere a senha da mesma forma (`hashlib.sha1(...).hexdigest()`).
- **Nome de personagem "estilo Tibia"**: 3 a 20 letras (com acentos) e espaços
  simples, sem espaço duplo nem nas pontas.
- **Colunas obrigatórias em `players`**: o INSERT preenche explicitamente
  `posx/posy/posz`, `town_id`, `conditions` (`NULL`, blob vazio),
  `lookbody/lookhead/looklegs/lookfeet` (0 — os looktypes 900+ são fantasias
  fechadas, não usam cor de doll) e `looktype` (do personagem escolhido),
  `vocation` (= `vocation_id` da vila), `health/healthmax` (150/150),
  `mana/manamax` (**110/110** — piso de chakra da rodada 5 de balanceamento,
  o mesmo valor que `character_switch.lua` aplicaria no primeiro login se o
  personagem nascesse com menos; gravar direto deixa o banco já coerente
  antes do 1º login), `cap` (400) — os valores base de nível 1 de qualquer
  vocação, já que o ganho por level das 4 vocações só começa a contar a partir
  do nível 2 (ver `gainhp`/`gainmana`/`gaincap` em `server/tfs/data/XML/vocations.xml`) —,
  `level=1`, `experience=0` e todos os `skill_*` em 10 / `skill_*_tries` em 0
  (os defaults "zerados" do TFS).
- **A escolha de personagem grava UMA storage, de propósito**: logo após o
  `INSERT` em `players`, o AAC grava `player_storage` (`key=60001`,
  `STORAGE_CHARACTER` — a mesma constante de `character_switch.lua`, gerado)
  com o `looktype` do personagem escolhido. É essa storage que
  `NarutoCharacters.current()` lê no primeiro login para saber qual dos 9
  personagens (e portanto quais 4 jutsus pessoais) aplicar — sem ela, o jogo
  cairia no primeiro personagem cadastrado daquela vila (`defaultFor()`),
  ignorando a escolha feita aqui. **Não** grava a storage `60002`
  (`STORAGE_ELEMENT`): sem ela, `NarutoCharacters.apply()` cai sozinho no
  `default_element` do personagem escolhido (mesmo campo de
  `characters.json`), que já é o elemento certo. **Também não** toca a
  storage `60000` (`STORAGE_ONBOARDED`) — isso continua proposital:
  `server/tfs/data/scripts/naruto/character_switch.lua` considera
  `first_time = true` enquanto a storage 60000 (`STORAGE_ONBOARDED`)
  não existir, e é isso que faz o **Menu Shinobi abrir sozinho** no primeiro
  login (aba Personagem), confirmado no teste (ver screenshots).
- **`town_id` é resolvido contra o banco, não copiado direto de `tfs_mapping.json`**:
  `IOLoginData::loadPlayer` (`server/tfs/src/iologindata.cpp:347`) **rejeita o
  login inteiro** (`return false`) se o `town_id` do personagem não existir na
  tabela `towns` carregada do mapa atual. Hoje (mapa `forest_valley`) só existe
  a Vila da Folha (`towns.id = 1`); Névoa/Nuvem/Areia ainda não têm mapa/templo
  próprio. Por isso `resolve_town()` consulta a tabela `towns` pelo `town_id` da
  vila escolhida e, se não existir, cai para a primeira town que existir (hoje,
  sempre a 1) — tanto na posição quanto no **valor de `town_id` gravado**,
  nunca o aspiracional do JSON. O aviso "nasceu na Vila da Folha até a vila
  escolhida ter mapa próprio" aparece na tela quando isso acontece.
- **Sem SQL manual, sem exposição de senha**: todas as queries usam parâmetros
  (`pymysql`, nunca f-string/format dentro do SQL); a senha nunca é logada nem
  devolvida em nenhuma resposta; o corpo do POST é limitado a 16 KB.

## Pendências conhecidas

- Só a Vila da Folha tem templo de verdade no mapa atual. Personagens de
  Névoa/Nuvem/Areia nascem lá mesmo (aviso explícito na tela de criação) até
  essas vilas terem mapa próprio — ver `docs/sistemas/mapas.md` /
  `CLAUDE.md` ("Estado atual").
- Preview do outfit usa o PNG do frame parado extraído do MUGEN
  (`assets-src/import/extracted/mugen/<looktype>/idle_*.png`), não o sprite
  real do `.spr/.dat` do cliente — é só uma miniatura de referência na tela de
  criação, não afeta o outfit gravado no personagem (`looktype`).
- Não há recuperação de senha (há troca de senha, em `/conta`) nem confirmação
  de e-mail (fora de escopo: ferramenta interna/local, não uma AAC pública).
- Nome de personagem só é validado por **formato** (3-20 letras/espaços, sem
  espaço duplo/nas pontas) — não existe hoje um bloqueio de "nomes do anime"
  em `docs/03-decisoes-tecnicas.md` (ADR-002 é sobre os nomes que o **jogo**
  usa — vilas/personagens/jutsus próprios —, não sobre um filtro de nomes que
  o jogador pode digitar). Decisão desta sessão: seguir só o formato, como
  pedido, em vez de inventar uma lista própria sem lastro em decisão de design.

## Teste feito em 2026-09-04 (criação original)

1. Subiu o AAC (`tools/aac.sh`), criou conta via `curl -X POST /criar-conta` e
   personagem (Vila da Folha, "Genin Laranja") via `curl -X POST /criar-personagem`.
2. Conferiu no banco (`mysql -u tfs -ptfs forgottenserver`): `level=1`,
   `vocation=1`, `town_id=1`, `posx/posy/posz` = templo real da Vila da Folha,
   `looktype=900`, senha em SHA1 (40 chars).
3. Testou erros: conta duplicada, senha errada na criação de personagem, nome
   de personagem inválido, personagem com nome duplicado — todos com mensagem
   amigável e HTTP 400.
4. Logou de verdade com essa conta/senha usando `tools/autotest_client.sh
   <conta> <senha>` (copia `client-otc/tests/autotest_rc.lua` para
   `client-otc/shinobirc.lua`, roda o OTClient, remove o rc ao final — nada
   deste teste editou `client-otc/tests/` nem `tools/autotest_client.sh`).
   Resultado: personagem nasceu no templo (1029, 1042, 7), com o outfit do
   "Genin Laranja" e o **Menu Shinobi abriu sozinho** (aba Personagem, "Genin
   Laranja" marcado como ATUAL, "Level 1 · Vila da Folha"). Screenshots em
   `screenshots/aac_01_spawn_templo.png` e `screenshots/aac_02_hud.png`.
5. Apagou a conta e o personagem de teste do banco ao final
   (`DELETE FROM players/accounts WHERE name = ...`).

## Teste feito em 2026-09-05 (sessão de polimento: tema, storage, senha)

1. `curl` em todas as rotas GET (`/`, `/criar-conta`, `/criar-personagem`,
   `/conta`, `/sprite/900.png`) → 200; `/sprite/999.png` (looktype fora da
   whitelist) e `/rota-inexistente` → 404.
2. Fluxo completo via `curl -X POST`: criou conta `aactest01`, criou
   personagem **"João Ninja"** (acento de propósito, ver item 3) escolhendo
   **Genin Uchiha** (vila da Folha) — resposta confirmou "criado na Vila da
   Folha como Genin Uchiha".
3. **UTF-8 conferido por SQL**: `SELECT HEX(name) FROM players WHERE
   name='João Ninja'` devolveu `4A6FC3A36F204E696E6A61` — os bytes
   `C3 A3` são exatamente o "ã" em UTF-8 (não latin1/mojibake). Sem problema
   de encoding no nome gravado (a conexão do AAC já usa `charset="utf8mb4"`
   e a tabela `players` aceita esses bytes dentro do seu `utf8` de 3 bytes,
   suficiente para acentos latinos).
4. **Personagem escolhido chega ao servidor**: `SELECT` confirmou
   `vocation=1`, `looktype=901` (Genin Uchiha, não o primeiro da vila) e
   `mana=manamax=110`; `player_storage` tinha a linha `(player_id, key=60001,
   value=901)` — exatamente o `STORAGE_CHARACTER` que
   `character_switch.lua` lê no primeiro login.
5. Testou erros: conta duplicada (400), personagem com nome duplicado (400),
   senha de conta errada ao criar personagem (400, "Conta ou senha
   inválidos."), nome de personagem inválido (400).
6. `/conta`: login válido listou o personagem com **level, vila, personagem
   (nome do personagem, não só a vila) e último login** ("nunca", campo
   `lastlogin=0`); login com senha errada → mensagem de erro.
7. `/trocar-senha`: trocou a senha da conta de teste, confirmou que a senha
   **antiga** passou a ser rejeitada em `/conta` e a **nova** funciona.
8. Apagou a conta e o personagem de teste do banco ao final.
9. Screenshots das 3 páginas (Chrome headless, `--screenshot`, contra o AAC
   já no ar): `screenshots/aac_01_home.png`, `screenshots/aac_02_criar_
   personagem.png`, `screenshots/aac_03_conta.png`.
10. Não editado e não reiniciado: `server/tfs/` (binário/processo do jogo),
    `tools/export_tfs.py`, `client-otc/` — só `tools/aac/aac.py`,
    `tools/aac/README.md` e os dois `docs/*.md` citados no relatório final.
