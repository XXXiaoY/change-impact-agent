"""
Tool: code_search — semantic search over indexed code chunks.

The agent calls this to find code relevant to a natural-language query
(e.g. "refund amount validation", "inventory stock deduction"). Filters
by source='code' so commit/incident records don't pollute the results.

Optional knobs:
    - include_tests: whether to return test code alongside production code.
      Defaults True because "is there test coverage for X?" is itself a
      valid question the agent asks.
    - file_path_prefix: restrict to a subdirectory (e.g. "src/services/").
      Used by impact trace to ask "other code in the same service".
"""

from __future__ import annotations

from src.rag.engine import search


def code_search(
    query: str,
    top_k: int = 5,
    include_tests: bool = True,
    file_path_prefix: str | None = None,
) -> list[dict]:
    """
    Semantic search over indexed code chunks.

    Returns a list of dicts:
        {
            "symbol_name": "OrderService.cancel_order",
            "file_path":   "src/services/order_service.py",
            "symbol_type": "method",
            "is_test":     False,
            "start_line":  45,
            "end_line":    62,
            "calls":       [...],
            "imports":     [...],
            "similarity":  0.58,
            "content":     "<full source text>",
        }
    """
    # Over-fetch to leave room for post-filters (tests exclusion, path prefix).
    # These two filters are structural, not semantic, so doing them post-search
    # is cheap and avoids complicating the SQL layer.
    raw_top_k = top_k * 3 if (not include_tests or file_path_prefix) else top_k

    raw = search(query, top_k=raw_top_k, filters={"source": "code"})

    results = []
    for r in raw:
        md = r.get("metadata") or {}

        # post-filter: exclude tests if asked
        if not include_tests and md.get("is_test"):
            continue

        # post-filter: restrict to a path prefix
        if file_path_prefix and not md.get("file_path", "").startswith(file_path_prefix):
            continue

        results.append({
            "symbol_name": md.get("symbol_name"),
            "file_path": md.get("file_path"),
            "symbol_type": md.get("symbol_type"),
            "is_test": md.get("is_test", False),
            "start_line": md.get("start_line"),
            "end_line": md.get("end_line"),
            "calls": md.get("calls", []),
            "imports": md.get("imports", []),
            "similarity": r["similarity"],
            "content": r["content"],
        })

        if len(results) >= top_k:
            break

    return results


# ---- CLI for quick manual testing ----
if __name__ == "__main__":
    import sys

    query = sys.argv[1] if len(sys.argv) > 1 else "refund validation"
    hits = code_search(query, top_k=5, include_tests=False)
    for h in hits:
        print(
            f"  {h['similarity']:.3f}  {h['file_path']} :: {h['symbol_name']}  "
            f"(L{h['start_line']}-{h['end_line']})"
        )
    print("\n[first hit content preview]")
    if hits:
        print(hits[0]["content"][:300])
