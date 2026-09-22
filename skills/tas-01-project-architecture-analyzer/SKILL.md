---
name: tas-01-project-architecture-analyzer
description: Analyze a single software repository and produce a structured Project Architecture Profile with strict JSON and Markdown outputs plus an append-only decisions log. Use when Codex needs to inspect code, configs, pipelines, Docker, IaC, and README files for one project and summarize frameworks, entry points, components, datastores, interfaces, integrations, security, and deployment clues into a reusable architecture report.
---

# Project Architecture Analyzer

Run the bundled analyzer script to create the baseline profile, then inspect only the gaps that still matter. Prefer evidence-backed facts, separate observations from inferences, and leave unknowns explicit instead of inventing details.

## Inputs

- Require `projectFolder`: source repository path.
- Require `architectureWorkspaceFolder`: root folder where outputs will be written.

If `architectureWorkspaceFolder` is not provided:
- Ask the user explicitly for it.
- Do not proceed until it is provided.

## Output Location

Write all outputs to:

`<architectureWorkspaceFolder>/01-analyzer/<sanitizedProjectName>/`

Derive `sanitizedProjectName` from the repository folder name. Remove spaces and keep only letters, numbers, dots, and underscores.

## Markdown template:

Use [references/project-architecture-template.md](references/project-architecture-template.md) unless the user explicitly requests a different format.

When generating `output.md`:
- Render the markdown from `tas-references/project-architecture-template.md`
- Populate the template using data from `output.json`
- Replace all template placeholders with actual values
- If a value is unavailable, render `No data available`
- Preserve the metadata header exactly as defined in the template
- Preserve the confidence note block
- Preserve the "Source" and "Review status" block
- Preserve the "Reviewer Checklist" section
- Leave checklist items unchecked unless the user explicitly asks to mark review progress
- Do not add, remove, or reorder top-level sections unless explicitly requested by the user
- Do not generate freeform markdown structure when the template is available

## Shared Template Location

Load templates only from the shared `references` folder that sits alongside the skill folders in the distributed skills package.

Required template for this skill:

`tas-references/project-architecture-template.md`

Do not create, copy, or modify template files inside this skill folder unless the user explicitly asks for that.

## Execution

A bundled script may be available to assist with generation.

If used, it should be treated as a helper for deterministic file generation and structure.

The skill may:
- use the script
- partially use the script
- or perform the generation directly

Final outputs must always be based on normalized data and follow the template rules defined above.

The script must:

- Create folders if missing.
- Overwrite `output.json`.
- Overwrite `output.md`.
- Append to `decisions.md` without deleting prior entries.

## Script Usage Policy

Bundled Python scripts or other automation tools may be used to assist with extraction, parsing, or file generation.

However:

- Script output must not be treated as inherently correct
- All conclusions must be evidence-based
- Model reasoning may override script output when the script is incomplete, misleading, or lacks sufficient context
- Scripts should be used primarily for deterministic extraction, not architectural interpretation

Final outputs must reflect validated evidence, not raw script results.

## Review Workflow

1. Run the script first.
2. Read `output.json` and `output.md`.
3. If confidence is low or key areas remain unknown, inspect only the most relevant files the script already surfaced in evidence.
4. If manual review changes conclusions, update `output.json` and `output.md` but keep `decisions.md` append-only.

## Analysis Rules

- Inspect code, configs, CI/CD, Docker, IaC, and READMEs.
- Detect frameworks, APIs, background jobs, databases, and external APIs.
- Classify information as:
  - `observed`: direct file-backed evidence.
  - `inferred`: reasonable conclusion from multiple clues.
  - `unknown`: not enough evidence.
- Use only `high`, `medium`, or `low` confidence.
- Include file-path evidence whenever possible.
- Do not invent integrations, databases, or security controls without evidence.

## Required Outputs

- `output.json`: strict schema documented in `references/output_contract.md`
- `output.md`: readable report rendered from `references/project-architecture-template.md` with the required metadata header and all template sections preserved
- `decisions.md`: append assumptions made during analysis, unresolved ambiguities, uncertain mappings, and any manual reviewer overrides for each run

Each appended entry in `decisions.md` must begin with:
- timestamp
- project name
- source project folder
- reviewer or runner if known

## Interpretation Guidance

- Treat package references, config keys, Docker base images, CI workflow names, infrastructure manifests, and endpoint definitions as strong evidence.
- Treat naming alone as weak evidence unless supported by code or config.
- Prefer conservative summaries for polyglot or monorepo-style repositories.
- If multiple deployable units exist, record each one separately.
- If a likely concern cannot be confirmed, place it in `unknowns` or `risks`, not `observed_facts`.
