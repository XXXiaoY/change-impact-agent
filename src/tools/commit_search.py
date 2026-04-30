"""
Tool: commit_search - search commit history and incident records.

Two query modes:
  1. Semantic mode: natural-language query -> vector similarity search,
     filtered to source IN ('commit', 'incident').
  2. File mode: given a file path, return all commits/incidents whose
     `affected_files` list includes that path. No embedding involved;
     this is a precise structural lookup.
"""

from __future__ import annotations

from sqlalchemy import text

from src.rag.engine import db_engine, search


def _normalize_metadata(md: dict) -> dict:
	"""Convert raw metadata into a stable shape for both commits and incidents."""
	src = md.get("source")
	if src == "commit":
		return {
			"source": "commit",
			"id": md.get("commit_id"),
			"date": md.get("date"),
			"author": md.get("author"),
			"title": md.get("message"),
			"affected_files": md.get("affected_files", []),
			"related_incidents": md.get("related_incidents", []),
			"severity": None,
		}
	if src == "incident":
		return {
			"source": "incident",
			"id": md.get("incident_id"),
			"date": md.get("date"),
			"author": None,
			"title": md.get("title"),
			"affected_files": md.get("affected_files", []),
			"related_incidents": [],
			"severity": md.get("severity"),
			"root_cause": md.get("root_cause"),
			"resolution": md.get("resolution"),
		}
	return {"source": src, **md}


def commit_search(
	query: str | None = None,
	file_path: str | None = None,
	sources: list[str] | None = None,
	top_k: int = 10,
) -> list[dict]:
	"""
	Search commit and incident history.

	Exactly one of `query` or `file_path` must be provided.
	"""
	if (query is None) == (file_path is None):
		raise ValueError("Provide exactly one of `query` or `file_path`.")

	if sources is None:
		sources = ["commit", "incident"]

	if file_path is not None:
		sql = """
			SELECT content, metadata
			FROM embeddings
			WHERE metadata->>'source' = ANY(:sources)
			  AND metadata->'affected_files' ? :file_path
			ORDER BY metadata->>'date' DESC
		"""
		with db_engine.connect() as conn:
			rows = conn.execute(
				text(sql),
				{"sources": sources, "file_path": file_path},
			).fetchall()
		return [
			{
				**_normalize_metadata(row[1]),
				"content": row[0],
				"similarity": None,
			}
			for row in rows
		]

	raw = search(query, top_k=top_k, filters={"source": sources})
	return [
		{
			**_normalize_metadata(result["metadata"]),
			"content": result["content"],
			"similarity": result["similarity"],
		}
		for result in raw
	]


if __name__ == "__main__":
	import sys

	if len(sys.argv) < 2:
		print("Usage:")
		print("  python -m src.tools.commit_search --query 'refund failures'")
		print("  python -m src.tools.commit_search --file src/services/payment_service.py")
		sys.exit(1)

	if sys.argv[1] == "--query":
		results = commit_search(query=" ".join(sys.argv[2:]))
		print(f"Semantic results ({len(results)}):")
	elif sys.argv[1] == "--file":
		results = commit_search(file_path=sys.argv[2])
		print(f"File history for {sys.argv[2]} ({len(results)}):")
	else:
		print("Unknown mode")
		sys.exit(1)

	for result in results:
		sim = f" sim={result['similarity']:.3f}" if result["similarity"] is not None else ""
		sev = f" [{result['severity']}]" if result["severity"] else ""
		print(f"  [{result['source']}]{sev} {result['id']}: {result['title'][:60]}{sim}")
		if result["affected_files"]:
			print(f"      files: {result['affected_files']}")
