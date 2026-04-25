"""
Index mock commit records into PGVector.

Reads data/commits.json and stores each commit as an embedding with
source='commit' metadata, so it can be retrieved alongside code chunks
and incident records.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.rag.engine import store_embedding


def _build_embedding_text(commit: dict) -> str:
    """
    Build the text to embed for a commit.

    Combines message + affected files + diff summary so semantic queries like
    'recent changes to refund logic' can hit on either the commit message or
    the diff content.
    """
    parts = [
        f"Commit: {commit['commit_id']}",
        f"Date: {commit['date']}",
        f"Message: {commit['message']}",
        f"Files changed: {', '.join(commit['affected_files'])}",
        f"Summary: {commit['diff_summary']}",
    ]
    if commit.get("related_incidents"):
        parts.append(f"Related incidents: {', '.join(commit['related_incidents'])}")
    return "\n".join(parts)


def _build_metadata(commit: dict) -> dict:
    return {
        "source": "commit",
        "commit_id": commit["commit_id"],
        "date": commit["date"],
        "author": commit["author"],
        "message": commit["message"],
        "affected_files": commit["affected_files"],
        "related_incidents": commit.get("related_incidents", []),
    }


def index_commits(commits_path: str | Path = "data/commits.json", verbose: bool = True) -> int:
    commits = json.loads(Path(commits_path).read_text())
    if verbose:
        print(f"Loaded {len(commits)} commits from {commits_path}")

    for i, commit in enumerate(commits, start=1):
        text = _build_embedding_text(commit)
        metadata = _build_metadata(commit)
        row_id = store_embedding(text, metadata)
        if verbose:
            print(f"  [{i}/{len(commits)}] {commit['commit_id']} -> id={row_id}")

    if verbose:
        print(f"Done. Indexed {len(commits)} commits.")
    return len(commits)


if __name__ == "__main__":
    index_commits()
