"""
Tool: ast_analyzer — structural queries over code symbols.

Unlike code_search (semantic), this tool works on structural relationships:
    - forward:  what does symbol X call / import?
    - reverse:  who calls symbol X?  (impact trace)

Data comes from the metadata stored at index time by code_chunker. No extra
parsing at query time.

Design notes:
  - Callers are matched heuristically: we match on method name suffix, not
    full qualified name. E.g. a caller with `self.payment_service.process_refund`
    in its calls list is considered a caller of `PaymentService.process_refund`.
    This is deliberately lossy — full type resolution is expensive and not
    needed for "show the agent candidate call sites".
"""

from __future__ import annotations

from sqlalchemy import text

from src.rag.engine import db_engine


def _fetch_all_code_chunks() -> list[dict]:
    """Load every indexed code chunk's metadata + content."""
    sql = """
        SELECT content, metadata
        FROM embeddings
        WHERE metadata->>'source' = 'code'
    """
    with db_engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
    return [{"content": r[0], "metadata": r[1]} for r in rows]


def _method_suffix(symbol_name: str) -> str:
    """Take 'OrderService.cancel_order' -> 'cancel_order'."""
    return symbol_name.split(".")[-1]


def get_symbol_info(file_path: str, symbol_name: str) -> dict | None:
    """
    Forward lookup: return the full metadata + content for a given symbol.
    Returns None if no exact match.
    """
    sql = """
        SELECT content, metadata
        FROM embeddings
        WHERE metadata->>'source' = 'code'
          AND metadata->>'file_path' = :file_path
          AND metadata->>'symbol_name' = :symbol_name
        LIMIT 1
    """
    with db_engine.connect() as conn:
        row = conn.execute(
            text(sql),
            {"file_path": file_path, "symbol_name": symbol_name},
        ).fetchone()

    if row is None:
        return None

    md = row[1]
    return {
        "symbol_name": md.get("symbol_name"),
        "file_path": md.get("file_path"),
        "symbol_type": md.get("symbol_type"),
        "calls": md.get("calls", []),
        "imports": md.get("imports", []),
        "is_test": md.get("is_test", False),
        "start_line": md.get("start_line"),
        "end_line": md.get("end_line"),
        "content": row[0],
    }


def find_callers(symbol_name: str, include_tests: bool = True) -> list[dict]:
    """
    Reverse lookup: find all symbols whose `calls` list references `symbol_name`.

    Matching heuristic: a caller is a match if any entry in its `calls` list
    ends with '.method_name' or equals 'method_name' itself. This catches:
        - self.payment_service.process_refund  (method call via attribute)
        - PaymentService.process_refund        (direct class reference)
        - process_refund                       (module-level function call)
    """
    target = _method_suffix(symbol_name)
    all_chunks = _fetch_all_code_chunks()

    callers = []
    for chunk in all_chunks:
        md = chunk["metadata"]
        if not include_tests and md.get("is_test"):
            continue
        if md.get("symbol_type") == "class":
            continue

        calls = md.get("calls", [])
        matched_call = None
        for c in calls:
            if c == target or c.endswith(f".{target}"):
                matched_call = c
                break

        if matched_call:
            callers.append({
                "symbol_name": md.get("symbol_name"),
                "file_path": md.get("file_path"),
                "symbol_type": md.get("symbol_type"),
                "is_test": md.get("is_test", False),
                "matched_call": matched_call,
                "start_line": md.get("start_line"),
                "end_line": md.get("end_line"),
            })

    callers.sort(key=lambda c: (c["is_test"], c["file_path"], c["start_line"] or 0))
    return callers


def ast_analyze(file_path: str, symbol_name: str, include_tests: bool = True) -> dict:
    """
    Main entry point: given a symbol, return both forward (what it calls)
    and reverse (who calls it) structural info.

    Returns:
        {
            "symbol": {...full info from get_symbol_info...} | None,
            "callers": [...list of callers from find_callers...],
            "caller_count": int,
            "test_caller_count": int,
        }
    """
    symbol_info = get_symbol_info(file_path, symbol_name)
    callers = find_callers(symbol_name, include_tests=include_tests)

    return {
        "symbol": symbol_info,
        "callers": callers,
        "caller_count": len(callers),
        "test_caller_count": sum(1 for c in callers if c["is_test"]),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m src.tools.ast_analyzer <file_path> <symbol_name>")
        print(
            "Example: python -m src.tools.ast_analyzer "
            "src/services/payment_service.py PaymentService.process_refund"
        )
        sys.exit(1)

    result = ast_analyze(sys.argv[1], sys.argv[2])
    sym = result["symbol"]
    if sym is None:
        print(f"Symbol not found: {sys.argv[1]} :: {sys.argv[2]}")
        sys.exit(1)

    print(f"=== {sym['symbol_name']} ({sym['symbol_type']}) ===")
    print(f"  file:    {sym['file_path']} (L{sym['start_line']}-{sym['end_line']})")
    print(f"  calls:   {sym['calls']}")
    print(f"  imports: {sym['imports'][:5]}{'...' if len(sym['imports']) > 5 else ''}")
    print(
        f"\n=== Callers: {result['caller_count']} "
        f"({result['test_caller_count']} in tests) ==="
    )
    for c in result["callers"]:
        tag = " [TEST]" if c["is_test"] else ""
        print(f"  {c['file_path']} :: {c['symbol_name']}{tag}")
        print(f"      matched via: {c['matched_call']}")
