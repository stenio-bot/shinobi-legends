#!/usr/bin/env python3
"""Gera a página 'Estrutura jogo Narutibia PvM' (hub de documentação) com todos os docs embutidos.
Uso: .venv/bin/python tools/docs_hub.py <saida.html>  (a página é publicada como Artifact)."""
import json, sys, os, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CATS = [
 ("O jogo", ["docs/ESTRUTURA.md", "docs/00-biblia-do-jogo.md", "docs/00-visao-geral.md", "docs/01-roadmap.md"]),
 ("História e mundo", ["docs/lore/mundo.md", "docs/lore/progressao.md", "docs/lore/pesquisa-naruto.md", "docs/design/auditoria-historia.md"]),
 ("Jogador e progressão", ["docs/sistemas/progressao-jogador.md", "docs/sistemas/progressao-servidor.md", "docs/sistemas/vilas-e-clas.md", "docs/sistemas/personagem-e-progressao.md"]),
 ("Sistemas de jogo", ["docs/sistemas/combate-e-jutsus.md", "docs/sistemas/missoes.md", "docs/sistemas/monstros-e-pvm.md", "docs/sistemas/itens-e-equipamentos.md", "docs/sistemas/economia.md", "docs/sistemas/mapas.md", "docs/sistemas/cliente-ux.md", "docs/sistemas/audio.md"]),
 ("Balanceamento", ["docs/sistemas/balanceamento.md"] + [f"docs/sistemas/balanceamento-relatorio{s}.md" for s in ["", "-v2", "-v3", "-v4", "-v5", "-v6", "-v7", "-v8"]]),
 ("Arte e áudio", ["docs/sistemas/arte-e-sprites.md", "docs/backlog-sprites.md", "docs/backlog-audio.md"]),
 ("Playtests", ["docs/qa/playtest-l1-20.md", "docs/qa/playtest-l1-20-r2.md", "docs/qa/playtest-l1-20-r3.md", "docs/qa/playtest-l1-20-r4.md", "docs/qa/playtest-l1-20-r5.md", "docs/qa/playtest-historia-arcos1-3.md", "docs/qa/playtest-historia-arcos4-6.md"]),
 ("Tecnologia", ["README.md", "docs/02-arquitetura.md", "docs/03-decisoes-tecnicas.md", "docs/04-setup-ot.md", "CLAUDE.md", "docs/referencias/nto-narutibia.md", "docs/referencias/otclient-arquitetura.md", "docs/referencias/otclient-modulos.md"]),
]
TREE = ('shinobi-legends/\\n├── <b>docs/</b>\\n│   ├── <i>00-biblia-do-jogo.md</i>      documento mãe\\n'
        '│   ├── 00-visao-geral.md · 01-roadmap.md · 02-arquitetura.md · 03-decisoes-tecnicas.md · 04-setup-ot.md\\n'
        '│   ├── ESTRUTURA.md               este índice\\n│   ├── lore/                      mundo, progressão de rank, pesquisa\\n'
        '│   ├── design/                    auditoria da história (6 arcos)\\n'
        '│   ├── sistemas/                  combate, missões, monstros, mapas, cliente, áudio, balanceamento, arte\\n'
        '│   ├── qa/                        playtests r1–r5 e de história\\n│   └── referencias/               Narutibia/NTO, OTClient\\n'
        '├── data/                          JSON = fonte da verdade (jutsus, monstros, npcs, itens, tarefas…)\\n'
        '├── tools/                         exportador TFS, mapa, sprites, áudio, balanceamento, testes\\n'
        '├── server/tfs/                    The Forgotten Server 1.4.2\\n└── client-otc/                    OTClient Redemption + módulos naruto_*')
def main(out_path):
    docs, words = [], 0
    for cat, files in CATS:
        for f in files:
            if not os.path.exists(f):
                continue
            t = open(f, encoding="utf-8").read()
            m = re.search(r'^# (.+)$', t, re.M)
            w = len(t.split()); words += w
            docs.append({"cat": cat, "path": f, "title": (m.group(1).strip() if m else f), "words": w, "md": t})
    commit = subprocess.run(['git', 'log', '-1', '--format=%h %ci'], capture_output=True, text=True).stdout.strip()
    payload = json.dumps(docs, ensure_ascii=False).replace('</', '<\\/')
    nav = ""
    for cat, _ in CATS:
        items = [d for d in docs if d["cat"] == cat]
        nav += f'<div class="cat"><h3>{cat}</h3><ul>' + ''.join(
            f'<li><a href="#{d["path"]}" data-path="{d["path"]}"><span>{d["title"]}</span><small>{d["words"]:,}</small></a></li>' for d in items) + '</ul></div>'
    tpl = open(os.path.join(ROOT, "tools", "docs_hub_template.html"), encoding="utf-8").read()
    html = (tpl.replace("{{NAV}}", nav).replace("{{PAYLOAD}}", payload).replace("{{TREE}}", TREE)
            .replace("{{NDOCS}}", str(len(docs))).replace("{{WORDS}}", f"{words:,}").replace("{{COMMIT}}", commit))
    open(out_path, "w", encoding="utf-8").write(html)
    print("docs", len(docs), "words", words, "bytes", len(html.encode()))
if __name__ == "__main__":
    main(sys.argv[1])
