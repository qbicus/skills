---
name: tas-02-architecture-project-grouper
description: Group multiple analyzed projects into conservative platform groupings using existing analyzer outputs. Use when Codex needs to read analyzer `output.json` files under a workspace `01-analyzer` tree, identify shared services, shared datastores, naming collisions, cross-project dependencies, and orphan projects, then write grouped outputs and an append-only decisions log under `02-grouper`.
---

# Architecture Project Grouper

Run the bundled grouper script against an analyzer workspace, then review only the low-confidence groupings or unknowns. Favor explicit evidence from analyzer outputs and leave weak candidates as orphans instead of forcing platform membership.

## Input

- Require `architectureWorkspaceFolder`.

## Read Scope

Scan recursively under:

`<architectureWorkspaceFolder>/01-analyzer/**/output.json`

Ignore invalid or unreadable files.

## Output Location

Write all outputs to:

`<architectureWorkspaceFolder>/02-grouper/`

The script must:

- Overwrite `grouped.json`
- Overwrite `grouped.md`
- Append to `decisions.md` without deleting prior entries

## Markdown template:

Use [references/project-grouping-template.md](references/project-grouping-template.md) unless the user explicitly requests a different format.

When generating `grouped.md`:
- Render the markdown from `tas-references/project-grouping-template.md`
- Populate the template using data from `grouped.json`
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

`tas-references/project-grouping-template.md`

Do not create, copy, or modify template files inside this skill folder unless the user explicitly asks for that.

## Run The Grouper

From the skill folder, run:

```bash
python3 scripts/group_projects.py \
  --workspace-folder "<architectureWorkspaceFolder>"
```

## Grouping Rules

- Use only analyzer outputs as input.
- Group conservatively.
- Do not force grouping.
- Allow orphan projects.
- Prefer links supported by:
  - shared integrations
  - shared datastores
  - naming similarity
  - cross-project dependencies
  - shared authentication systems
- Treat weak naming similarity alone as insufficient for grouping unless another clue supports it.
- Prefer leaving a project ungrouped rather than incorrectly grouped.
- A project must have at least one strong signal (shared datastore, integration, or dependency) to be grouped into a platform.

## Required Outputs

- `grouped.json`: strict schema documented in `references/output_contract.md`
- `grouped.md`: readable report rendered from `references/project-grouping-template.md` with the required metadata header and all template sections preserved
- `decisions.md`: append grouping assumptions, unresolved ambiguities, uncertain mappings, and any manual reviewer overrides for each run

Each appended entry in `decisions.md` must begin with:
- timestamp
- workspace folder
- number of projects processed
- reviewer or runner if known

## Review Workflow

1. Run the grouper script first.
2. Review `grouped.json` and `grouped.md`.
3. If a platform looks questionable, inspect the evidence paths copied from analyzer outputs before editing anything.
4. If manual review changes grouping conclusions, update `grouped.json` first, then regenerate `grouped.md` from it, and append the rationale to `decisions.md`.

## Interpretation Guidance

- Treat shared internal service names, repeated auth systems, repeated datastores, and dependency links as stronger than naming similarity.
- Keep a project in `orphans` when the evidence is thin or contradictory.
- Record uncertain links in `decisions.md` instead of silently folding them into a platform.
- Report naming collisions separately from actual platform groupings.
