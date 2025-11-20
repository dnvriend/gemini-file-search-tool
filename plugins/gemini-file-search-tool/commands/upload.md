---
description: Upload documents to store with caching
argument-hint: files... --store name
---

Upload files to a Gemini File Search store with intelligent caching and glob support.

## Usage

```bash
gemini-file-search-tool upload FILES... --store "STORE_NAME" [OPTIONS]
```

## Arguments

- `FILES`: File paths or glob patterns (required)
- `--store NAME`: Target store name (required)
- `--num-workers N`: Concurrent workers (default: CPU cores)
- `--no-wait`: Async upload without polling
- `--rebuild-cache`: Force re-upload all files
- `-v/-vv/-vvv`: Verbosity levels

## Examples

```bash
# Upload single file
gemini-file-search-tool upload document.pdf --store "papers"

# Upload with glob pattern
gemini-file-search-tool upload "docs/**/*.md" --store "documentation" -v

# Upload codebase for Code-RAG
gemini-file-search-tool upload "src/**/*.py" --store "my-codebase" -v

# Async upload with 8 workers
gemini-file-search-tool upload "*.pdf" --store "papers" --no-wait --num-workers 8
```

## Output

Returns JSON array with upload status for each file (completed, skipped, pending, failed).
