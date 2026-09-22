# Skill: repo-init

## Purpose

Initialize a new or existing repository for AI-agent work using the shared framework.

## Rules

- Create only missing files and folders.
- Do not overwrite existing `AGENTS.md`, `CLAUDE.md`, `.ai/`, `.codex/`, or project notes.
- If a file exists, leave it unchanged and report it as skipped.
- Project instructions override global instructions.
- Use templates from `%USERPROFILE%\.ai\templates` or `~/.ai/templates`.

## Default files to create

```text
AGENTS.md
CLAUDE.md
.ai/project-overview.md
.ai/architecture.md
.ai/current-work.md
.ai/decisions.md
.ai/pitfalls.md
.ai/commands.md
.ai/testing.md
.ai/deployment.md
.ai/skills/
.ai/prompts/
.ai/.session-state.json
```

## Optional modes

- `--dry-run`: show what would be created.
- `--type dotnet`: add .NET-specific templates.
- `--type vb-migration`: add VB.NET migration templates.
- `--with-codex-hooks`: add project-local Codex hooks if missing.
- `--force-generated`: overwrite only files that contain the generated template marker.

## Example command

```powershell
ai repo-init --type dotnet
```
