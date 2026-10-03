# Codex Setup

> Automated installation/update/uninstall is still pending. The runtime adapter and native Codex fragments are implemented; the installer will merge them safely into the user's Codex configuration without replacing unrelated settings.

## Global folders

```text
%USERPROFILE%\.codex   # Codex runtime/config
%USERPROFILE%\.ai      # shared company AI framework
```

## Global instructions

Codex should receive the company framework instructions from:

```text
%USERPROFILE%\.ai\AGENTS.md
```

Keep the shared framework as the source of truth rather than maintaining a divergent copy of company rules.

## Skills

Expose company-owned skills from:

```text
%USERPROFILE%\.ai\skills
```

through Codex's native skill mechanism. Leave Codex-owned and third-party skills under Codex management.

## Provider routing

Global Codex routing policy:

```text
%USERPROFILE%\.ai\providers\codex.yml
```

Optional repository override:

```text
<repo>\.ai\providers\codex.yml
```

Shared skills request the provider-neutral roles `primary`, `executor`, `researcher`, `advisor`, and `fast`.

Effective config and fallback resolution can be inspected now:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --effective
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --validate
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --role executor
```

## Native Codex agents

Current Codex supports custom agent TOML files with per-agent model/reasoning settings and session configuration. The framework renderer produces:

```text
ai-executor
ai-researcher
ai-advisor
ai-fast
```

`primary` remains the owning/main Codex thread.

Generate the native files for the global defaults:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider `
  --provider codex `
  --render-native "$env:USERPROFILE\.ai\generated\codex"
```

Generate them using a repository override:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider `
  --provider codex `
  --repo "D:\Work\MyRepo" `
  --render-native "$env:USERPROFILE\.ai\generated\codex"
```

Output:

```text
config.fragment.toml
agents/ai-executor.toml
agents/ai-researcher.toml
agents/ai-advisor.toml
agents/ai-fast.toml
```

The renderer intentionally does **not** write into `~/.codex`. The installer will own safe merge/update/uninstall and preserve unrelated Codex settings and agents.

### Fallback testing

To test how a reduced model set resolves without changing provider config:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider `
  --provider codex `
  --role executor `
  --available-model gpt-5.6-sol
```

`--available-model` can be repeated and can also be supplied while rendering native files. This is primarily a diagnostics/installer hook; normal operation uses the provider's preferred mapping.

### Runtime fallback contract

Codex does not automatically infer that `ai-fast-fallback-1` is the retry for `ai-fast`. The framework therefore makes fallback an explicit parent-orchestration rule: if `ai-<role>` cannot start because its model is unavailable/unsupported, invoke `ai-<role>-fallback-1`, then later generated fallbacks in order. Do not silently complete the delegated task in the primary thread. Only use primary when provider configuration explicitly resolves to it or the configured native chain is exhausted and that escalation is reported.

## Parallel execution

Codex can run subagents, but this framework remains **plan-controlled**. Native multi-agent support must not be treated as permission to fan out automatically. `parallel-exec` runs only for tasks explicitly marked parallel-safe/eligible by the approved plan and after parallel execution is selected.

The provider setting `behavior.execution.maxConcurrentAgents` becomes the generated Codex `max_concurrent_threads_per_session` cap. It is a ceiling, not an instruction to use that many agents.

## Initialize a project

From inside a repository:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1"
```

or choose a project type:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet
& "$env:USERPROFILE\.ai\init-project.ps1" -Type go
& "$env:USERPROFILE\.ai\init-project.ps1" -Type nextjs
& "$env:USERPROFILE\.ai\init-project.ps1" -Type python
& "$env:USERPROFILE\.ai\init-project.ps1" -Type vb-migration
```

## Current limitation

Native files are generated under `~/.ai/generated/codex/` (or another explicit `--render-native` output directory). The generated Codex config fragment points directly at those rendered agent files, so the agents do not need to be copied into `~/.codex/agents/`. Automatic safe merging into `~/.codex/config.toml` is intentionally deferred to the installer; until then, merge only the generated `[agents]` sections and preserve unrelated Codex configuration.

For full command/skill help, see `README.md`, `HELP.md`, and `docs/model-routing.md`.
