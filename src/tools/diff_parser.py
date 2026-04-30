"""
Tool: diff_parser - parse a unified diff into structured impact units.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy import text

from src.rag.engine import db_engine


_OLD_FILE_RE = re.compile(r"^--- (?:a/)?(.+?)(?:\s|$)")
_NEW_FILE_RE = re.compile(r"^\+\+\+ (?:b/)?(.+?)(?:\s|$)")
_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class FileChange:
	file_path: str
	change_type: str
	old_ranges: list[tuple[int, int]] = field(default_factory=list)
	new_ranges: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class AffectedSymbol:
	file_path: str
	symbol_name: str
	symbol_type: str
	start_line: int
	end_line: int
	is_test: bool


@dataclass
class DiffAnalysis:
	files: list[FileChange]
	affected_symbols: list[AffectedSymbol]


def _parse_diff(diff_text: str) -> list[FileChange]:
	"""Parse unified diff text into per-file FileChange records."""
	files: list[FileChange] = []
	current: FileChange | None = None
	old_path: str | None = None
	new_path: str | None = None

	for line in diff_text.splitlines():
		if line.startswith("diff --git "):
			if current is not None:
				files.append(current)
			current = None
			old_path = None
			new_path = None
			continue

		if line.startswith("--- "):
			match = _OLD_FILE_RE.match(line)
			if match:
				old_path = None if match.group(1) == "/dev/null" else match.group(1)
			continue

		if line.startswith("+++ "):
			match = _NEW_FILE_RE.match(line)
			if match:
				new_path = None if match.group(1) == "/dev/null" else match.group(1)

			if old_path is None and new_path is not None:
				change_type = "added"
				file_path = new_path
			elif old_path is not None and new_path is None:
				change_type = "deleted"
				file_path = old_path
			else:
				change_type = "modified"
				file_path = new_path or old_path or "<unknown>"

			current = FileChange(file_path=file_path, change_type=change_type)
			continue

		if line.startswith("@@") and current is not None:
			match = _HUNK_RE.match(line)
			if match:
				old_start = int(match.group(1))
				old_count = int(match.group(2)) if match.group(2) else 1
				new_start = int(match.group(3))
				new_count = int(match.group(4)) if match.group(4) else 1
				if old_count > 0:
					current.old_ranges.append((old_start, old_start + old_count - 1))
				if new_count > 0:
					current.new_ranges.append((new_start, new_start + new_count - 1))
			continue

	if current is not None:
		files.append(current)
	return files


def _ranges_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
	return a[0] <= b[1] and b[0] <= a[1]


def _fetch_chunks_for_file(file_path: str) -> list[dict]:
	"""Get all indexed chunks for a file, skipping class-level chunks as too coarse."""
	sql = """
		SELECT metadata
		FROM embeddings
		WHERE metadata->>'source' = 'code'
		  AND metadata->>'file_path' = :file_path
		  AND metadata->>'symbol_type' != 'class'
	"""
	with db_engine.connect() as conn:
		rows = conn.execute(text(sql), {"file_path": file_path}).fetchall()
	return [row[0] for row in rows]


def _affected_symbols_for_file(file_change: FileChange) -> list[AffectedSymbol]:
	"""Find indexed symbols whose pre-change line ranges overlap changed hunks."""
	if file_change.change_type == "added":
		return []

	ranges = file_change.old_ranges
	if not ranges:
		return []

	chunks = _fetch_chunks_for_file(file_change.file_path)
	affected: list[AffectedSymbol] = []
	for chunk in chunks:
		symbol_range = (chunk.get("start_line", 0), chunk.get("end_line", 0))
		if any(_ranges_overlap(symbol_range, changed_range) for changed_range in ranges):
			affected.append(
				AffectedSymbol(
					file_path=file_change.file_path,
					symbol_name=chunk.get("symbol_name", "?"),
					symbol_type=chunk.get("symbol_type", "?"),
					start_line=symbol_range[0],
					end_line=symbol_range[1],
					is_test=chunk.get("is_test", False),
				)
			)

	affected.sort(key=lambda symbol: symbol.start_line)
	return affected


def parse_diff(diff_text: str) -> DiffAnalysis:
	"""Parse a unified diff and return file-level and symbol-level impact info."""
	files = _parse_diff(diff_text)

	affected_symbols: list[AffectedSymbol] = []
	for file_change in files:
		affected_symbols.extend(_affected_symbols_for_file(file_change))

	return DiffAnalysis(files=files, affected_symbols=affected_symbols)


if __name__ == "__main__":
	import sys
	from pathlib import Path

	if len(sys.argv) < 2:
		print("Usage: python -m src.tools.diff_parser <path/to/diff.patch>")
		sys.exit(1)

	diff_text = Path(sys.argv[1]).read_text()
	result = parse_diff(diff_text)

	print(f"=== Files changed: {len(result.files)} ===")
	for file_change in result.files:
		print(f"  [{file_change.change_type:8s}] {file_change.file_path}")
		for changed_range in file_change.old_ranges:
			print(f"      old lines: {changed_range[0]}-{changed_range[1]}")

	print(f"\n=== Affected symbols: {len(result.affected_symbols)} ===")
	for symbol in result.affected_symbols:
		tag = " [TEST]" if symbol.is_test else ""
		print(
			f"  {symbol.file_path} :: {symbol.symbol_name} ({symbol.symbol_type}) "
			f"L{symbol.start_line}-{symbol.end_line}{tag}"
		)
