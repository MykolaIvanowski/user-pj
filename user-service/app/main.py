from fastapi import FastAPI, Request

from app.api.v1.routers.users import router as users_router
from app.core.logging import get_logger, setup_logging

logger = get_logger("user-service")

app = FastAPI(title="User Service")

app.include_router(users_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        "request.start",
        method=request.method,
        path=request.url.path,
        client=str(request.client),
    )

    response = await call_next(request)

    logger.info(
        "request.end",
        status_code=response.status_code,
        method=request.method,
        path=request.url.path,
    )

    return response


@app.on_event("startup")
async def on_startup():
    setup_logging()
    logger.info("service.startup", msg="User Service started")


@app.get("/health")
async def health():
    logger.info("health.check")
    return {"status": "ok"}
