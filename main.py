"""FastAPI entry point for WasteWise AI."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import APP_NAME, CORS_ORIGINS, MODEL_ARTIFACT_PATH
from app.database import db
from app.database.init_db import init_database
from app.ml.train_model import train_demand_model
from app.routes import (
    analytics,
    chatbot,
    dashboard,
    inventory,
    predictions,
    preparation,
    system,
    waste,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ensure SQLite database, synthetic demo records, and trained RF model exist on startup."""
    init_database(force_reset=False)
    if not MODEL_ARTIFACT_PATH.exists():
        train_demand_model(db)
    yield


app = FastAPI(
    title=APP_NAME,
    description="AI-Powered Food Waste Management System for College Canteens (JECRC University B.Tech CSE Data Science)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(predictions.router)
app.include_router(preparation.router)
app.include_router(waste.router)
app.include_router(inventory.router)
app.include_router(analytics.router)
app.include_router(chatbot.router)
app.include_router(system.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, _exc: Exception):
    """Avoid leaking internal tracebacks to API clients."""
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})


@app.get("/")
def root():
    return {
        "name": APP_NAME,
        "tagline": "Predict Better. Prepare Smarter. Waste Less.",
        "docs_url": "/docs",
    }
