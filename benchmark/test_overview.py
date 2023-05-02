import requests
import pytest

from .config import BASE_URL, AUTH_HEADERS


def test_get_countries(benchmark):
    f = lambda: requests.request("GET", f"{BASE_URL}/countries", headers=AUTH_HEADERS)
    benchmark(f)


def test_get_retailers(benchmark):
    f = lambda: requests.request("GET", f"{BASE_URL}/retailers", headers=AUTH_HEADERS)
    benchmark(f)


def test_get_categories(benchmark):
    f = lambda: requests.request("GET", f"{BASE_URL}/categories", headers=AUTH_HEADERS)
    benchmark(f)


def test_get_groups(benchmark):
    f = lambda: requests.request("GET", f"{BASE_URL}/groups", headers=AUTH_HEADERS)
    benchmark(f)
