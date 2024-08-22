from typing import List, TypeVar, Type

from pydantic import BaseModel

from app.models.retailer import MockRetailerProductGridItem
from app.schemas.product import MockRetailerProductGridItemV21
from app.crud.utils import get_currency_exchange_rates
from sqlalchemy.orm import Session


TRetailerProductSchemaOrModel = TypeVar("TRetailerProductSchemaOrModel")
TRetailerProductReturnSchema = TypeVar("TRetailerProductReturnSchema", bound=BaseModel)


def add_user_currency_to_retailer_offers(
    products: List[TRetailerProductSchemaOrModel],
    user_currency: str,
    db: Session,
    output_model_class: Type[
        TRetailerProductReturnSchema
    ] = MockRetailerProductGridItemV21,
) -> List[TRetailerProductReturnSchema]:
    # Get the currency conversion rates for the user's currency from PSQL.
    currencies = get_currency_exchange_rates(db, user_currency)
    updated_products = []
    for product in products:
        # Grab the conversion rate for the product's currency
        product_currency = product.currency
        if product_currency not in currencies:
            continue  # Skip if the product's currency is not supported
        conversion_rate = currencies[product_currency]

        # Convert prices and limit to 1 decimal point
        converted_retailer_price = round(product.retailer_price / conversion_rate, 1)

        # Convert the product to a dictionary, then update it with new fields
        product_dict = product.__dict__.copy()
        product_dict.update(
            {
                "retailer_price_in_user_currency": converted_retailer_price,
                "user_currency": user_currency,
            }
        )

        # Create a new instance with updated fields
        updated_product = output_model_class(**product_dict)
        updated_products.append(updated_product)

    # Return the new list of products with added fields
    return updated_products
