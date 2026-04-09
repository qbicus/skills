---
name: nf-spec
description: Write and maintain feature specifications for the `new-feature` workflow with a fixed 12-section core structure, plus a recommended Language section, and strict contract checks between API/data fields and shared types. Use when a user asks for `/nf-spec`, needs the spec stage of `new-feature`, or wants implementation-ready requirements, API contract documentation, validation/error rules, phased rollout plans, or revision updates to an existing spec.
---

# NF Spec

Produce implementation-ready feature specs with deterministic section coverage and consistency checks.

Use the template in [references/spec-template.md](references/spec-template.md) unless the user requests a different format.

## Workflow

1. Collect missing inputs
- Ask only for details that block correctness: feature goal, user roles, core entities, API surface, constraints, and rollout expectations.
- Ask for `projectFolder` and `featureShortName` if not already provided.
- Ask for preferred maximum parallel agent count only when the feature can plausibly be split into independent workstreams; otherwise default to `1`.
- If the feature includes Avalonia or cross-platform desktop UI, activate `nf-avalonia` and capture the required desktop UX, platform targets, and packaging expectations.

2. Draft all required sections
- Use the exact section names and order from "Required Sections".
- Keep content concrete and testable.
- Include "Language" by default unless the user explicitly opts out.

3. Enforce contract consistency
- Ensure every data field is labeled `required` or `optional`.
- Ensure labels are consistent across Data Model, Shared Types, API Endpoints, and Validation Rules.
- If uncertain, call out uncertainty in Open TODOs instead of guessing.

4. Add revision entry
- Append a new row in Revision History for every spec update.

5. Write output file
- Default output path: `<projectFolder>/_localnotes/<featureShortName>/specs.md`.
- Create missing directories before writing.
- Allow filename override when the user asks (for example `feature-spec.md`).
- If `projectFolder` is not given, use current working directory.

## Output Convention

- Directory: `_localnotes/<featureShortName>/`
- Default file: `specs.md`
- Allowed alternatives: any user-provided `.md` filename in the same directory
- Do not write outside `projectFolder` unless explicitly requested.

## Required Sections

Always include these 12 sections in this exact order:

1. Problem Statement
2. Design Decisions and Rejected Alternatives
3. Data Model
4. Shared Types
5. API Endpoints
6. Validation Rules and Boundary Values
7. Error Responses
8. UX Flows
9. Phasing
10. Out of Scope
11. Open TODOs
12. Revision History

## Recommended Section

Include this section by default between Shared Types and API Endpoints. If included, total sections become 13.

5. Language

When users explicitly request omission, skip this section and keep the 12-section core.

## Section Requirements

### Data Model

- List every entity and field.
- For each field, explicitly mark `required` or `optional`.
- Include type, constraints, and default behavior.

### Shared Types

- Define canonical request/response/domain types used by multiple components.
- Keep required/optional markers aligned with Data Model.

### Language (recommended)

- Capture implementation technology choices in a compact matrix.
- For each area, state `yes/no` plus selected variant when applicable.
- Use this shape unless the user asks for a custom format:
  - `UI: native|avalonia|no`
  - `SQL: yes/no + engine (mssql|pgsql|mysql|...)`
  - `HTML: yes/no`
  - `CSS: yes/no + style system (css|scss|...)`
  - `JS: yes/no + variant (vanilla|jquery|ts|...)`
- If `UI` is `avalonia`, apply `nf-avalonia` guidance while defining UX flows, platform targets, and desktop-specific constraints.

### API Endpoints

- If the solution includes callable service interfaces (HTTP/RPC/etc), specify method, path, purpose, auth, request body/query/path schema, success response, and error cases.
- For each request/response field, mark `required` or `optional`.
- If the solution is non-service (for example console app, desktop UI app, batch script, CLI utility), keep the section and state: `No API endpoints needed for this implementation`, plus a short reason.

### Validation Rules and Boundary Values

- Include both valid and invalid boundary examples.
- Tie each validation rule to relevant fields and endpoint behavior.

### Error Responses

- Define machine-readable error codes and HTTP statuses.
- Include trigger condition and client-facing message guidance.

### UX Flows

- Describe primary path, empty/error states, and recovery steps.
- Map UX behavior to API and validation outcomes where relevant.

### Phasing

- Split into incremental phases with entry/exit criteria.
- Note migration or compatibility risks per phase.
- Include a `Parallel Execution Preference` subsection stating whether parallel implementation is feasible, the approved maximum agent count, and the constraints that limit safe parallelism.

### Open TODOs

- Keep unresolved decisions explicit with owner and decision deadline when possible.

### Revision History

- Maintain chronological entries: date, author, summary, and impacted sections.

## Quality Gate

Before finalizing, verify all checks pass:

- All 12 required sections exist and are non-empty.
- Language section is present unless the user explicitly opted out.
- Every mentioned field has `required` or `optional`.
- No required/optional mismatches between Data Model, Shared Types, and API Endpoints when APIs are applicable.
- API Endpoints section explicitly declares `No API endpoints needed for this implementation` when non-service.
- Validation rules cover boundary conditions for constrained fields.
- Error responses exist for validation failures and major domain failures.
- Phasing includes a clear parallel execution preference with either a justified agent count greater than `1` or an explicit `1` when work should stay sequential.
- Open TODOs capture unresolved ambiguities.

If any check fails, fix it before returning the spec.
