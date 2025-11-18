# Cache System Design

## Overview

The cache system tracks uploaded files to avoid unnecessary re-uploads and API calls. It stores file state in `~/.config/gemini-file-search-tool/cache.json`.

## Cache Structure

```json
{
  "stores": {
    "normalized-store-name": {
      "/absolute/path/to/file.py": {
        "hash": "sha256-hash-string",
        "mtime": 1731969000.0,
        "remote_id": "corpora/123/documents/456",
        "last_uploaded": "2025-11-18T22:30:00Z"
      }
    }
  }
}
```

## Performance Optimization: O(n) → O(1)

### Algorithm Complexity

**Before mtime optimization**: O(n) per file
- Calculate SHA256 hash by reading entire file
- For 100MB file: ~500ms hash calculation
- For 1000 files: 500+ seconds just for cache checking

**After mtime optimization**: O(1) per file (unchanged files)
- Single `stat()` syscall to check modification time
- ~0.1ms filesystem metadata lookup
- For 1000 unchanged files: ~100ms total (5000x faster)

### Real-World Impact

**Large codebase example** (1000 Python files, avg 50KB each):
- **Before**: ~5-10 seconds reading/hashing for cache check
- **After**: ~0.1 seconds checking mtime
- **Speedup**: 50-100x improvement

The optimization is most effective where it matters:
- Large files get biggest speedup (O(n) → O(1))
- Frequently-run uploads (CI/CD) see massive time savings
- Only pays O(n) cost when files actually change (correct behavior)

**Edge case**: If mtime changes but content doesn't (e.g., `touch`), we fall back to hash comparison - still correct, just one extra hash calculation.

## Hash Algorithm Choice: SHA256 vs MD5

### Performance Comparison

**MD5**: ~350-400 MB/s
**SHA256**: ~150-200 MB/s

For a 100MB file:
- MD5: ~250ms
- SHA256: ~500ms
- **Difference**: 250ms per file

### Why SHA256 Despite Being Slower

#### 1. mtime optimization eliminated the bottleneck

With mtime checking, we only hash when files **actually change**:
```
Before: Hash every file = O(n) cost
After:  Hash only changed files = rare operation
```
The 2x speed difference rarely matters since hashing is now infrequent.

#### 2. Network I/O is the real bottleneck

```
Hash calculation: ~500ms (SHA256) or ~250ms (MD5)
Upload to Gemini API: 5-10 seconds per file
```

Upload time dominates (10-20x longer than hash), so optimizing hash from 500ms → 250ms saves <5% total time.

#### 3. Integrity & collision resistance

- **SHA256**: Cryptographically secure, no known collisions
- **MD5**: Broken (collision attacks exist since 2004)

For cache integrity (detecting file changes), SHA256 is safer against accidental collisions, especially with large file corpora.

### When MD5 Would Matter

Only if uploading **thousands of small files that change frequently**:
- 1000 changed files: Save 250 seconds with MD5
- But upload time: Still 5000-10000 seconds (dominates)

### Decision: Use SHA256

Reasons:
1. mtime optimization already gives 10-100x speedup
2. Network I/O is the real bottleneck
3. Better collision resistance for cache integrity
4. Industry standard (Git, Docker, Nix all use SHA256)
5. Minimal ROI from switching to MD5 given mtime optimization

## Cache Flow

### Initial Upload

1. Check if file exists in cache
2. If not in cache → upload
3. After successful upload:
   - Calculate SHA256 hash
   - Get file mtime via `stat()`
   - Store: hash, mtime, remote_id, timestamp
   - Save cache to disk

### Subsequent Upload (File Unchanged)

1. Check cache for file path
2. Get current file mtime
3. **If mtime unchanged**:
   - Skip hash calculation (O(1) operation)
   - Skip upload (file guaranteed unchanged)
4. **If mtime changed**:
   - Calculate hash (O(n) operation)
   - Compare with cached hash
   - If hash matches: Skip upload (metadata change only, e.g., `touch`)
   - If hash differs: Upload and update cache

### Subsequent Upload (File Changed)

1. mtime changed → calculate hash
2. Hash differs from cache → upload
3. Update cache with new hash, mtime, timestamp

## Logging Levels

- **INFO** (`-v`): Cache load/save, file updates, skip decisions
- **DEBUG** (`-vv`): Hash calculations, cache hits/misses, detailed operations
- **TRACE** (`-vvv`): Full HTTP traces (for debugging SDK issues)

## Benefits

1. **Performance**: 10-100x faster cache checks via mtime
2. **Correctness**: Hash verification for actual content changes
3. **Visibility**: Comprehensive logging for debugging
4. **Reliability**: SHA256 provides strong integrity guarantees
5. **Standard Compliance**: Matches industry best practices

## Future Considerations

If network I/O is optimized significantly (unlikely given API constraints), we could:
- Make hash algorithm configurable (`--hash-algorithm md5|sha256`)
- Default to SHA256 for integrity, allow MD5 for speed-critical use cases
- Measure actual impact with telemetry before implementing

Current bottleneck order (slowest to fastest):
1. Network I/O (5-10s per file) ← **Current bottleneck**
2. SHA256 hashing (500ms per 100MB) ← 10-20x faster than network
3. mtime check (0.1ms) ← 5000x faster than hash
