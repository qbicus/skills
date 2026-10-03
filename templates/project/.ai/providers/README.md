# Repository provider overrides

Optional project-specific overrides for the shared provider policy.

Create only the file(s) you need:

```text
.ai/providers/codex.yml
.ai/providers/claude.yml
```

Repository values deep-merge over the corresponding global file under `~/.ai/providers/`.

Example:

```yaml
roles:
  executor:
    model: <project-specific-model>
    effort: high

behavior:
  advisor:
    repeatedFailureThreshold: 3
```

You may override model routing and orchestration behavior. Do not copy the full global provider file unless the repository genuinely needs to own every setting; small overrides are easier to keep current.

## Native role agents

Changing a repository provider override changes the framework's effective routing immediately for helper diagnostics, but native Codex/Claude agent files must be regenerated/re-synced before the client-native role definitions use the new model settings.

Inspect the effective repo config:

```text
python ~/.ai/scripts/ai.py provider --repo <repo-root> --effective
```

Render native fragments for review/sync:

```text
python ~/.ai/scripts/ai.py provider --provider codex --repo <repo-root> --render-native <output-dir>
python ~/.ai/scripts/ai.py provider --provider claude --repo <repo-root> --render-native <output-dir>
```

The installer will automate safe syncing while preserving unrelated project/client configuration.
