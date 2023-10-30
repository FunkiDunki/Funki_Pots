from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


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
