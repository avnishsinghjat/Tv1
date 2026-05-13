"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from tenacity import RetryCallState, retry, retry_if_exception, stop_after_delay, wait_exponential

from app.api.routes import auth, fetch, health, objects
from app.config import settings
from app.database import Base, engine
from app.schema_fixup import quarantine_legacy_tc_objects_table
from app.utils.logger import configure_logging, get_logger

log = get_logger("app")


def _transient_db_connect_error(exc: BaseException) -> bool:
    if not isinstance(exc, OperationalError):
        return False
    msg = str(getattr(exc, "orig", None) or exc).lower()
    return any(
        s in msg
        for s in (
            "could not translate host name",
            "temporary failure in name resolution",
            "name or service not known",
            "eai_again",
        )
    )


def _before_db_retry(retry_state: RetryCallState) -> None:
    log.warning(
        "db_connect_retry",
        attempt=retry_state.attempt_number,
        wait_seconds=retry_state.next_action.sleep,
    )


@retry(
    stop=stop_after_delay(120),
    wait=wait_exponential(multiplier=0.5, min=0.8, max=15),
    retry=retry_if_exception(_transient_db_connect_error),
    before_sleep=_before_db_retry,
    reraise=True,
)
def _prepare_schema() -> None:
    quarantine_legacy_tc_objects_table(engine)
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    try:
        _prepare_schema()
    except OperationalError:
        log.exception("startup_db_schema_failed")
        raise
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
