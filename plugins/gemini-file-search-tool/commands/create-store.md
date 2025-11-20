---
description: Create a new Gemini File Search store
argument-hint: store-name
---

Create a new Gemini File Search store for document storage and RAG queries.

## Usage

```bash
gemini-file-search-tool create-store "STORE_NAME" [--display-name NAME]
```

## Arguments

- `STORE_NAME`: Store identifier (required)
- `--display-name NAME`: Human-readable display name (optional)

## Examples

```bash
# Create store with auto-generated display name
gemini-file-search-tool create-store "research-papers"

# Create store with custom display name
gemini-file-search-tool create-store "docs" --display-name "Project Documentation"

# Capture output as JSON
gemini-file-search-tool create-store "code" | jq '.name'
```

## Output

Returns JSON with store name, display_name, create_time, and update_time.
