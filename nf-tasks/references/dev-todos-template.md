# Dev Todos Template

## 1. Design Snapshot
- Design file:
- Feature short name:
- Scope summary:
- Out of scope:

## 2. Delivery Strategy
- Milestone sequence:
- Risk-first tasks:
- Rollout approach:
- Execution mode: `sequential-only|parallel-eligible`
- Approved max parallel agents:
- Parallel batch summary:

## 3. Ordered Task List
| Task ID | Objective | Touchpoints | Dependencies | Execution Mode | Parallel Batch | Agent Slot | Status | Acceptance Check |
|---|---|---|---|---|---|---|---|---|
| `T001` | `<objective>` | `<files/services>` | `<task ids>` | `sequential|parallel-safe` | `<none|P1>` | `<none|Agent 1>` | `not-started|in-progress|blocked|done` | `<measurable outcome>` |

## 4. Execution Status
- Completed:
- In progress:
- Blocked:
- Not started:
- Active work summary:

## 5. Dependency Notes
- Critical path:
- Parallelizable tasks:
- External dependencies:
- Parallel batching constraints:

## 6. Quality Checklist

Mark each as `pass`, `fail`, or `n-a`.

### A. Input and Data Validation
1. All external inputs are validated at boundaries.
2. Null/empty checks exist for required fields.
3. Length limits are enforced for text fields.
4. Numeric ranges are bounded and tested.
5. Enum/domain values are validated against allowed sets.
6. Date/time parsing uses explicit format/timezone assumptions.
7. File/path inputs are normalized and sanitized.
8. Unsafe defaults are rejected early.

### B. Security and Privacy
9. Auth checks exist for all protected actions.
10. Authorization is resource-scoped, not role-name only.
11. Secrets are not stored in plaintext.
12. Secrets are not logged or emitted in errors.
13. Sensitive data is redacted in logs.
14. SQL queries are parameterized (no concatenation).
15. Path traversal protections are in place.
16. Dependency versions are pinned or constrained.
17. Third-party calls use least-privilege credentials.
18. Audit trail captures actor + action + timestamp.

### C. Type Safety and Contracts
19. Public contracts are strongly typed.
20. Optional vs required fields are consistent across layers.
21. DTO-to-domain mapping handles unknown/missing fields safely.
22. Contract changes include backward compatibility decision.
23. Serialization settings are deterministic.
24. Magic strings are replaced with typed constants/enums.

### D. Error Handling and Resilience
25. Error classes are explicit and documented.
26. Retry policy exists only for retryable failures.
27. Non-retryable failures fail fast with clear diagnostics.
28. Timeout values are defined for all IO operations.
29. Circuit-break/fallback behavior is defined where needed.
30. Partial failure behavior is explicit.
31. Cancellation handling is safe and consistent.
32. Cleanup/rollback is defined for interrupted operations.

### E. Observability
33. Structured logs include correlation IDs.
34. Stage-level success/failure metrics are emitted.
35. Latency/duration metrics are emitted for critical operations.
36. Alerts exist for high-severity failure patterns.
37. Logs are actionable (who/what/where/why).
38. Reporting/output captures per-item outcomes.

### F. Data and Query Safety
39. Read queries have explicit filters and limits when applicable.
40. Write queries have guardrails and preconditions.
41. Destructive operations require explicit confirmation.
42. Transaction boundaries are explicit where needed.
43. Index assumptions are validated for heavy queries.
44. Idempotency behavior is defined for retries/re-runs.

### G. Configuration and Environment
45. All env-specific values are externalized to config.
46. Safe defaults exist for production-sensitive flags.
47. Feature flags include kill-switch behavior.
48. Startup fails clearly on invalid configuration.
49. Environment switching is deterministic and testable.

### H. Performance and Capacity
50. Hot paths are identified and benchmarked.
51. Batch/loop operations avoid unbounded memory growth.
52. Large IO uses streaming where appropriate.
53. Concurrency level is explicitly constrained.
54. Backpressure/rate limiting is defined for external dependencies.

### I. Testing Discipline
55. Unit tests cover core business rules.
56. Integration tests cover IO boundaries.
57. End-to-end tests cover main user workflow.
58. Failure-path tests exist for top error classes.
59. Regression tests exist for previously fixed bugs.
60. Test data is deterministic and isolated.

### J. Release and Maintainability
61. Rollout plan defines stages and success criteria.
62. Backout plan is documented and tested.
63. Migration steps are reversible or safely compensating.
64. Code ownership/review expectations are clear.
65. Documentation is updated with behavior changes.
66. Revision history entry added for this planning pass.

## 7. Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| `<risk>` | `low|med|high` | `low|med|high` | `<plan>` | `<owner>` |

## 8. Test and Verification Plan
| Level | Scope | Cases | Evidence |
|---|---|---|---|
| `unit|integration|e2e` | `<scope>` | `<cases>` | `<artifact/log>` |

## 9. Done Criteria
- All required tasks completed.
- All blocking checklist items marked `pass`.
- Failing non-blocking items have tracked follow-ups.
- Verification evidence attached.

## 10. Open Questions
| Question | Owner | Due Date | Blocking |
|---|---|---|---|
| `<question>` | `<owner>` | `<yyyy-mm-dd>` | `yes|no` |

## 11. Revision History
| Date | Author | Summary | Impacted Sections |
|---|---|---|---|
| `<yyyy-mm-dd>` | `<name>` | `<summary>` | `<sections>` |
