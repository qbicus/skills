---
document_type: project-tas
generated_at: {{generated_at}}
source_skill: tas-generator
workspace_folder: {{workspace_folder}}
project_name: {{project_name}}
confidence_summary: {{confidence_summary}}
---

# Technical Architecture Specification — {{project_name}}

> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.
>
> Source: Generated automatically from code and configuration analysis.
> Review status: Not reviewed / Partially reviewed / Reviewed

## 1. Overview

**Purpose**  
{{purpose}}

**Scope**  
{{scope}}

**Current State Summary**  
{{current_state_summary}}

---

## 2. Architecture Summary

{{architecture_summary}}

---

## 3. Core Components

{{#components}}
### {{name}}

- **Type:** {{type}}
- **Description:** {{description}}
- **Confidence:** {{confidence}}

{{/components}}

---

## 4. Interfaces and Integrations

### Inbound Interfaces
{{#inbound_interfaces}}
- {{.}}
{{/inbound_interfaces}}

### Outbound Integrations
{{#outbound_integrations}}
- {{.}}
{{/outbound_integrations}}

### Dependencies
{{#dependencies}}
- {{.}}
{{/dependencies}}

---

## 5. Data Architecture

### Data Stores
{{#datastores}}
- {{.}}
{{/datastores}}

### Data Notes
{{#data_notes}}
- {{.}}
{{/data_notes}}

---

## 6. Security and Access

### Authentication
{{#authentication}}
- {{.}}
{{/authentication}}

### Authorization
{{#authorization}}
- {{.}}
{{/authorization}}

### Secrets and Sensitive Configuration
{{#secrets}}
- {{.}}
{{/secrets}}

---

## 7. Deployment and Operations

### Hosting / Runtime
{{#hosting}}
- {{.}}
{{/hosting}}

### CI/CD
{{#cicd}}
- {{.}}
{{/cicd}}

### Operational Notes
{{#operations}}
- {{.}}
{{/operations}}

---

## 8. Observed Architecture Facts

{{#observed}}
- {{.}}
{{/observed}}

---

## 9. Inferred Architecture Facts

{{#inferred}}
- {{.}}
{{/inferred}}

---

## 10. Risks, Constraints, and Unknowns

### Risks
{{#risks}}
- {{.}}
{{/risks}}

### Constraints
{{#constraints}}
- {{.}}
{{/constraints}}

### Unknowns
{{#unknowns}}
- {{.}}
{{/unknowns}}

---

## 11. Reviewer Checklist

- [ ] Confirm purpose and scope
- [ ] Confirm architecture summary reflects the actual system
- [ ] Review all core components
- [ ] Review inbound and outbound integrations
- [ ] Confirm dependencies
- [ ] Validate data architecture
- [ ] Validate security and access notes
- [ ] Validate deployment and operational notes
- [ ] Review observed vs inferred facts
- [ ] Review risks, constraints, and unknowns
- [ ] Update Review status at the top of this document

---

## 12. Evidence / References Appendix

{{#references}}
- {{.}}
{{/references}}
