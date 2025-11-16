# Implementing Multi-Level Verbosity with Python Logging

**Date**: 2025-11-16
**Author**: Dennis Vriend with Claude Code
**Purpose**: Reference guide for implementing `-v`, `-vv`, `-vvv` verbosity in Python CLIs

## Overview

This guide demonstrates how to implement multi-level verbosity (`-v`, `-vv`, `-vvv`) in Python CLI applications using the standard `logging` module. This pattern provides progressive detail levels and can control logging from both your application and dependent libraries.

## Why Multi-Level Verbosity?

**Problem**: Single boolean verbose flags (`--verbose` on/off) are too coarse:
- Users can't control detail level
- Dependent library logs are either all on or all off
- Debugging requires code changes

**Solution**: Multi-level verbosity with progressive detail:
- `-v` (INFO): High-level operations, important events
- `-vv` (DEBUG): Detailed operations, API calls, validation steps
- `-vvv` (TRACE): Full request/response, library internals, tracebacks

## Implementation Pattern

### 1. Create Logging Configuration Module

**File**: `your_package/logging_config.py`

```python
"""Centralized logging configuration with multi-level verbosity support.

This module provides setup_logging() for configuring logging based on
verbosity count from CLI arguments (-v, -vv, -vvv).

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import logging
import sys


def setup_logging(verbose_count: int = 0) -> None:
    """Configure logging based on verbosity level.

    Maps CLI verbosity count to Python logging levels and configures
    both application and dependent library loggers.

    Args:
        verbose_count: Number of -v flags (0-3+)
            0: WARNING level (quiet mode)
            1: INFO level (normal verbose)
            2: DEBUG level (detailed debugging)
            3+: DEBUG + enable dependent library logging (trace mode)

    Example:
        >>> setup_logging(0)  # No -v flag: WARNING only
        >>> setup_logging(1)  # -v: INFO level
        >>> setup_logging(2)  # -vv: DEBUG level
        >>> setup_logging(3)  # -vvv: DEBUG + library internals
    """
    # Map verbosity count to logging levels
    if verbose_count == 0:
        level = logging.WARNING
    elif verbose_count == 1:
        level = logging.INFO
    elif verbose_count >= 2:
        level = logging.DEBUG
    else:
        level = logging.WARNING

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        stream=sys.stderr,
        force=True,  # Override any existing configuration
    )

    # Configure dependent library loggers at TRACE level (-vvv)
    if verbose_count >= 3:
        # Example: httpx library (HTTP client)
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        logging.getLogger("httpcore").setLevel(logging.DEBUG)

        # Example: urllib3 (used by requests)
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

        # Example: boto3/botocore (AWS SDK)
        logging.getLogger("boto3").setLevel(logging.DEBUG)
        logging.getLogger("botocore").setLevel(logging.DEBUG)

        # Example: google-api-core
        logging.getLogger("google.api_core").setLevel(logging.DEBUG)
    else:
        # Suppress noisy libraries at lower verbosity levels
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("google.api_core").setLevel(logging.WARNING)

    # Suppress your own package's internal modules at lower levels
    if verbose_count < 2:
        logging.getLogger("your_package.internal").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    This is a convenience wrapper around logging.getLogger() that
    ensures consistent logger naming across your application.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Operation started")
        >>> logger.debug("Detailed operation info")
    """
    return logging.getLogger(name)
```

### 2. Update CLI to Support Multi-Level Verbosity

**File**: `your_package/cli.py` or `your_package/commands/your_command.py`

#### Using Click Framework

```python
import click
from your_package.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


@click.command("your-command")
@click.option(
    "-v",
    "--verbose",
    count=True,  # Key change: count=True instead of is_flag=True
    help="Enable verbose output (use -v for INFO, -vv for DEBUG, -vvv for TRACE)",
)
def your_command(verbose: int) -> None:  # Type changed from bool to int
    """Your command description.

    Examples:

    \b
        # Normal mode (warnings only)
        your-cli command

    \b
        # Verbose mode (INFO level)
        your-cli command -v

    \b
        # Debug mode (DEBUG level)
        your-cli command -vv

    \b
        # Trace mode (DEBUG + library internals)
        your-cli command -vvv
    """
    # Setup logging at the start of the command
    setup_logging(verbose)
    logger.info("Command started")

    try:
        # Your command logic here
        logger.debug("Processing data...")
        # ... your code ...
        logger.info("Command completed successfully")
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        logger.debug("Full traceback:", exc_info=True)
        raise
```

#### Using argparse Framework

```python
import argparse
from your_package.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Your CLI tool")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",  # Key: action="count" instead of action="store_true"
        default=0,
        help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)",
    )
    args = parser.parse_args()

    # Setup logging based on verbosity count
    setup_logging(args.verbose)
    logger.info("Application started")

    # Your application logic
    try:
        logger.debug("Processing...")
        # ... your code ...
        logger.info("Completed successfully")
    except Exception as e:
        logger.error(f"Failed: {str(e)}")
        logger.debug("Full traceback:", exc_info=True)
        raise


if __name__ == "__main__":
    main()
```

### 3. Add Logging Throughout Your Codebase

**File**: `your_package/core/operations.py` (example)

```python
"""Core operations module.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def process_file(file_path: Path) -> dict[str, Any]:
    """Process a single file.

    Args:
        file_path: Path to file to process

    Returns:
        Result dictionary with status and metadata

    Raises:
        ValueError: If file is invalid
    """
    result: dict[str, Any] = {"file": str(file_path), "status": "failed"}

    try:
        # INFO: High-level operation start
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"Processing: {file_path} ({file_size_mb:.2f}MB)")

        # DEBUG: Detailed validation steps
        logger.debug(f"Validating file: {file_path}")
        _validate_file(file_path)
        logger.debug(f"Validation passed: {file_path}")

        # DEBUG: API call details
        logger.debug(f"Calling external API for: {file_path}")
        api_result = call_external_api(file_path)
        logger.debug(f"API returned status: {api_result.get('status')}")

        # INFO: Operation success
        result["status"] = "completed"
        logger.info(f"Processing completed successfully: {file_path}")

        return result

    except ValueError as e:
        # ERROR: Validation failures
        logger.error(f"Validation failed: {file_path}")
        logger.error(f"Validation error: {str(e)}")
        result["error"] = str(e)
        return result

    except Exception as e:
        # ERROR: Unexpected failures
        logger.error(f"Processing failed for {file_path}: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        # DEBUG: Full traceback (only shown with -vv or -vvv)
        logger.debug("Full traceback:", exc_info=True)
        result["error"] = f"Processing failed: {str(e)}"
        return result


def _validate_file(file_path: Path) -> None:
    """Validate file before processing.

    Args:
        file_path: Path to validate

    Raises:
        ValueError: If validation fails
    """
    logger.debug(f"Checking file exists: {file_path}")
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")

    logger.debug(f"Checking file size: {file_path}")
    if file_path.stat().st_size == 0:
        raise ValueError(f"File is empty: {file_path}")

    logger.debug(f"File validation passed: {file_path}")
```

### 4. Logging Best Practices

#### When to Use Each Level

**WARNING** (always shown):
- Critical errors that prevent operation
- Data loss or corruption
- Security issues
- Configuration problems

```python
logger.warning(f"Configuration missing: {key}, using default")
logger.warning(f"Deprecated feature used: {feature_name}")
```

**INFO** (`-v`):
- High-level operation status
- File/resource being processed
- Important milestones
- Summary statistics

```python
logger.info(f"Processing: {file_path}")
logger.info(f"Upload completed successfully: {file_path}")
logger.info(f"Found {count} items to process")
```

**DEBUG** (`-vv`):
- Detailed operation steps
- Validation results
- API call details (not full requests)
- Timing information
- Configuration values

```python
logger.debug(f"Validating file: {file_path}")
logger.debug(f"API call: endpoint={endpoint}, method={method}")
logger.debug(f"Operation completed in {duration:.2f}s")
logger.debug(f"Using configuration: workers={num_workers}")
```

**Full Tracebacks** (`-vv` with `exc_info=True`):
- Exception details with full stack traces
- Only use in exception handlers

```python
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {str(e)}")
    logger.debug("Full traceback:", exc_info=True)
```

#### Library-Level Logging (`-vvv`)

At trace level, enable logging from dependent libraries:

```python
# -vvv enables these automatically in setup_logging()
# httpx: HTTP request/response details
# boto3: AWS API calls
# google-api-core: Google API calls
# sqlalchemy: SQL queries
```

### 5. Complete Example: File Upload CLI

**Full working example showing all patterns:**

```python
"""File upload CLI with multi-level verbosity.

Example usage:
    # Quiet mode (warnings only)
    $ upload-cli files/*.txt

    # Verbose mode (see which files uploading)
    $ upload-cli files/*.txt -v

    # Debug mode (see validation, API calls)
    $ upload-cli files/*.txt -vv

    # Trace mode (see full HTTP requests)
    $ upload-cli files/*.txt -vvv
"""

import logging
from pathlib import Path
from typing import Any

import click

from your_package.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


@click.command()
@click.argument("files", nargs=-1, required=True)
@click.option("--bucket", required=True, help="S3 bucket name")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)",
)
def upload(files: tuple[str, ...], bucket: str, verbose: int) -> None:
    """Upload files to S3 bucket.

    FILES can be file paths or glob patterns.

    Examples:

    \b
        # Upload with INFO logging
        upload-cli document.pdf --bucket my-bucket -v

    \b
        # Upload with DEBUG logging
        upload-cli *.txt --bucket my-bucket -vv

    \b
        # Upload with TRACE logging (shows boto3 internals)
        upload-cli *.txt --bucket my-bucket -vvv
    """
    # Setup logging based on verbosity
    setup_logging(verbose)
    logger.info("Starting upload operation")

    # Expand glob patterns
    file_paths = _expand_patterns(files)
    logger.info(f"Found {len(file_paths)} files to upload")

    # Process files
    results = []
    for file_path in file_paths:
        result = _upload_file(file_path, bucket)
        results.append(result)

    # Summary
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")

    logger.info(f"Upload completed: {success_count} success, {failed_count} failed")

    if failed_count > 0:
        logger.error(f"{failed_count} uploads failed")
        raise click.ClickException("Some uploads failed")


def _upload_file(file_path: Path, bucket: str) -> dict[str, Any]:
    """Upload a single file to S3.

    Args:
        file_path: File to upload
        bucket: S3 bucket name

    Returns:
        Result dictionary with status
    """
    result: dict[str, Any] = {"file": str(file_path), "status": "failed"}

    try:
        # INFO: Operation start
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"Uploading: {file_path} ({file_size_mb:.2f}MB) to bucket '{bucket}'")

        # DEBUG: Validation
        logger.debug(f"Validating file: {file_path}")
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        logger.debug("Validation passed")

        # DEBUG: S3 upload (boto3 details shown with -vvv)
        logger.debug(f"Starting S3 upload: bucket={bucket}, key={file_path.name}")

        # Simulate S3 upload (replace with actual boto3 call)
        # s3_client.upload_file(str(file_path), bucket, file_path.name)

        # INFO: Success
        result["status"] = "success"
        logger.info(f"Upload completed successfully: {file_path}")

        return result

    except ValueError as e:
        # ERROR: Validation failure
        logger.error(f"Validation failed: {file_path}")
        logger.error(f"Error: {str(e)}")
        result["error"] = str(e)
        return result

    except Exception as e:
        # ERROR: Upload failure
        logger.error(f"Upload failed: {file_path}")
        logger.error(f"Error: {type(e).__name__}: {str(e)}")
        logger.debug("Full traceback:", exc_info=True)  # Shown with -vv or -vvv
        result["error"] = str(e)
        return result


def _expand_patterns(patterns: tuple[str, ...]) -> list[Path]:
    """Expand glob patterns to file paths.

    Args:
        patterns: Glob patterns or file paths

    Returns:
        List of file paths
    """
    logger.debug(f"Expanding patterns: {patterns}")
    files = []
    for pattern in patterns:
        expanded = list(Path().glob(pattern))
        logger.debug(f"Pattern '{pattern}' expanded to {len(expanded)} files")
        files.extend(expanded)
    return files


if __name__ == "__main__":
    upload()
```

## Testing Your Logging Implementation

### Test Script

```python
"""Test script to verify logging levels work correctly.

Run with different verbosity levels to see output:
    python test_logging.py        # WARNING only
    python test_logging.py -v     # INFO
    python test_logging.py -vv    # DEBUG
    python test_logging.py -vvv   # DEBUG + libraries
"""

import argparse
from your_package.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()

    setup_logging(args.verbose)

    # Test all log levels
    logger.debug("This is DEBUG (shown with -vv or -vvv)")
    logger.info("This is INFO (shown with -v, -vv, or -vvv)")
    logger.warning("This is WARNING (always shown)")
    logger.error("This is ERROR (always shown)")

    # Test exception logging
    try:
        raise ValueError("Test exception")
    except ValueError:
        logger.error("Caught exception (always shown)")
        logger.debug("Exception traceback:", exc_info=True)  # Only with -vv or -vvv


if __name__ == "__main__":
    main()
```

### Expected Output

**No flags** (WARNING only):
```
[WARNING] This is WARNING (always shown)
[ERROR] This is ERROR (always shown)
[ERROR] Caught exception (always shown)
```

**With `-v`** (INFO):
```
[INFO] This is INFO (shown with -v, -vv, or -vvv)
[WARNING] This is WARNING (always shown)
[ERROR] This is ERROR (always shown)
[ERROR] Caught exception (always shown)
```

**With `-vv`** (DEBUG):
```
[DEBUG] This is DEBUG (shown with -vv or -vvv)
[INFO] This is INFO (shown with -v, -vv, or -vvv)
[WARNING] This is WARNING (always shown)
[ERROR] This is ERROR (always shown)
[ERROR] Caught exception (always shown)
[DEBUG] Exception traceback:
Traceback (most recent call last):
  ...
```

**With `-vvv`** (TRACE + libraries):
```
[DEBUG] This is DEBUG (shown with -vv or -vvv)
[INFO] This is INFO (shown with -v, -vv, or -vvv)
[WARNING] This is WARNING (always shown)
[ERROR] This is ERROR (always shown)
[ERROR] Caught exception (always shown)
[DEBUG] Exception traceback:
Traceback (most recent call last):
  ...
[DEBUG] (httpx) HTTP Request: GET https://...
[DEBUG] (httpx) HTTP Response: 200 OK
```

## Common Dependent Libraries

Here are common Python libraries that provide useful logging at DEBUG level:

### HTTP Clients

```python
# httpx (modern HTTP client)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)

# requests + urllib3 (traditional HTTP client)
logging.getLogger("urllib3").setLevel(logging.DEBUG)
logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)
```

### AWS SDK

```python
# boto3 (AWS SDK)
logging.getLogger("boto3").setLevel(logging.DEBUG)
logging.getLogger("botocore").setLevel(logging.DEBUG)
logging.getLogger("botocore.credentials").setLevel(logging.DEBUG)
```

### Google Cloud SDK

```python
# google-cloud libraries
logging.getLogger("google.cloud").setLevel(logging.DEBUG)
logging.getLogger("google.api_core").setLevel(logging.DEBUG)
logging.getLogger("google.auth").setLevel(logging.DEBUG)
```

### Database Libraries

```python
# SQLAlchemy (SQL ORM)
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)  # SQL queries
logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)    # Connection pool

# asyncpg (PostgreSQL async)
logging.getLogger("asyncpg").setLevel(logging.DEBUG)
```

### Other Common Libraries

```python
# Paramiko (SSH)
logging.getLogger("paramiko").setLevel(logging.DEBUG)

# Celery (task queue)
logging.getLogger("celery").setLevel(logging.DEBUG)

# Alembic (database migrations)
logging.getLogger("alembic").setLevel(logging.DEBUG)
```

## Advanced Patterns

### Custom Log Formatting per Level

```python
def setup_logging(verbose_count: int = 0) -> None:
    """Setup logging with different formats per level."""
    if verbose_count == 0:
        level = logging.WARNING
        fmt = "[%(levelname)s] %(message)s"
    elif verbose_count == 1:
        level = logging.INFO
        fmt = "[%(levelname)s] %(message)s"
    elif verbose_count >= 2:
        level = logging.DEBUG
        # More detailed format for DEBUG
        fmt = "[%(levelname)s] %(name)s:%(lineno)d - %(message)s"

    logging.basicConfig(
        level=level,
        format=fmt,
        stream=sys.stderr,
        force=True,
    )
```

### Per-Module Verbosity Control

```python
def setup_logging(verbose_count: int = 0, module_levels: dict[str, int] | None = None) -> None:
    """Setup logging with per-module level control.

    Args:
        verbose_count: Global verbosity level
        module_levels: Per-module overrides, e.g. {"your_package.api": logging.DEBUG}
    """
    # Set global level
    if verbose_count == 0:
        level = logging.WARNING
    elif verbose_count == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s", stream=sys.stderr, force=True)

    # Apply per-module overrides
    if module_levels:
        for module, module_level in module_levels.items():
            logging.getLogger(module).setLevel(module_level)
```

### Structured Logging with JSON

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    """Format log records as JSON for machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging(verbose_count: int = 0, json_output: bool = False) -> None:
    """Setup logging with optional JSON output."""
    level = logging.DEBUG if verbose_count >= 2 else (logging.INFO if verbose_count == 1 else logging.WARNING)

    if json_output:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JSONFormatter())
        logging.basicConfig(level=level, handlers=[handler], force=True)
    else:
        logging.basicConfig(level=level, format="[%(levelname)s] %(message)s", stream=sys.stderr, force=True)
```

## Migration Guide

### Migrating from `print_verbose()` Pattern

**Before** (simple print pattern):
```python
def print_verbose(message: str, verbose: bool) -> None:
    if verbose:
        print(f"[INFO] {message}", file=sys.stderr)

# Usage
print_verbose("Processing file", verbose)
```

**After** (logging pattern):
```python
import logging
logger = logging.getLogger(__name__)

# Usage
logger.info("Processing file")
```

**Benefits**:
- No need to pass `verbose` parameter everywhere
- Automatic level filtering
- Dependent library logging support
- Traceback support with `exc_info=True`
- Easier testing and mocking

## Summary

**Key Takeaways**:

1. **Use `count=True`** in Click or `action="count"` in argparse
2. **Call `setup_logging()`** at the start of each command
3. **Use appropriate levels**: WARNING (critical), INFO (operations), DEBUG (details)
4. **Enable library logging** at trace level (`-vvv`)
5. **Log exceptions properly**: ERROR message + DEBUG traceback
6. **Output to stderr**: Keeps stdout clean for JSON/data output

**Pattern Summary**:
```python
# 1. Create logging_config.py with setup_logging()
# 2. CLI: @click.option("-v", "--verbose", count=True)
# 3. Command: setup_logging(verbose) at start
# 4. Modules: logger = logging.getLogger(__name__)
# 5. Use: logger.info(), logger.debug(), logger.error()
```

This pattern provides professional, flexible, and user-friendly logging for any Python CLI application!

## Learnings from Production Implementation

### Type Safety with Mypy

When implementing multi-level verbosity, ensure type compatibility across your codebase:

**Problem**: Changing from boolean verbose flag to integer count breaks type checking:
```python
# Old signature
@click.option("-v", "--verbose", is_flag=True)
def command(verbose: bool):
    pass

# New signature
@click.option("-v", "--verbose", count=True)
def command(verbose: int):
    pass
```

**Solution**: Use union types for backward compatibility in utility functions:
```python
def print_verbose(message: str, verbose: bool | int = False) -> None:
    """Print verbose message to stderr.

    Args:
        message: Message to print
        verbose: Whether verbose mode is enabled (bool or int count)
    """
    if verbose:
        click.echo(f"[INFO] {message}", err=True)
```

**Apply to all helper functions**:
```python
def _expand_file_patterns(patterns: list[str], verbose: bool | int) -> list[Path]:
    """Accepts both bool (legacy) and int (count-based) verbose."""
    pass

def _fetch_existing_documents(store_name: str, verbose: bool | int) -> dict[str, dict[str, Any]]:
    """Accepts both bool (legacy) and int (count-based) verbose."""
    pass
```

### Linting and Formatting

**Line Length**: Keep log statements under 100 characters (or your project's limit):
```python
# BAD: Line too long
logger.debug(f"Polling operation {operation_id} (attempt {poll_count}) - waiting {poll_interval}s")

# GOOD: Split across lines
logger.debug(
    f"Polling operation {operation_id} (attempt {poll_count}) - "
    f"waiting {poll_interval}s"
)
```

**f-strings**: Only use f-strings when they contain placeholders:
```python
# BAD: f-string without placeholder
logger.debug(f"Full traceback:", exc_info=True)

# GOOD: Regular string
logger.debug("Full traceback:", exc_info=True)
```

### Float Type Annotations

When using exponential backoff or similar patterns, explicitly annotate float types:
```python
# BAD: Mypy infers int, then fails on float assignment
poll_interval = 2
poll_interval = min(poll_interval * 1.5, max_interval)  # Type error!

# GOOD: Explicit float annotation
poll_interval: float = 2.0
max_interval: float = 30.0
poll_interval = min(poll_interval * 1.5, max_interval)  # Works!
```

### Testing the Implementation

Run your full pipeline to catch issues early:
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check with mypy
mypy your_package

# Run tests
pytest tests/

# Or use a Makefile
make pipeline  # format + lint + typecheck + test + build + install
```

### Migration Checklist

When migrating from boolean to count-based verbosity:

- [ ] Create `logging_config.py` module
- [ ] Change CLI option: `is_flag=True` → `count=True`
- [ ] Change parameter type: `bool` → `int`
- [ ] Add `setup_logging(verbose)` call at command start
- [ ] Update utility functions to accept `bool | int`
- [ ] Update all function signatures that receive verbose parameter
- [ ] Replace `print_verbose()` calls with `logger.info()`, `logger.debug()`
- [ ] Add type annotations for float variables if using exponential backoff
- [ ] Run linter and type checker
- [ ] Run full test suite
- [ ] Update documentation and help text

### Real-World Impact

Implementation in `gemini-file-search-tool` (2025-01):
- **Before**: 14 failed uploads, no visibility into failures
- **After**: Real-time logging showing which files failed and why
  - Empty files: Clear warning message, skipped (not failed)
  - MIME-type issues: Detected and registered automatically
  - API errors: Full operation tracking with exponential backoff logging
  - System files: Automatically filtered (__pycache__, .pyc, .DS_Store)
- **User Experience**: From "failed=14" with no context to detailed per-file feedback with `-v`, API operation details with `-vv`, and full HTTP traces with `-vvv`
