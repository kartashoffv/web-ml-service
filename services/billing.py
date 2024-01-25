from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, database
from typing import List
from .auth import get_current_user

router = APIRouter()

# Dependency to get the database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/bills/{user_id}", response_model=List[schemas.Bill])
def read_bills(user_id: int, db: Session = Depends(get_db)):
    bills = db.query(models.Bill).filter(models.Bill.user_id == user_id).all()
    return bills


@router.get("/get-bill-balance")
def get_bill_balance(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user_bill = db.query(models.Bill).filter(models.Bill.user_id == current_user.id).first()
    if not user_bill:
        raise HTTPException(status_code=404, detail="Bill record not found")
    return {"balance": user_bill.amount}


@router.post("/buy-coins")
def buy_coins(request: schemas.BuyCoinsRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    amount = request.amount
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    user_bill = db.query(models.Bill).filter(models.Bill.user_id == current_user.id).first()
    if not user_bill:
        user_bill = models.Bill(user_id=current_user.id, amount=0)
        db.add(user_bill)

    user_bill.amount += amount
    db.commit()

    return {"message": f"Successfully purchased {amount} coins."}


def deduct_balance(user_id: int, amount: int, db: Session):
    user_bill = db.query(models.Bill).filter(models.Bill.user_id == user_id).first()
    if not user_bill:
        raise HTTPException(status_code=400, detail="User's bill not found")
    
    if user_bill.amount < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    user_bill.amount -= amount
    db.commit()
