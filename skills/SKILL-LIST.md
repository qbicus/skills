# Skill List

- `nf-spec` (used by `new-feature`)
- `nf-design` (used by `new-feature`)
- `nf-tasks` (used by `new-feature`)
- `nf-avalonia` (used by `new-feature`)
- `decision` (standalone, used by `new-feature`, `session-close`)
- `modernize-eval` (standalone)
- `modernize-plan` (standalone, used after `modernize-eval`)
- `parallel-exec` (standalone, used by `new-feature`, `modernize-plan`)
- `new-feature` (standalone)
- `session-close` (standalone)
- `code-review` (standalone)
- `debug` (standalone)
- `tas-01-project-architecture-analyzer` (standalone)
- `tas-02-architecture-project-grouper` (standalone)
- `tas-03-architecture-normalizer` (standalone)
- `tas-04-generator` (standalone)

## Short Explanations

### `new-feature`
Top-level gated workflow for building a feature from start to finish.
Chain: `nf-spec` -> approval -> `nf-design` -> approval -> `nf-tasks` -> approval -> execution.
Also uses `decision` for important decisions and `nf-avalonia` when the feature includes Avalonia or cross-platform desktop UI.

### `nf-spec`
Specification stage for `new-feature`.
Creates the implementation-ready feature spec, including requirements, contracts, validation rules, phasing, and parallel-execution preference.

### `nf-design`
Design stage for `new-feature`.
Turns the approved spec into a file-by-file implementation design with architecture, risks, observability, rollout, and test planning.

### `nf-tasks`
Task-planning stage for `new-feature`.
Breaks the approved design into ordered tasks, marks sequential vs parallel-safe work, assigns agent slots when needed, applies the quality checklist, and keeps `dev-todos.md` usable as a live execution tracker.

### `nf-avalonia`
Support skill for Avalonia desktop UI work inside `new-feature`.
Adds Avalonia-specific guidance for spec, design, task planning, and execution without replacing the main approval chain.

### `decision`
Standalone running decision log.
Records what was decided, why it was chosen, which alternatives were considered, and what was rejected so context survives across sessions.

### `modernize-eval`
Standalone modernization assessment workflow.
Evaluates an existing system and recommends targeted refactor, migration, phased replacement, or rewrite using a management-ready report plus three summary scores.

### `modernize-plan`
Standalone modernization planning workflow.
Takes an approved `modernize-eval` result and turns it into an execution-ready plan with current and target state, breaking changes, rollback, verification, and ordered modernization tasks.

The modernization READMEs include example prompts for the full flow: evaluation, approval, plan creation, and sequential or parallel execution.

### `parallel-exec`
Standalone parallel execution orchestrator.
Runs approved parallel-safe tasks from `dev-todos.md` or `modernize-plan.md` using worker assignments, live status tracking, and merge checkpoints.

All skill folders also include a `README.md` with short usage guidance and example prompts for teammates.

### `session-close`
Standalone end-of-session wrap-up.
Uses `decision` when needed, writes a short session summary, and records blockers, restart notes, next steps, and task status across one or more active features.

### `code-review`
Standalone review workflow.
Reviews code across correctness, security, architecture, observability, and tests, validates findings in context, fixes validated issues by default, and re-reviews until clean.

### `debug`
Standalone logs-first debugging workflow.
Reads production or build logs first, identifies the real failure pattern, narrows the root cause, and only then proposes or applies fixes.

### `tas-01-project-architecture-analyzer`
Standalone repository architecture profiling workflow.
Scans one repository, writes a structured architecture profile under an external workspace folder, separates observed facts from inferred facts and unknowns, and keeps an append-only decisions log for assumptions and guessed integrations.

### `tas-02-architecture-project-grouper`
Standalone architecture workspace grouping workflow.
Reads multiple analyzer outputs from `01-analyzer`, groups related projects into platforms only when evidence is strong enough, identifies shared services and cross-project dependencies, and writes grouped outputs plus an append-only decisions log under `02-grouper`.

### `tas-03-architecture-normalizer`
Standalone architecture normalization workflow.
Reads analyzer and grouper outputs, resolves canonical names for projects, services, datastores, integrations, and platforms, preserves original aliases, flags uncertain matches for manual review, and writes deterministic normalized outputs plus an append-only decisions log under `03-normalizer`.

### `tas-04-generator`
Standalone Technical Architecture Specification generation workflow.
Reads normalized architecture data, creates missing TAS templates when needed, writes a master TAS plus one TAS file per platform and optional project TAS files, and records assumptions or missing context under `04-tas`.
