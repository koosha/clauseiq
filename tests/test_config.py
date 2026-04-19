import pytest
from pydantic import ValidationError
from app.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/d")
    monkeypatch.setenv("OPENSEARCH_URL", "http://localhost:9200")
    monkeypatch.setenv("OPENSEARCH_USER", "admin")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "admin")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    s = Settings()

    assert s.database_url == "postgresql+psycopg://u:p@h:5432/d"
    assert s.openai_embedding_model == "text-embedding-3-large"
    assert s.openai_embedding_dim == 3072
    assert s.openai_classifier_model == "gpt-5-mini"
    assert s.openai_reranker_model == "gpt-5-nano"
    assert s.opensearch_clauses_index == "clauses"


def test_settings_rejects_missing_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
