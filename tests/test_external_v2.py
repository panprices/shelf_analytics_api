import pytest
from fastapi.testclient import TestClient
from app.main import app  # Import the FastAPI app instance
from benchmark.config import BASE_URL
import random
import http.client

client = TestClient(app)

# This is an API key created for VD in sandbox environment.
# TODO: Don't send an API key to GitHub. Since it is sandbox, it is fine for now.
SANDBOX_API_KEY = "loupe_3dnXjnT4xc24KAoqFbiPKI0JjHhnuVyoY5098kZDGuwo40BP"
# We want to test the iteration of pages in the API
# Therefore we will randomly select a number of pages to test
MAX_PAGES = random.randint(2, 7)

def make_request(page, api_version, user_currency):
    # Construct the parameters for the request
    params = {}
    if page is not None:
        params["page"] = page
    if user_currency is not None:
        params["user_currency"] = user_currency    
    # Send the request with authentication headers
    response = client.get(
        f"{BASE_URL}/{api_version}/products/retailer_offers",
        headers= {
            "x-api-key": SANDBOX_API_KEY,
            "Accept": "application/json",
        },
        params=params
    )
    return response

def check_http_status(response):
    # Check the response status code
    status_code = response.status_code
    status_message = http.client.responses.get(response.status_code, "Unknown Status Code")
    # Use assert to check for success and print status if not successful
    assert status_code == 200, f"Expected status code 200 but got {status_code} ({status_message})"

def check_basics(data):
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
    assert "id" in data["rows"][0]
    assert "name" in data["rows"][0]
    assert "available_at_retailer" in data["rows"][0]

def check_fields(data, api_version):
   # List the fields we are expecting the API to return
    expected_fields = [
        "id", "url", "name", "description", "gtin", "retailer_name", 
        "country", "retailer_price", "currency", "review_average", 
        "number_of_reviews", "popularity_index", "retailer_images_count", 
        "brand_images_count", "title_matching_score", "environmental_images_count", 
        "transparent_images_count", "obsolete_images_count", "sku", 
        "wholesale_price", "in_stock", "matched_brand_product_id", 
        "brand_in_stock", "available_at_retailer", "retailer_category_name", 
        "title_score", "description_score", "specs_score", "text_score", 
        "image_score", "content_score", "is_discounted", "retailer_original_price", 
        "fetched_at", "created_at", "brand_sku", "msrp", "msrp_currency", 
        "price_deviation", "wholesale_currency", "markup_factor", 
        "category_page_number", "category_pages_count", "category_products_count", 
        "product_retailer_status", "screenshot_url", "price_standard", 
        "original_price_standard", "client_images_count", "msrp_standard", 
        "wholesale_price_standard"
    ]
    if api_version == "v2.1":
        expected_fields.extend("retailer_price_in_user_currency", "user_currency")
    # Check that all the fields we expect are in the response
    for row in data["rows"]:
        for field in expected_fields:
            assert field in row, f"Missing '{field}' in row with id {row.get('id')}"
        # Check that there are no unexpected fields in the response
        for field in row.keys():
            assert field in expected_fields, f"Unexpected field '{field}' found in row with id {row.get('id')}"

def check_user_currency(data, user_currency):
    # If no user_currency was requested, no need to check the user_currency field
    if user_currency is None:    
        return
    for row in data["rows"]:
        # Verify that the currency in the response matches the requested currency
        response_currency = row.get("currency")
        assert response_currency == user_currency, (
            f"Expected currency '{user_currency}' but found '{response_currency}' in row with id {row.get('id')}"
        )

def get_retailer_offers_no_filters_in_test(
        page=None,
        api_version="v2",
        user_currency=None
    ):
    response = make_request(page, api_version, user_currency)
    check_http_status(response)
    data = response.json()
    check_basics(data)
    check_fields(data, api_version)
    if api_version == "v2.1":
        check_user_currency(data, user_currency)
    return {
        "rows": data["rows"],
        "count": data["count"],
        "page": data["page"],
        "pages_count": data["pages_count"],
    }

def test_get_retailer_offers_no_filters_v2(page=None):
    response = get_retailer_offers_no_filters_in_test(page)
    # Exit the recursion if we have reached the maximum number of pages
    if response["page"] >= MAX_PAGES:
        return
    # Exit the recursion if we have reached the last page
    elif response["page"] == response["pages_count"]:
        return
    # Continue the recursion if we have not reached the last page
    else:
        test_get_retailer_offers_no_filters_v2(page=response["page"] + 1)

def test_get_retailer_offers_no_filters_v21(page=None):
    # Sending a currency or None to test the user_currency get parameter
    user_currency = random.choice(["SEK", "EUR", "DKK", None])
    response = get_retailer_offers_no_filters_in_test(
        page,
        api_version="v2.1",
        user_currency=user_currency
    )
    # Exit the recursion if we have reached the maximum number of pages
    if response["page"] >= MAX_PAGES:
        return
    # Exit the recursion if we have reached the last page
    elif response["page"] == response["pages_count"]:
        return
    # Continue the recursion if we have not reached the last page
    else:
        test_get_retailer_offers_no_filters_v2(
            page=response["page"] + 1,
            api_version="v2.1",
            user_currency=user_currency
        )