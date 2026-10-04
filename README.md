# Company AI Framework

Shared AI-engineering framework for **Codex** and **Claude Code**.

The framework is intended to live at:

```text
%USERPROFILE%\.ai
```

or:

```text
~/.ai
```

It is the source of truth for company rules, reusable skills, provider/model-routing policy, prompt starters, project templates, repository-intelligence guidance, scripts, and hooks.

> **Installation status:** Windows and Linux bootstrap/lifecycle installers are implemented. Live platform validation is still required before treating them as production-ready.

## Quick help

- Full quick-reference: [`HELP.md`](HELP.md)
- Skill catalog: [`skills/SKILL-LIST.md`](skills/SKILL-LIST.md)
- Model/role routing: [`docs/model-routing.md`](docs/model-routing.md)
- Codex setup notes: [`docs/setup-codex.md`](docs/setup-codex.md)
- Claude setup notes: [`docs/setup-claude.md`](docs/setup-claude.md)
- Global agent rules: [`AGENTS.md`](AGENTS.md)
- Claude global bridge: [`CLAUDE.md`](CLAUDE.md)

## Core idea

Skills are shared between Codex and Claude and **do not hard-code model names**.

They request one of five roles:

| Role | Responsibility |
|---|---|
| `primary` | Planning, architecture, material decisions, integration, final ownership |
| `executor` | Bounded implementation, edits, builds/tests, routine coding work |
| `researcher` | External docs, library/API/vendor research |
| `advisor` | Independent plan/stuck/completion review |
| `fast` | Trivial low-risk routing/mechanical decisions |

Provider profiles map those roles to concrete models and effort levels. `medium` is the default/recommended profile:

```text
~/.ai/providers/codex.yml          # medium (default)
~/.ai/providers/codex.low.yml
~/.ai/providers/codex.high.yml
~/.ai/providers/claude.yml         # medium (default)
~/.ai/providers/claude.low.yml
~/.ai/providers/claude.high.yml
```

Use `low` when usage/quota pressure matters more than maximum reasoning depth, `medium` for normal work, and `high` for difficult work where quality justifies higher usage.

Repositories may override either provider under:

```text
<repo>/.ai/providers/codex.yml
<repo>/.ai/providers/claude.yml
<repo>/.ai/providers/codex.<profile>.yml     # optional profile-specific override
<repo>/.ai/providers/claude.<profile>.yml    # optional profile-specific override
```

The generic repo override applies to every profile; a profile-specific repo override applies last.

See [Provider-aware model routing](docs/model-routing.md) for merge order, fallbacks, behavioral settings, and runtime notes.

## Installation

The framework now includes a shared installer lifecycle with thin Windows/Linux bootstrap scripts:

```text
install.ps1
install.sh
installer/installer.py
```

Supported operations:

```text
Install
Update / Repair
Uninstall
Doctor / Status
```

Targets can be `codex`, `claude`, or `both`, and provider profiles can be `low`, `medium`, or `high`.

### Windows

From an existing checkout/install:

```powershell
& "$env:USERPROFILE\.ai\install.ps1" doctor
& "$env:USERPROFILE\.ai\install.ps1" install -Target codex -Profile low
& "$env:USERPROFILE\.ai\install.ps1" update-repair -Target both
& "$env:USERPROFILE\.ai\install.ps1" uninstall -Target claude
```

Bootstrap from a raw Git-hosted script once the framework repository URL is configured/published:

```powershell
$env:AI_FRAMEWORK_REPO_URL = "<framework-git-url>"
irm <raw-install.ps1-url> | iex
```

For a non-default target/profile in a pipe bootstrap, invoke the downloaded script block with parameters or install once and use the local `~/.ai/install.ps1` lifecycle command.

### Linux

From an existing checkout/install:

```bash
~/.ai/install.sh doctor
~/.ai/install.sh install --target codex --profile low
~/.ai/install.sh update-repair --target both
~/.ai/install.sh uninstall --target claude
```

Bootstrap from a raw Git-hosted script once the framework repository URL is configured/published:

```bash
export AI_FRAMEWORK_REPO_URL="<framework-git-url>"
curl -fsSL <raw-install.sh-url> | bash
```

The bootstrap scripts ensure Git, a compatible Python runtime (3.11+), and `uv`, locate/clone the framework, then hand off to the shared Python installer. Existing compatible Python is preserved; a fresh Windows install selects the highest stable Python 3.x package available through `winget`, while Linux uses the distribution package manager.

### What the installer owns

The installer:

- wires shared skills without replacing unrelated skills;
- persists low/medium/high profiles per provider;
- renders machine-local native routing under `~/.ai/generated/<provider>/`;
- merges only framework-owned Codex/Claude config keys/sections and preserves unrelated settings;
- installs/updates Graphify using the official `graphifyy` package through `uv`;
- installs AiIndex CLI/MCP from release assets when available and verifies SHA-256;
- registers AiIndex MCP for selected clients where supported;
- records installer-owned state under `~/.ai/local/installer-state.json`;
- never owns repo-local `.ai/providers/`, `.ai-index.json`, or `.ai-index/`.

`Update / Repair` is intentionally both upgrade and repair: it regenerates missing/stale installer-owned wiring without requiring a destructive reinstall.

### Bootstrap repository URL

The public pipe-install command needs the canonical framework repository URL. Until that URL is hard-coded for release, set `AI_FRAMEWORK_REPO_URL` or pass the repository URL to the local bootstrap script. See [`installer/common/README.md`](installer/common/README.md).

## Native agent integration

The framework under `.ai` is the source of truth. Agent-native directories should point back to it rather than maintain independent copies of company-owned skills.

### Codex

Expose company skills through Codex's native skill location using links/junctions where supported. Keep Codex-owned and third-party content under Codex's own management.

Global framework instructions are in:

```text
~/.ai/AGENTS.md
```

Provider routing profiles are in:

```text
~/.ai/providers/codex.yml          # medium/default
~/.ai/providers/codex.low.yml
~/.ai/providers/codex.high.yml
```

Repository overrides are read conceptually from:

```text
<repo>/.ai/providers/codex.yml
<repo>/.ai/providers/codex.<profile>.yml
```

The framework can now resolve effective Codex routing and render native Codex custom-agent/config fragments. The installer is still responsible for safely merging those fragments into `~/.codex` while preserving unrelated configuration. See [`docs/setup-codex.md`](docs/setup-codex.md).

### Claude Code

Expose company skills through Claude's native skill directory, normally:

```text
~/.claude/skills/
```

using links/junctions back to:

```text
~/.ai/skills/
```

Leave Claude-managed content such as `~/.claude/skills/synced/` untouched.

Claude's global instruction file should import the shared framework:

```text
~/.claude/CLAUDE.md
```

with an import pointing to:

```text
~/.ai/CLAUDE.md
```

Provider routing profiles are in:

```text
~/.ai/providers/claude.yml         # medium/default
~/.ai/providers/claude.low.yml
~/.ai/providers/claude.high.yml
```

Repository overrides are read from:

```text
<repo>/.ai/providers/claude.yml
<repo>/.ai/providers/claude.<profile>.yml
```

Claude Code supports native model-specific subagents. The framework renders `ai-executor`, `ai-researcher`, `ai-advisor`, and `ai-fast` definitions with model/effort/tool boundaries from the selected profile and effective provider config. Claude's native full-session advisor remains optional rather than the framework checkpoint default because it receives the full conversation; framework checkpoints use the compact-context `ai-advisor`. See [`docs/setup-claude.md`](docs/setup-claude.md).

## Provider detection and overrides

Preferred resolution:

1. Detect the active runtime/provider automatically where possible.
2. If `AI_PROVIDER` is explicitly set, use it as the provider override.
3. Select `low`, `medium`, or `high` from `--profile`, then `AI_PROFILE`, then the saved per-provider profile, otherwise default to `medium`.
4. Load the selected global provider profile (`<provider>.yml` for medium, `<provider>.low.yml` / `<provider>.high.yml` otherwise).
5. Deep-merge the generic repository override `<repo>/.ai/providers/<provider>.yml` if present.
6. Deep-merge `<repo>/.ai/providers/<provider>.<profile>.yml` if present.
7. Resolve the requested role.
8. Follow the configured fallback chain if the preferred model/role is unavailable. For native role agents this is an explicit retry contract (`ai-<role>` -> `ai-<role>-fallback-1` -> later fallbacks); do not silently execute the delegated work in `primary` after a model-startup/availability failure unless configuration explicitly routes there.

Example explicit override:

```powershell
$env:AI_PROVIDER = "codex"
```

or:

```bash
export AI_PROVIDER=claude
```

Profile override examples:

```powershell
$env:AI_PROFILE = "low"
```

```bash
export AI_PROFILE=high
```

Or use `--profile low|medium|high` for one command. `--profile` wins over `AI_PROFILE`. Persist the normal profile for a provider with:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --set-profile low
```

The saved selection lives under ignored machine-local state (`~/.ai/local/provider-profiles.json`). Re-render/re-sync native client wiring after changing the saved profile.

A repository override only needs the keys it changes. Example:

```yaml
roles:
  executor:
    model: <repo-preferred-model>
    effort: high

behavior:
  advisor:
    repeatedFailureThreshold: 3
```

Repository overrides may change **both** model routing and behavioral settings.

The helper implements and exposes the effective merge:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --effective
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --profile low --effective
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --profile high --validate
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --role executor
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --diagnose
```

Render client-native fragments from the same effective config:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --render-native "$env:USERPROFILE\.ai\generated\codex"
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider claude --render-native "$env:USERPROFILE\.ai\generated\claude"
```

Add `--profile low|medium|high` before rendering to switch the native client wiring. After a profile change, re-render/re-sync native client configuration; changing `AI_PROFILE` alone does not rewrite already-generated native agents.

Use `--repo <path>` when repository overrides should be included. The renderer does not edit native client configuration directly; safe merge/update/uninstall belongs to the installer.

## Usage profiles

| Profile | Intent | Typical behavior |
|---|---|---|
| `low` | Conserve usage/quota | Lower effort, cheaper capable models, max concurrency `2` |
| `medium` | Recommended default | Balanced primary/executor split, max concurrency `4` |
| `high` | Quality-first difficult work | Stronger/higher-effort execution and review, max concurrency `4` |

Profiles change model/effort/concurrency policy, not the skill workflow contract: substantial-only advisor checkpoints, bounded workers, fallback behavior, and plan-only parallelism remain in force.

Current defaults:

| Codex profile | primary | executor | researcher | advisor | fast | max agents |
|---|---|---|---|---|---|---:|
| `low` | GPT-5.6 Sol / medium | GPT-5.6 Sol / low | GPT-5.6 Sol / low | GPT-5.6 Sol / low | GPT-6 Luna / low | 2 |
| `medium` | GPT-6 Astra / high | GPT-5.6 Sol / medium | GPT-5.6 Sol / medium | GPT-5.6 Sol / medium | GPT-6 Luna / low | 4 |
| `high` | GPT-6 Astra / high | GPT-6 Sol / high | GPT-6 Sol / high | GPT-6 Sol / high | GPT-6 Luna / low | 4 |

| Claude profile | primary | executor | researcher | advisor | fast | max agents |
|---|---|---|---|---|---|---:|
| `low` | Sonnet / medium | Sonnet / low | Sonnet / low | Sonnet / low | Haiku / low | 2 |
| `medium` | Opus / high | Sonnet / medium | Sonnet / medium | Sonnet / medium | Haiku / low | 4 |
| `high` | Opus / high | Sonnet / high | Sonnet / high | Opus / high | Haiku / low | 4 |

These are recommendations, not guarantees of account availability. Runtime fallback and installer/Doctor checks should handle unavailable models without hard-coding assumptions about a user's plan or workspace.

## Important orchestration defaults

Current defaults in both provider policies:

```yaml
advisor:
  repeatedFailureThreshold: 2
  completionCheck: substantial-only
  planCheck: substantial-only

execution:
  workerScope: bounded
  parallelMode: plan-only
```

### Substantial work

Parent workflows explicitly classify work as:

```yaml
substantial: true
```

or:

```yaml
substantial: false
```

Do not use file count alone. Features, migrations, modernization, architecture work, and non-trivial debugging are substantial by default. Small/local edits usually are not.

`new-feature` records this in the spec and carries it through planning/execution.

### Bounded worker scope

An executor may touch directly related files needed to finish the assigned outcome, but it must report meaningful scope expansion. It must not silently absorb a material architecture, contract, storage, rollout, or shared-policy decision.

Standard orchestration outcomes:

```text
COMPLETE
BLOCKED
NEEDS_DECISION
NEEDS_RESEARCH
```

### Parallel execution

Parallel execution is **plan-controlled**. Do not fan out merely because tasks appear independent.

A plan must explicitly mark work `parallel-safe` / `parallel-eligible`, and parallel execution must then be selected before `parallel-exec` starts workers.

## Skills: how to invoke them

Skills can be selected automatically when their descriptions match the task. Explicit invocation is preferable when you want a specific workflow.

Portable wording works in both clients:

```text
Use the new-feature skill for <feature>.
Use the debug skill for this failure.
Use the advisor skill in complete mode before we call this done.
```

Claude Code also exposes installed skills as slash commands such as:

```text
/new-feature
/debug
/code-review
/advisor
```

Codex skill invocation syntax can vary by surface; explicit natural-language skill selection remains portable. Where the client exposes a skill picker/shortcut, select the same skill name listed below.

## Skill catalog

### `new-feature`

Top-level gated feature workflow:

```text
nf-spec
  -> spec approval
nf-design
  -> advisor:plan when substantial
  -> design approval
nf-tasks
  -> task-plan approval
execution
  -> optional approved parallel-exec
  -> advisor:stuck at configured repeated-failure threshold
  -> advisor:complete when substantial
```

Use when delivering a new feature with explicit spec/design/task approval gates.

Example:

```text
Use the new-feature skill for customer-import. Project folder is D:\Work\MyApp.
```

### `nf-spec`

Creates/revises the implementation-ready feature specification. Includes contracts, validation, phasing, `substantial: true|false`, and parallel-execution preference.

Example:

```text
Use nf-spec to create the spec for customer-import.
```

### `nf-design`

Turns an approved spec into an implementation design with file/component impact, architecture, risks, observability, rollout, and test planning.

Example:

```text
Use nf-design with the approved customer-import specs.md.
```

### `nf-tasks`

Turns an approved design into `dev-todos.md`, including dependency order, sequential/parallel safety, execution roles, worker slots, acceptance checks, and resumable status.

Example:

```text
Use nf-tasks with the approved customer-import design.md.
```

### `nf-avalonia`

Supporting guidance for Avalonia/cross-platform desktop features. Used by `new-feature` rather than replacing its approval chain.

### `advisor`

Reusable independent checkpoint reviewer. Can be invoked by other skills or manually.

Modes:

```text
plan
stuck
complete
```

Examples:

```text
Use advisor in plan mode on this migration plan.
Use advisor in stuck mode; the same failure has occurred twice.
Use advisor in complete mode before we mark this feature done.
```

### `decision`

Maintains an append-only implementation/architecture decision log under the current feature's `_localnotes` folder.

Example:

```text
Use decision to record why we chose association-based Qdrant payloads over duplicate points.
```

### `parallel-exec`

Executes only approved, dependency-ready, explicitly parallel-safe tasks. Does not decide by itself that work should become parallel.

Example:

```text
Use parallel-exec for approved batch P2 from dev-todos.md with a maximum of 3 workers.
```

### `debug`

Logs-first debugging. Reads runtime/build/test evidence before code changes, narrows hypotheses, uses the advisor after repeated failure threshold, and completion-checks substantial investigations.

Example:

```text
Use debug. Start with these production logs and find the root cause before editing code.
```

### `code-review`

Context-aware review across correctness, security, architecture, observability, and tests. Fixes validated findings by default unless review-only is requested.

Examples:

```text
Use code-review on the current diff.
Use code-review in review-only mode on this PR.
```

### `modernize-eval`

Assesses an existing system and recommends targeted refactor, migration, phased replacement, or rewrite.

Example:

```text
Use modernize-eval on this .NET application and write the report under _localnotes.
```

### `modernize-plan`

Builds an execution-ready modernization plan from an approved evaluation. Modernization planning is substantial by default and receives an advisor plan check.

Example:

```text
Use modernize-plan with the approved modernization evaluation.
```

### `session-close`

End-of-session wrap-up. Records status, blockers, restart notes, next steps, and material decisions so work can resume cleanly.

Example:

```text
Use session-close for the current feature before we stop today.
```

### Architecture / TAS skills

Use the TAS sequence for repository/platform architecture documentation:

```text
tas-01-project-architecture-analyzer
tas-02-architecture-project-grouper
tas-03-architecture-normalizer
tas-04-generator
```

See `skills/architecture_skills_readme.md` and each skill README for details.

## Framework helper commands

The lightweight Python helper can expose the framework help/catalog directly:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" help
python "$env:USERPROFILE\.ai\scripts\ai.py" skills
python "$env:USERPROFILE\.ai\scripts\ai.py" provider
```

It also forwards repository initialization:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" repo-init --type dotnet --non-interactive
```

A future installer may expose this helper as a shorter `ai` command; do not assume that shim exists until the installation work is completed.

## Project initialization commands

Run from inside the target repository.

Interactive:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1"
```

Project types:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet
& "$env:USERPROFILE\.ai\init-project.ps1" -Type go
& "$env:USERPROFILE\.ai\init-project.ps1" -Type nextjs
& "$env:USERPROFILE\.ai\init-project.ps1" -Type python
& "$env:USERPROFILE\.ai\init-project.ps1" -Type vb-migration
```

Non-interactive:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -NonInteractive
```

Preview without writing:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -DryRun
```

Optional Codex hook scaffold:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -WithCodexHooks
```

Optional Graphify Claude integration:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -WithGraphifyClaude
```

Both:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" `
    -Type dotnet `
    -WithCodexHooks `
    -WithGraphifyClaude
```

Existing initialized repositories can use explicit actions:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -Action update -NonInteractive
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -Action reinit -NonInteractive
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -Action dry-run -NonInteractive
```

`reinit` is safe for framework templates: it reapplies templates but skips existing files.

## Repository intelligence

The framework uses AiIndex and Graphify for different questions.

### AiIndex

Prefer AiIndex for semantic/fuzzy discovery:

- where a feature/guardrail/retry/validation is implemented;
- behavioral questions;
- finding relevant files when the exact symbol is unknown;
- lexical/vector/hybrid search.

For agent-driven work prefer AiIndex MCP tools:

```text
init_project
index_status
index_project
search_code
```

Do not use `dotnet run` against the AiIndex source tree as the normal runtime.

Use the installed `aiindex` CLI when the user explicitly asks for a CLI command, MCP is unavailable, or the required operation is CLI-only.

### Graphify

Prefer Graphify for structure:

- callers/callees;
- dependency paths;
- imports/references;
- inheritance/implementation;
- architecture relationships;
- blast-radius/impact analysis.

When `graphify-out/graph.json` exists, query it instead of rebuilding unless an update/rebuild is required.

### Mixed questions

1. Use AiIndex to discover likely symbols/files/concepts.
2. Use Graphify to trace or verify structural relationships.

Generated `graphify-out/` should be excluded from AiIndex indexing.

## Core folders

```text
providers/   Provider-specific role/model and orchestration defaults
rules/       Shared global engineering rules
skills/      Canonical reusable workflows
prompts/     Reusable prompt starters
templates/   Project scaffolding templates
scripts/     Deterministic helper scripts
hooks/       Agent hook helpers
docs/        Framework/operator documentation
local/       Ignored personal/local overrides
```

## Rule priority

When instructions conflict:

1. Current user instruction.
2. Project-specific repository instructions.
3. Project-specific skills/config overrides.
4. Global skills from this framework.
5. Global framework rules.
6. Tool/runtime defaults.

## Important engineering defaults

- Prefer small incremental changes over large rewrites.
- Do not rewrite unrelated code.
- Preserve behavior unless the task explicitly changes it.
- Add/update automated tests unless the user explicitly says not to.
- Add/update tester-facing markdown test cases under `.ai/test-cases/` unless explicitly waived.
- Use interfaces for business/application services unless project conventions say otherwise.
- Preserve project naming conventions.
- Add useful comments/documentation for public APIs, business rules, compatibility decisions, assumptions, timing boundaries, and non-obvious logic.
- Do not add comments that merely restate code.
- Be explicit about null handling, errors, boundaries, and risks.
- Report changed files, verification run, residual risks, and blocked/unverified items.

## Session close

Before switching projects or ending meaningful implementation work, use `session-close` when files changed, decisions were made, blockers appeared, or task status changed.

Do not run it for simple Q&A with no project changes.

## Remaining installation work

Provider resolution, fallback diagnostics, repo overrides, and native Codex/Claude fragment generation are implemented. The main remaining framework lifecycle work is the installer: prerequisite handling, client detection, safe merge/update/uninstall, drift/backups, AiIndex/Graphify wiring, and end-to-end validation on real Codex/Claude installations. Until that is complete, this README intentionally keeps installation as a placeholder rather than presenting unfinished installer commands as supported behavior. See `INSTALLER.md` and `docs/REMAINING-WORK.md`.


Doctor and uninstall are intentionally non-mutating with respect to system prerequisites: they require an existing compatible Python runtime and never install Git, Python, or uv.
