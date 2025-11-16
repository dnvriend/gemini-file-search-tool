"""Gemini File Search Tool - Python library and CLI.

This package provides both a command-line interface and a Python library for
managing Gemini File Search stores, uploading documents, and querying with
Google's fully managed RAG system.

Supports both traditional document RAG and Code-RAG (semantic code search).

Library Usage:
    from gemini_file_search_tool import create_store, upload_file, query_store

    # Create a store
    store = create_store("my-store")

    # Upload a file
    result = upload_file(Path("document.pdf"), store["name"])

    # Query the store
    response = query_store(store["name"], "What is in this document?")
    print(response["response_text"])

Code-RAG Example:
    from gemini_file_search_tool import create_store, upload_files_concurrent, query_store
    from pathlib import Path

    # Create store for codebase
    store = create_store("my-codebase")

    # Upload all Python files
    files = list(Path("src").glob("**/*.py"))
    upload_files_concurrent(files, store["name"])

    # Query with natural language
    response = query_store(
        store["name"],
        "How does the authentication system work?"
    )
    print(response["response_text"])

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

# Core client management
from gemini_file_search_tool.core.client import (
    ClientError,
    MissingConfigurationError,
    get_client,
    reset_client,
)

# Document operations
from gemini_file_search_tool.core.documents import (
    DocumentError,
    DocumentNotFoundError,
    FileValidationError,
    delete_document,
    list_documents,
    upload_file,
    upload_files_concurrent,
)

# Query operations
from gemini_file_search_tool.core.query import QueryError, query_store

# Store operations
from gemini_file_search_tool.core.stores import (
    StoreError,
    StoreNotFoundError,
    create_store,
    delete_store,
    get_store,
    list_stores,
    update_store,
)

# Utilities
from gemini_file_search_tool.utils import normalize_store_name

__version__ = "0.1.0"

__all__ = [
    # Client
    "get_client",
    "reset_client",
    "ClientError",
    "MissingConfigurationError",
    # Stores
    "create_store",
    "list_stores",
    "get_store",
    "update_store",
    "delete_store",
    "StoreError",
    "StoreNotFoundError",
    # Documents
    "list_documents",
    "upload_file",
    "upload_files_concurrent",
    "delete_document",
    "DocumentError",
    "DocumentNotFoundError",
    "FileValidationError",
    # Query
    "query_store",
    "QueryError",
    # Utilities
    "normalize_store_name",
    # Version
    "__version__",
]
