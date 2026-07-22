# SOLID Principles

## Single Responsibility Principle (SRP)
A class or module should have one reason to change — one responsibility. When a class mixes concerns (e.g. business logic, persistence, and formatting), a change to one concern risks breaking the others. Split responsibilities into focused units.

## Open/Closed Principle (OCP)
Software entities should be open for extension but closed for modification. Add new behavior by adding new code (new subclasses, strategies, or plugins) rather than editing existing, tested code. Long `if/elif` chains that grow with every new case often signal an OCP violation better solved with polymorphism.

## Liskov Substitution Principle (LSP)
Subtypes must be substitutable for their base types without changing correctness. A subclass should not strengthen preconditions, weaken postconditions, or throw unexpected exceptions where the base class would not. If overriding a method forces callers to check the concrete type, LSP is being violated.

## Interface Segregation Principle (ISP)
Clients should not be forced to depend on methods they do not use. Prefer several small, role-specific interfaces (in Python, Protocols or ABCs) over one large interface. Fat interfaces couple unrelated clients together.

## Dependency Inversion Principle (DIP)
High-level modules should not depend on low-level modules; both should depend on abstractions. Depend on interfaces/Protocols, not concrete implementations. Inject dependencies (pass collaborators in) rather than constructing them inside a class, which improves testability and decoupling.
