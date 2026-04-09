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
      "description": "",
      "projects": [],
      "shared_services": [],
      "shared_datastores": [],
      "key_integrations": [],
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
  "orphans": [],
  "unknowns": [],
  "assumptions": []
}
```

## Markdown sections

`grouped.md` must contain:

1. Platforms
2. Shared Services
3. Dependencies
4. Orphans
5. Naming Collisions
6. Unknowns
7. Assumptions

Put this metadata header at the top:

- `generated_at:`
- `source_skill: tas-02-architecture-project-grouper`
- `workspace_folder:`
