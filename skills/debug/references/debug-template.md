# Debug Investigation Template

Use this structure when reporting a debugging pass.

## Failure Surface
- Production/runtime, build/test/package, or both
- Time window
- Affected component or stage

## Evidence
- Key log signatures
- First meaningful failure
- Correlation IDs, environment, or input clues

## Pattern
- Repeated or isolated
- Deterministic or intermittent
- Suspected scope of impact

## Narrowed Hypothesis
- Most likely root cause
- Competing hypotheses ruled out

## Fix
- Code, config, dependency, environment, or operational action
- Why this addresses the observed failure

## Verification
- Commands or checks run
- Outcome
- Remaining uncertainty
