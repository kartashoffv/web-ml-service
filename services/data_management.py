from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import JSONResponse
import pandas as pd
from uuid import uuid4
import os
import shutil
import models
from .auth import get_current_user

router = APIRouter()

# Directory where uploaded files will be stored
UPLOAD_DIR = os.path.join(os.getcwd(), 'upload-files', 'users-datasets')
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-data")
async def upload_data(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user)):
    user_id = current_user.id
    required_columns = [
        "N_Days", "Drug", "Age", "Sex", "Ascites", "Hepatomegaly", "Spiders", "Edema", 
        "Bilirubin", "Cholesterol", "Albumin", "Copper", "Alk_Phos", "SGOT", 
        "Tryglicerides", "Platelets", "Prothrombin", "Stage"
    ]
    try:
        # Generate a unique ID for the data
        data_id = str(uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{data_id}.csv")

        # Save the file to the file system
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Read and validate the CSV file
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()  # Clean column names

        # Check if the DF contains all required columns
        if not set(required_columns).issubset(df.columns):
            missing_columns = set(required_columns) - set(df.columns)
            raise ValueError(f"The file was not loaded due to incorrect data columns. The file is missing the following columns: {missing_columns}")
        
        return {"data_id": data_id, "file_path": file_path, "message": "File uploaded and processed successfully"}
    
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"There was an error processing the file: {e}")
    finally:
        await file.close()
