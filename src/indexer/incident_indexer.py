"""
Index incident records into PGVector.

Reads data/incidents.json and stores each incident as an embedding with
source='incident' metadata. Used by the agent's risk assessment step to
surface 'this code area has been the source of past P1/P2 incidents'.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.rag.engine import store_embedding


def _build_embedding_text(incident: dict) -> str:
    """
    Combine title + root cause + resolution + affected files.

    Root cause is the most semantically valuable field - it's what makes
    'race condition in stock' queries hit INC-3654. Files are included so
    file-name queries also work.
    """
    parts = [
        f"Incident: {incident['incident_id']} ({incident['severity']})",
        f"Date: {incident['date']}",
        f"Title: {incident['title']}",
        f"Affected files: {', '.join(incident['affected_files'])}",
        f"Root cause: {incident['root_cause']}",
        f"Resolution: {incident['resolution']}",
    ]
    return "\n".join(parts)


def _build_metadata(incident: dict) -> dict:
    return {
        "source": "incident",
        "incident_id": incident["incident_id"],
        "severity": incident["severity"],
        "date": incident["date"],
        "title": incident["title"],
        "affected_files": incident["affected_files"],
        "root_cause": incident["root_cause"],
        "resolution": incident["resolution"],
    }


def index_incidents(incidents_path: str | Path = "data/incidents.json", verbose: bool = True) -> int:
    incidents = json.loads(Path(incidents_path).read_text())
    if verbose:
        print(f"Loaded {len(incidents)} incidents from {incidents_path}")

    for i, incident in enumerate(incidents, start=1):
        text = _build_embedding_text(incident)
        metadata = _build_metadata(incident)
        row_id = store_embedding(text, metadata)
        if verbose:
            print(f"  [{i}/{len(incidents)}] {incident['incident_id']} ({incident['severity']}) -> id={row_id}")

    if verbose:
        print(f"Done. Indexed {len(incidents)} incidents.")
    return len(incidents)


if __name__ == "__main__":
    index_incidents()
