"""
Index code chunks into PGVector.

Takes CodeChunks from code_chunker, generates embeddings, and stores them in
the code_embeddings table with full metadata for later retrieval.
"""

from __future__ import annotations

import time
from pathlib import Path

from src.indexer.code_chunker import CodeChunk, chunk_repo
from src.rag.engine import store_embedding


def _build_embedding_text(chunk: CodeChunk) -> str:
    """
    Build the text that actually gets embedded.

    Structure: path + symbol header + calls hint + source body.
    This gives the embedding model hierarchical context (where this symbol lives,
    what it's called, who it talks to) on top of the raw code.
    """
    header = f"File: {chunk.file_path}\nSymbol: {chunk.symbol_name} ({chunk.symbol_type})"
    if chunk.calls:
        header += f"\nCalls: {', '.join(chunk.calls[:10])}"
    if chunk.is_test:
        header += "\n[TEST CODE]"
    return f"{header}\n\n{chunk.content}"


def _build_metadata(chunk: CodeChunk) -> dict:
    """Metadata stored alongside the embedding for filtering and display."""
    return {
        "source": "code",
        "file_path": chunk.file_path,
        "symbol_name": chunk.symbol_name,
        "symbol_type": chunk.symbol_type,
        "imports": chunk.imports,
        "calls": chunk.calls,
        "is_test": chunk.is_test,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
    }


def index_repo(repo_path: str | Path, verbose: bool = True) -> int:
    """
    Chunk a repo and index every chunk into PGVector.
    Returns the number of chunks indexed.
    """
    chunks = chunk_repo(repo_path)
    if verbose:
        print(f"Chunking done: {len(chunks)} chunks to index.")

    t0 = time.time()
    for i, chunk in enumerate(chunks, start=1):
        text = _build_embedding_text(chunk)
        metadata = _build_metadata(chunk)
        row_id = store_embedding(text, metadata)
        if verbose and i % 10 == 0:
            print(f"  indexed {i}/{len(chunks)}  (last id={row_id})")

    elapsed = time.time() - t0
    if verbose:
        print(
            f"Done. Indexed {len(chunks)} chunks in {elapsed:.1f}s "
            f"(~{elapsed/len(chunks)*1000:.0f}ms per chunk)."
        )
    return len(chunks)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.indexer.code_indexer <repo_path>")
        sys.exit(1)
    index_repo(sys.argv[1])
