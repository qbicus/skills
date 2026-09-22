# Code Review

Purpose: review code changes across correctness, security, architecture, observability, and tests.

Use it when you want:
- a PR or diff review
- validated findings with less noise
- optional auto-fix plus re-review until clean

Default behavior:
- review in context
- drop weak/speculative findings
- fix validated issues unless explicitly asked for review-only

Example prompts:
- `Use $code-review to review the current branch and fix validated issues.`
- `Use $code-review to review only the files changed in this PR and do not modify code.`
