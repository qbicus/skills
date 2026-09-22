---
name: session-close
description: "Close a work session by summarizing progress, appending important implementation decisions via the `decision` skill, and recording blockers, open questions, and next steps for the next restart. Use when a user asks for `/session-close`, wants cross-session continuity, or is ending a work session and does not want context to be lost."
---

# Session Close

Capture the state of work at the end of a session so the next restart does not depend on memory. Use the `decision` skill for durable rationale and write a concise session summary for status, blockers, and next actions.

Use the structure in [references/session-close-template.md](references/session-close-template.md) unless the user asks for another format.

## Workflow

1. Identify the session scope
- Confirm `projectFolder` and `featureShortName` when the close-out is feature-specific.
- If the session spans multiple features or areas, produce one close-out that clearly separates them instead of collapsing everything into one undifferentiated note.

2. Append important decisions first
- Use the `decision` skill to log any material implementation, architecture, scope, rollout, or debugging decisions made during the session.
- Do not duplicate trivial edits in the decision log.
- If no material decisions were made, state that explicitly.

3. Write the session summary
- Default path: `<projectFolder>/_localnotes/<featureShortName>/session-close.md`.
- If the user wants a rolling journal instead, append a dated entry instead of overwriting.
- Record what was completed, what remains in progress, what is blocked, and the most important restart context.
- For features using `nf-tasks`, record completed tasks, in-progress tasks, blocked tasks, and remaining tasks using the current `dev-todos.md` state.
- For features using `parallel-exec`, record active worker assignments or the last known batch summary when relevant.
- If multiple features were active, include a separate status block for each feature.

4. Capture restart guidance
- List the next concrete actions in priority order.
- Reference relevant artifacts such as specs, designs, task plans, decision logs, failing tests, or debug evidence.
- Note any commands, environments, or credentials the next session will need.

5. Preserve unresolved risks
- Record blockers, uncertainties, failed verifications, and pending approvals.
- Say exactly what was not finished or not verified.

## Output Rules

- Keep the summary concise but specific enough for a cold restart days later.
- Include exact artifact paths when they matter.
- Prefer durable facts over narrative.
- If decisions were appended, reference `decisions.md` in the summary.
- When multiple features were active, make each feature's current stage and task status easy to scan.
- When parallel execution was active, include the last known agent/batch status if it matters for resuming safely.

## Quality Gate

Before finalizing, verify all checks pass:

- Material decisions were appended through the `decision` skill when applicable.
- The summary states completed work, in-progress work, blockers, and next steps.
- For active `new-feature` executions, completed, in-progress, blocked, and remaining tasks are captured per feature.
- For active parallel execution, worker or batch state is captured when relevant to safe resumption.
- Restart guidance is concrete enough to resume work without re-discovery.
- Missing verification or approvals are stated explicitly.

If any check fails, fix it before returning the session close-out.
