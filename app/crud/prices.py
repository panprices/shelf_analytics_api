from typing import List

from sqlalchemy import text, func, literal_column
from sqlalchemy.orm import Session, selectinload

from app.models import (
    RetailerProductHistory,
    RetailerProduct,
    BrandProduct,
    Retailer,
    MSRP,
    ProductMatching,
    MockBrandProductWithMarketPrices,
)
from app.schemas.filters import GlobalFilter


def get_historical_prices_by_retailer_for_brand_product(
    db: Session, global_filter: GlobalFilter, brand_product_id: str
) -> List[RetailerProductHistory]:
    statement = f"""
        with available_prices as (
            select * 
            from (	
                select rpts.product_id, 
                    rp.retailer_id,
                    rpts.price * c.to_sek as price, 
                    'SEK' as currency, 
                    rpts.availability, 
                    date_trunc('week', time)::timestamp as time, 
                    row_number() over (
                        partition by rp.retailer_id, date_trunc('week', time)
                    ) as "rank"
                from retailer_product_time_series rpts 
                    join retailer_product rp on rp.id = rpts.product_id 
                    join retailer r on r.id = rp.retailer_id
                    join product_matching pm on rp.id = pm.retailer_product_id 
                    join brand_product bp on bp.id = pm.brand_product_id 
                    join currency c on c.name = rpts.currency
                    LEFT JOIN product_group_assignation pga ON pga.product_id = bp.id
                where bp.id = :brand_product_id and rpts.price <> 0
                    AND pm.certainty NOT IN ('auto_low_confidence', 'not_match')
                    {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                    {"AND rp.retailer_id IN :retailers" if global_filter.retailers else ""}
                    {"AND r.country IN :countries" if global_filter.countries else ""}
                    {"AND pga.product_group_id IN :groups" if global_filter.groups else ""}
                order by time asc
            ) per_retailer_time_series
            where rank = 1
        )
        select dates.product_id, 
            ap.price, 
            ap.currency, 
            ap.availability, 
            dates.time
        from (
            select retailer_id, product_id,
                generate_series(
                    (select min(time) from available_prices), 
                    (select max(time) from available_prices), 
                    '1w'
                )::timestamp as time
            from available_prices
            group by retailer_id, product_id
        ) dates left join available_prices ap using (retailer_id, time)
        order by dates.time asc
    """

    return (
        db.query(RetailerProductHistory)
        .from_statement(text(statement))
        .params(
            brand_product_id=brand_product_id,
            categories=tuple(global_filter.categories),
            retailers=tuple(global_filter.retailers),
            countries=tuple(global_filter.countries),
            groups=tuple(global_filter.groups),
        )
        .options(
            selectinload(RetailerProductHistory.product).selectinload(
                RetailerProduct.retailer
            )
        )
        .all()
    )


def get_price_table_data(db: Session, global_filter: GlobalFilter, brand_id: str):
    query = f"""
        SELECT * FROM brand_product_msrp_view
        WHERE brand_id = :brand_id
            {"AND category_id IN :categories" if global_filter.categories else ""}
            {"AND msrp_country IN :countries" if global_filter.countries else ""}
            {"AND id IN (SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)" 
                if global_filter.groups else ""}
        OFFSET :offset
        LIMIT :limit;
    """

    results = (
        db.query(MockBrandProductWithMarketPrices)
        .from_statement(statement=text(query))
        .params(brand_id=brand_id, offset=0, limit=10)
        .all()
    )

    return results
