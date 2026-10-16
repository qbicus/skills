# Skill: `project-takeover`

Efficiently take over an existing project without burning the primary model's context/usage by reading every repository file.

`project-takeover` first ensures the repository is ready for the shared framework through `repo-init`, then uses AiIndex, Graphify, bounded delegated workers, and targeted source reads to build a verified understanding of the project.

## Recommended prompt

```text
Use project-takeover on this repository.

It was previously developed by another developer or AI assistant. Initialize or
repair our AI framework setup if necessary, then build a verified understanding
of the project using AiIndex and Graphify.

Do not exhaustively read the repository into the primary context.

At the end, give me your understanding of the architecture, current state,
important decisions/risks, and any questions you need answered before we
continue development.
```

For normal use, the shorter form is enough:

```text
Use project-takeover on this repository.
```

## What it does

- performs only a lightweight preflight before repository intelligence exists;
- invokes `repo-init` to initialize/repair framework setup, AiIndex, Graphify, and ignore rules;
- reuses user approval for an explicitly requested full index instead of asking twice;
- uses AiIndex for semantic discovery rather than exhaustive source reading;
- uses Graphify for dependency/relationship questions;
- delegates bounded mechanical/inventory work where useful;
- keeps the primary model focused on synthesis, decisions, contradictions, and final ownership;
- verifies important conclusions with targeted source/config/test reads;
- updates concise `.ai/` project knowledge so future sessions do not need another expensive takeover pass;
- ends with architecture/current-state/risk summaries and unresolved questions.

## Relationship to `repo-init`

`repo-init` prepares and verifies the repository for framework use.

`project-takeover` uses that prepared repository intelligence to learn enough to safely own and continue the project.

```text
project-takeover
  -> lightweight preflight
  -> repo-init
  -> AiIndex discovery
  -> Graphify structural verification
  -> targeted source reads
  -> durable .ai project knowledge
  -> takeover report + questions
```

It must not turn the takeover into a recursive read of the entire repository.
