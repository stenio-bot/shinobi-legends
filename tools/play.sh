#!/usr/bin/env bash
# Sobe o servidor (se não estiver no ar) e abre o cliente. Uso: tools/play.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mysqladmin --silent ping >/dev/null 2>&1 || { brew services start mariadb >/dev/null 2>&1; sleep 4; }
if ! nc -z 127.0.0.1 7171 2>/dev/null; then
  echo "subindo o servidor..."
  (cd "$ROOT/server/tfs" && nohup ./build/tfs > /tmp/tfs_run.log 2>&1 &)
  for _ in $(seq 1 30); do sleep 1; nc -z 127.0.0.1 7171 2>/dev/null && break; done
fi
nc -z 127.0.0.1 7171 2>/dev/null && echo "servidor ok (127.0.0.1:7171) — conta god/god" || { echo "servidor não subiu, veja /tmp/tfs_run.log"; exit 1; }
cd "$ROOT/client-otc" && exec ./OTClient.app/Contents/MacOS/OTClient
