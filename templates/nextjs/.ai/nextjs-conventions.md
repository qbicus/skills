# Next.js Conventions

## Architecture

- Preserve the existing App Router or Pages Router structure.
- Keep server-side logic out of client components unless explicitly needed.
- Prefer small components with clear props.
- Extract reusable business/client logic into hooks, services, or utility modules.
- Use interfaces or types for component props, service contracts, and API shapes.

## Naming

- Preserve existing project naming conventions.
- Use PascalCase for React components and types/interfaces.
- Use camelCase for variables, functions, hooks, props, and local values.
- Prefix hooks with `use`.

## Documentation

- Add comments for non-obvious rendering behavior, data fetching rules, caching/revalidation behavior, authorization rules, and compatibility assumptions.
- Add JSDoc/TSDoc for exported utilities, service functions, and complex public types when newly created or significantly changed.

## Tests

- Add or update tests for new functionality, bug fixes, and behavior changes unless the user explicitly says not to add tests.
- Prefer unit tests for pure logic and component tests for UI behavior.
- Add integration/e2e tests when routing, auth, API calls, or critical flows are affected.
- Add or update tester-facing markdown test cases under `.ai/test-cases/`.

## Commands

Document project-specific commands in `.ai/commands.md`, such as:

```bash
npm test
npm run lint
npm run build
```
