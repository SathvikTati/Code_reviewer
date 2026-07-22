# pytest, Fixtures, Mocking, and Coverage

## Prefer pytest
Use `pytest`: plain `assert` statements, concise test functions, and rich
introspection on failure. Name tests descriptively for the scenario and
expectation, e.g. `test_withdraw_raises_when_balance_insufficient`.

## Fixtures for Setup
Use `@pytest.fixture` for shared setup/teardown instead of duplicated boilerplate
or module-level state. Scope fixtures (`function`, `module`, `session`)
appropriately. Keep tests independent and order-independent — no shared mutable
state leaking between tests.

## Parametrize Table-Driven Cases
Use `@pytest.mark.parametrize` to cover many input/output combinations without
copy-pasting test bodies. This makes edge cases explicit and easy to extend.

## Isolate External Systems
Mock or fake network, database, filesystem, and clock dependencies with
`unittest.mock` or fixtures so unit tests are fast and deterministic. Inject the
clock rather than sleeping. Reserve real integrations for a separate, smaller
suite of integration tests.

## Test Behavior and Edge Cases
Cover the public behavior, boundary values (empty, min/max, off-by-one), and error
paths — not just the happy path. Write a regression test for every fixed bug.
Follow Arrange–Act–Assert and assert on observable behavior, not internals.

## Coverage as a Signal, Not a Target
Measure branch coverage with `coverage.py`/`pytest-cov` to find untested paths,
but do not chase 100% for its own sake. Prioritize meaningful tests for complex,
critical, and bug-prone code. Flaky tests must be fixed or quarantined — they
erode trust in the suite.
