"""
Database setup: PostgreSQL + PGVector table creation and connection management.
"""

from sqlalchemy import create_engine, text

from src.config import settings

engine = create_engine(settings.database_url)


def init_db():
	"""Create the embeddings table if it doesn't exist."""
	with engine.connect() as conn:
		conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
		conn.execute(
			text(
				f"""
			CREATE TABLE IF NOT EXISTS embeddings (
				id SERIAL PRIMARY KEY,
				content TEXT NOT NULL,
				embedding vector({settings.embedding_dimensions}),
				metadata JSONB NOT NULL DEFAULT '{{}}'
			);
		"""
			)
		)
		# Index for vector similarity search
		conn.execute(
			text(
				"""
			CREATE INDEX IF NOT EXISTS idx_embeddings_vector
			ON embeddings USING ivfflat (embedding vector_cosine_ops)
			WITH (lists = 10);
		"""
			)
		)
		conn.commit()
		print("Database initialized.")


def reset_db():
	"""Drop and recreate the embeddings table."""
	with engine.connect() as conn:
		conn.execute(text("DROP TABLE IF EXISTS embeddings;"))
		conn.commit()
	init_db()


if __name__ == "__main__":
	init_db()

