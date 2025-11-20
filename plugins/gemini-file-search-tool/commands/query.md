---
description: Query store with natural language RAG
argument-hint: prompt --store name
---

Query a Gemini File Search store with natural language using RAG (Retrieval-Augmented Generation).

## Usage

```bash
gemini-file-search-tool query "PROMPT" --store "STORE_NAME" [OPTIONS]
```

## Arguments

- `PROMPT`: Natural language query (required, positional)
- `--store NAME`: Store to query (required)
- `--query-model {flash|pro}`: Query model (default: flash)
- `--query-grounding-metadata`: Include source citations
- `--show-cost`: Show token usage and cost
- `-v/-vv/-vvv`: Verbosity levels

## Examples

```bash
# Basic query
gemini-file-search-tool query "What is DORA?" --store "papers"

# Query with citations and cost tracking
gemini-file-search-tool query "How does authentication work?" \
  --store "codebase" --query-grounding-metadata --show-cost -v

# Query with Pro model
gemini-file-search-tool query "Explain the architecture" \
  --store "docs" --query-model pro
```

## Output

Returns JSON with response_text, usage_metadata, grounding_metadata (if requested), and estimated_cost (if requested).
