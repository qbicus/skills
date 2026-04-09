---
document_type: platform-tas
generated_at: {{generated_at}}
source_skill: tas-generator
workspace_folder: {{workspace_folder}}
platform_name: {{platform_name}}
confidence_summary: {{confidence_summary}}
---

# Technical Architecture Specification — {{platform_name}}

> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.
>
> Source: Generated automatically from code and configuration analysis.
> Review status: Not reviewed / Partially reviewed / Reviewed

## 1. Overview

**Purpose**  
{{purpose}}

**Scope**  
{{scope}}

**Included Projects**  
{{#included_projects}}
- {{.}}
{{/included_projects}}

---

## 2. Platform Architecture Summary

{{platform_architecture_summary}}

---

## 3. Constituent Projects

{{#projects}}
### {{name}}

- **Role:** {{role}}
- **Notes:** {{notes}}

{{/projects}}

---

## 4. Shared Services

{{#shared_services}}
### {{name}}

- **Used By:** {{used_by}}
- **Notes:** {{notes}}

{{/shared_services}}

---

## 5. Cross-Project Dependencies

{{#dependencies}}
### {{source}} → {{target}}

- **Relationship:** {{relationship}}
- **Confidence:** {{confidence}}
- **Notes:** {{notes}}

{{/dependencies}}

---

## 6. Data and Integration Landscape

### Shared Data Stores
{{#shared_datastores}}
- {{.}}
{{/shared_datastores}}

### Key Integrations
{{#key_integrations}}
- {{.}}
{{/key_integrations}}

### Data / Integration Notes
{{#integration_notes}}
- {{.}}
{{/integration_notes}}

---

## 7. Security and Operational Patterns

### Security Patterns
{{#security_patterns}}
- {{.}}
{{/security_patterns}}

### Operational Patterns
{{#operational_patterns}}
- {{.}}
{{/operational_patterns}}

---

## 8. Risks and Technical Debt

{{#risks}}
- {{.}}
{{/risks}}

---

## 9. Open Questions

{{#open_questions}}
- {{.}}
{{/open_questions}}

---

## 10. Reviewer Checklist

- [ ] Confirm included projects belong in this platform
- [ ] Review platform summary
- [ ] Review constituent project roles
- [ ] Confirm shared services are correct
- [ ] Confirm cross-project dependencies
- [ ] Review data and integration landscape
- [ ] Review security and operational patterns
- [ ] Review risks and technical debt
- [ ] Review open questions
- [ ] Update Review status at the top of this document

---

## 11. Appendix

### Source Projects
{{#source_projects}}
- {{.}}
{{/source_projects}}

### Notes
{{#appendix_notes}}
- {{.}}
{{/appendix_notes}}
