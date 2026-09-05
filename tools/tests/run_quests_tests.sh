#!/usr/bin/env bash
# Roda os testes headless da extensão de missões (docs/sistemas/missoes.md) em luajit puro,
# sem precisar do servidor TFS rodando. Reexporta antes (tools/export_tfs.py só escreve em
# server/generated/, nunca em server/tfs/) para garantir que os testes rodam contra o Lua
# gerado mais recente a partir de data/*.json.
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "== 1/3: python3 tools/validate_data.py =="
PYBIN=.venv/bin/python
[ -x "$PYBIN" ] || PYBIN=python3
"$PYBIN" tools/validate_data.py

echo
echo "== 2/3: python3 tools/export_tfs.py (gera server/generated/) =="
python3 tools/export_tfs.py

echo
echo "== 3/3: luajit -bl (checagem de sintaxe) em todo Lua gerado =="
fail=0
while IFS= read -r f; do
	if ! luajit -bl "$f" > /dev/null 2>/tmp/quests_luajit_err.txt; then
		echo "ERRO DE SINTAXE: $f"
		cat /tmp/quests_luajit_err.txt
		fail=1
	fi
done < <(find server/generated -name "*.lua")
if [ "$fail" -ne 0 ]; then
	echo "luajit -bl encontrou erro(s) de sintaxe — abortando antes dos testes funcionais."
	exit 1
fi
echo "OK — todo o Lua gerado compila."

echo
echo "== testes funcionais headless (tools/tests/test_quests_headless.lua) =="
luajit tools/tests/test_quests_headless.lua
