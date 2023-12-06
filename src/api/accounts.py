from fastapi import APIRouter, Request
from pydantic import BaseModel
from src import database as db
import sqlalchemy
from sqlalchemy.exc import DBAPIError

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"]
)

class AccountInfo(BaseModel):
    name: str
    email: str
    password: str
class SignInInfo(BaseModel):
    email: str
    password: str

@router.post("/")
def register_account(info: AccountInfo):
    """
    Registers a new account
    """
    try:
        with db.engine.begin() as connection:
            connection.execute(
                sqlalchemy.text(
                    """
                    Insert into accounts
                    (name, email, password)
                    Values
                    (:n, :e, :p)
                    """
                ),
                {
                    'n': info.name,
                    'e': info.email,
                    'p': info.password
                }
            )
        return [True]
    except DBAPIError as error:
        print(error)
        return [False]
@router.post("/login")
def sign_in_to_account(info: SignInInfo):
    '''Attempt to sign in to account, revealing id of account if successful.'''
    try:
        with db.engine.begin() as connection:
            row = connection.execute(sqlalchemy.text(
                """Select uid, name, password
                from accounts
                where email = :email"""
            ),
            {
                'email': info.email
            }).first()
        if row is not None and row.password == info.password:
            #success
            return [
                True,
                {
                    "name": row.name,
                    "id": row.uid
                }]
        else:
            #failure
            return [
                False,
                {}
            ]
    except DBAPIError as error:
        print(error)