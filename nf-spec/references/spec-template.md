# Feature Specification Template

## 1. Problem Statement
- Objective:
- Users impacted:
- Current pain:
- Measurable success criteria:

## 2. Design Decisions and Rejected Alternatives
- Decision 1:
  - Rationale:
  - Rejected alternatives:
    - Alternative:
    - Why rejected:

## 3. Data Model
### Entity: `<name>`
| Field | Type | Required/Optional | Constraints | Default |
|---|---|---|---|---|
| `<field>` | `<type>` | `required|optional` | `<rules>` | `<value or n/a>` |

## 4. Shared Types
### `<TypeName>`
| Field | Type | Required/Optional | Notes |
|---|---|---|---|
| `<field>` | `<type>` | `required|optional` | `<notes>` |

## 5. Language
| Area | Enabled (yes/no) | Variant/Stack | Notes |
|---|---|---|---|
| UI | `yes|no` | `native|avalonia|...` | `<notes>` |
| SQL | `yes|no` | `mssql|pgsql|mysql|...` | `<notes>` |
| HTML | `yes|no` | `<stack or n/a>` | `<notes>` |
| CSS | `yes|no` | `css|scss|...` | `<notes>` |
| JS | `yes|no` | `vanilla|jquery|ts|...` | `<notes>` |

## 6. API Endpoints
If not applicable, write: `No API endpoints needed for this implementation` and explain why in 1-2 lines.

### `<METHOD> <path>`
- Purpose:
- Auth:
- Request fields:

| Field | Location | Type | Required/Optional | Constraints |
| ---- | --- | --- | --- | --- |
| `<field>` | `path|query|body` | `<type>` | `required|optional` | `<rules>` |
- Success response:

| Field | Type | Required/Optional | Notes |
|---|---|---|---|
| `<field>` | `<type>` | `required|optional` | `<notes>` |

## 7. Validation Rules and Boundary Values
| Field | Rule | Boundary Values (valid/invalid) | Error Code |
|---|---|---|---|
| `<field>` | `<rule>` | `<example>` | `<code>` |

## 8. Error Responses
| Error Code | HTTP Status | Trigger | Client Message |
|---|---|---|---|
| `<code>` | `<status>` | `<condition>` | `<guidance>` |

## 9. UX Flows
### Primary Flow
1. Step:
2. Step:

### Empty/Error/Recovery States
- State:
- Trigger:
- UX behavior:

## 10. Phasing
| Phase | Scope | Entry Criteria | Exit Criteria | Risks |
|---|---|---|---|---|
| `P1` | `<scope>` | `<entry>` | `<exit>` | `<risk>` |

### Parallel Execution Preference
- Feasible: `yes|no`
- Approved max parallel agents: `<1..n>`
- Why:
- Constraints on safe parallelism:
- Non-parallelizable areas:

## 11. Out of Scope
- Explicitly excluded item:

## 12. Open TODOs
| TODO | Owner | Deadline | Blocking? |
|---|---|---|---|
| `<item>` | `<name>` | `<date>` | `yes|no` |

## 13. Revision History
| Date | Author | Summary | Impacted Sections |
|---|---|---|---|
| `<YYYY-MM-DD>` | `<name>` | `<change summary>` | `<sections>` |
