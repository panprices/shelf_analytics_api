from sqlalchemy.orm import Session

from app.models import BrandProduct
from app.models.groups import ProductGroup
from app.schemas.auth import TokenData
from app.schemas.groups import (
    BrandProductGroupCreationScaffold,
    BrandProductGroupAppendScaffold,
)


def create_brand_product_group(
    db: Session, group: BrandProductGroupCreationScaffold, user: TokenData
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


def add_products_to_group(db: Session, group: BrandProductGroupAppendScaffold):
    products_as_objects = (
        db.query(BrandProduct).filter(BrandProduct.id.in_(group.products)).all()
    )

    # Persist the group to the database
    product_group_model = (
        db.query(ProductGroup).filter(ProductGroup.id == group.id).first()
    )
    product_group_model.products.extend(products_as_objects)

    db.add(product_group_model)

    # Commit the changes to the database
    db.commit()
