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
VERSION_PATH = FRAMEWORK_ROOT / "version.json"
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




def local_versions() -> dict[str, str | None]:
    data = load_json(VERSION_PATH, {})
    return {
        "framework": data.get("framework"),
        "aiIndex": data.get("aiIndex"),
    }


def framework_version_url(config: dict[str, Any]) -> str | None:
    explicit = config.get("frameworkVersionUrl")
    if explicit:
        return str(explicit)
    repo = str(config.get("frameworkRepositoryUrl") or "")
    branch = str(config.get("frameworkBranch") or "main")
    match = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", repo)
    if not match:
        return None
    owner, name = match.groups()
    return f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/version.json"


def normalize_version_tuple(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    m = re.fullmatch(r"v?(\d+(?:\.\d+)*)", value.strip())
    if not m:
        return None
    return tuple(int(part) for part in m.group(1).split("."))


def newer_framework_version(current: str | None, latest: str | None) -> bool:
    cur = normalize_version_tuple(current)
    new = normalize_version_tuple(latest)
    if cur is not None and new is not None:
        width = max(len(cur), len(new))
        return cur + (0,) * (width - len(cur)) < new + (0,) * (width - len(new))
    return bool(latest and current != latest)


def default_state() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "frameworkRoot": str(FRAMEWORK_ROOT),
        "frameworkCommit": git_commit(FRAMEWORK_ROOT),
        "frameworkVersion": load_json(VERSION_PATH, {}).get("framework"),
        "installedClients": [],
        "profiles": {},
        "managedSkills": {"codex": [], "claude": []},
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
    managed = state.setdefault("managedSkills", {})
    managed.setdefault("codex", [])
    managed.setdefault("claude", [])
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


def is_directory_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if callable(is_junction):
        try:
            return bool(is_junction())
        except OSError:
            return False
    return False


def _skill_tree_files(root: Path) -> dict[str, bytes]:
    """Return meaningful skill files for safe legacy-copy comparison.

    Python caches are ignored because old manually copied skills commonly contain
    them and they are generated artifacts rather than skill source.
    """
    files: dict[str, bytes] = {}
    if not root.is_dir():
        return files
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if "__pycache__" in rel.parts or path.suffix == ".pyc":
            continue
        files[rel.as_posix()] = path.read_bytes()
    return files


def _skill_frontmatter_name(skill_md: Path) -> str | None:
    if not skill_md.is_file():
        return None
    try:
        text = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = re.search(r"(?m)^name:\s*[\"']?([^\"'\n]+)[\"']?\s*$", text)
    return match.group(1).strip() if match else None


def create_dir_link(link: Path, target: Path, dry_run: bool) -> str:
    """Create/adopt/repair a client skill directory link.

    Correct existing links are adopted and wrong-target links are repaired. An
    exact legacy *copied* framework skill may be migrated to a managed link. A
    modified or unrelated real directory is never overwritten automatically.
    """
    if link.exists() or link.is_symlink():
        try:
            if link.resolve() == target.resolve():
                print(f"  {'would adopt' if dry_run else 'adopted'} existing skill link {link}")
                return "adopted"
        except OSError:
            pass
        if is_directory_link(link):
            print(f"  {'would repair' if dry_run else 'repairing'} wrong-target skill link {link} -> {target}")
            if not dry_run:
                if link.is_symlink():
                    link.unlink()
                else:
                    os.rmdir(link)
        elif link.is_dir():
            # Older framework installs copied skills into the client directory
            # instead of linking them. Migrate only when the meaningful file tree
            # exactly matches the current canonical skill, so user edits are never
            # discarded.
            if _skill_tree_files(link) == _skill_tree_files(target):
                print(f"  {'would migrate' if dry_run else 'migrating'} legacy copied framework skill {link} -> managed link")
                if not dry_run:
                    shutil.rmtree(link)
            else:
                source_name = _skill_frontmatter_name(link / "SKILL.md")
                target_name = _skill_frontmatter_name(target / "SKILL.md")
                if source_name and target_name and source_name == target_name == target.name:
                    raise RuntimeError(
                        f"Legacy framework skill copy detected at {link}, but its contents differ from the current canonical skill. "
                        "The installer will not overwrite possible local edits. Move/rename or remove that directory, then rerun Update / Repair."
                    )
                raise RuntimeError(
                    f"Refusing to replace unrelated existing skill directory: {link}. "
                    "Move/rename it and rerun Update / Repair."
                )
        else:
            raise RuntimeError(
                f"Refusing to replace unrelated existing skill path: {link}. "
                "Move/rename it and rerun Update / Repair."
            )
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
    elif os.name == "nt" and hasattr(path, "is_junction") and path.is_junction():
        # Windows directory junctions must be removed as links only; recursively
        # deleting them could delete the junction target instead.
        os.rmdir(path)
    else:
        # Normal directories (including generated native wiring) own their
        # contents and should be removed recursively.
        shutil.rmtree(path)


def client_root(client: str) -> Path:
    if client == "codex":
        return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    if client == "claude":
        return Path(os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")))
    raise RuntimeError(f"Unsupported client: {client}")


def list_skills() -> list[Path]:
    result: list[Path] = []
    for child in sorted((FRAMEWORK_ROOT / "skills").iterdir()):
        if child.is_dir() and (child / "SKILL.md").exists():
            result.append(child)
    return result


def wire_skills(client: str, state: dict[str, Any], dry_run: bool) -> None:
    skill_root = client_root(client) / "skills"
    managed = state.setdefault("managedSkills", {}).setdefault(client, [])
    for skill in list_skills():
        link = skill_root / skill.name
        outcome = create_dir_link(link, skill, dry_run)
        if dry_run:
            continue
        if skill.name not in managed:
            managed.append(skill.name)
        if str(link) not in state.setdefault("links", []):
            state["links"].append(str(link))


def skill_health(client: str, state: dict[str, Any]) -> tuple[int, int, list[str]]:
    skill_root = client_root(client) / "skills"
    expected = list_skills()
    issues: list[str] = []
    healthy = 0
    for skill in expected:
        link = skill_root / skill.name
        if not (link.exists() or link.is_symlink()):
            issues.append(f"{skill.name}: missing")
            continue
        try:
            if link.resolve() == skill.resolve():
                healthy += 1
            else:
                issues.append(f"{skill.name}: wrong target")
        except OSError:
            issues.append(f"{skill.name}: broken")
    return healthy, len(expected), issues


def remove_managed_skills(client: str, state: dict[str, Any], dry_run: bool) -> None:
    root = client_root(client) / "skills"
    # Include canonical framework skills as well as recorded managed skills.
    # This safely cleans legacy/adoptable links created before installer ownership
    # tracking was complete, but only when the link resolves exactly to the
    # matching framework skill directory.
    recorded = set(state.get("managedSkills", {}).get(client, []))
    canonical = {skill.name for skill in list_skills()}
    names = sorted(recorded | canonical)
    for name in names:
        path = root / name
        target = FRAMEWORK_ROOT / "skills" / name
        if not (path.exists() or path.is_symlink()):
            continue
        try:
            points_to_framework = path.resolve() == target.resolve()
        except OSError:
            points_to_framework = is_directory_link(path)
        if not points_to_framework:
            print(f"  WARNING: preserving managed skill path with unexpected target: {path}")
            continue
        remove_owned_path(path, dry_run)
        if not dry_run:
            raw = str(path)
            if raw in state.get("links", []):
                state["links"].remove(raw)
    if not dry_run:
        state.setdefault("managedSkills", {})[client] = []


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


def wire_codex(profile: str, state: dict[str, Any], dry_run: bool, aiindex_mcp: Path | None, *, wire_shared: bool = True) -> None:
    generated = render_native("codex", profile, dry_run)
    config = client_root("codex") / "config.toml"
    instructions = config.parent / "AGENTS.md"
    if wire_shared:
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
    config = client_root("codex") / "config.toml"
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


def claude_aiindex_mcp_is_current(aiindex_mcp: Path) -> bool:
    """Return True when Claude already has the expected user-scoped AiIndex MCP entry.

    Claude stores user MCP registrations in ~/.claude.json.  Treat extra fields such
    as an empty env object as compatible; only the transport, command and arguments
    determine whether the framework needs to repair the registration.
    """
    config = load_json(Path.home() / ".claude.json", {})
    entry = config.get("mcpServers", {}).get("aiindex")
    if not isinstance(entry, dict):
        return False

    command = entry.get("command")
    args = entry.get("args", [])
    return (
        entry.get("type", "stdio") == "stdio"
        and isinstance(command, str)
        and os.path.normcase(os.path.normpath(command))
        == os.path.normcase(os.path.normpath(str(aiindex_mcp)))
        and (args is None or args == [])
    )


def wire_claude(profile: str, state: dict[str, Any], dry_run: bool, aiindex_mcp: Path | None, *, wire_shared: bool = True) -> None:
    generated = render_native("claude", profile, dry_run)
    root = client_root("claude")
    settings = root / "settings.json"
    instructions = root / "CLAUDE.md"
    if wire_shared:
        managed_markdown(instructions, f"@{(FRAMEWORK_ROOT / 'CLAUDE.md').as_posix()}", dry_run)
        wire_skills("claude", state, dry_run)
    if dry_run:
        print(f"  would merge Claude settings into {settings}")
        if aiindex_mcp and which("claude"):
            if claude_aiindex_mcp_is_current(aiindex_mcp):
                print(f"  would preserve existing Claude AiIndex MCP registration -> {aiindex_mcp}")
            else:
                print(f"  would register Claude AiIndex MCP -> {aiindex_mcp}")
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
        if claude_aiindex_mcp_is_current(aiindex_mcp):
            print(f"  preserving existing Claude AiIndex MCP registration -> {aiindex_mcp}")
        else:
            # Repair only our named registration, then add the expected user-scoped entry.
            run([which("claude") or "claude", "mcp", "remove", "aiindex", "--scope", "user"], check=False, capture=True)
            run([which("claude") or "claude", "mcp", "add", "--scope", "user", "aiindex", "--", str(aiindex_mcp)], check=False)


def restore_claude(state: dict[str, Any], dry_run: bool) -> None:
    root = client_root("claude")
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
            raise RuntimeError("AiIndex Windows ARM64 is not available as a native release asset. Use the Linux ARM64 build manually through WSL, or run the installer on a supported native platform.")
        return "win-x64", "zip"
    if system == "linux":
        return f"linux-{arch}", "tar.gz"
    if system == "darwin":
        return f"osx-{arch}", "tar.gz"
    raise RuntimeError(f"Unsupported platform: {system}/{machine}")


def _github_headers() -> dict[str, str]:
    # The framework and AiIndex release assets are public on GitHub. A token is
    # optional and only used to raise API rate limits in automated environments.
    headers = {
        "User-Agent": "company-ai-framework-installer",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def urlopen_json(url: str) -> Any:
    req = urllib.request.Request(url, headers=_github_headers())
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def download(url: str, dest: Path) -> None:
    headers = {"User-Agent": "company-ai-framework-installer"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response, dest.open("wb") as out:
        shutil.copyfileobj(response, out)


def latest_aiindex_release(config: dict[str, Any]) -> dict[str, Any]:
    api = os.environ.get("AIINDEX_RELEASE_API_URL") or config.get("aiIndexReleaseApiUrl")
    if not api:
        raise RuntimeError("AiIndex release API not configured")
    release = urlopen_json(str(api))
    tag = release.get("tag_name") or release.get("name")
    if not tag:
        raise RuntimeError("Latest AiIndex release did not include a tag/name")
    return release


def installed_aiindex_version(state: dict[str, Any], cli: Path, mcp: Path) -> str | None:
    if not (cli.exists() and mcp.exists()):
        return None
    recorded = state.get("aiIndex", {}).get("version")
    if recorded:
        return str(recorded)
    # A manually populated framework checkout may already contain the binaries.
    # In that case version.json describes the bundled/expected runtime version.
    return local_versions().get("aiIndex")


def install_aiindex(config: dict[str, Any], state: dict[str, Any], dry_run: bool, skip: bool, *, force: bool = False, allow_update: bool = True) -> tuple[Path | None, dict[str, Any]]:
    bin_dir = FRAMEWORK_ROOT / "bin"
    exe = "aiindex-mcp.exe" if os.name == "nt" else "aiindex-mcp"
    cli_name = "aiindex.exe" if os.name == "nt" else "aiindex"
    existing_mcp = bin_dir / exe
    existing_cli = bin_dir / cli_name
    if skip:
        return (existing_mcp if existing_mcp.exists() else None), {"skipped": True}
    api = os.environ.get("AIINDEX_RELEASE_API_URL") or config.get("aiIndexReleaseApiUrl")
    if not api:
        print("  AiIndex release API not configured; preserving any existing runtime")
        return (existing_mcp if existing_mcp.exists() else None), {"warning": "release API not configured"}

    current = installed_aiindex_version(state, existing_cli, existing_mcp)
    healthy = existing_cli.exists() and existing_mcp.exists()
    try:
        release = latest_aiindex_release(config)
        latest = str(release.get("tag_name") or release.get("name"))
        rid, ext = platform_rid()
        asset_name = f"aiindex-{rid}.{'zip' if ext == 'zip' else 'tar.gz'}"
        checksum_name = config.get("aiIndexChecksumAsset", "SHA256SUMS")
        assets = {a.get("name"): a for a in release.get("assets", [])}
        if asset_name not in assets or checksum_name not in assets:
            raise RuntimeError(f"Latest AiIndex release is missing {asset_name} or {checksum_name}")

        if healthy and current == latest and not force:
            print(f"  AiIndex {latest} already current")
            return existing_mcp, {
                "version": latest,
                "runtimePath": str(bin_dir),
                "asset": asset_name,
                "status": "current",
            }

        if healthy and current != latest and not force and not allow_update:
            print(f"  AiIndex update available: {current or 'unknown'} -> {latest}; preserving current version")
            return existing_mcp, {
                "version": current,
                "runtimePath": str(bin_dir),
                "asset": state.get("aiIndex", {}).get("asset"),
                "status": "update-available",
                "latest": latest,
            }

        if dry_run:
            if not healthy:
                reason = "missing CLI/MCP binaries"
                print(f"  would repair AiIndex {latest} ({reason})")
            elif force:
                print(f"  would reinstall AiIndex {latest}")
            else:
                print(f"  would update AiIndex {current or 'unknown'} -> {latest}")
            return (existing_mcp if existing_mcp.exists() else bin_dir / exe), {
                "version": latest,
                "runtimePath": str(bin_dir),
                "asset": asset_name,
                "planned": True,
            }

        action = "repairing" if not healthy else ("reinstalling" if force else "updating")
        if not healthy:
            print(f"  {action} AiIndex -> {latest}")
        elif current and current != latest:
            print(f"  {action} AiIndex {current} -> {latest}")
        else:
            print(f"  {action} AiIndex {latest}")

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
            found_cli = next((p for p in extract.rglob(cli_name) if p.is_file()), None)
            found_mcp = next((p for p in extract.rglob(exe) if p.is_file()), None)
            if not found_cli or not found_mcp:
                raise RuntimeError("AiIndex archive did not contain expected CLI + MCP executables")
            bin_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(found_cli, existing_cli)
            shutil.copy2(found_mcp, existing_mcp)
            if os.name != "nt":
                existing_cli.chmod(existing_cli.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                existing_mcp.chmod(existing_mcp.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            print(f"  installed AiIndex {latest} -> {bin_dir}")
            return existing_mcp, {
                "version": latest,
                "runtimePath": str(bin_dir),
                "asset": asset_name,
                "status": "installed",
            }
    except (urllib.error.URLError, RuntimeError, KeyError, ValueError) as exc:
        if healthy:
            print(f"  WARNING: AiIndex update unavailable ({exc}); preserving existing runtime")
            return existing_mcp, {
                "version": current,
                "warning": str(exc),
                "runtimePath": str(bin_dir),
            }
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
        if shim.exists() or shim.is_symlink():
            try:
                if shim.resolve() == cli.resolve():
                    print(f"  {'would preserve' if dry_run else 'preserving'} existing AiIndex link {shim} -> {cli}")
                    return
                print(f"  WARNING: preserving unrelated existing shim: {shim}")
                return
            except OSError:
                print(f"  WARNING: preserving unreadable existing shim: {shim}")
                return
        if dry_run:
            print(f"  would link {shim} -> {cli}")
            return
        shim_dir.mkdir(parents=True, exist_ok=True)
        shim.symlink_to(cli)
        state.setdefault("links", []).append(str(shim))
        print(f"  linked {shim} -> {cli}")


def graphify_executable() -> str | None:
    return which("graphify")


def graphify_integration_status(client: str) -> tuple[bool, str]:
    """Detect whether Graphify's assistant skill is already installed.

    The base Graphify install registers a skill under the assistant's skills
    directory. Optional always-on instructions/hooks are separate Graphify
    features and are deliberately not required for installer health.
    """
    home = Path.home()
    if client == "codex":
        skill = home / ".codex" / "skills" / "graphify" / "SKILL.md"
    elif client == "claude":
        skill = home / ".claude" / "skills" / "graphify" / "SKILL.md"
    else:
        return False, f"unsupported client: {client}"

    if skill.exists() and skill.is_file():
        return True, f"skill detected at {skill}"
    return False, f"missing skill at {skill}"


def _graphify_install_commands(graphify: str, client: str) -> list[list[str]]:
    """Return preferred/fallback commands for registering the Graphify skill."""
    if client == "codex":
        return [[graphify, "install", "--platform", "codex"]]
    if client == "claude":
        commands = [[graphify, "install", "--platform", "claude"]]
        # Some Graphify releases expose Claude-on-Windows as the legacy
        # platform name `windows`; keep it only as a compatibility fallback.
        if os.name == "nt":
            commands.append([graphify, "install", "--platform", "windows"])
        return commands
    raise RuntimeError(f"Unsupported Graphify client: {client}")


def install_graphify(clients: list[str], state: dict[str, Any], dry_run: bool, skip: bool) -> None:
    if skip:
        return
    uv = which("uv")
    if not uv:
        raise RuntimeError("uv is required for Graphify but was not found. Bootstrap should install uv first.")
    package = load_json(CONFIG_PATH, {}).get("graphifyPackage", "graphifyy")
    existing_graphify = graphify_executable()
    preexisting = existing_graphify is not None
    integration_status = {client: graphify_integration_status(client) for client in clients}
    if dry_run:
        if preexisting:
            print(f"  would preserve existing Graphify tool: {existing_graphify}")
        else:
            print(f"  would run: uv tool install {package}")
        for client in clients:
            healthy, detail = integration_status[client]
            if healthy:
                print(f"  would preserve existing Graphify skill for {client} ({detail})")
            else:
                cmd = _graphify_install_commands("graphify", client)[0]
                print(f"  would run: {' '.join(cmd)} ({detail})")
        return
    if not existing_graphify:
        proc = run([uv, "tool", "install", package], check=False, capture=True)
        if proc.returncode != 0 and "already installed" not in ((proc.stderr or "") + (proc.stdout or "")).lower():
            raise RuntimeError(f"Graphify install failed: {(proc.stderr or proc.stdout or '').strip()}")
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
    detected = state["graphify"].setdefault("detectedClients", [])
    for client in clients:
        healthy, detail = graphify_integration_status(client)
        if healthy:
            print(f"  preserving existing Graphify skill for {client} ({detail})")
            if client not in detected:
                detected.append(client)
            continue

        last_proc = None
        for command in _graphify_install_commands(graphify, client):
            last_proc = run(command, check=False)
            if last_proc.returncode == 0:
                break
        if not last_proc or last_proc.returncode != 0:
            code = last_proc.returncode if last_proc else "unknown"
            raise RuntimeError(f"Graphify skill install failed for {client} (exit {code})")
        if client not in managed:
            managed.append(client)
    state["graphify"]["executable"] = graphify


def uninstall_graphify_client(client: str, state: dict[str, Any], dry_run: bool) -> None:
    managed = state.get("graphify", {}).get("managedClients", [])
    if client not in managed:
        return
    graphify = state.get("graphify", {}).get("executable") or graphify_executable()
    if graphify:
        command = [graphify, "uninstall", "--platform", client]
        if dry_run:
            print(f"  would run: {' '.join(command)}")
        else:
            proc = run(command, check=False, capture=True)
            if proc.returncode != 0:
                # Compatibility with older Graphify CLI layouts.
                run([graphify, client, "uninstall"], check=False, capture=True)
    if not dry_run:
        managed.remove(client)


def client_detected(client: str) -> tuple[bool, str]:
    commands = [client]
    # The Linux ChatGPT/Codex desktop package currently exposes `chatgpt` rather
    # than `codex`. Accept either command while keeping `codex` preferred when
    # both are available.
    if client == "codex":
        commands.append("chatgpt")
    for command in commands:
        exe = which(command)
        if exe:
            version = command_version(command) or "installed"
            if command != client:
                return True, f"{version} ({command})"
            return True, version
    home = client_root(client)
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
    versions = local_versions()
    rows.append(("Git", command_version("git") or "MISSING"))
    rows.append(("Python", f"{platform.python_version()} ({sys.executable})"))
    rows.append(("uv", command_version("uv") or "MISSING"))
    rows.append(("Framework", str(FRAMEWORK_ROOT)))
    rows.append(("Framework version", versions.get("framework") or "unknown"))
    rows.append(("Framework git", git_commit(FRAMEWORK_ROOT) or "not a git checkout"))
    active_profiles = load_active_profiles()
    for client in ("codex", "claude"):
        detected, detail = client_detected(client)
        rows.append((client.capitalize(), detail))
        profile = active_profiles.get(client) or state.get("profiles", {}).get(client) or "medium"
        ok, _ = validate_provider(client, profile)
        source = "saved profile" if client in active_profiles else ("installer state" if state.get("profiles", {}).get(client) else "default")
        rows.append((f"{client} profile", f"{profile} ({'OK' if ok else 'INVALID'}; {source})"))
        generated = FRAMEWORK_ROOT / "generated" / client
        if not detected:
            rows.append((f"{client} wiring", "not applicable (client not detected)"))
            rows.append((f"{client} skills", "not applicable (client not detected)"))
        else:
            rows.append((f"{client} wiring", "OK" if generated.exists() else "missing/generated not rendered"))
            healthy, total, skill_issues = skill_health(client, state)
            if total:
                if healthy == total and not skill_issues:
                    detail_skills = f"{healthy}/{total} OK"
                else:
                    detail_skills = f"{healthy}/{total} healthy"
                    if skill_issues:
                        detail_skills += f" ({len(skill_issues)} issue{'s' if len(skill_issues) != 1 else ''})"
                rows.append((f"{client} skills", detail_skills))
    ai_bin = FRAMEWORK_ROOT / "bin" / ("aiindex.exe" if os.name == "nt" else "aiindex")
    ai_mcp = FRAMEWORK_ROOT / "bin" / ("aiindex-mcp.exe" if os.name == "nt" else "aiindex-mcp")
    installed_ai = installed_aiindex_version(state, ai_bin, ai_mcp)
    rows.append(("AiIndex version", installed_ai or "unknown"))
    rows.append(("AiIndex CLI", "OK" if ai_bin.exists() else "missing"))
    rows.append(("AiIndex MCP", "OK" if ai_mcp.exists() else "missing"))
    graphify = graphify_executable()
    rows.append(("Graphify", graphify or "missing"))
    width = max(len(k) for k, _ in rows)
    for key, value in rows:
        print(f"{key:<{width}}  {value}")
    issues = 0
    for key, value in rows:
        lower = value.lower()
        if value == "MISSING" or lower.startswith("missing") or "INVALID" in value:
            issues += 1
        if key.endswith(" skills") and "issue" in lower:
            issues += 1
    return 1 if issues else 0


def fetch_update_status(state: dict[str, Any]) -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    versions = local_versions()
    result: dict[str, Any] = {
        "framework": {
            "current": versions.get("framework"),
            "latest": None,
            "updateAvailable": False,
            "error": None,
        },
        "aiIndex": {
            "current": None,
            "latest": None,
            "updateAvailable": False,
            "healthy": False,
            "error": None,
        },
    }
    version_url = framework_version_url(config)
    if version_url:
        try:
            remote = urlopen_json(version_url)
            latest_framework = remote.get("framework")
            result["framework"]["latest"] = latest_framework
            result["framework"]["updateAvailable"] = newer_framework_version(versions.get("framework"), latest_framework)
        except (urllib.error.URLError, RuntimeError, KeyError, ValueError, json.JSONDecodeError) as exc:
            result["framework"]["error"] = str(exc)
    else:
        result["framework"]["error"] = "framework version URL unavailable"

    ai_bin = FRAMEWORK_ROOT / "bin" / ("aiindex.exe" if os.name == "nt" else "aiindex")
    ai_mcp = FRAMEWORK_ROOT / "bin" / ("aiindex-mcp.exe" if os.name == "nt" else "aiindex-mcp")
    current_ai = installed_aiindex_version(state, ai_bin, ai_mcp)
    result["aiIndex"]["current"] = current_ai
    result["aiIndex"]["healthy"] = ai_bin.exists() and ai_mcp.exists()
    try:
        release = latest_aiindex_release(config)
        latest_ai = release.get("tag_name") or release.get("name")
        result["aiIndex"]["latest"] = latest_ai
        result["aiIndex"]["updateAvailable"] = bool(latest_ai and current_ai != latest_ai)
    except (urllib.error.URLError, RuntimeError, KeyError, ValueError) as exc:
        result["aiIndex"]["error"] = str(exc)
    return result


def print_update_status(status: dict[str, Any]) -> None:
    print("Update status")
    print()
    fw = status["framework"]
    ai = status["aiIndex"]
    if fw.get("error"):
        fw_text = f"unknown ({fw['error']})"
    elif fw.get("updateAvailable"):
        fw_text = f"{fw.get('current') or 'unknown'} -> {fw.get('latest')}  UPDATE AVAILABLE"
    else:
        fw_text = f"{fw.get('current') or 'unknown'}  current"
    if ai.get("error"):
        ai_text = f"{ai.get('current') or 'unknown'}; latest unknown ({ai['error']})"
    elif not ai.get("healthy"):
        ai_text = f"{ai.get('current') or 'not installed'} -> {ai.get('latest') or 'latest'}  REPAIR NEEDED"
    elif ai.get("updateAvailable"):
        ai_text = f"{ai.get('current') or 'unknown'} -> {ai.get('latest')}  UPDATE AVAILABLE"
    else:
        ai_text = f"{ai.get('current') or 'unknown'}  current"
    print(f"Framework  {fw_text}")
    print(f"AiIndex    {ai_text}")


def check_updates(args: argparse.Namespace, state: dict[str, Any]) -> int:
    status = fetch_update_status(state)
    if args.json_output:
        print(json.dumps(status))
        return 0
    print_update_status(status)
    if not args.apply:
        return 0
    selections = {"framework", "aiindex"} if args.apply == "both" else {args.apply}
    if "framework" in selections:
        if status["framework"].get("updateAvailable"):
            update_framework_from_git(args.dry_run)
        else:
            print("  Framework already current; no update needed")
    if "aiindex" in selections:
        config = load_json(CONFIG_PATH, {})
        mcp, ai_state = install_aiindex(config, state, args.dry_run, False)
        if not args.dry_run:
            state["aiIndex"] = ai_state
            ensure_aiindex_cli_path(state, False)
    if not args.dry_run:
        state["frameworkVersion"] = local_versions().get("framework")
        state["frameworkCommit"] = git_commit(FRAMEWORK_ROOT)
        save_json(STATE_PATH, state)
    print("Preview complete. No changes were made." if args.dry_run else "Selected updates complete.")
    return 0


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
    if args.action == "update-repair" and not args.skip_framework_update:
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
    active_profiles = load_active_profiles()
    for client in clients:
        explicit = args.codex_profile if client == "codex" else args.claude_profile
        explicit = explicit or args.profile
        if args.action == "update-repair" and not explicit:
            # Repair preserves the currently active profile. Profile changes are
            # deliberate and belong to the separate change-profile operation.
            profiles[client] = active_profiles.get(client) or state.get("profiles", {}).get(client) or "medium"
            print(f"  preserving {client} profile -> {profiles[client]}")
        else:
            profiles[client] = choose_profile(client, explicit, state, args.yes)
        if profiles[client] not in {"low", "medium", "high"}:
            raise RuntimeError(f"Invalid profile for {client}: {profiles[client]}")
        # Avoid rewriting (or previewing a rewrite of) an already-selected
        # profile. Update / Repair should preserve the active profile rather
        # than looking like it is changing it.
        if active_profiles.get(client) != profiles[client]:
            set_profile(client, profiles[client], args.dry_run)
        if not args.dry_run:
            state["profiles"][client] = profiles[client]
    config = load_json(CONFIG_PATH, {})
    ai_mcp, ai_state = install_aiindex(config, state, args.dry_run, args.skip_aiindex, allow_update=not args.no_aiindex_update)
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
        state["frameworkVersion"] = local_versions().get("framework")
        save_json(STATE_PATH, state)
    print()
    if args.dry_run:
        print("Preview complete. No changes were made.")
    else:
        print(f"{args.action.replace('-', ' ').title()} complete for: {', '.join(clients)}")
    for client in clients:
        print(f"  {client}: profile={profiles[client]}")
    return 0


def change_profile(args: argparse.Namespace, state: dict[str, Any]) -> int:
    args.target = choose_target(args.target, args.yes)
    clients = target_clients(args.target)
    ai_mcp = FRAMEWORK_ROOT / "bin" / ("aiindex-mcp.exe" if os.name == "nt" else "aiindex-mcp")
    if not ai_mcp.exists():
        ai_mcp = None
    profiles: dict[str, str] = {}
    for client in clients:
        explicit = args.codex_profile if client == "codex" else args.claude_profile
        profiles[client] = choose_profile(client, explicit or args.profile, state, args.yes)
        if profiles[client] not in {"low", "medium", "high"}:
            raise RuntimeError(f"Invalid profile for {client}: {profiles[client]}")
        set_profile(client, profiles[client], args.dry_run)
        if client == "codex":
            wire_codex(profiles[client], state, args.dry_run, ai_mcp, wire_shared=False)
        else:
            wire_claude(profiles[client], state, args.dry_run, ai_mcp, wire_shared=False)
        if not args.dry_run:
            state.setdefault("profiles", {})[client] = profiles[client]
            if client not in state.setdefault("installedClients", []):
                state["installedClients"].append(client)
    if not args.dry_run:
        state["frameworkVersion"] = local_versions().get("framework")
        state["frameworkCommit"] = git_commit(FRAMEWORK_ROOT)
        save_json(STATE_PATH, state)
    print("Preview complete. No changes were made." if args.dry_run else "Profile change complete.")
    for client in clients:
        print(f"  {client}: profile={profiles[client]}")
    return 0


def uninstall(args: argparse.Namespace, state: dict[str, Any]) -> int:
    args.target = choose_target(args.target, args.yes)
    clients = target_clients(args.target)
    # Managed skill links are handled explicitly by remove_managed_skills().
    # Keep their paths so the generic recorded-link cleanup below does not
    # report/remove them a second time during dry-run previews.
    managed_skill_paths = {
        str(client_root(client) / "skills" / name)
        for client in clients
        for name in state.get("managedSkills", {}).get(client, [])
    }
    for client in clients:
        uninstall_graphify_client(client, state, args.dry_run)
        if client == "codex":
            restore_codex(state, args.dry_run)
        else:
            restore_claude(state, args.dry_run)
        remove_managed_skills(client, state, args.dry_run)
        generated = FRAMEWORK_ROOT / "generated" / client
        if generated.exists():
            remove_owned_path(generated, args.dry_run)
        if not args.dry_run and client in state["installedClients"]:
            state["installedClients"].remove(client)
            state["profiles"].pop(client, None)
    # Remove recorded links that belong to removed clients and still resolve into this framework.
    for raw in list(state.get("links", [])):
        if raw in managed_skill_paths:
            continue
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
    p.add_argument("action", choices=["install", "update-repair", "change-profile", "check-updates", "uninstall", "doctor"])
    p.add_argument("--target", choices=["codex", "claude", "both"])
    p.add_argument("--profile", choices=["low", "medium", "high"])
    p.add_argument("--codex-profile", choices=["low", "medium", "high"])
    p.add_argument("--claude-profile", choices=["low", "medium", "high"])
    p.add_argument("--yes", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--skip-aiindex", action="store_true")
    p.add_argument("--skip-graphify", action="store_true")
    p.add_argument("--skip-framework-update", action="store_true", help="Repair without pulling a newer framework version")
    p.add_argument("--no-aiindex-update", action="store_true", help="Repair AiIndex if broken but do not upgrade a healthy older version")
    p.add_argument("--apply", choices=["framework", "aiindex", "both"], help="For check-updates: apply selected updates")
    p.add_argument("--json-output", action="store_true", help="Emit machine-readable JSON where supported")
    return p


def main() -> int:
    # Keep parent-process status lines in order with output emitted by delegated
    # commands such as scripts/ai.py, even when stdout is piped by PowerShell.
    try:
        sys.stdout.reconfigure(line_buffering=True, write_through=True)
        sys.stderr.reconfigure(line_buffering=True, write_through=True)
    except (AttributeError, ValueError):
        pass

    args = parser().parse_args()
    if args.verbose:
        print(f"Framework root: {FRAMEWORK_ROOT}")
        print(f"State path: {STATE_PATH}")
    state = load_state()
    try:
        if args.action == "doctor":
            return doctor(state)
        if args.action == "check-updates":
            return check_updates(args, state)
        if args.action == "change-profile":
            return change_profile(args, state)
        if args.action in {"install", "update-repair"}:
            return install_or_repair(args, state)
        return uninstall(args, state)
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
