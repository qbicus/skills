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
  "normalized_platforms": [
    {
      "name": "",
      "summary": "",
      "business_context": "",
      "platform_type": "",
      "description": "",
      "projects": [],
      "primary_stack": [],
      "entry_surfaces": [],
      "deployable_units": [],
      "components": [
        {
          "name": "",
          "kind": ""
        }
      ],
      "datastores": [
        {
          "name": "",
          "type": ""
        }
      ],
      "interfaces": {
        "inbound": [],
        "outbound": []
      },
      "integrations": [
        {
          "name": "",
          "type": ""
        }
      ],
      "security": {
        "auth_systems": [],
        "secrets_handling": [],
        "confidence": ""
      },
      "deployment": {
        "hosting_clues": [],
        "ci_cd_clues": [],
        "runtime_clues": [],
        "confidence": ""
      },
      "shared_services": [],
      "shared_datastores": [],
      "key_integrations": [],
      "cross_project_dependencies": [
        {
          "source_project": "",
          "target_project_or_service": "",
          "relationship": "",
          "evidence": [],
          "confidence": ""
        }
      ],
      "observed_facts": [],
      "inferred_facts": [],
      "unknowns": [],
      "risks": [],
      "assumptions": [],
      "grouping_rationale": [],
      "notes": [],
      "confidence": ""
    }
  ],
  "normalized_dependencies": [
    {
      "source_project": "",
      "target_project_or_service": "",
      "relationship": "",
      "evidence": [],
      "confidence": ""
    }
  ],
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

- `document_type: architecture-normalization`
- `generated_at:`
- `source_skill: tas-03-architecture-normalizer`
- `workspace_folder:`

## Notes

- `normalized_platforms` should preserve the richer platform architecture data from `02-grouper/grouped.json` while canonicalizing entity names where justified.
- Platform-level summaries, facts, unknowns, assumptions, and risks are carried through from `tas-02`; the normalizer should not discard them.
- `decisions.md` entries must include workspace folder, analyzer output count, grouped output presence, and runner or reviewer when known.
