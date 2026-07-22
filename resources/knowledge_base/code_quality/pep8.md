# PEP 8 — Python Style Guide

## Layout
Use 4 spaces per indentation level; never mix tabs and spaces. Limit lines to 79 characters (or a project-agreed limit such as 88 for Black/99). Surround top-level function and class definitions with two blank lines; method definitions inside a class with one. Add imports at the top of the file, grouped standard-library / third-party / local, each group separated by a blank line. Avoid wildcard imports (`from module import *`).

## Naming Conventions
- `snake_case` for functions, methods, variables, and modules.
- `PascalCase` (CapWords) for classes.
- `UPPER_SNAKE_CASE` for constants.
- Prefix non-public methods and attributes with a single underscore.
- Avoid names that shadow built-ins (`list`, `id`, `type`, `dict`).

## Whitespace
No space immediately inside brackets or before a comma; one space after a comma. Surround binary operators with a single space. No trailing whitespace.

## Programming Recommendations
Compare to `None` with `is` / `is not`, not `==`. Use `if x is None:` not `if x == None:`. Use `isinstance(obj, cls)` rather than comparing types directly. Prefer `if not seq:` to test for empty sequences over `if len(seq) == 0:`. Use context managers (`with open(...) as f:`) so resources close reliably. Do not use mutable default arguments (`def f(x, items=[])`) — use `None` and create the container inside.

## Type Hints (PEP 484)
Add type hints to public function signatures to document intent and enable static analysis. Keep annotations consistent with the code they describe.
