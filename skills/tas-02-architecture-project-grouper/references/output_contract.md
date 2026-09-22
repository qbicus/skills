# Output Contract

The grouper writes files to:

`<architectureWorkspaceFolder>/02-grouper/`

## Required files

- `grouped.json`
- `grouped.md`
- `decisions.md` append-only

## JSON schema

```json
{
  "platforms": [
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
      "components": [],
      "datastores": [],
      "interfaces": {
        "inbound": [],
        "outbound": []
      },
      "integrations": [],
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
      "cross_project_dependencies": [],
      "observed_facts": [],
      "inferred_facts": [],
      "unknowns": [],
      "risks": [],
      "assumptions": [],
      "grouping_rationale": [],
      "confidence": ""
    }
  ],
  "shared_services": [
    {
      "name": "",
      "used_by": [],
      "evidence": [],
      "confidence": ""
    }
  ],
  "cross_project_dependencies": [
    {
      "source_project": "",
      "target_project_or_service": "",
      "relationship": "",
      "evidence": [],
      "confidence": ""
    }
  ],
  "naming_collisions": [
    {
      "canonical_candidate": "",
      "variants": [],
      "notes": []
    }
  ],
  "orphans": [
    {
      "project_name": "",
      "summary": "",
      "reasons_not_grouped": [],
      "observed_signals": [],
      "unknowns": [],
      "confidence": ""
    }
  ],
  "unknowns": [],
  "assumptions": []
}
```

## Notes

- Analyzer outputs from `01-analyzer` are the source of truth.
- The grouper may infer normalized auth families or normalized internal dependency links when analyzer fields are too generic for direct grouping.
- Any such inference must be conservative and recorded in `decisions.md`.
- Aggregated platform fields in `grouped.json` are a grouping-level summary, not a replacement for analyzer outputs.

## Markdown sections

`grouped.md` must contain:

1. Overview
2. Platform Summaries
3. Grouping Rationale
4. Shared Services
5. Cross-Project Dependencies
6. Architecture Overview by Platform
7. Data Stores
8. Interfaces & Integrations
9. Security
10. Deployment
11. Orphans
12. Naming Collisions
13. Observed Facts
14. Inferred Facts
15. Unknowns
16. Risks and Assumptions

Put this metadata header at the top:

- `document_type: architecture-grouping`
- `generated_at:`
- `source_skill: tas-02-architecture-project-grouper`
- `workspace_folder:`
