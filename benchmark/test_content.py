import requests
import pytest

from .config import BASE_URL, AUTH_HEADERS
from .filters import filters


def test_post_content_score(benchmark):
    payload = filters["none"]
    f = lambda: requests.request(
        "POST", f"{BASE_URL}/content/score", headers=AUTH_HEADERS, json=payload
    )
    benchmark(f)
