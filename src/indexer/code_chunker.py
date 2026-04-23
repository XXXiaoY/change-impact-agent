"""
AST-aware code chunker for Python repositories.

Splits Python files into semantically complete chunks at the function/class/method
level, using tree-sitter for accurate parsing. Each chunk carries structural
metadata (imports, call targets, test flag) for downstream impact analysis.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())
_parser = Parser(PY_LANGUAGE)


@dataclass
class CodeChunk:
    file_path: str          # relative path from repo root
    symbol_name: str        # "OrderService.cancel_order" or "calculate_total"
    symbol_type: str        # "function" | "class" | "method"
    content: str            # full source text of the symbol
    imports: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    is_test: bool = False
    start_line: int = 0
    end_line: int = 0


# -------------------------------------------------------------------
# File discovery
# -------------------------------------------------------------------
def _iter_python_files(repo_path: Path):
    """Yield all .py files under repo_path, skipping __pycache__ / .git / venv."""
    skip_dirs = {"__pycache__", ".git", ".venv", "venv", "node_modules"}
    for path in repo_path.rglob("*.py"):
        if any(part in skip_dirs for part in path.parts):
            continue
        yield path


# -------------------------------------------------------------------
# Per-file extraction
# -------------------------------------------------------------------
def _extract_imports(root_node, source_bytes: bytes) -> list[str]:
    """Collect all imported names from `import X` and `from Y import Z` statements."""
    imports = []
    for child in root_node.children:
        if child.type == "import_statement":
            # import a, b.c
            for name_node in child.children:
                if name_node.type in ("dotted_name", "aliased_import"):
                    imports.append(source_bytes[name_node.start_byte:name_node.end_byte].decode())
        elif child.type == "import_from_statement":
            # from a.b import c, d
            module_node = child.child_by_field_name("module_name")
            module = source_bytes[module_node.start_byte:module_node.end_byte].decode() if module_node else ""
            for name_node in child.children_by_field_name("name"):
                name = source_bytes[name_node.start_byte:name_node.end_byte].decode()
                imports.append(f"{module}.{name}" if module else name)
    return imports


def _extract_calls(node, source_bytes: bytes) -> list[str]:
    """Walk a subtree and collect all function call targets as dotted names."""
    calls = []

    def walk(n):
        if n.type == "call":
            fn_node = n.child_by_field_name("function")
            if fn_node is not None:
                calls.append(source_bytes[fn_node.start_byte:fn_node.end_byte].decode())
        for child in n.children:
            walk(child)

    walk(node)
    # dedup while preserving order
    seen = set()
    unique = []
    for c in calls:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


def _get_name(node, source_bytes: bytes) -> str:
    name_node = node.child_by_field_name("name")
    return source_bytes[name_node.start_byte:name_node.end_byte].decode() if name_node else "<unknown>"


def _chunks_from_file(file_path: Path, repo_root: Path) -> list[CodeChunk]:
    """Parse one .py file and return its CodeChunks."""
    source_bytes = file_path.read_bytes()
    tree = _parser.parse(source_bytes)
    root = tree.root_node

    rel_path = str(file_path.relative_to(repo_root))
    is_test = "tests" in file_path.parts or file_path.name.startswith("test_")
    file_imports = _extract_imports(root, source_bytes)

    chunks: list[CodeChunk] = []

    for node in root.children:
        if node.type == "function_decorated_definition":
            # unwrap: decorators + function_definition
            node = next((c for c in node.children if c.type == "function_definition"), node)

        if node.type == "function_definition":
            chunks.append(_make_chunk(
                node, source_bytes, rel_path, is_test, file_imports,
                symbol_type="function",
                symbol_name=_get_name(node, source_bytes),
            ))

        elif node.type == "class_definition":
            class_name = _get_name(node, source_bytes)
            # one chunk for the class itself (captures docstring + class-level code)
            chunks.append(_make_chunk(
                node, source_bytes, rel_path, is_test, file_imports,
                symbol_type="class",
                symbol_name=class_name,
            ))
            # one chunk per method
            body = node.child_by_field_name("body")
            if body is not None:
                for member in body.children:
                    if member.type == "function_decorated_definition":
                        member = next((c for c in member.children if c.type == "function_definition"), member)
                    if member.type == "function_definition":
                        chunks.append(_make_chunk(
                            member, source_bytes, rel_path, is_test, file_imports,
                            symbol_type="method",
                            symbol_name=f"{class_name}.{_get_name(member, source_bytes)}",
                        ))

    return chunks


def _make_chunk(node, source_bytes, rel_path, is_test, file_imports,
                *, symbol_type, symbol_name) -> CodeChunk:
    content = source_bytes[node.start_byte:node.end_byte].decode()
    return CodeChunk(
        file_path=rel_path,
        symbol_name=symbol_name,
        symbol_type=symbol_type,
        content=content,
        imports=file_imports,
        calls=_extract_calls(node, source_bytes),
        is_test=is_test,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
    )


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------
def chunk_repo(repo_path: str | Path) -> list[CodeChunk]:
    repo_root = Path(repo_path).resolve()
    if not repo_root.is_dir():
        raise ValueError(f"Not a directory: {repo_root}")

    all_chunks: list[CodeChunk] = []
    for py_file in _iter_python_files(repo_root):
        try:
            all_chunks.extend(_chunks_from_file(py_file, repo_root))
        except Exception as e:
            print(f"[WARN] Failed to parse {py_file}: {e}")
    return all_chunks


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.indexer.code_chunker <repo_path>")
        sys.exit(1)

    chunks = chunk_repo(sys.argv[1])
    print(f"Total chunks: {len(chunks)}\n")
    for ch in chunks:
        print(f"[{ch.symbol_type}] {ch.file_path} :: {ch.symbol_name}  (L{ch.start_line}-{ch.end_line}, test={ch.is_test})")
        if ch.calls:
            print(f"    calls: {ch.calls[:5]}{'...' if len(ch.calls) > 5 else ''}")
