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