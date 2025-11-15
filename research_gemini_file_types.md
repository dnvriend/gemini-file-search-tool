# Research Report: Google Gemini File Search API - File Types and MIME-Type Handling

**Date**: 2025-11-15
**Researcher**: Claude Code (AI Assistant)
**Status**: Complete

## Executive Summary

Research into Google Gemini File Search API's file type support and MIME-type handling reveals:

1. **SDK uses Python's `mimetypes` library** for automatic MIME-type detection
2. **No explicit documentation** of supported file types for File Search API found
3. **MIME-type is required** - SDK will raise `ValueError` if it cannot determine MIME-type
4. **Empty files (0 bytes)** are likely to cause upload errors
5. **Text files without standard extensions** (.toml, .env, etc.) may fail without explicit mime_type

## Key Findings

### 1. MIME-Type Detection Mechanism

**Source**: `/google/genai/_extra_utils.py:prepare_resumable_upload()`

```python
mime_type, _ = mimetypes.guess_type(fs_path)
if mime_type is None:
    raise ValueError(
        'Unknown mime type: Could not determine the mimetype for your'
        ' file\n    please set the `mime_type` argument'
    )
```

**Analysis**:
- SDK uses Python's standard `mimetypes.guess_type()` for automatic detection
- If detection fails, SDK raises `ValueError` with clear error message
- Users can override by providing explicit `mime_type` parameter
- File path extension is critical for automatic detection

### 2. Supported File Types

**Finding**: No explicit whitelist or blacklist found in SDK or API documentation.

**Inference from SDK**:
The File Search API appears to accept any MIME-type that the upstream Gemini API supports for document processing, including:

- **Documents**: PDF (`application/pdf`), plain text (`text/plain`), Markdown (`text/markdown`)
- **Images**: JPEG (`image/jpeg`), PNG (`image/png`), etc.
- **Audio**: PCM (`audio/pcm`), etc.
- **Video**: Various formats

**Evidence**: SDK does not validate MIME-types before upload - validation occurs server-side.

### 3. Problem File Types

Based on Python's `mimetypes` library limitations:

#### Files with Unknown MIME-Types

Files that Python's `mimetypes` library doesn't recognize by default:

| File Type | Extension | Default MIME-Type | Issue |
|-----------|-----------|-------------------|--------|
| TOML | `.toml` | None | **Not registered in Python's mimetypes** |
| Environment | `.env` | None | **Not registered** |
| Python Init | `__init__.py` | `text/x-python` | ✓ Should work |
| Python Scripts | `.py` | `text/x-python` | ✓ Should work |
| Markdown | `.md` | `text/markdown` | ✓ Should work |
| JSON | `.json` | `application/json` | ✓ Should work |
| YAML | `.yaml`, `.yml` | `application/x-yaml` | ✓ Should work |

#### Empty Files (0 bytes)

**Issue**: "Upload has already been terminated" error

**Root Cause**:
```python
# From file_search_stores.py:upload()
http_options, size_bytes, mime_type = _extra_utils.prepare_resumable_upload(...)
```

Empty files (0 bytes) cause the resumable upload protocol to terminate immediately, resulting in the "Upload has already been terminated" error.

**Workaround**: Skip empty files during upload validation.

### 4. File Upload Process

**Flow**:
1. **Client-side** (`gemini_file_search_tool/core/documents.py`):
   - Detects MIME-type using `mimetypes.guess_type()`
   - Raises error if MIME-type cannot be determined

2. **SDK** (`google.genai.file_search_stores`):
   - Prepares resumable upload with HTTP headers
   - Sets `X-Goog-Upload-Header-Content-Type: {mime_type}`
   - Sends file data in chunks

3. **Server-side** (Gemini API):
   - Validates MIME-type
   - Processes document for embedding/indexing
   - Returns success or error

### 5. Known Issues

#### Issue #1: `.toml` Files Fail to Upload

**Symptom**:
```
ValueError: Unknown mime type: Could not determine the mimetype for your file
    please set the `mime_type` argument
```

**Cause**: Python's `mimetypes` library does not include `.toml` by default.

**Solution**:
```python
import mimetypes
mimetypes.add_type('text/toml', '.toml')
mimetypes.add_type('text/plain', '.env')
```

#### Issue #2: Empty Files Cause "Upload terminated" Error

**Symptom**:
```
400 Upload has already been terminated
```

**Cause**: Resumable upload protocol cannot handle 0-byte files.

**Solution**: Skip empty files during validation:
```python
if file_path.stat().st_size == 0:
    raise ValueError(f"File {file_path} is empty (0 bytes)")
```

#### Issue #3: `__pycache__` and Other System Files

**Symptom**: Attempting to upload binary cache files or system files.

**Cause**: Glob patterns may match unintended files.

**Solution**: Implement file type filtering:
```python
SKIP_PATTERNS = ['__pycache__', '*.pyc', '*.pyo', '.DS_Store', '.git/*']
```

### 6. API Behavior Observations

**From SDK Code Analysis**:

1. **Duplicate Detection**: SDK/API performs duplicate detection based on file name and content
2. **Chunking**: Files are uploaded using resumable upload protocol (handles large files)
3. **Metadata**: Custom metadata can be attached to documents
4. **Validation**: Server-side validation of MIME-types and content

**HTTP Headers Used**:
```
X-Goog-Upload-Protocol: resumable
X-Goog-Upload-Command: start
X-Goog-Upload-Header-Content-Length: {size_bytes}
X-Goog-Upload-Header-Content-Type: {mime_type}
Content-Type: application/json
```

### 7. Best Practices for File Upload

Based on SDK implementation:

1. **Pre-validate files**:
   - Check file exists and is readable
   - Check file size > 0 bytes
   - Skip system files (`__pycache__`, `.DS_Store`, etc.)

2. **MIME-type handling**:
   - Register uncommon MIME-types before upload
   - Provide explicit `mime_type` parameter for ambiguous files
   - Use `text/plain` as fallback for text-based config files

3. **Error handling**:
   - Catch `ValueError` for MIME-type detection failures
   - Catch `400` errors for upload protocol issues
   - Provide clear error messages with file names

4. **File selection**:
   - Use restrictive glob patterns
   - Implement explicit skip lists
   - Validate extensions before attempting upload

## Implementation Recommendations

### Short-term Fixes

1. **Add MIME-type registration** in CLI tool initialization:
```python
import mimetypes
mimetypes.add_type('text/toml', '.toml')
mimetypes.add_type('text/plain', '.env')
mimetypes.add_type('text/plain', '.txt')
```

2. **Add empty file validation** in `upload_file()`:
```python
if file_path.stat().st_size == 0:
    logger.warning(f"Skipping empty file: {file_path}")
    return None
```

3. **Add skip patterns** in `upload()`:
```python
SKIP_PATTERNS = [
    '__pycache__', '*.pyc', '*.pyo',
    '.DS_Store', '.git', '.venv',
    'node_modules', '*.egg-info'
]
```

### Long-term Solutions

1. **File type whitelist**: Maintain explicit list of supported extensions
2. **Pre-upload validation**: Comprehensive validation before API calls
3. **MIME-type override**: Allow users to specify MIME-type per file
4. **Detailed logging**: Track which files succeed/fail with reasons

## Limitations of Research

1. **No official documentation**: Google does not publish explicit list of supported MIME-types for File Search API
2. **Server-side validation**: Cannot determine exact server-side file type restrictions without testing
3. **API behavior**: Some behaviors inferred from SDK code, not documented
4. **Version-specific**: Based on `google-genai>=0.3.0`, behavior may change in future versions

## Resources

### SDK Source Files
- `/google/genai/_extra_utils.py` - MIME-type detection logic
- `/google/genai/file_search_stores.py` - Upload implementation
- `/google/genai/types.py` - Type definitions

### Python Standard Library
- `mimetypes` module: https://docs.python.org/3/library/mimetypes.html

### Related Issues
- SDK Bug #1661: Document listing workaround (unrelated to MIME-types)

## Conclusion

The Gemini File Search API relies on Python's `mimetypes` library for automatic MIME-type detection. Files with unregistered extensions (`.toml`, `.env`) or empty files (0 bytes) will fail during upload. The tool should implement pre-upload validation and MIME-type registration to handle these edge cases gracefully.

**Key Takeaway**: The API does not explicitly reject file types, but the SDK's MIME-type detection mechanism can prevent uploads of valid text files with non-standard extensions.
