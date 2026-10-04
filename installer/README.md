# AI Framework Installer

Public bootstrap entry points:

- `install.ps1` — Windows
- `install.sh` — Linux/macOS-compatible shell bootstrap (Linux is the first validated target)

Both ensure the shared prerequisites (Git, compatible Python, and `uv`) and then hand off to the shared `installer/installer.py` lifecycle core using the installed Python runtime.

## Lifecycle

```text
install
update-repair
uninstall
doctor
```

Targets:

```text
codex
claude
both
```

Profiles:

```text
low
medium
high
```

## Examples

Windows:

```powershell
.\install.ps1 install -Target codex -Profile low
.\install.ps1 update-repair -Target both
.\install.ps1 doctor
```

Linux:

```bash
./install.sh install --target codex --profile low
./install.sh update-repair --target both
./install.sh doctor
```

## Shared state

Installer-owned state is recorded under `~/.ai/local/installer-state.json`. Generated client wiring lives under `~/.ai/generated/` and is disposable/rebuildable.

The installer does not own repository-local `.ai/providers/`, `.ai-index.json`, or `.ai-index/`.

## Current release configuration requirement

For a raw pipe bootstrap, the framework repository URL must be available via `AI_FRAMEWORK_REPO_URL` (or be embedded before publishing the bootstrap script). Existing checkouts do not need this variable.

AiIndex latest-release resolution defaults to the configured Gitea API in `installer/config.json`; set `AIINDEX_GITEA_TOKEN` only when that private release endpoint requires authentication.

## Bootstrap prerequisites

The framework itself uses Python, so Python is a first-class prerequisite rather than an installer-only runtime.

- Existing Python `>= 3.11` is accepted and left unchanged.
- On Windows, a missing/unsupported Python is installed from the highest stable `Python.Python.3.x` package currently available through `winget`.
- On Linux, a missing/unsupported Python is installed using the distribution package manager (`apt`, `dnf`, `yum`, `pacman`, `zypper`, or `apk`). The resulting interpreter must be Python 3.11 or newer.
- Git and `uv` are installed when missing.
- Python, Git, and `uv` are never removed by framework uninstall, even when the bootstrap originally installed them.

The installer records whether those prerequisites were pre-existing or installed by the framework bootstrap for diagnostics only.


Doctor and uninstall are intentionally non-mutating with respect to system prerequisites: they require an existing compatible Python runtime and never install Git, Python, or uv.
