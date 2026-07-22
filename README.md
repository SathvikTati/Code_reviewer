# Code Review Assistant

An AI-powered code review assistant that audits **Python** GitHub repositories using
**GraphRAG** — a repository knowledge graph (Neo4j) combined with Retrieval-Augmented
Generation over a software-engineering best-practices knowledge base — instead of relying
solely on an LLM's built-in knowledge.

The LLM only *reasons* over retrieved code structure and coding standards; all parsing,
dependency extraction, and graph construction are deterministic.

---

## How it works

```
GitHub URL
   │
   ▼
Clone ──▶ Scan (.py) ──▶ Parse (AST) ──▶ Build Repository Graph (Neo4j)
                                                │
                                                ▼
        Group files into logical modules + retrieve KB standards per module
        (Neo4j vector index, biased to each module's focus areas)
                                                │
                                                ▼
   ┌──────────── PHASE 1 · MAP (one call per module) ─────────────┐
   │  send the module's REAL source code + its standards to the   │
   │  LLM  ──▶  concise per-module review (findings, missing tests)│
   └──────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
   ┌──────────── PHASE 2 · REDUCE (one final call) ───────────────┐
   │  send all module reviews to the LLM  ──▶  final audit report  │
   └──────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
                            Delete clone · return report + token usage
```

- **Actual code is reviewed** — Phase 1 sends each module's real source (capped by
  `review.*` limits), not just names, so findings are grounded in the code.
- **Map-reduce** — per-module reviews (map) are consolidated by a final call (reduce),
  which keeps each LLM call bounded and scales to larger repositories.
- **Repository graph** — nodes `Repository`, `PythonFile`, `PythonClass`, `PythonFunction`
  linked by `CONTAINS`, `DECLARES`, `CALLS`, `INHERITS_FROM`, `IMPORTS`.
- **Knowledge base** — OWASP (secure coding + Top 10), SOLID, Clean Code, PEP 8/257/484,
  error handling, testing, performance, packaging, and design-pattern docs, chunked and
  embedded into a Neo4j **vector index**.
- **Hierarchical retrieval** — files are grouped into logical modules (authentication, api,
  services, database, …); each module retrieves only the standards relevant to its focus.
- **Observability** — every run is traced in **Arize Phoenix** with per-stage timing and
  token counts (one span per module review + the final report).

---

## Tech stack

| Concern            | Technology                                   |
| ------------------ | -------------------------------------------- |
| API                | FastAPI + Uvicorn                            |
| Graph database     | Neo4j 5.11+ (native vector index)            |
| LLM                | Qwen2.5-Coder 7B via Ollama (local) **or** OpenAI |
| Embeddings         | `nomic-embed-text` via Ollama (local) **or** OpenAI |
| Parsing            | Python `ast`                                 |
| Observability      | Arize Phoenix (OpenInference / OpenTelemetry)|
| Config             | JSON control panel + Markdown prompt templates |

---

## Prerequisites

1. **Python 3.12** and the project virtualenv.
2. **Neo4j 5.11+** running (vector index support). Quick start with Docker:
   ```bash
   docker run -d --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:latest
   ```
3. **Ollama** with the required models pulled:
   ```bash
   ollama pull qwen2.5-coder:7b
   ollama pull nomic-embed-text
   ```

---

## Setup

```bash
cd backend
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
```

Configure connections/secrets in `backend/.env`:

```ini
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# --- Provider selection (ollama | openai), chosen independently ---
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama

# --- Evaluation ---
# true  = grade STRICTLY against the knowledge base only (no outside knowledge,
#         every finding must cite a retrieved standard)
# false = looser "reference mode" (standards are a guide; general practices allowed)
STRICT_KNOWLEDGE_BASE=true

# --- Ollama (local) ---
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_EMBED_MODEL=nomic-embed-text

# --- OpenAI (used when *_PROVIDER=openai) ---
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
# OPENAI_BASE_URL=            # optional: Azure / OpenAI-compatible endpoint

# --- Phoenix observability ---
PHOENIX_ENABLED=true
PHOENIX_LAUNCH=false                                   # run Phoenix separately (recommended)
PHOENIX_PROJECT=code-review
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_WORKING_DIR=/absolute/path/to/code_reviewer/.phoenix
```

### Choosing a provider: Ollama or OpenAI

The LLM and the embedding model are selected independently via `LLM_PROVIDER`
and `EMBEDDING_PROVIDER` (`ollama` by default, or `openai`). This lets you mix,
e.g. local embeddings with an OpenAI LLM.

| Variable             | `ollama` (default)        | `openai`                      |
| -------------------- | ------------------------- | ----------------------------- |
| `LLM_PROVIDER`       | `OLLAMA_MODEL`            | `OPENAI_MODEL`, `OPENAI_API_KEY` |
| `EMBEDDING_PROVIDER` | `OLLAMA_EMBED_MODEL`      | `OPENAI_EMBED_MODEL`, `OPENAI_API_KEY` |

To use OpenAI for everything:

```ini
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

> **Re-ingest after switching `EMBEDDING_PROVIDER`.** The Neo4j vector index is
> sized to the embedding dimension at ingest time (nomic-embed-text = 768,
> text-embedding-3-small = 1536). Changing embedding provider requires re-running
> the ingest command below so the index matches. Switching only `LLM_PROVIDER`
> needs no re-ingest.

### Running the tests

The suite runs with **no external infrastructure** — Neo4j, Ollama, and OpenAI are
mocked, and Phoenix tracing is disabled.

```bash
cd backend
./venv/bin/python -m pip install -r requirements-dev.txt
./venv/bin/python -m pytest
```

Covers parsing, module grouping, chunking, context/prompt building (incl. strict
mode), settings/prompt rendering, embeddings (truncation + provider selection),
the vector-search query construction, hierarchical retrieval, token accounting,
tracing no-ops, the provider factory, and the API endpoints.

### Ingest the knowledge base (one time)

Builds the `KnowledgeChunk` nodes and the Neo4j vector index from `resources/knowledge_base/`.
Re-run whenever you edit the knowledge base.

```bash
cd backend
./venv/bin/python -m scripts.ingest_knowledge_base
```

---

## Running

Use **two terminals** so Phoenix persists across app reloads.

```bash
# Terminal 1 — Phoenix observability server (persistent, isolated data dir)
cd backend
./run_phoenix.sh                       # UI at http://localhost:6006

# Terminal 2 — the API
cd backend
uvicorn app.main:app --reload          # API at http://localhost:8000
```

> Start Phoenix via `./run_phoenix.sh` (not a bare `phoenix serve`) — the script points
> `PHOENIX_WORKING_DIR` at a fresh, project-local `.phoenix/` dir, avoiding the stale global
> `~/.phoenix` DB.

### Analyze a repository

```bash
curl -X POST http://localhost:8000/review/analyze \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/owner/repo"}'
```

Response:

```json
{
  "analysis": "…the audit report (executive summary, security, code quality, …)…",
  "usage": {
    "llm_calls": 1,
    "embedding_calls": 9,
    "prompt_tokens": 3421,
    "completion_tokens": 812,
    "total_tokens": 4233
  }
}
```

Open **http://localhost:6006** → project `code-review` to see the trace: the
`analyze_repository` span with `clone / scan / parse / build_graph / hierarchical_retrieval /
ollama.generate` children, plus token counts and per-stage timing.

---

## The control panel: `resources/`

Everything content/config lives in the root `resources/` folder so it can be tuned without
touching Python. Override its location with the `RESOURCES_DIR` env var.

```
resources/
├── config.json          # categories, chunking, retrieval tuning, module grouping rules
├── prompts/             # editable prompt templates ({{...}} tokens)
│   ├── module_review.md      # Phase 1 (map): review one module's real code
│   ├── final_report.md       # Phase 2 (reduce): consolidate module reviews
│   ├── strict_directive.md   # evaluation header injected when strict mode is on
│   ├── lenient_directive.md  # evaluation header for reference mode
│   ├── repository_report.md  # legacy single-call template
│   └── qa.md
└── knowledge_base/      # best-practices docs; folder name = review category
    ├── security/         # OWASP secure coding, OWASP Top 10, secrets & auth
    ├── code_quality/     # Clean Code, PEP 8, error handling & logging, naming & docstrings
    ├── performance/      # Python performance optimization
    ├── maintainability/  # Python best practices, packaging, type hints (PEP 484)
    ├── testing/          # testing best practices, pytest / fixtures / coverage
    └── architecture/     # SOLID, design patterns, API design & layering
```

The knowledge base is standards-based (OWASP, SOLID, Clean Code, PEP 8/257/484,
12-factor, testing best practices). Add a `.md` file under the right category
folder and re-ingest — each `##` section becomes a retrievable chunk.

### `config.json` highlights

- `categories` / `category_folders` — review dimensions and the KB folder→category mapping.
- `chunking.section_heading` — markdown heading that starts a new chunk.
- `embedding.max_input_chars` — truncation guard for the embedding model's context window.
- `retrieval.repository_top_k` / `module_top_k` / `category_overfetch` — retrieval sizing.
- `review.max_file_chars` / `max_module_chars` / `max_files_per_module` — caps on how much
  real source code is sent to the LLM per file / per module (Phase 1).
- `modules` — logical module rules. Each file is assigned to the **first** module whose
  keywords match a whole word in its path; `categories` biases that module's KB retrieval.
  The final `general` entry (empty keywords) is the catch-all.

To add or retune a module, edit the `modules` list — no code changes needed.

### Strict knowledge-base evaluation

`STRICT_KNOWLEDGE_BASE` (env, default `true`) controls how the audit is graded:

- **`true` (strict):** the LLM may judge the code **only** against the retrieved
  standards — no outside best-practice knowledge — and **every finding must cite a
  standard** as `[Category] Title`. If no standard supports a concern, it is
  omitted. This makes results reproducible and traceable to the knowledge base, so
  the quality of the audit is driven by the quality/coverage of the KB.
- **`false` (reference mode):** standards are a guide; the model may also apply
  well-established Python practices.

The directive text itself is **not hardcoded** — it lives in
[resources/prompts/strict_directive.md](resources/prompts/strict_directive.md) and
[lenient_directive.md](resources/prompts/lenient_directive.md), and the prompt builder
injects the right one into the module-review prompt. Because strict mode can only
surface issues the KB covers, keep the knowledge base broad and accurate.

---

## Observability & token usage

- LLM calls are traced as **LLM** spans with `llm.token_count.{prompt,completion,total}` and
  Ollama timing (`total/load/prompt_eval/eval` in ms).
- Embedding calls are traced as **EMBEDDING** spans (model, dimensions, input size).
- Each analysis returns an aggregate `usage` object (see above) and stamps the whole-run token
  total on the root span.

> Ollama's embeddings endpoint doesn't return token counts for `nomic-embed-text`, so
> `prompt_tokens`/`completion_tokens` reflect **LLM** tokens; embeddings are reported as a
> call count.

Tracing degrades gracefully: if `PHOENIX_ENABLED=false` or the server is down, the app runs
normally and spans become no-ops.

---

## Project structure

```
code_reviewer/
├── resources/                     # control panel (config, prompts, knowledge base)
├── .phoenix/                      # Phoenix trace data (gitignored)
└── backend/
    ├── run_phoenix.sh             # persistent Phoenix launcher
    ├── requirements.txt
    ├── .env
    ├── scripts/
    │   └── ingest_knowledge_base.py
    └── app/
        ├── main.py                # FastAPI app + tracing startup
        ├── api/                   # /review/analyze controller
        ├── config/                # settings (loads resources/)
        ├── dto/                   # request models
        ├── models/                # Repository / Python* domain models
        ├── telemetry/             # Phoenix tracing + token-usage accounting
        └── services/
            ├── github/            # clone (outside reload tree) + cleanup
            ├── scanner/           # recursive .py discovery
            ├── parser/            # AST extraction
            ├── graph/             # Neo4j graph + vector-index helpers
            ├── rag/               # embeddings, chunker, KB ingest,
            │                      #   knowledge/hierarchical retrievers, module grouper
            ├── builders/          # context + prompt builders
            ├── llm/               # Ollama + OpenAI clients + provider factory
            └── review/            # map-reduce orchestration
```

---

## Troubleshooting

- **`--reload` restarts mid-request** — clones now write to the OS temp dir (outside the
  watched `backend/`), so this no longer happens. Override the clone location with `CLONE_DIR`.
- **`input length exceeds the context length` (embeddings)** — large module summaries are
  truncated to `embedding.max_input_chars`; lower it if you still hit the model's limit.
- **Phoenix `Cannot return null for non-nullable field Project.name` / `Span.spanId`** — caused
  by a stale global `~/.phoenix` DB and/or repeated in-process launches under `--reload`. Fixed
  by running one persistent server via `./run_phoenix.sh` (fresh `PHOENIX_WORKING_DIR`) with
  `PHOENIX_LAUNCH=false`. To reset the global DB: `mv ~/.phoenix ~/.phoenix.old`.
- **Neo4j `db.index.vector.queryNodes is deprecated`** — a harmless warning on newer Neo4j;
  the query still works.

---

## Roadmap

- Structured JSON findings (severity/category/file/line/fix) per module, in addition to the
  Markdown report.
- Deterministic static analysis (bandit / ruff / radon / mypy) fed into Phase 1 to ground and
  cross-check LLM findings.
- `Folder` / `Module` nodes and `KnowledgeChunk`↔code links in the graph (deeper GraphRAG).
- Additional language parsers (Java, JavaScript, Go, C++) behind the same architecture.

Done recently: **actual source code is now reviewed** (Phase 1 sends real code, not just
names), and **per-module reviews are aggregated** via a final reduce call.
