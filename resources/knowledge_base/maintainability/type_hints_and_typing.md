# Type Hints and Static Typing (PEP 484)

## Annotate Public Interfaces
Add type hints to the signatures of public functions, methods, and class
attributes. Types document intent, enable editor autocomplete, and let static
checkers catch bugs before runtime. Prioritize annotating boundaries (public APIs,
module-level functions) over trivial internals.

## Run a Static Type Checker
Type hints are not enforced at runtime, so run mypy or pyright in CI. Treat new
type errors as build failures. Start lenient on legacy code and tighten over time
(e.g. per-module strictness) rather than blocking everything at once.

## Use Precise, Modern Types
Prefer specific types over `Any`, which disables checking. Use `Optional[T]`
(or `T | None`) for nullable values, `Sequence`/`Mapping`/`Iterable` for
read-only parameters, and generics (`list[int]`, `dict[str, User]`). Use
`Protocol` for structural (duck-typed) interfaces and `TypedDict`/`dataclass`/
`pydantic` models instead of loose dicts. Modern syntax (`list[int]`, `X | Y`)
is available on current Python versions.

## Avoid Common Pitfalls
Do not use mutable defaults (`def f(items: list = [])`) — annotate
`Optional[list]` and build inside. Keep annotations consistent with the code they
describe; a wrong type hint misleads readers and tools. Avoid over-engineering
types where a simple annotation suffices.

## Typed Data Models
Represent structured data with `dataclasses` or `pydantic` models rather than
passing tuples/dicts. This gives validation, clear field names, and better tool
support, improving both safety and readability.
