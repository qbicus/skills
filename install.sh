#!/usr/bin/env bash
set -euo pipefail

ACTION="install"
TARGET=""
PROFILE=""
CODEX_PROFILE=""
CLAUDE_PROFILE=""
REPOSITORY_URL="${AI_FRAMEWORK_REPO_URL:-https://github.com/qbicus/skills.git}"
YES=0
DRY_RUN=0
VERBOSE=0
SKIP_AIINDEX=0
SKIP_GRAPHIFY=0
SKIP_FRAMEWORK_UPDATE=0
NO_AIINDEX_UPDATE=0
APPLY=""
JSON_OUTPUT=0
FRAMEWORK_ROOT="${HOME}/.ai"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=11
MAX_PYTHON_MINOR=14
INTERACTIVE_MODE=0

usage() {
  cat <<'EOU'
Usage: install.sh [install|update-repair|change-profile|check-updates|uninstall|doctor] [options]

Run without arguments to open the interactive installer.

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
  --skip-framework-update
  --no-aiindex-update
  --apply framework|aiindex|both
  --json-output
EOU
}

if [[ $# -eq 0 ]]; then
  INTERACTIVE_MODE=1
else
  if [[ "$1" != --* ]]; then ACTION="$1"; shift; fi
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
      --skip-framework-update) SKIP_FRAMEWORK_UPDATE=1; shift ;;
      --no-aiindex-update) NO_AIINDEX_UPDATE=1; shift ;;
      --apply) APPLY="$2"; shift 2 ;;
      --json-output) JSON_OUTPUT=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
  done
fi

case "$ACTION" in install|update-repair|change-profile|check-updates|uninstall|doctor) ;; *) echo "Invalid action: $ACTION" >&2; exit 2 ;; esac
if [[ -n "$TARGET" ]]; then case "$TARGET" in codex|claude|both) ;; *) echo "Invalid target: $TARGET" >&2; exit 2 ;; esac; fi

say() { printf '==> %s\n' "$*"; }

# Always read interactive answers from the controlling terminal when possible.
# This keeps `curl .../install.sh | bash` interactive instead of consuming the
# script pipe as prompt input.
tty_read_line() {
  local prompt="$1"
  local answer=""
  if [[ -r /dev/tty ]]; then
    IFS= read -r -p "$prompt" answer < /dev/tty || return 1
  else
    IFS= read -r -p "$prompt" answer || return 1
  fi
  printf '%s' "$answer"
}

confirm() {
  [[ "$YES" -eq 1 ]] && return 0
  local answer=""
  answer="$(tty_read_line "$1 [Y/n] ")" || return 1
  [[ -z "$answer" || "$answer" =~ ^[Yy]([Ee][Ss])?$ ]]
}

ensure_git() {
  if command -v git >/dev/null 2>&1; then export AI_FRAMEWORK_PREREQ_GIT_ORIGIN=pre-existing; return 0; fi
  say "Git is missing."
  if [[ "$DRY_RUN" -eq 1 ]]; then echo "Would install Git using the detected package manager."; export AI_FRAMEWORK_PREREQ_GIT_ORIGIN=would-install; return 0; fi
  confirm "Install Git?" || { echo "Cancelled." >&2; return 2; }
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
    echo "Git is required and no supported package manager was found." >&2; return 2
  fi
  command -v git >/dev/null 2>&1 || { echo "Git installation completed but git is not visible." >&2; return 2; }
  export AI_FRAMEWORK_PREREQ_GIT_ORIGIN=installed-by-framework
}

python_compatible() {
  local exe="$1"
  "$exe" -c "import sys; v=sys.version_info; raise SystemExit(0 if v.major == $MIN_PYTHON_MAJOR and $MIN_PYTHON_MINOR <= v.minor <= $MAX_PYTHON_MINOR else 1)" >/dev/null 2>&1
}

find_python() {
  if command -v python3 >/dev/null 2>&1 && python_compatible "$(command -v python3)"; then command -v python3; return 0; fi
  if command -v python >/dev/null 2>&1 && python_compatible "$(command -v python)"; then command -v python; return 0; fi
  return 1
}

python_any_version() {
  local exe=""
  if command -v python3 >/dev/null 2>&1; then exe="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then exe="$(command -v python)"
  else return 1
  fi
  "$exe" -c 'import platform; print(platform.python_version())' 2>/dev/null
}

detect_package_manager() {
  local pm
  for pm in apt-get dnf yum pacman zypper apk; do
    if command -v "$pm" >/dev/null 2>&1; then printf '%s' "$pm"; return 0; fi
  done
  printf 'none'
}

show_prerequisite_preflight() {
  local git_status python_status uv_status codex_status claude_status distro pm py any
  git_status='missing - will install'
  command -v git >/dev/null 2>&1 && git_status="$(git --version 2>/dev/null || printf installed)"

  py="$(find_python || true)"
  if [[ -n "$py" ]]; then
    python_status="$("$py" -c 'import platform,sys; print(platform.python_version()+" ("+sys.executable+") - supported")' 2>/dev/null)"
  else
    any="$(python_any_version || true)"
    if [[ -n "$any" ]]; then
      python_status="$any - unsupported; install/use Python 3.11-3.14"
    else
      python_status='missing - will install from package manager'
    fi
  fi

  uv_status='missing - will install'
  command -v uv >/dev/null 2>&1 && uv_status="$(uv --version 2>/dev/null || printf installed)"
  codex_status='not detected'
  if command -v codex >/dev/null 2>&1 || command -v chatgpt >/dev/null 2>&1 || [[ -d "$HOME/.codex" ]]; then codex_status='detected'; fi
  claude_status='not detected'
  if command -v claude >/dev/null 2>&1 || [[ -d "$HOME/.claude" ]]; then claude_status='detected'; fi
  distro='unknown'
  if [[ -r /etc/os-release ]]; then
    distro="$(. /etc/os-release; printf '%s' "${PRETTY_NAME:-${ID:-unknown}}")"
  fi
  pm="$(detect_package_manager)"

  printf '\n'
  ui_yellow 'Prerequisite preflight'; printf '\n'
  printf 'OS           %s\n' "$distro"
  printf 'Pkg manager  %s\n' "$pm"
  printf 'Git          %s\n' "$git_status"
  printf 'Python       %s\n' "$python_status"
  printf 'uv           %s\n' "$uv_status"
  printf 'Codex        %s\n' "$codex_status"
  printf 'Claude       %s\n' "$claude_status"
  printf '\n'
  ui_gray 'Supported framework Python: 3.11-3.14.'
  printf '\n'
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
    echo "Python is required and no supported package manager was found." >&2; return 2
  fi
}

PYTHON_EXE=""
ensure_python() {
  local found=""
  found="$(find_python || true)"
  if [[ -n "$found" ]]; then
    export AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN=pre-existing
    export AI_FRAMEWORK_PYTHON="$found"
    PYTHON_EXE="$found"
    return 0
  fi

  say "Compatible Python is missing (supported range ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}-${MIN_PYTHON_MAJOR}.${MAX_PYTHON_MINOR})." >&2
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Would install a Python package from the detected Linux package manager, then require version 3.11-3.14." >&2
    export AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN=would-install
    PYTHON_EXE=""
    return 0
  fi
  confirm "Install Python?" || { echo "Cancelled." >&2; return 2; }
  install_python_package || return $?
  found="$(find_python || true)"
  if [[ -z "$found" ]]; then
    echo "The package manager installed Python outside the supported 3.11-3.14 range. Install Python 3.11-3.14 (3.14 preferred where available) and rerun." >&2
    return 2
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
  confirm "Install uv using the official Astral installer?" || { echo "Cancelled." >&2; return 2; }
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    echo "curl or wget is required to bootstrap uv." >&2; return 2
  fi
  export PATH="$HOME/.local/bin:$PATH"
  command -v uv >/dev/null 2>&1 || { echo "uv installation completed but uv is not visible." >&2; return 2; }
  export AI_FRAMEWORK_PREREQ_UV_ORIGIN=installed-by-framework
}

resolve_root() {
  local requested_action="$1"
  local requested_dry_run="$2"
  local script_dir=""
  if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" && "${BASH_SOURCE[0]}" != /dev/stdin ]]; then
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  fi
  if [[ -f "$FRAMEWORK_ROOT/installer/installer.py" ]]; then echo "$FRAMEWORK_ROOT"; return 0; fi
  if [[ -n "$script_dir" && -f "$script_dir/installer/installer.py" ]]; then
    if [[ "$script_dir" == "$FRAMEWORK_ROOT" ]]; then echo "$script_dir"; return 0; fi
    if [[ "$requested_action" == "doctor" || "$requested_action" == "uninstall" || "$requested_action" == "check-updates" || "$requested_action" == "change-profile" ]]; then echo "$script_dir"; return 0; fi
    [[ "$requested_dry_run" -eq 1 ]] && { echo "$script_dir"; return 0; }
    [[ -e "$FRAMEWORK_ROOT" ]] && { echo "$FRAMEWORK_ROOT exists but is not a valid framework installation." >&2; return 2; }
    say "Installing framework from local checkout" >&2
    git clone "$script_dir" "$FRAMEWORK_ROOT" >&2
    echo "$FRAMEWORK_ROOT"; return 0
  fi
  if [[ -z "$REPOSITORY_URL" ]]; then
    if [[ "$requested_action" == "doctor" || "$requested_action" == "uninstall" || "$requested_action" == "check-updates" || "$requested_action" == "change-profile" ]]; then
      echo "No installed framework was found at $FRAMEWORK_ROOT. Install the framework first." >&2
      return 2
    fi
    echo "Set AI_FRAMEWORK_REPO_URL or pass --repository-url for bootstrap install." >&2
    return 2
  fi
  [[ "$requested_dry_run" -eq 1 ]] && { echo "$FRAMEWORK_ROOT"; return 0; }
  [[ -e "$FRAMEWORK_ROOT" ]] && { echo "$FRAMEWORK_ROOT already exists but is not a valid framework installation." >&2; return 2; }
  say "Cloning framework" >&2
  git clone "$REPOSITORY_URL" "$FRAMEWORK_ROOT" >&2
  echo "$FRAMEWORK_ROOT"
}

# ---------- Interactive UI ----------

ui_color() {
  local code="$1"; shift
  if [[ -t 1 ]]; then printf '\033[%sm%s\033[0m' "$code" "$*"; else printf '%s' "$*"; fi
}
ui_cyan() { ui_color '36' "$*"; }
ui_green() { ui_color '32' "$*"; }
ui_yellow() { ui_color '33' "$*"; }
ui_gray() { ui_color '90' "$*"; }
ui_red() { ui_color '31' "$*"; }

clear_screen() {
  if command -v clear >/dev/null 2>&1; then clear; else printf '\033[2J\033[H'; fi
}

get_version_info() {
  local framework='?'
  local aiindex='?'
  local version_file="$FRAMEWORK_ROOT/version.json"
  local state_file="$FRAMEWORK_ROOT/local/installer-state.json"
  local py=""
  py="$(find_python || true)"
  if [[ -n "$py" && -f "$version_file" ]]; then
    framework="$($py -c 'import json,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); print(d.get("framework","?"))' "$version_file" 2>/dev/null || printf '?')"
    aiindex="$($py -c 'import json,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); print(d.get("aiIndex","?"))' "$version_file" 2>/dev/null || printf '?')"
  fi
  if [[ -n "$py" && -f "$state_file" ]]; then
    local vals
    vals="$($py -c 'import json,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); print(d.get("frameworkVersion", "")); print((d.get("aiIndex") or {}).get("version", ""))' "$state_file" 2>/dev/null || true)"
    local sf sa
    sf="$(printf '%s\n' "$vals" | sed -n '1p')"
    sa="$(printf '%s\n' "$vals" | sed -n '2p')"
    [[ -n "$sf" ]] && framework="$sf"
    [[ -n "$sa" ]] && aiindex="$sa"
  fi
  aiindex="${aiindex#aiindex-}"
  printf '%s|%s' "$framework" "$aiindex"
}

show_banner() {
  local versions fw ai
  versions="$(get_version_info)"
  fw="${versions%%|*}"
  ai="${versions#*|}"
  ui_cyan '    _    ___   _____                                            _'; printf '\n'
  ui_cyan '   / \  |_ _| |  ___| __ __ _ _ __ ___   _____      _____  _ __| | __'; printf '\n'
  ui_cyan "  / _ \\  | |  | |_ | '__/ _\` | '_ \` _ \\ / _ \\ \\ /\\ / / _ \\| '__| |/ /"; printf '\n'
  ui_cyan ' / ___ \ | |  |  _|| | | (_| | | | | | |  __/\ V  V / (_) | |  |   <'; printf '\n'
  ui_cyan '/_/   \_\___| |_|  |_|  \__,_|_| |_| |_|\___| \_/\_/ \___/|_|  |_|\_\'; printf '\n\n'
  printf 'AI Framework v%s  ' "$fw"; ui_gray "[AiIndex $ai]"; printf '\n\n'
}

read_key() {
  local key rest
  if [[ -r /dev/tty ]]; then
    IFS= read -rsn1 key < /dev/tty || return 1
  else
    IFS= read -rsn1 key || return 1
  fi
  if [[ "$key" == $'\e' ]]; then
    if [[ -r /dev/tty ]]; then
      IFS= read -rsn2 -t 0.05 rest < /dev/tty || true
    else
      IFS= read -rsn2 -t 0.05 rest || true
    fi
    key+="$rest"
  fi
  printf '%s' "$key"
}

SINGLE_SELECT_RESULT=-1
single_select() {
  local title="$1" default_index="$2" allow_back="$3"; shift 3
  local -a options=("$@")
  local index="$default_index" key i
  (( index < 0 )) && index=0
  (( index >= ${#options[@]} )) && index=$((${#options[@]} - 1))
  while true; do
    clear_screen; show_banner
    ui_yellow "$title"; printf '\n\n'
    for ((i=0; i<${#options[@]}; i++)); do
      if (( i == index )); then printf '> '; ui_green "${options[$i]}"; printf '\n'; else printf '  %s\n' "${options[$i]}"; fi
    done
    printf '\n'; ui_gray 'Up/Down Navigate   Enter Select'; [[ "$allow_back" == 1 ]] && ui_gray '   Esc Back'; printf '\n'
    key="$(read_key)" || return 1
    case "$key" in
      $'\e[A'|k) index=$(( (index - 1 + ${#options[@]}) % ${#options[@]} )) ;;
      $'\e[B'|j) index=$(( (index + 1) % ${#options[@]} )) ;;
      ''|$'\n'|$'\r') SINGLE_SELECT_RESULT="$index"; return 0 ;;
      $'\e') if [[ "$allow_back" == 1 ]]; then SINGLE_SELECT_RESULT=-1; return 0; fi ;;
    esac
  done
}

MULTI_SELECT_RESULT=()
multi_select() {
  local title="$1" defaults_csv="$2" allow_back="$3"; shift 3
  local -a options=("$@") selected=()
  local index=0 key i mark
  IFS=',' read -r -a selected <<< "$defaults_csv"
  while ((${#selected[@]} < ${#options[@]})); do selected+=(0); done
  while true; do
    clear_screen; show_banner
    ui_yellow "$title"; printf '\n\n'
    for ((i=0; i<${#options[@]}; i++)); do
      [[ "${selected[$i]}" == 1 ]] && mark='[x]' || mark='[ ]'
      if (( i == index )); then printf '> '; ui_green "$mark ${options[$i]}"; printf '\n'; else printf '  %s %s\n' "$mark" "${options[$i]}"; fi
    done
    printf '\n'; ui_gray 'Up/Down Move   Space Toggle   Enter Continue'; [[ "$allow_back" == 1 ]] && ui_gray '   Esc Back'; printf '\n'
    key="$(read_key)" || return 1
    case "$key" in
      $'\e[A'|k) index=$(( (index - 1 + ${#options[@]}) % ${#options[@]} )) ;;
      $'\e[B'|j) index=$(( (index + 1) % ${#options[@]} )) ;;
      ' ') [[ "${selected[$index]}" == 1 ]] && selected[$index]=0 || selected[$index]=1 ;;
      ''|$'\n'|$'\r')
        for i in "${selected[@]}"; do if [[ "$i" == 1 ]]; then MULTI_SELECT_RESULT=("${selected[@]}"); return 0; fi; done
        ;;
      $'\e') if [[ "$allow_back" == 1 ]]; then MULTI_SELECT_RESULT=(); return 0; fi ;;
    esac
  done
}

get_local_profiles() {
  local codex='medium' claude='medium'
  local path="$FRAMEWORK_ROOT/local/provider-profiles.json"
  local py="$(find_python || true)"
  if [[ -n "$py" && -f "$path" ]]; then
    local vals
    vals="$($py -c 'import json,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); p=d.get("profiles") or {}; print(p.get("codex","medium")); print(p.get("claude","medium"))' "$path" 2>/dev/null || true)"
    [[ -n "$vals" ]] && codex="$(printf '%s\n' "$vals" | sed -n '1p')" && claude="$(printf '%s\n' "$vals" | sed -n '2p')"
  fi
  printf '%s|%s' "$codex" "$claude"
}

get_installed_client_defaults() {
  local c=0 l=0
  local state="$FRAMEWORK_ROOT/local/installer-state.json"
  local py="$(find_python || true)"
  if [[ -n "$py" && -f "$state" ]]; then
    local clients
    clients="$($py -c 'import json,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); print(" ".join(d.get("installedClients") or []))' "$state" 2>/dev/null || true)"
    [[ " $clients " == *' codex '* ]] && c=1
    [[ " $clients " == *' claude '* ]] && l=1
  fi
  [[ $c -eq 0 && $l -eq 0 && -d "$HOME/.codex" ]] && c=1
  [[ $c -eq 0 && $l -eq 0 && -d "$HOME/.claude" ]] && l=1
  [[ $c -eq 0 && $l -eq 0 ]] && c=1
  printf '%s,%s' "$c" "$l"
}

selection_to_target() {
  local c="$1" l="$2"
  if [[ "$c" == 1 && "$l" == 1 ]]; then printf 'both'; elif [[ "$c" == 1 ]]; then printf 'codex'; else printf 'claude'; fi
}

SELECT_PROFILE_RESULT=''
select_profile() {
  local client="$1" current="${2:-medium}" default=1
  [[ "$current" == low ]] && default=0
  [[ "$current" == high ]] && default=2
  single_select "$client profile" "$default" 1 'Low (usage-saving)' 'Medium (recommended)' 'High (quality-first)'
  [[ "$SINGLE_SELECT_RESULT" -lt 0 ]] && { SELECT_PROFILE_RESULT=''; return 0; }
  case "$SINGLE_SELECT_RESULT" in 0) SELECT_PROFILE_RESULT='low';; 1) SELECT_PROFILE_RESULT='medium';; 2) SELECT_PROFILE_RESULT='high';; esac
}

invoke_core_action() {
  local selected_action="$1" selected_target="${2:-}" selected_codex_profile="${3:-}" selected_claude_profile="${4:-}" requested_dry_run="${5:-0}" requested_yes="${6:-0}" requested_skip_fw="${7:-0}" requested_no_ai_update="${8:-0}" apply="${9:-}" json_output="${10:-0}" capture="${11:-0}"
  local old_action="$ACTION" old_dry="$DRY_RUN" old_yes="$YES"
  local root installer output rc
  local -a args
  ACTION="$selected_action"; DRY_RUN="$requested_dry_run"; YES="$requested_yes"; PYTHON_EXE=''

  if [[ "$selected_action" == install || "$selected_action" == update-repair ]]; then
    ensure_git || { rc=$?; ACTION="$old_action"; DRY_RUN="$old_dry"; YES="$old_yes"; return "$rc"; }
    ensure_python || { rc=$?; ACTION="$old_action"; DRY_RUN="$old_dry"; YES="$old_yes"; return "$rc"; }
    ensure_uv || { rc=$?; ACTION="$old_action"; DRY_RUN="$old_dry"; YES="$old_yes"; return "$rc"; }
  else
    PYTHON_EXE="$(find_python || true)"
    if [[ -z "$PYTHON_EXE" ]]; then
      echo "Python 3.11-3.14 is required to run '$selected_action'." >&2
      ACTION="$old_action"; DRY_RUN="$old_dry"; YES="$old_yes"; return 2
    fi
    export AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN=pre-existing
  fi

  root="$(resolve_root "$selected_action" "$requested_dry_run")" || { rc=$?; ACTION="$old_action"; DRY_RUN="$old_dry"; YES="$old_yes"; return "$rc"; }
  installer="$root/installer/installer.py"
  if [[ -z "$PYTHON_EXE" ]]; then
    echo "Preview cannot execute the shared installer core because compatible Python is not currently installed. A real run would install Python first." >&2
    ACTION="$old_action"; DRY_RUN="$old_dry"; YES="$old_yes"; return 2
  fi
  if [[ ! -f "$installer" && "$requested_dry_run" -eq 0 ]]; then
    echo "Installer core not found: $installer" >&2
    ACTION="$old_action"; DRY_RUN="$old_dry"; YES="$old_yes"; return 2
  fi

  args=("$installer" "$selected_action")
  [[ -n "$selected_target" ]] && args+=(--target "$selected_target")
  [[ -n "$selected_codex_profile" ]] && args+=(--codex-profile "$selected_codex_profile")
  [[ -n "$selected_claude_profile" ]] && args+=(--claude-profile "$selected_claude_profile")
  [[ "$requested_yes" -eq 1 ]] && args+=(--yes)
  [[ "$requested_dry_run" -eq 1 ]] && args+=(--dry-run)
  [[ "$VERBOSE" -eq 1 ]] && args+=(--verbose)
  [[ "$SKIP_AIINDEX" -eq 1 ]] && args+=(--skip-aiindex)
  [[ "$SKIP_GRAPHIFY" -eq 1 ]] && args+=(--skip-graphify)
  [[ "$requested_skip_fw" -eq 1 ]] && args+=(--skip-framework-update)
  [[ "$requested_no_ai_update" -eq 1 ]] && args+=(--no-aiindex-update)
  [[ -n "$apply" ]] && args+=(--apply "$apply")
  [[ "$json_output" -eq 1 ]] && args+=(--json-output)

  [[ "$capture" -eq 0 ]] && say "$selected_action"
  if [[ "$capture" -eq 1 ]]; then
    if output="$($PYTHON_EXE "${args[@]}" 2>&1)"; then rc=0; else rc=$?; fi
    [[ "$rc" -eq 0 ]] && printf '%s' "$output" || printf '%s\n' "$output" >&2
  else
    if "$PYTHON_EXE" "${args[@]}"; then rc=0; else rc=$?; fi
  fi
  ACTION="$old_action"; DRY_RUN="$old_dry"; YES="$old_yes"
  return "$rc"
}

pause_for_menu() {
  printf '\n'; ui_gray "${1:-Press Enter to return to menu}"; printf '\n'
  local key
  while true; do key="$(read_key)" || return 0; [[ -z "$key" || "$key" == $'\r' || "$key" == $'\n' ]] && return 0; done
}

show_operation_result() {
  local code="$1"
  printf '\n'
  if [[ "$code" -eq 0 ]]; then ui_green 'Completed successfully.'; else ui_yellow "Operation returned exit code $code."; fi
  printf '\n'
  pause_for_menu
}

get_update_status_json() {
  invoke_core_action check-updates '' '' '' 0 0 0 0 '' 1 1
}

invoke_install_flow() {
  local preview="${1:-0}" title target codex_p='' claude_p='' rc confirm_idx
  [[ "$preview" -eq 1 ]] && title='Preview Install - select clients' || title='Install - select clients'
  multi_select "$title" '1,0' 1 'Codex' 'Claude'
  ((${#MULTI_SELECT_RESULT[@]} == 0)) && return 0
  target="$(selection_to_target "${MULTI_SELECT_RESULT[0]}" "${MULTI_SELECT_RESULT[1]}")"
  if [[ "${MULTI_SELECT_RESULT[0]}" == 1 ]]; then select_profile Codex medium; codex_p="$SELECT_PROFILE_RESULT"; [[ -z "$codex_p" ]] && return 0; fi
  if [[ "${MULTI_SELECT_RESULT[1]}" == 1 ]]; then select_profile Claude medium; claude_p="$SELECT_PROFILE_RESULT"; [[ -z "$claude_p" ]] && return 0; fi

  clear_screen; show_banner
  [[ "$preview" -eq 1 ]] && ui_yellow 'Preview Install' || ui_yellow 'Ready to install'; printf '\n\n'
  [[ -n "$codex_p" ]] && printf 'Codex   %s\n' "$codex_p"
  [[ -n "$claude_p" ]] && printf 'Claude  %s\n' "$claude_p"
  printf '\n'; ui_gray 'Components: AI Framework, skills, AiIndex CLI/MCP, Graphify, native wiring'; printf '\n'
  show_prerequisite_preflight
  if [[ "$preview" -eq 0 ]]; then
    pause_for_menu 'Press Enter to continue to install confirmation'
    single_select 'Continue?' 0 1 'Install' 'Cancel'; confirm_idx="$SINGLE_SELECT_RESULT"
    [[ "$confirm_idx" -ne 0 ]] && return 0
  fi
  if invoke_core_action install "$target" "$codex_p" "$claude_p" "$preview" 1; then rc=0; else rc=$?; fi
  show_operation_result "$rc"
}

invoke_repair_flow() {
  local preview="${1:-0}" profiles codex_current claude_current defaults title target status rc skip_fw=1 no_ai=1 choice
  profiles="$(get_local_profiles)"; codex_current="${profiles%%|*}"; claude_current="${profiles#*|}"
  defaults="$(get_installed_client_defaults)"
  [[ "$preview" -eq 1 ]] && title='Preview Update / Repair - select clients' || title='Update / Repair - select clients'
  multi_select "$title" "$defaults" 1 "Codex ($codex_current)" "Claude ($claude_current)"
  ((${#MULTI_SELECT_RESULT[@]} == 0)) && return 0
  target="$(selection_to_target "${MULTI_SELECT_RESULT[0]}" "${MULTI_SELECT_RESULT[1]}")"

  clear_screen; show_banner
  [[ "$preview" -eq 1 ]] && ui_yellow 'Preview Update / Repair' || ui_yellow 'Update / Repair preflight'
  printf '\n'
  show_prerequisite_preflight

  status="$(get_update_status_json 2>/dev/null || true)"
  if [[ -n "$status" && "$(find_python || true)" != '' ]]; then
    local py="$(find_python)" summary has_updates
    summary="$($py -c 'import json,sys; d=json.loads(sys.stdin.read()); f=d.get("framework") or {}; i=d.get("aiIndex") or {}; a=(["Framework %s -> %s" % (f.get("current"), f.get("latest"))] if f.get("updateAvailable") else []) + (["AiIndex %s -> %s" % (i.get("current"), i.get("latest"))] if i.get("updateAvailable") else []); print("\n".join(a))' <<< "$status" 2>/dev/null || true)"
    if [[ -n "$summary" ]]; then
      single_select "Updates are available:\n$summary\n\nInclude available updates in this repair?" 0 1 'Yes - update and repair' 'No - repair only'
      choice="$SINGLE_SELECT_RESULT"; [[ "$choice" -lt 0 ]] && return 0
      [[ "$choice" -eq 0 ]] && skip_fw=0 && no_ai=0
    fi
  fi
  if invoke_core_action update-repair "$target" '' '' "$preview" 1 "$skip_fw" "$no_ai"; then rc=0; else rc=$?; fi
  show_operation_result "$rc"
}

invoke_change_profile_flow() {
  local preview="${1:-0}" profiles codex_current claude_current defaults title target codex_p='' claude_p='' rc
  profiles="$(get_local_profiles)"; codex_current="${profiles%%|*}"; claude_current="${profiles#*|}"
  defaults="$(get_installed_client_defaults)"
  [[ "$preview" -eq 1 ]] && title='Preview Change profiles - select clients' || title='Change profiles - select clients'
  multi_select "$title" "$defaults" 1 "Codex (current: $codex_current)" "Claude (current: $claude_current)"
  ((${#MULTI_SELECT_RESULT[@]} == 0)) && return 0
  target="$(selection_to_target "${MULTI_SELECT_RESULT[0]}" "${MULTI_SELECT_RESULT[1]}")"
  if [[ "${MULTI_SELECT_RESULT[0]}" == 1 ]]; then select_profile Codex "$codex_current"; codex_p="$SELECT_PROFILE_RESULT"; [[ -z "$codex_p" ]] && return 0; fi
  if [[ "${MULTI_SELECT_RESULT[1]}" == 1 ]]; then select_profile Claude "$claude_current"; claude_p="$SELECT_PROFILE_RESULT"; [[ -z "$claude_p" ]] && return 0; fi
  if invoke_core_action change-profile "$target" "$codex_p" "$claude_p" "$preview" 1; then rc=0; else rc=$?; fi
  show_operation_result "$rc"
}

invoke_check_updates_flow() {
  clear_screen; show_banner; ui_yellow 'Checking for updates...'; printf '\n'
  local status py fw_line ai_line fw_need ai_need defaults rc apply=''
  status="$(get_update_status_json 2>/dev/null || true)"
  if [[ -z "$status" ]]; then ui_red 'Could not retrieve update status.'; printf '\n'; pause_for_menu; return 0; fi
  py="$(find_python || true)"
  [[ -z "$py" ]] && { ui_red 'Python is required to parse update status.'; printf '\n'; pause_for_menu; return 0; }
  fw_line="$($py -c 'import json,sys; d=json.loads(sys.stdin.read()); x=d.get("framework") or {}; print(("unknown - "+str(x.get("error"))) if x.get("error") else (("%s -> %s UPDATE AVAILABLE" % (x.get("current"), x.get("latest"))) if x.get("updateAvailable") else ("%s current" % x.get("current"))))' <<< "$status")"
  ai_line="$($py -c 'import json,sys; d=json.loads(sys.stdin.read()); x=d.get("aiIndex") or {}; print(("unknown - "+str(x.get("error"))) if x.get("error") else (("%s -> %s REPAIR NEEDED" % (x.get("current"), x.get("latest"))) if not x.get("healthy",True) else (("%s -> %s UPDATE AVAILABLE" % (x.get("current"), x.get("latest"))) if x.get("updateAvailable") else ("%s current" % x.get("current")))))' <<< "$status")"
  fw_need="$($py -c 'import json,sys; d=json.loads(sys.stdin.read()); print(1 if (d.get("framework") or {}).get("updateAvailable") else 0)' <<< "$status")"
  ai_need="$($py -c 'import json,sys; d=json.loads(sys.stdin.read()); x=d.get("aiIndex") or {}; print(1 if x.get("updateAvailable") or not x.get("healthy",True) else 0)' <<< "$status")"
  clear_screen; show_banner; ui_yellow 'Check for updates'; printf '\n\nFramework  %s\nAiIndex    %s\n' "$fw_line" "$ai_line"
  [[ "$fw_need" == 0 && "$ai_need" == 0 ]] && { pause_for_menu; return 0; }
  local -a opts=() keys=() defs=()
  if [[ "$fw_need" == 1 ]]; then opts+=('Framework'); keys+=('framework'); defs+=(1); fi
  if [[ "$ai_need" == 1 ]]; then opts+=('AiIndex'); keys+=('aiindex'); defs+=(1); fi
  defaults="$(IFS=,; echo "${defs[*]}")"
  multi_select 'Select updates to apply' "$defaults" 1 "${opts[@]}"
  ((${#MULTI_SELECT_RESULT[@]} == 0)) && return 0
  local -a chosen=(); local i
  for ((i=0;i<${#MULTI_SELECT_RESULT[@]};i++)); do [[ "${MULTI_SELECT_RESULT[$i]}" == 1 ]] && chosen+=("${keys[$i]}"); done
  ((${#chosen[@]} == 2)) && apply='both' || apply="${chosen[0]}"
  if invoke_core_action check-updates '' '' '' 0 1 0 0 "$apply"; then rc=0; else rc=$?; fi
  show_operation_result "$rc"
}

invoke_uninstall_flow() {
  local preview="${1:-0}" profiles codex_current claude_current defaults title target rc choice
  profiles="$(get_local_profiles)"; codex_current="${profiles%%|*}"; claude_current="${profiles#*|}"
  defaults="$(get_installed_client_defaults)"
  [[ "$preview" -eq 1 ]] && title='Preview Uninstall - select clients' || title='Uninstall - select clients'
  multi_select "$title" "$defaults" 1 "Codex ($codex_current)" "Claude ($claude_current)"
  ((${#MULTI_SELECT_RESULT[@]} == 0)) && return 0
  target="$(selection_to_target "${MULTI_SELECT_RESULT[0]}" "${MULTI_SELECT_RESULT[1]}")"
  clear_screen; show_banner; [[ "$preview" -eq 1 ]] && ui_yellow 'Preview Uninstall' || ui_yellow 'Ready to uninstall'; printf '\n\n'
  printf 'Will remove framework-owned client wiring, generated agents and managed skill links.\n'
  ui_gray 'Will preserve Python, Git, uv, unrelated settings/skills, repo overrides and .ai-index data.'; printf '\n'
  if [[ "$preview" -eq 0 ]]; then
    printf '\n'; single_select 'Continue?' 1 1 'Uninstall' 'Cancel'; choice="$SINGLE_SELECT_RESULT"; [[ "$choice" -ne 0 ]] && return 0
  fi
  if invoke_core_action uninstall "$target" '' '' "$preview" 1; then rc=0; else rc=$?; fi
  show_operation_result "$rc"
}

invoke_doctor_flow() {
  clear_screen; show_banner
  local rc
  if invoke_core_action doctor; then rc=0; else rc=$?; fi
  pause_for_menu
}

invoke_preview_flow() {
  single_select 'Preview which operation?' 0 1 'Install' 'Update / Repair' 'Change profiles' 'Uninstall'
  case "$SINGLE_SELECT_RESULT" in 0) invoke_install_flow 1;; 1) invoke_repair_flow 1;; 2) invoke_change_profile_flow 1;; 3) invoke_uninstall_flow 1;; esac
}

start_interactive_installer() {
  while true; do
    single_select 'AI Framework Installer' 0 0 'Install' 'Update / Repair' 'Change profiles' 'Check for updates' 'Uninstall' 'Doctor' 'Preview changes' 'Exit'
    case "$SINGLE_SELECT_RESULT" in
      0) invoke_install_flow 0 ;;
      1) invoke_repair_flow 0 ;;
      2) invoke_change_profile_flow 0 ;;
      3) invoke_check_updates_flow ;;
      4) invoke_uninstall_flow 0 ;;
      5) invoke_doctor_flow ;;
      6) invoke_preview_flow ;;
      7) clear_screen; return 0 ;;
    esac
  done
}

if [[ "$INTERACTIVE_MODE" -eq 1 ]]; then
  start_interactive_installer
  exit 0
fi

# ---------- CLI mode ----------

if [[ "$ACTION" == install || "$ACTION" == update-repair ]]; then
  show_prerequisite_preflight
  ensure_git
  ensure_python
  ensure_uv
else
  PYTHON_EXE="$(find_python || true)"
  if [[ -z "$PYTHON_EXE" ]]; then
    echo "Python 3.11-3.14 is required to run '$ACTION'. Doctor/uninstall do not install system prerequisites automatically." >&2
    exit 2
  fi
  export AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN=pre-existing
fi
ROOT="$(resolve_root "$ACTION" "$DRY_RUN")"
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
[[ "$SKIP_FRAMEWORK_UPDATE" -eq 1 ]] && ARGS+=(--skip-framework-update)
[[ "$NO_AIINDEX_UPDATE" -eq 1 ]] && ARGS+=(--no-aiindex-update)
[[ -n "$APPLY" ]] && ARGS+=(--apply "$APPLY")
[[ "$JSON_OUTPUT" -eq 1 ]] && ARGS+=(--json-output)

say "$ACTION"
exec "$PYTHON_EXE" "${ARGS[@]}"
