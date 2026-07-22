# Clean Code Principles

## Meaningful Names
Use intention-revealing names. A name should tell why something exists, what it does, and how it is used. Avoid single-letter names except for short loop counters. Avoid abbreviations and encodings. Functions should be verbs or verb phrases; classes should be nouns.

## Small, Single-Purpose Functions
Functions should be small and do one thing at one level of abstraction. If a function needs a comment to explain a block, that block probably wants to be its own well-named function. Prefer few parameters (0–3); many parameters often signal a missing object or a function doing too much. Avoid boolean "flag" arguments that make the function do two things.

## Don't Repeat Yourself (DRY)
Duplicated logic should be extracted into a single shared function or class. Duplication multiplies the cost of change and the risk of inconsistent fixes.

## Comments
Prefer expressive code over comments. Good comments explain *why*, not *what*. Delete commented-out code — version control already remembers it. Keep docstrings accurate; a stale docstring is worse than none.

## Command–Query Separation
A function should either do something (command) or answer something (query), not both. Avoid side effects that a caller cannot infer from the name.

## Error Handling over Return Codes
Use exceptions rather than returning error sentinels that callers forget to check. Catch specific exceptions, not bare `except:`. Never silently swallow exceptions.

## The Boy Scout Rule
Leave the code cleaner than you found it. Small, continuous improvements prevent large-scale rot.
