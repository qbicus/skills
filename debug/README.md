# Debug

Purpose: debug problems using a logs-first workflow.

Use it when you want:
- production/runtime issues investigated from logs first
- build/test/package failures analyzed from build logs first
- root-cause narrowing before code changes

Default behavior:
- read logs before suggesting fixes
- separate root cause from downstream noise
- verify against the original failure pattern

Example prompts:
- `Use $debug to inspect the production logs for this crash and identify the root cause before changing code.`
- `Use $debug to analyze this failed build from the build log and tell me the first real error.`
