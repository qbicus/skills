# Implementation Design Template

## 1. Spec Snapshot
- Spec file:
- Spec version/date:
- Approval status:
- Non-goals:

## 2. Scope Mapping
| Requirement ID | Requirement Summary | In Scope (yes/no) | Notes |
|---|---|---|---|
| `REQ-1` | `<summary>` | `yes|no` | `<notes>` |

## 3. Architecture Slice
- Entry points:
- Core services/components:
- Persistence:
- External integrations:
- Sequence summary:

## 4. Data Source Trust Matrix
| Source | Type | Trust Level | Validation Required | Rationale | Controls |
|---|---|---|---|---|---|
| `<name>` | `db/api/file/user-input` | `trusted-without-validation|validate-required` | `yes|no` | `<why>` | `<controls>` |

## 5. Validation and Invariants
| Invariant | Enforced Where | Failure Behavior |
|---|---|---|
| `<rule>` | `<component>` | `<error/rollback>` |

## 6. Query Safety Matrix
| Query/Operation | Classification | Guardrails | Fallback |
|---|---|---|---|
| `<query>` | `safe|guarded|forbidden` | `<limits/indexes/timeouts>` | `<behavior>` |

## 7. Error Taxonomy
| Error Class | Retryable | User Visible | Severity | Handling |
|---|---|---|---|---|
| `<class>` | `yes|no` | `yes|no` | `info|warn|error|fatal` | `<strategy>` |

## 8. File-by-File Implementation Plan
| File Path | Change Type | Purpose | Dependencies | Order |
|---|---|---|---|---|
| `<path>` | `new|modify|delete` | `<what/why>` | `<deps>` | `<n>` |

## 9. Contracts
| Contract | Change | Backward Compatible | Notes |
|---|---|---|---|
| `<api/schema/type>` | `<change>` | `yes|no` | `<notes>` |

## 10. State and Migration Plan
- Schema migrations:
- Data backfill:
- Idempotency:
- Rollback:

## 11. Config and Feature Flags
| Key | Default | Environment Overrides | Purpose |
|---|---|---|---|
| `<key>` | `<value>` | `<overrides>` | `<purpose>` |

## 12. Observability Plan
- Logs:
- Metrics:
- Traces:
- Alerts:
- Dashboard updates:

## 13. Security and Permissions
- Auth/authz:
- Secret handling:
- Data sensitivity:
- Audit events:

## 14. Performance and Capacity
- Latency budget:
- Throughput assumptions:
- Resource constraints:
- Load test plan:

## 15. Test Plan
| Test Level | Coverage | Key Cases |
|---|---|---|
| `unit|integration|e2e` | `<scope>` | `<cases>` |

## 16. Rollout and Backout
- Rollout stages:
- Success criteria:
- Rollback triggers:
- Backout steps:

## 17. Open Decisions
| Decision | Owner | Due Date | Blocking |
|---|---|---|---|
| `<item>` | `<owner>` | `<yyyy-mm-dd>` | `yes|no` |

## 18. Revision History
| Date | Author | Summary | Impacted Sections |
|---|---|---|---|
| `<yyyy-mm-dd>` | `<name>` | `<summary>` | `<sections>` |
