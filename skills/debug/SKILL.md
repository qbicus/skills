---
name: debug
description: "Debug failures with a logs-first workflow that reads production logs, runtime errors, and build logs before proposing code changes. Use when a user asks for `/debug`, wants disciplined root-cause analysis, is dealing with production failures, flaky behavior, crashes, or build/test/package failures."
---

# Debug

Start with evidence, not code edits. Read logs first, identify patterns, narrow the failure mode, and only then inspect or change code.

Use the structure in [references/debug-template.md](references/debug-template.md) when a written investigation record or consistent response shape would help.

## Workflow

1. Identify the failure surface
- Determine whether the issue is a production/runtime problem, a build/test/package failure, or both.
- Ask for or locate the relevant logs before suggesting fixes.
- If no logs are available, say that clearly and treat missing evidence as a blocker or uncertainty.

2. Read logs before code
- For production/runtime issues, inspect production logs, stack traces, error reports, and recent failure windows first.
- For build failures, inspect build logs, compiler output, test runner output, and packaging/deploy logs first.
- Pull the smallest useful log slice that still shows the failure pattern, not just one isolated line.

3. Extract failure patterns
- Look for repeated error signatures, timestamps, affected components, correlation IDs, environment clues, and the first meaningful failure.
- Separate primary failures from cascaded noise.
- Note whether the pattern is deterministic, intermittent, input-specific, environment-specific, or time-window-specific.

4. Narrow the problem before editing
- Form one or more evidence-backed hypotheses.
- Map each hypothesis to the likely component, code path, config surface, or dependency boundary.
- Prefer the earliest failing point over later symptoms.
- If the logs point to configuration, environment, or data issues, do not jump straight to code fixes.

5. Inspect the relevant code only after log analysis
- Read only the code paths implicated by the log evidence and hypotheses.
- Verify whether the code can actually produce the observed failure.
- Drop hypotheses that do not fit the evidence.

6. Fix only after the failure mode is understood
- Propose or apply the smallest change that addresses the validated root cause.
- If the issue is not a code problem, say so directly and recommend the correct operational/configuration action.
- For build failures, prefer fixes at the earliest compilation or contract mismatch point rather than patching downstream errors.

7. Verify against the original evidence
- Re-run the relevant build, test, or focused verification path when feasible.
- Confirm that the original log pattern is resolved or would be prevented by the change.
- State what was verified and what remains unverified.

## Evidence Rules

- Do not suggest code changes before reading the relevant logs unless the user explicitly forbids log inspection.
- Do not anchor on the first theory; let the logs narrow the search space.
- Do not confuse repeated downstream exceptions with the root cause.
- Prefer exact failure signatures, timestamps, and components over vague summaries.
- When build logs are involved, find the first real error and treat later failures as suspect until proven otherwise.

## Output Rules

- Start with the observed evidence and failure pattern.
- Then state the narrowed hypothesis or root cause.
- Then state the recommended or applied fix.
- Include verification results and remaining uncertainties.
- If logs were missing or incomplete, say that explicitly.

## Quality Gate

Before finalizing, verify all checks pass:

- Relevant production or build logs were read first when available.
- The response distinguishes evidence from hypothesis.
- The suspected root cause matches the observed log pattern.
- Any code change is justified by the narrowed failure mode.
- Verification addresses the original failure, not only nearby code.

If any check fails, fix it before returning the debugging result.
