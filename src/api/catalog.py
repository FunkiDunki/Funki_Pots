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

        result = connection.execute(
            sqlalchemy.text("SELECT i.sku sku, i.name name, p.stock stock, p.price price, p.recipe recipe FROM \
                            inventory i JOIN \
                                (SELECT potions.price, potions.sku sku, potions.recipe recipe, t.stock \
                                FROM potions JOIN \
                                    (SELECT COALESCE(SUM(change), 0) stock, sku \
                                    FROM transactions GROUP BY sku) t \
                                ON potions.sku = t.sku) p \
                            ON i.sku = p.sku")
        ).all()

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
