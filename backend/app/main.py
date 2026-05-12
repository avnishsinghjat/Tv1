"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, fetch, health, objects
from app.config import settings
from app.database import Base, engine
from app.schema_fixup import quarantine_legacy_tc_objects_table
from app.utils.logger import configure_logging, get_logger

log = get_logger("app")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    quarantine_legacy_tc_objects_table(engine)
    Base.metadata.create_all(bind=engine)
    log.info("startup", app=settings.app_name, env=settings.app_env)
    yield
    log.info("shutdown")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

_cors_origins = settings.cors_origins
_cors_credentials = bool(_cors_origins)
if not _cors_origins:
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api")
app.include_router(fetch.router, prefix="/api")
app.include_router(objects.router, prefix="/api")
