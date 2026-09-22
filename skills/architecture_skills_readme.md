# Technical Architecture Discovery Skills

This repository contains a set of Codex skills used to automatically analyze projects and generate Technical Architecture Specifications (TAS).

The workflow is designed to be run across multiple projects, then consolidated into a structured architecture view.

---

## Overview

The pipeline consists of four steps:

1. Project Analysis  
2. Project Grouping  
3. Architecture Normalization  
4. TAS Generation  

Each step produces structured outputs that feed into the next.

---

## Skills

### 1. Project Architecture Analyzer (tas-01-project-architecture-analyzer)

Analyzes a single repository and extracts architecture information.

**Input**
- projectFolder
- architectureWorkspaceFolder

**Output**
<workspace>/01-analyzer/<project>/
- output.json
- output.md
- decisions.md

**What it does**
- Detects components, APIs, databases, integrations, deployment clues
- Classifies data as observed, inferred, or unknown
- Produces a structured architecture profile per project

---

### 2. Architecture Project Grouper (tas-02-architecture-project-grouper)

Groups analyzed projects into platforms and identifies shared services.

**Input**
- architectureWorkspaceFolder

**Reads**
<workspace>/01-analyzer/**/output.json

**Output**
<workspace>/02-grouper/
- grouped.json
- grouped.md
- decisions.md

**What it does**
- Groups projects conservatively into platforms
- Detects shared services and dependencies
- Identifies orphan systems and naming collisions

---

### 3. Architecture Normalizer (tas-03-architecture-normalizer)

Resolves duplicate names, aliases, and inconsistencies across projects.

**Input**
- architectureWorkspaceFolder

**Reads**
- 01-analyzer/**/output.json
- 02-grouper/grouped.json

**Output**
<workspace>/03-normalizer/
- normalized.json
- normalized.md
- decisions.md

**What it does**
- Creates canonical names for services, systems, and databases
- Preserves aliases and original names
- Flags uncertain matches for manual review

---

### 4. TAS Generator (tas-04-generator)

Generates final Technical Architecture Specification documents.

**Input**
- architectureWorkspaceFolder

**Reads**
03-normalizer/normalized.json

**Output**
<workspace>/04-tas/
- master-tas.md
- platform-<name>.md
- project-<name>.md (optional)
- decisions.md

**What it does**
- Produces human-readable architecture documentation
- Generates one master view and per-platform documents
- Clearly separates observed vs inferred information

---

## Execution Order

1. Run Analyzer for each project (can be done in parallel)  
2. Run Grouper once across all results  
3. Run Normalizer  
4. Run TAS Generator  

---

## Key Principles

- Prefer observed evidence over inference  
- Do not invent missing data  
- Keep outputs deterministic and structured  
- Keep grouping and normalization conservative  
- Use decisions.md to track assumptions and manual changes  

---

## Notes

- Each skill is self-contained and includes its own references folder
- All markdown outputs are generated from templates
