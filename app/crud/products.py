from datetime import datetime
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.crud.brands import get_brand_categories
from app.crud.retailers import get_retailers, get_countries
from app.models import (
    RetailerProduct,
    BrandProduct,
    ProductMatching,
)
from app.schemas.filters import PagedGlobalFilter


def get_products(
    db: Session, brand_id: str, global_filter: PagedGlobalFilter
) -> List[RetailerProduct]:
    retailers = global_filter.retailers
    if not retailers:
        retailers = [r.id.hex for r in get_retailers(db, brand_id)]
    retailers_filter = f"""('{"', '".join(retailers)}')"""

    categories = global_filter.categories
    if not categories:
        categories = [c.id.hex for c in get_brand_categories(db, brand_id)]
    categories_filter = f"""('{"', '".join(categories)}')"""

    countries = global_filter.countries
    if not countries:
        countries = [c[0] for c in get_countries(db, brand_id)]
    countries_filter = f"""('{"', '".join(countries)}')"""

    marched_statement = f"""
        SELECT rp.id, 
            rp.url, 
            rp.description, 
            rp.specifications, 
            rp.sku, 
            rp.gtin, 
            rp.name, 
            rp.created_at, 
            rp.updated_at,
            rp.popularity_index,
            rp.price,
            rp.currency,
            rp.reviews,
            rp.review_average,
            rp.is_discounted,
            rp.original_price,
            rp.category_id,
            rp.retailer_id,
            rp.availability
        FROM retailer_product rp 
        JOIN retailer_to_brand_mapping rtb ON rtb.retailer_id = rp.retailer_id
        JOIN retailer r ON r.id = rp.retailer_id
        JOIN brand b ON rtb.brand_id = b.id
        JOIN product_matching pm on pm.retailer_product_id = rp.id
        JOIN brand_product bp ON pm.brand_product_id = bp.id
        WHERE bp.category_id IN {categories_filter}
            AND rp.retailer_id IN {retailers_filter}
            AND r.country IN {countries_filter}
            AND rp.created_at > :start_date
    """

    per_retailer_statements = [f"""
            SELECT
                bp.id as id, 
                NULL as url,
                bp.description AS description,
                bp.specifications AS specifications,
                bp.sku AS sku, 
                bp.gtin AS gtin,
                bp.name as name,
                bp.created_at as created_at,
                bp.updated_at as updated_at,
                -1 AS popularity_index, 
                0 AS price,
                '' AS currency,
                '{{}}'::json AS reviews,
                0 AS review_average,
                False AS is_discounted,
                0 AS original_price,
                NULL AS category_id,
                '{r}'::uuid AS retailer_id,
                'out_of_stock' as availability
            FROM (
                SELECT * 
                FROM brand_product 
                WHERE brand_id = '{brand_id}' AND category_id IN {categories_filter}
            ) bp 
            LEFT OUTER JOIN product_matching pm ON pm.brand_product_id = bp.id
            LEFT OUTER JOIN (
                SELECT * FROM retailer_product WHERE retailer_id = '{r}'
            ) rp ON pm.retailer_product_id = rp.id
            WHERE rp.id is NULL
        """ for r in retailers]
    statement = "UNION ALL".join([marched_statement, *per_retailer_statements])
    statement += f"""OFFSET {global_filter.get_products_offset()} LIMIT {global_filter.page_size}"""

    query = db.query(RetailerProduct).from_statement(text(statement))
    """
    This is a bit of a hackish move. By default SQLAlchemy constraints the results to be unique (constraint on the
    primary key column). Here because we assign a dummy id to all the "missing" rows we want to avoid that. 

    Upon expecting the source code I found the following: 
    ```
        if (
            result._attributes.get("filtered", False)
            and not self.load_options._yield_per
        ):
            result = result.unique()
    ```

    So it only applies the unique constraint if this parameter is not set. 
    The purpose of the parameter is to tell SQLAlchemy that we want to load the data in chunks when a lot of data is 
    loaded to avoid overusing RAM memory in the python process. 

    See: https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.yield_per 
    """
    query.load_options += {'_yield_per': global_filter.page_size}

    return (
        query
        .options(
            selectinload(RetailerProduct.retailer),
            selectinload(RetailerProduct.images),
            selectinload(
                RetailerProduct.matched_brand_products
            ).selectinload(
                ProductMatching.brand_product
            ).selectinload(
                BrandProduct.images
            ),
            selectinload(
                RetailerProduct.matched_brand_products
            ).selectinload(
                ProductMatching.brand_product
            ).selectinload(
                BrandProduct.category
            )
        )
        .params(start_date=global_filter.start_date)
        .all()
    )


def get_missing_products(
    db: Session, brand_id: str, global_filter: PagedGlobalFilter
) -> List[RetailerProduct]:
    retailers = global_filter.retailers
    if not retailers:
        retailers = [r.id for r in get_retailers(db, brand_id)]

    categories = global_filter.categories
    if not categories:
        categories = [c.id.hex for c in get_brand_categories(db, brand_id)]
    categories_filter = f"""('{"', '".join(categories)}')"""

    per_retailer_statements = [f"""
            SELECT
                bp.id as id, 
                NULL as url,
                bp.description AS description,
                bp.specifications AS specifications,
                bp.sku AS sku, 
                bp.gtin AS gtin,
                bp.name as name,
                bp.created_at as created_at,
                bp.updated_at as updated_at,
                -1 AS popularity_index, 
                0 AS price,
                '' AS currency,
                '{{}}'::json AS reviews,
                0 AS review_average,
                False AS is_discounted,
                0 AS original_price,
                NULL AS category_id,
                '{r}'::uuid AS retailer_id,
                'out_of_stock' as availability
            FROM (
                SELECT * 
                FROM brand_product 
                WHERE brand_id = '{brand_id}' AND category_id IN {categories_filter}
            ) bp 
            LEFT OUTER JOIN product_matching pm ON pm.brand_product_id = bp.id
            LEFT OUTER JOIN (
                SELECT * FROM retailer_product WHERE retailer_id = '{r}'
            ) rp ON pm.retailer_product_id = rp.id
            WHERE rp.id is NULL
        """ for r in retailers]
    statement = "UNION ALL".join(per_retailer_statements)
    statement += f"""OFFSET {global_filter.get_products_offset()}
        LIMIT {global_filter.page_size}
    """

    query = db.query(RetailerProduct).from_statement(text(statement))
    """
    This is a bit of a hackish move. By default SQLAlchemy constraints the results to be unique (constraint on the
    primary key column). Here because we assign a dummy id to all the "missing" rows we want to avoid that. 
    
    Upon expecting the source code I found the following: 
    ```
        if (
            result._attributes.get("filtered", False)
            and not self.load_options._yield_per
        ):
            result = result.unique()
    ```
    
    So it only applies the unique constraint if this parameter is not set. 
    The purpose of the parameter is to tell SQLAlchemy that we want to load the data in chunks when a lot of data is 
    loaded to avoid overusing RAM memory in the python process. 
    
    See: https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.yield_per 
    """
    query.load_options += {'_yield_per': global_filter.page_size}
    return query.options(
        selectinload(RetailerProduct.retailer),
        selectinload(RetailerProduct.images),
        selectinload(
            RetailerProduct.matched_brand_products
        ).selectinload(
            ProductMatching.brand_product
        ).selectinload(
            BrandProduct.images
        ),
        selectinload(
            RetailerProduct.matched_brand_products
        ).selectinload(
            ProductMatching.brand_product
        ).selectinload(
            BrandProduct.category
        )
    ).params(start_date=global_filter.start_date).all()
