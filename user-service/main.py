from fastapi import FastAPI
from app.api.v1.routers import auth
from app.db.database import init_db

app = FastAPI(title="User Service")

app.include_router(auth.router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth.router)
