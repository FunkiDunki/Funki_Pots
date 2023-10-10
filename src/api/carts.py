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
    with db.engine.begin() as connection:
        query = sqlalchemy.text("INSERT INTO carts (customer_name) VALUES ( :c ) RETURNING cart_id")
        result = connection.execute(query, {'c':new_cart.customer}).first().cart_id
    return {"cart_id": result}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        query = sqlalchemy.text("INSERT INTO cart_items (cart_id, item_sku, amount) VALUES (:cart, :sk, :am)")
        connection.execute(query, {'cart':cart_id, 'sk':item_sku, 'am':cart_item.quantity})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    #check database to find all items in their cart
    with db.engine.begin() as connection:
        #find all the purchases made
        query = sqlalchemy.text(
            "SELECT sku, price, amount FROM cart_items JOIN potions ON cart_items.item_sku = potions.sku WHERE cart_items.cart_id = :cid"
        )
        purchases = connection.execute(
            query,
            {
                'cid':cart_id
            }
        ).all()

    gold_paid = 0
    pots_bought = 0

    with db.engine.begin() as connection:
        for purchase in purchases:
            gold_paid += purchase.price * purchase.amount
            pots_bought += purchase.amount
            query = sqlalchemy.text(
                "UPDATE inventory SET stock = stock - :am WHERE sku = :sk"
            )
            connection.execute(
                query,
                {
                    'am': purchase.amount,
                    'sk': purchase.sku
                }
            )
        #now we update our gold
        query = sqlalchemy.text(
            "UPDATE inventory SET stock = stock + :g WHERE sku = 'GOLD'"
        )
        connection.execute(
            query,
            {
                'g': gold_paid
            }
        )
    
    
    return {"total_potions_bought": pots_bought, "total_gold_paid": gold_paid}
