#!/usr/bin/env sh

set -eu



REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

PYTHON_BIN=${PYTHON:-python3}



printf 'VELA macOS installer\n'

printf 'Source package: %s\n' "$REPO_ROOT"

printf 'Runtime targets: CODEX_HOME=%s, VELA_HOME=%s\n' "${CODEX_HOME:-$HOME/.codex}" "${VELA_HOME:-$HOME/.vela}"



if [ "$(uname -s)" != "Darwin" ]; then

  printf 'This installer is optimized for macOS. Use install.ps1 on Windows or install.sh on Linux.\n' >&2

  exit 2

fi



if ! command -v brew >/dev/null 2>&1; then

  printf 'Homebrew is required for one-command public-tool bootstrap on macOS.\n' >&2

  printf 'Install Homebrew from https://brew.sh, then rerun this script.\n' >&2

  exit 1

fi



if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then

  printf 'Python command %s not found. Installing python@3.13 with Homebrew.\n' "$PYTHON_BIN"

  brew install python@3.13

fi



VELA_BOOTSTRAP_TOOLS=1 exec sh "$REPO_ROOT/install.sh" --bootstrap-tools "$@"
