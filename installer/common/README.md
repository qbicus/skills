# Installer internals

The public entry points are `install.ps1` and `install.sh` at the repository root.
Both bootstrap Git + uv, locate/clone the framework, then invoke `installer/installer.py`.

Installer-owned machine state is stored under:

```text
~/.ai/local/installer-state.json
```

Generated provider/native state remains under `~/.ai/generated/` and is disposable.
Repository-local `.ai/providers/` overrides and `.ai-index*` project data are never owned by this installer.

## Repository URL

For a pipe/bootstrap install, set either:

- `AI_FRAMEWORK_REPO_URL`, or
- `frameworkRepositoryUrl` in `installer/config.json` before publishing the installer.

When running from an existing checkout, the installer can use that checkout directly.

## AiIndex private Gitea access

The default latest-release API points at the known AiIndex Gitea repository. If the
release API requires authentication, set `AIINDEX_GITEA_TOKEN` in the environment.
The token is sent as an Authorization header and is never written to installer state/logs.
