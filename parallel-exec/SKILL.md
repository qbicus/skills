---
name: parallel-exec
description: "Execute approved, dependency-ready, parallel-safe tasks using multiple worker slots with live status tracking and merge checkpoints. Use when a user asks for `/parallel-exec`, wants real parallel execution from an approved `dev-todos.md` or `modernize-plan.md`, or needs worker assignment, batch safety, and progress tracking for independent tasks."
---

# Parallel Exec

Orchestrate real parallel task execution from an approved task artifact. Only run tasks in parallel when they are explicitly marked safe, dependency-ready, and non-conflicting.

Use the structure in [references/parallel-exec-template.md](references/parallel-exec-template.md) when a written execution plan or live batch summary would help.

## Workflow

1. Confirm execution input
- Require an approved execution artifact such as `dev-todos.md` or `modernize-plan.md`.
- Confirm the user chose parallel execution and provide or infer the allowed worker count.
- Read current task statuses before assigning any worker.

2. Select an eligible batch
- Only select tasks marked `parallel-safe`.
- Only select tasks whose dependencies are already `done`.
- Exclude tasks already marked `done`, `blocked`, or actively owned by another worker unless the user explicitly wants recovery.
- Exclude tasks with conflicting touchpoints, shared schema risk, shared contract risk, shared deployment/config risk, or other unsafe overlap.

3. Assign workers
- Map selected tasks to `Agent 1..N`.
- Record the assignment in the execution artifact's status section or worker summary.
- Keep each worker scoped to a single approved task unless the artifact explicitly defines a batch-level unit.

4. Execute in isolated worker slots
- Each worker performs only its assigned task.
- Each worker reports:
  - task ID
  - files/areas touched
  - verification run
  - resulting status: `done` or `blocked`
- Mark task status `in-progress` before execution begins.

5. Merge and checkpoint
- After each parallel batch, merge the results back into the shared execution artifact.
- Update task statuses, completed/blocked counts, and active batch summary.
- Surface conflicts, integration work, or plan invalidation immediately.

6. Continue or stop
- If more dependency-ready parallel-safe work exists, start the next batch.
- If only sequential work remains, hand control back to the normal execution path.
- If a task invalidates spec/design/task assumptions, stop and escalate to the appropriate approval gate instead of continuing.

## Parallel Eligibility Rules

- Do not parallelize tasks that touch the same files unless the plan explicitly allows it and the merge risk is understood.
- Do not parallelize shared schema, migration, API contract, deployment, or common resource-dictionary changes casually.
- Do not parallelize work whose acceptance depends on another incomplete task in the same batch.
- Prefer smaller safe batches over larger risky batches.

## Worker Execution Contract

- A worker may act only within its assigned task scope.
- A worker must not expand scope because “it was nearby.”
- A worker must report when the task becomes blocked instead of silently changing plan shape.
- A worker must run the verification expected by the task before claiming `done`, unless blocked by a clearly stated reason.

## Status Update Rules

- Update the shared artifact live with:
  - current worker assignments
  - per-task status
  - batch summary
  - completed, in-progress, blocked, and remaining counts
- Use only these task statuses: `not-started`, `in-progress`, `blocked`, `done`.
- Never leave a task implicitly active; if a worker stops, the artifact must show whether the task is still `in-progress` or has moved to `blocked`.

## Conflict Detection Rules

- Stop the batch if workers overlap on shared contracts, schema, or deployment-critical files in an unsafe way.
- Stop the batch if one worker's result invalidates another worker's task assumptions.
- Escalate if the approved execution artifact is no longer sufficient for safe continuation.

## Output Rules

- Show worker assignment at batch start, for example:
  - `Agent 1 -> T004`
  - `Agent 2 -> T005`
- Show a live visual status summary after each checkpoint, for example:
  - `done: T004 | working: T005 | blocked: none | remaining: T006, T007`
- State when control should return to sequential execution because no safe parallel batch remains.

## Quality Gate

Before finalizing or launching the next batch, verify all checks pass:

- The execution artifact is approved and status-aware.
- Every task in the current batch is marked `parallel-safe`.
- Dependencies are satisfied for every assigned task.
- No unsafe overlap exists between worker scopes.
- The shared artifact was updated with current statuses and assignments.
- Any blocked or invalidating condition was surfaced explicitly.

If any check fails, stop the batch or reduce it before continuing.
