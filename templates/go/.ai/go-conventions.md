# Go Conventions

## Architecture

- Keep packages small and focused.
- Prefer interfaces at package boundaries and for dependencies that need testing/mocking.
- Do not create interfaces for every struct by default; create them where they simplify testing or decoupling.
- Keep HTTP handlers thin and move business logic into services/use cases.

## Naming

- Preserve existing project naming conventions.
- Use camelCase or PascalCase according to Go visibility rules.
- Use short names only when they are idiomatic and clear in context.

## Documentation

- Add Go doc comments for exported types, functions, methods, interfaces, and packages that are newly created or significantly changed.
- Add inline comments for non-obvious business rules, compatibility behavior, migration notes, and external system assumptions.

## Tests

- Add or update Go tests for new functionality, bug fixes, and behavior changes unless the user explicitly says not to add tests.
- Prefer table-driven tests where useful.
- Add or update tester-facing markdown test cases under `.ai/test-cases/`.

## Commands

Document project-specific commands in `.ai/commands.md`, such as:

```bash
go test ./...
go vet ./...
```
