from opensearchpy import OpenSearch

from app.config import get_settings


def make_client() -> OpenSearch:
    s = get_settings()
    return OpenSearch(
        hosts=[s.opensearch_url],
        http_auth=(s.opensearch_user, s.opensearch_password),
        use_ssl=s.opensearch_url.startswith("https"),
        verify_certs=False,
        ssl_show_warn=False,
    )
