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