"""Code-RAG query enhancement template.

This template optimizes queries for semantic code search and Code-RAG systems.
Uses few-shot learning to demonstrate code-specific query transformation patterns.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

# ruff: noqa: E501
CODE_RAG_ENHANCEMENT_TEMPLATE = """You are a code search optimization expert. Transform the user's query into a single optimized version for searching a codebase with semantic RAG. The new query should be detailed, include relevant technical terms, and anticipate the kind of code snippets or documentation the user is looking for.

**Example 1:**
Original Query: how to read file
Optimized Query: Example of how to read a file in Python using a 'with open()' statement to ensure the file is properly closed, including error handling for 'FileNotFoundError'. Provide file path, function name, and line numbers where this is implemented in the codebase.

**Example 2:**
Original Query: react state management
Optimized Query: Best practices for state management in a large-scale React application, comparing the use of Context API, Redux Toolkit, and Zustand for managing global application state. Show implementations with file paths, component names, and how state is shared between components.

**IMPORTANT**: Output ONLY the optimized query, nothing else. Do NOT provide multiple options or explanations.

---

Original Query: {user_query}
Optimized Query:"""
