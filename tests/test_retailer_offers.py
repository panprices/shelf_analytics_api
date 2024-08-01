import pytest
from fastapi.testclient import TestClient
from app.main import app  # Import the FastAPI app instance
from benchmark.config import BASE_URL, AUTH_HEADERS

client = TestClient(app)

def test_export_products_to_xlsx():
    # Prepare the request payload
    payload = {
        "start_date": "2024-04-30",
        "countries": [],
        "retailers": [],
        "categories": [],
        "groups": [],
        "search_text": "",
        "page_number": 0,
        "page_size": 0,
        "data_grid_filter": {
            "operator": "and",
            "items": [
                {"column": "name", "value": "ab", "operator": "contains"},
                {"column": "available_at_retailer", "operator": "is", "value": "true"}
            ]
        },
        "currency": "SEK"
    }

    # Send the request with authentication headers
    response = client.post(f"{BASE_URL}/products/retailers/export", json=payload, headers=AUTH_HEADERS)

    # Print the response content for debugging
    if response.status_code != 200:
        print("Response JSON:", response.json())

    # Check the response status code
    assert response.status_code == 200

    # Additional validation (if necessary)
    content_type = response.headers.get("Content-Type")
    if content_type:
        assert content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        print("Content-Type header is missing.")
