# API Design and Layered Architecture

## Separation of Concerns / Layering
Keep clear layers: transport/API (request handling, serialization), application/
service (use cases, orchestration), domain (business rules), and infrastructure
(database, external calls). Dependencies point inward — the domain does not import
web framework or database code. This keeps business logic testable and
framework-agnostic.

## Thin Controllers, Rich Services
HTTP handlers/controllers should validate input, call a service, and format the
response — not contain business logic or direct database queries. Put logic in
services/domain objects so it can be reused and unit-tested without a web server.

## Dependency Injection
Pass collaborators (clients, repositories, config) into objects rather than
constructing them inside. This decouples components, follows the Dependency
Inversion Principle, and makes testing with fakes/mocks straightforward. Avoid
hidden global singletons and import-time side effects.

## API Design
Design consistent, predictable interfaces: clear resource names, correct HTTP
methods and status codes, explicit request/response schemas (e.g. pydantic
models), and validated inputs. Version public APIs and avoid breaking changes.
Return structured errors, not stack traces.

## Cohesion and Coupling
Aim for high cohesion (a module does one well-defined job) and low coupling
(modules interact through small, stable interfaces). Avoid circular imports by
depending on abstractions and keeping module responsibilities focused. Watch for
"god modules" that accumulate unrelated responsibilities.

## Boundaries and Contracts
Define explicit contracts between layers and services (function signatures,
schemas, Protocols). Validate data as it crosses a boundary (especially the
outer edge) so inner layers can trust their inputs.
