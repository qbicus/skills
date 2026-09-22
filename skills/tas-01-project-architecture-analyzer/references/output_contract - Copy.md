# Output Contract

The analyzer writes files to:

`<architectureWorkspaceFolder>/01-analyzer/<projectName>/`

Where `projectName` is derived from the repository folder name with spaces removed and only letters, numbers, dots, and underscores retained.

## Required files

- `output.json`
- `output.md`
- `decisions.md` append-only

## JSON schema

```json
{
  "project_name": "",
  "source_project_folder": "",
  "workspace_output_folder": "",
  "summary": "",
  "project_type": "",
  "primary_stack": [],
  "entry_points": [],
  "deployable_units": [],
  "components": [
    {
      "name": "",
      "kind": "",
      "description": "",
      "evidence": [],
      "confidence": ""
    }
  ],
  "datastores": [
    {
      "name": "",
      "type": "",
      "usage": "",
      "evidence": [],
      "confidence": ""
    }
  ],
  "interfaces": {
    "inbound": [],
    "outbound": []
  },
  "integrations": [
    {
      "name": "",
      "type": "internal|external|unknown",
      "interaction": "",
      "evidence": [],
      "confidence": ""
    }
  ],
  "security": {
    "authentication": [],
    "authorization": [],
    "secrets_handling": [],
    "confidence": ""
  },
  "deployment": {
    "hosting_clues": [],
    "ci_cd_clues": [],
    "runtime_clues": [],
    "confidence": ""
  },
  "observed_facts": [],
  "inferred_facts": [],
  "unknowns": [],
  "risks": [],
  "assumptions": [],
  "overall_confidence": ""
}
```

## Markdown sections

`output.md` must contain:

1. Overview
2. Architecture Summary
3. Components
4. Data Stores
5. Interfaces
6. Integrations
7. Security
8. Deployment
9. Observed Facts
10. Inferred Facts
11. Unknowns
12. Risks and Assumptions

Put this metadata header at the top:

- `generated_at:`
- `source_skill: tas-01-project-architecture-analyzer`
- `project_folder:`
- `workspace_folder:`
- `confidence_summary:`
