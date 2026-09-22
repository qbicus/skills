---
name: decision
description: "Maintain a running implementation decision log that records what was decided, why it was chosen, and which alternatives were considered and rejected. Use when a user asks for `/decision`, wants architecture or implementation rationale preserved across sessions, or needs to document why Approach A was chosen over Approach B."
---

# Decision

Capture durable implementation rationale in a running log so future sessions can recover the reasoning behind earlier choices.

Use the entry structure in [references/decision-template.md](references/decision-template.md) unless the user asks for a different format.

## Workflow

1. Identify the decision scope
- Confirm the project area, feature, or change the decision belongs to.
- Capture the concrete question being decided before writing the log entry.
- If the user already made the decision, document it; if not, help compare options first and then log the result.

2. Locate or create the running log
- Default path: `<projectFolder>/_localnotes/<featureShortName>/decisions.md`.
- If `projectFolder` is not provided, use the current working directory.
- If `featureShortName` is not provided, ask for it when needed to avoid writing into the wrong log.
- Append to the existing log instead of creating fragmented files unless the user explicitly wants a separate decision record.

3. Record the actual decision
- State exactly what was chosen.
- Keep the decision specific enough that a later session can act on it without guessing.
- Include implementation impact when relevant: files, interfaces, migration choices, constraints, or rollout implications.

4. Record the rationale
- Explain why the chosen option won in this context.
- Prefer concrete drivers: correctness, operability, migration safety, team conventions, delivery speed, maintenance cost, or user impact.
- Capture assumptions and constraints that materially affected the choice.

5. Record alternatives and rejections
- List the realistic options considered.
- For each rejected option, state why it was not chosen in this context.
- Avoid generic reasons like `too complex`; explain the real tradeoff.

6. Keep the log current
- Add a new dated entry when a decision changes instead of silently overwriting old rationale.
- Cross-reference superseded decisions when appropriate.
- If the new choice invalidates downstream plans or code, note the affected artifacts explicitly.

## Output Rules

- Use a chronological append-only style unless the user explicitly asks for reorganization.
- Prefer concise entries with enough context to survive a cold restart one or more weeks later.
- Include dates in ISO format.
- If a decision is still pending, mark it clearly as provisional instead of presenting it as final.

## Quality Gate

Before finalizing, verify all checks pass:

- The entry states what was decided in one unambiguous sentence.
- The rationale explains why the chosen option fits this codebase or feature.
- At least one alternative is documented when realistic alternatives existed.
- Rejected options include concrete rejection reasons.
- The log path is consistent with the current feature area.

If any check fails, fix it before returning the decision log update.
