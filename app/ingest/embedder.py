"""Batched text embedder backed by the configured OpenAI embedding model."""

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

# OpenAI embedding endpoint accepts up to 2048 inputs per call; we keep batches
# small enough to stay well inside TPM limits on the 3072-dim model.
MAX_BATCH = 128


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _embed_batch(client: OpenAI, texts: list[str], model: str) -> list[list[float]]:
    response = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in response.data]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return one embedding vector per input text, batching API calls as needed."""
    if not texts:
        return []
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    embeddings: list[list[float]] = []
    for start in range(0, len(texts), MAX_BATCH):
        batch = texts[start : start + MAX_BATCH]
        embeddings.extend(_embed_batch(client, batch, settings.openai_embedding_model))
    return embeddings
