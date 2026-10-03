# Parallel Exec

Purpose: run approved parallel-safe tasks with explicit worker assignment and live status tracking.

Use it when you want:
- true parallel execution from an approved task plan
- worker slots assigned to independent tasks
- shared status updates and merge checkpoints after each batch

Default behavior:
- requires an approved status-aware execution artifact
- only runs dependency-ready tasks explicitly approved as parallel-safe; it never auto-enables parallelism
- keeps worker scope bounded and escalates `NEEDS_DECISION` / `NEEDS_RESEARCH` instead of silently expanding the plan
- updates the shared task artifact as work progresses

Example prompts:
- `Use $parallel-exec with _localnotes/customer-import/dev-todos.md and execute the next approved parallel-safe batch with 3 workers.`
- `Use $parallel-exec with _localnotes/app-a/modernize-plan.md and run the next eligible modernization batch with 2 workers.`
