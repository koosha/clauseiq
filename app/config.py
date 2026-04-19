from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    opensearch_url: str = "http://localhost:9200"
    opensearch_user: str = "admin"
    opensearch_password: str = "admin"
    opensearch_clauses_index: str = "clauses"

    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-large"
    openai_embedding_dim: int = 3072
    openai_classifier_model: str = "gpt-5-mini"
    openai_reranker_model: str = "gpt-5-nano"

    log_level: str = "INFO"
    contracts_dir: str = "./contracts/source_files"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
