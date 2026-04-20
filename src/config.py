from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/impact_agent"

    # Models
    llm_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # RAG
    code_chunk_top_k: int = 10
    commit_top_k: int = 5
    incident_top_k: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
