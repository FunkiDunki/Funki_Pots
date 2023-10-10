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
        price = connection.execute(
            sqlalchemy.text("SELECT price FROM potions WHERE sku = :sk"),
            { 'sk': item_sku }
        ).first().price
        connection.execute(
            sqlalchemy.text("INSERT INTO cart_items (cart_id, item_sku, amount, historic_price) \
                            VALUES (:cart, :sk, :am, :price)"),
            {
                'cart': cart_id,
                'sk': item_sku,
                'am': cart_item.quantity,
                'price': price
            }
        )
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    #check database to find all items in their cart
    with db.engine.begin() as connection:
        #find all the purchases made
        purchases = connection.execute(
            sqlalchemy.text("SELECT item_sku, historic_price, amount FROM cart_items WHERE cart_items.cart_id = :cid"),
            {
                'cid':cart_id
            }
        ).all()

    gold_paid = 0
    pots_bought = 0

    with db.engine.begin() as connection:
        for purchase in purchases:
            gold_paid += purchase.historic_price * purchase.amount
            pots_bought += purchase.amount
            connection.execute(
                sqlalchemy.text("UPDATE inventory SET stock = stock - :am WHERE sku = :sk"),
                {
                    'am': purchase.amount,
                    'sk': purchase.item_sku
                }
            )
        #now we update our gold
        
        connection.execute(
            sqlalchemy.text("UPDATE inventory SET stock = stock + :g WHERE sku = 'GOLD'"),
            {
                'g': gold_paid
            }
        )
        connection.execute(
            sqlalchemy.text("UPDATE carts SET payment = :pay WHERE cart_id = :cid"),
            {
                'pay': cart_checkout.payment,
                'cid': cart_id
            }
        )
    
    
    return {"total_potions_bought": pots_bought, "total_gold_paid": gold_paid}
