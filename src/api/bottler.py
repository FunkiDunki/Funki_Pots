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
    #find our current stock of ingredients, and our potion wishlist 
    with db.engine.begin() as connection:
        ingredients = connection.execute(
            sqlalchemy.text("SELECT inventory.sku as sku, ingredient_order, stock FROM \
                            inventory JOIN ingredients ON inventory.sku = ingredients.sku \
                            ORDER BY ingredient_order ASC")
        ).all()
        wishlist = connection.execute(
            sqlalchemy.text("SELECT recipe, stock, amount FROM \
                            inventory JOIN \
                            (SELECT sku, priority, amount, recipe FROM \
                            potions JOIN potions_wishlist ON potions.id = potions_wishlist.potion_id) AS pots \
                            ON inventory.sku = pots.sku \
                            ORDER BY pots.priority ASC")
        ).all()
    
    ingredients = [row.stock for row in ingredients]
    plan = []

    #go through our wishlist, by priority
    for wish in wishlist:
        #check how many we can make
        num_pots = 0#number of potions we can make
        any_yet = False#flag for whether we've used any ingredients for this recipe
        for i, ml in enumerate(wish.recipe):
            if ml == 0:
                continue #we shouldn't be checking how many times we can make the 0 cost parts of a recipe
            tmp = min(ingredients[i] // ml, wish.amount - wish.stock)#how many potions we can make if they only cost this ingredient
            if any_yet:
                num_pots = min(tmp, num_pots)#how many potions we can make, including any previous ingredients
            else:
                num_pots = tmp
        #based on how many pots we could make, add to the plan and subtract from ingredients
        if num_pots > 0:
            plan.append({
                "potion_type": wish.recipe,
                "quantity": num_pots
            })
            for i, ml in enumerate(wish.recipe):
                ingredients[i] -= ml * num_pots #subtract ingredients

    return plan
