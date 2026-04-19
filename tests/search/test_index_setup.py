from unittest.mock import MagicMock

from app.search.index_mapping import CLAUSES_INDEX_BODY, ensure_clauses_index


def test_index_body_has_required_fields():
    props = CLAUSES_INDEX_BODY["mappings"]["properties"]
    assert props["clause_id"]["type"] == "keyword"
    assert props["contract_id"]["type"] == "keyword"
    assert props["clause_family"]["type"] == "keyword"
    assert props["text_normalized"]["type"] == "text"
    assert props["text_normalized"]["similarity"] == "BM25"
    assert props["embedding"]["type"] == "knn_vector"
    assert props["embedding"]["dimension"] == 3072


def test_index_body_enables_knn():
    assert CLAUSES_INDEX_BODY["settings"]["index"]["knn"] is True


def test_ensure_clauses_index_creates_when_missing():
    client = MagicMock()
    client.indices.exists.return_value = False

    ensure_clauses_index(client)

    client.indices.exists.assert_called_once()
    client.indices.create.assert_called_once()
    call_args = client.indices.create.call_args
    assert call_args.kwargs["body"] == CLAUSES_INDEX_BODY


def test_ensure_clauses_index_noop_when_present():
    client = MagicMock()
    client.indices.exists.return_value = True

    ensure_clauses_index(client)

    client.indices.create.assert_not_called()
