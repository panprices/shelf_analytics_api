from sqlalchemy.orm import Session

from app.models import BrandProduct
from app.models.groups import ProductGroup
from app.schemas.auth import TokenData
from app.schemas.groups import BrandProductGroupScaffold


def create_brand_product_group(
    db: Session, group: BrandProductGroupScaffold, user: TokenData
):
    products_as_objects = (
        db.query(BrandProduct).filter(BrandProduct.id.in_(group.products)).all()
    )

    # Persist the group to the database
    product_group_model = ProductGroup(
        name=group.name,
        user_id=user.uid,
        brand_id=user.client,
        products=products_as_objects,
    )
    db.add(product_group_model)

    # Commit the changes to the database
    db.commit()
