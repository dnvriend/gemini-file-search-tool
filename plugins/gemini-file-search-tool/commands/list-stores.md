---
description: List all available File Search stores
argument-hint: (no arguments)
---

List all Gemini File Search stores with their metadata.

## Usage

```bash
gemini-file-search-tool list-stores [-v]
```

## Arguments

- `-v`: Verbose logging (optional)

## Examples

```bash
# List all stores
gemini-file-search-tool list-stores

# List with verbose logging
gemini-file-search-tool list-stores -v

# Filter with jq
gemini-file-search-tool list-stores | jq '.[] | select(.display_name | contains("docs"))'
```

## Output

Returns JSON array of stores with name, display_name, create_time, and update_time.
