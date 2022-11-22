from typing import List, Dict

from sqlalchemy import text, func
from sqlalchemy.orm import Session, selectinload

from app.crud.utils import convert_rows_to_dicts
from app.models import retailer, brand, RetailerProduct, Retailer, ProductMatching
from app.schemas.filters import GlobalFilter


def get_retailers(db: Session, brand_id: str) -> List[retailer.Retailer]:
    return (
        db.query(retailer.Retailer)
        .filter(retailer.Retailer.brands.any(brand.Brand.id == brand_id))
        .all()
    )


def get_countries(db: Session, brand_id: str) -> List[str]:
    return (
        db.query(retailer.Retailer.country)
        .filter(retailer.Retailer.brands.any(brand.Brand.id == brand_id))
        .distinct()
        .all()
    )


def get_categories_split(
    db: Session, brand_id: str, global_filter: GlobalFilter
) -> List[Dict]:
    brand_category_filter = (
        """
        where rc.id in (
            select rp.category_id 
            from retailer_product rp 
                join product_matching pm on rp.id = pm.retailer_product_id 
                join brand_product bp on bp.id = pm.brand_product_id 
                where bp.category_id in :brand_categories
        )
    """
        if global_filter.categories
        else ""
    )

    statement = f"""
        select 
            (
                select string_agg(value::json ->> 'name', ' > ') from json_array_elements_text(category_tree)
            ) as category_name, categories_split.*
        from (
            select category_id, brand, COUNT(*) as product_count, is_customer from (
                select rp.id, rp.category_id as category_id, 
                    (b.id = :brand_id OR rp.brand = (SELECT name from brand WHERe id = :brand_id)) as is_customer, 
                    CASE 
                        WHEN b.id = :brand_id then b.name
                        WHEN rp.brand is NULL then 'No brand'
                        ELSE rp.brand
                    end as brand
                from retailer_product rp
                    left join product_matching pm on rp.id = pm.retailer_product_id 
                    left join brand_product bp on pm.brand_product_id = bp.id
                    left join brand b on bp.brand_id = b.id
                where rp.retailer_id = :retailer_id
            ) rp_brand_fixed
            where category_id in (
                select category_id 
                from retailer_product rp 
                    join product_matching pm on rp.id = pm.retailer_product_id 
                where rp.retailer_id = :retailer_id
            )
            group by brand, category_id, is_customer
        ) categories_split
        join retailer_category rc on categories_split.category_id = rc.id
        {brand_category_filter}
        ORDER BY is_customer ASC
    """
    rows = db.execute(
        text(statement),
        params={
            "brand_id": brand_id,
            "retailer_id": global_filter.retailers[0],
            "brand_categories": tuple(global_filter.categories),
        },
    ).fetchall()

    return convert_rows_to_dicts(rows)


def get_retailer_products_for_brand_product(
    db: Session, global_filter: GlobalFilter, brand_product_id: str
) -> List[RetailerProduct]:
    statement = f"""
        select * from (
            select rp.*, 
                row_number() over (
                    partition by retailer_id
                ) as "rank"
            from product_matching pm 
                join brand_product bp on bp.id = pm.brand_product_id
                join retailer_product rp on pm.retailer_product_id = rp.id
                join retailer r on r.id = rp.retailer_id
            where bp.id = 'ed5145cb-790d-4bc7-97b7-9b08de20106c'
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {"AND rp.retailer_id IN :retailers" if global_filter.retailers else ""}
                {"AND r.country IN :countries" if global_filter.countries else ""}
        ) ranked_matches
        where ranked_matches.rank = 1
    """

    return (
        db.query(RetailerProduct)
        .from_statement(text(statement))
        .params(
            brand_product_id=brand_product_id,
            categories=tuple(global_filter.categories),
            retailers=tuple(global_filter.retailers),
            countries=tuple(global_filter.countries),
        )
        .options(selectinload(RetailerProduct.category))
        .all()
    )


def get_individual_category_performance_details(db: Session, categories: List[str]):
    if not categories:
        return []

    rows = db.execute(
        text(
            """
        select rc.id, r.category_page_size as page_size, MAX(rp.popularity_index) as products_count,
            (
                select string_agg(value::json ->> 'name', ' > ') from json_array_elements_text(category_tree)
            ) as full_name
        from retailer_category rc 
            join retailer r on rc.retailer_id = r.id
            join retailer_product rp on rp.category_id = rc.id
        where rc.id in :categories
        group by rc.id, page_size, full_name
    """
        ),
        params={"categories": tuple(categories)},
    ).fetchall()

    return convert_rows_to_dicts(rows)
