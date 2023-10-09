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

    #find out our current inventory so we can update it
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT stock, ingredient, ingredient_order FROM inventory WHERE ingredient = TRUE ORDER BY ingredient_order ASC")
            )
        mls = result.all()
        result = connection.execute(
            sqlalchemy.text("SELECT name, stock FROM inventory WHERE name = 'gold'")
        )
        gold = result.first().stock
    red_mls = mls[0].stock
    green_mls = mls[1].stock

    #update that info with the delivered barrels
    for barrel in barrels_delivered:
        red_mls += (barrel.potion_type[0] * barrel.ml_per_barrel * barrel.quantity)
        green_mls += (barrel.potion_type[1] * barrel.ml_per_barrel * barrel.quantity)
        gold -= barrel.price * barrel.quantity
    
    #now update our database with the new information
    with db.engine.begin() as connection:
        query = sqlalchemy.text("UPDATE inventory SET stock = :mls WHERE sku = 'RED_ML'")
        result = connection.execute(query, {'mls': red_mls})
        query = sqlalchemy.text("UPDATE inventory SET stock = :mls WHERE sku = 'GREEN_ML'")
        connection.execute(query, {'mls': green_mls})
        query = sqlalchemy.text("UPDATE inventory SET stock = :g WHERE name = 'gold'")
        connection.execute(query, {'g': gold})
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT name, stock FROM inventory WHERE name = 'green potion'"))
        pots = result.first().stock
        gold = connection.execute(sqlalchemy.text("SELECT name, stock FROM invenotyr WHERE sku = 'GOLD'")).first().stock
    return [
        {
            "sku": "MINI_GREEN_BARREL",
            "quantity": 1 if pots < 10 and gold >= 60 else 0
        }
    ]
