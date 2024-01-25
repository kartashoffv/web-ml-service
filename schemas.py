from pydantic import BaseModel
from typing import List

class BillBase(BaseModel):
    amount: int

class Bill(BillBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
        
class BuyCoinsRequest(BaseModel):
    amount: int

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    bills: List[Bill] = []
    class Config:
        orm_mode = True
