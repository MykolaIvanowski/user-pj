from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    metadata: dict | None = None

class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
    metadata: dict | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    avatar_url: str | None
    metadata: dict | None

    class Config:
        orm_mode = True
