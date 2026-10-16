---
name: project-takeover
description: "Take over an existing repository efficiently without exhaustively ingesting the codebase into the primary context. Ensure framework repository intelligence is initialized via repo-init, then use AiIndex, Graphify, bounded delegated workers, and targeted source reads to build a durable understanding of architecture, current state, risks, and open questions. Use when inheriting a project from another developer/agent/team or when asked to understand an existing repository before continuing development."
---

# Project Takeover

Take ownership of an existing repository without loading the entire codebase into the primary model context.

The goal is not to memorize every file. The goal is to establish reliable repository intelligence, build a verified mental model of the system, persist useful project knowledge, and identify the questions that must be answered before substantial changes begin.

## Core rule: never exhaustively ingest the repository

Do **not** recursively read every source file, dump large directory trees into context, or attempt to understand the project by brute-force context loading.

Prefer, in order:

1. lightweight repository structure and instruction-file inspection;
2. `repo-init` to initialize/repair framework repository intelligence;
3. AiIndex for semantic/fuzzy discovery;
4. Graphify for structural/dependency questions;
5. targeted source/config/test reads to verify specific findings.

Read source files because they answer a concrete question, not merely because they exist.

## Role usage

Keep expensive primary-model work focused on synthesis and decisions.

- `primary`
  - owns takeover strategy and final understanding;
  - reviews the `repo-init` handoff;
  - interprets architecture and conflicting evidence;
  - decides what additional targeted investigation is needed;
  - writes/approves the final project understanding and user questions.
- `fast`
  - may classify project/language/framework types;
  - may summarize top-level repository structure and obvious entry points;
  - must remain bounded and mechanical.
- `executor`
  - may perform repository inventory, targeted evidence gathering, approved setup/index commands, and bounded project-knowledge updates;
  - must not independently make material architecture or product decisions.
- `researcher`
  - use only when understanding depends on external documentation/vendor behavior;
  - do not research every dependency by default.
- `advisor`
  - optional for unusually complex/risky takeover plans;
  - not required merely because the repository is large.

Do not delegate the same broad "understand the entire repository" request to a worker. Delegation must remain bounded.

## Workflow

### 1. Lightweight preflight

Before broad analysis:

- identify the repository root;
- inspect top-level structure at a shallow depth;
- read applicable repository instructions such as `AGENTS.md` and `CLAUDE.md`;
- read the main `README` and obvious architecture/current-work documentation when present;
- detect project/solution/package manifests and primary runtime entry points;
- detect existing `.ai/`, `.ai-index.json`, `.ai-index/`, `graphify-out/`, and `.gitignore`;
- determine whether the framework, AiIndex, and Graphify are already available.

Do not recursively enumerate/read the full repository during preflight.

### 2. Ensure repository framework setup

Invoke `repo-init` as the repository-setup subworkflow.

Pass through the user's existing approvals/constraints. In particular:

- if the user explicitly requested an initial full AiIndex index or Graphify build, that is approval to perform it **after the plan is shown**, unless inspection reveals a materially different/riskier operation;
- do not ask for the same approval twice;
- preserve all existing project files/configuration and Git history;
- do not create repo provider overrides unless genuinely needed.

Consume `repo-init`'s compact handoff:

- repository type(s);
- files/config created, modified, or preserved;
- AiIndex configuration/status/index status;
- Graphify availability/output status;
- ignore-rule changes;
- warnings/manual actions.

Do not repeat `repo-init`'s broad setup inspection afterward.

### 3. Build a repository map using intelligence tools

Use AiIndex first to discover the important concepts/files for questions such as:

- application purpose and major features;
- main runtime entry points;
- request/event/job flow;
- configuration and environment handling;
- storage/databases;
- authentication/authorization;
- external integrations;
- tests and test strategy;
- deployment/build/release paths;
- known TODOs, incomplete areas, migration notes, or active work.

Use Graphify to verify structural questions such as:

- callers/callees;
- dependency paths;
- module/project relationships;
- imports/references;
- inheritance/implementations;
- blast radius around important components.

Use targeted source reads to verify the most important conclusions.

### 4. Understand current state, not just architecture

Determine, when evidence exists:

- what the system does;
- major components and boundaries;
- important data/control flows;
- how it is built, run, tested, and deployed;
- active or unfinished work;
- important technical/product decisions already encoded in docs/code;
- risky/fragile areas;
- contradictions between documentation and implementation;
- missing information that cannot be derived safely from the repository.

Clearly distinguish:

- **verified** facts from code/config/tests;
- **documented** claims that were not independently verified;
- **inferences**;
- **unknowns/questions**.

### 5. Persist durable project knowledge

Update only useful, verified repo-local framework knowledge. Typical files include:

```text
.ai/project-overview.md
.ai/architecture.md
.ai/current-work.md
.ai/decisions.md
.ai/testing.md
.ai/deployment.md
.ai/pitfalls.md
```

Rules:

- preserve useful existing content;
- prefer targeted additive/reconciled updates over wholesale replacement;
- do not duplicate large chunks of README/source code;
- do not invent decisions/history that cannot be verified;
- record uncertainty explicitly;
- keep the files concise enough to help future sessions avoid another expensive takeover pass.

### 6. Final verification

Before declaring takeover complete:

- verify AiIndex is usable;
- verify Graphify is usable when applicable;
- confirm important conclusions with targeted source/config/test evidence;
- inspect `git status`;
- ensure only intended framework/project-knowledge changes were made.

## Output

Finish with a concise takeover report containing:

1. **Project purpose**
2. **Architecture / major components**
3. **Important flows and integrations**
4. **Build / run / test / deployment**
5. **Current or unfinished work**
6. **Important decisions / risks / pitfalls**
7. **Repository intelligence status**
   - AiIndex
   - Graphify
8. **Project-knowledge files updated**
9. **Questions / unknowns before further development**

Do not produce a file-by-file repository summary.

## Typical invocation

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
