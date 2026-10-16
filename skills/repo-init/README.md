# Skill: `repo-init`

Initialize a new or existing repository for the shared Codex/Claude AI framework without overwriting unrelated project configuration.

Use this once when onboarding an existing codebase, and again later when the framework project scaffold needs repair/update.

## Recommended prompt

```text
Use repo-init to initialize this existing repository for our AI framework.
Set up Graphify, AiIndex, repo-local configuration and gitignore entries as appropriate.
Preserve all existing config and code.
Inspect first, show me the planned changes, then proceed.
```

## What it covers

- inspect the repository before changing it;
- preserve existing `AGENTS.md`, `CLAUDE.md`, `.ai/` project knowledge, provider overrides, source files, and Git history;
- create only missing framework project scaffold files;
- create or preserve `.ai-index.json` and set up AiIndex repository intelligence;
- detect/use Graphify and avoid unnecessary graph rebuilds;
- add missing generated-data ignore entries such as `.ai-index/` and `graphify-out/`;
- keep `.ai-index.json` and useful repo-local `.ai/` project knowledge commit-friendly by default;
- ask before broad/expensive full or rebuild indexing on an existing repository;
- verify the resulting AiIndex/Graphify setup and report exactly what changed.

## Scaffold-only helper

From inside the target repository on Windows:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1"
```

or through the framework helper:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" repo-init --type dotnet --non-interactive
```

The deterministic helper only scaffolds missing framework files. The `repo-init` skill adds the repository inspection, AiIndex/Graphify setup, ignore rules, approvals, and verification around it.
