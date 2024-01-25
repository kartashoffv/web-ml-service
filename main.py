from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

from services.auth import router as auth_router
from services.billing import router as billing_router
from services.data_management import router as data_management_router
from services.model_execution import router as model_execution_router
from services.model_broker import router as model_broker_router

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import MLModel, Base

import app as dash_app
import models

app = FastAPI()

# Include the routers
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(data_management_router)
app.include_router(model_execution_router)
app.include_router(model_broker_router)

app.mount("/dash", WSGIMiddleware(dash_app.server))

# Function to create tables and add initial data
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if the data already exists to prevent duplicates
    if db.query(MLModel).first() is None:
        new_model = MLModel(name='CatBoost', file_path='/models/CatBoost.pkl', cost=30)
        new_model1 = MLModel(name='Logistic Regression', file_path='/models/LogisticRegression.pkl', cost=10)
        new_model2 = MLModel(name='Random Forest', file_path='/models/RandomForest.pkl', cost=20)

        db.add(new_model)
        db.add(new_model1)
        db.add(new_model2)
        db.commit()

    db.close()

@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    from database import engine
    import models
    models.Base.metadata.create_all(bind=engine)
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
