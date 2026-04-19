from opensearchpy import OpenSearch

from app.config import get_settings


CLAUSES_INDEX_BODY = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100,
        },
        "analysis": {
            "analyzer": {
                "legal_english": {
                    "type": "standard",
                    "stopwords": "_english_",
                }
            }
        },
    },
    "mappings": {
        "properties": {
            "clause_id": {"type": "keyword"},
            "contract_id": {"type": "keyword"},
            "agreement_type": {"type": "keyword"},
            "clause_family": {"type": "keyword"},
            "governing_law": {"type": "keyword"},
            "jurisdiction": {"type": "keyword"},
            "section_path": {"type": "text"},
            "heading_text": {"type": "text"},
            "text_display": {"type": "text", "analyzer": "legal_english"},
            "text_normalized": {
                "type": "text",
                "analyzer": "legal_english",
                "similarity": "BM25",
            },
            "embedding": {
                "type": "knn_vector",
                "dimension": 3072,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "lucene",
                    "parameters": {"ef_construction": 128, "m": 16},
                },
            },
        }
    },
}


def ensure_clauses_index(client: OpenSearch) -> None:
    idx = get_settings().opensearch_clauses_index
    if not client.indices.exists(index=idx):
        client.indices.create(index=idx, body=CLAUSES_INDEX_BODY)
