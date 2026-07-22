# Naming and Documentation

## Intention-Revealing Names
Names should reveal intent: why something exists, what it does, how it is used.
Avoid abbreviations, single letters (except short loop indices), and "magic"
numbers — name constants. Functions/methods are verbs (`calculate_total`);
classes are nouns (`InvoiceBuilder`); booleans read as predicates (`is_valid`,
`has_items`). Keep one consistent vocabulary; don't call the same concept
`user`, `account`, and `member` interchangeably.

## Follow PEP 8 Conventions
`snake_case` for functions/variables/modules, `PascalCase` for classes,
`UPPER_SNAKE_CASE` for constants, and a leading underscore for non-public names.
Avoid shadowing built-ins (`list`, `id`, `type`, `dict`, `input`).

## Docstrings (PEP 257)
Every public module, class, and function should have a docstring. The first line
is a short imperative summary ending in a period. For non-trivial functions,
document parameters, return value, and raised exceptions (Google, NumPy, or
reStructuredText style — pick one and be consistent). Keep docstrings accurate as
code changes; a stale docstring is worse than none.

## Comments Explain Why, Not What
Prefer self-explanatory code over comments. Good comments capture rationale,
trade-offs, and non-obvious constraints — not a restatement of the code. Delete
commented-out code; version control remembers it.

## Consistency
Consistent naming, formatting, and structure reduce cognitive load. Automate it
with a formatter (Black) and linter (Ruff/flake8) so style is never a review
topic.
