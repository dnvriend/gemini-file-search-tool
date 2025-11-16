# gemini-file-search-tool

[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://github.com/python/mypy)
[![AI Generated](https://img.shields.io/badge/AI-Generated-blueviolet.svg)](https://www.anthropic.com/claude)
[![Built with Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-5A67D8.svg)](https://www.anthropic.com/claude/code)

Gemini File Search Tool

## Table of Contents

- [About](#about)
- [Use Cases](#use-cases)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Known Issues](#known-issues)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)
- [Resources](#resources)

## About

`gemini-file-search-tool` is a production-ready CLI and Python library for [Google's Gemini File Search API](https://ai.google.dev/gemini-api/docs/file-search), a fully managed Retrieval-Augmented Generation (RAG) system that eliminates the operational complexity of vector databases, embeddings, and retrieval infrastructure.

### What is Gemini File Search?

Gemini File Search is Google's fully managed RAG solution that automatically handles document ingestion, chunking, embedding generation, and semantic retrieval. As announced in [Google's developer blog](https://blog.google/technology/developers/file-search-gemini-api/), it provides enterprise-grade document search capabilities with zero infrastructure overhead, allowing developers to focus on building intelligent applications rather than managing search infrastructure.

### Why This Tool?

This tool provides a **CLI-first interface** to the Gemini File Search API, designed specifically for integration with AI agents, automation workflows, and human operators:

- **Agent-Friendly Design**: CLIs provide structured commands with built-in documentation and rich error messages that AI agents can parse and act upon in ReAct (Reasoning and Acting) loops, making them superior to standalone scripts for agentic workflows
- **Composable Architecture**: JSON output to stdout and logs to stderr enable seamless piping and integration with other tools, perfect for complex automation pipelines
- **Reusable Building Blocks**: Commands can be composed into larger workflows, used in skills for Claude Code, or integrated into custom automation without modification
- **Dual-Mode Operation**: Functions as both a CLI tool for command-line operations and a Python library for programmatic integration
- **Production Quality**: Type-safe, thoroughly tested, with comprehensive error handling that provides actionable feedback for both humans and agents

Whether you're building AI-powered document search, integrating RAG into agentic workflows, or automating knowledge base operations, this tool provides the foundation for reliable, maintainable solutions.

## Use Cases

- **📚 Knowledge Base Management**: Index documentation, research papers, wikis, and technical specifications into searchable stores for instant retrieval
- **💻 Code-RAG (Retrieval-Augmented Generation for Code)**: Upload entire codebases to enable semantic code search and natural language querying. Ask questions like "how does authentication work?", "where is error handling implemented?", or "explain the database architecture". Perfect for onboarding, code reviews, architecture discovery, and building AI coding assistants.
- **🔍 Semantic Search**: Query your document stores with natural language questions and receive contextually relevant answers with automatic citation
- **🎯 RAG Applications**: Build production-ready retrieval-augmented generation systems with JSON-formatted responses including grounding metadata and source attribution

### Code-RAG Example

Upload a codebase and query it with natural language:

```bash
# Upload your entire codebase
gemini-file-search-tool upload "src/**/*.py" --store "my-project-code" -v

# Query with natural language
gemini-file-search-tool query --store "my-project-code" \
  --prompt "How does the authentication system work?" \
  --show-cost -v

# Ask architectural questions
gemini-file-search-tool query --store "my-project-code" \
  --prompt "What design patterns are used in this codebase?" \
  --pro

# Find implementations
gemini-file-search-tool query --store "my-project-code" \
  --prompt "Where is error handling for API calls implemented?"
```

**Meta Note**: This tool itself was built using Code-RAG! We uploaded the codebase to a Gemini File Search store and used it to answer questions during development. The tool enables the very functionality it provides.

## Features

- ✅ **Fully Managed RAG**: Automatic chunking, embeddings, and retrieval without infrastructure management
- ✅ **Multi-Format Support**: PDF, DOCX, TXT, JSON, CSV, HTML, and source code files
- ✅ **Code-RAG Enabled**: Upload codebases and query with natural language for semantic code search
- ✅ **Natural Language Queries**: Ask questions in plain language and get contextual answers
- ✅ **Automatic Citations**: Built-in source attribution and grounding metadata
- ✅ **Multi-Level Verbosity**: Progressive logging detail with `-v` (INFO), `-vv` (DEBUG), `-vvv` (TRACE)
- ✅ **Cost Tracking**: Token usage monitoring and cost estimation for query operations
- ✅ **Composable CLI**: JSON output for easy integration with other tools and scripts
- ✅ **Python Library**: Import and use programmatically in your applications
- ✅ **Type-Safe**: Strict mypy type checking and modern Python 3.14+ syntax
- ✅ **Production-Ready**: Comprehensive testing, linting, and quality checks

## Installation

### Prerequisites

- Python 3.14 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Google Gemini API access (see [Configuration](#configuration))

### Core Dependencies

This tool uses the [Google Generative AI Python SDK](https://github.com/googleapis/python-genai) (`google-genai`) for interacting with Google's Gemini API.

### Install from source

```bash
# Clone the repository
git clone https://github.com/dnvriend/gemini-file-search-tool.git
cd gemini-file-search-tool

# Install globally with uv
uv tool install .
```

### Install with mise (recommended for development)

```bash
cd gemini-file-search-tool
mise trust
mise install
uv sync
uv tool install .
```

### Verify installation

```bash
gemini-file-search-tool --version
```

## Configuration

### Environment Variables

The CLI automatically detects and supports both authentication methods. Configuration depends on whether you're using the Gemini Developer API or the Gemini API in Vertex AI.

#### Gemini Developer API (Recommended)

Set `GEMINI_API_KEY` or `GOOGLE_API_KEY`. The client will automatically pick up these variables. If both are set, `GOOGLE_API_KEY` takes precedence.

```bash
export GEMINI_API_KEY='your-api-key'
```

**Get your API key:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create or select a project
3. Generate an API key
4. Set the environment variable

**Example:**
```bash
export GEMINI_API_KEY='AIza...'
gemini-file-search-tool list-stores
```

#### Gemini API on Vertex AI

For Vertex AI, set the following environment variables:

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT='your-project-id'
export GOOGLE_CLOUD_LOCATION='us-central1'
```

**Prerequisites:**
- Google Cloud project with Vertex AI API enabled
- Proper IAM permissions for Vertex AI
- Authenticated with `gcloud auth application-default login`

**Example:**
```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT='my-project'
export GOOGLE_CLOUD_LOCATION='us-central1'

# Authenticate with Google Cloud
gcloud auth application-default login

# Use the CLI (automatically uses Vertex AI)
gemini-file-search-tool list-stores
```

**Note:** The CLI automatically detects which authentication method to use based on the `GOOGLE_GENAI_USE_VERTEXAI` environment variable.

For more information, see the [Google Generative AI Python SDK documentation](https://github.com/googleapis/python-genai).

## Usage

### Basic Usage

```bash
# Show help
gemini-file-search-tool --help

# Show version
gemini-file-search-tool --version

# Get help for specific commands
gemini-file-search-tool create-store --help
gemini-file-search-tool upload --help
```

### Store Management

```bash
# Create a new store
gemini-file-search-tool create-store --name "my-documents"

# List all stores
gemini-file-search-tool list-stores

# Get store details
gemini-file-search-tool get-store --store "my-documents"

# Update store display name
gemini-file-search-tool update-store --store "my-documents" --display-name "My Documents 2024"

# Delete a store
gemini-file-search-tool delete-store --store "my-documents" --force
```

### Document Management

```bash
# Upload a single file
gemini-file-search-tool upload document.pdf --store "my-documents"

# Upload multiple files with glob pattern
gemini-file-search-tool upload "*.pdf" --store "my-documents"

# Recursive upload
gemini-file-search-tool upload "docs/**/*.md" --store "my-documents"

# Upload with metadata
gemini-file-search-tool upload document.pdf --store "my-documents" \
  --title "Important Document" \
  --url "https://example.com/doc"

# Upload with custom chunking
gemini-file-search-tool upload document.pdf --store "my-documents" \
  --max-tokens 300 \
  --max-overlap 25

# Upload respecting .gitignore (default behavior)
gemini-file-search-tool upload "**/*.py" --store "my-codebase" -v

# Upload ignoring .gitignore patterns
gemini-file-search-tool upload "**/*.py" --store "my-codebase" --ignore-gitignore

# Dry-run to preview files before uploading
gemini-file-search-tool upload "**/*.py" --store "my-codebase" --dry-run -v

# Upload with verbose logging (see what's happening)
gemini-file-search-tool upload "*.pdf" --store "my-documents" -v

# Upload with debug logging (see detailed operations)
gemini-file-search-tool upload "*.pdf" --store "my-documents" -vv

# Upload with trace logging (see full API calls)
gemini-file-search-tool upload "*.pdf" --store "my-documents" -vvv

# List documents in a store
gemini-file-search-tool list-documents --store "my-documents"

# List documents with verbose output
gemini-file-search-tool list-documents --store "my-documents" -v
```

### Querying

```bash
# Basic query
gemini-file-search-tool query --store "my-documents" \
  --prompt "What are the key findings?"

# Query with Pro model
gemini-file-search-tool query --store "my-documents" \
  --prompt "Analyze the technical architecture" \
  --pro

# Query with metadata filter
gemini-file-search-tool query --store "my-documents" \
  --prompt "Tell me about the book" \
  --metadata-filter "author=Robert Graves"

# Query with cost tracking and verbose output
gemini-file-search-tool query --store "my-documents" \
  --prompt "Explain the methodology" \
  --show-cost -v

# Query with debug logging (see API operations)
gemini-file-search-tool query --store "my-documents" \
  --prompt "What are the findings?" \
  --show-cost -vv

# Query with trace logging (see full HTTP requests)
gemini-file-search-tool query --store "my-documents" \
  --prompt "Analyze this" \
  --show-cost -vvv
```

### Cost Tracking

The CLI automatically tracks token usage for query operations and can estimate costs based on current Gemini API pricing:

```bash
# View token usage (verbose mode)
gemini-file-search-tool query --store "my-documents" \
  --prompt "What is this about?" --verbose

# Output:
# [INFO] Token usage: 150 prompt + 320 candidates = 470 total

# Show estimated cost
gemini-file-search-tool query --store "my-documents" \
  --prompt "What is this about?" --show-cost --verbose

# Output:
# [INFO] Token usage: 150 prompt + 320 candidates = 470 total
# [INFO] Estimated cost: $0.00010725 USD
```

**Query Response with Cost Information:**

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

**Current Pricing (as of 2025-01):**
- **gemini-2.5-flash**: $0.075 input / $0.30 output per 1M tokens
- **gemini-2.5-pro**: $1.25 input / $5.00 output per 1M tokens

**Note**: Pricing is subject to change. Verify current rates at [Google AI Pricing](https://ai.google.dev/pricing).

**Limitations:**
- Token usage is only available for query operations
- Upload costs (document embedding) are not tracked by the API
- Cost estimates are calculated locally using published pricing

### Upload Features

**Automatic File Validation**:
- **Empty Files**: 0-byte files automatically skipped with warning
- **File Size**: 50MB limit enforced
- **Base64 Images**: Detects base64-encoded images in text files (can cause upload failures)
- **System Files**: Auto-skips `__pycache__`, `.pyc`, `.DS_Store`, etc.
- **Gitignore Support**: Automatically respects `.gitignore` patterns (use `--ignore-gitignore` to disable)
- **MIME Types**: Automatic registration for `.toml`, `.env`, `.txt`, `.md` files

**Duplicate Detection**:
- Automatically detects existing files by name and size
- Skips unchanged files (no re-upload)
- Updates files when size changes (deletes old, uploads new)

**Preview & Control**:
- **Dry-Run**: Use `--dry-run` to preview which files would be uploaded without actually uploading
- **Skip Validation**: Use `--skip-validation` to bypass checks for faster uploads
- **Ignore Gitignore**: Use `--ignore-gitignore` to upload files normally excluded by .gitignore

### Dry-Run Mode

Preview which files would be uploaded without actually uploading:

```bash
# Preview files with sizes
gemini-file-search-tool upload "**/*.py" --store "code" --dry-run -v

# Output (to stderr):
# [INFO] Loaded 38 patterns from .gitignore
# [INFO] DRY-RUN: Would upload 13 file(s)

# Output (to stdout - JSON):
[
  {
    "file": "/path/to/file1.py",
    "size_bytes": 1809,
    "size_mb": 0.0
  },
  {
    "file": "/path/to/file2.py",
    "size_bytes": 2691,
    "size_mb": 0.0
  }
]
```

**Benefits**:
- **Preview Files**: See exactly which files match your glob pattern
- **Verify Gitignore**: Confirm .gitignore filtering is working correctly
- **Check Sizes**: Review file sizes before uploading
- **No API Calls**: Completely safe, no interaction with Gemini API

### Verbosity Levels

All commands support multi-level verbosity for controlling log output detail:

| Flag | Level | Description | Use Case |
|------|-------|-------------|----------|
| (none) | WARNING | Only critical errors | Production, clean output |
| `-v` | INFO | High-level operations | See progress, identify failures |
| `-vv` | DEBUG | Detailed operations | Debug issues, see API calls |
| `-vvv` | TRACE | Full API details | Deep debugging, HTTP traces |

**Examples:**

```bash
# INFO level: See which files are uploaded/failed
gemini-file-search-tool upload "*.pdf" --store "docs" -v

# DEBUG level: See validation, polling, API operations
gemini-file-search-tool upload "*.pdf" --store "docs" -vv

# TRACE level: See full HTTP requests/responses from SDK
gemini-file-search-tool upload "*.pdf" --store "docs" -vvv
```

**Output:**

```bash
# With -v (INFO)
[INFO] Starting upload operation
[INFO] Uploading: document.pdf (2.50MB) to store 'fileSearchStores/docs-123'
[INFO] Upload completed successfully: document.pdf

# With -vv (DEBUG)
[INFO] Starting upload operation
[INFO] Uploading: document.pdf (2.50MB) to store 'fileSearchStores/docs-123'
[DEBUG] Validating file: document.pdf
[DEBUG] File validation passed: document.pdf
[DEBUG] Starting upload operation for: document.pdf
[DEBUG] Operation started: operations/upload-abc123
[DEBUG] Polling operation operations/upload-abc123 (attempt 1) - waiting 2.0s
[DEBUG] Polling operation operations/upload-abc123 (attempt 2) - waiting 3.0s
[INFO] Upload completed successfully: document.pdf

# With -vvv (TRACE) - includes all above plus:
[DEBUG] (httpx) HTTP Request: POST https://...
[DEBUG] (httpx) HTTP Response: 200 OK
```

**Benefits:**
- **Real-time Feedback**: See progress and failures as they happen (not just in final JSON)
- **Progressive Detail**: Choose the right level of verbosity for your needs
- **Clean stdout**: All logs go to stderr, keeping JSON output clean for piping
- **Library Logging**: At `-vvv`, see internals from `httpx`, `google-api-core`, etc.

### Library Usage

You can also use this package as a Python library:

```python
from pathlib import Path
from gemini_file_search_tool import (
    create_store,
    upload_file,
    query_store,
    list_documents,
)

# Create a store
store = create_store("my-documents")
print(f"Created store: {store['name']}")

# Upload a file
result = upload_file(
    file_path=Path("document.pdf"),
    store_name=store["name"],
    title="Important Document"
)
print(f"Upload status: {result['status']}")

# Query the store
response = query_store(
    store_name=store["name"],
    prompt="What is in this document?",
    model="gemini-2.5-flash"
)
print(response["response_text"])

# List documents
documents = list_documents(store["name"])
print(f"Found {len(documents)} documents")
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/dnvriend/gemini-file-search-tool.git
cd gemini-file-search-tool

# Install dependencies
make install

# Show available commands
make help
```

### Available Make Commands

```bash
make install          # Install dependencies
make format           # Format code with ruff
make lint             # Run linting with ruff
make typecheck        # Run type checking with mypy
make test             # Run tests with pytest
make check            # Run all checks (lint, typecheck, test)
make pipeline         # Run full pipeline (format, lint, typecheck, test, build, install-global)
make build            # Build package
make run ARGS="..."   # Run gemini-file-search-tool locally
make clean            # Remove build artifacts
```

### Project Structure

```
gemini-file-search-tool/
├── gemini_file_search_tool/    # Main package
│   ├── __init__.py
│   ├── cli.py          # CLI entry point
│   └── utils.py        # Utility functions
├── tests/              # Test suite
│   ├── __init__.py
│   └── test_utils.py
├── pyproject.toml      # Project configuration
├── Makefile            # Development commands
├── README.md           # This file
├── LICENSE             # MIT License
└── CLAUDE.md           # Development documentation
```

## Testing

Run the test suite:

```bash
# Run all tests
make test

# Run tests with verbose output
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_utils.py

# Run with coverage
uv run pytest tests/ --cov=gemini_file_search_tool
```

## Known Issues

### SDK Bug #1661 - Document Listing with Vertex AI

**Issue**: The Google Generative AI Python SDK has a bug ([#1661](https://github.com/googleapis/python-genai/issues/1661)) where `documents.list()` requires a 'parent' parameter that causes failures.

**Impact**: The `list-documents` command cannot be used with Vertex AI authentication.

**Workaround**: We use the REST API directly instead of the SDK's `documents.list()` method. This workaround only works with the Developer API (requires `GEMINI_API_KEY` or `GOOGLE_API_KEY`).

**Status**: Waiting for upstream fix in the Google Generative AI Python SDK.

**Affected Commands**:
- `list-documents` - Only works with Developer API, not Vertex AI

**Code Location**: `gemini_file_search_tool/core/documents.py:list_documents()`

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the full pipeline (`make pipeline`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for public functions
- Format code with `ruff`
- Pass all linting and type checks

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Dennis Vriend**

- GitHub: [@dnvriend](https://github.com/dnvriend)

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for CLI framework
- Developed with [uv](https://github.com/astral-sh/uv) for fast Python tooling

## Resources

### Gemini File Search Documentation

- **[Gemini File Search API Documentation](https://ai.google.dev/gemini-api/docs/file-search)** - Official API documentation and guides
- **[Gemini API File Search Stores Reference](https://ai.google.dev/api/file-search/file-search-stores)** - API reference for file search stores
- **[Introducing File Search for the Gemini API](https://blog.google/technology/developers/file-search-gemini-api/)** - Official announcement and overview from Google

### Related Tools

- **[Google Generative AI Python SDK](https://github.com/googleapis/python-genai)** - Python SDK for Google's Gemini API

---

**Generated with AI**

This project was generated using [Claude Code](https://www.anthropic.com/claude/code), an AI-powered development tool by [Anthropic](https://www.anthropic.com/). Claude Code assisted in creating the project structure, implementation, tests, documentation, and development tooling.

Made with ❤️ using Python 3.14
