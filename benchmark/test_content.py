import requests
import pytest

from .config import BASE_URL, AUTH_HEADERS
from .filters import filters


@pytest.mark.parametrize("payload", filters.values())
def test_post_content_score(benchmark, payload):
    response = benchmark(
        requests.post,
        f"{BASE_URL}/content/score",
        headers=AUTH_HEADERS,
        json=payload,
    )
    assert response.status_code in range(200, 300)
