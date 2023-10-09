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
        red_pots = connection.execute(sqlalchemy.text("SELECT name, stock FROM inventory WHERE name = 'red potion'")).first().stock
        green_pots = connection.execute(sqlalchemy.text("SELECT name, stock FROM  inventory WHERE sku = 'GREEN_POTION_0'")).first().stock
        mls = connection.execute(
            sqlalchemy.text("SELECT stock, ingredient, ingredient_order FROM inventory WHERE ingredient = TRUE ORDER BY ingredient_order ASC")
        ).all()
    red = mls[0].stock
    green = mls[1].stock

    blue = 0
    blue_pots = 0

    print(potions_delivered)

    #for each potion delivered, subtract the ingredients used and add the resulting potion
    for potInv in potions_delivered:
        red -= potInv.potion_type[0] * potInv.quantity
        green -= potInv.potion_type[1] * potInv.quantity
        blue -= potInv.potion_type[2] * potInv.quantity
        if potInv.potion_type[0] == 100:
            red_pots += potInv.quantity
        elif potInv.potion_type[1] == 100:
            green_pots += potInv.quantity
        elif potInv.potion_type[2] == 100:
            blue_pots += potInv.quantity

    #now, update our stock of potions and ingredients according to those changes
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("UPDATE inventory SET stock = :s WHERE name = 'green ml'"),
            {'s': green}
        )
        connection.execute(
            sqlalchemy.text("UPDATE inventory SET stock = :s WHERE name = 'green potion'"),
            {'s': green_pots}
        )
        connection.execute(
            sqlalchemy.text("UPDATE inventory SET stock = :s WHERE name = 'red ml'"),
            {'s': red}
        )
        connection.execute(
            sqlalchemy.text("UPDATE inventory SET stock = :s WHERE name = 'red potion'"),
            {'s': red_pots}
        )
        connection.execute(
            sqlalchemy.text("UPDATE inventory SET stock = stock + :s WHERE sku = 'BLUE_POTION_0'"),
            {'s': blue_pots}
        )
        connection.execute(
            sqlalchemy.text("UPDATE inventory SET stock = stock + :s WHERE sku = 'BLUE_ML'"),
            {'s': blue}
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
        result = connection.execute(sqlalchemy.text("SELECT sku, stock from inventory WHERE sku = 'RED_ML'"))
        red = result.first()
        result = connection.execute(sqlalchemy.text("SELECT sku, stock from inventory WHERE sku = 'GREEN_ML'"))
        green = result.first()
        blue = connection.execute(
            sqlalchemy.text("SELECT sku, stock FROM inventory WHERE sku = 'BLUE_ML'")
        ).first()
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    #say that we want to bottle it all

    plan = []

    if red.stock >= 100:
        plan.append({
            "potion_type": [100, 0, 0, 0],
            "quantity": red.stock //100
        })
    if green.stock >= 100:
        plan.append({
            "potion_type": [0, 100, 0, 0],
            "quantity": green.stock //100
        })
    if blue.stock >= 100:
        plan.append({
            "potion_type": [0, 0, 100, 0],
            "quantity": blue.sock // 100
        })

    return plan
