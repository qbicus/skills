#!/usr/bin/env bash
set -euo pipefail

ACTION="install"
TARGET=""
PROFILE=""
CODEX_PROFILE=""
CLAUDE_PROFILE=""
REPOSITORY_URL="${AI_FRAMEWORK_REPO_URL:-}"
YES=0
DRY_RUN=0
VERBOSE=0
SKIP_AIINDEX=0
SKIP_GRAPHIFY=0
FRAMEWORK_ROOT="${HOME}/.ai"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=11

usage() {
  cat <<'EOF'
Usage: install.sh [install|update-repair|uninstall|doctor] [options]

Options:
  --target codex|claude|both
  --profile low|medium|high
  --codex-profile low|medium|high
  --claude-profile low|medium|high
  --repository-url URL
  --yes
  --dry-run
  --verbose
  --skip-aiindex
  --skip-graphify
EOF
}

if [[ $# -gt 0 && "$1" != --* ]]; then ACTION="$1"; shift; fi
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --codex-profile) CODEX_PROFILE="$2"; shift 2 ;;
    --claude-profile) CLAUDE_PROFILE="$2"; shift 2 ;;
    --repository-url) REPOSITORY_URL="$2"; shift 2 ;;
    --yes) YES=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --verbose) VERBOSE=1; shift ;;
    --skip-aiindex) SKIP_AIINDEX=1; shift ;;
    --skip-graphify) SKIP_GRAPHIFY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$ACTION" in install|update-repair|uninstall|doctor) ;; *) echo "Invalid action: $ACTION" >&2; exit 2 ;; esac
if [[ -n "$TARGET" ]]; then case "$TARGET" in codex|claude|both) ;; *) echo "Invalid target: $TARGET" >&2; exit 2 ;; esac; fi

say() { printf '==> %s\n' "$*"; }
confirm() {
  [[ "$YES" -eq 1 ]] && return 0
  read -r -p "$1 [Y/n] " answer
  [[ -z "$answer" || "$answer" =~ ^[Yy]([Ee][Ss])?$ ]]
}

ensure_git() {
  if command -v git >/dev/null 2>&1; then export AI_FRAMEWORK_PREREQ_GIT_ORIGIN=pre-existing; return 0; fi
  say "Git is missing."
  if [[ "$DRY_RUN" -eq 1 ]]; then echo "Would install Git using the detected package manager."; export AI_FRAMEWORK_PREREQ_GIT_ORIGIN=would-install; return 0; fi
  confirm "Install Git?" || { echo "Cancelled." >&2; exit 2; }
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y git
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y git
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y git
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm git
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper --non-interactive install git
  elif command -v apk >/dev/null 2>&1; then
    sudo apk add git
  else
    echo "Git is required and no supported package manager was found." >&2; exit 2
  fi
  command -v git >/dev/null 2>&1 || { echo "Git installation completed but git is not visible." >&2; exit 2; }
  export AI_FRAMEWORK_PREREQ_GIT_ORIGIN=installed-by-framework
}

python_compatible() {
  local exe="$1"
  "$exe" -c "import sys; raise SystemExit(0 if sys.version_info >= ($MIN_PYTHON_MAJOR, $MIN_PYTHON_MINOR) else 1)" >/dev/null 2>&1
}

find_python() {
  if command -v python3 >/dev/null 2>&1 && python_compatible "$(command -v python3)"; then command -v python3; return 0; fi
  if command -v python >/dev/null 2>&1 && python_compatible "$(command -v python)"; then command -v python; return 0; fi
  return 1
}

install_python_package() {
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3 python3-venv
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y python3
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm python
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper --non-interactive install python3
  elif command -v apk >/dev/null 2>&1; then
    sudo apk add python3
  else
    echo "Python is required and no supported package manager was found." >&2; exit 2
  fi
}

ensure_python() {
  local found=""
  found="$(find_python || true)"
  if [[ -n "$found" ]]; then
    export AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN=pre-existing
    export AI_FRAMEWORK_PYTHON="$found"
    PYTHON_EXE="$found"
    return 0
  fi

  say "Compatible Python is missing (minimum ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR})." >&2
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Would install the current stable Python package provided by the detected Linux package manager." >&2
    export AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN=would-install
    PYTHON_EXE=""
    return 0
  fi
  confirm "Install Python?" || { echo "Cancelled." >&2; exit 2; }
  install_python_package
  found="$(find_python || true)"
  if [[ -z "$found" ]]; then
    echo "The package manager installed Python, but it is older than ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}. Install a current stable Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ and rerun." >&2
    exit 2
  fi
  export AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN=installed-by-framework
  export AI_FRAMEWORK_PYTHON="$found"
  PYTHON_EXE="$found"
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then export AI_FRAMEWORK_PREREQ_UV_ORIGIN=pre-existing; return 0; fi
  if [[ -x "$HOME/.local/bin/uv" ]]; then export PATH="$HOME/.local/bin:$PATH"; export AI_FRAMEWORK_PREREQ_UV_ORIGIN=pre-existing; return 0; fi
  say "uv is missing."
  if [[ "$DRY_RUN" -eq 1 ]]; then echo "Would install uv using the official Astral installer."; export AI_FRAMEWORK_PREREQ_UV_ORIGIN=would-install; return 0; fi
  confirm "Install uv using the official Astral installer?" || { echo "Cancelled." >&2; exit 2; }
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    echo "curl or wget is required to bootstrap uv." >&2; exit 2
  fi
  export PATH="$HOME/.local/bin:$PATH"
  command -v uv >/dev/null 2>&1 || { echo "uv installation completed but uv is not visible." >&2; exit 2; }
  export AI_FRAMEWORK_PREREQ_UV_ORIGIN=installed-by-framework
}

resolve_root() {
  local script_dir=""
  if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  fi
  if [[ -f "$FRAMEWORK_ROOT/installer/installer.py" ]]; then echo "$FRAMEWORK_ROOT"; return 0; fi
  if [[ -n "$script_dir" && -f "$script_dir/installer/installer.py" ]]; then
    if [[ "$script_dir" == "$FRAMEWORK_ROOT" ]]; then echo "$script_dir"; return 0; fi
    if [[ "$ACTION" == "doctor" || "$ACTION" == "uninstall" ]]; then echo "$script_dir"; return 0; fi
    [[ "$DRY_RUN" -eq 1 ]] && { echo "$script_dir"; return 0; }
    [[ -e "$FRAMEWORK_ROOT" ]] && { echo "$FRAMEWORK_ROOT exists but is not a valid framework installation." >&2; exit 2; }
    say "Installing framework from local checkout" >&2
    git clone "$script_dir" "$FRAMEWORK_ROOT" >&2
    echo "$FRAMEWORK_ROOT"; return 0
  fi
  if [[ -z "$REPOSITORY_URL" ]]; then
    if [[ "$ACTION" == "doctor" || "$ACTION" == "uninstall" ]]; then
      echo "No installed framework was found at $FRAMEWORK_ROOT. Run doctor/uninstall from an installed or local framework checkout." >&2
      exit 2
    fi
    echo "Set AI_FRAMEWORK_REPO_URL or pass --repository-url for bootstrap install." >&2
    exit 2
  fi
  [[ "$DRY_RUN" -eq 1 ]] && { echo "$FRAMEWORK_ROOT"; return 0; }
  [[ -e "$FRAMEWORK_ROOT" ]] && { echo "$FRAMEWORK_ROOT already exists but is not a valid framework installation." >&2; exit 2; }
  say "Cloning framework" >&2
  git clone "$REPOSITORY_URL" "$FRAMEWORK_ROOT" >&2
  echo "$FRAMEWORK_ROOT"
}

PYTHON_EXE=""
if [[ "$ACTION" == "install" || "$ACTION" == "update-repair" ]]; then
  ensure_git
  ensure_python
  ensure_uv
else
  PYTHON_EXE="$(find_python || true)"
  if [[ -z "$PYTHON_EXE" ]]; then
    echo "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required to run '$ACTION'. Doctor/uninstall do not install system prerequisites automatically." >&2
    exit 2
  fi
  export AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN=pre-existing
fi
ROOT="$(resolve_root)"
INSTALLER="$ROOT/installer/installer.py"

if [[ -z "$PYTHON_EXE" ]]; then
  echo "Dry-run cannot execute the shared installer core because compatible Python is not currently installed. A real run would install Python first." >&2
  exit 2
fi

ARGS=("$INSTALLER" "$ACTION")
[[ -n "$TARGET" ]] && ARGS+=(--target "$TARGET")
[[ -n "$PROFILE" ]] && ARGS+=(--profile "$PROFILE")
[[ -n "$CODEX_PROFILE" ]] && ARGS+=(--codex-profile "$CODEX_PROFILE")
[[ -n "$CLAUDE_PROFILE" ]] && ARGS+=(--claude-profile "$CLAUDE_PROFILE")
[[ "$YES" -eq 1 ]] && ARGS+=(--yes)
[[ "$DRY_RUN" -eq 1 ]] && ARGS+=(--dry-run)
[[ "$VERBOSE" -eq 1 ]] && ARGS+=(--verbose)
[[ "$SKIP_AIINDEX" -eq 1 ]] && ARGS+=(--skip-aiindex)
[[ "$SKIP_GRAPHIFY" -eq 1 ]] && ARGS+=(--skip-graphify)

say "$ACTION"
exec "$PYTHON_EXE" "${ARGS[@]}"
