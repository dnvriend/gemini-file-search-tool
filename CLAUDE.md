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
│   ├── client.py           # Gemini API client management
│   ├── stores.py           # Store CRUD operations
│   ├── documents.py        # Document operations (list, upload)
│   └── query.py            # Query operations
├── commands/                # CLI command implementations
│   ├── store_commands.py   # Store management commands
│   ├── document_commands.py # Document management commands
│   └── query_commands.py   # Query commands
└── utils.py                 # Shared utilities (normalize_store_name, output_json, etc.)
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
uv run gemini-file-search-tool create-store --name "test"
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
- `create-store --name NAME` - Create new store
- `list-stores` - List all stores
- `get-store --store NAME` - Get store details
- `update-store --store NAME --display-name NAME` - Update store
- `delete-store --store NAME [--force]` - Delete store

### Document Commands (document_commands.py)
- `list-documents --store NAME` - List documents in store
- `upload FILES... --store NAME [OPTIONS]` - Upload files (supports globs)
  - **Note**: FILES is positional (changed from `--input`)
  - Supports glob patterns: `*.pdf`, `docs/**/*.md`
  - Options: `--title`, `--url`, `--file-name`, `--max-tokens`, `--max-overlap`, `--num-workers`, `--skip-validation`

### Query Commands (query_commands.py)
- `query --store NAME --prompt TEXT [--pro] [--metadata-filter FILTER]` - Query documents

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

## Important Notes

- **Core Dependency**: Uses [Google Generative AI Python SDK](https://github.com/googleapis/python-genai) (`google-genai>=0.3.0`)
- **Authentication Support**: The CLI automatically detects and supports both authentication methods:
  - **Gemini Developer API** (default): Requires `GEMINI_API_KEY` or `GOOGLE_API_KEY` (latter takes precedence)
  - **Vertex AI**: Requires `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`
- **Client Implementation** (`core/client.py`):
  - Auto-detects authentication mode based on `GOOGLE_GENAI_USE_VERTEXAI` environment variable
  - Validates required configuration before creating client
  - Uses singleton pattern for client instance
  - Raises `MissingConfigurationError` with helpful messages for missing configuration
- **Store Name Resolution**: `normalize_store_name()` accepts display names, IDs, or full resource names
- **Upload Behavior**: Automatically detects duplicates, skips unchanged files, updates changed files
- **Composability**: Clean stdout/stderr separation for piping (JSON to stdout, logs to stderr)
- **Version Sync**: Keep version in sync across `cli.py`, `pyproject.toml`, and `__init__.py`

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
