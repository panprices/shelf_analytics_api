import requests
import pytest

from .config import BASE_URL, AUTH_HEADERS
from .filters import filters


@pytest.mark.parametrize("payload", filters.values())
def test_post_availability_per_retailer(benchmark, payload):
    response = benchmark(
        requests.post,
        f"{BASE_URL}/availability/per_retailer",
        headers=AUTH_HEADERS,
        json=payload,
    )
    assert response.status_code in range(200, 300)
