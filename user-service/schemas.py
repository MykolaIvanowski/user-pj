from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    full_name: str


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool

    class Config:
        orm_mode = True

