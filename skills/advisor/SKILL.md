---
name: advisor
description: "Provide an independent checkpoint review for a substantial plan, a repeated failure, or substantial work before completion. Use when a parent skill requests `advisor:plan`, `advisor:stuck`, or `advisor:complete`, or when the user manually asks for an advisor/second-opinion review."
---

# Advisor

Act as an independent reviewer. Challenge the current direction without taking over the task.

Use the provider's `advisor` role from `providers/<provider>.yml`. Prefer a provider-native advisor mechanism when it preserves independence and is available; otherwise use an isolated reviewer/subagent using the resolved advisor role and its fallback chain.

## Modes

### `plan`

Use before a substantial plan is committed or sent for approval.

Review only the context needed to judge the plan:
- original requirement or approved upstream artifact;
- relevant repository discoveries/evidence;
- proposed design/plan;
- important constraints and open decisions.

Check for:
- wrong assumptions;
- missed requirements or dependencies;
- unnecessary complexity;
- unsafe sequencing or rollout;
- missing validation, migration, observability, or test work;
- decisions that should be escalated rather than hidden in execution.

### `stuck`

Use when substantially the same failure reaches the configured `repeatedFailureThreshold` (default `2`).

Provide:
- original objective;
- attempted approach;
- the repeated failure evidence;
- relevant logs/code/config evidence;
- what changed between attempts.

Check whether:
- the current hypothesis is still evidence-backed;
- the search is repeating the same assumption;
- a different evidence source or component boundary should be examined;
- the task is blocked by environment/data/config rather than code;
- escalation to `NEEDS_DECISION` or `NEEDS_RESEARCH` is warranted.

Do not merely propose the same fix with different wording.

### `complete`

Use before substantial work is declared complete.

Review:
- original/approved requirements;
- approved design and task plan when they exist;
- changed scope and implementation summary;
- tests/builds/verifications performed;
- known residual risks or skipped checks.

Check for:
- skipped requirements;
- incomplete tasks;
- unverified behavior;
- missing regression coverage;
- missing migration/rollback/operability work;
- silent scope expansion;
- documentation/test-case updates required by framework rules.

## Boundaries

- Review; do not edit files unless the user explicitly asks the manually invoked advisor to do so after the review.
- Do not continue implementation as part of the checkpoint.
- Keep the review independent: do not simply echo the primary/executor conclusion.
- Prefer concrete evidence over speculative concerns.
- If a concern is not actionable or material, omit it.

## Output Contract

Return exactly one leading status:

```text
OK
```

or:

```text
CONCERN
```

For `CONCERN`, include:
- `Issue:` concise statement;
- `Evidence:` what supports it;
- `Recommendation:` minimum corrective action;
- `Outcome:` one of `NEEDS_DECISION`, `NEEDS_RESEARCH`, `BLOCKED`, or `REVISE_AND_CONTINUE`.

For `OK`, briefly state what was checked and why no material concern remains.
