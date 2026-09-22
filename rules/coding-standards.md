# Coding Standards

## General

- Keep code readable and boring.
- Prefer explicit names over clever abbreviations.
- Keep methods small enough to understand, but do not split code artificially.
- Preserve existing style unless the project has an approved modernization task.

## Naming

- Preserve existing project naming conventions.
- For C#/.NET, use PascalCase for public types, methods, properties, events, and constants.
- For C#/.NET, use camelCase for local variables and method parameters.
- For C#/.NET, use `_camelCase` for private fields when that matches the project style.
- Use clear names over abbreviations.

## Services

- Prefer interfaces for business/application services.
- Use dependency injection.
- Keep infrastructure concerns out of domain/application logic when possible.

## Documentation and comments

Add useful documentation/comments to generated or modified code, especially for:

- public APIs, public services, DTOs, options, and extension methods;
- business rules;
- non-obvious edge cases;
- risky compatibility behavior;
- legacy migration notes;
- external system assumptions.

Avoid comments that simply restate the code.

## Errors and logging

- Log enough context to diagnose issues.
- Do not log secrets or sensitive user data.
- Prefer structured, searchable messages.

## Tests

- Add or update automated tests for new functionality, bug fixes, and behavior changes unless the user explicitly says not to add tests.
- Prefer unit tests for business/application logic.
- Add integration tests when the change crosses persistence, external APIs, queues, files, or framework boundaries.
- If tests cannot be added immediately, document the reason and the manual verification path.
- Mention which tests were added, updated, run, or still need to be run.

## Tester-facing test cases

- For each new or changed functionality, create or update a markdown test case file unless the user explicitly says not to.
- Store tester-facing test cases under the project `.ai/test-cases/` folder.
- Use one file per functionality or feature area.
- Include scope, prerequisites, test data, positive cases, negative/edge cases, regression checks, expected results, and notes for testers.
