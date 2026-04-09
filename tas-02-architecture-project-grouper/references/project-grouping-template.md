---
document_type: architecture-grouping
generated_at: {{generated_at}}
source_skill: architecture-project-grouper
workspace_folder: {{workspace_folder}}
---

# Project Grouping Summary

> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.
>
> Source: Generated automatically from code and configuration analysis.
> Review status: Not reviewed / Partially reviewed / Reviewed

## 1. Overview

This document groups analyzed projects into likely platforms, identifies shared services, and highlights cross-project dependencies.

**Projects Analyzed:** {{projects_analyzed_count}}  
**Platforms Proposed:** {{platforms_count}}  
**Shared Services Identified:** {{shared_services_count}}  
**Orphans:** {{orphans_count}}

---

## 2. Proposed Platforms

{{#platforms}}
### {{name}}

**Description**  
{{description}}

**Projects**
{{#projects}}
- {{.}}
{{/projects}}

**Shared Services**
{{#shared_services}}
- {{.}}
{{/shared_services}}

**Shared Data Stores**
{{#shared_datastores}}
- {{.}}
{{/shared_datastores}}

**Key Integrations**
{{#key_integrations}}
- {{.}}
{{/key_integrations}}

**Grouping Rationale**
{{#grouping_rationale}}
- {{.}}
{{/grouping_rationale}}

**Confidence:** {{confidence}}

{{/platforms}}

---

## 3. Shared Services

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

## 4. Cross-Project Dependencies

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

## 5. Naming Collisions

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

## 6. Orphans

{{#orphans}}
- {{.}}
{{/orphans}}

---

## 7. Unknowns

{{#unknowns}}
- {{.}}
{{/unknowns}}

---

## 8. Assumptions

{{#assumptions}}
- {{.}}
{{/assumptions}}

---

## 9. Reviewer Checklist

- [ ] Confirm all expected analyzer outputs were included
- [ ] Review whether each proposed platform grouping is sensible
- [ ] Confirm shared services are truly shared
- [ ] Validate shared data store grouping
- [ ] Review cross-project dependencies for false positives
- [ ] Review orphan projects to ensure none were missed
- [ ] Review naming collisions for likely duplicates
- [ ] Review unknowns and assumptions
- [ ] Update Review status at the top of this document
