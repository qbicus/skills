# Provider-aware model routing

The framework keeps reusable skills provider-agnostic. Skills request a role; the active provider profile resolves that role to a concrete model, effort level, fallback chain, and native execution mechanism.

## Roles

| Role | Purpose | Native agent |
|---|---|---|
| `primary` | Planning, architecture, material decisions, integration, and final ownership. | Owning/main thread |
| `executor` | Bounded implementation, file edits, focused test/build loops, and routine coding work. | `ai-executor` |
| `researcher` | External documentation, library/API research, and evidence gathering outside the repository. | `ai-researcher` |
| `advisor` | Independent review at plan, repeated-failure, and substantial-completion checkpoints. | `ai-advisor` |
| `fast` | Low-risk routing and trivial decisions that do not justify a stronger model. | `ai-fast` |

Shared skills use role names, never concrete model names.

## Usage profiles

Both providers expose three cost/quality profiles:

| Profile | Intent | Typical policy |
|---|---|---|
| `low` | Conserve usage/quota | Lower reasoning effort, cheaper capable models, lower concurrency |
| `medium` | Recommended/default | Balanced flagship-primary + mid-tier execution/review |
| `high` | Quality-first difficult work | Stronger/higher-effort execution and review |

`medium` is the default when no explicit, environment, or saved per-provider profile is set.

Global profile files:

```text
~/.ai/providers/codex.yml          # medium/default
~/.ai/providers/codex.low.yml
~/.ai/providers/codex.high.yml
~/.ai/providers/claude.yml         # medium/default
~/.ai/providers/claude.low.yml
~/.ai/providers/claude.high.yml
```

Profiles change model/effort/concurrency policy. They do **not** disable the shared workflow contract: advisor checkpoints remain substantial-only unless explicitly overridden, workers remain bounded, fallback remains explicit, and parallel execution remains plan-only.

Current recommended mappings:

| Codex | low | medium | high |
|---|---|---|---|
| primary | GPT-5.6 Sol / medium | GPT-6 Astra / high | GPT-6 Astra / high |
| executor | GPT-5.6 Sol / low | GPT-5.6 Sol / medium | GPT-6 Sol / high |
| researcher | GPT-5.6 Sol / low | GPT-5.6 Sol / medium | GPT-6 Sol / high |
| advisor | GPT-5.6 Sol / low | GPT-5.6 Sol / medium | GPT-6 Sol / high |
| fast | GPT-6 Luna / low | GPT-6 Luna / low | GPT-6 Luna / low |
| max agents | 2 | 4 | 4 |

| Claude | low | medium | high |
|---|---|---|---|
| primary | Sonnet / medium | Opus / high | Opus / high |
| executor | Sonnet / low | Sonnet / medium | Sonnet / high |
| researcher | Sonnet / low | Sonnet / medium | Sonnet / high |
| advisor | Sonnet / low | Sonnet / medium | Opus / high |
| fast | Haiku / low | Haiku / low | Haiku / low |
| max agents | 2 | 4 | 4 |

Model availability remains account/workspace-specific; fallback and Doctor should treat availability as runtime evidence rather than infer it from model names.

## Profile selection

Selection precedence:

1. `--profile low|medium|high`, when supplied;
2. `AI_PROFILE`, when set;
3. saved per-provider selection under `~/.ai/local/provider-profiles.json`;
4. `medium`.

Examples:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --profile low --effective
$env:AI_PROFILE = "high"
```

```bash
python ~/.ai/scripts/ai.py provider --provider claude --profile low --effective
export AI_PROFILE=high
```

Persist the usual profile independently per provider:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --set-profile low
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider claude --set-profile medium
```

Saved selections live in ignored machine-local state at `~/.ai/local/provider-profiles.json`.

Changing the profile used by the helper does not mutate already-generated native Codex/Claude agent files. Re-render/re-sync native client wiring after switching the profile.

## Repository overrides

Generic overrides apply to every selected profile:

```text
<repo>/.ai/providers/codex.yml
<repo>/.ai/providers/claude.yml
```

Optional profile-specific overrides apply last:

```text
<repo>/.ai/providers/codex.low.yml
<repo>/.ai/providers/codex.medium.yml
<repo>/.ai/providers/codex.high.yml
<repo>/.ai/providers/claude.low.yml
<repo>/.ai/providers/claude.medium.yml
<repo>/.ai/providers/claude.high.yml
```

Only overridden keys need to appear in a repository file. Mappings deep-merge; lists and scalar values replace the inherited value.

## Executable resolution order

The runtime helper implements this order:

1. `--provider codex|claude`, if supplied.
2. `AI_PROVIDER`, if set.
3. Known client runtime environment markers when unambiguous.
4. If no provider can be determined, fail clearly and require an explicit provider.
5. Resolve the profile from `--profile`, `AI_PROFILE`, saved per-provider state, then `medium`.
6. Load the selected global profile (`<provider>.yml` for medium, `<provider>.low.yml` / `<provider>.high.yml` otherwise).
7. Deep-merge `<repo>/.ai/providers/<provider>.yml` if present.
8. Deep-merge `<repo>/.ai/providers/<provider>.<profile>.yml` if present.
9. Validate the effective config.
10. Resolve the requested role's preferred model/effort.
11. If a supplied availability set excludes it, try `fallbackModels`, then `fallbackRoles` recursively.
12. Report whether fallback was used.
13. For native delegated agents, an unavailable/unsupported model must trigger the next generated `ai-<role>-fallback-N` agent explicitly. The primary thread must not silently execute the delegated task itself unless the configured fallback chain explicitly resolves to `primary` or every configured candidate is exhausted and that escalation is reported. Model startup/availability failures do not count as task-attempt failures.

Commands:

```text
python ~/.ai/scripts/ai.py provider --effective
python ~/.ai/scripts/ai.py provider --profile low --effective
python ~/.ai/scripts/ai.py provider --profile high --validate
python ~/.ai/scripts/ai.py provider --role executor
```

## Provider schema

Current supported shape:

```yaml
version: 1
provider: codex
profile: medium

roles:
  primary:
    model: <model>
    effort: high
    fallbackModels:
      - <fallback-model>

  executor:
    model: <model>
    effort: medium
    fallbackModels:
      - <fallback-model>

  researcher:
    model: <model>
    effort: medium

  advisor:
    model: <model>
    effort: medium
    fallbackRoles:
      - executor
      - primary

  fast:
    model: <model>
    effort: low
    fallbackRoles:
      - executor
      - primary

behavior:
  advisor:
    repeatedFailureThreshold: 2
    completionCheck: substantial-only
    planCheck: substantial-only
  execution:
    workerScope: bounded
    parallelMode: plan-only
    maxConcurrentAgents: 4
  workClassification:
    defaultSubstantial: false

runtime:
  automaticDetection: true
  defaultProfile: medium
  explicitProviderOverrideEnvironmentVariable: AI_PROVIDER
  explicitProfileOverrideEnvironmentVariable: AI_PROFILE
  repositoryOverridePath: .ai/providers/codex.yml
  repositoryProfileOverridePath: .ai/providers/codex.{profile}.yml
  nativeAgentPrefix: ai-
```

Provider-specific runtime metadata may add keys under `runtime`.

## Repository override example

Generic override, applied to every profile:

```yaml
behavior:
  advisor:
    repeatedFailureThreshold: 3
```

Profile-only override:

```yaml
# <repo>/.ai/providers/codex.low.yml
roles:
  fast:
    effort: medium
```

## Validation and diagnostics

Validate a selected profile before rendering/installing native files:

```text
python ~/.ai/scripts/ai.py provider --provider codex --profile medium --validate
python ~/.ai/scripts/ai.py provider --provider codex --profile low --validate
python ~/.ai/scripts/ai.py provider --provider codex --profile high --validate
```

Examples rejected by validation include unknown fallback roles, repeated-failure thresholds below `1`, or unsupported automatic parallel modes.

Provider YAML should use the documented schema and 2-space indentation. The helper uses PyYAML when installed and includes a small built-in parser for this framework's supported YAML subset so provider inspection does not require an extra package.

## Fallback diagnostics

Normal execution uses the preferred configured models. For diagnostics, tests, and future installer capability probing, restrict the helper to an explicit availability set:

```text
python ~/.ai/scripts/ai.py provider --provider codex --profile medium --role executor --available-model gpt-6-sol
```

Repeat `--available-model` to supply more than one candidate. The same availability list can be supplied to `--render-native`; generated native files then contain the resolved fallback models rather than unavailable preferred ones.

### Runtime fallback contract

Native clients do not infer that `ai-fast-fallback-1` is the retry for `ai-fast`. The framework therefore makes fallback an explicit parent-orchestration rule: if `ai-<role>` cannot start because its model is unavailable/unsupported, invoke `ai-<role>-fallback-1`, then later generated fallbacks in order. Do not silently complete the delegated task in the primary thread. Only use primary when provider configuration explicitly resolves to it or the configured native chain is exhausted and that escalation is reported.

## Native rendering

The selected provider profile plus repository overrides are the source of truth. Native files are generated, not hand-maintained.

```text
python ~/.ai/scripts/ai.py provider --provider codex --profile medium --render-native ~/.ai/generated/codex
python ~/.ai/scripts/ai.py provider --provider codex --profile low --render-native ~/.ai/generated/codex
python ~/.ai/scripts/ai.py provider --provider claude --profile high --render-native ~/.ai/generated/claude
```

Use `--repo <repo-root>` to include repository overrides.

`generated/` is machine/runtime state and is not checked into the framework repository. The installer will regenerate and merge/reference these files rather than relying on checked-in native snapshots.

### Codex

The generated config fragment declares `ai-executor`, `ai-researcher`, `ai-advisor`, and `ai-fast`, while the main thread uses the selected profile's `primary` model/effort. Read-only roles use `sandbox_mode = "read-only"`; executor uses `workspace-write`. `behavior.execution.maxConcurrentAgents` becomes the native concurrency cap, but actual parallel execution still requires plan approval.

### Claude Code

Generated Claude subagents apply the selected profile's `model`, `effort`, and role-specific tool boundaries. The owning/main Claude conversation uses the selected profile's `primary` mapping.

## Advisor behavior

The reusable `advisor` skill supports:

- `plan` — challenge a substantial plan before it is committed/approved;
- `stuck` — reassess direction when substantially the same failure reaches the configured threshold;
- `complete` — check that substantial work has not skipped requirements, validation, tests, rollout, or documentation before completion is declared.

The framework checkpoint contract uses compact, purpose-specific context and does not silently take over implementation.

### Claude native advisor

Claude Code's native advisor is **not** the default implementation of framework checkpoints because it receives the full conversation for every consultation. `ai-advisor` preserves the framework's compact-context contract. Native advisor remains an optional/manual full-session second opinion. The selected Claude profile still controls the portable `ai-advisor` model/effort.

## Substantial work

Parent workflows explicitly classify work using:

```yaml
substantial: true
```

or:

```yaml
substantial: false
```

Do not infer substantial work from file count alone. Treat features, migrations, modernization, architecture changes, and non-trivial debugging as substantial by default unless the parent workflow has a clear reason not to. Small local edits normally classify as false.

## Worker scope

`bounded` means an executor receives an explicit task scope but may touch directly related files required to complete that task, such as an interface paired with its implementation or focused tests. It must report meaningful scope expansion. A new architecture, contract, storage, rollout, or cross-cutting decision must be escalated as `NEEDS_DECISION` rather than silently absorbed.

Standard outcomes:

- `COMPLETE`
- `BLOCKED`
- `NEEDS_DECISION`
- `NEEDS_RESEARCH`

`NEEDS_DECISION` routes back to `primary`; `NEEDS_RESEARCH` routes to `researcher`. `BLOCKED` must state the missing prerequisite and evidence collected so far.

## Fast role safety

`fast` is only for low-risk, reversible, local decisions: targeted existence checks, simple classification/routing, narrow file/symbol lookup, or mechanical questions where a wrong answer is easy to detect and recover from.

Do not delegate architecture, contracts, security, storage, deployment, user-impacting behavior, or irreversible decisions to `fast`. Escalate uncertain work to `executor` or `primary`.

## Research role

Use `researcher` when safe execution depends on external/current evidence such as library documentation, provider behavior, API contracts, release notes, compatibility constraints, or standards. Keep raw research out of the main thread where practical; return concise findings and references.

## Parallel execution

Parallel execution is never enabled merely because tasks appear independent. A planning artifact must explicitly mark the work `parallel-safe`/`parallel-eligible`, and the user or parent workflow must select parallel execution before `parallel-exec` starts workers.

`maxConcurrentAgents` is only an upper bound. Task dependency order and conflict checks remain authoritative. Low profiles intentionally use a lower cap; that does not authorize automatic fan-out.
