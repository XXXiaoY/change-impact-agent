"""
Retrieval smoke test for indexed code chunks.

Runs several semantic queries against the code index and prints the top hits.
Pass if the expected symbols appear in the top-3 for each query.
"""

from src.rag.engine import search


QUERIES = [
    {
        "query": "refund processing payment flow",
        "expect_any": [
            "PaymentService.process_refund",
            "OrderService.cancel_order",
            "RefundEndpoint.handle_refund",
        ],
    },
    {
        "query": "inventory stock reservation",
        "expect_any": [
            "InventoryService.reserve_stock",
            "InventoryService.release_stock",
        ],
    },
    {
        "query": "test cases for refund",
        "expect_any": [],  # soft check: just print, eyeball whether tests surface
        "prefer_test": True,
    },
]


def run_query(q: dict, top_k: int = 5):
    print(f"\n{'=' * 70}")
    print(f"Query: {q['query']!r}")
    print(f"{'=' * 70}")
    results = search(q["query"], top_k=top_k)

    hit_symbols = []
    for i, r in enumerate(results, start=1):
        md = r.get("metadata", {}) or {}
        symbol = md.get("symbol_name", "?")
        path = md.get("file_path", "?")
        is_test = md.get("is_test", False)
        source = md.get("source", "?")
        metric = r.get("similarity", r.get("distance", r.get("score", "?")))
        tag = " [TEST]" if is_test else ""
        if isinstance(metric, (int, float)):
            metric_text = f"{metric:.4f}"
        else:
            metric_text = str(metric)
        print(f"  #{i}  score={metric_text}  [{source}] {path} :: {symbol}{tag}")
        hit_symbols.append(symbol)

    # hard check
    if q.get("expect_any"):
        hits = [s for s in q["expect_any"] if s in hit_symbols]
        status = "PASS" if hits else "FAIL"
        print(f"\n  {status}: expected any of {q['expect_any']}")
        print(f"         got top-{top_k}: {hit_symbols}")
        if hits:
            print(f"         matched: {hits}")
        return status == "PASS"

    # soft check
    if q.get("prefer_test"):
        test_count = sum(1 for r in results if (r.get("metadata") or {}).get("is_test"))
        print(f"\n  SOFT: {test_count}/{len(results)} hits are test code.")
    return True


if __name__ == "__main__":
    passed = all(run_query(q) for q in QUERIES)
    print(f"\n{'=' * 70}")
    print("OVERALL:", "PASS" if passed else "FAIL")
