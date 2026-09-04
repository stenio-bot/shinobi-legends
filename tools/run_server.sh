#!/usr/bin/env bash
# Roda o The Forgotten Server a partir da pasta server/tfs (ele exige o cwd correto:
# procura config.lua, data/ e key.pem relativos ao diretório atual).
# Uso: tools/run_server.sh          # foreground, Ctrl+C para parar
#      tools/run_server.sh --build  # recompila antes de subir
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TFS="$ROOT/server/tfs"
BIN="$TFS/build/tfs"

if [ "${1:-}" = "--build" ]; then
  cmake --build "$TFS/build" -j8
fi

[ -x "$BIN" ] || { echo "erro: $BIN não existe. Rode: tools/run_server.sh --build"; exit 1; }
[ -f "$TFS/config.lua" ] || { echo "erro: $TFS/config.lua não existe (copie de config.lua.dist)"; exit 1; }

# MariaDB precisa estar no ar.
if ! mysqladmin --silent ping >/dev/null 2>&1; then
  echo "aviso: MariaDB não respondeu ao ping. Tente: brew services start mariadb"
fi

cd "$TFS"
exec ./build/tfs "$@"
