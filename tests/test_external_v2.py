import pytest
from fastapi.testclient import TestClient
from app.main import app  # Import the FastAPI app instance
from benchmark.config import BASE_URL

client = TestClient(app)

def test_get_retailer_offers_no_filters():
    # Send the request with authentication headers
    response = client.get(
        f"{BASE_URL}/v2/products/retailer_offers",
        headers= {
            "x-api-key": "loupe_3dnXjnT4xc24KAoqFbiPKI0JjHhnuVyoY5098kZDGuwo40BP",
            "Accept": "application/json",
        }
    )

    # Print the response content for debugging
    if response.status_code != 200:
        print("Response JSON:", response.json())

    # Check the response status code
    assert response.status_code == 200

    data = response.json()
    
    # Check the structure of the response
    assert "rows" in data
    assert "count" in data
    assert "page" in data
    assert "pages_count" in data
    
    # You can validate specific data points if needed
    # For example, check if the count matches expected values
    assert isinstance(data["rows"], list)
    assert isinstance(data["count"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["pages_count"], int)
    
    # Validate data content
    if data["rows"]:
        assert "id" in data["rows"][0]
        assert "name" in data["rows"][0]
        assert "available_at_retailer" in data["rows"][0]