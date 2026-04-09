---
document_type: architecture-normalization
generated_at: {{generated_at}}
source_skill: architecture-normalizer
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

**Shared Services**
{{#shared_services}}
- {{.}}
{{/shared_services}}

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
- **Notes:**
{{#notes}}
  - {{.}}
{{/notes}}

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
