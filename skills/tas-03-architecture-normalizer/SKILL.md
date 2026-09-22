---
name: tas-03-architecture-normalizer
description: Normalize architecture entities after analysis and grouping. Use when Codex needs to read analyzer `output.json` files under `01-analyzer` plus `02-grouper/grouped.json`, detect aliases and duplicate names across projects, services, datastores, integrations, and platforms, then write deterministic normalization outputs and an append-only decisions log under `03-normalizer`.
---

# TAS 03 Architecture Normalizer

Run the bundled normalizer script against an architecture workspace after the analyzer and grouper have produced outputs. Prefer conservative canonicalization, preserve every original name as an alias, and send ambiguous matches to manual review instead of forcing merges.

## Input

- Require `architectureWorkspaceFolder`.

## Read Scope

Read:

- `<architectureWorkspaceFolder>/01-analyzer/**/output.json`
- `<architectureWorkspaceFolder>/02-grouper/grouped.json`

Ignore invalid analyzer outputs. Treat missing `grouped.json` as a valid degraded run and record it in `unknowns`.

## Output Location

Write all outputs to:

`<architectureWorkspaceFolder>/03-normalizer/`

The script must:

- Overwrite `normalized.json`
- Overwrite `normalized.md`
- Append to `decisions.md` without deleting prior entries

## Markdown Template

Use the template in [references/architecture-normalization-template.md](references/architecture-normalization-template.md) unless the user explicitly requests a different format.

When generating `normalized.md`:

- Render the markdown from the template file
- Populate the template using data from `normalized.json`
- Replace all template placeholders with actual values
- If a value is unavailable, render `No data available`
- Preserve the metadata header exactly as defined in the template
- Preserve the confidence note block
- Preserve the "Source" and "Review status" block
- Preserve the "Reviewer Checklist" section
- Leave checklist items unchecked unless the user explicitly asks to mark review progress
- Do not add, remove, or reorder top-level sections unless explicitly requested by the user
- Do not generate freeform markdown structure when the template is available

## Alias Mapping

Support a deterministic alias mapping file stored at:

`assets/alias_mappings.json`

Use it to:

- seed canonical names
- keep preferred spellings stable across runs
- avoid re-guessing known aliases

Do not delete original names from outputs even when aliases collapse into one canonical entity.

Alias-map entries must guide normalization but must not suppress conflicting evidence. If an alias-map entry conflicts with strong evidence from the current run, keep the issue in `manual_review_queue` and record it in `decisions.md`.

## Normalization Rules

- Detect duplicates
- Identify aliases
- Propose canonical names
- Flag uncertain matches
- Be conservative
- Prefer `manual_review` if unsure
- Never delete original names
- Preserve every original name as an alias or source reference
- Do not merge entities across different entity types unless explicit evidence supports it
- Keep output deterministic by sorting entities, aliases, and references

## Required Outputs

- `normalized.json`: strict schema documented in [references/output_contract.md](references/output_contract.md)
- `normalized.md`: readable report rendered from the template with all sections preserved
- `decisions.md`: append ambiguous matches, unresolved conflicts, reviewer overrides, and alias-map-driven merge decisions for each run

Each appended entry in `decisions.md` must include:

- timestamp
- workspace folder
- number of analyzer outputs processed
- whether grouped.json was present
- reviewer or runner (if known)

## Review Workflow

1. Run the normalizer script first.
2. Review `normalized.json` and `normalized.md`.
3. Check `manual_review_queue` before accepting merge recommendations.
4. If repeated ambiguities are legitimate aliases, add them to `assets/alias_mappings.json` and rerun.
5. If manual review changes normalization conclusions:
    - Update `normalized.json` first
    - Regenerate `normalized.md` from it
    - Append the rationale to `decisions.md`

## Interpretation Guidance

- Treat explicit alias-map entries as stronger than heuristic similarity.
- Treat case changes, punctuation changes, singular/plural drift, and known abbreviations as weak alias clues unless another signal supports them.
- Use grouped platforms and cross-project dependencies to support entity resolution, not to override weak evidence.
- Keep conflicting names separate when entity type is unclear.
