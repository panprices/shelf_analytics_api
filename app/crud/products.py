from typing import Dict, List

from sqlalchemy import func, text, case
from sqlalchemy.orm import Session, selectinload

from app.crud.utils import convert_rows_to_dicts
from app.models import (
    RetailerProduct,
    BrandProduct,
    ProductMatching,
    RetailerProductHistory,
    AvailabilityStatus,
    Retailer,
)
from app.schemas.filters import PagedGlobalFilter, GlobalFilter


def _create_query_for_products_datapool(global_filter: PagedGlobalFilter) -> str:
    return f"""
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
        JOIN product_matching pm on pm.retailer_product_id = rp.id
        JOIN brand_product bp ON pm.brand_product_id = bp.id
        WHERE rp.created_at > :start_date AND bp.brand_id = :brand_id
            {"AND bp.category_id IN :categories" if global_filter.categories else ""}
            {"AND rp.retailer_id IN :retailers" if global_filter.retailers else ""}
            {"AND r.country IN :countries" if global_filter.countries else ""}
            {"AND (bp.sku LIKE :search_text OR bp.gtin LIKE :search_text)" if global_filter.search_text else ""}
        UNION ALL
        SELECT
            uuid_generate_v4() as id, 
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
            retailer_id,
            'out_of_stock' as availability
        from (
            select *, 
                row_number() over (
                    partition by id, retailer_id order by is_match desc, retailer_product_id DESC nulls last 
                ) as "rank"
            from (
                select retailer_brand_product.*, rp.id as retailer_product_id, 
                    coalesce (retailer_brand_product.retailer_id = rp.retailer_id, false) as is_match
                from (
                    select aux.*, r.id as retailer_id
                    from brand_product aux cross join retailer r
                    WHERE 1 = 1
                        {"AND r.id IN :retailers" if global_filter.retailers else ""}
                        {"AND r.country IN :countries" if global_filter.countries else ""}
                        {"AND aux.category_id IN :categories" if global_filter.categories else ""}
                        {
                            "AND (aux.sku LIKE :search_text OR aux.gtin LIKE :search_text)" 
                            if global_filter.search_text 
                            else ""
                        }
                ) retailer_brand_product
                left outer join product_matching pm on pm.brand_product_id = retailer_brand_product.id
                left outer join retailer_product rp on pm.retailer_product_id = rp.id
            ) outer_aux
        ) bp 
        where bp.rank = 1 and not is_match
    """


def _get_full_product_list(
    db: Session, brand_id: str, statement: str, global_filter: PagedGlobalFilter
):
    query = db.query(RetailerProduct).from_statement(text(statement))

    """
    These options are required to load the nested referred classes together with the base queried class.
    Without these individual queries for each object are issued by SQLAlchemy when returning the result.

    See: https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#select-in-loading
    """
    query = query.options(
        selectinload(RetailerProduct.retailer),
        selectinload(RetailerProduct.images),
        selectinload(RetailerProduct.matched_brand_products)
        .selectinload(ProductMatching.brand_product)
        .selectinload(BrandProduct.images),
        selectinload(RetailerProduct.matched_brand_products)
        .selectinload(ProductMatching.brand_product)
        .selectinload(BrandProduct.category),
    )
    return query.params(
        start_date=global_filter.start_date,
        brand_id=brand_id,
        categories=tuple(global_filter.categories),
        retailers=tuple(global_filter.retailers),
        countries=tuple(global_filter.countries),
        offset=global_filter.get_products_offset(),
        limit=global_filter.page_size,
        search_text=f"{global_filter.search_text}%",
    ).all()


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
    set LIMIT and OFFSET corresponding to paging on the result. A mock product will have a randomly generated id. We
    tried also using the id of the brand product, but that resulted in duplicated values for the primary key (the same
    brand product mocked for different retailers) which generated weird behaviour from SQLAlchemy.

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

    statement = f"""
        SELECT * FROM (
            {_create_query_for_products_datapool(global_filter)}
        ) products_datapool
        OFFSET :offset
        LIMIT :limit
    """

    return _get_full_product_list(db, brand_id, statement, global_filter)


def count_products(db: Session, brand_id: str, global_filter: PagedGlobalFilter) -> int:
    statement = f"""
        SELECT COUNT(*) FROM (
            {_create_query_for_products_datapool(global_filter)}
        ) products_datapool
    """

    return db.execute(
        text(statement),
        params={
            "start_date": global_filter.start_date,
            "brand_id": brand_id,
            "categories": tuple(global_filter.categories),
            "retailers": tuple(global_filter.retailers),
            "countries": tuple(global_filter.countries),
            "search_text": f"{global_filter.search_text}%",
        },
    ).scalar()


def get_historical_stock_status(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    result = (
        db.query(
            RetailerProductHistory.time,
            func.sum(
                case(
                    [
                        (
                            RetailerProductHistory.availability.in_(
                                AvailabilityStatus.available_status_list()
                            ),
                            1,
                        )
                    ]
                )
            ).label("available_count"),
            func.sum(
                case(
                    [
                        (
                            ~RetailerProductHistory.availability.in_(
                                AvailabilityStatus.available_status_list()
                            ),
                            1,
                        )
                    ]
                )
            ).label("unavailable_count"),
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


def get_historical_visibility(db: Session, brand_id: str, global_filter: GlobalFilter):
    result = db.execute(
        text(
            f"""
                select full_products.date as time, full_count - visible_count as not_visible_count, visible_count
                from (
                    select date_trunc('week', rpts.time)::date as date, COUNT(distinct bp.id) as visible_count
                    from brand_product bp 
                        join product_matching pm on bp.id = pm.brand_product_id 
                        join retailer_product_time_series rpts on pm.retailer_product_id = rpts.product_id
                        join retailer_product rp on rpts.product_id = rp.id 
                        join retailer r on rp.retailer_id = r.id
                    where bp.brand_id = :brand_id
                        {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                        {"AND r.id in :retailers" if global_filter.retailers else ""}
                        {"AND r.country in :countries" if global_filter.countries else ""}
                    group by date_trunc('week', rpts.time)::date
                ) visible_products join (
                    select rpts.time as date, COUNT(distinct bp.id) as full_count
                    from brand_product bp 
                    CROSS join (
                        select distinct date_trunc('week', time)::date as time from retailer_product_time_series 
                    ) rpts
                    where date_trunc('week', bp.created_at) <= rpts.time::date and bp.brand_id = :brand_id
                        {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                    group by rpts.time
                ) full_products on visible_products.date = full_products.date 
                -- Only present data up to last week:
                where full_products.date < date_trunc('week', now())::date
                order by full_products.date asc 
            """
        ),
        params={
            "brand_id": brand_id,
            "start_date": global_filter.start_date,
            "countries": tuple(global_filter.countries),
            "retailers": tuple(global_filter.retailers),
            "categories": tuple(global_filter.categories),
        },
    ).all()

    return convert_rows_to_dicts(result)


def count_brand_products(
    db: Session, brand_id: str, global_filter: GlobalFilter
) -> int:
    products = db.query(BrandProduct).filter(BrandProduct.brand_id == brand_id)
    if global_filter.categories:
        products = products.filter(
            BrandProduct.category_id.in_(global_filter.categories)
        )

    return products.count()


def export_full_brand_products_result(
    db: Session, brand_id: str, global_filter: PagedGlobalFilter
):
    return _get_full_product_list(
        db,
        brand_id,
        statement=_create_query_for_products_datapool(global_filter),
        global_filter=global_filter,
    )


def count_available_products_by_retailers(
    db: Session, brand_id: str, global_filter: GlobalFilter
) -> List[Dict]:
    statement = f"""
        select retailer, available_products_count, 
            total_count - available_products_count as not_available_products_count
        from (
            SELECT
              r.name AS retailer,
              COUNT(DISTINCT bp.id) AS available_products_count,
              (select COUNT(*) from brand_product) as total_count
            from product_matching pm 
                join brand_product bp on bp.id = pm.brand_product_id 
                join retailer_product rp on rp.id = pm.retailer_product_id
                join retailer r on r.id = rp.retailer_id 
            where bp.brand_id = :brand_id
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {"AND rp.retailer_id IN :retailers" if global_filter.retailers else ""}
                {"AND r.country IN :countries" if global_filter.countries else ""}
            GROUP BY
              r.id
        ) product_availability
    """

    rows = db.execute(
        text(statement),
        params={
            "brand_id": brand_id,
            "start_date": global_filter.start_date,
            "countries": tuple(global_filter.countries),
            "retailers": tuple(global_filter.retailers),
            "categories": tuple(global_filter.categories),
        },
    ).fetchall()

    return convert_rows_to_dicts(rows)
