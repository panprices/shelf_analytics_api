from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.crud import convert_rows_to_dicts
from app.models import RetailerProduct, ProductMatching, ManualUrlMatching
from app.models.retailer import RetailerImage
from app.schemas.filters import GlobalFilter


def _compose_product_matching_tasks_query(global_filters: GlobalFilter):
    return f"""
        SELECT brand_product_id, retailer_id, skip_count
        FROM matching_tasks mt
            JOIN brand_product bp ON bp.id = mt.brand_product_id
            JOIN retailer r ON mt.retailer_id = r.id
        WHERE status = 'pending'
            {"AND retailer_id IN :retailers" if global_filters.retailers else ""}
            {"AND r.country IN :countries" if global_filters.countries else ""}
            {"AND bp.category_id IN :categories" if global_filters.categories else ""}
            {'''
                AND brand_product_id IN (
                    SELECT product_id 
                    FROM product_group_assignation pga 
                    WHERE pga.product_group_id IN :groups
                )
            ''' if global_filters.groups else ""}
    """


def get_next_brand_product_to_match(
    db: Session, brand_id: str, global_filters: GlobalFilter, index: int
):
    statement = f"""
        {_compose_product_matching_tasks_query(global_filters)}
        ORDER BY skip_count ASC
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
            "groups": tuple(global_filters.groups),
        },
    ).all()

    return convert_rows_to_dicts(result)[0] if len(result) > 0 else None


def count_product_matching_tasks(
    db: Session, brand_id: str, global_filters: GlobalFilter
):
    statement = f"""
        SELECT COUNT(*) 
        FROM ({_compose_product_matching_tasks_query(global_filters)}) AS subquery
    """

    return db.execute(
        text(statement),
        params={
            "brand_id": brand_id,
            "retailers": tuple(global_filters.retailers),
            "countries": tuple(global_filters.countries),
            "categories": tuple(global_filters.categories),
            "groups": tuple(global_filters.groups),
        },
    ).scalar()


def get_brand_product_to_match_deterministically(
    db: Session, brand_product_id: str, retailer_id: str
):
    statement = f"""
        SELECT bp.id, rp.retailer_id 
        FROM brand_product bp
            JOIN product_matching pm ON bp.id = pm.brand_product_id
            JOIN retailer_product rp ON rp.id = pm.retailer_product_id
        WHERE bp.id = :brand_product_id AND rp.retailer_id = :retailer_id
        GROUP BY bp.id, rp.retailer_id
    """

    result = db.execute(
        text(statement),
        params={
            "brand_product_id": brand_product_id,
            "retailer_id": retailer_id,
        },
    ).all()

    return convert_rows_to_dicts(result)[0]


def get_matched_retailer_products_by_brand_product_id(
    db: Session, brand_product_id: str, retailer_id: str
):
    statement = f"""
        SELECT rp.*
        FROM (
            SELECT * FROM retailer_product
            WHERE retailer_id = :retailer_id
        ) rp JOIN (
            SELECT * FROM product_matching
            WHERE brand_product_id = :brand_product_id
                AND certainty >= 'auto_low_confidence_skipped'
                AND certainty < 'auto_high_confidence'
        ) pm ON rp.id = pm.retailer_product_id
            JOIN retailer_to_brand_mapping rbm ON rbm.retailer_id = rp.retailer_id;
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
            selectinload(RetailerProduct.matched_brand_products),
            selectinload(RetailerProduct.matched_brand_products).selectinload(
                ProductMatching.image_matches
            ),
            selectinload(RetailerProduct.images).selectinload(
                RetailerImage.matched_brand_images
            ),
        )
        .all()
    )


def submit_product_matching_selection(
    db: Session, brand_product_id: str, retailer_product_id: str, retailer_id: str
):
    db.query(ProductMatching).filter(
        ProductMatching.brand_product_id == brand_product_id,
        ProductMatching.retailer_product_id == retailer_product_id,
    ).update({"certainty": "manual_input"})

    db.query(ProductMatching).filter(
        ProductMatching.brand_product_id == brand_product_id,
        ProductMatching.retailer_product_id == RetailerProduct.id,
        RetailerProduct.retailer_id == retailer_id,
        ProductMatching.retailer_product_id != retailer_product_id,
    ).update({"certainty": "not_match"}, synchronize_session="fetch")

    db.commit()


def invalidate_product_matching_selection(
    db: Session, brand_product_id: str, retailer_id: str, certainty: str = "not_match"
):
    # Invalidate all other potential matches
    db.query(ProductMatching).filter(
        ProductMatching.brand_product_id == brand_product_id,
        ProductMatching.retailer_product_id == RetailerProduct.id,
        RetailerProduct.retailer_id == retailer_id,
    ).update({"certainty": certainty}, synchronize_session="fetch")

    db.commit()


def submit_product_matching_url(
    db: Session, user_id: str, brand_product_id: str, retailer_id: str, url: str
):
    # Insert a new ManualUrlMatching object
    manual_url_matching = ManualUrlMatching(
        user_id=user_id,
        brand_product_id=brand_product_id,
        url=url,
        status="pending",
        retailer_id=retailer_id,
    )
    db.add(manual_url_matching)
    db.commit()

    invalidate_product_matching_selection(db, brand_product_id, retailer_id)
