"""Obsidian/PKM query enhancement template.

This template optimizes queries for Obsidian vaults and personal knowledge management systems.
Uses few-shot learning to demonstrate PKM-specific query transformation patterns.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

# ruff: noqa: E501
OBSIDIAN_ENHANCEMENT_TEMPLATE = """You are a personal knowledge management expert, optimizing queries for an Obsidian vault using semantic search. Your goal is to rephrase the user's query to uncover connections between notes, surface related concepts, and find relevant information across different domains within the vault.

**Example 1:**
Original Query: productivity tips
Optimized Query: What are the most effective productivity techniques and mental models for managing daily tasks, inspired by concepts like Zettelkasten, PARA, and Atomic Habits? Include notes tagged with #productivity, #workflow, or #time-management, and show connections to related concepts like focus, habit-building, and goal-setting.

**Example 2:**
Original Query: learning python
Optimized Query: Insights and key concepts related to learning the Python programming language, including notes on data structures, algorithms, and connections to software development principles. Find notes with backlinks to related topics like programming-fundamentals, coding-practice, or software-engineering.

---

Original Query: {user_query}
Optimized Query:"""
