# Global Claude Instructions

Follow the shared AI framework used by other coding agents.

Read and follow:

- `AGENTS.md`
- `rules/team-rules.md`
- `rules/coding-standards.md`
- `rules/security-rules.md`

Use skills from:

- `skills/`

## Shared repository intelligence

Follow the repository-intelligence rules defined in `AGENTS.md`.

In particular:

- Use AiIndex for semantic or fuzzy code discovery, implementation details, behavioral logic, and questions such as "where is the code that does X?".
- Use Graphify for callers/callees, dependency paths, imports, inheritance or implementation relationships, architectural connections, and impact/blast-radius analysis.
- For mixed questions, use AiIndex first to discover likely files, symbols, or concepts, then use Graphify to verify or expand the structural relationships.

Prefer source code and extracted structural relationships over generated reports when verifying implementation details.

## Tool usage

Prefer native tool integrations when available.

For AiIndex:
- Prefer its MCP tools for agent-driven repository work.
- Do not run AiIndex via `dotnet run`.
- Do not invoke AiIndex from its source tree as the normal runtime.
- Use the installed CLI only when explicitly requested, when MCP is unavailable, or when the required operation is CLI-only.

For Graphify:
- When `graphify-out/graph.json` exists, query the existing graph instead of rebuilding it unless a rebuild/update is explicitly needed.
- Use `graphify query`, `graphify path`, or `graphify explain` according to the type of structural question.

## Session close

Before ending meaningful coding work or switching projects, run the `session-close` skill.

Run it when:
- files changed;
- decisions were made;
- blockers were found;
- task status changed;
- the user says they are done, closing, wrapping up, or switching projects.

Do not run it for simple Q&A with no project changes.

## Provider-aware execution

Use the shared role-routing policy in `providers/claude.yml` (medium/default), `providers/claude.low.yml`, `providers/claude.high.yml`, and `docs/model-routing.md`. Shared skills request `primary`, `executor`, `researcher`, `advisor`, or `fast`; they must not hard-code Claude model names. Select profiles through `--profile`, `AI_PROFILE`, or the saved per-provider selection (default `medium`). Apply generic repository overrides from `<repo>/.ai/providers/claude.yml` and optional profile-specific overrides from `<repo>/.ai/providers/claude.<profile>.yml`.

When installed, delegate provider roles to the generated Claude subagents `ai-executor`, `ai-researcher`, `ai-advisor`, and `ai-fast`. Keep `primary` in the owning conversation. The generated subagent frontmatter carries model, effort, and read/write tool boundaries; repository provider overrides require regenerating/re-syncing the native artifacts before they affect Claude's native agent files. If a preferred role model is unavailable, use the generated `ai-<role>-fallback-N` agent in order.

For substantial plan/stuck/completion checkpoints, use the reusable `advisor` skill. Prefer Claude Code's native advisor tool when it is enabled, compatible with the active model, and available; otherwise use an isolated advisor-role subagent/fallback. Follow the configured repeated-failure threshold rather than repeatedly retrying the same approach.

Parallel worker execution remains plan-controlled: use workers concurrently only where an approved plan explicitly marks parallel-safe work and parallel execution has been selected.
