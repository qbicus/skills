---
name: nf-tasks
description: Generate task plans for the `new-feature` workflow from approved technical designs by breaking work into small, ordered implementation tasks and applying a comprehensive quality checklist. Use when a user asks for `/nf-tasks`, needs the task-planning stage of `new-feature`, or wants task breakdowns, implementation sequencing, delivery checklists, or mistake-prevention guardrails before coding.
---

# NF Tasks

Produce an implementation todo plan that teams can execute safely and incrementally.

Use the template in [references/dev-todos-template.md](references/dev-todos-template.md) unless the user requests a different format.

## Workflow

1. Confirm inputs
- Require an approved design doc path or pasted content.
- Capture `projectFolder` and `featureShortName`.
- Read the approved spec's `Parallel Execution Preference` before assigning task groups.

2. Decompose into tasks
- Break design into small, ordered tasks with explicit dependencies.
- Keep tasks implementation-ready and scoped to single outcomes.
- Mark tasks as sequential-only or parallel-safe based on dependencies, shared touchpoints, and the approved maximum parallel agent count from the spec.
- When parallel work is safe, group tasks into explicit parallel batches and assign agent slots such as `Agent 1`, `Agent 2`, up to the approved maximum.
- Treat `dev-todos.md` as a living execution tracker, not only a planning artifact.

3. Apply quality checklist
- Run the full checklist before finalizing.
- Convert failing checks into explicit todo items.

4. Write output file
- Default output path: `<projectFolder>/_localnotes/<featureShortName>/dev-todos.md`.
- Create missing directories before writing.
- Allow filename override when requested.

## Required Sections

Always include these sections in this exact order:

1. Design Snapshot
2. Delivery Strategy
3. Ordered Task List
4. Execution Status
5. Dependency Notes
6. Quality Checklist
7. Risks and Mitigations
8. Test and Verification Plan
9. Done Criteria
10. Open Questions
11. Revision History

## Section Requirements

### Ordered Task List
- Use stable IDs: `T001`, `T002`, ...
- For each task include: objective, files/services touched, dependencies, execution mode, parallel batch, agent slot, status, and acceptance check.
- Keep each task small enough for one focused implementation pass.

### Execution Status
- Include a compact progress view with `completed`, `in-progress`, `blocked`, and `not-started` counts.
- Track per-task status using only: `not-started`, `in-progress`, `blocked`, `done`.
- Include a short active-work summary such as `working on T004` or `parallel batch P2 active: T004, T005`.
- Update this section and the task table during execution so the file stays resumable across sessions.

### Delivery Strategy
- State whether execution is `sequential-only` or `parallel-eligible`.
- If parallel-eligible, include the approved maximum agent count from the spec and summarize which batches can run concurrently.

### Quality Checklist
- Use the expanded checklist from [references/dev-todos-template.md](references/dev-todos-template.md).
- Mark each item `pass/fail/n-a`.
- Add remediation todo items for each `fail`.

### Test and Verification Plan
- Map verification steps directly to tasks and risk areas.
- Include unit, integration, and end-to-end verification where applicable.

## Output Convention

- Directory: `_localnotes/<featureShortName>/`
- Default file: `dev-todos.md`
- Allowed alternatives: any user-provided `.md` filename in same directory

## Quality Gate

Before finalizing, verify all checks pass:

- All required sections exist and are non-empty.
- Ordered tasks cover all in-scope design requirements.
- Every task has dependency and acceptance criteria.
- Every task has an execution status.
- Parallel-safe tasks are explicitly marked, and no parallel group exceeds the approved maximum agent count from the spec.
- Checklist includes explicit `pass/fail/n-a` status per item.
- Every failed check has a remediation task.
- Done criteria are measurable and testable.

If any check fails, fix it before returning the todo plan.
