from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128, description="Plain password; hashed server-side")
    # `metadata` shadows Model.metadata — use alias `user_metadata` internally
    user_metadata: dict[str, Any] | None = Field(default=None, alias="metadata", validation_alias="metadata", serialization_alias="metadata")


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=2048)
    user_metadata: dict[str, Any] | None = Field(default=None, alias="metadata", validation_alias="metadata", serialization_alias="metadata")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None
    user_metadata: dict[str, Any] | None = Field(default=None, alias="metadata", validation_alias="metadata", serialization_alias="metadata")
