from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    full_name: str
    is_active: bool = True

    orders: List["Order"] = Relationship(back_populates="user")


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item: str
    price: float

    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="orders")
