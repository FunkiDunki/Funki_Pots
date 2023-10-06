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
    #find our current stock of potions and ingredients for potions
    with db.engine.begin() as connection:
        red_pots = connection.execute(sqlalchemy.text("SELECT name, stock FROM inventory WHERE name = 'red potions'")).first()
        mls = connection.execute(
            sqlalchemy.text("SELECT stock, ingredient, ingredient_order FROM inventory WHERE ingredient = TRUE SORT BY ingredient_order ASC")
        ).all()
    red = mls[0]

    print(potions_delivered)

    #for each potion delivered, subtract the ingredients used and add the resulting potion
    for potInv in potions_delivered:
        red -= potInv.potion_type[0] * potInv.quantity
        if potInv.potion_type[0] == 100:
            red_pots += potInv.quantity

    #now, update our stock of potions and ingredients according to those changes
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("UPDATE inventory SET stock = :s WHERE name = 'red mls'"),
            {'s': red}
        )
        connection.execute(
            sqlalchemy.text("UPDATE inventory SET stock = :s WHERE name = 'red potions'"),
            {'s': red_pots}
        )
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    #find our current stock of red mls
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT name, stock from inventory WHERE name = 'red mls'"))
        red = result.first()
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    #say that we want to bottle it all
    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": red.stock//100,
            }
        ]
