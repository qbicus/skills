# New Feature

Purpose: run a gated feature-delivery workflow from idea to implementation.

Chain:
- `nf-spec`
- approval
- `nf-design`
- `advisor:plan` when substantial
- approval
- `nf-tasks`
- approval
- execution
- `advisor:complete` before substantial work is declared done

Also uses:
- `decision` for important decisions
- `nf-avalonia` when the feature includes Avalonia or cross-platform desktop UI

Default behavior:
- do not skip approvals
- pause and fall back to the earliest invalidated stage when scope or design changes
- update `dev-todos.md` during execution so work can pause and resume across sessions
- record and carry `substantial: true|false` from the spec
- use provider-neutral roles (`primary`, `executor`, `researcher`, `advisor`, `fast`)
- invoke `advisor:stuck` when the configured repeated-failure threshold is reached
- use `parallel-exec` only when approved parallel execution is chosen

Example prompts:
- `Use $new-feature for customer-import and start from nf-spec.`
- `Use $new-feature for customer-import. The spec in _localnotes/customer-import/specs.md is approved. Continue with nf-design.`
- `Use $new-feature for customer-import. The design in _localnotes/customer-import/design.md is approved. Generate nf-tasks.`
- `Use $new-feature for customer-import. The task plan in _localnotes/customer-import/dev-todos.md is approved. Start execution.`
- `Use $new-feature for customer-import. Resume from task execution and continue with the remaining approved tasks.`
- `Use $new-feature for customer-import. Resume execution from _localnotes/customer-import/dev-todos.md. Completed: T001, T002. In progress: T003. Continue from the remaining approved tasks.`
- `Use $new-feature for customer-import. The task plan is parallel-eligible and approved. Start execution with parallel-exec using 3 workers.`
