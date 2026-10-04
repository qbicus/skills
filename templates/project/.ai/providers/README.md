# Repository provider overrides

Optional project-specific overrides for the shared provider policy.

Create only the file(s) you need:

```text
.ai/providers/codex.yml
.ai/providers/claude.yml
.ai/providers/codex.low.yml       # optional low-profile-only override
.ai/providers/codex.medium.yml    # optional medium-profile-only override
.ai/providers/codex.high.yml      # optional high-profile-only override
.ai/providers/claude.low.yml
.ai/providers/claude.medium.yml
.ai/providers/claude.high.yml
```

The generic provider override applies to every selected profile. A profile-specific override applies last. Global `medium` is stored in `~/.ai/providers/<provider>.yml`; global low/high profiles use `<provider>.low.yml` / `<provider>.high.yml`.

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
python ~/.ai/scripts/ai.py provider --repo <repo-root> --profile low --effective
```

Render native fragments for review/sync:

```text
python ~/.ai/scripts/ai.py provider --provider codex --profile low --repo <repo-root> --render-native <output-dir>
python ~/.ai/scripts/ai.py provider --provider claude --profile high --repo <repo-root> --render-native <output-dir>
```

The installer will automate safe syncing while preserving unrelated project/client configuration.
