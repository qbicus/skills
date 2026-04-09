# Scoring Rubric

Score each dimension from `0-10`.

- `0-2`: favorable / low concern
- `3-4`: mild concern
- `5-6`: moderate concern
- `7-8`: high concern
- `9-10`: severe concern

For `Team familiarity / implementation confidence`, invert the intuition:
- `0-2`: team is highly confident and experienced
- `9-10`: team confidence is low or required skills are missing

## Dimensions

### 1. Framework/runtime obsolescence
- Score high when the system is on unsupported or deeply outdated runtime/framework versions or depends on legacy hosting assumptions that block modernization.

### 2. Dependency/support risk
- Score high when key packages, vendors, or internal libraries are unsupported, abandoned, hard to upgrade, or strongly lock the system to old technology.

### 3. Architecture/coupling
- Score high when concerns are tightly mixed, modules are hard to isolate, and a small change has broad unpredictable impact.

### 4. Code maintainability
- Score high when the code is hard to understand, inconsistent, duplicated, poorly structured, or relies on fragile patterns.

### 5. Test coverage/testability
- Score high when meaningful automated tests are missing and the code is difficult to validate safely after change.

### 6. Data/integration complexity
- Score high when the system has many external integrations, fragile database assumptions, queue/workflow coupling, or difficult-to-mock side effects.

### 7. Security/compliance risk
- Score high when there are known security gaps, outdated auth models, insecure defaults, or regulatory exposure that modernization must address.

### 8. Deployment/operations fragility
- Score high when releases are manual, rollback is hard, environments drift, observability is weak, or production support is brittle.

### 9. Business continuity constraints
- Score high when downtime tolerance is low, the system is mission-critical, and transition risk must be tightly controlled.

### 10. Team familiarity / implementation confidence
- Score high when the team has limited expertise with the legacy stack, target stack, or migration domain.

## Final Score Guidance

Use the dimension scores to derive three final scores.

### Modernization Complexity Score
Reflect overall difficulty and risk of changing the system at all.
Weight heavily:
- architecture/coupling
- code maintainability
- test coverage/testability
- data/integration complexity
- deployment/operations fragility
- business continuity constraints

### Migration Suitability Score
Reflect how viable an in-place migration or upgrade path is.
Increase when:
- architecture is reasonably separable
- maintainability is acceptable
- tests exist or can be added incrementally
- dependency risk is manageable
- team confidence is good
Decrease when:
- framework lock-in is deep
- dependencies block upgrade
- coupling is severe
- deployments are brittle

### Rewrite Pressure Score
Reflect how strong the case is for rewrite or phased replacement.
Increase when:
- framework/runtime is deeply obsolete
- dependencies are unsupported
- coupling is severe
- maintainability is poor
- tests are weak
- security or operational risk is high

## Recommendation Rules

- `Migration Suitability >= 70` and `Rewrite Pressure <= 40` -> `migrate`
- `Migration Suitability 50-69` and `Rewrite Pressure <= 60` -> `migrate with targeted refactor`
- `Migration Suitability 40-60` and `Rewrite Pressure 50-75` -> `phased replacement`
- `Migration Suitability <= 40` and `Rewrite Pressure >= 70` -> `rewrite`
- `Modernization Complexity >= 80` -> add high-risk warning
- If scores conflict materially -> `manual review required`
