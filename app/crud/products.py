from typing import List

from sqlalchemy import func, text, case
from sqlalchemy.orm import Session, selectinload

from app.crud.utils import convert_rows_to_dicts
from app.models import (
    RetailerProduct,
    BrandProduct,
    ProductMatching,
    RetailerProductHistory,
    AvailabilityStatus,
    Retailer
)
from app.schemas.filters import PagedGlobalFilter, GlobalFilter


def get_products(
    db: Session, brand_id: str, global_filter: PagedGlobalFilter
) -> List[RetailerProduct]:
    """
    Returns the list of products from each retailer corresponding to the client currently using the application.

    A special request here was to also return unmatched items from the client (brand), so they can easily keep an eye
    on the products they need to push on. These lists of unmatched items should be added on a 'per retailer' basis
    meaning that if the item A is missing from retailers X and Y, then we need to add to rows corresponding to A at X,
    and A at Y respectively.

    To fulfill this requirement, we use plain SQL queries concatenated by 'UNION ALL' statements, then we apply the
    set LIMIT and OFFSET corresponding to paging on the result.

    Note: the mock-up missing products are returned without the matching brand product. The connection between a
    retailer product and a brand product is done through the `product_matching` association table, which does not have
    any rows for the mock-up products. If you require the "match" as well, see :func:~`app.routers.data` for an example
    of how to do that. We chose to keep that logic out of this file to avoid creating a dependency between 2 crud
    solvers, which could evolve in a circular dependency in the future.

    :param db:
    :param brand_id:
    :param global_filter:
    :return:
    """

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
        WHERE bp.category_id IN :categories
            AND rp.retailer_id IN :retailers
            AND r.country IN :countries
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
                :retailer_{index} AS retailer_id,
                'out_of_stock' as availability
            FROM (
                SELECT * 
                FROM brand_product 
                WHERE brand_id = :brand_id AND category_id IN :categories
            ) bp 
            LEFT OUTER JOIN product_matching pm ON pm.brand_product_id = bp.id
            LEFT OUTER JOIN (
                SELECT * FROM retailer_product WHERE retailer_id = :retailer_{index}
            ) rp ON pm.retailer_product_id = rp.id
            WHERE rp.id is NULL
        """ for index, _ in enumerate(global_filter.retailers)]

    # perform "UNION ALL" operation on all the statements (existing products and non-existing per retailer"
    statement = "UNION ALL".join([marched_statement, *per_retailer_statements])

    # enforce pagination
    statement += f"""OFFSET {global_filter.get_products_offset()} LIMIT {global_filter.page_size}"""

    return (
        db.query(RetailerProduct).from_statement(text(statement))
        # These options are required to load the nested referred classes together with the base queried class.
        # Without these individual queries for each object are issued by SQLAlchemy when returning the result.
        #
        # See: https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#select-in-loading
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
        .params(
            start_date=global_filter.start_date,
            brand_id=brand_id,
            categories=tuple(global_filter.categories),
            retailers=tuple(global_filter.retailers),
            countries=tuple(global_filter.countries),
            # This is necessary to use SQLAlchemy parameter substitution mechanism. This is necessary to ensure
            # protection against SQL injection.
            #
            # See: https://security.openstack.org/guidelines/dg_parameterize-database-queries.html
            **{
                f'retailer_{index}': retailer_id for index, retailer_id in enumerate(global_filter.retailers)
            }
        )
        .all()
    )


def get_historical_stock_status(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    result = (
        db.query(
            RetailerProductHistory.time,
            func.sum(
                case(
                    [(RetailerProductHistory.availability.in_(AvailabilityStatus.available_status_list()), 1)]
                )
            ).label("available_count"),
            func.sum(
                case(
                    [(~RetailerProductHistory.availability.in_(AvailabilityStatus.available_status_list()), 1)]
                )
            ).label("unavailable_count")
        )
        .join(RetailerProductHistory.product)
        .join(RetailerProduct.matched_brand_products)
        .join(ProductMatching.brand_product)
        .join(RetailerProduct.retailer)
        .filter(RetailerProduct.retailer_id.in_(global_filter.retailers))
        .filter(BrandProduct.category_id.in_(global_filter.categories))
        .filter(Retailer.country.in_(global_filter.countries))
        .filter(RetailerProductHistory.time >= global_filter.start_date)
        .filter(BrandProduct.brand_id == brand_id)
        .group_by(RetailerProductHistory.time)
        .all()
    )

    return convert_rows_to_dicts(result)


def get_historical_visibility(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    result = (
        db.execute(
            text("""
                select time,
                    coalesce (SUM(case when product_id is null then 1 end), 0) as not_visible_count,
                    coalesce (SUM(case when product_id is not null then 1 end), 0) as visible_count
                from (
                    select brand_product_in_time.id, brand_product_in_time.time as time, rpts.product_id as product_id, 
                        row_number() OVER (
                            PARTITION BY brand_product_in_time.id, brand_product_in_time.time 
                            ORDER BY rpts.product_id DESC
                        ) as "rank"
                    from (
                        select distinct bp.id, rpts.time
                        from brand_product bp
                        CROSS join (
                            select distinct time from retailer_product_time_series 
                        ) rpts
                        WHERE bp.brand_id = :brand_id
                            AND bp.category_id IN :categories
                    ) brand_product_in_time
                    left join (
                        select pm.*
                        from product_matching pm
                        inner join (
                            select * from retailer_product 
                            WHERE retailer_id in :retailers
                        ) rp ON rp.id = pm.retailer_product_id
                    ) pm on brand_product_in_time.id = pm.brand_product_id 
                    left join retailer_product_time_series rpts ON rpts.product_id = pm.retailer_product_id 
                ) matched_brand_product_in_time
                where rank = 1
                group by time"""),
            params={
                "brand_id": brand_id,
                "start_date": global_filter.start_date,
                "countries": tuple(global_filter.countries),
                "retailers": tuple(global_filter.retailers),
                "categories": tuple(global_filter.categories)
            })
        .all()
    )

    return convert_rows_to_dicts(result)
