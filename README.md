# Team AI Framework

Shared AI-engineering framework for **Codex** and **Claude Code**.

The framework is intended to live at:

```text
%USERPROFILE%\.ai
```

or:

```text
~/.ai
```

It is the source of truth for team rules, reusable skills, provider/model-routing policy, prompt starters, project templates, repository-intelligence guidance, scripts, and hooks.

> **Installation status:** Windows x64 is live-validated for Codex and Claude Code. Linux x64 is live-validated for Codex, including fresh bootstrap, install, Doctor, Update / Repair, profile changes, update checks, preview, uninstall, and reinstall. Linux Claude and Linux ARM64 validation are still pending.

## Quick help

- Full quick-reference: [`HELP.md`](HELP.md)
- Skill catalog: [`skills/SKILL-LIST.md`](skills/SKILL-LIST.md)
- Model/role routing: [`docs/model-routing.md`](docs/model-routing.md)
- Codex setup notes: [`docs/setup-codex.md`](docs/setup-codex.md)
- Claude setup notes: [`docs/setup-claude.md`](docs/setup-claude.md)
- Global agent rules: [`AGENTS.md`](AGENTS.md)
- Claude global bridge: [`CLAUDE.md`](CLAUDE.md)

## Windows colleague quick start

Most team members can use this two-step flow.

1. Install or repair the global framework:

```powershell
irm https://raw.githubusercontent.com/qbicus/skills/main/install.ps1 | iex
```

Choose **Install**, select **Codex**, **Claude**, or **Both**, then choose a usage profile. `medium` is the recommended default.

2. Open an existing code repository in Codex/Claude and run:

```text
Use repo-init to initialize this existing repository for our AI framework.
Set up Graphify, AiIndex, repo-local configuration and gitignore entries as appropriate.
Preserve all existing config and code.
Inspect first, show me the planned changes, then proceed.
```

`repo-init` preserves existing project configuration, asks before broad full/rebuild indexing, and reports exactly what it changed.

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

Provider profiles map delegated roles to concrete models and effort levels. The active **primary** model remains the model selected for the current Codex/Claude session; choosing a framework profile does not override that host/session model. `medium` is the default/recommended delegated-role profile:

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
Change profiles
Check for updates
Uninstall
Doctor / Status
Preview changes (interactive Windows/Linux UI)
```

Targets can be `codex`, `claude`, or `both`, and provider profiles can be `low`, `medium`, or `high`.

### Windows

For a fresh install, the shortest path is:

```powershell
irm https://raw.githubusercontent.com/qbicus/skills/main/install.ps1 | iex
```

If you prefer to inspect the bootstrap before running it:

```powershell
irm https://raw.githubusercontent.com/qbicus/skills/main/install.ps1 -OutFile install.ps1
.\install.ps1
```

The bootstrap ensures the framework is available under `%USERPROFILE%\.ai` and then opens the installer. For an existing install, run the maintenance console directly:

```powershell
& "$env:USERPROFILE\.ai\install.ps1"
```

The interactive menu provides Install, Update / Repair, Change profiles, Check for updates, Uninstall, Doctor, and Preview changes. Arrow keys navigate, Space toggles multi-select items, Enter continues, and Esc goes back where supported.

Non-interactive commands remain available:

```powershell
& "$env:USERPROFILE\.ai\install.ps1" doctor
& "$env:USERPROFILE\.ai\install.ps1" install -Target codex -Profile low -Yes
& "$env:USERPROFILE\.ai\install.ps1" update-repair -Target both -Yes
& "$env:USERPROFILE\.ai\install.ps1" change-profile -Target codex -Profile medium -Yes
& "$env:USERPROFILE\.ai\install.ps1" check-updates
& "$env:USERPROFILE\.ai\install.ps1" uninstall -Target claude -Yes
```

### Linux

> Linux x64 Codex lifecycle support has been live-validated. Linux Claude and Linux ARM64 validation are still pending.

From an existing checkout/install:

```bash
~/.ai/install.sh doctor
~/.ai/install.sh install --target codex --profile low
~/.ai/install.sh update-repair --target both
~/.ai/install.sh uninstall --target claude
```

Bootstrap from the public framework repository:

```bash
curl -fsSL https://raw.githubusercontent.com/qbicus/skills/main/install.sh | bash
```

The bootstrap scripts ensure Git, a compatible Python runtime (3.11+), and `uv`, locate/clone the framework, then hand off to the shared Python installer. Existing compatible Python is preserved; a fresh Windows install selects the highest stable Python 3.x package available through `winget`, while Linux uses the distribution package manager.

### What the installer owns

The installer:

- installs/adopts canonical shared skill links (`debug`, `new-feature`, `advisor`, etc.) without prefixes or replacement of unrelated skills;
- persists low/medium/high profiles per provider;
- renders machine-local native routing under `~/.ai/generated/<provider>/`;
- merges only framework-owned Codex/Claude config keys/sections and preserves unrelated settings;
- installs Graphify through the official `graphifyy` package when missing and preserves an existing Graphify tool/integration;
- installs/repairs/updates AiIndex CLI/MCP from GitHub release assets, verifies SHA-256, and skips re-download when the current runtime is healthy;
- registers AiIndex MCP for selected clients where supported;
- records installer-owned state under `~/.ai/local/installer-state.json`;
- never owns repo-local `.ai/providers/`, `.ai-index.json`, or `.ai-index/`.

`Update / Repair` preserves each client's active profile unless a profile change is explicitly requested. It repairs missing/stale installer-owned wiring and can include available Framework/AiIndex updates after confirmation in the interactive UI.

The canonical repository is `https://github.com/qbicus/skills.git`.

## Native agent integration

The framework under `.ai` is the source of truth. Agent-native directories should point back to it rather than maintain independent copies of team-owned skills.

### Codex

Expose team skills through Codex's native skill location using links/junctions where supported. Keep Codex-owned and third-party content under Codex's own management.

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

The framework resolves effective Codex routing and renders native Codex custom-agent/config fragments. The installer safely merges the framework-owned wiring into `~/.codex` while preserving unrelated configuration. See [`docs/setup-codex.md`](docs/setup-codex.md).

### Claude Code

Expose team skills through Claude's native skill directory, normally:

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

Add `--profile low|medium|high` before rendering when using the helper manually. Normal users should use the installer's **Change profiles** action, which persists the selection and regenerates/re-syncs the provider wiring. Setting `AI_PROFILE` only changes helper resolution for that process; it does not rewrite already-generated native agents.

Use `--repo <path>` when repository overrides should be included. The renderer does not edit native client configuration directly; safe merge/update/uninstall belongs to the installer.

## Usage profiles

| Profile | Intent | Typical delegated-role behavior |
|---|---|---|
| `low` | Conserve usage/quota | Lower-effort workers, max concurrency `2` |
| `medium` | Recommended default | Balanced workers/review, max concurrency `4` |
| `high` | Quality-first difficult work | Stronger/higher-effort workers and review, max concurrency `4` |

The **primary model is host/session controlled**. For example, if Codex is currently running GPT-6.1 Sol and the framework profile is `low`, the primary thread stays GPT-6.1 Sol while the delegated executor/researcher/advisor/fast roles use the `low` profile. Profiles do not silently change the model selected in the Codex or Claude UI/session.

Profiles change delegated model/effort/concurrency policy, not the skill workflow contract: substantial-only advisor checkpoints, bounded workers, fallback behavior, and plan-only parallelism remain in force.

Current delegated-role defaults:

| Codex profile | executor | researcher | advisor | fast | max agents |
|---|---|---|---|---|---:|
| `low` | GPT-5.6 Sol / low | GPT-5.6 Sol / low | GPT-5.6 Sol / low | GPT-6 Luna / low | 2 |
| `medium` | GPT-5.6 Sol / medium | GPT-5.6 Sol / medium | GPT-5.6 Sol / medium | GPT-6 Luna / low | 4 |
| `high` | GPT-6 Sol / high | GPT-6 Sol / high | GPT-6 Sol / high | GPT-6 Luna / low | 4 |

| Claude profile | executor | researcher | advisor | fast | max agents |
|---|---|---|---|---|---:|
| `low` | Sonnet / low | Sonnet / low | Sonnet / low | Haiku / low | 2 |
| `medium` | Sonnet / medium | Sonnet / medium | Sonnet / medium | Haiku / low | 4 |
| `high` | Sonnet / high | Sonnet / high | Opus / high | Haiku / low | 4 |

Provider YAMLs may still contain a `primary` role entry for framework routing metadata/fallback resolution, but it is not an instruction for the installer to replace the active main-session model. Model availability also varies by account/workspace, so runtime fallback and Doctor checks must not assume every configured model is available.

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

### `repo-init`

Initialize a new or existing repository for this framework without overwriting unrelated project configuration. It inspects the repository first, proposes the intended changes, scaffolds missing project AI files, configures repository intelligence (AiIndex and Graphify) as appropriate, updates generated-data ignore rules, and verifies the resulting setup.

Typical prompt:

```text
Use repo-init to initialize this existing repository for our AI framework.
Set up Graphify, AiIndex, repo-local configuration and gitignore entries as appropriate.
Preserve all existing config and code.
Inspect first, show me the planned changes, then proceed.
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

The helper can always be invoked through Python. Do not assume a separate global `ai` shim exists unless your environment explicitly provides one.

## Initialize an existing repository

After the framework is installed globally, open the repository in Codex or Claude and ask the agent to use `repo-init`. This is the recommended first-run workflow for an existing codebase because the skill can inspect the repository before changing anything.

Recommended prompt:

```text
Use repo-init to initialize this existing repository for our AI framework.
Set up Graphify, AiIndex, repo-local configuration and gitignore entries as appropriate.
Preserve all existing config and code.
Inspect first, show me the planned changes, then proceed.
```

The workflow should:

- preserve existing source files, Git history, `AGENTS.md`, `CLAUDE.md`, and unrelated configuration;
- create only missing framework project scaffolding;
- ensure `.ai-index.json` exists when AiIndex is enabled;
- keep generated AiIndex data (`.ai-index/`) and Graphify output (`graphify-out/`) out of Git and out of each other's indexes where appropriate;
- initialize or refresh repository intelligence only after showing the planned changes;
- treat a full/rebuild index as an explicit potentially expensive operation and obtain approval before running it;
- verify AiIndex/Graphify availability and report anything that remains manual.

For deterministic scaffolding without an agent, use the commands in the next section.

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

## Validation status and remaining work

Windows x64 has completed the live installer lifecycle pass for Codex and Claude Code. Linux x64 Codex has also completed fresh bootstrap, install, Doctor, Update / Repair, profile changes, update checks, preview behavior, uninstall, and reinstall. Windows remains the primary supported colleague path.

Still to complete before calling the whole cross-platform installer production-ready:

- live Linux x64 Claude validation where available;
- Linux ARM64 validation where hardware/CI is available;
- final Linux troubleshooting/documentation checks;
- optional future macOS validation if/when that platform is actively supported by the team.

See [`docs/REMAINING-WORK.md`](docs/REMAINING-WORK.md) for engineering validation notes.
