# AI Framework Installer

Public bootstrap entry points:

- `install.ps1` — Windows interactive + non-interactive installer
- `install.sh` — Linux shell bootstrap / non-interactive lifecycle entry point

Both use the shared `installer/installer.py` lifecycle core. The framework requires Git, Python 3.11+, and `uv`; bootstrap installs missing prerequisites where supported. Python, Git, and `uv` are never removed by framework uninstall.

## Lifecycle

```text
install
update-repair
change-profile
check-updates
uninstall
doctor
```

Windows with no arguments opens the interactive maintenance console:

```powershell
.\install.ps1
```

Menu:

```text
Install
Update / Repair
Change profiles
Check for updates
Uninstall
Doctor
Preview changes
Exit
```

Targets are `codex`, `claude`, or `both`. Profiles are `low`, `medium`, or `high`.

## Examples

Windows:

```powershell
.\install.ps1 install -Target codex -Profile low -Yes
.\install.ps1 update-repair -Target both -Yes
.\install.ps1 change-profile -Target codex -Profile medium -Yes
.\install.ps1 check-updates
.\install.ps1 doctor
```

Linux:

```bash
./install.sh install --target codex --profile low --yes
./install.sh update-repair --target both --yes
./install.sh change-profile --target codex --profile medium --yes
./install.sh check-updates
./install.sh doctor
```

## Repository and versions

Canonical framework repository:

```text
https://github.com/qbicus/skills.git
```

`version.json` contains the framework version and bundled/expected AiIndex release tag. The installer compares the local framework version to the repository's `version.json`, and the installed AiIndex version to the latest GitHub release.

AiIndex release API:

```text
https://api.github.com/repos/qbicus/skills/releases/latest
```

Release downloads are checksum-verified with `SHA256SUMS`.

## Skill ownership

Framework skills keep their canonical names (`new-feature`, `debug`, `advisor`, etc.). The installer never prefixes skill names. Correct existing links/junctions are adopted; broken or wrong-target framework links are repaired; unrelated real directories are preserved and reported as conflicts.

Managed skill names are recorded per client in `~/.ai/local/installer-state.json` so uninstall removes only installer-managed framework links.

## Update / Repair

Update / Repair preserves the currently selected provider profile unless an explicit profile override is supplied. It repairs missing/broken installer-owned wiring and skips a healthy current AiIndex runtime.

The interactive Windows flow checks for available Framework/AiIndex updates and asks whether to include them in the repair.

## Graphify

The Python package is `graphifyy`; the CLI is `graphify`.

An existing Graphify tool and existing client skill integration are preserved. The installer only installs the Graphify tool or client integration when missing.

## Shared state

Installer-owned state is recorded under:

```text
~/.ai/local/installer-state.json
```

Generated native provider wiring lives under `~/.ai/generated/` and is disposable/rebuildable.

The installer never owns or removes repository-local `.ai/providers/`, `.ai-index.json`, or `.ai-index/`.
