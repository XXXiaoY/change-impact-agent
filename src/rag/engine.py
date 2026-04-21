"""
RAG engine: Handles embedding generation, PGVector storage, and retrieval.
"""

import json

from openai import OpenAI
from sqlalchemy import text

from src.config import settings
from src.rag.database import engine as db_engine

client = OpenAI(api_key=settings.openai_api_key)


def generate_embedding(text_input: str) -> list[float]:
	"""Generate embedding vector for a text string."""
	response = client.embeddings.create(
		model=settings.embedding_model,
		input=text_input,
	)
	return response.data[0].embedding


def store_embedding(content: str, metadata: dict) -> int:
	"""Store content with its embedding and metadata. Returns the row ID."""
	embedding = generate_embedding(content)

	with db_engine.connect() as conn:
		result = conn.execute(
			text(
				"""
				INSERT INTO embeddings (content, embedding, metadata)
				VALUES (:content, :embedding, :metadata)
				RETURNING id
			"""
			),
			{
				"content": content,
				"embedding": str(embedding),
				"metadata": json.dumps(metadata),
			},
		)
		row_id = result.scalar()
		conn.commit()
		return row_id


def store_embeddings_batch(items: list[dict]) -> int:
	"""Store multiple items. Each item has 'content' and 'metadata' keys.
	Returns the number of items stored."""
	if not items:
		return 0

	# Generate embeddings in batch (OpenAI supports batch input)
	texts = [item["content"] for item in items]
	response = client.embeddings.create(
		model=settings.embedding_model,
		input=texts,
	)
	embeddings = [d.embedding for d in response.data]

	with db_engine.connect() as conn:
		for item, embedding in zip(items, embeddings):
			conn.execute(
				text(
					"""
					INSERT INTO embeddings (content, embedding, metadata)
					VALUES (:content, :embedding, :metadata)
				"""
				),
				{
					"content": item["content"],
					"embedding": str(embedding),
					"metadata": json.dumps(item["metadata"]),
				},
			)
		conn.commit()

	return len(items)


def search(query: str, top_k: int = 5, filters: dict = None) -> list[dict]:
	"""Search for similar content using vector similarity.

	Args:
		query: Search query text
		top_k: Number of results to return
		filters: Optional metadata filters, e.g. {"source": "code", "is_test": false}

	Returns:
		List of dicts with 'content', 'metadata', and 'similarity' keys
	"""
	query_embedding = generate_embedding(query)

	# Build filter clause
	filter_clauses = []
	filter_params = {}
	if filters:
		for i, (key, value) in enumerate(filters.items()):
			param_name = f"filter_{i}"
			filter_clauses.append(f"metadata->>'{key}' = :{param_name}")
			filter_params[param_name] = str(value).lower() if isinstance(value, bool) else str(value)

	where_clause = ""
	if filter_clauses:
		where_clause = "WHERE " + " AND ".join(filter_clauses)

	sql = f"""
		SELECT content, metadata,
			   1 - (embedding <=> :query_embedding) AS similarity
		FROM embeddings
		{where_clause}
		ORDER BY embedding <=> :query_embedding
		LIMIT :top_k
	"""

	with db_engine.connect() as conn:
		conn.execute(text("SET LOCAL ivfflat.probes = 10"))
		result = conn.execute(
			text(sql),
			{"query_embedding": str(query_embedding), "top_k": top_k, **filter_params},
		)
		rows = result.fetchall()

	return [
		{
			"content": row[0],
			"metadata": row[1] if isinstance(row[1], dict) else json.loads(row[1]),
			"similarity": float(row[2]),
		}
		for row in rows
	]
