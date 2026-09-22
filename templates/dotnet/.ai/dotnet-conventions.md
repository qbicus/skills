# .NET Conventions

## Architecture

- Prefer services with interfaces for business/application logic.
- Use dependency injection.
- Keep controllers/endpoints thin.
- Keep infrastructure concerns outside domain/application logic when possible.

## Naming and casing

- Use PascalCase for public types, methods, properties, events, and constants.
- Use camelCase for local variables and method parameters.
- Use `_camelCase` for private fields when that matches the project style.
- Use the `I` prefix for interfaces, for example `IChatAnswerService`.
- Preserve existing project naming conventions when working in existing files.

## Documentation

- Add XML documentation comments for public APIs, public services, DTOs, options, and extension methods when they are newly created or significantly changed.
- Add inline comments for non-obvious business rules, compatibility behavior, migration notes, and external system assumptions.
- Do not add comments that merely repeat what the code says.

## Tests

- Add or update automated tests for new functionality, bug fixes, and behavior changes unless the user explicitly says not to add tests.
- Prefer unit tests for services and business rules.
- Add integration tests when persistence, external APIs, queues, files, or framework boundaries are involved.
- Add or update tester-facing markdown test cases under `.ai/test-cases/`.

## Nullable and async

- Be explicit with nullable values.
- Use async/await for I/O work.
- Use cancellation tokens for long-running or I/O-heavy operations when the project style supports it.
