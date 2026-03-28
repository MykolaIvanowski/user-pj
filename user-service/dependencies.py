from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from config import JWT_SECRET, JWT_ALGORITHM
import jwt


def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exceptiona as e:
        raise HTTPException(status_code=401, details="Invalid token")



