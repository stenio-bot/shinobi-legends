#!/usr/bin/env bash
# Roda o cliente com login automático e captura screenshots. Requer servidor no ar (tools/run_server.sh).
# Uso: tools/autotest_client.sh [conta] [senha]   (padrão god/god)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="$ROOT/client-otc"
OUT="$HOME/Library/Application Support/shinobi/.shinobi"
export SL_ACCOUNT="${1:-god}" SL_PASSWORD="${2:-god}"
nc -z 127.0.0.1 7171 || { echo "servidor não está na porta 7171 (tools/run_server.sh)"; exit 1; }
cp "$CLI/tests/autotest_rc.lua" "$CLI/shinobirc.lua"
rm -f "$OUT"/autotest_*.png
( cd "$CLI" && ./OTClient.app/Contents/MacOS/OTClient > /tmp/otc_autotest.log 2>&1 & )
for _ in $(seq 1 60); do sleep 1; pgrep -x OTClient >/dev/null || break; done
pkill -x OTClient 2>/dev/null
rm -f "$CLI/shinobirc.lua"
echo "== eventos:"; grep -E "AUTOTEST" /tmp/otc_autotest.log | sed 's/.*AUTOTEST: //'
echo "== erros do cliente: $(grep -c 'error' /tmp/otc_autotest.log)"; grep 'error' /tmp/otc_autotest.log | grep -v "^\s" | cut -c1-160 | sort | uniq -c | sort -rn | head -5
mkdir -p "$ROOT/screenshots"; cp "$OUT"/autotest_*.png "$ROOT/screenshots/" 2>/dev/null
echo "== screenshots em $ROOT/screenshots/"; ls "$ROOT/screenshots" | grep autotest
