---
name: tas-04-generator
description: Generate Technical Architecture Specification markdown documents from normalized architecture data. Use when Codex needs to read `03-normalizer/normalized.json`, produce a master TAS plus one TAS file per platform and optional project TAS files, create missing TAS templates, and write append-only generation decisions under `04-tas`.
---

# TAS 04 Generator

Run the bundled generator script after normalization has completed. Generate markdown only from normalized architecture data, mark observed versus inferred content explicitly, include confidence notes, and do not invent business context.

## Input

- Require `architectureWorkspaceFolder`.

## Read Scope

Read:

`<architectureWorkspaceFolder>/03-normalizer/normalized.json`

If the file is missing or invalid, fail fast with a clear error.

## Output Location

Write all outputs to:

`<architectureWorkspaceFolder>/04-tas/`

The script must:

- Overwrite `master-tas.md`
- Overwrite `platform-<name>.md`
- Overwrite `project-<name>.md` when generated
- Append to `decisions.md` without deleting prior entries

## Markdown Templates

Use the templates in the local `references/tas/` folder unless the user explicitly requests a different format:

- [references/tas/project-template.md](references/tas/project-template.md)
- [references/tas/platform-template.md](references/tas/platform-template.md)
- [references/tas/master-template.md](references/tas/master-template.md)

When generating TAS markdown:

- Project TAS documents must render from the project template
- Platform TAS documents must render from the platform template
- Master TAS documents must render from the master template
- Populate all templates using data from `normalized.json`
- Replace all template placeholders with actual values
- If a value is unavailable, render `No data available`
- Preserve the metadata header exactly as defined in the template
- Preserve the confidence note block
- Preserve the "Source" and "Review status" block
- Preserve the "Reviewer Checklist" section
- Leave checklist items unchecked unless the user explicitly asks to mark review progress
- Do not add, remove, or reorder top-level sections unless explicitly requested by the user
- Do not generate freeform markdown structure when templates are available

## Generation Rules

- Generate one master TAS document.
- Generate one file per platform.
- Generate project TAS files only when a project has platform membership or dependency data worth documenting separately.
- Clearly mark:
    - `Observed`
    - `Inferred`
- Include confidence notes in each document.
- Do not invent business context or product intent.
- Keep output deterministic by sorting platforms, projects, and sections consistently.
- Do not introduce entities that do not exist in `normalized.json`
- Do not merge or reinterpret normalized entities during TAS generation
- TAS generation is a presentation step, not a transformation step

## Required Outputs

- `master-tas.md`
- `platform-<name>.md`
- `project-<name>.md` optional
- `decisions.md` append-only

Each appended entry in `decisions.md` must include:

- timestamp
- workspace folder
- number of platforms generated
- number of projects processed
- whether project-level TAS files were generated
- reviewer or runner (if known)

## Review Workflow

1. Run the generator script first.
2. Review `master-tas.md` for overall coherence.
3. Review platform documents for platform-specific scope and dependency accuracy.
4. If manual review identifies issues:
- Update the source normalized data if required
- Regenerate TAS documents from `normalized.json`
- Append rationale to `decisions.md`

## Interpretation Guidance

- Treat canonical entities and normalized dependencies as the primary source of truth.
- Treat `manual_review_queue` and `unknowns` as unresolved architecture ambiguity.
- When normalized data is sparse, keep sections short and explicit about missing context instead of filling gaps with guesses.
