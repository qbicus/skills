#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]
PROJECT_TYPES = ["base", "dotnet", "vb-migration", "go", "nextjs", "python"]
PROJECT_TYPE_LABELS = {
    "base": "Base / generic",
    "dotnet": ".NET / C#",
    "vb-migration": "VB.NET migration",
    "go": "Go",
    "nextjs": "Next.js",
    "python": "Python",
}
ACTIONS = ["update", "reinit", "dry-run", "cancel"]
ACTION_LABELS = {
    "update": "Update / repair missing files only",
    "reinit": "Re-init safely (apply templates again, still no overwrites)",
    "dry-run": "Preview only",
    "cancel": "Cancel",
}


@dataclass(frozen=True)
class InstallStatus:
    has_agents: bool
    has_claude: bool
    has_ai_dir: bool
    has_session_state: bool
    has_codex_hooks: bool

    @property
    def is_installed(self) -> bool:
        return self.has_agents or self.has_claude or self.has_ai_dir or self.has_session_state


def find_repo(start: Path) -> Path:
    current = start.resolve()
    for p in [current, *current.parents]:
        if (p / ".git").exists():
            return p
    return current


def get_install_status(repo: Path) -> InstallStatus:
    return InstallStatus(
        has_agents=(repo / "AGENTS.md").exists(),
        has_claude=(repo / "CLAUDE.md").exists(),
        has_ai_dir=(repo / ".ai").exists(),
        has_session_state=(repo / ".ai" / ".session-state.json").exists(),
        has_codex_hooks=(repo / ".codex" / "hooks.json").exists(),
    )


def print_install_status(status: InstallStatus) -> None:
    if not status.is_installed:
        print("\nNo existing project AI setup detected.")
        return

    print("\nExisting project AI setup detected:")
    print(f"  {'✓' if status.has_agents else '×'} AGENTS.md")
    print(f"  {'✓' if status.has_claude else '×'} CLAUDE.md")
    print(f"  {'✓' if status.has_ai_dir else '×'} .ai/")
    print(f"  {'✓' if status.has_session_state else '×'} .ai/.session-state.json")
    print(f"  {'✓' if status.has_codex_hooks else '×'} .codex/hooks.json")


def copy_missing(src: Path, dest: Path, dry_run: bool, created: list[str], skipped: list[str]) -> None:
    if dest.exists():
        skipped.append(str(dest))
        return
    if dry_run:
        created.append(str(dest))
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        dest.mkdir(parents=True, exist_ok=True)
    else:
        shutil.copy2(src, dest)
    created.append(str(dest))


def copy_tree_missing(template_root: Path, repo: Path, dry_run: bool) -> tuple[list[str], list[str]]:
    created: list[str] = []
    skipped: list[str] = []
    if not template_root.exists():
        return created, skipped
    for src in sorted(template_root.rglob("*")):
        rel = src.relative_to(template_root)
        dest = repo / rel
        if src.is_dir():
            if not dest.exists():
                if not dry_run:
                    dest.mkdir(parents=True, exist_ok=True)
                created.append(str(dest))
            else:
                skipped.append(str(dest))
        else:
            copy_missing(src, dest, dry_run, created, skipped)
    return created, skipped


def ask_yes_no(prompt: str, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    answer = input(f"{prompt} {suffix}: ").strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes", "1", "true"}


def ask_project_type(default: str = "base") -> str:
    print("\nSelect project type:")
    for i, key in enumerate(PROJECT_TYPES, start=1):
        default_marker = " (default)" if key == default else ""
        print(f"  [{i}] {PROJECT_TYPE_LABELS[key]}{default_marker}")

    while True:
        answer = input("Choice: ").strip().lower()
        if not answer:
            return default
        if answer.isdigit():
            idx = int(answer)
            if 1 <= idx <= len(PROJECT_TYPES):
                return PROJECT_TYPES[idx - 1]
        if answer in PROJECT_TYPES:
            return answer
        print("Invalid choice. Enter a number or one of: " + ", ".join(PROJECT_TYPES))


def ask_existing_action(default: str = "update") -> str:
    print("\nWhat do you want to do?")
    for i, key in enumerate(ACTIONS, start=1):
        default_marker = " (default)" if key == default else ""
        print(f"  [{i}] {ACTION_LABELS[key]}{default_marker}")

    while True:
        answer = input("Choice: ").strip().lower()
        if not answer:
            return default
        if answer.isdigit():
            idx = int(answer)
            if 1 <= idx <= len(ACTIONS):
                return ACTIONS[idx - 1]
        if answer in ACTIONS:
            return answer
        print("Invalid choice. Enter a number or one of: " + ", ".join(ACTIONS))


def should_prompt(args: argparse.Namespace) -> bool:
    if args.non_interactive:
        return False
    if args.type is not None or args.action is not None:
        return False
    return sys.stdin.isatty()


def get_templates(project_type: str) -> list[Path]:
    templates = [FRAMEWORK_ROOT / "templates" / "project"]
    if project_type == "dotnet":
        templates.append(FRAMEWORK_ROOT / "templates" / "dotnet")
    elif project_type == "vb-migration":
        templates.append(FRAMEWORK_ROOT / "templates" / "dotnet")
        templates.append(FRAMEWORK_ROOT / "templates" / "vb-migration")
    elif project_type == "go":
        templates.append(FRAMEWORK_ROOT / "templates" / "go")
    elif project_type == "nextjs":
        templates.append(FRAMEWORK_ROOT / "templates" / "nextjs")
    elif project_type == "python":
        templates.append(FRAMEWORK_ROOT / "templates" / "python")
    return templates


def create_project_hooks(repo: Path, dry_run: bool, created: list[str], skipped: list[str]) -> None:
    hook_dest = repo / ".codex" / "hooks.json"
    if hook_dest.exists():
        skipped.append(str(hook_dest))
        return

    created.append(str(hook_dest))
    if dry_run:
        return

    hook_dest.parent.mkdir(parents=True, exist_ok=True)
    hook_dest.write_text(json.dumps({
        "hooks": {
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python \"%USERPROFILE%\\.ai\\hooks\\codex_session_close_guard.py\"",
                            "statusMessage": "Checking whether session-close is needed"
                        }
                    ]
                }
            ]
        }
    }, indent=2) + "\n", encoding="utf-8")



def install_graphify_claude(repo: Path, dry_run: bool) -> None:
    """Install Graphify's Claude integration and normalize its routing section.

    The actual install/normalization logic lives in the shared PowerShell wrapper so
    repo-init does not duplicate the AiIndex/Graphify routing policy.
    """
    installer = FRAMEWORK_ROOT / "scripts" / "install-graphify-claude.ps1"
    if not installer.exists():
        raise RuntimeError(f"Graphify Claude installer not found: {installer}")

    if dry_run:
        print(f"\nGraphify Claude integration: would run {installer} for {repo}")
        return

    # Prefer PowerShell 7 for cross-platform framework use, then Windows PowerShell.
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        raise RuntimeError(
            "PowerShell was not found. Install PowerShell 7 (pwsh) or run the "
            "Graphify Claude installer manually."
        )

    result = subprocess.run(
        [
            shell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(installer),
            "-RepoPath",
            str(repo),
        ],
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Graphify Claude integration failed with exit code {result.returncode}."
        )

def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize or update repository AI framework files without overwriting existing files.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without writing files.")
    parser.add_argument("--type", choices=PROJECT_TYPES, default=None, help="Additional template type to apply. If omitted in an interactive terminal, you will be prompted.")
    parser.add_argument("--action", choices=ACTIONS, default=None, help="Action to perform for an existing setup. Defaults to update in non-interactive mode.")
    parser.add_argument("--with-codex-hooks", action="store_true", help="Create project-local .codex/hooks.json if missing.")
    parser.add_argument("--with-graphify-claude", action="store_true", help="Install Graphify Claude integration and normalize its CLAUDE.md routing section.")
    parser.add_argument("--repo", default=None, help="Repository path. Defaults to current directory or nearest git repo.")
    parser.add_argument("--non-interactive", action="store_true", help="Do not ask questions. Defaults to base type and update action unless flags are provided.")
    args = parser.parse_args()

    start = Path(args.repo) if args.repo else Path.cwd()
    repo = find_repo(start)
    status = get_install_status(repo)

    project_type = args.type or "base"
    action = args.action or "update"
    dry_run = args.dry_run
    with_codex_hooks = args.with_codex_hooks
    with_graphify_claude = args.with_graphify_claude

    if should_prompt(args):
        print("AI Project Initializer")
        print(f"Framework: {FRAMEWORK_ROOT}")
        print(f"Target:    {repo}")
        print_install_status(status)

        if status.is_installed:
            action = ask_existing_action(default="update")
            if action == "cancel":
                print("\nCancelled. No files were changed.")
                return 0
            if action == "dry-run":
                dry_run = True
                action = "update"
        else:
            action = "update"

        project_type = ask_project_type(default="base")
        with_codex_hooks = ask_yes_no("Add Codex project hooks?", default=False)
        with_graphify_claude = ask_yes_no("Install Graphify Claude integration?", default=False)
        if not dry_run:
            dry_run = ask_yes_no("Dry run only?", default=False)

    if action == "cancel":
        print("Cancelled. No files were changed.")
        return 0
    if action == "dry-run":
        dry_run = True
        action = "update"

    templates = get_templates(project_type)

    all_created: list[str] = []
    all_skipped: list[str] = []
    for template in templates:
        created, skipped = copy_tree_missing(template, repo, dry_run)
        all_created.extend(created)
        all_skipped.extend(skipped)

    if with_codex_hooks:
        create_project_hooks(repo, dry_run, all_created, all_skipped)

    if with_graphify_claude:
        install_graphify_claude(repo, dry_run)

    print(f"\nRepository: {repo}")
    print(f"Detected setup: {'yes' if status.is_installed else 'no'}")
    print(f"Action: {action} ({ACTION_LABELS.get(action, action)})")
    print(f"Template type: {project_type} ({PROJECT_TYPE_LABELS[project_type]})")
    print(f"Graphify Claude: {'enabled' if with_graphify_claude else 'disabled'}")
    if dry_run:
        print("Mode: dry-run")

    # De-duplicate output while preserving order. This keeps dry-run output readable
    # when multiple templates share parent folders such as `.ai`.
    all_created = list(dict.fromkeys(all_created))
    all_skipped = list(dict.fromkeys(all_skipped))

    print("\nCreated / would create:")
    if all_created:
        for item in all_created:
            print(f"  + {item}")
    else:
        print("  (none)")

    print("\nSkipped existing:")
    if all_skipped:
        for item in all_skipped:
            print(f"  = {item}")
    else:
        print("  (none)")

    if status.is_installed and not all_created and not dry_run:
        print("\nProject AI setup already appears complete for the selected template.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
