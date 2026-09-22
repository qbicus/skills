# Company AI Framework

This folder is intended to be cloned or copied to:

```text
%USERPROFILE%\.ai
```

or:

```text
~/.ai
```

It is the canonical shared location for company AI-agent rules, reusable skills, prompt templates, project templates, scripts, hooks, and repository-intelligence guidance.

## First-time setup

Clone/copy this framework to your user profile:

```powershell
cd $env:USERPROFILE
git clone <framework-repo-url> .ai
```

### Prerequisites

The project initializer requires Python available as `python` or `py`.

Some optional integrations have additional prerequisites:

- Codex project hooks require Codex.
- Graphify Claude integration requires `graphify` to be installed and available on `PATH`.
- `scripts/install-graphify-claude.ps1` requires PowerShell (`pwsh` preferred, Windows PowerShell supported).

## Native agent integration

The framework under `.ai` is the source of truth. Agent-native directories should point back to it rather than maintain independent copies of company-owned skills.

### Codex

Company skills should be exposed through Codex's native skill directory:

```text
~/.codex/skills/
```

using directory junctions/symlinks that point to:

```text
~/.ai/skills/
```

Leave Codex-owned and third-party skills such as `.system`, `.idea`, and `graphify` under Codex's own management.

Global repository-intelligence routing and company-wide agent rules are defined in:

```text
~/.ai/AGENTS.md
```

### Claude Code

Company skills should be exposed through Claude's native skill directory:

```text
~/.claude/skills/
```

using directory junctions/symlinks that point to:

```text
~/.ai/skills/
```

Leave Claude-managed content such as `~/.claude/skills/synced/` untouched.

Claude's native global instruction file should import the shared framework:

```text
~/.claude/CLAUDE.md
```

with:

```text
@<user-home>/.ai/CLAUDE.md
```

The shared `.ai/CLAUDE.md` in turn follows the common framework and repository-intelligence routing defined in `.ai/AGENTS.md`.

## Initialize a project

Run this from inside the target repository. If you omit `-Type`, the initializer asks interactive questions. It also detects whether the repository already has AI framework files and offers update/repair, safe re-init, preview, or cancel options:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1"
```

Non-interactive project type variants:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet
& "$env:USERPROFILE\.ai\init-project.ps1" -Type go
& "$env:USERPROFILE\.ai\init-project.ps1" -Type nextjs
& "$env:USERPROFILE\.ai\init-project.ps1" -Type python
& "$env:USERPROFILE\.ai\init-project.ps1" -Type vb-migration
```

For automation/CI or scripted setup, pass `-NonInteractive`:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -NonInteractive
```

Preview without writing files:

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

This runs Graphify's Claude installer for the target repository and then normalizes the generated `## graphify` section in project `CLAUDE.md` so it follows the shared AiIndex/Graphify routing policy.

Both optional integrations can be enabled together:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" `
    -Type dotnet `
    -WithCodexHooks `
    -WithGraphifyClaude
```

The initializer creates missing project AI files only. It does not overwrite existing `AGENTS.md`, `CLAUDE.md`, or `.ai` template files. If the project is already initialized, interactive mode shows the detected files and lets you choose update/repair, safe re-init, dry-run preview, or cancel.

Graphify's own installer may update its managed project integration files; the framework wrapper then normalizes only the generated Graphify routing section.

Non-interactive actions:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -Action update -NonInteractive
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -Action reinit -NonInteractive
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -Action dry-run -NonInteractive
```

`reinit` is safe for framework templates: it reapplies templates but still skips existing files.

## Repository intelligence

The shared framework uses complementary repository-intelligence tools.

### AiIndex

Use AiIndex primarily for:

- semantic or fuzzy code discovery;
- implementation and behavioral questions;
- finding where a feature, rule, retry, validation, guardrail, or business behavior is implemented;
- hybrid lexical/vector search when the exact symbol is not known.

For agent-driven work, prefer the AiIndex MCP tools. Do not use `dotnet run` against the AiIndex source tree as the normal runtime.

### Graphify

Use Graphify primarily for:

- callers and callees;
- dependency paths;
- imports and references;
- inheritance and implementation relationships;
- architecture relationships;
- impact/blast-radius analysis;
- paths between known symbols or concepts.

When `graphify-out/graph.json` exists, query the existing graph rather than rebuilding it unless an update/rebuild is required.

### Mixed questions

For questions that require both discovery and structure:

1. Use AiIndex to discover likely files, symbols, or concepts.
2. Use Graphify to trace, expand, or verify their structural relationships.

Generated Graphify output under `graphify-out/` should be excluded from AiIndex indexing.

## Core folders

```text
rules/       Shared global engineering rules
skills/      Canonical reusable workflows
prompts/     Reusable prompt starters
templates/   Project scaffolding templates
scripts/     Deterministic helper scripts
hooks/       Codex/agent hook helpers
local/       Ignored personal/local overrides
```

## Important defaults

- Add/update automated tests unless the user explicitly says not to.
- Add/update tester-facing markdown test cases under `.ai/test-cases/`.
- Use interfaces for business/application services unless project rules say otherwise.
- Preserve project naming conventions; for C#/.NET, use camelCase for locals/parameters and PascalCase for public members.
- Add useful documentation/comments to generated or modified code, especially for public APIs, business rules, compatibility behavior, assumptions, and non-obvious logic.
- Do not add comments that merely restate the code.