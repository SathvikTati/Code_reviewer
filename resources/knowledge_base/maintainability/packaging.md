# Python Packaging and Project Structure

## Project Layout
Use a clear, conventional layout. The `src/` layout (package under `src/`) prevents accidentally importing the in-tree package instead of the installed one and is recommended for libraries. Keep tests in a top-level `tests/` directory. Group code by responsibility (e.g. `api/`, `services/`, `models/`) rather than dumping everything in one module.

## Metadata and Dependencies
Declare project metadata and dependencies in `pyproject.toml` (PEP 621) rather than legacy `setup.py`. Pin direct dependencies with compatible version ranges and lock exact versions for reproducible installs. Separate runtime dependencies from development/test dependencies. Do not commit virtual environments or build artifacts.

## Environments and Configuration
Use a virtual environment (`venv`) per project so dependencies are isolated. Keep configuration in environment variables or config files, not in code, following twelve-factor principles. Provide a `.env.example` documenting required variables without real secrets.

## Imports and Packages
Every package directory should have a clear public surface. Prefer absolute imports within a project for clarity. Avoid circular imports by depending on abstractions and keeping module responsibilities focused. Keep `__init__.py` light — it should expose the package API, not run heavy work at import time.

## Reproducibility and CI
Provide a documented way to install, run, lint, and test the project (Makefile, scripts, or documented commands). Run linting, type-checking, and tests in continuous integration on every change.
