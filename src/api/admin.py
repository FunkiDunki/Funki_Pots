from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from src import database as db
import sqlalchemy

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        query = sqlalchemy.text("UPDATE global_inventory SET num_red_potions = 0, num_red_ml = 0, gold = 100")
        connection.execute(query)

        q2 = sqlalchemy.text("UPDATE inventory SET stock = 0")
        connection.execute(q2)
        q2 = sqlalchemy.text("UPDATE inventory SET stock = 100 WHERE name = 'gold'")
        connection.execute(q2)
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Funki Pots",
        "shop_owner": "Nicholas Hotelling",
    }

