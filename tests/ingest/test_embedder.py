from unittest.mock import MagicMock, patch

from app.ingest.embedder import embed_texts


@patch("app.ingest.embedder.OpenAI")
def test_embed_texts_returns_one_vector_per_input(MockOpenAI: MagicMock) -> None:
    client = MagicMock()
    MockOpenAI.return_value = client
    client.embeddings.create.return_value.data = [
        MagicMock(embedding=[0.1] * 3072),
        MagicMock(embedding=[0.2] * 3072),
    ]

    vecs = embed_texts(["first clause", "second clause"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 3072
    assert vecs[0][0] == 0.1


@patch("app.ingest.embedder.OpenAI")
def test_embed_texts_batches_over_max_inputs(MockOpenAI: MagicMock) -> None:
    client = MagicMock()
    MockOpenAI.return_value = client

    # Mock to return the correct number of embeddings per call
    # 300 items -> 3 calls: [128, 128, 44]
    def side_effect(*args: object, **kwargs: object) -> MagicMock:
        inputs = kwargs.get("input", [])
        response = MagicMock()
        response.data = [MagicMock(embedding=[0.0] * 3072) for _ in range(len(inputs))]
        return response

    client.embeddings.create.side_effect = side_effect

    # 300 inputs should trigger 3 API calls (batch size 128)
    vecs = embed_texts(["x"] * 300)
    assert client.embeddings.create.call_count == 3
    assert len(vecs) == 300


@patch("app.ingest.embedder.OpenAI")
def test_embed_texts_empty_input_returns_empty(MockOpenAI: MagicMock) -> None:
    vecs = embed_texts([])
    assert vecs == []
    MockOpenAI.assert_not_called()
