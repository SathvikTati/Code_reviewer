# Error Handling and Logging

## Catch Specific Exceptions
Catch the narrowest exception that expresses what you expect to fail. Never use a
bare `except:` or a broad `except Exception:` that hides bugs. A bare except also
swallows `KeyboardInterrupt` and `SystemExit`. Let unexpected errors propagate.

## Never Silently Swallow Errors
Do not write `except SomeError: pass`. At minimum log the error with context, or
re-raise. Swallowing exceptions hides failures and makes debugging painful. If you
must translate an exception, chain it with `raise NewError(...) from err` to keep
the original traceback.

## Fail Fast, Clean Up Reliably
Validate inputs early and raise on invalid state rather than limping along. Use
context managers (`with`) or `try/finally` to release files, locks, and
connections even on error. Prefer custom exception types for domain errors so
callers can handle them precisely.

## Don't Use Exceptions for Normal Control Flow
Exceptions signal exceptional conditions, not routine branching. Returning a
value or using a conditional is clearer for expected cases.

## Use `logging`, Not `print`
Use the standard `logging` module (or a structured logger) instead of `print` for
diagnostics. Choose appropriate levels (DEBUG/INFO/WARNING/ERROR) and configure
handlers at the application edge, not inside libraries. Include context (ids,
operation) in messages. Never log secrets, tokens, passwords, or full PII.

## Actionable Messages
Error messages should explain what failed and, where possible, how to fix it —
without leaking internal paths, SQL, or stack traces to end users. Log the detail
server-side; return a safe message to the client.
