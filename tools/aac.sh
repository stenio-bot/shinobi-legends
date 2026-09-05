#!/usr/bin/env bash
# Sobe o AAC (tools/aac/aac.py) em background na porta 8080 (ou $AAC_PORT).
# Uso:
#   tools/aac.sh          # sobe (nao faz nada se ja estiver no ar)
#   tools/aac.sh stop     # derruba
#   tools/aac.sh status   # mostra se esta no ar
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${AAC_PORT:-8080}"
PIDFILE="/tmp/shinobi_aac.pid"
LOG="/tmp/shinobi_aac.log"
PY="$ROOT/.venv/bin/python3"

[ -x "$PY" ] || PY="python3"

is_up() {
  nc -z 127.0.0.1 "$PORT" 2>/dev/null
}

case "${1:-start}" in
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null && echo "AAC derrubado (pid $(cat "$PIDFILE"))."
      rm -f "$PIDFILE"
    else
      pkill -f "tools/aac/aac.py" 2>/dev/null && echo "AAC derrubado." || echo "AAC nao estava no ar."
    fi
    ;;
  status)
    if is_up; then echo "AAC no ar em http://127.0.0.1:$PORT/"; else echo "AAC fora do ar."; fi
    ;;
  *)
    if is_up; then
      echo "AAC ja esta no ar em http://127.0.0.1:$PORT/"
      exit 0
    fi
    "$PY" -c "import pymysql" 2>/dev/null || {
      echo "aviso: pymysql nao encontrado em $PY -- instale com: $ROOT/.venv/bin/pip install pymysql"
    }
    ( cd "$ROOT" && AAC_PORT="$PORT" nohup "$PY" tools/aac/aac.py > "$LOG" 2>&1 & echo $! > "$PIDFILE" )
    for _ in $(seq 1 20); do
      sleep 0.3
      is_up && break
    done
    if is_up; then
      echo "AAC no ar em http://127.0.0.1:$PORT/ (log: $LOG, pid: $(cat "$PIDFILE" 2>/dev/null))"
    else
      echo "AAC nao subiu, veja $LOG"
      exit 1
    fi
    ;;
esac
