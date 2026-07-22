"""Shared test setup.

These tests run with NO external infrastructure: Phoenix tracing is disabled,
and anything that would touch Neo4j / Ollama / OpenAI is mocked in the tests
themselves. Env is set here (before app modules import) so that load_dotenv()
in the app cannot override it (python-dotenv does not overwrite existing vars).
"""

import os
import sys
from pathlib import Path

# Make the `app` package importable regardless of the working directory.
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Never launch/observe Phoenix during tests.
os.environ["PHOENIX_ENABLED"] = "false"
os.environ["PHOENIX_LAUNCH"] = "false"

# Deterministic default for the strict-evaluation flag (individual tests override).
os.environ.setdefault("STRICT_KNOWLEDGE_BASE", "true")
