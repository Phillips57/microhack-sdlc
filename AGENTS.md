# Project Guidelines

## General

- Keep changes focused, preserve existing behavior, and follow the style of nearby code.
- Prefer explicit types and existing helpers over `any`, duplicated logic, or broad abstractions.
- Handle errors through the established API error and middleware patterns; do not hide failures.
- Add or update tests and documentation when behavior, endpoints, or data structures change.
- See `.github/instructions/` for API, frontend, and database-specific guidance, and `src/docs/` for architecture and build details.

## Scope Rules

- For API work in this checkout, limit changes to `src/api-py/`. For frontend work, limit changes to `src/frontend/`.
- Change `src/database/migrations/` or `src/database/seed/` only when the requested behavior requires a shared schema or seed-data change; add a new migration rather than editing a historical one.
- Change tests and documentation only when directly relevant to the requested behavior.
- Do not modify `infra/`, generated output (including `src/frontend/dist/`, `node_modules/`, or Python cache files), other API implementations, or unrelated services.
- Do not update dependency manifests or lockfiles unless the requested change requires a dependency change.

## Naming

- In Python, use `snake_case` for modules, functions, and variables; `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants.
- In TypeScript, use `PascalCase` for React components and types, `camelCase` for variables, functions, and methods, and `UPPER_SNAKE_CASE` for true constants.
- Use descriptive file names consistent with the surrounding folder: Python modules use `snake_case.py`, and React component files use `PascalCase.tsx`.
- Keep API model properties in `camelCase` and SQLite table/column names in `snake_case`. Map between them through the existing database utilities.
- Use `use`-prefixed names for React hooks and keep component names aligned with their exported components.

## Preferred Patterns

- Keep FastAPI routes thin: validate and coordinate requests, then delegate persistence to repositories.
- Put SQL and persistence logic in repositories. Always bind user-supplied values as SQL parameters.
- Reuse domain errors and centralized error handling so API variants return consistent status codes and response shapes.
- Use Pydantic models for API input/output validation and the existing asynchronous `aiosqlite` repository patterns for database access.
- Document API changes in Swagger/OpenAPI. Add new sequential SQL migrations for schema changes; do not rewrite historical migrations.
- In the frontend, use small, focused React components, typed API contracts, React Query for server state, and Tailwind utility classes in line with existing code.
- Favor semantic HTML and accessible labels, keyboard behavior, and visible focus states.
- Test repository behavior and API responses; add frontend tests for important UI behavior.

## Build and Test

Run these commands from `src/` after dependencies are installed:

| Area | Build / validation | Tests |
| --- | --- | --- |
| Python API | `make build-py` | `make test-py` |
| Frontend | `make build-frontend` | `make test-frontend` |

`make build-py` checks Python syntax by compiling `src/api-py/main.py`; it is not a package build. `make test-frontend` runs the Playwright suite and installs Chromium if it is not already available. For both areas, run `make build-py && make test-py && make build-frontend && make test-frontend` from `src/`.
