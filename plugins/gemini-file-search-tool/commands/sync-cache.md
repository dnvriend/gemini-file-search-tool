---
description: Sync pending upload operations to cache
argument-hint: --store name
---

Synchronize pending upload operations and update cache with final status.

## Usage

```bash
gemini-file-search-tool sync-cache --store "STORE_NAME" [OPTIONS]
```

## Arguments

- `--store NAME`: Store name (required)
- `--num-workers N`: Parallel workers (default: 4)
- `--text`: Human-readable output (default: JSON)
- `-v`: Verbose logging

## Examples

```bash
# Sync with default workers
gemini-file-search-tool sync-cache --store "papers"

# Sync with 8 parallel workers
gemini-file-search-tool sync-cache --store "codebase" --num-workers 8 -v

# Human-readable output
gemini-file-search-tool sync-cache --store "docs" --text
```

## Output

Returns JSON with synced/failed/pending counts and operation details (or text format with --text).
