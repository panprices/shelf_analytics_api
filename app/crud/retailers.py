from typing import List, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload, subqueryload

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
        retailer.Retailer.status,
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
        AND category_id in (
            select rp.popularity_category_id 
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
        SELECT *, COALESCE(brand_id = :brand_id, False) AS is_current_customer
        FROM categories_split
        WHERE category_id IN (
            SELECT DISTINCT category_id 
            FROM categories_split 
            WHERE brand_id = :brand_id
          ) AND retailer_id = :retailer_id
        {brand_category_filter}
        ORDER BY is_current_customer DESC NULLS LAST
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

    result = convert_rows_to_dicts(rows)
    # HARD CODE to remove Louis Polsen categories from the result.
    # Only for the PoC. Delete this by 2024-03-01.
    result = [
        category
        for category in result
        if "Louis Poulsen >" not in category["category_name"]
    ]

    return result


def get_retailer_products_for_brand_product(
    db: Session, global_filter: GlobalFilter, brand_product_id: str, brand_id: str
) -> List[ProductMatching]:
    """
    Get retailer products for a brand product

    Returns only products matched on deep indexed retailers
    :param db:
    :param global_filter:
    :param brand_product_id:
    :param brand_id:
    :return:
    """

    filter_on_product_group_statement = """
        AND matched_brand_product_id IN (
            SELECT product_id 
            FROM product_group_assignation pga 
            WHERE pga.product_group_id IN :groups
        )
    """

    statement = f"""
        select DISTINCT pm.*
        from product_matching pm 
            JOIN (
                SELECT id, matched_brand_product_id
                FROM retailer_product_including_unavailable_matview
                WHERE matched_brand_product_id = :brand_product_id
                    AND available_at_retailer = true
                    AND brand_id = :brand_id
                    AND retailer_images_count > 0
                    {"AND brand_category_id IN :categories" if global_filter.categories else ""}
                    {"AND retailer_id IN :retailers" if global_filter.retailers else ""}
                    {"AND country IN :countries" if global_filter.countries else ""}
                    {filter_on_product_group_statement if global_filter.groups else ""}
            ) rp on pm.retailer_product_id = rp.id 
                AND rp.matched_brand_product_id = pm.brand_product_id
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
            brand_id=brand_id,
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
            join retailer_product rp on rp.popularity_category_id = rc.id
        where rc.id in :categories
        group by rc.id, page_size, full_name
    """
        ),
        params={"categories": tuple(categories)},
    ).fetchall()

    result = convert_rows_to_dicts(rows)
    # HARD CODE to remove Louis Polsen categories from the result.
    # Only for the PoC. Delete this by 2024-03-01.
    result = [
        category
        for category in result
        if "Louis Poulsen >" not in category["category_name"]
    ]

    return result


def get_top_n_performance(db: Session, brand_id: str, global_filter: GlobalFilter):
    statement = f"""
        WITH rp_brand_fixed AS (
            SELECT rp.id,
                rp.retailer_id,
                    CASE
                        WHEN b.id IS NULL THEN ( SELECT brand.id
                        FROM brand
                        WHERE brand.name::text = rp.brand::text)
                        ELSE b.id
                    END AS brand_id,
                rp.popularity_category_id, -- AS category_id,
                rp.popularity_index,
                b.id IS NOT NULL OR (rp.brand::text IN ( SELECT brand.name
                    FROM brand)) AS is_customer,
                    CASE
                        WHEN b.id IS NOT NULL THEN b.name
                        WHEN rp.brand IS NULL THEN 'No brand'::character varying
                        ELSE rp.brand
                    END AS brand
            FROM retailer_product rp
                LEFT JOIN product_matching pm ON rp.id = pm.retailer_product_id
                LEFT JOIN brand_product bp ON pm.brand_product_id = bp.id
                LEFT JOIN brand b ON bp.brand_id = b.id
                JOIN retailer_category rc_1 ON rc_1.id = rp.popularity_category_id
        )

        SELECT 
            rc.id,
            COALESCE(
                (
                    SELECT string_agg(value::json ->> 'name', ' > ') FROM json_array_elements_text(category_tree)
                ),
                'No category'
            ) as category_name,
            COUNT(*) FILTER (WHERE popularity_index IS NOT NULL) AS product_count,
            max_popularity_index.value as full_category_count,
            COUNT(*) FILTER (WHERE popularity_index <= 10) AS product_count_top_10,
            COUNT(*) FILTER (WHERE popularity_index <= 20) AS product_count_top_20,
            COUNT(*) FILTER (WHERE popularity_index <= 40) AS product_count_top_40,
            COUNT(*) FILTER (WHERE popularity_index <= 100) AS product_count_top_100
        FROM rp_brand_fixed rp
            JOIN retailer_category rc ON rp.popularity_category_id = rc.id
            JOIN LATERAL (
                SELECT count(*) as value
                FROM retailer_product rp2
                WHERE popularity_category_id = rc.id
                    AND popularity_index IS NOT NULL
            ) AS max_popularity_index ON TRUE
            {'JOIN product_group_assignation pga ON pga.product_id = bp.id' if global_filter.groups else ''}
        WHERE bp.brand_id = :brand_id
            AND rc.retailer_id = :retailer_id
            AND max_popularity_index.value IS NOT NULL
            {'AND bp.category_id IN :categories' if global_filter.categories else ''}
            {'AND pga.product_group_id IN :groups' if global_filter.groups else ''}
        GROUP BY rc.id, max_popularity_index.value
        ORDER BY product_count DESC
    """

    result = convert_rows_to_dicts(
        db.execute(
            statement,
            {
                "brand_id": brand_id,
                "categories": tuple(global_filter.categories),
                "retailer_id": global_filter.retailers[0],
                "groups": tuple(global_filter.groups),
            },
        ).fetchall()
    )

    # HARD CODE to remove Louis Polsen categories from the result.
    # Only for the PoC. Delete this by 2024-03-01.
    if global_filter.retailers[0] == "9a4e566a-fb8f-4250-9986-6d0dc945d714":
        result = [
            category
            for category in result
            if "Louis Poulsen >" not in category["category_name"]
        ]

    return result
