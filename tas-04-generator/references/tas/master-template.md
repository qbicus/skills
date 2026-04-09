---
document_type: master-tas
generated_at: {{generated_at}}
source_skill: tas-generator
workspace_folder: {{workspace_folder}}
confidence_summary: {{confidence_summary}}
---

# Technical Architecture Specification — Master Architecture Summary

> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.
>
> Source: Generated automatically from code and configuration analysis.
> Review status: Not reviewed / Partially reviewed / Reviewed

## 1. Overview

**Purpose**  
{{purpose}}

**Scope**  
{{scope}}

**Included Platforms**  
{{#included_platforms}}
- {{.}}
{{/included_platforms}}

---

## 2. Architectural Landscape

{{architectural_landscape_summary}}

---

## 3. Major Platforms

{{#platforms}}
### {{name}}

- **Description:** {{description}}
- **Projects:** {{projects}}
- **Key Notes:** {{notes}}

{{/platforms}}

---

## 4. Shared Enterprise Services

{{#shared_enterprise_services}}
### {{name}}

- **Consumers:** {{consumers}}
- **Notes:** {{notes}}

{{/shared_enterprise_services}}

---

## 5. Cross-Platform Dependencies

{{#cross_platform_dependencies}}
### {{source}} → {{target}}

- **Relationship:** {{relationship}}
- **Confidence:** {{confidence}}
- **Notes:** {{notes}}

{{/cross_platform_dependencies}}

---

## 6. Strategic Risks and Constraints

### Risks
{{#risks}}
- {{.}}
{{/risks}}

### Constraints
{{#constraints}}
- {{.}}
{{/constraints}}

---

## 7. Normalization Notes

{{#normalization_notes}}
- {{.}}
{{/normalization_notes}}

---

## 8. Open Questions and Gaps

{{#open_questions}}
- {{.}}
{{/open_questions}}

---

## 9. Reviewer Checklist

- [ ] Confirm included platforms
- [ ] Review the architectural landscape summary
- [ ] Review major platform descriptions
- [ ] Confirm shared enterprise services
- [ ] Confirm cross-platform dependencies
- [ ] Review strategic risks and constraints
- [ ] Review normalization notes
- [ ] Review open questions and gaps
- [ ] Update Review status at the top of this document

---

## 10. Appendix

### Input Sources
{{#input_sources}}
- {{.}}
{{/input_sources}}

### Additional Notes
{{#appendix_notes}}
- {{.}}
{{/appendix_notes}}
