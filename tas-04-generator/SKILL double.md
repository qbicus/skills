---
name: tas-04-generator
description: Generate Technical Architecture Specification markdown documents from normalized architecture data. Use when Codex needs to read `03-normalizer/normalized.json`, produce a master TAS plus one TAS file per platform and optional project TAS files, create missing TAS templates, and write append-only generation decisions under `04-tas`.
---

# TAS 04 Generator

Run the bundled generator script after normalization has completed. Generate markdown only from normalized architecture data, mark observed versus inferred content explicitly, include confidence notes, and do not invent business context.

This skill must run in two modes:

1. **Scripted pass** (Python-based generation)
2. **Model-only pass** (no Python scripts)

Both outputs must be compared and merged into a final result.

## Input

- Require `architectureWorkspaceFolder`.
 
If `architectureWorkspaceFolder` is not provided:
- Ask the user explicitly for it.
- Do not proceed until it is provided.

## Read Scope

Read:

`<architectureWorkspaceFolder>/03-normalizer/normalized.json`

For dual-pass pipelines, prefer:

`<architectureWorkspaceFolder>/03-normalizer/final/normalized.json`

If the file is missing or invalid, fail fast with a clear error.

## Output Location

Write all outputs to:

`<architectureWorkspaceFolder>/04-tas/`

## Output Structure

```text
<architectureWorkspaceFolder>/04-tas/
  scripted/
    master-tas.md
    platform-<name>.md
    project-<name>.md
  model-only/
    master-tas.md
    platform-<name>.md
    project-<name>.md
  comparison.md
  final/
    master-tas.md
    platform-<name>.md
    project-<name>.md
  decisions.md
```

The scripted pass must:

- Overwrite all files under `scripted/`
- Append to `decisions.md` without deleting prior entries

The model-only must:

- Overwrite all files under `model-only/`
- Append to `decisions.md` without deleting prior entries

The final pass must:

- Overwrite all files under `final/`
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

When generating files under `scripted/`, `model-only/`, or `final/`:

- Apply the same template rules above
- Populate using the same normalized input data for that pass

## Run The Generator

### Scripted Pass

From the skill folder, run:

```bash
python3 scripts/generate_tas.py \
  --workspace-folder "<architectureWorkspaceFolder>"
```

### Model-Only Pass

After the scripted pass, run a second pass without using Python scripts.

The model-only pass must:

- Read only normalized architecture data
- Produce equivalent TAS outputs under:
  - `model-only/master-tas.md`
  - `model-only/platform-<name>.md`
  - `model-only/project-<name>.md` when generated
- Follow the same template rules as the scripted pass

### Comparison Step

After both passes complete, generate:

`comparison.md`

The comparison must:

- Compare scripted and model-only TAS outputs
- Highlight differences in:
  - included platforms
  - included projects
  - section completeness
  - observed vs inferred labeling
  - confidence notes
  - missing or extra content
- Identify which pass is more faithful to normalized data for each disagreement
- Record unresolved conflicts explicitly

### Final Output

After comparison, create final TAS documents under:

- `final/master-tas.md`
- `final/platform-<name>.md`
- `final/project-<name>.md` when generated

Rules for the final output:

- Prefer the result that is more faithful to normalized data
- If both results are plausible, merge conservatively
- Never invent content not supported by normalized data
- Never introduce entities that do not exist in the normalized input
- Do not reinterpret, merge, or transform normalized entities during TAS generation
- TAS generation remains a presentation step, not a transformation step

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

- `scripted/master-tas.md`
- `scripted/platform-<name>.md`
- `scripted/project-<name>.md` optional
- `model-only/master-tas.md`
- `model-only/platform-<name>.md`
- `model-only/project-<name>.md` optional
- `final/master-tas.md`
- `final/platform-<name>.md`
- `final/project-<name>.md` optional
- `comparison.md`
- `decisions.md` append-only

Each appended entry in `decisions.md` must include:

- timestamp
- workspace folder
- number of platforms generated
- number of projects processed
- whether project-level TAS files were generated
- reviewer or runner (if known)

## Review Workflow

1. Run the scripted pass first.
2. Run the model-only pass second.
3. Review:
   - `scripted/master-tas.md`
   - `model-only/master-tas.md`
   - `comparison.md` 
4. Review platform documents for platform-specific scope and dependency accuracy.
5. If differences exist or confidence is low:
   - Check fidelity back to normalized input data
   - Do not broaden interpretation beyond what is present in normalized data unless strictly necessary
6. Review final outputs:
   - `final/master-tas.md`
   - `final/platform-<name>.md`
   - `final/project-<name>.md` when present
7. If manual review identifies issues:
   - Update the source normalized data if required
   - Regenerate TAS documents from `normalized.json`
   - Append rationale to `decisions.md`

## Interpretation Guidance

- Treat canonical entities and normalized dependencies as the primary source of truth.
- Treat `manual_review_queue` and `unknowns` as unresolved architecture ambiguity.
- When normalized data is sparse, keep sections short and explicit about missing context instead of filling gaps with guesses.

## Downstream publication or sharing should use only:

`<architectureWorkspaceFolder>/04-tas/final/`