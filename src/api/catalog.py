from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    with db.engine.begin() as connection:
        query = sqlalchemy.text("SELECT i.sku AS sku, name, stock, p.price as price, recipe FROM \
                                inventory i JOIN potions p ON i.sku = p.sku")
        result = connection.execute(query).all()

    cata = []

    for row in result:
        if row.stock >= 1:
            cata.append({
                "sku": row.sku,
                "name": row.name,
                "quantity": row.stock,
                "price": row.price,
                "potion_type": row.recipe
            })
    return cata
