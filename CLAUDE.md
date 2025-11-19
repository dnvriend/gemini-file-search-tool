# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`gemini-file-search-tool` is a Python CLI tool and library for managing Gemini File Search stores, uploading documents, and querying with Google's fully managed RAG system. Built with modern Python tooling (uv, mise, click) using Python 3.14+.

## Architecture

The codebase follows a modular architecture with clear separation between CLI, core library, and utilities:

```
gemini_file_search_tool/
├── __init__.py              # Public API exports for library usage
├── cli.py                   # Main CLI entry point (Click group)
├── core/                    # Core library functions (importable)
│   ├── cache.py            # Local cache management (mtime-based optimization)
│   ├── client.py           # Gemini API client management
│   ├── stores.py           # Store CRUD operations
│   ├── documents.py        # Document operations (list, upload)
│   ├── query.py            # Query operations
│   └── query_enhancement.py # Query enhancement engine
├── prompts/                 # Enhancement prompt templates
│   ├── generic_rag.py      # Generic RAG optimization template
│   ├── code_rag.py         # Code-specific optimization template
│   └── obsidian.py         # Obsidian/PKM optimization template
├── commands/                # CLI command implementations
│   ├── store_commands.py   # Store management commands
│   ├── document_commands.py # Document management commands
│   └── query_commands.py   # Query commands (with enhancement integration)
└── utils.py                 # Shared utilities (normalize_store_name, output_json, aggregate_costs, etc.)
```

### Key Design Principles

1. **Separation of Concerns**: Core library functions (in `core/`) are independent of CLI and can be imported for programmatic use
2. **CLI Wrapping**: Commands in `commands/` wrap core functions with Click decorators and error handling
3. **Exception-Based Errors**: Core functions raise exceptions (not sys.exit), CLI handles formatting and exit codes
4. **Composability**: JSON output to stdout, logs to stderr for easy piping
5. **Flat Command Structure**: Commands like `create-store`, `list-stores`, `upload`, `query` (no nested subcommands)

## Development Commands

### Quick Start
```bash
# Install dependencies
make install

# Run locally during development
uv run gemini-file-search-tool --help
uv run gemini-file-search-tool create-store "test"
uv run gemini-file-search-tool upload "*.pdf" --store "test"

# Or use make run
make run ARGS="list-stores"
make run ARGS="upload document.pdf --store test"

# Run specific test
uv run pytest tests/test_utils.py
uv run pytest tests/test_utils.py::test_function_name -v
```

### Quality Checks
```bash
make format      # Auto-format with ruff
make lint        # Lint with ruff
make typecheck   # Type check with mypy (strict mode)
make test        # Run pytest suite
make check       # Run lint + typecheck + test
make pipeline    # Full pipeline: format + check + build + install-global
```

### Build & Install
```bash
make build           # Build package with uv
make install-global  # Install globally with uv tool
make uninstall-global
make clean          # Remove build artifacts and caches
```

## Code Standards

- **Type safety**: Strict mypy with type hints required for all functions
- **Line length**: 100 characters (configured in pyproject.toml)
- **Formatting**: ruff (auto-fix with `make format`)
- **Docstrings**: Required for all public functions with Args, Returns, and Raises sections
- **Module headers**: All .py files include AI-generated code acknowledgment
- **Error handling**: Core functions raise exceptions, CLI catches and formats them

## CLI Commands

### Store Commands (store_commands.py)
- `create-store NAME` - Create new store
- `list-stores` - List all stores
- `get-store NAME` - Get store details
- `update-store NAME --display-name NAME` - Update store
- `delete-store NAME [--force]` - Delete store

### Document Commands (document_commands.py)
- `list-documents --store NAME [-v|-vv|-vvv]` - List documents in store
  - Supports multi-level verbosity for logging
- `upload FILES... --store NAME [OPTIONS] [-v|-vv|-vvv]` - Upload files (supports globs)
  - **Note**: FILES is positional (changed from `--input`)
  - Supports glob patterns: `*.pdf`, `docs/**/*.md`
  - Options: `--title`, `--url`, `--file-name`, `--max-tokens`, `--max-overlap`, `--num-workers`, `--skip-validation`, `--ignore-gitignore`, `--dry-run`
  - **Verbosity**: `-v` (INFO), `-vv` (DEBUG), `-vvv` (TRACE with library logging)
  - **Intelligent Caching**: Automatically tracks uploaded files to skip unchanged files
    - Uses mtime-based optimization (O(1) check before O(n) hash calculation)
    - Cache location: `~/.config/gemini-file-search-tool/stores/`
    - Per-store isolation prevents cache overwrites
    - See `core/cache.py` for implementation details
  - **System File Filtering**: Automatically skips `__pycache__`, `.pyc`, `.DS_Store`, etc.
  - **Gitignore Support**: Automatically respects `.gitignore` patterns (use `--ignore-gitignore` to disable)
  - **Dry-Run Mode**: Use `--dry-run` to preview files without uploading (returns JSON with file paths and sizes)
  - **Empty File Handling**: Skips 0-byte files with warning (not error)
  - **MIME-Type Support**: Registers `.toml`, `.env` files automatically

### Query Commands (query_commands.py)
- `query PROMPT --store NAME [OPTIONS]` - Query documents with optional enhancement
  - **PROMPT**: First positional argument - the query text
  - **Enhancement Mode**: `--enhance-mode {generic|code-rag|obsidian}` - Query optimization strategy
    - `generic` - Generic RAG optimization for better document retrieval
    - `code-rag` - Code-specific optimization for semantic code search
    - `obsidian` - Obsidian/PKM optimization for personal knowledge bases
  - **Enhancement Model**: `--enhancement-model {flash|pro}` - Model for enhancement (default: flash)
  - **Query Model**: `--query-model {flash|pro}` - Model for RAG query (default: flash)
  - **Observability**: `--show-enhancement` displays enhanced query, `--dry-run-enhancement` previews without executing
  - **Cost Tracking**: `--show-cost` includes separate costs for enhancement + query
  - **Verbosity**: `-v` displays token usage and cost info, `-vv` shows API operations, `-vvv` shows HTTP traces
  - **Metadata Filtering**: `--metadata-filter "key=value"` - Filter documents by metadata
  - **Grounding**: `--query-grounding-metadata` - Include source citations in response

## Library Usage

Core functions can be imported and used programmatically:

```python
from gemini_file_search_tool import (
    create_store, upload_file, query_store
)

store = create_store("my-store")
upload_file(Path("doc.pdf"), store["name"])
response = query_store(store["name"], "What is this about?")
```

See `__init__.py` for full API exports.

## Testing

```bash
# Run all tests
make test

# Run with verbose output
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=gemini_file_search_tool
```

## Query Enhancement

Query enhancement uses Gemini LLM to optimize user queries before RAG retrieval. **However, comprehensive benchmarks show that enhancement is counterproductive for most use cases.**

### ⚠️ Important: Enhancement is Disabled by Default

**Benchmark Results** (30 queries, 6 configurations):
- **None + Flash**: Quality 97.7/100, Cost $0.000125/query, Success 100% → Value: 156.1
- **Flash + Flash**: Quality 90.0/100, Cost $0.000758/query, Success 80% → Value: 23.7 (6.6x worse)
- **Pro Enhancement**: Quality 60-80/100, Cost $0.001-0.002/query, Success 20-60% → Value: 5.5-6.0 (28x worse)

**Key Findings:**
1. **Simple queries work best** - RAG relies on semantic similarity. Over-specifying queries with technical jargon that may not exist in documentation harms retrieval.
2. **Enhancement introduces risk** - Forces models to add detail, leading to over-specification and potential hallucination (especially with Pro).
3. **Flash is ideal for RAG** - 12x more cost-efficient than Pro, safer (sticks to facts), perfectly adequate for semantic matching.

**Reference**: Lewis et al., 2020. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (https://arxiv.org/abs/2005.11401)

See `references/benchmark-model-comparison-2025-11-16.md` and `references/rag-query-enhancement-analysis-2025-11-16.md` for detailed analysis.

### Enhancement Modes (Use Sparingly)

Enhancement should **only** be used for:
- Vague or poorly worded queries ("authentication stuff", "that database thing")
- Exploratory queries where you're unsure what you're looking for
- Cases where simple queries consistently fail to retrieve relevant documents

1. **Generic RAG** (`--enhance-mode generic`)
   - Optimizes queries for general document retrieval
   - Adds specificity, domain terminology, and explicit source attribution
   - Best for: Research papers, documentation, general knowledge bases

2. **Code-RAG** (`--enhance-mode code-rag`)
   - Optimizes for semantic code search
   - Requests file paths, function names, line numbers, and dependencies
   - Best for: Codebase exploration, architecture discovery, implementation finding
   - **Warning**: Can make queries too specific, reducing success rates

3. **Obsidian** (`--enhance-mode obsidian`)
   - Optimizes for personal knowledge management systems
   - Considers atomic notes, backlinks, tags, and personal terminology
   - Best for: Personal notes, Zettelkasten, PKM systems

### Model Selection

- **Flash (default)**: Fast, cost-effective, suitable for 95% of queries (~$0.00003 per enhancement)
- **Pro** (`--enhancement-model pro`): More sophisticated reasoning but 15x more expensive (~$0.0005 per enhancement) and prone to hallucination

### Cost Tracking

When using `--show-cost`, the output includes separate cost breakdowns:
```json
{
  "estimated_cost": {
    "enhancement": {
      "input_cost_usd": 0.00000375,
      "output_cost_usd": 0.000024,
      "total_cost_usd": 0.00002775,
      "model": "gemini-2.5-flash"
    },
    "query": {
      "input_cost_usd": 0.00001125,
      "output_cost_usd": 0.000096,
      "total_cost_usd": 0.00010725,
      "model": "gemini-2.5-flash"
    },
    "total_cost_usd": 0.000135,
    "currency": "USD"
  }
}
```

### Recommended Usage

```bash
# ✅ Recommended: No enhancement (best value, highest quality)
gemini-file-search-tool query "How does authentication work?" \
  --store "docs" --show-cost -v

# ✅ With grounding metadata (verify sources)
gemini-file-search-tool query "Explain the architecture" \
  --store "docs" --query-grounding-metadata --show-cost -v

# ⚠️ Use enhancement ONLY for vague queries
gemini-file-search-tool query "authentication stuff" \
  --store "docs" --enhance-mode code-rag --show-enhancement

# Preview enhancement without executing query
gemini-file-search-tool query "database schema" \
  --store "docs" --enhance-mode generic --dry-run-enhancement
```

## Code-RAG Capability

This tool enables **Code-RAG (Retrieval-Augmented Generation for Code)** - the ability to upload entire codebases and query them with natural language. This is powerful for:

- **Codebase Onboarding**: New developers can ask questions about architecture and implementation
- **Code Discovery**: Find where specific functionality is implemented without grepping
- **Architecture Analysis**: Understand design patterns and structural decisions
- **Documentation Generation**: Generate contextual documentation from actual code
- **AI Coding Assistants**: Build agents that can answer questions about your codebase

**Example Usage:**
```bash
# Upload a codebase
gemini-file-search-tool upload "src/**/*.py" --store "my-project" -v

# Query with natural language
gemini-file-search-tool query "How does the authentication system work?" \
  --store "my-project" -v

# Ask architectural questions
gemini-file-search-tool query "What design patterns are used?" \
  --store "my-project" --query-model pro
```

**Meta Note**: This tool itself was built using Code-RAG! During development, we uploaded the codebase to a Gemini File Search store and queried it to understand implementation details, find bugs, and plan features. The tool enables the very functionality it provides.

**Source Code Documentation**: All Python modules include comprehensive docstrings to maximize Code-RAG effectiveness. Well-documented code provides better semantic search results and more accurate answers.

## Important Notes

- **Core Dependency**: Uses [Google Generative AI Python SDK](https://github.com/googleapis/python-genai) (`google-genai>=0.3.0`)
- **Logging Module** (`logging_config.py`): Centralized multi-level verbosity configuration
  - Setup: `setup_logging(verbose_count)` at command start
  - Levels: 0=WARNING, 1=INFO, 2=DEBUG, 3+=TRACE (with library logging)
  - Library loggers: Configures `httpx`, `httpcore`, `google-api-core` at TRACE level
- **Authentication Support**: The CLI automatically detects and supports both authentication methods:
  - **Gemini Developer API** (default): Requires `GEMINI_API_KEY` or `GOOGLE_API_KEY` (latter takes precedence)
  - **Vertex AI**: Requires `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`
- **Client Implementation** (`core/client.py`):
  - Auto-detects authentication mode based on `GOOGLE_GENAI_USE_VERTEXAI` environment variable
  - Validates required configuration before creating client
  - Uses singleton pattern for client instance
  - Raises `MissingConfigurationError` with helpful messages for missing configuration
- **Cache System** (`core/cache.py`):
  - **Location**: `~/.config/gemini-file-search-tool/stores/`
  - **Structure**: One JSON file per store (e.g., `fileSearchStores__my-store.json`)
  - **Filename Sanitization**: Store names with "/" converted to "__" for filesystem safety
  - **Cache Contents**: Each file maps absolute paths to state objects:
    ```json
    {
      "/absolute/path/to/file.py": {
        "hash": "sha256-hash",
        "mtime": 1731969000.0,
        "remote_id": "documents/123",
        "last_uploaded": "2025-11-18T22:30:00Z"
      }
    }
    ```
  - **Performance Optimization**: O(n) → O(1) using mtime checks
    - First checks file modification time (O(1) filesystem stat)
    - Only calculates SHA256 hash (O(n)) if mtime changed
    - For 1000 unchanged files: ~0.1s (mtime check) vs ~5-10s (full hash)
  - **Load-on-Demand**: No in-memory cache, always loads from disk for consistency
  - **Per-Store Isolation**: Prevents cache overwrites when uploading to different stores
  - **Implementation Details**: See `docs/cache-design.md` for full architecture and benchmarks
- **Store Name Resolution**: `normalize_store_name()` accepts display names, IDs, or full resource names
- **Upload Behavior**: Automatically detects duplicates, skips unchanged files, updates changed files
- **File Validation** (`core/documents.py:_validate_file()`):
  - Empty file detection (0 bytes) - skipped with warning
  - File size limit (50MB)
  - Base64 image detection using regex pattern `data:image/[^;]+;base64,[A-Za-z0-9+/=]{50,}`
  - System file filtering (__pycache__, .pyc, .DS_Store)
  - Gitignore pattern matching (`commands/document_commands.py:_load_gitignore_patterns()`)
    - Automatically loads .gitignore from working directory
    - Uses fnmatch for pattern matching
    - Supports directory patterns (ending with /), path-specific patterns (with /), and simple patterns
    - Disable with `--ignore-gitignore` flag
  - MIME-type registration (.toml, .env, .txt, .md)
- **Composability**: Clean stdout/stderr separation for piping (JSON to stdout, logs to stderr)
- **Version Sync**: Keep version in sync across `cli.py`, `pyproject.toml`, and `__init__.py`

## Cost Tracking

The tool includes built-in cost tracking for query operations:

### Implementation Details

**Core Functions** (`core/query.py`):
- `query_store()` automatically captures `usage_metadata` from API responses
- Returns token counts: `prompt_token_count`, `candidates_token_count`, `total_token_count`
- Token usage is always included in response (no opt-in required)

**Utility Functions** (`utils.py`):
- `estimate_cost(usage_metadata, model)` - Calculate estimated cost in USD
  - Uses current Gemini API pricing (as of 2025-01)
  - gemini-2.5-flash: $0.075 input / $0.30 output per 1M tokens
  - gemini-2.5-pro: $1.25 input / $5.00 output per 1M tokens
  - Returns `None` if usage_metadata is missing
  - Raises `ValueError` for unknown models
- `DecimalJSONEncoder` - Custom JSON encoder to prevent scientific notation
  - Formats small floats as normal decimals (e.g., `0.00000045` not `4.5e-07`)
  - Applied automatically in `output_json()`

**CLI Command** (`commands/query_commands.py`):
- `--show-cost` flag: Adds `estimated_cost` field to JSON output
- `--verbose` flag: Displays token usage and cost info to stderr
- Token usage always included in JSON response

### Usage Examples

```bash
# View token usage (verbose mode)
gemini-file-search-tool query "What is this?" --store "test" -v
# Output to stderr: [INFO] Token usage: 150 prompt + 320 candidates = 470 total

# Show estimated cost
gemini-file-search-tool query "What is this?" --store "test" --show-cost -v
# Output to stderr:
# [INFO] Token usage: 150 prompt + 320 candidates = 470 total
# [INFO] Estimated cost: $0.00010725 USD
```

### Response Format

```json
{
  "response_text": "The document discusses...",
  "usage_metadata": {
    "prompt_token_count": 150,
    "candidates_token_count": 320,
    "total_token_count": 470
  },
  "estimated_cost": {
    "input_cost_usd": 0.00001125,
    "output_cost_usd": 0.000096,
    "total_cost_usd": 0.00010725,
    "currency": "USD",
    "model": "gemini-2.5-flash",
    "note": "Estimated cost based on current pricing. Subject to change."
  }
}
```

### Limitations

- **Query Operations Only**: Token usage is only available for query operations
- **No Upload Tracking**: Document embedding costs are not exposed by the API
- **Local Estimation**: Costs are calculated locally using published pricing
- **Pricing Updates**: Hardcoded pricing requires manual updates when Google changes rates
- **No Historical Billing**: No API endpoint for aggregated billing or historical cost data

### Testing

Cost tracking is covered by comprehensive tests in `tests/test_utils.py`:
- `test_estimate_cost_flash_model()` - Flash model cost calculation
- `test_estimate_cost_pro_model()` - Pro model cost calculation
- `test_estimate_cost_none_usage()` - Handles missing usage metadata
- `test_estimate_cost_unknown_model()` - Validates model names
- `test_estimate_cost_zero_tokens()` - Zero token edge case
- `test_output_json_no_scientific_notation()` - Verifies decimal formatting

## Known Issues & Future Fixes

### SDK Bug #1661 - Document Listing Workaround

**Issue**: [googleapis/python-genai#1661](https://github.com/googleapis/python-genai/issues/1661)

The SDK's `documents.list()` method requires a 'parent' parameter that causes failures. As a workaround, `list_documents()` in `core/documents.py` uses the REST API directly with API key authentication.

**Current Implementation**:
- Uses `requests` library to call REST API endpoint directly
- Only works with Developer API (GEMINI_API_KEY/GOOGLE_API_KEY)
- Raises clear error message when Vertex AI is detected
- See `core/documents.py:list_documents()` for implementation

**Future Fix** (when SDK bug is resolved):
1. Monitor the GitHub issue for resolution
2. Test if SDK's `client.file_search_stores.documents.list()` works correctly
3. Replace REST API workaround with SDK method:
   ```python
   def list_documents(store_name: str) -> list[dict[str, Any]]:
       client = get_client()
       documents = client.file_search_stores.documents.list(
           file_search_store_name=store_name
       )
       return [{"name": doc.name, "display_name": doc.display_name}
               for doc in documents]
   ```
4. Remove `requests` dependency from pyproject.toml if no longer needed
5. Remove Vertex AI restriction (allow both auth methods)
6. Update Known Issues section in README.md
7. Run full test suite to ensure compatibility
