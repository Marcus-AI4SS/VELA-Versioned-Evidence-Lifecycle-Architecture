#!/usr/bin/env sh
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON_BIN=${PYTHON:-python3}
VELA_HOME=${VELA_HOME:-"$HOME/.vela"}
STATE_DIR="$VELA_HOME/state"
BIN_DIR="$VELA_HOME/bin"
mkdir -p "$STATE_DIR" "$BIN_DIR"

if [ "${VELA_SKIP_DEP_INSTALL:-0}" != "1" ] && [ -f "$REPO_ROOT/requirements.txt" ]; then
  "$PYTHON_BIN" -m pip install -r "$REPO_ROOT/requirements.txt"
fi

SHIM="$BIN_DIR/vela"
SCRIPT="$REPO_ROOT/scripts/vela.py"
cat > "$SHIM" <<EOF
#!/usr/bin/env sh
exec "$PYTHON_BIN" "$SCRIPT" "\$@"
EOF
chmod +x "$SHIM"

cat > "$STATE_DIR/install.json" <<EOF
{
  "schema_version": "vela.install.receipt.v1",
  "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "repo_root": "$REPO_ROOT",
  "python": "$PYTHON_BIN",
  "vela_home": "$VELA_HOME",
  "shim": "$SHIM",
  "codex_home": "${CODEX_HOME:-$HOME/.codex}"
}
EOF

"$PYTHON_BIN" "$SCRIPT" doctor
if [ "${VELA_SKIP_LOCAL_ENV:-0}" != "1" ]; then
  if [ "${VELA_FORCE_LOCAL_ENV:-0}" = "1" ]; then
    "$PYTHON_BIN" "$SCRIPT" local-env install --python "$PYTHON_BIN" --force
  else
    "$PYTHON_BIN" "$SCRIPT" local-env install --python "$PYTHON_BIN"
  fi
fi
printf '\nVELA shim created: %s\n' "$SHIM"
printf 'Add this directory to PATH if you want to run vela directly: %s\n' "$BIN_DIR"
if [ "${VELA_SKIP_LOCAL_ENV:-0}" != "1" ]; then
  printf 'VELA local research environment installed. Restart Codex so new skills are discovered.\n'
fi
