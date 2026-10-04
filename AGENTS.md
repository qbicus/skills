# Global AI Agent Instructions

These are global instructions for AI coding agents working on company projects.

## Always apply

- Prefer small, incremental changes over large rewrites.
- Do not rewrite unrelated code.
- Preserve existing behavior unless the current task explicitly asks for behavior changes.
- Prefer dependency injection and clear service boundaries.
- Use interfaces for business/application services unless project rules say otherwise.
- Add useful documentation/comments to generated or modified code, especially public APIs, services, business rules, compatibility behavior, and non-obvious logic.
- Do not add comments that merely repeat the code.
- Add or update automated tests for new functionality, bug fixes, and behavior changes unless the user explicitly says not to add tests.
- For each new or changed functionality, create or update a tester-facing markdown test case file unless the user explicitly says not to.
- Preserve existing project naming conventions. For C#/.NET, use PascalCase for public members and camelCase for local variables and parameters.
- Be explicit about null handling, error handling, and edge cases.
- Explain changed files, risks, tests added/run, and tester-facing test case files created/updated.

## Rule priority

When rules conflict, use this priority:

1. Current user instruction.
2. Project-specific instructions in the repository.
3. Project-specific skills.
4. Global skills from this framework.
5. Global rules from this file and `rules/`.
6. Tool defaults.

## Shared framework location

The shared framework should be available at:

```text
%USERPROFILE%\.ai
```

or:

```text
~/.ai
```

Use:

- `rules/team-rules.md`
- `rules/coding-standards.md`
- `rules/security-rules.md`
- `skills/`
- `prompts/`

## Skill usage

Before doing specialized work, check whether a relevant skill exists.

Common mappings:

- New feature: `skills/new-feature`
- Feature spec: `skills/nf-spec`
- Feature design: `skills/nf-design`
- Feature tasks: `skills/nf-tasks`
- Decision logging: `skills/decision`
- End-of-session wrap-up: `skills/session-close`
- Debugging: `skills/debug`
- Code review: `skills/code-review`
- Modernization assessment: `skills/modernize-eval`
- Modernization planning: `skills/modernize-plan`
- Parallel execution: `skills/parallel-exec`
- Architecture/TAS workflows: `skills/tas-*`
- Independent checkpoint review: `skills/advisor`


## Provider-aware role routing

Shared skills are provider-agnostic. They request execution roles instead of concrete model names. Resolve roles through:

- `providers/codex.yml` / `providers/claude.yml` for the default `medium` profile;
- `providers/<provider>.low.yml` for lower-usage operation;
- `providers/<provider>.high.yml` for quality-first difficult work;
- optional repository overrides at `<repo>/.ai/providers/<provider>.yml` and `<repo>/.ai/providers/<provider>.<profile>.yml`.

Profile selection order is `--profile`, then `AI_PROFILE`, then the saved per-provider profile, then `medium`. Use `AI_PROVIDER=codex|claude` only as an explicit provider override when automatic runtime detection is unavailable or intentionally overridden. Generic repository provider values override the selected global profile; profile-specific repository values apply last.

Standard roles:

- `primary`: planning, architecture, material decisions, integration, and final ownership;
- `executor`: bounded implementation/edit/test work;
- `researcher`: external documentation/API/library research;
- `advisor`: independent plan/stuck/completion review;
- `fast`: trivial low-risk routing decisions.

Do not hard-code provider model names inside shared skills.

When native subagents are available, use the framework-generated role agents:

- `ai-executor` for `executor`;
- `ai-researcher` for `researcher`;
- `ai-advisor` for portable advisor fallback/review;
- `ai-fast` for `fast`.

`primary` is the owning/main thread. The native client default for that thread is generated from the provider `primary` mapping.

### Mandatory role fallback protocol

When a delegated native role agent fails because its configured model is unavailable, unsupported, inaccessible to the account, or otherwise cannot start, the parent **must** retry that same delegated task with the generated fallback agents in numeric order:

1. `ai-<role>`
2. `ai-<role>-fallback-1`
3. `ai-<role>-fallback-2` (and any later generated fallback)

Do not silently perform the delegated task in the `primary` thread after a role-model availability failure. The primary thread may take over only when the provider configuration explicitly resolves/falls back to `primary`, or when every configured native candidate has failed and the workflow reports that escalation/blocker explicitly. A model-availability failure is not a task failure and must not consume the task's normal retry/failure budget. Report when a fallback agent was used when it materially affects cost, quality, or reviewer independence.

The provider helper is the executable source of truth for merged config and native fragments:

```text
python ~/.ai/scripts/ai.py provider --effective
python ~/.ai/scripts/ai.py provider --profile low --effective
python ~/.ai/scripts/ai.py provider --role executor
python ~/.ai/scripts/ai.py provider --validate
```

### Execution boundaries

- Worker scope is `bounded`: executors may touch directly related files required for the assigned task, but must report meaningful expansion.
- Escalate architecture, contract, storage, rollout, or other material choices as `NEEDS_DECISION`.
- Use `NEEDS_RESEARCH` when external evidence is required before safe continuation.
- Use `BLOCKED` when continuation requires missing input/infrastructure; include the blocker, evidence collected, exact prerequisite/input needed, and useful progress already completed.
- Use `COMPLETE` only when the assigned scope and acceptance checks are satisfied.
- Parallel execution is `plan-only`: do not create parallel workers unless the approved plan explicitly marks the work parallel-safe/parallel-eligible and parallel execution has been selected.

### Advisor checkpoints

Use the reusable `advisor` skill for:

- `plan`: before a substantial plan is committed or presented for approval;
- `stuck`: when substantially the same failure reaches the provider-configured threshold (default `2`);
- `complete`: before substantial work is declared complete.

Parent workflows explicitly classify work as `substantial: true|false`; do not use file count as the sole classifier.

See `docs/model-routing.md` for resolution, fallbacks, overrides, and provider-specific notes.

## Session close rule

Before switching projects, closing a coding session, or ending meaningful implementation work, run the `session-close` skill.

Run it when:

- files changed;
- decisions were made;
- blockers were found;
- task status changed;
- the user says they are done, closing, wrapping up, or switching projects.

Do not run it for simple Q&A with no project changes.

## Repository intelligence

Use installed repository-intelligence tools instead of invoking their source projects directly.

### AiIndex

Use AiIndex when the task is primarily about:

- semantic or fuzzy code discovery;
- finding implementation details by concept or behavior;
- locating where a feature, rule, retry, validation, guardrail, or business behavior is implemented;
- hybrid lexical/vector search across the repository;
- discovering relevant files when the exact symbol is not known.

For agent-driven repository search and index operations, prefer the AiIndex MCP tools:

- `init_project`
- `index_status`
- `index_project`
- `search_code`

Rules:

- Do not run AiIndex via `dotnet run`.
- Do not invoke `AiIndex.Cli` or `AiIndex.Mcp` from the AiIndex source tree.
- Prefer MCP for repository intelligence during agent work.
- Use the installed `aiindex` CLI only when:
  - the user explicitly asks for a CLI command;
  - an operation is not available through MCP;
  - or MCP is unavailable.

The installed AiIndex runtime is expected under:

- Windows: `%USERPROFILE%\.ai\bin`
- Linux/macOS: `~/.ai/bin`

### Graphify

Use Graphify when the task is primarily about:

- callers and callees;
- dependency paths;
- imports and references;
- inheritance or implementation relationships;
- architectural relationships between components;
- impact analysis or blast radius;
- shortest paths between symbols or concepts;
- explaining how known parts of the codebase are structurally connected.

When `graphify-out/graph.json` exists, prefer querying the existing graph instead of rebuilding it.

Do not use Graphify merely for semantic discovery such as "where is the code that does X?" when AiIndex is the better fit.

### Mixed tasks

For questions that need both semantic discovery and structural analysis:

1. Use AiIndex first to discover likely symbols, files, or concepts.
2. Use Graphify to expand, verify, or trace the structural relationships between those results.

Prefer source code and extracted structural relationships over generated reports when verifying implementation details.