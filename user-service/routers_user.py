from http.client import HTTPException

from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from crud import create_user, get_user, list_users
from schemas import UserCreate, UserRead
from dependencies import get_current_user


router  = APIRouter(prefix="/user", tags=["User"])

@router.get("/", responce_model=list[UserRead])
def get_all_users(session: Session = Depends(get_session),
                  user=Depends(get_current_user)):
    return list_users(session=session)

@router.post("/", responce_model=UserRead)
def create_new_user(data: UserCreate, session=Depends(get_session),
                    user=Depends(get_current_user)):
    return create_user(session, user)


@router.get("/{user_id}", responce_model=UserRead)
def get_user_by_id(user_id: int, session: Session=Depends(get_session),
                   user=Depends(get_current_user)):
    result = get_user(session, user_id=user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result