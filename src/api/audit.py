from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
from src import database as db
import sqlalchemy

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        #find gold
        q1 = sqlalchemy.text("SELECT COALESCE(SUM(change), 0) stock FROM transactions \
                             WHERE sku = 'GOLD'")
        gold = connection.execute(q1).first().stock
        #find number of potions
        q2 = sqlalchemy.text("SELECT COALESCE(SUM(CHANGE), 0) stock, sku FROM transactions \
                             WHERE sku IN (SELECT sku FROM potions) GROUP BY sku")
        pots = connection.execute(q2).all()
        pots = [r.stock for r in pots]
        pots = sum(pots)
        #find the total mls
        q3 = sqlalchemy.text("SELECT COALESCE(SUM(CHANGE), 0) stock, sku FROM transactions \
                             WHERE sku IN (SELECT sku FROM ingredients) GROUP BY sku")
        mls = connection.execute(q3).all()
        mls = [r.stock for r in mls]
        mls = sum(mls)
    
    return {"number_of_potions": pots, "ml_in_barrels": mls, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
