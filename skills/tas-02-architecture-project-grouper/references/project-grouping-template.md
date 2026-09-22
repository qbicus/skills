---
document_type: architecture-grouping
generated_at: {{generated_at}}
source_skill: tas-02-architecture-project-grouper
workspace_folder: {{workspace_folder}}
---

# Project Grouping Summary

> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.
>
> Source: Generated automatically from analyzer outputs plus conservative normalization.
> Review status: Not reviewed / Partially reviewed / Reviewed

## 1. Overview

This document groups analyzed projects into likely platforms, identifies shared services, and summarizes aggregated platform architecture signals.

**Projects Analyzed:** {{projects_analyzed_count}}  
**Platforms Proposed:** {{platforms_count}}  
**Shared Services Identified:** {{shared_services_count}}  
**Orphans:** {{orphans_count}}

---

## 2. Platform Summaries

{{#platforms}}
### {{name}}

**Summary**  
{{summary}}

**Business Context**  
{{business_context}}

**Platform Type**  
{{platform_type}}

**Projects**
{{#projects}}
- {{.}}
{{/projects}}

**Primary Stack**
{{#primary_stack}}
- {{.}}
{{/primary_stack}}

**Confidence:** {{confidence}}

{{/platforms}}

---

## 3. Grouping Rationale

{{#platforms}}
### {{name}}
{{#grouping_rationale}}
- {{.}}
{{/grouping_rationale}}

{{/platforms}}

---

## 4. Shared Services

{{#shared_services}}
### {{name}}

**Used By**
{{#used_by}}
- {{.}}
{{/used_by}}

**Evidence**
{{#evidence}}
- {{.}}
{{/evidence}}

**Confidence:** {{confidence}}

{{/shared_services}}

---

## 5. Cross-Project Dependencies

{{#cross_project_dependencies}}
### {{source_project}} → {{target_project_or_service}}

- **Relationship:** {{relationship}}
- **Confidence:** {{confidence}}
- **Evidence:**
{{#evidence}}
  - {{.}}
{{/evidence}}

{{/cross_project_dependencies}}

---

## 6. Architecture Overview by Platform

{{#platforms}}
### {{name}}

**Entry Surfaces**
{{#entry_surfaces}}
- {{.}}
{{/entry_surfaces}}

**Deployable Units**
{{#deployable_units}}
- {{.}}
{{/deployable_units}}

**Shared Services**
{{#shared_services}}
- {{.}}
{{/shared_services}}

**Shared Data Stores**
{{#shared_datastores}}
- {{.}}
{{/shared_datastores}}

{{/platforms}}

---

## 7. Data Stores

{{#platforms}}
### {{name}}
{{#datastores}}
- {{name}}
{{/datastores}}

{{/platforms}}

---

## 8. Interfaces & Integrations

{{#platforms}}
### {{name}}

**Inbound Interfaces**
{{#interfaces.inbound}}
- {{.}}
{{/interfaces.inbound}}

**Outbound Interfaces**
{{#interfaces.outbound}}
- {{.}}
{{/interfaces.outbound}}

**Integrations**
{{#integrations}}
- {{name}}
{{/integrations}}

{{/platforms}}

---

## 9. Security

{{#platforms}}
### {{name}}

**Auth Systems**
{{#security.auth_systems}}
- {{.}}
{{/security.auth_systems}}

**Secrets Handling**
{{#security.secrets_handling}}
- {{.}}
{{/security.secrets_handling}}

**Confidence:** {{security.confidence}}

{{/platforms}}

---

## 10. Deployment

{{#platforms}}
### {{name}}

**Hosting Clues**
{{#deployment.hosting_clues}}
- {{.}}
{{/deployment.hosting_clues}}

**CI/CD Clues**
{{#deployment.ci_cd_clues}}
- {{.}}
{{/deployment.ci_cd_clues}}

**Runtime Clues**
{{#deployment.runtime_clues}}
- {{.}}
{{/deployment.runtime_clues}}

**Confidence:** {{deployment.confidence}}

{{/platforms}}

---

## 11. Orphans

{{#orphans}}
### {{project_name}}

**Summary**  
{{summary}}

**Reasons Not Grouped**
{{#reasons_not_grouped}}
- {{.}}
{{/reasons_not_grouped}}

**Observed Signals**
{{#observed_signals}}
- {{.}}
{{/observed_signals}}

**Unknowns**
{{#unknowns}}
- {{.}}
{{/unknowns}}

**Confidence:** {{confidence}}

{{/orphans}}

---

## 12. Naming Collisions

{{#naming_collisions}}
### {{canonical_candidate}}

**Variants**
{{#variants}}
- {{.}}
{{/variants}}

**Notes**
{{#notes}}
- {{.}}
{{/notes}}

{{/naming_collisions}}

---

## 13. Observed Facts

{{#platforms}}
### {{name}}
{{#observed_facts}}
- {{.}}
{{/observed_facts}}

{{/platforms}}

---

## 14. Inferred Facts

{{#platforms}}
### {{name}}
{{#inferred_facts}}
- {{.}}
{{/inferred_facts}}

{{/platforms}}

---

## 15. Unknowns

{{#platforms}}
### {{name}}
{{#unknowns}}
- {{.}}
{{/unknowns}}

{{/platforms}}

{{#unknowns}}
- {{.}}
{{/unknowns}}

---

## 16. Risks and Assumptions

{{#platforms}}
### {{name}}

**Risks**
{{#risks}}
- {{.}}
{{/risks}}

**Assumptions**
{{#assumptions}}
- {{.}}
{{/assumptions}}

{{/platforms}}

{{#assumptions}}
- {{.}}
{{/assumptions}}

---

## 17. Reviewer Checklist

- [ ] Confirm all expected analyzer outputs were included
- [ ] Review whether each proposed platform grouping is sensible
- [ ] Confirm inferred auth mappings are justified
- [ ] Review inferred cross-project dependencies for false positives
- [ ] Validate shared data store grouping
- [ ] Review orphan projects to ensure none were missed
- [ ] Review naming collisions for likely duplicates
- [ ] Review unknowns, risks, and assumptions
- [ ] Update Review status at the top of this document
