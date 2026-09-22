---
document_type: architecture-normalization
generated_at: {{generated_at}}
source_skill: tas-03-architecture-normalizer
workspace_folder: {{workspace_folder}}
---

# Architecture Normalization Summary

> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.
>
> Source: Generated automatically from code and configuration analysis.
> Review status: Not reviewed / Partially reviewed / Reviewed

## 1. Overview

This document reconciles naming differences, aliases, duplicates, and conflicting terminology across analyzed projects and grouped platform data.

**Canonical Entities:** {{canonical_entities_count}}  
**Manual Review Items:** {{manual_review_queue_count}}

---

## 2. Canonical Entities

{{#canonical_entities}}
### {{canonical_name}}

- **Entity Type:** {{entity_type}}
- **Merge Recommendation:** {{merge_recommendation}}
- **Confidence:** {{confidence}}

**Aliases**
{{#aliases}}
- {{.}}
{{/aliases}}

**Source References**
{{#source_references}}
- {{.}}
{{/source_references}}

**Rationale**
{{#rationale}}
- {{.}}
{{/rationale}}

{{/canonical_entities}}

---

## 3. Normalized Platforms

{{#normalized_platforms}}
### {{name}}

**Projects**
{{#projects}}
- {{.}}
{{/projects}}

**Primary Stack**
{{#primary_stack}}
- {{.}}
{{/primary_stack}}

**Entry Surfaces**
{{#entry_surfaces}}
- {{.}}
{{/entry_surfaces}}

**Deployable Units**
{{#deployable_units}}
- {{.}}
{{/deployable_units}}

**Components**
{{#components}}
- {{name}}
{{/components}}

**Datastores**
{{#datastores}}
- {{name}}
{{/datastores}}

**Interfaces**
- Inbound: {{interfaces.inbound_text}}
- Outbound: {{interfaces.outbound_text}}

**Integrations**
{{#integrations}}
- {{name}}
{{/integrations}}

**Security**
- Auth Systems: {{security.auth_systems_text}}
- Secrets Handling: {{security.secrets_handling_text}}
- Confidence: {{security.confidence}}

**Deployment**
- Hosting Clues: {{deployment.hosting_clues_text}}
- CI/CD Clues: {{deployment.ci_cd_clues_text}}
- Runtime Clues: {{deployment.runtime_clues_text}}
- Confidence: {{deployment.confidence}}

**Shared Services**
{{#shared_services}}
- {{.}}
{{/shared_services}}

**Shared Datastores**
{{#shared_datastores}}
- {{.}}
{{/shared_datastores}}

**Key Integrations**
{{#key_integrations}}
- {{.}}
{{/key_integrations}}

**Cross-Project Dependencies**
{{#cross_project_dependencies}}
- {{source_project}} -> {{target_project_or_service}} | {{relationship}} | {{confidence}}
{{/cross_project_dependencies}}

**Grouping Rationale**
{{#grouping_rationale}}
- {{.}}
{{/grouping_rationale}}

**Observed Facts**
{{#observed_facts}}
- {{.}}
{{/observed_facts}}

**Inferred Facts**
{{#inferred_facts}}
- {{.}}
{{/inferred_facts}}

**Unknowns**
{{#unknowns}}
- {{.}}
{{/unknowns}}

**Risks**
{{#risks}}
- {{.}}
{{/risks}}

**Assumptions**
{{#assumptions}}
- {{.}}
{{/assumptions}}

**Notes**
{{#notes}}
- {{.}}
{{/notes}}

{{/normalized_platforms}}

---

## 4. Normalized Dependencies

{{#normalized_dependencies}}
### {{source}} → {{target}}

- **Relationship:** {{relationship}}
- **Confidence:** {{confidence}}
- **Evidence:**
{{#evidence}}
- {{.}}
{{/evidence}}

{{/normalized_dependencies}}

---

## 5. Manual Review Queue

{{#manual_review_queue}}
### {{issue_type}}

**Candidates**
{{#candidates}}
- {{.}}
{{/candidates}}

**Reason**  
{{reason}}

{{/manual_review_queue}}

---

## 6. Unknowns

{{#unknowns}}
- {{.}}
{{/unknowns}}

---

## 7. Assumptions

{{#assumptions}}
- {{.}}
{{/assumptions}}

---

## 8. Reviewer Checklist

- [ ] Confirm canonical names are appropriate
- [ ] Confirm aliases map to the correct canonical entities
- [ ] Review all merge recommendations
- [ ] Review keep_separate recommendations
- [ ] Work through the manual review queue
- [ ] Check normalized platforms for unintended merges
- [ ] Check normalized dependencies for clarity and correctness
- [ ] Review unknowns and assumptions
- [ ] Update Review status at the top of this document
