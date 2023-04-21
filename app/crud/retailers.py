from typing import List, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.crud.utils import convert_rows_to_dicts
from app.models import (
    retailer,
    brand,
    RetailerProduct,
    ProductMatching,
    BrandProduct,
    BrandImage,
)
from app.models.mappings import RetailerBrandAssociation
from app.models.retailer import RetailerImage, CountryToLanguage
from app.schemas.filters import GlobalFilter
from app.schemas.general import FilterRetailer


def get_retailers(
    db: Session, brand_id: str, countries: Optional[List[str]]
) -> List[FilterRetailer]:
    query = db.query(
        retailer.Retailer.id,
        retailer.Retailer.name,
        retailer.Retailer.country,
        CountryToLanguage.language,
        RetailerBrandAssociation.shallow,
    )
    if countries:
        query = query.filter(retailer.Retailer.country.in_(countries))

    result = (
        query.join(RetailerBrandAssociation)
        .join(CountryToLanguage)
        .filter(RetailerBrandAssociation.brand_id == brand_id)
        .all()
    )
    return [FilterRetailer.from_orm(r) for r in result]


def get_retailer_name_and_country(db: Session, retailer_id: str) -> str:
    result = (
        db.query(retailer.Retailer.name, retailer.Retailer.country)
        .filter(retailer.Retailer.id == retailer_id)
        .first()
    )
    return result["name"] + " " + result["country"]


def get_countries(db: Session, brand_id: str) -> List[str]:
    return (
        db.query(retailer.Retailer.country)
        .join(RetailerBrandAssociation)
        .filter(RetailerBrandAssociation.brand_id == brand_id)
        .distinct()
        .all()
    )


def get_categories_split(
    db: Session, brand_id: str, global_filter: GlobalFilter
) -> List[Dict]:
    brand_category_filter = (
        f"""
        where rc.id in (
            select rp.category_id 
            from retailer_product rp 
                join product_matching pm on rp.id = pm.retailer_product_id 
                join brand_product bp on bp.id = pm.brand_product_id
                LEFT JOIN product_group_assignation pga on pga.product_id = bp.id 
            where {"bp.category_id in :brand_categories" if global_filter.categories else "1=1"}
                {"AND pga.product_group_id in :groups" if global_filter.groups else ""}
        )
        """
        if global_filter.categories or global_filter.groups
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
                    (b.id = :brand_id OR rp.brand = (SELECT name from brand WHERE id = :brand_id)) as is_customer, 
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
                select distinct category_id 
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
            "groups": tuple(global_filter.groups),
        },
    ).fetchall()

    return convert_rows_to_dicts(rows)


def get_retailer_products_for_brand_product(
    db: Session, global_filter: GlobalFilter, brand_product_id: str
) -> List[ProductMatching]:
    """
    Get retailer products for a brand product

    Returns only products matched on deep indexed retailers
    :param db:
    :param global_filter:
    :param brand_product_id:
    :return:
    """
    statement = f"""
        select * from (
            select pm.*, 
                rank() over (
                    partition by r.id ORDER BY date_trunc('week', rp.fetched_at) DESC
                ) as "rank"
            from product_matching pm 
                join brand_product bp on bp.id = pm.brand_product_id
                join retailer_product rp on pm.retailer_product_id = rp.id
                join retailer r on r.id = rp.retailer_id
                JOIN retailer_to_brand_mapping rtbm on rtbm.retailer_id = r.id
                LEFT JOIN product_group_assignation pga on pga.product_id = bp.id
            where bp.id = :brand_product_id
                AND pm.certainty NOT IN ('auto_low_confidence', 'not_match')
                AND NOT rtbm.shallow
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {"AND rp.retailer_id IN :retailers" if global_filter.retailers else ""}
                {"AND r.country IN :countries" if global_filter.countries else ""}
                {"AND pga.product_group_id IN :groups" if global_filter.groups else ""}
        ) ranked_matches
        where ranked_matches.rank = 1
    """

    return (
        db.query(ProductMatching)
        .from_statement(text(statement))
        .params(
            brand_product_id=brand_product_id,
            categories=tuple(global_filter.categories),
            retailers=tuple(global_filter.retailers),
            countries=tuple(global_filter.countries),
            groups=tuple(global_filter.groups),
        )
        .options(
            selectinload(ProductMatching.retailer_product).selectinload(
                RetailerProduct.category
            ),
            selectinload(ProductMatching.retailer_product).selectinload(
                RetailerProduct.images
            ),
            selectinload(ProductMatching.retailer_product).selectinload(
                RetailerProduct.retailer
            ),
            selectinload(ProductMatching.retailer_product)
            .selectinload(RetailerProduct.images)
            .selectinload(RetailerImage.type_predictions),
            selectinload(ProductMatching.retailer_product)
            .selectinload(RetailerProduct.matched_brand_products)
            .selectinload(ProductMatching.brand_product)
            .selectinload(BrandProduct.images),
        )
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
