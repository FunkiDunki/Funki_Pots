from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions FROM global_inventory"))
    result = result.first()
    red = result[0] + 0
    red_pots = result[1] + 0
    print(potions_delivered)
    for potInv in potions_delivered:
        red -= potInv.potion_type[0] * potInv.quantity
        if potInv.potion_type[0] == 100:
            red_pots += potInv.quantity

    with db.engine.begin() as connection:
        text = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :r , num_red_potions = :pots")
        result = connection.execute(text, {"r":red, "pots":red_pots})
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
    red = result.first()[0]
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": red//100,
            }
        ]
