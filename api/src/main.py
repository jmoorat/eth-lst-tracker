from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/prices")
def get_last_prices(db: Session = Depends(get_db)):
    last_prices = crud.get_last_prices(db)
    return last_prices


@app.get("/prices/{token_name}")
def get_price_history(token_name: str, network: str, db: Session = Depends(get_db), is_primary_market: bool = True):
    if network != "ethereum":
        is_primary_market = False
    result = crud.get_price_history(db, token_name, network, is_primary_market)

    return result


@app.get("/prices/{token_name}/last")
def get_last_price(token_name: str, network: str, db: Session = Depends(get_db), is_primary_market: bool = True):
    if network != "ethereum":
        is_primary_market = False
    last_prices = crud.get_last_price(db, token_name, network, is_primary_market)

    if not last_prices:
        raise HTTPException(status_code=404, detail="Item not found")

    return last_prices
