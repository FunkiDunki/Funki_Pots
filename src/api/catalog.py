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
        query = sqlalchemy.text("SELECT * FROM inventory WHERE for_sale = TRUE")
        result = connection.execute(query).all()

    cata = []

    for row in result:
        if row.stock >= 1:
            cata.append({
                "sku": row.sku,
                "name": row.name,
                "quantity": row.stock,
                "price": row.price,
                "potion_type": [row.potion_type[0], row.potion_type[1], row.potion_type[2], row.potion_type[3]]
            })
    return cata
