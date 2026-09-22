<!-- AI-FRAMEWORK-GENERATED: project AGENTS.md v2 -->
# Project AI Instructions

This repository uses the shared AI framework.

Global framework location:

```text
%USERPROFILE%\.ai
```

or:

```text
~/.ai
```

## Project context

Read project context from:

- `.ai/project-overview.md`
- `.ai/architecture.md`
- `.ai/current-work.md`
- `.ai/decisions.md`
- `.ai/pitfalls.md`
- `.ai/commands.md`
- `.ai/testing.md`
- `.ai/deployment.md`
- `.ai/test-cases/README.md`

## Rules

- Project instructions override global instructions.
- Do not overwrite project memory without preserving useful existing information.
- Add or update automated tests for new functionality, bug fixes, and behavior changes unless the user explicitly says not to add tests.
- Create or update tester-facing markdown test cases under `.ai/test-cases/` for each new or changed functionality unless the user explicitly says not to.
- Use interfaces for business/application services unless project rules say otherwise.
- Preserve existing project naming conventions. For C#/.NET, use PascalCase for public members and camelCase for local variables and parameters.
- Add useful documentation/comments to generated or modified code; do not add comments that merely repeat the code.
- Before ending meaningful work or switching projects, run the `session-close` skill.
- For new features, use the `new-feature` workflow unless the user asks for a lighter process.
- For debugging, use the `debug` workflow.
- For code reviews, use the `code-review` workflow.

## Tester-facing test cases

For each new or changed functionality, create or update a markdown test case file under:

```text
.ai/test-cases/
```

Use one file per functionality or feature area. Include:

- feature/functionality name;
- scope;
- prerequisites;
- test data;
- positive test cases;
- negative/edge test cases;
- regression checks;
- expected results;
- notes for testers.
