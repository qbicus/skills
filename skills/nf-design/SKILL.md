---
name: nf-design
description: Take an approved `new-feature` spec and produce an implementation design with explicit file-by-file changes, risk controls, and rollout guidance. Use when a user asks for `/nf-design`, needs the design stage of `new-feature`, or wants implementation planning, technical design breakdown, or engineering execution steps from an existing spec.
---

# NF Design

Produce execution-ready technical designs from approved specs.

Use the template in [references/design-template.md](references/design-template.md) unless the user requests a different format.

## Workflow

1. Confirm inputs
- Require an approved spec path or pasted spec content.
- Capture `projectFolder` and `featureShortName`.
- If approval status is unclear, ask before producing final design.
- If the approved spec's Language section or UX scope indicates Avalonia or cross-platform desktop UI, activate `nf-avalonia`.

2. Extract implementation requirements
- Map each in-scope requirement to architecture, data, error, and testing impacts.
- Identify gaps and unresolved decisions as explicit Open Decisions.
- For Avalonia features, include view/viewmodel boundaries, window/dialog flow, threading concerns, styling/resources, and platform adapters in the extracted requirements.

3. Produce sectioned design
- Use the required sections and order from this skill.
- Fill file-by-file plan with concrete paths and change type (`new/modify/delete`).

4. Apply safety decisions explicitly
- Specify trusted vs untrusted data sources.
- Define error taxonomy and retry policy.
- Define query safety classes and required guardrails.

5. Write output file
- Default output path: `<projectFolder>/_localnotes/<featureShortName>/design.md`.
- Create missing directories before writing.
- Allow filename override if requested.

## Required Sections

Always include these sections in this exact order:

1. Spec Snapshot
2. Scope Mapping
3. Architecture Slice
4. Data Source Trust Matrix
5. Validation and Invariants
6. Query Safety Matrix
7. Error Taxonomy
8. File-by-File Implementation Plan
9. Contracts
10. State and Migration Plan
11. Config and Feature Flags
12. Observability Plan
13. Security and Permissions
14. Performance and Capacity
15. Test Plan
16. Rollout and Backout
17. Open Decisions
18. Revision History

## Section Requirements

### Data Source Trust Matrix
- For each source, classify as `trusted-without-validation` or `validate-required`.
- Include rationale and compensating controls.

### Query Safety Matrix
- Classify queries as `safe`, `guarded`, or `forbidden`.
- For guarded queries, define mandatory controls (timeouts, row limits, indexes, filters, feature flags).

### Error Taxonomy
- Define clear error classes, retryability, user visibility, and logging severity.
- Map each class to API/CLI/UI behavior.

### File-by-File Implementation Plan
- Include concrete repository file paths.
- For each file, include: purpose, change type, dependencies, and order.
- Avoid vague “update service layer” statements.

### Rollout and Backout
- Include rollout stages, success criteria, and rollback triggers.
- Include how to disable feature quickly (flag/config kill switch) where applicable.

## Output Convention

- Directory: `_localnotes/<featureShortName>/`
- Default file: `design.md`
- Allowed alternatives: any user-provided `.md` filename in same directory

## Quality Gate

Before finalizing, verify all checks pass:

- All required sections exist and are non-empty.
- Every file change item contains path + change type + purpose.
- Trust matrix covers every external/internal data source used by the design.
- Query safety matrix covers all non-trivial reads/writes.
- Error taxonomy includes retryability and user-facing behavior.
- Test plan maps back to scope requirements.
- Open Decisions captures unresolved blockers with owner.

If any check fails, fix it before returning the design.
