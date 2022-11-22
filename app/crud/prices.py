from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.models import (
    RetailerProductHistory,
    RetailerProduct,
)
from app.schemas.filters import GlobalFilter


def get_historical_prices_by_retailer_for_brand_product(
    db: Session, global_filter: GlobalFilter, brand_product_id: str
) -> List[RetailerProductHistory]:
    statement = f"""
        with available_prices as (
            select product_id, 
                rpts.price, 
                rpts.currency, 
                rpts.availability, 
                date_trunc('week', time)::timestamp as time, 
                rank
            from (
                    select *, 
                        row_number() over (
                            partition by product_id, date_trunc('week', time)
                        ) as "rank"
                    from retailer_product_time_series
                ) rpts 
                join retailer_product rp on rp.id = rpts.product_id 
                join product_matching pm on rp.id = pm.retailer_product_id 
                join brand_product bp on bp.id = pm.brand_product_id 
            where rank = 1 and bp.id = :brand_product_id and rpts.price <> 0
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {"AND rp.retailer_id IN :retailers" if global_filter.retailers else ""}
                {"AND r.country IN :countries" if global_filter.countries else ""}
            order by time asc
        )
        select dates.product_id, 
            ap.price, 
            ap.currency, 
            ap.availability, 
            dates.time
        from (
            select product_id, 
                generate_series(
                    (select min(time) from available_prices), 
                    (select max(time) from available_prices), 
                    '1w'
                )::timestamp as time
            from available_prices
            group by product_id
        ) dates left join available_prices ap using (product_id, time)
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
        )
        .options(
            selectinload(RetailerProductHistory.product).selectinload(
                RetailerProduct.retailer
            )
        )
        .all()
    )
