## graphify

This project has a knowledge graph at `graphify-out/` with god nodes, community structure, and cross-file relationships.

Follow the repository-intelligence routing rules from the shared global framework.

Rules:

- Use Graphify when the question is primarily structural, including:
  - callers and callees;
  - dependency paths;
  - imports and references;
  - inheritance or implementation relationships;
  - architectural relationships;
  - impact or blast-radius analysis;
  - paths between known symbols or concepts.
- For semantic or behavioral discovery such as "where is the code that does X?", use AiIndex first when it is available.
- For mixed questions, use AiIndex to discover relevant files, symbols, or concepts first, then use Graphify to trace or verify their structural relationships.
- When Graphify is appropriate and `graphify-out/graph.json` exists, query the existing graph instead of rebuilding it.
- Use `graphify query "<question>"` for broader structural traversal.
- Use `graphify path "<A>" "<B>"` for relationships between known concepts or symbols.
- Use `graphify explain "<concept>"` for focused structural explanations.
- If `graphify-out/wiki/index.md` exists, use it for broad graph navigation rather than reading the raw graph.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review or when query/path/explain do not provide enough context.
- After modifying code, run `graphify update .` to keep the graph current.