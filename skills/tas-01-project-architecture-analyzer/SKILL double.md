---
name: tas-01-project-architecture-analyzer
description: Analyze a single software repository and produce a structured Project Architecture Profile with strict JSON and Markdown outputs plus an append-only decisions log. Use when Codex needs to inspect code, configs, pipelines, Docker, IaC, and README files for one project and summarize frameworks, entry points, components, datastores, interfaces, integrations, security, and deployment clues into a reusable architecture report.
---

# Project Architecture Analyzer

Run the bundled analyzer script to create the baseline profile, then inspect only the gaps that still matter. Prefer evidence-backed facts, separate observations from inferences, and leave unknowns explicit instead of inventing details.

This skill must run in two modes:

1. Scripted pass (Python-based)
2. Model-only pass (no Python scripts)

Both outputs must be compared and merged into a final result.

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

## Output Structure

<architectureWorkspaceFolder>/01-analyzer/<sanitizedProjectName>/
  scripted/
    output.json
    output.md
  model-only/
    output.json
    output.md
  comparison.md
  final/
    output.json
    output.md
  decisions.md

## Markdown template:

Use `references/project-architecture-template.md` unless the user explicitly requests a different format.

When generating `output.md`:
- Render the markdown from `references/project-architecture-template.md`
- Populate the template using data from output.json
- Replace all template placeholders with actual values
- If a value is unavailable, render No data available
- Preserve the metadata header exactly as defined in the template
- Preserve the confidence note block
- Preserve the "Source" and "Review status" block
- Preserve the "Reviewer Checklist" section
- Leave checklist items unchecked unless the user explicitly asks to mark review progress
- Do not add, remove, or reorder top-level sections unless explicitly requested by the user
- Do not generate freeform markdown structure when the template is available

## Shared Template Location

Load templates only from the shared references folder.

Required template:
`references/project-architecture-template.md`

Do not create or modify template files.

## Run The Analyzer

### Scripted Pass

python3 scripts/analyze_project.py \
  --project-folder "<projectFolder>" \
  --workspace-folder "<architectureWorkspaceFolder>" \
  --output-subfolder "scripted"

### Model-Only Pass

- Do not use Python scripts
- Analyze repository directly
- Write outputs to model-only/

## Comparison Step

Generate comparison.md:
- Compare scripted vs model-only results
- Highlight differences
- Identify stronger evidence
- Record unresolved conflicts

## Final Output

Create:
final/output.json
final/output.md

Rules:
- Prefer stronger evidence
- Merge conservatively
- Never invent data
- Keep unresolved items as unknown

## Review Workflow

1. Run the scripted pass first.
2. Run the model-only pass second.
3. Read:
  - `scripted/output.json`
  - `model-only/output.json`
  - `comparison.md`

4. If confidence is low, key areas remain unknown, or the two passes disagree:
  - Inspect only the most relevant files already surfaced as evidence in the outputs
  - Do not expand analysis beyond those files unless strictly necessary

5. Produce and review:
  - `final/output.json`
  - `final/output.md`

6. If manual review changes conclusions:
  - Update `final/output.json` first
  - Regenerate `final/output.md` from it
  - Append the rationale to `decisions.md` (append-only)

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

- scripted/output.json
- model-only/output.json
- final/output.json
- comparison.md
- decisions.md

Downstream skills must use:
final/output.json

## Decisions Log

Append:
- timestamp
- project name
- differences
- reasoning

## Interpretation Guidance

- Treat package references, config keys, Docker base images, CI workflow names, infrastructure manifests, and endpoint definitions as strong evidence.
- Treat naming alone as weak evidence unless supported by code or config.
- Prefer conservative summaries for polyglot or monorepo-style repositories.
- If multiple deployable units exist, record each one separately.
- If a likely concern cannot be confirmed, place it in `unknowns` or `risks`, not `observed_facts`.
