---
name: tas-03-architecture-normalizer
description: Normalize architecture entities after analysis and grouping. Use when Codex needs to read analyzer `output.json` files under `01-analyzer` plus `02-grouper/grouped.json`, detect aliases and duplicate names across projects, services, datastores, integrations, and platforms, then write deterministic normalization outputs and an append-only decisions log under `03-normalizer`.
---

# TAS 03 Architecture Normalizer

Run the bundled normalizer script against an architecture workspace after the analyzer and grouper have produced outputs. Prefer conservative canonicalization, preserve every original name as an alias, and send ambiguous matches to manual review instead of forcing merges.

This skill must run in two modes:

1. **Scripted pass** (Python-based)
2. **Model-only pass** (no Python scripts)

Both outputs must be compared and merged into a final result.

## Input

- Require `architectureWorkspaceFolder`.

If `architectureWorkspaceFolder` is not provided:
- Ask the user explicitly for it.
- Do not proceed until it is provided.

## Read Scope

Read:

- `<architectureWorkspaceFolder>/01-analyzer/**/output.json`
- `<architectureWorkspaceFolder>/02-grouper/grouped.json`

For dual-pass pipelines, prefer:

- `<architectureWorkspaceFolder>/01-analyzer/**/final/output.json`
- `<architectureWorkspaceFolder>/02-grouper/final/grouped.json`

Ignore invalid analyzer outputs. Treat missing `grouped.json` as a valid degraded run and record it in `unknowns`.

## Output Location

Write all outputs to:

`<architectureWorkspaceFolder>/03-normalizer/`

---

## Output Structure

```text
<architectureWorkspaceFolder>/03-normalizer/
  scripted/
    normalized.json
    normalized.md
  model-only/
    normalized.json
    normalized.md
  comparison.md
  final/
    normalized.json
    normalized.md
  decisions.md
```

The scripted pass must:

- Overwrite `scripted/normalized.json`
- Overwrite `scripted/normalized.md`
- Append to `decisions.md` without deleting prior entries

The model-only pass must:

- Overwrite `model-only/normalized.json`
- Overwrite `model-only/normalized.md`
- Append to `decisions.md` without deleting prior entries

The final pass must:

- Overwrite `final/normalized.json`
- Overwrite `final/normalized.md`
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

When generating `scripted/normalized.md`, `model-only/normalized.md`, or `final/normalized.md`:

- Apply the same template rules above
- Populate from the corresponding JSON file

## Alias Mapping

Support a deterministic alias mapping file stored at:

`assets/alias_mappings.json`

Use it to:

- seed canonical names
- keep preferred spellings stable across runs
- avoid re-guessing known aliases

Do not delete original names from outputs even when aliases collapse into one canonical entity.

Alias-map entries must guide normalization but must not suppress conflicting evidence. If an alias-map entry conflicts with strong evidence from the current run, keep the issue in `manual_review_queue` and record it in `decisions.md`.

## Run The Normalizer

### Scripted Pass

From the skill folder, run:

```bash
python3 scripts/normalize_architecture.py \
  --workspace-folder "<architectureWorkspaceFolder>" \
  --alias-map "assets/alias_mappings.json"
```

### Model-Only Pass

After the scripted pass, run a second pass without using Python scripts.

The model-only pass must:

- Use analyzer + grouping outputs only
- Apply the same normalization logic conceptually
- Produce:
  - model-only/normalized.json
  - model-only/normalized.md
- Follow the same schema and template rules

### Comparison Step

After both passes complete, generate:

`comparison.md`

The comparison must:

- Compare `scripted/normalized.json` and `model-only/normalized.json`
- Highlight differences in:
  - canonical names
  - alias mappings
  - entity merges
  - entity splits
  - manual review queue
  - unknowns
- Identify stronger evidence
- Record unresolved conflicts explicitly

### Final Output

After comparison, create:

- `final/normalized.json`
- `final/normalized.md`

Rules for the final output:

- Prefer stronger evidence
- Merge conservatively
- Never force alias merges without evidence
- If uncertain, move to `manual_review_queue`
- Never delete original names
- Preserve alias relationships
- `final/normalized.md` must be generated from `final/normalized.json`

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

- `scripted/normalized.json`: strict schema documented in [references/output_contract.md](references/output_contract.md)
- `model-only/normalized.json`: strict schema documented in [references/output_contract.md](references/output_contract.md)
- `final/normalized.json`: strict schema documented in [references/output_contract.md](references/output_contract.md)
- `scripted/normalized.md`: readable report rendered from the template with all sections preserved
- `model-only/normalized.md`: readable report rendered from the template with all sections preserved
- `final/normalized.md`: readable report rendered from the template with all sections preserved
- `decisions.md`: append ambiguous matches, unresolved conflicts, reviewer overrides, and alias-map-driven merge decisions for each run
- `comparison.md`

Each appended entry in `decisions.md` must include:

- timestamp
- workspace folder
- number of analyzer outputs processed
- whether grouped.json was present
- reviewer or runner (if known)

## Review Workflow

1. Run the scripted pass first.
2. Run the model-only pass second.
3. Review 
   - `scripted/normalized.json`
   - `model-only/normalized.json`
   - `comparison.md`
4. Check `manual_review_queue` before accepting merge recommendations.
5. If ambiguity remains or passes disagree:
   - Inspect only evidence already surfaced from analyzer and grouping outputs
   - Do not expand analysis scope unless necessary
6. Produce and review:
   - final/normalized.json
   - final/normalized.md
7. If repeated ambiguities are legitimate aliases, add them to `assets/alias_mappings.json` and rerun.
8. If manual review changes normalization conclusions:
   - Update final/normalized.json first
   - Regenerate final/normalized.md
   - Append rationale to decisions.md

## Interpretation Guidance

- Treat explicit alias-map entries as stronger than heuristic similarity.
- Treat case changes, punctuation changes, singular/plural drift, and known abbreviations as weak alias clues unless another signal supports them.
- Use grouped platforms and cross-project dependencies to support entity resolution, not to override weak evidence.
- Keep conflicting names separate when entity type is unclear.

## Downstream skills must consume:

`<architectureWorkspaceFolder>/03-normalizer/final/normalized.json`