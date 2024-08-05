import random
from tests.routers.external_v2.helpers import get_retailer_offers_no_filters_in_test

# We want to test the iteration of pages in the API
# Therefore we will randomly select a number of pages to test
MAX_PAGES = random.randint(1, 3)

def test_get_retailer_offers_no_filters_v2(page=None):
    response = get_retailer_offers_no_filters_in_test(page)
    if response["page"] >= MAX_PAGES:
        return
    elif response["page"] == response["pages_count"]:
        return
    else:
        test_get_retailer_offers_no_filters_v2(page=response["page"] + 1)

def test_get_retailer_offers_no_filters_v21(page=None):
    user_currency = random.choice(["SEK", "EUR", "DKK", None])
    response = get_retailer_offers_no_filters_in_test(
        page,
        api_version="v2.1",
        user_currency=user_currency
    )
    if response["page"] >= MAX_PAGES:
        return
    elif response["page"] == response["pages_count"]:
        return
    else:
        test_get_retailer_offers_no_filters_v21(
            page=response["page"] + 1)
