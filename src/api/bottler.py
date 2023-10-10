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

    ingredients = [0, 0, 0, 0]
    pots = []

    print(potions_delivered)

    #for each potion delivered, subtract the ingredients used and add the resulting potion
    for potInv in potions_delivered:
        ingredients = [ingredients[i] - (amount * potInv.quantity) for i, amount in enumerate(potInv.potion_type)]
        pots.append({
            "potion-type": potInv.potion_type,
            "quantity": potInv.quantity
        })

    #now, update our stock of potions and ingredients according to those changes
    with db.engine.begin() as connection:
        for i, ml in enumerate(ingredients):
            connection.execute(
                sqlalchemy.text("UPDATE inventory SET stock = stock + :am \
                                WHERE sku IN (SELECT sku FROM ingredients WHERE ingredient_order = :idx )"),
                {
                    'am': ml,
                    'idx': i
                }
            )
        for i, pot in enumerate(pots):
            pt = pot["potion-type"]
            connection.execute(
                sqlalchemy.text("UPDATE inventory SET stock = stock + :am \
                                WHERE sku IN (SELECT sku FROM potions WHERE recipe = :rec)"),
                {
                    'am': pot["quantity"],
                    'rec': pt
                }
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
            "quantity": blue.stock // 100
        })

    return plan
