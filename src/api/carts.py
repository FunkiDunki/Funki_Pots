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
        connection.execute(
            sqlalchemy.text("INSERT INTO cart_items (cart_id, item_sku, amount) \
                            VALUES (:cart, :sk, :am)"),
            {
                'cart': cart_id,
                'sk': item_sku,
                'am': cart_item.quantity
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
            sqlalchemy.text("SELECT cart_items.id id, cart_items.item_sku sku, cart_items.amount amount, potions.price price \
                            FROM cart_items JOIN potions ON cart_items.item_sku = potions.sku \
                            WHERE cart_items.cart_id = :cid"),
            {
                'cid':cart_id
            }
        ).all()

    gold_total = 0
    pots_total = 0

    with db.engine.begin() as connection:
        for purchase in purchases:
            gold = purchase.price * purchase.amount
            gold_total += gold
            pots = purchase.amount
            pots_total += pots
            pot_transaction = connection.execute(
                sqlalchemy.text("INSERT INTO transactions (sku, change, description) \
                                VALUES (:sk, :ch, :desc) \
                                RETURNING transaction_id"),
                {
                    'ch': -purchase.amount,
                    'sk': purchase.sku,
                    'desc': f"someone buys this potion"
                }
            ).first()
            gold_transaction = connection.execute(
                sqlalchemy.text("INSERT INTO transactions (sku, change, description) \
                                VALUES (:sk, :ch, :desc) \
                                RETURNING transaction_id"),
                {
                    'sk': 'GOLD',
                    'ch': gold,
                    'desc': f"someone buys a potion"
                }
            ).first()
            #now we update our cart_item to connect to the transaction
            connection.execute(
                sqlalchemy.text("UPDATE cart_items \
                                SET potion_transaction = :pt, gold_transaction = :gt \
                                WHERE id = :cit_id"),
                {
                    'pt': pot_transaction.transaction_id,
                    'gt': gold_transaction.transaction_id,
                    'cit_id': purchase.id
                }
            )

        #also, we want to store the payment they gave us
        connection.execute(
            sqlalchemy.text("UPDATE carts SET payment = :pay WHERE cart_id = :cid"),
            {
                'pay': cart_checkout.payment,
                'cid': cart_id
            }
        )
    
    
    return {"total_potions_bought": pots_total, "total_gold_paid": gold_total}
