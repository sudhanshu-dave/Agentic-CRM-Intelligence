from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api import actions, agent, analytics, audit, classification, dashboard, emails, health, ingest, rag, threads
from app.config import settings
from app.core.errors import (
    AppError,
    app_error_handler,
    validation_exception_handler,
)
from app.database import Base, engine

# Important: importing models registers them with SQLAlchemy metadata.
from app import models  # noqa: F401


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="AI-powered CRM email triage and agentic operations platform.",
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(dashboard.router)
app.include_router(threads.router)
app.include_router(emails.router)
app.include_router(rag.router)
app.include_router(classification.router)
app.include_router(agent.router)
app.include_router(analytics.router)
app.include_router(audit.router)
app.include_router(actions.router)

@app.get("/")
def root():
    return {
        "success": True,
        "message": "Agentic CRM Intelligence Platform API is running.",
        "docs": "/docs",
        "health": "/health",
    }