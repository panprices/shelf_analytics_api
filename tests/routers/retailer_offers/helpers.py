import http

PAYLOAD = {
    "page_number": 1,
    "page_size": 10,
    "start_date": "2022-09-01",
    "countries": [],
    "retailers": [],
    "categories": [],
    "groups": [],
    "data_grid_filter": {
        "operator": "and",
        "items": [

            {
                "column": "name",
                "value": "ab",
                "operator": "contains"
            },
            {
                "column": "available_at_retailer",
                "operator": "is",
                "value": "true"
            }
        ]
    },
    "currency": "CNY"
}

def check_fields(data):
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
        "wholesale_price_standard",
        "retailer_price_in_user_currency", "user_currency"
    ]
    for row in data["rows"]:
        for field in expected_fields:
            assert field in row, f"Missing '{field}' in row with id {row.get('id')}"
        for field in row.keys():
            assert field in expected_fields, f"Unexpected field '{field}' found in row with id {row.get('id')}"

def check_http_status(response):
    status_code = response.status_code
    status_message = http.client.responses.get(response.status_code, "Unknown Status Code")
    assert status_code == 200, f"Expected status code 200 but got {status_code} ({status_message})"
