from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    cost = 0
    ingredients = [0, 0, 0, 0]

    #update that info with the delivered barrels
    for barrel in barrels_delivered:
        for i, ml in enumerate(barrel.potion_type):
            ingredients[i] += ml * barrel.ml_per_barrel * barrel.quantity
        cost += barrel.price * barrel.quantity
    
    #now update our database with the new information
    with db.engine.begin() as connection:
        for i, ml in enumerate(ingredients):
            #for each ingredient, add to our stock based on how much we got from these barrels
            connection.execute(
                sqlalchemy.text("UPDATE inventory SET stock = stock + :m WHERE sku IN (SELECT sku FROM ingredients WHERE ingredient_order = :idx)"),
                {
                    'm': ml,
                    'idx': i
                }
            )

        #subtract the cost from our gold
        query = sqlalchemy.text("UPDATE inventory SET stock = stock - :c WHERE sku = 'GOLD'")
        connection.execute(query, {'c': cost})
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT name, stock FROM inventory WHERE sku = 'BLUE_POTION_0'"))
        blue_pots = result.first().stock
        gold = connection.execute(sqlalchemy.text("SELECT name, stock FROM inventory WHERE sku = 'GOLD'")).first().stock

        red_pots = connection.execute(
            sqlalchemy.text("SELECT stock FROM inventory WHERE sku = 'RED_POTION_0'")
        ).first().stock

        green_pots = connection.execute(sqlalchemy.text(
            "SELECT stock FROM inventory WHERE sku = 'GREEN_POTION_0'"
        )).first().stock

        barrel_spam = connection.execute(
            sqlalchemy.text("SELECT stringish, active FROM launch_codes WHERE code = 'BARREL_SPAM'")
        ).first()
    

    price = 0
    plan = []

    if barrel_spam.active:
        #we just want to spam this one barrel if we can, do nothing if else
        for barrel in wholesale_catalog:
            if barrel.sku == barrel_spam.stringish and gold >= barrel.price:
                #add as many of this barrel as we can until we have not enough gold or there aren't enough barrels for sale
                amount = min(gold // barrel.price, barrel.quantity)
                price = amount * barrel.price
                plan.append({
                    "sku": barrel.sku,
                    "quantity": amount
                })


    else:
        if blue_pots < 10 and gold >= 100:
            plan.append({
                "sku": "SMALL_BLUE_BARREL",
                "quantity": 1
            })
            price += 100
        if red_pots < 10 and gold - price >= 100:
            plan.append({
                "sku": "SMALL_RED_BARREL",
                "quantity": 1
            })
            price += 100
        if green_pots < 10 and gold - price >= 100:
            plan.append({
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1
            })
            price += 100

    return plan
