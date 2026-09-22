# Python Conventions

## Architecture

- Keep modules focused and readable.
- Prefer dependency injection or explicit dependency passing for code that needs testing.
- Use abstract base classes or protocols where an interface boundary is useful.
- Separate business logic from CLI, web, task, or framework entry points.

## Naming

- Preserve existing project naming conventions.
- Use snake_case for functions, methods, variables, and module names.
- Use PascalCase for classes.
- Use UPPER_SNAKE_CASE for constants.

## Documentation

- Add docstrings for public modules, classes, functions, and methods when newly created or significantly changed.
- Add inline comments for non-obvious business rules, compatibility behavior, migration notes, and external system assumptions.

## Tests

- Add or update tests for new functionality, bug fixes, and behavior changes unless the user explicitly says not to add tests.
- Prefer pytest-style tests when the project uses pytest.
- Add or update tester-facing markdown test cases under `.ai/test-cases/`.

## Commands

Document project-specific commands in `.ai/commands.md`, such as:

```bash
pytest
python -m pytest
ruff check .
```
