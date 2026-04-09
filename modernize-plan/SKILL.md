---
name: modernize-plan
description: "Turn an approved `modernize-eval` outcome into an execution-ready modernization plan for refactor, migration, phased replacement, or rewrite work on an existing system. Use when a user asks for `/modernize-plan`, wants a modernization execution plan, or needs sequencing, rollback, verification, and ordered tasks after a modernization recommendation is approved."
---

# Modernize Plan

Plan modernization work for an existing system. Use the approved `modernize-eval` output as the starting point and produce an execution-ready plan that makes compatibility risks, rollback, verification, and task sequencing explicit.

Use the template in [references/modernize-plan-template.md](references/modernize-plan-template.md) unless the user requests a different format.

## Workflow

1. Confirm inputs
- Require an approved `modernize-eval` report path or pasted content.
- Capture `projectFolder` and `projectShortName`.
- If the evaluation recommendation or approval status is unclear, ask before producing the final plan.

2. Define baseline and target
- Summarize the current-state baseline from the evaluation.
- Make the target state explicit: framework/runtime, dependency posture, hosting/deployment assumptions, and intended non-goals.
- Preserve the evaluation boundary; do not silently expand scope.

3. Map compatibility and risk surfaces
- Enumerate framework, package, hosting, configuration, auth, serialization, data-access, and integration breaking changes.
- Identify the areas where modernization can fail operationally even if code compiles.
- Separate hard blockers from manageable risks.

4. Design the modernization path
- Choose a sequencing model: direct migration, phased migration, strangler, module-by-module refactor, or other approved path.
- Define prerequisite work, migration waves, and safe cut points.
- Make rollback and verification part of the plan, not afterthoughts.

5. Produce the execution plan
- Build an ordered, testable execution plan with explicit dependencies.
- Include task-level acceptance checks and verification evidence.
- Call out tasks that can run in parallel only when they are truly independent.
- Treat `modernize-plan.md` as a living execution artifact by including status-aware execution tracking.

6. Write output file
- Default output path: `<projectFolder>/_localnotes/<projectShortName>/modernize-plan.md`.
- Create missing directories before writing.
- Allow filename override if requested.

## Required Sections

Always include these sections in this exact order:

1. Evaluation Snapshot
2. Current-State Baseline
3. Target-State Definition
4. Compatibility and Breaking Change Inventory
5. Dependency Upgrade Matrix
6. Architecture and Code Impact Areas
7. Data and Integration Impact
8. Environment and Deployment Impact
9. Migration Strategy and Sequencing
10. Verification Strategy
11. Rollback and Safety Controls
12. Ordered Execution Plan
13. Execution Status
14. Risks and Mitigations
15. Open Decisions
16. Revision History

## Section Requirements

### Evaluation Snapshot
- Reference the approved `modernize-eval` input.
- Include the recommended strategy, confidence, and the three modernization scores.

### Current-State Baseline
- State the current framework/runtime, dependency posture, build/test state, deployment model, and major known constraints.

### Target-State Definition
- State the target framework/runtime, intended dependency posture, hosting model, and explicit non-goals.

### Compatibility and Breaking Change Inventory
- List major compatibility risks with severity, affected area, and required action.
- Include both compile-time and runtime/operational break surfaces.

### Dependency Upgrade Matrix
- For each important dependency, list current version, target version, compatibility notes, blockers, and required upgrade order.

### Architecture and Code Impact Areas
- Identify which layers, modules, entry points, or services need change and why.
- Avoid vague “update app to latest framework” summaries.

### Data and Integration Impact
- Cover databases, caches, queues, search, third-party APIs, and internal service contracts.
- Call out compatibility or migration sequencing constraints.

### Environment and Deployment Impact
- Include local/dev/test/prod differences, config changes, secret handling, hosting/runtime changes, and release implications.

### Migration Strategy and Sequencing
- Define phases or waves, critical path, safe cut points, and what can or cannot be parallelized.

### Verification Strategy
- Map verification directly to risky surfaces.
- Include build, automated test, regression, smoke, and environment validation as applicable.

### Rollback and Safety Controls
- Define backout steps, irreversible actions, guardrails, and kill-switch or deployment-stop conditions where relevant.

### Ordered Execution Plan
- Use stable IDs: `M001`, `M002`, ...
- For each item include: objective, files/areas touched, dependencies, execution mode, worker slot, status, acceptance check, and verification evidence.
- Keep tasks implementation-ready.

### Execution Status
- Include a progress summary with `completed`, `in-progress`, `blocked`, and `not-started` counts.
- Track active worker assignments or batch summaries when parallel execution is in use.
- Use only these statuses: `not-started`, `in-progress`, `blocked`, `done`.
- Update this section during execution so modernization work can pause and resume safely across sessions.

### Risks and Mitigations
- Include likelihood, impact, mitigation, and owner.

### Open Decisions
- Capture unresolved blockers with owner and due date when possible.

## Output Convention

- Directory: `_localnotes/<projectShortName>/`
- Default file: `modernize-plan.md`
- Allowed alternatives: any user-provided `.md` filename in the same directory

## Quality Gate

Before finalizing, verify all checks pass:

- `modernize-eval` input is referenced.
- Current and target state are both explicit.
- Breaking changes are enumerated.
- Dependency upgrade order is concrete.
- Rollback is defined.
- Ordered execution items are testable and dependency-aware.
- Ordered execution items include status-aware tracking suitable for execution or `parallel-exec`.
- Verification maps to risky areas.
- Open decisions are explicit.

If any check fails, fix it before returning the modernization plan.
