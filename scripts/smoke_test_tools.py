"""
Smoke test for Day 6 tools: code_search + ast_analyzer.

Verifies:
  1. code_search returns only source='code' results
  2. code_search respects include_tests flag
  3. ast_analyzer finds the correct callers for a known method
  4. ast_analyzer flags missing test coverage correctly
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.tools.ast_analyzer import ast_analyze
from src.tools.code_search import code_search


def test_code_search_filters_to_code():
    """code_search must never return commits or incidents."""
    print("\n[test] code_search returns only source=code")
    hits = code_search("refund", top_k=10)
    non_code = [h for h in hits if h.get("symbol_name") is None]
    assert not non_code, f"Got non-code hits: {non_code}"
    print(f"  PASS: all {len(hits)} hits are code chunks")


def test_code_search_excludes_tests():
    """include_tests=False must drop test files."""
    print("\n[test] code_search include_tests=False")
    all_hits = code_search("refund", top_k=10, include_tests=True)
    prod_hits = code_search("refund", top_k=10, include_tests=False)

    test_in_all = sum(1 for h in all_hits if h["is_test"])
    test_in_prod = sum(1 for h in prod_hits if h["is_test"])

    print(f"  include_tests=True:  {test_in_all} test hits in top 10")
    print(f"  include_tests=False: {test_in_prod} test hits in top 10")
    assert test_in_prod == 0, "test chunks leaked with include_tests=False"
    print("  PASS")


def test_ast_analyzer_finds_callers():
    """PaymentService.process_refund should have callers in OrderService / RefundEndpoint."""
    print("\n[test] ast_analyze finds callers of PaymentService.process_refund")
    result = ast_analyze(
        "src/services/payment_service.py",
        "PaymentService.process_refund",
    )

    assert result["symbol"] is not None, "symbol not found"
    print(f"  target found: {result['symbol']['symbol_name']}")
    print(
        f"  total callers: {result['caller_count']} "
        f"({result['test_caller_count']} in tests)"
    )

    caller_symbols = [c["symbol_name"] for c in result["callers"]]
    print(f"  callers: {caller_symbols}")

    expect_any = ["OrderService.cancel_order", "RefundEndpoint.handle_refund"]
    hits = [s for s in expect_any if s in caller_symbols]
    assert hits, f"missing expected callers, got: {caller_symbols}"
    print(f"  PASS: matched {hits}")


def test_ast_analyzer_detects_missing_test_coverage():
    """
    RefundEndpoint.handle_refund has no tests (by demo_repo design).
    find_callers of handle_refund should return only prod callers (or none).
    """
    print("\n[test] ast_analyze confirms RefundEndpoint has no test coverage")
    result = ast_analyze(
        "src/api/refund_endpoint.py",
        "RefundEndpoint.handle_refund",
    )
    print(f"  callers: {result['caller_count']}  (tests: {result['test_caller_count']})")

    assert result["test_caller_count"] == 0, (
        f"expected 0 test callers for RefundEndpoint.handle_refund, "
        f"got {result['test_caller_count']}"
    )
    print("  PASS: no test callers, demo story holds")


if __name__ == "__main__":
    test_code_search_filters_to_code()
    test_code_search_excludes_tests()
    test_ast_analyzer_finds_callers()
    test_ast_analyzer_detects_missing_test_coverage()
    print("\n" + "=" * 60)
    print("OVERALL: PASS")
