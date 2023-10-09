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
    blue_mls = mls[2].stock

    #update that info with the delivered barrels
    for barrel in barrels_delivered:
        red_mls += (barrel.potion_type[0] * barrel.ml_per_barrel * barrel.quantity)
        green_mls += (barrel.potion_type[1] * barrel.ml_per_barrel * barrel.quantity)
        blue_mls += (barrel.potion_type[2] * barrel.ml_per_barrel * barrel.quantity)
        gold -= barrel.price * barrel.quantity
    
    #now update our database with the new information
    with db.engine.begin() as connection:
        query = sqlalchemy.text("UPDATE inventory SET stock = :mls WHERE sku = 'RED_ML'")
        result = connection.execute(query, {'mls': red_mls})
        query = sqlalchemy.text("UPDATE inventory SET stock = :mls WHERE sku = 'GREEN_ML'")
        connection.execute(query, {'mls': green_mls})
        connection.execute(
            sqlalchemy.text("UPDATE inventory SET stock = :mls WHERE sku = 'BLUE_ML'"),
            { 'mls': blue_mls}
        )
        query = sqlalchemy.text("UPDATE inventory SET stock = :g WHERE name = 'gold'")
        connection.execute(query, {'g': gold})
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT name, stock FROM inventory WHERE name = 'blue potion'"))
        blue_pots = result.first().stock
        gold = connection.execute(sqlalchemy.text("SELECT name, stock FROM inventory WHERE sku = 'GOLD'")).first().stock
        red_pots = connection.execute(
            sqlalchemy.text("SELECT stock FROM inventory WHERE sku = 'RED_POTION_0'")
        ).first().stock
        green_pots = connection.execute(sqlalchemy.text(
            "SELECT stock FROM inventory WHERE sku = 'GREEN_POTION_0'"
        )).first().stock
    
    price = 0
    plan = []

    if blue_pots < 10 and gold >= 60:
        plan.append({
            "sku": "MINI_BLUE_BARREL",
            "quantity": 1
        })
        price += 60
    if red_pots < 10 and gold - price >= 60:
        plan.append({
            "sku": "MINI_RED_BARREL",
            "quantity": 1
        })
        price += 60
    if green_pots < 10 and gold - price >= 60:
        plan.append({
            "sku": "MINI_GREEN_BARREL",
            "quantity": 1
        })

    return plan
