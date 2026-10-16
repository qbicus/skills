# Installer internals

Windows x64 is the currently live-validated lifecycle path. Linux shares this core but still requires live lifecycle validation.

Public entry points:

- `install.ps1`
- `install.sh`

Shared lifecycle implementation:

```text
installer/installer.py
```

Canonical repository:

```text
https://github.com/qbicus/skills.git
```

Installer state:

```text
~/.ai/local/installer-state.json
```

Generated provider/native state:

```text
~/.ai/generated/
```

Repository-local provider overrides and `.ai-index*` project data are never installer-owned.

## Version sources

Framework metadata is stored in root `version.json`. The current public copy used for update checks is:

```text
https://raw.githubusercontent.com/qbicus/skills/main/version.json
```

AiIndex latest release metadata comes from:

```text
https://api.github.com/repos/qbicus/skills/releases/latest
```

A `GITHUB_TOKEN` may be supplied only to increase GitHub API rate limits; normal public installs do not require authentication.

## Prerequisites

Git, Python 3.11+, and `uv` are first-class prerequisites. Bootstrap may install them if absent, but uninstall never removes them.
