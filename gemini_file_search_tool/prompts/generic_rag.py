"""Generic RAG query enhancement template.

This template optimizes queries for general document retrieval using RAG best practices.
Uses few-shot learning to demonstrate effective query transformation patterns.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

# ruff: noqa: E501
GENERIC_ENHANCEMENT_TEMPLATE = """You are a RAG query optimization expert. Your task is to transform a user's query into a more detailed and semantically rich query that will improve retrieval from a vector database. Focus on adding relevant keywords, clarifying intent, and expanding on the original concept.

**Example 1:**
Original Query: database connection issues
Optimized Query: How to diagnose and resolve common database connection errors in a Python application using SQLAlchemy, including handling timeouts, authentication failures, and network problems.

**Example 2:**
Original Query: file search tool
Optimized Query: Implementing a high-performance file search utility in Python, focusing on efficient directory traversal, multithreading for speed, and using libraries like 'glob' and 'os.walk'.

---

Original Query: {user_query}
Optimized Query:"""
