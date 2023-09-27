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
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row = result.first()
    red_mls = row[1]
    gold = row[2]

    #update that info with the delivered barrels
    for barrel in barrels_delivered:
        red_mls += (barrel.potion_type[0] * barrel.ml_per_barrel * barrel.quantity) / 100
        gold -= barrel.price * barrel.quantity
    
    #now update our database with the new information
    with db.engine.begin() as connection:
        query = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :mls , gold = :g")
        result = connection.execute(query, {'mls': red_mls, 'g': gold})
        connection.commit()
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
    pots = result.first()[0]
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1 if pots < 10 else 0
        }
    ]
