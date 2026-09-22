---
name: modernize-eval
description: "Evaluate an existing project and recommend a modernization strategy such as targeted refactor, in-place migration, phased replacement, or rewrite. Use when a user asks for `/modernize-eval`, wants a migrate-vs-rewrite assessment, needs a management-ready report for a legacy or aging system, or wants comparative modernization scores across multiple projects."
---

# Modernize Eval

Evaluate modernization strategy neutrally. Do not assume rewrite or migration up front; compare realistic options using evidence from the codebase, dependencies, operations, and delivery constraints.

Use the report structure in [references/modernize-report-template.md](references/modernize-report-template.md) and the scoring rubric in [references/scoring-rubric.md](references/scoring-rubric.md).

## Workflow

1. Establish scope and constraints
- Confirm the project or repository under evaluation.
- Capture known business constraints: deadlines, downtime tolerance, compliance concerns, staffing limits, and whether the goal is recommendation only or implementation planning later.
- If the system is only one part of a larger estate, state the evaluation boundary explicitly.

2. Inspect the current system
- Review the codebase structure, framework/runtime version, dependency health, build state, test posture, data stores, integration points, and deployment assumptions.
- Note whether the system is legacy framework, early .NET Core, or modern .NET with localized issues.
- Look for concrete evidence of coupling, unsupported dependencies, operational fragility, and areas where changes are risky.

3. Evaluate modernization options
- Always consider at least these options when relevant:
  - stay as-is temporarily
  - targeted refactor
  - in-place migration/upgrade
  - phased replacement / strangler
  - full rewrite
- Drop options only with an explicit reason.
- Compare option viability in this codebase, not in the abstract.

4. Score the system
- Score each dimension from `0-10` using the rubric:
  - framework/runtime obsolescence
  - dependency/support risk
  - architecture/coupling
  - code maintainability
  - test coverage/testability
  - data/integration complexity
  - security/compliance risk
  - deployment/operations fragility
  - business continuity constraints
  - team familiarity / implementation confidence
- Convert those dimension scores into:
  - `Modernization Complexity Score` (`0-100`)
  - `Migration Suitability Score` (`0-100`)
  - `Rewrite Pressure Score` (`0-100`)
- Show the dimension scores and the three final scores in the report.

5. Apply recommendation rules
- Use these baseline rules unless the evidence strongly justifies an override:
  - `Migration Suitability >= 70` and `Rewrite Pressure <= 40` -> recommend `migrate`
  - `Migration Suitability 50-69` and `Rewrite Pressure <= 60` -> recommend `migrate with targeted refactor`
  - `Migration Suitability 40-60` and `Rewrite Pressure 50-75` -> recommend `phased replacement`
  - `Migration Suitability <= 40` and `Rewrite Pressure >= 70` -> recommend `rewrite`
  - `Modernization Complexity >= 80` -> add an explicit high-risk warning regardless of path
  - if scores conflict materially -> recommend `manual review required`
- Scores summarize the evaluation; they do not override obvious evidence.

6. Produce a management-ready report
- Explain the findings in plain engineering language without hand-wavy “the code is bad” claims.
- Tie the recommendation to concrete drivers such as unsupported dependencies, deep coupling, missing tests, or manageable upgrade surface.
- Distinguish short-term feasibility from long-term strategic value.

## Output Rules

- End every report with:
  - `Recommended Strategy`
  - `Confidence: low|medium|high`
  - `Modernization Complexity Score: X/100`
  - `Migration Suitability Score: Y/100`
  - `Rewrite Pressure Score: Z/100`
  - `Reason Summary` with 3-5 bullets explaining the dominant drivers
- If evidence is weak or incomplete, lower confidence and say what is missing.
- If the system appears to support more than one viable path, say so instead of forcing false certainty.

## Quality Gate

Before finalizing, verify all checks pass:

- The evaluation considered multiple modernization paths, not only the user's preferred one.
- Findings are grounded in observed codebase or operational evidence.
- All 10 scoring dimensions are present with `0-10` values.
- The three final scores are shown and the recommendation matches the scoring rules or explicitly explains an override.
- The report can be read by both engineers and management.

If any check fails, fix it before returning the evaluation.
