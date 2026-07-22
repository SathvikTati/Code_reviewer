# Testing Best Practices

## What to Test
Cover the public behavior of each unit, the important edge cases (empty, boundary, and invalid inputs), and the error paths — not just the happy path. Prioritize tests for complex logic, bug-prone areas, and code that has broken before. Aim for meaningful coverage of branches, not a vanity percentage.

## Structure
Follow Arrange–Act–Assert: set up inputs, invoke the unit, assert the outcome. Keep each test focused on one behavior with a descriptive name that states the scenario and expectation (e.g. `test_withdraw_raises_when_balance_insufficient`). Tests should be independent and order-independent — no shared mutable state between tests.

## Fast and Deterministic
Unit tests should be fast and deterministic. Isolate external systems (network, database, clock, filesystem) with fakes, mocks, or fixtures so tests do not depend on the environment. Avoid `sleep`-based timing; inject the clock. Flaky tests erode trust and should be fixed or quarantined.

## Tools and Practice
Use `pytest` with fixtures for setup and `parametrize` for table-driven cases. Use `unittest.mock` to isolate collaborators. Run tests in CI on every change. Practice test-driven or test-alongside development so code stays testable — code that is hard to test usually has a design problem (tight coupling, hidden dependencies).

## Coverage Recommendations
For each public function or class, ensure there is at least one test for normal input, one for a boundary/edge case, and one for an invalid input or expected exception.
