from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import appointments, catalog
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.services.seed import run_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        run_seed(db)
    yield


app = FastAPI(
    title="Northside Repair Desk API",
    description="Concurrency-safe appointment scheduling (demo)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointments.router)
app.include_router(catalog.router)
