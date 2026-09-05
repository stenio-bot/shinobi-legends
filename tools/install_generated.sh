#!/usr/bin/env bash
# Instala server/generated/ dentro de server/tfs/data/. Idempotente: pode rodar quantas vezes quiser.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GEN="$ROOT/server/generated"
TFS="$ROOT/server/tfs/data"
[ -d "$TFS" ] || { echo "server/tfs/data não existe (clone o TFS primeiro)"; exit 1; }

python3 "$ROOT/tools/export_tfs.py"

mkdir -p "$TFS/monster/naruto" "$TFS/spells/scripts/naruto" "$TFS/npc/scripts/naruto" "$TFS/scripts/naruto"
cp "$GEN"/monster/naruto/*.xml "$TFS/monster/naruto/"
cp "$GEN"/spells/scripts/naruto/*.lua "$TFS/spells/scripts/naruto/"
cp "$GEN"/npc/*.xml "$TFS/npc/"
cp "$GEN"/npc/scripts/naruto/*.lua "$TFS/npc/scripts/naruto/"
cp "$GEN"/scripts/naruto/*.lua "$TFS/scripts/naruto/"
# village_outfit.lua deixou de existir (a logica de 1o login foi absorvida por character_switch.lua)
rm -f "$TFS/scripts/naruto/village_outfit.lua"
cp "$GEN"/lib/naruto_quests.lua "$TFS/lib/"
cp "$GEN"/lib/naruto_jutsus.lua "$TFS/lib/"
cp "$GEN"/lib/naruto_items.lua "$TFS/lib/"
cp "$GEN"/XML/vocations.xml "$TFS/XML/vocations.xml"
cp "$GEN"/XML/outfits.xml "$TFS/XML/outfits.xml"
cp "$GEN"/lib/naruto_json.lua "$TFS/lib/"
cp "$GEN"/lib/naruto_villages.lua "$TFS/lib/"
cp "$GEN"/lib/naruto_characters.lua "$TFS/lib/"

# Blocos delimitados por marcadores: substitui se já existir, senão insere antes da tag de fechamento.
inject() {  # inject <arquivo> <tag_fechamento> <arquivo_bloco>
  local file="$1" close="$2" block="$3"
  python3 - "$file" "$close" "$block" <<'PY'
import sys,re
f,close,block=sys.argv[1:4]
s=open(f,encoding="utf-8",errors="surrogateescape").read()
b=open(block,encoding="utf-8").read()
b=re.sub(r"<!--.*?-->", "", b, flags=re.S)  # remove todos os comentários (cabeçalhos multi-linha quebram o parser)
start,end="<!-- NARUTO:BEGIN -->","<!-- NARUTO:END -->"
payload=f"{start}\n{b.strip()}\n{end}\n"
if start in s:
    s=re.sub(re.escape(start)+r".*?"+re.escape(end)+r"\n?", payload, s, flags=re.S)
else:
    s=s.replace(close, payload+close, 1)
if close == "</items>":
    # OVERRIDE: remove as entradas vanilla cujos ids nós redefinimos no bloco NARUTO
    ours=set(re.findall(r'<item id="(\d+)"', b))
    idx=s.index(start); before, rest = s[:idx], s[idx:]
    before=re.sub(r'\n[ \t]*<item id="(\d+)"[^>]*/>', lambda m: "" if m.group(1) in ours else m.group(0), before)
    before=re.sub(r'\n[ \t]*<item id="(\d+)"[^>]*(?<!/)>.*?</item>', lambda m: "" if m.group(1) in ours else m.group(0), before, flags=re.S)
    def split_range(m):
        a,b=int(m.group(1)),int(m.group(2)); body=m.group(3)
        hit=[i for i in range(a,b+1) if str(i) in ours]
        if not hit: return m.group(0)
        out=[]; lo=a
        for h in hit+[b+1]:
            if lo<=h-1:
                out.append(f'\n\t<item fromid="{lo}" toid="{h-1}"{body}')
            lo=h+1
        return "".join(out)
    before=re.sub(r'\n[ \t]*<item fromid="(\d+)" toid="(\d+)"([^>]*/>)', split_range, before)
    before=re.sub(r'\n[ \t]*<item fromid="(\d+)" toid="(\d+)"([^>]*(?<!/)>.*?</item>)', split_range, before, flags=re.S)
    s=before+rest
if close == "</spells>":
    # só os jutsus: spells vanilla removidas (referenciam vocações Knight/Druid que não existem mais)
    s='<?xml version="1.0" encoding="UTF-8"?>\n<spells>\n'+payload+'</spells>\n'
open(f,"w",encoding="utf-8",errors="surrogateescape").write(s)
PY
}
inject "$TFS/monster/monsters.xml" "</monsters>" "$GEN/monster/monsters_naruto.xml"
inject "$TFS/spells/spells.xml" "</spells>" "$GEN/spells/spells_naruto.xml"
# itens gerados + tiles novos (server ids 30000+) no mesmo bloco NARUTO
cat "$GEN/items/items_naruto.xml" > "$GEN/items/_items_all.xml"
[ -f "$GEN/items/items_tiles_naruto.xml" ] && cat "$GEN/items/items_tiles_naruto.xml" >> "$GEN/items/_items_all.xml"
inject "$TFS/items/items.xml" "</items>" "$GEN/items/_items_all.xml"
rm -f "$GEN/items/_items_all.xml"

grep -q "naruto_quests" "$TFS/lib/lib.lua" || echo "dofile('data/lib/naruto_quests.lua')" >> "$TFS/lib/lib.lua"
grep -q "naruto_jutsus" "$TFS/lib/lib.lua" || echo "dofile('data/lib/naruto_jutsus.lua')" >> "$TFS/lib/lib.lua"
grep -q "naruto_items" "$TFS/lib/lib.lua" || echo "dofile('data/lib/naruto_items.lua')" >> "$TFS/lib/lib.lua"
grep -q "naruto_json" "$TFS/lib/lib.lua" || echo "dofile('data/lib/naruto_json.lua')" >> "$TFS/lib/lib.lua"
grep -q "naruto_villages" "$TFS/lib/lib.lua" || echo "dofile('data/lib/naruto_villages.lua')" >> "$TFS/lib/lib.lua"
grep -q "naruto_characters" "$TFS/lib/lib.lua" || echo "dofile('data/lib/naruto_characters.lua')" >> "$TFS/lib/lib.lua"
echo "instalado em $TFS"
