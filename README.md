# Change Impact Analysis Agent

A multi-step investigation agent that analyzes PR diffs to identify affected modules, trace dependency chains, and generate structured risk reports by retrieving evidence from code, commit history, and incident records.

## Architecture

```
Input: PR diff (unified diff format)
        │
        ▼
┌────────────────────────────────────────┐
│        LangGraph Workflow              │
│                                        │
│  Stage 1: Parse Diff                   │
│     └─ diff_parser + ast_analyzer      │
│              │                         │
│  Stage 2: Impact Trace                 │
│     └─ code_search + commit_search     │
│              │                         │
│  Stage 3: Risk Assessment              │
│     └─ incident_search + risk rules    │
│              │                         │
│  Stage 4: Report Generation            │
│     └─ LLM structured report           │
│                                        │
├────────────────────────────────────────┤
│          RAG Knowledge Base            │
│  ┌──────────┬────────────┬───────────┐ │
│  │  Code    │  Commits   │ Incidents │ │
│  │  Chunks  │  History   │ Records   │ │
│  └──────────┴────────────┴───────────┘ │
│          PostgreSQL + PGVector         │
└────────────────────────────────────────┘
        │
        ▼
Output: Structured Impact Analysis Report
```

## Tech Stack

- **Language**: Python 3.13
- **Agent Orchestration**: LangGraph
- **Code Parsing**: tree-sitter (Python grammar)
- **Vector Database**: PostgreSQL + PGVector
- **Embedding**: OpenAI text-embedding-3-small
- **LLM**: OpenAI GPT-4o (configurable)
- **Git Operations**: GitPython
- **API**: FastAPI

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database config

# 4. Set up PostgreSQL + PGVector
# (see docs/setup.md)

# 5. Index demo repo
python -m src.indexer.index_repo

# 6. Run analysis
python -m src.main --diff path/to/diff.patch
```

## Project Structure

```
change-impact-agent/
├── src/
│   ├── agent/          # LangGraph workflow & state
│   ├── tools/          # Agent tools (diff_parser, ast_analyzer, etc.)
│   ├── rag/            # RAG engine (embedding, storage, retrieval)
│   ├── indexer/        # Knowledge base indexing (code, commits, incidents)
│   └── models/         # Data models (Pydantic schemas)
├── demo_repo/          # Demo Python project for testing
├── tests/              # Unit & integration tests
├── data/
│   └── incidents.json  # Pre-built incident records
└── docs/
    └── design.md       # Architecture decision records
```
