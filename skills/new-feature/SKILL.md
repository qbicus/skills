---
name: new-feature
description: "Drive a new feature through a mandatory staged workflow covering `nf-spec`, approval, `nf-design`, approval, `nf-tasks`, approval, and only then execution. Use when a user asks for `/new-feature`, wants disciplined feature delivery, or needs protection against skipping planning and starting implementation too early."
---

# New Feature

Enforce a gated delivery process for new work. Do not skip stages, do not start coding until the task-plan approval gate is explicitly passed, and keep a running decision log for important choices made along the way.

## Workflow

1. Establish feature identity
- Capture or confirm `projectFolder` and `featureShortName`.
- Clarify the feature goal only if missing details block the spec.
- Treat the request as a net-new delivery flow unless the user clearly says this is only a revision to an existing stage artifact.
- Use the same `projectFolder` and `featureShortName` for the `decision` log at `<projectFolder>/_localnotes/<featureShortName>/decisions.md`.
- If the feature includes Avalonia or cross-platform desktop UI, activate `nf-avalonia` as a supporting skill throughout spec, design, task planning, and execution.

2. Run `nf-spec`
- Produce the specification using the `nf-spec` skill.
- If the feature uses Avalonia, apply `nf-avalonia` guidance while drafting the spec.
- Write the spec to `<projectFolder>/_localnotes/<featureShortName>/specs.md` unless the user requests another filename.
- Capture a `Parallel Execution Preference` in the spec: ask for preferred maximum parallel agents only when the work can plausibly be decomposed safely; otherwise record `1`.
- Do not continue automatically after drafting.

3. Stop for spec approval
- Ask for explicit approval of the spec.
- Accept only clear approval language such as `approved`, `approve spec`, or an unambiguous revision request followed by final approval.
- If feedback is given, revise the spec and ask again.
- Do not begin `nf-design` until spec approval is explicit.
- After spec approval, log any material product or scope decisions using the `decision` skill.

4. Run `nf-design`
- Produce the implementation design using the approved spec and the `nf-design` skill.
- If the approved spec indicates Avalonia or cross-platform desktop UI, apply `nf-avalonia` guidance while drafting the design.
- Write the design to `<projectFolder>/_localnotes/<featureShortName>/design.md` unless the user requests another filename.
- Keep the design traceable to the approved spec; do not introduce hidden scope expansion.

5. Stop for design approval
- Ask for explicit approval of the design.
- If the user requests changes that only affect implementation approach, update the design and ask again.
- If the requested change alters approved requirements, scope, user-visible behavior, core entities, contracts, or validations, return to `nf-spec`, revise it, get spec approval again, then regenerate design and re-run downstream stages.
- Do not create tasks and do not code until design approval is explicit.
- After design approval, log any material architecture, data-flow, interface, migration, security, or observability decisions using the `decision` skill.

6. Run `nf-tasks` as the task stage
- Treat `nf-tasks` as the required tasks phase for this workflow.
- Produce the task plan from the approved design.
- If the approved design includes Avalonia UI work, apply `nf-avalonia` guidance while generating UI-related task slices and dependencies.
- Require the task plan to mark `sequential-only` vs `parallel-safe` tasks, define any parallel batches, and assign `Agent 1..N` slots without exceeding the approved maximum from the spec.
- Write the task plan to `<projectFolder>/_localnotes/<featureShortName>/dev-todos.md` unless the user requests another filename.

7. Stop for task-plan approval
- Ask for explicit approval of the task plan.
- If the user asks to "just start coding" before this approval, refuse and point back to the required process.
- If the requested change only affects sequencing, batching, rollout ordering, or task decomposition, revise the task plan and ask again.
- If the requested change alters implementation approach or architecture, return to `nf-design`, revise it, get design approval again, then regenerate the task plan.
- If the requested change alters requirements, scope, user-visible behavior, core entities, contracts, or validations, return to `nf-spec`, revise it, get spec approval again, then regenerate design and the task plan.
- After task-plan approval, log any material sequencing, rollout, or risk-management decisions using the `decision` skill.

8. Execute only after approval
- Start implementation only after spec, design, and task-plan approvals are all explicit.
- Before execution, tell the user whether the approved task plan is `sequential-only` or `parallel-eligible`.
- If the plan is `parallel-eligible`, ask whether to execute in parallel or one task at a time. Do not exceed the approved maximum agent count from the spec.
- If the user chooses sequential execution, implement in task order.
- If the user chooses parallel execution, hand batch orchestration to `parallel-exec` and run only approved parallel-safe batches concurrently while preserving dependency order between batches.
- Update `dev-todos.md` during execution to mark tasks `in-progress`, `blocked`, or `done`.
- Treat execution as resumable: a later session should continue from the remaining approved tasks recorded in `dev-todos.md`.
- If the approved work includes Avalonia UI, keep `nf-avalonia` active during implementation.
- After implementation, verify with the narrowest useful tests/build commands and report what was or was not run.
- During execution, append a `decision` entry whenever an implementation choice materially changes behavior, contracts, architecture, storage, rollout, operability, or testing strategy.
- If execution reveals a change that affects only task sequencing, return to `nf-tasks` approval.
- If execution reveals a change that affects implementation approach or architecture without changing approved requirements, return to `nf-design` approval and then re-run `nf-tasks`.
- If execution reveals a change that affects requirements, scope, user-visible behavior, core entities, contracts, or validations, return to `nf-spec` approval and then re-run all downstream stages.

## Decision Logging Rules

- Use the `decision` skill to append to `<projectFolder>/_localnotes/<featureShortName>/decisions.md`.
- Log decisions that future sessions would struggle to reconstruct from code alone.
- Do not log trivial mechanical edits, obvious refactors, or choices fully dictated by the approved artifacts.
- When a previously approved direction changes, add a new decision entry explaining the change and note which prior decision it supersedes.
- If a new implementation decision invalidates approved spec, design, or task assumptions, pause execution and return to the appropriate approval gate.

## Enforcement Rules

- Do not merge stages into one response when approval is still pending.
- Do not treat silence, impatience, or "looks fine" in another context as approval; get explicit confirmation tied to the current stage.
- Do not let the user skip directly from idea to design, tasks, or code unless they explicitly instruct you to abandon this workflow.
- If the user wants to bypass the process, state that the `new-feature` skill is designed to prevent that shortcut and ask whether they want to exit the skill-driven flow.
- If an upstream artifact changes after approval, return to the affected stage and re-run downstream stages that depend on it.
- Use the earliest invalidated stage rule: go back to `nf-spec` for requirement changes, `nf-design` for implementation-approach changes, and `nf-tasks` for execution-plan-only changes.

## Output Rules

- At each stage, state the current gate clearly: `awaiting spec approval`, `awaiting design approval`, or `awaiting task-plan approval`.
- Reference the artifact path written for that stage.
- Reference `decisions.md` whenever a new decision entry is added.
- When execution begins, state that all three approvals have been received.
- During execution, show task progress with completed, active, blocked, and remaining tasks or batches.
- Include an explicit visual cue such as `done: T001, T002 | working: T003 | blocked: T004 | remaining: T005, T006`.
- When parallel batches are active, show the current work split by agent or batch and reference `parallel-exec` if it is orchestrating the batch.
- If execution is blocked because approval is missing, say so directly instead of partially implementing.
