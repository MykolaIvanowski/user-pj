from pydantic import BaseModel
from typing import List


class UserCreate(BaseModel):
    email: str
    full_name: str


class OrderRead(BaseModel):
    id: int
    item: str
    price: float

    class Config:
        orm_mode = True


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    orders: List[OrderRead] = []

    class Config:
        orm_mode = True
