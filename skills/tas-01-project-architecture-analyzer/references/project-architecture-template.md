---
document_type: project-architecture-profile
generated_at: {{generated_at}}
source_skill: tas-01-project-architecture-analyzer
project_name: {{project_name}}
project_folder: {{source_project_folder}}
workspace_folder: {{workspace_output_folder}}
confidence_summary: {{overall_confidence}}
overall_confidence: {{overall_confidence}}
---

File Version: V1.1

# Project Architecture Profile: {{project_name}}

> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns, assumptions, risks, and confidence levels before treating the document as authoritative.
>
> Source: Generated automatically from code and configuration analysis.
> Review status: Not reviewed / Partially reviewed / Reviewed

## 1. Overview

**Summary**  
{{summary}}

**Project Name**  
{{project_name}}

**Source Project Folder**  
{{source_project_folder}}

**Workspace Output Folder**  
{{workspace_output_folder}}

---

## 2. Business Context

{{business_context}}

---

## 3. Architecture Overview

**Architecture Style**  
{{architecture.style}}

**High-Level Description**  
{{architecture.high_level_description}}

**Design Principles**  
{{#architecture.design_principles}}
- {{.}}
{{/architecture.design_principles}}

---

## 4. Architecture Summary

**Project Type**  
{{project_type}}

**Primary Stack**  
{{#primary_stack}}
- {{.}}
{{/primary_stack}}

**Entry Points**  
{{#entry_points}}
- {{.}}
{{/entry_points}}

**Deployable Units**  
{{#deployable_units}}
- {{.}}
{{/deployable_units}}

**Constraints**  
{{#constraints}}
- {{.}}
{{/constraints}}

---

## 5. Components

{{#components}}
### {{name}}

- **Kind:** {{kind}}
- **Description:** {{description}}
- **Dependencies:**
{{#dependencies}}
  - {{.}}
{{/dependencies}}
- **Interfaces Exposed:**
{{#interfaces_exposed}}
  - {{.}}
{{/interfaces_exposed}}
- **Evidence:**
{{#evidence}}
  - {{.}}
{{/evidence}}
- **Confidence:** {{confidence}}

{{/components}}

---

## 6. Data Stores

{{#datastores}}
### {{name}}

- **Type:** {{type}}
- **Usage:** {{usage}}
- **Data Classification:** {{data_classification}}
- **Encryption at Rest:** {{encryption.at_rest}}
- **Encryption in Transit:** {{encryption.in_transit}}
- **Evidence:**
{{#evidence}}
  - {{.}}
{{/evidence}}
- **Confidence:** {{confidence}}

{{/datastores}}

---

## 7. Data Architecture

**Data Flow**  
{{#data_architecture.data_flow}}
- {{.}}
{{/data_architecture.data_flow}}

**Data Storage Strategy**  
{{data_architecture.data_storage_strategy}}

**Caching Strategy**  
{{data_architecture.caching_strategy}}

---

## 8. Interfaces & APIs

### Inbound Interfaces
{{#interfaces.inbound}}
- {{.}}
{{/interfaces.inbound}}

### Outbound Interfaces
{{#interfaces.outbound}}
- {{.}}
{{/interfaces.outbound}}

### Protocols
{{#interfaces.protocols}}
- {{.}}
{{/interfaces.protocols}}

### Authentication Methods
{{#interfaces.authentication_methods}}
- {{.}}
{{/interfaces.authentication_methods}}

### API Catalog
{{#api_catalog}}
- {{.}}
{{/api_catalog}}

---

## 9. Integrations

{{#integrations}}
### {{name}}

- **Type:** {{type}}
- **Interaction:** {{interaction}}
- **Data Exchanged:** {{data_exchanged}}
- **Authentication Method:** {{auth_method}}
- **Evidence:**
{{#evidence}}
  - {{.}}
{{/evidence}}
- **Confidence:** {{confidence}}

{{/integrations}}

---

## 10. Security Architecture

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

### Network Security
{{#security.network_security}}
- {{.}}
{{/security.network_security}}

### Application Security
{{#security.application_security}}
- {{.}}
{{/security.application_security}}

### Data Protection
{{#security.data_protection}}
- {{.}}
{{/security.data_protection}}

### Compliance Scope
{{#security.compliance_scope}}
- {{.}}
{{/security.compliance_scope}}

**Security Confidence**  
{{security.confidence}}

---

## 11. Deployment

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

### Environments
{{#deployment.environments}}
- {{.}}
{{/deployment.environments}}

### Infrastructure Components
{{#deployment.infrastructure_components}}
- {{.}}
{{/deployment.infrastructure_components}}

**Network Topology**  
{{deployment.network_topology}}

**Deployment Confidence**  
{{deployment.confidence}}

---

## 12. Scalability & Performance

**Scaling Strategy**  
{{scalability_performance.scaling_strategy}}

### Performance Considerations
{{#scalability_performance.performance_considerations}}
- {{.}}
{{/scalability_performance.performance_considerations}}

### Bottlenecks
{{#scalability_performance.bottlenecks}}
- {{.}}
{{/scalability_performance.bottlenecks}}

---

## 13. Resilience

### Retry Strategies
{{#resilience.retry_strategies}}
- {{.}}
{{/resilience.retry_strategies}}

### Failover
{{#resilience.failover}}
- {{.}}
{{/resilience.failover}}

### Circuit Breakers
{{#resilience.circuit_breakers}}
- {{.}}
{{/resilience.circuit_breakers}}

---

## 14. Logging & Monitoring

### Logging
{{#observability.logging}}
- {{.}}
{{/observability.logging}}

### Monitoring
{{#observability.monitoring}}
- {{.}}
{{/observability.monitoring}}

### Alerting
{{#observability.alerting}}
- {{.}}
{{/observability.alerting}}

---

## 15. Disaster Recovery

**Backup Strategy**  
{{disaster_recovery.backup_strategy}}

**RTO**  
{{disaster_recovery.rto}}

**RPO**  
{{disaster_recovery.rpo}}

---

## 16. Compliance

### Standards
{{#compliance.standards}}
- {{.}}
{{/compliance.standards}}

### Notes
{{#compliance.notes}}
- {{.}}
{{/compliance.notes}}

---

## 17. Observed Facts

{{#observed_facts}}
- {{.}}
{{/observed_facts}}

---

## 18. Inferred Facts

{{#inferred_facts}}
- {{.}}
{{/inferred_facts}}

---

## 19. Unknowns

{{#unknowns}}
- {{.}}
{{/unknowns}}

---

## 20. Risks and Assumptions

### Risks
{{#risks}}
- {{.}}
{{/risks}}

### Assumptions
{{#assumptions}}
- {{.}}
{{/assumptions}}

---

## 21. Future Enhancements

{{#future_enhancements}}
- {{.}}
{{/future_enhancements}}

---

## Reviewer Checklist

- [ ] Confirm generated_at, project_name, source_project_folder, and workspace_output_folder
- [ ] Confirm summary and business_context align with the codebase and business purpose
- [ ] Confirm architecture.style, architecture.high_level_description, and architecture.design_principles
- [ ] Validate project_type, primary_stack, entry_points, and deployable_units
- [ ] Check that components, dependencies, interfaces_exposed, and evidence are accurate
- [ ] Check that datastores, encryption, and usage details are accurate
- [ ] Confirm data_architecture content, interfaces, API catalog, and integrations
- [ ] Review security findings, confidence levels, and compliance scope
- [ ] Review deployment clues, environments, runtime assumptions, and network topology
- [ ] Validate scalability, resilience, observability, and disaster recovery details
- [ ] Validate observed_facts and review inferred_facts for weak assumptions
- [ ] Expand unknowns where evidence is insufficient
- [ ] Review risks, assumptions, and future_enhancements
- [ ] Update Review status at the top of this document

---

## Evidence Appendix

### Component Evidence
{{#components}}
#### {{name}}
{{#evidence}}
- {{.}}
{{/evidence}}

{{/components}}

### Datastore Evidence
{{#datastores}}
#### {{name}}
{{#evidence}}
- {{.}}
{{/evidence}}

{{/datastores}}

### Integration Evidence
{{#integrations}}
#### {{name}}
{{#evidence}}
- {{.}}
{{/evidence}}

{{/integrations}}