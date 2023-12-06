from fastapi import FastAPI, exceptions
from fastapi.responses import JSONResponse
from pydantic import ValidationError
#from src.api import audit, carts, catalog, bottler, barrels, admin
from src.api import admin, accounts
import json
import logging
import sys
from starlette.middleware.cors import CORSMiddleware

description = """
Elo Keeper is the spot to go for keeping track of your competition!
"""

app = FastAPI(
    title="Elo Keeper",
    description=description,
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Nicholas Hotelling",
        "email": "nicholashotelling@gmail.com",
    },
)

origins = ["https://potion-exchange.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

#app.include_router(audit.router)
app.include_router(admin.router)
app.include_router(accounts.router)

@app.exception_handler(exceptions.RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    logging.error(f"The client sent invalid data!: {exc}")
    exc_json = json.loads(exc.json())
    response = {"message": [], "data": None}
    for error in exc_json:
        response['message'].append(f"{error['loc']}: {error['msg']}")

    return JSONResponse(response, status_code=422)

@app.get("/")
async def root():
    return {"message": "Welcome to the Elo Keeper."}
