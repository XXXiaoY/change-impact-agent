"""
Cross-source retrieval smoke test.

Verifies that a single semantic query can pull relevant hits from all three
knowledge sources (code / commit / incident). This is the foundation for the
agent's ability to produce reports that combine "what changed" + "who touched
it recently" + "what broke here before".
"""

from collections import Counter

from src.rag.engine import search


QUERIES = [
    {
        "query": "refund logic changes and failures",
        "expect_sources": {"code", "commit", "incident"},
        "expect_hints": ["process_refund", "a3f9c21", "INC-4521"],
    },
    {
        "query": "inventory race condition flash sale",
        "expect_sources": {"code", "commit", "incident"},
        "expect_hints": ["reserve_stock", "d8f6b13", "INC-3654"],
    },
    {
        "query": "order cancellation timeout",
        "expect_sources": {"code", "commit", "incident"},
        "expect_hints": ["cancel_order", "b7e2d88", "INC-3892"],
    },
]


def _label(md: dict) -> str:
    """Format a result row based on its source type."""
    src = md.get("source", "?")
    if src == "code":
        return f"[code]     {md.get('file_path', '?')} :: {md.get('symbol_name', '?')}"
    if src == "commit":
        return f"[commit]   {md.get('commit_id', '?')}  \"{md.get('message', '')[:60]}\""
    if src == "incident":
        return f"[incident] {md.get('incident_id', '?')} ({md.get('severity', '?')}) {md.get('title', '')[:50]}"
    return f"[{src}] {md}"


def _identifier(md: dict) -> str:
    """Pull the identifying string used for hint matching."""
    return (
        md.get("symbol_name")
        or md.get("commit_id")
        or md.get("incident_id")
        or ""
    )


def run_query(q: dict, top_k: int = 10) -> bool:
    print(f"\n{'=' * 70}")
    print(f"Query: {q['query']!r}")
    print(f"{'=' * 70}")

    results = search(q["query"], top_k=top_k)

    source_counts = Counter()
    identifiers = []

    for i, r in enumerate(results, start=1):
        md = r.get("metadata", {}) or {}
        source_counts[md.get("source", "?")] += 1
        identifiers.append(_identifier(md))
        print(f"  #{i:2d}  score={r.get('similarity', r.get('score', 0)):.4f}  {_label(md)}")

    # check 1: all expected sources appear in top-k
    got_sources = {s for s, _ in source_counts.items() if s != "?"}
    sources_ok = q["expect_sources"].issubset(got_sources)

    # check 2: expected specific items show up
    hints_hit = [h for h in q["expect_hints"] if any(h in idf for idf in identifiers)]
    hints_ok = len(hints_hit) >= 2  # at least 2 of 3 hints should surface

    print(f"\n  sources in top-{top_k}: {dict(source_counts)}")
    print(f"  hint matches: {hints_hit} / expected {q['expect_hints']}")

    status = "PASS" if (sources_ok and hints_ok) else "FAIL"
    if not sources_ok:
        print(f"  [X] missing sources: {q['expect_sources'] - got_sources}")
    if not hints_ok:
        print(f"  [X] fewer than 2 expected hints surfaced")
    print(f"  {status}")
    return sources_ok and hints_ok


if __name__ == "__main__":
    passed = all(run_query(q) for q in QUERIES)
    print(f"\n{'=' * 70}")
    print("OVERALL:", "PASS" if passed else "FAIL")
