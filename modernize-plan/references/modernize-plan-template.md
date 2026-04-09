# Modernize Plan Template

## 1. Evaluation Snapshot
- `modernize-eval` input:
- Recommended strategy:
- Confidence:
- Modernization Complexity Score:
- Migration Suitability Score:
- Rewrite Pressure Score:

## 2. Current-State Baseline
- Current framework/runtime:
- Build/test posture:
- Current dependency posture:
- Current deployment model:
- Known constraints:

## 3. Target-State Definition
- Target framework/runtime:
- Target dependency posture:
- Target hosting/deployment assumptions:
- Explicit non-goals:

## 4. Compatibility and Breaking Change Inventory
| Area | Severity | Breaking Change | Impact | Required Action |
|---|---|---|---|---|
| `<area>` | `low|med|high` | `<change>` | `<impact>` | `<action>` |

## 5. Dependency Upgrade Matrix
| Dependency | Current | Target | Compatibility Notes | Blockers | Upgrade Order |
|---|---|---|---|---|---|
| `<name>` | `<ver>` | `<ver>` | `<notes>` | `<blockers>` | `<order>` |

## 6. Architecture and Code Impact Areas
| Area | Why It Changes | Expected Work |
|---|---|---|
| `<module>` | `<reason>` | `<change summary>` |

## 7. Data and Integration Impact
| Surface | Impact | Constraint | Required Validation |
|---|---|---|---|
| `<db/api/queue/cache>` | `<impact>` | `<constraint>` | `<validation>` |

## 8. Environment and Deployment Impact
- Local/dev/test/prod differences:
- Hosting/runtime changes:
- Config/secret changes:
- Release pipeline or manual deploy impact:

## 9. Migration Strategy and Sequencing
- Strategy:
- Phases or waves:
- Critical path:
- Safe cut points:
- Parallelizable areas:

## 10. Verification Strategy
| Level | Area | Verification | Evidence |
|---|---|---|---|
| `build|unit|integration|smoke|env` | `<area>` | `<check>` | `<evidence>` |

## 11. Rollback and Safety Controls
- Backout approach:
- Irreversible actions:
- Kill switches / stop conditions:
- Safety guardrails:

## 12. Ordered Execution Plan
| ID | Objective | Files/Areas | Dependencies | Execution Mode | Worker Slot | Status | Acceptance Check | Verification Evidence |
|---|---|---|---|---|---|---|---|---|
| `M001` | `<objective>` | `<files/areas>` | `<deps>` | `sequential|parallel-safe` | `<none|Agent 1>` | `not-started|in-progress|blocked|done` | `<acceptance>` | `<evidence>` |

## 13. Execution Status
- Completed:
- In progress:
- Blocked:
- Not started:
- Active batch or worker summary:

## 14. Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| `<risk>` | `low|med|high` | `low|med|high` | `<plan>` | `<owner>` |

## 15. Open Decisions
| Decision | Owner | Due Date | Blocking |
|---|---|---|---|
| `<item>` | `<owner>` | `<date>` | `yes|no` |

## 16. Revision History
| Date | Author | Summary | Impacted Sections |
|---|---|---|---|
| `<yyyy-mm-dd>` | `<name>` | `<summary>` | `<sections>` |
