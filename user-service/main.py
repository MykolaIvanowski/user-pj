from fastapi import FastAPI
from routers.users import router
from database import init_db


app  = FastAPI(title="User service")

@app.on_event('startup')
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(router)