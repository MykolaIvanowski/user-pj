from sqlmodel import Session, select
from models import User
from schemas import UserCreate


def create_user(session: Session, data: UserCreate)-> User:
    user = user(email=data.email, full_name=data.full_name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)

def list_users(session: Session):
    return session.exec(select(User)).all()

