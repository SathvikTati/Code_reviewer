# Python Best Practices

## Idiomatic Python
Write Pythonic code: iterate directly over sequences rather than indices, use `enumerate` when you need the index, and `zip` to iterate in parallel. Use context managers (`with`) for files, locks, and connections so resources are always released. Prefer f-strings for formatting. Use `pathlib` over manual string path manipulation. Return early to avoid deep nesting.

## Explicit and Predictable
Prefer explicit over implicit. Avoid mutable default arguments; use `None` and create the container inside the function. Avoid global mutable state. Make functions pure where practical — same inputs produce same outputs with no hidden side effects. Use `dataclasses` or `pydantic` models instead of passing around loose dicts and tuples.

## Type Hints and Documentation
Add type hints to public interfaces and run a static checker (mypy, pyright). Write concise docstrings describing purpose, parameters, return value, and raised exceptions. Keep them accurate as the code evolves.

## Errors and Resources
Catch specific exceptions, never bare `except:`. Do not swallow errors silently; log with context or re-raise. Use custom exception types for domain errors. Clean up resources in `finally` or with context managers.

## Project Hygiene
Keep functions and modules cohesive and reasonably small. Remove dead code and unused imports. Use logging instead of `print` for diagnostics. Pin and manage dependencies. Automate formatting (Black) and linting (Ruff/flake8) so style is consistent and not a review topic.
