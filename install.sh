#!/usr/bin/env sh
set -eu

for arg in "$@"; do
  case "$arg" in
    --bootstrap-tools) VELA_BOOTSTRAP_TOOLS=1 ;;
    --skip-dependency-install) VELA_SKIP_DEP_INSTALL=1 ;;
    --skip-local-environment) VELA_SKIP_LOCAL_ENV=1 ;;
    --force-local-environment) VELA_FORCE_LOCAL_ENV=1 ;;
    *)
      printf 'Unknown option: %s\n' "$arg" >&2
      exit 2
      ;;
  esac
done

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON_BIN=${PYTHON:-python3}
VELA_HOME=${VELA_HOME:-"$HOME/.vela"}
STATE_DIR="$VELA_HOME/state"
BIN_DIR="$VELA_HOME/bin"
SCRIPT="$REPO_ROOT/scripts/vela.py"
mkdir -p "$STATE_DIR" "$BIN_DIR"

if [ "${VELA_BOOTSTRAP_TOOLS:-0}" = "1" ]; then
  printf 'VELA bootstrap: checking public system tools. Private runtime state will not be copied.\n'
  if [ "$(uname -s)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    if ! command -v git >/dev/null 2>&1; then brew install git || printf 'Git Homebrew install failed; install manually.\n'; fi
    if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then brew install python@3.13 || printf 'Python Homebrew install failed; install manually or set PYTHON=/path/to/python.\n'; fi
    if ! command -v pwsh >/dev/null 2>&1; then brew install powershell || printf 'PowerShell Homebrew install failed; install manually if needed.\n'; fi
    if ! command -v rg >/dev/null 2>&1; then brew install ripgrep || printf 'ripgrep Homebrew install failed; install manually.\n'; fi
    if ! command -v node >/dev/null 2>&1; then brew install node || printf 'Node.js Homebrew install failed; install manually.\n'; fi
    if ! command -v gh >/dev/null 2>&1; then brew install gh || printf 'GitHub CLI Homebrew install failed; install manually if needed.\n'; fi
  else
    if ! command -v git >/dev/null 2>&1; then printf 'Install Git before using repository workflows.\n'; fi
    if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then printf 'Install Python 3.13+ or set PYTHON=/path/to/python.\n'; fi
    if ! command -v pwsh >/dev/null 2>&1; then printf 'Install PowerShell 7 (pwsh) if you need cross-platform runtime scripts.\n'; fi
    if ! command -v rg >/dev/null 2>&1; then printf 'Install ripgrep for validators and repository audits.\n'; fi
    if ! command -v node >/dev/null 2>&1; then printf 'Install Node.js LTS for optional JavaScript runtime tools.\n'; fi
    if ! command -v gh >/dev/null 2>&1; then printf 'Install GitHub CLI if you need repository and release checks.\n'; fi
    if [ "$(uname -s)" = "Darwin" ]; then printf 'Install Homebrew first for automatic macOS public-tool bootstrap.\n'; fi
  fi
  if ! command -v agentmemory >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    npm install -g agentmemory || printf 'agentmemory npm install failed; continue with manual optional setup.\n'
  fi
  printf 'CodeGraph, MCP vendors, Codex plugins, browser/CNKI sessions, Zotero, and Obsidian are doctor/manual setup only.\n'
fi

if [ "${VELA_SKIP_DEP_INSTALL:-0}" != "1" ] && [ -f "$REPO_ROOT/requirements.txt" ]; then
  "$PYTHON_BIN" -m pip install -r "$REPO_ROOT/requirements.txt"
fi

SHIM="$BIN_DIR/vela"
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
if [ "${VELA_BOOTSTRAP_TOOLS:-0}" = "1" ]; then
  "$PYTHON_BIN" "$SCRIPT" local-env bootstrap-tools --include all --install --yes
fi
if [ "${VELA_SKIP_LOCAL_ENV:-0}" != "1" ]; then
  if [ "${VELA_FORCE_LOCAL_ENV:-0}" = "1" ]; then
    "$PYTHON_BIN" "$SCRIPT" local-env install-runtime --include core,automation,toolchain --python "$PYTHON_BIN" --commit --force-core
  else
    "$PYTHON_BIN" "$SCRIPT" local-env install-runtime --include core,automation,toolchain --python "$PYTHON_BIN" --commit
  fi
fi
printf '\nVELA shim created: %s\n' "$SHIM"
printf 'Add this directory to PATH if you want to run vela directly: %s\n' "$BIN_DIR"
if [ "${VELA_SKIP_LOCAL_ENV:-0}" != "1" ]; then
  printf 'VELA local research environment and runtime shims installed. Restart Codex so new skills are discovered.\n'
fi
