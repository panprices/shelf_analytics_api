import requests
import pytest

from .config import BASE_URL, AUTH_HEADERS


def test_get_countries(benchmark):
    response = benchmark(requests.get, f"{BASE_URL}/countries", headers=AUTH_HEADERS)
    assert response.status_code in range(200, 300)


def test_get_retailers(benchmark):
    response = benchmark(requests.get, f"{BASE_URL}/retailers", headers=AUTH_HEADERS)
    assert response.status_code in range(200, 300)


def test_get_categories(benchmark):
    response = benchmark(requests.get, f"{BASE_URL}/categories", headers=AUTH_HEADERS)
    assert response.status_code in range(200, 300)


def test_get_groups(benchmark):
    response = benchmark(requests.get, f"{BASE_URL}/groups", headers=AUTH_HEADERS)
    assert response.status_code in range(200, 300)
