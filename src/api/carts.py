from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    return {"cart_id": 1}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    #TODO: change to use a carts table

    #update table with purchase info:
    with db.engine.begin() as connection:
        query = sqlalchemy.text("SELECT num_red_potions, gold from global_inventory")
        result = connection.execute(query).first()
        pots = result[0] - 1
        gold = result[1] + 50
        query = sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :r , gold = :g")
        connection.execute(query, {"r":pots, "g":gold})

    return {"total_potions_bought": 1, "total_gold_paid": 50}
