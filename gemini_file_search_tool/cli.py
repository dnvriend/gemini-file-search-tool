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
    """Gemini File Search Tool

    A command-line tool for managing Gemini File Search stores, uploading files,
    and querying documents using Google's fully managed RAG system.
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
