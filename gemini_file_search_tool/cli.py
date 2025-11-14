"""CLI entry point for gemini-file-search-tool.

A command-line tool for managing Gemini File Search stores, uploading files,
and querying documents using Google's fully managed RAG system.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import click

from gemini_file_search_tool.commands.document_commands import (
    list_documents,
    upload,
)
from gemini_file_search_tool.commands.query_commands import query
from gemini_file_search_tool.commands.store_commands import (
    create_store,
    delete_store,
    get_store,
    list_stores,
    update_store,
)


@click.group()
@click.version_option(version="0.1.0", prog_name="gemini-file-search-tool")
def cli() -> None:
    """Gemini File Search Tool - Managed RAG for document search and Q&A.

    A CLI and library for managing Gemini File Search stores, uploading documents,
    and querying with Google's fully managed RAG system. Supports concurrent uploads,
    duplicate detection, and natural language queries with automatic citations.

    \b
    Authentication:
      Developer API (default):
        Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.
        Get your API key from: https://aistudio.google.com/app/apikey

    \b
      Vertex AI:
        Set GOOGLE_GENAI_USE_VERTEXAI=true
        Set GOOGLE_CLOUD_PROJECT='your-project-id'
        Set GOOGLE_CLOUD_LOCATION='us-central1'

    \b
    Examples:
      gemini-file-search-tool list-stores
      gemini-file-search-tool create-store --name "research-papers"
      gemini-file-search-tool upload "*.pdf" --store "research-papers"
      gemini-file-search-tool query --store "research-papers" --prompt "Summarize key findings"

    \b
    For detailed help on each command:
      gemini-file-search-tool create-store --help
      gemini-file-search-tool upload --help
      gemini-file-search-tool query --help
    """
    pass


# Register store commands
cli.add_command(create_store)
cli.add_command(list_stores)
cli.add_command(get_store)
cli.add_command(update_store)
cli.add_command(delete_store)

# Register document commands
cli.add_command(list_documents)
cli.add_command(upload)

# Register query commands
cli.add_command(query)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
