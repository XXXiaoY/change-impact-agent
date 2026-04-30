"""
Smoke test for Day 7 tools: commit_search + diff_parser.

Verifies:
  1. commit_search semantic mode returns commits + incidents only
  2. commit_search file mode finds known history for a file
  3. commit_search file mode + sources filter narrows correctly
  4. diff_parser handles all three demo diffs and maps to expected symbols
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.tools.commit_search import commit_search
from src.tools.diff_parser import parse_diff


def test_commit_search_semantic():
	print("\n[test] commit_search semantic mode")
	results = commit_search(query="refund validation failures", top_k=5)
	sources = {result["source"] for result in results}
	assert sources.issubset({"commit", "incident"}), f"unexpected sources: {sources}"
	print(f"  PASS: {len(results)} hits, sources={sources}")
	for result in results[:3]:
		print(f"    [{result['source']}] {result['id']}: {result['title'][:60]}")


def test_commit_search_by_file():
	"""payment_service.py should have known history."""
	print("\n[test] commit_search file mode for payment_service.py")
	results = commit_search(file_path="src/services/payment_service.py")
	ids = [result["id"] for result in results]
	print(f"  found {len(results)} records: {ids}")

	expect = ["a3f9c21", "INC-4521"]
	hits = [expected for expected in expect if expected in ids]
	assert hits == expect, f"missing expected history: {set(expect) - set(ids)}"
	print(f"  PASS: matched {hits}")


def test_commit_search_by_file_only_incidents():
	print("\n[test] commit_search file mode + sources=['incident']")
	results = commit_search(
		file_path="src/services/payment_service.py",
		sources=["incident"],
	)
	sources = {result["source"] for result in results}
	assert sources == {"incident"}, f"got non-incident sources: {sources}"
	print(f"  PASS: {len(results)} incidents, all source=incident")


def test_diff_parser_all_demo_diffs():
	"""Run parse_diff on each demo diff and print the resulting impact map."""
	diff_dir = Path("data/diffs")
	for diff_file in sorted(diff_dir.glob("*.patch")):
		print(f"\n[test] diff_parser: {diff_file.name}")
		diff_text = diff_file.read_text()
		result = parse_diff(diff_text)

		print(f"  files: {[(fc.file_path, fc.change_type) for fc in result.files]}")
		print(f"  affected symbols ({len(result.affected_symbols)}):")
		for symbol in result.affected_symbols:
			tag = " [TEST]" if symbol.is_test else ""
			print(f"    {symbol.file_path} :: {symbol.symbol_name}{tag}")

		assert len(result.files) > 0, "no files parsed from diff"
		prod_modified = [
			file_change
			for file_change in result.files
			if file_change.change_type == "modified" and "tests/" not in file_change.file_path
		]
		if prod_modified:
			prod_symbols = [symbol for symbol in result.affected_symbols if not symbol.is_test]
			assert prod_symbols, (
				f"diff modifies prod file {[fc.file_path for fc in prod_modified]} "
				f"but no symbols mapped - check line range alignment"
			)
		print("  PASS")


if __name__ == "__main__":
	test_commit_search_semantic()
	test_commit_search_by_file()
	test_commit_search_by_file_only_incidents()
	test_diff_parser_all_demo_diffs()
	print("\n" + "=" * 60)
	print("OVERALL: PASS")
