# Output Contract

The analyzer writes files to:

`<architectureWorkspaceFolder>/01-analyzer/<projectName>/`

Where `projectName` is derived from the repository folder name with spaces removed and only letters, numbers, dots, and underscores retained.

## Required files

- `output.json`
- `output.md`
- `decisions.md` (append-only)

## JSON schema

```json
{
  "project_name": "",
  "source_project_folder": "",
  "workspace_output_folder": "",

  "summary": "",
  "business_context": "",
  "project_type": "",

  "architecture": {
    "style": "",
    "high_level_description": "",
    "design_principles": []
  },

  "constraints": [],
  "assumptions": [],

  "primary_stack": [],
  "entry_points": [],
  "deployable_units": [],

  "components": [
    {
      "name": "",
      "kind": "",
      "description": "",
      "dependencies": [],
      "interfaces_exposed": [],
      "evidence": [],
      "confidence": ""
    }
  ],

  "datastores": [
    {
      "name": "",
      "type": "",
      "usage": "",
      "data_classification": "",
      "encryption": {
        "at_rest": "",
        "in_transit": ""
      },
      "evidence": [],
      "confidence": ""
    }
  ],

  "interfaces": {
    "inbound": [],
    "outbound": [],
    "protocols": [],
    "authentication_methods": []
  },

  "api_catalog": [],

  "integrations": [
    {
      "name": "",
      "type": "internal|external|unknown",
      "interaction": "",
      "data_exchanged": "",
      "auth_method": "",
      "evidence": [],
      "confidence": ""
    }
  ],

  "data_architecture": {
    "data_flow": [],
    "data_storage_strategy": "",
    "caching_strategy": ""
  },

  "security": {
    "authentication": [],
    "authorization": [],
    "secrets_handling": [],
    "network_security": [],
    "application_security": [],
    "data_protection": [],
    "compliance_scope": [],
    "confidence": ""
  },

  "deployment": {
    "hosting_clues": [],
    "ci_cd_clues": [],
    "runtime_clues": [],
    "environments": [],
    "infrastructure_components": [],
    "network_topology": "",
    "confidence": ""
  },

  "scalability_performance": {
    "scaling_strategy": "",
    "performance_considerations": [],
    "bottlenecks": []
  },

  "resilience": {
    "retry_strategies": [],
    "failover": [],
    "circuit_breakers": []
  },

  "observability": {
    "logging": [],
    "monitoring": [],
    "alerting": []
  },

  "disaster_recovery": {
    "backup_strategy": "",
    "rto": "",
    "rpo": ""
  },

  "compliance": {
    "standards": [],
    "notes": []
  },

  "observed_facts": [],
  "inferred_facts": [],
  "unknowns": [],
  "risks": [],

  "future_enhancements": [],

  "overall_confidence": ""
}
```

## Markdown sections

`output.md` must contain:

1. Overview
2. Business Context
3. Architecture Overview
4. Architecture Summary
5. Components
6. Data Stores
7. Data Architecture
8. Interfaces & APIs
9. Integrations
10. Security Architecture
11. Deployment
12. Scalability & Performance
13. Resilience
14. Logging & Monitoring
15. Disaster Recovery
16. Compliance
17. Observed Facts
18. Inferred Facts
19. Unknowns
20. Risks and Assumptions
21. Future Enhancements

Put this metadata header at the top:

- `generated_at:`
- `source_skill: tas-01-project-architecture-analyzer`
- `project_folder:`
- `workspace_folder:`
- `confidence_summary:`
