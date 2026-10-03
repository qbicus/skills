# Provider-aware model routing

The framework keeps reusable skills provider-agnostic. Skills request a role; the active provider configuration resolves that role to a concrete model, effort level, fallback chain, and native execution mechanism.

## Roles

| Role | Purpose | Native agent |
|---|---|---|
| `primary` | Planning, architecture, material decisions, integration, and final ownership. | Owning/main thread |
| `executor` | Bounded implementation, file edits, focused test/build loops, and routine coding work. | `ai-executor` |
| `researcher` | External documentation, library/API research, and evidence gathering outside the repository. | `ai-researcher` |
| `advisor` | Independent review at plan, repeated-failure, and substantial-completion checkpoints. | `ai-advisor` |
| `fast` | Low-risk routing and trivial decisions that do not justify a stronger model. | `ai-fast` |

Shared skills use role names, never concrete model names.

## Provider files

Global defaults:

```text
~/.ai/providers/codex.yml
~/.ai/providers/claude.yml
```

Optional repository overrides:

```text
<repo>/.ai/providers/codex.yml
<repo>/.ai/providers/claude.yml
```

Only overridden keys need to appear in a repository file. Repository values deep-merge over global values. Lists and scalar values replace their inherited value; nested mappings merge recursively.

## Executable resolution order

The runtime helper now implements this order:

1. `--provider codex|claude`, if supplied.
2. `AI_PROVIDER`, if set.
3. Known client runtime environment markers when unambiguous.
4. If no provider can be determined, fail clearly and require an explicit provider.
5. Load `~/.ai/providers/<provider>.yml` (the framework copy in the current installation).
6. Deep-merge `<repo>/.ai/providers/<provider>.yml` if present.
7. Validate the effective config.
8. Resolve the requested role's preferred model/effort.
9. If a supplied availability set excludes it, try `fallbackModels`, then `fallbackRoles` recursively.
10. Report whether fallback was used.
11. For native delegated agents, an unavailable/unsupported model must trigger the next generated `ai-<role>-fallback-N` agent explicitly. The primary thread must not silently execute the delegated task itself unless the configured fallback chain explicitly resolves to `primary` or every configured candidate is exhausted and that escalation is reported. Model startup/availability failures do not count as task-attempt failures.

Commands:

```text
python ~/.ai/scripts/ai.py provider --effective
python ~/.ai/scripts/ai.py provider --validate
python ~/.ai/scripts/ai.py provider --role executor
```

When automatic detection is unavailable:

```bash
export AI_PROVIDER=claude
```

or:

```powershell
$env:AI_PROVIDER = "codex"
```

## Provider schema

Current supported shape:

```yaml
version: 1
provider: codex

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
    effort: high
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
  explicitProviderOverrideEnvironmentVariable: AI_PROVIDER
  repositoryOverridePath: .ai/providers/codex.yml
  nativeAgentPrefix: ai-
```

Provider-specific runtime metadata may add keys under `runtime`.

## Repository override example

```yaml
roles:
  executor:
    model: <repo-preferred-model>
    effort: high

behavior:
  advisor:
    repeatedFailureThreshold: 3
```

Everything not listed continues to inherit from the global provider config.

## Validation and common config errors

Validate the merged config before rendering/installing native files:

```text
python ~/.ai/scripts/ai.py provider --provider codex --validate
```

Examples rejected by validation:

```yaml
# unknown role fallback
roles:
  advisor:
    fallbackRoles: [super-reviewer]
```

```yaml
# threshold must be >= 1
behavior:
  advisor:
    repeatedFailureThreshold: 0
```

```yaml
# parallel mode is deliberately restricted
behavior:
  execution:
    parallelMode: automatic
```

Provider YAML should use the documented schema and 2-space indentation. The helper uses PyYAML when installed and includes a small built-in parser for this framework's supported YAML subset so provider inspection does not require an extra package.

## Fallback diagnostics

Normal execution uses the preferred configured models. For diagnostics, tests, and future installer capability probing, restrict the helper to an explicit availability set:

```text
python ~/.ai/scripts/ai.py provider --provider codex --role executor --available-model gpt-5.6-sol
```

Repeat `--available-model` to supply more than one candidate.

The same availability list can be supplied to `--render-native`; generated native files then contain the resolved fallback models rather than unavailable preferred ones.

## Native rendering

The provider files are the source of truth. Native files are generated, not hand-maintained.

```text
python ~/.ai/scripts/ai.py provider --provider codex --render-native <output-dir>
python ~/.ai/scripts/ai.py provider --provider claude --render-native <output-dir>
```

Use `--repo <repo-root>` to include repository overrides.

`providers/*.yml` is the source of truth. Client-native files are rendered into local `generated/<provider>/` directories (or a temporary output directory during tests). `generated/` is machine/runtime state and is not checked into the framework repository. The installer will regenerate and merge/reference these files rather than relying on checked-in native snapshots.

### Codex

Current Codex supports custom agents in `~/.codex/agents/` / `.codex/agents/`, including per-agent `model`, `model_reasoning_effort`, and inherited session configuration. The generated config fragment declares `ai-executor`, `ai-researcher`, `ai-advisor`, and `ai-fast`, while the main thread uses the `primary` model/effort.

The generated read-only roles use `sandbox_mode = "read-only"`; executor uses `workspace-write`. Parallel capacity is capped by `maxConcurrentAgents`, but actual parallel execution still requires plan approval.

Official reference: https://learn.chatgpt.com/docs/agent-configuration/subagents

### Claude Code

Claude Code custom subagents support `model`, `effort`, `tools`, `disallowedTools`, permissions, MCP servers, skills, and other role-specific configuration. Generated framework agents apply narrower tool sets to research/review/fast roles and write/shell capability to the executor.

Official reference: https://code.claude.com/docs/en/sub-agents

## Advisor behavior

The reusable `advisor` skill supports:

- `plan` — challenge a substantial plan before it is committed/approved;
- `stuck` — reassess direction when substantially the same failure reaches the configured threshold;
- `complete` — check that substantial work has not skipped requirements, validation, tests, rollout, or documentation before completion is declared.

The framework checkpoint contract uses compact, purpose-specific context and does not silently take over implementation.

### Claude native advisor

Claude Code also has a native advisor tool. It is **not the default implementation of framework checkpoints** because the native advisor receives the full conversation for every consultation. `ai-advisor` preserves the framework's compact-context contract.

Native advisor remains an optional/manual full-session second opinion. As of 2026-10-03, Claude documentation states that Fable is temporarily unavailable as a native advisor selection. The provider retains `preferredWhenAvailable: fable`, while the current `advisor` role resolves to `opus`.

Official reference: https://code.claude.com/docs/en/advisor

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

`new-feature` records the classification in the approved spec and carries it through design, task planning, execution, and final review.

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

`maxConcurrentAgents` is only an upper bound. Task dependency order and conflict checks remain authoritative.
