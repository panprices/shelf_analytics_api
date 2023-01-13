from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.crud import convert_rows_to_dicts
from app.models import RetailerProduct, ProductMatching
from app.models.retailer import RetailerImage
from app.schemas.filters import GlobalFilter


def get_next_brand_product_to_match(
    db: Session, brand_id: str, global_filters: GlobalFilter, index: int
):
    statement = f"""
        SELECT bp.id, rp.retailer_id 
        FROM brand_product bp
            JOIN product_matching pm ON bp.id = pm.brand_product_id
            JOIN retailer_product rp ON rp.id = pm.retailer_product_id
        WHERE bp.brand_id = :brand_id
            {"AND rp.retailer_id IN :retailers" if global_filters.retailers else ""}
            {"AND rp.country IN :countries" if global_filters.countries else ""}
            {"AND bp.category_id IN :categories" if global_filters.categories else ""}
        GROUP BY bp.id, rp.retailer_id
        HAVING COUNT(bp.id) > 1 AND SUM(CASE WHEN pm.certainty = 'manual_input' THEN 1 ELSE 0 END) = 0
        ORDER BY bp.name ASC
        OFFSET :index        
        LIMIT 1
    """

    result = db.execute(
        text(statement),
        params={
            "brand_id": brand_id,
            "index": index,
            "retailers": tuple(global_filters.retailers),
            "countries": tuple(global_filters.countries),
            "categories": tuple(global_filters.categories),
        },
    ).all()

    return convert_rows_to_dicts(result)[0]


def get_matched_retailer_products_by_brand_product_id(
    db: Session, brand_product_id: str, retailer_id: str
):
    statement = f"""
        SELECT rp.* 
        FROM retailer_product rp
            JOIN product_matching pm ON rp.id = pm.retailer_product_id
        WHERE pm.brand_product_id = :brand_product_id
            AND rp.retailer_id = :retailer_id
    """

    return (
        db.query(RetailerProduct)
        .from_statement(text(statement))
        .params(brand_product_id=brand_product_id, retailer_id=retailer_id)
        .options(
            selectinload(RetailerProduct.category),
            selectinload(RetailerProduct.images),
            selectinload(RetailerProduct.retailer),
            selectinload(RetailerProduct.images).selectinload(
                RetailerImage.type_predictions
            ),
            selectinload(RetailerProduct.candidate_brand_products),
            selectinload(RetailerProduct.candidate_brand_products).selectinload(
                ProductMatching.image_matches
            ),
            selectinload(RetailerProduct.images).selectinload(
                RetailerImage.matched_brand_images
            ),
        )
        .all()
    )


def submit_product_matching_selection(
    db: Session, brand_product_id: str, retailer_product_id: str
):
    db.query(ProductMatching).filter(
        ProductMatching.brand_product_id == brand_product_id,
        ProductMatching.retailer_product_id == retailer_product_id,
    ).update({"certainty": "manual_input"})

    db.query(ProductMatching).filter(
        ProductMatching.brand_product_id == brand_product_id,
        ProductMatching.retailer_product_id != retailer_product_id,
    ).update({"certainty": "not_match"})

    db.commit()
