# Modernize Plan

Purpose: turn an approved `modernize-eval` result into an execution-ready modernization plan.

Use it when you want:
- a concrete plan for migration, refactor, phased replacement, or rewrite work
- breaking changes, rollback, and verification made explicit
- ordered modernization tasks from an approved evaluation

Default behavior:
- requires `modernize-eval` input
- produces current-state vs target-state planning
- includes sequencing, risks, rollback, verification, and ordered execution tasks
- keeps `modernize-plan.md` status-aware so it can be executed sequentially or via `parallel-exec`

Example prompts:
- `Use $modernize-plan with the approved modernize-eval report in _localnotes/app-a/modernize-eval.md and build an execution plan.`
- `Use $modernize-plan to turn the approved .NET Core 3 to .NET 8 evaluation into a phased upgrade plan with rollback and verification.`
- `Use $modernize-plan for project-x. The evaluation in _localnotes/project-x/modernize-eval.md is approved. Create the modernization plan.`
- `Use $modernize-plan for project-x. The plan in _localnotes/project-x/modernize-plan.md is approved. Start executing the remaining modernization tasks in order.`
- `Use $parallel-exec with _localnotes/project-x/modernize-plan.md and execute the next approved parallel-safe modernization batch with 2 workers.`
