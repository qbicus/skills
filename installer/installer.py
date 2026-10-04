#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = FRAMEWORK_ROOT / "installer" / "config.json"
STATE_PATH = FRAMEWORK_ROOT / "local" / "installer-state.json"
PROFILES_PATH = FRAMEWORK_ROOT / "local" / "provider-profiles.json"
MANAGED_BEGIN = "# BEGIN COMPANY AI FRAMEWORK"
MANAGED_END = "# END COMPANY AI FRAMEWORK"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def run(cmd: list[str], *, check: bool = True, capture: bool = False, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    kwargs: dict[str, Any] = {"text": True, "cwd": str(cwd) if cwd else None, "env": env}
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    proc = subprocess.run(cmd, **kwargs)
    if check and proc.returncode != 0:
        detail = ""
        if capture:
            detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}" + (f"\n{detail}" if detail else ""))
    return proc


def which(name: str) -> str | None:
    result = shutil.which(name)
    if result:
        return result
    home = Path.home()
    candidates: list[Path] = []
    if os.name == "nt":
        candidates += [home / ".local" / "bin" / f"{name}.exe", home / ".local" / "bin" / name]
    else:
        candidates += [home / ".local" / "bin" / name]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def command_version(name: str, args: list[str] | None = None) -> str | None:
    exe = which(name)
    if not exe:
        return None
    proc = run([exe, *(args or ["--version"])], check=False, capture=True)
    text = ((proc.stdout or "") + " " + (proc.stderr or "")).strip().splitlines()
    return text[0].strip() if text else "installed"


def git_commit(root: Path) -> str | None:
    if not (root / ".git").exists() or not which("git"):
        return None
    proc = run([which("git") or "git", "rev-parse", "HEAD"], check=False, capture=True, cwd=root)
    return proc.stdout.strip() if proc.returncode == 0 else None


def default_state() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "frameworkRoot": str(FRAMEWORK_ROOT),
        "frameworkCommit": git_commit(FRAMEWORK_ROOT),
        "installedClients": [],
        "profiles": {},
        "links": [],
        "configOwnership": {},
        "aiIndex": {},
        "graphify": {"managedClients": []},
        "pathChanges": [],
        "prerequisites": {},
    }


def load_state() -> dict[str, Any]:
    state = load_json(STATE_PATH, default_state())
    base = default_state()
    for key, value in base.items():
        state.setdefault(key, value)
    return state


def record_bootstrap_prerequisites(state: dict[str, Any]) -> None:
    mapping = {
        "git": "AI_FRAMEWORK_PREREQ_GIT_ORIGIN",
        "python": "AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN",
        "uv": "AI_FRAMEWORK_PREREQ_UV_ORIGIN",
    }
    prereqs = state.setdefault("prerequisites", {})
    for name, env_name in mapping.items():
        origin = os.environ.get(env_name)
        if origin and origin != "would-install":
            entry = prereqs.setdefault(name, {})
            entry["origin"] = origin
    prereqs.setdefault("python", {})["version"] = platform.python_version()
    prereqs["python"]["executable"] = sys.executable
    git_version = command_version("git")
    if git_version:
        prereqs.setdefault("git", {})["version"] = git_version
    uv_version = command_version("uv")
    if uv_version:
        prereqs.setdefault("uv", {})["version"] = uv_version


def target_clients(target: str) -> list[str]:
    return ["codex", "claude"] if target == "both" else [target]


def choose_target(current: str | None, yes: bool) -> str:
    if current:
        return current
    if yes:
        raise RuntimeError("--target is required with --yes/non-interactive use")
    print("Select target:")
    print("  1. Codex")
    print("  2. Claude")
    print("  3. Both")
    value = input("Target [3]: ").strip() or "3"
    mapping = {"1": "codex", "2": "claude", "3": "both", "codex": "codex", "claude": "claude", "both": "both"}
    if value.lower() not in mapping:
        raise RuntimeError(f"Invalid target selection: {value}")
    return mapping[value.lower()]


def load_active_profiles() -> dict[str, str]:
    """Load the framework's persisted provider-profile selection.

    Current profile state uses {"version": 1, "profiles": {...}}.  Older flat
    mappings are still accepted so Doctor/repair can adopt pre-installer setups.
    """
    data = load_json(PROFILES_PATH, {})
    profiles = data.get("profiles", data) if isinstance(data, dict) else {}
    if not isinstance(profiles, dict):
        return {}
    return {str(k): str(v) for k, v in profiles.items() if isinstance(v, str)}


def choose_profile(client: str, explicit: str | None, state: dict[str, Any], yes: bool) -> str:
    if explicit:
        return explicit
    # The framework's live profile selection is authoritative. Installer state
    # records ownership/history and can be stale or absent for manual installs.
    current = load_active_profiles().get(client) or state.get("profiles", {}).get(client)
    if yes:
        return current or "medium"
    print(f"Select {client} usage profile:")
    print("  1. Low    (usage-saving)")
    print("  2. Medium (recommended)")
    print("  3. High   (quality-first)")
    default_num = {"low": "1", "medium": "2", "high": "3"}.get(current or "medium", "2")
    value = input(f"Profile [{default_num}]: ").strip() or default_num
    mapping = {"1": "low", "2": "medium", "3": "high", "low": "low", "medium": "medium", "high": "high"}
    if value.lower() not in mapping:
        raise RuntimeError(f"Invalid profile selection: {value}")
    return mapping[value.lower()]


def ask(prompt: str, default: bool = True) -> bool:
    suffix = " [Y/n] " if default else " [y/N] "
    answer = input(prompt + suffix).strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


def ensure_parent(path: Path, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)


def backup_file(path: Path, dry_run: bool) -> Path | None:
    if not path.exists():
        return None
    backup_dir = FRAMEWORK_ROOT / "local" / "backups"
    backup = backup_dir / (path.name + ".before-company-ai")
    if dry_run:
        print(f"  would back up {path} -> {backup}")
        return backup
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup)
    return backup


def managed_markdown(path: Path, body: str, dry_run: bool) -> None:
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(re.escape(MANAGED_BEGIN) + r".*?" + re.escape(MANAGED_END), re.S)
    block = f"{MANAGED_BEGIN}\n{body.rstrip()}\n{MANAGED_END}"
    if pattern.search(original):
        updated = pattern.sub(block, original, count=1)
    else:
        sep = "" if not original else ("" if original.endswith("\n") else "\n") + "\n"
        updated = original + sep + block + "\n"
    if updated == original:
        return
    print(f"  {'would update' if dry_run else 'updated'} {path}")
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")


def remove_managed_markdown(path: Path, dry_run: bool) -> None:
    if not path.exists():
        return
    original = path.read_text(encoding="utf-8")
    pattern = re.compile(r"\n?" + re.escape(MANAGED_BEGIN) + r".*?" + re.escape(MANAGED_END) + r"\n?", re.S)
    updated = pattern.sub("\n", original).strip("\n")
    updated = updated + ("\n" if updated else "")
    if updated != original:
        print(f"  {'would clean' if dry_run else 'cleaned'} {path}")
        if not dry_run:
            path.write_text(updated, encoding="utf-8")


def create_dir_link(link: Path, target: Path, dry_run: bool) -> str:
    if link.exists() or link.is_symlink():
        try:
            if link.resolve() == target.resolve():
                return "existing"
        except OSError:
            pass
        raise RuntimeError(f"Refusing to replace unrelated existing path: {link}")
    print(f"  {'would link' if dry_run else 'linked'} {link} -> {target}")
    if dry_run:
        return "planned"
    link.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, stdout=subprocess.DEVNULL)
    else:
        link.symlink_to(target, target_is_directory=True)
    return "created"


def create_file_link_or_copy(link: Path, target: Path, dry_run: bool) -> str:
    if link.exists() or link.is_symlink():
        try:
            if link.is_symlink() and link.resolve() == target.resolve():
                return "existing"
        except OSError:
            pass
        if link.is_file() and link.read_bytes() == target.read_bytes():
            return "existing-copy"
        raise RuntimeError(f"Refusing to replace unrelated existing path: {link}")
    print(f"  {'would link/copy' if dry_run else 'linked/copied'} {link} -> {target}")
    if dry_run:
        return "planned"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target)
        return "created-link"
    except OSError:
        shutil.copy2(target, link)
        return "created-copy"


def remove_owned_path(path: Path, dry_run: bool) -> None:
    if not (path.exists() or path.is_symlink()):
        return
    print(f"  {'would remove' if dry_run else 'removed'} {path}")
    if dry_run:
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif os.name == "nt":
        os.rmdir(path)  # junction: remove link only
    else:
        shutil.rmtree(path)


def list_skills() -> list[Path]:
    result: list[Path] = []
    for child in sorted((FRAMEWORK_ROOT / "skills").iterdir()):
        if child.is_dir() and (child / "SKILL.md").exists():
            result.append(child)
    return result


def wire_skills(client: str, state: dict[str, Any], dry_run: bool) -> None:
    home = Path.home()
    client_root = home / (".codex" if client == "codex" else ".claude")
    skill_root = client_root / "skills"
    for skill in list_skills():
        link = skill_root / skill.name
        outcome = create_dir_link(link, skill, dry_run)
        if outcome == "created" and str(link) not in state["links"]:
            state["links"].append(str(link))


def set_profile(client: str, profile: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  would set {client} profile -> {profile}")
        return
    profiles = load_active_profiles()
    profiles[client] = profile
    save_json(PROFILES_PATH, {"version": 1, "profiles": profiles})


def render_native(client: str, profile: str, dry_run: bool) -> Path:
    out = FRAMEWORK_ROOT / "generated" / client
    print(f"  {'would render' if dry_run else 'rendering'} {client}/{profile} native wiring -> {out}")
    if dry_run:
        return out
    if out.exists():
        shutil.rmtree(out)
    cmd = [sys.executable, str(FRAMEWORK_ROOT / "scripts" / "ai.py"), "provider", "--provider", client, "--profile", profile, "--render-native", str(out)]
    run(cmd)
    return out


def extract_codex_fragment(fragment: str) -> tuple[dict[str, str], str, dict[str, str]]:
    top: dict[str, str] = {}
    agents_root: dict[str, str] = {}
    lines = fragment.splitlines()
    sections_start = next((i for i, line in enumerate(lines) if line.strip().startswith("[")), len(lines))
    for line in lines[:sections_start]:
        m = re.match(r"^(model|model_reasoning_effort)\s*=\s*(.+)$", line.strip())
        if m:
            top[m.group(1)] = m.group(2)
    block_lines: list[str] = []
    in_agents_root = False
    for line in lines[sections_start:]:
        stripped = line.strip()
        if stripped == "[agents]":
            in_agents_root = True
            continue
        if stripped.startswith("["):
            in_agents_root = False
        if in_agents_root:
            m = re.match(r"^(enabled|max_concurrent_threads_per_session)\s*=\s*(.+)$", stripped)
            if m:
                agents_root[m.group(1)] = m.group(2)
            continue
        block_lines.append(line)
    return top, "\n".join(block_lines).strip() + "\n", agents_root


def toml_get_top(text: str, key: str) -> str | None:
    first_section = re.search(r"(?m)^\s*\[", text)
    prefix = text[: first_section.start()] if first_section else text
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", prefix)
    return m.group(1) if m else None


def toml_set_top(text: str, key: str, value: str | None) -> str:
    first_section = re.search(r"(?m)^\s*\[", text)
    cut = first_section.start() if first_section else len(text)
    prefix, suffix = text[:cut], text[cut:]
    pattern = re.compile(rf"(?m)^\s*{re.escape(key)}\s*=\s*.+?\s*$\n?")
    if value is None:
        prefix = pattern.sub("", prefix, count=1)
    elif pattern.search(prefix):
        prefix = pattern.sub(f"{key} = {value}\n", prefix, count=1)
    else:
        prefix = prefix.rstrip() + ("\n" if prefix.strip() else "") + f"{key} = {value}\n\n"
    return prefix + suffix


def toml_section_range(text: str, section: str) -> tuple[int, int] | None:
    pat = re.compile(rf"(?m)^\[{re.escape(section)}\]\s*$")
    m = pat.search(text)
    if not m:
        return None
    next_m = re.search(r"(?m)^\[", text[m.end():])
    end = m.end() + (next_m.start() if next_m else len(text[m.end():]))
    return m.start(), end


def toml_get_section_key(text: str, section: str, key: str) -> str | None:
    rng = toml_section_range(text, section)
    if not rng:
        return None
    body = text[rng[0]:rng[1]]
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body)
    return m.group(1) if m else None


def toml_set_section_key(text: str, section: str, key: str, value: str | None) -> str:
    rng = toml_section_range(text, section)
    if not rng:
        if value is None:
            return text
        text = text.rstrip() + f"\n\n[{section}]\n{key} = {value}\n"
        return text
    start, end = rng
    body = text[start:end]
    pattern = re.compile(rf"(?m)^\s*{re.escape(key)}\s*=\s*.+?\s*$\n?")
    if value is None:
        body = pattern.sub("", body, count=1)
    elif pattern.search(body):
        body = pattern.sub(f"{key} = {value}\n", body, count=1)
    else:
        body = body.rstrip() + f"\n{key} = {value}\n"
    return text[:start] + body + text[end:]


def remove_codex_owned_sections(text: str) -> str:
    # Installer owns all ai-* agent sections plus AiIndex MCP section.
    pattern = re.compile(r"(?ms)^\[agents\.ai-[^\]]+\]\s*.*?(?=^\[|\Z)")
    text = pattern.sub("", text)
    mcp = re.compile(r"(?ms)^\[mcp_servers\.aiindex\]\s*.*?(?=^\[|\Z)")
    return mcp.sub("", text)


def wire_codex(profile: str, state: dict[str, Any], dry_run: bool, aiindex_mcp: Path | None) -> None:
    generated = render_native("codex", profile, dry_run)
    config = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"
    instructions = config.parent / "AGENTS.md"
    managed_markdown(instructions, (FRAMEWORK_ROOT / "AGENTS.md").read_text(encoding="utf-8"), dry_run)
    wire_skills("codex", state, dry_run)
    if dry_run:
        print(f"  would merge Codex native config into {config}")
        return
    fragment = (generated / "config.fragment.toml").read_text(encoding="utf-8")
    top, agent_sections, agents_root = extract_codex_fragment(fragment)
    config.parent.mkdir(parents=True, exist_ok=True)
    text = config.read_text(encoding="utf-8") if config.exists() else ""
    ownership = state["configOwnership"].setdefault("codex", {})
    if "previous" not in ownership:
        ownership["previous"] = {
            "model": toml_get_top(text, "model"),
            "model_reasoning_effort": toml_get_top(text, "model_reasoning_effort"),
            "features.multi_agent": toml_get_section_key(text, "features", "multi_agent"),
            "agents.enabled": toml_get_section_key(text, "agents", "enabled"),
            "agents.max_concurrent_threads_per_session": toml_get_section_key(text, "agents", "max_concurrent_threads_per_session"),
        }
    text = remove_codex_owned_sections(text)
    for key, value in top.items():
        text = toml_set_top(text, key, value)
    text = toml_set_section_key(text, "features", "multi_agent", "true")
    for key, value in agents_root.items():
        text = toml_set_section_key(text, "agents", key, value)
    text = text.rstrip() + "\n\n" + agent_sections.rstrip() + "\n"
    if aiindex_mcp:
        command = str(aiindex_mcp).replace("\\", "\\\\")
        text += f"\n[mcp_servers.aiindex]\ncommand = \"{command}\"\n"
    backup_file(config, False)
    config.write_text(text, encoding="utf-8")
    print(f"  updated {config}")


def restore_codex(state: dict[str, Any], dry_run: bool) -> None:
    config = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"
    remove_managed_markdown(config.parent / "AGENTS.md", dry_run)
    if config.exists():
        text = config.read_text(encoding="utf-8")
        text = remove_codex_owned_sections(text)
        prev = state.get("configOwnership", {}).get("codex", {}).get("previous", {})
        text = toml_set_top(text, "model", prev.get("model"))
        text = toml_set_top(text, "model_reasoning_effort", prev.get("model_reasoning_effort"))
        text = toml_set_section_key(text, "features", "multi_agent", prev.get("features.multi_agent"))
        text = toml_set_section_key(text, "agents", "enabled", prev.get("agents.enabled"))
        text = toml_set_section_key(text, "agents", "max_concurrent_threads_per_session", prev.get("agents.max_concurrent_threads_per_session"))
        if not dry_run:
            config.write_text(text, encoding="utf-8")
        print(f"  {'would clean' if dry_run else 'cleaned'} {config}")


def wire_claude(profile: str, state: dict[str, Any], dry_run: bool, aiindex_mcp: Path | None) -> None:
    generated = render_native("claude", profile, dry_run)
    root = Path.home() / ".claude"
    settings = root / "settings.json"
    instructions = root / "CLAUDE.md"
    managed_markdown(instructions, f"@{(FRAMEWORK_ROOT / 'CLAUDE.md').as_posix()}", dry_run)
    wire_skills("claude", state, dry_run)
    if dry_run:
        print(f"  would merge Claude settings into {settings}")
        return
    fragment = load_json(generated / "settings.fragment.json", {})
    data = load_json(settings, {})
    ownership = state["configOwnership"].setdefault("claude", {})
    if "previous" not in ownership:
        ownership["previous"] = {key: data.get(key, "__MISSING__") for key in fragment}
    data.update(fragment)
    settings.parent.mkdir(parents=True, exist_ok=True)
    backup_file(settings, False)
    save_json(settings, data)
    print(f"  updated {settings}")
    agent_root = root / "agents"
    for source in sorted((generated / "agents").glob("ai-*.md")):
        dest = agent_root / source.name
        # A Windows machine without symlink privileges may have an installer-owned
        # copy here from an earlier run. Refresh that copy instead of treating it
        # as unrelated drift; true unrelated files are still refused.
        if str(dest) in state.get("links", []) and dest.exists() and not dest.is_symlink():
            if dest.read_bytes() != source.read_bytes():
                shutil.copy2(source, dest)
                print(f"  refreshed {dest}")
            continue
        outcome = create_file_link_or_copy(dest, source, False)
        if outcome.startswith("created") and str(dest) not in state["links"]:
            state["links"].append(str(dest))
    if aiindex_mcp and which("claude"):
        # Remove only our named registration before re-adding at user scope.
        run([which("claude") or "claude", "mcp", "remove", "aiindex", "--scope", "user"], check=False, capture=True)
        run([which("claude") or "claude", "mcp", "add", "--scope", "user", "aiindex", "--", str(aiindex_mcp)], check=False)


def restore_claude(state: dict[str, Any], dry_run: bool) -> None:
    root = Path.home() / ".claude"
    remove_managed_markdown(root / "CLAUDE.md", dry_run)
    settings = root / "settings.json"
    if settings.exists():
        data = load_json(settings, {})
        prev = state.get("configOwnership", {}).get("claude", {}).get("previous", {})
        for key, value in prev.items():
            if value == "__MISSING__":
                data.pop(key, None)
            else:
                data[key] = value
        if not dry_run:
            save_json(settings, data)
        print(f"  {'would restore' if dry_run else 'restored'} {settings}")
    if which("claude"):
        if dry_run:
            print("  would remove Claude user MCP registration: aiindex")
        else:
            run([which("claude") or "claude", "mcp", "remove", "aiindex", "--scope", "user"], check=False, capture=True)


def platform_rid() -> tuple[str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "arm64" if machine in {"arm64", "aarch64"} else "x64" if machine in {"x86_64", "amd64"} else machine
    if system == "windows":
        if arch == "arm64":
            raise RuntimeError("AiIndex Windows ARM64 is not currently supported by the bundled sqlite-vec runtime.")
        return "win-x64", "zip"
    if system == "linux":
        return f"linux-{arch}", "tar.gz"
    if system == "darwin":
        return f"osx-{arch}", "tar.gz"
    raise RuntimeError(f"Unsupported platform: {system}/{machine}")


def urlopen_json(url: str) -> Any:
    headers = {"User-Agent": "company-ai-framework-installer"}
    token = os.environ.get("AIINDEX_GITEA_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def download(url: str, dest: Path) -> None:
    headers = {"User-Agent": "company-ai-framework-installer"}
    token = os.environ.get("AIINDEX_GITEA_TOKEN")
    if token and "gt.qbic.ro" in url:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response, dest.open("wb") as out:
        shutil.copyfileobj(response, out)


def install_aiindex(config: dict[str, Any], dry_run: bool, skip: bool) -> tuple[Path | None, dict[str, Any]]:
    bin_dir = FRAMEWORK_ROOT / "bin"
    exe = "aiindex-mcp.exe" if os.name == "nt" else "aiindex-mcp"
    cli = "aiindex.exe" if os.name == "nt" else "aiindex"
    existing_mcp = bin_dir / exe
    existing_cli = bin_dir / cli
    if skip:
        return (existing_mcp if existing_mcp.exists() else None), {"skipped": True}
    api = os.environ.get("AIINDEX_RELEASE_API_URL") or config.get("aiIndexReleaseApiUrl")
    if not api:
        print("  AiIndex release API not configured; preserving any existing runtime")
        return (existing_mcp if existing_mcp.exists() else None), {"warning": "release API not configured"}
    if dry_run:
        print(f"  would resolve/install latest AiIndex from {api}")
        return (existing_mcp if existing_mcp.exists() else bin_dir / exe), {"planned": True}
    try:
        release = urlopen_json(api)
        rid, ext = platform_rid()
        asset_name = f"aiindex-{rid}.{'zip' if ext == 'zip' else 'tar.gz'}"
        checksum_name = config.get("aiIndexChecksumAsset", "SHA256SUMS")
        assets = {a.get("name"): a for a in release.get("assets", [])}
        if asset_name not in assets or checksum_name not in assets:
            raise RuntimeError(f"Latest AiIndex release is missing {asset_name} or {checksum_name}")
        with tempfile.TemporaryDirectory(prefix="aiindex-install-") as tmp_s:
            tmp = Path(tmp_s)
            archive = tmp / asset_name
            checksums = tmp / checksum_name
            download(assets[asset_name]["browser_download_url"], archive)
            download(assets[checksum_name]["browser_download_url"], checksums)
            expected = None
            for line in checksums.read_text(encoding="utf-8").splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[-1].lstrip("*") == asset_name:
                    expected = parts[0].lower()
                    break
            if not expected:
                raise RuntimeError(f"Checksum for {asset_name} not found")
            actual = hashlib.sha256(archive.read_bytes()).hexdigest().lower()
            if actual != expected:
                raise RuntimeError(f"AiIndex SHA-256 mismatch for {asset_name}")
            extract = tmp / "extract"
            extract.mkdir()
            if ext == "zip":
                with zipfile.ZipFile(archive) as zf:
                    zf.extractall(extract)
            else:
                with tarfile.open(archive, "r:gz") as tf:
                    tf.extractall(extract)
            found_cli = next((p for p in extract.rglob(cli) if p.is_file()), None)
            found_mcp = next((p for p in extract.rglob(exe) if p.is_file()), None)
            if not found_cli or not found_mcp:
                raise RuntimeError("AiIndex archive did not contain expected CLI + MCP executables")
            bin_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(found_cli, existing_cli)
            shutil.copy2(found_mcp, existing_mcp)
            if os.name != "nt":
                existing_cli.chmod(existing_cli.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                existing_mcp.chmod(existing_mcp.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            print(f"  installed AiIndex {release.get('tag_name') or release.get('name') or 'latest'} -> {bin_dir}")
            return existing_mcp, {"version": release.get("tag_name") or release.get("name"), "runtimePath": str(bin_dir), "asset": asset_name}
    except (urllib.error.URLError, RuntimeError, KeyError, ValueError) as exc:
        if existing_mcp.exists() and existing_cli.exists():
            print(f"  WARNING: AiIndex update unavailable ({exc}); preserving existing runtime")
            return existing_mcp, {"warning": str(exc), "runtimePath": str(bin_dir)}
        raise RuntimeError(f"AiIndex installation failed: {exc}") from exc



def ensure_aiindex_cli_path(state: dict[str, Any], dry_run: bool) -> None:
    bin_dir = FRAMEWORK_ROOT / "bin"
    cli_name = "aiindex.exe" if os.name == "nt" else "aiindex"
    cli = bin_dir / cli_name
    if not cli.exists() and not dry_run:
        return
    if os.name == "nt":
        try:
            import winreg  # type: ignore
            key_path = r"Environment"
            if dry_run:
                print(f"  would ensure user PATH contains {bin_dir}")
                return
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                try:
                    current, _ = winreg.QueryValueEx(key, "Path")
                except FileNotFoundError:
                    current = ""
                parts = [p for p in current.split(";") if p]
                norm = {os.path.normcase(os.path.normpath(p)) for p in parts}
                if os.path.normcase(os.path.normpath(str(bin_dir))) not in norm:
                    updated = ";".join(parts + [str(bin_dir)])
                    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, updated)
                    state.setdefault("pathChanges", []).append(str(bin_dir))
                    print(f"  added {bin_dir} to user PATH")
            if str(bin_dir) not in os.environ.get("PATH", "").split(os.pathsep):
                os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
        except Exception as exc:
            print(f"  WARNING: could not update Windows user PATH: {exc}")
    else:
        shim_dir = Path.home() / ".local" / "bin"
        shim = shim_dir / "aiindex"
        if dry_run:
            print(f"  would link {shim} -> {cli}")
            return
        shim_dir.mkdir(parents=True, exist_ok=True)
        if shim.exists() or shim.is_symlink():
            try:
                if shim.resolve() != cli.resolve():
                    print(f"  WARNING: preserving unrelated existing shim: {shim}")
                    return
            except OSError:
                return
        else:
            shim.symlink_to(cli)
            state.setdefault("links", []).append(str(shim))
            print(f"  linked {shim} -> {cli}")


def graphify_executable() -> str | None:
    return which("graphify")


def install_graphify(clients: list[str], state: dict[str, Any], dry_run: bool, skip: bool) -> None:
    if skip:
        return
    uv = which("uv")
    if not uv:
        raise RuntimeError("uv is required for Graphify but was not found. Bootstrap should install uv first.")
    package = load_json(CONFIG_PATH, {}).get("graphifyPackage", "graphifyy")
    preexisting = graphify_executable() is not None
    if dry_run:
        print(f"  would run: uv tool install --upgrade {package}")
        for client in clients:
            print(f"  would run Graphify integration install for {client}")
        return
    proc = run([uv, "tool", "install", "--upgrade", package], check=False, capture=True)
    if proc.returncode != 0 and "already installed" not in (proc.stderr or "").lower():
        # uv sometimes prefers `uv tool upgrade` for an existing tool.
        run([uv, "tool", "upgrade", package], check=True)
    graphify = graphify_executable()
    if not graphify:
        # uv tool dir --bin is authoritative when current shell PATH has not refreshed.
        p = run([uv, "tool", "dir", "--bin"], capture=True, check=False)
        if p.returncode == 0:
            candidate = Path(p.stdout.strip()) / ("graphify.exe" if os.name == "nt" else "graphify")
            if candidate.exists():
                graphify = str(candidate)
    if not graphify:
        raise RuntimeError("Graphify was installed with uv but its executable could not be located")
    managed = state["graphify"].setdefault("managedClients", [])
    state["graphify"].setdefault("preexisting", preexisting)
    for client in clients:
        run([graphify, client, "install"], check=False)
        if client not in managed:
            managed.append(client)
    state["graphify"]["executable"] = graphify


def uninstall_graphify_client(client: str, state: dict[str, Any], dry_run: bool) -> None:
    managed = state.get("graphify", {}).get("managedClients", [])
    if client not in managed:
        return
    graphify = state.get("graphify", {}).get("executable") or graphify_executable()
    if graphify:
        if dry_run:
            print(f"  would run: {graphify} {client} uninstall")
        else:
            run([graphify, client, "uninstall"], check=False, capture=True)
    if not dry_run:
        managed.remove(client)


def client_detected(client: str) -> tuple[bool, str]:
    exe = which(client)
    home = Path.home() / (".codex" if client == "codex" else ".claude")
    if exe:
        return True, command_version(client) or "installed"
    if home.exists():
        return True, "home/config present; CLI not on PATH"
    return False, "not detected"


def validate_provider(client: str, profile: str) -> tuple[bool, str]:
    proc = run([sys.executable, str(FRAMEWORK_ROOT / "scripts" / "ai.py"), "provider", "--provider", client, "--profile", profile, "--validate"], check=False, capture=True)
    return proc.returncode == 0, (proc.stdout or proc.stderr).strip()


def doctor(state: dict[str, Any]) -> int:
    print("AI Framework Doctor")
    print()
    rows: list[tuple[str, str]] = []
    rows.append(("Git", command_version("git") or "MISSING"))
    rows.append(("Python", f"{platform.python_version()} ({sys.executable})"))
    rows.append(("uv", command_version("uv") or "MISSING"))
    rows.append(("Framework", str(FRAMEWORK_ROOT)))
    rows.append(("Framework git", git_commit(FRAMEWORK_ROOT) or "not a git checkout"))
    for client in ("codex", "claude"):
        detected, detail = client_detected(client)
        rows.append((client.capitalize(), detail))
        active_profiles = load_active_profiles()
        profile = active_profiles.get(client) or state.get("profiles", {}).get(client) or "medium"
        ok, msg = validate_provider(client, profile)
        source = "saved profile" if client in active_profiles else ("installer state" if state.get("profiles", {}).get(client) else "default")
        rows.append((f"{client} profile", f"{profile} ({'OK' if ok else 'INVALID'}; {source})"))
        generated = FRAMEWORK_ROOT / "generated" / client
        rows.append((f"{client} wiring", "OK" if generated.exists() else "missing/generated not rendered"))
    ai_bin = FRAMEWORK_ROOT / "bin" / ("aiindex.exe" if os.name == "nt" else "aiindex")
    ai_mcp = FRAMEWORK_ROOT / "bin" / ("aiindex-mcp.exe" if os.name == "nt" else "aiindex-mcp")
    rows.append(("AiIndex CLI", "OK" if ai_bin.exists() else "missing"))
    rows.append(("AiIndex MCP", "OK" if ai_mcp.exists() else "missing"))
    graphify = graphify_executable()
    rows.append(("Graphify", graphify or "missing"))
    width = max(len(k) for k, _ in rows)
    for key, value in rows:
        print(f"{key:<{width}}  {value}")
    issues = sum(1 for _, value in rows if value == "MISSING" or value.startswith("missing") or "INVALID" in value)
    return 1 if issues else 0


def update_framework_from_git(dry_run: bool) -> None:
    if not (FRAMEWORK_ROOT / ".git").exists() or not which("git"):
        return
    status = run([which("git") or "git", "status", "--porcelain"], capture=True, check=False, cwd=FRAMEWORK_ROOT)
    if status.stdout.strip():
        print("  framework checkout has local changes; skipping automatic git pull")
        return
    if dry_run:
        print("  would run git pull --ff-only")
        return
    run([which("git") or "git", "pull", "--ff-only"], check=False, cwd=FRAMEWORK_ROOT)


def install_or_repair(args: argparse.Namespace, state: dict[str, Any]) -> int:
    args.target = choose_target(args.target, args.yes)
    clients = target_clients(args.target)
    if args.action == "update-repair":
        update_framework_from_git(args.dry_run)
    for client in clients:
        detected, detail = client_detected(client)
        if not detected:
            message = f"{client.capitalize()} was not detected ({detail})."
            if args.yes:
                raise RuntimeError(message)
            if not ask(message + " Continue wiring anyway?", default=False):
                raise RuntimeError("Cancelled")
    profiles: dict[str, str] = {}
    for client in clients:
        explicit = args.codex_profile if client == "codex" else args.claude_profile
        profiles[client] = choose_profile(client, explicit or args.profile, state, args.yes)
        if profiles[client] not in {"low", "medium", "high"}:
            raise RuntimeError(f"Invalid profile for {client}: {profiles[client]}")
        set_profile(client, profiles[client], args.dry_run)
        if not args.dry_run:
            state["profiles"][client] = profiles[client]
    config = load_json(CONFIG_PATH, {})
    ai_mcp, ai_state = install_aiindex(config, args.dry_run, args.skip_aiindex)
    if ai_mcp is not None or args.dry_run:
        ensure_aiindex_cli_path(state, args.dry_run)
    if not args.dry_run:
        state["aiIndex"] = ai_state
    install_graphify(clients, state, args.dry_run, args.skip_graphify)
    for client in clients:
        if client == "codex":
            wire_codex(profiles[client], state, args.dry_run, ai_mcp)
        else:
            wire_claude(profiles[client], state, args.dry_run, ai_mcp)
        if client not in state["installedClients"] and not args.dry_run:
            state["installedClients"].append(client)
    if not args.dry_run:
        record_bootstrap_prerequisites(state)
        state["frameworkCommit"] = git_commit(FRAMEWORK_ROOT)
        save_json(STATE_PATH, state)
    print()
    print(f"{args.action.replace('-', ' ').title()} complete for: {', '.join(clients)}")
    for client in clients:
        print(f"  {client}: profile={profiles[client]}")
    return 0


def uninstall(args: argparse.Namespace, state: dict[str, Any]) -> int:
    args.target = choose_target(args.target, args.yes)
    clients = target_clients(args.target)
    for client in clients:
        uninstall_graphify_client(client, state, args.dry_run)
        if client == "codex":
            restore_codex(state, args.dry_run)
        else:
            restore_claude(state, args.dry_run)
        generated = FRAMEWORK_ROOT / "generated" / client
        if generated.exists():
            remove_owned_path(generated, args.dry_run)
        if not args.dry_run and client in state["installedClients"]:
            state["installedClients"].remove(client)
            state["profiles"].pop(client, None)
    # Remove recorded links that belong to removed clients and still resolve into this framework.
    for raw in list(state.get("links", [])):
        path = Path(raw)
        parent_name = path.parent.parent.name.lower() if len(path.parents) > 1 else ""
        belongs = any((client == "codex" and ".codex" in str(path)) or (client == "claude" and ".claude" in str(path)) for client in clients)
        if belongs:
            remove_owned_path(path, args.dry_run)
            if not args.dry_run:
                state["links"].remove(raw)
    if not args.dry_run:
        save_json(STATE_PATH, state)
    print(f"Uninstall complete for: {', '.join(clients)}")
    if not state.get("installedClients"):
        print("No installer-managed clients remain. Shared ~/.ai, AiIndex runtime, and Graphify tool were preserved.")
        print("Python, Git, and uv are shared prerequisites and are never uninstalled automatically.")
        print("Remove shared components only after confirming no other workflows depend on them.")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Company AI Framework installer lifecycle")
    p.add_argument("action", choices=["install", "update-repair", "uninstall", "doctor"])
    p.add_argument("--target", choices=["codex", "claude", "both"])
    p.add_argument("--profile", choices=["low", "medium", "high"])
    p.add_argument("--codex-profile", choices=["low", "medium", "high"])
    p.add_argument("--claude-profile", choices=["low", "medium", "high"])
    p.add_argument("--yes", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--skip-aiindex", action="store_true")
    p.add_argument("--skip-graphify", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    if args.verbose:
        print(f"Framework root: {FRAMEWORK_ROOT}")
        print(f"State path: {STATE_PATH}")
    state = load_state()
    try:
        if args.action == "doctor":
            return doctor(state)
        if args.action in {"install", "update-repair"}:
            return install_or_repair(args, state)
        return uninstall(args, state)
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
