from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, database
from pydantic import BaseModel
from .auth import get_current_user

router = APIRouter()

@router.get("/models")
async def list_models(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # List all available models
    models_list = db.query(models.MLModel).all()
    return models_list

@router.get("/models/{model_id}")
async def get_model_details(model_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Fetch a single model's details
    model = db.query(models.MLModel).filter(models.MLModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


class ChooseModelRequest(BaseModel):
    data_id: str
    model_type: str

@router.post("/choose-model")
async def choose_model(request: ChooseModelRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    model_type = request.model_type
    data_id = request.data_id
    current_user_balance = db.query(models.Bill).filter(models.Bill.user_id == current_user.id).first().amount
    model = db.query(models.MLModel).filter(models.MLModel.name == model_type).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if current_user_balance < model.cost:
        raise HTTPException(status_code=403, detail="Insufficient balance")
    return model
