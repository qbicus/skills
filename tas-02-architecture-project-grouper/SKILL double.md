---
name: tas-02-architecture-project-grouper
description: Group multiple analyzed projects into conservative platform groupings using existing analyzer outputs. Use when Codex needs to read analyzer `output.json` files under a workspace `01-analyzer` tree, identify shared services, shared datastores, naming collisions, cross-project dependencies, and orphan projects, then write grouped outputs and an append-only decisions log under `02-grouper`.
---

# Architecture Project Grouper

Run the bundled grouper script against an analyzer workspace, then review only the low-confidence groupings or unknowns. Favor explicit evidence from analyzer outputs and leave weak candidates as orphans instead of forcing platform membership.

This skill must run in two modes:

1. **Scripted pass** (Python-based)
2. **Model-only pass** (no Python scripts)

Both outputs must be compared and merged into a final result.

## Input

- Require `architectureWorkspaceFolder`.
  
- If `architectureWorkspaceFolder` is not provided:
- Ask the user explicitly for it.
- Do not proceed until it is provided.

## Read Scope

Scan recursively under:

`<architectureWorkspaceFolder>/01-analyzer/**/output.json`

Ignore invalid or unreadable files.

For dual-pass pipelines, prefer reading from the finalized analyzer outputs when present:

`<architectureWorkspaceFolder>/01-analyzer/**/final/output.json`

If `final/output.json` is not present for a project, fall back to that project’s top-level `output.json` if it exists.

## Output Location

Write outputs using this structure:

```text
<architectureWorkspaceFolder>/02-grouper/
  scripted/
    grouped.json
    grouped.md
  model-only/
    grouped.json
    grouped.md
  comparison.md
  final/
    grouped.json
    grouped.md
  decisions.md
```

The scripted pass must:

- Overwrite `scripted/grouped.json`
- Overwrite `scripted/grouped.md`
- Append to `decisions.md` without deleting prior entries

The model-only pass must:

- Overwrite `model-only/grouped.json`
- Overwrite `model-only/grouped.md`
- Append to `decisions.md` without deleting prior entries

The final pass must:

- Overwrite `final/grouped.json`
- Overwrite `final/grouped.md`
- Append to `decisions.md` without deleting prior entries

## Markdown template:

Use [references/project-grouping-template.md](references/project-grouping-template.md) unless the user explicitly requests a different format.

When generating `grouped.md`:
- Render the markdown from `references/project-grouping-template.md`
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

When generating `scripted/grouped.md`, `model-only/grouped.md`, or `final/grouped.md`:
- Apply the same template rules above.
- Populate the template using the corresponding JSON file for that folder.

## Shared Template Location

Load templates only from the shared `references` folder that sits alongside the skill folders in the distributed skills package.

Required template for this skill:

`references/project-grouping-template.md`

Do not create, copy, or modify template files inside this skill folder unless the user explicitly asks for that.

## Run The Grouper

### Scripted Pass

From the skill folder, run:

```bash
python3 scripts/group_projects.py \
  --workspace-folder "<architectureWorkspaceFolder>"
```
### Model-Only Pass

After the scripted pass, run a second pass without using Python scripts.
The model-only pass must:

- Inspect only the analyzer outputs within the workspace
- Use the same evidence sources as the scripted pass where relevant
- Produce equivalent outputs under:
  - model-only/grouped.json
  - model-only/grouped.md
- Follow the same JSON contract and markdown template rules as the scripted pass

### Comparison Step

After both passes complete, generate:

`comparison.md`

The comparison must:

- Compare `scripted/grouped.json` and `model-only/grouped.json`
- Highlight differences in:
  - proposed platforms
  - project membership
  - shared services
  - shared datastores
  - cross-project dependencies
  - orphans
  - naming collisions
  - confidence levels
- Identify which pass has stronger evidence for each disagreement
- Record unresolved conflicts explicitly

### Final Output

After comparison, create:

- `final/grouped.json`
- `final/grouped.md`

Rules for the final output:

- Prefer the result with stronger evidence
- If both results are plausible, merge conservatively
- If disagreement cannot be resolved confidently, keep the more conservative interpretation
- Prefer leaving a project in `orphans` rather than assigning it to a questionable platform
- Never invent relationships not supported by at least one pass
- If unresolved, keep the issue in `orphans`, `unknowns`, `assumptions`, or an equivalent conservative location
- `final/grouped.md` must be generated from `final/grouped.json`

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

- `scripted/grouped.json`: strict schema documented in `references/output_contract.md`
- `model-only/grouped.json`: strict schema documented in `references/output_contract.md`
- `final/grouped.json`: strict schema documented in `references/output_contract.md`
- `scripted/grouped.md`: readable report rendered from `references/project-grouping-template.md` with the required metadata header and all template sections preserved
- `model-only/grouped.md`: readable report rendered from `references/project-grouping-template.md` with the required metadata header and all template sections preserved
- `final/grouped.md`: readable report rendered from `references/project-grouping-template.md` with the required metadata header and all template sections preserved
- `comparison.md`: comparison between scripted and model-only grouping results
- `decisions.md`: append grouping assumptions, unresolved ambiguities, uncertain mappings, and any manual reviewer overrides for each run

Each appended entry in `decisions.md` must begin with:
- timestamp
- workspace folder
- number of projects processed
- reviewer or runner if known

## Review Workflow

1. Run the scripted pass first.
2. Run the model-only pass second.
3. Read:
   - `scripted/grouped.json`
   - `model-only/grouped.json`
   - `comparison.md`
4. If a platform looks questionable, confidence is low, or the two passes disagree:
   - Inspect only the evidence paths copied from analyzer outputs before editing anything
   - Do not expand analysis beyond those surfaced evidence paths unless strictly necessary
5. Produce and review:
   - `final/grouped.json`
   - `final/grouped.md`
6. If manual review changes grouping conclusions, update `final/grouped.json` first, then regenerate `final/grouped.md` from it, and append the rationale to `decisions.md`.

## Interpretation Guidance

- Treat shared internal service names, repeated auth systems, repeated datastores, and dependency links as stronger than naming similarity.
- Keep a project in `orphans` when the evidence is thin or contradictory.
- Record uncertain links in `decisions.md` instead of silently folding them into a platform.
- Report naming collisions separately from actual platform groupings.

## Downstream skills must consume:

`<architectureWorkspaceFolder>/02-grouper/final/grouped.json`