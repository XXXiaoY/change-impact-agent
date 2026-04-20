"""
LangGraph workflow for Change Impact Analysis.

Stages:
    1. Parse Diff     - Extract changed files and symbols from unified diff
    2. Impact Trace   - Find dependents via code search and AST analysis
    3. Risk Assessment - Evaluate risk using commit history and incident records
    4. Report Generation - Produce structured impact analysis report
"""

