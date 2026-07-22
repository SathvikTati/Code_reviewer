# Common Design Patterns (Python)

## Creational
- **Factory / Factory Method**: centralize object creation so callers depend on an abstraction, not concrete classes. Useful when the concrete type is chosen at runtime.
- **Builder**: construct complex objects step by step; good when a constructor would need many optional parameters.
- **Singleton**: a single shared instance. In Python, prefer a module-level object or dependency injection over classic singleton hacks.

## Structural
- **Adapter**: wrap an incompatible interface so existing code can use it unchanged.
- **Facade**: provide a simple interface over a complex subsystem; reduces coupling between clients and internals.
- **Decorator**: add behavior by wrapping. Python's function decorators are a language-level form of this.

## Behavioral
- **Strategy**: encapsulate interchangeable algorithms behind a common interface; replaces sprawling conditionals and supports the Open/Closed Principle.
- **Observer**: notify dependents of state changes; underpins event systems and pub/sub.
- **Template Method**: define an algorithm skeleton in a base class, deferring specific steps to subclasses.

## Pythonic Guidance
Do not force Java-style patterns where a language feature is cleaner: first-class functions replace many Strategy/Command uses, context managers replace some Template Method setups, and generators replace Iterator boilerplate. Apply a pattern when it removes duplication or decouples change — not for its own sake.
