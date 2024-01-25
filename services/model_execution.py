import os
import pickle
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import models, database
from pydantic import BaseModel
from .auth import get_current_user
from .billing import deduct_balance


router = APIRouter()

# Directory where uploaded files are stored
UPLOAD_DIR = os.path.join(os.getcwd(), 'upload-files', 'users-datasets')
os.makedirs(UPLOAD_DIR, exist_ok=True)

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')


class RunModelRequest(BaseModel):
    data_id: str
    model_name: str
    model_path: str
    model_cost: int

def run_model(data, file_path):
    with open(file_path, 'rb') as file:
        model = pickle.load(file)
    predictions = model.predict(data)
    
    return predictions

@router.post("/run-model")
async def execute_model(request: RunModelRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    data_file_path = os.path.join(UPLOAD_DIR, f"{request.data_id}.csv")
    model_file_path = os.path.join(MODEL_DIR, request.model_path)
    
    if not os.path.exists(data_file_path):
        raise HTTPException(status_code=404, detail="Uploaded data not found")

    data = pd.read_csv(data_file_path)
    # try:
    predictions = run_model(data, f".{model_file_path}")
    deduct_balance(current_user.id, request.model_cost, db)
    output = pd.DataFrame(predictions, columns=['Status'])
    download_path = f"download-files/prediction_{request.data_id}.csv"
    output.to_csv(download_path)
    
    return {"model_name": request.model_name, "price": request.model_cost,"predictions": f"{predictions}", "file_path": download_path, "data":f"{output}"}


@router.get("/download-files/{file_path}")
async def download(file_path: str):
    base_path = os.path.dirname(os.path.dirname(__file__))
    absolute_file_path = os.path.join(base_path, 'download-files', file_path)

    if os.path.exists(absolute_file_path):
        return FileResponse(path=absolute_file_path, filename=file_path, media_type='application/octet-stream')
    else:
        raise HTTPException(status_code=404, detail="File not found")
