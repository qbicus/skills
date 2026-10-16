---
name: repo-init
description: "Initialize a new or existing repository for the shared AI framework. Inspect first, preserve existing project configuration, scaffold only missing framework files, set up AiIndex and Graphify repository intelligence as appropriate, maintain generated-data ignore rules, and verify the resulting setup. Use when a user asks to initialize/onboard an existing repo, set up AiIndex/Graphify, or prepare a repository for Codex/Claude framework workflows."
---

# Repo Init

Initialize a repository safely for framework-driven AI work. Treat existing code and project configuration as authoritative; add only what is needed.

`repo-init` prepares repository intelligence and framework scaffolding. It is **not** a general "understand the whole repository" workflow. Use `project-takeover` when the goal is to inherit and understand an existing project after setup.

## Role usage

Keep setup work bounded and avoid spending the primary model on mechanical inventory work.

- `primary`: owns the setup plan, approval gates, conflicts, and final verification.
- `fast`: may classify project/language/framework types and shallow top-level structure.
- `executor`: may perform bounded inventory, deterministic scaffolding, ignore-rule edits, approved index/build commands, and verification commands.
- `researcher`: use only if setup depends on external documentation/provider behavior.
- Never delegate a broad "read/understand the entire repository" task.

## Required behavior

1. **Inspect before changing anything.**
   - Identify the repository root and project type(s).
   - Check existing `AGENTS.md`, `CLAUDE.md`, `.ai/`, `.ai-index.json`, `.ai-index/`, `graphify-out/`, `.gitignore`, and any existing Graphify/AiIndex setup.
   - Check whether AiIndex MCP/CLI and Graphify are available from the installed global framework.
   - Keep this setup inspection shallow/targeted; do not recursively read source files merely to understand the project.
   - Do not assume a repository is uninitialized because one expected file is missing.

2. **Show the plan first.**
   - Briefly list files/configuration that would be created or modified.
   - Call out any potentially expensive operation, especially a full/rebuild AiIndex index or Graphify rebuild.
   - For an existing repository, wait for user approval before running a full/rebuild index or other broad analysis operation.
   - If the user or an invoking parent workflow has already explicitly approved that exact full/rebuild operation, do not ask for the same approval a second time after showing the plan unless inspection reveals a materially different/riskier operation.

3. **Preserve existing project configuration.**
   - Never overwrite unrelated `AGENTS.md`, `CLAUDE.md`, project notes, provider overrides, or source/config files.
   - Project instructions override global framework instructions.
   - Prefer additive edits to `.gitignore`; preserve existing patterns and comments.
   - If framework-generated files already exist, update/repair only when the change is clearly framework-owned and safe. Otherwise report the difference instead of replacing it.

4. **Scaffold missing framework project files.**
   Use the shared project templates as the baseline. Typical files include:

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
   .ai/test-cases/
   .ai/providers/
   .ai/skills/
   .ai/prompts/
   .ai/.session-state.json
   .ai-index.json
   ```

   Do not create repository provider overrides unless the repository actually needs behavior different from the selected global provider profile.

5. **Set up AiIndex.**
   - Ensure `.ai-index.json` exists and is appropriate for the repository languages/layout.
   - Preserve a valid existing config; do not replace it just to match the template.
   - Ensure `.ai-index/` is ignored by Git.
   - Ensure generated Graphify output such as `graphify-out/` is excluded from AiIndex scanning when relevant.
   - Prefer AiIndex MCP tools for agent-driven setup/search when available (`init_project`, `index_status`, `index_project`, `search_code`). Use the installed CLI when MCP is unavailable or the user explicitly requests CLI usage.
   - Do not silently run a full/rebuild index on a substantial existing repository. Explain it and obtain approval first unless that exact operation was already explicitly approved by the user/parent workflow.
   - Incremental/changed indexing may be used later as normal maintenance.

6. **Set up Graphify repository intelligence.**
   - Use the installed Graphify integration/skill rather than installing a second repository-local copy of Graphify.
   - Detect existing Graphify output before rebuilding it.
   - Keep generated Graphify output (normally `graphify-out/`) out of Git unless the repository explicitly chooses to version it.
   - Follow the installed Graphify skill/tool instructions for the actual project analysis/build command rather than inventing provider-specific commands.

7. **Maintain `.gitignore`.**
   Add missing generated/local entries conservatively. Typical entries are:

   ```gitignore
   # AI repository intelligence (generated/local)
   .ai-index/
   graphify-out/
   ```

   `.ai-index.json` is configuration and is normally intended to be committed. The repo-local `.ai/` folder also contains project knowledge/configuration and should not be blanket-ignored unless the project explicitly wants it local-only.

8. **Verify the result.**
   - Confirm the expected framework files exist or were intentionally preserved.
   - Check AiIndex status/configuration and, when approved, complete the initial index.
   - Confirm Graphify is available and existing/generated graph output is usable.
   - Check `git status` and report exactly what repo files changed.
   - Report skipped files, manual steps, or unavailable tools clearly.

## Parent-workflow handoff

When another skill such as `project-takeover` invokes `repo-init`, return a compact setup handoff and stop. Do not continue into broad project analysis.

The handoff should contain:

- repository type(s) detected;
- files/config created, modified, skipped, or preserved;
- AiIndex config/status and whether a full/initial index was run;
- Graphify availability/output status;
- `.gitignore` changes;
- warnings/manual actions.

This prevents a parent workflow from repeating the same setup inspection and keeps repository-understanding work out of `repo-init`.

## Deterministic scaffold helper

For scaffold-only setup, the shared helper can be used directly:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1"
```

or:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" repo-init --type dotnet --non-interactive
```

The helper creates missing template files without overwriting existing files. The full `repo-init` skill remains responsible for repository inspection, AiIndex/Graphify setup, ignore rules, approvals, and verification.

## Optional scaffold modes

- `--dry-run`: show what the deterministic helper would create.
- `--type dotnet`: add .NET-specific templates.
- `--type vb-migration`: add VB.NET migration templates.
- `--type go`, `--type nextjs`, `--type python`: add project-type templates.
- `--with-codex-hooks`: add project-local Codex hooks if missing.
- `--with-graphify-claude`: install/normalize the optional Claude Graphify project integration when needed.

## Output

Finish with a concise summary containing:

- repository type(s) detected;
- files created/modified/skipped;
- AiIndex status and whether an initial/full index was run;
- Graphify status/output;
- `.gitignore` changes;
- remaining manual actions or warnings.
