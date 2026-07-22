# How It Works — Detailed Workflow

This document walks through **everything** the Code Review Assistant does, step by
step, with the actual files and functions involved. Read it top to bottom to
understand the whole system.

---

## 1. The big picture

The system has **two phases**:

- **Phase A — Knowledge Base ingestion** (run once, offline): load best-practice
  docs, embed them, and store them in Neo4j as a searchable vector index.
- **Phase B — Repository analysis** (per request): clone a repo, turn it into a
  graph, retrieve the relevant standards, and have an LLM write an audit.

Both phases share one **Neo4j** database, which effectively holds two things:

```
Neo4j
├── Knowledge graph of best practices   → KnowledgeChunk nodes (+ vector index)   [persistent]
└── Code graph of the repo being audited → Repository/File/Class/Function nodes   [rebuilt each run]
```

The code graph is wiped and rebuilt on every analysis; the knowledge base is
built once and reused (see `clear_database()` which deliberately preserves
`KnowledgeChunk` nodes).

---

## 2. The moving parts

```
resources/                      ← "control panel" (edit these, no code changes)
├── config.json                 ← categories, chunking, retrieval sizes, module rules
├── prompts/                    ← LLM prompt templates ({{context}}, {{standards}})
│   ├── repository_report.md
│   └── qa.md
└── knowledge_base/             ← best-practice docs; folder name = category
    ├── security/  code_quality/  performance/
    └── maintainability/  testing/  architecture/

backend/app/
├── main.py                     ← FastAPI app, serves frontend, starts tracing
├── api/review_controller.py    ← POST /review/analyze
├── config/settings.py          ← loads resources/ (config + prompts)
├── dto/                         ← request models
├── models/                      ← Repository, PythonFile, PythonClass, ...
├── telemetry/
│   ├── tracing.py              ← Phoenix / OpenTelemetry spans
│   └── usage.py                ← per-request token accounting
└── services/
    ├── github/clone_service.py       ← clone + delete repo
    ├── scanner/scanner_service.py    ← find .py files
    ├── parser/ParserService.py       ← AST → structure
    ├── graph/
    │   ├── graph_service.py          ← raw Neo4j driver (nodes, rels, vector index)
    │   └── graph_builder.py          ← builds the code graph
    ├── rag/
    │   ├── embedding_service.py      ← embeddings (Ollama or OpenAI)
    │   ├── chunker.py                ← splits KB docs into chunks
    │   ├── knowledge_base_service.py ← ingests KB into Neo4j
    │   ├── knowledge_retriever.py    ← semantic search over KB
    │   ├── module_grouper.py         ← groups files into logical modules
    │   ├── hierarchical_retriever.py ← repo → module → standards
    │   └── retriever.py              ← Cypher queries over the code graph
    ├── builders/
    │   ├── context_builder.py        ← turns graph data into prompt text
    │   └── prompt_builder.py         ← fills the prompt templates
    ├── llm/
    │   ├── ollama_service.py         ← local LLM
    │   ├── openai_service.py         ← OpenAI LLM
    │   └── factory.py                ← picks provider from env
    └── review/review_service.py      ← orchestrates the whole pipeline

frontend/index.html             ← single-page UI (served by FastAPI at /)
scripts/ingest_knowledge_base.py← one-time KB ingest entry point
run_phoenix.sh                  ← starts the Phoenix observability server
```

---

## 3. Phase A — Knowledge Base ingestion (run once)

Command: `python -m scripts.ingest_knowledge_base` → `KnowledgeBaseService.ingest()`.

```
resources/knowledge_base/**/*.md
        │
        ▼  MarkdownChunker.chunk_file()
   split each doc into section-level chunks
   (category = top folder name, e.g. security → "Security")
        │
        ▼  for each chunk:
   EmbeddingService.embed_document(text)  → 768-dim (nomic) or 1536-dim (OpenAI) vector
        │
        ▼  GraphService.create_node("KnowledgeChunk", {...})     ← id, text, category, source, title
   GraphService.set_node_vector(... "embedding", vector)         ← stores the vector
        │
        ▼  GraphService.create_vector_index("knowledge_chunk_embedding", ...)
   builds the Neo4j native vector index over KnowledgeChunk.embedding
```

Key points:
- **Chunking** ([chunker.py](backend/app/services/rag/chunker.py)): one chunk per
  `##` section. Each chunk carries `category` (from the folder), `source` (file),
  and `title` (doc + heading). This is why retrieval can filter by category.
- **Embeddings** are generated locally by Ollama (`nomic-embed-text`) or by OpenAI,
  depending on `EMBEDDING_PROVIDER`.
- **Dimension matters**: the vector index is created with the dimension of the first
  embedding. nomic = 768, OpenAI `text-embedding-3-small` = 1536. If you switch
  embedding provider you must **re-ingest**, or query vectors won't match the index.
- Re-running ingest clears only `KnowledgeChunk` nodes and rebuilds them; the code
  graph is untouched.

---

## 4. Phase B — Repository analysis (per request)

Entry point: `POST /review/analyze {"github_url": "..."}` →
[review_controller.py](backend/app/api/review_controller.py) →
`ReviewService.analyze_repository()` in
[review_service.py](backend/app/services/review/review_service.py).

Here is the full pipeline, in order. Each numbered step is wrapped in a Phoenix
span so you can see its timing.

```
POST /review/analyze
   │
   ├─ usage.start()                     ← begin token counter for this request
   │
   ├─ (1) CloneService.clone_repository(url)
   │        git clone → OS temp dir (outside backend/, so --reload ignores it)
   │        → Repository(name, github_url, local_path)
   │
   ├─ (2) RepositoryScanner.scan(repo)
   │        rglob "*.py" → list of PythonFile(id, name, relative_path, absolute_path, size)
   │
   ├─ (3) ParserService.parse(repo)
   │        for each file: ast.parse (wrapped in try/except — bad files are skipped)
   │        extract: imports, classes (+ base classes, methods), functions
   │                 (+ parameters, decorators, calls)
   │
   ├─ (4) GraphBuilder.build(repo)
   │        create_constraints() · clear_database() (keeps KnowledgeChunk)
   │        create Repository node, then:
   │          _create_nodes       → File/Class/Function nodes + CONTAINS/DECLARES
   │          _create_calls       → CALLS (matched by function name)
   │          _create_inheritance → INHERITS_FROM
   │          _create_imports     → IMPORTS (matched by module path)
   │
   ├─ (5) HierarchicalRetriever.retrieve()          ← the GraphRAG core (see §5)
   │        returns { modules: [ {name, categories, files, standards}, ... ] }
   │
   ├─ (6) PHASE 1 · MAP — for each module:
   │        _collect_module_code(module)            ← read REAL source from disk (capped by review.*)
   │        PromptBuilder.build_module_review_prompt(name, categories, code, standards)
   │           → fills resources/prompts/module_review.md (+ strict/lenient directive)
   │        llm_service.generate(prompt)            ← one call per module → module summary
   │
   ├─ (7) PHASE 2 · REDUCE — once:
   │        PromptBuilder.build_final_report_prompt(repo, all module summaries)
   │           → fills resources/prompts/final_report.md
   │        llm_service.generate(prompt)            ← Ollama or OpenAI (factory) → final report
   │        (every generate() records prompt/completion tokens into usage + a span)
   │
   └─ finally:
         CloneService.delete_repository(local_path)  ← no user code left on disk
         tracing.flush()                             ← push spans to Phoenix now

Response: { "analysis": "<markdown report>", "usage": { total_tokens, ... } }
```

### Step details

**(1) Clone** — [clone_service.py](backend/app/services/github/clone_service.py).
Clones into the OS temp dir (`code_reviewer_repos/`), not inside `backend/`. This
was a real bug fix: `uvicorn --reload` watches `backend/`, so cloning there caused
the server to restart mid-request. Override the location with `CLONE_DIR`.

**(2) Scan** — [scanner_service.py](backend/app/services/scanner/scanner_service.py).
Recursively finds every `.py` file and records paths + size into `PythonFile` models.

**(3) Parse** — [ParserService.py](backend/app/services/parser/ParserService.py).
Uses Python's `ast`. For each file it walks the top-level nodes:
- `Import` / `ImportFrom` → `PythonImport(module=...)`
- `ClassDef` → `PythonClass` with `base_classes`, and each method as `PythonFunction`
- `FunctionDef` → module-level `PythonFunction` with `parameters`, `decorators`, and
  the names of functions it `calls` (found via `ast.walk`).
A file that fails to parse (invalid syntax, bad encoding, Python 2, etc.) is
**skipped** and recorded in `parse_error` — one bad file never aborts the run.

**(4) Build graph** — [graph_builder.py](backend/app/services/graph/graph_builder.py)
via [graph_service.py](backend/app/services/graph/graph_service.py). See §6 for the
schema. `CALLS` is resolved by matching call names to function names (best-effort,
can over-match); `IMPORTS` maps a file's imports to other files by module path.

**(9) LLM** — chosen by `create_llm_service()` in
[factory.py](backend/app/services/llm/factory.py) based on `LLM_PROVIDER`
(`ollama` → [ollama_service.py](backend/app/services/llm/ollama_service.py),
`openai` → [openai_service.py](backend/app/services/llm/openai_service.py)). Both
expose `generate(prompt) -> str` and record token usage + a Phoenix LLM span.

---

## 5. The GraphRAG core: hierarchical retrieval

This is what makes the system "GraphRAG" rather than a flat prompt.
[hierarchical_retriever.py](backend/app/services/rag/hierarchical_retriever.py)

```
(a) Retriever.retrieve_repository_tree()          [retriever.py]
      Cypher: for each PythonFile, collect its class names and function names
      → rows: [ {file, classes:[...], functions:[...]}, ... ]

(b) ModuleGrouper.group(rows)                      [module_grouper.py]
      assign each file to the FIRST logical module whose keywords match a
      whole word in its path (config.json → modules).
      e.g. auth/login.py → "authentication"; models/user.py → "database"
      unmatched files → "general" (catch-all)
      Matching is whole-word + singularized:
        'models' matches 'model', but 'tokenizer' does NOT match 'token',
        and 'author' does NOT match 'auth'   (a deliberate fix)

(c) For each module:
      summary = list of its files + class/function names
      query   = "<module name>.\n<summary>"
      standards = KnowledgeRetriever.search(query, k=module_top_k,
                                            categories=module.categories)
```

`KnowledgeRetriever.search()`
([knowledge_retriever.py](backend/app/services/rag/knowledge_retriever.py)):
```
EmbeddingService.embed_query(query)   → query vector
        │
        ▼  Cypher: CALL db.index.vector.queryNodes('knowledge_chunk_embedding', k, vector)
   returns the k most similar KnowledgeChunk nodes (cosine similarity)
        │
        ▼  if categories given: over-fetch (k × category_overfetch), then
           filter WHERE node.category IN categories, LIMIT k
```

So each module pulls only the standards relevant to **both** its code (semantic
similarity) **and** its focus categories (e.g. an `authentication` module is biased
toward `Security`; a `database` module toward `Security`, `Performance`,
`Architecture`). This keeps irrelevant standards out of the prompt.

The result structure returned to the review service:
```json
{
  "modules": [
    {
      "name": "services",
      "categories": ["Architecture", "Maintainability", "Code Quality"],
      "files": [ {"relative_path": "app/x.py", "classes": ["X"], "functions": ["run"]} ],
      "standards": [ {"category": "...", "title": "...", "text": "...", "score": 0.83} ]
    }
  ]
}
```

---

## 6. The Neo4j graph schema

**Code graph** (rebuilt every analysis):

```
(:Repository {id, name, github_url})
      │ CONTAINS
      ▼
(:PythonFile {id, name, relative_path})
      │ DECLARES
      ├────────────► (:PythonClass {id, name, line_number})
      │                     │ DECLARES        │ INHERITS_FROM
      │                     ▼                 ▼
      │              (:PythonFunction)   (:PythonClass)
      │ DECLARES
      ▼
(:PythonFunction {id, name, line_number})
      │ CALLS
      ▼
(:PythonFunction)

(:PythonFile) ─IMPORTS→ (:PythonFile)
```

**Knowledge graph** (persistent):
```
(:KnowledgeChunk {id, text, category, source, title, embedding[]})
   indexed by → VECTOR INDEX knowledge_chunk_embedding (cosine)
```

Relationships: `CONTAINS`, `DECLARES`, `CALLS`, `INHERITS_FROM`, `IMPORTS`.
Uniqueness constraints exist on the `id` of each code node type and on
`KnowledgeChunk.id`.

---

## 7. Prompt assembly

- **Context** ([context_builder.py](backend/app/services/builders/context_builder.py)):
  `build_hierarchical_context()` emits a readable block — repository header, then
  each module with its files/classes/functions and the titles of standards that
  apply to it. `merge_standards()` collects the full standard texts, de-duplicated
  by `(source, title)` and sorted by relevance score.
- **Prompt** ([prompt_builder.py](backend/app/services/builders/prompt_builder.py)):
  loads `resources/prompts/repository_report.md` via
  [settings.py](backend/app/config/settings.py) and substitutes `{{context}}`,
  `{{standards}}`, and `{{strict_directive}}`. The template is strict: every finding
  must cite real code, no inventing topics (auth/DB/secrets) that aren't present,
  severity labels, a fixed section layout, and a justified 0–100 health score.
- **Strict knowledge-base mode** (`STRICT_KNOWLEDGE_BASE`, default `true`): the
  prompt builder injects a directive requiring the LLM to grade the code **only**
  against the retrieved standards and to cite `[Category] Title` for every finding.
  Set it `false` for looser "reference mode".

Because prompts and config live in `resources/` and are read at request time,
editing them takes effect **without restarting** the server (settings caches per
process, so a restart is only needed if the process is already running when you
edit — with `--reload`, code edits restart it anyway).

---

## 8. Provider abstraction (Ollama ↔ OpenAI)

Selected independently via env, so you can mix (e.g. local embeddings + OpenAI LLM):

| Env var              | `ollama` (default)   | `openai`                          |
| -------------------- | -------------------- | --------------------------------- |
| `LLM_PROVIDER`       | Qwen via Ollama      | `OPENAI_MODEL` + `OPENAI_API_KEY` |
| `EMBEDDING_PROVIDER` | nomic-embed-text     | `OPENAI_EMBED_MODEL` + key        |

- LLM: `factory.create_llm_service()` returns `OllamaService` or `OpenAIService`.
- Embeddings: `EmbeddingService`
  ([embedding_service.py](backend/app/services/rag/embedding_service.py)) is a facade
  that picks `_OllamaEmbedder` or `_OpenAIEmbedder`. Ollama uses nomic's
  `search_query:` / `search_document:` prefixes; OpenAI does not. Shared truncation
  (`embedding.max_input_chars`), tracing, and usage accounting live in the facade.

**Switching `EMBEDDING_PROVIDER` requires re-ingesting** (vector dimension changes).

---

## 9. Observability & token usage

- **Tracing** ([tracing.py](backend/app/telemetry/tracing.py)): manual
  OpenInference/OpenTelemetry spans exported to **Arize Phoenix**. The pipeline is a
  `CHAIN` span (`analyze_repository`) with child spans for clone/scan/parse/
  build_graph/hierarchical_retrieval, plus `LLM` spans (with token counts + Ollama
  timing) and `EMBEDDING` spans. No-op safe: if Phoenix is off/down, the app still
  runs.
- **Token usage** ([usage.py](backend/app/telemetry/usage.py)): a `UsageCollector`
  kept in a `ContextVar` for the request. The LLM and embedding services add to it;
  the review service returns `usage` in the response and stamps the total on the root
  span. (Ollama's embeddings endpoint returns no token counts, so
  `prompt_tokens`/`completion_tokens` reflect LLM tokens; embeddings are a call
  count.)

Run Phoenix as a **persistent** server via `./run_phoenix.sh` (sets an isolated
`PHOENIX_WORKING_DIR`), with `PHOENIX_LAUNCH=false`, so `--reload` never restarts or
corrupts it.

---

## 10. Frontend

[frontend/index.html](frontend/index.html) — a single self-contained page served by
FastAPI at `/` (same origin → no CORS needed). It POSTs the URL to
`/review/analyze`, shows a spinner + elapsed timer while waiting, and renders the
returned Markdown report with a small built-in Markdown → HTML converter (no
external libraries). GeeksforGeeks-style green/light theme.

---

## 11. End-to-end example

Request: `{"github_url": "https://github.com/psf/requests"}`

1. Clone → `/tmp/.../requests_<timestamp>/`.
2. Scan → ~30 `.py` files.
3. Parse → classes like `Session`, functions like `get`, `request`, imports, calls.
4. Graph → `Repository`→`PythonFile`→`PythonClass`/`PythonFunction`, plus CALLS/IMPORTS.
5. Group → files land in modules: `api` (`api.py`), `services` (`sessions.py`),
   `utilities` (`utils.py`), `general`, etc.
6. Retrieve → for the `api` module, embed its file/function names and pull the top
   `Security`/`Architecture`/`Maintainability` chunks (e.g. "Injection Prevention",
   "Facade", "Type Hints").
7. Build context + merge standards → one grounded prompt.
8. LLM → returns a Markdown audit (summary, findings by category with severity,
   prioritized recommendations, health score).
9. Cleanup → clone deleted; spans flushed to Phoenix; response includes token usage.

---

## 12. Design decisions & fixes worth knowing

- **Clone outside `backend/`** — prevents `--reload` from killing requests.
- **Per-file parse guard** — one unparseable file can't crash the analysis.
- **Embedding truncation** — large module summaries are trimmed to fit the embed
  model's context window (`embedding.max_input_chars`).
- **Whole-word module matching** — fixed false positives (`tokenizer`≠`token`,
  `author`≠`auth`) that were fabricating an "authentication" module.
- **Strict, grounded prompt** — the model must cite real code and must not invent
  topics that aren't present; this is the real guard against hallucinated findings.
- **Knowledge base survives `clear_database()`** — the code graph is per-run; the KB
  is persistent.
- **Isolated Phoenix data dir + persistent server** — avoids the stale-DB GraphQL
  errors and data loss under `--reload`.

---

## 13. Known limitations / roadmap

- The final report is a **single** LLM call over the whole hierarchical context; very
  large repos can exceed the model's context window. Next step: per-module reviews
  producing structured JSON, aggregated into the final report.
- `CALLS` is name-based (can over-match across files with same-named functions).
- No `Folder`/`Module` nodes in the graph yet (grouping is done in Python); and no
  `KnowledgeChunk`↔code links yet (deeper GraphRAG).
- Python only, by design — additional language parsers can plug in behind the same
  architecture.
```
