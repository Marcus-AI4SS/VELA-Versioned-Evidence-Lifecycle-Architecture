#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PAYLOAD_SKILLS="$BUNDLE_ROOT/payload/skills"
DEFAULT_TARGET="$HOME/Desktop/Codex Research Console"
TARGET_ROOT="${1:-$DEFAULT_TARGET}"
TARGET_SKILLS="$TARGET_ROOT/skills"
TARGET_VENV="$TARGET_ROOT/.venv"
TARGET_PYTHON="$TARGET_VENV/bin/python3"
DESKTOP_LAUNCHER="$HOME/Desktop/Codex Research Console.command"
INSTALL_NOTE="$TARGET_ROOT/安装完成.txt"
INNER_LAUNCHER="$TARGET_ROOT/Launch Codex Research Console.command"

warn() {
  printf "\n[提示] %s\n" "$1"
}

die() {
  printf "\n[失败] %s\n" "$1" >&2
  exit 1
}

detect_app() {
  local app_name="$1"
  if [ -d "/Applications/$app_name.app" ] || [ -d "$HOME/Applications/$app_name.app" ]; then
    return 0
  fi
  return 1
}

[ -d "$PAYLOAD_SKILLS" ] || die "未找到 payload：$PAYLOAD_SKILLS"

ARCH="$(uname -m)"
if [ "$ARCH" != "arm64" ]; then
  warn "当前机器不是 Apple Silicon（arm64）。这套朋友版按 Apple Silicon 优先设计，继续安装前请自行确认兼容性。"
fi

PYTHON3_BIN="$(command -v python3 || true)"
[ -n "$PYTHON3_BIN" ] || die "未探测到 python3。请先安装 Python 3.11+ 后重新运行。"

PYTHON_OK="$("$PYTHON3_BIN" - <<'PY'
import sys
print(int(sys.version_info >= (3, 11)))
PY
)"
[ "$PYTHON_OK" = "1" ] || die "当前 python3 版本低于 3.11。请升级后重试。"

if ! detect_app "Codex" && ! detect_app "OpenAI Codex"; then
  warn "暂时没有探测到 Codex App；如果你已经安装可直接忽略，否则请先补齐再继续用完整工作流。"
fi

if ! command -v git >/dev/null 2>&1; then
  warn "未探测到 Git。控制台可以启动，但新项目初始化和版本记录功能会受影响。"
fi

if ! command -v node >/dev/null 2>&1; then
  warn "未探测到 Node。部分扩展脚本和辅助工具链会提示缺失。"
fi

if ! detect_app "Zotero"; then
  warn "未探测到 Zotero。正式文献链相关功能会提示缺失。"
fi

if ! detect_app "Obsidian"; then
  warn "未探测到 Obsidian。知识沉淀相关功能会提示缺失。"
fi

printf "\nCodex Research Console（macOS）安装程序\n"
printf "安装位置：%s\n\n" "$TARGET_ROOT"

mkdir -p "$TARGET_ROOT"
rm -rf "$TARGET_SKILLS" "$TARGET_VENV"
mkdir -p "$TARGET_SKILLS"
cp -R "$PAYLOAD_SKILLS/." "$TARGET_SKILLS/"

"$PYTHON3_BIN" -m venv "$TARGET_VENV"
"$TARGET_PYTHON" -m pip install --upgrade pip >/dev/null
"$TARGET_PYTHON" -m pip install PySide6 >/dev/null

cat > "$INNER_LAUNCHER" <<'EOF'
#!/bin/zsh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export CODEX_RESEARCH_ROOT="$SCRIPT_DIR/skills"
PY_BIN="$SCRIPT_DIR/.venv/bin/python3"
if [ ! -x "$PY_BIN" ]; then
  echo "未找到本地 Python：$PY_BIN"
  exit 1
fi
"$PY_BIN" "$SCRIPT_DIR/skills/manager/app.py"
EOF
chmod +x "$INNER_LAUNCHER"

cat > "$DESKTOP_LAUNCHER" <<EOF
#!/bin/zsh
set -euo pipefail
"$INNER_LAUNCHER"
EOF
chmod +x "$DESKTOP_LAUNCHER"

cat > "$INSTALL_NOTE" <<EOF
Codex Research Console 安装完成
================================

安装位置：$TARGET_ROOT
桌面入口：$DESKTOP_LAUNCHER

下一步
------
- 直接双击桌面的 Codex Research Console.command
- 如果是第一次从压缩包解开，macOS 可能要求你确认打开来源
- 如果后续补齐了 Git / Node / Zotero / Obsidian，重新打开工作台即可刷新状态
EOF

printf "安装完成。\n"
printf "启动入口：%s\n" "$DESKTOP_LAUNCHER"
printf "安装说明：%s\n" "$INSTALL_NOTE"
