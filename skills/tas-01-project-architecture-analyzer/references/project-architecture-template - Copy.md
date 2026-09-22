---
document_type: project-architecture-profile
generated_at: {{generated_at}}
source_skill: project-architecture-analyzer
project_name: {{project_name}}
project_folder: {{project_folder}}
workspace_folder: {{workspace_folder}}
overall_confidence: {{overall_confidence}}
---

# Project Architecture Profile: {{project_name}}

> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.
>
> Source: Generated automatically from code and configuration analysis.
> Review status: Not reviewed / Partially reviewed / Reviewed

## 1. Overview

**Summary**  
{{summary}}

**Project Type**  
{{project_type}}

**Primary Stack**  
{{primary_stack}}

**Entry Points**  
{{entry_points}}

**Deployable Units**  
{{deployable_units}}

---

## 2. Architecture Summary

{{architecture_summary}}

---

## 3. Core Components

{{#components}}
### {{name}}

- **Kind:** {{kind}}
- **Description:** {{description}}
- **Confidence:** {{confidence}}
- **Evidence:**
{{#evidence}}
  - {{.}}
{{/evidence}}

{{/components}}

---

## 4. Data Stores

{{#datastores}}
### {{name}}

- **Type:** {{type}}
- **Usage:** {{usage}}
- **Confidence:** {{confidence}}
- **Evidence:**
{{#evidence}}
  - {{.}}
{{/evidence}}

{{/datastores}}

---

## 5. Interfaces

### Inbound

{{#interfaces.inbound}}
- {{.}}
{{/interfaces.inbound}}

### Outbound

{{#interfaces.outbound}}
- {{.}}
{{/interfaces.outbound}}

---

## 6. Integrations

{{#integrations}}
### {{name}}

- **Type:** {{type}}
- **Interaction:** {{interaction}}
- **Confidence:** {{confidence}}
- **Evidence:**
{{#evidence}}
  - {{.}}
{{/evidence}}

{{/integrations}}

---

## 7. Security

### Authentication
{{#security.authentication}}
- {{.}}
{{/security.authentication}}

### Authorization
{{#security.authorization}}
- {{.}}
{{/security.authorization}}

### Secrets Handling
{{#security.secrets_handling}}
- {{.}}
{{/security.secrets_handling}}

**Security Confidence:** {{security.confidence}}

---

## 8. Deployment and Operations

### Hosting Clues
{{#deployment.hosting_clues}}
- {{.}}
{{/deployment.hosting_clues}}

### CI/CD Clues
{{#deployment.ci_cd_clues}}
- {{.}}
{{/deployment.ci_cd_clues}}

### Runtime Clues
{{#deployment.runtime_clues}}
- {{.}}
{{/deployment.runtime_clues}}

**Deployment Confidence:** {{deployment.confidence}}

---

## 9. Observed Facts

{{#observed_facts}}
- {{.}}
{{/observed_facts}}

---

## 10. Inferred Facts

{{#inferred_facts}}
- {{.}}
{{/inferred_facts}}

---

## 11. Unknowns

{{#unknowns}}
- {{.}}
{{/unknowns}}

---

## 12. Risks

{{#risks}}
- {{.}}
{{/risks}}

---

## 13. Assumptions

{{#assumptions}}
- {{.}}
{{/assumptions}}

---

## 14. Reviewer Checklist

- [ ] Confirm the detected project name and source path are correct
- [ ] Confirm the project type is accurate
- [ ] Validate the primary stack and entry points
- [ ] Validate the listed deployable units
- [ ] Check that the core components match the codebase
- [ ] Check that all important data stores are captured
- [ ] Confirm inbound and outbound interfaces
- [ ] Confirm internal and external integrations
- [ ] Review security findings for accuracy
- [ ] Review deployment / CI/CD clues
- [ ] Validate observed facts
- [ ] Review inferred facts and remove weak assumptions
- [ ] Add or clarify unknowns where evidence is missing
- [ ] Review risks and assumptions
- [ ] Update Review status at the top of this document

---

## 15. Evidence Appendix

{{evidence_appendix}}
