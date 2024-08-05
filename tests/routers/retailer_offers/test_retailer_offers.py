from fastapi.testclient import TestClient
from app.main import app  # Import the FastAPI app instance
from benchmark.config import BASE_URL, AUTH_HEADERS
from tests.routers.retailer_offers.helpers import (
    PAYLOAD,
    check_http_status,
    check_fields
)

client = TestClient(app)

def test_export_products_to_xlsx():
    # Send the request with authentication headers
    response = client.post(
        f"{BASE_URL}/products/retailers/export",
        json=PAYLOAD,
        headers=AUTH_HEADERS
    )
    check_http_status(response)

    # Check the response status code
    assert response.status_code == 200

    # Additional validation (if necessary)
    content_type = response.headers.get("Content-Type")
    if content_type:
        assert content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        print("Content-Type header is missing.")

def test_retailer_offers():
    # Send the request with authentication headers
    response = client.post(
        f"{BASE_URL}/products/retailers",
        json=PAYLOAD,
        headers=AUTH_HEADERS
    )
    check_http_status(response)
    data = response.json()
    # Check that we get the fields we expect
    check_fields(data)