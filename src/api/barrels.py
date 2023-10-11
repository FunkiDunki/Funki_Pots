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
        gold = connection.execute(sqlalchemy.text("SELECT name, stock FROM inventory WHERE sku = 'GOLD'")).first().stock
        wishlist = connection.execute(
            sqlalchemy.text("SELECT sku, amount FROM barrel_wishlist WHERE amount > 0 ORDER BY priority ASC")
        ).all()
    

    price = 0
    plan = []

    #for each item we want, check if it is for sale:
    for dream in wishlist:
        for barrel in wholesale_catalog:
            #check if this is the dream item
            if barrel.sku != dream.sku:
                continue
            #now check if we have enough gold
            if gold - price < barrel.price:
                continue #we don't have enough for one of them
            #now we add however many we can afford, limited by the amount we want and the amount for sale
            i = min((gold - price) // barrel.price, dream.amount, barrel.quantity)
            price += i * barrel.price
            plan.append({
                "sku": barrel.sku,
                "quantity": i
            })

    return plan
