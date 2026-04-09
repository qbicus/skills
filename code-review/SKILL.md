---
name: code-review
description: "Review code changes across five dimensions: correctness, security, architecture, observability, and tests. Use when a user asks for `/code-review`, a PR review, a commit review, a diff review, a bug-risk scan, a security-focused review, or a \"review and fix\" pass on current repository changes."
---

# Code Review

Review code with a low-noise, context-aware workflow. Validate each candidate finding against the actual codebase before reporting or fixing it.

Use the structure in [references/review-template.md](references/review-template.md) when a written review artifact or a consistent response shape would help.

## Workflow

1. Establish review scope
- Determine whether the review target is a diff, a branch, specific files, or the whole feature area.
- Prefer the smallest scope that answers the request.
- If the user did not explicitly ask for review-only, assume code changes are allowed.

2. Run a first-pass review across all five dimensions
- Check correctness for broken behavior, contract mismatches, invalid assumptions, state bugs, race conditions, and edge cases.
- Check security for auth/authz gaps, injection risk, path traversal, secret exposure, unsafe deserialization, trust-boundary mistakes, and missing validation.
- Check architecture for layering violations, tight coupling, missing abstractions, backward-compatibility breaks, and rollout or migration hazards.
- Check observability for missing logs, poor error context, absent metrics, weak tracing hooks, and failures that would be hard to detect in production.
- Check tests for missing regression coverage, untested edge cases, weak assertions, and test changes that no longer match behavior.

3. Validate every candidate finding in context
- Re-read the relevant code before keeping a finding.
- Ask: `Is this actually a problem in this codebase, with these constraints, right now?`
- Drop findings that are speculative, stylistic, already handled elsewhere, or irrelevant to the requested scope.
- Keep only findings with a concrete failure mode, risk, or maintainability cost.

4. Prioritize validated issues
- Fix high-confidence correctness and security problems first.
- Fix architecture, observability, and test gaps when they materially improve safety or maintainability.
- Do not churn code for minor style preferences unless the repository clearly requires it.

5. Apply fixes by default
- Implement fixes directly unless the user asked for review-only or no edits.
- Keep fixes minimal, local, and compatible with surrounding patterns.
- Add or update tests when behavior changes or regression coverage is missing.
- Add observability improvements only where they provide operational value; avoid log spam.

6. Verify after each fix set
- Run focused tests, builds, or linters when feasible.
- If full verification is expensive, run the narrowest command that gives confidence and state what was not run.
- Re-open the touched code and review the final result, not just the original bug.

7. Re-review until clean or blocked
- Perform another review pass on the updated code.
- Continue until no validated findings remain, or stop at a real blocker such as missing requirements, failing infrastructure, or unclear intended behavior.

## Review Standards

### Correctness
- Favor issues that can break runtime behavior, data integrity, API contracts, or state transitions.
- Look for boundary conditions, null handling, ordering bugs, partial updates, concurrency hazards, and incorrect defaults.

### Security
- Treat all external input as untrusted unless the code proves otherwise.
- Verify authorization checks happen at the correct boundary, not only in the UI or caller.
- Prefer concrete exploit paths over vague "possible vulnerability" language.

### Architecture
- Focus on structural issues that will cause repeated mistakes, not personal taste.
- Flag hidden coupling, policy leakage across layers, incompatible schema changes, and features that cannot be rolled back safely.

### Observability
- Ensure production failures can be detected and diagnosed.
- Prefer actionable telemetry: stable log messages, relevant context, bounded cardinality, and coverage for critical failure paths.

### Tests
- Require tests for bug fixes and non-trivial behavior changes unless there is a strong reason not to.
- Prefer tests that would fail before the fix and pass after it.

## Output Rules

- If the user asked for review-only, present findings first, ordered by severity, with concrete file references and a short explanation of impact.
- If fixes were applied, summarize the fixes, verification performed, and any residual risks or blockers.
- State explicitly when no validated findings remain.
- If verification could not be completed, say exactly what was not run.

## Noise Filters

- Do not report hypothetical issues without a concrete path to failure.
- Do not demand refactors unless the current shape creates material risk.
- Do not ask for tests that merely restate implementation details without improving regression protection.
- Do not treat absent observability as a bug unless the code path matters operationally.
