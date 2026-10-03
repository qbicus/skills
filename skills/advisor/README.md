# Advisor

Purpose: independent checkpoint review without taking over implementation.

Modes:
- `plan` — review a substantial design/plan before commitment or approval.
- `stuck` — reassess direction after the configured repeated-failure threshold.
- `complete` — verify substantial work before it is declared done.

Examples:
- `Use $advisor in plan mode to review this implementation plan.`
- `Use $advisor in stuck mode; the same test failure has happened twice.`
- `Use $advisor in complete mode before we mark this migration done.`

Parent skills may invoke the advisor automatically according to the active provider policy.
