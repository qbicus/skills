# Output Contract

The normalizer writes files to:

`<architectureWorkspaceFolder>/03-normalizer/`

## Required files

- `normalized.json`
- `normalized.md`
- `decisions.md` append-only

## JSON schema

```json
{
  "canonical_entities": [
    {
      "canonical_name": "",
      "entity_type": "project|service|datastore|integration|platform",
      "aliases": [],
      "source_references": [],
      "merge_recommendation": "merge|keep_separate|manual_review",
      "rationale": [],
      "confidence": ""
    }
  ],
  "normalized_platforms": [],
  "normalized_dependencies": [],
  "manual_review_queue": [
    {
      "issue_type": "",
      "candidates": [],
      "reason": ""
    }
  ],
  "assumptions": [],
  "unknowns": []
}
```

## Markdown sections

`normalized.md` must contain:

1. Canonical Entities
2. Alias Mapping
3. Merge Decisions
4. Manual Review Queue
5. Unknowns
6. Assumptions

Put this metadata header at the top:

- `generated_at:`
- `source_skill: architecture-normalizer`
- `workspace_folder:`
